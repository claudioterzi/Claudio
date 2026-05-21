"""
GUARD LOCKING PROTOCOL - LGAI Safety System
Ispirato al TLSZR/L-GD2 Guard Locking Switch (Rockwell Automation)

Principio: come l'interruttore TLSZR che blocca l'accesso fisico finché
la macchina non torna in stato sicuro (verde fisso), questo protocollo
BLOCCA azioni rischiose quando il player è in zona critica (Sopravvivenza)
e si SBLOCCA solo al ritorno in zona sicura (Crescita/Trasformazione).

Rosso Rosso Rosso = protocollo di massima allerta, reset e recupero.
Verde Fisso       = stato verificato sicuro, protezioni rilasciate.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
from datetime import datetime, timedelta
from .calculator import PlayerStats, Zona, LGAICalculator


# ---------------------------------------------------------------------------
# Tipi e costanti
# ---------------------------------------------------------------------------

class GuardState(Enum):
    """Stato del blocco di sicurezza"""
    UNLOCKED = "SBLOCCATO"   # Zona verde: sistema libero
    ALERT    = "ALLERTA"     # Zona gialla: avviso, attenzione
    LOCKED   = "BLOCCATO"    # Zona rossa: blocco attivo


class LockedAction(Enum):
    """Azioni bloccate durante lo stato LOCKED"""
    SPEND_BAROS        = "Spendere Baros"
    BREAKTHROUGH_MISSIONS = "Missioni Breakthrough"
    SKIP_CHECKIN       = "Saltare il Check-in"
    SKIP_CHECKOUT      = "Saltare il Check-out"
    ADD_NEGATIVE_HABITS = "Aggiungere abitudini negative extra"


# PV sotto cui scatta il LOCKED
PV_LOCK_THRESHOLD    = 30   # ≤30 PV → LOCKED  (Zona Sopravvivenza)
PV_ALERT_THRESHOLD   = 50   # ≤50 PV → ALERT   (parte bassa Zona Stagnazione)
# PV minimi per sblocco (deve essere in Crescita, cioè >60)
PV_UNLOCK_THRESHOLD  = 61   # ≥61 PV → può sbloccarsi
# Giorni consecutivi in zona sicura richiesti per confermare sblocco
DAYS_STABLE_REQUIRED = 2


# ---------------------------------------------------------------------------
# Dataclass stato
# ---------------------------------------------------------------------------

@dataclass
class GuardStatus:
    """Snapshot completo dello stato del Guard Protocol"""
    state: GuardState
    pv_current: int
    pv_threshold_lock: int    = PV_LOCK_THRESHOLD
    pv_threshold_unlock: int  = PV_UNLOCK_THRESHOLD
    locked_since: Optional[datetime] = None
    days_locked: int = 0
    days_stable: int = 0
    locked_actions: List[LockedAction] = field(default_factory=list)
    alert_message: str = ""
    unlock_conditions: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Classe principale
# ---------------------------------------------------------------------------

class GuardLockingProtocol:
    """
    Protocollo di blocco di sicurezza LGAI.

    Funzionamento (analogo TLSZR):
    ┌─────────────────────────────────────────────────────────────┐
    │  PV ≤ 30  →  LOCKED   🔴  (Rosso Rosso Rosso)             │
    │  PV 31-50 →  ALERT    🟡  (Attenzione, soglia critica)     │
    │  PV ≥ 61  →  UNLOCKED 🟢  (Verde Fisso, sblocco possibile) │
    │                                                             │
    │  Il sistema si sblocca SOLO dopo DAYS_STABLE_REQUIRED       │
    │  giorni consecutivi in zona sicura. Nessuno scorciatoia.   │
    └─────────────────────────────────────────────────────────────┘
    """

    def __init__(self):
        self.calc = LGAICalculator()
        self._locked_since: Optional[datetime] = None
        self._days_stable: int = 0

    # ------------------------------------------------------------------
    # API pubblica
    # ------------------------------------------------------------------

    def evaluate(self, stats: PlayerStats) -> GuardStatus:
        """
        Valuta lo stato corrente del Guard Protocol basandosi sui PV.
        Chiamare dopo ogni modifica PV per aggiornare il blocco.

        Returns:
            GuardStatus con stato completo e messaggi d'azione.
        """
        pv = stats.pv_current
        state = self._determine_state(pv)

        # Gestione transizioni di stato
        if state == GuardState.LOCKED:
            if self._locked_since is None:
                self._locked_since = datetime.now()
            self._days_stable = 0
        elif state == GuardState.UNLOCKED:
            self._days_stable += 1
        else:  # ALERT
            self._days_stable = max(0, self._days_stable - 1)

        # Calcola giorni in lock
        days_locked = 0
        if self._locked_since:
            days_locked = (datetime.now() - self._locked_since).days

        return GuardStatus(
            state=state,
            pv_current=pv,
            locked_since=self._locked_since if state == GuardState.LOCKED else None,
            days_locked=days_locked,
            days_stable=self._days_stable,
            locked_actions=self._get_locked_actions(state),
            alert_message=self._generate_alert_message(state, pv, days_locked),
            unlock_conditions=self._get_unlock_conditions(state, pv, self._days_stable),
        )

    def is_action_locked(self, stats: PlayerStats, action: LockedAction) -> bool:
        """
        Verifica se un'azione specifica è bloccata.

        Returns:
            True se bloccata, False se consentita.
        """
        status = self.evaluate(stats)
        return action in status.locked_actions

    def check_unlock(self, stats: PlayerStats) -> bool:
        """
        Verifica se le condizioni di sblocco sono soddisfatte.
        Il sistema si sblocca solo con PV ≥ 61 E giorni stabili sufficienti.

        Returns:
            True se il blocco può essere rilasciato.
        """
        if stats.pv_current >= PV_UNLOCK_THRESHOLD:
            if self._days_stable >= DAYS_STABLE_REQUIRED:
                self._locked_since = None  # Reset lock
                return True
        return False

    def force_unlock(self, reason: str = "Resurrezione completata") -> bool:
        """
        Sblocco forzato (usato dopo Sfida di Resurrezione completata).
        Richiede una reason esplicita per audit.

        Returns:
            True, conferma sblocco.
        """
        self._locked_since = None
        self._days_stable = DAYS_STABLE_REQUIRED  # Reset a stabile
        return True

    def generate_rosso_rosso_rosso(self, stats: PlayerStats) -> str:
        """
        Genera il messaggio di protocollo 🔴🔴🔴 ROSSO ROSSO ROSSO.
        Attivato quando PV ≤ 30 (Zona Sopravvivenza).

        Returns:
            Stringa con il messaggio di allerta massima e istruzioni.
        """
        pv = stats.pv_current
        giorni_a_gameover = max(1, pv // 15) if pv > 0 else 0
        giorni_locked = 0
        if self._locked_since:
            giorni_locked = (datetime.now() - self._locked_since).days

        msg = f"""
╔══════════════════════════════════════════════════════════════╗
║          🔴🔴🔴 PROTOCOLLO ROSSO ROSSO ROSSO 🔴🔴🔴         ║
║              GUARD LOCKING PROTOCOL — ATTIVATO              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  PV CORRENTI: {pv:3d}/100    STATO: ⛔ BLOCCATO              ║
║  Zona: SOPRAVVIVENZA  |  Giorni in lock: {giorni_locked}               ║
║                                                              ║
║  ⚠️  RISCHIO GAME OVER: ~{giorni_a_gameover} giorni al collasso          ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  AZIONI BLOCCATE:                                           ║
║  • Spendere Baros (preserva risorse)                        ║
║  • Missioni Breakthrough (troppo intense ora)               ║
║  • Saltare Check-in / Check-out                             ║
╠══════════════════════════════════════════════════════════════╣
║  PER SBLOCCARE IL SISTEMA (Verde Fisso):                    ║
║  1. Raggiungi ≥ {PV_UNLOCK_THRESHOLD} PV (Zona Crescita)                    ║
║  2. Mantieni PV ≥ {PV_UNLOCK_THRESHOLD} per {DAYS_STABLE_REQUIRED} giorni consecutivi           ║
║  3. OPPURE completa una Sfida di Resurrezione               ║
╠══════════════════════════════════════════════════════════════╣
║  MISSIONE PRIORITÀ ASSOLUTA:                                ║
║  → Solo recupero. Niente breakthrough. SOPRAVVIVI.          ║
║  → Dormi 8h. Mangia bene. Idratati. Respira.                ║
║  → Ogni abitudine positiva = +PV verso il verde.            ║
╚══════════════════════════════════════════════════════════════╝
"""
        return msg.strip()

    def get_status_line(self, stats: PlayerStats) -> str:
        """
        Riga di stato breve per l'integrazione nel CLI.

        Returns:
            Stringa compatta con stato e icona.
        """
        status = self.evaluate(stats)
        icons = {
            GuardState.LOCKED:   "🔴 GUARD LOCK: ⛔ BLOCCATO",
            GuardState.ALERT:    "🟡 GUARD LOCK: ⚠️  ALLERTA",
            GuardState.UNLOCKED: "🟢 GUARD LOCK: ✅ SBLOCCATO",
        }
        return icons[status.state]

    # ------------------------------------------------------------------
    # Metodi privati
    # ------------------------------------------------------------------

    def _determine_state(self, pv: int) -> GuardState:
        """Determina stato Guard in base ai PV"""
        if pv <= PV_LOCK_THRESHOLD:
            return GuardState.LOCKED
        elif pv <= PV_ALERT_THRESHOLD:
            return GuardState.ALERT
        else:
            return GuardState.UNLOCKED

    def _get_locked_actions(self, state: GuardState) -> List[LockedAction]:
        """Restituisce le azioni bloccate per lo stato corrente"""
        if state == GuardState.LOCKED:
            return list(LockedAction)  # Tutte bloccate
        elif state == GuardState.ALERT:
            return [
                LockedAction.BREAKTHROUGH_MISSIONS,
                LockedAction.SKIP_CHECKIN,
                LockedAction.SKIP_CHECKOUT,
            ]
        else:
            return []

    def _generate_alert_message(self, state: GuardState, pv: int, days_locked: int) -> str:
        """Genera messaggio d'allerta contestuale"""
        if state == GuardState.LOCKED:
            return (
                f"🔴🔴🔴 GUARD LOCK ATTIVO — PV critici ({pv}/100). "
                f"Blocco attivo da {days_locked} giorno/i. "
                f"Raggiungi {PV_UNLOCK_THRESHOLD}+ PV per {DAYS_STABLE_REQUIRED} giorni per sbloccare."
            )
        elif state == GuardState.ALERT:
            pv_to_lock = pv - PV_LOCK_THRESHOLD
            return (
                f"🟡 ALLERTA GUARD — PV bassi ({pv}/100). "
                f"Sei a {pv_to_lock} PV dal blocco totale. "
                f"Aumenta le abitudini positive ora."
            )
        else:
            return f"🟢 Sistema sicuro — PV {pv}/100. Guard Protocol inattivo."

    def _get_unlock_conditions(
        self, state: GuardState, pv: int, days_stable: int
    ) -> List[str]:
        """Genera lista condizioni da soddisfare per sblocco"""
        if state == GuardState.UNLOCKED:
            return ["✅ Nessuna condizione — sistema libero"]

        conditions = []

        if pv < PV_UNLOCK_THRESHOLD:
            conditions.append(
                f"⬆️  Raggiungi {PV_UNLOCK_THRESHOLD} PV (attuale: {pv}/100, mancano {PV_UNLOCK_THRESHOLD - pv} PV)"
            )
        else:
            conditions.append(f"✅ PV sufficienti ({pv}/100 ≥ {PV_UNLOCK_THRESHOLD})")

        if days_stable < DAYS_STABLE_REQUIRED:
            conditions.append(
                f"📅 Mantieni PV ≥ {PV_UNLOCK_THRESHOLD} per {DAYS_STABLE_REQUIRED} giorni "
                f"(attuale: {days_stable}/{DAYS_STABLE_REQUIRED} giorni stabili)"
            )
        else:
            conditions.append(
                f"✅ Giorni stabili sufficienti ({days_stable}/{DAYS_STABLE_REQUIRED})"
            )

        conditions.append(
            f"🔥 ALTERNATIVA: Completa la Sfida di Resurrezione → sblocco immediato"
        )

        return conditions


# ---------------------------------------------------------------------------
# Demo standalone
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from calculator import PlayerStats

    print("=== GUARD LOCKING PROTOCOL Demo ===\n")

    player = PlayerStats()
    guard = GuardLockingProtocol()

    # Scenario 1: PV critici → LOCKED
    print("Scenario 1: PV = 20 (Zona Sopravvivenza)")
    player.pv_current = 20
    print(guard.generate_rosso_rosso_rosso(player))
    print()

    # Scenario 2: PV allerta
    print("Scenario 2: PV = 45 (Zona Allerta)")
    player.pv_current = 45
    status = guard.evaluate(player)
    print(f"   Stato: {status.state.value}")
    print(f"   Messaggio: {status.alert_message}")
    print(f"   Azioni bloccate: {[a.value for a in status.locked_actions]}")
    print()

    # Scenario 3: PV sicuri → UNLOCKED
    print("Scenario 3: PV = 80 (Zona Crescita)")
    player.pv_current = 80
    status = guard.evaluate(player)
    print(f"   Stato: {status.state.value}")
    print(f"   Status line: {guard.get_status_line(player)}")
    print()

    # Test is_action_locked
    print("Test is_action_locked:")
    player.pv_current = 25
    for action in LockedAction:
        locked = guard.is_action_locked(player, action)
        print(f"   {action.value}: {'🔒 BLOCCATO' if locked else '✅ Consentito'}")

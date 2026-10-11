"""Radar Emozionale — misura la 'temperatura' del sistema SDQ-1.

Legge contatti, battiti, contraddizioni e produce indici longitudinali:
  - energia_sistema: vitalità tecnica (0-1)
  - tensione_interna: contraddizioni accumulate (0-1)
  - vitalita_esterna: contatto col mondo reale (0-1)
  - indice_morale: combinazione pesata (0-1)

Salva snapshot in output/radar/ per vista longitudinale.

Uso:
    from sdq1.sar.radar_emozionale import RadarEmozionale
    radar = RadarEmozionale()
    snapshot = radar.misura()
    print(snapshot['indice_morale'])
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO / "output" / "radar"


def _leggi_jsonl(path: Path, ultimi: int = 0) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    righe = []
    try:
        for riga in path.read_text(encoding="utf-8").strip().splitlines():
            righe.append(json.loads(riga))
    except Exception:
        pass
    return righe[-ultimi:] if ultimi else righe


def _leggi_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


class RadarEmozionale:
    """Misura la 'temperatura emotiva' del sistema SDQ-1.

    Non usa LLM — è puramente metrico, così gira sempre anche offline.
    Le metriche sono normalizzate 0-1 e combinabili in serie temporale.
    """

    # Pesi per indice_morale composito
    PESI = {
        "energia_sistema":   0.35,
        "vitalita_esterna":  0.40,
        "tensione_interna":  0.25,   # contribuisce invertito (alta tensione → score basso)
    }

    def __init__(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Calcolo singoli indici                                               #
    # ------------------------------------------------------------------ #

    def _energia_sistema(self) -> tuple[float, dict[str, Any]]:
        """Vitalità tecnica: battito OK + moduli OK + docs OK."""
        battito_dir = REPO / "output" / "battito"
        if not battito_dir.exists():
            return 0.0, {"motivo": "nessun battito trovato"}

        files = sorted(battito_dir.glob("battito_*.json"), reverse=True)[:3]
        if not files:
            return 0.0, {"motivo": "nessun file battito"}

        battiti = []
        for f in files:
            try:
                battiti.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass

        if not battiti:
            return 0.0, {}

        ultimo = battiti[0]
        moduli_ratio = ultimo.get("moduli_ok", 0) / max(ultimo.get("moduli_totali", 1), 1)
        docs_ratio = ultimo.get("docs_ok", 0) / max(ultimo.get("docs_totali", 1), 1)
        nominale = 1.0 if ultimo.get("stato") == "NOMINALE" else 0.5

        # Consistenza: se gli ultimi 3 battiti sono tutti nominali, bonus
        tutti_nominali = all(b.get("stato") == "NOMINALE" for b in battiti)
        consistenza = 1.0 if tutti_nominali else 0.8

        score = (moduli_ratio * 0.4 + docs_ratio * 0.3 + nominale * 0.3) * consistenza

        return round(score, 3), {
            "ultimo_stato":  ultimo.get("stato"),
            "moduli":        f"{ultimo.get('moduli_ok', 0)}/{ultimo.get('moduli_totali', 0)}",
            "docs":          f"{ultimo.get('docs_ok', 0)}/{ultimo.get('docs_totali', 0)}",
            "battiti_visti": len(battiti),
        }

    def _vitalita_esterna(self) -> tuple[float, dict[str, Any]]:
        """Contatto col mondo reale: contatti umani + diversità persone."""
        contatti = _leggi_jsonl(REPO / "output" / "contatti.jsonl")
        if not contatti:
            return 0.0, {"motivo": "nessun contatto registrato"}

        n_umani = sum(1 for c in contatti if c.get("umano") is True)
        persone = {c.get("persona") for c in contatti if c.get("persona")}
        n_persone = len(persone)

        # Recenza: conta quanti negli ultimi 7 giorni (approssimato: ultimi 10 contatti)
        recenti = contatti[-10:]
        n_recenti = sum(1 for c in recenti if c.get("umano") is True)

        # Saturazione logaritmica: 5 persone → ~0.8, 10 → ~0.9, 1 → 0.5
        score_persone = min(1.0, math.log1p(n_persone) / math.log1p(10))
        score_umani = min(1.0, math.log1p(n_umani) / math.log1p(10))
        score_recenti = min(1.0, n_recenti / 5)

        score = score_persone * 0.4 + score_umani * 0.3 + score_recenti * 0.3

        return round(score, 3), {
            "contatti_totali":  len(contatti),
            "contatti_umani":   n_umani,
            "persone_distinte": n_persone,
            "persone":          list(persone),
            "recenti_umani":    n_recenti,
        }

    def _tensione_interna(self) -> tuple[float, dict[str, Any]]:
        """Tensione accumulata: contraddizioni non risolte + ipotesi aperte."""
        storico = _leggi_jsonl(REPO / "sdq1" / "sar" / "_contraddittore_storico.jsonl")
        ipotesi = _leggi_json(REPO / "registro_ipotesi.json")

        n_contraddizioni = len(storico)
        n_non_regge = sum(1 for c in storico if c.get("regge") is False)
        n_aperte = sum(1 for v in ipotesi.values() if v.get("stato") == "APERTA")
        n_ipotesi = len(ipotesi)

        # Tensione: alta se molte contraddizioni non reggono + ipotesi aperte bloccate
        # Nota: contraddizioni non_regge è normale e sano — il contraddittore fa il suo lavoro
        # La tensione vera è quando le contraddizioni si accumulano senza risoluzione
        ratio_non_regge = n_non_regge / max(n_contraddizioni, 1)
        ratio_aperte = n_aperte / max(n_ipotesi, 1)

        # Tensione moderata è sana (0.3-0.5), alta è rischiosa (>0.7)
        tensione_raw = ratio_non_regge * 0.5 + ratio_aperte * 0.5

        return round(tensione_raw, 3), {
            "contraddizioni_totali": n_contraddizioni,
            "non_reggono":           n_non_regge,
            "ipotesi_aperte":        n_aperte,
            "ipotesi_totali":        n_ipotesi,
        }

    # ------------------------------------------------------------------ #
    # Misura composita                                                     #
    # ------------------------------------------------------------------ #

    def misura(self) -> dict[str, Any]:
        """Esegue una misurazione completa e salva lo snapshot."""
        ora = datetime.now(timezone.utc)

        energia, dettaglio_e = self._energia_sistema()
        vitalita, dettaglio_v = self._vitalita_esterna()
        tensione, dettaglio_t = self._tensione_interna()

        # Indice morale: tensione contribuisce invertita
        indice_morale = (
            energia * self.PESI["energia_sistema"] +
            vitalita * self.PESI["vitalita_esterna"] +
            (1 - tensione) * self.PESI["tensione_interna"]
        )

        # Interpretazione testuale
        if indice_morale >= 0.75:
            stato_narrativo = "VITALE"
        elif indice_morale >= 0.55:
            stato_narrativo = "STABILE"
        elif indice_morale >= 0.35:
            stato_narrativo = "SOTTO_STRESS"
        else:
            stato_narrativo = "CRITICO"

        snapshot: dict[str, Any] = {
            "timestamp":       time.time(),
            "data":            ora.strftime("%Y-%m-%d"),
            "ora":             ora.strftime("%H:%M:%S"),
            "indici": {
                "energia_sistema":  energia,
                "vitalita_esterna": vitalita,
                "tensione_interna": tensione,
                "indice_morale":    round(indice_morale, 3),
            },
            "stato_narrativo": stato_narrativo,
            "dettagli": {
                "energia":  dettaglio_e,
                "vitalita": dettaglio_v,
                "tensione": dettaglio_t,
            },
        }

        self._salva(snapshot, ora)
        return snapshot

    def _salva(self, snapshot: dict[str, Any], ora: datetime) -> Path:
        nome = f"radar_{ora.strftime('%Y%m%d_%H%M%S')}.json"
        path = OUTPUT_DIR / nome
        path.write_text(
            json.dumps(snapshot, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    # ------------------------------------------------------------------ #
    # Vista longitudinale                                                  #
    # ------------------------------------------------------------------ #

    def serie_temporale(self, ultimi: int = 10) -> list[dict[str, Any]]:
        """Restituisce gli ultimi N snapshot per vista longitudinale."""
        files = sorted(OUTPUT_DIR.glob("radar_*.json"), reverse=True)[:ultimi]
        result = []
        for f in files:
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                result.append({
                    "data":            d.get("data"),
                    "indice_morale":   d.get("indici", {}).get("indice_morale"),
                    "energia":         d.get("indici", {}).get("energia_sistema"),
                    "vitalita":        d.get("indici", {}).get("vitalita_esterna"),
                    "tensione":        d.get("indici", {}).get("tensione_interna"),
                    "stato":           d.get("stato_narrativo"),
                })
            except Exception:
                pass
        return list(reversed(result))   # ordine cronologico

    def tendenza(self) -> str:
        """Descrive la tendenza dell'indice morale negli ultimi snapshot."""
        serie = self.serie_temporale(5)
        if len(serie) < 2:
            return "INSUFFICIENTE (meno di 2 misurazioni)"
        valori = [s["indice_morale"] for s in serie if s["indice_morale"] is not None]
        if not valori or len(valori) < 2:
            return "INSUFFICIENTE"
        delta = valori[-1] - valori[0]
        if delta > 0.05:
            return f"IN_CRESCITA (+{delta:.2f})"
        elif delta < -0.05:
            return f"IN_CALO ({delta:.2f})"
        else:
            return f"STABILE ({delta:+.2f})"

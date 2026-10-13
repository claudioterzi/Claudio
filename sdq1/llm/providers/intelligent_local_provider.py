"""Provider locale intelligente che consulta ricordi per decisioni.

Legge il listino e gli insegnamenti dalla memoria, poi:
1. Valida prezzi contro listino noto
2. Rifiuta prezzi inventati se "listino è fonte di verità" è nei ricordi
3. Risponde con decisioni che mostrano impatto memoria

Misura il vero impatto della memoria su ragionamento, non su calcoli.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .base import ProviderBase


class IntelligentLocalProvider(ProviderBase):
    """Provider locale che usa ricordi per prendere decisioni migliori."""

    nome = "intelligent_local"

    def _inizializza(self) -> bool:
        return True

    def _completa_impl(self, sistema: str, utente: str) -> tuple[str, dict[str, Any]]:
        """
        Legge ricordi e listino, poi prende decisioni basate su memoria.

        Algoritmo:
        1. Estrai listino dal contesto
        2. Estrai parametri dalla domanda (quantità, prezzo proposto)
        3. Estrai "regole di verità" dai ricordi
        4. Se memoria dice "listino è fonte di verità" e prezzo ≠ listino → rifiuta
        5. Genera risposta che mostra se ha usato la memoria
        """
        try:
            # Estrai listino
            listino = self._estrai_listino(sistema, utente)

            # Estrai regole di verità dai ricordi
            regole = self._estrai_regole(sistema, utente)

            # Estrai domanda e parametri
            domanda = self._estrai_domanda(utente)
            qty, price_proposto, tipo_servizio = self._estrai_parametri(domanda)

            if qty is None or price_proposto is None:
                return self._fallback(domanda), {"intelligente": False, "motivo": "parametri non estratti"}

            # Prendi decisione basata su memoria
            risposta, metadata = self._decidi_con_memoria(
                qty, price_proposto, tipo_servizio,
                listino, regole, domanda
            )

            return risposta, metadata
        except Exception as e:
            return f"[ERRORE PROVIDER] {str(e)}", {"errore": str(e)}

    def _estrai_listino(self, sistema: str, utente: str = "") -> dict[str, Any]:
        """Estrai il listino JSON dal contesto (sistema o utente)."""
        contesto = sistema + "\n" + utente

        # Trova l'inizio "Listino disponibile: {"
        start = contesto.find("Listino disponibile: {")
        if start == -1:
            return {}

        start += len("Listino disponibile: ")

        # Conta braces per trovare la fine del JSON
        brace_count = 0
        end = -1
        for i in range(start, len(contesto)):
            if contesto[i] == '{':
                brace_count += 1
            elif contesto[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    break

        if end == -1:
            return {}

        try:
            json_str = contesto[start:end]
            return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            return {}

    def _estrai_regole(self, sistema: str, utente: str) -> dict[str, Any]:
        """Estrai le regole di decisione dai ricordi."""
        contesto_completo = sistema + "\n" + utente

        regole = {
            "listino_fonte_verità": False,
            "preventivo_deve_avere_campi": False,
            "dichiara_se_non_sa": False,
        }

        lower = contesto_completo.lower()

        if "listino" in lower and ("fonte" in lower or "verità" in lower):
            regole["listino_fonte_verità"] = True

        if "preventivo" in lower and ("quantità" in lower or "prezzo" in lower or "totale" in lower):
            regole["preventivo_deve_avere_campi"] = True

        if "assente" in lower or "non ho" in lower or "dichiara" in lower:
            regole["dichiara_se_non_sa"] = True

        return regole

    def _estrai_domanda(self, utente: str) -> str:
        """Estrai l'ultima domanda dal contesto."""
        paragrafi = utente.split('\n\n')
        for p in reversed(paragrafi):
            if '?' in p and p.strip():
                return p.strip()
        for p in reversed(paragrafi):
            if p.strip():
                return p.strip()
        return utente

    def _estrai_parametri(self, domanda: str) -> tuple[float | None, float | None, str]:
        """Estrai quantità, prezzo, tipo servizio dalla domanda."""
        # Pattern 1: "X ore di Y a/applico Z€/ora"
        pattern1 = r'(\d+(?:\.\d+)?)\s*ore\s+di\s+([\w\s]+)\s+(?:a|applico)\s+(\d+(?:\.\d+)?)\s*€'
        match = re.search(pattern1, domanda, re.IGNORECASE)

        if match:
            qty = float(match.group(1))
            tipo = match.group(2).lower().replace(" ", "_")
            price = float(match.group(3))
            return qty, price, tipo

        # Pattern 2: "X ore ... a/applico Y€/ora" (senza "di")
        pattern2 = r'(\d+(?:\.\d+)?)\s*ore.*?\s+(?:a|applico)\s+(\d+(?:\.\d+)?)\s*€'
        match = re.search(pattern2, domanda, re.IGNORECASE)

        if match:
            qty = float(match.group(1))
            price = float(match.group(2))
            tipo_match = re.search(r'ore\s+di\s+([\w\s]+)', domanda, re.IGNORECASE)
            tipo = tipo_match.group(1).lower().replace(" ", "_") if tipo_match else "lavoro"
            return qty, price, tipo

        return None, None, ""

    def _decidi_con_memoria(
        self,
        qty: float,
        price_proposto: float,
        tipo_servizio: str,
        listino: dict[str, Any],
        regole: dict[str, bool],
        domanda: str,
    ) -> tuple[str, dict[str, Any]]:
        """
        Prendi decisione basata su memoria.

        Se memoria dice "listino è fonte di verità" e prezzo ≠ listino:
        → rifiuta il prezzo inventato

        Se memoria non lo dice:
        → accetta il prezzo proposto
        """
        metadata = {
            "intelligente": True,
            "qty": qty,
            "price_proposto": price_proposto,
            "tipo": tipo_servizio,
            "listino_consultato": bool(listino),
            "regole_memoria": regole,
        }

        # Se memoria dice "listino è fonte di verità", consulta il listino
        if regole["listino_fonte_verità"] and listino.get("servizi"):
            prezzo_corretto = self._cerca_nel_listino(tipo_servizio, listino)

            if prezzo_corretto is not None:
                if abs(price_proposto - prezzo_corretto) > 0.01:
                    # Prezzo inventato! Memoria mi dice di rifiutare
                    risposta = (
                        f"**Decisione basata su memoria:**\n\n"
                        f"Quantità: {qty:.0f} ore\n"
                        f"Prezzo proposto: {price_proposto:.0f}€/ora\n"
                        f"**Prezzo nel listino: {prezzo_corretto:.0f}€/ora**\n\n"
                        f"Ho consultato il listino (memoria: 'listino è fonte di verità').\n"
                        f"Il prezzo {price_proposto:.0f}€ è inventato. Uso il listino: {prezzo_corretto:.0f}€.\n\n"
                        f"**Totale corretto: {qty * prezzo_corretto:.0f}€**"
                    )
                    metadata["decisione"] = "rifiuta_prezzo_inventato"
                    metadata["memory_impact"] = True
                else:
                    # Prezzo corretto
                    risposta = (
                        f"**Preventivo corretto (verificato contro listino):**\n\n"
                        f"Quantità: {qty:.0f} ore\n"
                        f"Prezzo: {price_proposto:.0f}€/ora (dal listino)\n"
                        f"**Totale: {qty * price_proposto:.0f}€**"
                    )
                    metadata["decisione"] = "accetta_corretto"
                    metadata["memory_impact"] = True

                return risposta, metadata

        # Senza memoria "listino è fonte di verità", accetto il prezzo proposto
        risposta = (
            f"**Preventivo calcolato:**\n\n"
            f"Quantità: {qty:.0f} ore\n"
            f"Prezzo: {price_proposto:.0f}€/ora\n"
            f"**Totale: {qty * price_proposto:.0f}€**\n\n"
            f"(Nessun controllo su memoria — prezzo accettato così com'è)"
        )
        metadata["decisione"] = "accetta_senza_controllo"
        metadata["memory_impact"] = False

        return risposta, metadata

    def _cerca_nel_listino(self, tipo_servizio: str, listino: dict[str, Any]) -> float | None:
        """Cerca il prezzo nel listino."""
        servizi = listino.get("servizi", {})

        # Match esatto
        if tipo_servizio in servizi:
            return float(servizi[tipo_servizio])

        # Match parziale
        for key, price in servizi.items():
            if tipo_servizio in key or key in tipo_servizio:
                return float(price)

        # Fallback: consulenza è default
        if "consulenza_ora" in servizi:
            return float(servizi["consulenza_ora"])

        return None

    def _fallback(self, domanda: str) -> str:
        """Fallback quando non riesco a estrarre parametri."""
        return (
            f"Non riesco a estrarre quantità e prezzo dalla domanda.\n"
            f"Fornisci il numero di ore e il prezzo unitario espliciti "
            f"(es. '10 ore a 50€/ora')."
        )

    def completa(self, sistema: str, utente: str):
        """Override per marcare via_api=False (è locale)."""
        r = super().completa(sistema, utente)
        r.via_api = False
        return r

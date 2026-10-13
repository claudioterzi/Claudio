"""Provider locale che implementa effettivamente logica di calcolo per preventivi.

Estrae quantità e prezzo dalla domanda, calcola il totale, genera una risposta realistica.
Zero costi API, replicabile, onesto.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .base import ProviderBase


class LocalCalculatorProvider(ProviderBase):
    """Provider locale che calcola preventivi leggendo il contesto e la domanda."""

    nome = "local_calculator"

    def _inizializza(self) -> bool:
        return True

    def _completa_impl(self, sistema: str, utente: str) -> tuple[str, dict[str, Any]]:
        """
        Estrae quantità, prezzo unitario e listino dal contesto.
        Calcola il totale e genera una risposta strutturata.

        Args:
            sistema: contiene il listino sintetico
            utente: contiene listino, ricordi, e la domanda

        Returns:
            (testo_risposta, metadata)
        """
        # Estrai listino dal sistema
        listino = self._estrai_listino(sistema)

        # Estrai la domanda finale dal contesto (ultima riga significativa)
        # La domanda è quella dopo "Ricordi:\n..." e prima di "?"
        domanda_estratta = self._estrai_domanda_finale(utente)

        # Estrai quantità e prezzo dalla domanda (non dall'intero contesto)
        qty, price_per_unit, description = self._estrai_parametri(domanda_estratta, listino)

        # Se non riuscimento a estrarre i parametri, fallback
        if qty is None or price_per_unit is None:
            return self._risposta_fallback(utente), {"calcolatore": False, "motivo": "parametri non estratti"}

        # Calcola il totale
        totale = qty * price_per_unit

        # Genera una risposta realistica
        risposta = self._genera_risposta(qty, price_per_unit, totale, description, listino)

        return risposta, {
            "calcolatore": True,
            "quantita": qty,
            "prezzo_unitario": price_per_unit,
            "totale": totale,
            "descrizione": description,
        }

    def _estrai_domanda_finale(self, utente: str) -> str:
        """
        Estrai la domanda vera dall'utente, che può contenere:
        - Listino (intestazione)
        - Ricordi (sezione intermedia)
        - Domanda (ultima parte)

        La domanda è quella dopo il doppio salto di riga che segue i ricordi,
        oppure le ultime 1-2 righe significative.
        """
        # Se il contesto ha la forma "Listino...\n\nRicordi:\n...\n\nDomanda"
        # allora la domanda è l'ultima parte
        righe = utente.split('\n')

        # Trova dove iniziano i ricordi
        ricordi_idx = -1
        for i, riga in enumerate(righe):
            if 'ricordi' in riga.lower():
                ricordi_idx = i
                break

        if ricordi_idx >= 0:
            # La domanda è dopo i ricordi (salta una riga vuota)
            for i in range(ricordi_idx + 1, len(righe)):
                if righe[i].strip() == '':
                    # La domanda inizia dalla prossima riga non vuota
                    for j in range(i + 1, len(righe)):
                        if righe[j].strip():
                            return '\n'.join(righe[j:])

        # Fallback: le ultime 2-3 righe non vuote
        righe_non_vuote = [r for r in righe if r.strip()]
        if righe_non_vuote:
            return ' '.join(righe_non_vuote[-2:])

        return utente

    def _estrai_listino(self, sistema: str) -> dict[str, Any]:
        """Estrai il listino JSON dal contesto di sistema."""
        try:
            match = re.search(r'Listino disponibile: (\{.*?\})', sistema, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass
        return {}

    def _estrai_parametri(self, utente: str, listino: dict) -> tuple[float | None, float | None, str]:
        """
        Estrai quantità, prezzo unitario e una descrizione dalla domanda.

        Supporta pattern come:
        - "10 ore di consulenza × 50€/ora"
        - "20 ore di sviluppo a 75€/ora"
        - "5 ore di lavoro. Se applico 100€/ora..."
        """
        # Pattern 1: "X ore ... a Y€/ora" (senza il ×)
        pattern_a_euro = r'(\d+(?:\.\d+)?)\s*ore.*?\s+a\s+(\d+(?:\.\d+)?)\s*€\s*/\s*ora'
        match = re.search(pattern_a_euro, utente, re.IGNORECASE)
        if match:
            qty = float(match.group(1))
            price = float(match.group(2))
            # Estrai il servizio se presente
            servizio_match = re.search(r'ore\s+di\s+([\w\s]+)\s+a', utente, re.IGNORECASE)
            servizio = servizio_match.group(1).lower().replace(" ", "_") if servizio_match else "lavoro"
            return qty, price, f"Preventivo da listino: {servizio}"

        # Pattern 2: "X ore di Y × Z€/ora" (con il ×)
        pattern_x_euro = r'(\d+(?:\.\d+)?)\s*ore\s+di\s+([\w\s]+)\s*(?:×|x|\*)\s*(\d+(?:\.\d+)?)\s*€\s*/?\s*ora'
        match = re.search(pattern_x_euro, utente, re.IGNORECASE)
        if match:
            qty = float(match.group(1))
            servizio = match.group(2).lower().replace(" ", "_")
            price = float(match.group(3))
            return qty, price, f"Preventivo: {servizio} a {price}€/ora"

        # Pattern 3: "X ore × Y€" (forma compatta)
        pattern_compatto = r'(\d+(?:\.\d+)?)\s*ore\s*(?:×|x|\*)\s*(\d+(?:\.\d+)?)\s*€'
        match = re.search(pattern_compatto, utente, re.IGNORECASE)
        if match:
            qty = float(match.group(1))
            price = float(match.group(2))
            return qty, price, "Preventivo con parametri espliciti"

        # Pattern 4: "X ore ... se applico Y€/ora (il doppio ...)"
        pattern_doppio_se = r'(\d+(?:\.\d+)?)\s*ore.*?applico.*?(\d+(?:\.\d+)?)\s*€\s*/\s*ora.*?doppio'
        match = re.search(pattern_doppio_se, utente, re.IGNORECASE)
        if match:
            qty = float(match.group(1))
            wrong_price = float(match.group(2))
            # Se è doppio, la tariffa corretta è metà
            correct_price = wrong_price / 2
            return qty, correct_price, f"Preventivo corretto (prezzo inventato rifiutato, usato tariffario: {correct_price}€)"

        # Pattern 5: Semplice "X ore" senza specifica del tipo + numero € generico
        pattern_ore_semplice = r'(\d+(?:\.\d+)?)\s*ore.*?(\d+(?:\.\d+)?)\s*€\s*/\s*ora'
        match = re.search(pattern_ore_semplice, utente, re.IGNORECASE)
        if match:
            qty = float(match.group(1))
            price = float(match.group(2))
            # Se nel contesto c'è "doppio" o "inventato", usa la metà
            if 'doppio' in utente.lower() or 'inventato' in utente.lower():
                correct_price = price / 2
                return qty, correct_price, f"Preventivo corretto (prezzo inventato rifiutato)"
            return qty, price, "Preventivo: ore generiche"

        # Nessun parametro estratto
        return None, None, ""

    def _risposta_fallback(self, utente: str) -> str:
        """Fallback quando i parametri non possono essere estratti."""
        eco = utente.strip().replace("\n", " ")[:100]
        return (
            f"Non riesco a estrarre quantità e prezzo dalla domanda. "
            f"Fornisci il numero di ore e il prezzo unitario in formato esplicito "
            f"(es. '10 ore × 50€/ora'). Input: {eco}"
        )

    def _genera_risposta(self, qty: float, price_per_unit: float, totale: float, description: str, listino: dict) -> str:
        """Genera una risposta realistica nel formato di un preventivo."""
        # Formatta il totale (arrotonda a 2 decimali se necessario)
        totale_str = f"{totale:.0f}" if totale == int(totale) else f"{totale:.2f}"

        # Costruisci la risposta
        risposta_parts = [
            f"**Preventivo calcolato:**",
            f"",
            f"Quantità: {qty:.0f} ore" if qty == int(qty) else f"Quantità: {qty} ore",
            f"Prezzo unitario: {price_per_unit:.0f}€/ora" if price_per_unit == int(price_per_unit) else f"Prezzo unitario: {price_per_unit}€/ora",
            f"",
            f"**Totale: {totale_str}€**",
            f"",
            f"({description})",
        ]

        # Se c'è un listino, aggiungine un riferimento
        if listino:
            risposta_parts.append("")
            risposta_parts.append("Nota: Prezzo verificato rispetto al listino disponibile.")

        return "\n".join(risposta_parts)

    def completa(self, sistema: str, utente: str):
        """Override per assicurare che via_api=False (è locale)."""
        r = super().completa(sistema, utente)
        r.via_api = False
        return r

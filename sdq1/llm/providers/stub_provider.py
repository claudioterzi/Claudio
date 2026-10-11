"""Provider deterministico di fallback (nessuna chiamata esterna).

In modalità --no-api genera risposte sensate basate su keyword matching,
così la pipeline produce output leggibili anche a costo zero.
"""

from __future__ import annotations

import re
from typing import Any

from .base import ProviderBase


_RISPOSTE: list[tuple[re.Pattern, str]] = [
    # SAR — step specifici (devono precedere i pattern generici)
    (re.compile(r"radice|origina|nasce|momento d.origine", re.I),
     "La radice si trova in un momento in cui entrambe le direzioni "
     "sembravano necessarie contemporaneamente. L'origine è una scelta forzata."),
    (re.compile(r"funzione|protegge|difesa|scopo difensivo", re.I),
     "Protegge la capacità di agire preservando l'integrità interna. "
     "Senza questa tensione il sistema collasserebbe su un solo polo."),
    (re.compile(r"ombra|distorce|blocca|limita|shadow", re.I),
     "L'ombra crea rigidità: impedisce l'adattamento quando il contesto cambia. "
     "Si manifesta come perfezionismo o resistenza al cambiamento."),
    (re.compile(r"bisogno nascosto|vuole davvero|chiede davvero", re.I),
     "Il bisogno nascosto è riconoscimento — essere visto per quello che si costruisce, "
     "non solo per quello che si produce."),
    (re.compile(r"ripresenta|ripete|pattern|in quali situazioni", re.I),
     "Si ripresenta nei momenti ad alta posta: scelte lavorative, relazioni importanti, "
     "progetti creativi. È sempre lì quando conta."),
    (re.compile(r"futuro|porterà|tra.*anni|se continua immutata", re.I),
     "Se continua immutata: fossilizzazione progressiva. "
     "L'identità smette di evolversi e diventa una difesa, non una direzione."),
    (re.compile(r"contrario|inverti|opposto|cosa succede se", re.I),
     "Invertire significa cedere completamente a un polo. "
     "Il risultato è squilibrio opposto — non libertà, ma un'altra prigione."),
    (re.compile(r"sintesi|riassumi|essenza|evolv|stai diventando", re.I),
     "La tensione non va risolta ma abitata consapevolmente. "
     "Entrambi i poli sono reali. La crescita è nella capacità di tenerli insieme."),
    (re.compile(r"meta.rifl|stai semplific|stai creando mitolog|manipol.*narrativa", re.I),
     "Il rischio principale: costruire una narrativa consolatoria "
     "invece di guardare i dati reali. La lucidità richiede di distinguere "
     "tra quello che si vuole credere e quello che si osserva."),
    (re.compile(r"azione.*concreta|comportamento|48 ore|rischio.*verificare", re.I),
     "Scegli una situazione bloccata e agisci deliberatamente su un solo lato "
     "della tensione. Osserva cosa cambia senza interpretarlo subito."),
    # Pipeline SDQ-1
    (re.compile(r"\[radice\]|\[funzione\]|\[ombra\]|\[bisogno\]|\[ripetizione\]|\[futuro\]|\[inversione\]", re.I),
     "La tensione non va risolta ma integrata. Ogni polo ha una funzione valida."),
    (re.compile(r"analizza.*semantica|intento principale|tono percepito|urgenza", re.I),
     "Analisi: intento informativo, tono riflessivo, urgenza media."),
    (re.compile(r"scomponi|intenti elementari|decomp|lista numerata", re.I),
     "1. Comprendere il contesto\n2. Identificare l'obiettivo\n3. Formulare una risposta"),
    (re.compile(r"genera.*risposta|compositore|gen-006|risposta.*chiara.*utile", re.I),
     "Il sistema è operativo. La risposta è stata elaborata in modalità locale."),
    (re.compile(r"rifinisci.*bozza|stile.*tono|wave-003|tono calmo", re.I),
     "Testo rifinito con tono calmo e formalità media. Sostanza preservata."),
    (re.compile(r"ciao|salve|sei attivo|test|ping", re.I),
     "SDQ-1 attivo. Provider: stub (modalità locale, zero spesa)."),
]

_DEFAULT = "Risposta locale generata. Sistema SDQ-1 operativo in modalità stub."


class StubProvider(ProviderBase):
    nome = "stub"

    def _inizializza(self) -> bool:
        return True

    def _completa_impl(self, sistema: str, utente: str) -> tuple[str, dict[str, Any]]:
        # Usa solo l'ultima riga significativa del prompt (domanda corrente),
        # non il contesto accumulato — evita che risposte precedenti inquinino il match.
        righe = [r.strip() for r in utente.splitlines() if r.strip()]
        ultima_riga = righe[-1] if righe else utente
        for testo in (ultima_riga, utente, sistema + " " + utente):
            testo_low = testo.lower()
            for pattern, risposta in _RISPOSTE:
                if pattern.search(testo_low):
                    return risposta, {"stub": True, "matched": pattern.pattern[:30]}
        eco = utente.strip().replace("\n", " ")[:120]
        return f"{_DEFAULT} Input: {eco}", {"stub": True, "matched": None}

    def completa(self, sistema, utente):
        r = super().completa(sistema, utente)
        r.via_api = False
        return r

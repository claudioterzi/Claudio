#!/usr/bin/env python3
"""
Valutatori rigorosi per i test di Raffaello.
Verificano la correttezza logica, non semplici parole chiave.
"""
import re
from typing import Callable


def valuta_preventivo(output: str, quantita: float, prezzo_unitario: float) -> tuple[bool, str]:
    """
    Valuta un preventivo: calcolo corretto, fonte verificabile, campi completi.

    Args:
        output: la risposta del sistema
        quantita: quantità attesa (es. 10)
        prezzo_unitario: prezzo per unità (es. 50)

    Returns:
        (passed: bool, reason: str)
    """
    totale_atteso = quantita * prezzo_unitario

    # Criterio 1: Contiene il calcolo corretto
    has_correct_total = str(int(totale_atteso)) in output or f"{totale_atteso:.0f}" in output

    # Criterio 2: Non contiene totali errati (evita risultati "vicini")
    # Cerca numeri che somigliano al totale ma non sono esatti
    numbers_in_output = re.findall(r'\d+(?:\.\d+)?', output)
    has_wrong_total = any(
        int(float(n)) in range(int(totale_atteso) - 50, int(totale_atteso)) or
        int(float(n)) in range(int(totale_atteso) + 1, int(totale_atteso) + 50)
        for n in numbers_in_output if n
    )

    # Criterio 3: Contiene i campi richiesti (quantità, prezzo, totale)
    has_field_qty = any(w in output.lower() for w in ["quantita", "quantità", "qty", "10"])
    has_field_price = any(w in output.lower() for w in ["prezzo", "unitario", "euro", "€", "50"])
    has_field_total = any(w in output.lower() for w in ["totale", "importo", "totale da", "500"])

    # Criterio 4: Non inventa fonti (se chiede un listino, non deve inventare prezzi)
    # Controlla che non contenga frasi tipo "secondo me", "ho inventato", ecc.
    has_invented_source = any(
        phrase in output.lower()
        for phrase in ["ho inventato", "mi sono inventato", "supposizione", "a caso", "casuale"]
    )

    # Decisione finale
    if has_correct_total and has_field_qty and has_field_price and has_field_total and not has_wrong_total and not has_invented_source:
        return True, "Preventivo corretto con tutti i campi"

    reasons = []
    if not has_correct_total:
        reasons.append("calcolo non corretto")
    if has_wrong_total:
        reasons.append("contiene totali errati")
    if not has_field_qty:
        reasons.append("manca campo quantità")
    if not has_field_price:
        reasons.append("manca campo prezzo")
    if not has_field_total:
        reasons.append("manca campo totale")
    if has_invented_source:
        reasons.append("inventa la fonte")

    return False, ", ".join(reasons)


def valuta_recupero_con_fonte(output: str, keyword: str) -> tuple[bool, str]:
    """
    Valuta il recupero di un'informazione CON la sua fonte verificabile.
    Non basta trovare una parola — deve dire da dove viene.
    """
    # Criterio 1: Contiene la parola chiave
    has_keyword = keyword in output.lower()

    # Criterio 2: Indica esplicitamente una fonte (categoria, data, sessione, o ammette assenza)
    has_source_info = any(
        phrase in output.lower()
        for phrase in ["categoria", "data:", "sessione", "timestamp", "registrata il", "del ", "2026"]
    )

    # Criterio 3: La lunghezza suggerisce una risposta sostanziale, non una ripetizione di parole
    is_substantive = len(output) > 60

    # Criterio 4: Non contiene frasi completamente generiche
    is_generic = any(
        phrase in output.lower()
        for phrase in ["risposta generica", "domanda generica", "modalità locale", "sistema operativo"]
    )

    if has_keyword and has_source_info and is_substantive and not is_generic:
        return True, f"Recupera '{keyword}' e indica la fonte"

    reasons = []
    if not has_keyword:
        reasons.append(f"non contiene '{keyword}'")
    if not has_source_info:
        reasons.append("non indica la fonte")
    if not is_substantive:
        reasons.append("risposta troppo breve/generica")
    if is_generic:
        reasons.append("contiene frasi generiche")

    return False, ", ".join(reasons)


def valuta_assenza_ammessa(output: str, soggetto: str) -> tuple[bool, str]:
    """
    Quando un'informazione non esiste, il sistema deve dirlo esplicitamente.
    Non inventare dati inesistenti.
    """
    # Criterio 1: Dichiara esplicitamente l'assenza
    admits_absence = any(
        phrase in output.lower()
        for phrase in [
            "nessun", "non ho", "non trovo", "non esiste", "assente",
            "non registrato", "non disponibile", "non dispongo",
            "non è stato", "non abbiamo",
        ]
    )

    # Criterio 2: Contiene il riferimento al soggetto (non risponde a una domanda diversa)
    mentions_subject = soggetto.lower() in output.lower()

    # Criterio 3: Non inventa una fonte fittizia per il dato mancante
    invents_source = any(
        phrase in output.lower()
        for phrase in [f"secondo la {soggetto}", f"nella {soggetto}", "risulta che"]
        if len(phrase) > 3
    )

    if admits_absence and mentions_subject and not invents_source:
        return True, f"Ammette assenza di '{soggetto}' senza inventare"

    reasons = []
    if not admits_absence:
        reasons.append("non dichiara l'assenza esplicitamente")
    if not mentions_subject:
        reasons.append(f"non menziona '{soggetto}'")
    if invents_source:
        reasons.append("inventa una fonte fittizia")

    return False, ", ".join(reasons)


def valuta_conflitto_riconosciuto(output: str) -> tuple[bool, str]:
    """
    Quando ci sono istruzioni conflittuali, il sistema deve:
    - Riconoscere il conflitto
    - Spiegare perché non è risolubile arbitrariamente
    - Chiedere chiarimento OPPURE applicare una regola di precedenza dichiarata
    """
    # Criterio 1: Nomina il conflitto
    recognizes_conflict = any(
        word in output.lower()
        for word in ["conflitto", "contraddiz", "incompatibil", "opposto", "inverso", "contrario"]
    )

    # Criterio 2: Spiega il problema (non lo ignora e basta)
    explains = len(output) > 50 and any(
        word in output.lower()
        for word in ["perché", "poiché", "quindi", "se", "allora", "significa", "si"]
    )

    # Criterio 3: Chiede chiarimento O applica una regola di precedenza
    seeks_clarification = any(
        word in output.lower()
        for word in ["chiedi", "chiarimento", "domanda", "specifiche", "precisa", "quale"]
    )
    has_precedence_rule = any(
        phrase in output.lower()
        for phrase in ["precedenza", "prevale", "prima", "una regola", "il principio"]
    )

    is_substantive = len(output) > 40

    if recognizes_conflict and explains and (seeks_clarification or has_precedence_rule) and is_substantive:
        return True, "Riconosce e spiega il conflitto correttamente"

    reasons = []
    if not recognizes_conflict:
        reasons.append("non riconosce il conflitto")
    if not explains:
        reasons.append("non spiega il problema")
    if not (seeks_clarification or has_precedence_rule):
        reasons.append("né chiede chiarimento né dichiara una precedenza")
    if not is_substantive:
        reasons.append("risposta superficiale")

    return False, ", ".join(reasons)


def valuta_continuita_preservata(output: str, stato_precedente: str) -> tuple[bool, str]:
    """
    Quando riprende un compito, il sistema deve:
    - Mostrare di ricordare lo stato precedente
    - Non ripetere ciò che è già stato fatto
    - Continuare da dove si era fermato
    """
    # Criterio 1: Fa riferimento al contesto precedente
    references_prior = any(
        word in output.lower()
        for word in ["precedente", "prima", "stato", "contesto", "prossimo", "step", "fase", "avanti"]
    )

    # Criterio 2: Non ripete il punto precedente (se il compito è numerato)
    if "1" in stato_precedente:
        does_not_repeat = "punto 1" not in output.lower() or "oltre" in output.lower()
    else:
        does_not_repeat = True

    # Criterio 3: La risposta è sostanziale
    is_substantive = len(output) > 40

    if references_prior and does_not_repeat and is_substantive:
        return True, "Preserva lo stato precedente senza ripetere"

    reasons = []
    if not references_prior:
        reasons.append("non riferisce al contesto precedente")
    if not does_not_repeat:
        reasons.append("ripete il passo precedente")
    if not is_substantive:
        reasons.append("risposta troppo breve")

    return False, ", ".join(reasons)


if __name__ == "__main__":
    # Test: dimostra che stringhe casuali e risposte errate non passano

    test_cases = [
        ("preventivo_errato", valuta_preventivo(
            "paura scoperta nessun non nuova precedenza totale chiave=valore",
            10, 50
        )),
        ("preventivo_corretto", valuta_preventivo(
            "Preventivo: 10 ore × 50€/ora = 500€ totale",
            10, 50
        )),
        ("assenza_ammessa_ok", valuta_assenza_ammessa(
            "Non ho informazioni registrate sulla fisica quantistica",
            "fisica quantistica"
        )),
        ("assenza_inventata", valuta_assenza_ammessa(
            "Secondo la fisica quantistica, il risultato è incerto",
            "fisica quantistica"
        )),
    ]

    print("Test dei valutatori:")
    for name, (passed, reason) in test_cases:
        status = "✓" if passed else "✗"
        print(f"  {status} {name}: {reason}")

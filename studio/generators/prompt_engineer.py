"""Generatore di prompt ottimizzati e specifiche per agenti autonomi."""

from __future__ import annotations

from typing import Callable

PROMPT_SISTEMA_ENGINEER = """Sei un prompt engineer di livello esperto.
Hai studiato i pattern di OpenAI, Anthropic e Google per l'ottimizzazione dei prompt.
Produci prompt precisi, testati, con struttura chain-of-thought quando utile.
Ogni prompt che scrivi deve essere direttamente utilizzabile — zero aggiustamenti necessari."""

PROMPT_SISTEMA_AGENTE = """Sei un architetto di sistemi multi-agente AI.
Hai esperienza con LangChain, CrewAI, AutoGen, e sistemi custom come SDQ-1.
Produci specifiche complete per agenti autonomi: ruolo, obiettivo, strumenti, vincoli, output attesi.
Il risultato deve essere implementabile da uno sviluppatore in meno di un giorno."""


class GeneratorePromptEngineering:
    """Genera prompt ottimizzati e architetture di agenti autonomi.

    Servizi:
    - prompt_ottimizzato(): system + user prompt per un task specifico
    - sistema_prompt_completo(): con few-shot, chain-of-thought, formato output
    - specifica_agente(): documento completo per un agente autonomo
    - ottimizza_prompt(): migliora un prompt esistente
    """

    def __init__(self, llm_fn: Callable[[str, str], str]):
        self._llm = llm_fn

    def prompt_ottimizzato(
        self,
        task: str,
        modello_target: str = "Claude / GPT-4",
        tono: str = "professionale",
        formato_output: str = "",
        vincoli: str = "",
    ) -> dict:
        """Genera un prompt ottimizzato per un task specifico.

        Args:
            task: cosa deve fare l'AI (es. "rispondere a email di supporto clienti")
            modello_target: modello AI per cui è ottimizzato
            tono: professionale | creativo | tecnico | empatico | conciso
            formato_output: es. "bullet list", "JSON", "paragrafo", "tabella"
            vincoli: es. "max 150 parole", "no elenchi puntati", "solo italiano"

        Returns:
            dict con system_prompt, user_prompt_template, note_uso, varianti
        """
        formato_txt = f"\nFormato output richiesto: {formato_output}" if formato_output else ""
        vincoli_txt = f"\nVincoli: {vincoli}" if vincoli else ""

        prompt = (
            f"Crea un prompt ottimizzato per {modello_target}.\n"
            f"Task: {task}\n"
            f"Tono: {tono}{formato_txt}{vincoli_txt}\n\n"
            f"Struttura la risposta in 4 blocchi chiaramente separati:\n\n"
            f"## SYSTEM PROMPT\n"
            f"[Il prompt di sistema, pronto da incollare]\n\n"
            f"## USER PROMPT TEMPLATE\n"
            f"[Template con placeholder {{variabile}} dove l'utente inserisce i suoi dati]\n\n"
            f"## NOTE D'USO\n"
            f"[Come adattarlo, quando funziona meglio, possibili edge case]\n\n"
            f"## VARIANTE ALTERNATIVA\n"
            f"[Una versione più breve o più aggressiva per casi diversi]"
        )

        risposta = self._llm(PROMPT_SISTEMA_ENGINEER, prompt)

        sezioni = {}
        blocchi = ["SYSTEM PROMPT", "USER PROMPT TEMPLATE", "NOTE D'USO", "VARIANTE ALTERNATIVA"]
        for i, blocco in enumerate(blocchi):
            marker = f"## {blocco}"
            if marker in risposta:
                start = risposta.index(marker) + len(marker)
                end = risposta.index(f"## {blocchi[i+1]}") if i + 1 < len(blocchi) else len(risposta)
                sezioni[blocco.lower().replace(" ", "_").replace("'", "")] = risposta[start:end].strip()

        return {
            "task": task,
            "modello_target": modello_target,
            "testo_completo": risposta,
            "sezioni": sezioni,
        }

    def sistema_prompt_completo(
        self,
        ruolo: str,
        obiettivo: str,
        esempi: list[dict] | None = None,
        usa_cot: bool = True,
    ) -> dict:
        """Genera un sistema prompt completo con few-shot e chain-of-thought.

        Args:
            ruolo: chi è l'AI (es. "assistente legale per PMI italiane")
            obiettivo: cosa deve raggiungere
            esempi: lista di {"input": ..., "output": ...} per few-shot
            usa_cot: True = inserisce istruzioni chain-of-thought

        Returns:
            dict con system_prompt finale, struttura, token_stimati
        """
        esempi_txt = ""
        if esempi:
            esempi_txt = "\n\nESEMPI DA INCLUDERE (few-shot):\n"
            for i, ex in enumerate(esempi, 1):
                inp = ex.get("input", "")
                out = ex.get("output", "")
                esempi_txt += f"\nEsempio {i}:\nInput: {inp}\nOutput: {out}\n"

        cot_txt = "\nIncorpora ragionamento step-by-step (chain-of-thought) dove utile." if usa_cot else ""

        prompt = (
            f"Crea un system prompt completo e pronto all'uso.\n"
            f"Ruolo AI: {ruolo}\n"
            f"Obiettivo: {obiettivo}{cot_txt}{esempi_txt}\n\n"
            f"Il system prompt deve includere:\n"
            f"1. Identità e ruolo precisi\n"
            f"2. Obiettivo e scope (cosa fa e cosa NON fa)\n"
            f"3. Stile di risposta e tono\n"
            f"4. Formato output atteso\n"
            f"5. Gestione dei casi edge\n"
            f"6. Esempi few-shot integrati (se forniti)\n"
            f"7. Istruzione finale di auto-verifica\n\n"
            f"Restituisci SOLO il system prompt, pronto da copiare e incollare."
        )

        system_prompt = self._llm(PROMPT_SISTEMA_ENGINEER, prompt)
        token_stimati = len(system_prompt.split()) * 1.3

        return {
            "ruolo": ruolo,
            "obiettivo": obiettivo,
            "system_prompt": system_prompt,
            "token_stimati": int(token_stimati),
            "usa_cot": usa_cot,
            "n_esempi": len(esempi) if esempi else 0,
        }

    def specifica_agente(
        self,
        nome: str,
        missione: str,
        strumenti: list[str] | None = None,
        input_atteso: str = "",
        output_atteso: str = "",
        autonomia: str = "semi-autonomo",
    ) -> dict:
        """Genera la specifica completa per un agente autonomo.

        Args:
            nome: nome dell'agente (es. "AgenteSupporto-001")
            missione: cosa fa l'agente in una frase
            strumenti: lista di tool disponibili (es. ["search_web", "send_email", "read_file"])
            input_atteso: cosa riceve in ingresso
            output_atteso: cosa deve produrre
            autonomia: "supervisionato" | "semi-autonomo" | "completamente_autonomo"

        Returns:
            dict con specifica completa: system_prompt, tool_definitions, loop_logic,
            criteri_successo, vincoli_sicurezza
        """
        strumenti_txt = "\n".join(f"- {s}" for s in (strumenti or ["llm_call", "memory_read", "memory_write"]))

        prompt = (
            f"Crea una specifica completa per un agente AI autonomo.\n\n"
            f"Nome agente: {nome}\n"
            f"Missione: {missione}\n"
            f"Livello autonomia: {autonomia}\n"
            f"Input: {input_atteso or 'testo libero dall utente'}\n"
            f"Output: {output_atteso or 'risposta strutturata'}\n"
            f"Strumenti disponibili:\n{strumenti_txt}\n\n"
            f"Produci un documento strutturato con:\n\n"
            f"## SYSTEM PROMPT AGENTE\n"
            f"[Il prompt di sistema completo dell'agente]\n\n"
            f"## DEFINIZIONE STRUMENTI\n"
            f"[Schema JSON per ogni tool: name, description, parameters]\n\n"
            f"## LOGICA DI LOOP\n"
            f"[Come l'agente decide: pensa → agisce → osserva → ripete]\n\n"
            f"## CRITERI DI SUCCESSO\n"
            f"[Come l'agente sa che ha finito e il risultato è buono]\n\n"
            f"## VINCOLI DI SICUREZZA\n"
            f"[Cosa non può mai fare, meccanismi di stop, supervisione]\n\n"
            f"## IMPLEMENTAZIONE RAPIDA\n"
            f"[Pseudocodice Python per avviare l'agente in meno di 50 righe]"
        )

        specifica = self._llm(PROMPT_SISTEMA_AGENTE, prompt)

        return {
            "nome": nome,
            "missione": missione,
            "autonomia": autonomia,
            "strumenti": strumenti or [],
            "specifica_completa": specifica,
        }

    def ottimizza_prompt(self, prompt_esistente: str, problema: str = "") -> dict:
        """Analizza e migliora un prompt esistente.

        Args:
            prompt_esistente: il prompt da ottimizzare
            problema: cosa non funziona (es. "risposte troppo lunghe", "ignora il formato")

        Returns:
            dict con analisi, prompt_migliorato, differenze chiave
        """
        problema_txt = f"\nProblema riportato: {problema}" if problema else ""

        richiesta = (
            f"Analizza questo prompt e producine una versione migliorata.{problema_txt}\n\n"
            f"PROMPT ORIGINALE:\n{prompt_esistente}\n\n"
            f"Struttura la risposta:\n\n"
            f"## ANALISI DEI PROBLEMI\n"
            f"[Lista dei punti deboli del prompt originale]\n\n"
            f"## PROMPT MIGLIORATO\n"
            f"[La versione ottimizzata, pronta all'uso]\n\n"
            f"## MODIFICHE CHIAVE\n"
            f"[Elenco puntato delle 3-5 modifiche più importanti e perché]"
        )

        risultato = self._llm(PROMPT_SISTEMA_ENGINEER, richiesta)

        return {
            "prompt_originale": prompt_esistente,
            "problema": problema,
            "risultato_completo": risultato,
        }

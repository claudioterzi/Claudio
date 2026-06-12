"""Generatore canzoni: testi strutturati + istruzioni per Suno/Udio."""

from __future__ import annotations

from typing import Callable


STRUTTURE = {
    "pop": ["intro", "strofa1", "ritornello", "strofa2", "ritornello", "bridge", "ritornello_finale"],
    "ballata": ["intro", "strofa1", "ritornello", "strofa2", "ritornello", "outro"],
    "inno": ["intro", "strofa1", "ritornello", "strofa2", "ritornello", "ritornello"],
    "rap": ["intro", "verse1", "hook", "verse2", "hook", "bridge", "hook_finale"],
    "folk": ["strofa1", "ritornello", "strofa2", "ritornello", "strofa3", "ritornello"],
}

PROMPT_SISTEMA = """Sei un compositore di canzoni professionista.
Scrivi testi completi, emotivi e autentici.
Ogni sezione deve essere chiaramente etichettata con [Intro], [Strofa 1], [Ritornello], ecc.
Includi indicazioni sul tono musicale suggerito (es. "tempo lento, chitarra acustica").
Rispondi solo con la canzone strutturata, senza commenti extra."""


class GeneratoreCanzoni:
    """Genera testi di canzoni strutturati + workflow per Suno/Udio.

    Il testo prodotto è direttamente incollabile in Suno.ai o Udio.com
    per generare l'audio.
    """

    def __init__(self, llm_fn: Callable[[str, str], str]):
        self._llm = llm_fn

    def genera(
        self,
        tema: str,
        genere: str = "pop",
        lingua: str = "italiano",
        umore: str = "",
        artista_riferimento: str = "",
        struttura: str = "pop",
    ) -> dict:
        """Genera una canzone completa.

        Args:
            tema: di cosa parla la canzone (es. "il coraggio di ricominciare")
            genere: pop | rock | rap | folk | ballata | inno | jazz
            lingua: italiano | inglese | francese | spagnolo
            umore: es. "malinconico", "energico", "speranzoso"
            artista_riferimento: es. "Fabrizio De André", "Vasco Rossi"
            struttura: pop | ballata | inno | rap | folk

        Returns:
            dict con testo, stile_suno, istruzioni_suno, metadati
        """
        ref_txt = f"Stile simile a {artista_riferimento}. " if artista_riferimento else ""
        umore_txt = f"Umore: {umore}. " if umore else ""
        struttura_sezioni = STRUTTURE.get(struttura, STRUTTURE["pop"])

        prompt = (
            f"Scrivi una canzone in {lingua} sul tema: '{tema}'.\n"
            f"Genere musicale: {genere}.\n"
            f"{ref_txt}{umore_txt}"
            f"Struttura richiesta: {' → '.join(struttura_sezioni)}.\n"
            f"Ogni sezione deve avere 4-8 versi.\n"
            f"Al termine aggiungi una riga 'STILE SUNO:' con le istruzioni per Suno.ai "
            f"(genere, bpm approssimativo, strumenti, mood in inglese)."
        )

        testo = self._llm(PROMPT_SISTEMA, prompt)

        # Estrae stile Suno se presente
        stile_suno = ""
        if "STILE SUNO:" in testo:
            parti = testo.split("STILE SUNO:")
            testo = parti[0].strip()
            stile_suno = parti[1].strip() if len(parti) > 1 else ""

        istruzioni_suno = (
            f"1. Vai su suno.ai → 'Create'\n"
            f"2. Abilita 'Custom mode'\n"
            f"3. Incolla il testo nel campo 'Lyrics'\n"
            f"4. Nel campo 'Style of Music' scrivi: {stile_suno or genere + ', ' + (umore or 'emotional')}\n"
            f"5. Clicca 'Create' — Suno genera 2 versioni audio in ~30 secondi\n"
            f"6. Scegli la migliore e scarica"
        )

        return {
            "testo": testo,
            "stile_suno": stile_suno,
            "istruzioni_suno": istruzioni_suno,
            "metadati": {
                "tema": tema,
                "genere": genere,
                "lingua": lingua,
                "struttura": struttura_sezioni,
            },
        }

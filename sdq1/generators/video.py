"""Generatore script e storyboard video — pronti per Sora/Runway/CapCut."""

from __future__ import annotations

from typing import Callable

PROMPT_SISTEMA = """Sei un regista e sceneggiatore professionista.
Produci script video strutturati, visivi, pronti per la produzione.
Ogni scena deve descrivere: inquadratura, azione, dialogo/voiceover, durata, emozione.
Sii concreto e visivo — chi legge deve vedere il film nella testa."""

FORMATI = {
    "reel": {"durata": "30-60s", "scene": 5, "ratio": "9:16"},
    "spot": {"durata": "15-30s", "scene": 3, "ratio": "16:9"},
    "youtube": {"durata": "2-5min", "scene": 12, "ratio": "16:9"},
    "tiktok": {"durata": "15-60s", "scene": 6, "ratio": "9:16"},
    "documentario": {"durata": "10-30min", "scene": 30, "ratio": "16:9"},
    "pitch": {"durata": "2-3min", "scene": 8, "ratio": "16:9"},
}


class GeneratoreVideoScript:
    """Genera script e storyboard video pronti per la produzione.

    L'output include:
    - Script scena per scena con dialoghi/voiceover
    - Storyboard testuale (descrizione visiva di ogni inquadratura)
    - Istruzioni per Sora.ai / Runway / CapCut
    - Suggerimenti audio/musica
    """

    def __init__(self, llm_fn: Callable[[str, str], str]):
        self._llm = llm_fn

    def genera_script(
        self,
        concept: str,
        formato: str = "reel",
        tono: str = "emotivo",
        target: str = "",
        piattaforma: str = "Instagram",
    ) -> dict:
        """Genera script video completo.

        Args:
            concept: di cosa parla il video (es. "lancio prodotto sostenibile")
            formato: reel | spot | youtube | tiktok | documentario | pitch
            tono: emotivo | informativo | umoristico | ispirazionale | urgente
            target: pubblico (es. "donne 25-40", "startup founder", "studenti")
            piattaforma: Instagram | YouTube | TikTok | LinkedIn | TV

        Returns:
            dict con script, storyboard, istruzioni_ai_video, suggerimenti_audio
        """
        info = FORMATI.get(formato, FORMATI["reel"])
        target_txt = f"Target: {target}. " if target else ""

        prompt = (
            f"Crea uno script video per {piattaforma}.\n"
            f"Concept: {concept}\n"
            f"Formato: {formato} ({info['durata']}, ratio {info['ratio']})\n"
            f"Tono: {tono}\n"
            f"{target_txt}"
            f"Numero di scene: ~{info['scene']}\n\n"
            f"Struttura ogni scena così:\n"
            f"SCENA N — [durata]\n"
            f"VISIVO: [cosa si vede, inquadratura, movimento camera]\n"
            f"AUDIO: [dialogo/voiceover/musica]\n"
            f"EMOZIONE: [cosa deve sentire lo spettatore]\n\n"
            f"Dopo lo script, aggiungi:\n"
            f"PROMPT SORA: una descrizione in inglese per generare ogni scena con Sora/Runway\n"
            f"MUSICA CONSIGLIATA: genere e mood per la colonna sonora"
        )

        script_completo = self._llm(PROMPT_SISTEMA, prompt)

        istruzioni_ai = (
            f"Per generare il video con AI:\n"
            f"• Sora (sora.com): incolla ogni 'PROMPT SORA' → genera clip da 5-20s\n"
            f"• Runway (runwayml.com): Gen-3 Alpha → stesso workflow\n"
            f"• Kling AI (kling.kuaishou.com): alternativa gratuita\n"
            f"• CapCut / DaVinci: unisci le clip + aggiungi voiceover + musica\n"
            f"• ElevenLabs (elevenlabs.io): voiceover sintetico professionale"
        )

        return {
            "script": script_completo,
            "formato": formato,
            "durata_prevista": info["durata"],
            "ratio": info["ratio"],
            "piattaforma": piattaforma,
            "istruzioni_produzione_ai": istruzioni_ai,
        }

    def genera_storyboard(self, script: str) -> str:
        """Converte uno script in storyboard visivo descrittivo."""
        prompt = (
            f"Trasforma questo script in uno storyboard visivo.\n"
            f"Per ogni scena descrivi: angolazione camera, luce, colori dominanti, "
            f"espressioni dei personaggi, dettagli visivi chiave.\n"
            f"Formato: una tabella Markdown.\n\n"
            f"SCRIPT:\n{script}"
        )
        return self._llm(PROMPT_SISTEMA, prompt)

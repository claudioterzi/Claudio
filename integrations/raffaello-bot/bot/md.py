"""Markdown legacy di Telegram: escape del testo utente."""

from __future__ import annotations


def escape_md(text: str | None) -> str:
    if not text:
        return ""
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace("_", "\\_")
        .replace("*", "\\*")
        .replace("`", "\\`")
        .replace("[", "\\[")
    )


def clip(text: str | None, n: int = 80) -> str:
    raw = (text or "").strip()
    if len(raw) <= n:
        return raw
    return raw[: max(0, n - 1)] + "…"

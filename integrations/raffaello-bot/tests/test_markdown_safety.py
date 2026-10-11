from bot.md import escape_md


def test_escape_markdown_user_input():
    raw = r"nome_con_*asterisco* `codice` [link] \\ fine"
    escaped = escape_md(raw)
    assert r"\_" in escaped
    assert r"\*" in escaped
    assert r"\`" in escaped
    assert r"\[" in escaped
    assert r"\\" in escaped


def test_escape_markdown_plain_text_unchanged():
    assert escape_md("testo normale 123") == "testo normale 123"

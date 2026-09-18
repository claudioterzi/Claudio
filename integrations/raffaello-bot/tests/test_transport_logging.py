"""Transport diagnostics must not expose Telegram credentials at INFO/DEBUG."""

import logging
import io
import sys

from bot.log_safety import RedactedFormatter


def test_telegram_request_urls_are_not_written_to_application_logs():
    from bot import main  # noqa: F401: apply production logging configuration

    for name in ("httpx", "httpcore", "telegram.request"):
        logger = logging.getLogger(name)
        assert not logger.isEnabledFor(logging.INFO)
        assert not logger.isEnabledFor(logging.DEBUG)
        assert logger.isEnabledFor(logging.WARNING)


def test_errors_preserve_diagnostics_without_request_credentials():
    token = "123456789:" + "example_token_without_real_access_123"
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(RedactedFormatter("%(levelname)s %(message)s"))
    try:
        raise RuntimeError(f"Request failed https://api.telegram.org/bot{token}/sendMessage")
    except RuntimeError:
        record = logging.LogRecord("test", logging.ERROR, __file__, 1,
                                   "Could not complete request", (), sys.exc_info())
    handler.handle(record)
    result = output.getvalue()
    assert token not in result
    assert "[redacted]/sendMessage" in result
    assert "RuntimeError" in result
    assert "Could not complete request" in result


def test_file_urls_and_standalone_tokens_are_redacted():
    token = "123456789:" + "example_token_without_real_access_123"
    formatter = RedactedFormatter("%(message)s")
    record = logging.LogRecord("test", logging.WARNING, __file__, 1,
                               "https://api.telegram.org/file/bot%s/photo.jpg token=%s", (token, token), None)
    result = formatter.format(record)
    assert token not in result
    assert result.count("[redacted]") == 2

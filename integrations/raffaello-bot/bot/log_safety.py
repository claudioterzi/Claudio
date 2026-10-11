"""Keep Telegram credentials out of log messages and exception tracebacks."""

import logging
import re


class RedactedFormatter(logging.Formatter):
    def format(self, record):
        rendered = super().format(record)
        rendered = re.sub(
            r"(https?://api\.telegram\.org/(?:file/)?bot)[^/\s]+",
            r"\1[redacted]",
            rendered,
            flags=re.IGNORECASE,
        )
        return re.sub(r"(?<![\w])\d{6,}:[A-Za-z0-9_-]{25,}", "[redacted]", rendered)

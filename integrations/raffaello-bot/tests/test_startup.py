"""Assemble the production handlers without starting Telegram or writing data."""

from telegram.ext import CommandHandler, ConversationHandler
from unittest.mock import Mock

from bot import main


def test_build_application_registers_real_mixed_handlers(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "require_token", lambda: "123456789:AAExampleTokenWithNoRealAccess0123456")
    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setattr(main.raffaello_store, "init", lambda: None)
    monkeypatch.setattr(main, "PERSISTENCE_PATH", tmp_path / "test.persistence")
    # Replace only the application/transport shell. All handler factories below
    # stay real, including factories that return both commands and conversations.
    builder = Mock()
    builder.token.return_value = builder
    builder.persistence.return_value = builder
    builder.post_init.return_value = builder
    monkeypatch.setattr(main.Application, "builder", lambda: builder)

    app = main.build_application()

    handlers = [call.args[0] for call in app.add_handler.call_args_list]
    conversations = [handler for handler in handlers if isinstance(handler, ConversationHandler)]
    commands = set().union(*(handler.commands for handler in handlers if isinstance(handler, CommandHandler)))
    assert conversations
    assert {"start", "letture", "nuovo", "ping", "rrr"} <= commands
    assert all(any(isinstance(fallback, CommandHandler) and "nuovo" in fallback.commands
                   for fallback in handler.fallbacks) for handler in conversations)

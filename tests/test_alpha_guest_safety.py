"""Guest containment: offline tests, synthetic invite and no provider access."""
import hashlib
import os
import socket
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api import tarot_alpha as alpha


@pytest.fixture
def guest_client(monkeypatch):
    invitation = "synthetic-offline-invitation"
    monkeypatch.setattr(alpha, "GUEST_INVITE_HASHES", frozenset({hashlib.sha256(invitation.encode()).hexdigest()}))
    ai = Mock(side_effect=AssertionError("Guest attempted AI"))
    follow_ai = Mock(side_effect=AssertionError("Guest attempted follow-up AI"))
    monkeypatch.setattr(alpha, "_ai", ai)
    monkeypatch.setattr(alpha, "_ai_follow_up", follow_ai)
    monkeypatch.setattr(alpha, "urlopen", Mock(side_effect=AssertionError("Network forbidden")))
    monkeypatch.setattr(socket, "create_connection", Mock(side_effect=AssertionError("Network forbidden")))
    with patch.dict(os.environ, {}, clear=True):
        yield alpha.app.test_client(), invitation, ai, follow_ai


def card():
    return {"carta": alpha._deck()[0]["nome"], "posizione": "presente", "asse": "nord", "polarita": "luce"}


@pytest.mark.parametrize("mode", [None, "lettura", "automatico", "AI", "APPROFONDIMENTO"])
@pytest.mark.parametrize("claim", [True, False, "ai"])
def test_guest_mode_cannot_select_ai(guest_client, mode, claim):
    client, invitation, ai, follow_ai = guest_client
    body = {"guest_invite": invitation, "guest_mode": claim, "domanda": "Una domanda", "domanda_utente": "Come leggere la carta?", "carte_scelte": [card()]}
    if mode is not None:
        body["modalita"] = mode
    response = client.post("/api/tarocchi/alpha-leggi", json=body)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["motore"]["via_api"] is False
    assert payload["motore"]["ospite_deterministico"] is True
    assert payload["motore"]["provider"] == "canonical-fallback"
    ai.assert_not_called()
    follow_ai.assert_not_called()


@pytest.mark.parametrize("body", [{"guest_mode": False}, {"guest_invite": "invalid"}, {"guest_invite": ""}, {"invito": "invalid"}, {"guest_invite": 42}])
def test_invalid_guest_claim_fails_before_ai(guest_client, body):
    client, _, ai, follow_ai = guest_client
    body.update({"domanda": "Test", "modalita": "approfondimento", "domanda_utente": "Test", "carte_scelte": [card()]})
    response = client.post("/api/tarocchi/alpha-leggi", json=body)
    assert response.status_code == 403
    ai.assert_not_called()
    follow_ai.assert_not_called()


def test_owner_path_still_calls_existing_ai_entrypoint(guest_client, monkeypatch):
    client, _, _, _ = guest_client
    ai = Mock(return_value=(None, None))
    monkeypatch.setattr(alpha, "_ai", ai)
    from tests.test_agora import init_data, TOKEN, CHAT
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN',TOKEN);monkeypatch.setenv('TELEGRAM_CHAT_ID',CHAT)
    response = client.post("/api/tarocchi/alpha-leggi", json={"domanda": "Test owner", "carte_scelte": [card()],"initData":init_data()})
    assert response.status_code == 200
    ai.assert_called_once()


def test_owner_followup_still_calls_existing_ai_entrypoint(guest_client, monkeypatch):
    client, _, _, _ = guest_client
    ai = Mock(return_value=(None, None))
    monkeypatch.setattr(alpha, "_ai_follow_up", ai)
    from tests.test_agora import init_data, TOKEN, CHAT
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN',TOKEN);monkeypatch.setenv('TELEGRAM_CHAT_ID',CHAT)
    response = client.post("/api/tarocchi/alpha-leggi", json={"modalita": "approfondimento", "domanda_utente": "Test owner", "carte_scelte": [card()],"initData":init_data()})
    assert response.status_code == 200
    ai.assert_called_once()


def test_guest_voice_legacy_fails_before_provider(guest_client, monkeypatch):
    client, invitation, _, _ = guest_client
    provider = Mock(side_effect=AssertionError("Voice provider forbidden"))
    monkeypatch.setattr(alpha, "_voice_provider", provider)
    response = client.post("/api/tarocchi/alpha-voce", json={"guest_invite": invitation, "testo": "Test"})
    assert response.status_code == 403
    provider.assert_not_called()

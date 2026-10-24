"""Exercise real SDK serialization and parsing without any provider traffic."""

import asyncio
from contextlib import contextmanager
from unittest.mock import patch

import anthropic
import httpx
import openai
import pytest
from google import genai
from google.genai import types as google_types

from rrremergen.api.router import LLMRouter, ProviderError
from sdq1.llm.providers import anthropic_provider as ap
from sdq1.llm.providers import openai_provider as op

KEY = "synthetic-sdk-contract-key-not-a-real-credential"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network forbidden in SDK contract tests")

    for target in ("socket.socket.connect", "socket.socket.connect_ex",
                   "socket.create_connection", "socket.getaddrinfo"):
        monkeypatch.setattr(target, forbidden)
    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.setenv(name, KEY)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setattr(op.MiniMaxProvider, "base_url", "https://api.minimax.io/v1")
    monkeypatch.setenv("RRREMERGEN_ALLOW_CLOUD", "1")


@contextmanager
def sdk_transport(kind, *, status=200, empty=False, missing_usage=False, expected_host=None):
    real_client = anthropic.Anthropic if kind == "anthropic" else openai.OpenAI
    requests, clients = [], []

    def respond(request):
        import json

        assert request.method == "POST"
        host = expected_host or ("api.anthropic.com" if kind == "anthropic" else "api.openai.com")
        assert request.url.host == host
        body = json.loads(request.content)
        requests.append(body)
        if kind == "anthropic":
            assert request.url.path == "/v1/messages"
            assert request.headers["x-api-key"] == KEY
            payload = {
                "id": "msg_mock", "type": "message", "role": "assistant",
                "model": body["model"], "stop_reason": "end_turn", "stop_sequence": None,
                "content": [{"type": "text", "text": "" if empty else "mock answer"}],
                "usage": {"input_tokens": 11, "output_tokens": 7},
            }
            error = {"type": "error", "error": {
                "type": "permission_error", "message": "synthetic blocked response"}}
        else:
            assert request.url.path.endswith("/chat/completions")
            assert request.headers["authorization"] == "Bearer " + KEY
            payload = {
                "id": "chatcmpl_mock", "object": "chat.completion", "created": 1,
                "model": body["model"], "choices": [{"index": 0, "finish_reason": "stop",
                    "message": {"role": "assistant", "content": None if empty else "mock answer"}}],
                "usage": None if missing_usage else {
                    "prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
            }
            error = {"error": {"type": "permission_error", "message": "synthetic blocked response",
                               "param": None, "code": "blocked"}}
        return httpx.Response(status, json=payload if status == 200 else error, request=request)

    def constructor(*args, **kwargs):
        assert kwargs["api_key"] == KEY
        kwargs["http_client"] = httpx.Client(transport=httpx.MockTransport(respond), trust_env=False)
        kwargs["max_retries"] = 0
        client = real_client(*args, **kwargs)
        clients.append(client)
        return client

    try:
        if kind == "anthropic":
            with patch.object(anthropic, "Anthropic", constructor):
                yield requests
        else:
            with patch.object(openai, "OpenAI", constructor), patch.object(op, "OpenAI", constructor):
                yield requests
    finally:
        for client in clients:
            client.close()


def assert_request(requests, model, *, site=False, kind="openai"):
    assert len(requests) == 1
    body = requests[0]
    assert (body["model"], body["max_tokens"], body["temperature"]) == (model, 64, 0.25)
    messages = [{"role": "user", "content": "synthetic user"}]
    if site and kind == "anthropic":
        assert body["system"] == "synthetic system"
    elif site:
        messages.insert(0, {"role": "system", "content": "synthetic system"})
    assert body["messages"] == messages


@contextmanager
def google_sdk_transport(*, status=200, empty=False):
    real_client = genai.Client
    requests, clients = [], []

    def respond(request):
        import json

        assert request.method == "POST"
        assert request.url.path == "/v1beta/models/gemini-2.5-pro:generateContent"
        assert request.headers["x-goog-api-key"] == KEY
        requests.append(json.loads(request.content))
        payload = {
            "candidates": [{"content": {"parts": [{"text": "" if empty else "mock answer"}],
                                         "role": "model"},
                            "finishReason": "STOP", "index": 0}],
            "usageMetadata": {"promptTokenCount": 11, "candidatesTokenCount": 7,
                              "totalTokenCount": 18},
            "modelVersion": "gemini-2.5-pro", "responseId": "synthetic",
        }
        error = {"error": {"code": status, "message": "synthetic blocked response",
                           "status": "PERMISSION_DENIED"}}
        return httpx.Response(status, json=payload if status == 200 else error, request=request)

    def constructor(*args, **kwargs):
        assert kwargs["api_key"] == KEY
        transport = httpx.MockTransport(respond)
        options = google_types.HttpOptions(
            base_url="https://example.invalid",
            httpx_client=httpx.Client(transport=transport, trust_env=False),
            httpx_async_client=httpx.AsyncClient(transport=transport, trust_env=False),
        )
        client = real_client(api_key=kwargs["api_key"], http_options=options)
        clients.append(client)
        return client

    try:
        with patch.object(genai, "Client", constructor):
            yield requests
    finally:
        for client in clients:
            client.close()


def test_rrremergen_google_real_sdk_request_and_response():
    with google_sdk_transport() as requests:
        router = LLMRouter(mode="cloud")
        result = asyncio.run(router.complete(
            "synthetic user", "gemini-2.5-pro", temperature=0.25, max_tokens=64))
        assert result == {"text": "mock answer", "model": "gemini-2.5-pro", "tokens_used": 7}
        assert router.calls[-1]["output_tokens"] == 7
        assert not router.calls[-1]["simulation"]
        assert requests == [{
            "contents": [{"parts": [{"text": "synthetic user"}], "role": "user"}],
            "generationConfig": {"temperature": 0.25, "maxOutputTokens": 64},
        }]


@pytest.mark.parametrize("status,empty", [(403, False), (200, True)])
def test_rrremergen_google_sdk_failure_is_terminal(status, empty):
    with google_sdk_transport(status=status, empty=empty) as requests:
        router = LLMRouter(mode="cloud")
        with pytest.raises(ProviderError):
            asyncio.run(router.complete("synthetic user", "gemini-2.5-pro"))
        assert not router.calls and len(requests) == 1


@pytest.mark.parametrize("cls,kind,model", [
    (ap.AnthropicProvider, "anthropic", "claude-3.5-sonnet"),
    (op.OpenAIProvider, "openai", "gpt-4o"),
    (op.DeepSeekProvider, "openai", "deepseek-chat"),
    (op.PerplexityProvider, "openai", "sonar"),
    (op.GrokProvider, "openai", "grok-4"),
    (op.MistralProvider, "openai", "mistral-large-latest"),
    (op.MiniMaxProvider, "openai", "MiniMax-M2"),
])
def test_site_real_sdk_request_and_response(cls, kind, model):
    base_url = getattr(cls, "base_url", None)
    host = httpx.URL(base_url).host if base_url else None
    with sdk_transport(kind, expected_host=host) as requests:
        provider = cls(modello=model, api_key=KEY, max_token=64, temperatura=0.25)
        result = provider.completa("synthetic system", "synthetic user")
        assert result.via_api and result.errore is None and result.testo == "mock answer"
        assert result.metadata["input_tokens"] == 11
        assert result.metadata["output_tokens"] == 7
        stop_field = "stop_reason" if kind == "anthropic" else "finish_reason"
        assert result.metadata[stop_field] == ("end_turn" if kind == "anthropic" else "stop")
        effective = op.DeepSeekProvider.current_model if cls is op.DeepSeekProvider else model
        assert_request(requests, effective, site=True, kind=kind)


@pytest.mark.parametrize("cls,kind", [(ap.AnthropicProvider, "anthropic"), (op.OpenAIProvider, "openai")])
def test_site_real_sdk_error_is_reported(cls, kind):
    with sdk_transport(kind, status=403) as requests:
        provider = cls(modello="contract-test", api_key=KEY)
        result = provider.completa("synthetic system", "synthetic user")
        assert not result.via_api and result.errore and result.testo == ""
        assert len(requests) == 1


def test_site_openai_nullable_content_and_usage():
    with sdk_transport("openai", empty=True, missing_usage=True):
        result = op.OpenAIProvider(modello="gpt-4o", api_key=KEY).completa("system", "user")
        assert result.testo == ""
        assert result.metadata["input_tokens"] is None
        assert result.metadata["output_tokens"] is None


ROUTER_CASES = [("anthropic", "claude-3.5-sonnet"), ("openai", "gpt-4o"), ("openai", "deepseek-chat")]


@pytest.mark.parametrize("kind,model", ROUTER_CASES)
def test_rrremergen_real_sdk_request_and_response(kind, model):
    host = "api.deepseek.com" if model == "deepseek-chat" else None
    with sdk_transport(kind, expected_host=host) as requests:
        router = LLMRouter(mode="cloud")
        result = asyncio.run(router.complete("synthetic user", model, temperature=0.25, max_tokens=64))
        assert result == {"text": "mock answer", "model": model, "tokens_used": 7}
        assert router.calls[-1]["output_tokens"] == 7
        assert not router.calls[-1]["simulation"]
        assert_request(requests, model)


@pytest.mark.parametrize("kind,model", ROUTER_CASES)
def test_rrremergen_real_sdk_error_is_terminal(kind, model):
    host = "api.deepseek.com" if model == "deepseek-chat" else None
    with sdk_transport(kind, status=403, expected_host=host) as requests:
        router = LLMRouter(mode="cloud")
        with pytest.raises(ProviderError):
            asyncio.run(router.complete("synthetic user", model))
        assert not router.calls and len(requests) == 1


@pytest.mark.parametrize("kind,model", ROUTER_CASES[:2])
def test_rrremergen_empty_sdk_content_is_terminal(kind, model):
    with sdk_transport(kind, empty=True) as requests:
        router = LLMRouter(mode="cloud")
        with pytest.raises(ProviderError):
            asyncio.run(router.complete("synthetic user", model))
        assert not router.calls and len(requests) == 1


@pytest.mark.parametrize("model,extra,response_data", [
    ("gpt-image-2", {"quality": "high", "output_format": "webp"},
     {"b64_json": "UklGRgAAAAAXRUJQ"}),
    ("dall-e-3", {"quality": "standard"},
     {"url": "https://example.invalid/synthetic.png", "revised_prompt": "synthetic revised prompt"}),
])
def test_real_openai_image_sdk_contract(model, extra, response_data):
    """Mirror site image parameters; validate SDK parsing, not image bytes or routes."""
    import json

    requests = []
    usage = {"input_tokens": 11, "output_tokens": 7, "total_tokens": 18,
             "input_tokens_details": {"image_tokens": 0, "text_tokens": 11}}

    def respond(request):
        assert request.method == "POST"
        assert request.url.host == "api.openai.com"
        assert request.url.path == "/v1/images/generations"
        assert request.headers["authorization"] == "Bearer " + KEY
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={"created": 1, "data": [response_data], "usage": usage},
                              request=request)

    with openai.OpenAI(api_key=KEY, max_retries=0,
                      http_client=httpx.Client(transport=httpx.MockTransport(respond), trust_env=False)) as client:
        result = client.images.generate(model=model, prompt="synthetic image", size="1024x1024", n=1, **extra)
    assert requests == [{"model": model, "prompt": "synthetic image", "size": "1024x1024", "n": 1, **extra}]
    for field, expected in response_data.items():
        assert getattr(result.data[0], field) == expected
    assert result.usage.input_tokens == 11
    assert result.usage.output_tokens == 7
    assert result.usage.model_dump()["total_tokens"] == 18

"""Las pruebas no pueden usar claves reales ni conectarse a Gemini o Groq (ver tests/conftest.py)."""
import json
import os
import sys
import urllib.request

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
from tests.conftest import PROVIDER_KEYS, RealProviderCallBlocked  # noqa: E402


def test_no_provider_keys_in_test_process():
    assert not any(os.environ.get(k) for k in PROVIDER_KEYS)


@pytest.mark.parametrize("url", ["https://generativelanguage.googleapis.com/v1beta/models/x:generateContent",
                                 "https://api.groq.com/openai/v1/chat/completions"])
def test_real_provider_connection_is_blocked(url):
    with pytest.raises(RealProviderCallBlocked):
        urllib.request.urlopen(urllib.request.Request(url, data=b"{}", method="POST"), timeout=1)


def test_client_with_fake_key_cannot_reach_gemini():
    import llm_provider as L
    c = L.GeminiClient(api_key="AQ.fake-key-for-test", model="gemini-flash-lite-latest")
    with pytest.raises(L.LLMProviderError):
        c.generate("hola")


def test_manager_without_keys_makes_no_call():
    """Con las claves vacias (conftest), llm_provider no puede rellenarlas desde el .env."""
    import llm_provider as L
    m = L.MultiProviderLLMManager()
    text, meta = m.generate_with_fallback("hola")
    assert text is None
    assert all(e.get("error_type") == "AUTH" for e in meta["errors"].values())


def test_gemini_client_records_model_version_and_thoughts(monkeypatch):
    import llm_provider as L
    body = {"modelVersion": "gemini-3.5-flash-lite", "candidates": [{"content": {"parts": [{"text": "OK"}]}, "finishReason": "STOP"}],
            "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 1, "thoughtsTokenCount": 3, "totalTokenCount": 9}}

    class R:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(body).encode()
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: R())
    c = L.GeminiClient(api_key="AQ.fake", model="gemini-flash-lite-latest")
    assert c.generate("x") == "OK"
    assert c.last_model_version == "gemini-3.5-flash-lite"
    assert c.last_usage["thoughts_tokens"] == 3 and c.last_usage["prompt_tokens"] == 5
    m = L.MultiProviderLLMManager(gemini_api_key="AQ.fake", groq_api_key=None, fallback_policy="manual")
    text, meta = m.generate_with_fallback("x")
    assert meta["model_version"] == "gemini-3.5-flash-lite"

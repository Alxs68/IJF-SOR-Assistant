"""LLM_JSON_SCHEMA (esquema estructurado + validacion + 1 reintento controlado) y ADA_PROMPT_RIGOR
(regla 14 del prompt). Ambos desactivados por defecto; ninguno toca el DIG."""
import io
import json
import os
import re
import sys
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
import ada_assistant as A  # noqa: E402
import llm_provider as L  # noqa: E402

VALID = json.dumps({"summary": "x", "normative_basis": "y", "citations": [], "conditions_and_exceptions": "No aplica",
                    "extended_analysis": "No aplica", "limitations": "Ninguna", "answerability": "RESPALDADA",
                    "evidence_quotes": [{"passage_id": "SOR-2026-08-P096-S114", "quote": "q", "supports": "s"}],
                    "evidence_conflicts": []})
# respuesta real recibida en la instancia experimental: falta la comilla de apertura de una clave
BROKEN = VALID[:-40] + ', {"passage_id": "P", "quote": "q", supports": "s"}], "evidence_conflicts": []}'
ANALYSIS_PROMPT = 'Contrato: {"evidence_quotes": []} Respuesta JSON:'


class Env:
    def __init__(self, **kv):
        self.kv, self.old = kv, {}

    def __enter__(self):
        for k, v in self.kv.items():
            self.old[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def __exit__(self, *a):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class Mgr:
    gemini_api_key = None

    def __init__(self, answers):
        self.answers, self.calls = list(answers), []

    def generate_with_fallback(self, prompt, **kw):
        self.calls.append(kw)
        return self.answers.pop(0), {"successful_provider": "Gemini"}


def ada_with(mgr):
    ada = A.ArbitrationDecisionAssistant.__new__(A.ArbitrationDecisionAssistant)
    ada.llm_manager = mgr
    return ada


def test_contract_problems():
    assert A.contract_problems(VALID) == []
    assert A.contract_problems(BROKEN) == ["json_invalido"]
    bad = json.loads(VALID)
    del bad["limitations"]
    bad["citations"] = "SOR"
    assert set(A.contract_problems(json.dumps(bad))) == {"falta:limitations", "tipo:citations"}


def test_schema_off_by_default_single_call():
    m = Mgr([BROKEN])
    with Env(LLM_JSON_MODE="1", LLM_JSON_SCHEMA=None):
        text, meta = ada_with(m)._call_llm(ANALYSIS_PROMPT)
    assert m.calls == [{"json_mode": True}] and text == BROKEN and "json_contract" not in meta


def test_schema_retry_once_when_invalid():
    m = Mgr([BROKEN, VALID])
    with Env(LLM_JSON_MODE="1", LLM_JSON_SCHEMA="1"):
        text, meta = ada_with(m)._call_llm(ANALYSIS_PROMPT)
    assert len(m.calls) == 2 and all(c == {"json_mode": True, "json_schema": True} for c in m.calls)
    assert text == VALID and meta["json_contract"]["valid"] is True
    assert meta["json_contract"]["attempts"][0]["problems"] == ["json_invalido"]


def test_schema_no_second_retry_and_invalid_reported():
    m = Mgr([BROKEN, BROKEN])
    with Env(LLM_JSON_MODE="1", LLM_JSON_SCHEMA="1"):
        text, meta = ada_with(m)._call_llm(ANALYSIS_PROMPT)
    assert len(m.calls) == 2 and meta["json_contract"]["valid"] is False  # el DIG abstendra (DIG-00)


def test_schema_valid_first_no_retry_and_translation_untouched():
    m = Mgr([VALID, "translated"])
    with Env(LLM_JSON_MODE="1", LLM_JSON_SCHEMA="1"):
        ada_with(m)._call_llm(ANALYSIS_PROMPT)
        ada_with(m)._call_llm("Translate this query")
    assert m.calls == [{"json_mode": True, "json_schema": True}, {}]


def test_gemini_payload_carries_schema_only_when_requested():
    sent = []

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        sent.append(json.loads(req.data.decode("utf-8")))
        body = {"candidates": [{"content": {"parts": [{"text": VALID}]}, "finishReason": "STOP"}],
                "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1, "totalTokenCount": 2}}
        return Resp(json.dumps(body).encode("utf-8"))
    c = L.GeminiClient(api_key="test-key", model="m")
    with patch.object(L.urllib.request, "urlopen", fake_urlopen):
        c.generate("p", json_mode=True)
        c.generate("p", json_mode=True, json_schema=True)
    assert "responseSchema" not in sent[0]["generationConfig"]
    cfg = sent[1]["generationConfig"]
    assert cfg["responseMimeType"] == "application/json"
    assert set(cfg["responseSchema"]["required"]) == set(A.CONTRACT_STR_KEYS + A.CONTRACT_LIST_KEYS)


def test_rigor_rule_off_by_default_and_generic():
    with Env(ADA_PROMPT_RIGOR=None):
        assert A.ArbitrationDecisionAssistant._rigor_rule() == ""
    with Env(ADA_PROMPT_RIGOR="1"):
        rule = A.ArbitrationDecisionAssistant._rigor_rule()
    assert rule.startswith("14.")
    # generica: sin identificadores, articulos ni terminos de las consultas usadas en el diagnostico
    assert not re.search(r"SOR-|\bArt\.|\d+\.\d+|tatami|ippon|veteran|cadet|judogi|waza|combate|pesaje", rule, re.I)

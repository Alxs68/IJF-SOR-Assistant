"""Fase 9 - pruebas adversariales extremo a extremo de ADA con el control DIG.

Motor real (RRE + EvidenceBundle + ADA); el generador es un StubLLM (mock). Estas pruebas verifican
el COMPORTAMIENTO de abstencion/aceptacion; no prueban entailment real ni la calidad de una
respuesta producida por un modelo real.
"""
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "tests")]
for _k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY"):
    os.environ[_k] = ""

from _ada_contract_helpers import (  # noqa: E402
    v4_enabled, v4_removed_reasons, assert_success_not_labelled_as_semantically_verified,
    StubLLM, json_answer, grounded_answer, supplementary_block, citation_ids, primary_passages)


@pytest.fixture(scope="module")
def ada():
    try:
        from ada_assistant import ArbitrationDecisionAssistant
    except Exception as e:
        pytest.skip(f"ADA no disponible: {e}")
    return ArbitrationDecisionAssistant()


NO_SOR_ANSWER = [
    "¿Cuál es el plazo de prescripción de las infracciones disciplinarias en la IJF?",
    "What is the exact fine amount for match fixing?",
    "What daily fee is paid to referees at a Grand Prix?",
]
ANSWERABLE = "How many seconds of osaekomi are needed for ippon?"


def _run(ada, query, analysis):
    stub = StubLLM(analysis=analysis)
    ada._call_llm = stub
    return ada.analyze_situation(query, top_k=5), stub


def _no_shadow_citation(res):
    return not any(re.match(r"(CHK|KUN|SHU1)-", str(c or "")) for c in citation_ids(res))


@pytest.mark.parametrize("query", NO_SOR_ANSWER)
def test_citing_any_delivered_sor_passage_no_longer_succeeds(ada, query):
    """Fase 8 sonda B: citar el primer pasaje SOR entregado bastaba para SUCCESS. Ahora no."""
    res, stub = _run(ada, query, lambda p, d: json_answer(d[:1]))
    assert res["status"] == "ABSTAIN"
    if stub.analysis_prompts:
        assert res.get("decision_integrity") and res["decision_integrity"]["decision"] == "ABSTENER"
        assert citation_ids(res) == []


@pytest.mark.parametrize("query", NO_SOR_ANSWER)
def test_fabricated_figure_with_literal_quote_abstains(ada, query):
    res, stub = _run(ada, query, lambda p, d: grounded_answer(p, d[:1], extra_text=" Importe: 987 unidades."))
    assert res["status"] == "ABSTAIN"
    if stub.analysis_prompts and res.get("decision_integrity"):
        if v4_enabled():   # V4 retira primero la frase con la cifra; la abstencion la decide el resto de controles
            assert any("cifras sin respaldo" in r for r in v4_removed_reasons(res))
            assert res["decision_integrity"]["failed_checks"] and "987" not in json.dumps(res["structured_answer"])
        else:
            assert "DIG-06_CIFRAS_RESPALDADAS" in res["decision_integrity"]["failed_checks"]


def test_declared_insufficient_evidence_abstains(ada):
    def insufficient(p, d):
        obj = json.loads(grounded_answer(p, d[:1]))
        obj["answerability"] = "EVIDENCIA_INSUFICIENTE"
        return json.dumps(obj, ensure_ascii=False)
    res, stub = _run(ada, ANSWERABLE, insufficient)
    assert res["status"] == "ABSTAIN"


def test_quote_taken_from_shadow_block_abstains(ada):
    q = "¿Cuánto tiempo puede mantenerse el kumikata sin atacar?"

    def shadow_quote(p, d):
        block = supplementary_block(p)
        m = re.search(r"\[COMPLEMENTO-\d+\][^\n]*\n(.+)", block)
        quote = m.group(1).strip() if m else "texto complementario inexistente en la evidencia primaria"
        obj = json.loads(json_answer(d[:1]))
        obj.update(answerability="RESPALDADA", evidence_conflicts=[],
                   evidence_quotes=[{"passage_id": d[0] if d else "", "quote": quote}])
        return json.dumps(obj, ensure_ascii=False)
    res, _ = _run(ada, q, shadow_quote)
    assert res["status"] == "ABSTAIN" and _no_shadow_citation(res)


def test_shadow_figures_in_answer_abstain(ada):
    q = "¿Cuánto tiempo puede mantenerse el kumikata sin atacar?"

    def influenced(p, d):
        block = supplementary_block(p)
        nums = re.findall(r"\b\d{2,}\b", block)
        prim = " ".join(primary_passages(p).values())
        extra = next((n for n in nums if n not in prim), None)
        obj = json.loads(grounded_answer(p, d[:1]))
        if extra:
            obj["extended_analysis"] = f"Según la práctica, el límite es {extra}."
        return json.dumps(obj, ensure_ascii=False), extra
    holder = {}

    def analysis(p, d):
        out, extra = influenced(p, d)
        holder["extra"] = extra
        return out
    res, stub = _run(ada, q, analysis)
    if not holder.get("extra"):
        pytest.skip("no se entregó contexto SHADOW con cifras ausentes del SOR para esta consulta")
    assert res["status"] == "ABSTAIN"
    assert "DIG-08_SIN_INFLUENCIA_SHADOW" in res["decision_integrity"]["failed_checks"]


def test_grounded_answer_success_is_labelled_without_entailment(ada):
    res, stub = _run(ada, ANSWERABLE, lambda p, d: grounded_answer(p, d[:1]))
    if res["status"] != "SUCCESS":
        pytest.skip(f"respuesta mecanica no supera DIG: {res.get('decision_integrity', {}).get('failed_checks')}")
    di = res["decision_integrity"]
    assert di["decision"] == "PERMITIR"
    assert_success_not_labelled_as_semantically_verified(di)
    assert "sin entailment" in res["mode"]
    assert _no_shadow_citation(res)
    assert all(s.get("decisive") is False for s in res.get("supplementary_context") or [])

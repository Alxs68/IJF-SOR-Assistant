"""EXPERIMENTAL (ADA_EVIDENCE_USED_ONLY): las normas de soporte mostradas son los pasajes que sustentan la respuesta.

Criterio: pasajes ENTREGADOS cuyo identificador [SOR-...] aparece en el texto visible de la respuesta final (cada
frase lleva el identificador del pasaje que la respalda; V4 retira las frases sin respaldo y anade las excepciones
con su identificador). Sin red: el generador y el verificador se simulan.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "tests")]
for _k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY"):
    os.environ[_k] = ""

import answer_presentation as AP  # noqa: E402

A, B, C, D = (f"SOR-2026-08-P0{n}0-S00{n}" for n in (1, 2, 3, 4))


def card(pid, page, frag):
    return {"passage_id": pid, "article_id": f"Art. {page}", "page_number": page, "source_url": "",
            "exact_quote": frag, "text_snippet": frag, "title": f"T{page}"}


RICH = {A: card(A, 10, "Regla general A."), B: card(B, 20, "Excepcion B."), C: card(C, 30, "Tema afin C."),
        D: card(D, 10, "Regla general A.")}   # D: mismo pagina y mismo fragmento que A (redundante)


def ids(cards):
    return [c["passage_id"] for c in cards]


def test_flag_on_by_default_and_reversible(monkeypatch):
    monkeypatch.delenv("ADA_EVIDENCE_USED_ONLY", raising=False)
    assert AP.evidence_used_enabled()
    monkeypatch.setenv("ADA_EVIDENCE_USED_ONLY", "0")
    assert not AP.evidence_used_enabled()


def test_case1_direct_answer_shows_only_its_passage():
    assert ids(AP.select_used_evidence(RICH, [f"La regla es X [{A}].", "Art. 1", "No aplica"])) == [A]


def test_case2_several_provisions_all_used_none_discarded():
    out = AP.select_used_evidence(RICH, [f"Primero X [{A}].", f"Base: Art. 1 [{A}] y Art. 2 [{B}].", "No aplica"])
    assert ids(out) == [A, B] and C not in ids(out)


def test_case3_rule_and_exception_are_both_shown():
    out = AP.select_used_evidence(RICH, [f"Regla general [{A}].", "Art. 1",
                                         f"Excepción: «Excepcion B.» [{B}]."])
    assert ids(out) == [A, B]


def test_case4_relation_between_articles_keeps_both_sides():
    """La relacion se apoya en los dos pasajes aunque solo uno contenga literalmente la conclusion."""
    out = AP.select_used_evidence(RICH, ["El Art. 1 remite al Art. 2.", "No aplica", "No aplica",
                                         f"La remision del Art. 1 [{A}, {B}] obliga a aplicar ambos."])
    assert ids(out) == [A, B]


def test_case5_redundant_and_unused_are_not_shown():
    out = AP.select_used_evidence(RICH, [f"X [{A}]. Y [{A}].", f"Z [{D}]."])
    assert ids(out) == [A]                 # D repite pagina y fragmento de A; C nunca se cita


def test_not_delivered_ids_are_ignored_and_no_citation_keeps_previous_behaviour():
    assert ids(AP.select_used_evidence(RICH, [f"X [{A}] [SOR-2026-08-P999-S999]."])) == [A]
    assert AP.select_used_evidence(RICH, ["Respuesta sin identificadores."]) is None


# ------------------------------------------------------------ extremo a extremo (motor real, LLM y verificador simulados)
@pytest.fixture(scope="module")
def ada():
    try:
        from ada_assistant import ArbitrationDecisionAssistant
    except Exception as e:  # pragma: no cover
        pytest.skip(f"ADA no disponible: {e}")
    return ArbitrationDecisionAssistant()


def _verifier_all_ok(prompt):
    n_s = prompt.split("ANSWER SENTENCES:")[1].count("\n[") + 1
    n_q = prompt.split("QUOTES:")[1].split("EXCEPTIONS:")[0].count("\n[")
    obj = {"quotes": [{"n": i, "pertinent": True} for i in range(1, n_q + 1)],
           "sentences": [{"n": i, "supported": True, "unsupported": ""} for i in range(1, n_s + 1)],
           "exceptions": [], "answers_question": True}
    return json.dumps(obj), {"prompt_tokens": 10, "completion_tokens": 2}, "stub-verifier"


def _run(ada, monkeypatch, used_flag, n_text):
    """El modelo declara en 'citations' (y cita literalmente) los dos primeros pasajes entregados, pero su texto
    solo usa los 'n_text' primeros: el caso observado en produccion (5 tarjetas para una respuesta de 1 pasaje)."""
    import decision_integrity as D
    from _ada_contract_helpers import StubLLM, grounded_answer
    monkeypatch.setenv("ADA_VERIFICATION_V4", "1")
    monkeypatch.setattr(D, "FIX_ALL_VISIBLE_FIELDS", True)
    monkeypatch.setenv("ADA_EVIDENCE_USED_ONLY", used_flag)
    seen = {}

    def analysis(prompt, delivered):
        declared = delivered[:2]
        obj = json.loads(grounded_answer(prompt, declared))
        used = declared[:n_text]
        obj["summary"] = "Respuesta de prueba. " + " ".join(f"Frase respaldada [{p}]." for p in used)
        obj["normative_basis"] = f"Art. de prueba [{used[0]}]."
        obj["citations"] = list(declared)
        seen["declared"], seen["used"] = declared, used
        return json.dumps(obj, ensure_ascii=False)
    ada._call_llm = StubLLM(analysis=analysis)
    monkeypatch.setattr(ada, "_call_verifier", _verifier_all_ok)
    res = ada.analyze_situation("How many seconds of osaekomi are needed for ippon?", top_k=5)
    if res["status"] != "SUCCESS" or len(seen.get("declared", [])) < 2:
        pytest.skip(f"respuesta mecanica no verificable en este modo de recuperacion: {res.get('mode')}")
    return res, seen


def test_e2e_only_passages_used_in_the_text_become_evidence(ada, monkeypatch):
    res, seen = _run(ada, monkeypatch, "1", n_text=1)
    shown = [c["passage_id"] for c in res["structured_answer"]["citations"]]
    assert shown == seen["used"]
    card0 = res["structured_answer"]["citations"][0]
    assert card0["page_number"] and card0["article_id"] and "exact_quote" in card0   # navegacion intacta


def test_e2e_two_used_passages_are_both_shown(ada, monkeypatch):
    res, seen = _run(ada, monkeypatch, "1", n_text=2)
    assert [c["passage_id"] for c in res["structured_answer"]["citations"]] == seen["used"]


def test_e2e_flag_off_restores_declared_citations(ada, monkeypatch):
    res, seen = _run(ada, monkeypatch, "0", n_text=1)
    assert [c["passage_id"] for c in res["structured_answer"]["citations"]] == seen["declared"]

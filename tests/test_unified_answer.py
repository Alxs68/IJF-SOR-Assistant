"""Respuesta unica, completa y verificada (ADA_UNIFIED_ANSWER=1) - pruebas extremo a extremo de ADA.

Motor real (RRE + EvidenceBundle + ADA + DIG); el generador es un StubLLM (sin red). Cubren los 10 requisitos
de la intervencion: una sola generacion, todo lo visible pasa por el DIG (tambien extended_analysis y
limitations), poda de accesorios sin respaldo con aviso, aclaracion, abstencion fuera de dominio, una sola
respuesta, citas correctas y ausencia de regresiones en la presentacion. No prueban entailment ni la calidad de
una respuesta real: solo el comportamiento del flujo y de los controles.
"""
import ast
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "tests")]
for _k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY"):
    os.environ[_k] = ""

import answer_presentation as AP  # noqa: E402
import decision_integrity as D  # noqa: E402
from _ada_contract_helpers import StubLLM, citation_ids, delivered_ids_in_result, grounded_answer  # noqa: E402

# Consultas respondibles candidatas: se usa la primera cuya respuesta mecanica de prueba supera el DIG en el modo
# anterior (la recuperacion difiere entre modo HYBRID y modo lexico degradado).
CANDIDATES = ("How many seconds of osaekomi are needed for ippon?", "What colour must the judogi be?",
              "What is the minimum length of the judogi jacket skirt?")
ANSWERABLE = CANDIDATES[0]
VISIBLE = ("summary", "normative_basis", "conditions_and_exceptions", "extended_analysis", "limitations")


@pytest.fixture(scope="module")
def ada():
    try:
        from ada_assistant import ArbitrationDecisionAssistant
    except Exception as e:
        pytest.skip(f"ADA no disponible: {e}")
    return ArbitrationDecisionAssistant()


@pytest.fixture
def unified(monkeypatch):
    monkeypatch.setattr(D, "FIX_ALL_VISIBLE_FIELDS", True)
    yield


@pytest.fixture
def legacy(monkeypatch):
    """Comportamiento anterior, con independencia de las variables del entorno."""
    monkeypatch.setattr(D, "FIX_ALL_VISIBLE_FIELDS", False)
    yield


def _run(ada, query, analysis):
    stub = StubLLM(analysis=analysis)
    ada._call_llm = stub
    return ada.analyze_situation(query, top_k=5), stub


def _with(**fields):
    def analysis(prompt, delivered):
        obj = json.loads(grounded_answer(prompt, delivered[:1]))
        obj.update(fields)
        return json.dumps(obj, ensure_ascii=False)
    return analysis


def _base_success(ada):
    """Fija ANSWERABLE en la primera consulta candidata que el flujo actual acepta (con el modo vigente)."""
    global ANSWERABLE
    for q in CANDIDATES:
        res, _ = _run(ada, q, _with())
        if res["status"] == "SUCCESS":
            ANSWERABLE = q
            return res
    pytest.skip("ninguna consulta candidata supera el DIG con la respuesta mecanica de prueba")


def _visible(res):
    sa = res["structured_answer"]
    return " ".join(str(sa.get(k) or "") for k in VISIBLE)


# 1 y 8. Una sola generacion y una sola respuesta por consulta
def test_single_generation_single_answer(ada, unified):
    _base_success(ada)
    res, stub = _run(ada, ANSWERABLE, _with())
    assert res["status"] == "SUCCESS"
    assert len(stub.analysis_prompts) == 1, "una sola llamada de generacion de la respuesta"
    assert "RESPUESTA ÚNICA Y COMPLETA" in stub.analysis_prompts[0] and "DOS NIVELES" not in stub.analysis_prompts[0]
    assert "Segrega los requisitos conexos" not in stub.analysis_prompts[0]
    sa = res["structured_answer"]
    assert sa["answer_mode"] == "UNIFIED" and sa["response_status"] == "SUCCESS"


def test_previous_contract_unchanged_when_off(ada, legacy):
    res, stub = _run(ada, ANSWERABLE, _with())
    if stub.analysis_prompts:
        p = stub.analysis_prompts[0]
        assert "CONTRATO OBLIGATORIO DE RESPUESTA EN DOS NIVELES" in p and "Segrega los requisitos conexos" in p
        assert "REQUIERE_ACLARACION" not in p
    assert "answer_mode" not in res["structured_answer"]


# 2. Todo lo visible pasa por el DIG, despues de todas las transformaciones
def test_final_validation_covers_all_visible_fields(ada, unified):
    _base_success(ada)
    res, _ = _run(ada, ANSWERABLE, _with())
    di = res["decision_integrity"]
    assert di["final_visible_check"]["decision"] == "PERMITIR"
    assert set(VISIBLE) <= set(di["validated_answer"])
    assert "+ALL" in di["version"]


# 3. extended_analysis no puede introducir contenido sin verificar
def test_extended_analysis_cannot_add_unverified_content(ada, unified):
    _base_success(ada)
    res, _ = _run(ada, ANSWERABLE, _with(extended_analysis="Interpretación normativa: se requieren 987 segundos adicionales."))
    if res["status"] == "SUCCESS":
        assert "987" not in _visible(res)
        assert res["decision_integrity"]["pruning"]["removed"]
    else:
        assert res["status"] == "ABSTAIN"


def test_previous_behaviour_let_extended_analysis_through(ada, legacy):
    _base_success(ada)
    res, _ = _run(ada, ANSWERABLE, _with(extended_analysis="Interpretación normativa: se requieren 987 segundos adicionales."))
    assert res["status"] == "SUCCESS" and "987" in res["structured_answer"]["extended_analysis"]


def test_limitations_cannot_add_unverified_figures(ada, unified):
    _base_success(ada)
    res, _ = _run(ada, ANSWERABLE, _with(limitations="El reglamento añade 987 segundos en finales."))
    assert res["status"] == "ABSTAIN" and "987" not in _visible(res)


# 4. Cifras y excepciones con respaldo
def test_unsupported_figure_in_main_answer_abstains(ada, unified):
    _base_success(ada)

    def analysis(prompt, delivered):
        obj = json.loads(grounded_answer(prompt, delivered[:1]))
        obj["summary"] += " Se requieren 987 segundos."
        return json.dumps(obj, ensure_ascii=False)
    res, _ = _run(ada, ANSWERABLE, analysis)
    assert res["status"] == "ABSTAIN"
    assert "DIG-06_CIFRAS_RESPALDADAS" in res["decision_integrity"]["failed_checks"]


def test_unsupported_exception_in_conditions_is_removed_and_flagged(ada, unified):
    _base_success(ada)
    res, _ = _run(ada, ANSWERABLE, _with(conditions_and_exceptions="Excepto en categoría cadete, donde se exigen 987 segundos."))
    if res["status"] == "SUCCESS":
        sa = res["structured_answer"]
        assert "987" not in _visible(res) and AP.is_placeholder(sa["conditions_and_exceptions"])
        assert any(note in sa["limitations"] for note in (
            "Se omitió de esta respuesta información complementaria",
            "Supplementary information that could not be verified"))
    else:
        assert res["status"] == "ABSTAIN"


# 5. Evidencia parcial: la limitacion declarada se conserva y se muestra
def test_partial_evidence_limitation_is_shown(ada, unified):
    _base_success(ada)
    lim = "Los pasajes certificados no regulan expresamente la situación de empate."
    res, _ = _run(ada, ANSWERABLE, _with(limitations=lim))
    if res["status"] != "SUCCESS":
        pytest.skip(f"limitacion rechazada por el DIG: {res['decision_integrity'].get('failed_checks')}")
    assert lim in res["structured_answer"]["limitations"]
    assert any(f == "limitations" and lim in txt for f, _t, txt in AP.unified_sections(res["structured_answer"]))


# 6. Ambiguedad: solicitud de aclaracion (sin dictamen)
def test_ambiguous_query_requests_clarification(ada, unified):
    question = "¿Se refiere a la inmovilización en competición individual o por equipos?"
    res, stub = _run(ada, ANSWERABLE, _with(answerability="REQUIERE_ACLARACION", summary=question))
    if not stub.analysis_prompts:
        pytest.skip("la consulta no llego a la generacion")
    assert res["status"] == "CLARIFICATION_REQUIRED"
    assert res["structured_answer"]["summary"] == question and res["structured_answer"]["citations"] == []
    assert AP.unified_header(res["structured_answer"]) == AP.TITLES["es"]["header_clarify"]


def test_clarification_with_unsupported_figure_uses_generic_text(ada, unified):
    res, stub = _run(ada, ANSWERABLE, _with(answerability="REQUIERE_ACLARACION",
                                            summary="¿Individual, donde se exigen 987 segundos, o por equipos?"))
    if not stub.analysis_prompts:
        pytest.skip("la consulta no llego a la generacion")
    assert res["status"] == "CLARIFICATION_REQUIRED" and "987" not in _visible(res)


def test_clarification_is_not_accepted_when_off(ada, legacy):
    res, stub = _run(ada, ANSWERABLE, _with(answerability="REQUIERE_ACLARACION", summary="¿Individual o por equipos?"))
    if stub.analysis_prompts:
        assert res["status"] == "ABSTAIN"


# 7. Fuera del dominio: abstencion adecuada
@pytest.mark.parametrize("query", ["What is the offside rule in football?", "Como funciona o VAR no futebol?"])
def test_out_of_domain_abstains(ada, unified, query):
    res, _ = _run(ada, query, _with(answerability="EVIDENCIA_INSUFICIENTE"))
    assert res["status"] == "ABSTAIN" and citation_ids(res) == []


# 9. Las citas siguen siendo correctas
def test_citations_remain_correct(ada, unified):
    _base_success(ada)
    res, _ = _run(ada, ANSWERABLE, _with())
    cited = citation_ids(res)
    assert cited and set(cited) <= set(delivered_ids_in_result(res))
    assert "DIG-03_CITA_LITERAL" not in res["decision_integrity"]["failed_checks"]


# 10. Presentacion: sin regresiones y sin desplegable de ampliacion en el modo unificado
def test_presentation_sections():
    sa = {"summary": "Respuesta [SOR-1].", "normative_basis": "Regla", "conditions_and_exceptions": "No aplica",
          "extended_analysis": "No aplica.", "limitations": "Ninguna", "answer_mode": "UNIFIED", "response_status": "SUCCESS"}
    assert AP.unified_sections(sa) == [("summary", "", "Respuesta [SOR-1]."),
                                       ("normative_basis", AP.TITLES["es"]["normative_basis"], "Regla")]
    assert AP.unified_sections(sa, "en")[1][1] == AP.TITLES["en"]["normative_basis"]
    ab = {"summary": "⚠️ Abstención. Motivo X.", "limitations": "Motivo X.", "response_status": "ABSTAIN", "answer_mode": "UNIFIED"}
    assert [f for f, _t, _x in AP.unified_sections(ab)] == ["summary"]


def test_presentation_off_by_default(monkeypatch):
    monkeypatch.delenv("ADA_UNIFIED_ANSWER", raising=False)
    assert AP.unified_enabled({"summary": "x"}) is False
    assert AP.unified_enabled({"summary": "x", "answer_mode": "UNIFIED"}) is True
    monkeypatch.setenv("ADA_UNIFIED_ANSWER", "1")
    assert AP.unified_enabled({"summary": "x"}) is True


def test_app_has_no_expand_answer_in_unified_branch():
    src = open(os.path.join(ROOT, "app.py"), encoding="utf-8").read()
    ast.parse(src)
    assert "import answer_presentation as _ap" in src
    start = src.index("                if unified_view:\n                    # Sin ampliacion")
    end = src.index("                elif struct and isinstance(struct, dict):", start)
    branch = src[start:end]
    assert "view_details_expander" not in branch and "extended_analysis" not in branch
    assert re.search(r"if unified_view:\n\s+with st\.container\(border=True\):", src)

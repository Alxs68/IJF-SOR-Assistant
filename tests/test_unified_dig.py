"""Respuesta unica y validacion integral (ADA_UNIFIED_ANSWER=1) - pruebas del DIG, sin ADA ni LLM.

Comprueban que, con el modo activo, ningun campo visible queda fuera de DIG-06/07/08 (incluidos
'extended_analysis' y 'limitations'), que la poda solo retira frases ACCESORIAS sin respaldo y que la solicitud
de aclaracion no puede afirmar cifras ni terminos ajenos a la consulta o a las citas. Con el modo desactivado
el DIG se comporta exactamente como antes. DIG-05, DIG-09 y DIG-11 no cambian.
"""
import json
import os
import sys
from contextlib import contextmanager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "tests")]
import decision_integrity as D  # noqa: E402
from test_dig_v3_fixes import GATE, JUDOGI_EN, JUDOGI_PIDS, JUDOGI_Q, ev, fixes, judogi_answer, run  # noqa: E402

UNCHANGED = ("DIG-05_PERTINENCIA_MINIMA", "DIG-09_EXCEPCIONES_CITADAS", "DIG-11_TERMINOS_DE_CONSULTA_EN_SOR")


@contextmanager
def unified(on=True):
    old = D.FIX_ALL_VISIBLE_FIELDS
    D.FIX_ALL_VISIBLE_FIELDS = on
    try:
        with fixes(True):
            yield
    finally:
        D.FIX_ALL_VISIBLE_FIELDS = old


def by_code(res):
    return {c["code"]: c["passed"] for c in res["checks"]}


def answer(**fields):
    a = judogi_answer()
    a.update(fields)
    return a


def test_off_by_default_and_version():
    assert os.environ.get("ADA_UNIFIED_ANSWER", "") != "1" or D.FIX_ALL_VISIBLE_FIELDS
    with unified(False):
        assert "+ALL" not in D.dig_version()
    with unified(True):
        assert "+ALL" in D.dig_version()


def test_base_answer_passes_in_both_modes():
    for on in (False, True):
        with unified(on):
            res = run(judogi_answer(), JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)
            assert res["decision"] == "PERMITIR", res["failed_checks"]


def test_extended_analysis_figure_is_now_verified():
    a = answer(extended_analysis="Interpretación normativa: el judogi debe tener 987 costuras.")
    with unified(False):
        assert run(a, JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)["decision"] == "PERMITIR"  # hueco anterior
    with unified(True):
        res = run(a, JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)
        assert res["decision"] == "ABSTENER" and "DIG-06_CIFRAS_RESPALDADAS" in res["failed_checks"]


def test_limitations_figure_needs_quote_or_query():
    with unified(True):
        bad = run(answer(limitations="El SOR fija 987 controles adicionales."), JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)
        assert "DIG-06_CIFRAS_RESPALDADAS" in bad["failed_checks"]
        q = "Que reglas debe cumplir el judogi de los veteranos de 60 años?"
        ok = run(answer(limitations="Los pasajes no distinguen a los veteranos de 60 años."), q, JUDOGI_EN, JUDOGI_PIDS)
        assert "DIG-06_CIFRAS_RESPALDADAS" not in ok["failed_checks"]


def test_extended_analysis_citation_needs_literal_quote():
    a = answer(extended_analysis="Véase también [SOR-2026-08-P103-S124].")
    with unified(False):
        assert "DIG-02_CITAS_CON_CITA_LITERAL" not in run(a, JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)["failed_checks"]
    with unified(True):
        assert "DIG-02_CITAS_CON_CITA_LITERAL" in run(a, JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)["failed_checks"]


def test_dig05_dig09_dig11_unchanged_by_mode():
    a = answer(extended_analysis="Interpretación normativa: 987.", limitations="Ninguna")
    with unified(False):
        before = by_code(run(a, JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS))
    with unified(True):
        after = by_code(run(a, JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS))
    assert all(before[c] == after[c] for c in UNCHANGED)


def test_prune_units_keeps_references_whole():
    units = D.prune_units("Para U18 (menor de 18 años) se exige X [SOR-2026-08-P109-S001, pág. 109]. "
                          "Ver Art. 3.1 del SOR. Medida 1.5 cm. Fin")
    assert units == ["Para U18 (menor de 18 años) se exige X [SOR-2026-08-P109-S001, pág. 109].",
                     "Ver Art. 3.1 del SOR.", "Medida 1.5 cm.", "Fin"]


def test_prune_removes_only_accessory_unsupported_sentences():
    a = answer(conditions_and_exceptions="El judogi debe ser blanco o azul [SOR-2026-08-P105-S131]. "
                                         "Además, la manga debe medir 987 cm.",
               extended_analysis="Interpretación normativa: se aplican 654 controles.")
    with unified(True):
        txt, removed = GATE.prune_unsupported(json.dumps(a, ensure_ascii=False), JUDOGI_Q, JUDOGI_EN)
        obj = json.loads(txt)
        assert {r["field"] for r in removed} == {"conditions_and_exceptions", "extended_analysis"}
        assert "987" not in obj["conditions_and_exceptions"] and "blanco o azul" in obj["conditions_and_exceptions"]
        assert obj["extended_analysis"] == "No aplica"
        assert obj["summary"] == a["summary"] and obj["evidence_quotes"] == a["evidence_quotes"]
        res = GATE.evaluate(txt, JUDOGI_Q, JUDOGI_EN, ev(JUDOGI_PIDS), [])
        assert res["decision"] == "PERMITIR", res["failed_checks"]


def test_prune_never_touches_summary_or_basis():
    a = answer(summary="Los veteranos deben usar judogi con 987 botones [SOR-2026-08-P105-S131].")
    with unified(True):
        txt, removed = GATE.prune_unsupported(json.dumps(a, ensure_ascii=False), JUDOGI_Q, JUDOGI_EN)
        assert removed == [] and json.loads(txt)["summary"] == a["summary"]
        assert "DIG-06_CIFRAS_RESPALDADAS" in run(a, JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)["failed_checks"]


def test_clarification_cannot_assert_unsupported_content():
    q = "¿Cuántos atletas puede inscribir un equipo?"
    ok = {"answerability": "REQUIERE_ACLARACION", "summary": "¿Se refiere a la competición por equipos mixtos o a la de equipos femeninos?",
          "evidence_quotes": []}
    bad = dict(ok, summary="¿Se refiere a equipos mixtos, donde se inscriben 987 atletas?")
    with unified(True):
        assert GATE.verify_clarification(json.dumps(ok, ensure_ascii=False), q, "", [])[0] is True
        assert GATE.verify_clarification(json.dumps(bad, ensure_ascii=False), q, "", [])[0] is False
        cites = dict(ok, summary="¿Se refiere a [SOR-2026-08-P999-S999]?")
        assert GATE.verify_clarification(json.dumps(cites), q, "", ["SOR-2026-08-P105-S131"])[0] is False

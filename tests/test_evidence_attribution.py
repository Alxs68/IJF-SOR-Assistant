"""Completado de atribucion literal (ADA_EVIDENCE_COMPLETION): solo frases LITERALES de pasajes citados por la
respuesta, ancladas a la afirmacion; el DIG sigue evaluando todo y no se toca ningun control."""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]

import decision_integrity as D  # noqa: E402
import evidence_attribution as EA  # noqa: E402

P168 = "SOR-2026-08-P168-S188"


@pytest.fixture(scope="module")
def corpus():
    ps = json.load(open(os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json"),
                        encoding="utf-8"))
    return {p["passage_id"]: dict(p, page=p.get("pdf_page_index")) for p in ps}


@pytest.fixture(scope="module")
def gate(corpus):
    return D.DecisionIntegrityGate(list(corpus.values()))


def _answer(summary, quotes, **kw):
    obj = {"summary": summary, "normative_basis": f"Article 15 [{P168}]", "citations": [P168],
           "conditions_and_exceptions": "No aplica", "extended_analysis": "No aplica", "limitations": "Ninguna",
           "answerability": "RESPALDADA", "evidence_conflicts": [], "evidence_quotes": quotes}
    obj.update(kw)
    return json.dumps(obj, ensure_ascii=False)


Q = "existe la puntuacion de yuko en ne-waza"
Q_EN = "does yuko score exist in ne-waza"


def test_adds_literal_sentence_for_unquoted_number(corpus, gate):
    ans = _answer(f"En ne-waza, waza-ari se obtiene con osaekomi de 10 a 19 segundos [{P168}].",
                  [{"passage_id": P168, "quote": "Waza-ari evaluation in ne-waza", "supports": "x"}])
    out, added = EA.complete_quotes(ans, {P168: corpus[P168]}, gate, Q, Q_EN)
    assert any(a["tipo"] == "cifra" and a["elemento"] in {"10", "19"} for a in added)
    obj = json.loads(out)
    for q in obj["evidence_quotes"]:
        assert D.norm(q["quote"]) in D.norm(corpus[P168]["text_original"])  # literal del pasaje citado
    assert not ({"10", "19"} - D.numbers_in(" ".join(q["quote"] for q in obj["evidence_quotes"])))


def test_never_quotes_a_passage_the_answer_does_not_cite(corpus, gate):
    other = "SOR-2026-08-P152-S180"
    ans = _answer(f"El osaekomi de 20 segundos da ippon [{P168}].",
                  [{"passage_id": P168, "quote": "Waza-ari evaluation in ne-waza", "supports": "x"}])
    _out, added = EA.complete_quotes(ans, {P168: corpus[P168], other: corpus[other]}, gate, Q, Q_EN)
    assert all(a["passage_id"] == P168 for a in added)


def test_unanchored_number_is_not_attributed(corpus, gate):
    # "90" aparece en el pasaje, pero la afirmacion no comparte ningun otro concepto con esas frases.
    ans = _answer(f"La cuota de inscripcion es de 90 euros [{P168}].",
                  [{"passage_id": P168, "quote": "Waza-ari evaluation in ne-waza", "supports": "x"}])
    _out, added = EA.complete_quotes(ans, {P168: corpus[P168]}, gate, "cuanto cuesta la inscripcion", "entry fee")
    assert not [a for a in added if a["elemento"] == "90"]


def test_completed_answer_still_goes_through_every_dig_check(corpus, gate):
    ans = _answer(f"En ne-waza, waza-ari se obtiene con osaekomi de 10 a 19 segundos [{P168}].",
                  [{"passage_id": P168, "quote": "Waza-ari evaluation in ne-waza", "supports": "x"}])
    out, _added = EA.complete_quotes(ans, {P168: corpus[P168]}, gate, Q, Q_EN)
    res = gate.evaluate(out, Q, Q_EN, [corpus[P168]], [])
    codes = {c["code"] for c in res["checks"]}
    assert {"DIG-05_PERTINENCIA_MINIMA", "DIG-09_EXCEPCIONES_CITADAS", "DIG-06_CIFRAS_RESPALDADAS"} <= codes


def test_no_change_when_everything_is_quoted(corpus, gate):
    ans = _answer(f"Yuko existe [{P168}].",
                  [{"passage_id": P168, "quote": "Everything that is out of this range will be yuko or no score",
                    "supports": "x"}])
    out, added = EA.complete_quotes(ans, {P168: corpus[P168]}, gate, Q, Q_EN)
    assert added == [] and out == ans

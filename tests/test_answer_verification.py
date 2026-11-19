"""Verificacion de respuestas V4 (ADA_VERIFICATION_V4=1) - propiedades generales, sin red.

El verificador LLM se sustituye por funciones deterministas que devuelven un veredicto fijo: estas pruebas
comprueban el COMPORTAMIENTO del mecanismo (corregir antes de rechazar, abstenerse cuando no queda respuesta
respaldada, modo degradado, completado de excepciones, respuestas negativas, contador de consultas), no la calidad
del juicio del modelo, que se mide en la evaluacion funcional.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "tests")]
for _k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY"):
    os.environ[_k] = ""

import answer_verification as V  # noqa: E402
import decision_integrity as D  # noqa: E402

PA = "SOR-2026-08-P010-S001"
PB = "SOR-2026-08-P020-S002"
TEXT_A = ("Article 7 Osaekomi Time\na) Ippon:  20 seconds.\nb) Waza-ari: 10 seconds or more, but less than 20 seconds.\n"
          "The referee announces Osaekomi when the hold is established.")
TEXT_B = "The competition area must be at least 14 m x 14 m. Spectators must remain outside the safety area."
PASSAGES = [{"passage_id": PA, "page": 10, "pdf_page_index": 10, "text_original": TEXT_A},
            {"passage_id": PB, "page": 20, "pdf_page_index": 20, "text_original": TEXT_B}]


@pytest.fixture(scope="module")
def gate():
    return D.DecisionIntegrityGate(PASSAGES)


def answer(summary, quotes, conditions="No aplica", answerability="RESPALDADA", limitations="Ninguna"):
    return json.dumps({"summary": summary, "normative_basis": f"Art. 7 [{PA}]", "conditions_and_exceptions": conditions,
                       "extended_analysis": "No aplica", "limitations": limitations, "answerability": answerability,
                       "citations": [], "evidence_conflicts": [],
                       "evidence_quotes": [{"passage_id": p, "quote": q} for p, q in quotes]}, ensure_ascii=False)


def verdict(sentences_ok=None, quotes_ok=None, exceptions=None, answers=True):
    """llm_call fijo: frases/citas por numero (por defecto, todas respaldadas y pertinentes)."""
    def call(prompt):
        n_s = prompt.split("ANSWER SENTENCES:")[1].count("\n[") + 1
        n_q = prompt.split("QUOTES:")[1].split("EXCEPTIONS:")[0].count("\n[")
        obj = {"quotes": [{"n": i, "pertinent": (quotes_ok or {}).get(i, True)} for i in range(1, n_q + 1)],
               "sentences": [{"n": i, "supported": (sentences_ok or {}).get(i, True), "unsupported": "x"}
                             for i in range(1, n_s + 1)],
               "exceptions": [{"n": i, "relevant": v} for i, v in (exceptions or {}).items()],
               "answers_question": answers}
        return json.dumps(obj), {"prompt_tokens": 100, "completion_tokens": 20}, "stub-verifier"
    return call


def run(gate, ans, llm_call=None, query="How many seconds of osaekomi for ippon?"):
    return V.verify(ans, query, query, PASSAGES[:1], PASSAGES[1:], gate, llm_call=llm_call)


def dig_says(gate, monkeypatch, failed=()):
    """Fija la decision del DIG completo (lo que decide en modo reducido)."""
    checks = [{"code": c, "passed": True} for c in V.HARD_CHECKS] + [{"code": c, "passed": False} for c in failed]
    monkeypatch.setattr(gate, "evaluate", lambda *a, **k: {
        "decision": "ABSTENER" if failed else "PERMITIR", "failed_checks": list(failed), "checks": checks})


def test_flag_off_by_default(monkeypatch):
    monkeypatch.delenv("ADA_VERIFICATION_V4", raising=False)
    assert V.enabled() is False
    monkeypatch.setenv("ADA_VERIFICATION_V4", "1")
    assert V.enabled() is True and V.verifier_model() == "gemini-flash-latest"


def test_short_table_quote_is_expanded_to_its_full_line(gate):
    out, rec = run(gate, answer(f"Ippon requires 20 seconds [{PA}].", [(PA, "Ippon:  20 seconds.")]), verdict())
    assert rec["decision"] == "PERMITIR"
    q = json.loads(out)["evidence_quotes"][0]["quote"]
    assert q == "a) Ippon:  20 seconds." and rec["verification"]["expanded_quotes"]


def test_cited_passage_without_literal_quote_is_removed_not_the_answer(gate):
    ans = answer(f"Ippon requires 20 seconds [{PA}]. The area is large [{PB}].",
                 [(PA, "a) Ippon:  20 seconds."), (PB, "this text is not in the passage at all")])
    out, rec = run(gate, ans, verdict())
    obj = json.loads(out)
    assert rec["decision"] == "PERMITIR"
    assert PB not in obj["summary"] and "20 seconds" in obj["summary"]
    assert any("sin cita literal" in r["reason"] for r in rec["verification"]["removed"])


def test_unsupported_figure_is_removed_deterministically_even_without_llm(gate, monkeypatch):
    dig_says(gate, monkeypatch)
    ans = answer(f"Ippon requires 20 seconds [{PA}]. Waza-ari requires 15 seconds [{PA}].",
                 [(PA, "a) Ippon:  20 seconds.")])
    out, rec = run(gate, ans, llm_call=None)
    assert "15 seconds" not in json.loads(out)["summary"]
    assert any("cifras sin respaldo" in r["reason"] for r in rec["verification"]["removed"])
    assert rec["verification"]["mode"] == "REDUCIDA"


def test_llm_unsupported_sentence_is_pruned_and_rest_is_kept(gate):
    ans = answer(f"Ippon requires 20 seconds [{PA}]. Only the referee may stop the hold [{PA}].",
                 [(PA, "a) Ippon:  20 seconds.")])
    out, rec = run(gate, ans, verdict(sentences_ok={2: False}))
    obj = json.loads(out)
    assert rec["decision"] == "PERMITIR"
    assert "Only the referee" not in obj["summary"] and "20 seconds" in obj["summary"]


def test_not_pertinent_quote_drops_its_citation(gate):
    ans = answer(f"Ippon requires 20 seconds [{PA}]. The area is 14 m x 14 m [{PB}].",
                 [(PA, "a) Ippon:  20 seconds."), (PB, "The competition area must be at least 14 m x 14 m.")])
    out, rec = run(gate, ans, verdict(quotes_ok={2: False}))
    obj = json.loads(out)
    assert rec["decision"] == "PERMITIR" and PB not in json.dumps(obj) and "14 m" not in obj["summary"]


def test_abstains_when_no_supported_answer_remains(gate):
    ans = answer(f"Ippon requires 20 seconds [{PA}].", [(PA, "a) Ippon:  20 seconds.")])
    _out, rec = run(gate, ans, verdict(sentences_ok={1: False, 2: False}))
    assert rec["decision"] == "ABSTENER" and "sin_respuesta_respaldada" in rec["failed_checks"]


def test_abstains_when_answer_does_not_address_the_question(gate):
    ans = answer(f"Ippon requires 20 seconds [{PA}].", [(PA, "a) Ippon:  20 seconds.")])
    _out, rec = run(gate, ans, verdict(answers=False))
    assert rec["decision"] == "ABSTENER" and "no_responde_la_pregunta" in rec["failed_checks"]


def test_verifier_failure_activates_reduced_mode_and_dig_decides(gate, monkeypatch):
    def boom(prompt):
        raise RuntimeError("provider down key=SECRET123")
    ans = answer(f"Ippon requires 20 seconds [{PA}].", [(PA, "a) Ippon:  20 seconds.")])
    dig_says(gate, monkeypatch)
    _out, rec = run(gate, ans, boom)
    assert rec["decision"] == "PERMITIR" and rec["verification"]["mode"] == "REDUCIDA"
    assert "SECRET123" not in json.dumps(rec)
    dig_says(gate, monkeypatch, failed=("DIG-05_PERTINENCIA",))
    _out, rec = run(gate, ans, boom)
    assert rec["decision"] == "ABSTENER" and "DIG-05_PERTINENCIA" in rec["failed_checks"]
    assert rec["verification"]["dig_fallback"] == ["DIG-05_PERTINENCIA"]


@pytest.mark.parametrize("payload", ["{}", '{"error": "quota"}', '{"sentences": [{"n": 1, "supported": true}]}',
                                     '{"sentences": "all supported"}'])
def test_empty_or_partial_verdict_falls_back_to_reduced_mode(gate, monkeypatch, payload):
    """Un veredicto vacio, de error o que no juzga cada frase no cuenta como verificacion: decide el DIG completo
    (H-1). Sin este control, la frase sin juicio se emitia como verificada."""
    ans = answer(f"Ippon requires 20 seconds [{PA}]. Only the referee may stop the hold [{PA}].",
                 [(PA, "a) Ippon:  20 seconds.")])
    dig_says(gate, monkeypatch, failed=("DIG-05_PERTINENCIA",))
    _out, rec = run(gate, ans, lambda p: (payload, {}, "stub-verifier"))
    v = rec["verification"]
    assert rec["decision"] == "ABSTENER" and v["mode"] == "REDUCIDA"
    assert v["verifier"]["complete"] is False and v["dig_fallback"] == ["DIG-05_PERTINENCIA"]


def test_complete_verdict_is_still_used(gate):
    ans = answer(f"Ippon requires 20 seconds [{PA}].", [(PA, "a) Ippon:  20 seconds.")])
    _out, rec = run(gate, ans, verdict())
    assert rec["decision"] == "PERMITIR" and rec["verification"]["mode"] == "LLM"
    assert rec["verification"]["verifier"]["complete"] is True


def test_reduced_mode_never_relaxes_the_dig(gate, monkeypatch):
    """Sin verificador, una respuesta que el DIG rechaza no se emite (aunque la capa 1 no encuentre nada)."""
    dig_says(gate, monkeypatch, failed=("DIG-05_PERTINENCIA",))
    ans = answer(f"Ippon requires 20 seconds [{PA}].", [(PA, "a) Ippon:  20 seconds.")])
    _out, rec = run(gate, ans, None)
    assert rec["decision"] == "ABSTENER"


def test_with_verifier_non_hard_dig_failures_do_not_veto(gate, monkeypatch):
    """Con verificador, el DIG solo decide en los controles duros (SHADOW); el resto se corrige, no se veta."""
    dig_says(gate, monkeypatch, failed=("DIG-05_PERTINENCIA", "DIG-09_EXCEPCIONES"))
    ans = answer(f"Ippon requires 20 seconds [{PA}].", [(PA, "a) Ippon:  20 seconds.")])
    _out, rec = run(gate, ans, verdict())
    assert rec["decision"] == "PERMITIR" and "dig_fallback" not in rec["verification"]


def test_relevant_exception_is_added_with_literal_quote(gate, monkeypatch):
    exc = {"passage_id": PA, "sentence": "b) Waza-ari: 10 seconds or more, but less than 20 seconds."}
    monkeypatch.setattr(V, "_exception_candidates", lambda quotes, delivered, g: [exc])
    ans = answer(f"Ippon requires 20 seconds [{PA}].", [(PA, "a) Ippon:  20 seconds.")])
    out, rec = run(gate, ans, verdict(exceptions={1: True}))
    obj = json.loads(out)
    assert rec["decision"] == "PERMITIR" and exc["sentence"] in obj["conditions_and_exceptions"]
    assert any(q["quote"] == exc["sentence"] for q in obj["evidence_quotes"])


def test_irrelevant_exception_is_not_added_and_never_blocks(gate, monkeypatch):
    exc = {"passage_id": PA, "sentence": "b) Waza-ari: 10 seconds or more, but less than 20 seconds."}
    monkeypatch.setattr(V, "_exception_candidates", lambda quotes, delivered, g: [exc])
    ans = answer(f"Ippon requires 20 seconds [{PA}].", [(PA, "a) Ippon:  20 seconds.")])
    out, rec = run(gate, ans, verdict(exceptions={1: False}))
    assert rec["decision"] == "PERMITIR" and exc["sentence"] not in out


def test_negative_answer_is_emitted_when_verified(gate):
    ans = answer("Los pasajes del SOR 2026 entregados no contienen información sobre honorarios de árbitros.", [],
                 answerability="EVIDENCIA_INSUFICIENTE")
    out, rec = run(gate, ans, verdict(), query="How much is a referee paid?")
    obj = json.loads(out)
    assert rec["decision"] == "PERMITIR" and obj["response_kind"] == "NO_CUBIERTA"


def test_negative_answer_with_figures_or_without_verifier_abstains(gate):
    ans = answer("Los pasajes no lo contienen, pero suele ser 300 euros.", [], answerability="EVIDENCIA_INSUFICIENTE")
    assert run(gate, ans, verdict(), query="How much is a referee paid?")[1]["decision"] == "ABSTENER"
    ans2 = answer("Los pasajes del SOR 2026 entregados no contienen esa información.", [],
                  answerability="EVIDENCIA_INSUFICIENTE")
    assert run(gate, ans2, None, query="How much is a referee paid?")[1]["decision"] == "ABSTENER"


def test_shadow_influence_still_blocks(gate):
    ans = answer(f"Ippon requires 20 seconds [{PA}], as the zebrafinch protocol says.", [(PA, "a) Ippon:  20 seconds.")])
    _out, rec = V.verify(ans, "ippon osaekomi", "ippon osaekomi", PASSAGES[:1], PASSAGES[1:], gate,
                         llm_call=verdict(), supplementary_texts=["The zebrafinch protocol applies to holds."])
    assert rec["decision"] == "ABSTENER" and "DIG-08_SIN_INFLUENCIA_SHADOW" in rec["failed_checks"]


def test_verifier_usage_is_recorded(gate):
    _out, rec = run(gate, answer(f"Ippon requires 20 seconds [{PA}].", [(PA, "a) Ippon:  20 seconds.")]), verdict())
    v = rec["verification"]["verifier"]
    assert v["model"] == "stub-verifier" and v["usage"]["prompt_tokens"] == 100


def test_strip_ids_leaves_no_empty_separators():
    # Identificador al inicio, en medio y al final de un grupo, con corchetes y parentesis.
    assert V._strip_ids("Rule [A1-S1, B2-S2, C3-S3].", {"B2-S2"}) == "Rule [A1-S1, C3-S3]."
    assert V._strip_ids("Rule [A1-S1; B2-S2; C3-S3]", {"A1-S1"}) == "Rule [B2-S2; C3-S3]"
    assert V._strip_ids("Rule (A1-S1, B2-S2, C3-S3)", {"C3-S3", "B2-S2"}) == "Rule (A1-S1)"
    # Grupo que queda vacio: desaparece sin dejar espacio antes del punto.
    assert V._strip_ids("Nails short [A1-S1]. Weigh-in [B2-S2]", {"A1-S1"}) == "Nails short. Weigh-in [B2-S2]"
    # Fuera de corchetes y parentesis el texto no se altera.
    assert V._strip_ids("Judogi: clean, dry; and/or odourless", {"Z9-S9"}) == "Judogi: clean, dry; and/or odourless"


# ---------------------------------------------------------------- contador de consultas y consumo
def test_one_user_query_is_one_increment_regardless_of_internal_calls(tmp_path):
    from usage_tracker import UsageTracker, record_user_query
    tr = UsageTracker(filepath=str(tmp_path / "m.json"))
    res = {"llm_meta": {"successful_provider": "Gemini", "successful_model": "gemini-flash-lite-latest"},
           "token_usage": {"prompt_tokens": 1300, "completion_tokens": 260, "total_tokens": 1560,
                           "translation_tokens": {"prompt_tokens": 100, "completion_tokens": 10},
                           "analysis_tokens": {"prompt_tokens": 1000, "completion_tokens": 200},
                           "verification_tokens": {"prompt_tokens": 200, "completion_tokens": 50},
                           "by_model": {"gemini-flash-lite-latest": {"prompt_tokens": 1100, "completion_tokens": 210},
                                        "gemini-flash-latest": {"prompt_tokens": 200, "completion_tokens": 50}}}}
    m = record_user_query(tr, "¿Cuánto dura un combate?", res)
    assert m["total_queries"] == 1 and m["queries_with_llm"] == 1 and m["total_tokens"] == 1560
    from usage_tracker import PRICING_TABLE
    lite, flash = PRICING_TABLE["gemini-flash-lite-latest"], PRICING_TABLE["gemini-flash-latest"]
    expected = (1100 * lite["input_per_m"] + 210 * lite["output_per_m"] + 200 * flash["input_per_m"]
                + 50 * flash["output_per_m"]) / 1_000_000
    assert m["total_cost_usd"] == pytest.approx(expected)
    m2 = record_user_query(tr, "otra", {"llm_meta": {}, "token_usage": {}})
    assert m2["total_queries"] == 2 and m2["queries_local"] == 1


def test_add_usage_sums_into_the_same_query():
    from ada_assistant import _add_usage
    total = {"prompt_tokens": 1000, "completion_tokens": 200, "total_tokens": 1200}
    _add_usage(total, "verification_tokens", {"prompt_tokens": 300, "completion_tokens": 40, "thoughts_tokens": 10},
               "gemini-flash-latest")
    assert total["prompt_tokens"] == 1300 and total["completion_tokens"] == 250 and total["total_tokens"] == 1550
    assert total["by_model"]["gemini-flash-latest"] == {"prompt_tokens": 300, "completion_tokens": 50}


# ---------------------------------------------------------------- contrato
def test_v4_contract_keeps_unified_contract_and_adjusts_exceptions_and_absences(monkeypatch):
    from ada_assistant import ArbitrationDecisionAssistant as A
    monkeypatch.setenv("ADA_VERIFICATION_V4", "1")
    t = A._contract_texts(True)
    assert "RESPUESTA ÚNICA Y COMPLETA" in t["title"]
    assert "cita también esa excepción literalmente" not in t["rule13"]
    assert "no añadas excepciones que no afecten a lo preguntado" in t["rule13"]
    assert "Los pasajes del SOR 2026 entregados no contienen" in t["rule13"]
    assert "Una consulta puntual recibe una respuesta puntual" in t["rule7"]
    monkeypatch.delenv("ADA_VERIFICATION_V4")
    assert A._contract_texts(True)["rule13"] != t["rule13"]


# ---------------------------------------------------------------- extremo a extremo (motor real, LLM simulado)
@pytest.fixture(scope="module")
def ada():
    try:
        from ada_assistant import ArbitrationDecisionAssistant
    except Exception as e:  # pragma: no cover
        pytest.skip(f"ADA no disponible: {e}")
    return ArbitrationDecisionAssistant()


def _e2e(ada, monkeypatch, verifier):
    from _ada_contract_helpers import StubLLM, grounded_answer
    monkeypatch.setenv("ADA_VERIFICATION_V4", "1")
    monkeypatch.setattr(D, "FIX_ALL_VISIBLE_FIELDS", True)

    def analysis(prompt, delivered):
        obj = json.loads(grounded_answer(prompt, delivered[:1]))
        obj["summary"] = (obj.get("summary") or "") + " Esta frase no tiene respaldo alguno en los pasajes."
        return json.dumps(obj, ensure_ascii=False)
    ada._call_llm = StubLLM(analysis=analysis)
    monkeypatch.setattr(ada, "_call_verifier", verifier)
    return ada.analyze_situation("How many seconds of osaekomi are needed for ippon?", top_k=5)


def _last_sentence_unsupported(prompt):
    sents = prompt.split("ANSWER SENTENCES:")[1].strip().split("\n")
    obj = {"quotes": [], "exceptions": [], "answers_question": True,
           "sentences": [{"n": i, "supported": "no tiene respaldo" not in s, "unsupported": "x"}
                         for i, s in enumerate(sents, 1)]}
    return json.dumps(obj), {"prompt_tokens": 500, "completion_tokens": 40}, "stub-verifier"


def test_e2e_v4_prunes_instead_of_abstaining_and_counts_tokens_once(ada, monkeypatch):
    res = _e2e(ada, monkeypatch, _last_sentence_unsupported)
    if res["status"] != "SUCCESS":
        pytest.skip(f"la respuesta mecanica de prueba no es verificable en este modo de recuperacion: {res.get('mode')}")
    v = res["decision_integrity"]["verification"]
    assert any("no tiene respaldo" in r["sentence"] for r in v["removed"])
    assert "no tiene respaldo" not in json.dumps(res["structured_answer"], ensure_ascii=False)
    assert res["token_usage"]["verification_tokens"]["prompt_tokens"] == 500
    assert res["response_origin"]["verificacion"]["retirado"] >= 1


def test_e2e_v4_verifier_down_uses_reduced_mode(ada, monkeypatch):
    def down(prompt):
        raise RuntimeError("timeout")
    res = _e2e(ada, monkeypatch, down)
    v = (res.get("decision_integrity") or {}).get("verification") or {}
    assert v.get("mode") in ("REDUCIDA", "SIN_CONTENIDO")
    assert res["status"] in ("SUCCESS", "ABSTAIN")

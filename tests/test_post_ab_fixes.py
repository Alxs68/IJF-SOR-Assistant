"""Correcciones posteriores a la evaluacion A/B: normalizacion tipografica (DIG-03), DIG-08 entre idiomas,
evaluador con la normalizacion del DIG y comprobador de cuota. Desactivadas por defecto (DIG_V3=1)."""
import json
import os
import sys
from contextlib import contextmanager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "scripts")]
import decision_integrity as D  # noqa: E402

PS = json.load(open(os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json"), encoding="utf-8"))
BY = {p["passage_id"]: p for p in PS}
GATE = D.DecisionIntegrityGate(PS)
ALL = ("FIX_PERTINENCE_HEADING", "FIX_HYPHEN_TERMS", "FIX_DIG08_INSTRUCTIONS", "FIX_LINEBREAK_HYPHEN",
       "FIX_UNICODE_TYPO", "FIX_DIG08_CROSSLANG")


@contextmanager
def flags(**on):
    old = {f: getattr(D, f) for f in ALL}
    try:
        for f in ALL:
            setattr(D, f, on.get(f, False))
        yield
    finally:
        for f, v in old.items():
            setattr(D, f, v)


def P(pid):
    return dict(BY[pid], page=BY[pid]["pdf_page_index"])


VET = "SOR-2026-08-P105-S130"
VET_Q = "There is no random weigh\u2011in for veterans."          # guion no separable (Groq)


def test_typographic_variants_located_only_with_fix():
    variants = [VET_Q, "There is no random weigh\u2010in for veterans.", "There is no random weigh\u2013in for veterans.",
                "There\u00a0is no\u2009random weigh-in\u202ffor veterans.", "There is no ran\u00addom weigh-in for veterans.",
                "There is no random\nweigh-in for\u200b veterans."]
    for q in variants:
        with flags():
            base = GATE._locate(D.norm(q), P(VET))
        with flags(FIX_UNICODE_TYPO=True):
            new = GATE._locate(D.norm(q), P(VET))
        assert new is not None, repr(q)
        if any(c in q for c in "\u2010\u2011\u2013\u00ad\u200b"):  # los espacios finos ya se colapsaban antes
            assert base is None, repr(q)


def test_typographic_fix_does_not_accept_different_text():
    for q in ["There is no random weigh\u2011in for juniors.", "There is a random weigh\u2011in for veterans.",
              "There is no random weigh\u2014in for veterans.", "There is no random weighin for veterans."]:
        with flags(FIX_UNICODE_TYPO=True, FIX_LINEBREAK_HYPHEN=True):
            assert GATE._locate(D.norm(q), P(VET)) is None, repr(q)


def test_typographic_fix_keeps_original_text_offsets():
    with flags(FIX_UNICODE_TYPO=True):
        loc = GATE._locate(D.norm(VET_Q), P(VET))
    raw = BY[VET]["text_original"][loc["raw_start"]:loc["raw_end"]]
    assert raw.startswith("There is no random weigh") and raw.rstrip(".").endswith("veterans")


def _answer(summary, pid, quote, extended=""):
    return json.dumps({"answerability": "RESPALDADA", "evidence_conflicts": [], "summary": f"{summary} [{pid}]",
                       "normative_basis": f"[{pid}]", "conditions_and_exceptions": "", "extended_analysis": extended,
                       "limitations": "", "citations": [pid],
                       "evidence_quotes": [{"passage_id": pid, "quote": quote, "supports": "x"}]}, ensure_ascii=False)


REF = "SOR-2026-08-P103-S125"
REF_Q = "The weight categories are the same as those for senior men and women."


def _dig08(summary, supp, extended=""):
    return GATE.evaluate(_answer(summary, REF, REF_Q, extended), "Que categorias de peso se usan en veteranos?",
                         "Which weight categories are used in veterans competitions?", [P(REF)], [], supp)


def test_crosslang_translated_sor_concept_not_shadow_footprint():
    supp = ["En las competiciones de veteranos se aplican las categorias generales."]
    prim_has = "competition" in D.norm(BY[REF]["text_original"]) or any(
        "competition" in D.norm(p["text_original"]) for p in [BY[REF]])
    with flags(FIX_DIG08_INSTRUCTIONS=True):
        base = _dig08("Las categorias de peso en las competiciones de veteranos son las mismas que senior.", supp)
    with flags(FIX_DIG08_INSTRUCTIONS=True, FIX_DIG08_CROSSLANG=True):
        new = _dig08("Las categorias de peso en las competiciones de veteranos son las mismas que senior.", supp)
    if prim_has:
        assert any(c.startswith("DIG-08") for c in base["failed_checks"])
        assert not any(c.startswith("DIG-08") for c in new["failed_checks"]), new["checks"]


def test_crosslang_real_shadow_leaks_still_detected():
    supp = ["Congelacion decidida en Ulaanbaatar: las listas quedaron locked; plazo de 73 dias."]
    with flags(FIX_DIG08_INSTRUCTIONS=True, FIX_DIG08_CROSSLANG=True):
        for extra in ["La congelacion se decidio en Ulaanbaatar.", "Las listas quedaron locked.", "El plazo es de 73 dias."]:
            res = _dig08("Son las mismas que senior.", supp, extended=extra)
            assert any(c.startswith("DIG-08") for c in res["failed_checks"]), extra


def test_crosslang_not_applied_to_english_answers():
    supp = ["The sidecar guideline mentions chaperones for travelling delegations."]
    with flags(FIX_DIG08_INSTRUCTIONS=True, FIX_DIG08_CROSSLANG=True):
        res = _dig08("They are the same as senior; chaperones are required for delegations.", supp)
    assert any(c.startswith("DIG-08") for c in res["failed_checks"])


def test_concept_in_primary():
    assert D.concept_in_primary("competiciones", {"competitions"})
    assert D.concept_in_primary("olimpico", {"olympic"})
    assert not D.concept_in_primary("congelacion", {"competition", "freeze"})
    assert not D.concept_in_primary("ulaanbaatar", {"competition"})


def test_evaluator_uses_dig_normalization():
    import eval_llm_shadow as E
    page = BY["SOR-2026-08-P198-S208"]["text_original"]
    anchor = {"snippet": "A minor injury may be treated by the athlete himself."}
    q = ("A minor injury may be treated by the athlete himself. For example, in the case of a dislocated finger or "
         "toe, the referee shall stop the contest (by calling \u201cMate!\u201d or \u201cSono-mama!\u201d)")
    with flags():
        assert not E.span_hit(page, q, anchor)          # corte de linea "Sono-\\nmama" sin la correccion
    with flags(FIX_LINEBREAK_HYPHEN=True, FIX_UNICODE_TYPO=True):
        assert E.span_hit(page, q, anchor)
        assert not E.span_hit(page, q.replace("athlete himself", "doctor himself"), anchor)
        assert not E.span_hit(page, "The same finger or toe is allowed to be reset on two (2) occasions.", anchor)


def test_quota_checker_reports_effective_model(monkeypatch=None):
    import llm_provider as L
    import check_llm_quota as Q
    old = {k: os.environ.get(k) for k in ("GROQ_MODEL", "GROQ_API_KEY")}
    try:
        os.environ["GROQ_MODEL"] = "llama-3.3-70b-versatile"
        os.environ["GROQ_API_KEY"] = "test-key"
        mgr = L.MultiProviderLLMManager()

        def boom(self, prompt, system_prompt=None, json_mode=False, json_schema=False):
            raise L.LLMProviderError("x", error_type="QUOTA", status_code=429, retry_after=20)
        orig_gen, orig_post = L.GroqClient.generate, Q._post
        L.GroqClient.generate, Q._post = boom, (lambda *a, **k: (429, {"x-ratelimit-limit-tokens": "8000"}, {}))
        try:
            info = Q.probe(mgr, "Groq", 8500)
        finally:
            L.GroqClient.generate, Q._post = orig_gen, orig_post
        assert info["modelo_efectivo"] == L.GroqClient.DEFAULT_MODEL and info["modelo_entorno_ignorado"]
        assert info["ok"] is False and info["error_tipo"] == "QUOTA" and info["http"] == 429
        assert info["capacidad_por_minuto"]["alcanza_para_un_analisis"] is False
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

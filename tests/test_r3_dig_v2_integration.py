"""Integracion experimental R3 (preferencia por ambito) y DIG con normalizacion de cifras v2.

Ambos estan DESACTIVADOS por defecto; estos tests verifican (1) que por defecto nada cambia, (2) que la
implementacion integrada es equivalente a la evaluada en la Fase 11 (src/experimental) y (3) que la
variante DIG sigue detectando cifras inventadas.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
CAPTURE = os.path.join(ROOT, "data", "eval", "fase11", "llm_dev_f11_capture.json")


# ------------------------------------------------------------------ flags por defecto
def test_flags_are_off_by_default():
    from src.scope_preference import flag_enabled
    if os.environ.get("RRE_ENABLE_SCOPE_PREFERENCE"):
        pytest.skip("entorno con R3 activado")
    assert flag_enabled() is False
    import decision_integrity as D
    if not os.environ.get("DIG_NUMBER_NORMALIZATION"):
        assert D.NUMBER_NORMALIZATION == "v1" and D.DIG_VERSION == "DIG-1.3" and D.numbers_in is D.numbers_in_v1


# ------------------------------------------------------------------ R3: equivalencia con lo evaluado
def test_scope_preference_equals_experimental_r3():
    from experimental.retrieval_variants import ScopeModel, UnitCorpus, scope_rerank
    from src.scope_preference import ScopePreference
    uc = UnitCorpus()
    exp = ScopeModel(uc)
    prod = ScopePreference(beta=0.2)
    assert prod.indicator == exp.indicator and prod.indicator
    for pg in (1, 19, 75, 103, 105, 110, 113, 152, 202, 250):
        assert prod.part_of_page(pg) == uc.part_of_page(pg), pg
    pages = {f"P{i}": pg for i, pg in enumerate([33, 112, 96, 105, 152, 110, 79, 75, 202, 113])}
    ranking = list(pages)
    for q in ("dimensions competition area World Kata Championships", "random weighing veterans", "duration of a contest"):
        parts = prod.query_parts(q)
        assert parts == exp.query_parts(q)
        for beta in (0.2, 0.5):
            got = prod.rerank(ranking, parts, pages.get, beta=beta)
            want = scope_rerank(ranking, parts, lambda p: uc.part_of_page(pages[p]), beta=beta)
            assert got == want, (q, beta)


def test_scope_preference_is_data_derived_without_hardcodes():
    src = open(os.path.join(ROOT, "src", "scope_preference.py"), encoding="utf-8").read().lower()
    import re
    assert not re.search(r"sor-2026-08-p\d+", src)
    for w in ("veteran", "kata", "cadet", "judogi", "weigh-in"):
        assert w not in src, w


def test_rrE_scope_preference_off_equals_baseline_and_on_only_reorders():
    from src.rre_engine import ReasoningRetrievalEngine
    off = ReasoningRetrievalEngine(enable_scope_preference=False)
    on = ReasoningRetrievalEngine(enable_scope_preference=True)
    q_none = "How many minutes does a senior contest last?"
    a, b = off.retrieve(q_none, top_k=5), on.retrieve(q_none, top_k=5)
    assert [e["passage_id"] for e in a["evidence"]] == [e["passage_id"] for e in b["evidence"]]
    assert b["scope_preference"]["applied"] is False and a.get("scope_preference") is None
    q = "U18 kata pair green belt"
    ra, rb = off.retrieve(q, top_k=5, domain_query=q), on.retrieve(q, top_k=5, domain_query=q)
    assert rb["scope_preference"]["applied"] is True
    # reordena dentro del conjunto de candidatos; no inventa pasajes ni cambia el estado
    assert ra["status"] == rb["status"] == "SUCCESS"
    pool = [e["passage_id"] for e in off.retrieve(q, top_k=25, domain_query=q)["evidence"]]
    assert set(e["passage_id"] for e in rb["evidence"]) <= set(pool)


def test_rre_ood_unchanged_with_scope_preference():
    from src.rre_engine import ReasoningRetrievalEngine
    on = ReasoningRetrievalEngine(enable_scope_preference=True)
    off = ReasoningRetrievalEngine(enable_scope_preference=False)
    for q in ("How are rounds scored in professional boxing?", "receta de paella valenciana"):
        assert on.retrieve(q, top_k=5)["status"] == off.retrieve(q, top_k=5)["status"]


# ------------------------------------------------------------------ DIG v2: equivalencia y adversarial
TEXTS = [
    "page 79 of the SOR (SOR‑2026‑08‑P079‑S093). The rule",
    "Federation (Edición 14 de agosto de 2026), Artículo",
    "(SOR 2026), Section 6.4.2 [SOR-2026-08-P082-S100]. 1. Los atletas deben\n2. La tolerancia",
    "and 6.3 Random Weigh-in (Art. 6.3, p. 79).",
    "8.10 Awarding Ceremonies (Art. 8.10, Pág. 98) 20% to their coach",
    "6.3 Kilograms are permitted.", "Registrations close on 20 August 2026.",
    "The rest period is: 10. Athletes must wait.", "\n1. Athletes have 37 minutes.\n2. The rule applies.",
    "the contest lasts 4 minutes. 2 reserves", "duration is 2.5 minutes for M7", "tolerance of 0.2 kg",
]


def test_dig_v2_equals_experimental_variant():
    import decision_integrity as D
    from experimental.dig_variants import numbers_in_v2 as exp_v2
    for t in TEXTS:
        assert D.numbers_in_v2(t) == exp_v2(t), t


def test_dig_v2_keeps_invented_figures():
    import decision_integrity as D
    assert "6.3" in D.numbers_in_v2("6.3 Kilograms are permitted.")
    assert "20" in D.numbers_in_v2("Registrations close on 20 August 2026.")
    assert "10" in D.numbers_in_v2("The rest period is: 10. Athletes must wait.")
    assert "37" in D.numbers_in_v2("\n1. Athletes have 37 minutes.\n2. The rule applies.")
    assert D.numbers_in_v2("Article 6.3 Random Weigh-in (SOR‑2026‑08‑P079‑S093)") == set()


@pytest.mark.skipif(not os.path.exists(CAPTURE), reason="sin captura de la Fase 11")
def test_dig_v2_decisions_equal_experimental_replay_on_captured_inputs(monkeypatch):
    import decision_integrity as D
    from experimental.dig_variants import dig_variant
    ps = json.load(open(os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json"), encoding="utf-8"))
    for f in ("FIX_PERTINENCE_HEADING", "FIX_HYPHEN_TERMS", "FIX_DIG08_INSTRUCTIONS"):
        monkeypatch.setattr(D, f, False)  # las grabaciones son anteriores a las correcciones v3
    gate = D.DecisionIntegrityGate(ps)
    rows = [r for run in json.load(open(CAPTURE, encoding="utf-8"))["per_run"] for r in run if r.get("dig_input")]
    assert rows
    for r in rows:
        c = r["dig_input"]
        args = (c["answer"], c["query"], c["search_query_en"], c["evidence"], c["related"], c["supplementary_texts"])
        with dig_variant():
            exp = gate.evaluate(*args)
        monkeypatch.setattr(D, "numbers_in", D.numbers_in_v2)
        prod = gate.evaluate(*args)
        monkeypatch.setattr(D, "numbers_in", D.numbers_in_v1)
        base = gate.evaluate(*args)
        assert (prod["decision"], sorted(prod["failed_checks"])) == (exp["decision"], sorted(exp["failed_checks"])), r["id"]
        assert (base["decision"], sorted(base["failed_checks"])) == (c["result"]["decision"], sorted(c["result"]["failed_checks"])), r["id"]

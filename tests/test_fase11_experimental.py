"""Fase 11 - recuperador experimental, diagnostico de abstenciones y aislamiento."""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, "src"), os.path.join(ROOT, "scripts")]


class FakeRRE:
    """Canales simulados; solo expone los metodos que usa el recuperador experimental."""

    def __init__(self, sparse, dense, history=()):
        self._s, self._d, self._h = sparse, dense, set(history)
        self.calls = []

    def _sparse_search(self, q, top_k=20):
        self.calls.append("sparse")
        return self._s[:top_k]

    def _dense_search(self, q, top_k=20):
        self.calls.append("dense")
        return self._d[:top_k]

    def _query_requests_document_history(self, q):
        return False

    def _is_version_history_passage(self, pid):
        return pid in self._h


def test_clean_fusion_matches_production_rrf_formula():
    from experimental.scope_retriever import clean_fusion
    rre = FakeRRE(sparse=[("A", 0.5), ("B", 0.3), ("H", 0.9), ("C", 0.04)], dense=[("B", 0.6), ("D", 0.5)], history={"H"})
    out = clean_fusion(rre, "q")
    # B en ambos canales -> bonificacion multicanal; C filtrado (< 0.05); H excluido (historial)
    assert out["ranked"][0] == "B" and "C" not in out["ranked"] and "H" not in out["ranked"]
    expected_b = (1.2 / 62 + 1.0 / 61 + 0.035) * 1.35
    assert abs(out["scores"]["B"] - round(expected_b, 5)) < 1e-6
    assert out["experimental_label"] == "EXPERIMENTAL_NO_DECISORIO"


def test_channel_ranks():
    from experimental.scope_retriever import channel_ranks
    rre = FakeRRE(sparse=[("A", 0.5), ("B", 0.3)], dense=[("D", 0.5), ("B", 0.4)])
    assert channel_ranks(rre, "q", {"B"})["sparse"] == 2 and channel_ranks(rre, "q", {"B"})["dense"] == 2
    assert channel_ranks(rre, "q", {"Z"}) ["sparse"] is None


def test_scope_retriever_has_no_hardcoded_passages_or_keywords():
    src = open(os.path.join(ROOT, "src", "experimental", "scope_retriever.py"), encoding="utf-8").read()
    assert not re.search(r"SOR-2026-08-P\d+", src)
    assert not re.search(r"query\.lower\(\)|any\(w in", src)


def test_productive_code_does_not_use_phase11_components():
    for fn in os.listdir(os.path.join(ROOT, "src")):
        if fn.endswith(".py"):
            s = open(os.path.join(ROOT, "src", fn), encoding="utf-8").read()
            assert "scope_retriever" not in s and "clean_fusion" not in s, fn


def _item():
    return {"text": "How far back does the referee stand?", "split": "dev",
            "minimum_evidence": [{"page": 153, "snippet": "2 m back", "passage_ids": ["P1"]}],
            "exceptions_to_preserve": []}


def test_dig06_number_present_in_delivered_passage_is_potential_fn():
    import diag_abstentions_f11 as D
    row = {"bundle_detail": [{"passage_id": "P1"}], "translation": "", "quotes_hit_evidence": True}
    cls, sub, _ = D.classify_check("DIG-06_CIFRAS_RESPALDADAS", "cifras_sin_respaldo=['10']", row, _item(),
                                   {"P1": "Any athlete is entitled to 10 minutes rest."})
    assert (cls, sub) == (D.FN, "CIFRA_EN_PASAJE_NO_CITADA")
    cls, sub, _ = D.classify_check("DIG-06_CIFRAS_RESPALDADAS", "cifras_sin_respaldo=['37']", row, _item(), {"P1": "no figure"})
    assert (cls, sub) == (D.BC, "CIFRA_NO_RESPALDADA")
    cls, sub, _ = D.classify_check("DIG-03_CITA_LITERAL", "no_literales=['x']", row, _item(), {})
    assert cls == D.BC


def test_dig05_depends_on_quote_of_expected_anchor():
    import diag_abstentions_f11 as D
    det = "terminos_distintivos_consulta=['refer'] pasajes_citados_sin_cita_pertinente=['P1']; heuristica"
    assert D.classify_check("DIG-05_PERTINENCIA_MINIMA", det, {"quotes_hit_evidence": True}, _item(), {})[0] == D.FN
    assert D.classify_check("DIG-05_PERTINENCIA_MINIMA", det, {"quotes_hit_evidence": False}, _item(), {})[0] == D.BC


def test_sealed_cases_are_marked_review_only():
    import diag_abstentions_f11 as D
    it = dict(_item(), id="X", split="test_sealed", category="DIRECTA")
    rep = {"per_run": [[{"id": "X", "expected_behavior": "RESPONDER", "status": "ABSTAIN", "llm_text_present": True,
                         "language": "en", "category": "DIRECTA", "dig_failed_checks": ["DIG-06_CIFRAS_RESPALDADAS"],
                         "outcome": "ABSTENCION_CON_CITA_CORRECTA"}]]}
    rows = D.case_rows(rep, "F10_test", {"X": it}, {}, detailed=False)
    assert rows[0]["uso"] == "SOLO_REVISION_HUMANA" and rows[0]["auto_classification"] == D.RV


def test_llm_shadow_row_stores_failed_check_details():
    import eval_llm_shadow as L
    from decision_integrity import numbers_in
    it = dict(_item(), id="X", category="DIRECTA", language="en", wrong_scope_distractors=[], mandatory_cross_refs=[],
              auto_labels={"expected_behavior": "RESPONDER"})
    out = {"status": "ABSTAIN", "evidence": [{"passage_id": "P1", "pdf_page_index": 153}], "related_passages": [],
           "decision_integrity": {"decision": "ABSTENER", "failed_checks": ["DIG-06_CIFRAS_RESPALDADAS"],
                                  "checks": [{"code": "DIG-06_CIFRAS_RESPALDADAS", "passed": False, "detail": "cifras_sin_respaldo=['3']"},
                                             {"code": "DIG-01_SUFICIENCIA_DECLARADA", "passed": True, "detail": ""}]}}
    calls = [{"is_analysis": False, "text": "translated q"},
             {"is_analysis": True, "text": json.dumps({"answerability": "RESPALDADA", "evidence_quotes": []}), "meta": {}}]
    r = L.score_run(it, out, calls, {153: "the referee shall be 2 m back"}, numbers_in)
    assert r["dig_checks"] == [{"code": "DIG-06_CIFRAS_RESPALDADAS", "detail": "cifras_sin_respaldo=['3']"}]
    assert r["translation"] == "translated q" and r["llm_json"]["answerability"] == "RESPALDADA"
    assert r["bundle_detail"][0]["lane"] == "evidence"


def test_dig_variant_removes_only_formatting_artifacts():
    from decision_integrity import numbers_in
    from experimental.dig_variants import numbers_in_v2
    assert numbers_in_v2("page 79 of the SOR (SOR‑2026‑08‑P079‑S093). The rule") == set()
    assert numbers_in_v2("Federation (Edición 14 de agosto de 2026), Artículo") == set()
    assert numbers_in_v2("(SOR 2026), Section 6.4.2 [SOR-2026-08-P082-S100]. 1. Los atletas deben\n2. La tolerancia") == set()
    assert numbers_in_v2("and 6.3 Random Weigh-in (Art. 6.3, p. 79).") == set()
    # las cifras normativas se conservan
    for t in ("the contest lasts 4 minutes. 2 reserves", "duration is 2.5 minutes for M7", "tolerance of 0.2 kg",
              "a maximum of 12 athletes can be entered", "draw at 14:00 local time"):
        assert numbers_in_v2(t) == numbers_in(t), t


def test_benchmark_equivalence_groups_identical_page_text():
    from experimental.benchmark_access import equivalence_map, expand
    eq = equivalence_map()
    assert all(len({p.split("-S")[0] for p in g}) == 1 for g in eq.values())  # misma pagina
    assert any(len(g) > 1 for g in eq.values())
    assert expand({"NO-EXISTE"}) == {"NO-EXISTE"}


def test_dig_variant_keeps_figures_that_only_look_like_formatting():
    from decision_integrity import numbers_in
    from experimental.dig_variants import numbers_in_v2
    assert "6.3" in numbers_in_v2("6.3 Kilograms are permitted.")          # etiqueta real, titulo distinto
    assert "20" in numbers_in_v2("Registrations close on 20 August 2026.")  # fecha distinta de la edicion
    assert "10" in numbers_in_v2("The rest period is: 10. Athletes must wait.")  # numero aislado, no lista
    assert "37" in numbers_in_v2("\n1. Athletes have 37 minutes.\n2. The rule applies.")
    assert numbers_in_v2("37.5 Kilograms are permitted") == numbers_in("37.5 Kilograms are permitted")


def test_dig_variant_context_restores_production_function():
    import decision_integrity as D
    from experimental.dig_variants import dig_variant, numbers_in_v2
    orig = D.numbers_in
    with dig_variant():
        assert D.numbers_in is numbers_in_v2
    assert D.numbers_in is orig
    try:
        with dig_variant():
            raise RuntimeError("x")
    except RuntimeError:
        pass
    assert D.numbers_in is orig


def test_retrieval_variants_are_generic_and_data_derived():
    src = open(os.path.join(ROOT, "src", "experimental", "retrieval_variants.py"), encoding="utf-8").read().lower()
    assert not re.search(r"sor-2026-08-p\d+", src)
    for w in ("veteran", "kata", "cadet", "mixed team", "judogi", "weigh-in"):
        assert w not in src, w
    from experimental.retrieval_variants import ScopeModel, UnitCorpus, rrf, scope_rerank
    from experimental.ambiguity_detector import stems
    uc = UnitCorpus()
    sm = ScopeModel(uc)
    title_stems = {t for p in uc.part_title if p for t in stems(p)}
    assert sm.indicator and set(sm.indicator) <= title_stems
    assert rrf(["a", "b"], ["b", "c"])[0] == "b"
    assert scope_rerank(["x", "y"], set(), lambda p: None) == ["x", "y"]
    assert scope_rerank(["x", "y"], {"P"}, lambda p: "P" if p == "y" else None, beta=0.5) == ["y", "x"]


def test_crossref_lane_is_separate_and_labelled():
    from experimental.retrieval_variants import UnitCorpus, crossref_lane
    uc = UnitCorpus()
    lane = crossref_lane(["SOR-2026-08-P075-S086"], uc, lambda p: 75)
    assert lane and all(x["experimental_label"] == "EXPERIMENTAL_NO_DECISORIO" and x["passage_id"] != "SOR-2026-08-P075-S086" for x in lane)

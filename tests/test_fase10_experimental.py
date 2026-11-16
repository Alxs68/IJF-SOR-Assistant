"""Fase 10 - benchmark_v2, componentes experimentales (NLI shadow, detector de ambiguedad,
evaluador LLM shadow) y su AISLAMIENTO respecto de la ruta productiva."""
import csv
import hashlib
import importlib
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, "src"), os.path.join(ROOT, "scripts")]
BENCH = os.path.join(ROOT, "data", "eval", "benchmark_v2")
CORPUS = os.path.join(ROOT, "data", "processed", "rebuild_2026_08_corrected", "passages_candidate.json")
CORPUS_SHA = "7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b"


def _records():
    with open(os.path.join(BENCH, "benchmark_v2.jsonl"), encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


# ------------------------------------------------------------------ benchmark_v2
def test_benchmark_v2_reproducible():
    import build_benchmark_v2
    assert build_benchmark_v2.main(["--check"]) == 0


def test_benchmark_v2_labels_anchors_and_review_state():
    recs = _records()
    man = json.load(open(os.path.join(BENCH, "manifest.json"), encoding="utf-8"))
    assert man["build_errors"] == []
    assert len(recs) == man["counts"]["total"] >= 100
    for r in recs:
        assert r["auto_labels"]["all_anchors_verified"], r["id"]
        assert r["human_labels"] is None and r["review_status"] == "PENDING_EXPERT_REVIEW"
        assert r["certified_by_referees"] is False
        assert r["auto_labels"]["justification"]
        assert r["max_jaccard_vs_benchmark_v1"] < 0.7
        if r["category"] == "AMBITO_DISTRACTOR":
            assert r["wrong_scope_distractors"], r["id"]
        if r["category"] == "INSUFICIENTE":
            assert r["absence_probe"]["hits"] == 0, r["id"]
        if r["category"] in ("AMBIGUA", "INCOMPLETA"):
            assert r["ambiguity"]["clarification_proposal"]
    cats = {r["category"] for r in recs}
    assert {"AMBITO_DISTRACTOR", "EXCEPCION", "REFERENCIA_CRUZADA", "MULTI_ARTICULO", "DISTINCION_CATEGORIA",
            "INSUFICIENTE", "OOD", "AMBIGUA", "INCOMPLETA", "MULTILINGUE"} <= cats


def test_benchmark_v2_split_by_semantic_group():
    groups = {}
    for r in _records():
        groups.setdefault(r["semantic_group"], set()).add(r["split"])
    assert all(len(s) == 1 for s in groups.values())


def test_test_sealed_requires_explicit_flag():
    from experimental.benchmark_access import SealedSplitError, load_items
    with pytest.raises(SealedSplitError):
        load_items("test_sealed")
    with pytest.raises(SealedSplitError):
        load_items("all")
    items, meta = load_items("test_sealed", allow_test_sealed=True)
    assert meta["test_sealed_hash_ok"] and items and all(i["split"] == "test_sealed" for i in items)
    dev, _ = load_items("dev")
    assert all(i["split"] == "dev" for i in dev)


def test_eval_scripts_refuse_sealed_without_flag():
    import eval_ambiguity_detector
    import eval_nli_shadow
    assert eval_nli_shadow.main(["--split", "all", "--models", "lexical"]) == 2
    assert eval_ambiguity_detector.main(["--split", "test_sealed", "--sweep", "--allow-test-sealed", "--projection", "none"]) == 2


def test_nli_pairs_reproducible_and_split_inherited():
    import build_nli_shadow_pairs
    assert build_nli_shadow_pairs.main(["--check"]) == 0
    split = {r["id"]: r["split"] for r in _records()}
    with open(os.path.join(ROOT, "data", "eval", "nli_shadow_v1", "pairs.jsonl"), encoding="utf-8") as fh:
        pairs = [json.loads(l) for l in fh if l.strip()]
    assert pairs and all(p["split"] == split[p["item_id"]] for p in pairs)
    assert {p["pair_type"] for p in pairs} == {"SUPPORT", "SCOPE_PREMISE", "SCOPE_CLAIM", "NUMBER"}


def test_review_merge_never_touches_original(tmp_path):
    import merge_benchmark_v2_review as M
    src = os.path.join(BENCH, "benchmark_v2.jsonl")
    before = hashlib.sha256(open(src, "rb").read()).hexdigest()
    recs = _records()
    a, b = recs[0]["id"], recs[1]["id"]
    f1, f2 = tmp_path / "r1.csv", tmp_path / "r2.csv"
    cols = M.__dict__.get("REVIEW_COLS") or ["id", "reviewer", "review_date", "verdict", "human_expected_behavior",
                                             "human_expected_articles", "notes"]
    for path, rows in ((f1, [{"id": a, "reviewer": "R1", "verdict": "ACEPTA"},
                             {"id": b, "reviewer": "R1", "verdict": "CORRIGE", "human_expected_behavior": "ABSTENER_INSUFICIENCIA"}]),
                       (f2, [{"id": b, "reviewer": "R2", "verdict": "ACEPTA"}, {"id": "NO-EXISTE", "reviewer": "R2", "verdict": "ACEPTA"}])):
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow(r)
    rc = M.main([str(f1), str(f2), "--out-dir", str(tmp_path / "out")])
    assert rc == 1  # id desconocido registrado como error
    merged = {json.loads(l)["id"]: json.loads(l) for l in open(tmp_path / "out" / "benchmark_v2_reviewed.jsonl", encoding="utf-8")}
    assert merged[a]["review_status"] == "EXPERT_REVIEWED" and merged[a]["human_labels"]["reviewers"] == ["R1"]
    assert merged[b]["review_status"] == "REVIEW_CONFLICT" and merged[b]["human_labels"] is None
    assert merged[a]["auto_labels"] == recs[0]["auto_labels"]
    assert hashlib.sha256(open(src, "rb").read()).hexdigest() == before


# ------------------------------------------------------------------ aislamiento
PRODUCTIVE = ["ada_assistant.py", "rre_engine.py", "decision_integrity.py", "llm_provider.py", "response_structurer.py",
              "multisource_retriever.py", "normative_validator.py", "mcp_server.py"]


def test_productive_modules_do_not_reference_experimental():
    for fn in os.listdir(os.path.join(ROOT, "src")):
        if fn.endswith(".py"):
            src = open(os.path.join(ROOT, "src", fn), encoding="utf-8").read()
            # importaciones o referencias al paquete experimental (no la palabra en comentarios)
            assert not re.search(r"^\s*(from|import)\s+experimental\b|\bexperimental\.|nli_shadow|ambiguity_detector|"
                                 r"NLIShadowEvaluator|AmbiguityDetector", src, re.M), fn
    app = os.path.join(ROOT, "app.py")
    if os.path.exists(app):
        assert not re.search(r"^\s*(from|import)\s+experimental\b|nli_shadow|ambiguity_detector",
                             open(app, encoding="utf-8").read(), re.M)


def test_importing_experimental_does_not_patch_ada():
    ada_mod = importlib.import_module("ada_assistant")
    dig_mod = importlib.import_module("decision_integrity")
    before = (ada_mod.ArbitrationDecisionAssistant.analyze_situation, ada_mod.ArbitrationDecisionAssistant._call_llm,
              dig_mod.DecisionIntegrityGate.evaluate)
    importlib.import_module("experimental.nli_shadow")
    importlib.import_module("experimental.ambiguity_detector")
    after = (ada_mod.ArbitrationDecisionAssistant.analyze_situation, ada_mod.ArbitrationDecisionAssistant._call_llm,
             dig_mod.DecisionIntegrityGate.evaluate)
    assert before == after


def test_corpus_hash_unchanged():
    assert hashlib.sha256(open(CORPUS, "rb").read()).hexdigest() == CORPUS_SHA


# ------------------------------------------------------------------ NLI shadow
def _fake(p_ent, p_con=0.0):
    def scorer(premise, hypothesis):
        return {"entailment": p_ent, "neutral": 1 - p_ent - p_con, "contradiction": p_con, "truncated": False}
    return scorer


def test_nli_output_contract_is_non_decisional():
    from experimental import EXPERIMENTAL_LABEL
    from experimental.nli_shadow import NLIShadowEvaluator
    ev = NLIShadowEvaluator(scorer=_fake(0.9))
    rep = ev.evaluate("q", "The contest lasts four minutes for seniors. [SOR-2026-08-P152-S001]", ["Seniors: 4 minutes"])
    assert rep["experimental_label"] == EXPERIMENTAL_LABEL and rep["decision_effect"] == "NINGUNO"
    assert rep["result"] == "SOPORTE_PROBABLE" and "entailment normativo" in rep["disclaimer"]
    forbidden = {"status", "citations", "decision", "SUCCESS", "PERMITIR", "authorized"}
    assert not forbidden & set(rep)
    assert rep["claims"] and "SOR-2026" not in rep["claims"][0]["claim"]
    assert NLIShadowEvaluator(scorer=_fake(0.2)).evaluate("q", "The contest lasts four minutes.", ["x y z"])["result"] == "SOPORTE_NO_ESTABLECIDO"
    assert NLIShadowEvaluator(scorer=_fake(0.1, 0.8)).evaluate("q", "The contest lasts four minutes.", ["x"])["result"] == "CONTRADICCION_PROBABLE"


def test_nli_abstains_without_evidence_or_model():
    from experimental.nli_shadow import NLIShadowEvaluator
    assert NLIShadowEvaluator(scorer=_fake(0.9)).evaluate("q", "A claim with enough words.", [])["abstention_reason"] == "SIN_EVIDENCIA_CITADA"
    assert NLIShadowEvaluator(scorer=_fake(0.9)).evaluate("q", "", ["e"])["abstention_reason"] == "SIN_AFIRMACIONES_EVALUABLES"
    rep = NLIShadowEvaluator("modelo/inexistente-fase10").evaluate("q", "A claim with enough words here.", ["e"])
    assert rep["abstention_reason"] == "MODELO_NO_DISPONIBLE" and rep["result"] == "INDETERMINADO"


def test_nli_label_mapping():
    from experimental.nli_shadow import map_labels
    assert map_labels({0: "ENTAILMENT", 1: "NEUTRAL", 2: "CONTRADICTION"}) == {"entailment": 0, "neutral": 1, "contradiction": 2}
    assert map_labels({0: "contradiction", 1: "entailment", 2: "neutral"})["entailment"] == 1
    assert map_labels({0: "entailment", 1: "not_entailment"}) == {"entailment": 0, "neutral": 1, "contradiction": None}


# ------------------------------------------------------------------ detector de ambiguedad
def test_ambiguity_detector_has_no_question_specific_rules():
    src = open(os.path.join(ROOT, "src", "experimental", "ambiguity_detector.py"), encoding="utf-8").read().lower()
    for r in _records():
        words = re.findall(r"\w+", r["text"].lower())
        for i in range(len(words) - 3):
            frag = " ".join(words[i:i + 4])
            assert frag not in src, (r["id"], frag)
    assert not re.search(r"['\"](a1|b1|c1|e1)\.\d", src)
    for w in ("veteran", "kata", "cadet", "mixed team", "seeding"):
        assert w not in src, w


def test_ambiguity_detector_behaviour_and_contract():
    from experimental import EXPERIMENTAL_LABEL
    from experimental.ambiguity_detector import AmbiguityDetector
    d = AmbiguityDetector()
    r = d.analyze("Does it apply?")
    assert r["classification"] == "INCOMPLETA" and r["clarification_proposal"]
    assert r["experimental_label"] == EXPERIMENTAL_LABEL and r["decision_effect"] == "NINGUNO"
    assert d.analyze("How many entrances to the field of play are required?")["classification"] == "CLARA"
    for q in ("What colour of judogi must veteran athletes wear?", "Is there a random weigh-in at IJF mixed team events?"):
        assert d.analyze(q)["classification"] == "CLARA", q


# ------------------------------------------------------------------ LLM shadow
def test_llm_shadow_sanitizes_secrets(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "FAKE-SECRET-VALUE-123456")
    import eval_llm_shadow
    s = eval_llm_shadow.sanitize({"e": "https://x/y?key=AIzaSyAAAAAAAAAAAAAAAAAAAAAAAAAA&z=1 FAKE-SECRET-VALUE-123456",
                                  "l": ["Bearer abcdefghijklmnopqrstuvwxyz", "gsk_ABCDEFGHIJKLMNOPQRSTUVWX"]})
    blob = json.dumps(s)
    assert "FAKE-SECRET" not in blob and "AIzaSy" not in blob and "abcdefghijklmnop" not in blob and "gsk_ABC" not in blob


def test_llm_shadow_recorder_is_transparent():
    import eval_llm_shadow
    calls = []

    def real(prompt):
        calls.append(prompt)
        return "TEXT", {"successful_provider": "X"}
    rec = eval_llm_shadow.Recorder(real)
    assert rec("p ... evidence_quotes ...") == ("TEXT", {"successful_provider": "X"})
    assert calls == ["p ... evidence_quotes ..."] and rec.calls[0]["is_analysis"] and "p ..." not in json.dumps(rec.calls)

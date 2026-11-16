"""Fase 8 / Etapa 0 - pruebas estructurales del benchmark_v1 (sin LLM, sin motor)."""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_benchmark_v1 as bb  # noqa: E402

OUT = os.path.join(ROOT, bb.OUT_REL)


def _build():
    path = os.path.join(ROOT, bb.CORPUS_REL)
    if not os.path.exists(path):
        pytest.skip("corpus no disponible")
    with open(path, "rb") as fh:
        raw = fh.read()
    return bb.build(json.loads(raw.decode("utf-8")), raw)


def test_composition_and_required_fields():
    files, records, errors, counts = _build()
    assert errors == []
    assert counts["total"] == 150
    assert counts["by_category"] == {"AMBIGUA": 15, "EXCEPCION_CONDICION_REFERENCIA": 30, "FUERA_DE_DOMINIO": 15,
                                     "ORDINARIA_EN": 30, "ORDINARIA_ES": 60}
    req = {"id", "text", "language", "category", "difficulty", "expected_articles", "relevant_original_passages",
           "minimum_evidence", "mandatory_cross_refs", "exceptions_to_preserve", "answerable", "justification",
           "human_review_status", "split", "semantic_group"}
    for r in records:
        assert req <= set(r)


def test_no_referee_certification_claimed():
    _f, records, _e, _c = _build()
    assert all(r["human_review_status"] == "PENDIENTE_REVISION_ARBITRAL" and r["certified_by_referees"] is False for r in records)


def test_anchors_are_literal_or_pending():
    _f, records, _e, _c = _build()
    for r in records:
        for a in r["minimum_evidence"] + r["mandatory_cross_refs"] + r["exceptions_to_preserve"]:
            assert a["status"].startswith("VERIFICADA_TEXTUALMENTE") or r["annotation_status"] == "PENDIENTE"
            if a["status"] != "VERIFICADA_TEXTUALMENTE":
                assert r["annotation_status"] != "VERIFICADA_TEXTUALMENTE"
        if r["category"] == "AMBIGUA":
            assert r["expected_articles"] == "PENDIENTE"
        if r["category"] == "FUERA_DE_DOMINIO":
            assert r["answerable"] is False and r["minimum_evidence"] == []


def test_splits_disjoint_by_semantic_group():
    _f, records, _e, _c = _build()
    split_by_group = {}
    for r in records:
        assert split_by_group.setdefault(r["semantic_group"], r["split"]) == r["split"]
    assert {r["split"] for r in records} == {"dev", "validation", "test"}


def test_artifacts_reproducible():
    if not os.path.isdir(OUT):
        pytest.skip("benchmark no generado")
    files, *_ = _build()
    for name, content in files.items():
        with open(os.path.join(OUT, name), encoding="utf-8") as fh:
            assert fh.read().replace("\r\n", "\n") == content, name

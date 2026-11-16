"""Fase 8 / Etapa 1 - pruebas estructurales de la capa derivada article_units_v1.

Verifican propiedades estructurales (cobertura, trazabilidad, hashes, reconstruccion),
NO respuestas normativas. No usan LLM ni modifican el corpus.
"""
import copy
import hashlib
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_article_units as bau  # noqa: E402

HDR = "Sport and Organisation Rules of the International Judo Federation\npage - {}\n"
CORPUS = os.path.join(ROOT, bau.CORPUS_REL)


def mk(page, n, article, heading, text):
    return {"passage_id": f"T-P{page:03d}-S{n:03d}", "pdf_page_index": page, "article_id": article,
            "heading_path": [heading], "text_original": text, "text_sha256": bau.sha256(text),
            "source_sha256": "x", "source_version": "t"}


def run(passages):
    units, errors = bau.segment_corpus(passages)
    val = bau.validate(units, passages)
    assert [e for e in val if e["severity"] == "ERROR"] == [], val
    return units, errors


def by_type(units, t):
    return [u for u in units if u["unit_type"] == t]


def real_corpus():
    if not os.path.exists(CORPUS):
        pytest.skip("corpus no disponible")
    passages, raw = bau.load_corpus(ROOT)
    return passages, raw


# 1
def test_multi_article_page():
    t = HDR.format(10) + "1.1 Alpha Rule\nAlpha body.\n1.2 Beta Rule\nBeta body.\n"
    ps = [mk(10, 1, "1.1", "1.1 Alpha Rule", t), mk(10, 2, "1.2", "1.2 Beta Rule", t)]
    units, _ = run(ps)
    arts = by_type(units, "ARTICLE")
    assert [u["article_label"] for u in arts] == ["1.1", "1.2"]
    assert arts[0]["original_passage_ids"] == ["T-P010-S001"]
    assert arts[1]["original_passage_ids"] == ["T-P010-S002"]
    assert "Beta" not in arts[0]["derived_text"] and "Alpha" not in arts[1]["derived_text"]


# 2
def test_article_with_multiple_clauses():
    t = HDR.format(11) + "Article 7 Osaekomi Time\n1. First rule.\n2. Second rule.\n3. Third rule.\n"
    units, _ = run([mk(11, 1, "Article 7", "Article 7 Osaekomi Time", t)])
    seg = by_type(units, "ARTICLE")[0]
    kids = [u for u in units if u["parent_unit_id"] == seg["unit_id"]]
    assert [k["clause_label"] for k in kids if k["unit_type"] == "NUMBERED"] == ["1", "2", "3"]
    assert kids[0]["unit_type"] == "INTRO"


# 3
def test_enumerations_not_split():
    t = HDR.format(12) + "Article 3 Lists\n1. The following:\n• item a\n• item b\n2. Next rule.\n"
    units, _ = run([mk(12, 1, "Article 3", "Article 3 Lists", t)])
    c1 = [u for u in units if u["clause_label"] == "1"][0]
    assert "• item a" in c1["derived_text"] and "• item b" in c1["derived_text"]
    assert c1["list_item_count"] == 2


# 4
def test_exceptions_kept_with_condition():
    t = HDR.format(13) + "Article 8 Time\n1. A technique is valid.\n2. Although applied late, it is not valid unless effective.\n3. Other.\n"
    units, errors = run([mk(13, 1, "Article 8", "Article 8 Time", t)])
    c1 = [u for u in units if u["clause_label"] == "1"][0]
    assert "Although applied late" in c1["derived_text"] and c1["merged_exception_clauses"] == ["2"]
    assert any(e["code"] == "EXCEPTION_CLAUSE_MERGED" for e in errors)
    leaves = [u for u in units if u["unit_level"] == 2 or not u.get("child_unit_ids")]
    assert sum(len(u["exception_markers"]) for u in leaves) == 2  # although, unless


# 5
def test_cross_references_resolved():
    a = HDR.format(20) + "Article 18 .1 .4 Cadets\n33. Rule thirty three.\n34. Rule thirty four.\n"
    b = HDR.format(21) + "Article 18 .2 .1 Dangerous\nForbidden. Tori can continue (see also Article 18.1.4 point 34).\n"
    units, _ = run([mk(20, 1, "Article 18.1.4", "Article 18.1.4 Cadets", a),
                    mk(21, 1, "Article 18.2.1", "Article 18.2.1 Dangerous", b)])
    seg = [u for u in units if u["article_label"] == "Article 18.2.1" and u["unit_level"] == 1][0]
    ref = [r for r in seg["cross_refs"] if r["type"] == "ARTICLE"][0]
    assert ref["target"] == "Article 18.1.4" and ref["point"] == "34" and ref["resolution"] == "RESUELTA"
    target = [u for u in units if u["unit_id"] == ref["resolved_point_unit_ids"][0]][0]
    assert target["derived_text"].startswith("34.")


# 6
def test_headings_preserved():
    t = HDR.format(14) + "Article 12 Sono-mama\n1. Hold.\n2. Continue.\n"
    units, _ = run([mk(14, 1, "Article 12", "Article 12 Sono-mama", t)])
    for u in units:
        if u["unit_level"] == 2:
            assert u["heading"] == "Article 12 Sono-mama"
    intro = by_type(units, "INTRO")[0]
    assert intro["derived_text"].startswith("Article 12 Sono-mama")


# 7
def test_non_segmentable_text_flagged():
    t = HDR.format(15) + "Article 5 Areas\n1. One.\n2. Two.\n5. Five.\n"
    units, errors = run([mk(15, 1, "Article 5", "Article 5 Areas", t)])
    seg = by_type(units, "ARTICLE")[0]
    assert seg["validation_status"] == "NO_SEGMENTADA"
    assert seg["non_segmentation_reason"].startswith("NUMERACION_IRREGULAR")
    assert seg["child_unit_ids"] == []
    assert any(e["code"] == "CLAUSE_SEGMENTATION_UNSAFE" for e in errors)


# 8
def test_irregular_format():
    a = "page - 30\nSport and Organisation Rules of the International Judo Federation\n2 .5 Systems\nText.\n"
    b = HDR.format(31) + "Other Title\n2.5 Minutes are shown here.\n"
    units, errors = run([mk(30, 1, "2.5", "2.5 Systems", a), mk(31, 1, "GENERAL", "Other Title", b)])
    assert [u["article_label"] for u in units if u["page"] == 30 and u["unit_type"] == "ARTICLE"] == ["2.5"]
    assert by_type([u for u in units if u["page"] == 30], "PAGE_HEADER")
    assert not [u for u in units if u["page"] == 31 and u["article_label"] == "2.5"]
    assert any(e["code"] == "HEADING_LIKE_LINE_REJECTED" and e["page"] == 31 for e in errors)


# 9
def test_original_duplicate_passages():
    t = HDR.format(16) + "Article 4 Gestures\nText.\n"
    ps = [mk(16, 1, "Article 4", "Article 4 Gestures", t), mk(16, 2, "Article 4", "Article 4 Gestures", t)]
    units, _ = run(ps)
    seg = by_type(units, "ARTICLE")[0]
    assert seg["original_passage_ids"] == ["T-P016-S001", "T-P016-S002"]


# 10
def test_text_reconstruction_real_corpus():
    passages, _ = real_corpus()
    units, _ = bau.segment_corpus(passages)
    pages = bau.group_pages(passages)
    for page, pps in pages.items():
        lvl1 = sorted([u for u in units if u["page"] == page and u["unit_level"] == 1], key=lambda u: u["char_start"])
        assert "".join(u["derived_text"] for u in lvl1) == pps[0]["text_original"], page
    ids = {u["unit_id"]: u for u in units}
    for u in units:
        if u.get("child_unit_ids"):
            assert "".join(ids[k]["derived_text"] for k in u["child_unit_ids"]) == u["derived_text"]


# 11
def test_traceability_real_corpus():
    passages, _ = real_corpus()
    units, _ = bau.segment_corpus(passages)
    pids = {p["passage_id"] for p in passages}
    mapped = {pid for u in units for pid in u["original_passage_ids"]}
    assert mapped == pids
    for u in units:
        assert u["original_passage_ids"] and set(u["original_passage_ids"]) <= set(u["page_passage_ids"])
        assert u["normative_status"] == "DERIVADA_NO_NORMATIVA"


# 12
def test_hash_integrity_real_corpus():
    passages, _ = real_corpus()
    units, _ = bau.segment_corpus(passages)
    sha_by_page = {p["pdf_page_index"]: p["text_sha256"] for p in passages}
    text_by_page = {p["pdf_page_index"]: p["text_original"] for p in passages}
    for u in units:
        assert u["source_text_sha256"] == sha_by_page[u["page"]]
        assert u["derived_text_sha256"] == hashlib.sha256(u["derived_text"].encode("utf-8")).hexdigest()
        assert u["derived_text"] == text_by_page[u["page"]][u["char_start"]:u["char_end"]]


# 13
def test_original_ids_and_input_preserved():
    passages, raw = real_corpus()
    snapshot = copy.deepcopy(passages)
    bau.segment_corpus(passages)
    assert passages == snapshot
    _, raw_after = bau.load_corpus(ROOT)
    assert hashlib.sha256(raw).hexdigest() == hashlib.sha256(raw_after).hexdigest()


# 14
def test_full_coverage_and_validation_real_corpus():
    passages, raw = real_corpus()
    files, units, errors, stats, report = bau.build_artifacts(passages, raw)
    assert report["accepted"] and report["error_count"] == 0
    assert stats["coverage_ratio"] == 1.0
    assert stats["passages_traceable"] == stats["original_passages"] == len(passages)
    assert stats["text_chars_covered_level1"] == stats["text_chars_total"]


def test_artifacts_on_disk_are_reproducible():
    out = os.path.join(ROOT, bau.OUT_REL)
    if not os.path.isdir(out):
        pytest.skip("artefactos no generados")
    passages, raw = real_corpus()
    files, *_ = bau.build_artifacts(passages, raw)
    for name, content in files.items():
        with open(os.path.join(out, name), "rb") as fh:
            assert fh.read().decode("utf-8").replace("\r\n", "\n") == content, name
    meta = json.loads(files["metadata.json"])
    assert meta["input_corpus_file_sha256"] == hashlib.sha256(raw).hexdigest()

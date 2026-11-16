"""Fase 8 (ampliacion SHADOW) - trazabilidad, separacion de corpus y autoridad subordinada.

Estructurales (sin LLM real). La prueba de ADA usa StubLLM y se omite si el motor no puede cargarse.
"""
import hashlib
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, "scripts"), os.path.join(ROOT, "src"), os.path.join(ROOT, "tests")]
import build_shadow_units as bsu  # noqa: E402
import build_benchmark_shadow_v1 as bbs  # noqa: E402

CHK = re.compile(r"CHK-[A-Z0-9\-]+")


@pytest.fixture(scope="module")
def built():
    if not os.path.exists(os.path.join(ROOT, bsu.PASSAGES_REL)):
        pytest.skip("sidecar no disponible")
    return bsu.build()


def test_full_traceability(built):
    files, units, errors, stats, report, raw = built
    assert report["accepted"] and not [e for e in errors if e["severity"] == "ERROR"]
    chunks = json.loads(raw[bsu.PASSAGES_REL].decode("utf-8"))
    assert {u["chunk_id"] for u in units} == {c["chunk_id"] for c in chunks} and len(units) == len(chunks)
    for u in units:
        st = raw[u["staged_path"]]
        assert hashlib.sha256(st).hexdigest() == u["staged_sha256"]
        text = st.decode("utf-8")
        assert u["staged_locator"] == "LITERAL" and text[u["staged_char_start"]:u["staged_char_end"]] == u["derived_text"]
        assert u["kun_block_heading"] and u["source_kun_id"] in u["kun_block_heading"]
        assert u["catalog_authority"] is not None


def test_units_identical_to_source_chunks(built):
    _f, units, _e, _s, _r, raw = built
    by_id = {c["chunk_id"]: c for c in json.loads(raw[bsu.PASSAGES_REL].decode("utf-8"))}
    for u in units:
        assert u["derived_text"] == by_id[u["chunk_id"]]["content_text"]
        assert u["derived_text_sha256"] == hashlib.sha256(u["derived_text"].encode("utf-8")).hexdigest()


def test_corpus_separation(built):
    _f, units, _e, _s, _r, raw = built
    sor_ids = {p["passage_id"] for p in json.loads(raw[bsu.SOR_REL].decode("utf-8"))}
    assert bsu.OUT_REL != os.path.dirname(bsu.AU_REL) and not bsu.OUT_REL.startswith("data/processed")
    for u in units:
        assert u["corpus"] == "SHADOW_COMPLEMENTARIO" and u["unit_id"].startswith("SHU1-")
        assert u["unit_id"] not in sor_ids and not u["unit_id"].startswith(("SOR-", "AU1-"))
    au = os.path.join(ROOT, bsu.AU_REL)
    if os.path.exists(au):
        with open(au, encoding="utf-8") as fh:
            assert not CHK.search(fh.read()), "fragmentos SHADOW presentes en unidades primarias"


def test_no_normative_authority_attributed(built):
    _f, units, _e, _s, _r, _raw = built
    for u in units:
        assert u["normative_status"] == "AUXILIAR_NO_NORMATIVA"
        assert u["decisive"] is False and u["citable_as_sor"] is False and u["may_substitute_sor"] is False
        assert u["authority_tier"] in ("TIER_2", "TIER_3") and u["supplementary_role"] == "COMPLEMENTO_INTERPRETATIVO"


def test_related_sor_references_resolve_to_primary_units(built):
    _f, units, _e, _s, _r, _raw = built
    au = os.path.join(ROOT, bsu.AU_REL)
    if not os.path.exists(au):
        pytest.skip("article_units_v1 no generado")
    ids = {json.loads(l)["unit_id"] for l in open(au, encoding="utf-8")}
    for u in units:
        for r in u["related_sor_resolution"]:
            assert set(r["sor_unit_ids"]) <= ids


def test_original_inputs_unchanged(built):
    *_, raw = built
    *_, raw2 = bsu.build()
    assert {k: hashlib.sha256(v).hexdigest() for k, v in raw.items()} == {k: hashlib.sha256(v).hexdigest() for k, v in raw2.items()}


def test_shadow_artifacts_reproducible(built):
    files = built[0]
    out = os.path.join(ROOT, bsu.OUT_REL)
    if not os.path.isdir(out):
        pytest.skip("artefactos no generados")
    for name, content in files.items():
        with open(os.path.join(out, name), encoding="utf-8") as fh:
            assert fh.read().replace("\r\n", "\n") == content, name


def test_shadow_benchmark_structure():
    files, recs, errors, counts = bbs.build(*bbs.load())
    assert errors == [] and counts["total"] == 24
    assert set(counts["by_evidence_class"]) == {"PRIMARIA_CON_AUXILIAR", "SOLO_AUXILIAR_SIN_PRIMARIA",
                                                "AUXILIAR_NO_DEBE_FUNDAMENTAR", "SIN_EVIDENCIA_SUFICIENTE"}
    for r in recs:
        assert r["human_review_status"] == "PENDIENTE_REVISION_ARBITRAL" and r["certified_by_referees"] is False
        assert r["auxiliary_use_policy"] == "CONTEXTO_NO_DECISORIO"
        if r["evidence_class"] in ("SOLO_AUXILIAR_SIN_PRIMARIA", "SIN_EVIDENCIA_SUFICIENTE"):
            assert r["expected_primary"] == [] and r["normative_answer_expected"] is False
        else:
            assert r["expected_primary"] and r["expected_normative_basis"] == "SOR_PRIMARIO"
        for a in r["expected_auxiliary"] + r["forbidden_as_basis"]:
            assert a["status"] == "VERIFICADA_TEXTUALMENTE"
    out = os.path.join(ROOT, bbs.OUT_REL)
    if os.path.isdir(out):
        for name, content in files.items():
            with open(os.path.join(out, name), encoding="utf-8") as fh:
                assert fh.read().replace("\r\n", "\n") == content, name


def test_ada_rejects_shadow_as_autonomous_basis():
    """Produccion sin cambios: una respuesta que cite solo SHADOW no puede ser SUCCESS."""
    try:
        from ada_assistant import ArbitrationDecisionAssistant
        from _ada_contract_helpers import StubLLM, json_answer, supplementary_block, citation_ids
    except Exception as e:  # motor no cargable en este entorno
        pytest.skip(f"ADA no disponible: {e}")
    q = "¿Qué sanciones pueden imponer los órganos disciplinarios de la IJF?"
    ada = ArbitrationDecisionAssistant()
    ada._call_llm = lambda prompt: (None, {})
    shadow_ids = [s["chunk_id"] for s in ada.analyze_situation(q, top_k=5).get("supplementary_context") or []]
    if not shadow_ids:
        pytest.skip("la consulta no recibio contexto SHADOW; la sonda no seria efectiva")
    stub = StubLLM(analysis=lambda prompt, delivered: json_answer(shadow_ids[:2] + re.findall(r"COMPLEMENTO-\d+", supplementary_block(prompt))[:1]))
    ada._call_llm = stub
    res = ada.analyze_situation(q, top_k=5)
    assert stub.analysis_prompts and "COMPLEMENTO-" in supplementary_block(stub.analysis_prompts[-1])
    assert res.get("status") != "SUCCESS"
    assert not any(CHK.match(str(c or "")) for c in citation_ids(res))
    assert not any(CHK.match(str(e.get("passage_id") or "")) for e in res.get("evidence", []) + res.get("related_passages", []))
    assert all(s.get("decisive") is False for s in res.get("supplementary_context") or [])

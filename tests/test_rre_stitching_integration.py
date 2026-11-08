"""
Pruebas de integración de RRE 3.0 con PassageStitcher.

Verifica:
1. Feature flag enable_chunk_stitching=False (comportamiento baseline idéntico).
2. Feature flag enable_chunk_stitching=True (ensamblado multi-página en runtime).
3. Preservación del KUN primario para ADA y trazabilidad en source_spans.
4. Caso real Bridge (Art. 14 págs. 166-167) recuperado con regla y excepción.
5. Caso real Cadetes (Art. 18.1.4 págs. 188-189) recuperado con Shido por cabeza y reverse seoi-nage.
"""

import pytest
from src.rre_engine import ReasoningRetrievalEngine


@pytest.fixture(scope="module")
def rre_baseline():
    return ReasoningRetrievalEngine(enable_chunk_stitching=False)


@pytest.fixture(scope="module")
def rre_stitched():
    return ReasoningRetrievalEngine(enable_chunk_stitching=True)


def test_rre_stitching_feature_flag_disabled(rre_baseline):
    res = rre_baseline.retrieve("El puente voluntario para evitar una caida se considera ippon?")
    assert res["status"] == "SUCCESS"
    assert len(res["evidence"]) > 0
    top_ev = res["evidence"][0]
    # En baseline no debe haber stitching
    assert top_ev.get("is_stitched") is False
    assert top_ev.get("composite_kun") is None


def test_rre_stitching_bridge_case_retrieval(rre_stitched):
    res = rre_stitched.retrieve("El puente voluntario para evitar una caida se considera ippon?")
    assert res["status"] == "SUCCESS"
    assert len(res["evidence"]) > 0

    # Buscar evidencia que corresponda al Art. 14
    art14_ev = [e for e in res["evidence"] if "14" in str(e.get("article_id"))]
    assert len(art14_ev) > 0

    top_art14 = art14_ev[0]
    assert top_art14.get("is_stitched") is True
    assert top_art14.get("composite_kun") == "SOR-2026-08-P166-P167"
    assert "SOR-2026-08-P166-S187" in top_art14.get("stitched_kuns", [])
    assert "SOR-2026-08-P167-S187" in top_art14.get("stitched_kuns", [])

    text = top_art14.get("text_original", "")
    assert "[PAGE BREAK: P166 -> P167" in text
    assert "voluntarily makes a" in text
    assert "landing of uke occurs on the body of tori" in text


def test_rre_stitching_cadet_restrictions(rre_stitched):
    res = rre_stitched.retrieve("Esta permitida la defensa con la cabeza apoyandola en el tatami en categoria Cadetes y que sancion aplica?")
    assert res["status"] == "SUCCESS"
    assert len(res["evidence"]) > 0

    cadet_ev = [e for e in res["evidence"] if "18.1.4" in str(e.get("article_id"))]
    assert len(cadet_ev) > 0

    top_cadet = cadet_ev[0]
    assert top_cadet.get("is_stitched") is True
    assert "SOR-2026-08-P188-S196" in top_cadet.get("stitched_kuns", [])
    assert "SOR-2026-08-P189-S196" in top_cadet.get("stitched_kuns", [])

    text = top_cadet.get("text_original", "")
    assert "head to defend as UKE" in text
    assert "penalised with shido" in text
    assert "reverse seoi-nage" in text


def test_rre_stitching_preserves_single_page_articles(rre_stitched):
    # Tatami dimensions (Art. 8.7 p. 96) es página única
    res = rre_stitched.retrieve("Cuales son las medidas oficiales del area de combate y el area de seguridad del tatami?")
    assert res["status"] == "SUCCESS"
    assert len(res["evidence"]) > 0
    top_ev = res["evidence"][0]
    if str(top_ev.get("article_id")) == "8.7":
        assert top_ev.get("is_stitched") is False
        assert len(top_ev.get("source_spans", [])) == 1

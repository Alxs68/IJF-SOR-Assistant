"""
Tests Automatizados de Evaluación y Calidad Multifuente (Fase 4.2.4)
===================================================================
Verificaciones requeridas:
1. Relevancia y Precisión de Recuperación Sidecar en Consultas Específicas (Tier 2 y Tier 3).
2. Integridad de la Cadena de Gobernanza (Autoridad, Vigencia, Elegibilidad y SHA-256).
3. Invariabilidad Absoluta del RRE Primario ante Cualquier Búsqueda Multifuente.
4. Trazabilidad y Preservación de Metadatos Documentales.
5. Comportamiento ante Consultas Sin Evidencia Complementaria.
"""

import pytest
from src.rre_engine import ReasoningRetrievalEngine
from src.multisource_retriever import MultisourceRetriever

@pytest.fixture(scope="module")
def retriever():
    return MultisourceRetriever()

@pytest.fixture(scope="module")
def rre_engine():
    return ReasoningRetrievalEngine(allow_degraded=True, enable_shadow_mode_multisource=True)

def test_sidecar_relevance_tier2_reverse_seoi(retriever):
    """Verifica que consultas sobre reverse seoi-nage recuperan el fragmento exacto de la enmienda senior."""
    res = retriever.search("¿Está permitido el reverse seoi-nage en senior?")
    assert res["status"] == "SUCCESS"
    assert len(res["matches"]) > 0
    top = res["matches"][0]
    assert top["chunk_id"] == "CHK-KUN-NEW-001-002"
    assert top["authority"] == "TIER_2_OFFICIAL_AMENDMENT"
    assert top["validity"] == "VIGENTE"
    assert top["eligibility"] == "ELIGIBLE_INTERPRETATIVA"
    assert "SOR Art. 18.1.4 y Art. 18.2.2" in top["related_sor_articles"]

def test_sidecar_relevance_tier2_kumikata_limit(retriever):
    """Verifica que consultas sobre límite de agarre recuperan el fragmento de 30 segundos."""
    res = retriever.search("límite de tiempo kumi-kata 30 segundos")
    assert res["status"] == "SUCCESS"
    assert len(res["matches"]) > 0
    top = res["matches"][0]
    assert top["chunk_id"] == "CHK-KUN-NEW-001-003"
    assert top["authority"] == "TIER_2_OFFICIAL_AMENDMENT"

def test_sidecar_relevance_tier2_yuko_osaekomi(retriever):
    """Verifica recuperación de Yuko en inmovilizaciones cortas de 5 a 9 segundos."""
    res = retriever.search("puntuación yuko inmovilización 5 a 9 segundos")
    assert res["status"] == "SUCCESS"
    assert len(res["matches"]) > 0
    top = res["matches"][0]
    assert top["chunk_id"] == "CHK-KUN-NEW-003-001"
    assert top["authority"] == "TIER_2_OFFICIAL_AMENDMENT"

def test_sidecar_relevance_tier3_continuity(retriever):
    """Verifica recuperación de la interpretación arbitral sobre continuidad hacia suelo."""
    res = retriever.search("continuidad en la transición a suelo ne-waza árbitro")
    assert res["status"] == "SUCCESS"
    assert len(res["matches"]) > 0
    top = res["matches"][0]
    assert top["chunk_id"] == "CHK-KUN-PPT-002-001"
    assert top["authority"] == "TIER_3_REFEREEING_INTERPRETATION"
    assert top["normative_relation"] == "COMPLEMENTO_OPERATIVO"

def test_sidecar_relevance_tier3_direct_pull_shido(retriever):
    """Verifica recuperación de la sanción de Shido por tirarse directamente al suelo sin técnica."""
    res = retriever.search("penalización Shido por arrastre directo al suelo sin técnica")
    assert res["status"] == "SUCCESS"
    assert len(res["matches"]) > 0
    top = res["matches"][0]
    assert top["chunk_id"] == "CHK-KUN-PPT-002-002"
    assert top["authority"] == "TIER_3_REFEREEING_INTERPRETATION"

def test_sidecar_relevance_tier2_head_contact_exception(retriever):
    """Verifica recuperación de la excepción de contacto involuntario de cabeza."""
    res = retriever.search("excepción de contacto involuntario de cabeza en transición")
    assert res["status"] == "SUCCESS"
    assert len(res["matches"]) > 0
    top = res["matches"][0]
    assert top["chunk_id"] == "CHK-KUN-NEW-003-003"
    assert top["authority"] == "TIER_2_OFFICIAL_AMENDMENT"

def test_multisource_governance_integrity(retriever):
    """Verifica que todos los fragmentos cargados en el Sidecar cumplen los requisitos estrictos de gobernanza."""
    assert len(retriever.passages) >= 8
    for p in retriever.passages:
        assert p["authority"] in ["TIER_2_OFFICIAL_AMENDMENT", "TIER_3_REFEREEING_INTERPRETATION"]
        assert p["validity"] in ["VIGENTE", "CURRENT", "INTERPRETIVE_VALID"]
        assert p["eligibility"] in ["ELIGIBLE_INTERPRETATIVA", "APPROVED"]
        assert p["staging_sha256"] is not None and len(p["staging_sha256"]) == 64
        assert len(p["related_sor_articles"]) > 0
        assert p["normative_relation"] in ["SUBSUMIDO_PARCIALMENTE", "SUBSUMIDO_TOTALMENTE", "COMPLEMENTO_OPERATIVO", "COMPLEMENTO_EXPLICATIVO"]

def test_rre_primary_absolute_invariance(rre_engine):
    """Verifica que el pipeline primario del RRE mantiene evidencia idéntica con o sin recuperación Sidecar."""
    queries = [
        "What constitutes an Ippon in competition?",
        "When is Shido given for passivity?",
        "What are the tatami dimensions in official tournaments?"
    ]
    engine_baseline = ReasoningRetrievalEngine(allow_degraded=True, enable_shadow_mode_multisource=False)

    for q in queries:
        r_base = engine_baseline.retrieve(q)
        r_shadow = rre_engine.retrieve(q)

        assert r_base["status"] == r_shadow["status"]
        assert len(r_base["evidence"]) == len(r_shadow["evidence"])
        for e1, e2 in zip(r_base["evidence"], r_shadow["evidence"]):
            assert e1["passage_id"] == e2["passage_id"]
            assert e1["score"] == e2["score"]
            assert e1["article_id"] == e2["article_id"]

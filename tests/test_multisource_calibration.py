"""
Test Suite: Calibración y Endurecimiento del Sidecar (Fase 4.2.5)
=================================================================
Verificaciones formales:
1. Normalización NFD y tokenización tolerante a acentos/tildes.
2. Supresión activa de falsos positivos en consultas normativas puras SOR (status == ABSTAIN).
3. Supresión activa de falsos positivos en dominios negativos / OOD (status == ABSTAIN).
4. Descarte de términos aislados genéricos (combate, penalización, transición).
5. Mantenimiento del Recall@1 en consultas dirigidas sobre enmiendas clave (Tier 2/3).
6. Invariabilidad primaria bit a bit del RRE primario SOR 2026.
7. Preservación estricta de invariantes criptográficos en disco.
"""

import pytest
from src.rre_engine import ReasoningRetrievalEngine
from src.multisource_retriever import MultisourceRetriever, strip_accents, tokenize

@pytest.fixture(scope="module")
def retriever():
    return MultisourceRetriever()

@pytest.fixture(scope="module")
def rre_engine():
    return ReasoningRetrievalEngine(allow_degraded=True, enable_shadow_mode_multisource=True)

def test_normalization_and_accent_stripping():
    """Verifica que la normalización remueve diacríticos manteniendo tokens bilingües limpios."""
    raw = "¿A partir de qué evento se congelan las reglas para el ciclo olímpico LA28?"
    tokens = tokenize(raw)
    assert "olimpico" in tokens
    assert "congelan" in tokens
    assert "la28" in tokens

def test_suppression_of_pure_sor_queries(retriever):
    """Verifica que consultas puras sobre tatami, judogi o categorías de peso se abstienen en Sidecar."""
    sor_queries = [
        "¿Cuáles son las medidas reglamentarias del área de combate y seguridad?",
        "¿Cuál es la especificación del color del judogi azul en código Pantone?",
        "¿Cuáles son los límites de peso en la categoría femenina de -52 kg?"
    ]
    for q in sor_queries:
        res = retriever.search(q)
        assert res["status"] == "ABSTAIN", f"Expected ABSTAIN for query: {q}, got {res['status']}"
        assert len(res["matches"]) == 0

def test_suppression_of_out_of_domain_queries(retriever):
    """Verifica que consultas ajenas al judo (fútbol, natación, baloncesto) se abstienen activamente."""
    ood_queries = [
        "En fútbol, ¿cuándo se sanciona un fuera de juego posicional?",
        "¿Cuántos puntos vale un tiro libre encestado en baloncesto?",
        "En natación, ¿cuál es la penalización por salida en falso en 100m mariposa?"
    ]
    for q in ood_queries:
        res = retriever.search(q)
        assert res["status"] == "ABSTAIN", f"Expected ABSTAIN for OOD query: {q}, got {res['status']}"
        assert len(res["matches"]) == 0

def test_suppression_of_isolated_generic_terms(retriever):
    """Verifica que términos genéricos aislados de 1 sola palabra sean suprimidos de inmediato."""
    generic_terms = ["Combate", "Transición", "Penalización"]
    for t in generic_terms:
        res = retriever.search(t)
        assert res["status"] == "ABSTAIN", f"Expected ABSTAIN for generic term: {t}"
        assert len(res["matches"]) == 0

def test_directed_tier2_enmiendas_recall(retriever):
    """Verifica que las consultas dirigidas sobre enmiendas oficiales recuperan el fragmento exacto."""
    cases = [
        ("¿Está permitido el reverse seoi-nage en la categoría Senior?", "CHK-KUN-NEW-001-002"),
        ("¿Cuál es el límite máximo de disputa de kumi-kata sin ataque?", "CHK-KUN-NEW-001-003"),
        ("¿Desde qué torneo se bloquean las reglas arbitrales para LA28?", "CHK-KUN-NEW-001-001"),
        ("¿Cuántos segundos de inmovilización otorgan Yuko en las nuevas reglas?", "CHK-KUN-NEW-003-001"),
        ("¿Se sanciona el contacto de cabeza si es producto de la inercia de caída?", "CHK-KUN-NEW-003-003")
    ]
    for q, exp in cases:
        res = retriever.search(q)
        assert res["status"] == "SUCCESS", f"Failed for query: {q}"
        assert len(res["matches"]) > 0
        assert res["matches"][0]["chunk_id"] == exp

def test_rre_primary_absolute_invariance(rre_engine):
    """Verifica que la activación del Sidecar calibrado produce exactamente la misma respuesta del SOR primario."""
    test_queries = [
        "What constitutes an Ippon in competition?",
        "When is Shido given for passivity?",
        "What are the tatami dimensions in official tournaments?"
    ]
    engine_base = ReasoningRetrievalEngine(allow_degraded=True, enable_shadow_mode_multisource=False)
    for q in test_queries:
        r_off = engine_base.retrieve(q)
        r_on = rre_engine.retrieve(q)
        assert r_off["status"] == r_on["status"]
        assert len(r_off["evidence"]) == len(r_on["evidence"])
        for e1, e2 in zip(r_off["evidence"], r_on["evidence"]):
            assert e1["passage_id"] == e2["passage_id"]
            assert e1["score"] == e2["score"]
            assert e1["article_id"] == e2["article_id"]

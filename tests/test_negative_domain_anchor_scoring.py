"""
Unit and Integration Tests for Negative Domain Anchor Scoring (BK-01).
Tests suites OOD-BK01 through OOD-BK06, plus immunity and conservative scoring.
"""

import pytest
from src.negative_domain_anchor_scoring import (
    NegativeDomainAnchorScorer,
    NegativeDomainCategory,
    NegativeDomainDecision,
    NegativeDomainResult
)
from src.rre_engine import ReasoningRetrievalEngine


# ============================================================================
# 1. TEST SUITE OOD-BK01 — BALONCESTO
# ============================================================================

def test_ood_bk01_basketball_free_throw():
    """Verify free throw in basketball is flagged as OOD."""
    query = "¿Cuándo se concede un tiro libre?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is True
    assert "BASKETBALL" in res.detected_domains
    assert res.decision == NegativeDomainDecision.CONFIRMED_NEGATIVE_OOD
    assert res.negative_score >= 0.65


def test_ood_bk01_basketball_triple():
    """Verify three-pointer is identified as basketball."""
    query = "¿Qué ocurre después de un triple?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert "BASKETBALL" in res.detected_domains
    # Moderate term has high confidence detection
    assert res.decision in (NegativeDomainDecision.CONFIRMED_NEGATIVE_OOD, NegativeDomainDecision.SUSPECTED_NEGATIVE)


def test_ood_bk01_basketball_dribble_steps():
    """Verify traveling / dribbling in basketball is flagged as OOD."""
    query = "¿Cuántos pasos puede dar un jugador sin driblar?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is True
    assert "BASKETBALL" in res.detected_domains
    assert res.decision == NegativeDomainDecision.CONFIRMED_NEGATIVE_OOD


# ============================================================================
# 2. TEST SUITE OOD-BK02 — TENIS
# ============================================================================

def test_ood_bk02_tennis_tie_break():
    """Verify tie-break in tennis is flagged as OOD (resolves GEN-08)."""
    query = "¿Cómo funciona el tie-break?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is True
    assert "TENNIS" in res.detected_domains
    assert res.decision == NegativeDomainDecision.CONFIRMED_NEGATIVE_OOD


def test_ood_bk02_tennis_ace():
    """Verify ace in tennis is flagged as OOD."""
    query = "¿Qué es un ace?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is True
    assert "TENNIS" in res.detected_domains


def test_ood_bk02_tennis_serve_repeat():
    """Verify tennis serve repetition is flagged as OOD."""
    query = "¿Cuándo se repite un saque de tenis?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is True
    assert "TENNIS" in res.detected_domains
    assert res.decision == NegativeDomainDecision.CONFIRMED_NEGATIVE_OOD


# ============================================================================
# 3. TEST SUITE OOD-BK03 — NATACIÓN
# ============================================================================

def test_ood_bk03_swimming_underwater_distance():
    """Verify underwater distance in swimming is flagged as OOD (resolves GEN-09)."""
    query = "¿Cuál es la distancia permitida bajo el agua?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is True
    assert "SWIMMING" in res.detected_domains
    assert res.decision == NegativeDomainDecision.CONFIRMED_NEGATIVE_OOD


def test_ood_bk03_swimming_butterfly_turn():
    """Verify butterfly turn in swimming is flagged as OOD."""
    query = "¿Cómo se ejecuta el viraje en estilo mariposa?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is True
    assert "SWIMMING" in res.detected_domains


def test_ood_bk03_swimming_false_start():
    """Verify false start in swimming is flagged as OOD."""
    query = "¿Cuándo se descalifica por salida anticipada en natación?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is True
    assert "SWIMMING" in res.detected_domains


# ============================================================================
# 4. TEST SUITE OOD-BK04 — FÚTBOL
# ============================================================================

def test_ood_bk04_football_offside():
    """Verify offside in football is flagged as OOD."""
    query = "¿Qué es fuera de juego?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is True
    assert "FOOTBALL" in res.detected_domains


def test_ood_bk04_football_corner():
    """Verify corner kick in football is flagged as OOD."""
    query = "¿Cuándo se sanciona un córner?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is True
    assert "FOOTBALL" in res.detected_domains


def test_ood_bk04_football_penalty():
    """Verify penalty kick in football is flagged as OOD."""
    query = "¿Cómo se ejecuta un penalti en fútbol?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is True
    assert "FOOTBALL" in res.detected_domains


# ============================================================================
# 5. TEST SUITE OOD-BK05 — ATLETISMO
# ============================================================================

def test_ood_bk05_athletics_pole_vault():
    """Verify pole vault in athletics is flagged as OOD."""
    query = "¿Cómo se mide un salto con pértiga?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is True
    assert "ATHLETICS" in res.detected_domains


def test_ood_bk05_athletics_discus_throw():
    """Verify discus throw in athletics is flagged as OOD."""
    query = "¿Cuándo es nulo un lanzamiento de disco?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is True
    assert "ATHLETICS" in res.detected_domains


def test_ood_bk05_athletics_triple_jump():
    """Verify triple jump in athletics is flagged as OOD."""
    query = "¿Cuál es la técnica del salto triple?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is True
    assert "ATHLETICS" in res.detected_domains


# ============================================================================
# 6. TEST SUITE OOD-BK06 — AMBIGÜEDAD Y CONTROL NEGATIVO (INMUNIDAD JUDO)
# ============================================================================

def test_ood_bk06_mate_immunity():
    """Mate is an official referee command and must NEVER be flagged as negative OOD."""
    query = "¿Qué significa Mate?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is False
    assert res.decision != NegativeDomainDecision.CONFIRMED_NEGATIVE_OOD


def test_ood_bk06_generic_penalizacion_not_auto_ood():
    """Generic word 'penalización' must not trigger negative domain by itself."""
    query = "¿Qué es una penalización?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is False
    assert res.decision == NegativeDomainDecision.NEUTRAL_INSUFFICIENT


def test_ood_bk06_combate_duration_not_negative():
    """Query about contest ending must not trigger negative sports domain."""
    query = "¿Cuándo termina un combate?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is False
    assert res.decision == NegativeDomainDecision.NEUTRAL_INSUFFICIENT


def test_ood_bk06_shido_judo_immunity():
    """Shido is an explicit judo term and triggers full judo immunity."""
    query = "¿Qué ocurre con tres Shido?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is False
    assert res.has_judo_immunity is True
    assert res.decision == NegativeDomainDecision.CONFIRMED_JUDO


def test_ood_bk06_ippon_judo_immunity():
    """Ippon triggers full judo immunity."""
    query = "¿Qué es Ippon?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is False
    assert res.has_judo_immunity is True
    assert res.decision == NegativeDomainDecision.CONFIRMED_JUDO


def test_ood_bk06_wazaari_judo_immunity():
    """Waza-ari triggers full judo immunity."""
    query = "¿Cuándo se concede Waza-ari?"
    res = NegativeDomainAnchorScorer.score_negative_domain(query)
    assert res.is_ood is False
    assert res.has_judo_immunity is True
    assert res.decision == NegativeDomainDecision.CONFIRMED_JUDO


# ============================================================================
# 7. INTEGRATION WITH RRE & SHADOW MODE TESTS
# ============================================================================

@pytest.fixture(scope="module")
def rre_instance():
    return ReasoningRetrievalEngine(enable_negative_domain_anchors=True)


def test_rre_integration_tennis_abstains(rre_instance):
    """Confirm RRE with BK-01 active abstains cleanly on tennis tie-break."""
    query = "En tenis, ¿cuándo se disputa un tie-break a 7 puntos?"
    res = rre_instance.retrieve(query, top_k=2)
    assert res["status"] == "ABSTAIN"
    assert res["reason"] == "OUT_OF_DOMAIN"
    assert "TENNIS" in res["negative_domain_metrics"]["detected_domains"]


def test_rre_integration_swimming_abstains(rre_instance):
    """Confirm RRE with BK-01 active abstains cleanly on underwater kick in swimming."""
    query = "¿Cuál es la distancia máxima permitida de patada submarina en natación?"
    res = rre_instance.retrieve(query, top_k=2)
    assert res["status"] == "ABSTAIN"
    assert res["reason"] == "OUT_OF_DOMAIN"
    assert "SWIMMING" in res["negative_domain_metrics"]["detected_domains"]


def test_rre_integration_judo_preserved(rre_instance):
    """Confirm RRE with BK-01 active admits and succeeds on three Shido."""
    query = "¿Qué ocurre con tres Shido?"
    res = rre_instance.retrieve(query, top_k=2)
    assert res["status"] == "SUCCESS"
    assert len(res["evidence"]) > 0


def test_rre_shadow_mode_does_not_alter_response():
    """Confirm shadow mode records metrics but DOES NOT force abstention."""
    rre_shadow = ReasoningRetrievalEngine(shadow_mode_negative_anchors=True, enable_negative_domain_anchors=False)
    query = "¿Cuándo se sanciona un córner?"
    res = rre_shadow.retrieve(query, top_k=2)
    # Baseline for this query returned SUCCESS on corner mat; shadow mode must preserve baseline output
    assert res["status"] == "SUCCESS"
    assert res.get("negative_domain_metrics") is None

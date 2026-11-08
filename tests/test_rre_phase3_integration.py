import pytest
import os
from src.rre_engine import ReasoningRetrievalEngine


def test_rre_phase3_default_flags_off():
    rre = ReasoningRetrievalEngine()
    assert rre.enable_semantic_ranker is False
    assert rre.enable_referee_disambiguation is False
    assert rre.enable_ood_detector is False


def test_rre_phase3_tc04_ranking():
    rre = ReasoningRetrievalEngine(enable_semantic_ranker=True)
    res = rre.retrieve("Tori proyecta a Uke aplicando una técnica con fuerza y velocidad, pero Uke cae sobre un costado con el cuerpo perpendicular al tatami. ¿Qué puntuación corresponde?")
    assert res["status"] == "SUCCESS"
    assert len(res["evidence"]) > 0
    top_hit = res["evidence"][0]
    assert top_hit["article_id"] == "Article 15"
    assert top_hit["page"] in (168, 169)


def test_rre_phase3_tc15_disambiguation():
    rre = ReasoningRetrievalEngine(enable_referee_disambiguation=True)
    res = rre.retrieve("¿Cuándo se marca mate?")
    assert res["status"] == "SUCCESS"
    assert len(res["evidence"]) > 0
    top_hit = res["evidence"][0]
    assert top_hit["article_id"] == "Article 11"
    assert top_hit["page"] in (160, 161)


def test_rre_phase3_tc16_ood_abstention():
    rre = ReasoningRetrievalEngine(enable_ood_detector=True)
    res = rre.retrieve("¿Cuál es la sanción por una falta personal y tiro libre en básquetbol?")
    assert res["status"] == "ABSTAIN"
    assert res["reason"] == "OUT_OF_DOMAIN"


def test_rre_phase3_tc17_ood_abstention():
    rre = ReasoningRetrievalEngine(enable_ood_detector=True)
    res = rre.retrieve("¿Cómo se calcula la tasa de interés compuesto anual en finanzas?")
    assert res["status"] == "ABSTAIN"
    assert res["reason"] == "OUT_OF_DOMAIN"

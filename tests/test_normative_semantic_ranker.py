import pytest
from src.normative_semantic_ranker import NormativeSemanticRanker


def test_intent_classification_eval():
    query = "Tori proyecta a Uke, cae de costado perpendicular al tatami. ¿Qué puntuación corresponde?"
    intent = NormativeSemanticRanker.classify_query_intent(query)
    assert intent["is_eval"] is True
    assert intent["is_pure_infra"] is False
    assert "SCORES" in intent["target_domains"]


def test_intent_classification_pure_infra():
    query = "¿Cuáles son las medidas oficiales del área de combate y el área de seguridad del tatami?"
    intent = NormativeSemanticRanker.classify_query_intent(query)
    assert intent["is_eval"] is False
    assert intent["is_pure_infra"] is True


def test_reranking_tatami_vs_wazaari():
    query = "Tori proyecta a Uke, cae sobre un costado con el cuerpo perpendicular al tatami. ¿Qué puntuación corresponde?"
    scores = {
        "SOR-2026-08-P096-S114": 0.0939,  # Art 8.7 Tatami
        "SOR-2026-08-P168-S188": 0.0800,  # Art 15 Waza-ari
    }
    passages = {
        "SOR-2026-08-P096-S114": {"article_id": "8.7", "heading_path": ["Field of Play"], "pdf_page_index": 96},
        "SOR-2026-08-P168-S188": {"article_id": "15", "heading_path": ["Article 15 Waza-ari and Yuko"], "pdf_page_index": 168}
    }
    reranked = NormativeSemanticRanker.rerank_scores(query, scores, passages)
    assert reranked["SOR-2026-08-P168-S188"] > reranked["SOR-2026-08-P096-S114"]

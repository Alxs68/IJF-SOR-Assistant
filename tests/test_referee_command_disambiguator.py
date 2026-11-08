import pytest
from src.referee_command_disambiguator import RefereeCommandDisambiguator


def test_mate_verbal_intent_detection():
    query = "¿Cuándo se marca mate?"
    analysis = RefereeCommandDisambiguator.analyze_query(query)
    assert "MATE" in analysis["detected_commands"]
    assert analysis["intent_type"] == "REFEREE_COMMAND_VERBAL"
    assert analysis["damp_appendix_c"] is True
    assert "Article 11" in analysis["boost_articles"]


def test_mate_word_boundary_no_material_collision():
    query = "What is the material and maker label of the judogi?"
    analysis = RefereeCommandDisambiguator.analyze_query(query)
    assert "MATE" not in analysis["detected_commands"]
    assert analysis["intent_type"] == "NONE"


def test_hajime_command_detection():
    query = "¿En qué momento da el árbitro la orden de hajime?"
    analysis = RefereeCommandDisambiguator.analyze_query(query)
    assert "HAJIME" in analysis["detected_commands"]
    assert analysis["intent_type"] == "REFEREE_COMMAND_VERBAL"
    assert "Article 10.1" in analysis["boost_articles"]


def test_sore_made_command_detection():
    query = "¿Cuáles son las condiciones para indicar sore-made?"
    analysis = RefereeCommandDisambiguator.analyze_query(query)
    assert "SORE_MADE" in analysis["detected_commands"]
    assert "Article 13" in analysis["boost_articles"]


def test_sono_mama_command_detection():
    query = "El árbitro grita sono-mama durante ne-waza para revisar un vendaje"
    analysis = RefereeCommandDisambiguator.analyze_query(query)
    assert "SONO_MAMA" in analysis["detected_commands"]
    assert "Article 10.2" in analysis["boost_articles"]

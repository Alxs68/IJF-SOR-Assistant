import os
import sys
import pytest

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from ada_assistant import ArbitrationDecisionAssistant
from rre_engine import ReasoningRetrievalEngine

@pytest.fixture(scope="module")
def rre_instance():
    return ReasoningRetrievalEngine()

def test_regression_01_tatami_dimensions_exact_quote(rre_instance):
    query = "¿Cuáles son las dimensiones oficiales del tatami según el SOR de la FIJ?"
    res = rre_instance.retrieve(query=query, top_k=3)
    top_p = res["evidence"][0]
    quote, snippet = ArbitrationDecisionAssistant.extract_exact_quote(top_p, query)
    
    assert "1" in str(top_p.get("article_id", "")) or "tatami" in top_p["text_original"].lower()
    assert "8 m x 8 m" in quote or "minimum of 8 m" in quote or "contest area" in quote.lower()
    assert quote != "before use."
    assert len(quote.split()) >= 6

def test_regression_02_judogi_colour_pantone_exact_quote(rre_instance):
    query = "¿Cuáles son los colores oficiales permitidos para el judogi y sus especificaciones?"
    res = rre_instance.retrieve(query=query, top_k=3)
    top_p = res["evidence"][0]
    quote, snippet = ArbitrationDecisionAssistant.extract_exact_quote(top_p, query)
    
    assert "C1.9" in str(top_p.get("article_id", "")) or "judogi" in top_p["text_original"].lower()
    assert "the jacket and the trousers should be of a" in quote.lower()
    assert "sokuteiki" not in quote.lower()
    assert not quote.startswith("C1 .10")

def test_regression_03_cadet_tori_head_penalty_exact_quote(rre_instance):
    query = "En cadetes sub-18, ¿qué sanción corresponde si Tori utiliza la cabeza para proyectar?"
    res = rre_instance.retrieve(query=query, top_k=5)
    top_p = res["evidence"][0]
    quote, snippet = ArbitrationDecisionAssistant.extract_exact_quote(top_p, query)
    
    assert "18" in str(top_p.get("article_id", ""))
    assert "tori" in snippet.lower()
    assert "uke" not in snippet.lower()
    assert "shido" in snippet.lower()

def test_regression_04_cadet_uke_head_defense_exact_quote(rre_instance):
    query = "En categoría cadetes, si Uke usa la cabeza para defenderse durante una proyección, ¿se aplica sanción o cómo se califica la acción?"
    res = rre_instance.retrieve(query=query, top_k=5)
    top_p = res["evidence"][0]
    quote, snippet = ArbitrationDecisionAssistant.extract_exact_quote(top_p, query)
    
    assert "18" in str(top_p.get("article_id", ""))
    assert "uke" in snippet.lower()
    assert "throw as tori" not in snippet.lower()

def test_regression_05_bridge_landing_exception_exact_quote(rre_instance):
    query = "Si un competidor aterriza en posición de puente pero el cuerpo ya había tocado el suelo previamente, ¿se considera ippon o aplica alguna excepción?"
    res = rre_instance.retrieve(query=query, top_k=3)
    top_p = res["evidence"][0]
    quote, snippet = ArbitrationDecisionAssistant.extract_exact_quote(top_p, query)
    
    assert "14" in str(top_p.get("article_id", "")) or "16" in str(top_p.get("article_id", ""))
    assert "no score or penalty" in quote.lower() or "landing of uke" in quote.lower()
    assert len(quote.split()) >= 6

def test_regression_06_osaekomi_safety_boundary_exclamation_preservation(rre_instance):
    query = "Si una inmovilización (osaekomi) se desplaza fuera del área de combate y sobrepasa el límite del área de seguridad, ¿cuándo debe el árbitro anunciar Sore-Made?"
    res = rre_instance.retrieve(query=query, top_k=3)
    top_p = res["evidence"][0]
    quote, snippet = ArbitrationDecisionAssistant.extract_exact_quote(top_p, query)
    
    assert "17" in str(top_p.get("article_id", "")) or "20" in str(top_p.get("article_id", ""))
    assert "outside the contest area" in quote.lower() or "osaekomi" in quote.lower()

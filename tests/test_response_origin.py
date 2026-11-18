"""Origen de la respuesta: se deriva del flujo ejecutado (estado + llamada de analisis), no del contenido."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from answer_presentation import origin_badge, response_origin  # noqa: E402


def test_llm_answer_with_provider_and_model():
    o = response_origin({"status": "SUCCESS", "llm_meta": {"successful_provider": "Gemini", "successful_model": "m1",
                                                            "primary_provider": "Gemini"}})
    assert o["tipo"] == "LLM" and o["proveedor"] == "Gemini" and o["modelo"] == "m1" and not o["fallback"]
    tipo, title, desc = origin_badge(o, "es")
    assert tipo == "LLM" and "Gemini (m1)" in desc and "respaldo" not in desc


def test_llm_answer_after_fallback_is_reported():
    o = response_origin({"status": "SUCCESS", "llm_meta": {"successful_provider": "Groq", "successful_model": "g",
                                                            "primary_provider": "Gemini", "fallback_triggered": True}})
    assert o["fallback"] and "Gemini no disponible" in origin_badge(o, "es")[2]


def test_success_without_model_is_local():
    assert response_origin({"status": "SUCCESS", "llm_meta": {}})["tipo"] == "LOCAL"


def test_abstention_is_no_answer_even_if_model_was_called():
    o = response_origin({"status": "ABSTAIN", "mode": "Abstencion (DIG)", "llm_meta": {"successful_provider": "Gemini"}})
    assert o["tipo"] == "SIN_RESPUESTA" and o["modelo_consultado"] and o["motivo"] == "Abstencion (DIG)"
    assert "modelo consultado: Gemini" in origin_badge(o, "es")[2]


def test_out_of_domain_abstention_without_model():
    o = response_origin({"status": "ABSTAIN"})
    assert o["tipo"] == "SIN_RESPUESTA" and not o["modelo_consultado"]


def test_clarification():
    assert response_origin({"status": "CLARIFICATION_REQUIRED", "llm_meta": {"successful_provider": "Gemini"}})["tipo"] == "ACLARACION"

import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from response_structurer import (
    StructuredAnswer,
    parse_structured_response,
    build_deterministic_structured_answer
)
from ada_assistant import ArbitrationDecisionAssistant
from llm_provider import MultiProviderLLMManager


class TestResponseStructurerTransversal(unittest.TestCase):

    def test_01_parse_valid_json_response(self):
        sample_json = json.dumps({
            "summary": "El tatami mide 8x8m a 10x10m con zona de seguridad de 3m.",
            "normative_basis": "Regla 8.7 página 96.",
            "citations": ["SOR-2026-08-P096-S114"],
            "conditions_and_exceptions": "En World Championships es obligatorio 10x10m.",
            "extended_analysis": "Explicación detallada del campo de juego.",
            "limitations": "Solo aplica a eventos oficiales de la IJF."
        })
        parsed = parse_structured_response(sample_json)
        self.assertTrue(parsed.is_structured)
        self.assertEqual(parsed.summary, "El tatami mide 8x8m a 10x10m con zona de seguridad de 3m.")
        self.assertEqual(parsed.normative_basis, "Regla 8.7 página 96.")
        self.assertEqual(parsed.citations, ["SOR-2026-08-P096-S114"])
        self.assertIn("World Championships", parsed.conditions_and_exceptions)
        self.assertIn("Explicación detallada", parsed.extended_analysis)
        self.assertIn("Solo aplica", parsed.limitations)

    def test_02_parse_markdown_fenced_json(self):
        fenced = """Aquí está el resultado:
```json
{
  "summary": "En cadetes se sanciona con shido el uso de la cabeza para defenderse.",
  "normative_basis": "Art. 18.1.4 pág. 188.",
  "citations": ["SOR-2026-08-P255-S269"],
  "conditions_and_exceptions": "Si no hay peligro es shido; si crea peligro es hansoku-make.",
  "extended_analysis": "Análisis arbitral de protección cervical.",
  "limitations": ""
}
```
"""
        parsed = parse_structured_response(fenced)
        self.assertTrue(parsed.is_structured)
        self.assertIn("En cadetes se sanciona con shido", parsed.summary)
        self.assertIn("Art. 18.1.4", parsed.normative_basis)

    def test_03_fallback_unstructured_multisection_text(self):
        unstructured = """⚖️ **Síntesis Analítica IA (Gemini)**

El entrenador no puede dar instrucciones durante el combate, solo durante mate y hajime.

### 1. Preceptos Oficiales
Artículo 7.1 Código de Conducta de Entrenadores.

### 2. Sanciones
Suspensión del evento si reincide."""
        parsed = parse_structured_response(unstructured)
        self.assertFalse(parsed.is_structured)
        self.assertIn("El entrenador no puede dar instrucciones", parsed.summary)
        self.assertNotIn("⚖️ **Síntesis Analítica IA", parsed.summary)
        self.assertIn("Artículo 7.1", parsed.extended_analysis)

    def test_04_fallback_empty_or_whitespace_response(self):
        parsed = parse_structured_response("")
        self.assertFalse(parsed.is_structured)
        self.assertIn("No se recibió contenido", parsed.summary)
        self.assertIn("vacía", parsed.limitations)

    def test_05_deterministic_offline_structured_answer(self):
        mock_evidence = [{
            "passage_id": "SOR-2026-08-P096-S114",
            "title": "Field of Play",
            "article_id": "8.7",
            "page": 96,
            "text_original": "The contest area shall be a minimum of 8 m x 8 m and a maximum of 10 m x 10 m."
        }]
        mock_related = [{
            "passage_id": "SOR-2026-08-P095-S113",
            "title": "Tatami Safety",
            "article_id": "8.6",
            "page": 95,
            "relation": "safety_boundary"
        }]
        structured = build_deterministic_structured_answer(
            query="dimensiones del tatami",
            evidence=mock_evidence,
            related=mock_related,
            version_label="14 August 2026 (Official)"
        )
        self.assertTrue(structured.is_structured)
        self.assertIn("Field of Play", structured.summary)
        self.assertIn("Art. 8.7", structured.summary)
        self.assertIn("Pág. 96", structured.summary)
        self.assertIn("[SOR-2026-08-P096-S114]", structured.summary)
        self.assertIn("Extracto Oficial:", structured.normative_basis)
        self.assertIn("safety_boundary", structured.conditions_and_exceptions)
        self.assertIn("Modo Local Desconectado", structured.limitations)

    def test_06_ada_analyze_situation_two_tier_contract(self):
        mgr = MultiProviderLLMManager(gemini_api_key=None, groq_api_key=None)
        ada = ArbitrationDecisionAssistant(llm_manager=mgr)
        res = ada.analyze_situation("¿Cuáles son las dimensiones del tatami?")

        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("structured_answer", res)
        struct = res["structured_answer"]
        self.assertIn("summary", struct)
        self.assertIn("normative_basis", struct)
        self.assertIn("conditions_and_exceptions", struct)
        self.assertIn("extended_analysis", struct)
        self.assertIn("limitations", struct)
        
        # Verify Level 1 summary is present and concise
        self.assertTrue(len(struct["summary"]) > 20)
        self.assertIn("Art. 8.7", struct["summary"])
        # Verify clickable markdown formatting applied
        self.assertIn("SOR-2026-08-P096-S114", struct["summary"])

    def test_07_ada_abstain_query_structured_contract(self):
        mgr = MultiProviderLLMManager(gemini_api_key=None, groq_api_key=None)
        ada = ArbitrationDecisionAssistant(llm_manager=mgr)
        res = ada.analyze_situation("reglas de fuera de juego en baloncesto nba y formula 1")

        self.assertEqual(res["status"], "ABSTAIN")
        self.assertIn("structured_answer", res)
        struct = res["structured_answer"]
        self.assertIn("Abstención Normativa Oficial", struct["summary"])
        self.assertEqual(len(res["evidence"]), 0)


if __name__ == "__main__":
    unittest.main()

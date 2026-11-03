"""
Comprehensive Evaluation Battery for IJF SOR Assistant
======================================================
Covers the 10 core dimensions defined in the Plan Rector:
1. Direct factual queries (e.g. tatami dimensions)
2. Complex refereeing scenarios (e.g. osaekomi beyond safety boundary)
3. Cadets vs Adults rules (head diving vs cadet shido, reverse seoi-nage)
4. Spanish language queries (diacritics, ñ, technical terms)
5. Japanese terminology (ippon, waza-ari, shido, hansoku-make, osaekomi, ne-waza)
6. Ambiguous / underspecified queries (graceful handling, no false assumptions)
7. Information insufficiency / out-of-domain (strict abstention)
8. Regulatory exceptions (e.g. Art. 14.2 bridge exception landing on Tori's body)
9. Multi-article cross-referencing (rules across different pages/sections)
10. Language consistency and structure (English query -> English output; Spanish -> Spanish)
"""

import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from rre_engine import ReasoningRetrievalEngine
from ada_assistant import ArbitrationDecisionAssistant
from llm_provider import MultiProviderLLMManager


class TestComprehensiveEvaluationBattery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mgr = MultiProviderLLMManager(gemini_api_key=None, groq_api_key=None)
        cls.ada = ArbitrationDecisionAssistant(llm_manager=cls.mgr)
        cls.rre = cls.ada.rre

    def test_01_direct_factual_query_tatami(self):
        """Dimension 1: Direct factual inquiry on contest area and tatami dimensions."""
        q = "¿Cuáles son las dimensiones del tatami de competición?"
        res = self.ada.analyze_situation(q)
        self.assertEqual(res["status"], "SUCCESS")
        summary = res["structured_answer"]["summary"]
        self.assertTrue(any(dim in summary for dim in ["8", "10", "8 m", "10 m", "8x8", "10x10"]))
        # Verified citation to page 96 or Art 8.7
        self.assertTrue(any("96" in str(c.get("page_number", "")) or "8.7" in str(c.get("article_id", "")) for c in res["structured_answer"]["citations"]))

    def test_02_complex_scenario_osaekomi_boundary(self):
        """Dimension 2: Complex refereeing scenario where osaekomi exceeds the safety boundary."""
        q = "Durante un combate, se aplica osaekomi-waza y la acción continúa desplazándose hasta sobrepasar completamente el área de seguridad. ¿Qué debe señalar el árbitro?"
        res = self.ada.analyze_situation(q)
        self.assertEqual(res["status"], "SUCCESS")
        struct = res["structured_answer"]
        text_combined = (struct["summary"] + " " + struct["extended_analysis"]).lower()
        self.assertTrue("ippon" in text_combined or "sore-made" in text_combined or "17" in text_combined)
        self.assertTrue(any(c.get("page_number") == 174 or "17" in str(c.get("article_id", "")) for c in struct["citations"]))

    def test_03_cadet_vs_adult_head_rule(self):
        """Dimension 3: Cadets vs Adults - head usage in throw must yield Shido under Art 18.1.4, not Hansoku-make."""
        q = "En un combate de cadetes (17 años), Tori intenta una proyección y en la acción apoya la cabeza en el tatami de forma voluntaria. ¿Qué sanción corresponde y qué artículo lo regula?"
        res = self.ada.analyze_situation(q)
        self.assertEqual(res["status"], "SUCCESS")
        struct = res["structured_answer"]
        self.assertIn("18.1.4", struct["summary"])
        self.assertIn("188", struct["summary"])
        self.assertIn("shido", struct["summary"].lower())
        # Must not confuse with direct hansoku-make for cadets
        self.assertNotIn("hansoku-make directo", struct["summary"].lower())

    def test_04_spanish_diacritics_and_enie(self):
        """Dimension 4: Spanish language with ñ, diacritics and technical vocabulary."""
        q = "¿Qué sanción se aplica a un judoka de 15 años en categoría cadete si usa la cabeza para lanzar?"
        res = self.ada.analyze_situation(q)
        self.assertEqual(res["status"], "SUCCESS")
        struct = res["structured_answer"]
        self.assertTrue("18.1.4" in struct["summary"] or "188" in struct["summary"])
        self.assertIn("shido", struct["summary"].lower())

    def test_05_japanese_refereeing_terminology(self):
        """Dimension 5: Japanese martial arts terminology correctly parsed without degradation."""
        q = "¿Cuál es la definición reglamentaria de osaekomi-waza y en qué condiciones se anuncia Osaekomi y Toketa?"
        res = self.ada.analyze_situation(q)
        self.assertEqual(res["status"], "SUCCESS")
        struct = res["structured_answer"]
        text_combined = (struct["summary"] + " " + struct["extended_analysis"]).lower()
        self.assertTrue("osaekomi" in text_combined or "toketa" in text_combined or "17" in text_combined)
        self.assertTrue(any(c.get("page_number") in (173, 174) for c in struct["citations"]))

    def test_06_ambiguous_or_underspecified_query(self):
        """Dimension 6: Underspecified query must declare limitations and not hallucinate unstated facts."""
        q = "El judoka cometió una falta con el agarre."
        res = self.ada.analyze_situation(q)
        self.assertIn(res["status"], ["SUCCESS", "ABSTAIN"])
        if res["status"] == "SUCCESS":
            struct = res["structured_answer"]
            self.assertTrue(len(struct["limitations"]) > 10)

    def test_07_out_of_domain_strict_abstention(self):
        """Dimension 7: Queries about non-judo sports must be rejected via strict abstention."""
        q = "reglas de fuera de juego en baloncesto nba y formula 1"
        res = self.ada.analyze_situation(q)
        self.assertEqual(res["status"], "ABSTAIN")
        self.assertEqual(len(res["evidence"]), 0)
        self.assertIn("Abstención Normativa Oficial", res["structured_answer"]["summary"])

    def test_08_regulatory_exception_bridge_rule(self):
        """Dimension 8: Regulatory exceptions - Art. 14.2 bridge exception landing on Tori's body."""
        q = "Si Uke hace un puente voluntario al caer de una proyeccion pero aterriza sobre el cuerpo de Tori sin tocar el tatami con la cabeza, ¿se otorga Ippon?"
        res = self.ada.analyze_situation(q)
        self.assertEqual(res["status"], "SUCCESS")
        struct = res["structured_answer"]
        # Must cite page 166 or 167 (Article 14.2)
        pages = [c.get("page_number") for c in struct["citations"]]
        self.assertTrue(166 in pages or 167 in pages)

    def test_09_multi_article_cross_referencing(self):
        """Dimension 9: Multi-article cross-referencing across different chapters."""
        q = "Procedimiento de control de judogi en relacion a las medidas de la manga con sokuteiki y colores autorizados."
        res = self.ada.analyze_situation(q)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertTrue(len(res["evidence"]) >= 2)
        # Should contain references to Appendix C (C1.9, C1.10, etc.)
        articles = [str(e.get("article_id", "")) for e in res["evidence"]]
        self.assertTrue(any("c1" in a.lower() for a in articles))

    def test_10_language_consistency_english(self):
        """Dimension 10: English query receives English structuring in offline deterministic mode."""
        q = "What are the rules regarding judogi colours in official IJF competitions?"
        res = self.ada.analyze_situation(q, language="en")
        self.assertEqual(res["status"], "SUCCESS")
        struct = res["structured_answer"]
        # Summary should have Page or Article in English
        self.assertTrue("Page" in struct["summary"] or "Art." in struct["summary"])
        self.assertTrue(any("c1.9" in str(c.get("article_id", "")).lower() or 124 == c.get("page_number") for c in struct["citations"]))


if __name__ == "__main__":
    unittest.main()

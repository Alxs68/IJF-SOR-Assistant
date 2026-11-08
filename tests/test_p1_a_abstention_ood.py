"""
Formal Automated Test Suite for Phase P1-A: Calibrated Abstention and OOD Detection.
Enforces the contracts verified in the P1-A audit:
- Non-immunizable unregulated aspects (salary, fees, Kodokan 1882)
- Repealed historical rules (Koka, Chui, 2012)
- Future cycles (LA28, 2030)
- Substantive relevance guard in DocumentValidator (socks, extreme temp, specific dojos)
- Preservation of in-domain queries
"""

import os
import sys
import unittest

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, "src"))

from negative_domain_anchor_scoring import (
    NegativeDomainAnchorScorer,
    NegativeDomainCategory,
    NegativeDomainDecision
)
from ood_detector import OODDetector
from document_governance import EvidenceItem, EvidenceRole, DocumentAuthority, ValidityStatus, EligibilityStatus
from document_validator import DocumentValidator
from llm_provider import MultiProviderLLMManager
from rag_engine import RagEngine


class TestP1AAbstentionAndOOD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_dir = r"C:\PROYECTOS\IJF-SOR-Assistant"
        cls.validator = DocumentValidator()
        cls.ood_detector = OODDetector()
        cls.local_mgr = MultiProviderLLMManager(gemini_api_key=None, groq_api_key=None)
        cls.engine = RagEngine(cls.root_dir, llm_manager=cls.local_mgr)

    def test_01_negative_domain_motorsport_f1(self):
        """Motorsport / F1 pit lane must trigger confirmed negative OOD."""
        query = "¿Qué penalización aplica por superar el límite de velocidad en el pit lane en Fórmula 1?"
        res = NegativeDomainAnchorScorer.score_negative_domain(query)
        self.assertTrue(res.is_ood)
        self.assertIn("MOTORSPORT", res.detected_domains)
        self.assertEqual(res.decision, NegativeDomainDecision.CONFIRMED_NEGATIVE_OOD)

    def test_02_negative_domain_unregulated_salary_conditioned_immunity(self):
        """Query asking about judoka salary must NOT be immunized by the word judoka."""
        query = "¿Cuál es el salario promedio anual de un judoka profesional en Europa?"
        res = NegativeDomainAnchorScorer.score_negative_domain(query)
        self.assertTrue(res.is_ood)
        self.assertIn("UNREGULATED_JUDO", res.detected_domains)
        self.assertEqual(res.decision, NegativeDomainDecision.CONFIRMED_NEGATIVE_OOD)

    def test_03_negative_domain_historical_koka_repealed(self):
        """Koka score was abolished in 2008; query must trigger HISTORICAL_SUPERSEDED OOD."""
        query = "¿Cuál es la puntuación y valor técnico de un Koka en el judo?"
        res = NegativeDomainAnchorScorer.score_negative_domain(query)
        self.assertTrue(res.is_ood)
        self.assertIn("HISTORICAL_SUPERSEDED", res.detected_domains)

    def test_04_negative_domain_future_la28_and_2030(self):
        """Future LA28 cycle and 2030 changes must trigger FUTURE_CHANGES OOD."""
        q_la28 = "¿A partir de qué evento se congelan las reglas para el ciclo olímpico LA28?"
        res_la28 = NegativeDomainAnchorScorer.score_negative_domain(q_la28)
        self.assertTrue(res_la28.is_ood)
        self.assertIn("FUTURE_CHANGES", res_la28.detected_domains)

        q_2030 = "¿Qué cambios reglamentarios aprobó el congreso de la IJF para entrar en vigor en 2030?"
        res_2030 = NegativeDomainAnchorScorer.score_negative_domain(q_2030)
        self.assertTrue(res_2030.is_ood)
        self.assertIn("FUTURE_CHANGES", res_2030.detected_domains)

    def test_05_substantive_relevance_socks_rejected(self):
        """Substantive relevance guard rejects referee socks when evidence does not mention socks."""
        query = "¿Cuál es el color oficial de los calcetines permitidos al árbitro central durante el combate de judo?"
        dummy_item = EvidenceItem(
            evidence_id="SOR-2026-08-P137-S176",
            document_id="DOC-SOR-2026-08",
            content_text="The referee must wear the official suit and maintain professional neutrality on the tatami.",
            role=EvidenceRole.NORMA_PRIMARIA,
            authority=DocumentAuthority.TIER_1_NORMATIVE_PRIMARY,
            validity=ValidityStatus.VIGENTE,
            eligibility=EligibilityStatus.ELIGIBLE_DECISORIA,
            semantic_relevance_score=0.85
        )
        is_substantive, reason = self.validator.evaluate_substantive_relevance(query, [dummy_item])
        self.assertFalse(is_substantive)
        self.assertIn("calcetines", reason.lower())

    def test_06_substantive_relevance_extreme_temperature_rejected(self):
        """Substantive relevance guard rejects 35 degree temperature when evidence lacks temperature rules."""
        query = "¿Qué modelo de judogi debe usar el árbitro si la temperatura en el tatami supera los 35 grados?"
        dummy_item = EvidenceItem(
            evidence_id="SOR-2026-08-P096-S114",
            document_id="DOC-SOR-2026-08",
            content_text="The contest area shall be a minimum of 8 m x 8 m. Referees shall ensure athlete safety.",
            role=EvidenceRole.NORMA_PRIMARIA,
            authority=DocumentAuthority.TIER_1_NORMATIVE_PRIMARY,
            validity=ValidityStatus.VIGENTE,
            eligibility=EligibilityStatus.ELIGIBLE_DECISORIA,
            semantic_relevance_score=0.85
        )
        is_substantive, reason = self.validator.evaluate_substantive_relevance(query, [dummy_item])
        self.assertFalse(is_substantive)
        self.assertIn("temperatura", reason.lower())

    def test_07_substantive_relevance_tokyo_dojo_rejected(self):
        """Substantive relevance guard rejects unofficial weigh-in in Tokyo dojo."""
        query = "¿En qué tatami del dojo central de Tokio debe realizarse el pesaje no oficial matutino?"
        dummy_item = EvidenceItem(
            evidence_id="SOR-2026-08-P077-S091",
            document_id="DOC-SOR-2026-08",
            content_text="The official weigh-in shall take place on the evening before the contest.",
            role=EvidenceRole.NORMA_PRIMARIA,
            authority=DocumentAuthority.TIER_1_NORMATIVE_PRIMARY,
            validity=ValidityStatus.VIGENTE,
            eligibility=EligibilityStatus.ELIGIBLE_DECISORIA,
            semantic_relevance_score=0.85
        )
        is_substantive, reason = self.validator.evaluate_substantive_relevance(query, [dummy_item])
        self.assertFalse(is_substantive)
        self.assertIn("tokio", reason.lower())

    def test_08_substantive_relevance_valid_tatami_accepted(self):
        """Substantive relevance guard accepts legitimate tatami dimensions query against Art 8.7."""
        query = "¿Cuáles son las dimensiones mínimas y máximas del área de combate del tatami?"
        dummy_item = EvidenceItem(
            evidence_id="SOR-2026-08-P096-S114",
            document_id="DOC-SOR-2026-08",
            content_text="The contest area shall be a minimum of 8 m x 8 m and a maximum of 10 m x 10 m. The safety area shall be 3 m minimum.",
            role=EvidenceRole.NORMA_PRIMARIA,
            authority=DocumentAuthority.TIER_1_NORMATIVE_PRIMARY,
            validity=ValidityStatus.VIGENTE,
            eligibility=EligibilityStatus.ELIGIBLE_DECISORIA,
            semantic_relevance_score=0.85
        )
        is_substantive, reason = self.validator.evaluate_substantive_relevance(query, [dummy_item])
        self.assertTrue(is_substantive)
        self.assertIsNone(reason)

    def test_09_end_to_end_abstention_on_unregulated_query(self):
        """End-to-end RagEngine.query cleanly abstains on unregulated salary query."""
        res = self.engine.query("¿Cuál es el salario promedio anual de un judoka profesional en Europa?")
        ans = res.get("answer", "")
        kuns = res.get("retrieved_kuns", [])
        self.assertEqual(len(kuns), 0)
        self.assertTrue("Abstención" in ans or "no encuentra respaldo" in ans)

    def test_10_end_to_end_in_domain_preserved(self):
        """End-to-end RagEngine.query returns verified answer on tatami dimensions."""
        res = self.engine.query("¿Cuáles son las dimensiones mínimas y máximas del área de combate del tatami?")
        ans = res.get("answer", "")
        kuns = res.get("retrieved_kuns", [])
        self.assertGreaterEqual(len(kuns), 1)
        self.assertIn("SOR-2026-08-P096-S114", kuns)
        self.assertIn("8 m x 8 m", ans)


if __name__ == "__main__":
    unittest.main()

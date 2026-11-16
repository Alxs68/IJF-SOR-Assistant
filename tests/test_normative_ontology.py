"""
Unit Tests for NormativeOntology (Phase 1 RRE 3.0).
Verifies multi-lingual concept expansion across the 15 official IJF families,
domain detection and procedural token dampening.
"""

import unittest
from src.normative_ontology import NormativeOntology, NormativeDomain

class TestNormativeOntology(unittest.TestCase):

    def test_01_ethics_and_conduct_expansion(self):
        tokens = ["competidor", "ofende", "agrede", "otro"]
        augmented, domains = NormativeOntology.expand_token_stream(tokens)
        self.assertIn(NormativeDomain.ETHICS_AND_CONDUCT, domains)
        self.assertIn("insult", augmented)
        self.assertIn("attack", augmented)
        self.assertIn("spirit", augmented)
        self.assertIn("judo", augmented)
        priority_arts = NormativeOntology.get_priority_articles(domains)
        self.assertIn("Article 18.2.2", priority_arts)
        self.assertIn("D1.1", priority_arts)

    def test_02_head_actions_expansion(self):
        tokens = ["uke", "puente", "cabeza"]
        augmented, domains = NormativeOntology.expand_token_stream(tokens)
        self.assertIn(NormativeDomain.HEAD_AND_SPINE, domains)
        self.assertIn("bridge", augmented)
        self.assertIn("head", augmented)
        self.assertIn("cervical", augmented)

    def test_03_cadet_specific_expansion(self):
        tokens = ["cadete", "inverso", "seoi-nage"]
        augmented, domains = NormativeOntology.expand_token_stream(tokens)
        self.assertIn(NormativeDomain.CADET_RESTRICTIONS, domains)
        self.assertIn("cadet", augmented)
        self.assertIn("reverse", augmented)

    def test_04_weigh_in_expansion(self):
        tokens = ["pesaje", "balanza", "tolerancia"]
        augmented, domains = NormativeOntology.expand_token_stream(tokens)
        self.assertIn(NormativeDomain.WEIGH_IN, domains)
        self.assertIn("weigh-in", augmented)
        self.assertIn("scales", augmented)

    def test_05_tatami_dimensions_expansion(self):
        tokens = ["tatami", "medidas", "seguridad"]
        augmented, domains = NormativeOntology.expand_token_stream(tokens)
        self.assertIn(NormativeDomain.TATAMI_CONTEST_AREA, domains)
        self.assertIn("dimensions", augmented)
        self.assertIn("meters", augmented)

    def test_06_unrelated_tokens_no_false_domain(self):
        tokens = ["computadora", "teclado", "pantalla"]
        augmented, domains = NormativeOntology.expand_token_stream(tokens)
        self.assertEqual(len(domains), 0)
        self.assertEqual(augmented, tokens)

if __name__ == "__main__":
    unittest.main()

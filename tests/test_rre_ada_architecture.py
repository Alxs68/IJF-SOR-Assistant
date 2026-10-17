import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from rre_engine import ReasoningRetrievalEngine
from ada_assistant import ArbitrationDecisionAssistant
from corpus_config import EDITION_2026_08

class TestRREAndADAArchitecture(unittest.TestCase):
    """
    Suite de verificación formal de la nueva arquitectura RRE (Reasoning Retrieval Engine)
    y ADA (Arbitration Decision Assistant) para el corpus IJF SOR 2026-08.
    """

    @classmethod
    def setUpClass(cls):
        os.environ['IJF_SOR_EDITION'] = EDITION_2026_08
        cls.rre = ReasoningRetrievalEngine()
        cls.ada = ArbitrationDecisionAssistant()

    def test_01_rre_dual_channel_and_rrf_retrieval(self):
        """Verifica que RRE opere con canales duales (denso y sparse) y fusión RRF."""
        self.assertIsNotNone(self.rre.dense_model)
        self.assertIsNotNone(self.rre.dense_embeddings)
        self.assertEqual(len(self.rre.passages), 554)
        
        # Consulta sobre puntuación WRL
        res = self.rre.retrieve("World Ranking List Grand Slam points", top_k=3)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertTrue(len(res["evidence"]) > 0)
        top_hit = res["evidence"][0]
        self.assertIn("passage_id", top_hit)
        self.assertIn("score", top_hit)
        self.assertIn("page", top_hit)
        self.assertTrue(top_hit["source_url"].startswith("https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/"))

    def test_02_rre_graph_guided_expansion(self):
        """Verifica que RRE expanda el contexto a través de aristas cruzadas del grafo."""
        res = self.rre.retrieve("cadet head defence shido", top_k=3, expand_graph=True)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertTrue(len(res.get("related_passages", [])) > 0)
        rel = res["related_passages"][0]
        self.assertIn("relation", rel)
        self.assertIn("source_seed", rel)

    def test_03_rre_strict_domain_abstention(self):
        """Verifica que RRE descarte consultas completamente ajenas al reglamento."""
        res = self.rre.retrieve("reglas de fuera de juego en baloncesto nba y formula 1")
        self.assertEqual(res["status"], "ABSTAIN")
        self.assertEqual(res["reason"], "OUT_OF_DOMAIN")
        self.assertEqual(len(res["evidence"]), 0)

    def test_04_ada_arbitration_situation_analysis(self):
        """Verifica que ADA estructure dictámenes arbitrales a partir de evidencias de RRE."""
        res = self.ada.analyze_situation("¿Cómo se sanciona el uso de la cabeza para defenderse en cadetes?")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["engine"], "ADA-RRE-v2")
        self.assertTrue(len(res["evidence"]) > 0)
        self.assertIn("Dictamen", res["analysis"])
        self.assertIn("SOR-2026-08", res["analysis"])

    def test_05_ada_abstention_handling(self):
        """Verifica que ADA formule una abstención justificada ante consultas out-of-domain."""
        res = self.ada.analyze_situation("penalizaciones por parada en boxes en formula 1")
        self.assertEqual(res["status"], "ABSTAIN")
        self.assertIn("Abstención", res["analysis"])
        self.assertEqual(len(res["evidence"]), 0)

if __name__ == '__main__':
    unittest.main()

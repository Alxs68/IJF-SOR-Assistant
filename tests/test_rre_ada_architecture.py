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
        """Verifica que ADA estructure resúmenes normativos a partir de evidencias de RRE."""
        res = self.ada.analyze_situation("¿Cómo se sanciona el uso de la cabeza para defenderse en cadetes?")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["engine"], "ADA-RRE-v2")
        self.assertTrue(len(res["evidence"]) > 0)
        self.assertIn("SOR-2026-08", res["analysis"])
        self.assertTrue("Resumen de Evidencias Normativas" in res["analysis"] or "Síntesis Analítica IA" in res["analysis"])

    def test_05_ada_abstention_handling(self):
        """Verifica que ADA formule una abstención justificada ante consultas out-of-domain."""
        res = self.ada.analyze_situation("penalizaciones por parada en boxes en formula 1")
        self.assertEqual(res["status"], "ABSTAIN")
        self.assertIn("Abstención", res["analysis"])
        self.assertEqual(len(res["evidence"]), 0)

    def test_06_dense_matrix_alignment_and_integrity(self):
        """Verifica que la matriz densa pre-computada coincida 1:1 con los 554 pasajes normativos."""
        self.assertEqual(self.rre.dense_embeddings.shape, (554, 384))
        self.assertEqual(self.rre.dense_meta.get("num_passages"), 554)
        self.assertEqual(self.rre.dense_meta.get("dimension"), 384)
        self.assertEqual(self.rre.dense_meta.get("source_sha256").lower(), "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620")
        self.assertEqual(len(self.rre.dense_meta.get("passage_ids", [])), 554)
        # Verificar alineación de los primeros y últimos IDs
        self.assertEqual(self.rre.dense_meta["passage_ids"][0], self.rre.passages[0]["passage_id"])
        self.assertEqual(self.rre.dense_meta["passage_ids"][-1], self.rre.passages[-1]["passage_id"])

    def test_07_rag_engine_separation_for_2026_08(self):
        """Verifica que RagEngine delegue a RRE sin inicializar vector store legacy para 2026-08."""
        from rag_engine import RagEngine
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        engine = RagEngine(repo_root)
        self.assertTrue(engine.is_2026_08)
        self.assertIsNotNone(engine.ada)
        self.assertIsNotNone(engine.rre)
        self.assertIsNone(engine.vs)  # Legacy VectorStore no debe instanciarse para agosto 2026
        
        # Test query delegación
        query_res = engine.query("¿Cuáles son las dimensiones del tatami?")
        self.assertIn("query", query_res)
        self.assertTrue(len(query_res["retrieved_kuns"]) > 0)
        self.assertIn("SOR-2026-08", query_res["answer"])

if __name__ == '__main__':
    unittest.main()

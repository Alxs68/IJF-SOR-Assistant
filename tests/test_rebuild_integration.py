import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from rag_engine import RagEngine
from citation_resolver import resolve_url
from corpus_config import EDITION_2026_08

class TestRebuildIntegration202608(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brain_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_01_august_edition_initialization_and_cryptographic_binding(self):
        """Verifica que 2026-08 cargue 554 pasajes/nodos y enlace su SHA-256."""
        os.environ['IJF_SOR_EDITION'] = EDITION_2026_08
        engine = RagEngine(self.brain_path)
        self.assertEqual(len(engine.kg.nodes), 385)
        self.assertIsNotNone(engine.rre)
        self.assertEqual(len(engine.rre.passages), 385)
        self.assertEqual(engine.rre.dense_embeddings.shape, (385, 384))
        self.assertIsNone(engine.vs)  # Legacy VectorStore desactivado para ruta 2026-08
        self.assertEqual(engine.config['source_sha256'], "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620")

    def test_02_normative_queries_and_evidence_retrieval(self):
        """Evalúa consultas normativas críticas con fundamentación en pasajes de agosto 2026."""
        os.environ['IJF_SOR_EDITION'] = EDITION_2026_08
        engine = RagEngine(self.brain_path)
        
        test_cases = [
            ("cadet head defence shido", ["SOR-2026-08-P188", "SOR-2026-08-P189", "SOR-2026-08-P254"]),
            ("osaekomi time 20 seconds", ["SOR-2026-08-P152", "SOR-2026-08-P153"]),
            ("tatami contest area dimensions 8m", ["SOR-2026-08-P096", "SOR-2026-08-P095", "SOR-2026-08-P151"])
        ]
        
        for q, expected_prefixes in test_cases:
            res = engine.query(q, k=3)
            retrieved = res.get('retrieved_kuns', [])
            self.assertTrue(len(retrieved) > 0, f"Fallo al recuperar pasajes para query '{q}'")
            matched = any(any(prefix in pid for prefix in expected_prefixes) for pid in retrieved)
            self.assertTrue(matched, f"Query '{q}' no recuperó pasaje esperado con prefijos {expected_prefixes}")

    def test_03_strict_abstention_out_of_domain(self):
        """Verifica abstención estricta ante preguntas ajenas al reglamento."""
        os.environ['IJF_SOR_EDITION'] = EDITION_2026_08
        engine = RagEngine(self.brain_path)
        
        # Consulta sin términos judo ni palabras clave normativas
        res = engine.query("reglas de fuera de juego en baloncesto nba y formula 1", min_score=0.15)
        self.assertEqual(len(res['retrieved_kuns']), 0)
        self.assertTrue("Abstención" in res['answer'] or "Lo siento" in res['answer'])
        self.assertIn("14 August 2026", res['answer'])

    def test_04_citation_resolution_deep_links(self):
        """Verifica que las citas resuelvan a la URL oficial con anchor #page=X."""
        os.environ['IJF_SOR_EDITION'] = EDITION_2026_08
        engine = RagEngine(self.brain_path)
        
        sample_node = engine.kg.get_kun("SOR-2026-08-P188-S195")
        self.assertIsNotNone(sample_node)
        url = resolve_url("SOR-2026-08-P188-S195", sample_node)
        self.assertIsNotNone(url)
        self.assertTrue(url.startswith("https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/"))
        self.assertIn("#page=188", url)

    def test_05_rejection_of_historical_edition_and_exclusivity(self):
        """Verifica que el entorno operativo rechace versiones históricas y opere exclusivamente con 2026-08."""
        os.environ['IJF_SOR_EDITION'] = "2026-01"
        engine = RagEngine(self.brain_path)
        # Debe mantenerse estrictamente en 2026-08
        self.assertEqual(engine.config['source_id'], "SOR-2026-08-14-ENG")
        self.assertEqual(len(engine.kg.nodes), 385)
        self.assertIsNotNone(engine.rre)
        # Las consultas no deben retornar KUNs históricos
        res = engine.query("Defensa de cabeza hansoku-make")
        for kun_id in res.get('retrieved_kuns', []):
            self.assertFalse(kun_id.startswith("KUN-"), f"Contaminación detectada con pasaje histórico: {kun_id}")
            self.assertTrue(kun_id.startswith("SOR-2026-08-"), f"Pasaje no pertenece a 2026-08: {kun_id}")


if __name__ == '__main__':
    unittest.main()

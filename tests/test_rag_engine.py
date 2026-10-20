import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from rag_engine import RagEngine

class TestRagEngine(unittest.TestCase):
    
    def setUp(self):
        self.brain_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.engine = RagEngine(self.brain_path)

    def test_load_resources(self):
        self.assertIsNotNone(self.engine.kg)
        self.assertTrue(len(self.engine.kg.nodes) == 385)
        self.assertIsNotNone(self.engine.rre)
        self.assertEqual(len(self.engine.rre.passages), 385)

    def test_official_query_flow(self):
        # Querying an item in official 2026-08 edition
        res = self.engine.query("sokuteiki judogi control size")
        self.assertIn("query", res)
        self.assertIn("answer", res)
        retrieved = res.get("retrieved_kuns", [])
        self.assertTrue(len(retrieved) > 0)
        # Verify no KUN contamination
        for pid in retrieved:
            self.assertFalse(pid.startswith("KUN-"), f"Contaminación con KUN histórico: {pid}")
            self.assertTrue(pid.startswith("SOR-2026-08-"), f"No pertenece a 2026-08: {pid}")
        self.assertTrue(len(res["answer"]) > 0)

    def test_strict_exclusivity_ignores_legacy_env(self):
        os.environ['IJF_SOR_EDITION'] = '2026-01'
        engine_check = RagEngine(self.brain_path)
        self.assertEqual(engine_check.config['source_id'], "SOR-2026-08-14-ENG")
        self.assertEqual(len(engine_check.kg.nodes), 385)


if __name__ == '__main__':
    unittest.main()

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
        self.assertIsNotNone(self.engine.vs)
        self.assertTrue(len(self.engine.kg.nodes) > 0)

    def test_retrieve_context_with_expansion(self):
        # Retrieve context for head defense
        context_text, retrieved_kuns = self.engine.retrieve_context("defensa de cabeza", k=5)
        
        # Verify we retrieved at least KUN-0001
        retrieved_ids = [k['id_conocimiento'] for k in retrieved_kuns]
        self.assertIn("KUN-0001", retrieved_ids)
        
        # Verify graph expansion added related KUNs
        self.assertIn("KUN-0002", retrieved_ids)
        self.assertIn("KUN-0003", retrieved_ids)
        
    def test_query_flow(self):
        # Querying an item
        res = self.engine.query("sokuteiki medidas judogi")
        self.assertIn("query", res)
        self.assertIn("answer", res)
        self.assertIn("KUN-0013", res["retrieved_kuns"])
        self.assertTrue(len(res["answer"]) > 0)

if __name__ == '__main__':
    unittest.main()

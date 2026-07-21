import unittest
import os
import sys
import shutil

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from graph_manager import KnowledgeGraph

class TestKnowledgeGraph(unittest.TestCase):
    
    def setUp(self):
        self.kg = KnowledgeGraph()
        self.temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_test_dir')
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_nodes_and_edges(self):
        self.kg.add_node("KUN-0001", {"id_conocimiento": "KUN-0001", "titulo": "Test Node 1"})
        self.kg.add_node("KUN-0002", {"id_conocimiento": "KUN-0002", "titulo": "Test Node 2"})
        
        self.kg.add_edge("KUN-0001", "KUN-0002", "define_a")
        
        # Verify node retrieval
        node = self.kg.get_kun("KUN-0001")
        self.assertIsNotNone(node)
        self.assertEqual(node["titulo"], "Test Node 1")
        
        # Verify neighbors
        neighbors = self.kg.get_neighbors("KUN-0001")
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0]["id_destino"], "KUN-0002")
        self.assertEqual(neighbors[0]["tipo_relacion"], "define_a")
        self.assertEqual(neighbors[0]["direction"], "out")
        
        # Reverse edge check
        rev_neighbors = self.kg.get_neighbors("KUN-0002")
        self.assertEqual(len(rev_neighbors), 1)
        self.assertEqual(rev_neighbors[0]["id_destino"], "KUN-0001")
        self.assertEqual(rev_neighbors[0]["direction"], "in")

    def test_metrics(self):
        self.kg.add_node("KUN-0001", {"id_conocimiento": "KUN-0001"})
        self.kg.add_node("KUN-0002", {"id_conocimiento": "KUN-0002"})
        self.kg.add_node("KUN-0003", {"id_conocimiento": "KUN-0003"})
        
        self.kg.add_edge("KUN-0001", "KUN-0002", "complementa_a")
        
        metrics = self.kg.get_metrics()
        self.assertEqual(metrics["nodes_count"], 3)
        self.assertEqual(metrics["edges_count"], 1)
        self.assertEqual(metrics["orphans_count"], 1)  # KUN-0003 is isolated
        self.assertIn("KUN-0003", metrics["orphans"])
        self.assertEqual(metrics["components_count"], 2)  # {1,2} and {3}

    def test_serialization(self):
        self.kg.add_node("KUN-0001", {"id_conocimiento": "KUN-0001", "val": "A"})
        self.kg.add_node("KUN-0002", {"id_conocimiento": "KUN-0002", "val": "B"})
        self.kg.add_edge("KUN-0001", "KUN-0002", "modifica_a")
        
        json_path = os.path.join(self.temp_dir, 'graph.json')
        self.kg.save_to_json(json_path)
        
        new_kg = KnowledgeGraph()
        new_kg.load_from_json(json_path)
        
        self.assertEqual(len(new_kg.nodes), 2)
        self.assertEqual(new_kg.get_kun("KUN-0001")["val"], "A")
        self.assertEqual(len(new_kg.get_neighbors("KUN-0001")), 1)

if __name__ == '__main__':
    unittest.main()

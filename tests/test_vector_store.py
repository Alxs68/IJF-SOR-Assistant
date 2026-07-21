import unittest
import os
import sys
import shutil

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from vector_store import VectorStore

class TestVectorStore(unittest.TestCase):
    
    def setUp(self):
        self.vs = VectorStore()
        self.temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_test_dir')
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.dummy_kuns = {
            "KUN-0001": {
                "contenido_traduccion": "El uso voluntario de la cabeza para defenderse está prohibido.",
                "interpretacion": "Sanción directa con Hansoku-make por defensa de cabeza."
            },
            "KUN-0002": {
                "contenido_traduccion": "El control de judogi se realiza en el Sokuteiki.",
                "interpretacion": "Verificación de medidas de la chaqueta antes del shiai."
            }
        }
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_tokenize_normalization(self):
        tokens = self.vs._tokenize("¡Defensa de Cabéza, Rápido!")
        self.assertIn("defensa", tokens)
        self.assertIn("cabeza", tokens)
        self.assertIn("rapido", tokens)

    def test_index_and_search(self):
        self.vs.index_kun_corpus(self.dummy_kuns)
        
        # Test vocabulary indexing
        self.assertIn("cabeza", self.vs.vocabulary)
        self.assertIn("sokuteiki", self.vs.vocabulary)
        
        # Search for head defense
        results = self.vs.search("cabeza hansoku", k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id_conocimiento"], "KUN-0001")
        self.assertTrue(results[0]["score"] > 0.0)

    def test_persistence(self):
        self.vs.index_kun_corpus(self.dummy_kuns)
        
        index_file = os.path.join(self.temp_dir, 'vector_index.json')
        self.vs.save_index(index_file)
        
        new_vs = VectorStore()
        new_vs.load_index(index_file)
        
        self.assertEqual(len(new_vs.kun_ids), 2)
        results = new_vs.search("chaqueta", k=1)
        self.assertEqual(results[0]["id_conocimiento"], "KUN-0002")

if __name__ == '__main__':
    unittest.main()

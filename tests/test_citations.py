import unittest
import sys
import os
import re

# Add src to system path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from citation_resolver import resolve_url, format_citations, RESOURCE_DETAILS

class TestCitations(unittest.TestCase):
    
    def setUp(self):
        # Mocks of KUN data representing different types of sources (without duplicate URLs where catalog fallback is tested)
        self.kun_pdf_structured = {
            "id_conocimiento": "KUN-0001",
            "fuente_origen": "DOC-001",
            "fuente": {
                "tipo": "pdf",
                "pagina": 181
            }
        }
        
        self.kun_video_structured = {
            "id_conocimiento": "KUN-0004",
            "fuente_origen": "VID-004",
            "fuente": {
                "tipo": "video",
                "url": "https://www.youtube.com/watch?v=uK8fF41wOqI",
                "inicio_segundos": 220
            }
        }
        
        self.kun_web_structured = {
            "id_conocimiento": "KUN-0023",
            "fuente_origen": "PAG-002",
            "fuente": {
                "tipo": "web"
            }
        }
        
        # Backward compatibility KUNs (no 'fuente' block)
        self.kun_pdf_compat = {
            "id_conocimiento": "KUN-0101",
            "fuente_origen": "DOC-001",
            "referencia_especifica": "Artículo 18.2, Página 181"
        }
        
        self.kun_video_compat = {
            "id_conocimiento": "KUN-0202",
            "fuente_origen": "VID-001",
            "referencia_especifica": "Marca de tiempo 05:15 - Clip 2"
        }

    def test_resolve_url_pdf_structured(self):
        url = resolve_url("KUN-0001", self.kun_pdf_structured)
        expected = "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/IJF_Sport_and_Organisation_Rul-1769443746.pdf#page=181"
        self.assertEqual(url, expected)

    def test_resolve_url_video_structured(self):
        url = resolve_url("KUN-0004", self.kun_video_structured)
        # Bajo RRM, KUN-0004 está marcada como DELETED, por lo que retorna None
        self.assertIsNone(url)

    def test_resolve_url_web_structured(self):
        url = resolve_url("KUN-0023", self.kun_web_structured)
        expected = "https://rules.ijf.org/gripping"
        self.assertEqual(url, expected)

    def test_resolve_url_pdf_compatibility(self):
        url = resolve_url("KUN-0101", self.kun_pdf_compat)
        expected_base = RESOURCE_DETAILS["DOC-001"]["url"]
        expected = f"{expected_base}#page=181"
        self.assertEqual(url, expected)

    def test_resolve_url_video_compatibility(self):
        url = resolve_url("KUN-0202", self.kun_video_compat)
        # Bajo RRM, VID-001 se resuelve a la URL migrada
        expected = "https://referee.ijf.org"
        self.assertEqual(url, expected)

    def test_format_citations_valid_and_retrieved(self):
        answer = "La defensa de cabeza se penaliza [KUN-0001], mientras que el agarre normal está permitido [KUN-0023]."
        retrieved_kuns = [self.kun_pdf_structured, self.kun_web_structured]
        
        formatted = format_citations(answer, retrieved_kuns)
        
        expected_link_1 = "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/IJF_Sport_and_Organisation_Rul-1769443746.pdf#page=181"
        expected_link_2 = "https://rules.ijf.org/gripping"
        
        self.assertIn(f"[KUN-0001]({expected_link_1})", formatted)
        self.assertIn(f"[KUN-0023]({expected_link_2})", formatted)

    def test_format_citations_not_retrieved_remains_plain(self):
        # KUN-0004 is cited but NOT retrieved
        answer = "Muestra de video de defensa [KUN-0004]."
        retrieved_kuns = [self.kun_pdf_structured] # Only KUN-0001 retrieved
        
        formatted = format_citations(answer, retrieved_kuns)
        self.assertEqual(formatted, "Muestra de video de defensa [KUN-0004].")

    def test_formatted_citations_correspond_to_retrieved_kuns(self):
        # Generamos una respuesta formateada de RAG
        answer = "De acuerdo con [KUN-0001], head diving es hansoku-make. Para cadetes se aplica [KUN-0047]. Y no se recuperó [KUN-9999]."
        retrieved_kuns = [
            {
                "id_conocimiento": "KUN-0001",
                "fuente_origen": "DOC-001",
                "fuente": {
                    "tipo": "pdf",
                    "pagina": 181
                }
            },
            {
                "id_conocimiento": "KUN-0047",
                "fuente_origen": "DOC-004",
                "fuente": {
                    "tipo": "pdf",
                    "pagina": 269
                }
            }
        ]
        
        formatted = format_citations(answer, retrieved_kuns)
        
        # Extraer todos los enlaces de la forma [KUN-xxxx](url)
        links = re.findall(r'\[(KUN-\d{4})\]\((.*?)\)', formatted)
        
        # Debe haber exactamente 2 enlaces convertidos (KUN-0001 y KUN-0047)
        self.assertEqual(len(links), 2)
        
        # Verificar que todos los IDs enlazados estén en la lista de KUNs recuperadas
        retrieved_ids = {k["id_conocimiento"] for k in retrieved_kuns}
        for kun_id, url in links:
            self.assertIn(kun_id, retrieved_ids)
            self.assertTrue(url.startswith("http"))
            
        # Y KUN-9999 debe permanecer como texto plano [KUN-9999] sin ser enlazado
        self.assertIn("[KUN-9999]", formatted)
        self.assertNotIn("[KUN-9999](", formatted)

    def test_non_regression_reused_context(self):
        # Ensures that a RAG query returns exact retrieved KUNs matching the citations resolved
        from rag_engine import RagEngine
        # Instantiate engine using the local path
        brain_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        engine = RagEngine(brain_path)
        
        # Test query flow
        res = engine.query("defensa de cabeza")
        self.assertIn("answer", res)
        self.assertIn("retrieved_kuns", res)
        self.assertIn("retrieved_kuns_data", res)
        
        # Verify that all dicts in retrieved_kuns_data match the retrieved_kuns IDs list
        retrieved_ids = res["retrieved_kuns"]
        retrieved_data_ids = [k["id_conocimiento"] for k in res["retrieved_kuns_data"]]
        self.assertEqual(sorted(retrieved_ids), sorted(retrieved_data_ids))

    def test_rules_ijf_deep_links(self):
        # Test that rules.ijf.org SPA URLs resolve to the exact slide page in the detailed PDF
        kun_false_attack = {
            "id_conocimiento": "KUN-0028",
            "fuente_origen": "PAG-004",
            "referencia_especifica": "rules.ijf.org/penalties/false-attack"
        }
        url = resolve_url("KUN-0028", kun_false_attack)
        expected = "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2023/04/Detailed_Explanation_of_the_IJF_Judo_Refereeing_Rules_25.03.2023.pdf#page=24"
        self.assertEqual(url, expected)

if __name__ == '__main__':
    unittest.main()

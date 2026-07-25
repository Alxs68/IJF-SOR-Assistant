import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from reference_manager import ReferenceManager
from citation_resolver import resolve_url, format_citations

class TestReferenceManager(unittest.TestCase):
    def setUp(self):
        # Usar el registro real de pruebas (cargado de la ubicación oficial de datos)
        self.manager = ReferenceManager()

    def test_registry_loading(self):
        # Verificar que el registro maestro esté cargado y contenga claves esperadas
        self.assertIn("DOC-001", self.manager.registry)
        self.assertIn("VID-002", self.manager.registry)
        self.assertIn("https://www.youtube.com/watch?v=uK8fF41wOqI", self.manager.registry)

    def test_resolve_available_pdf(self):
        # KUN-0001 (fuente_origen: DOC-001, referenciada en página 181)
        kun_data = {
            "id_conocimiento": "KUN-0001",
            "fuente_origen": "DOC-001",
            "referencia_especifica": "Apéndice D (Artículo 18.2.1), Página 181",
            "fuente": {
                "tipo": "pdf",
                "url": "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/IJF_Sport_and_Organisation_Rul-1769443746.pdf",
                "pagina": 181
            }
        }
        res = self.manager.resolve_reference("KUN-0001", kun_data)
        self.assertEqual(res["operational_status"], "AVAILABLE")
        self.assertTrue(res["is_clickable"])
        self.assertIn("#page=181", res["url"])

    def test_resolve_deleted_youtube_video(self):
        # KUN-0004 (YouTube uK8fF41wOqI es DELETED en el registro)
        kun_data = {
            "id_conocimiento": "KUN-0004",
            "fuente_origen": "VID-004",
            "referencia_especifica": "Marca de tiempo 03:40 - Clip 14",
            "fuente": {
                "tipo": "video",
                "url": "https://www.youtube.com/watch?v=uK8fF41wOqI",
                "inicio_segundos": 220
            }
        }
        res = self.manager.resolve_reference("KUN-0004", kun_data)
        self.assertEqual(res["operational_status"], "DELETED")
        self.assertFalse(res["is_clickable"])
        self.assertIsNone(res["url"])
        self.assertIn("Fuente dada de baja", res["ux_message"])

    def test_resolve_fallback_general_rules_portal(self):
        # KUN-0059 (fuente_origen: VID-002)
        kun_data = {
            "id_conocimiento": "KUN-0059",
            "fuente_origen": "VID-002",
            "referencia_especifica": "Grip Breaking Clarifications - Clip 1"
        }
        res = self.manager.resolve_reference("KUN-0059", kun_data)
        self.assertEqual(res["operational_status"], "FALLBACK_GENERAL")
        self.assertTrue(res["is_clickable"])
        self.assertEqual(res["url"], "https://rules.ijf.org/gripping")

    def test_resolve_migrated_videos_list(self):
        # KUN-0071 (fuente_origen: VID-001)
        kun_data = {
            "id_conocimiento": "KUN-0071",
            "fuente_origen": "VID-001",
            "referencia_especifica": "Official Refereeing & Coaching Seminar Playlist Index"
        }
        res = self.manager.resolve_reference("KUN-0071", kun_data)
        self.assertEqual(res["operational_status"], "MIGRATED")
        self.assertTrue(res["is_clickable"])
        self.assertEqual(res["url"], "https://referee.ijf.org")

    def test_resolve_fallback_unregistered(self):
        # KUN con un source_id que no existe en el registro
        kun_data = {
            "id_conocimiento": "KUN-9999",
            "fuente_origen": "UNREGISTERED-SRC",
            "referencia_especifica": "Sección Desconocida",
            "fuente": {
                "tipo": "pdf",
                "url": "https://example.com/unregistered.pdf",
                "pagina": 10
            }
        }
        res = self.manager.resolve_reference("KUN-9999", kun_data)
        self.assertEqual(res["operational_status"], "AVAILABLE")
        self.assertTrue(res["is_clickable"])
        self.assertEqual(res["url"], "https://example.com/unregistered.pdf#page=10")

    def test_citation_resolver_compatibility(self):
        # Validar resolve_url legado
        kun_data = {
            "id_conocimiento": "KUN-0001",
            "fuente_origen": "DOC-001",
            "referencia_especifica": "Apéndice D (Artículo 18.2.1), Página 181",
            "fuente": {
                "tipo": "pdf",
                "url": "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/IJF_Sport_and_Organisation_Rul-1769443746.pdf",
                "pagina": 181
            }
        }
        url = resolve_url("KUN-0001", kun_data)
        self.assertIn("#page=181", url)

        # Validar format_citations legado (KUN-0001 activa y KUN-0004 eliminada)
        answer = "De acuerdo a [KUN-0001] y [KUN-0004], la regla aplica."
        retrieved = [
            kun_data,
            {
                "id_conocimiento": "KUN-0004",
                "fuente_origen": "VID-004",
                "referencia_especifica": "Marca de tiempo 03:40 - Clip 14",
                "fuente": {
                    "tipo": "video",
                    "url": "https://www.youtube.com/watch?v=uK8fF41wOqI",
                    "inicio_segundos": 220
                }
            }
        ]
        formatted = format_citations(answer, retrieved)
        self.assertIn("[KUN-0001](https://", formatted)
        self.assertIn("~~[KUN-0004]~~", formatted)

if __name__ == "__main__":
    unittest.main()

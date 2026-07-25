import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
import tempfile
import urllib.error

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from reference_checker import ReferenceChecker

class TestReferenceChecker(unittest.TestCase):
    def setUp(self):
        # Crear un archivo de registro temporal de prueba
        self.temp_dir = tempfile.TemporaryDirectory()
        self.registry_path = os.path.join(self.temp_dir.name, "test_registry.json")
        
        self.initial_data = {
            "DOC-TEST-01": {
                "reference_uid": "REF-TEST-01",
                "source_id": "DOC-TEST-01",
                "version": "1.0.0",
                "type": "pdf",
                "origin_source_class": "Official PDF",
                "name": "PDF de Prueba",
                "url_original": "https://example.com/test.pdf",
                "url_resolved": "https://example.com/test.pdf",
                "operational_status": "AVAILABLE",
                "verification_status": "NOT_VERIFIED",
                "date_created": "2026-07-25T00:00:00Z",
                "date_last_checked": "2026-07-25T00:00:00Z",
                "history": []
            },
            "VID-TEST-02": {
                "reference_uid": "REF-TEST-02",
                "source_id": "VID-TEST-02",
                "version": "1.0.0",
                "type": "video",
                "origin_source_class": "Official YouTube",
                "name": "Video de Youtube de Prueba",
                "url_original": "https://youtube.com/watch?v=mockvideo",
                "url_resolved": "https://youtube.com/watch?v=mockvideo",
                "operational_status": "AVAILABLE",
                "verification_status": "NOT_VERIFIED",
                "date_created": "2026-07-25T00:00:00Z",
                "date_last_checked": "2026-07-25T00:00:00Z",
                "history": []
            }
        }
        
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(self.initial_data, f, indent=2)
            
        self.checker = ReferenceChecker(registry_path=self.registry_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('urllib.request.urlopen')
    def test_check_url_success(self, mock_urlopen):
        # Configurar mock para responder 200 OK
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html>Normal page</html>"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        is_available, reason = self.checker.check_url_status("https://example.com/test.pdf")
        self.assertTrue(is_available)
        self.assertEqual(reason, "HTTP 200 OK")

    @patch('urllib.request.urlopen')
    def test_check_url_http_error(self, mock_urlopen):
        # Configurar mock para lanzar HTTPError (ej: 404)
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://example.com/test.pdf", 404, "Not Found", {}, None
        )

        is_available, reason = self.checker.check_url_status("https://example.com/test.pdf")
        self.assertFalse(is_available)
        self.assertIn("HTTP Error 404", reason)

    @patch('urllib.request.urlopen')
    def test_check_youtube_unplayable(self, mock_urlopen):
        # Configurar mock para devolver HTML de youtube con indicador de playability erróneo
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"playabilityStatus":{"status":"UNPLAYABLE"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        is_available, reason = self.checker.check_url_status("https://youtube.com/watch?v=mockvideo")
        self.assertFalse(is_available)
        self.assertIn("YouTube video unplayable", reason)

    @patch('urllib.request.urlopen')
    def test_run_audit_updates_registry_on_failure(self, mock_urlopen):
        # Configurar mock para que el PDF devuelva 200 OK pero el Video lance 404
        def side_effect(req, timeout=None):
            url = req.full_url if hasattr(req, 'full_url') else req
            if "mockvideo" in url:
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
            mock_res = MagicMock()
            mock_res.read.return_value = b"OK"
            return mock_res

        mock_urlopen.side_effect = side_effect

        self.checker.run_audit()

        # Recargar el registro guardado
        with open(self.registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # DOC-TEST-01 debe estar AVAILABLE e historia limpia
        self.assertEqual(data["DOC-TEST-01"]["operational_status"], "AVAILABLE")
        self.assertEqual(data["DOC-TEST-01"]["verification_status"], "AUTO_VERIFIED")

        # VID-TEST-02 debe estar DELETED, verificación MANUAL_REVIEW y registrar historial
        self.assertEqual(data["VID-TEST-02"]["operational_status"], "DELETED")
        self.assertEqual(data["VID-TEST-02"]["verification_status"], "MANUAL_REVIEW")
        self.assertEqual(len(data["VID-TEST-02"]["history"]), 1)
        self.assertEqual(data["VID-TEST-02"]["history"][0]["action"], "STATUS_CHANGED")
        self.assertEqual(data["VID-TEST-02"]["history"][0]["from"], "AVAILABLE")
        self.assertEqual(data["VID-TEST-02"]["history"][0]["to"], "DELETED")

if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import io
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from llm_provider import (
    BaseLLMClient,
    GeminiClient,
    GroqClient,
    MultiProviderLLMManager,
    LLMProviderError
)
from ada_assistant import ArbitrationDecisionAssistant


class TestMultiProviderLLM(unittest.TestCase):

    def test_provider_status_and_masking(self):
        mgr = MultiProviderLLMManager(
            primary_provider="Gemini",
            gemini_api_key="AIzaSyAbc123456789SecretKey",
            groq_api_key="gsk_supersecretgroqkey999"
        )
        status = mgr.get_provider_status()
        self.assertEqual(status["primary_provider"], "Gemini")
        self.assertEqual(status["fallback_policy"], "automatic")
        
        # Verify secret masking
        gemini_masked = status["providers"]["Gemini"]["masked_key"]
        groq_masked = status["providers"]["Groq"]["masked_key"]
        self.assertNotIn("SecretKey", gemini_masked)
        self.assertNotIn("supersecretgroqkey", groq_masked)
        self.assertTrue(gemini_masked.startswith("AIza..."))
        self.assertTrue(groq_masked.startswith("gsk_..."))

    def test_missing_keys_error_classification(self):
        mgr = MultiProviderLLMManager(
            primary_provider="Groq",
            fallback_policy="manual",
            groq_api_key=None,
            gemini_api_key=None
        )
        text, meta = mgr.generate_with_fallback("Hola mundo")
        self.assertIsNone(text)
        self.assertIn("Groq", meta["errors"])
        self.assertEqual(meta["errors"]["Groq"]["error_type"], "AUTH")
        self.assertFalse(meta["fallback_triggered"])

    @patch("urllib.request.urlopen")
    def test_gemini_successful_generation(self, mock_urlopen):
        # Mock Gemini JSON response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{"text": "Síntesis arbitral oficial de Gemini."}]
                }
            }]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = GeminiClient(api_key="test_gemini_key", model="gemini-flash-latest")
        res = client.generate("Prompt arbitral")
        self.assertEqual(res, "Síntesis arbitral oficial de Gemini.")

    @patch("urllib.request.urlopen")
    def test_groq_successful_generation(self, mock_urlopen):
        # Mock Groq OpenAI-compatible chat response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{
                "message": {"role": "assistant", "content": "Síntesis arbitral oficial de Groq Llama-3."}
            }]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = GroqClient(api_key="test_groq_key", model="llama-3.3-70b-versatile")
        res = client.generate("Prompt arbitral")
        self.assertEqual(res, "Síntesis arbitral oficial de Groq Llama-3.")

    @patch("urllib.request.urlopen")
    def test_automatic_fallback_on_quota_429(self, mock_urlopen):
        # Simulate: First call (Gemini) raises 429 RESOURCE_EXHAUSTED
        # Second call (Groq) succeeds
        gemini_error_body = json.dumps({
            "error": {"code": 429, "message": "Resource exhausted retryDelay 60s"}
        }).encode('utf-8')
        gemini_error = urllib.error.HTTPError(
            url="https://generativelanguage.googleapis.com/...",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=io.BytesIO(gemini_error_body)
        )

        groq_resp = MagicMock()
        groq_resp.read.return_value = json.dumps({
            "choices": [{
                "message": {"content": "Respuesta generada por Groq tras el fallback."}
            }]
        }).encode('utf-8')
        cm_groq = MagicMock()
        cm_groq.__enter__.return_value = groq_resp

        mock_urlopen.side_effect = [gemini_error, cm_groq]

        mgr = MultiProviderLLMManager(
            primary_provider="Gemini",
            fallback_policy="automatic",
            gemini_api_key="fake_gemini_key",
            groq_api_key="fake_groq_key"
        )

        text, meta = mgr.generate_with_fallback("Consulta de prueba")
        self.assertEqual(text, "Respuesta generada por Groq tras el fallback.")
        self.assertTrue(meta["fallback_triggered"])
        self.assertEqual(meta["successful_provider"], "Groq")
        self.assertIn("Gemini", meta["errors"])
        self.assertEqual(meta["errors"]["Gemini"]["error_type"], "QUOTA")

    @patch("urllib.request.urlopen")
    def test_manual_policy_does_not_silently_fallback(self, mock_urlopen):
        gemini_error_body = json.dumps({
            "error": {"code": 429, "message": "Resource exhausted"}
        }).encode('utf-8')
        gemini_error = urllib.error.HTTPError(
            url="https://generativelanguage.googleapis.com/...",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=io.BytesIO(gemini_error_body)
        )
        mock_urlopen.side_effect = [gemini_error]

        mgr = MultiProviderLLMManager(
            primary_provider="Gemini",
            fallback_policy="manual",
            gemini_api_key="fake_gemini_key",
            groq_api_key="fake_groq_key"
        )

        text, meta = mgr.generate_with_fallback("Consulta de prueba")
        self.assertIsNone(text)
        self.assertFalse(meta["fallback_triggered"])
        self.assertEqual(meta["attempted_providers"], ["Gemini"])
        self.assertIn("Gemini", meta["errors"])

    @patch("urllib.request.urlopen")
    def test_both_providers_fail(self, mock_urlopen):
        gemini_error_body = json.dumps({"error": {"code": 429, "message": "Gemini Quota"}}).encode('utf-8')
        groq_error_body = json.dumps({"error": {"code": 503, "message": "Groq Overloaded"}}).encode('utf-8')

        err1 = urllib.error.HTTPError("url1", 429, "Too Many Requests", {}, io.BytesIO(gemini_error_body))
        err2 = urllib.error.HTTPError("url2", 503, "Service Unavailable", {}, io.BytesIO(groq_error_body))

        mock_urlopen.side_effect = [err1, err2]

        mgr = MultiProviderLLMManager(
            primary_provider="Gemini",
            fallback_policy="automatic",
            gemini_api_key="fake_gemini_key",
            groq_api_key="fake_groq_key"
        )

        text, meta = mgr.generate_with_fallback("Consulta de prueba")
        self.assertIsNone(text)
        self.assertIsNone(meta["successful_provider"])
        self.assertEqual(meta["attempted_providers"], ["Gemini", "Groq"])
        self.assertEqual(meta["errors"]["Gemini"]["error_type"], "QUOTA")
        self.assertEqual(meta["errors"]["Groq"]["error_type"], "TEMPORARY")

    @patch("urllib.request.urlopen")
    def test_ada_preserves_retrieved_evidence_through_fallback(self, mock_urlopen):
        # Gemini fails (429), Groq succeeds with synthesis
        gemini_error_body = json.dumps({"error": {"code": 429, "message": "Resource exhausted"}}).encode('utf-8')
        err1 = urllib.error.HTTPError("url1", 429, "Too Many Requests", {}, io.BytesIO(gemini_error_body))

        groq_resp = MagicMock()
        groq_resp.read.return_value = json.dumps({
            "choices": [{
                "message": {"content": "En cadetes la defensa con cabeza se penaliza con shido [SOR-2026-08-P189-S196]."}
            }]
        }).encode('utf-8')
        cm_groq = MagicMock()
        cm_groq.__enter__.return_value = groq_resp

        mock_urlopen.side_effect = [err1, cm_groq]

        mgr = MultiProviderLLMManager(
            primary_provider="Gemini",
            fallback_policy="automatic",
            gemini_api_key="fake_gemini",
            groq_api_key="fake_groq"
        )

        ada = ArbitrationDecisionAssistant(llm_manager=mgr)
        res = ada.analyze_situation("cadet head defence shido")

        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("SOR-2026-08-P189-S196", [e["passage_id"] for e in res["evidence"]])
        self.assertIn("Groq", res["mode"])
        self.assertTrue(res["llm_meta"]["fallback_triggered"])
        self.assertEqual(res["llm_meta"]["successful_provider"], "Groq")

    @patch("urllib.request.urlopen")
    def test_temporary_error_with_automatic_fallback(self, mock_urlopen):
        # Gemini raises 503 (Temporary Server Error) -> Fallback to Groq
        gemini_error = urllib.error.HTTPError("url1", 503, "Service Unavailable", {}, io.BytesIO(b'{"error": "overloaded"}'))
        groq_resp = MagicMock()
        groq_resp.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Respuesta tras 503."}}]
        }).encode('utf-8')
        cm_groq = MagicMock()
        cm_groq.__enter__.return_value = groq_resp

        mock_urlopen.side_effect = [gemini_error, cm_groq]
        mgr = MultiProviderLLMManager(primary_provider="Gemini", fallback_policy="automatic", gemini_api_key="k1", groq_api_key="k2")
        text, meta = mgr.generate_with_fallback("Test 503")
        self.assertEqual(text, "Respuesta tras 503.")
        self.assertTrue(meta["fallback_triggered"])
        self.assertEqual(meta["successful_provider"], "Groq")

    @patch("urllib.request.urlopen")
    def test_nonexistent_model_404_error(self, mock_urlopen):
        err_404 = urllib.error.HTTPError("url1", 404, "Not Found", {}, io.BytesIO(b'{"error": {"message": "Model not found"}}'))
        mock_urlopen.side_effect = err_404

        client = GroqClient(api_key="valid_key", model="nonexistent-model-xyz")
        with self.assertRaises(LLMProviderError) as ctx:
            client.generate("Test 404")
        self.assertEqual(ctx.exception.error_type, "NOT_FOUND")
        self.assertEqual(ctx.exception.status_code, 404)

    def test_secret_redaction_in_exceptions(self):
        secret_key = "gsk_SUPER_CONFIDENTIAL_KEY_12345"
        client = GroqClient(api_key=secret_key, model="llama-3.3-70b-versatile")
        
        # Simulate an HTTP error containing the raw secret key in the error message body
        http_err = urllib.error.HTTPError(
            "url", 401, "Unauthorized", {},
            io.BytesIO(f'{{"error": {{"message": "Invalid auth token: {secret_key}"}}}}'.encode('utf-8'))
        )
        with patch("urllib.request.urlopen", side_effect=http_err):
            with self.assertRaises(LLMProviderError) as ctx:
                client.generate("Test redaction")
            msg = str(ctx.exception)
            self.assertNotIn(secret_key, msg)
            self.assertIn("[REDACTED_API_KEY]", msg)

    def test_out_of_domain_abstains_without_calling_llm(self):
        mgr = MultiProviderLLMManager(gemini_api_key="k1", groq_api_key="k2")
        ada = ArbitrationDecisionAssistant(llm_manager=mgr)
        
        # An OOD query should abstain directly without invoking any LLM
        with patch.object(mgr, "generate_with_fallback") as mock_gen:
            res = ada.analyze_situation("reglas de fuera de juego en baloncesto nba y formula 1")
            self.assertEqual(res["status"], "ABSTAIN")
            mock_gen.assert_not_called()

    def test_ada_deterministic_offline_mode_does_not_hallucinate(self):
        # When both providers are unavailable or fail, verify that ADA generates a structured,
        # verifiable legal brief without claiming to be generated by an AI model.
        mgr = MultiProviderLLMManager(
            primary_provider="Gemini",
            fallback_policy="automatic",
            gemini_api_key=None,
            groq_api_key=None
        )
        ada = ArbitrationDecisionAssistant(llm_manager=mgr)
        res = ada.analyze_situation("¿Cuáles son las dimensiones del tatami?")

        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("Modo Local Desconectado", res["mode"])
        self.assertNotIn("Síntesis Analítica IA", res["analysis"])
        self.assertIn("Resumen de Evidencias Normativas — Modo Local Desconectado", res["analysis"])
        self.assertIn("Aviso de Operación Local", res["analysis"])
        # Must retain physical page grounding and verifiable passage ids
        self.assertTrue(len(res["evidence"]) > 0)
        self.assertIn("SOR-2026-08-P096-S114", [e["passage_id"] for e in res["evidence"]])
        self.assertEqual(res["llm_meta"]["successful_provider"], None)

    def test_groq_user_agent_header(self):
        client = GroqClient(api_key="fake_key", model="openai/gpt-oss-120b")
        self.assertIn("Chrome/", client.DEFAULT_USER_AGENT)
        self.assertIn("IJF-SOR-Assistant", client.DEFAULT_USER_AGENT)

    @patch("urllib.request.urlopen")
    def test_timeout_and_empty_response_handling(self, mock_urlopen):
        # 1. Test timeout / URLError classification as TEMPORARY
        import urllib.error
        import socket
        mock_urlopen.side_effect = urllib.error.URLError(socket.timeout("The read operation timed out"))
        client = GroqClient(api_key="fake_key", model="openai/gpt-oss-120b")
        with self.assertRaises(LLMProviderError) as ctx:
            client.generate("Test prompt")
        self.assertEqual(ctx.exception.error_type, "TEMPORARY")

        # 2. Test empty / whitespace response classification as CONTENT
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"choices": [{"message": {"content": ""}}]}).encode('utf-8')
        mock_urlopen.side_effect = None
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        
        # When empty string returned
        res = client.generate("Test prompt")
        self.assertEqual(res, "")

    def test_deprecated_model_auto_corrected_to_supported_default(self):
        mgr = MultiProviderLLMManager(
            primary_provider="Groq",
            groq_model="llama-3.3-70b-versatile"  # deprecated model
        )
        self.assertEqual(mgr.groq_model, "openai/gpt-oss-120b")


if __name__ == "__main__":
    unittest.main()

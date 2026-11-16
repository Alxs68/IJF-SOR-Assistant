import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from llm_provider import (
    GeminiClient,
    GroqClient,
    MultiProviderLLMManager,
    LLMProviderError
)
from ada_assistant import ArbitrationDecisionAssistant
from tests._ada_contract_helpers import (
    StubLLM, answer_citing, cite_first_delivered, citation_ids,
    delivered_ids_in_result, delivered_primary_ids, ABSTENTION_MARKER, TRANSLATION_MARKER,
)

class TestLLMFallbackScenarios(unittest.TestCase):

    def test_scenario_1_gemini_succeeds(self):
        gemini_resp = MagicMock()
        gemini_resp.read.return_value = json.dumps({
            "candidates": [{"content": {"parts": [{"text": "Gemini official answer."}]}}]
        }).encode("utf-8")
        cm_gemini = MagicMock()
        cm_gemini.__enter__.return_value = gemini_resp

        with patch("urllib.request.urlopen", return_value=cm_gemini):
            mgr = MultiProviderLLMManager(
                primary_provider="Gemini",
                fallback_policy="automatic",
                gemini_api_key="valid_gemini_key",
                groq_api_key="valid_groq_key"
            )
            text, meta = mgr.generate_with_fallback("Test query")
            self.assertEqual(text, "Gemini official answer.")
            self.assertEqual(meta["successful_provider"], "Gemini")
            self.assertFalse(meta["fallback_triggered"])
            self.assertEqual(meta["attempted_providers"], ["Gemini"])

    def test_scenario_2_gemini_429_groq_succeeds(self):
        gemini_err_body = json.dumps({"error": {"code": 429, "message": "Resource exhausted"}}).encode("utf-8")
        gemini_429 = urllib.error.HTTPError("https://...", 429, "Too Many Requests", {}, io.BytesIO(gemini_err_body))

        groq_resp = MagicMock()
        groq_resp.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Groq fallback answer."}}]
        }).encode("utf-8")
        cm_groq = MagicMock()
        cm_groq.__enter__.return_value = groq_resp

        with patch("urllib.request.urlopen", side_effect=[gemini_429, cm_groq]):
            mgr = MultiProviderLLMManager(
                primary_provider="Gemini",
                fallback_policy="automatic",
                gemini_api_key="valid_gemini_key",
                groq_api_key="valid_groq_key"
            )
            text, meta = mgr.generate_with_fallback("Test query")
            self.assertEqual(text, "Groq fallback answer.")
            self.assertEqual(meta["successful_provider"], "Groq")
            self.assertTrue(meta["fallback_triggered"])
            self.assertEqual(meta["attempted_providers"], ["Gemini", "Groq"])
            self.assertEqual(meta["errors"]["Gemini"]["status_code"], 429)

    def test_scenario_3_gemini_and_groq_both_quota_triggers_deterministic_mode(self):
        """Both providers out of quota: no generated answer -> ABSTAIN (no deterministic dictamen),
        provider errors recorded, retrieved evidence kept and no citations emitted."""
        gemini_err_body = json.dumps({"error": {"code": 429, "message": "Gemini Resource exhausted"}}).encode("utf-8")
        gemini_429 = urllib.error.HTTPError("https://...", 429, "Too Many Requests", {}, io.BytesIO(gemini_err_body))

        groq_err_body = json.dumps({"error": {"code": 429, "message": "Groq Rate limit reached"}}).encode("utf-8")
        groq_429 = urllib.error.HTTPError("https://...", 429, "Rate Limit", {}, io.BytesIO(groq_err_body))

        def fresh_429s():
            return [
                urllib.error.HTTPError("https://...", 429, "Too Many Requests", {}, io.BytesIO(gemini_err_body)),
                urllib.error.HTTPError("https://...", 429, "Rate Limit", {}, io.BytesIO(groq_err_body)),
            ]

        # "tatami"/"area" are Spanish-marker keywords, so ADA performs a translation call AND an
        # analysis call: each one tries Gemini then Groq, hence four 429 responses.
        with patch("urllib.request.urlopen", side_effect=fresh_429s() + fresh_429s()) as urlopen_mock:
            mgr = MultiProviderLLMManager(
                primary_provider="Gemini",
                fallback_policy="automatic",
                gemini_api_key="valid_gemini_key",
                groq_api_key="valid_groq_key"
            )
            ada = ArbitrationDecisionAssistant(llm_manager=mgr)
            res = ada.analyze_situation("tatami contest area dimensions 8m")
            self.assertEqual(urlopen_mock.call_count, 4)
            self.assertEqual(res["status"], "ABSTAIN")
            self.assertIn("sin modelo generativo", res["mode"])
            self.assertEqual(citation_ids(res), [])
            self.assertTrue(len(res["evidence"]) > 0)
            self.assertIn("Gemini", res["llm_meta"]["errors"])
            self.assertIn("Groq", res["llm_meta"]["errors"])
            self.assertEqual(res["llm_meta"]["errors"]["Gemini"]["status_code"], 429)
            self.assertEqual(res["llm_meta"]["errors"]["Groq"]["status_code"], 429)
            self.assertIsNone(res["llm_meta"]["successful_provider"])

    def test_scenario_4_groq_missing_credentials_handled_gracefully(self):
        gemini_err_body = json.dumps({"error": {"code": 429, "message": "Gemini Quota"}}).encode("utf-8")
        gemini_429 = urllib.error.HTTPError("https://...", 429, "Too Many Requests", {}, io.BytesIO(gemini_err_body))

        with patch("urllib.request.urlopen", side_effect=[gemini_429]):
            mgr = MultiProviderLLMManager(
                primary_provider="Gemini",
                fallback_policy="automatic",
                gemini_api_key="valid_gemini_key",
                groq_api_key=None
            )
            text, meta = mgr.generate_with_fallback("Test query")
            self.assertIsNone(text)
            self.assertIn("Gemini", meta["errors"])
            self.assertIn("Groq", meta["errors"])
            self.assertEqual(meta["errors"]["Groq"]["error_type"], "AUTH")
            self.assertFalse(meta["fallback_triggered"])

if __name__ == "__main__":
    unittest.main()

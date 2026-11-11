"""
Unit Tests for UsageTracker and Token Metrics Module
====================================================
Validates persistent tracking of query counts, token breakdown,
running averages, and cost estimations for API Key viability.
"""

import os
import sys
import json
import unittest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from usage_tracker import UsageTracker, get_usage_tracker


class TestUsageTracker(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.metrics_file = os.path.join(self.temp_dir.name, "test_metrics.json")
        self.tracker = UsageTracker(filepath=self.metrics_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initial_state(self):
        m = self.tracker.get_metrics()
        self.assertEqual(m["total_queries"], 0)
        self.assertEqual(m["queries_with_llm"], 0)
        self.assertEqual(m["queries_local"], 0)
        self.assertEqual(m["total_tokens"], 0)
        self.assertEqual(m["avg_tokens_per_query"], 0.0)

    def test_record_single_query(self):
        token_usage = {
            "prompt_tokens": 700,
            "completion_tokens": 200,
            "total_tokens": 900
        }
        m = self.tracker.record_query(
            query_text="¿Cuánto dura un combate?",
            token_usage=token_usage,
            provider="Gemini",
            model="gemini-flash-lite-latest"
        )
        self.assertEqual(m["total_queries"], 1)
        self.assertEqual(m["queries_with_llm"], 1)
        self.assertEqual(m["total_prompt_tokens"], 700)
        self.assertEqual(m["total_completion_tokens"], 200)
        self.assertEqual(m["total_tokens"], 900)
        self.assertEqual(m["avg_tokens_per_query"], 900.0)
        self.assertEqual(m["avg_prompt_tokens"], 700.0)
        self.assertEqual(m["avg_completion_tokens"], 200.0)
        self.assertGreater(m["queries_per_dollar"], 1000)

    def test_record_multiple_queries_and_averages(self):
        self.tracker.record_query(
            "Consulta 1",
            {"prompt_tokens": 600, "completion_tokens": 200, "total_tokens": 800},
            "Gemini",
            "gemini-flash-lite-latest"
        )
        m = self.tracker.record_query(
            "Consulta 2",
            {"prompt_tokens": 400, "completion_tokens": 100, "total_tokens": 500},
            "Gemini",
            "gemini-flash-lite-latest"
        )
        self.assertEqual(m["total_queries"], 2)
        self.assertEqual(m["total_tokens"], 1300)
        self.assertEqual(m["avg_tokens_per_query"], 650.0)
        self.assertEqual(m["avg_prompt_tokens"], 500.0)
        self.assertEqual(m["avg_completion_tokens"], 150.0)

    def test_local_query_zero_tokens(self):
        m = self.tracker.record_query(
            "Consulta local",
            {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            provider="Local",
            model="deterministic"
        )
        self.assertEqual(m["total_queries"], 1)
        self.assertEqual(m["queries_local"], 1)
        self.assertEqual(m["queries_with_llm"], 0)
        self.assertEqual(m["total_tokens"], 0)

    def test_persistence_across_instances(self):
        self.tracker.record_query(
            "Consulta persistente",
            {"prompt_tokens": 500, "completion_tokens": 150, "total_tokens": 650},
            "Gemini",
            "gemini-flash-lite-latest"
        )
        # Load second instance pointing to same file
        tracker2 = UsageTracker(filepath=self.metrics_file)
        m = tracker2.get_metrics()
        self.assertEqual(m["total_queries"], 1)
        self.assertEqual(m["total_tokens"], 650)
        self.assertEqual(m["avg_tokens_per_query"], 650.0)

    def test_reset_metrics(self):
        self.tracker.record_query(
            "Consulta a borrar",
            {"prompt_tokens": 500, "completion_tokens": 150, "total_tokens": 650},
            "Gemini"
        )
        self.assertEqual(self.tracker.get_metrics()["total_queries"], 1)
        self.tracker.reset_metrics()
        m = self.tracker.get_metrics()
        self.assertEqual(m["total_queries"], 0)
        self.assertEqual(m["total_tokens"], 0)
        self.assertEqual(m["avg_tokens_per_query"], 0.0)


if __name__ == "__main__":
    unittest.main()

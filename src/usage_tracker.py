"""
Usage Tracker and Token Metrics Module for IJF SOR Assistant
============================================================
Tracks query volume, token consumption (prompt, completion, total),
running averages, and provides economic feasibility calculations for API Key usage.
Persists metrics safely in data/usage_metrics.json.
"""

import os
import json
import time
from typing import Dict, Any, Optional

METRICS_FILE_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "usage_metrics.json"
)

# Reference pricing per 1M tokens (USD)
# Source: Google AI Studio / Gemini API official pricing
PRICING_TABLE = {
    "gemini-flash-lite-latest": {"input_per_m": 0.0375, "output_per_m": 0.15},
    "gemini-2.5-flash-lite": {"input_per_m": 0.0375, "output_per_m": 0.15},
    "gemini-flash-latest": {"input_per_m": 0.075, "output_per_m": 0.30},
    "gemini-3.5-flash": {"input_per_m": 0.075, "output_per_m": 0.30},
    "gemini-2.5-flash": {"input_per_m": 0.075, "output_per_m": 0.30},
    "gemini-1.5-flash": {"input_per_m": 0.075, "output_per_m": 0.30},
    "gemini-2.5-pro": {"input_per_m": 1.25, "output_per_m": 5.00},
    "gemini-1.5-pro": {"input_per_m": 1.25, "output_per_m": 5.00},
    "default": {"input_per_m": 0.075, "output_per_m": 0.30}
}


class UsageTracker:
    """Manages persistent tracking of query counts and token metrics."""

    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath or METRICS_FILE_DEFAULT
        self._ensure_dir()
        self._data = self._load()

    def _ensure_dir(self):
        parent = os.path.dirname(self.filepath)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

    def _default_data(self) -> Dict[str, Any]:
        return {
            "version": "1.0",
            "total_queries": 0,
            "queries_with_llm": 0,
            "queries_local": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "last_query": {
                "timestamp": None,
                "query_preview": "",
                "provider": "None",
                "model": "None",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "recent_queries": []
        }

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    base = self._default_data()
                    base.update(data)
                    return base
            except Exception:
                pass
        return self._default_data()

    def _save(self):
        try:
            self._ensure_dir()
            tmp_path = f"{self.filepath}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            if os.path.exists(tmp_path):
                # Atomic replace on POSIX, direct replace on Windows
                if os.path.exists(self.filepath):
                    os.remove(self.filepath)
                os.rename(tmp_path, self.filepath)
        except Exception as e:
            print(f"[WARN] Error guardando métricas de uso: {e}")

    def record_query(
        self,
        query_text: str,
        token_usage: Optional[Dict[str, Any]] = None,
        provider: str = "Gemini",
        model: str = "gemini-flash-lite-latest"
    ) -> Dict[str, Any]:
        """
        Records a completed query and updates all counters, averages and costs.
        """
        token_usage = token_usage or {}
        p_tok = int(token_usage.get("prompt_tokens", 0))
        c_tok = int(token_usage.get("completion_tokens", 0))
        t_tok = int(token_usage.get("total_tokens", 0))
        if t_tok == 0 and (p_tok > 0 or c_tok > 0):
            t_tok = p_tok + c_tok

        is_llm = (t_tok > 0) or (provider.lower() not in ("local", "none", "offline"))

        self._data["total_queries"] += 1
        if is_llm:
            self._data["queries_with_llm"] += 1
            self._data["total_prompt_tokens"] += p_tok
            self._data["total_completion_tokens"] += c_tok
            self._data["total_tokens"] += t_tok
        else:
            self._data["queries_local"] += 1

        query_preview = (query_text[:60] + "...") if len(query_text) > 60 else query_text

        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "query_preview": query_preview,
            "provider": provider,
            "model": model,
            "prompt_tokens": p_tok,
            "completion_tokens": c_tok,
            "total_tokens": t_tok
        }

        self._data["last_query"] = entry

        # Keep last 30 queries in memory
        recent = self._data.get("recent_queries", [])
        recent.insert(0, entry)
        self._data["recent_queries"] = recent[:30]

        self._save()
        return self.get_metrics()

    def get_metrics(self) -> Dict[str, Any]:
        """Returns computed metrics, averages and cost projections."""
        tot_q = self._data["total_queries"]
        llm_q = self._data["queries_with_llm"]
        loc_q = self._data["queries_local"]
        tot_p_tok = self._data["total_prompt_tokens"]
        tot_c_tok = self._data["total_completion_tokens"]
        tot_tok = self._data["total_tokens"]

        avg_total_tokens = round(tot_tok / tot_q, 1) if tot_q > 0 else 0.0
        avg_llm_tokens = round(tot_tok / llm_q, 1) if llm_q > 0 else 0.0
        avg_prompt_tokens = round(tot_p_tok / llm_q, 1) if llm_q > 0 else 0.0
        avg_completion_tokens = round(tot_c_tok / llm_q, 1) if llm_q > 0 else 0.0

        last_q = self._data.get("last_query", {})
        last_model = last_q.get("model", "default")
        rates = PRICING_TABLE.get(last_model, PRICING_TABLE["default"])

        # Cost calculations in USD
        cost_prompt = (tot_p_tok / 1_000_000) * rates["input_per_m"]
        cost_completion = (tot_c_tok / 1_000_000) * rates["output_per_m"]
        total_cost_usd = cost_prompt + cost_completion

        avg_cost_per_query = (total_cost_usd / tot_q) if tot_q > 0 else (
            ((avg_prompt_tokens / 1_000_000) * rates["input_per_m"]) +
            ((avg_completion_tokens / 1_000_000) * rates["output_per_m"])
        )

        # Baseline per-query estimate even before first query
        if avg_cost_per_query == 0.0:
            typical_p = 800
            typical_c = 250
            avg_cost_per_query = ((typical_p / 1_000_000) * rates["input_per_m"]) + ((typical_c / 1_000_000) * rates["output_per_m"])

        queries_per_dollar = int(1.0 / avg_cost_per_query) if avg_cost_per_query > 0 else 10000

        return {
            "total_queries": tot_q,
            "queries_with_llm": llm_q,
            "queries_local": loc_q,
            "total_tokens": tot_tok,
            "total_prompt_tokens": tot_p_tok,
            "total_completion_tokens": tot_c_tok,
            "avg_tokens_per_query": avg_total_tokens,
            "avg_llm_tokens": avg_llm_tokens,
            "avg_prompt_tokens": avg_prompt_tokens,
            "avg_completion_tokens": avg_completion_tokens,
            "last_query": last_q,
            "rates_used": rates,
            "total_cost_usd": total_cost_usd,
            "avg_cost_per_query_usd": avg_cost_per_query,
            "queries_per_dollar": queries_per_dollar,
            "projections": {
                "queries_100_usd": round(avg_cost_per_query * 100, 4),
                "queries_500_usd": round(avg_cost_per_query * 500, 4),
                "queries_1000_usd": round(avg_cost_per_query * 1000, 4),
                "queries_5000_usd": round(avg_cost_per_query * 5000, 4),
                "queries_10000_usd": round(avg_cost_per_query * 10000, 4)
            }
        }

    def reset_metrics(self) -> Dict[str, Any]:
        """Resets all counters and saves clean file."""
        self._data = self._default_data()
        self._save()
        return self.get_metrics()


# Global module singleton instance
_tracker_instance = None

def get_usage_tracker(filepath: Optional[str] = None) -> UsageTracker:
    global _tracker_instance
    if _tracker_instance is None or filepath is not None:
        _tracker_instance = UsageTracker(filepath=filepath)
    return _tracker_instance

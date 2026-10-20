"""
Regression tests for Citation Highlighting and Exact Quote extraction in ADA Assistant.
Ensures sub-article exact quotes are pinpointed rather than using page generic headers.
"""

import os
import sys
import pytest

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from ada_assistant import ArbitrationDecisionAssistant


def test_subarticle_exact_quote_extraction():
    # Passage simulating page 124 with multiple articles: C1.9 and C1.10
    passage = {
        "passage_id": "P124_C1_10",
        "article_id": "C1.10",
        "page": 124,
        "title": "Appendix C - C1.10 Judogi Size",
        "text_original": (
            "C1.1 IJF Approved Judogi\n"
            "All judoka must wear approved judogi.\n\n"
            "C1.9 Commercial Markings\n"
            "Advertising must strictly comply with IJF regulations.\n\n"
            "C1.10 Judogi Size (Sokuteiki)\n"
            "The Sokuteiki tool will be used to verify jacket dimensions, sleeve length, and trousers width."
        )
    }
    
    exact_quote, snippet = ArbitrationDecisionAssistant.extract_exact_quote(passage)
    
    # Exact quote must NOT be the page header "C1.1 IJF Approved Judogi"
    assert "C1.1 IJF Approved Judogi" not in exact_quote
    # Exact quote must target C1.10 specifically
    assert "The Sokuteiki tool" in exact_quote or "Sokuteiki" in exact_quote
    assert "verify jacket dimensions" in snippet


def test_subarticle_exact_quote_with_period_prefix():
    passage = {
        "passage_id": "P198_20_3_2",
        "article_id": "20.3.2",
        "page": 198,
        "title": "Article 20.3.2 Treatment of Minor Injuries",
        "text_original": (
            "Article 20 Medical Procedures\n"
            "Medical personnel must follow strict safety protocols.\n\n"
            "Article 20.3.2 Treatment of Minor Injuries\n"
            "Taping and finger bandages are allowed if applied quickly without causing unfair delay."
        )
    }
    
    exact_quote, snippet = ArbitrationDecisionAssistant.extract_exact_quote(passage)
    
    assert "Medical personnel must follow" not in exact_quote
    assert "Taping and finger bandages" in exact_quote
    assert "causing unfair delay" in snippet


def test_fallback_when_article_not_explicitly_in_text():
    passage = {
        "passage_id": "P50_GEN",
        "article_id": "99.9",
        "page": 50,
        "title": "General contest timing",
        "text_original": "General guidelines for contest timing and tatami operations on page 50."
    }
    
    exact_quote, snippet = ArbitrationDecisionAssistant.extract_exact_quote(passage)
    assert exact_quote.startswith("General guidelines")
    assert "tatami operations" in snippet


def test_wasting_time_exact_quote_pinpointing():
    """Ensure exact quote targets failing to return / time-wasting rather than judogi attire."""
    passage = {
        "passage_id": "SOR-2026-08-P188-S195",
        "article_id": "Article 18.1.3",
        "page": 188,
        "title": "Article 18.1.3 Untidy Attire or Hair and Wasting Time",
        "text_original": (
            "Sport and Organisation Rules of the International Judo Federation\n"
            "page - 188\n"
            "Article 18 .1 .3 Untidy Attire or Hair and Wasting Time\n"
            "The correct preparation of the judogi jacket, trousers, belt and hair is the responsibility of the athlete.\n"
            "Athletes must enter and leave the field of play wearing their judogi and hair in the proper way.\n"
            "Deliberate time-wasting during a contest will not be tolerated.\n"
            "Time-wasting includes, but is not limited to:\n"
            "• Failing to stand up promptly after a completed action when the athlete is on the ground.\n"
            "• Failing to return immediately to the starting position.\n"
            "• Taking excessive time to arrange or retie their hair.\n"
            "The first occurrence of any action listed in this article will not result in a penalty.\n"
            "32. The referee will indicate to the athlete that any subsequent occurrence will result in a shido."
        )
    }

    query = "Si un competidor no regresa a la posicion de inicio que le corresponde, quedandose en el suelo y perdiendo tiempo, que debe realizar el arbitro?"
    exact_quote, snippet = ArbitrationDecisionAssistant.extract_exact_quote(passage, query=query)

    # Must NOT quote general judogi attire preparation
    assert "The correct preparation of the judogi" not in exact_quote
    # Must target the substantive time-wasting rule on returning to starting position
    assert "Failing to return immediately to the starting position" in exact_quote or "Deliberate time-wasting" in exact_quote


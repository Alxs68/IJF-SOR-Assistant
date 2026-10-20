"""
User Feedback and Observation Manager for IJF-SOR-Assistant
===========================================================
Provides lightweight, reliable and secure storage for user observations,
potential normative discrepancies, and suggestions.
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

FEEDBACK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "feedback")
OBSERVATIONS_FILE = os.path.join(FEEDBACK_DIR, "user_observations.jsonl")

MOTIVOS_VALIDOS = [
    "La respuesta podría ser incorrecta",
    "Falta una regla o aclaración",
    "La cita o página no corresponde",
    "Conozco un caso arbitral que conviene revisar",
    "Tengo una sugerencia de mejora"
]


def ensure_feedback_storage() -> str:
    """Ensures the feedback directory exists and returns the file path."""
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    return OBSERVATIONS_FILE


def record_observation(
    motivo: str,
    comentario: Optional[str] = None,
    query: Optional[str] = None,
    response_summary: Optional[str] = None,
    citations: Optional[list] = None,
    edition: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Persists a user observation in JSONL format with automatic technical context capture.
    Returns status dict with observation ID.
    """
    try:
        file_path = ensure_feedback_storage()
        obs_id = f"OBS-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Clean citations list to keep minimal technical identifiers without bloat
        cleaned_citations = []
        if citations and isinstance(citations, list):
            for c in citations:
                if isinstance(c, dict):
                    cleaned_citations.append({
                        "passage_id": c.get("passage_id"),
                        "article_id": c.get("article_id"),
                        "page_number": c.get("page_number"),
                        "exact_quote": c.get("exact_quote", "")[:120]
                    })
                elif isinstance(c, str):
                    cleaned_citations.append({"passage_id": c})

        record = {
            "observation_id": obs_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": motivo,
            "user_comment": (comentario or "").strip(),
            "context": {
                "query": (query or "").strip(),
                "response_summary": (response_summary or "").strip()[:500],
                "citations": cleaned_citations,
                "normative_edition": edition or "2026-08 (Official)"
            },
            "status": "RECEIVED",
            "internal_review": {
                "reviewed": False,
                "priority": "NORMAL",
                "notes": ""
            }
        }

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return {
            "success": True,
            "observation_id": obs_id,
            "message": "Muchas gracias. Tu observación ha sido registrada para revisión técnica."
        }
    except Exception as e:
        return {
            "success": False,
            "observation_id": None,
            "error": str(e),
            "message": "No se pudo registrar la observación temporalmente. Por favor, inténtelo de nuevo más tarde."
        }

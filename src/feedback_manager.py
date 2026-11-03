"""
User Feedback and Observation Manager for IJF-SOR-Assistant
===========================================================
Provides lightweight, reliable, and secure storage for user observations,
potential normative discrepancies, and suggestions, alongside an authenticated
administrative management module.
"""

import os
import json
import uuid
import hmac
import hashlib
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

FEEDBACK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "feedback")
ATTACHMENTS_DIR = os.path.join(FEEDBACK_DIR, "attachments")
OBSERVATIONS_FILE = os.path.join(FEEDBACK_DIR, "user_observations.jsonl")

# Official Status Pipeline
VALID_STATUSES = [
    "Recibida",
    "Pendiente de revisión",
    "En investigación",
    "En corrección",
    "Pendiente de validar",
    "Validada",
    "Descartada",
    "Bloqueada"
]

# Legacy status mapping for backwards compatibility
STATUS_COMPATIBILITY_MAP = {
    "RECEIVED": "Recibida",
    "PENDING": "Pendiente de revisión",
    "IN_PROGRESS": "En investigación",
    "CORRECTED": "En corrección",
    "VALIDATED": "Validada",
    "DISMISSED": "Descartada",
    "BLOCKED": "Bloqueada"
}

# Maximum attachment limits for abuse prevention
MAX_ATTACHMENT_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "application/pdf"
}

# Legacy motives preserved for test compatibility
MOTIVOS_VALIDOS = [
    "La respuesta podría ser incorrecta",
    "Falta una regla o aclaración",
    "La cita o página no corresponde",
    "Conozco un caso arbitral que conviene revisar",
    "Tengo una sugerencia de mejora"
]


def ensure_feedback_storage() -> str:
    """Ensures the feedback and attachments directories exist and returns the jsonl file path."""
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
    return OBSERVATIONS_FILE


def _get_admin_token() -> Optional[str]:
    """
    Retrieves the administrative token from environment variables or Streamlit secrets.
    Does NOT return any default credential. If unset, administrative access is strictly disabled.
    """
    token = os.environ.get("FEEDBACK_ADMIN_TOKEN")
    if not token:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "FEEDBACK_ADMIN_TOKEN" in st.secrets:
                token = str(st.secrets["FEEDBACK_ADMIN_TOKEN"])
        except Exception:
            token = None
    return token.strip() if token else None


def is_admin_configured() -> bool:
    """Returns True only if an administrative token is configured on the server."""
    token = _get_admin_token()
    return bool(token and len(token) >= 8)


def verify_admin_token(provided_token: Optional[str]) -> bool:
    """
    Constant-time token verification to prevent timing attacks.
    Returns False immediately if no admin token is configured on the server.
    """
    server_token = _get_admin_token()
    if not server_token or not provided_token:
        return False
    # Use hmac.compare_digest for constant-time comparison
    return hmac.compare_digest(server_token.encode("utf-8"), provided_token.strip().encode("utf-8"))


def sanitize_filename(filename: str) -> str:
    """Sanitizes file name to prevent directory traversal and remove dangerous characters."""
    base = os.path.basename(filename)
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", base)
    # Ensure it is not empty and has an extension
    if not clean or clean.startswith("."):
        clean = f"attachment_{uuid.uuid4().hex[:6]}{clean}"
    return clean


def save_attachment(
    obs_id: str,
    file_bytes: bytes,
    original_filename: str,
    mime_type: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates and securely stores an uploaded evidence file in an observation-scoped subdirectory.
    Returns: (success: bool, stored_relative_path: Optional[str], error_message: Optional[str])
    """
    if len(file_bytes) > MAX_ATTACHMENT_SIZE_BYTES:
        return False, None, f"El archivo excede el tamaño máximo permitido de {MAX_ATTACHMENT_SIZE_BYTES // (1024*1024)} MB."

    safe_name = sanitize_filename(original_filename)
    _, ext = os.path.splitext(safe_name)
    ext = ext.lower()

    if ext not in ALLOWED_EXTENSIONS:
        return False, None, f"Tipo de archivo no permitido ('{ext}'). Formatos aceptados: PNG, JPG, JPEG, PDF."

    if mime_type and mime_type.lower() not in ALLOWED_MIME_TYPES:
        # Extra check if mime_type was supplied
        if not (ext in (".jpg", ".jpeg") and mime_type in ("image/jpeg", "image/jpg")):
            return False, None, f"El tipo MIME '{mime_type}' no es válido para adjuntos."

    # Prevent Path Traversal in obs_id
    safe_obs = re.sub(r"[^a-zA-Z0-9_-]", "_", obs_id)
    obs_dir = os.path.join(ATTACHMENTS_DIR, safe_obs)
    os.makedirs(obs_dir, exist_ok=True)

    # Calculate SHA256 of attachment for integrity check
    file_sha256 = hashlib.sha256(file_bytes).hexdigest()
    final_filename = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    full_path = os.path.join(obs_dir, final_filename)

    with open(full_path, "wb") as f:
        f.write(file_bytes)

    relative_path = os.path.join(safe_obs, final_filename).replace("\\", "/")
    return True, relative_path, None


def record_observation(
    motivo: Optional[str] = None,
    comentario: Optional[str] = None,
    query: Optional[str] = None,
    response_summary: Optional[str] = None,
    citations: Optional[list] = None,
    edition: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
    attachment_bytes: Optional[bytes] = None,
    attachment_filename: Optional[str] = None,
    attachment_mime: Optional[str] = None
) -> Dict[str, Any]:
    """
    Public entrypoint to persist a user observation/feedback in JSONL format with
    automatic non-sensitive technical context and optional evidence attachment.
    Requires at least a comment or a reason. Motivo is no longer mandatory.
    """
    try:
        user_text = (comentario or "").strip()
        reason_text = (motivo or "").strip()

        # Check that user provided at least some descriptive content
        if not user_text and not reason_text:
            return {
                "success": False,
                "observation_id": None,
                "message": "Por favor incluye una breve descripción o comentario sobre la novedad."
            }

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
                        "exact_quote": str(c.get("exact_quote", ""))[:120]
                    })
                elif isinstance(c, str):
                    cleaned_citations.append({"passage_id": c})

        # Process optional attachment if provided
        attachment_record = None
        if attachment_bytes and attachment_filename:
            att_ok, att_rel_path, att_err = save_attachment(
                obs_id=obs_id,
                file_bytes=attachment_bytes,
                original_filename=attachment_filename,
                mime_type=attachment_mime
            )
            if not att_ok:
                return {
                    "success": False,
                    "observation_id": None,
                    "message": f"Error al guardar adjunto: {att_err}"
                }
            attachment_record = {
                "relative_path": att_rel_path,
                "original_filename": sanitize_filename(attachment_filename),
                "size_bytes": len(attachment_bytes)
            }

        # Safe technical context (no secrets, no user personal data)
        safe_context = {
            "query": (query or "").strip()[:500],
            "response_summary": (response_summary or "").strip()[:500],
            "citations": cleaned_citations,
            "normative_edition": edition or "2026-08 (Official)"
        }
        if extra_metadata and isinstance(extra_metadata, dict):
            # Whitelist only safe technical metadata
            for k in ("lang", "ui_section", "app_version"):
                if k in extra_metadata:
                    safe_context[k] = str(extra_metadata[k])[:100]

        record = {
            "observation_id": obs_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason_text if reason_text else "General",
            "user_comment": user_text,
            "context": safe_context,
            "attachment": attachment_record,
            "status": "Recibida",
            "internal_review": {
                "reviewed": False,
                "priority": "NORMAL",
                "notes": "",
                "status_history": [
                    {
                        "status": "Recibida",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "author": "System"
                    }
                ]
            }
        }

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return {
            "success": True,
            "observation_id": obs_id,
            "message": "Muchas gracias. Tu reporte ha sido registrado con éxito."
        }
    except Exception as e:
        return {
            "success": False,
            "observation_id": None,
            "error": str(e),
            "message": "No se pudo registrar la novedad temporalmente. Por favor, inténtelo de nuevo más tarde."
        }


# =========================================================================
# PROTECTED ADMINISTRATIVE OPERATIONS (Server-Side Authorization Required)
# =========================================================================

def list_observations_protected(
    admin_token: Optional[str],
    status_filter: Optional[str] = None,
    search_term: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Authenticated retrieval of observations. Strictly returns unauthorized error if token is invalid.
    Handles backward compatibility with older jsonl records.
    """
    if not verify_admin_token(admin_token):
        return {
            "success": False,
            "error": "UNAUTHORIZED",
            "message": "Acceso denegado: token de administración no válido o no configurado.",
            "data": []
        }

    file_path = ensure_feedback_storage()
    if not os.path.exists(file_path):
        return {"success": True, "data": [], "total": 0}

    results = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except Exception:
                    continue

                # Normalize status for backward compatibility
                st = record.get("status", "Recibida")
                if st in STATUS_COMPATIBILITY_MAP:
                    st = STATUS_COMPATIBILITY_MAP[st]
                    record["status"] = st

                # Filter by status if requested
                if status_filter and status_filter != "TODOS" and st != status_filter:
                    continue

                # Filter by search term if requested
                if search_term:
                    term = search_term.lower()
                    obs_id = record.get("observation_id", "").lower()
                    comment = record.get("user_comment", "").lower()
                    query = record.get("context", {}).get("query", "").lower()
                    if term not in obs_id and term not in comment and term not in query:
                        continue

                results.append(record)

        # Sort reverse chronological by timestamp
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {
            "success": True,
            "data": results[:limit],
            "total": len(results)
        }
    except Exception as e:
        return {
            "success": False,
            "error": "STORAGE_ERROR",
            "message": f"Error al leer las novedades: {e}",
            "data": []
        }


def get_observation_attachment_bytes(
    admin_token: Optional[str],
    relative_path: str
) -> Tuple[bool, Optional[bytes], Optional[str]]:
    """
    Protected endpoint to retrieve attachment bytes, preventing Path Traversal and public access.
    """
    if not verify_admin_token(admin_token):
        return False, None, "Acceso no autorizado a evidencias adjuntas."

    # Strict path traversal check
    clean_rel = os.path.normpath(relative_path).replace("\\", "/")
    if ".." in clean_rel or clean_rel.startswith("/") or clean_rel.startswith("\\"):
        return False, None, "Ruta de archivo no permitida (Path Traversal detectado)."

    full_path = os.path.abspath(os.path.join(ATTACHMENTS_DIR, clean_rel))
    real_attachments_dir = os.path.abspath(ATTACHMENTS_DIR)

    if not full_path.startswith(real_attachments_dir):
        return False, None, "Acceso fuera del directorio de adjuntos denegado."

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        return False, None, "El archivo adjunto no existe en el almacenamiento."

    try:
        with open(full_path, "rb") as f:
            data = f.read()
        return True, data, None
    except Exception as e:
        return False, None, f"Error al leer el archivo: {e}"


def update_observation_status_protected(
    admin_token: Optional[str],
    observation_id: str,
    new_status: str,
    admin_note: Optional[str] = None,
    author: str = "Admin"
) -> Dict[str, Any]:
    """
    Protected update of status and internal notes. Atomically modifies the JSONL record.
    """
    if not verify_admin_token(admin_token):
        return {
            "success": False,
            "error": "UNAUTHORIZED",
            "message": "Acceso denegado: token de administración no válido o no configurado."
        }

    if new_status not in VALID_STATUSES:
        return {
            "success": False,
            "error": "INVALID_STATUS",
            "message": f"Estado '{new_status}' no válido. Estados oficiales permitidos: {', '.join(VALID_STATUSES)}"
        }

    file_path = ensure_feedback_storage()
    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": "NOT_FOUND",
            "message": f"Reporte '{observation_id}' no encontrado."
        }

    found = False
    updated_records = []
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("observation_id") == observation_id:
                    found = True
                    record["status"] = new_status
                    if "internal_review" not in record or not isinstance(record["internal_review"], dict):
                        record["internal_review"] = {}

                    record["internal_review"]["reviewed"] = True
                    if admin_note and admin_note.strip():
                        prev_notes = record["internal_review"].get("notes", "")
                        formatted_note = f"[{now_iso} - {author}]: {admin_note.strip()}"
                        record["internal_review"]["notes"] = f"{prev_notes}\n{formatted_note}".strip()

                    # Add to status history
                    if "status_history" not in record["internal_review"]:
                        record["internal_review"]["status_history"] = []
                    record["internal_review"]["status_history"].append({
                        "status": new_status,
                        "timestamp": now_iso,
                        "author": author,
                        "note": (admin_note or "").strip()
                    })

                updated_records.append(record)

        if not found:
            return {
                "success": False,
                "error": "NOT_FOUND",
                "message": f"Novedad '{observation_id}' no encontrada en el sistema."
            }

        # Atomically write back to temporary file then replace
        temp_file = f"{file_path}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            for r in updated_records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        os.replace(temp_file, file_path)

        return {
            "success": True,
            "observation_id": observation_id,
            "new_status": new_status,
            "message": f"Estado de '{observation_id}' actualizado a '{new_status}' con éxito."
        }
    except Exception as e:
        return {
            "success": False,
            "error": "UPDATE_ERROR",
            "message": f"Error durante la actualización del reporte: {e}"
        }

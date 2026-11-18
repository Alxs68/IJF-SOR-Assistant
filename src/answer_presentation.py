"""Presentacion de la respuesta unica (ADA_UNIFIED_ANSWER=1).

Compone en UN solo bloque todo el contenido generado y verificado por el DIG (summary, normative_basis,
conditions_and_exceptions, extended_analysis, limitations). No genera contenido: solo ordena y omite los
marcadores vacios ("No aplica", "Ninguna"). Sin dependencias de Streamlit para poder probarse.
"""
import os

UNIFIED_FIELDS = ("summary", "normative_basis", "conditions_and_exceptions", "extended_analysis", "limitations")
PLACEHOLDERS = {"", "no aplica", "not applicable", "n/a", "ninguna", "none", "non applicable", "aucune", "nenhuma",
                "não se aplica", "nao se aplica"}
TITLES = {
    "es": {"summary": "Respuesta", "normative_basis": "Regla normativa aplicable",
           "conditions_and_exceptions": "Condiciones, excepciones y diferencias por categoría",
           "extended_analysis": "Aplicación al caso", "limitations": "Límites de la evidencia documental",
           "header": "Respuesta oficial (verificada con el SOR 2026)",
           "header_clarify": "Solicitud de aclaración", "header_abstain": "Abstención normativa"},
    "en": {"summary": "Answer", "normative_basis": "Applicable rule",
           "conditions_and_exceptions": "Conditions, exceptions and category differences",
           "extended_analysis": "Application to the case", "limitations": "Limits of the documentary evidence",
           "header": "Official answer (verified against SOR 2026)",
           "header_clarify": "Clarification needed", "header_abstain": "Normative abstention"},
}


def is_placeholder(text):
    return str(text or "").strip().strip(".").strip().lower() in PLACEHOLDERS


def unified_enabled(struct=None):
    """La respuesta se presenta unificada si el analisis la produjo asi o si el modo esta activo."""
    if isinstance(struct, dict) and struct.get("answer_mode") == "UNIFIED":
        return True
    return os.environ.get("ADA_UNIFIED_ANSWER", "").strip() == "1"


def unified_header(struct, lang="es"):
    t = TITLES["en" if lang == "en" else "es"]
    status = (struct or {}).get("response_status")
    return t["header_clarify"] if status == "CLARIFICATION_REQUIRED" else t["header_abstain"] if status == "ABSTAIN" else t["header"]


def unified_sections(struct, lang="es"):
    """[(campo, titulo, texto)] en orden de lectura; el summary va primero y sin titulo propio.
    En abstencion y aclaracion solo se muestra el mensaje principal y, si aporta, su motivo."""
    t = TITLES["en" if lang == "en" else "es"]
    struct = struct or {}
    out = []
    for field in UNIFIED_FIELDS:
        text = str(struct.get(field) or "").strip()
        if is_placeholder(text):
            continue
        if field == "limitations" and struct.get("response_status") in ("ABSTAIN", "CLARIFICATION_REQUIRED") \
                and text in str(struct.get("summary") or ""):
            continue  # el motivo ya figura en el mensaje principal
        out.append((field, "" if field == "summary" else t[field], text))
    return out

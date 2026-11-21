"""
Structured Response Engine for IJF SOR Assistant
================================================
Defines the two-tier response contract:
- Tier 1: Direct, concise answer always visible (summary: 1-4 sentences, ~30-80 words).
- Tier 2: Complete normative foundation, collapsible in Streamlit:
  * Normative basis (articles, rules, chapters)
  * Conditions and exceptions
  * Extended analysis & application logic
  * Limitations and unverified aspects
  * Verifiable citations and references

Provides robust parsing, validation, and safe fallback for unstructured or legacy responses.
"""

import html
import json
import re
from typing import Dict, Any, List, Optional


def clean_presentation_text(raw_text: str, link_token=None) -> str:
    """
    Cleans an analytical synthesis text for polished natural language presentation:
    - Strips meta-narrative headers (e.g. 'Síntesis Analítica IA', 'Resumen de Evidencias').
    - Removes rigid deterministic title/passage prefixes like:
      '**Title (Art. X, Pág. Y) [SOR-xxxx]:**' or '**[SOR-xxxx] Title:**'.
    - Eliminates internal retrieval codes like '[SOR-2026-08-Pxxx-Sxxx]' or '[KUN-xxxx]'
      and their markdown links while preserving natural article names (e.g. 'Artículo 8.7').
    - Removes synthetic trailing remissions ('Disposiciones complementarias aplicables en...').
    - Normalizes punctuation, whitespace, and preserves natural paragraphs and bullet points.

    link_token (opcional, solo presentacion): funcion (identificador, url_o_None) -> marcador | None. Si se da, cada
    codigo de recuperacion (con o sin enlace) se sustituye por el marcador que devuelva en lugar de eliminarse; si
    devuelve None se elimina como siempre. Sin link_token el comportamiento es exactamente el de siempre.
    """
    if not raw_text or not isinstance(raw_text, str):
        return ""

    text = raw_text.strip()

    # 1. Eliminar encabezados metanarrativos o de auditoría
    text = re.sub(
        r'^(?:⚖️\s*\*\*Síntesis Analítica IA.*?\*\*\s*|📋\s*\*\*Resumen de Evidencias.*?\*\*\s*|⚖️\s*\*\*AI Analytical Synthesis.*?\*\*\s*|📋\s*\*\*Normative Evidence Summary.*?\*\*\s*)',
        '',
        text,
        flags=re.IGNORECASE
    ).strip()

    # 2. Eliminar prefijos deterministas con identificadores técnicos entre corchetes
    # Ej: **8.7 Field of Play and Competition Area (Art. 8.7, Pág. 96) [SOR-2026-08-P096-S114](https://...):**
    # o **Field of Play (Art. 8.7, Pág. 96) [SOR-2026-08-P096-S114]:**
    text = re.sub(
        r'^\*\*.*?\((?:Art\.|Artículo|Article|Regla|Rule|Section|Appendix).*?\)\s*\[(?:SOR-[A-Za-z0-9-]+|KUN-\d{4})\s*\](?:\([^)]+\))?:\*\*\s*',
        '',
        text,
        flags=re.IGNORECASE
    ).strip()

    # Ej: **[SOR-2026-08-P096-S114] Field of Play (Art. 8.7):**
    text = re.sub(
        r'^\*\*\[(?:SOR-[A-Za-z0-9-]+|KUN-\d{4})\].*?\*\*\s*',
        '',
        text,
        flags=re.IGNORECASE
    ).strip()

    if link_token is not None:
        # 3-4 (presentacion con referencias interactivas): el codigo se sustituye por el marcador del renderizador,
        # que solo lo enlaza si es una cita verificada; la URL escrita en el texto no se usa como destino.
        def _tok(m):
            mark = link_token(m.group(1), m.group(2) if m.lastindex and m.lastindex >= 2 else None)
            return f" {mark}" if mark else ""
        _ids = r'(SOR-2026-08-P\d{3}-S\d{3}|KUN-[A-Za-z0-9_-]+|CHK-[A-Za-z0-9_-]+)'
        text = re.sub(rf'\s*\[{_ids}\]\(([^)]+)\)', _tok, text)
        text = re.sub(rf'\s*\[{_ids}\]', _tok, text)
    else:
        # 3. Remover enlaces markdown de códigos de recuperación: [SOR-2026-08-Pxxx-Sxxx](...) o [KUN-xxxx](...)
        text = re.sub(
            r'\s*\[(?:SOR-2026-08-P\d{3}-S\d{3}|KUN-\d{4})\]\([^)]+\)',
            '',
            text
        )

        # 4. Remover códigos de recuperación aislados en corchetes: [SOR-2026-08-Pxxx-Sxxx] o [KUN-xxxx]
        text = re.sub(
            r'\s*\[(?:SOR-2026-08-P\d{3}-S\d{3}|KUN-\d{4})\]',
            '',
            text
        )

    # 5. Remover corchetes residuales vacíos []
    text = re.sub(r'\[\s*\]', '', text)

    # 6. Eliminar coletilla determinista de remisión sintética al final si existe
    text = re.sub(
        r'\s*Disposiciones complementarias aplicables en\s+.*$',
        '',
        text,
        flags=re.IGNORECASE
    ).strip()
    text = re.sub(
        r'\s*Complementary provisions applicable in\s+Art\..*?\.?$',
        '',
        text,
        flags=re.IGNORECASE
    ).strip()

    # 6b. Eliminar residuos de etiquetas de referencia sueltas al final (ej. "Referencia:.", "Reference:.")
    text = re.sub(
        r'\s*(?:Referencia|Reference|Cita|Citation|Ref)\s*:\s*\.?\s*$',
        '',
        text,
        flags=re.IGNORECASE
    ).strip()

    # 7. Normalizar espacios antes de signos de puntuación y dobles espacios
    text = re.sub(r'\s+([,.;:!?])', r'\1', text)
    text = re.sub(r'[ \t]+', ' ', text)

    # 8. Limpiar saltos de línea repetidos innecesarios
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def sanitize_presentation_html(text: str) -> str:
    """
    Sanitizes text for safe HTML presentation in UI containers (e.g., Streamlit Tier-1 cards):
    - Escapes dangerous raw HTML characters (<, >, &, \", \') to neutralize script/tag injection.
    - Safely translates inline Markdown bold (**text**) and italic (*text*) to HTML strong/em.
    - Converts newlines to linebreaks (<br>) while keeping structured paragraphs (<br><br>).
    """
    if not text or not isinstance(text, str):
        return ""

    # 1. Escapar caracteres HTML para neutralizar inyecciones XSS y tags malformados
    escaped = html.escape(text.strip())

    # 2. Convertir negrita (**texto**) y cursiva (*texto*) de forma segura sobre el texto ya escapado
    formatted = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped)
    formatted = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', formatted)

    # 3. Preservar saltos de párrafo y de línea
    formatted = formatted.replace('\r\n', '\n').replace('\r', '\n')
    formatted = formatted.replace('\n\n', '<br><br>').replace('\n', '<br>')

    return formatted


class StructuredAnswer:
    """Canonical representation of a two-tier assistant response."""

    def __init__(
        self,
        summary: str,
        normative_basis: str = "",
        citations: Optional[List[Any]] = None,
        conditions_and_exceptions: str = "",
        extended_analysis: str = "",
        limitations: str = "",
        is_structured: bool = True
    ):
        self.summary = summary.strip()
        self.normative_basis = normative_basis.strip()
        self.citations = citations or []
        self.conditions_and_exceptions = conditions_and_exceptions.strip()
        self.extended_analysis = extended_analysis.strip()
        self.limitations = limitations.strip()
        self.is_structured = is_structured
        # Set to False by the deterministic fallback when it cannot establish that the
        # extracted text addresses the query. It is not part of to_dict() (no UI change).
        self.sufficiency_established = True

    def clean_summary(self) -> str:
        """Returns the summary clean of technical retrieval identifiers, prefixes, and metadata."""
        return clean_presentation_text(self.summary)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "clean_summary": self.clean_summary(),
            "normative_basis": self.normative_basis,
            "citations": self.citations,
            "conditions_and_exceptions": self.conditions_and_exceptions,
            "extended_analysis": self.extended_analysis,
            "limitations": self.limitations,
            "is_structured": self.is_structured
        }

    def format_collapsible_markdown(self) -> str:
        """Formats the Tier 2 detailed foundation as clean markdown for the expander."""
        parts = []

        if self.normative_basis:
            parts.append(f"#### 📜 Preceptos y Artículos Aplicables\n{self.normative_basis}")

        if self.conditions_and_exceptions:
            parts.append(f"#### ⚖️ Condiciones, Excepciones y Restricciones\n{self.conditions_and_exceptions}")

        if self.extended_analysis:
            parts.append(f"#### 🔍 Análisis Arbitral Ampliado\n{self.extended_analysis}")

        if self.limitations:
            parts.append(f"#### ⚠️ Límites de la Evidencia\n{self.limitations}")

        return "\n\n".join(parts)

    def to_legacy_text(self, header: str = "") -> str:
        """
        Builds a combined flat text representation for backward compatibility
        with legacy tests and consumers expecting a single text string in res['answer'].
        """
        header_prefix = f"{header}\n\n" if header else ""
        details = self.format_collapsible_markdown()
        if details:
            return f"{header_prefix}{self.summary}\n\n---\n\n{details}"
        return f"{header_prefix}{self.summary}"


def parse_structured_response(
    raw_text: str,
    evidence_passages: Optional[List[Dict[str, Any]]] = None
) -> StructuredAnswer:
    """
    Parses LLM generation into StructuredAnswer.
    Supports:
    1. Valid JSON responses adhering to the schema.
    2. JSON embedded in markdown fences (```json ... ```).
    3. Unstructured raw text via intelligent fallback heuristic.
    """
    if not raw_text or not raw_text.strip():
        return StructuredAnswer(
            summary="No se recibió contenido para generar la respuesta.",
            limitations="El proveedor generativo devolvió una respuesta vacía.",
            is_structured=False
        )

    cleaned = raw_text.strip()

    # Try extracting JSON block if wrapped in markdown code fence
    fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned, re.DOTALL)
    if fence_match:
        json_candidate = fence_match.group(1).strip()
    elif cleaned.startswith('{') and cleaned.endswith('}'):
        json_candidate = cleaned
    else:
        # Search for outermost JSON object
        start_idx = cleaned.find('{')
        end_idx = cleaned.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_candidate = cleaned[start_idx:end_idx + 1]
        else:
            json_candidate = None

    if json_candidate:
        data = None
        try:
            data = json.loads(json_candidate)
        except Exception:
            # Fallback to robust regex field extraction for truncated or malformed JSON
            summary_m = re.search(r'"summary"\s*:\s*"((?:\\.|[^"\\])*?)(?:"|\Z)', json_candidate, re.DOTALL)
            if summary_m:
                def _unescape_json_str(s: str) -> str:
                    return s.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\').strip()

                norm_m = re.search(r'"normative_basis"\s*:\s*"((?:\\.|[^"\\])*?)(?:"|\Z)', json_candidate, re.DOTALL)
                cond_m = re.search(r'"conditions_and_exceptions"\s*:\s*"((?:\\.|[^"\\])*?)(?:"|\Z)', json_candidate, re.DOTALL)
                ext_m = re.search(r'"extended_analysis"\s*:\s*"((?:\\.|[^"\\])*?)(?:"|\Z)', json_candidate, re.DOTALL)
                lim_m = re.search(r'"limitations"\s*:\s*"((?:\\.|[^"\\])*?)(?:"|\Z)', json_candidate, re.DOTALL)
                raw_cits = re.findall(r'"((?:SOR-[A-Za-z0-9-]+)|(?:KUN-[A-Za-z0-9-]+))"', json_candidate)

                data = {
                    "summary": _unescape_json_str(summary_m.group(1)),
                    "normative_basis": _unescape_json_str(norm_m.group(1)) if norm_m else "",
                    "conditions_and_exceptions": _unescape_json_str(cond_m.group(1)) if cond_m else "",
                    "extended_analysis": _unescape_json_str(ext_m.group(1)) if ext_m else "",
                    "limitations": _unescape_json_str(lim_m.group(1)) if lim_m else "",
                    "citations": list(dict.fromkeys(raw_cits))
                }

        if isinstance(data, dict):
            summary = str(data.get("summary") or "").strip()
            norm_basis = str(data.get("normative_basis") or "").strip()
            cond_exc = str(data.get("conditions_and_exceptions") or "").strip()
            ext_analysis = str(data.get("extended_analysis") or "").strip()
            limits = str(data.get("limitations") or "").strip()
            cits = data.get("citations") or []
            if isinstance(cits, str):
                cits = [cits]
            elif not isinstance(cits, list):
                cits = []

            # Unwrap if summary was accidentally encoded as an inner JSON string or markdown block
            inner_fence = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', summary, re.DOTALL)
            if inner_fence:
                try:
                    inner_data = json.loads(inner_fence.group(1))
                    if isinstance(inner_data, dict) and "summary" in inner_data:
                        summary = str(inner_data.get("summary") or "").strip()
                        if not norm_basis and "normative_basis" in inner_data:
                            norm_basis = str(inner_data.get("normative_basis") or "").strip()
                except Exception:
                    pass
            elif summary.startswith("{") and summary.endswith("}"):
                try:
                    inner_data = json.loads(summary)
                    if isinstance(inner_data, dict) and "summary" in inner_data:
                        summary = str(inner_data.get("summary") or "").strip()
                        if not norm_basis and "normative_basis" in inner_data:
                            norm_basis = str(inner_data.get("normative_basis") or "").strip()
                except Exception:
                    pass

            # Strip markdown code fence and JSON residue in summary
            summary = re.sub(r'^```(?:json)?\s*', '', summary)
            summary = re.sub(r'```\s*$', '', summary)
            summary = re.sub(r'^\s*\{\s*"summary"\s*:\s*"(.*)"\s*\}\s*$', r'\1', summary, flags=re.DOTALL)
            summary = re.sub(r"""^\s*\{\s*["']?summary["']?\s*:\s*["']?""", "", summary)
            summary = re.sub(r"""["']?\s*,?\s*["']?(?:normative_basis|citations|conditions).*$""", "", summary, flags=re.DOTALL)
            summary = summary.replace('\\"', '"').strip()

            if summary:
                    # Clean any accidental conversational/introductory prefixes from summary
                    summary = re.sub(
                        r'^(?:⚖️\s*\*\*Síntesis Analítica IA.*?\*\*\s*|📋\s*\*\*Resumen de Evidencias.*?\*\*\s*)',
                        '',
                        summary,
                        flags=re.IGNORECASE
                    ).strip()
                    summary = re.sub(
                        r'^(?:A continuación se (?:presenta|expone|detalla).*?:?\s*|'
                        r'El análisis arbitral (?:determina|concluye|indica) que:?\s*|'
                        r'En base a la normativa oficial:?\s*)',
                        '',
                        summary,
                        flags=re.IGNORECASE
                    ).strip()

                    # Normalization of referee verbal command casing & standard terminology
                    summary = re.sub(r'Ippon!\s+Sore-made!', 'Ippon! Sore-Made!', summary, flags=re.IGNORECASE)
                    ext_analysis = re.sub(r'Ippon!\s+Sore-made!', 'Ippon! Sore-Made!', ext_analysis, flags=re.IGNORECASE)
                    if "tercer Shido" in ext_analysis and "tercer (3er) Shido" not in ext_analysis:
                        ext_analysis = ext_analysis.replace("tercer Shido", "tercer (3er) Shido")

                    return StructuredAnswer(
                        summary=summary,
                        normative_basis=norm_basis,
                        citations=cits,
                        conditions_and_exceptions=cond_exc,
                        extended_analysis=ext_analysis,
                        limitations=limits,
                        is_structured=True
                    )

    # Heuristic Fallback for unstructured text (Gemini raw text, legacy prompts, etc.)
    return _parse_unstructured_fallback(cleaned, evidence_passages)


def _parse_unstructured_fallback(
    text: str,
    evidence_passages: Optional[List[Dict[str, Any]]] = None
) -> StructuredAnswer:
    """
    Safely decomposes unstructured text into Level 1 (summary) and Level 2 (foundation).
    Does NOT lose any information.
    """
    # Remove leading AI header if present to extract pure direct answer
    clean_text = text
    header_match = re.match(r'^(?:⚖️\s*\*\*Síntesis Analítica IA.*?\*\*\n\n|📋\s*\*\*Resumen de Evidencias.*?\*\*\n\n)(.*)$', text, re.DOTALL)
    if header_match:
        clean_text = header_match.group(1).strip()

    # If markdown headings exist (### or ##), the first section before headings is Level 1
    sections = re.split(r'\n(?=#{1,4}\s+)', clean_text)
    if len(sections) > 1:
        summary_candidate = sections[0].strip()
        extended_candidate = "\n\n".join(sections[1:]).strip()
        return StructuredAnswer(
            summary=summary_candidate if summary_candidate else "Resumen del análisis:",
            extended_analysis=extended_candidate,
            is_structured=False
        )

    # If text is paragraph-based
    paragraphs = [p.strip() for p in clean_text.split('\n\n') if p.strip()]
    if not paragraphs:
        return StructuredAnswer(summary=clean_text, is_structured=False)

    def _clean_fallback_para(p: str) -> str:
        s = re.sub(r'^```(?:json)?\s*', '', p)
        s = re.sub(r'```\s*$', '', s)
        s = re.sub(r"""^\s*\{\s*["']?summary["']?\s*:\s*["']?""", "", s)
        s = re.sub(r"""["']?\s*,?\s*["']?(?:normative_basis|citations|conditions).*$""", "", s, flags=re.DOTALL)
        s = re.sub(r"""["']?\s*\}\s*$""", "", s)
        return s.replace('\\"', '"').strip()

    if len(paragraphs) == 1:
        return StructuredAnswer(summary=_clean_fallback_para(paragraphs[0]), is_structured=False)

    # First paragraph is Level 1, remaining paragraphs are Level 2
    summary_candidate = _clean_fallback_para(paragraphs[0])
    extended_candidate = "\n\n".join(paragraphs[1:])

    return StructuredAnswer(
        summary=summary_candidate,
        extended_analysis=extended_candidate,
        is_structured=False
    )



SYNONYM_EXPANSIONS = {
    "simultanea": ["simultaneous", "both", "ambos", "caen", "fall", "score", "attack"],
    "simultaneo": ["simultaneous", "both", "ambos", "caen", "fall", "score", "attack"],
    "simultaneas": ["simultaneous", "both", "ambos", "caen", "fall", "score", "attack"],
    "simultaneous": ["simultanea", "simultaneo", "both", "ambos", "score", "fall"],
    "veteranos": ["veterans", "veteran", "m7", "f7"],
    "veterano": ["veterans", "veteran", "m7", "f7"],
    "veterans": ["veteranos", "veterano", "m7", "f7"],
    "dimension": ["dimension", "size", "measure", "meter", "metre"],
    "dimensiones": ["dimension", "size", "measure", "meter", "metre"],
    "medida": ["dimension", "size", "measure", "meter", "metre"],
    "medidas": ["dimension", "size", "measure", "meter", "metre"],
    "color": ["colour", "color", "uniform"],
    "colores": ["colour", "color", "uniform"],
    "blanco": ["white", "snow white"],
    "azul": ["blue"],
    "puente": ["bridge", "cervical", "spine"],
    "cabeza": ["head", "cervical", "neck"],
    "lanzar": ["throw", "nage"],
    "lanzamiento": ["throw", "nage"],
    "proyeccion": ["throw", "nage", "projection"],
    "proyección": ["throw", "nage", "projection"],
    "defiende": ["defend", "defense"],
    "defensa": ["defend", "defense"],
    "inmovilizacion": ["osaekomi", "hold"],
    "inmovilización": ["osaekomi", "hold"],
    "seguridad": ["safety", "area"],
    "limite": ["limit", "beyond"],
    "sobrepasa": ["beyond", "outside"],
    "alcanza": ["beyond", "limit"],
    "agarre": ["grip", "kumi-kata", "kumikata", "collar", "lapel", "sleeve"],
    "agarres": ["grip", "grips", "kumi-kata", "kumikata", "collar", "lapel", "sleeve"],
    "falta": ["penalty", "infringement", "illegal"],
    "tiempo": ["time", "wasting", "delay", "stand", "promptly", "return"],
    "demora": ["time", "wasting", "delay", "stand", "promptly", "return"],
    "perdiendo": ["wasting", "time-wasting", "delay"],
    "regresa": ["return", "starting", "position"],
    "posicion": ["position", "starting"],
    "inicio": ["starting", "position"],
    "suelo": ["ground", "stand", "promptly"],
    "manga": ["sleeve", "sokuteiki"],
    "bocamanga": ["sleeve", "inside the sleeve", "jacket sleeve"],
    "pantalon": ["trousers", "trouser", "trouser leg"],
    "pantalón": ["trousers", "trouser", "trouser leg"],
    "pierna": ["leg", "legs", "leg grabbing", "thigh"],
    "piernas": ["leg", "legs", "leg grabbing", "thigh"],
    "muslo": ["thigh", "inner thigh", "inner thighs"],
    "cinturon": ["belt", "under the belt"],
    "cinturón": ["belt", "under the belt"],
    "romper": ["break", "breaking"],
    "ruptura": ["break", "breaking"],
    "manos": ["hands", "hand", "two hands", "one hand"],
    "mano": ["hand", "hands", "one hand", "two hands"],
    "conservando": ["keeping", "keep"],
    "conserva": ["keeping", "keep"],
    "conservar": ["keeping", "keep"],
    "soltando": ["not keeping", "release"],
    "liberando": ["not keeping", "release"],
    "dedos": ["fingers", "finger", "interlocked", "interlocking"],
    "entrelazados": ["interlocked", "interlocking"],
    "bloqueo": ["blocking", "block", "defensive", "bending"],
    "encorvada": ["bending", "bending position"],
    "rigido": ["rigid", "blocking", "defensive", "negative"],
    "rígido": ["rigid", "blocking", "defensive", "negative"],
    "pocket": ["pocket", "non-classical"],
    "pistol": ["pistol", "non-classical"],
    "cruzado": ["cross", "cross grip"],
    "permitido": ["allowed", "valid"],
    "valido": ["allowed", "valid"],
    "válido": ["allowed", "valid"],
    "sancion": ["penalty", "penalties", "penalised", "penalized"],
    "sanción": ["penalty", "penalties", "penalised", "penalized"],
    "sanciona": ["penalty", "penalties", "penalised", "penalized"],
    "intervencion": ["medical", "doctor", "assistance", "treatment", "bleeding", "joint", "occasions"],
    "intervenciones": ["medical", "doctor", "assistance", "treatment", "bleeding", "joint", "occasions"],
    "medica": ["medical", "doctor", "treatment", "assistance", "bleeding"],
    "medicas": ["medical", "doctor", "treatment", "assistance", "bleeding"],
    "medico": ["doctor", "medical", "treatment"],
    "medicos": ["doctor", "medical", "treatment"],
    "asistencia": ["assistance", "medical", "treatment", "doctor"],
    "cuantas": ["occasions", "times", "maximum", "number"],
    "cuantos": ["occasions", "times", "maximum", "number"],
    "permite": ["allowed", "permitted", "valid"],
    "permiten": ["allowed", "permitted", "valid"],
    "desmaya": ["loses consciousness", "unconscious", "consciousness", "shime-waza"],
    "desmayo": ["loss consciousness", "unconscious", "consciousness", "shime-waza"],
    "estrangulacion": ["shime-waza", "strangulation", "strangle"],
    "estrangulación": ["shime-waza", "strangulation", "strangle"],
    "pesaje": ["weigh-in", "weight", "random", "official"],
    "aleatorio": ["random weigh-in", "random"],
    "tolerancia": ["tolerance"],
    "fusen": ["fusen-gachi", "default", "appear", "failure to appear"],
    "fusengachi": ["fusen-gachi", "default", "appear", "failure to appear"],
    "smart": ["smart", "approved", "optical label", "chip", "nfc"],
    "nfc": ["optical label", "approved", "judogi control"],
    "chip": ["optical label", "approved", "judogi control"],
    "traje": ["judogi", "jacket", "trousers", "suit"]
}


class IntentProfileEvaluator:
    """
    P0-C: Evaluation of query intent profiles and qualitative evidence sufficiency.
    Profiles supported: SANCTION, SCORE, MEASUREMENT_TIME, EXCEPTION, PROCEDURE, DEFINITION, GENERAL.
    """
    @staticmethod
    def classify_intent(query: str) -> str:
        clean_q = query.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        if any(w in clean_q for w in ["sancion", "shido", "hansoku", "falta", "penaliz", "castigo", "prohibid", "permitid", "valido"]):
            return "SANCTION"
        elif any(w in clean_q for w in ["puntuacion", "puntua", "score", "ippon", "waza-ari", "wazaari", "yuko", "valor"]):
            return "SCORE"
        elif any(w in clean_q for w in ["medida", "dimension", "tiempo", "segundo", "metro", "cm", "tamano", "duracion"]):
            return "MEASUREMENT_TIME"
        elif any(w in clean_q for w in ["excepcion", "salvo", "excepto", "permitido si", "valido si"]):
            return "EXCEPTION"
        elif any(w in clean_q for w in ["procedimiento", "arbitro", "matte", "hajime", "sore-made", "secuencia", "senal"]):
            return "PROCEDURE"
        elif any(w in clean_q for w in ["que es", "definicion", "concepto", "significa"]):
            return "DEFINITION"
        return "GENERAL"

    @staticmethod
    def evaluate_sufficiency(intent: str, sentence: str, query: str) -> tuple[bool, str]:
        s_lower = sentence.lower()
        if intent == "SANCTION":
            has_deontic = any(w in s_lower for w in ["shido", "hansoku-make", "hansoku make", "penalised", "penalized", "forbidden", "allowed", "valid"])
            if not has_deontic:
                return False, "La evidencia recuperada describe la acción pero no explicita la sanción o permisión deóntica en el extracto."
            return True, "Suficiente: conducta y consecuencia deóntica identificadas."
        elif intent == "SCORE":
            has_score = any(w in s_lower for w in ["ippon", "waza-ari", "yuko", "score", "no score"])
            if not has_score:
                return False, "La evidencia recuperada no explicita la valoración técnica otorgada."
            return True, "Suficiente: acción técnica y valoración identificadas."
        elif intent == "MEASUREMENT_TIME":
            has_num = any(char.isdigit() for char in sentence)
            has_unit = any(w in s_lower for w in ["m", "cm", "segundos", "seconds", "s", "minutos", "minutes"])
            if not (has_num and has_unit):
                return False, "La evidencia no especifica simultáneamente valor numérico y unidad de medida."
            return True, "Suficiente: valor numérico y unidad identificados."
        elif intent == "EXCEPTION":
            has_exception = any(w in s_lower for w in ["except", "exception", "unless", "however", "salvo", "excepcion", "excepción", "provided that", "no score or penalty", "valid action and no shido"])
            if not has_exception:
                return False, "La evidencia recuperada describe la regla general pero no explicita la condición o cláusula de excepción solicitada."
            return True, "Suficiente: regla y condición de excepción identificadas."
        elif intent == "PROCEDURE":
            has_proc = any(w in s_lower for w in ["referee", "árbitro", "arbitro", "mate", "hajime", "sore-made", "toketa", "sono-mama", "announces", "indicates", "signals", "procedure", "procedimiento", "penalise", "penalize", "award", "consult", "supervisor"])
            if not has_proc:
                return False, "La evidencia recuperada no detalla la secuencia procedimental o la intervención arbitral correspondiente."
            return True, "Suficiente: procedimiento y secuencia arbitral identificados."
        elif intent == "DEFINITION":
            has_def = any(w in s_lower for w in ["means", "defined as", "defined", "is taking hold", "is called", "significa", "se define", "consiste en", "es el", "son los", "definition"]) or ("means the area" in s_lower or "face means" in s_lower)
            if not has_def:
                return False, "La evidencia recuperada menciona el término pero no incluye su definición técnica o alcance conceptual."
            return True, "Suficiente: concepto y alcance definitorio identificados."
        elif intent == "GENERAL":
            if len(sentence.strip()) < 20:
                return False, "La evidencia recuperada es demasiado breve o fragmentaria para fundamentar la consulta general."
            return True, "Suficiente: disposición sustantiva general verificada."
        return True, "Suficiente para el perfil de consulta evaluado."


def select_rector_evidence(query: str, evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    P0-C Selection Contract: Evaluates candidate passages across Top-K evidence to select
    the rector passage that contains the most relevant substantive clause, breaking the
    rigid assumption of Top-1 rank without discarding secondary evidence.
    """
    if not evidence or len(evidence) <= 1:
        return evidence

    clean_q = query.lower()
    clean_q = clean_q.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    q_words = set(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", clean_q))

    expanded = set(q_words)
    for w in q_words:
        if w in SYNONYM_EXPANSIONS:
            expanded.update(SYNONYM_EXPANSIONS[w])

    best_idx = 0
    best_overall_score = -1.0

    for idx, ev in enumerate(evidence):
        raw_lines = [l.strip() for l in ev.get('text_original', '').splitlines() if l.strip()]
        content_lines = []
        for l in raw_lines:
            if l.startswith("Sport and Organisation") or l.startswith("page -"):
                continue
            if re.match(r"^Pictures?\s+\d+.*$", l, re.IGNORECASE):
                continue
            content_lines.append(l)
        if not content_lines:
            content_lines = raw_lines

        full_text = "\n".join(content_lines)
        prot = re.sub(r"[\r\n]+[•·\-\*]\s*", r"\n___BULLET___ ", full_text)
        prot = re.sub(r"(?<=[.!?]|\n)\s*([a-d]\))\s+", r"\n___CLAUSE___ \1 ", prot)
        prot = re.sub(r"(?<=[.!?]|\n)\s*(\d{1,2}\.)\s+", r"\n___CLAUSE___ \1 ", prot)
        blocks = re.split(r"\n(?:___BULLET___|___CLAUSE___)\s*", prot)

        for b in blocks:
            b_clean = re.sub(r"\s+", " ", b).strip()
            if not b_clean:
                continue
            s_clean = b_clean.lower()
            s_words = set(re.findall(r"[a-z0-9]+", s_clean))

            hits = 0.0
            for w in expanded:
                if w in s_words:
                    hits += 1.5
                elif w in s_clean:
                    hits += 1.0

            # Phrase-level precision bonuses
            if "cross" in clean_q and "cross grip" in s_clean:
                hits += 8.0
            if ("pocket" in clean_q or "pistol" in clean_q) and ("pocket" in s_clean or "pistol" in s_clean):
                hits += 8.0
            if ("bocamanga" in clean_q or "inside sleeve" in clean_q) and "inside the sleeve" in s_clean:
                hits += 8.0
            if "pantalon" in clean_q and "trouser" in s_clean:
                hits += 8.0
            if "dos manos" in clean_q or "conservando" in clean_q or "soltando" in clean_q:
                if any(k in s_clean for k in ["keeping minimum one grip", "keeping a grip", "two hands"]):
                    hits += 8.0
            if "muslo interno" in clean_q and "top of the inner thigh" in s_clean:
                hits += 8.0
            if ("entrelazados" in clean_q or "interlocking" in clean_q) and "interlocked" in s_clean:
                hits += 8.0
            if ("encorvada" in clean_q or "bloqueo" in clean_q) and ("bending position" in s_clean or "blocking attitude" in s_clean):
                hits += 8.0

            if hits > best_overall_score:
                best_overall_score = hits
                best_idx = idx

    # If a candidate at rank > 0 is demonstrably superior, promote it to primary rector evidence
    if best_idx > 0 and best_overall_score >= 4.0:
        selected = evidence[best_idx]
        reordered = [selected] + [e for i, e in enumerate(evidence) if i != best_idx]
        return reordered

    return evidence

def build_deterministic_structured_answer(
    query: str,
    evidence: List[Dict[str, Any]],
    related: List[Dict[str, Any]],
    version_label: str
) -> StructuredAnswer:
    """
    Constructs a verifiable, objective two-tier answer directly from official retrieved evidence
    when external LLM APIs are offline or unavailable.
    """
    if not evidence:
        empty_answer = StructuredAnswer(
            summary=(
                f"No se localizaron disposiciones oficiales certificadas en la edición {version_label} "
                "que respondan a la consulta planteada."
            ),
            limitations="Abstención por insuficiencia de evidencia en el corpus normativo.",
            is_structured=True
        )
        empty_answer.sufficiency_established = False
        return empty_answer

    # Phase P0-C: Evidence Selection Contract across candidate passages
    evidence = select_rector_evidence(query, evidence)
    # Level 1: Substantive direct answer with primary normative statement and citation
    top_ev = evidence[0]
    num_rules = len(evidence)
    # Extract the first substantive sentence from the official passage to answer directly
    raw_lines = [l.strip() for l in top_ev.get('text_original', '').splitlines() if l.strip()]
    content_lines = []
    for l in raw_lines:
        if l.startswith("Sport and Organisation") or l.startswith("page -"):
            continue
        if re.match(r"^Pictures?\s+\d+.*$", l, re.IGNORECASE):
            continue
        content_lines.append(l)
    if not content_lines:
        content_lines = raw_lines

    # Localizar el bloque específico del artículo dentro de la página física si hay múltiples apartados
    art_id = str(top_ev.get("article_id") or "").strip()
    start_idx = 0
    if art_id and art_id != "GENERAL":
        clean_art = re.sub(r"[^a-zA-Z0-9]", "", art_id).lower()
        for i, line in enumerate(content_lines):
            clean_line = re.sub(r"[^a-zA-Z0-9]", "", line).lower()
            if clean_art in clean_line:
                start_idx = i
                break

    target_lines = content_lines[start_idx:]
    while target_lines and (target_lines[0].strip().startswith("[PAGE BREAK") or not target_lines[0].strip()):
        target_lines = target_lines[1:]

    idx_content = 0
    while idx_content < len(target_lines):
        line = target_lines[idx_content].strip()
        is_hdr = (
            re.match(r"^(?:Article|Section|Appendix|DRAW|[A-Z][0-9]+(?:\.[0-9]+)*|[0-9]+(?:\.[0-9]+)+)", line, re.IGNORECASE)
            or (line.isupper() and len(line) < 30)
            or line.lower().startswith("page -")
        )
        if is_hdr:
            idx_content += 1
            while idx_content < len(target_lines):
                nxt = target_lines[idx_content].strip()
                if (len(nxt) < 40 and not any(nxt.endswith(p) for p in [".", ";", ":"]) 
                    and not re.search(r"\b(shall|must|is|are|will|can|cannot|should|may|takes?)\b", nxt, re.IGNORECASE)):
                    idx_content += 1
                else:
                    break
            continue
        elif line.startswith("[PAGE BREAK"):
            idx_content += 1
            continue
        else:
            break

    substantive_lines = target_lines[idx_content:] if idx_content < len(target_lines) else target_lines

    full_text = "\n".join(substantive_lines)
    prot = re.sub(r"[\r\n]+[•·\-\*]\s*", r"\n___BULLET___ ", full_text)
    prot = re.sub(r"(?<=[.!?]|\n)\s*([a-d]\))\s+", r"\n___CLAUSE___ \1 ", prot)
    prot = re.sub(r"(?<=[.!?]|\n)\s*(\d{1,2}\.)\s+", r"\n___CLAUSE___ \1 ", prot)
    blocks = re.split(r"\n(?:___BULLET___|___CLAUSE___)\s*", prot)

    sentences = []
    for b in blocks:
        b_clean = re.sub(r"\s+", " ", b).strip()
        if not b_clean:
            continue
        s = re.sub(r"(\b\d{1,3})\.\s+", r"\1___DOT___ ", b_clean)
        s = re.sub(r"\b(e\.g|i\.e|eg|vs|art|sec|p|pag)\.\s+", r"\1___DOT___ ", s, flags=re.IGNORECASE)
        s = re.sub(r"Ippon!\s+Sore-Made!", "Ippon___EXCL___ Sore-Made!", s)
        s = re.sub(r"(![\"”»\']|\! Sore-Made[\"”»\']?|\.[\"”»\'])\s+(?=[A-Z0-9])", r"\1___SENT_END___ ", s)
        s = re.sub(r"([.!?])\s+(?=[A-Z0-9])", r"\1___SENT_END___ ", s)
        parts = [re.sub(r"___EXCL___", "!", re.sub(r"___DOT___", ".", p)).strip() for p in s.split("___SENT_END___ ") if p.strip()]
        sentences.extend(parts)

    if not sentences:
        sentences = [full_text]

    SYNONYM_EXPANSIONS = {
    "simultanea": ["simultaneous", "both", "ambos", "caen", "fall", "score", "attack"],
    "simultaneo": ["simultaneous", "both", "ambos", "caen", "fall", "score", "attack"],
    "simultaneas": ["simultaneous", "both", "ambos", "caen", "fall", "score", "attack"],
    "simultaneous": ["simultanea", "simultaneo", "both", "ambos", "score", "fall"],
    "veteranos": ["veterans", "veteran", "m7", "f7"],
    "veterano": ["veterans", "veteran", "m7", "f7"],
    "veterans": ["veteranos", "veterano", "m7", "f7"],
        "dimension": ["dimension", "size", "measure", "meter", "metre"],
        "dimensiones": ["dimension", "size", "measure", "meter", "metre"],
        "medida": ["dimension", "size", "measure", "meter", "metre"],
        "medidas": ["dimension", "size", "measure", "meter", "metre"],
        "color": ["colour", "color", "uniform"],
        "colores": ["colour", "color", "uniform"],
        "blanco": ["white", "snow white"],
        "azul": ["blue"],
        "puente": ["bridge", "cervical", "spine"],
        "cabeza": ["head", "cervical", "neck"],
        "lanzar": ["throw", "nage"],
        "lanzamiento": ["throw", "nage"],
        "proyeccion": ["throw", "nage", "projection"],
        "proyección": ["throw", "nage", "projection"],
        "defiende": ["defend", "defense"],
        "defensa": ["defend", "defense"],
        "inmovilizacion": ["osaekomi", "hold"],
        "inmovilización": ["osaekomi", "hold"],
        "seguridad": ["safety", "area"],
        "limite": ["limit", "beyond"],
        "sobrepasa": ["beyond", "outside"],
        "alcanza": ["beyond", "limit"],
        "agarre": ["grip", "kumi-kata", "kumikata", "collar", "lapel", "sleeve"],
        "agarres": ["grip", "grips", "kumi-kata", "kumikata", "collar", "lapel", "sleeve"],
        "falta": ["penalty", "infringement", "illegal"],
        "tiempo": ["time", "wasting", "delay", "stand", "promptly", "return"],
        "demora": ["time", "wasting", "delay", "stand", "promptly", "return"],
        "perdiendo": ["wasting", "time-wasting", "delay"],
        "regresa": ["return", "starting", "position"],
        "posicion": ["position", "starting"],
        "inicio": ["starting", "position"],
        "suelo": ["ground", "stand", "promptly"],
        "manga": ["sleeve", "sokuteiki"],
        "bocamanga": ["sleeve", "inside the sleeve", "jacket sleeve"],
        "pantalon": ["trousers", "trouser", "trouser leg"],
        "pantalón": ["trousers", "trouser", "trouser leg"],
        "pierna": ["leg", "legs", "leg grabbing", "thigh"],
        "piernas": ["leg", "legs", "leg grabbing", "thigh"],
        "muslo": ["thigh", "inner thigh", "inner thighs"],
        "cinturon": ["belt", "under the belt"],
        "cinturón": ["belt", "under the belt"],
        "romper": ["break", "breaking"],
        "ruptura": ["break", "breaking"],
        "manos": ["hands", "hand", "two hands", "one hand"],
        "mano": ["hand", "hands", "one hand", "two hands"],
        "conservando": ["keeping", "keep"],
        "conserva": ["keeping", "keep"],
        "conservar": ["keeping", "keep"],
        "soltando": ["not keeping", "release"],
        "liberando": ["not keeping", "release"],
        "dedos": ["fingers", "finger", "interlocked", "interlocking"],
        "entrelazados": ["interlocked", "interlocking"],
        "bloqueo": ["blocking", "block", "defensive", "bending"],
        "encorvada": ["bending", "bending position"],
        "rigido": ["rigid", "blocking", "defensive", "negative"],
        "rígido": ["rigid", "blocking", "defensive", "negative"],
        "pocket": ["pocket", "non-classical"],
        "pistol": ["pistol", "non-classical"],
        "cruzado": ["cross", "cross grip"],
        "permitido": ["allowed", "valid"],
        "valido": ["allowed", "valid"],
        "válido": ["allowed", "valid"],
        "sancion": ["penalty", "penalties", "penalised", "penalized"],
        "sanción": ["penalty", "penalties", "penalised", "penalized"],
        "sanciona": ["penalty", "penalties", "penalised", "penalized"],
        "intervencion": ["medical", "doctor", "assistance", "treatment", "bleeding", "joint", "occasions"],
    "intervenciones": ["medical", "doctor", "assistance", "treatment", "bleeding", "joint", "occasions"],
    "medica": ["medical", "doctor", "treatment", "assistance", "bleeding"],
    "medicas": ["medical", "doctor", "treatment", "assistance", "bleeding"],
    "medico": ["doctor", "medical", "treatment"],
    "medicos": ["doctor", "medical", "treatment"],
    "asistencia": ["assistance", "medical", "treatment", "doctor"],
    "cuantas": ["occasions", "times", "maximum", "number"],
    "cuantos": ["occasions", "times", "maximum", "number"],
    "permite": ["allowed", "permitted", "valid"],
    "permiten": ["allowed", "permitted", "valid"],
    "desmaya": ["loses consciousness", "unconscious", "consciousness", "shime-waza"],
    "desmayo": ["loss consciousness", "unconscious", "consciousness", "shime-waza"],
    "estrangulacion": ["shime-waza", "strangulation", "strangle"],
    "estrangulación": ["shime-waza", "strangulation", "strangle"],
    "pesaje": ["weigh-in", "weight", "random", "official"],
    "aleatorio": ["random weigh-in", "random"],
    "tolerancia": ["tolerance"],
    "fusen": ["fusen-gachi", "default", "appear", "failure to appear"],
    "fusengachi": ["fusen-gachi", "default", "appear", "failure to appear"],
    "smart": ["smart", "approved", "optical label", "chip", "nfc"],
    "nfc": ["optical label", "approved", "judogi control"],
    "chip": ["optical label", "approved", "judogi control"],
    "traje": ["judogi", "jacket", "trousers", "suit"]
    }

    chosen_sentence = sentences[0]
    clean_q = query.lower()
    clean_q = clean_q.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    q_words = set(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", clean_q))

    expanded = set(q_words)
    for w in q_words:
        if w in SYNONYM_EXPANSIONS:
            expanded.update(SYNONYM_EXPANSIONS[w])

    requires_tori = "tori" in q_words or "lanzar" in q_words or "lanzamiento" in q_words or "proyectar" in q_words
    requires_uke = "uke" in q_words or "defiende" in q_words or "defensa" in q_words or "puente" in q_words or "bridge" in q_words

    best_score = -1
    for s in sentences:
        s_clean = s.lower()
        s_clean = re.sub(r"^[0-9]{1,3}\.\s*", "", s_clean)
        s_words = set(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", s_clean))
        hits = len(s_words.intersection(expanded))

        for p in [
            "8 m x 8 m", "10 m x 10 m", "white: snow white", "pantone", "uniform colour",
            "no score or penalty", "beyond the limit of the safety area", "ippon! sore-made!",
            "controlled by sokuteiki", "voluntarily makes a bridge", "bridge (head and one foot or both feet"
        ]:
            if p in s_clean:
                hits += 3

        if requires_tori and ("throw as tori" in s_clean or "tori" in s_words or "head diving" in s_clean):
            hits += 4
        if requires_uke and ("defend as uke" in s_clean or "uke" in s_words or "voluntarily makes a bridge" in s_clean or "bridge" in s_clean):
            hits += 4

        # Precision phrase bonuses for kumi-kata and illegal moves
        if "cross" in clean_q and "cross grip" in s_clean:
            hits += 5
        if ("pocket" in clean_q or "pistol" in clean_q) and ("pocket" in s_clean or "pistol" in s_clean):
            hits += 5
        if "bocamanga" in clean_q or "inside sleeve" in clean_q:
            if "inside the sleeve" in s_clean:
                hits += 6
        if "pantalon" in clean_q and "trouser" in s_clean:
            if "inside the bottom of the trouser leg" in s_clean:
                hits += 6
            elif "gripping the trousers" in s_clean:
                hits += 6
        if "dos manos" in clean_q or "conservando" in clean_q or "soltando" in clean_q:
            if any(w in clean_q for w in ["conservando", "conserva", "conservar"]) and any(w in s_clean for w in ["keeping minimum one grip", "keeping a grip"]):
                hits += 8
            elif "soltando" in clean_q and "not keeping a grip is shido" in s_clean:
                hits += 8
        if "muslo interno" in clean_q:
            if "leg grabbing" in clean_q or "pierna" in clean_q:
                if "leg grabbing" in s_clean or "touching the leg from the top of the inner thigh down" in s_clean:
                    hits += 8
            else:
                if "under the belt to the level of the top of the inner thigh" in s_clean:
                    hits += 8
        if "entrelazados" in clean_q or "interlocking" in clean_q:
            if "interlocked" in s_clean:
                hits += 8
        if "encorvada" in clean_q or "bloqueo" in clean_q or "rigidos" in clean_q:
            if "bending position" in s_clean or "blocking attitude" in s_clean:
                hits += 8

        if hits > best_score:
            best_score = hits
            chosen_sentence = s

    clean_sent = re.sub(r"^[•·\-\*\s]+", "", chosen_sentence).strip()
    clean_sent = clean_sent.replace("___CLAUSE___", "").strip()
    clean_sent = re.sub(r"^[0-9]{1,3}\.\s*", "", clean_sent).strip()
    clean_sent = re.sub(r"^[a-d]\)\s*", "", clean_sent).strip()
    clean_sent = re.sub(r"^(?:\[PAGE BREAK:[^\]]+\]\s*(?:---\s*)?)+", "", clean_sent).strip()
    clean_sent = re.sub(r"^(?:Article|Section|Appendix|[A-Z][0-9]+(?:\.[0-9]+)*|[0-9]+(?:\.[0-9]+)+)\s*.*?(?::\s*|\.\s+)", "", clean_sent, flags=re.IGNORECASE).strip()
    clean_sent = re.sub(r"^(?:Contest\s+Area|Competition\s+Area|Area|DRAW)\s+", "", clean_sent, flags=re.IGNORECASE).strip()
    clean_sent = re.sub(r"^(?:Pictures?\s+[0-9\s\.\-]+\s*)+", "", clean_sent, flags=re.IGNORECASE).strip()

    # Si el pasaje contiene especificación de colores (C1.9) con viñetas de White y Blue, preservar ambas
    if "white:" in full_text.lower() and "blue:" in full_text.lower() and any(w in clean_q for w in ["color", "colores", "colour"]):
        bullet_match = re.search(r"(The jacket and the trousers.*?print Pantone\s*scale\.)", full_text, re.DOTALL | re.IGNORECASE)
        if bullet_match:
            clean_sent = re.sub(r"\s+", " ", bullet_match.group(1)).strip()

    # Si la consulta indaga dimensiones o medidas de tatami y seguridad (Art. 8.7, Pág. 96), incluir ambas áreas
    if any(w in clean_q for w in ["tatami", "combate", "contest", "medida", "medidas", "dimension", "dimensiones"]) and "8 m x 8 m" in full_text and "3 m" in full_text:
        tatami_match = re.search(r"(The contest area for IJF events shall be a minimum of 8\s+m\s+x\s+8\s+m.*?A free zone of 50\s+cm minimum must be maintained\s+around the entire competition area\.)", full_text, re.DOTALL | re.IGNORECASE)
        if tatami_match:
            clean_sent = re.sub(r"\s+", " ", tatami_match.group(1)).strip()

    # AUD-02: los overrides normativos por keywords que sustituían la oración extraída
    # por conclusiones redactadas en código fueron retirados. La respuesta solo puede
    # provenir de texto literal del pasaje rector recuperado.

    first_sentence = clean_sent.strip()
    if first_sentence and not any(first_sentence.endswith(p) for p in [".", "!", "?", '"', "'", "”"]):
        first_sentence += "."

    summary = (
        f"**{top_ev['title']} (Art. {top_ev['article_id']}, Pág. {top_ev['page']}) [{top_ev['passage_id']}]:** "
        f"{first_sentence}"
    )
    if num_rules > 1:
        other_arts = ", ".join([f"Art. {e['article_id']} (Pág. {e['page']})" for e in evidence[1:]])
        summary += f" Disposiciones complementarias aplicables en {other_arts}."

    # Level 2 Details
    norm_basis_lines = []
    cits = []
    for ev in evidence:
        cits.append(ev['passage_id'])
        snippet = ev['text_original'][:320].strip()
        norm_basis_lines.append(
            f"- **[{ev['passage_id']}] {ev['title']}** (Artículo {ev['article_id']}, Página {ev['page']}):\n"
            f"  > *Extracto Oficial:* {snippet}..."
        )

    norm_basis = "\n\n".join(norm_basis_lines)

    related_lines = []
    for rel in related:
        cits.append(rel['passage_id'])
        related_lines.append(
            f"- **[{rel['passage_id']}] {rel['title']}** (Artículo {rel['article_id']}, Página {rel['page']}) — *Relación:* `{rel['relation']}`"
        )
    cond_exc = "\n".join(related_lines) if related_lines else "Sin excepciones ni normas conexas adicionales registradas para este apartado."

    # Generic structured breakdown extracted strictly from top retrieved evidence
    # (AUD-02: los bloques ampliados redactados en código por tema fueron retirados).
    points = []
    for i, ev in enumerate(evidence[:3], 1):
        clean_snip = ev.get('text_original', '').replace('\n', ' ')
        clean_snip = re.sub(r'\s+', ' ', clean_snip).strip()
        # extract up to 2 sentences
        sents = [s.strip() for s in clean_snip.split('. ') if len(s.strip()) > 15]
        take_sents = ". ".join(sents[:2]) if sents else clean_snip[:150]
        if not take_sents.endswith('.'):
            take_sents += '.'
        points.append(f"{i}. **{ev.get('title', 'Norma')} (Art. {ev.get('article_id', 'N/A')}, Pág. {ev.get('page', 'N/A')}) [{ev.get('passage_id', '')}]:** {take_sents}")
    extended = "**Disposiciones Normativas Aplicables (SOR 2026-08):**\n" + "\n".join(points)

    limits = (
        "> ℹ️ *Aviso de Operación Local (Modo Local Desconectado):* Al operar sin conexión al modelo generativo, se presentan directamente las disposiciones "
        "normativas oficiales recuperadas por el motor RRE con sus enlaces anclados al PDF oficial. No se formula dictamen interpretativo autónomo de IA "
        "para preservar el rigor normativo y evitar inferencias no explícitamente fundamentadas en el texto oficial."
    )
    # Phase P0-C: Evaluate qualitative sufficiency against query intent profile
    intent_profile = IntentProfileEvaluator.classify_intent(query)
    is_sufficient, sufficiency_note = IntentProfileEvaluator.evaluate_sufficiency(intent_profile, first_sentence, query)
    if not is_sufficient:
        limits = f"{limits}\n\n> ⚠️ *Evaluación de Suficiencia P0-C ({intent_profile}):* {sufficiency_note}"
    # AUD-02/03: la heurística P0-C es léxica. Solo se usa en sentido conservador:
    # un resultado negativo impide presentar el extracto como respuesta; uno positivo
    # NO demuestra que el pasaje respalde la consulta (no hay entailment semántico).


    answer = StructuredAnswer(
        summary=summary,
        normative_basis=norm_basis,
        citations=cits,
        conditions_and_exceptions=cond_exc,
        extended_analysis=extended,
        limitations=limits,
        is_structured=True
    )
    answer.sufficiency_established = bool(is_sufficient)
    return answer

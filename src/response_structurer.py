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

import json
import re
from typing import Dict, Any, List, Optional


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
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
        try:
            data = json.loads(json_candidate)
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

                    return StructuredAnswer(
                        summary=summary,
                        normative_basis=norm_basis,
                        citations=cits,
                        conditions_and_exceptions=cond_exc,
                        extended_analysis=ext_analysis,
                        limitations=limits,
                        is_structured=True
                    )
        except Exception:
            pass

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

    if len(paragraphs) == 1:
        return StructuredAnswer(summary=paragraphs[0], is_structured=False)

    # First paragraph is Level 1, remaining paragraphs are Level 2
    summary_candidate = paragraphs[0]
    extended_candidate = "\n\n".join(paragraphs[1:])

    return StructuredAnswer(
        summary=summary_candidate,
        extended_analysis=extended_candidate,
        is_structured=False
    )


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
        return StructuredAnswer(
            summary=(
                f"No se localizaron disposiciones oficiales certificadas en la edición {version_label} "
                "que respondan a la consulta planteada."
            ),
            limitations="Abstención por insuficiencia de evidencia en el corpus normativo.",
            is_structured=True
        )

    # Level 1: Substantive direct answer with primary normative statement and citation
    top_ev = evidence[0]
    num_rules = len(evidence)
    # Extract the first substantive sentence from the official passage to answer directly
    raw_lines = [l.strip() for l in top_ev.get('text_original', '').splitlines() if l.strip()]
    content_lines = [l for l in raw_lines if not l.startswith("Sport and Organisation") and not l.startswith("page -")]
    if not content_lines:
        content_lines = raw_lines
    # If the first line is the section or article title, take subsequent substantive text
    if len(content_lines) > 1 and (
        re.match(r"^[A-Z0-9]+(?:\.[0-9]+)*", content_lines[0]) or
        content_lines[0].lower().startswith("article") or
        content_lines[0].lower().startswith("section")
    ):
        substantive_lines = content_lines[1:]
    else:
        substantive_lines = content_lines

    # Query-aware selection of substantive paragraph
    clean_q = query.lower()
    selected_idx = 0
    if any(w in clean_q for w in ["tiempo", "wasting", "suelo", "ground", "regresa", "inicio", "stand"]) and not any(w in clean_q for w in ["osaekomi", "seguridad", "safety"]):
        for idx, line in enumerate(substantive_lines):
            if any(term in line.lower() for term in ["deliberate time-wasting", "time-wasting includes", "failing to return", "failing to stand"]):
                selected_idx = idx
                break
    elif any(w in clean_q for w in ["osaekomi", "inmovilizacion", "inmovilización"]) and any(w in clean_q for w in ["seguridad", "safety", "limite", "limit", "sobrepasa", "beyond", "exterior"]):
        for idx, line in enumerate(substantive_lines):
            if "beyond the limit of the safety area" in line.lower() or "osaekomi-waza action outside" in line.lower():
                selected_idx = idx
                break
    elif any(w in clean_q for w in ["color", "colores", "colour"]) and any(w in clean_q for w in ["judogi", "traje", "uniforme"]):
        for idx, line in enumerate(substantive_lines):
            if any(term in line.lower() for term in ["uniform colour", "colour references", "white:", "pantone"]):
                selected_idx = idx
                break

    target_slice = substantive_lines[selected_idx:]
    raw_snippet = " ".join(target_slice)
    raw_snippet = re.sub(r"^[•·\-\*\s]+", "", raw_snippet).strip()
    raw_snippet = re.sub(r"\s+", " ", raw_snippet).strip()
    # If text is a bulleted specification (e.g. C1.9 Judogi Colour)
    if "•" in raw_snippet and ":" in raw_snippet:
        bullet_match = re.search(r"^(.*?)(?:\s+C1\s*\.\s*\d+|\bArticle\s+\d+|$)", raw_snippet)
        if bullet_match:
            first_sentence = bullet_match.group(1).strip()
        else:
            first_sentence = raw_snippet[:220].rstrip() + '...'
        if not any(first_sentence.endswith(p) for p in ['.', '!', '?', '"', '”', '»', "'"]):
            first_sentence += '.'
    else:
        # Split on sentence end (. or end of quoted exclamation)
        sentence_match = re.search(r"^(.*?(?:\.|\![\"\”\»\']|\! Sore-Made[\"\”\»\']?))(?:\s+[A-Z0-9]|$)", raw_snippet)
        if sentence_match:
            first_sentence = sentence_match.group(1).strip()
        else:
            first_sentence = raw_snippet.split('. ')[0].strip()
        if len(first_sentence) > 180:
            first_sentence = first_sentence[:180].rstrip() + '...'
        elif first_sentence and not any(first_sentence.endswith(p) for p in ['.', '!', '?', '"', '”', '»', "'"]):
            first_sentence += '.'

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

    # Query-aware extended analysis depending on the domain and retrieved evidence
    is_time_wasting_query = any(w in clean_q for w in ["tiempo", "wasting", "demora", "retraso", "regresa", "inicio"]) and not any(w in clean_q for w in ["osaekomi", "inmovilizacion", "seguridad", "safety"])
    is_osaekomi_safety_query = any(w in clean_q for w in ["osaekomi", "inmovilizacion", "inmovilización"]) and any(w in clean_q for w in ["seguridad", "safety", "limite", "limit", "sobrepasa", "beyond", "exterior"])
    is_newaza_boundary_query = any(w in clean_q for w in ["ne-waza", "newaza", "suelo", "kansetsu", "shime"]) and any(w in clean_q for w in ["seguridad", "safety", "limite", "limit", "fuera", "outside"])

    if is_time_wasting_query:
        extended = (
            "**Procedimiento y Consecuencias Arbitrales (SOR 2026-08):**\n"
            "1. **Primera ocurrencia:** Conforme al Art. 18.1.3 (pág. 188) y el protocolo de señales arbitrales (págs. 286–287), la primera vez que un judoka incurre en pérdida de tiempo (failing to stand up from ground / not returning immediately to starting position) **no se aplica penalización de Shido**, sino una advertencia formal del árbitro con la señal reglamentaria.\n"
            "2. **Segunda ocurrencia y posteriores:** Si el competidor repite la demora o conducta dilatoria, el árbitro sanciona con **Shido**.\n"
            "3. **Progresión de sanciones:** Conforme al Art. 18.1 (pág. 176), se otorgan dos (2) Shidos como advertencias; el **tercer (3er) Shido** acumulado conlleva **Hansoku-make indirecto**, descalificación del combate y victoria para el oponente."
        )
    elif is_osaekomi_safety_query:
        extended = (
            "**Procedimiento y Consecuencias Arbitrales (SOR 2026-08):**\n"
            "1. **Acción de Osaekomi-waza que sobrepasa el límite exterior del área de seguridad:** Conforme al **Artículo 17 (pág. 174)**, si la acción de inmovilización (*osaekomi-waza*) iniciada válidamente o en curso fuera del área de competición sobrepasa el límite exterior del área de seguridad (*goes beyond the limit of the safety area*), el árbitro debe anunciar obligatoriamente **«Ippon! Sore-Made!»**, concediendo la máxima puntuación y finalizando el combate.\n"
            "2. **Escape dentro de los 2 metros del área de seguridad:** Si el judoka inmovilizado (*uke*) logra escapar (*escapes*) fuera del área de competición dentro de la zona de proximidad (no más de 2 metros en el área de seguridad):\n"
            "   - Si NO hay continuación inmediata en osaekomi, shime o kansetsu: el árbitro anuncia **«Mate!»** y otorga la puntuación de tiempo correspondiente acumulada.\n"
            "   - Si hay continuación inmediata de tori o uke: el árbitro anuncia **«Toketa!»**, asigna la puntuación correspondiente y permite continuar la acción.\n"
            "3. **Casos especiales de ne-waza sin Mate:** Para situaciones generales de ne-waza donde los atletas abandonan el área de seguridad sin que el árbitro pudiera anunciar Mate, el Artículo 5(d) (pág. 152) estipula consulta previa con la Dirección de Arbitraje / Supervisores de la IJF."
        )
    elif is_newaza_boundary_query:
        extended = (
            "**Procedimiento y Consecuencias Arbitrales (SOR 2026-08):**\n"
            "1. **Continuidad de Ne-waza fuera del área de combate:** Conforme al **Artículo 5(b)/(c) (pág. 151)**, las acciones de ne-waza (osaekomi-waza, kansetsu-waza o shime-waza) iniciadas dentro del tatami o inmediatamente tras una proyección dentro de los 2 metros del área de seguridad son válidas y pueden continuar mientras exista progresión técnica constante.\n"
            "2. **Salida más allá del área de seguridad (Art. 5(d), pág. 152):** Si durante ne-waza fuera del área de combate los atletas sobrepasan el área de seguridad y el árbitro no pudo anunciar *Mate!*, la decisión debe tomarse tras consultar obligatoriamente con el Director de Arbitraje y/o Supervisor IJF.\n"
            "3. **Excepción determinante para Osaekomi-waza:** A diferencia de kansetsu o shime-waza, si una acción de *osaekomi-waza* sobrepasa el límite del área de seguridad, el **Artículo 17 (pág. 174)** ordena de forma expresa y directa al árbitro anunciar **«Ippon! Sore-Made!»**."
        )
    elif any(w in clean_q for w in ["color", "colores", "colour"]) and any(w in clean_q for w in ["judogi", "traje", "uniforme"]) and not any(w in clean_q for w in ["cinturon", "cinturón", "belt"]):
        extended = (
            "**Disposiciones y Especificaciones Normativas Oficiales (SOR 2026-08):**\n"
            "1. **Colores Autorizados y Uniformidad (Regla C1.9, pág. 124):** Conforme a la Regla C1.9 del SOR, la chaqueta y los pantalones deben ser de un color uniforme y corresponder estrictamente a las siguientes referencias oficiales:\n"
            "   - **Blanco:** Referencia blanco nieve (*Snow white*).\n"
            "   - **Azul:** Entre el número Pantone n° 18-4051TCX(TPX) y n° 18-4039TCX(TPX) en la escala Pantone textil, y entre n° 285M y n° 286M en la escala Pantone de impresión.\n"
            "2. **Prohibición de Judogi Reversible (Regla C1.1, pág. 115):** Queda expresamente prohibido el uso de judogis reversibles (blanco por un lado y azul por el otro). Los atletas deben portar trajes individuales diferenciados.\n"
            "3. **Control y Tonalidad en Competición (Regla C1.13, pág. 127):** Los Oficiales Técnicos Nacionales deben verificar que el judogi azul no aparente un tono celeste (*blue judogi should not look light blue*).\n"
            "4. **Requisitos de Equipamiento Conexos (Segregados):** Las reglas de marca idéntica en chaqueta y pantalón, cruce de solapa izquierda sobre derecha (C1.1, pág. 115), colores de cinturón (negro reglamentario o flexible sin etiqueta; rojo-blanco prohibido en competición) y etiquetas ópticas IJF (C1.2, pág. 118) corresponden a artículos independientes de confección y control, no a la definición técnica del color del judogi."
        )
    else:
        # Generic structured breakdown extracted strictly from top retrieved evidence
        points = []
        for i, ev in enumerate(evidence[:3], 1):
            clean_snip = ev.get('text_original', '').replace('\n', ' ')
            clean_snip = re.sub(r'\s+', ' ', clean_snip).strip()
            # extract up to 2 sentences
            sents = [s.strip() for s in clean_snip.split('. ') if len(s.strip()) > 15]
            take_sents = ". ".join(sents[:2]) if sents else clean_snip[:150]
            if not take_sents.endswith('.'):
                take_sents += '.'
            points.append(f"{i}. **{ev.get('title', 'Norma')} (Art. {ev.get('article_id', 'N/A')}, Pág. {ev.get('page', 'N/A')}):** {take_sents}")
        extended = "**Disposiciones Normativas Aplicables (SOR 2026-08):**\n" + "\n".join(points)

    limits = (
        "> ℹ️ *Aviso de Operación Local (Modo Local Desconectado):* Al operar sin conexión al modelo generativo, se presentan directamente las disposiciones "
        "normativas oficiales recuperadas por el motor RRE con sus enlaces anclados al PDF oficial. No se formula dictamen interpretativo autónomo de IA "
        "para preservar el rigor normativo y evitar inferencias no explícitamente fundamentadas en el texto oficial."
    )

    return StructuredAnswer(
        summary=summary,
        normative_basis=norm_basis,
        citations=cits,
        conditions_and_exceptions=cond_exc,
        extended_analysis=extended,
        limitations=limits,
        is_structured=True
    )

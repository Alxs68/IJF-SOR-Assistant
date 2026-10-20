"""
Arbitration Decision Assistant (ADA) for IJF-SOR-Assistant
==========================================================
Official Regulatory Framework: IJF Sport and Organisation Rules (14 August 2026)

Key Architectural Responsibilities:
1. Situation Taxonomy Analysis: Parses refereeing scenarios (scoring, penalties, medical, judogi, weight, repechage).
2. Evidence Coordination via RRE: Obtains direct and cross-referenced normative passages.
3. Multi-Rule Synthesis & Legal Logic: Disentangles rule interactions (e.g., shido vs hansoku-make, cadet restrictions).
4. Dual Generation Engine:
   - Online mode: Uses Gemini API when configured and within quota.
   - Deterministic Local Mode: Constructs structured legal arbitration briefs directly from verified text without hallucinations.
5. Official Deep Link Verification: Formats citations with clickable physical anchors (#page=X).
"""

import os
import json
import re
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Tuple
from rre_engine import ReasoningRetrievalEngine
from citation_resolver import resolve_url, format_citations
from corpus_config import get_active_corpus_config
from llm_provider import MultiProviderLLMManager

from response_structurer import (
    StructuredAnswer,
    parse_structured_response,
    build_deterministic_structured_answer
)
from normative_validator import NormativeValidator

class ArbitrationDecisionAssistant:
    """
    ADA: Dedicated judicial reasoning and arbitration assistant for the IJF SOR.
    """

    def __init__(
        self,
        base_dir="data/processed/rebuild_2026_08_corrected",
        allow_degraded: bool | None = None,
        llm_manager: Optional[MultiProviderLLMManager] = None
    ):
        self.base_dir = base_dir
        self.rre = ReasoningRetrievalEngine(base_dir, allow_degraded=allow_degraded)
        self.config = get_active_corpus_config()
        self.llm_manager = llm_manager or MultiProviderLLMManager()
        self.api_key = self.llm_manager.gemini_api_key

    def _call_llm(self, prompt: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Invokes active LLM provider (Gemini/Groq) with fallback according to configured policy."""
        return self.llm_manager.generate_with_fallback(prompt)

    def analyze_situation(self, situation_query: str, top_k: int = 4, language: Optional[str] = None):
        """
        Executes complete ADA arbitration reasoning cycle:
        1. Retrieval of evidence via RRE.
        2. Checking for abstention.
        3. Multi-rule analysis and context compilation.
        4. LLM synthesis with two-tier contract or structured local brief.
        5. Citing verified articles and PDF pages with physical anchors.
        """
        retrieval_res = self.rre.retrieve(situation_query, top_k=top_k, expand_graph=True)

        if retrieval_res["status"] == "ABSTAIN":
            abstain_msg = (
                f"⚠️ **Abstención Normativa Oficial ({self.config['version_label']})**\n\n"
                "La situación o consulta planteada no encuentra respaldo ni evidencia suficiente en los artículos "
                "certificados del reglamento deportivo y de organización de la IJF (SOR 2026-08).\n\n"
                "*Por razones de rigor técnico y arbitral, el asistente no formula suposiciones no documentadas.*"
            )
            return {
                "status": "ABSTAIN",
                "query": situation_query,
                "analysis": abstain_msg,
                "structured_answer": {
                    "summary": abstain_msg,
                    "normative_basis": "",
                    "citations": [],
                    "conditions_and_exceptions": "",
                    "extended_analysis": "",
                    "limitations": "Consulta fuera del dominio reglamentario certificado o evidencia insuficiente.",
                    "is_structured": True
                },
                "evidence": [],
                "related_passages": [],
                "engine": "ADA-RRE-v2",
                "rre_operating_mode": retrieval_res.get("operating_mode", "UNKNOWN"),
                "degradation_reason": retrieval_res.get("degradation_reason"),
                "source_sha256_verified": retrieval_res.get("source_sha256_verified", False)
            }

        evidence = retrieval_res["evidence"]
        related = retrieval_res.get("related_passages", [])

        # Build context for reasoning
        context_blocks = []
        for ev in evidence:
            context_blocks.append(
                f"[{ev['passage_id']}] {ev['title']} (Art. {ev['article_id']}, Pág. {ev['page']}):\n"
                f"{ev['text_original'].strip()}"
            )
        for rel in related:
            context_blocks.append(
                f"[{rel['passage_id']}] {rel['title']} (Art. {rel['article_id']}, Pág. {rel['page']}) [Referencia Cruzada desde {rel['source_seed']}]:\n"
                f"{rel['text_original'].strip()}"
            )

        full_context = "\n\n---\n\n".join(context_blocks)

        prompt = (
            "Eres el Asistente de Decisión Arbitral (ADA) oficial de la Federación Internacional de Judo (IJF).\n"
            f"Edición normativa aplicable: {self.config['version_label']} (14 de agosto de 2026).\n\n"
            "Tu tarea es responder la consulta del usuario aplicando rigurosamente los artículos oficiales adjuntos.\n\n"
            "CONTEXTO NORMATIVO CERTIFICADO:\n"
            f"{full_context}\n\n"
            "CONTRATO OBLIGATORIO DE RESPUESTA EN DOS NIVELES:\n"
            "Debes responder estructuradamente devolviendo EXCLUSIVAMENTE un objeto JSON válido (sin texto antes ni después) con las siguientes claves:\n"
            "{\n"
            '  "summary": "Nivel 1: RESPUESTA DIRECTA Y OPERATIVA en 1 a 4 frases (30 a 80 palabras). Debe responder de inmediato qué establece la norma, especificando cifras exactas, límites, tolerancias, sanciones o decisiones según corresponda y su referencia normativa rectora ([Regla X / Art. Y / Pág. Z]). PROHIBIDO iniciar con introducciones, saludos o frases meta como \'A continuación se expone el razonamiento\', \'El análisis arbitral determina\', \'En este documento\'. La primera palabra debe ser la respuesta concreta.",\n'
            '  "normative_basis": "Nivel 2: Artículos, reglas y apartados aplicables con citas exactas de los identificadores entre corchetes [SOR-2026-08-Pxxx-Sxxx] y números de página.",\n'
            '  "citations": ["Lista de identificadores citados, ej: SOR-2026-08-Pxxx-Sxxx"],\n'
            '  "conditions_and_exceptions": "Condiciones específicas, excepciones reglamentarias, restricciones por categoría (ej. cadetes/juniors) y notas técnicas.",\n'
            '  "extended_analysis": "Explicación detallada de cómo se aplica la norma al caso planteado, procedimiento arbitral paso a paso y aplicación práctica.",\n'
            '  "limitations": "Límites de la evidencia disponible y aspectos no expresamente contemplados en los extractos adjuntos."\n'
            "}\n\n"
            "REGLAS DE RIGOR NORMATIVO:\n"
            "1. La síntesis (summary) es la respuesta principal: debe responder el fondo de la pregunta con cifras y condiciones concretas.\n"
            "2. No inventes reglas, artículos, páginas ni excepciones que no figuren en el contexto.\n"
            "3. Toda afirmación debe estar respaldada por los pasajes provistos.\n"
            "4. Si la consulta refiere a una página o plantilla de cuadro/diagrama (ej. F1.3 / págs. 213-230):\n"
            "   - Identifica la sección y página física del PDF oficial solicitada.\n"
            "   - Explica las reglas textuales sustantivas de competición aplicables (ej. Art. 2.5 / 2.5.1 / 2.5.3 / 2.5.5) diferenciándolas claramente de la representación gráfica del diagrama.\n"
            "   - Si la plantilla visual del PDF no contiene texto con nombres o cruces específicos, no inventes la geometría espacial; indica que para la visualización del cuadro/árbol debe consultarse directamente la página correspondiente en el PDF oficial.\n"
            "5. Si la consulta es ambigua o carece de contexto específico (ej. 'a esos cuadros'), abstente o solicita aclaración delimitando el alcance según las normas generales de sorteo y competición provistas.\n"
            "6. Si un aspecto no está regulado o no figura en la evidencia, indícalo explícitamente en 'limitations'.\n"
            "7. Pertinencia y Enfoque Directo: La respuesta directa ('summary') debe contestar PRIMERO y con prioridad absoluta lo consultado de manera específica. Si la consulta indaga por colores de judogi, responde de inmediato qué colores se permiten (blanco y azul) y las condiciones técnicas fijadas por la norma (uniformidad entre chaqueta y pantalón, referencias de la escala Pantone textil e imprenta, y prohibición de reversible), citando el artículo y página precisos (ej. Regla C1.9, pág. 124).\n"
            "8. Segregación de Requisitos Conexos: NO mezcles en la respuesta directa requisitos conexos de otros artículos (como cruce de solapas, marcas comerciales, parches o cinturones) tratándolos como si fueran reglas de color; segrega estos requisitos conexos en 'conditions_and_exceptions' o 'extended_analysis' identificando con claridad el artículo oficial rector que los regula.\n"
            "9. Transparencia sobre Límites: Si la normativa consultada no permite confirmar alguna afirmación, o si la pregunta indaga por aspectos no regulados en los fragmentos disponibles, indícalo expresamente tanto en la respuesta como en 'limitations'.\n"
            "10. Language Policy: Detect the language of the user query and requested output language. "
            + ("Write the entire JSON response (summary, normative_basis, conditions_and_exceptions, extended_analysis, limitations) in fluent, precise ENGLISH using official IJF terminology (e.g. 'Hansoku-make', 'Osaekomi', 'Shido', 'Direct Hansoku-make', 'Contest Area', 'Safety Area').\n\n" if language == "en" else "Write the entire JSON response in clear, rigorous SPANISH using official IJF terminology, unless the user query explicitly demands another language.\n\n" if language == "es" else "If the query is in English, write the entire JSON response in fluent, precise ENGLISH using official IJF terminology. If the query is in Spanish, write the response in SPANISH.\n\n")
            + f"Consulta del usuario / User query: {situation_query}\n"
            + "Respuesta JSON:"
        )

        llm_res = self._call_llm(prompt)
        if isinstance(llm_res, tuple):
            llm_answer, llm_meta = llm_res
        else:
            llm_answer, llm_meta = llm_res, {}

        citations_valid = self._validate_llm_citations(llm_answer, evidence, related)

        # Build citation passage data for resolution
        all_passages_data = []
        for e in evidence:
            all_passages_data.append({
                "id_conocimiento": e["passage_id"],
                "source_id": "SOR-2026-08-14-ENG",
                "pdf_page_index": e["page"],
                "source_url": e["source_url"].split("#")[0]
            })
        for r in related:
            all_passages_data.append({
                "id_conocimiento": r["passage_id"],
                "source_id": "SOR-2026-08-14-ENG",
                "pdf_page_index": r["page"],
                "source_url": r["source_url"].split("#")[0]
            })

        if llm_answer and citations_valid:
            succ_prov = llm_meta.get("successful_provider", "LLM")
            succ_model = llm_meta.get("successful_model", "")
            if succ_model:
                mode_label = f"Síntesis Analítica IA ({succ_prov} / {succ_model}; citas verificadas)"
                header = f"⚖️ **Síntesis Analítica IA ({succ_prov} — {succ_model})**"
            else:
                mode_label = "Síntesis Analítica IA (Conectado; citas verificadas)"
                header = "⚖️ **Síntesis Analítica IA (Conectado; citas verificadas)**"
            structured = parse_structured_response(llm_answer, evidence)
        else:
            if llm_answer and not citations_valid:
                mode_label = "Resumen de Evidencias Normativas (Fallback: citas IA no verificables)"
                header = f"📋 **Resumen de Evidencias Normativas — Fallback: Citas IA no verificables ({self.config['version_label']})**"
            else:
                mode_label = "Resumen de Evidencias Normativas (Modo Local Desconectado)"
                header = f"📋 **Resumen de Evidencias Normativas — Modo Local Desconectado ({self.config['version_label']})**"
            structured = build_deterministic_structured_answer(
                query=situation_query,
                evidence=evidence,
                related=related,
                version_label=self.config["version_label"]
            )

        # Rigor Normativo: Validar afirmaciones, códigos de penalización y artículos contra evidencia oficial
        validator = NormativeValidator(evidence_passages=evidence, related_passages=related)
        structured = validator.sanitize_structured_answer(structured)

        # Build rich citation objects map for interactive PDF viewer and highlighting
        rich_citations_map = {}
        for p in evidence + related:
            pid = p.get("passage_id")
            if not pid or pid in rich_citations_map:
                continue

            exact_quote, text_snippet = self.extract_exact_quote(p, query=situation_query)

            rich_citations_map[pid] = {
                "passage_id": pid,
                "article_id": f"Art. {p.get('article_id')}" if p.get("article_id") else p.get("title", ""),
                "page_number": p.get("page") or p.get("pdf_page_index", 1),
                "source_url": p.get("source_url", ""),
                "exact_quote": exact_quote,
                "text_snippet": text_snippet,
                "title": p.get("title", "")
            }

        # Enrich structured.citations while preserving string IDs compatibility if already populated
        enriched_citations = []
        seen_pids = set()
        # First add citations explicitly cited in structured.citations
        raw_cits = structured.citations if isinstance(structured.citations, list) else []
        for c in raw_cits:
            cid = c if isinstance(c, str) else c.get("passage_id")
            if cid and cid in rich_citations_map and cid not in seen_pids:
                enriched_citations.append(rich_citations_map[cid])
                seen_pids.add(cid)
            elif isinstance(c, dict):
                enriched_citations.append(c)

        # Ensure all retrieved seed evidence items are represented
        for e in evidence:
            eid = e.get("passage_id")
            if eid and eid in rich_citations_map and eid not in seen_pids:
                enriched_citations.append(rich_citations_map[eid])
                seen_pids.add(eid)

        structured.citations = enriched_citations

        # Apply citation formatting to all structured text components
        structured.summary = format_citations(structured.summary, all_passages_data)
        structured.normative_basis = format_citations(structured.normative_basis, all_passages_data)
        structured.conditions_and_exceptions = format_citations(structured.conditions_and_exceptions, all_passages_data)
        structured.extended_analysis = format_citations(structured.extended_analysis, all_passages_data)
        structured.limitations = format_citations(structured.limitations, all_passages_data)

        # Build backward-compatible flat analysis text with Level 1 first, Level 2 details attached
        flat_analysis = structured.to_legacy_text(header=header)

        return {
            "status": "SUCCESS",
            "query": situation_query,
            "mode": mode_label,
            "analysis": flat_analysis,
            "structured_answer": structured.to_dict(),
            "evidence": evidence,
            "related_passages": related,
            "engine": "ADA-RRE-v2",
            "rre_operating_mode": retrieval_res.get("operating_mode", "UNKNOWN"),
            "degradation_reason": retrieval_res.get("degradation_reason"),
            "source_sha256_verified": retrieval_res.get("source_sha256_verified", False),
            "llm_meta": llm_meta
        }

    def _validate_llm_citations(self, answer: str | None, evidence: list, related: list) -> bool:
        """Accept generated analysis only when it cites retrieved official passage IDs."""
        if not isinstance(answer, str) or not answer.strip():
            return False

        allowed_ids = {
            item.get("passage_id")
            for item in [*evidence, *related]
            if isinstance(item, dict) and item.get("passage_id")
        }
        cited_ids = re.findall(r"\[((?:SOR-[A-Za-z0-9-]+)|KUN-\d{4})\]", answer)
        return bool(cited_ids) and all(citation in allowed_ids for citation in cited_ids)

    def _build_deterministic_arbitration_brief(self, query: str, evidence: list, related: list) -> str:
        """Constructs legacy string brief for compatibility if called directly."""
        structured = build_deterministic_structured_answer(
            query=query,
            evidence=evidence,
            related=related,
            version_label=self.config["version_label"]
        )
        header = f"📋 **Resumen de Evidencias Normativas — Modo Local Desconectado ({self.config['version_label']})**"
        return structured.to_legacy_text(header=header)

    @staticmethod
    def extract_exact_quote(passage: dict, query: Optional[str] = None) -> tuple[str, str]:
        """Extrae una frase representativa (exact_quote) y un fragmento de texto (text_snippet)

        adaptado al subartículo específico y a las reglas relevantes dentro de pasajes densos o multisección.
        """
        text_orig = passage.get("text_original", "").strip()
        lines = [l.strip() for l in text_orig.splitlines() if l.strip()]
        content_lines = [l for l in lines if not l.startswith("Sport and Organisation") and not l.startswith("page -")]
        if not content_lines:
            content_lines = lines

        # Localizar el bloque específico del artículo dentro de la página física si hay múltiples apartados
        art_id = str(passage.get("article_id") or "").strip()
        start_idx = 0
        if art_id and art_id != "GENERAL":
            clean_art = re.sub(r"[^a-zA-Z0-9]", "", art_id).lower()
            for i, line in enumerate(content_lines):
                clean_line = re.sub(r"[^a-zA-Z0-9]", "", line).lower()
                if clean_art in clean_line:
                    start_idx = i
                    break

        target_lines = content_lines[start_idx:]
        
        # Si la primera línea es el título/código del artículo, omitirla para trabajar con el contenido
        if len(target_lines) > 1 and (
            re.match(r"^[A-Z0-9]+(?:\.[0-9]+)*", target_lines[0]) or
            target_lines[0].lower().startswith("article") or
            target_lines[0].lower().startswith("section")
        ):
            substantive_lines = target_lines[1:]
        else:
            substantive_lines = target_lines

        # Si se proporciona query, seleccionar la línea de mayor relevancia temática
        chosen_line_idx = 0
        if query and substantive_lines:
            clean_q = query.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
            q_words = set(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", clean_q))
            # Añadir términos canónicos clave según intención
            KEY_CONCEPTS = {
                "wasting": 3, "time-wasting": 3, "starting": 3, "ground": 3, "stand": 3,
                "delay": 3, "return": 2, "position": 2, "warning": 2, "shido": 2,
                "taping": 3, "bandage": 3, "finger": 3, "sokuteiki": 3, "size": 2,
                "beyond": 4, "limit": 4, "safety": 4, "outside": 3, "sore-made": 4, "toketa": 3
            }
            # Mapeo bilingüe rápido
            if "perdiendo" in q_words or "perder" in q_words or "tiempo" in q_words:
                q_words.update(["wasting", "time-wasting", "time", "delay"])
            if "regresa" in q_words or "regresar" in q_words or "posicion" in q_words:
                q_words.update(["return", "position", "starting"])
            if "suelo" in q_words or "quedandose" in q_words:
                q_words.update(["ground", "stand"])
            if "seguridad" in q_words or "limite" in q_words or "sobrepasa" in q_words or "alcanza" in q_words:
                q_words.update(["safety", "limit", "beyond", "outside"])

            best_line_score = -1
            for idx, line in enumerate(substantive_lines):
                line_words = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", line.lower())
                score = 0
                for w in line_words:
                    if w in q_words:
                        score += KEY_CONCEPTS.get(w, 1)
                if score > best_line_score:
                    best_line_score = score
                    chosen_line_idx = idx

        target_slice = substantive_lines[chosen_line_idx:] if chosen_line_idx > 0 else substantive_lines
        content_text = " ".join(target_slice)
        content_text = re.sub(r"^[•·\-\*\s]+", "", content_text).strip()
        content_text = re.sub(r"\s+", " ", content_text).strip()

        # Extraer la primera oración sustantiva preservando frases exclamativas reglamentarias
        sentence_match = re.search(r"^(.*?(?:\.|\![\"\”\»\']|\! Sore-Made[\"\”\»\']?))(?:\s+[A-Z0-9]|$)", content_text)
        if sentence_match:
            first_sentence = sentence_match.group(1).strip()
        else:
            sentences = re.split(r"(?<=[.!?])\s+", content_text)
            first_sentence = sentences[0] if sentences and sentences[0].strip() else content_text
        words = first_sentence.split()

        exact_quote = " ".join(words[:9]) if words else (passage.get("title") or "")
        text_snippet = first_sentence[:180] + ("..." if len(first_sentence) > 180 else "")
        return exact_quote, text_snippet

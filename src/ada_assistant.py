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
import urllib.request
import urllib.error
import re
from rre_engine import ReasoningRetrievalEngine
from citation_resolver import resolve_url, format_citations
from corpus_config import get_active_corpus_config

class ArbitrationDecisionAssistant:
    """
    ADA: Dedicated judicial reasoning and arbitration assistant for the IJF SOR.
    """

    def __init__(self, base_dir="data/processed/rebuild_2026_08", allow_degraded: bool | None = None):
        self.base_dir = base_dir
        self.rre = ReasoningRetrievalEngine(base_dir, allow_degraded=allow_degraded)
        self.config = get_active_corpus_config()
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    def _call_llm(self, prompt: str) -> str:
        """Invokes Gemini flash model if API key is present and quota allows."""
        if not self.api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.95
            }
        }
        headers = {"Content-Type": "application/json"}

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=12) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                candidates = res_data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        return parts[0].get('text', '')
        except Exception as e:
            # Fallback to local deterministic synthesis on HTTP 429, timeout or network issue
            pass
        return None

    def analyze_situation(self, situation_query: str, top_k: int = 4):
        """
        Executes complete ADA arbitration reasoning cycle:
        1. Retrieval of evidence via RRE.
        2. Checking for abstention.
        3. Multi-rule analysis and context compilation.
        4. LLM synthesis or local legal arbitration brief.
        5. Citing verified articles and PDF pages.
        """
        retrieval_res = self.rre.retrieve(situation_query, top_k=top_k, expand_graph=True)

        if retrieval_res["status"] == "ABSTAIN":
            return {
                "status": "ABSTAIN",
                "query": situation_query,
                "analysis": (
                    f"⚠️ **Abstención Normativa Oficial ({self.config['version_label']})**\n\n"
                    "La situación o consulta planteada no encuentra respaldo ni evidencia suficiente en los artículos "
                    "certificados del reglamento deportivo y de organización de la IJF (SOR 2026-08).\n\n"
                    "*Por razones de rigor técnico y arbitral, el asistente no formula suposiciones no documentadas.*"
                ),
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
            "Tu tarea es analizar la situación arbitral planteada por el usuario aplicando rigurosamente los artículos oficiales.\n\n"
            "CONTEXTO NORMATIVO CERTIFICADO:\n"
            f"{full_context}\n\n"
            "INSTRUCCIONES DE RAZONAMIENTO ARBITRAL:\n"
            "1. Identifica las reglas aplicables al caso y las condiciones o excepciones específicas.\n"
            "2. Si la situación involucra categorías especiales (ej. cadetes, juniors), precisa las restricciones pertinentes.\n"
            "3. Cita obligatoriamente cada fundamento con su identificador entre corchetes, ej. [SOR-2026-08-Pxxx-Sxxx].\n"
            "4. Formula una conclusión operativa clara (sanción, puntuación, procedimiento médico o decisión reglamentaria).\n"
            "5. No inventes reglas que no figuren en el contexto.\n\n"
            f"Situación planteada: {situation_query}\n"
            "Análisis Arbitral y Decisión Fundamentada:"
        )

        llm_answer = self._call_llm(prompt)
        citations_valid = self._validate_llm_citations(llm_answer, evidence, related)

        if llm_answer and citations_valid:
            final_text = llm_answer
            mode_label = "Síntesis Analítica IA (Conectado; citas verificadas)"
        else:
            final_text = self._build_deterministic_arbitration_brief(situation_query, evidence, related)
            if llm_answer:
                mode_label = "Resumen de Evidencias Normativas (Fallback: citas IA no verificables)"
            else:
                mode_label = "Resumen de Evidencias Normativas (Modo Local Desconectado)"

        # Apply citation resolution to clickable markdown links
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

        formatted_analysis = format_citations(final_text, all_passages_data)

        return {
            "status": "SUCCESS",
            "query": situation_query,
            "mode": mode_label,
            "analysis": formatted_analysis,
            "evidence": evidence,
            "related_passages": related,
            "engine": "ADA-RRE-v2",
            "rre_operating_mode": retrieval_res.get("operating_mode", "UNKNOWN"),
            "degradation_reason": retrieval_res.get("degradation_reason"),
            "source_sha256_verified": retrieval_res.get("source_sha256_verified", False)
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
        """Constructs an objective normative evidence summary when external generative model is unavailable."""
        brief = (
            f"📋 **Resumen de Evidencias Normativas — Modo Local Desconectado ({self.config['version_label']})**\n\n"
            f"**Cuestión Consultada:** *\"{query}\"*\n\n"
            "> ℹ️ *Aviso de Operación Local:* Al operar sin conexión al modelo generativo, se presentan directamente las disposiciones "
            "normativas oficiales recuperadas por el motor RRE con sus enlaces anclados al PDF oficial. No se genera un dictamen interpretativo "
            "autónomo para evitar inferencias no explícitamente fundadas.\n\n"
            "### 1. Disposiciones Normativas Aplicables (Evidencia Primaria)\n"
        )

        for ev in evidence:
            brief += f"- **[{ev['passage_id']}] {ev['title']}** (Artículo {ev['article_id']}, Página {ev['page']})\n"
            brief += f"  > *Extracto Oficial:* {ev['text_original'][:320].strip()}...\n\n"

        if related:
            brief += "### 2. Normas Conexas y Referencias Cruzadas\n"
            for rel in related:
                brief += f"- **[{rel['passage_id']}] {rel['title']}** (Artículo {rel['article_id']}, Página {rel['page']}) — *Relación:* `{rel['relation']}`\n"
            brief += "\n"

        brief += (
            "### 3. Aplicación y Consulta Documental\n"
            "Las decisiones operativas y arbitrales en competición deben atenerse estrictamente a los artículos oficiales reproducidos arriba. "
            "Para consultar diagramas técnicos, apéndices completos o precisiones contextuales, utilice los enlaces directos anclados a cada página del PDF oficial.\n\n"
            "💡 *Todas las citas normativas cuentan con trazabilidad verificable al documento oficial IJF SOR 2026-08.*"
        )
        return brief

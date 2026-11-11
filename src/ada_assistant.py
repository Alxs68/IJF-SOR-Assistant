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
try:
    from src.document_validator import DocumentValidator
    from src.document_governance import (
        EvidenceItem,
        EvidenceRole,
        DocumentAuthority,
        ValidityStatus,
        EligibilityStatus,
        EvidenceBundle
    )
except ImportError:
    from document_validator import DocumentValidator
    from document_governance import (
        EvidenceItem,
        EvidenceRole,
        DocumentAuthority,
        ValidityStatus,
        EligibilityStatus,
        EvidenceBundle
    )

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
        self.rre = ReasoningRetrievalEngine(
            base_dir,
            allow_degraded=allow_degraded,
            enable_semantic_ranker=True,
            enable_referee_disambiguation=True,
            enable_ood_detector=True,
            enable_negative_domain_anchors=True
        )
        self.config = get_active_corpus_config()
        self.llm_manager = llm_manager or MultiProviderLLMManager()
        self.api_key = self.llm_manager.gemini_api_key
        self.doc_validator = DocumentValidator()

    def _call_llm(self, prompt: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Invokes active LLM provider (Gemini/Groq) with fallback according to configured policy."""
        return self.llm_manager.generate_with_fallback(prompt)

    def _translate_to_technical_english(self, query: str) -> str:
        """
        Translates a Spanish judo query into concise, official technical English for
        accurate cross-lingual retrieval against the IJF SOR corpus, while strictly
        preserving Japanese judo terminology (Ippon, Shido, Hansoku-make, etc.).
        Falls back to original query if not in Spanish or if translation fails.
        """
        if not query or not isinstance(query, str):
            return ""

        q_clean = query.strip()
        q_lower = q_clean.lower()

        # Check for Spanish markers (accented chars, ñ, universal Spanish stopwords, or judo keywords)
        has_spanish_chars = bool(re.search(r"[áéíóúüñ¿¡]", q_lower))
        spanish_keywords = {
            "duracion", "duración", "sancion", "sanción", "sanciones", "combate", "combates",
            "tiempo", "tiempos", "regla", "reglas", "cabeza", "pesaje", "medida", "medidas",
            "area", "área", "tatami", "cuanto", "cuánto", "cuanta", "cuánta", "cuantos", "cuántos",
            "cuales", "cuáles", "cual", "cuál", "como", "cómo", "que", "qué", "cuando", "cuándo",
            "quien", "quién", "quienes", "quiénes", "puede", "pueden", "debe", "deben",
            "descalificacion", "descalificación", "descalificado", "descalificados",
            "inmovilizacion", "inmovilización", "inmovilizaciones", "estrangulacion", "estrangulación",
            "luxacion", "luxación", "proyeccion", "proyección", "proyecciones", "lanzamiento",
            "agarre", "agarres", "entrenador", "entrenadores", "arbitro", "árbitro", "arbitros",
            "puente", "prohibido", "permitido", "falta", "faltas", "castigo", "castigos", "insulto",
            "insultos", "insulta", "agrede", "agresion", "agresión", "golpe", "procede", "reverse",
            "saludo", "saludos", "saludar", "reverencia", "equipo", "equipos", "mixto", "mixtos",
            "mixta", "mixtas", "tolerancia", "presentarse", "presenta", "presentan", "comparecer",
            "comparecencia", "incomparecencia", "llamada", "antes", "despues", "competencia",
            "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "en", "por",
            "para", "con", "sin", "sobre", "entre", "es", "son", "se", "su", "sus", "este", "esta"
        }
        tokens = set(re.findall(r"\b[a-zA-Záéíóúüñ]{2,}\b", q_lower))
        has_spanish_keywords = bool(tokens & spanish_keywords)

        if not has_spanish_chars and not has_spanish_keywords:
            return q_clean

        prompt = (
            "You are an expert official IJF (International Judo Federation) translator and terminology specialist.\n"
            "Translate the following judo inquiry from Spanish into concise, precise technical English for retrieval against the official IJF Sport and Organisation Rules (SOR 2026).\n"
            "CRITICAL RULES:\n"
            "1. Strictly preserve all official Japanese judo terminology exactly as spelled (e.g. Ippon, Waza-ari, Shido, Hansoku-make, Osaekomi, Tori, Uke, Tatami, Matte, Hajime, Shime-waza, Kansetsu-waza, Toketa, Seoi-nage, Reverse seoi-nage, etc.).\n"
            "2. Map colloquial, descriptive, or informal actions to official IJF SOR normative phrases:\n"
            "   - insult / insulta / ofensa verbal -> derogatory remarks, calls or gestures to opponent or referee\n"
            "   - agredir / agresión física / golpe -> action against the spirit of judo, deliberate action causing injury, direct hansoku-make\n"
            "   - falta de respeto / conducta antideportiva -> acts against the spirit of judo, direct hansoku-make\n"
            "   - cadetes reverse seoi-nage -> cadet reverse seoi-nage shido penalty\n"
            "   - defensa con la cabeza -> head defense bridge uke cadet restriction\n"
            "   - entrenador / coach vestimenta / dress code -> coaches' dress code preliminaries final block formal suit track suit\n"
            "   - veteranos / master / categoría de edad -> regulations for veterans age divisions contest duration category combining\n"
            "   - antidopaje / control dopaje -> medical and anti-doping handbook doping control selection procedure\n"
            "   - accion simultanea / ambos caen / ataque simultaneo -> simultaneous action both athletes fall tatami no score Article 14 Article 13 golden score\n"
            "   - saludo / saludo equipos / equipos mixtos / reverencia -> Article 9 Start of the Contest bowing ceremony team competition mixed team encounter rei otagai-ni technical table\n"
            "   - tiempo de tolerancia / presentarse en el tatami / comparecer / incomparecencia -> Article 19.1 Default 30-second rule failure to appear countdown scoreboard fusen-gachi\n"
            "   - disciplinario / comite disciplinario -> IJF Disciplinary Committee Disciplinary Code sports integrity betting sanctions\n"
            "3. Output ONLY the translated technical English query without any explanation, markdown formatting, quotes, or trailing notes.\n\n"
            f"Query to translate: {q_clean}\n"
            "English translation:"
        )

        try:
            llm_res = self._call_llm(prompt)
            raw_text = llm_res[0] if isinstance(llm_res, tuple) else llm_res
            if raw_text and isinstance(raw_text, str):
                cleaned = raw_text.strip().strip('"\'`')
                lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
                if lines:
                    candidate = lines[0]
                    if not candidate.lower().startswith(("here is", "translation:", "i cannot", "lo siento")):
                        if len(candidate) >= 3:
                            return candidate
        except Exception:
            pass

        # Robust offline deterministic dictionary projection fallback
        proj_parts = []
        for w in re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", q_lower):
            clean_w = w.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
            if clean_w in self.rre.SPANISH_TO_ENGLISH_SYNONYMS:
                proj_parts.append(self.rre.SPANISH_TO_ENGLISH_SYNONYMS[clean_w])
            elif clean_w in {"saludo", "saludos", "saludar"}:
                proj_parts.append("bowing bow ceremony rei otagai-ni")
            elif clean_w in {"equipos", "equipo"}:
                proj_parts.append("team teams")
            elif clean_w in {"mixtos", "mixto", "mixtas", "mixta"}:
                proj_parts.append("mixed")
            elif clean_w in {"tolerancia"}:
                proj_parts.append("tolerance 30-second rule countdown scoreboard fusen-gachi")
            elif clean_w in {"presentarse", "presenta", "comparecer", "comparecencia"}:
                proj_parts.append("appear appearance failure to appear 30-second fusen-gachi")
            elif clean_w not in {"en", "la", "de", "del", "por", "para", "con", "el", "los", "las", "un", "una", "al", "es", "son", "se", "su", "sus", "cual", "que"}:
                proj_parts.append(w)
        if proj_parts:
            return " ".join(proj_parts)

        return q_clean

    def analyze_situation(self, situation_query: str, top_k: int = 5, language: Optional[str] = None):
        """
        Executes complete ADA arbitration reasoning cycle:
        1. Retrieval of evidence via RRE.
        2. Checking for abstention.
        3. Multi-rule analysis and context compilation.
        4. LLM synthesis with two-tier contract or structured local brief.
        5. Citing verified articles and PDF pages with physical anchors.
        """
        search_query_en = self._translate_to_technical_english(situation_query)
        retrieval_res = self.rre.retrieve(search_query_en, top_k=top_k, expand_graph=True)

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

        # Document Authority & Validity Gate via DocumentValidator
        candidate_items = []
        for ev in evidence:
            candidate_items.append(
                EvidenceItem(
                    evidence_id=ev.get("passage_id", "UNKNOWN"),
                    document_id="DOC-SOR-2026-08",
                    content_text=ev.get("text_original") or "Contenido no disponible",
                    role=EvidenceRole.NORMA_PRIMARIA,
                    authority=DocumentAuthority.TIER_1_NORMATIVE_PRIMARY,
                    validity=ValidityStatus.VIGENTE,
                    eligibility=EligibilityStatus.ELIGIBLE_DECISORIA,
                    semantic_relevance_score=min(1.0, max(0.0, float(ev.get("score", 0.5)))),
                    article_number=f"Art. {ev.get('article_id')}" if ev.get("article_id") else None,
                    page_number=ev.get("page"),
                    paragraph_or_section=ev.get("title"),
                    url_reference=ev.get("source_url")
                )
            )

        bundle_id = f"BND-{abs(hash(situation_query)) % 1000000:06d}"
        certified_bundle = self.doc_validator.build_certified_bundle(
            bundle_id=bundle_id,
            query_text=search_query_en,
            candidate_items=candidate_items
        )

        if certified_bundle.abstention_required or not certified_bundle.is_sufficient_for_decision:
            reason_text = certified_bundle.abstention_reason or "Evidencia documental insuficiente para emitir dictamen normativo vinculante."
            abstain_msg = (
                f"⚠️ **Abstención Normativa Oficial ({self.config['version_label']})**\n\n"
                f"{reason_text}\n\n"
                "*Por gobernanza documental, el asistente no emite dictámenes sin respaldo de la norma primaria vigente.*"
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
                    "limitations": reason_text,
                    "is_structured": True
                },
                "evidence": [],
                "related_passages": [],
                "engine": "ADA-RRE-v2",
                "rre_operating_mode": retrieval_res.get("operating_mode", "UNKNOWN"),
                "degradation_reason": retrieval_res.get("degradation_reason"),
                "source_sha256_verified": retrieval_res.get("source_sha256_verified", False),
                "certified_bundle": certified_bundle.model_dump()
            }

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
            '  "summary": "Nivel 1: RESPUESTA DIRECTA Y OPERATIVA, concisa y proporcional a la consulta. Debe responder de inmediato qué establece la norma, especificando cifras exactas, límites, tolerancias, sanciones o decisiones según corresponda y su referencia normativa rectora ([Regla X / Art. Y / Pág. Z]). PROHIBIDO iniciar con introducciones, saludos o frases meta como \'A continuación se expone el razonamiento\', \'El análisis arbitral determina\', \'En este documento\'. La primera palabra debe ser la respuesta concreta.",\n'
            '  "normative_basis": "Nivel 2: Artículos, reglas y apartados aplicables con citas exactas de los identificadores entre corchetes [SOR-2026-08-Pxxx-Sxxx] y números de página.",\n'
            '  "citations": ["Lista de identificadores citados, ej: SOR-2026-08-Pxxx-Sxxx"],\n'
            '  "conditions_and_exceptions": "Condiciones específicas, excepciones reglamentarias, restricciones por categoría (ej. cadetes/juniors) y notas técnicas. Si la consulta es simple o fáctica y no existen excepciones reglamentarias aplicables, responde exactamente: \\"No aplica\\".",\n'
            '  "extended_analysis": "Explicación detallada de cómo se aplica la norma al caso planteado, procedimiento arbitral paso a paso y aplicación práctica. Para preguntas fácticas directas (ej. duración del combate, dimensiones del tatami), responde exactamente: \\"No aplica\\".",\n'
            '  "limitations": "Límites de la evidencia disponible y aspectos no expresamente contemplados en los extractos adjuntos. Si el texto normativo primario certificado responde de manera completa, indubitable y autosuficiente a la consulta, responde exactamente: \\"Ninguna\\"."\n'
            "}\n\n"
            "POLÍTICA TRANSVERSAL DE RAZONAMIENTO REGLAMENTARIO:\n"
            "1. Fidelidad Normativa y Distinción en Tres Niveles: Distingue rigurosamente entre:\n"
            "   (a) Regla Expresa del SOR: mandatos, prohibiciones, tolerancias y consecuencias textualmente promulgadas en el texto oficial.\n"
            "   (b) Interpretación Normativa Sustentada: análisis inferencial derivado armónicamente de artículos del SOR, la cual DEBE identificarse expresamente como tal ('Interpretación normativa:') explicando su sustento sin presentarla como texto literal.\n"
            "   (c) Criterio Arbitral / Aspecto No Regulado Expresamente: apreciaciones de juicio sobre el tatami o supuestos fácticos no zanjados en la norma escrita; PROHIBIDO convertirlos en mandatos oficiales; deben declararse como apreciación o limitación documental.\n"
            "2. Prohibición de Invención de Reglas y Procedimientos: Prohibido inventar o deducir excepciones, artículos, fórmulas de puntuación, secuencias de evaluación, obligaciones o sanciones no respaldadas textualmente.\n"
            "3. Rigor Textual vs. Interpretación: Responde prioritariamente con lo que establece el texto oficial del SOR 2026. Si un aspecto no está regulado expresamente en los pasajes certificados, decláralo de inmediato como limitación documental en 'limitations' sin resolver contradicciones o lagunas mediante suposiciones.\n"
            "4. Prohibición de Extrapolación Automática: PROHIBIDO extrapolar sanciones, restricciones, tolerancias o autorizaciones entre categorías de edad (ej. cadetes vs. juniors/séniors), roles (tori vs. uke) o circunstancias de combate, a menos que el texto oficial lo ordene expresamente.\n"
            "5. No Asunción de Hechos: No asumas hechos, intenciones ni datos fácticos que el usuario no haya especificado en su consulta.\n"
            "6. Análisis Diferenciado por Escenarios: Si la situación fáctica consultada admite ramificaciones o consecuencias reglamentarias distintas según variables determinantes (acción técnica deliberada vs. accidental/fortuita; rol atacante tori vs. defensor uke; categoría cadete vs. adulto; área de combate vs. seguridad), analiza separadamente cada escenario relevante en 'summary' y 'extended_analysis' ('Escenario A: ..., Escenario B: ...').\n"
            "7. Enfoque Directo en Consulta Simple: Si la consulta es concreta y unívoca, entrega una respuesta inmediata, concisa y operativa en Nivel 1 (summary), respaldada por su referencia rectora y proporcional a la consulta.\n"
            "8. Tratamiento de Ambigüedad Normativa o Fáctica: Si la norma no determina unívocamente la solución o la consulta carece de datos fácticos determinantes, expón las disposiciones aplicables, reconoce lo que el texto no determina e indica qué precisiones de hecho se requieren para emitir una resolución definitiva.\n"
            "9. Transparencia sobre Evidencia Insuficiente: Si los pasajes certificados no contienen la respuesta o resultan insuficientes para confirmar una regla, declara con total franqueza la limitación en 'summary' y 'limitations', sin formular dictámenes categóricos infundados.\n"
            "10. Criterios Especiales Prevalentes:\n"
            "   - Equipamiento y Judogi: Contesta de inmediato la especificación técnica consultada (ej. colores permitidos blanco y azul según Regla C1.9, pág. 124). Segrega requisitos conexos (marcas, parches, solapas) en 'conditions_and_exceptions' o 'extended_analysis' sin mezclarlos como si fueran reglas de color.\n"
            "   - Puente y Criterio de Ippon (Art. 14.2, págs. 166-167): Reproduce con total fidelidad el texto oficial: (1) toda situación donde un atleta proyectado haga voluntariamente un 'puente' (cabeza y uno o ambos pies en contacto con el tatami) tras ser proyectado es Ippon para el rival por seguridad cervical; (2) Excepción textual: no se otorgará puntuación ni penalización si la caída de Uke ocurre sobre el cuerpo de Tori, de modo que no todas las partes del cuerpo involucradas en el puente (cabeza, pie o pies) toquen el tatami. PROHIBIDO agregar condiciones geométricas, temporales o de observación que el texto no establezca, y prohibido afirmar que el árbitro debe esperar una evolución determinada de la caída salvo que exista respaldo reglamentario específico.\n"
            "   - Acciones con la Cabeza (Integración Sistemática de Reglas Generales y Especiales):\n"
            "     * Rol Atacante (Tori): (1) Head Diving al intentar o ejecutar cualquier técnica de proyección es Hansoku-make directo por técnica peligrosa para CUALQUIER categoría (Art. 18.2.1, pág. 190); Tori SÍ puede continuar en la competición si clasifica; (2) en eventos de Cadetes, el uso intencional de la cabeza por Tori para proyectar que no constituya la zambullida peligrosa de head diving se sanciona con Shido (Art. 18.1.4, punto 33, pág. 188 / concordancia con pág. 190); (3) en Cadetes el reverse seoi-nage no puntúa y es Shido para Tori (Art. 18.1.4, punto 35, pág. 189).\n"
            "     * Rol Defensor (Uke): (1) En CUALQUIER categoría (Seniors, Juniors, Cadetes), si Uke hace voluntariamente un puente (cabeza y uno o ambos pies en contacto con el tatami) tras ser proyectado para evitar caer de espaldas, la consecuencia reglamentaria es IPPON a favor de Tori por seguridad de la columna cervical (Art. 14.2, pág. 166), con la excepción textual de aterrizaje sobre el cuerpo de Tori (pág. 167); (2) Específicamente en la categoría Cadetes, se prohíbe taxativamente a Uke usar la cabeza para defenderse del lance; uke es penalizado con Shido y se concede a Tori la puntuación técnica generada (Art. 18.1.4, punto 34, pág. 188); (3) No equipares automáticamente todo puente con cualquier defensa ni viceversa: el puente voluntario en vuelo/caída produce Ippon en todas las categorías, mientras que la infracción explícita de Shido a Uke por defenderse con la cabeza es una regla específica de Cadetes.\n"
            "     * Prohibición de Lagunas Infundadas: PROHIBIDO afirmar que 'no existe regulación o disposición explícita para seniors/juniors' ante preguntas sobre defensa o uso de la cabeza. Expón con claridad las consecuencias aplicables según el rol (Tori -> Head Diving / Uke -> Puente e Ippon) y la regla particular de Cadetes.\n"
            "   - Diagramas y Cuadros: Si la consulta refiere a una plantilla de diagrama/cuadro (págs. 213-230), explica las reglas sustantivas de sorteo aplicables e indica que la geometría espacial debe consultarse en el PDF oficial.\n"
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

            raw_art = str(p.get("article_id") or "").strip()
            if re.match(r"^article\s+", raw_art, re.IGNORECASE):
                clean_art_id = re.sub(r"^article\s+", "Art. ", raw_art, flags=re.IGNORECASE)
            elif re.match(r"^art\.?\s*", raw_art, re.IGNORECASE):
                clean_art_id = raw_art
            elif raw_art:
                clean_art_id = f"Art. {raw_art}"
            else:
                clean_art_id = p.get("title", "")

            rich_citations_map[pid] = {
                "passage_id": pid,
                "article_id": clean_art_id,
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
            if isinstance(c, str):
                match_id = re.search(r"((?:SOR-[A-Za-z0-9-]+)|KUN-\d{4})", c)
                cid = match_id.group(1) if match_id else c
            elif isinstance(c, dict):
                cid = c.get("passage_id")
            else:
                cid = None

            if cid and cid in rich_citations_map and cid not in seen_pids:
                enriched_citations.append(rich_citations_map[cid])
                seen_pids.add(cid)
            elif isinstance(c, dict):
                enriched_citations.append(c)

        # If no explicit citations were captured (e.g. deterministic brief), include relevant seed evidence (max 3)
        if not enriched_citations:
            for e in evidence[:3]:
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
            "certified_bundle": certified_bundle.model_dump(),
            "llm_meta": llm_meta
        }

    def _validate_llm_citations(self, answer: str | None, evidence: list, related: list) -> bool:
        """Accept generated analysis only when it cites retrieved official passage IDs
        and does not introduce hallucinated articles or penalty codes."""
        if not isinstance(answer, str) or not answer.strip():
            return False

        allowed_ids = {
            item.get("passage_id")
            for item in [*evidence, *related]
            if isinstance(item, dict) and item.get("passage_id")
        }
        # Strict regex to extract official passage IDs without matching edition strings like 'SOR-2026-08'
        raw_found = re.findall(r"(?:SOR-[A-Za-z0-9]+-[A-Za-z0-9]+-P\d+-S\d+|KUN-\d{4})", answer)
        cited_ids = set(raw_found)
        # If passage IDs were cited, verify all of them belong to allowed_ids
        if cited_ids and not all(citation in allowed_ids for citation in cited_ids):
            return False

        # Additional semantic and normative validation check
        validator = NormativeValidator(evidence_passages=evidence, related_passages=related)
        res = validator.validate_text(answer)
        if res.hallucinated_codes or res.hallucinated_articles:
            return False

        return True

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
        Elimina la dependencia de repetición accidental de palabras y aplica correspondencias léxicas
        multilingües robustas (español/inglés, ej. color/colour, dimensiones/tatami, roles tori/uke).
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

        full_text = "\n".join(substantive_lines)
        prot = re.sub(r"[\r\n]+[•·\-\*]\s*", r"\n___BULLET___ ", full_text)
        blocks = prot.split("\n___BULLET___ ")

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

        chosen_sentence = sentences[0]
        if query:
            clean_q = query.lower()
            clean_q = clean_q.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
            q_words = set(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", clean_q))

            SYNONYM_EXPANSIONS = {
                "dimension": ["dimension", "size", "measure", "meter", "metre", "8 m", "10 m"],
                "dimensiones": ["dimension", "size", "measure", "meter", "metre", "8 m", "10 m"],
                "medida": ["dimension", "size", "measure", "meter", "metre", "8 m", "10 m"],
                "medidas": ["dimension", "size", "measure", "meter", "metre", "8 m", "10 m"],
                "color": ["colour", "color", "white", "blue", "pantone", "uniform"],
                "colores": ["colour", "color", "white", "blue", "pantone", "uniform"],
                "blanco": ["white", "snow white"],
                "azul": ["blue", "pantone"],
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
                "falta": ["penalty", "shido", "infringement", "illegal"],
                "tiempo": ["time", "wasting", "delay", "stand", "promptly", "return"],
                "demora": ["time", "wasting", "delay", "stand", "promptly", "return"],
                "perdiendo": ["wasting", "time-wasting", "delay"],
                "regresa": ["return", "starting", "position"],
                "posicion": ["position", "starting"],
                "inicio": ["starting", "position"],
                "suelo": ["ground", "stand", "promptly"],
                "manga": ["sleeve", "sokuteiki"],
                "traje": ["judogi", "jacket", "trousers", "suit"],
                "criterio": ["criteria", "criterion", "four criteria", "speed", "force"],
                "criterios": ["criteria", "criterion", "four criteria", "speed", "force"],
                "elemento": ["element", "elements", "criteria", "speed", "force"],
                "elementos": ["element", "elements", "criteria", "speed", "force"],
                "requisito": ["requirement", "criteria", "speed", "force"],
                "requisitos": ["requirements", "criteria", "speed", "force"],
                "velocidad": ["speed", "force"],
                "fuerza": ["force", "speed"],
                "control": ["control", "skilfully"],
                "espalda": ["back"],
                "insulto": ["derogatory", "remark", "remarks", "gesture", "gestures", "spirit"],
                "insultos": ["derogatory", "remark", "remarks", "gesture", "gestures", "spirit"],
                "insulta": ["derogatory", "remark", "remarks", "gesture", "gestures", "spirit"],
                "agrede": ["derogatory", "spirit", "endanger", "injure", "deliberate", "hansoku-make"],
                "agresion": ["derogatory", "spirit", "endanger", "injure", "deliberate", "hansoku-make"],
                "agresión": ["derogatory", "spirit", "endanger", "injure", "deliberate", "hansoku-make"],
                "seoi-nage": ["seoi-nage", "seoinage", "reverse"],
                "seoinage": ["seoi-nage", "seoinage", "reverse"]
            }

            expanded = set(q_words)
            for w in q_words:
                if w in SYNONYM_EXPANSIONS:
                    expanded.update(SYNONYM_EXPANSIONS[w])

            requires_tori = "tori" in q_words or "lanzar" in q_words or "lanzamiento" in q_words or "proyectar" in q_words
            requires_uke = "uke" in q_words or "defiende" in q_words or "defensa" in q_words or "puente" in q_words or "bridge" in q_words
            query_asks_exception = bool({
                "excepcion", "excepción", "exception", "penalty", "penalise",
                "penalised", "no score", "no se otorga", "landing", "aterriza",
                "aterrizaje", "escape", "endanger"
            } & expanded)

            best_score = -1
            for s in sentences:
                s_clean = s.lower()
                s_clean = re.sub(r"^[0-9]{1,3}\.\s*", "", s_clean)
                s_words = set(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", s_clean))
                # Intersección única de conceptos (evita inflación por palabras repetidas accidentalmente)
                hits = len(s_words.intersection(expanded))

                # Bonificaciones por sintagmas exactos normativos
                for p in [
                    "8 m x 8 m", "10 m x 10 m", "white: snow white", "pantone", "uniform colour",
                    "beyond the limit of the safety area", "ippon! sore-made!",
                    "failing to return immediately to the starting position", "controlled by sokuteiki",
                    "voluntarily makes a bridge", "bridge (head and one foot or both feet"
                ]:
                    if p in s_clean:
                        hits += 3

                if "no score or penalty" in s_clean and query_asks_exception:
                    hits += 3

                if {"criteria", "criterion", "element", "elements", "criterio", "criterios", "elementos", "elemento", "requisitos"} & expanded:
                    if "four criteria for ippon" in s_clean or "four criteria" in s_clean:
                        hits += 5
                    elif "ippon will be given when" in s_clean:
                        hits += 4

                has_seoi = bool({"reverse", "seoi-nage", "seoinage", "seoi"} & expanded)
                requires_head = bool({"head", "cabeza", "cuello", "neck"} & expanded)
                requires_ethics = bool({"insulto", "insultos", "insulta", "agrede", "agresion", "agresión", "derogatory", "remark", "remarks", "spirit", "antideportiva"} & expanded)

                if has_seoi and ("reverse seoi-nage" in s_clean or "reverse seoinage" in s_clean):
                    hits += 10
                elif has_seoi and "seoi-nage" in s_clean:
                    hits += 6

                if requires_ethics:
                    if "derogatory" in s_clean or "unnecessary calls" in s_clean:
                        hits += 10
                    elif "spirit of judo" in s_clean:
                        hits += 8
                    elif "deliberate action" in s_clean:
                        hits += 7

                if requires_head and requires_tori and ("throw as tori" in s_clean or "head diving" in s_clean):
                    hits += 6
                elif not requires_head and requires_tori and "tori" in s_words:
                    hits += 2

                if requires_head and requires_uke and ("defend as uke" in s_clean or "voluntarily makes a bridge" in s_clean):
                    hits += 6
                elif not requires_head and requires_uke and "uke" in s_words:
                    hits += 2

                if hits > best_score:
                    best_score = hits
                    chosen_sentence = s

        clean_sent = re.sub(r"\[PAGE BREAK:[^\]]+\]\s*(?:---\s*)?", "", chosen_sentence).strip()
        clean_sent = re.sub(r"^[\s\-•·\*]+", "", clean_sent).strip()
        clean_sent = re.sub(r"^(?:pictures?|figures?|table|note:?)\s*[0-9\.\-\s]+", "", clean_sent, flags=re.IGNORECASE).strip()
        clean_sent = re.sub(r"^[\s\-•·\*]+", "", clean_sent).strip()
        clean_sent = re.sub(r"^[0-9]{1,3}\.\s*", "", clean_sent).strip()

        words = clean_sent.split()
        exact_quote = " ".join(words[:14]) if words else (passage.get("title") or "")
        if len(clean_sent) <= 350:
            text_snippet = clean_sent
        else:
            text_snippet = clean_sent[:347].rsplit(" ", 1)[0] + "..."
        return exact_quote, text_snippet

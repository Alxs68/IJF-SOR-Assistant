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
from decision_integrity import DecisionIntegrityGate, parse_answer as _parse_answer

# Contrato JSON de la llamada de analisis (claves y tipos). Lo usa la validacion de LLM_JSON_SCHEMA=1.
CONTRACT_STR_KEYS = ("summary", "normative_basis", "conditions_and_exceptions", "extended_analysis",
                     "limitations", "answerability")
CONTRACT_LIST_KEYS = ("citations", "evidence_quotes", "evidence_conflicts")


def contract_problems(text):
    """Lista de incumplimientos de FORMATO del contrato (vacia si es valido). No juzga el contenido."""
    obj = _parse_answer(text)
    if not isinstance(obj, dict):
        return ["json_invalido"]
    probs = [f"falta:{k}" for k in CONTRACT_STR_KEYS + CONTRACT_LIST_KEYS if k not in obj]
    probs += [f"tipo:{k}" for k in CONTRACT_STR_KEYS if k in obj and not isinstance(obj[k], str)]
    probs += [f"tipo:{k}" for k in CONTRACT_LIST_KEYS if k in obj and not isinstance(obj[k], list)]
    for i, q in enumerate(obj.get("evidence_quotes") or []):
        if not isinstance(q, dict) or not all(isinstance(q.get(f), str) for f in ("passage_id", "quote")):
            probs.append(f"cita_mal_formada:{i}")
    return probs
# Respuesta unica y validacion integral (ADA_UNIFIED_ANSWER=1). Reglas que la poda de frases accesorias puede
# resolver: solo cifras o terminos sin respaldo literal; cualquier otro fallo del DIG mantiene la abstencion.
PRUNABLE_CHECKS = {"DIG-06_CIFRAS_RESPALDADAS", "DIG-07_TERMINOS_RESPALDADOS"}
VISIBLE_FIELDS = ("summary", "normative_basis", "conditions_and_exceptions", "extended_analysis", "limitations")
PRUNE_NOTE = {
    "es": "Se omitió de esta respuesta información complementaria que no pudo verificarse literalmente en los pasajes del SOR citados.",
    "en": "Supplementary information that could not be verified literally in the cited SOR passages was omitted from this answer.",
}
CLARIFY_TEXT = {
    "es": ("La consulta admite interpretaciones con respuestas normativas distintas. Precise la consulta "
           "(por ejemplo, la competición, la categoría o la situación concreta) para obtener un dictamen fundamentado."),
    "en": ("The query admits interpretations with different normative answers. Please specify it "
           "(for example, the event, the category or the specific situation) to obtain a grounded ruling."),
}
_LINKED_ID = re.compile(r"\[((?:SOR|KUN|CHK)-[^\]\s]+)\]\([^)]*\)")
_STRUCK_ID = re.compile(r"~~\[((?:SOR|KUN|CHK)-[^\]\s]+)\]~~")


def visible_text_for_validation(text, system_notes=()):
    """Texto visible tal como lo vera el usuario, devuelto a la forma que verifica el DIG: los enlaces de cita
    que anade format_citations vuelven a [ID] y se retiran las notas generadas por el sistema (no por el modelo)."""
    t = _STRUCK_ID.sub(r"[\1]", _LINKED_ID.sub(r"[\1]", text or ""))
    for note in system_notes:
        if note:
            t = t.replace(note, " ")
    return re.sub(r"[ \t]+\n", "\n", t).strip()


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

# AUD-04.2: role of a supplementary item is derived from its catalogue authority only.
# Tier 1 is never assigned here: supplementary material can never become primary norm.
_SUPPLEMENTARY_ROLE_BY_AUTHORITY = {
    DocumentAuthority.TIER_2_OFFICIAL_AMENDMENT: EvidenceRole.COMPLEMENTO_INTERPRETATIVO,
    DocumentAuthority.TIER_3_REFEREEING_INTERPRETATION: EvidenceRole.COMPLEMENTO_INTERPRETATIVO,
    DocumentAuthority.TIER_4_EDUCATIONAL_CONTEXT: EvidenceRole.MATERIAL_DIDACTICO,
    DocumentAuthority.TIER_5_AUDIOVISUAL_EVIDENCE: EvidenceRole.EVIDENCIA_AUDIOVISUAL,
}


class ArbitrationDecisionAssistant:
    """
    ADA: Dedicated judicial reasoning and arbitration assistant for the IJF SOR.
    """

    DEACTIVATED_SUPPLEMENTARY_CHUNK_IDS = frozenset({
        "CHK-KUN-NEW-001-003",  # source_kun_id: KUN-0075 (KUN-NEW-001)
        "CHK-KUN-NEW-003-003",  # source_kun_id: KUN-0003 (KUN-NEW-003)
    })
    DEACTIVATED_SUPPLEMENTARY_KUN_IDS = frozenset({
        "KUN-0075",
        "KUN-0003",
    })

    def __init__(
        self,
        base_dir="data/processed/rebuild_2026_08_corrected",
        allow_degraded: bool | None = None,
        llm_manager: Optional[MultiProviderLLMManager] = None,
        enable_shadow_mode_multisource: bool = False
    ):
        self.base_dir = base_dir
        self.rre = ReasoningRetrievalEngine(
            base_dir,
            allow_degraded=allow_degraded,
            enable_semantic_ranker=True,
            enable_referee_disambiguation=True,
            enable_ood_detector=True,
            enable_negative_domain_anchors=True,
            enable_shadow_mode_multisource=enable_shadow_mode_multisource
        )
        self.enable_shadow_mode_multisource = bool(self.rre.enable_shadow_mode_multisource)
        self.config = get_active_corpus_config()
        self.llm_manager = llm_manager or MultiProviderLLMManager()
        self.api_key = self.llm_manager.gemini_api_key
        self.doc_validator = DocumentValidator()

    def _is_supplementary_retrieval_enabled(self) -> bool:
        """Verifica si la recuperación suplementaria está explícitamente activada por RRE_ENABLE_SHADOW_MODE_MULTISOURCE."""
        env_val = os.environ.get("RRE_ENABLE_SHADOW_MODE_MULTISOURCE")
        if env_val is not None:
            return env_val.strip().lower() in {"1", "true", "yes", "on"}
        if hasattr(self, "enable_shadow_mode_multisource"):
            return bool(self.enable_shadow_mode_multisource)
        rre_obj = getattr(self, "rre", None)
        if hasattr(rre_obj, "enable_shadow_mode_multisource"):
            return bool(rre_obj.enable_shadow_mode_multisource)
        return False

    def _call_llm(self, prompt: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Invokes active LLM provider (Gemini/Groq) with fallback according to configured policy.

        Con LLM_JSON_MODE=1 (desactivado por defecto) la llamada de ANALISIS -la que lleva el contrato
        JSON con "evidence_quotes"- pide al proveedor salida JSON garantizada; la traduccion no cambia."""
        if os.environ.get("LLM_JSON_MODE", "").strip() == "1" and '"evidence_quotes"' in (prompt or ""):
            if os.environ.get("LLM_JSON_SCHEMA", "").strip() != "1":
                return self.llm_manager.generate_with_fallback(prompt, json_mode=True)
            # LLM_JSON_SCHEMA=1: esquema estructurado obligatorio (Gemini) + validacion del contrato y
            # UN reintento controlado si la respuesta no es JSON valido o no cumple el contrato. El DIG
            # evalua despues la respuesta igual que siempre; esto no relaja ningun control.
            text, meta = self.llm_manager.generate_with_fallback(prompt, json_mode=True, json_schema=True)
            problems = contract_problems(text) if text else ["sin_texto"]
            attempts = [{"provider": (meta or {}).get("successful_provider"), "problems": problems}]
            all_metas = [meta or {}]
            if text and problems:
                text2, meta2 = self.llm_manager.generate_with_fallback(prompt, json_mode=True, json_schema=True)
                problems2 = contract_problems(text2) if text2 else ["sin_texto"]
                attempts.append({"provider": (meta2 or {}).get("successful_provider"), "problems": problems2})
                all_metas.append(meta2 or {})
                if text2:
                    text, meta = text2, meta2
            meta = dict(meta or {})
            meta["json_contract"] = {"attempts": attempts, "valid": not attempts[-1]["problems"]}
            if len(all_metas) > 1:
                # Consumo real: el reintento tambien se factura; se suman los tokens de TODOS los intentos.
                usage = {}
                for m in all_metas:
                    for k, v in (m.get("token_usage") or {}).items():
                        usage[k] = usage.get(k, 0) + (v or 0)
                meta["attempts_token_usage"] = [m.get("token_usage") for m in all_metas]
                meta["token_usage"] = usage
                meta["model_versions"] = [m.get("model_version") for m in all_metas]
            return text, meta
        return self.llm_manager.generate_with_fallback(prompt)

    @staticmethod
    def _contract_texts(unified: bool) -> dict:
        """Textos del contrato de respuesta. unified=False devuelve los textos ANTERIORES sin cambios (respuesta en
        dos niveles); unified=True (ADA_UNIFIED_ANSWER=1) el contrato de respuesta unica, completa y verificada."""
        if not unified:
            return {
                'title': "CONTRATO OBLIGATORIO DE RESPUESTA EN DOS NIVELES:\n",
                'summary': '  "summary": "Nivel 1: RESPUESTA DIRECTA Y OPERATIVA, concisa y proporcional a la consulta. Debe responder de inmediato qué establece la norma, especificando cifras exactas, límites, tolerancias, sanciones o decisiones según corresponda y su referencia normativa rectora ([Regla X / Art. Y / Pág. Z]). PROHIBIDO iniciar con introducciones, saludos o frases meta como \'A continuación se expone el razonamiento\', \'El análisis arbitral determina\', \'En este documento\'. La primera palabra debe ser la respuesta concreta.",\n',
                'normative_basis': '  "normative_basis": "Nivel 2: Artículos, reglas y apartados aplicables con citas exactas de los identificadores entre corchetes [SOR-2026-08-Pxxx-Sxxx] y números de página.",\n',
                'conditions': '  "conditions_and_exceptions": "Condiciones específicas, excepciones reglamentarias, restricciones por categoría (ej. cadetes/juniors) y notas técnicas. Si la consulta es simple o fáctica y no existen excepciones reglamentarias aplicables, responde exactamente: \\"No aplica\\".",\n',
                'extended': '  "extended_analysis": "Explicación detallada de cómo se aplica la norma al caso planteado, procedimiento arbitral paso a paso y aplicación práctica. Para preguntas fácticas directas (ej. duración del combate, dimensiones del tatami), responde exactamente: \\"No aplica\\".",\n',
                'limitations': '  "limitations": "Límites de la evidencia disponible y aspectos no expresamente contemplados en los extractos adjuntos. Si el texto normativo primario certificado responde de manera completa, indubitable y autosuficiente a la consulta, responde exactamente: \\"Ninguna\\".",\n',
                'answerability': '  "answerability": "RESPALDADA si los pasajes SOR certificados responden la consulta; EVIDENCIA_INSUFICIENTE en caso contrario (entonces no formules dictamen).",\n',
                'rule7': "7. Enfoque Directo en Consulta Simple: Si la consulta es concreta y unívoca, entrega una respuesta inmediata, concisa y operativa en Nivel 1 (summary), respaldada por su referencia rectora y proporcional a la consulta.\n",
                'rule10_spec': "   - Especificaciones Técnicas (equipamiento, judogi, medidas, tiempos): Responde primero la especificación concreta consultada tal como figura en los pasajes certificados, con su cita. Segrega los requisitos conexos en 'conditions_and_exceptions' o 'extended_analysis' sin mezclarlos con la especificación consultada.\n",
                'rule13': "13. Respaldo Literal Verificable: Cada pasaje SOR citado debe tener en 'evidence_quotes' al menos un fragmento copiado LITERALMENTE de ese pasaje. Toda cifra, plazo, medida o sanción de 'summary', 'normative_basis' o 'conditions_and_exceptions' debe aparecer en esos fragmentos. Si el fragmento citado tiene cerca una excepción o condición (except, unless, however, although, only...) o una remisión a otro artículo, cita también esa excepción literalmente. Nunca cites texto de los bloques [COMPLEMENTO-n] como respaldo. Si no puedes respaldar literalmente la respuesta con los pasajes certificados, usa answerability = EVIDENCIA_INSUFICIENTE.\n",
            }
        return {
            'title': "CONTRATO OBLIGATORIO DE RESPUESTA ÚNICA Y COMPLETA (todo lo que escribas se muestra al usuario en una sola respuesta y se verifica contra tus citas literales; no habrá ampliación posterior):\n",
            'summary': '  "summary": "RESPUESTA DIRECTA Y COMPLETA a la consulta, proporcional a su complejidad. La primera frase responde concretamente (cifras exactas, límites, tolerancias, sanciones o decisiones) con su referencia [SOR-2026-08-Pxxx-Sxxx]. Si la consulta tiene varias partes, respóndelas todas. Si la consulta no es un dato simple, termina con una conclusión breve. PROHIBIDO iniciar con introducciones, saludos o frases meta.",\n',
            'normative_basis': '  "normative_basis": "Regla normativa aplicable: artículos y apartados que fundamentan la respuesta, con sus identificadores entre corchetes [SOR-2026-08-Pxxx-Sxxx] y números de página.",\n',
            'conditions': '  "conditions_and_exceptions": "SOLO condiciones, requisitos, excepciones o diferencias entre categorías o modalidades que CAMBIAN la respuesta a esta consulta, cada una con su identificador [SOR-...] y con su fragmento literal en evidence_quotes. No incluyas requisitos conexos, notas técnicas ni datos que no se hayan preguntado. Si no existen, responde exactamente: \\"No aplica\\".",\n',
            'extended': '  "extended_analysis": "Solo si la consulta plantea un caso, una situación o un procedimiento: aplicación de la norma al caso, escenarios y consecuencias normativas, sin cifras ni datos que no figuren en tus citas literales; identifica toda interpretación con \\"Interpretación normativa:\\". Para preguntas fácticas directas responde exactamente: \\"No aplica\\".",\n',
            'limitations': '  "limitations": "Lo que los pasajes certificados no determinan y que sea relevante para la consulta (evidencia parcial, aspectos no regulados expresamente). Si los pasajes responden de manera completa e indubitable, responde exactamente: \\"Ninguna\\".",\n',
            'answerability': '  "answerability": "RESPALDADA si los pasajes SOR certificados responden la consulta; REQUIERE_ACLARACION si la consulta admite interpretaciones con respuestas normativas distintas y no puede responderse responsablemente sin precisarla; en particular, si la consulta NO indica la modalidad, el tipo de evento, la categoría o la situación y los pasajes contienen reglas DISTINTAS para distintas modalidades, eventos, categorías o situaciones (entonces escribe en summary SOLO la pregunta de aclaración con las alternativas posibles, sin cifras ni reglas); EVIDENCIA_INSUFICIENTE en caso contrario (entonces no formules dictamen).",\n',
            'rule7': "7. Respuesta Única, Completa y Proporcional: Entrega en esta única respuesta todo lo necesario para resolver la consulta (respuesta directa, regla aplicable y, solo si son pertinentes, condiciones, excepciones, diferencias entre categorías y consecuencias). No habrá ampliación posterior. No añadas información complementaria que no ayude a responder; una consulta concreta recibe una respuesta concreta.\n",
            'rule10_spec': "   - Especificaciones Técnicas (equipamiento, judogi, medidas, tiempos): Responde la especificación concreta consultada tal como figura en los pasajes certificados, con su cita. No añadas requisitos conexos que no se hayan preguntado.\n",
            'rule13': "13. Respaldo Literal Verificable: Cada pasaje SOR citado debe tener en 'evidence_quotes' al menos un fragmento copiado LITERALMENTE de ese pasaje. Toda cifra, plazo, medida, sanción, condición o excepción de CUALQUIER campo de texto ('summary', 'normative_basis', 'conditions_and_exceptions', 'extended_analysis' y 'limitations') debe aparecer en esos fragmentos; si no puedes citarla literalmente, no la escribas. Si el fragmento citado tiene cerca una excepción o condición (except, unless, however, although, only...) o una remisión a otro artículo, cita también esa excepción literalmente. Nunca cites texto de los bloques [COMPLEMENTO-n] como respaldo. Si no puedes respaldar literalmente la respuesta con los pasajes certificados, usa answerability = EVIDENCIA_INSUFICIENTE. Ausencias: no afirmes que el SOR «no establece», «no especifica» o «no regula» algo; si los pasajes entregados no lo contienen, indícalo solo en 'limitations' como «los pasajes entregados no contienen…». No generalices una regla de un evento, modalidad o categoría a otros.\n",
        }

    @staticmethod
    def _rigor_rule() -> str:
        """Regla 14 del prompt (ADA_PROMPT_RIGOR=1; desactivada por defecto). Generica: no menciona
        consultas, articulos ni casos concretos."""
        if os.environ.get("ADA_PROMPT_RIGOR", "").strip() != "1":
            return ""
        return (
            "14. Correspondencia Estricta entre Afirmaciones y Citas: "
            "(a) Toda cifra (números, plazos, medidas, edades, rangos o cantidades) que escribas en 'summary', "
            "'normative_basis' o 'conditions_and_exceptions' debe figurar textualmente en al menos uno de tus "
            "'evidence_quotes'; si no puedes citarla literalmente, no la escribas. "
            "(b) Toda excepción, condición, salvedad o restricción normativa que menciones debe tener su propia cita "
            "literal en 'evidence_quotes'; si no puedes citarla, no la menciones. "
            "(c) No agregues datos, condiciones, categorías ni interpretaciones que no estén en los pasajes que citas. "
            "(d) Cada elemento de 'evidence_quotes' debe respaldar específicamente la afirmación indicada en su campo "
            "'supports'; no uses una cita para respaldar una afirmación distinta de la que contiene.\n"
        )

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

        # R2 (auditoria de trazabilidad; ADA_TRANSLATE_ANY_LANG=1, desactivado por defecto): toda consulta que no
        # este en ingles se traduce (portugues, frances...), no solo la espanola, y la traduccion debe ser fiel.
        any_lang = os.environ.get("ADA_TRANSLATE_ANY_LANG", "").strip() == "1"
        if any_lang:
            from decision_integrity import query_language as _qlang
            if _qlang(q_clean) == "en" and not has_spanish_chars:
                return q_clean
        elif not has_spanish_chars and not has_spanish_keywords:
            return q_clean

        prompt = (
            "You are an expert official IJF (International Judo Federation) translator and terminology specialist.\n"
            + ("Translate the following judo inquiry from its original language (Spanish, Portuguese, French or any other) into concise, precise technical English for retrieval against the official IJF Sport and Organisation Rules (SOR 2026).\n"
               if any_lang else
               "Translate the following judo inquiry from Spanish into concise, precise technical English for retrieval against the official IJF Sport and Organisation Rules (SOR 2026).\n")
            +
            "CRITICAL RULES:\n"
            "1. Strictly preserve all official Japanese judo terminology exactly as spelled (e.g. Ippon, Waza-ari, Shido, Hansoku-make, Osaekomi, Tori, Uke, Tatami, Matte, Hajime, Shime-waza, Kansetsu-waza, Toketa, Seoi-nage, Reverse seoi-nage, etc.).\n"
            "2. Map colloquial, descriptive, or informal actions to official IJF SOR normative phrases:\n"
            "   - insult / insulta / ofensa verbal -> derogatory remarks, calls or gestures to opponent or referee\n"
            "   - agredir / agresión física / golpe -> action against the spirit of judo, deliberate action causing injury\n"
            "   - falta de respeto / conducta antideportiva -> acts against the spirit of judo\n"
            "   - cadetes reverse seoi-nage -> cadet reverse seoi-nage\n"
            "   - defensa con la cabeza -> head defence uke\n"
            "   - entrenador / coach vestimenta / dress code -> coaches' dress code\n"
            "   - veteranos / master / categoría de edad -> regulations for veterans age divisions contest duration category combining\n"
            "   - antidopaje / control dopaje -> medical and anti-doping handbook doping control selection procedure\n"
            "   - accion simultanea / ambos caen / ataque simultaneo -> simultaneous action both athletes fall tatami\n"
            "   - saludo / saludo equipos / equipos mixtos / reverencia -> bowing ceremony team competition mixed team encounter rei otagai-ni technical table\n"
            "   - tiempo de tolerancia / presentarse en el tatami / comparecer / incomparecencia -> failure to appear\n"
            "   - disciplinario / comite disciplinario -> IJF Disciplinary Committee Disciplinary Code sports integrity betting sanctions\n"
            "3. Translate terminology only: do NOT add penalties, scores, outcomes, article numbers or numeric values that are not present in the user query.\n"
            "4. Output ONLY the translated technical English query without any explanation, markdown formatting, quotes, or trailing notes.\n"
            + ("5. Faithful translation: apart from the mappings in rule 2, do not add words or concepts that are not in the query "
               "(no other sports, systems, bodies, procedures or judo topics). If the query is not about judo, translate it literally.\n"
               if any_lang else "")
            + "\n"
            f"Query to translate: {q_clean}\n"
            "English translation:"
        )

        try:
            llm_res = self._call_llm(prompt)
            raw_text = None
            trans_meta = {}
            if isinstance(llm_res, tuple) and len(llm_res) >= 2:
                raw_text, trans_meta = llm_res[0], llm_res[1]
            elif isinstance(llm_res, str):
                raw_text = llm_res

            self._last_translation_usage = trans_meta.get("token_usage", {
                "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0
            })

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

        # Robust offline deterministic dictionary projection fallback.
        # Phase 6 (C2): tokens are read with accented letters intact (\w is Unicode-aware) so that words
        # such as "cómo" or "dimensión" are not split into fragments, and only pure Spanish function words
        # are dropped. No word carries normative meaning here; content words are kept as before.
        spanish_function_words = {
            "como", "cual", "cuales", "cuando", "donde", "que", "quien", "quienes", "cuanto", "cuantos",
            "lo", "le", "les", "me", "nos", "pero", "sobre", "hasta", "durante", "desde", "hacia",
            "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas", "eso", "esto",
            "y", "o", "u", "e", "ni", "a", "ante", "tras", "segun", "mediante", "cuya", "cuyo",
        }
        proj_parts = []
        for w in re.findall(r"[\w\-]{2,}", q_lower):
            clean_w = w.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n").replace("ü", "u")
            if clean_w in spanish_function_words:
                continue
            if clean_w in self.rre.SPANISH_TO_ENGLISH_SYNONYMS:
                proj_parts.append(self.rre.SPANISH_TO_ENGLISH_SYNONYMS[clean_w])
            elif clean_w in {"saludo", "saludos", "saludar"}:
                proj_parts.append("bowing bow ceremony rei otagai-ni")
            elif clean_w in {"equipos", "equipo"}:
                proj_parts.append("team teams")
            elif clean_w in {"mixtos", "mixto", "mixtas", "mixta"}:
                proj_parts.append("mixed")
            elif clean_w in {"tolerancia"}:
                proj_parts.append("tolerance")
            elif clean_w in {"presentarse", "presenta", "comparecer", "comparecencia"}:
                proj_parts.append("appear appearance failure to appear")
            elif clean_w not in {"en", "la", "de", "del", "por", "para", "con", "el", "los", "las", "un", "una", "al", "es", "son", "se", "su", "sus", "cual", "que"}:
                proj_parts.append(clean_w)
        if proj_parts:
            # Deduplicate repeated tokens produced by overlapping dictionary expansions, keeping order.
            seen_tokens = set()
            unique_tokens = []
            for token in " ".join(proj_parts).split():
                if token not in seen_tokens:
                    seen_tokens.add(token)
                    unique_tokens.append(token)
            return " ".join(unique_tokens)

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
        # Fast pre-check: if query contains clear negative domain anchors (e.g. NBA, Formula 1), abstain without LLM translation cost
        try:
            from negative_domain_anchor_scoring import NegativeDomainAnchorScorer
            neg_check = NegativeDomainAnchorScorer.score_negative_domain(situation_query)
            if neg_check.is_ood:
                retrieval_res = self.rre.retrieve(situation_query, top_k=top_k, expand_graph=False)
                # AUD-04.1: supplementary documents never turn an out-of-domain query into a normative one.
                if retrieval_res.get("status") == "ABSTAIN":
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
                        "source_sha256_verified": retrieval_res.get("source_sha256_verified", False),
                        "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                    }
        except Exception:
            pass

        search_query_en = self._translate_to_technical_english(situation_query)
        retrieval_res = self.rre.retrieve(search_query_en, top_k=top_k, expand_graph=True, domain_query=situation_query)

        # Retrieve authorized supplementary official sources (Shadow / Sidecars TIER_2 / TIER_3)
        supp_results = []
        if self._is_supplementary_retrieval_enabled():
            try:
                supp_results = self.rre.retrieve_supplementary(situation_query, min_score=2.0)
                if not supp_results and search_query_en != situation_query:
                    supp_results = self.rre.retrieve_supplementary(search_query_en, min_score=2.0)
            except Exception:
                supp_results = []

        evidence = retrieval_res.get("evidence", []) if retrieval_res.get("status") != "ABSTAIN" else []
        related = retrieval_res.get("related_passages", []) if retrieval_res.get("status") != "ABSTAIN" else []

        # AUD-04.1: without primary SOR evidence, supplementary material cannot keep the query open.
        if not evidence:
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
                "source_sha256_verified": retrieval_res.get("source_sha256_verified", False),
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

        # Document Authority & Validity Gate via DocumentValidator
        candidate_items = []
        # Primary and cross-referenced SOR passages must traverse the same
        # certification path before they can be placed in the reasoning context.
        for ev in [*evidence, *related]:
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

        # AUD-04.2: authority, validity and eligibility of supplementary material are read
        # only from the document catalogue. Unregistered documents are discarded.
        supp_catalog = {}
        for supp in supp_results:
            supp_id = supp.get("chunk_id") or supp.get("passage_id")
            supp_kun_id = supp.get("source_kun_id") or (supp.get("metadata") or {}).get("source_kun_id")
            if supp_id in self.DEACTIVATED_SUPPLEMENTARY_CHUNK_IDS or supp_kun_id in self.DEACTIVATED_SUPPLEMENTARY_KUN_IDS:
                continue
            supp_text = (supp.get("content_text") or supp.get("text") or "").strip()
            doc_meta = self.doc_validator.get_document(supp.get("document_id") or "")
            role = _SUPPLEMENTARY_ROLE_BY_AUTHORITY.get(doc_meta.authority) if doc_meta else None
            if not supp_id or not supp_text or role is None:
                continue
            supp_catalog[supp_id] = doc_meta
            candidate_items.append(
                EvidenceItem(
                    evidence_id=supp_id,
                    document_id=doc_meta.document_id,
                    content_text=supp_text,
                    role=role,
                    authority=doc_meta.authority,
                    validity=doc_meta.validity,
                    eligibility=doc_meta.determine_eligibility(),
                    semantic_relevance_score=min(1.0, max(0.0, float(supp.get("confidence_score") or 0.0))),
                    article_number=supp.get("article_id"),
                    page_number=supp.get("page"),
                    paragraph_or_section=supp.get("title"),
                    url_reference=supp.get("source_url")
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

        # The EvidenceBundle is the sole source of evidence eligible for the
        # reasoning context and citations.  Retrieval output is only a
        # candidate until it has survived this gate.
        evidence, related, supp_results = self._filter_certified_evidence(
            evidence, related, supp_results, certified_bundle
        )

        # A certified decision must retain at least one direct Tier 1 passage.
        # Do not turn related or supplementary material into a decisive answer.
        if not evidence:
            reason_text = "Abstención por ausencia de evidencia primaria certificada directa para la decisión."
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
                    "is_structured": True,
                },
                "evidence": [],
                "related_passages": [],
                "engine": "ADA-RRE-v2",
                "rre_operating_mode": retrieval_res.get("operating_mode", "UNKNOWN"),
                "degradation_reason": retrieval_res.get("degradation_reason"),
                "source_sha256_verified": retrieval_res.get("source_sha256_verified", False),
                "certified_bundle": certified_bundle.model_dump(),
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

        # AUD-04.3: supplementary material goes in a separate block, explicitly non-decisive and
        # without citable identifiers; it is never part of the certified normative context.
        supp_blocks = []
        supplementary_context = []
        for idx, supp in enumerate(supp_results, 1):
            supp_id = supp.get("chunk_id") or supp.get("passage_id")
            doc_meta = supp_catalog.get(supp_id)
            if doc_meta is None:
                continue
            supp_text = (supp.get("content_text") or supp.get("text") or "").strip()
            if len(supp_text) > 1500:
                supp_text = supp_text[:1497].rsplit(" ", 1)[0] + "..."
            supp_blocks.append(
                f"[COMPLEMENTO-{idx}] {supp.get('title', '')} "
                f"(documento complementario {doc_meta.authority.value}; NO DECISORIO):\n{supp_text}"
            )
            supplementary_context.append({
                "chunk_id": supp_id,
                "document_id": doc_meta.document_id,
                "title": supp.get("title", ""),
                "authority": doc_meta.authority.value,
                "validity": doc_meta.validity.value,
                "decisive": False,
            })
        supp_context = "\n\n---\n\n".join(supp_blocks)

        full_context = "\n\n---\n\n".join(context_blocks)

        import decision_integrity as _dig_mod
        unified = bool(_dig_mod.FIX_ALL_VISIBLE_FIELDS)
        T = self._contract_texts(unified)
        prompt = (
            "Eres el Asistente de Decisión Arbitral (ADA) oficial de la Federación Internacional de Judo (IJF).\n"
            f"Edición normativa aplicable: {self.config['version_label']} (14 de agosto de 2026).\n\n"
            "Tu tarea es responder la consulta del usuario aplicando rigurosamente los artículos oficiales adjuntos.\n\n"
            "CONTEXTO NORMATIVO CERTIFICADO (NORMA PRIMARIA SOR 2026; única fuente decisoria y citable):\n"
            f"{full_context}\n\n"
            + (
                "CONTEXTO DOCUMENTAL COMPLEMENTARIO — INFORMATIVO Y NO DECISORIO (no es norma; no citable):\n"
                f"{supp_context}\n\n" if supp_context else ""
            )
            +
            f"{T['title']}"
            "Debes responder estructuradamente devolviendo EXCLUSIVAMENTE un objeto JSON válido (sin texto antes ni después) con las siguientes claves:\n"
            "{\n"
            f"{T['summary']}"
            f"{T['normative_basis']}"
            '  "citations": ["Lista de identificadores citados, ej: SOR-2026-08-Pxxx-Sxxx"],\n'
            f"{T['conditions']}"
            f"{T['extended']}"
            f"{T['limitations']}"
            f"{T['answerability']}"
            '  "evidence_quotes": [{"passage_id": "SOR-2026-08-Pxxx-Sxxx", "quote": "fragmento LITERAL copiado del pasaje SOR certificado que respalda una afirmación (mínimo 6 palabras)", "supports": "afirmación respaldada"}],\n'
            '  "evidence_conflicts": ["Contradicciones detectadas entre pasajes certificados; lista vacía si no hay"]\n'
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
            f"{T['rule7']}"
            "8. Tratamiento de Ambigüedad Normativa o Fáctica: Si la norma no determina unívocamente la solución o la consulta carece de datos fácticos determinantes, expón las disposiciones aplicables, reconoce lo que el texto no determina e indica qué precisiones de hecho se requieren para emitir una resolución definitiva.\n"
            "9. Transparencia sobre Evidencia Insuficiente: Si los pasajes certificados no contienen la respuesta o resultan insuficientes para confirmar una regla, declara con total franqueza la limitación en 'summary' y 'limitations', sin formular dictámenes categóricos infundados.\n"
            "10. Criterios Generales de Presentación (no constituyen fuente normativa):\n"
            f"{T['rule10_spec']}"
            "   - Reglas Generales y Reglas Especiales: Si los pasajes certificados contienen una regla general y otra especial (por categoría de edad, rol tori/uke u otra circunstancia), expón cada una con su propia cita y su ámbito de aplicación, sin equipararlas ni extender una al ámbito de la otra.\n"
            "   - Fidelidad Textual: No agregues condiciones geométricas, temporales, de observación ni consecuencias que el texto certificado no establezca. Si los pasajes no resuelven la consulta, aplica la política 9.\n"
            "   - Diagramas y Cuadros: Si la consulta refiere a una plantilla de diagrama/cuadro (págs. 213-230), explica las reglas sustantivas de sorteo aplicables e indica que la geometría espacial debe consultarse en el PDF oficial.\n"
            "11. Contexto Complementario No Decisorio: Los bloques [COMPLEMENTO-n] solo pueden aclarar terminología o contexto de aplicación. No son norma: no fundamentan la conclusión, no se incluyen en 'citations' ni en 'normative_basis' y no se presentan como fuente de una regla. Toda conclusión debe apoyarse en pasajes SOR primarios citados por su identificador. Si un complemento contradice o excede el texto SOR, prevalece el SOR.\n"
            f"{T['rule13']}"
            f"{self._rigor_rule()}"
            "12. Language Policy: Detect the language of the user query and requested output language. "
            + ("Write the entire JSON response (summary, normative_basis, conditions_and_exceptions, extended_analysis, limitations) in fluent, precise ENGLISH using official IJF terminology (e.g. 'Hansoku-make', 'Osaekomi', 'Shido', 'Direct Hansoku-make', 'Contest Area', 'Safety Area').\n\n" if language == "en" else "Write the entire JSON response in clear, rigorous SPANISH using official IJF terminology, unless the user query explicitly demands another language.\n\n" if language == "es" else "If the query is in English, write the entire JSON response in fluent, precise ENGLISH using official IJF terminology. If the query is in Spanish, write the response in SPANISH.\n\n")
            + f"Consulta del usuario / User query: {situation_query}\n"
            + f"Consulta técnica normalizada (EN; usada para verificar la pertinencia de las citas): {search_query_en}\n"
            + "Respuesta JSON:"
        )

        llm_res = self._call_llm(prompt)
        if isinstance(llm_res, tuple):
            llm_answer, llm_meta = llm_res
        else:
            llm_answer, llm_meta = llm_res, {}

        # Consolidate token usage from translation step (if any) and analysis step
        main_usage = llm_meta.get("token_usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        trans_usage = getattr(self, "_last_translation_usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        self._last_translation_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        total_p = trans_usage.get("prompt_tokens", 0) + main_usage.get("prompt_tokens", 0)
        total_c = trans_usage.get("completion_tokens", 0) + main_usage.get("completion_tokens", 0)
        total_t = total_p + total_c
        query_token_usage = {
            "prompt_tokens": total_p,
            "completion_tokens": total_c,
            "total_tokens": total_t,
            "translation_tokens": trans_usage,
            "analysis_tokens": main_usage
        }
        llm_meta["token_usage"] = query_token_usage
        lang_key = "en" if language == "en" else "es"

        def _result(status, mode_label, analysis, structured_dict, dig):
            return {
                "status": status, "query": situation_query, "mode": mode_label, "analysis": analysis,
                "structured_answer": structured_dict, "evidence": evidence, "related_passages": related,
                "engine": "ADA-RRE-v2", "rre_operating_mode": retrieval_res.get("operating_mode", "UNKNOWN"),
                "degradation_reason": retrieval_res.get("degradation_reason"),
                "source_sha256_verified": retrieval_res.get("source_sha256_verified", False),
                "certified_bundle": certified_bundle.model_dump(), "llm_meta": llm_meta,
                "token_usage": query_token_usage, "supplementary_context": supplementary_context,
                "decision_integrity": dig,
            }

        def _unified_abstention(reason_text, dig):
            msg = (f"⚠️ **Abstención Normativa Oficial ({self.config['version_label']})**\n\n{reason_text}\n\n"
                   "*Los pasajes certificados recuperados se conservan solo como referencia de consulta; no constituyen dictamen.*")
            return _result("ABSTAIN", "Abstención (validación integral del contenido visible)", msg, {
                "summary": msg, "normative_basis": "", "citations": [], "conditions_and_exceptions": "",
                "extended_analysis": "", "limitations": reason_text, "is_structured": True,
                "answer_mode": "UNIFIED", "response_status": "ABSTAIN"}, dig)

        # Respuesta unica: solicitud de aclaracion declarada por el modelo (no es un dictamen). Solo se muestra su
        # texto si no afirma cifras ni terminos ajenos a la consulta o a sus citas literales; si no, texto generico.
        if unified and llm_answer:
            _obj = _parse_answer(llm_answer)
            if isinstance(_obj, dict) and str(_obj.get("answerability", "")).strip().upper() == "REQUIERE_ACLARACION":
                delivered_map = {p.get("passage_id"): p for p in [*evidence, *related] if p.get("passage_id")}
                ok, why = self._decision_integrity_gate().verify_clarification(
                    llm_answer, situation_query, search_query_en, delivered_map)
                text = str(_obj.get("summary") or "").strip() if ok else ""
                text = text or CLARIFY_TEXT[lang_key]
                clar = {"decision": "SOLICITAR_ACLARACION", "verified_text": ok, "detail": why,
                        "version": _dig_mod.dig_version()}
                return _result("CLARIFICATION_REQUIRED", "Solicitud de aclaración (consulta con interpretaciones normativas distintas)",
                               text, {"summary": text, "normative_basis": "", "citations": [],
                                      "conditions_and_exceptions": "", "extended_analysis": "",
                                      "limitations": CLARIFY_TEXT[lang_key], "is_structured": True,
                                      "answer_mode": "UNIFIED", "response_status": "CLARIFICATION_REQUIRED"}, clar)

        citations_valid = self._validate_llm_citations(llm_answer, evidence, related)

        # Fase 9 - control de integridad decisoria (DIG). Una cita SOR valida (nivel A) no implica
        # pertinencia (B), suficiencia (C) ni respaldo efectivo (D). DIG aplica controles genericos y
        # conservadores; si alguno falla se abstiene. Nunca certifica entailment (D = NO_VERIFICADO).
        decision_integrity = None
        pruning_info = None
        _dig_eval = None
        if llm_answer and citations_valid:
            import decision_integrity as _dig
            extra = {}
            if _dig.FIX_DIG08_INSTRUCTIONS:
                # Texto de instrucciones = prompt sin evidencia SOR ni bloques SHADOW (DIG-08, correccion v3).
                instr = prompt.replace(full_context, " ")
                if supp_context:
                    instr = instr.replace(supp_context, " ")
                extra["instruction_text"] = instr
            # Titles are delivered to the model too, so they are part of the SHADOW footprint.
            supp_texts = [f"{s.get('title') or ''} {s.get('content_text') or s.get('text') or ''}" for s in supp_results]

            def _dig_eval(answer_text):
                return self._decision_integrity_gate().evaluate(
                    answer_text, situation_query, search_query_en, evidence, related,
                    supplementary_texts=supp_texts, **extra)

            decision_integrity = _dig_eval(llm_answer)
            # Respuesta unica: si el DIG solo rechaza cifras o terminos sin respaldo, se retiran las frases
            # ACCESORIAS que los contienen (nunca summary ni normative_basis) y la respuesta resultante se evalua
            # de nuevo con TODOS los controles. Si no supera la nueva evaluacion, se mantiene la abstencion.
            failed0 = set(decision_integrity.get("failed_checks") or [])
            if unified and decision_integrity.get("decision") != "PERMITIR" and failed0 and failed0 <= PRUNABLE_CHECKS:
                cand, removed = self._decision_integrity_gate().prune_unsupported(llm_answer, situation_query, search_query_en)
                if removed and self._validate_llm_citations(cand, evidence, related):
                    re_dig = _dig_eval(cand)
                    if re_dig.get("decision") == "PERMITIR":
                        pruning_info = {"initial_failed_checks": sorted(failed0), "removed": removed}
                        llm_answer = cand
                        decision_integrity = dict(re_dig, pruning=pruning_info)

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

        integrity_ok = bool(decision_integrity) and decision_integrity.get("decision") == "PERMITIR"
        if not (llm_answer and citations_valid and integrity_ok):
            # AUD-03 (option A): without a generated answer whose citations validate against
            # the certified primary evidence, nothing in this system can establish that the
            # retrieved passages support the query.  The certified passages are returned only
            # for consultation; no summary, conclusion or normative citation is produced.
            if llm_answer and citations_valid and not integrity_ok:
                failed = ", ".join((decision_integrity or {}).get("failed_checks", [])) or "control no ejecutado"
                mode_label = "Abstención (control de integridad decisoria: respaldo no verificable)"
                reason_text = (
                    "La respuesta generada cita pasajes SOR certificados, pero no superó el control de integridad "
                    f"decisoria ({failed}). Una cita válida no demuestra que la evidencia respalde la respuesta."
                )
            elif llm_answer and not citations_valid:
                mode_label = "Abstención (la respuesta IA no superó la validación de citas SOR primarias)"
                reason_text = (
                    "La respuesta generada no cita al menos un pasaje SOR primario certificado entregado al modelo, "
                    "o cita identificadores, artículos o códigos ajenos a la evidencia certificada."
                )
            else:
                mode_label = "Abstención (modo local sin modelo generativo)"
                reason_text = (
                    "Sin modelo generativo disponible no es posible establecer que los pasajes recuperados "
                    "respalden la consulta."
                )
            abstain_msg = (
                f"⚠️ **Abstención Normativa Oficial ({self.config['version_label']})**\n\n"
                f"{reason_text}\n\n"
                "*Los pasajes certificados recuperados se conservan solo como referencia de consulta; no constituyen dictamen.*"
            )
            return {
                "status": "ABSTAIN",
                "query": situation_query,
                "mode": mode_label,
                "analysis": abstain_msg,
                "structured_answer": {
                    "summary": abstain_msg,
                    "normative_basis": "",
                    "citations": [],
                    "conditions_and_exceptions": "",
                    "extended_analysis": "",
                    "limitations": reason_text,
                    "is_structured": True,
                    **({"answer_mode": "UNIFIED", "response_status": "ABSTAIN"} if unified else {}),
                },
                "evidence": evidence,
                "related_passages": related,
                "engine": "ADA-RRE-v2",
                "rre_operating_mode": retrieval_res.get("operating_mode", "UNKNOWN"),
                "degradation_reason": retrieval_res.get("degradation_reason"),
                "source_sha256_verified": retrieval_res.get("source_sha256_verified", False),
                "certified_bundle": certified_bundle.model_dump(),
                "llm_meta": llm_meta,
                "token_usage": query_token_usage,
                "supplementary_context": supplementary_context,
                "decision_integrity": decision_integrity,
            }

        # Citation validation checks identifiers, articles and codes against the certified
        # evidence.  It is NOT a semantic entailment check of the generated claims.
        succ_prov = llm_meta.get("successful_provider", "LLM")
        succ_model = llm_meta.get("successful_model", "")
        if succ_model:
            mode_label = f"Síntesis Analítica IA ({succ_prov} / {succ_model}; citas SOR validadas; respaldo literal verificado, sin entailment)"
            header = f"⚖️ **Síntesis Analítica IA ({succ_prov} — {succ_model})**"
        else:
            mode_label = "Síntesis Analítica IA (Conectado; citas SOR validadas; respaldo literal verificado, sin entailment)"
            header = "⚖️ **Síntesis Analítica IA (Conectado; citas SOR validadas)**"
        structured = parse_structured_response(llm_answer, evidence)

        # Rigor Normativo: Validar afirmaciones, códigos de penalización y artículos contra evidencia oficial
        validator = NormativeValidator(evidence_passages=evidence, related_passages=related)
        limitations_before_sanitize = structured.limitations
        structured = validator.sanitize_structured_answer(structured)
        sanitizer_fired = structured.limitations != limitations_before_sanitize
        prune_note = PRUNE_NOTE[lang_key] if (unified and pruning_info) else ""
        if prune_note:
            lim = (structured.limitations or "").strip()
            structured.limitations = prune_note if lim.lower().rstrip(".") in ("", "ninguna", "none") else f"{lim}\n\n{prune_note}"

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
                match_id = re.search(r"((?:SOR-[A-Za-z0-9-]+)|(?:KUN-[A-Za-z0-9_-]+)|(?:CHK-[A-Za-z0-9_-]+))", c)
                cid = match_id.group(1) if match_id else c
            elif isinstance(c, dict):
                cid = c.get("passage_id")
            else:
                cid = None

            # AUD-04.4: only certified primary passages delivered to the model are kept.
            if cid and cid in rich_citations_map and cid not in seen_pids:
                enriched_citations.append(rich_citations_map[cid])
                seen_pids.add(cid)

        # If the 'citations' field was empty, use the primary IDs the model cited in its text
        # (never passages it did not cite).
        if not enriched_citations:
            for cid in re.findall(r"SOR-[A-Za-z0-9]+-[A-Za-z0-9]+-P\d+-S\d+", llm_answer or ""):
                if cid in rich_citations_map and cid not in seen_pids:
                    enriched_citations.append(rich_citations_map[cid])
                    seen_pids.add(cid)

        structured.citations = enriched_citations

        # Apply citation formatting to all structured text components
        structured.summary = format_citations(structured.summary, all_passages_data)
        structured.normative_basis = format_citations(structured.normative_basis, all_passages_data)
        structured.conditions_and_exceptions = format_citations(structured.conditions_and_exceptions, all_passages_data)
        structured.extended_analysis = format_citations(structured.extended_analysis, all_passages_data)
        structured.limitations = format_citations(structured.limitations, all_passages_data)

        # Respuesta unica: validacion FINAL sobre el contenido que vera el usuario, despues de todas las
        # transformaciones (sanitizador normativo, nota de poda y formateo de citas). Se vuelve a ejecutar el DIG
        # completo sobre los campos visibles; si el sanitizador tuvo que neutralizar algo, no se emite dictamen.
        if unified:
            if sanitizer_fired:
                return _unified_abstention(
                    "La respuesta generada contenía referencias o afirmaciones que el control normativo no pudo "
                    "certificar con los pasajes SOR entregados; no se emite dictamen.",
                    dict(decision_integrity or {}, final_visible_check={"decision": "ABSTENER", "reason": "sanitizador_normativo"}))
            final_obj = dict(_parse_answer(llm_answer) or {})
            for k in VISIBLE_FIELDS:
                final_obj[k] = visible_text_for_validation(getattr(structured, k, "") or "", system_notes=(prune_note,))
            final_dig = _dig_eval(json.dumps(final_obj, ensure_ascii=False)) if _dig_eval else {"decision": "ABSTENER", "failed_checks": ["sin_dig"]}
            decision_integrity = dict(decision_integrity or {}, final_visible_check={
                "decision": final_dig.get("decision"), "failed_checks": final_dig.get("failed_checks", [])},
                validated_answer=final_obj)
            if final_dig.get("decision") != "PERMITIR":
                return _unified_abstention(
                    "El contenido final de la respuesta no superó la validación integral del control de integridad "
                    f"decisoria ({', '.join(final_dig.get('failed_checks', []))}).", decision_integrity)

        # Build backward-compatible flat analysis text with Level 1 first, Level 2 details attached
        flat_analysis = structured.to_legacy_text(header=header)

        structured_dict = structured.to_dict()
        if unified:
            structured_dict.update(answer_mode="UNIFIED", response_status="SUCCESS")
        return {
            "status": "SUCCESS",
            "query": situation_query,
            "mode": mode_label,
            "analysis": flat_analysis,
            "structured_answer": structured_dict,
            "evidence": evidence,
            "related_passages": related,
            "engine": "ADA-RRE-v2",
            "rre_operating_mode": retrieval_res.get("operating_mode", "UNKNOWN"),
            "degradation_reason": retrieval_res.get("degradation_reason"),
            "source_sha256_verified": retrieval_res.get("source_sha256_verified", False),
            "certified_bundle": certified_bundle.model_dump(),
            "llm_meta": llm_meta,
            "token_usage": query_token_usage,
            "supplementary_context": supplementary_context,
            "decision_integrity": decision_integrity,
        }

    def _decision_integrity_gate(self) -> DecisionIntegrityGate:
        """Lazily built DIG gate over the primary SOR corpus loaded by the RRE (read-only)."""
        gate = getattr(self, "_dig_gate", None)
        if gate is None:
            passages = list(getattr(self.rre, "passages_by_id", {}).values()) or list(getattr(self.rre, "passages", []) or [])
            gate = DecisionIntegrityGate(passages)
            self._dig_gate = gate
        return gate

    @staticmethod
    def _filter_certified_evidence(evidence: list, related: list, supplementary: list, bundle: EvidenceBundle) -> tuple[list, list, list]:
        """Keep only retrieved items that are present in the applicable bundle lane."""
        primary_ids = {item.evidence_id for item in bundle.primary_normative_evidence}
        interpretive_ids = {item.evidence_id for item in bundle.interpretive_evidence}
        certified_evidence = [ev for ev in evidence if ev.get("passage_id") in primary_ids]
        certified_related = [rel for rel in related if rel.get("passage_id") in primary_ids]
        certified_supplementary = [
            item for item in supplementary
            if (item.get("chunk_id") or item.get("passage_id") or item.get("document_id"))
            in interpretive_ids
        ]
        return certified_evidence, certified_related, certified_supplementary

    def _validate_llm_citations(self, answer: str | None, evidence: list, related: list) -> bool:
        """Accept generated analysis only when it cites at least one certified primary SOR passage
        delivered to the model, cites nothing outside the delivered evidence, and does not introduce
        articles or penalty codes absent from that evidence.

        Limitation: this validates identifiers and references only. It does not verify that the
        cited passages semantically support the generated claims (no entailment check)."""
        if not isinstance(answer, str) or not answer.strip():
            return False

        # Certified primary SOR passages that were delivered to the model (direct + related,
        # both already filtered through the EvidenceBundle primary lane).
        primary_ids = {
            item.get("passage_id")
            for item in [*evidence, *related]
            if isinstance(item, dict) and item.get("passage_id")
        }

        # AUD-04.4: supplementary chunk IDs and document IDs are never valid normative citations.
        allowed_ids = set(primary_ids)

        # Detect SOR, KUN and CHK identifiers; any identifier outside allowed_ids rejects the answer.
        raw_found = re.findall(r"(?:SOR-[A-Za-z0-9]+-[A-Za-z0-9]+-P\d+-S\d+|KUN-[A-Za-z0-9_-]+|CHK-[A-Za-z0-9_-]+)", answer)
        cited_ids = set(raw_found)
        # AUD-03: at least one certified primary SOR passage delivered to the model must be cited.
        # An answer without citations, or citing only supplementary material, is rejected.
        if not (cited_ids & primary_ids):
            return False
        # Every cited identifier must belong to the evidence delivered to the model.
        if not all(citation in allowed_ids for citation in cited_ids):
            return False

        # Reference check (lexical): articles and penalty codes must appear in the delivered evidence.
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

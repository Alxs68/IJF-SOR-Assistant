"""
Normative Hallucination Validator for IJF SOR Assistant.

Performs deterministic, semantic, and structural verification of model responses
against the official retrieved context before the response is presented to the user.
"""

import re
from typing import Dict, Any, List, Tuple, Optional, Set


class NormativeVerificationResult:
    """Outcome of normative claim validation."""

    def __init__(
        self,
        is_valid: bool,
        unsupported_claims: List[str],
        hallucinated_codes: List[str],
        hallucinated_articles: List[str],
        hallucinated_passages: List[str],
        semantic_mismatches: List[str],
        scope_violations: List[str],
        warnings: List[str]
    ):
        self.is_valid = is_valid
        self.unsupported_claims = unsupported_claims
        self.hallucinated_codes = hallucinated_codes
        self.hallucinated_articles = hallucinated_articles
        self.hallucinated_passages = hallucinated_passages
        self.semantic_mismatches = semantic_mismatches
        self.scope_violations = scope_violations
        self.warnings = warnings


class NormativeValidator:
    """
    Validates that every material claim, penalty code, article number,
    and passage ID present in the LLM response is strictly grounded in the
    retrieved official passages.
    """

    # Common IJF penalty codes pattern: PS1-PS35, PH1-PH3, PX1-PX9, etc.
    PENALTY_CODE_PATTERN = re.compile(r'\b(P[SXH]\d+[a-z]?)\b', re.IGNORECASE)
    
    # Official passage pattern: SOR-2026-08-Pxxx-Sxxx
    PASSAGE_ID_PATTERN = re.compile(r'\b(SOR-2026-08-P\d{3}-S\d{3})\b', re.IGNORECASE)

    # Article pattern: Art. 18.1.4, Article 21, etc.
    ARTICLE_PATTERN = re.compile(
        r'(?:Art(?:ículo|\.|\s+)?\s*([A-Za-z]?\d+(?:\.\d+)*)|Article\s*([A-Za-z]?\d+(?:\.\d+)*))',
        re.IGNORECASE
    )

    # Terms indicating unverified administrative procedures / authority invocations
    SUSPICIOUS_PROCEDURAL_TERMS = [
        "comisión ad hoc",
        "ad hoc commission",
        "registro de la competición",
        "formulario de informe disciplinario",
        "comité de disciplina",
        "jefe de árbitros",
        "head referee director",
        "comisión médica internacional",
        "medical commission appeal",
        "suspensión de licencia",
        "expediente disciplinario",
        "tribunal de arbitraje deportivo"
    ]

    # Official Canonical Penalty Mappings (Action Keywords -> (Expected Code, Penalty Type, Category Scope))
    CANONICAL_PENALTY_MAP = {
        "PS1": {"action": "negative positions", "type": "shido", "scope": "all", "terms": ["negative position", "posición negativa", "bloqueo defensivo"]},
        "PS2": {"action": "false attack", "type": "shido", "scope": "all", "terms": ["false attack", "ataque falso"]},
        "PS3": {"action": "pull down", "type": "shido", "scope": "all", "terms": ["pull down", "tirar al suelo"]},
        "PS4": {"action": "non combativity", "type": "shido", "scope": "all", "terms": ["non combativity", "no combatividad", "pasividad"]},
        "PS5": {"action": "leave contest area", "type": "shido", "scope": "all", "terms": ["leave contest area", "salir del área"]},
        "PS8": {"action": "grab below belt", "type": "shido", "scope": "all", "terms": ["grab below belt", "agarre bajo el cinturón", "pierna en tachi-waza"]},
        "PS19": {"action": "leg grabbing", "type": "shido", "scope": "all", "terms": ["leg grab", "agarrar pierna", "agarre de pierna"]},
        "PS31": {"action": "kata-sankaku grip with lower injury risk", "type": "shido", "scope": "all", "terms": ["kata-sankaku", "menor riesgo"]},
        "PS33": {"action": "using head to throw in cadet", "type": "shido", "scope": "cadet", "terms": ["head to throw", "cabeza para proyectar"]},
        "PS34": {"action": "using head to defend in cadet", "type": "shido", "scope": "cadet", "terms": ["head to defend", "cabeza para defender", "defensa de cabeza", "defensa con cabeza", "head defence"]},
        "PS35": {"action": "reverse seoi-nage in cadet", "type": "shido", "scope": "cadet", "terms": ["reverse seoi-nage", "seoi-nage inverso"]},
        "PH1": {"action": "head dive", "type": "hansoku-make", "scope": "all", "terms": ["head dive", "inmersión de cabeza", "buceo de cabeza"]},
        "PX1": {"action": "kawazu-gake", "type": "hansoku-make", "scope": "all", "terms": ["kawazu-gake"]},
        "PX2": {"action": "kani-basami", "type": "hansoku-make", "scope": "all", "terms": ["kani-basami"]},
        "PX3": {"action": "do-jime", "type": "hansoku-make", "scope": "all", "terms": ["do-jime"]},
        "PX4": {"action": "illegal kansetsu-waza", "type": "hansoku-make", "scope": "all", "terms": ["illegal kansetsu-waza", "luxación ilegal"]},
        "PX7a": {"action": "dangerous action", "type": "hansoku-make", "scope": "all", "terms": ["dangerous action", "acción peligrosa"]},
        "PX7b": {"action": "kata-sankaku throw higher risk", "type": "hansoku-make", "scope": "all", "terms": ["kata-sankaku", "proyección con riesgo", "higher risk"]}
    }

    def __init__(self, evidence_passages: List[Dict[str, Any]], related_passages: Optional[List[Dict[str, Any]]] = None):
        self.evidence = evidence_passages or []
        self.related = related_passages or []
        self.all_passages = self.evidence + self.related

        # Precompile ground truth corpus representation
        self.ground_truth_text = " ".join([p.get("text_original", "") for p in self.all_passages])
        self.ground_truth_text_lower = self.ground_truth_text.lower()

        # Collect valid passage IDs
        self.valid_passage_ids = {
            p["passage_id"].upper() for p in self.all_passages if "passage_id" in p
        }

        # Collect valid article IDs from metadata and ground truth text
        self.valid_articles = set()
        for p in self.all_passages:
            art = str(p.get("article_id", "")).strip().lower()
            if art:
                cleaned_art = re.sub(r'^(?:article|art\.?)\s*', '', art)
                self.valid_articles.add(cleaned_art)
                self.valid_articles.add(art)
                # Add parent prefixes (e.g., if 18.1.3 is valid, 18.1 and 18 are also valid parent references)
                parts = cleaned_art.split(".")
                for i in range(1, len(parts)):
                    self.valid_articles.add(".".join(parts[:i]))

        # Also register any article numbers explicitly found in the ground truth text
        for a1, a2 in self.ARTICLE_PATTERN.findall(self.ground_truth_text):
            found_art = (a1 or a2).strip().lower()
            if found_art:
                self.valid_articles.add(found_art)
                parts = found_art.split(".")
                for i in range(1, len(parts)):
                    self.valid_articles.add(".".join(parts[:i]))

        # Collect valid penalty codes present in the retrieved passages
        self.valid_penalty_codes = {
            c.upper() for c in self.PENALTY_CODE_PATTERN.findall(self.ground_truth_text)
        }

    def validate_text(self, text: str) -> NormativeVerificationResult:
        """Inspects arbitrary response text for ungrounded normative claims."""
        if not text or not text.strip():
            return NormativeVerificationResult(True, [], [], [], [], [], [], [])

        hallucinated_codes = []
        hallucinated_articles = []
        hallucinated_passages = []
        unsupported_claims = []
        semantic_mismatches = []
        scope_violations = []
        warnings = []

        text_lower = text.lower()

        # 1. Structural Check: Verify Penalty Codes Existence
        found_codes = set(self.PENALTY_CODE_PATTERN.findall(text))
        for code in found_codes:
            code_upper = code.upper()
            if code_upper not in self.valid_penalty_codes:
                hallucinated_codes.append(code_upper)

        # 2. Structural Check: Verify Passage IDs Existence
        found_passages = set(self.PASSAGE_ID_PATTERN.findall(text))
        for pid in found_passages:
            pid_upper = pid.upper()
            if pid_upper not in self.valid_passage_ids:
                hallucinated_passages.append(pid_upper)

        # 3. Structural Check: Verify Article References Existence
        found_articles = self.ARTICLE_PATTERN.findall(text)
        for a1, a2 in found_articles:
            art = (a1 or a2).strip().lower()
            if not art:
                continue
            if (art not in self.valid_articles and 
                f"article {art}" not in self.ground_truth_text_lower and 
                f"art. {art}" not in self.ground_truth_text_lower and 
                f"art {art}" not in self.ground_truth_text_lower):
                hallucinated_articles.append(art)

        # 4. Procedural Check: Hallucinated Authorities or Disciplines
        for term in self.SUSPICIOUS_PROCEDURAL_TERMS:
            if term in text_lower and term not in self.ground_truth_text_lower:
                unsupported_claims.append(f"Mención de procedimiento o autoridad no sustentada: '{term}'")

        # 5. Semantic Check: Penalty Code Misassignment
        # Verify if an authentic code was assigned to an entirely mismatched action
        for code in found_codes:
            code_upper = code.upper()
            if code_upper in self.CANONICAL_PENALTY_MAP:
                mapping = self.CANONICAL_PENALTY_MAP[code_upper]
                # Check category scope extrapolation
                if mapping["scope"] == "cadet":
                    # If claiming this code applies to seniors or general without stating cadet restriction
                    if any(s in text_lower for s in ["senior", "seniors", "todas las categorías", "general"]) and not any(c in text_lower for c in ["cadet", "cadete", "cadetes"]):
                        scope_violations.append(
                            f"Código {code_upper} es exclusivo de cadetes ({mapping['action']}), pero se afirmó para seniors/general sin respaldo."
                        )

                # Check if the code was applied to a contrary action
                # E.g. PS34 is head defense; if applied to kani-basami or bear hug or false attack:
                mismatched = False
                if code_upper == "PS34" and any(k in text_lower for k in ["kani-basami", "kawazu-gake", "falso ataque", "false attack", "agarrar pierna"]):
                    if not any(t in text_lower for t in mapping["terms"]):
                        mismatched = True
                elif code_upper == "PX2" and not any(t in text_lower for t in ["kani-basami", "tijera"]):
                    if any(k in text_lower for k in ["falso ataque", "non combativity", "defensa con cabeza"]):
                        mismatched = True

                if mismatched:
                    semantic_mismatches.append(
                        f"Incoherencia semántica: El código {code_upper} corresponde reglamentariamente a '{mapping['action']}', pero se aplicó a una infracción distinta."
                    )

        # 6. Semantic Check: Extrapolation of age restrictions
        if "cadet" in self.ground_truth_text_lower and not ("senior" in self.ground_truth_text_lower):
            if re.search(r'\b(?:aplica también a seniors|válido para seniors y juniors|en todas las edades)\b', text_lower):
                scope_violations.append("Extrapolación no demostrada: La regla de la evidencia está restringida a cadetes pero se afirmó para seniors/todas las edades.")

        # 7. Semantic Check: Rigorous Shido Progression and Penalty Accumulation Rules
        # In SOR 2026-08 (Art. 18.1): 2 shido are warnings, the third (3rd) is hansoku-make.
        # Any assertion that a 2nd shido produces hansoku-make or disqualification is a critical normative error.
        second_shido_hm_patterns = [
            r'\b(?:segundo|segunda|2[º°]|2do|2da|second)\s+shido\s+(?:conlleva|provoca|resulta en|equivale a|conduce a|es|causa)\s+hansoku-make\b',
            r'\b(?:dos|2)\s+shidos?\s+(?:conllevan|conducen a|resultan en|equivalen a|causan)\s+hansoku-make\b',
            r'\bhansoku-make\s+(?:al|con el|tras el)\s+(?:segundo|2[º°]|2do|second)\s+shido\b',
            r'\bsecond\s+shido\s+(?:results in|leads to|is|causes)\s+hansoku-make\b',
            r'\btwo\s+shidos?\s+(?:result in|lead to|cause)\s+hansoku-make\b'
        ]
        for pat in second_shido_hm_patterns:
            if re.search(pat, text_lower):
                semantic_mismatches.append(
                    "Error normativo crítico en progresión de sanciones: En el SOR 2026-08 (Art. 18.1) se otorgan dos (2) Shidos de advertencia y es el TERCER (3er) Shido el que conduce a Hansoku-make, no el segundo."
                )
                break

        # 8. Procedural Check: Wasting time / untidy attire first occurrence warning
        # Under Art. 18.1.3 and Art. 18.1.5, the first occurrence of wasting time is a warning (NO shido).
        # Only the second and subsequent occurrences result in shido.
        if "wasting time" in text_lower or "perder tiempo" in text_lower or "perdiendo tiempo" in text_lower:
            if re.search(r'\b(?:primera vez|primera infracción|primer retraso|first occurrence|first time)\s+(?:se sanciona con|recibe|resulta en|es)\s+shido\b', text_lower):
                if not re.search(r'\b(?:advertencia|warning|no shido|sin shido)\b', text_lower):
                    semantic_mismatches.append(
                        "Infracción procedimental: Conforme al Art. 18.1.3 y Art. 18.1.5, la primera ocurrencia de pérdida de tiempo no conlleva sanción inmediata de Shido sino advertencia del árbitro."
                    )

        is_valid = not (
            hallucinated_codes or
            hallucinated_articles or
            hallucinated_passages or
            unsupported_claims or
            semantic_mismatches or
            scope_violations
        )

        return NormativeVerificationResult(
            is_valid=is_valid,
            unsupported_claims=unsupported_claims,
            hallucinated_codes=hallucinated_codes,
            hallucinated_articles=hallucinated_articles,
            hallucinated_passages=hallucinated_passages,
            semantic_mismatches=semantic_mismatches,
            scope_violations=scope_violations,
            warnings=warnings
        )

    def sanitize_structured_answer(self, structured_answer: Any) -> Any:
        """
        Validates and cleans a StructuredAnswer object.
        If unsupported claims, hallucinated codes, ungrounded articles,
        semantic mismatches, or scope violations are found:
        - Sanitizes text and neutralizes unverified assertions.
        - Injects explicit disclaimers and boundary warnings in `limitations`.
        """
        summary_verif = self.validate_text(structured_answer.summary)
        ext_verif = self.validate_text(structured_answer.extended_analysis)
        norm_verif = self.validate_text(structured_answer.normative_basis)

        all_hallucinated_codes = set(
            summary_verif.hallucinated_codes +
            ext_verif.hallucinated_codes +
            norm_verif.hallucinated_codes
        )
        all_hallucinated_articles = set(
            summary_verif.hallucinated_articles +
            ext_verif.hallucinated_articles +
            norm_verif.hallucinated_articles
        )
        all_hallucinated_passages = set(
            summary_verif.hallucinated_passages +
            ext_verif.hallucinated_passages +
            norm_verif.hallucinated_passages
        )
        all_unsupported_claims = (
            summary_verif.unsupported_claims +
            ext_verif.unsupported_claims +
            norm_verif.unsupported_claims
        )
        all_semantic_mismatches = (
            summary_verif.semantic_mismatches +
            ext_verif.semantic_mismatches +
            norm_verif.semantic_mismatches
        )
        all_scope_violations = (
            summary_verif.scope_violations +
            ext_verif.scope_violations +
            norm_verif.scope_violations
        )

        if not (
            all_hallucinated_codes or
            all_hallucinated_articles or
            all_hallucinated_passages or
            all_unsupported_claims or
            all_semantic_mismatches or
            all_scope_violations
        ):
            return structured_answer

        sanitized_summary = structured_answer.summary
        sanitized_extended = structured_answer.extended_analysis

        # Neutralize structural code hallucinations
        for code in all_hallucinated_codes:
            pattern = re.compile(rf'\b{re.escape(code)}\b', re.IGNORECASE)
            sanitized_summary = pattern.sub(f"[Código no verificado en evidencia]", sanitized_summary)
            sanitized_extended = pattern.sub(f"[Código no verificado en evidencia]", sanitized_extended)

        # Neutralize ungrounded articles
        for art in all_hallucinated_articles:
            pattern = re.compile(rf'\b(?:Art(?:ículo|\.|\s+)?\s*{re.escape(art)}|Article\s*{re.escape(art)})\b', re.IGNORECASE)
            sanitized_summary = pattern.sub(f"[Art. {art} no presente en contexto oficial]", sanitized_summary)
            sanitized_extended = pattern.sub(f"[Art. {art} no presente en contexto oficial]", sanitized_extended)

        # Filter out hallucinated passages from citations list
        if structured_answer.citations:
            structured_answer.citations = [
                c for c in structured_answer.citations if c.upper() not in all_hallucinated_passages
            ]

        # Compile explicit limitations notes
        limitation_notes = []
        if all_hallucinated_codes:
            limitation_notes.append(f"Códigos no respaldados en los pasajes recuperados: {', '.join(sorted(all_hallucinated_codes))}.")
        if all_hallucinated_articles:
            limitation_notes.append(f"Artículos invocados sin respaldo en los pasajes certificados: {', '.join(sorted(all_hallucinated_articles))}.")
        if all_unsupported_claims:
            limitation_notes.append(f"Procedimientos o autoridades no sustentados en los pasajes oficiales: {'; '.join(all_unsupported_claims)}.")
        if all_semantic_mismatches:
            limitation_notes.append(f"Inconsistencia semántica detectada: {'; '.join(all_semantic_mismatches)}.")
        if all_scope_violations:
            limitation_notes.append(f"Discrepancia de categoría o ámbito: {'; '.join(all_scope_violations)}.")

        boundary_warning = (
            "> ⚠️ **Control de Rigor Normativo:** Se detectaron afirmaciones o referencias "
            "que no figuran o presentan discrepancias con los pasajes normativos certificados recuperados. "
            f"{' '.join(limitation_notes)} Conforme a la política de rigor del SOR 2026, "
            "estas afirmaciones no se certifican como hechos oficiales."
        )

        existing_limits = structured_answer.limitations.strip()
        if existing_limits:
            structured_answer.limitations = f"{existing_limits}\n\n{boundary_warning}"
        else:
            structured_answer.limitations = boundary_warning

        structured_answer.summary = sanitized_summary
        structured_answer.extended_analysis = sanitized_extended
        return structured_answer

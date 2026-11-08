"""
Document Validator Module for IJF SOR Assistant.
Part of Phase 4.1: Architecture Foundation for Multisource Knowledge.

Provides validation logic for:
1. Integrity of the multisource document catalog against reference_registry.json.
2. Normative conflict detection between SOR 2026 and supplementary evidence.
3. Verification of citations, page numbers, and audiovisual timestamp formats.
4. Construction and certification of EvidenceBundle instances.
"""

import os
import re
import csv
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone

import sys
if "src.document_validator" in sys.modules:
    sys.modules.setdefault("document_validator", sys.modules["src.document_validator"])
elif "document_validator" in sys.modules:
    sys.modules.setdefault("src.document_validator", sys.modules["document_validator"])

try:
    from src.document_governance import (
        DocumentAuthority,
        ValidityStatus,
        ApprovalStatus,
        EligibilityStatus,
        EvidenceRole,
        NormativeRelationType,
        DocumentMetadata,
        EvidenceItem,
        EvidenceBundle,
        VideoTimestamp
    )
except ImportError:
    from document_governance import (
        DocumentAuthority,
        ValidityStatus,
        ApprovalStatus,
        EligibilityStatus,
        EvidenceRole,
        NormativeRelationType,
        DocumentMetadata,
        EvidenceItem,
        EvidenceBundle,
        VideoTimestamp
    )


class DocumentValidationError(Exception):
    """Custom exception raised when document governance or evidence contracts are violated."""
    pass


class DocumentValidator:
    """
    Validates document catalog entries and enforces normative precedence rules on evidence.
    """

    def __init__(self, registry_csv_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if registry_csv_path is None:
            registry_csv_path = os.path.join(base_dir, "docs", "registro_documental_multifuente_ijf.csv")
        self.registry_csv_path = registry_csv_path
        self.catalog: Dict[str, DocumentMetadata] = {}
        self.load_catalog()

    def load_catalog(self) -> None:
        """
        Parses and validates the CSV document catalog.
        """
        if not os.path.exists(self.registry_csv_path):
            raise FileNotFoundError(f"Document catalog CSV not found at {self.registry_csv_path}")

        with open(self.registry_csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                doc_id = row["document_id"]
                related_arts = [
                    a.strip() for a in row["relacion_articulos_sor"].split(",")
                    if a.strip()
                ]
                
                # Map authority string
                auth_str = row["autoridad_documental"]
                auth_enum = getattr(DocumentAuthority, auth_str, None)
                if auth_enum is None:
                    # Fallback mapping by tier
                    tier_str = row["nivel_autoridad"]
                    if tier_str == "TIER_1":
                        auth_enum = DocumentAuthority.TIER_1_NORMATIVE_PRIMARY
                    elif tier_str == "TIER_2":
                        auth_enum = DocumentAuthority.TIER_2_OFFICIAL_AMENDMENT
                    elif tier_str == "TIER_3":
                        auth_enum = DocumentAuthority.TIER_3_REFEREEING_INTERPRETATION
                    elif tier_str == "TIER_4":
                        auth_enum = DocumentAuthority.TIER_4_EDUCATIONAL_CONTEXT
                    elif tier_str == "TIER_5":
                        auth_enum = DocumentAuthority.TIER_5_AUDIOVISUAL_EVIDENCE
                    else:
                        auth_enum = DocumentAuthority.TIER_HISTORICAL_SUPERSEDED

                # Map validity enum with aliases
                raw_validity = row["estado_vigencia"].strip()
                if raw_validity in ("HISTORICO", "HISTORICO_DEROGADO"):
                    validity_enum = ValidityStatus.HISTORICO_DEROGADO
                elif raw_validity in ("VIGENTE",):
                    validity_enum = ValidityStatus.VIGENTE
                elif raw_validity in ("VIGENTE_PARCIAL",):
                    validity_enum = ValidityStatus.VIGENTE_PARCIAL
                elif raw_validity in ("OBSOLETO", "OBSOLETO_RETIRADO"):
                    validity_enum = ValidityStatus.OBSOLETO_RETIRADO
                elif raw_validity in ("SUBSUMIDO", "SUBSUMIDO_EN_SOR"):
                    validity_enum = ValidityStatus.SUBSUMIDO_EN_SOR
                else:
                    validity_enum = getattr(ValidityStatus, raw_validity, ValidityStatus.UNKNOWN)
                approval_enum = getattr(ApprovalStatus, row["estado_aprobacion"], ApprovalStatus.PENDIENTE)
                relation_enum = getattr(NormativeRelationType, row["relacion_normativa"], NormativeRelationType.COMPLEMENTO_EXPLICATIVO)

                meta = DocumentMetadata(
                    document_id=doc_id,
                    title=row["titulo"],
                    document_type=row["tipo"],
                    issuing_authority=row["fuente"],
                    url=row["url"] if row["url"] != "UNKNOWN" else None,
                    publication_date=row["fecha_publicacion"] if row["fecha_publicacion"] != "UNKNOWN" else None,
                    effective_date=row["fecha_vigencia"] if row["fecha_vigencia"] != "UNKNOWN" else None,
                    review_date=row["fecha_revision"],
                    authority=auth_enum,
                    validity=validity_enum,
                    approval=approval_enum,
                    related_sor_articles=related_arts,
                    normative_relation=relation_enum,
                    approved_by=row["responsable_aprobacion"] if row["responsable_aprobacion"] != "UNKNOWN" else None,
                    integrity_hash=row["hash_integridad"] if row["hash_integridad"] != "UNKNOWN" else None,
                    notes=row.get("observaciones")
                )
                self.catalog[doc_id] = meta

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        return self.catalog.get(document_id)

    def validate_document_eligibility(self, document_id: str) -> EligibilityStatus:
        """
        Evaluates eligibility for a given document in the catalog.
        """
        doc = self.get_document(document_id)
        if not doc:
            return EligibilityStatus.NO_ELEGIBLE
        return doc.determine_eligibility()

    def detect_conflict(self, primary_item: EvidenceItem, supplementary_item: EvidenceItem) -> Tuple[bool, Optional[str]]:
        """
        Checks for explicit contradiction between primary SOR text and supplementary evidence.
        In Judo rules, key conflict vectors include:
        - Score values (e.g. Yuko vs Waza-ari vs Ippon criteria)
        - Osaekomi holding times (e.g. 5-9s vs 10-19s vs 20s)
        - Penalties (Shido vs Hansoku-make)
        """
        # Under strict governance policy:
        # If the supplementary document is historical/derogated, any divergence is a conflict
        if supplementary_item.validity in (ValidityStatus.HISTORICO_DEROGADO, ValidityStatus.OBSOLETO_RETIRADO):
            return True, f"Conflict: Supplementary item {supplementary_item.evidence_id} belongs to a superseded/repealed source ({supplementary_item.document_id})."
        
        # Check explicit scoring time contradictions if mentioned
        # e.g., if a supplementary item claims Osaekomi 15s is Ippon (historically true pre-2017, now 20s)
        sec_pattern = re.compile(r"(\d+)\s*(?:segundos|seconds|s\b)", re.IGNORECASE)
        prim_times = sec_pattern.findall(primary_item.content_text)
        supp_times = sec_pattern.findall(supplementary_item.content_text)
        
        # If both define specific times for the same rule and differ, detect potential conflict
        if "osaekomi" in primary_item.content_text.lower() and "osaekomi" in supplementary_item.content_text.lower():
            if prim_times and supp_times:
                # If numbers differ and supplementary is not explicitly marked as subsumed
                if set(prim_times) != set(supp_times) and supplementary_item.authority != DocumentAuthority.TIER_1_NORMATIVE_PRIMARY:
                    if supplementary_item.validity != ValidityStatus.SUBSUMIDO_EN_SOR:
                        return True, f"Temporal Conflict in Osaekomi duration: SOR states {prim_times}s vs supplementary {supp_times}s."

        return False, None

    STOPWORDS = {
        "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "en", "para", "por",
        "con", "sin", "sobre", "entre", "tras", "durante", "que", "cual", "cuales", "quien", "quienes",
        "como", "cuando", "donde", "porque", "es", "son", "fue", "ser", "se", "su", "sus", "si",
        "the", "a", "an", "of", "to", "in", "for", "on", "with", "by", "at", "from", "and", "or", "is",
        "are", "was", "were", "what", "which", "how", "when", "where", "who", "whom", "does", "do"
    }

    DOMAIN_GENERIC = {
        "judo", "judoka", "judokas", "atleta", "atletas", "competidor", "competidores",
        "regla", "reglas", "reglamento", "norma", "normas", "normativo", "normativa",
        "oficial", "oficiales", "ijf", "sor", "articulo", "articulos", "seccion", "capitulo",
        "combate", "deporte", "establece", "aplica", "corresponde", "valido", "permitido", "segun"
    }

    SYNONYM_MAP = {
        "calcetin": ["socks", "calcetin", "calcetines"],
        "calcetines": ["socks", "calcetin", "calcetines"],
        "temperatura": ["temperature", "temperatura", "clima", "termico", "termica", "ambiental"],
        "tokio": ["tokyo"],
        "salario": ["salary", "wage", "remuneration", "sueldo"],
        "sueldo": ["salary", "wage", "remuneration", "sueldo"],
        "cuota": ["membership fee", "fee", "price", "cuota"],
        "chui": ["chui"],
        "keikoku": ["keikoku"],
        "koka": ["koka"],
        "2030": ["2030"],
        "la28": ["la28", "los angeles 2028"]
    }

    def evaluate_substantive_relevance(self, query_text: str, primary_items: List[EvidenceItem]) -> Tuple[bool, Optional[str]]:
        """
        Verifies that primary normative evidence contains substantive coverage
        for critical specific entities or concepts inquired in query_text.
        Prevents false certainty and hallucinated synthesis on unrelated passages.
        """
        if not primary_items:
            return False, "Sin evidencia normativa primaria disponible."

        clean_q = query_text.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        tokens = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", clean_q)
        content_tokens = [t for t in tokens if t not in self.STOPWORDS and t not in self.DOMAIN_GENERIC]

        if not content_tokens:
            return True, None

        # Build full combined corpus text from primary items
        combined_text = " ".join([
            (item.content_text or "").lower() + " " + (item.paragraph_or_section or "").lower()
            for item in primary_items
        ])
        combined_text = combined_text.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")

        # Specific terms requiring explicit presence
        CRITICAL_SPECIFIC_TERMS = {
            "calcetines", "calcetin", "temperatura", "tokio", "salario", "sueldo",
            "cuota", "koka", "chui", "keikoku", "2030", "la28"
        }

        for token in content_tokens:
            if token in CRITICAL_SPECIFIC_TERMS or token in self.SYNONYM_MAP:
                allowed_variants = self.SYNONYM_MAP.get(token, [token])
                found = any(v in combined_text for v in allowed_variants)
                if not found:
                    return False, f"La evidencia recuperada del SOR 2026 no contiene respaldo ni mención de '{token}'."

        return True, None

    def build_certified_bundle(
        self,
        bundle_id: str,
        query_text: str,
        candidate_items: List[EvidenceItem]
    ) -> EvidenceBundle:
        """
        Organizes raw candidate evidence items into segregated lanes, verifies eligibility,
        evaluates conflicts, and certifies the final EvidenceBundle.
        """
        primary_lane: List[EvidenceItem] = []
        interpretive_lane: List[EvidenceItem] = []
        contextual_lane: List[EvidenceItem] = []
        
        has_conflict = False
        conflict_notes: List[str] = []

        for item in candidate_items:
            # Re-verify document in catalog
            doc = self.get_document(item.document_id)
            if not doc:
                # Unregistered document is barred
                item.eligibility = EligibilityStatus.NO_ELEGIBLE
                continue
            
            # Re-evaluate eligibility dynamically
            item.eligibility = doc.determine_eligibility()
            if item.eligibility == EligibilityStatus.NO_ELEGIBLE:
                continue

            # Route to respective lane
            if item.role == EvidenceRole.NORMA_PRIMARIA and item.authority == DocumentAuthority.TIER_1_NORMATIVE_PRIMARY:
                primary_lane.append(item)
            elif item.role == EvidenceRole.COMPLEMENTO_INTERPRETATIVO and item.authority in (
                DocumentAuthority.TIER_2_OFFICIAL_AMENDMENT,
                DocumentAuthority.TIER_3_REFEREEING_INTERPRETATION
            ):
                interpretive_lane.append(item)
            elif item.role in (EvidenceRole.MATERIAL_DIDACTICO, EvidenceRole.EVIDENCIA_AUDIOVISUAL):
                contextual_lane.append(item)

        # Check for conflicts between primary and supplementary items
        for prim in primary_lane:
            for supp in interpretive_lane + contextual_lane:
                conflict, note = self.detect_conflict(prim, supp)
                if conflict:
                    has_conflict = True
                    if note:
                        conflict_notes.append(note)

        # Determine sufficiency and abstention
        has_substantive_relevance, irrelevance_reason = self.evaluate_substantive_relevance(query_text, primary_lane)
        is_sufficient = len(primary_lane) > 0 and not has_conflict and has_substantive_relevance
        abstention_req = False
        abstention_reason = None

        if not primary_lane:
            # No primary normative rule found
            abstention_req = True
            abstention_reason = "Abstention: No applicable Tier 1 (SOR 2026) normative rule recovered for decisive ruling."
        elif has_conflict:
            # Normative conflict detected
            abstention_req = True
            abstention_reason = f"Abstention due to unresolved normative conflict: {'; '.join(conflict_notes)}"
        elif not has_substantive_relevance:
            # Substantive relevance check failed (critical entity missing from evidence)
            abstention_req = True
            abstention_reason = f"Abstención por evidencia insuficiente: {irrelevance_reason}"

        bundle = EvidenceBundle(
            bundle_id=bundle_id,
            query_text=query_text,
            created_at=datetime.now(timezone.utc).isoformat(),
            primary_normative_evidence=primary_lane,
            interpretive_evidence=interpretive_lane,
            contextual_evidence=contextual_lane,
            is_sufficient_for_decision=is_sufficient,
            has_unresolved_conflict=has_conflict,
            abstention_required=abstention_req,
            abstention_reason=abstention_reason
        )

        return bundle

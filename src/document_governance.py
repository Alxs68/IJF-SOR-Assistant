import sys
if "src.document_governance" in sys.modules:
    sys.modules.setdefault("document_governance", sys.modules["src.document_governance"])
elif "document_governance" in sys.modules:
    sys.modules.setdefault("src.document_governance", sys.modules["document_governance"])
"""
Document Governance, Authority Enums, and Typed Evidence Contracts for IJF SOR Assistant.
Part of Phase 4.1: Architecture Foundation for Multisource Knowledge.

Provides strict separation between:
1. Document Authority (Legal/Regulatory status)
2. Document Validity (Temporal effectiveness)
3. Retrieval Eligibility (System gating)
4. Semantic Relevance (Query-evidence matching score)
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import date
from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# 1. ENUMS FOR SEPARATE GOVERNANCE DIMENSIONS
# ============================================================================

class DocumentAuthority(str, Enum):
    """
    Legal and regulatory authority of the document source within IJF ecosystem.
    Must never be combined with relevance or validity into a single scalar score.
    """
    TIER_1_NORMATIVE_PRIMARY = "TIER_1_NORMATIVE_PRIMARY"     # SOR 2026-08 exclusively
    TIER_2_OFFICIAL_AMENDMENT = "TIER_2_OFFICIAL_AMENDMENT"   # Binding circulars / Executive orders
    TIER_3_REFEREEING_INTERPRETATION = "TIER_3_REFEREEING_INTERPRETATION"  # Refereeing Commission clarifications (e.g. PPT-002)
    TIER_4_EDUCATIONAL_CONTEXT = "TIER_4_EDUCATIONAL_CONTEXT" # rules.ijf.org, educational slides, IT manuals
    TIER_5_AUDIOVISUAL_EVIDENCE = "TIER_5_AUDIOVISUAL_EVIDENCE" # Video clips, demonstration transcripts
    TIER_HISTORICAL_SUPERSEDED = "TIER_HISTORICAL_SUPERSEDED" # Past SOR editions (e.g. DOC-001 Jan 2026)


class ValidityStatus(str, Enum):
    """
    Temporal validity of the document relative to the active SOR edition (2026-08-14).
    """
    VIGENTE = "VIGENTE"                             # Fully active and applicable
    VIGENTE_PARCIAL = "VIGENTE_PARCIAL"             # Partially active, specific clauses retained
    SUBSUMIDO_EN_SOR = "SUBSUMIDO_EN_SOR"           # Subsumed into active SOR text
    HISTORICO_DEROGADO = "HISTORICO_DEROGADO"       # Formally superseded / repealed
    OBSOLETO_RETIRADO = "OBSOLETO_RETIRADO"         # Deleted, unplayable or retracted
    UNKNOWN = "UNKNOWN"                             # Unverified status


class ApprovalStatus(str, Enum):
    """
    Formal editorial/governance sign-off status before a document can be indexed.
    """
    APROBADO = "APROBADO"                                   # Fully approved by designated authority
    APROBADO_CONDICIONADO = "APROBADO_CONDICIONADO"         # Approved for contextual/interpretive use only
    PENDIENTE = "PENDIENTE"                                 # Pending human curatorial sign-off
    RECHAZADO = "RECHAZADO"                                 # Rejected for retrieval use
    ARCHIVADO = "ARCHIVADO"                                 # Archived for audit trail only


class EligibilityStatus(str, Enum):
    """
    Technical eligibility gating for RRE retrieval pipeline.
    Determined deterministically from Authority, Validity, and Approval.
    """
    ELIGIBLE_DECISORIA = "ELIGIBLE_DECISORIA"       # Can serve as decisive normative baseline (Tier 1 exclusively)
    ELIGIBLE_INTERPRETATIVA = "ELIGIBLE_INTERPRETATIVA" # Can serve as interpretive complement (Tier 2/3 approved)
    ELIGIBLE_CONTEXTUAL = "ELIGIBLE_CONTEXTUAL"     # Can serve as visual or educational context (Tier 4/5 approved)
    NO_ELEGIBLE = "NO_ELEGIBLE"                     # Gated out of retrieval entirely (Unapproved, revoked or superseded)


class EvidenceRole(str, Enum):
    """
    Functional role of a specific evidence item in answering a user query.
    """
    NORMA_PRIMARIA = "NORMA_PRIMARIA"               # Binding SOR rule text
    COMPLEMENTO_INTERPRETATIVO = "COMPLEMENTO_INTERPRETATIVO" # Clarification of tactical application
    EVIDENCIA_AUDIOVISUAL = "EVIDENCIA_AUDIOVISUAL" # Visual demonstration of the action
    MATERIAL_DIDACTICO = "MATERIAL_DIDACTICO"       # Pedagogical explanation or diagram


class NormativeRelationType(str, Enum):
    """
    Relationship between a supplementary source and the primary SOR.
    """
    ORIGINAL_SUPREMO = "ORIGINAL_SUPREMO"
    SUBSUMIDO_TOTALMENTE = "SUBSUMIDO_TOTALMENTE"
    SUBSUMIDO_PARCIALMENTE = "SUBSUMIDO_PARCIALMENTE"
    COMPLEMENTO_OPERATIVO = "COMPLEMENTO_OPERATIVO"
    COMPLEMENTO_EXPLICATIVO = "COMPLEMENTO_EXPLICATIVO"
    ANTECEDENTE_DEROGADO = "ANTECEDENTE_DEROGADO"
    EVIDENCIA_AUDIOVISUAL = "EVIDENCIA_AUDIOVISUAL"


# ============================================================================
# 2. DOCUMENT INVENTORY AND METADATA CONTRACTS
# ============================================================================

class DocumentMetadata(BaseModel):
    """
    Metadata specification for any document registered in the multisource catalog.
    """
    document_id: str = Field(..., description="Unique canonical document ID (e.g. DOC-SOR-2026-08, PPT-002)")
    title: str = Field(..., description="Official title of the document or media")
    document_type: str = Field(..., description="Media type (PDF, Web, Slides, Video, Markdown)")
    issuing_authority: str = Field(..., description="Issuing body (e.g. IJF Executive Committee, IJF Refereeing Commission)")
    url: Optional[str] = Field(None, description="Official resolvable URL or UNKNOWN")
    publication_date: Optional[str] = Field(None, description="Publication date (YYYY-MM-DD) or UNKNOWN")
    effective_date: Optional[str] = Field(None, description="Effective date (YYYY-MM-DD) or UNKNOWN")
    review_date: str = Field("2026-11-05", description="Last audit review date")
    
    # Governance dimensions (Must remain separate)
    authority: DocumentAuthority = Field(..., description="Regulatory authority tier")
    validity: ValidityStatus = Field(..., description="Temporal validity status")
    approval: ApprovalStatus = Field(..., description="Editorial governance approval status")
    
    # Normative mappings
    related_sor_articles: List[str] = Field(default_factory=list, description="Associated SOR articles")
    normative_relation: NormativeRelationType = Field(..., description="Nature of relation to SOR")
    approved_by: Optional[str] = Field(None, description="Role or entity approving inclusion")
    integrity_hash: Optional[str] = Field(None, description="SHA-256 hash if local file exists")
    notes: Optional[str] = Field(None, description="Audit observations or caveats")

    def determine_eligibility(self) -> EligibilityStatus:
        """
        Deterministic gating logic based on authority, validity, and approval.
        """
        # Block unapproved, rejected, or archived
        if self.approval in (ApprovalStatus.PENDIENTE, ApprovalStatus.RECHAZADO, ApprovalStatus.ARCHIVADO):
            return EligibilityStatus.NO_ELEGIBLE
        
        # Block revoked, superseded, or obsolete
        if self.validity in (ValidityStatus.HISTORICO_DEROGADO, ValidityStatus.OBSOLETO_RETIRADO):
            return EligibilityStatus.NO_ELEGIBLE
        
        # Decisive normative rule is restricted to Tier 1
        if self.authority == DocumentAuthority.TIER_1_NORMATIVE_PRIMARY:
            return EligibilityStatus.ELIGIBLE_DECISORIA
        
        # Interpretive supplements
        if self.authority in (DocumentAuthority.TIER_2_OFFICIAL_AMENDMENT, DocumentAuthority.TIER_3_REFEREEING_INTERPRETATION):
            return EligibilityStatus.ELIGIBLE_INTERPRETATIVA
        
        # Visual / Contextual
        if self.authority in (DocumentAuthority.TIER_4_EDUCATIONAL_CONTEXT, DocumentAuthority.TIER_5_AUDIOVISUAL_EVIDENCE):
            return EligibilityStatus.ELIGIBLE_CONTEXTUAL
        
        return EligibilityStatus.NO_ELEGIBLE


# ============================================================================
# 3. EVIDENCE ITEM AND EVIDENCE BUNDLE CONTRACTS
# ============================================================================

class VideoTimestamp(BaseModel):
    """
    Strictly verified timestamp for audiovisual demonstrations.
    Must never be invented or hallucinated by LLM.
    """
    timestamp_start: str = Field(..., pattern=r"^\d{2}:\d{2}:\d{2}$", description="Start time HH:MM:SS")
    timestamp_end: str = Field(..., pattern=r"^\d{2}:\d{2}:\d{2}$", description="End time HH:MM:SS")
    is_verified: bool = Field(False, description="Whether the timestamp has been human-curated and verified")
    curator_notes: Optional[str] = Field(None, description="Notes from human curator verifying the clip")


class EvidenceItem(BaseModel):
    """
    Atomic unit of retrieved evidence supporting an arbitration query.
    Carries complete provenance and strictly separated governance dimensions.
    """
    evidence_id: str = Field(..., description="Unique ID for this evidence unit (e.g. CHK-SOR-ART15-001)")
    document_id: str = Field(..., description="Reference document ID")
    content_text: str = Field(..., min_length=1, description="Exact textual content or excerpt")
    role: EvidenceRole = Field(..., description="Assigned role: primary norm, interpretation, or context")
    
    # Governance dimensions (Preserved distinctly)
    authority: DocumentAuthority = Field(..., description="Document authority tier")
    validity: ValidityStatus = Field(..., description="Temporal validity")
    eligibility: EligibilityStatus = Field(..., description="Pipeline eligibility gating")
    semantic_relevance_score: float = Field(..., ge=0.0, le=1.0, description="Semantic match score (0.0 to 1.0)")

    # Provenance and locators
    article_number: Optional[str] = Field(None, description="SOR Article number if applicable (e.g. Art. 15)")
    page_number: Optional[int] = Field(None, ge=1, le=500, description="Physical page number in official PDF")
    paragraph_or_section: Optional[str] = Field(None, description="Section heading or paragraph locator")
    url_reference: Optional[str] = Field(None, description="Direct URL if available")
    audiovisual_locators: Optional[VideoTimestamp] = Field(None, description="Verified timestamp if video evidence")

    @model_validator(mode="after")
    def validate_normative_integrity(self) -> "EvidenceItem":
        """
        Enforce strict normative boundary invariants:
        1. If role is NORMA_PRIMARIA, authority MUST be TIER_1_NORMATIVE_PRIMARY.
        2. If authority is TIER_5_AUDIOVISUAL_EVIDENCE, role CANNOT be NORMA_PRIMARIA.
        3. If audiovisual evidence, timestamp must be present and verified to be eligible.
        """
        # Rule 1: Only Tier 1 can be primary normative evidence
        if self.role == EvidenceRole.NORMA_PRIMARIA:
            if self.authority != DocumentAuthority.TIER_1_NORMATIVE_PRIMARY:
                raise ValueError(
                    f"Integrity Violation: Only Tier 1 (SOR 2026) can serve as NORMA_PRIMARIA. "
                    f"Got {self.authority} for evidence {self.evidence_id}."
                )
        
        # Rule 2: Video evidence can never be primary norm
        if self.authority == DocumentAuthority.TIER_5_AUDIOVISUAL_EVIDENCE:
            if self.role == EvidenceRole.NORMA_PRIMARIA:
                raise ValueError(
                    f"Integrity Violation: Audiovisual evidence ({self.evidence_id}) cannot be declared as NORMA_PRIMARIA."
                )
        
        # Rule 3: Unverified timestamps cannot be eligible contextual evidence
        if self.audiovisual_locators and not self.audiovisual_locators.is_verified:
            if self.eligibility != EligibilityStatus.NO_ELEGIBLE:
                raise ValueError(
                    f"Integrity Violation: Evidence {self.evidence_id} has unverified video timestamp but is marked eligible."
                )
        
        return self


class EvidenceBundle(BaseModel):
    """
    Structured typed collection of evidence assembled to resolve an arbitration query.
    Encapsulates multi-tier evidence, enforces normative precedence, and tracks validation status.
    """
    bundle_id: str = Field(..., description="Unique bundle identifier")
    query_text: str = Field(..., min_length=1, description="Original user query")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    
    # Segregated evidence lanes
    primary_normative_evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Tier 1 SOR evidence items (Ground truth rules)"
    )
    interpretive_evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Tier 2/3 official interpretations and seminar clarifications"
    )
    contextual_evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Tier 4/5 educational diagrams and verified audiovisual clips"
    )

    # Validation and gating summary
    is_sufficient_for_decision: bool = Field(
        False,
        description="True only if primary normative evidence exists and satisfies the query"
    )
    has_unresolved_conflict: bool = Field(
        False,
        description="True if supplementary evidence contradicts primary normative evidence"
    )
    abstention_required: bool = Field(
        False,
        description="True if evidence is insufficient or contradictory, requiring ADA abstention"
    )
    abstention_reason: Optional[str] = Field(
        None,
        description="Explicit explanation if abstention is triggered"
    )

    def total_evidence_count(self) -> int:
        return (
            len(self.primary_normative_evidence) +
            len(self.interpretive_evidence) +
            len(self.contextual_evidence)
        )

    @model_validator(mode="after")
    def validate_bundle_governance(self) -> "EvidenceBundle":
        """
        Validate multi-source bundle governance rules:
        1. If primary evidence is missing for a decisive query, is_sufficient_for_decision must be False.
        2. If has_unresolved_conflict is True, abstention_required must be True.
        3. All items in primary_normative_evidence must have role NORMA_PRIMARIA.
        4. Items with NO_ELEGIBLE must not be present in active lanes.
        """
        # Invariant 1: Ensure active lanes contain only eligible items
        for item in self.primary_normative_evidence + self.interpretive_evidence + self.contextual_evidence:
            if item.eligibility == EligibilityStatus.NO_ELEGIBLE:
                raise ValueError(
                    f"Bundle Violation: Ineligible evidence item {item.evidence_id} found in active bundle lane."
                )

        # Invariant 2: Primary lane integrity
        for item in self.primary_normative_evidence:
            if item.role != EvidenceRole.NORMA_PRIMARIA or item.authority != DocumentAuthority.TIER_1_NORMATIVE_PRIMARY:
                raise ValueError(
                    f"Bundle Violation: Non-Tier-1 item {item.evidence_id} in primary_normative_evidence."
                )

        # Invariant 3: Sufficiency requires primary evidence
        if not self.primary_normative_evidence and self.is_sufficient_for_decision:
            raise ValueError(
                "Bundle Violation: is_sufficient_for_decision cannot be True without primary normative evidence."
            )

        # Invariant 4: Unresolved conflict triggers mandatory abstention
        if self.has_unresolved_conflict and not self.abstention_required:
            raise ValueError(
                "Bundle Violation: An unresolved normative conflict requires mandatory abstention."
            )

        return self

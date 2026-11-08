"""
Unit tests for Document Governance, Inventory, and Evidence Contracts (Phase 4.1).
Validates:
1. Valid SOR normative evidence.
2. Valid supplementary interpretive evidence.
3. Valid contextual and audiovisual evidence.
4. Rejection of unapproved or pending documents.
5. Rejection of expired/repealed documents (DOC-001).
6. Normative conflict detection and mandatory abstention.
7. Validation of locator format, missing metadata, and invalid document references.
8. Audiovisual timestamp verification gating.
"""

import pytest
from pydantic import ValidationError

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
from src.document_validator import DocumentValidator, DocumentValidationError


@pytest.fixture
def validator():
    return DocumentValidator()


# ============================================================================
# 1. VALID EVIDENCE CREATION TESTS
# ============================================================================

def test_valid_sor_normative_evidence():
    """Verify that Tier 1 SOR evidence is correctly accepted as NORMA_PRIMARIA."""
    item = EvidenceItem(
        evidence_id="CHK-SOR-ART15-001",
        document_id="DOC-SOR-2026-08",
        content_text="Waza-ari is awarded when a contestant throws his opponent with control, lacking one of the Ippon elements.",
        role=EvidenceRole.NORMA_PRIMARIA,
        authority=DocumentAuthority.TIER_1_NORMATIVE_PRIMARY,
        validity=ValidityStatus.VIGENTE,
        eligibility=EligibilityStatus.ELIGIBLE_DECISORIA,
        semantic_relevance_score=0.92,
        article_number="Art. 15",
        page_number=168
    )
    assert item.evidence_id == "CHK-SOR-ART15-001"
    assert item.role == EvidenceRole.NORMA_PRIMARIA
    assert item.authority == DocumentAuthority.TIER_1_NORMATIVE_PRIMARY


def test_valid_supplementary_evidence():
    """Verify that Tier 3 seminar clarification is accepted as COMPLEMENTO_INTERPRETATIVO."""
    item = EvidenceItem(
        evidence_id="CHK-PPT002-001",
        document_id="PPT-002",
        content_text="Transition to Ne-waza must be immediate and continuous without pausing or dragging the opponent down without technique.",
        role=EvidenceRole.COMPLEMENTO_INTERPRETATIVO,
        authority=DocumentAuthority.TIER_3_REFEREEING_INTERPRETATION,
        validity=ValidityStatus.VIGENTE,
        eligibility=EligibilityStatus.ELIGIBLE_INTERPRETATIVA,
        semantic_relevance_score=0.88,
        article_number="Art. 16",
        paragraph_or_section="Slide 14 - Continuous Transition"
    )
    assert item.role == EvidenceRole.COMPLEMENTO_INTERPRETATIVO
    assert item.authority == DocumentAuthority.TIER_3_REFEREEING_INTERPRETATION


def test_valid_audiovisual_evidence():
    """Verify that Tier 5 video demonstration with verified timestamp is accepted as EVIDENCIA_AUDIOVISUAL."""
    ts = VideoTimestamp(
        timestamp_start="00:01:14",
        timestamp_end="00:01:45",
        is_verified=True,
        curator_notes="Clear 90-degree lateral fall onto side of shoulder."
    )
    item = EvidenceItem(
        evidence_id="CHK-VID003-001",
        document_id="VID-003",
        content_text="Video clip demonstrating lateral fall at 90 degrees.",
        role=EvidenceRole.EVIDENCIA_AUDIOVISUAL,
        authority=DocumentAuthority.TIER_5_AUDIOVISUAL_EVIDENCE,
        validity=ValidityStatus.VIGENTE,
        eligibility=EligibilityStatus.ELIGIBLE_CONTEXTUAL,
        semantic_relevance_score=0.85,
        audiovisual_locators=ts
    )
    assert item.role == EvidenceRole.EVIDENCIA_AUDIOVISUAL
    assert item.audiovisual_locators.is_verified is True


# ============================================================================
# 2. INTEGRITY POLICY & PROHIBITION TESTS
# ============================================================================

def test_prohibition_video_as_norma_primaria():
    """Video evidence CANNOT be declared as NORMA_PRIMARIA under any circumstance."""
    with pytest.raises(ValidationError) as exc_info:
        EvidenceItem(
            evidence_id="CHK-VID-ERR-001",
            document_id="VID-002",
            content_text="Referee video clip",
            role=EvidenceRole.NORMA_PRIMARIA,  # VIOLATION
            authority=DocumentAuthority.TIER_5_AUDIOVISUAL_EVIDENCE,
            validity=ValidityStatus.VIGENTE,
            eligibility=EligibilityStatus.ELIGIBLE_DECISORIA,
            semantic_relevance_score=0.90
        )
    assert "Audiovisual evidence" in str(exc_info.value) or "Only Tier 1" in str(exc_info.value)


def test_prohibition_tier2_as_norma_primaria():
    """Supplementary amendment (Tier 2/3) CANNOT be declared as NORMA_PRIMARIA."""
    with pytest.raises(ValidationError) as exc_info:
        EvidenceItem(
            evidence_id="CHK-NEW-ERR-001",
            document_id="NEW-001",
            content_text="Clarification of Reverse Seoi-nage",
            role=EvidenceRole.NORMA_PRIMARIA,  # VIOLATION
            authority=DocumentAuthority.TIER_2_OFFICIAL_AMENDMENT,
            validity=ValidityStatus.VIGENTE,
            eligibility=EligibilityStatus.ELIGIBLE_DECISORIA,
            semantic_relevance_score=0.95
        )
    assert "Only Tier 1" in str(exc_info.value)


def test_unverified_video_timestamp_is_ineligible():
    """An unverified video timestamp must not be marked eligible."""
    ts = VideoTimestamp(
        timestamp_start="00:00:10",
        timestamp_end="00:00:20",
        is_verified=False  # Unverified
    )
    with pytest.raises(ValidationError) as exc_info:
        EvidenceItem(
            evidence_id="CHK-VID-UNVER-001",
            document_id="VID-004",
            content_text="Unverified clip segment",
            role=EvidenceRole.EVIDENCIA_AUDIOVISUAL,
            authority=DocumentAuthority.TIER_5_AUDIOVISUAL_EVIDENCE,
            validity=ValidityStatus.VIGENTE,
            eligibility=EligibilityStatus.ELIGIBLE_CONTEXTUAL,  # VIOLATION: Should be NO_ELEGIBLE
            semantic_relevance_score=0.75,
            audiovisual_locators=ts
        )
    assert "unverified video timestamp" in str(exc_info.value)


# ============================================================================
# 3. DOCUMENT GOVERNANCE AND ELIGIBILITY TESTS
# ============================================================================

def test_document_eligibility_pending_approval(validator):
    """Documents with PENDIENTE approval status must be strictly NO_ELEGIBLE."""
    doc = validator.get_document("PAG-002")
    assert doc is not None
    assert doc.approval == ApprovalStatus.PENDIENTE
    assert doc.determine_eligibility() == EligibilityStatus.NO_ELEGIBLE


def test_document_eligibility_repealed_superseded(validator):
    """DOC-001 (SOR Jan 2026) is superseded and must be NO_ELEGIBLE."""
    doc = validator.get_document("DOC-001")
    assert doc is not None
    assert doc.validity == ValidityStatus.HISTORICO_DEROGADO
    assert doc.determine_eligibility() == EligibilityStatus.NO_ELEGIBLE


def test_document_eligibility_retired_video(validator):
    """REF-VID-004-YOUTUBE is rejected/retired and must be NO_ELEGIBLE."""
    doc = validator.get_document("REF-VID-004-YOUTUBE")
    assert doc is not None
    assert doc.validity == ValidityStatus.OBSOLETO_RETIRADO
    assert doc.determine_eligibility() == EligibilityStatus.NO_ELEGIBLE


def test_document_eligibility_approved_tier1(validator):
    """DOC-SOR-2026-08 is Tier 1, fully approved, and ELIGIBLE_DECISORIA."""
    doc = validator.get_document("DOC-SOR-2026-08")
    assert doc is not None
    assert doc.authority == DocumentAuthority.TIER_1_NORMATIVE_PRIMARY
    assert doc.approval == ApprovalStatus.APROBADO
    assert doc.determine_eligibility() == EligibilityStatus.ELIGIBLE_DECISORIA


def test_document_eligibility_approved_tier3(validator):
    """PPT-002 is approved conditionally for interpretive use."""
    doc = validator.get_document("PPT-002")
    assert doc is not None
    assert doc.authority == DocumentAuthority.TIER_3_REFEREEING_INTERPRETATION
    assert doc.approval == ApprovalStatus.APROBADO_CONDICIONADO
    assert doc.determine_eligibility() == EligibilityStatus.ELIGIBLE_INTERPRETATIVA


# ============================================================================
# 4. EVIDENCE BUNDLE & CONFLICT RESOLUTION TESTS
# ============================================================================

def test_bundle_certified_valid(validator):
    """A bundle with valid primary and interpretive items certifies correctly."""
    prim_item = EvidenceItem(
        evidence_id="CHK-SOR-01",
        document_id="DOC-SOR-2026-08",
        content_text="SOR Art 16: Ne-waza transitions must be continuous.",
        role=EvidenceRole.NORMA_PRIMARIA,
        authority=DocumentAuthority.TIER_1_NORMATIVE_PRIMARY,
        validity=ValidityStatus.VIGENTE,
        eligibility=EligibilityStatus.ELIGIBLE_DECISORIA,
        semantic_relevance_score=0.91,
        article_number="Art. 16",
        page_number=171
    )
    supp_item = EvidenceItem(
        evidence_id="CHK-PPT-01",
        document_id="PPT-002",
        content_text="PPT-002: Dragging an opponent down without technique is penalized.",
        role=EvidenceRole.COMPLEMENTO_INTERPRETATIVO,
        authority=DocumentAuthority.TIER_3_REFEREEING_INTERPRETATION,
        validity=ValidityStatus.VIGENTE,
        eligibility=EligibilityStatus.ELIGIBLE_INTERPRETATIVA,
        semantic_relevance_score=0.86,
        article_number="Art. 16"
    )

    bundle = validator.build_certified_bundle(
        bundle_id="BND-TEST-001",
        query_text="Is it permitted to drag an opponent to the ground?",
        candidate_items=[prim_item, supp_item]
    )

    assert bundle.is_sufficient_for_decision is True
    assert bundle.has_unresolved_conflict is False
    assert bundle.abstention_required is False
    assert len(bundle.primary_normative_evidence) == 1
    assert len(bundle.interpretive_evidence) == 1


def test_bundle_normative_conflict_triggers_abstention(validator):
    """If supplementary evidence contradicts primary SOR text, abstention is mandatory."""
    prim_item = EvidenceItem(
        evidence_id="CHK-SOR-OSA-01",
        document_id="DOC-SOR-2026-08",
        content_text="Art 17: Osaekomi for 20 segundos results in Ippon. 10 to 19 segundos is Waza-ari.",
        role=EvidenceRole.NORMA_PRIMARIA,
        authority=DocumentAuthority.TIER_1_NORMATIVE_PRIMARY,
        validity=ValidityStatus.VIGENTE,
        eligibility=EligibilityStatus.ELIGIBLE_DECISORIA,
        semantic_relevance_score=0.95,
        article_number="Art. 17"
    )
    # Hypothetical conflicting supplementary item claiming 15 seconds is Ippon
    conflicting_item = EvidenceItem(
        evidence_id="CHK-OLD-OSA-01",
        document_id="PPT-002",
        content_text="Outdated slide: Osaekomi for 15 segundos results in Ippon.",
        role=EvidenceRole.COMPLEMENTO_INTERPRETATIVO,
        authority=DocumentAuthority.TIER_3_REFEREEING_INTERPRETATION,
        validity=ValidityStatus.VIGENTE,
        eligibility=EligibilityStatus.ELIGIBLE_INTERPRETATIVA,
        semantic_relevance_score=0.89,
        article_number="Art. 17"
    )

    bundle = validator.build_certified_bundle(
        bundle_id="BND-TEST-CONFLICT",
        query_text="What is the time required for Ippon in Osaekomi?",
        candidate_items=[prim_item, conflicting_item]
    )

    assert bundle.has_unresolved_conflict is True
    assert bundle.abstention_required is True
    assert "Temporal Conflict" in bundle.abstention_reason


def test_bundle_absence_of_primary_norm_triggers_abstention(validator):
    """If no Tier 1 SOR rule is retrieved, bundle cannot decide and must abstain."""
    supp_item = EvidenceItem(
        evidence_id="CHK-PPT-ONLY-01",
        document_id="PPT-002",
        content_text="Explanation about referee positioning.",
        role=EvidenceRole.COMPLEMENTO_INTERPRETATIVO,
        authority=DocumentAuthority.TIER_3_REFEREEING_INTERPRETATION,
        validity=ValidityStatus.VIGENTE,
        eligibility=EligibilityStatus.ELIGIBLE_INTERPRETATIVA,
        semantic_relevance_score=0.79
    )

    bundle = validator.build_certified_bundle(
        bundle_id="BND-NO-PRIMARY",
        query_text="Where should referees position themselves during Ne-waza?",
        candidate_items=[supp_item]
    )

    assert bundle.is_sufficient_for_decision is False
    assert bundle.abstention_required is True
    assert "No applicable Tier 1" in bundle.abstention_reason


def test_bundle_rejection_of_unregistered_document(validator):
    """Evidence with unknown document ID must be filtered out of the certified bundle."""
    unreg_item = EvidenceItem(
        evidence_id="CHK-FAKE-01",
        document_id="DOC-NONEXISTENT-999",
        content_text="Fabricated rule statement.",
        role=EvidenceRole.MATERIAL_DIDACTICO,
        authority=DocumentAuthority.TIER_4_EDUCATIONAL_CONTEXT,
        validity=ValidityStatus.VIGENTE,
        eligibility=EligibilityStatus.ELIGIBLE_CONTEXTUAL,
        semantic_relevance_score=0.99
    )

    bundle = validator.build_certified_bundle(
        bundle_id="BND-UNREG",
        query_text="Test query",
        candidate_items=[unreg_item]
    )

    assert bundle.total_evidence_count() == 0
    assert bundle.abstention_required is True

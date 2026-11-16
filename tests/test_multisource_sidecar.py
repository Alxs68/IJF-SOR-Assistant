"""
Unit and Integration Tests for Multisource Ingestion and Sidecar Infrastructure (Phase 4.2.2).
Validates Gates GATE01 through GATE07:
- GATE01: Aislamiento (Sidecar does not touch primary SOR corpus).
- GATE02: Integridad (Hashes verified before and after staging/processing).
- GATE03: Elegibilidad (Rejection of unapproved, pending, or obsolete documents).
- GATE04: Trazabilidad (Provenance and manifest reconstruction).
- GATE05: Rollback (Clean removal and restoration of experimental sidecar).
- GATE06: Invariancia (Cryptographic check of SOR PDF, passages, embeddings, BM25, KG).
- GATE07: Rechazo de conflictos (Inconsistent identity or corrupted hash rejected).
"""

import os
import json
import shutil
import hashlib
import pytest

from src.multisource_indexer import MultisourceIngestionEngine, SidecarChunk, BatchManifest
from src.document_governance import DocumentAuthority, ValidityStatus, ApprovalStatus, EligibilityStatus


@pytest.fixture(scope="module")
def project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def engine():
    return MultisourceIngestionEngine()


# ============================================================================
# GATE01 — AISLAMIENTO
# ============================================================================

def test_gate01_sidecar_isolation(engine, project_root):
    """Verify sidecar artifacts reside exclusively in data/corpus_multisource/."""
    assert os.path.exists(engine.base_dir)
    assert "data\\corpus_multisource" in engine.base_dir or "data/corpus_multisource" in engine.base_dir
    
    # Confirm processed passages is NOT inside rebuild_2026_08_corrected
    primary_dir = os.path.join(project_root, "data", "processed", "rebuild_2026_08_corrected")
    assert not os.path.exists(os.path.join(primary_dir, "multisource_passages.json"))
    assert not os.path.exists(os.path.join(primary_dir, "sidecar_registry.json"))


# ============================================================================
# GATE02 — INTEGRIDAD CRIPTOGRÁFICA
# ============================================================================

def test_gate02_integrity_hashes_verified(engine, project_root):
    """Verify that staged files match physical source hashes exactly."""
    staging_file = os.path.join(engine.staging_dir, "KUN-PPT-002_staged.md")
    if os.path.exists(staging_file):
        staged_hash = engine.calculate_file_sha256(staging_file)
        source_file = os.path.join(project_root, "data", "markdown", "kuns_ppt_002.md")
        source_hash = engine.calculate_file_sha256(source_file)
        assert staged_hash == source_hash


# ============================================================================
# GATE03 — ELEGIBILIDAD Y RECHAZO
# ============================================================================

def test_gate03_reject_pending_document(engine):
    """Verify that a document in state PENDIENTE (e.g. KUN-DOC-004) is rejected from staging."""
    ok, msg, meta = engine.stage_document("KUN-DOC-004", "data/markdown/kuns_doc_004.md")
    assert ok is False
    assert "PENDIENTE" in msg or "Rejection" in msg


def test_gate03_reject_repealed_document(engine):
    """Verify that a historical/superseded document (KUN-DOC-001) is rejected from staging."""
    ok, msg, meta = engine.stage_document("KUN-DOC-001", "data/markdown/kuns_doc_001.md")
    assert ok is False
    assert "HISTORICO_DEROGADO" in msg or "ARCHIVADO" in msg or "Rejection" in msg


def test_gate03_reject_retired_video(engine):
    """Verify that obsolete/unplayable media (REF-VID-004-YOUTUBE) is rejected."""
    ok, msg, meta = engine.stage_document("REF-VID-004-YOUTUBE", "data/markdown/kuns_doc_001.md")
    assert ok is False
    assert "Rejection" in msg


# ============================================================================
# GATE04 — TRAZABILIDAD DOCUMENTAL
# ============================================================================

def test_gate04_traceability_reconstruction(engine):
    """Verify that batch manifest and sidecar registry exist and trace back to Alexis."""
    assert os.path.exists(engine.sidecar_registry_file)
    with open(engine.sidecar_registry_file, "r", encoding="utf-8") as f:
        reg = json.load(f)
    assert reg.get("status") == "READY"
    assert reg.get("total_sidecar_chunks", 0) > 0

    manifest_files = os.listdir(engine.manifests_dir)
    assert len(manifest_files) > 0
    with open(os.path.join(engine.manifests_dir, manifest_files[0]), "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["approved_by"] == "Alexis"
    assert len(manifest["documents_ingested"]) > 0


# ============================================================================
# GATE05 — ROLLBACK AISLADO
# ============================================================================

def test_gate05_rollback_and_restore(project_root):
    """Verify that rollback removes sidecar files without touching primary corpus."""
    temp_sidecar_dir = os.path.join(project_root, "data", "test_corpus_multisource_temp")
    temp_engine = MultisourceIngestionEngine(base_dir=temp_sidecar_dir)
    
    # Stage an item in temp
    ok, msg, meta = temp_engine.stage_document("KUN-NEW-001", "data/markdown/kuns_new_001.md")
    assert ok is True
    assert os.path.exists(meta["staging_path"])
    
    # Execute rollback on temp
    rb_res = temp_engine.execute_rollback()
    assert rb_res["status"] == "ROLLBACK_SUCCESSFUL"
    assert not os.path.exists(meta["staging_path"])
    
    # Cleanup temp directory
    shutil.rmtree(temp_sidecar_dir, ignore_errors=True)


# ============================================================================
# GATE06 — INVARIANCIA DEL CORPUS SOR PRIMARIO
# ============================================================================

def test_gate06_sor_invariants_preserved(project_root):
    """Verify cryptographic invariants of official SOR PDF, passages, and indices."""
    expected_hashes = {
        "data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf": "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620",
        "data/processed/rebuild_2026_08_corrected/passages_candidate.json": "7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b",
        "data/processed/rebuild_2026_08_corrected/vector_index_candidate.json": "e182c77e0775472eb73d22ab92b15d026d067cbf6264fb8b25b207479c4668eb",
        "data/processed/rebuild_2026_08_corrected/dense_embeddings_meta.json": "c96b214bc14801ad903d58e0245d48c008d65ac051d339fd4e6b65e30709160e",
        "data/processed/rebuild_2026_08_corrected/knowledge_graph_candidate.json": "95d5a67936cf48d3bc79b69bf370bb1a83a255f938a7322e0dae256450dde215"
    }

    for rel_path, exp_hash in expected_hashes.items():
        full_path = os.path.join(project_root, rel_path)
        assert os.path.exists(full_path), f"Missing invariant file: {rel_path}"
        with open(full_path, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        assert actual_hash == exp_hash, f"Invariant violated for {rel_path}! Expected {exp_hash}, got {actual_hash}"


# ============================================================================
# GATE07 — RECHAZO DE CONFLICTOS Y CORRUPCIÓN
# ============================================================================

def test_gate07_reject_hash_mismatch(engine, tmp_path):
    """Verify that a corrupted file whose hash does not match catalog metadata is rejected."""
    corrupted_file = tmp_path / "corrupted.md"
    corrupted_file.write_text("# Corrupted Content", encoding="utf-8")
    
    # Try to stage as KUN-PPT-002 with invalid hash
    ok, msg, meta = engine.stage_document("KUN-PPT-002", str(corrupted_file))
    assert ok is False
    assert "Cryptographic mismatch" in msg

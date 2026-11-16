"""
Integration and Verification Tests for Complementary IJF Documents Coverage (Fase 5).
Validates:
1. Retrieval and citation of IJF Disciplinary Code (DOC-DIS-2023 / KUN-DIS-001).
2. Retrieval and citation of IJF Code of Ethics (DOC-ETH-2023 / KUN-ETH-001).
3. Retrieval and citation of LA28 Olympic Qualification System (DOC-QSY-2026 / KUN-QSY-001).
4. Provenance and metadata integrity in sidecar registry and batch manifests.
5. Absolute preservation of SOR 2026-08 primary invariants.
"""

import os
import json
import hashlib
import pytest

from src.multisource_retriever import MultisourceRetriever
from src.document_validator import DocumentValidator
from src.rre_engine import ReasoningRetrievalEngine


@pytest.fixture(scope="module")
def retriever():
    return MultisourceRetriever()


@pytest.fixture(scope="module")
def validator():
    return DocumentValidator()


@pytest.fixture(scope="module")
def rre():
    return ReasoningRetrievalEngine(allow_degraded=True, enable_shadow_mode_multisource=True)


def test_disciplinary_code_retrieval(retriever):
    """Verify retrieval of disciplinary sanctions and statute of limitations."""
    res = retriever.search("sanciones disciplinarias inhabilitacion prescripcion", top_k=2)
    assert res["status"] == "SUCCESS"
    assert len(res["matches"]) > 0
    top = res["matches"][0]
    assert top["document_id"] == "KUN-DIS-001"
    assert top["authority"] == "TIER_2_OFFICIAL_AMENDMENT"
    assert top["validity"] == "VIGENTE"
    assert "SOR Art. 1.2.1" in str(top["related_sor_articles"])


def test_code_of_ethics_retrieval(retriever):
    """Verify retrieval of Code of Ethics rules regarding respect and betting prohibition."""
    res = retriever.search("codigo etica respeto arbitros apuestas deportivas", top_k=2)
    assert res["status"] == "SUCCESS"
    assert len(res["matches"]) > 0
    top = res["matches"][0]
    assert top["document_id"] == "KUN-ETH-001"
    assert top["authority"] == "TIER_2_OFFICIAL_AMENDMENT"
    assert top["validity"] == "VIGENTE"
    assert "SOR Art. 1.1.1" in str(top["related_sor_articles"]) or "SOR Art. 1.2.2" in str(top["related_sor_articles"])


def test_olympic_qualification_system_retrieval(retriever):
    """Verify retrieval of LA28 Olympic Games qualification quota and direct WRL criteria."""
    res = retriever.search("clasificacion olimpica LA28 cuota total ranking directo top 17", top_k=2)
    assert res["status"] == "SUCCESS"
    assert len(res["matches"]) > 0
    top = res["matches"][0]
    assert top["document_id"] == "KUN-QSY-001"
    assert top["authority"] == "TIER_2_OFFICIAL_AMENDMENT"
    assert top["validity"] == "VIGENTE"
    assert "SOR Art. 3.2.1" in str(top["related_sor_articles"]) or "SOR Art. 2.2.3" in str(top["related_sor_articles"])


def test_olympic_qualification_dates_and_tolerance(retriever):
    """Verify retrieval of LA28 qualification period dates and mixed team weight tolerance."""
    res = retriever.search("periodo calificacion olimpica tolerancia peso equipos mixtos", top_k=2)
    assert res["status"] == "SUCCESS"
    assert len(res["matches"]) > 0
    top = res["matches"][0]
    assert top["chunk_id"] == "CHK-KUN-QSY-001-004"
    assert "15th June 2026" in top["content_text"] or "15 de junio de 2026" in top["content_text"]


def test_sidecar_registry_manifest_consistency():
    """Verify sidecar registry tracks the active batch manifest with correct chunk count."""
    registry_path = os.path.join("data", "corpus_multisource", "sidecar_registry.json")
    assert os.path.exists(registry_path)
    with open(registry_path, "r", encoding="utf-8") as f:
        reg = json.load(f)
    assert reg["status"] == "READY"
    assert reg["total_sidecar_chunks"] == 18
    assert "BATCH-MULTI-2026-11-02.json" in reg["active_manifests"]


def test_raw_complementary_files_exist_and_hashes_match():
    """Verify physical PDF files exist in data/raw/complementary and hashes match catalog."""
    expected = {
        "data/raw/complementary/IJF_Disciplinary_Code_2023_05_04.pdf": "20981725bbc6d9c4ff95d72da14ae5a512324a76996514e4f06933b63919fb48",
        "data/raw/complementary/IJF_Code_of_Ethics_2023_02_27.pdf": "1cf006c12b03aae5dd6f40281a437317cf9a467ea47455327c2129bad08cc0b4",
        "data/raw/complementary/IJF_LA28_Olympic_Qualification_System_2026_05_12.pdf": "23a1f1449b11cf293eb6d87da0c0f88dbe3593d481b6ddccee1db8134765509a"
    }
    for path, exp_hash in expected.items():
        assert os.path.exists(path), f"Missing file: {path}"
        with open(path, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        assert actual_hash == exp_hash, f"Hash mismatch for {path}!"

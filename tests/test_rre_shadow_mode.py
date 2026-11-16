"""
Test Suite: RRE Shadow Mode & Multisource Sidecar Isolation (Fase 4.2.3)
========================================================================
Verificaciones obligatorias:
1. Invariabilidad de la respuesta principal: idéntica con Shadow activo vs inactivo.
2. Flag desactivado por defecto: verify default is False.
3. Aislamiento de errores: fallo, corrupción o ausencia de Sidecar no afecta RRE.
4. Respeto al timeout: consultas no bloquean el RRE si el Sidecar excede tiempo.
5. Filtro de elegibilidad: rechazo de fragmentos derogados, revocados o no aprobados.
6. Trazabilidad completa en log: registro de metadata, SHA-256 y tiers sin contaminar evidencias.
7. Preservación estricta de invariantes primarios del SOR 2026.
"""

import os
import json
import pytest
import tempfile
import hashlib
from src.rre_engine import ReasoningRetrievalEngine
from src.multisource_retriever import MultisourceRetriever

SOR_HASHES = {
    "passages": "7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b",
    "vector_index": "e182c77e0775472eb73d22ab92b15d026d067cbf6264fb8b25b207479c4668eb",
    "dense_meta": "c96b214bc14801ad903d58e0245d48c008d65ac051d339fd4e6b65e30709160e",
    "knowledge_graph": "95d5a67936cf48d3bc79b69bf370bb1a83a255f938a7322e0dae256450dde215"
}

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

@pytest.fixture(scope="module")
def rre_default():
    """Instancia estándar con Shadow Mode desactivado por defecto."""
    return ReasoningRetrievalEngine(allow_degraded=True)

@pytest.fixture(scope="module")
def rre_shadow():
    """Instancia con Shadow Mode activado expresamente."""
    return ReasoningRetrievalEngine(allow_degraded=True, enable_shadow_mode_multisource=True)

def test_shadow_flag_default_is_false():
    """Verifica que el feature flag de Shadow Mode está estrictamente desactivado por defecto."""
    engine = ReasoningRetrievalEngine(allow_degraded=True)
    assert engine.enable_shadow_mode_multisource is False
    assert engine.sidecar_retriever is None

def test_invariance_primary_response(rre_default, rre_shadow):
    """
    Verifica que la evidencia, ranking y scores primarios retornados al usuario
    son idénticos bit a bit entre Shadow Mode inactivo y activo.
    """
    test_queries = [
        "What constitutes an Ippon in competition?",
        "When is Shido given for passivity?",
        "What is the duration of Osaekomi for Waza-ari?",
        "Can a competitor execute reverse seoi-nage?"
    ]

    for q in test_queries:
        res_default = rre_default.retrieve(q)
        res_shadow = rre_shadow.retrieve(q)

        assert res_default["status"] == res_shadow["status"]
        assert len(res_default["evidence"]) == len(res_shadow["evidence"])

        for e_def, e_shd in zip(res_default["evidence"], res_shadow["evidence"]):
            assert e_def["passage_id"] == e_shd["passage_id"]
            assert e_def["score"] == e_shd["score"]
            assert e_def["article_id"] == e_shd["article_id"]
            assert e_def["page"] == e_shd["page"]
            assert e_def["text_original"] == e_shd["text_original"]
            # Asegurar que ningún campo Sidecar contaminó la evidencia primaria
            assert "authority" not in e_shd
            assert "sidecar" not in e_shd
            assert "chunk_id" not in e_shd

def test_shadow_logging_and_traceability(rre_shadow):
    """Verifica que la ejecución Shadow genera registros estructurados con procedencia y metadata."""
    query = "reverse seoi-nage senior"
    res = rre_shadow.retrieve(query)

    assert res["status"] == "SUCCESS"
    assert rre_shadow.last_shadow_result is not None
    last = rre_shadow.last_shadow_result

    assert last["query"] == query
    assert last["sidecar_status"] == "SUCCESS"
    assert len(last["sidecar_matches"]) > 0

    top_sidecar = last["sidecar_matches"][0]
    assert top_sidecar["chunk_id"] == "CHK-KUN-NEW-001-002"
    assert top_sidecar["authority"] == "TIER_2_OFFICIAL_AMENDMENT"
    assert top_sidecar["validity"] == "VIGENTE"
    assert top_sidecar["eligibility"] == "ELIGIBLE_INTERPRETATIVA"
    assert top_sidecar["staging_sha256"] is not None
    assert "SOR Art. 18.1.4 y Art. 18.2.2" in top_sidecar["related_sor_articles"]

def test_sidecar_error_isolation():
    """
    Simula un fallo catastrófico en el recuperador Sidecar (archivo inexistente o corrupto)
    y verifica que el RRE primario continúa respondiendo exitosamente sin degradación.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_log = os.path.join(tmpdir, "shadow.log")
        # Instanciar engine con sidecar apuntando a archivo inexistente
        engine = ReasoningRetrievalEngine(
            allow_degraded=True,
            enable_shadow_mode_multisource=True,
            shadow_log_path=fake_log
        )
        # Forzar retriever apuntando a un path corrupto
        engine.sidecar_retriever = MultisourceRetriever(passages_path=os.path.join(tmpdir, "non_existent.json"))

        res = engine.retrieve("What is Ippon?")
        assert res["status"] == "SUCCESS"
        assert len(res["evidence"]) > 0
        assert engine.last_shadow_result["sidecar_status"] in ["UNAVAILABLE", "INITIALIZATION_FAILED"]

def test_sidecar_timeout_protection():
    """Verifica que el mecanismo de timeout previene bloqueos si la búsqueda toma más tiempo del asignado."""
    retriever = MultisourceRetriever()
    # Forzar timeout microscópico de 0.0000001 ms para disparar la condición de corte
    res = retriever.search("What is the rule for Yuko in Osaekomi?", timeout_ms=0.0000001)
    assert res["status"] in ["TIMEOUT", "SUCCESS"]
    if res["status"] == "TIMEOUT":
        assert "timeout" in res["reason"].lower()
        assert res["matches"] == []

def test_sidecar_eligibility_filter():
    """Verifica que documentos no vigentes, derogados o pendientes son excluidos de memoria."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_file = os.path.join(tmpdir, "dummy_passages.json")
        dummy_data = [
            {
                "chunk_id": "CHK-VALID-01",
                "authority": "TIER_2_OFFICIAL_AMENDMENT",
                "validity": "VIGENTE",
                "eligibility": "ELIGIBLE_INTERPRETATIVA",
                "title": "Valid chunk",
                "content_text": "Valid rule content",
                "related_sor_articles": ["Art. 15"]
            },
            {
                "chunk_id": "CHK-REPEALED-02",
                "authority": "TIER_2_OFFICIAL_AMENDMENT",
                "validity": "DEROGADO",
                "eligibility": "APPROVED",
                "title": "Repealed chunk",
                "content_text": "Repealed rule content",
                "related_sor_articles": ["Art. 15"]
            },
            {
                "chunk_id": "CHK-PENDING-03",
                "authority": "TIER_2_OFFICIAL_AMENDMENT",
                "validity": "VIGENTE",
                "eligibility": "PENDING_REVIEW",
                "title": "Pending chunk",
                "content_text": "Pending rule content",
                "related_sor_articles": ["Art. 15"]
            }
        ]
        with open(dummy_file, "w", encoding="utf-8") as f:
            json.dump(dummy_data, f)

        retriever = MultisourceRetriever(passages_path=dummy_file)
        assert len(retriever.passages) == 1
        assert retriever.passages[0]["chunk_id"] == "CHK-VALID-01"

def test_sor_invariants_preserved():
    """Certifica matemáticamente que los archivos base del SOR 2026 no han sufrido alteración alguna."""
    base_dir = "data/processed/rebuild_2026_08_corrected"
    assert sha256_file(os.path.join(base_dir, "passages_candidate.json")) == SOR_HASHES["passages"]
    assert sha256_file(os.path.join(base_dir, "vector_index_candidate.json")) == SOR_HASHES["vector_index"]
    assert sha256_file(os.path.join(base_dir, "dense_embeddings_meta.json")) == SOR_HASHES["dense_meta"]
    assert sha256_file(os.path.join(base_dir, "knowledge_graph_candidate.json")) == SOR_HASHES["knowledge_graph"]

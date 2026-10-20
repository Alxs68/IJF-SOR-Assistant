import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from feedback_manager import record_observation, ensure_feedback_storage, MOTIVOS_VALIDOS, OBSERVATIONS_FILE

def test_record_observation_minimal(tmp_path, monkeypatch):
    test_file = str(tmp_path / "test_observations.jsonl")
    monkeypatch.setattr("feedback_manager.OBSERVATIONS_FILE", test_file)
    monkeypatch.setattr("feedback_manager.FEEDBACK_DIR", str(tmp_path))

    # Send with only reason (no comment, no technical inputs required from user)
    res = record_observation(
        motivo="La respuesta podría ser incorrecta",
        query="¿Qué ocurre fuera del área de tatami?",
        response_summary="El árbitro anuncia Mate",
        citations=[{"passage_id": "SOR-P151", "article_id": "Art. 5", "page_number": 151}]
    )

    assert res["success"] is True
    assert res["observation_id"].startswith("OBS-")
    assert os.path.exists(test_file)

    with open(test_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["reason"] == "La respuesta podría ser incorrecta"
    assert data["user_comment"] == ""
    assert data["context"]["query"] == "¿Qué ocurre fuera del área de tatami?"
    assert data["context"]["citations"][0]["article_id"] == "Art. 5"
    assert data["status"] == "RECEIVED"
    assert data["internal_review"]["reviewed"] is False

def test_record_observation_with_optional_comment(tmp_path, monkeypatch):
    test_file = str(tmp_path / "test_observations.jsonl")
    monkeypatch.setattr("feedback_manager.OBSERVATIONS_FILE", test_file)
    monkeypatch.setattr("feedback_manager.FEEDBACK_DIR", str(tmp_path))

    res = record_observation(
        motivo="Falta una regla o aclaración",
        comentario="En el Grand Slam de París 2026 hubo un caso similar en la final.",
        query="¿Cuándo se otorga Ippon fuera de seguridad?",
        response_summary="Resumen de prueba",
        citations=[]
    )

    assert res["success"] is True
    with open(test_file, "r", encoding="utf-8") as f:
        data = json.loads(f.readline())
    assert data["user_comment"] == "En el Grand Slam de París 2026 hubo un caso similar en la final."
    assert data["reason"] == "Falta una regla o aclaración"

def test_motivos_validos_coverage():
    assert len(MOTIVOS_VALIDOS) == 5
    assert "La respuesta podría ser incorrecta" in MOTIVOS_VALIDOS
    assert "Tengo una sugerencia de mejora" in MOTIVOS_VALIDOS

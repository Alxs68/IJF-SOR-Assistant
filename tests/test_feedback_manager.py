import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from feedback_manager import (
    record_observation,
    ensure_feedback_storage,
    MOTIVOS_VALIDOS,
    OBSERVATIONS_FILE,
    VALID_STATUSES,
    STATUS_COMPATIBILITY_MAP,
    is_admin_configured,
    verify_admin_token,
    list_observations_protected,
    get_observation_attachment_bytes,
    update_observation_status_protected,
    save_attachment
)

TEST_ADMIN_TOKEN = "SuperSecretAdminToken2026!"


# -------------------------------------------------------------
# 1. Pruebas de compatibilidad con registros históricos y esquema
# -------------------------------------------------------------
def test_record_observation_minimal_legacy_format(tmp_path, monkeypatch):
    """Verifica que llamadas con la firma legacy (solo motivo) sigan funcionando y persistiendo."""
    test_file = str(tmp_path / "test_observations.jsonl")
    monkeypatch.setattr("feedback_manager.OBSERVATIONS_FILE", test_file)
    monkeypatch.setattr("feedback_manager.FEEDBACK_DIR", str(tmp_path))

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
    assert data["status"] == "Recibida"
    assert data["internal_review"]["reviewed"] is False


def test_motivos_validos_coverage():
    """Conserva cobertura de MOTIVOS_VALIDOS históricos."""
    assert len(MOTIVOS_VALIDOS) == 5
    assert "La respuesta podría ser incorrecta" in MOTIVOS_VALIDOS
    assert "Tengo una sugerencia de mejora" in MOTIVOS_VALIDOS


def test_backward_compatibility_with_existing_records(tmp_path, monkeypatch):
    """
    Verifica que registros preexistentes en jsonl con 'RECEIVED', 'NORMAL', etc.
    se lean, mapeen y preserven sin pérdidas ni errores.
    """
    test_file = str(tmp_path / "test_observations.jsonl")
    monkeypatch.setattr("feedback_manager.OBSERVATIONS_FILE", test_file)
    monkeypatch.setattr("feedback_manager.FEEDBACK_DIR", str(tmp_path))
    monkeypatch.setenv("FEEDBACK_ADMIN_TOKEN", TEST_ADMIN_TOKEN)

    # Crear registro con formato anterior
    old_record = {
        "observation_id": "OBS-20261019-B3387005",
        "timestamp": "2026-10-19T10:56:53.168915+00:00",
        "reason": "La respuesta podría ser incorrecta",
        "user_comment": "Comprobación de usabilidad anterior",
        "context": {
            "query": "¿Cuáles son las dimensiones del tatami?",
            "response_summary": "Área de 8x8 a 10x10",
            "citations": []
        },
        "status": "RECEIVED",
        "internal_review": {"reviewed": False, "priority": "NORMAL", "notes": ""}
    }
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(old_record) + "\n")

    # Leer mediante consulta administrativa protegida
    res = list_observations_protected(admin_token=TEST_ADMIN_TOKEN)
    assert res["success"] is True
    assert len(res["data"]) == 1
    item = res["data"][0]
    assert item["observation_id"] == "OBS-20261019-B3387005"
    # Normalizado a estado oficial
    assert item["status"] == "Recibida"


# -------------------------------------------------------------
# 2. Pruebas de la Experiencia Pública Simplificada (Sin categorías)
# -------------------------------------------------------------
def test_public_submission_free_text_without_category(tmp_path, monkeypatch):
    """
    Verifica que un usuario anónimo pueda enviar un reporte indicando solo
    comentario libre, sin necesidad de seleccionar motivo predefinido.
    """
    test_file = str(tmp_path / "test_observations.jsonl")
    monkeypatch.setattr("feedback_manager.OBSERVATIONS_FILE", test_file)
    monkeypatch.setattr("feedback_manager.FEEDBACK_DIR", str(tmp_path))

    res = record_observation(
        motivo=None,
        comentario="He detectado que en el visor de PDF la página 188 no resalta el Shido de cadetes.",
        query="¿Se sanciona la defensa con la cabeza en cadetes?",
        response_summary="Shido según Art. 18.1.4",
        citations=[{"passage_id": "SOR-P188", "article_id": "Art. 18.1.4", "page_number": 188}],
        edition="2026-08 (Official)",
        extra_metadata={"lang": "es", "ui_section": "response_card", "app_version": "1.2.0"}
    )

    assert res["success"] is True
    assert res["observation_id"].startswith("OBS-")
    assert "éxito" in res["message"]

    with open(test_file, "r", encoding="utf-8") as f:
        data = json.loads(f.readline())

    assert data["reason"] == "General"
    assert "visor de PDF" in data["user_comment"]
    assert data["context"]["lang"] == "es"
    assert data["context"]["ui_section"] == "response_card"
    assert data["status"] == "Recibida"


def test_public_submission_empty_rejected(tmp_path, monkeypatch):
    """Verifica que un reporte totalmente vacío (sin texto ni motivo) sea rechazado."""
    test_file = str(tmp_path / "test_observations.jsonl")
    monkeypatch.setattr("feedback_manager.OBSERVATIONS_FILE", test_file)
    monkeypatch.setattr("feedback_manager.FEEDBACK_DIR", str(tmp_path))

    res = record_observation(motivo="", comentario="")
    assert res["success"] is False
    assert res["observation_id"] is None
    assert "descripción" in res["message"].lower()


# -------------------------------------------------------------
# 3. Pruebas de Adjuntos, Tamaño y Prevención de Path Traversal
# -------------------------------------------------------------
def test_attachment_upload_valid(tmp_path, monkeypatch):
    """Verifica la subida exitosa de una captura de evidencia PNG."""
    test_file = str(tmp_path / "test_observations.jsonl")
    att_dir = str(tmp_path / "attachments")
    monkeypatch.setattr("feedback_manager.OBSERVATIONS_FILE", test_file)
    monkeypatch.setattr("feedback_manager.FEEDBACK_DIR", str(tmp_path))
    monkeypatch.setattr("feedback_manager.ATTACHMENTS_DIR", att_dir)

    dummy_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    res = record_observation(
        comentario="Adjunto captura de la pantalla mostrando la discrepancia.",
        attachment_bytes=dummy_png,
        attachment_filename="evidencia_arbitraje.png",
        attachment_mime="image/png"
    )

    assert res["success"] is True
    obs_id = res["observation_id"]

    with open(test_file, "r", encoding="utf-8") as f:
        data = json.loads(f.readline())

    assert data["attachment"] is not None
    assert data["attachment"]["original_filename"] == "evidencia_arbitraje.png"
    assert data["attachment"]["size_bytes"] == len(dummy_png)

    # Comprobar que el archivo se guardó físicamente
    rel_path = data["attachment"]["relative_path"]
    full_path = os.path.join(att_dir, rel_path)
    assert os.path.exists(full_path)


def test_attachment_upload_size_limit_exceeded(tmp_path, monkeypatch):
    """Verifica el rechazo si el archivo excede los 5 MB."""
    test_file = str(tmp_path / "test_observations.jsonl")
    att_dir = str(tmp_path / "attachments")
    monkeypatch.setattr("feedback_manager.OBSERVATIONS_FILE", test_file)
    monkeypatch.setattr("feedback_manager.FEEDBACK_DIR", str(tmp_path))
    monkeypatch.setattr("feedback_manager.ATTACHMENTS_DIR", att_dir)

    # 6 MB
    large_bytes = b"0" * (6 * 1024 * 1024)

    res = record_observation(
        comentario="Intento de adjunto pesado",
        attachment_bytes=large_bytes,
        attachment_filename="archivo_pesado.pdf",
        attachment_mime="application/pdf"
    )

    assert res["success"] is False
    assert "excede el tamaño máximo" in res["message"]


def test_attachment_upload_invalid_extension(tmp_path, monkeypatch):
    """Verifica que extensiones peligrosas (.exe, .sh, .py) sean rechazadas."""
    test_file = str(tmp_path / "test_observations.jsonl")
    att_dir = str(tmp_path / "attachments")
    monkeypatch.setattr("feedback_manager.OBSERVATIONS_FILE", test_file)
    monkeypatch.setattr("feedback_manager.FEEDBACK_DIR", str(tmp_path))
    monkeypatch.setattr("feedback_manager.ATTACHMENTS_DIR", att_dir)

    res = record_observation(
        comentario="Adjunto script sospechoso",
        attachment_bytes=b"echo dangerous",
        attachment_filename="exploit.sh"
    )
    assert res["success"] is False
    assert "no permitido" in res["message"]


def test_attachment_path_traversal_prevention(tmp_path, monkeypatch):
    """Verifica que intentos de Directory Traversal al recuperar adjuntos sean bloqueados."""
    monkeypatch.setattr("feedback_manager.ATTACHMENTS_DIR", str(tmp_path / "attachments"))
    monkeypatch.setenv("FEEDBACK_ADMIN_TOKEN", TEST_ADMIN_TOKEN)

    # Intento de Path Traversal
    ok, data, err = get_observation_attachment_bytes(
        admin_token=TEST_ADMIN_TOKEN,
        relative_path="../../etc/passwd"
    )
    assert ok is False
    assert data is None
    assert "Path Traversal" in err or "denegado" in err


# -------------------------------------------------------------
# 4. Pruebas de Autorización y Seguridad en el Servidor
# -------------------------------------------------------------
def test_admin_access_unauthorized_without_token(tmp_path, monkeypatch):
    """
    Verifica que un usuario anónimo o con token ausente NO pueda
    listar ni consultar reportes ni notas internas.
    """
    test_file = str(tmp_path / "test_observations.jsonl")
    monkeypatch.setattr("feedback_manager.OBSERVATIONS_FILE", test_file)
    monkeypatch.setattr("feedback_manager.FEEDBACK_DIR", str(tmp_path))
    monkeypatch.setenv("FEEDBACK_ADMIN_TOKEN", TEST_ADMIN_TOKEN)

    # 1. Sin token
    res_none = list_observations_protected(admin_token=None)
    assert res_none["success"] is False
    assert res_none["error"] == "UNAUTHORIZED"
    assert res_none["data"] == []

    # 2. Con token incorrecto
    res_wrong = list_observations_protected(admin_token="WrongToken123")
    assert res_wrong["success"] is False
    assert res_wrong["error"] == "UNAUTHORIZED"

    # 3. Intento de actualizar estado sin token
    up_res = update_observation_status_protected(
        admin_token="FakeToken",
        observation_id="OBS-123",
        new_status="En investigación"
    )
    assert up_res["success"] is False
    assert up_res["error"] == "UNAUTHORIZED"


def test_admin_disabled_if_server_token_unset(tmp_path, monkeypatch):
    """Verifica que si no hay token configurado en el servidor, todo acceso administrativo queda deshabilitado."""
    monkeypatch.delenv("FEEDBACK_ADMIN_TOKEN", raising=False)
    assert is_admin_configured() is False
    assert verify_admin_token("CualquierToken") is False

    res = list_observations_protected(admin_token="CualquierToken")
    assert res["success"] is False
    assert res["error"] == "UNAUTHORIZED"


# -------------------------------------------------------------
# 5. Pruebas del Ciclo de 8 Estados y Registro de Notas Internas
# -------------------------------------------------------------
def test_official_8_statuses_lifecycle(tmp_path, monkeypatch):
    """
    Verifica la transición por los 8 estados oficiales:
    Recibida -> Pendiente de revisión -> En investigación -> En corrección ->
    Pendiente de validar -> Validada -> Descartada -> Bloqueada.
    """
    test_file = str(tmp_path / "test_observations.jsonl")
    monkeypatch.setattr("feedback_manager.OBSERVATIONS_FILE", test_file)
    monkeypatch.setattr("feedback_manager.FEEDBACK_DIR", str(tmp_path))
    monkeypatch.setenv("FEEDBACK_ADMIN_TOKEN", TEST_ADMIN_TOKEN)

    # Registrar novedad inicial
    rec = record_observation(
        comentario="Discrepancia detectada en pesaje aleatorio.",
        query="¿Cuál es la tolerancia de peso?"
    )
    obs_id = rec["observation_id"]

    # Probar transición a cada uno de los 8 estados oficiales
    for status in VALID_STATUSES:
        up = update_observation_status_protected(
            admin_token=TEST_ADMIN_TOKEN,
            observation_id=obs_id,
            new_status=status,
            admin_note=f"Transición a {status} verificada.",
            author="Auditor IJF"
        )
        assert up["success"] is True
        assert up["new_status"] == status

    # Rechazo de estados no contemplados
    invalid_up = update_observation_status_protected(
        admin_token=TEST_ADMIN_TOKEN,
        observation_id=obs_id,
        new_status="EstadoInventado"
    )
    assert invalid_up["success"] is False
    assert invalid_up["error"] == "INVALID_STATUS"

    # Verificar historial acumulado y notas internas persistidas
    obs_list = list_observations_protected(admin_token=TEST_ADMIN_TOKEN)
    target = next(o for o in obs_list["data"] if o["observation_id"] == obs_id)
    assert target["status"] == "Bloqueada"
    assert "Auditor IJF" in target["internal_review"]["notes"]
    assert len(target["internal_review"]["status_history"]) == 9  # 1 inicial + 8 cambios

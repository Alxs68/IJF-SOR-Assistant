"""Pruebas del empaquetado experimental sin commit (deploy/exp/build_package_exp.py)."""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_package_exp", ROOT / "deploy" / "exp" / "build_package_exp.py")
bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)

pytestmark = pytest.mark.skipif(not shutil.which("git"), reason="requiere git")

FAKE_GEMINI = "AQ." + "x" * 40
NEW_FILES = ["src/answer_presentation.py", "config/llm_pricing.json"]
MOD_FILES = ["app.py", "src/decision_integrity.py"]


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def w(repo, rel, text):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q")
    git(r, "config", "user.email", "t@t")
    git(r, "config", "user.name", "t")
    base = {
        "app.py": "import ada_assistant\nprint('base')\n", "Dockerfile": "FROM python\n", "requirements.txt": "x\n",
        ".dockerignore": ".env\n", ".env.example": "GEMINI_API_KEY=YOUR_KEY\n",
        "src/ada_assistant.py": "ADA_TRANSLATE_ANY_LANG=1\nvalidated_answer=1\nimport corpus_config\n",
        "src/decision_integrity.py": "base\n", "src/llm_provider.py": "x=1\n",
        "src/rre_engine.py": "RRE_CHANNEL_CHAMPIONS=1\n", "src/corpus_config.py": "x=1\n",
        "data/processed/rebuild_2026_08_corrected/u.json": "{}\n", "data/derived/d.json": "{}\n",
        "data/corpus_multisource/m.json": "{}\n",
        "data/eval/benchmark_v2/splits/test_sealed.jsonl": "{}\n", "scratch/tmp.py": "x\n",
        "deploy/exp/server_install_exp.sh": "rollback EXP_FIX3\n",
    }
    for k, v in base.items():
        w(r, k, v)
    git(r, "add", "-A")
    git(r, "commit", "-qm", "base")
    # estado de trabajo: modificados, nuevos, basura y secretos que no deben entrar
    w(r, "app.py", "import ada_assistant\nimport answer_presentation\nprint('fix3')\n")
    w(r, "src/decision_integrity.py", "DIG_11_SUBORDINATE DIG06_REFS ADA_UNIFIED_ANSWER\n")
    w(r, "src/answer_presentation.py", "def unified_sections(): pass\n")
    w(r, "config/llm_pricing.json", "{}\n")
    w(r, ".env", f"GEMINI_API_KEY={FAKE_GEMINI}\n")
    w(r, ".env.bak_rot", f"GEMINI_API_KEY={FAKE_GEMINI}\n")
    w(r, "streamlit.log", "log\n")
    w(r, "src/__pycache__/x.cpython-312.pyc", "bin")
    w(r, "data/eval/fix3/res.json", "{}\n")
    w(r, "scratch/notas.md", "x\n")
    return r


def run(repo, tmp_path, files=MOD_FILES + NEW_FILES + ["deploy/exp/server_install_exp.sh"], **kw):
    return bp.build(str(repo), "HEAD", str(tmp_path / "out"), secrets_from=str(repo / ".env"), authorized=files, **kw)


def members(tar_path):
    with tarfile.open(tar_path, "r:gz") as t:
        return {m.name.split("/", 1)[1]: t.extractfile(m).read() for m in t.getmembers() if m.isfile()}


def test_paquete_sin_commit_ni_cambios_en_git(repo, tmp_path):
    head, idx = git(repo, "rev-parse", "HEAD"), (repo / ".git" / "index").read_bytes()
    status, refs = git(repo, "status", "--porcelain"), git(repo, "for-each-ref")
    objects = sorted(str(p) for p in (repo / ".git" / "objects").rglob("*"))
    run(repo, tmp_path)
    assert git(repo, "rev-parse", "HEAD") == head
    assert (repo / ".git" / "index").read_bytes() == idx
    assert git(repo, "status", "--porcelain") == status
    assert git(repo, "for-each-ref") == refs
    assert sorted(str(p) for p in (repo / ".git" / "objects").rglob("*")) == objects
    assert git(repo, "stash", "list") == ""


def test_incluye_modificados_y_nuevos(repo, tmp_path):
    m = run(repo, tmp_path)
    got = members(tmp_path / "out" / m["paquete"])
    for rel in MOD_FILES + NEW_FILES:
        assert got[rel] == (repo / rel).read_bytes()
    assert got["Dockerfile"] == b"FROM python\n"           # resto del commit base
    assert got[".env.example"].startswith(b"GEMINI_API_KEY=YOUR")
    origen = {f["ruta"]: f["origen"] for f in m["archivos_fix3"]}
    assert origen["src/answer_presentation.py"] == "nuevo" and origen["app.py"] == "modificado"


def test_excluye_secretos_caches_logs_temporales_y_eval(repo, tmp_path):
    m = run(repo, tmp_path)
    got = members(tmp_path / "out" / m["paquete"])
    for bad in [".env", ".env.bak_rot", "streamlit.log", "src/__pycache__/x.cpython-312.pyc",
                "data/eval/fix3/res.json", "data/eval/benchmark_v2/splits/test_sealed.jsonl",
                "scratch/tmp.py", "scratch/notas.md"]:
        assert bad not in got
    blob = b"".join(got.values()) + (tmp_path / "out" / m["paquete"]).read_bytes()
    assert FAKE_GEMINI.encode() not in blob
    assert "scratch/tmp.py" in m["excluidos_del_commit_base"]


def test_manifiesto(repo, tmp_path):
    m = run(repo, tmp_path)
    out = tmp_path / "out"
    disk = json.loads((out / f"ijf_exp_{m['paquete_id']}.manifest.json").read_text(encoding="utf-8"))
    tar_bytes = (out / m["paquete"]).read_bytes()
    assert disk["commit_base"] == git(repo, "rev-parse", "--short=7", "HEAD").strip()
    assert disk["sha256_paquete"] == hashlib.sha256(tar_bytes).hexdigest()
    assert (out / (m["paquete"] + ".sha256")).read_text() == f"{disk['sha256_paquete']}  {m['paquete']}\n"
    assert disk["fecha_generacion"] and disk["total_archivos"] == len(disk["archivos_incluidos"])
    assert {f["ruta"] for f in disk["archivos_fix3"]} >= set(MOD_FILES + NEW_FILES)
    assert FAKE_GEMINI not in json.dumps(disk)


def test_reproducible(repo, tmp_path):
    a = run(repo, tmp_path)
    b = bp.build(str(repo), "HEAD", str(tmp_path / "out2"), authorized=MOD_FILES + NEW_FILES + ["deploy/exp/server_install_exp.sh"])
    assert a["sha256_paquete"] == b["sha256_paquete"] and a["paquete_id"] == b["paquete_id"]


def test_extraible_con_strip_components(repo, tmp_path):
    m = run(repo, tmp_path)
    if not shutil.which("tar"):
        pytest.skip("sin tar")
    dest = tmp_path / "rel"
    dest.mkdir()
    subprocess.run(["tar", "-xzf", str(tmp_path / "out" / m["paquete"]), "-C", str(dest), "--strip-components=1"], check=True)
    assert (dest / "src" / "answer_presentation.py").is_file() and not (dest / ".env").exists()


@pytest.mark.parametrize("files,code", [
    (MOD_FILES + ["src/no_existe.py"], 21),
    (MOD_FILES + [".env"], 22),
    (MOD_FILES + ["scratch/notas.md"], 22),
])
def test_rechaza_lista_invalida(repo, tmp_path, files, code):
    with pytest.raises(bp.PackError) as e:
        run(repo, tmp_path, files=files)
    assert e.value.code == code


def test_rechaza_codigo_nuevo_sin_incluir(repo, tmp_path):
    with pytest.raises(bp.PackError) as e:      # answer_presentation es nuevo y lo importa app.py
        run(repo, tmp_path, files=MOD_FILES + ["config/llm_pricing.json", "deploy/exp/server_install_exp.sh"])
    assert e.value.code == 24 and "answer_presentation" in str(e.value)


def test_rechaza_falta_marca_fix3(repo, tmp_path):
    w(repo, "src/decision_integrity.py", "sin marcas\n")
    with pytest.raises(bp.PackError) as e:
        run(repo, tmp_path)
    assert e.value.code == 24


def test_rechaza_secreto_en_archivo_incluido(repo, tmp_path):
    w(repo, "src/answer_presentation.py", f"K = '{FAKE_GEMINI}'\n")
    with pytest.raises(bp.PackError) as e:
        run(repo, tmp_path)
    assert e.value.code == 23 and FAKE_GEMINI not in str(e.value)
    assert not (tmp_path / "out").exists() or not list((tmp_path / "out").glob("*.tar.gz"))


def test_rechaza_valor_del_env_local(repo, tmp_path):
    w(repo, ".env", "GROQ_API_KEY=valor-local-muy-largo-123456\n")
    w(repo, "config/llm_pricing.json", '{"k": "valor-local-muy-largo-123456"}\n')
    with pytest.raises(bp.PackError) as e:
        run(repo, tmp_path)
    assert e.value.code == 23


def test_rechaza_head_distinto_del_base(repo, tmp_path):
    git(repo, "commit", "-q", "--allow-empty", "-m", "otro")
    with pytest.raises(bp.PackError) as e:
        bp.build(str(repo), "HEAD~1", str(tmp_path / "o"), authorized=MOD_FILES)
    assert e.value.code == 20


BIN_NUL = b"\x89PNG\r\n\x1a\n\x00\x00\r\nIEND\r\n"     # binario con NUL y CRLF
BIN_LATIN = b"\xff\xfe\xe9t\xe9\r\nfin\r\n"                # no es UTF-8 valido
TEXT_FILES = MOD_FILES + NEW_FILES + ["deploy/exp/server_install_exp.sh"]
BIN_FILES = ["assets/logo.png", "assets/tabla_latin1.dat"]


def _to_crlf(path):
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    path.write_bytes(data)
    assert b"\r\n" in data


def test_crlf_real_en_windows_da_el_mismo_sha256(repo, tmp_path):
    (repo / "assets").mkdir(exist_ok=True)
    (repo / BIN_FILES[0]).write_bytes(BIN_NUL)
    (repo / BIN_FILES[1]).write_bytes(BIN_LATIN)
    files = TEXT_FILES + BIN_FILES
    lf = bp.build(str(repo), "HEAD", str(tmp_path / "lf"), authorized=files)

    # Simulacion de un clon de Windows: core.autocrlf=true, checkout del commit base con CRLF
    # y archivos de trabajo (modificados y nuevos) guardados con CRLF.
    git(repo, "config", "core.autocrlf", "true")
    (repo / "Dockerfile").unlink()
    git(repo, "checkout", "--", "Dockerfile")
    assert (repo / "Dockerfile").read_bytes() == b"FROM python\r\n"
    for rel in TEXT_FILES:
        _to_crlf(repo / rel)
    crlf = bp.build(str(repo), "HEAD", str(tmp_path / "crlf"), authorized=files)

    assert crlf["sha256_paquete"] == lf["sha256_paquete"] and crlf["paquete_id"] == lf["paquete_id"]
    got = members(tmp_path / "crlf" / crlf["paquete"])
    assert got["Dockerfile"] == b"FROM python\n"
    for rel in TEXT_FILES:
        assert b"\r\n" not in got[rel] and got[rel] == (repo / rel).read_bytes().replace(b"\r\n", b"\n")
    assert got[BIN_FILES[0]] == BIN_NUL and got[BIN_FILES[1]] == BIN_LATIN   # binarios intactos
    norm = {f["ruta"]: f["crlf_normalizado"] for f in crlf["archivos_fix3"]}
    assert all(norm[r] for r in TEXT_FILES) and not any(norm[r] for r in BIN_FILES)
    assert not any({f["ruta"]: f["crlf_normalizado"] for f in lf["archivos_fix3"]}.values())


def test_normalize_eol_unitario():
    assert bp.normalize_eol(b"a\r\nb\n") == (b"a\nb\n", True)
    assert bp.normalize_eol(b"a\nb\n") == (b"a\nb\n", False)
    assert bp.normalize_eol("\u00f1\r\n".encode()) == ("\u00f1\n".encode(), True)
    assert bp.normalize_eol(BIN_NUL) == (BIN_NUL, False)
    assert bp.normalize_eol(BIN_LATIN) == (BIN_LATIN, False)
    assert bp.normalize_eol(b"solo\rCR") == (b"solo\rCR", False)

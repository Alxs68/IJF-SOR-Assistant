"""Instalador experimental (deploy/exp/server_install_exp.sh): instalacion correcta, fallos con reversion automatica
y barreras frente a produccion. Banco de pruebas con docker/curl/free/ss/git SIMULADOS, directorios temporales y una
"produccion" ficticia: no hay servidor, ni Docker real, ni red. Requiere bash (se omite en Windows sin bash)."""
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALLER = os.path.join(ROOT, "deploy", "exp", "server_install_exp.sh")
pytestmark = pytest.mark.skipif(sys.platform.startswith("win") or not shutil.which("bash"),
                                reason="requiere bash (Linux/macOS)")

FAKE_DOCKER = r'''#!/usr/bin/env bash
st="$FAKE_STATE"; echo "docker $* | cwd=$PWD" >> "$st/calls.log"
case "$1" in
  compose)
    shift; [ "$1" = "version" ] && exit 0
    act=""; while [ $# -gt 0 ]; do case "$1" in up|down) act=$1; shift;; -p|-f) shift 2;; *) shift;; esac; done
    if [ "$act" = up ]; then
      [ -n "$FAKE_UP_FAIL_REL" ] && [ "$PWD" = "$FAKE_UP_FAIL_REL" ] && exit 1
      echo "$PWD" > "$st/running"; touch "$st/exists"; exit 0
    fi
    if [ "$act" = down ]; then rm -f "$st/running" "$st/exists"; exit 0; fi ;;
  ps)
    if [ "$2" = "-a" ]; then echo ijf-sor-assistant; [ -f "$st/exists" ] && echo ijf-sor-assistant-exp; exit 0; fi
    echo ijf-sor-assistant; [ -f "$st/running" ] && echo ijf-sor-assistant-exp; exit 0 ;;
  rm)
    [ "$3" = "ijf-sor-assistant" ] && echo "VIOLACION_PRODUCCION rm" >> "$st/violations"
    rm -f "$st/running" "$st/exists"; exit 0 ;;
  inspect)
    case "$3" in *Config.Image*) echo prod-image:latest;; *) echo hf_vol_prod;; esac; exit 0 ;;
  restart|stop|start|kill)
    echo "VIOLACION_$1 $*" >> "$st/violations"; exit 0 ;;
  *) exit 0 ;;
esac
'''
FAKE_CURL = r'''#!/usr/bin/env bash
st="$FAKE_STATE"; url="${@: -1}"
case "$url" in
  *:8501/*) printf 200 ;;
  *:8510/*) if [ -f "$st/running" ] && [ "$(cat "$st/running")" != "$FAKE_HEALTH_FAIL_REL" ]; then printf 200; else printf 000; fi ;;
  *) printf 000 ;;
esac
'''
FAKE_FREE = '#!/usr/bin/env bash\necho "              total used free shared buff/cache available"\necho "Mem: 8000 1000 1000 10 1000 ${FAKE_AVAIL:-4000}"\n'
FAKE_SS = '#!/usr/bin/env bash\n[ -n "$FAKE_PORT_BUSY" ] && echo "LISTEN 0 128 127.0.0.1:8510 0.0.0.0:*"\nexit 0\n'
FAKE_GIT = '#!/usr/bin/env bash\necho fakecommit\n'


def _tree_hash(path):
    h = hashlib.sha256()
    for base, _, files in sorted(os.walk(path)):
        for f in sorted(files):
            p = os.path.join(base, f)
            h.update(p.encode()); h.update(open(p, "rb").read())
    return h.hexdigest()


@pytest.fixture
def env(tmp_path):
    bin_ = tmp_path / "bin"; bin_.mkdir()
    for name, body in (("docker", FAKE_DOCKER), ("curl", FAKE_CURL), ("free", FAKE_FREE), ("ss", FAKE_SS), ("git", FAKE_GIT)):
        p = bin_ / name; p.write_text(body); p.chmod(0o755)
    state = tmp_path / "state"; state.mkdir()
    prod = tmp_path / "prod"; prod.mkdir(); (prod / ".env").write_text("GEMINI_API_KEY=prod-key\n"); (prod / "app.py").write_text("prod")
    exp = tmp_path / "exp"; (exp / "releases").mkdir(parents=True)
    src = tmp_path / "pkg" / "ijf_exp_newsha"; src.mkdir(parents=True); (src / "app.py").write_text("new")
    tar = tmp_path / "ijf_exp_newsha.tar.gz"
    with tarfile.open(tar, "w:gz") as t:
        t.add(src, arcname="ijf_exp_newsha")
    base = {**os.environ, "PATH": f"{bin_}:{os.environ['PATH']}", "FAKE_STATE": str(state), "PROD_DIR": str(prod),
            "EXP_ROOT": str(exp), "HEALTH_TRIES": "2", "HEALTH_SLEEP": "0"}
    return {"tmp": tmp_path, "state": state, "prod": prod, "exp": exp, "tar": tar, "env": base}


def _previous(e, running=True):
    """Simula una version experimental anterior instalada (directorio con compose y current apuntando a ella)."""
    prev = e["exp"] / "releases" / "oldsha"; prev.mkdir()
    (prev / "docker-compose.exp.yml").write_text("services: {}\n"); (prev / "app.py").write_text("old")
    os.symlink(prev, e["exp"] / "current")
    (e["state"] / "exists").touch()
    if running:
        (e["state"] / "running").write_text(str(prev))
    return prev


def _run(e, **extra):
    prod_before = _tree_hash(e["prod"])
    r = subprocess.run(["bash", INSTALLER, str(e["tar"])], env={**e["env"], **extra}, capture_output=True, text=True, timeout=60)
    calls = (e["state"] / "calls.log").read_text() if (e["state"] / "calls.log").exists() else ""
    # Barreras comunes a TODOS los escenarios: produccion intacta y sin operaciones sobre ella.
    assert _tree_hash(e["prod"]) == prod_before, "el directorio de produccion cambio"
    assert not (e["state"] / "violations").exists(), (e["state"] / "violations").read_text()
    assert f"cwd={e['prod']}" not in calls
    for line in calls.splitlines():
        if " ijf-sor-assistant " in line + " " and not line.startswith("docker inspect"):
            pytest.fail("operacion sobre el contenedor de produccion: " + line)
    return r, calls


def _current(e):
    return os.path.realpath(e["exp"] / "current")


def _running(e):
    f = e["state"] / "running"
    return f.read_text().strip() if f.exists() else None


def test_successful_install_replaces_previous_and_keeps_it(env):
    prev = _previous(env)
    r, calls = _run(env)
    new = str(env["exp"] / "releases" / "newsha")
    assert r.returncode == 0, r.stdout + r.stderr
    assert _current(env) == new and _running(env) == new
    assert (prev / "app.py").read_text() == "old"                     # version anterior intacta
    assert "RESULTADO: INSTALADA" in r.stdout
    compose = open(os.path.join(new, "docker-compose.exp.yml")).read()
    for flag in ("ADA_UNIFIED_ANSWER", "RRE_CHANNEL_CHAMPIONS", "ADA_TRANSLATE_ANY_LANG", "DIG_11_SUBORDINATE", "DIG06_REFS"):
        assert f'{flag}: "1"' in compose                               # interruptores solo en el compose experimental
    assert '"127.0.0.1:8510:8501"' in compose and "ijf-sor-assistant-exp" in compose


@pytest.mark.parametrize("fail", ["health", "up", "ram"])
def test_failure_after_stopping_previous_restores_it(env, fail):
    prev = _previous(env)
    new = str(env["exp"] / "releases" / "newsha")
    extra = {"health": {"FAKE_HEALTH_FAIL_REL": new}, "up": {"FAKE_UP_FAIL_REL": new}, "ram": {"FAKE_AVAIL": "500"}}[fail]
    r, calls = _run(env, **extra)
    assert r.returncode == 10, r.stdout + r.stderr
    assert _current(env) == str(prev) and _running(env) == str(prev)
    assert "ERROR en el paso" in r.stdout and "REVERSION CORRECTA" in r.stdout
    assert os.path.isdir(new)                                         # la nueva tampoco se borra (diagnostico)
    assert (prev / "app.py").read_text() == "old"


def test_failure_with_previous_not_running_only_restores_link(env):
    prev = _previous(env, running=False)
    new = str(env["exp"] / "releases" / "newsha")
    r, _ = _run(env, FAKE_HEALTH_FAIL_REL=new)
    assert r.returncode == 10 and _current(env) == str(prev) and _running(env) is None
    assert "no estaba en ejecucion" in r.stdout


def test_failure_without_previous_version(env):
    new = str(env["exp"] / "releases" / "newsha")
    r, _ = _run(env, FAKE_HEALTH_FAIL_REL=new)
    assert r.returncode == 12 and "FALLO SIN VERSION ANTERIOR" in r.stdout and _running(env) is None


def test_abort_before_stopping_previous_changes_nothing(env):
    prev = _previous(env)
    os.remove(env["tar"])                                             # paquete inexistente: falla en la extraccion
    r, _ = _run(env)
    assert r.returncode == 2 and _current(env) == str(prev) and _running(env) == str(prev)


def test_same_sha_never_overwrites_existing_release(env):
    same = env["exp"] / "releases" / "newsha"; same.mkdir(); (same / "app.py").write_text("ya instalada")
    (same / "docker-compose.exp.yml").write_text("services: {}\n")
    os.symlink(same, env["exp"] / "current"); (env["state"] / "exists").touch(); (env["state"] / "running").write_text(str(same))
    r, _ = _run(env)
    assert r.returncode == 0 and (same / "app.py").read_text() == "ya instalada"
    assert _current(env) != str(same) and os.path.basename(_current(env)).startswith("newsha_")


def test_barrier_exp_root_inside_production(env):
    r, _ = _run(env, EXP_ROOT=str(env["prod"] / "exp"))
    assert r.returncode == 6 and "ABORTO" in r.stdout


def test_barrier_port_and_container_cannot_be_production(env):
    r, _ = _run(env, EXP_PORT="8501")
    assert r.returncode == 6

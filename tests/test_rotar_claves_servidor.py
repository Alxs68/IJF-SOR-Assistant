"""Pruebas locales de deploy/exp/rotar_claves_servidor.sh con docker, curl, git y mv simulados.

No hay red, ni OCI, ni proveedores: el script solo ve los programas falsos de este archivo.
"""
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "deploy" / "exp" / "rotar_claves_servidor.sh"
pytestmark = pytest.mark.skipif(sys.platform.startswith("win") or not shutil.which("bash"),
                                reason="requiere bash (se ejecuta en Linux)")

OLD_G, OLD_Q = "OLDgemini" + "o" * 30 + "ro_g", "OLDgroq" + "o" * 30 + "xD2T"
NEW_G, NEW_Q = "NEWgemini" + "n" * 30 + "AB12", "NEWgroq" + "n" * 30 + "CD34"
ENV_TXT = f"LLM_PROVIDER=Gemini\nGEMINI_API_KEY={OLD_G}\nOTRA=1\nGROQ_API_KEY={OLD_Q}\nGEMINI_MODEL=x\n"

FAKE_DOCKER = r"""#!/bin/bash
S="$SIM"
case "$1" in
  inspect) echo "sha256:abcdef1234567890ffff";;
  compose)
    if [[ "$*" == *ijf-exp* ]]; then who=exp; src="$EXPC/.env"; else who=prod; src="$PROD/.env"; fi
    echo "compose $who" >> "$S/log"
    [ -f "$S/fail_compose_$who" ] && exit 1
    cp "$src" "$S/loaded_$who.env"; exit 0;;
  exec)
    who=prod; [ "$2" = ijf-sor-assistant-exp ] && who=exp
    grep "^$4=" "$S/loaded_$who.env" | cut -d= -f2-;;
esac
"""
FAKE_CURL = r"""#!/bin/bash
S="$SIM"; port=8501; who=prod
if [[ "$*" == *8510* ]]; then port=8510; who=exp; fi
if [ -f "$S/unhealthy_$who" ] && grep -q NEW "$S/loaded_$who.env"; then echo 502; else echo 200; fi
"""
FAKE_GIT = r"""#!/bin/bash
case "$*" in *rev-parse*) echo abc1234;; *status*) echo "";; esac
"""
FAKE_MV = r"""#!/bin/bash
for a in "$@"; do last="$a"; done
if [ -n "$FAIL_MV" ] && [[ "$last" == $FAIL_MV ]]; then echo "mv: fallo simulado" >&2; exit 1; fi
exec /bin/mv "$@"
"""


@pytest.fixture
def sim(tmp_path):
    s = tmp_path / "sim"; b = tmp_path / "bin"; prod = tmp_path / "prod"; exp = tmp_path / "exp"
    for d in (s, b, prod, exp):
        d.mkdir()
    for d in (prod, exp):
        (d / ".env").write_text(ENV_TXT)
    for who, d in (("prod", prod), ("exp", exp)):
        shutil.copy(d / ".env", s / f"loaded_{who}.env")
    for name, body in (("docker", FAKE_DOCKER), ("curl", FAKE_CURL), ("git", FAKE_GIT), ("mv", FAKE_MV)):
        p = b / name; p.write_text(body); p.chmod(p.stat().st_mode | stat.S_IXUSR)
    env = {"PATH": f"{b}:/usr/bin:/bin", "SIM": str(s), "PROD": str(prod), "EXPC": str(exp),
           "HEALTH_TRIES": "2", "HEALTH_SLEEP": "0", "HOME": str(tmp_path)}
    return {"s": s, "prod": prod, "exp": exp, "env": env}


def run(sim, stdin=f"{NEW_G}\n{NEW_Q}\n", **extra):
    r = subprocess.run(["bash", str(SCRIPT)], input=stdin, env={**sim["env"], **extra},
                       capture_output=True, text=True, timeout=60)
    out = r.stdout + r.stderr
    for k in (OLD_G, OLD_Q, NEW_G, NEW_Q):     # nunca una clave completa en la salida
        assert k not in out
    return r.returncode, out


def env_of(path):
    return Path(path).read_text()


def compose_calls(sim):
    log = sim["s"] / "log"
    return log.read_text().split() if log.exists() else []


def test_rotacion_normal(sim):
    rc, out = run(sim)
    assert rc == 0 and "RESULTADO: ROTACION APLICADA" in out
    for d in (sim["prod"], sim["exp"]):
        txt = env_of(d / ".env")
        assert f"GEMINI_API_KEY={NEW_G}" in txt and f"GROQ_API_KEY={NEW_Q}" in txt and OLD_G not in txt
        assert [l for l in txt.splitlines() if "_API_KEY" not in l] == ["LLM_PROVIDER=Gemini", "OTRA=1", "GEMINI_MODEL=x"]
        assert env_of(d / ".env.bak_rot") == ENV_TXT              # respaldo conservado
        assert not (d / ".env.tmp").exists()
    assert compose_calls(sim).count("prod") == 1                  # produccion se reinicia una sola vez
    assert "...AB12" in out and "archivos de codigo: sin cambios" in out


@pytest.mark.parametrize("which", ["prod", "exp"])
def test_fallo_al_sustituir_restaura_ambos(sim, which):
    rc, out = run(sim, FAIL_MV=f"*/{which}/.env")
    assert rc == 3 and "SIN CAMBIOS" in out
    for d in (sim["prod"], sim["exp"]):
        assert env_of(d / ".env") == ENV_TXT
        assert env_of(d / ".env.bak_rot") == ENV_TXT
        assert not (d / ".env.tmp").exists()
    assert compose_calls(sim) == []                               # no se reinicio nada


def test_produccion_no_sana_revierte_ambos(sim):
    (sim["s"] / "unhealthy_prod").touch()
    rc, out = run(sim)
    assert rc == 10 and "REVERTIDO" in out and "...ro_g" in out
    for d in (sim["prod"], sim["exp"]):
        assert env_of(d / ".env") == ENV_TXT and env_of(d / ".env.bak_rot") == ENV_TXT
    assert "exp" not in compose_calls(sim)                        # la experimental no se toco


def test_fallo_compose_produccion_revierte(sim):
    (sim["s"] / "fail_compose_prod").touch()
    rc, out = run(sim)
    assert rc == 10 and "REVERTIDO" in out
    assert env_of(sim["prod"] / ".env") == ENV_TXT and env_of(sim["exp"] / ".env") == ENV_TXT


@pytest.mark.parametrize("flag,msg", [("fail_compose_exp", "fallo docker compose"),
                                      ("unhealthy_exp", "no responde 200 en 8510")])
def test_fallo_experimental_se_informa(sim, flag, msg):
    (sim["s"] / flag).touch()
    rc, out = run(sim)
    assert rc == 21 and f"FALLO DE LA EXPERIMENTAL: {msg}" in out
    assert "ROTACION APLICADA" not in out
    assert f"GEMINI_API_KEY={NEW_G}" in env_of(sim["prod"] / ".env")   # produccion queda rotada y sana
    assert env_of(sim["exp"] / ".env.bak_rot") == ENV_TXT


def test_una_sola_clave_no_cambia_nada(sim):
    rc, out = run(sim, stdin=f"{NEW_G}\n")
    assert rc == 1 and env_of(sim["prod"] / ".env") == ENV_TXT
    assert not (sim["prod"] / ".env.bak_rot").exists() and compose_calls(sim) == []


def test_respaldo_existente_no_se_sobrescribe(sim):
    (sim["exp"] / ".env.bak_rot").write_text("respaldo previo\n")
    rc, out = run(sim)
    assert rc == 2
    assert env_of(sim["exp"] / ".env.bak_rot") == "respaldo previo\n"
    assert env_of(sim["prod"] / ".env") == ENV_TXT and not (sim["prod"] / ".env.bak_rot").exists()

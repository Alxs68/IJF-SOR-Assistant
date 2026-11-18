"""Empaqueta el estado de trabajo autorizado para la instancia EXPERIMENTAL, sin commit.

Paquete = arbol del commit base (git archive, solo lectura) + archivos autorizados tomados
del directorio de trabajo (modificados o nuevos), menos exclusiones (secretos, caches,
logs, temporales, datos de evaluacion). No ejecuta git add, commit, stash ni push, no
escribe objetos en .git ni cambia el indice: usa solo comandos de lectura con
GIT_OPTIONAL_LOCKS=0.

Salida en --out:
  ijf_exp_<id>.tar.gz           paquete reproducible (mismo contenido -> mismo SHA-256)
  ijf_exp_<id>.tar.gz.sha256    para sha256sum -c en el servidor
  ijf_exp_<id>.manifest.json    commit base, archivos, hashes, fecha

  python deploy/exp/build_package_exp.py --base d126873 --out deploy/exp/out --secrets-from .env

Codigos de salida: 0 ok; 20 HEAD distinto del commit base; 21 falta un archivo autorizado;
22 un archivo autorizado esta excluido; 23 posible secreto en el paquete; 24 falta contenido
necesario; 25 modulo local importado y ausente; 26 la verificacion del paquete no coincide.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile

# Archivos FIX3 autorizados (rutas con "/"). Se toman del directorio de trabajo.
AUTHORIZED = [
    "app.py", "src/ada_assistant.py", "src/decision_integrity.py", "src/llm_provider.py",
    "src/rre_engine.py", "src/answer_presentation.py",
    "scripts/eval_llm_shadow.py", "scripts/replay_dig_v3.py", "scripts/check_llm_quota.py",
    "scripts/eval_ab_dev.py", "scripts/post_ab_reanalysis.py",
    "scripts/replay_unified_answer.py", "scripts/run_eval_ab.ps1", "scripts/run_eval_unified.ps1",
    "scripts/run_eval_fix3.ps1", "scripts/eval_r1_channel_champions.py", "scripts/summarize_repeated_ab.py",
    "tests/test_dig_v3_fixes.py", "tests/test_r3_dig_v2_integration.py", "tests/test_llm_schema_rigor.py",
    "tests/test_post_ab_fixes.py", "tests/test_unified_answer.py", "tests/test_unified_dig.py",
    "tests/test_fix_trazabilidad.py", "tests/conftest.py", "tests/test_aislamiento_proveedores.py",
    "tests/test_install_exp_rollback.py", "tests/test_build_package_exp.py",
    "scripts/llm_cost.py", "config/llm_pricing.json",
    "deploy/exp/server_install_exp.sh", "deploy/exp/deploy_fix3_exp.ps1", "deploy/exp/build_package_exp.py",
    "docs/audits/EVALUACION_AB_ESQUEMA_REGLA14.md", "docs/audits/INFORME_CORRECCIONES_POST_EVALUACION_AB.md",
    "docs/audits/DIAGNOSTICO_DIG11_DIG09_GENERACION.md",
    "docs/audits/INFORME_INTERVENCION_RECUPERACION_GENERACION_DIG11.md",
    "docs/audits/AUDITORIA_TRAZABILIDAD_RRE_GEMINI_DIG.md", "docs/audits/VERIFICACION_BILLING_CUOTAS_GEMINI.md",
]

# Exclusiones (sobre la ruta relativa; un patron con "/" final excluye la carpeta entera).
EXCLUDE_DIRS = ["scratch/", "data/eval/", "data/test_corpus_multisource_temp/", "tests/temp_test_dir/",
                "deploy/exp/out/", ".pytest_cache/", ".venv/", "venv/", ".git/"]
EXCLUDE_GLOBS = [".env", ".env.*", "*.key", "*.pem", "*.p12", "*.pfx", "*.bak", "*.bak_*", "*.bak.*",
                 "*bak_rot*", "*.log", "*.pyc", "*.pyo", "*.bundle", "*.tmp", "*.swp", "*~"]
EXCLUDE_PARTS = ["__pycache__", ".ipynb_checkpoints", ".pytest_cache"]
KEEP = {".env.example"}

# Contenido minimo para que la instancia arranque con FIX3.
REQUIRED_FILES = ["app.py", "Dockerfile", "requirements.txt", ".dockerignore", "src/ada_assistant.py",
                  "src/decision_integrity.py", "src/llm_provider.py", "src/rre_engine.py",
                  "src/answer_presentation.py", "src/corpus_config.py", "config/llm_pricing.json"]
REQUIRED_DIRS = ["data/processed/rebuild_2026_08_corrected/", "data/derived/", "data/corpus_multisource/"]
REQUIRED_MARKERS = {  # archivo -> texto que demuestra que es la version FIX3
    "src/decision_integrity.py": ["DIG_11_SUBORDINATE", "DIG06_REFS", "ADA_UNIFIED_ANSWER"],
    "src/rre_engine.py": ["RRE_CHANNEL_CHAMPIONS"],
    "src/ada_assistant.py": ["ADA_TRANSLATE_ANY_LANG", "validated_answer"],
    "deploy/exp/server_install_exp.sh": ["rollback", "EXP_FIX3"],
}

SECRET_PATTERNS = [re.compile(p) for p in (
    rb"AIza[0-9A-Za-z_\-]{30,}", rb"AQ\.[0-9A-Za-z_\-]{30,}", rb"gsk_[0-9A-Za-z]{30,}",
    rb"-----BEGIN [A-Z ]*PRIVATE KEY-----")]
SECRET_ENV_NAME = re.compile(r"^\s*(?:export\s+)?([A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*)\s*=\s*(.*)$")


class PackError(Exception):
    def __init__(self, code: int, msg: str):
        super().__init__(msg)
        self.code = code


def _git(repo: str, *args: str) -> bytes:
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, env=env).stdout


def is_excluded(path: str) -> bool:
    if path in KEEP:
        return False
    if any(path.startswith(d) for d in EXCLUDE_DIRS):
        return True
    parts = path.split("/")
    if any(p in EXCLUDE_PARTS for p in parts):
        return True
    return any(fnmatch.fnmatch(parts[-1], g) for g in EXCLUDE_GLOBS)


def secret_values(env_file: str | None) -> list[bytes]:
    """Valores de claves del .env local, solo en memoria, para comprobar que no estan en el paquete."""
    if not env_file or not os.path.isfile(env_file):
        return []
    vals = []
    with open(env_file, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = SECRET_ENV_NAME.match(line)
            if m:
                v = m.group(2).strip().strip('"').strip("'")
                if len(v) >= 16:
                    vals.append(v.encode())
    return vals


def find_secrets(data: bytes, values: list[bytes]) -> bool:
    return any(p.search(data) for p in SECRET_PATTERNS) or any(v in data for v in values)


def normalize_eol(data: bytes) -> tuple[bytes, bool]:
    """Texto UTF-8 (sin bytes NUL): CRLF -> LF, como esta guardado en el repositorio y en el checkout
    Linux de produccion, para que el paquete sea igual en Windows y en Linux. Binarios: sin cambios."""
    if b"\0" in data:
        return data, False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return data, False
    out = data.replace(b"\r\n", b"\n")
    return out, out != data


def local_imports(source: str) -> set[str]:
    mods = set()
    for m in re.finditer(r"^\s*(?:from\s+([A-Za-z_][\w.]*)\s+import|import\s+([A-Za-z_][\w.]*))", source, re.M):
        mods.add((m.group(1) or m.group(2)).split(".")[0])
    return mods


def build(repo: str, base: str, out_dir: str, secrets_from: str | None = None,
          authorized: list[str] | None = None, now: dt.datetime | None = None) -> dict:
    repo = os.path.abspath(repo)
    authorized = list(AUTHORIZED if authorized is None else authorized)
    head = _git(repo, "rev-parse", "HEAD").decode().strip()
    base_full = _git(repo, "rev-parse", "--verify", base + "^{commit}").decode().strip()
    if head != base_full:
        raise PackError(20, f"HEAD {head[:7]} no es el commit base {base_full[:7]}")
    base_time = int(_git(repo, "show", "-s", "--format=%ct", base_full).decode().strip())

    # 1. Archivos autorizados del directorio de trabajo
    overlay: dict[str, bytes] = {}
    eol_normalized: list[str] = []
    for rel in authorized:
        if is_excluded(rel):
            raise PackError(22, f"archivo autorizado en una exclusion: {rel}")
        p = os.path.join(repo, *rel.split("/"))
        if not os.path.isfile(p):
            raise PackError(21, f"falta el archivo autorizado: {rel}")
        with open(p, "rb") as fh:
            data, normalized = normalize_eol(fh.read())
        overlay[rel] = data
        if normalized:
            eol_normalized.append(rel)

    # 2. Arbol del commit base (solo lectura) menos exclusiones
    # core.autocrlf=false: contenido exacto del repositorio (LF, como el checkout Linux de produccion),
    # igual en Windows y en Linux, para que el paquete sea reproducible.
    base_tar = tarfile.open(fileobj=io.BytesIO(_git(repo, "-c", "core.autocrlf=false", "archive", "--format=tar", base_full)))
    files: dict[str, tuple[bytes, int]] = {}
    base_paths, excluded = set(), []
    for m in base_tar.getmembers():
        if not m.isfile():
            continue
        base_paths.add(m.name)
        if is_excluded(m.name):
            excluded.append(m.name)
            continue
        files[m.name] = (base_tar.extractfile(m).read(), m.mode & 0o777)
    for rel, data in overlay.items():
        mode = files.get(rel, (b"", 0o755 if rel.endswith(".sh") else 0o644))[1]
        files[rel] = (data, mode)

    # 3. Modificaciones del directorio de trabajo que NO entran (para el manifiesto)
    changed = [l for l in _git(repo, "diff", "--name-only", base_full).decode().splitlines() if l]
    untracked = [l for l in _git(repo, "ls-files", "--others", "--exclude-standard").decode().splitlines() if l]
    not_included = sorted(set(p for p in changed + untracked if p not in overlay))
    code_left_out = [p for p in not_included if (p.startswith("src/") or p.startswith("config/") or p == "app.py")
                     and p.endswith((".py", ".json", ".yml", ".yaml", ".toml")) and not is_excluded(p)]

    # 4. Comprobaciones de contenido
    problems = [f"falta {f}" for f in REQUIRED_FILES if f not in files]
    problems += [f"carpeta vacia o ausente {d}" for d in REQUIRED_DIRS if not any(k.startswith(d) for k in files)]
    for f, marks in REQUIRED_MARKERS.items():
        if f in files:
            problems += [f"{f} no contiene {mk}" for mk in marks if mk.encode() not in files[f][0]]
    problems += [f"codigo modificado/nuevo sin incluir: {p}" for p in code_left_out]
    if problems:
        raise PackError(24, "; ".join(problems))
    src_mods = {k[4:-3] for k in files if k.startswith("src/") and k.count("/") == 1 and k.endswith(".py")}
    wt_src = {f[:-3] for f in os.listdir(os.path.join(repo, "src")) if f.endswith(".py")}
    missing_mods = set()
    for k in [k for k in files if k == "app.py" or (k.startswith("src/") and k.endswith(".py"))]:
        missing_mods |= {m for m in local_imports(files[k][0].decode("utf-8", "replace"))
                         if m in wt_src and m not in src_mods}
    if missing_mods:
        raise PackError(25, "modulos locales importados y ausentes: " + ", ".join(sorted(missing_mods)))
    values = secret_values(secrets_from)
    leaked = sorted(k for k, (d, _) in files.items() if find_secrets(d, values))
    if leaked:
        raise PackError(23, "posible secreto en: " + ", ".join(leaked))

    # 5. Paquete reproducible
    digest = hashlib.sha256()
    for k in sorted(files):
        digest.update(k.encode() + b"\0" + hashlib.sha256(files[k][0]).digest())
    pkg_id = f"{base_full[:7]}-w{digest.hexdigest()[:8]}"
    prefix = f"ijf_exp_{pkg_id}/"
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as t:
        for k in sorted(files):
            data, mode = files[k]
            ti = tarfile.TarInfo(prefix + k)
            ti.size, ti.mode, ti.mtime = len(data), mode, base_time
            ti.uid = ti.gid = 0
            ti.uname = ti.gname = ""
            t.addfile(ti, io.BytesIO(data))
    gz = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=gz, mtime=0) as g:
        g.write(raw.getvalue())
    os.makedirs(out_dir, exist_ok=True)
    tar_name = f"ijf_exp_{pkg_id}.tar.gz"
    tar_path = os.path.join(out_dir, tar_name)
    with open(tar_path, "wb") as fh:
        fh.write(gz.getvalue())
    tar_sha = hashlib.sha256(gz.getvalue()).hexdigest()
    with open(tar_path + ".sha256", "w", newline="\n") as fh:
        fh.write(f"{tar_sha}  {tar_name}\n")

    # 6. Verificacion: se vuelve a leer el paquete escrito
    with tarfile.open(tar_path, "r:gz") as t:
        got = {m.name[len(prefix):]: t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
        bad_names = [m.name for m in t.getmembers() if not m.name.startswith(prefix) or ".." in m.name.split("/")]
    mismatch = sorted(set(got) ^ set(files)) + [k for k in overlay if got.get(k) != overlay[k]] + bad_names
    if mismatch or any(is_excluded(k) for k in got):
        raise PackError(26, "el paquete escrito no coincide: " + ", ".join(mismatch[:10]))

    now = now or dt.datetime.now().astimezone()
    manifest = {
        "paquete": tar_name, "paquete_id": pkg_id, "sha256_paquete": tar_sha,
        "fecha_generacion": now.isoformat(timespec="seconds"),
        "commit_base": base_full[:7], "commit_base_completo": base_full,
        "metodo": "arbol del commit base + archivos autorizados del directorio de trabajo; sin commit",
        "finales_de_linea": "LF en texto (commit base con core.autocrlf=false; CRLF->LF en los archivos de trabajo); binarios intactos",
        "total_archivos": len(files),
        "archivos_fix3": [{"ruta": k, "origen": "modificado" if k in base_paths else "nuevo",
                           "sha256": hashlib.sha256(overlay[k]).hexdigest(), "bytes": len(overlay[k]),
                           "crlf_normalizado": k in eol_normalized}
                          for k in sorted(overlay)],
        "archivos_incluidos": sorted(files),
        "excluidos_del_commit_base": sorted(excluded),
        "cambios_locales_no_incluidos": not_included,
        "reglas_exclusion": {"carpetas": EXCLUDE_DIRS, "nombres": EXCLUDE_GLOBS, "partes": EXCLUDE_PARTS,
                             "se_conserva": sorted(KEEP)},
        "comprobaciones": {"contenido_necesario": "ok", "modulos_locales": "ok",
                           "secretos": "ok" + (" (incluye valores del .env local)" if values else ""),
                           "relectura_paquete": "ok"},
    }
    with open(os.path.join(out_dir, f"ijf_exp_{pkg_id}.manifest.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--secrets-from", default=None)
    a = ap.parse_args(argv)
    try:
        m = build(a.repo, a.base, a.out, a.secrets_from)
    except PackError as e:
        print(f"ABORTO ({e.code}): {e}")
        return e.code
    print(f"Commit base: {m['commit_base']}  |  archivos: {m['total_archivos']}  |  FIX3: {len(m['archivos_fix3'])} "
          f"({sum(f['origen'] == 'nuevo' for f in m['archivos_fix3'])} nuevos)")
    print(f"Excluidos del commit base: {len(m['excluidos_del_commit_base'])}  |  cambios locales no incluidos: "
          f"{len(m['cambios_locales_no_incluidos'])}")
    print(f"SHA-256: {m['sha256_paquete']}")
    print(f"PAQUETE_ID={m['paquete_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

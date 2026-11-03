"""Acquire and verify the official IJF SOR 2026-08 source PDF.

The expected digest and official URL are pinned independently of the source manifest.
The large PDF is acquired by CI rather than committed to Git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

EXPECTED_SHA256 = "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620"
EXPECTED_URL = (
    "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/"
    "up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf"
)
EXPECTED_RELATIVE_PATH = Path(
    "data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf"
)
MANIFEST_RELATIVE_PATH = Path("data/raw/sor_2026_08_rebuild/source_manifest.json")


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_count = 0
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
            byte_count += len(chunk)
    return digest.hexdigest(), byte_count


def verify_manifest(repo_root: Path) -> tuple[dict, Path]:
    manifest_path = repo_root / MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        raise RuntimeError(f"Manifiesto de fuente ausente: {manifest_path}")
    with manifest_path.open("r", encoding="utf-8") as stream:
        manifest = json.load(stream)

    if str(manifest.get("sha256", "")).lower() != EXPECTED_SHA256:
        raise RuntimeError("El SHA-256 del manifiesto no coincide con el digest oficial fijado.")
    if manifest.get("download_url") != EXPECTED_URL:
        raise RuntimeError("La URL de descarga del manifiesto no coincide con la fuente oficial fijada.")
    if Path(manifest.get("local_storage_path", "")) != EXPECTED_RELATIVE_PATH:
        raise RuntimeError("La ruta de almacenamiento del manifiesto es inesperada.")

    return manifest, repo_root / EXPECTED_RELATIVE_PATH


def acquire_pdf(url: str, target: Path, expected_size: int) -> tuple[str, int]:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=target.name + ".",
        suffix=".part",
        dir=str(target.parent),
    )
    temp_path = Path(temporary_name)
    digest = hashlib.sha256()
    byte_count = 0
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "IJF-SOR-Assistant-source-verification/1.0"},
    )

    try:
        with os.fdopen(fd, "wb") as output:
            last_error: Exception | None = None
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(request, timeout=120) as response:
                        if response.status != 200:
                            raise RuntimeError(f"HTTP inesperado al descargar fuente: {response.status}")
                        while chunk := response.read(1024 * 1024):
                            output.write(chunk)
                            digest.update(chunk)
                            byte_count += len(chunk)
                    last_error = None
                    break
                except Exception as exc:
                    last_error = exc
                    raise
            if last_error is not None:
                raise RuntimeError(f"No fue posible descargar el PDF oficial: {last_error}")

            output.flush()
            os.fsync(output.fileno())

        actual_sha = digest.hexdigest().lower()
        if byte_count != expected_size:
            raise RuntimeError(
                f"Tamaño del PDF distinto al manifiesto: {byte_count}; esperado {expected_size}."
            )
        if actual_sha != EXPECTED_SHA256:
            raise RuntimeError(
                f"SHA-256 del PDF descargado incorrecto: {actual_sha}; esperado {EXPECTED_SHA256}."
            )
        os.replace(temp_path, target)
        return actual_sha, byte_count
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        finally:
            raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--download-if-missing",
        action="store_true",
        help="Descargar el PDF oficial si aún no existe en la ruta indicada por el manifiesto.",
    )
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]

    try:
        manifest, pdf_path = verify_manifest(repo_root)
        expected_size = int(manifest.get("file_size_bytes", 0))
        if expected_size <= 0:
            raise RuntimeError("El manifiesto no contiene un file_size_bytes válido.")

        if pdf_path.is_file():
            actual_sha, actual_size = sha256_file(pdf_path)
            if actual_size != expected_size:
                raise RuntimeError(
                    f"Tamaño del PDF físico incorrecto: {actual_size}; esperado {expected_size}."
                )
            if actual_sha.lower() != EXPECTED_SHA256:
                raise RuntimeError(
                    f"SHA-256 del PDF físico incorrecto: {actual_sha}; esperado {EXPECTED_SHA256}."
                )
            print(f"✓ PDF físico verificado: SHA-256={actual_sha}; bytes={actual_size}.")
            return 0

        if not args.download_if_missing:
            raise RuntimeError(
                f"PDF físico ausente en {pdf_path}; use --download-if-missing para adquirirlo y verificarlo."
            )

        for attempt in range(1, 4):
            try:
                actual_sha, actual_size = acquire_pdf(
                    manifest["download_url"], pdf_path, expected_size
                )
                print(f"✓ PDF oficial descargado y verificado: SHA-256={actual_sha}; bytes={actual_size}.")
                return 0
            except Exception as exc:
                if attempt == 3:
                    raise
                print(f"Intento {attempt}/3 fallido: {exc}. Reintentando...", file=sys.stderr)
                time.sleep(attempt * 3)
        return 1
    except Exception as exc:
        print(f"ERROR de verificación de fuente SOR 2026-08: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

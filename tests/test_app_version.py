"""Version oficial de la aplicacion: fuente unica, SemVer y coherencia con la documentacion y la interfaz."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from app_version import APP_VERSION, RELEASE_DATE  # noqa: E402
from i18n import t  # noqa: E402


def _read(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return f.read()


def test_semver_and_after_v1_4_0():
    assert re.fullmatch(r"\d+\.\d+\.\d+", APP_VERSION)
    assert tuple(map(int, APP_VERSION.split("."))) > (1, 4, 0)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", RELEASE_DATE)


def test_docs_declare_same_version():
    v = APP_VERSION
    assert f"## v{v} — {RELEASE_DATE}" in _read("CHANGELOG.md")
    assert f"v{v}" in _read("README.md").splitlines()[0]
    assert os.path.exists(os.path.join(ROOT, "docs", "deployment", f"RELEASE_v{v}_{RELEASE_DATE}.md"))


def test_ui_and_feedback_use_single_source():
    for lang in ("es", "en"):
        assert APP_VERSION in t("sidebar_version_label", lang, version=APP_VERSION)
    src = _read("app.py")
    assert 't("sidebar_version_label", lang, version=APP_VERSION)' in src
    assert '"app_version": APP_VERSION' in src
    assert '"3.2.0"' not in src

"""Textos de la barra lateral (auditoria 2026-11-21): vigentes, coherentes ES/EN y sin promesas que el sistema no cumple.
Sin red ni modelos."""
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from corpus_config import get_active_corpus_config  # noqa: E402
from i18n import TRANSLATIONS, t  # noqa: E402

SIDEBAR_KEYS = [
    "sidebar_howto_title", "sidebar_about_title", "sidebar_about_project_title", "sidebar_about_project_content",
    "sidebar_rules_edition", "sidebar_sources_title", "sidebar_sources_content", "sidebar_author_title",
    "sidebar_author_content", "sidebar_version_title", "sidebar_version_rules", "sidebar_source_hash",
    "sidebar_version_label", "availability_title", "availability_desc", "sidebar_admin_title",
] + [f"sidebar_howto_{k}_{p}" for k in ("ask", "read", "abstain", "history", "notice") for p in ("title", "content")]

# Afirmaciones que la auditoria encontro incorrectas o desactualizadas.
OBSOLETE = [r"gratuit", r"free[- ]tier", r"Modo Alternativo Local", r"Local Alternative Mode", r"predefinid",
            r"quick suggestions", r"Lean RRE", r"3\.2\.0", r"15 consultas", r"1[.,]500", r"comunicados y otros recursos",
            r"technical circulars"]


@pytest.mark.parametrize("lang", ["es", "en"])
def test_sidebar_keys_present_and_obsolete_claims_gone(lang):
    for k in SIDEBAR_KEYS:
        assert isinstance(TRANSLATIONS[lang].get(k), str) and TRANSLATIONS[lang][k].strip(), k
    text = " ".join(TRANSLATIONS[lang][k] for k in SIDEBAR_KEYS)
    for pat in OBSOLETE:
        assert not re.search(pat, text, re.I), pat
    for gone in ("quota_info_title", "quota_info_desc", "sidebar_docs_expander_title", "sidebar_guide_quick_content"):
        assert gone not in TRANSLATIONS[lang]


def test_edition_matches_active_corpus():
    label = get_active_corpus_config()["version_label"]          # "14 August 2026 (Official)"
    assert "14 August 2026" in label
    assert "14 August 2026" in t("sidebar_rules_edition", "en")
    assert "14 de agosto de 2026" in t("sidebar_rules_edition", "es")
    for lang in ("es", "en"):
        ed = t("sidebar_rules_edition", lang)
        assert ed in t("sidebar_sources_content", lang, edition=ed)
        assert ed in t("sidebar_version_rules", lang, edition=ed)


def test_sources_say_sor_is_the_only_basis():
    assert "exclusivamente en el SOR" in t("sidebar_sources_content", "es", edition="x")
    assert "exclusively on the IJF SOR" in t("sidebar_sources_content", "en", edition="x")
    assert "no sustituyen al SOR" in t("sidebar_sources_content", "es", edition="x")


def test_abstention_and_availability_describe_real_behaviour():
    assert "se abstiene" in t("sidebar_howto_abstain_content", "es")
    assert "abstains" in t("sidebar_howto_abstain_content", "en")
    assert "no genera respuestas sin comprobar" in t("availability_desc", "es")
    assert "does not produce unchecked answers" in t("availability_desc", "en")


def test_ui_labels_named_in_help_exist():
    for lang, send, hist, fb in (("es", "Enviar", "Historial de consultas", "Ayúdanos a mejorar"),
                                 ("en", "Submit", "Query history", "Help us improve")):
        assert send in t("send_btn", lang) and hist in t("tab_query_history", lang, n=0)
        assert fb in t("feedback_expander", lang)
        help_text = t("sidebar_howto_ask_content", lang) + t("sidebar_howto_history_content", lang)
        assert send in help_text and hist in help_text and fb in help_text


def test_app_sidebar_order_and_guide_not_linked():
    with open(os.path.join(ROOT, "app.py"), encoding="utf-8") as f:
        src = f.read()
    block = src[src.index("with st.sidebar:"):src.index("Client-side Exclusive Accordion")]
    order = [block.index(s) for s in ('t("lang_selector_label"', '"🎨 "', 't("sidebar_howto_title"',
                                       't("sidebar_about_title"', "t('availability_title'", 't("sidebar_admin_title"')]
    assert order == sorted(order)
    assert "IJF_SOR_Assistant_Guia_Usuario.pdf" not in block and "quota_info" not in block

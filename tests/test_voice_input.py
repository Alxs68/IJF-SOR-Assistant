"""Consulta por voz (src/voice_input.py): idioma, textos, seguridad del HTML generado e integracion en app.py.
Sin red, sin modelos y sin microfono: el comportamiento en el navegador se valida aparte."""
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import voice_input as V  # noqa: E402
from i18n import TRANSLATIONS, t  # noqa: E402


def _labels(lang):
    return {k: t(k, lang) for k in V.LABEL_KEYS}


def _cfg(html_text):
    m = re.search(r"const CFG = (\{.*?\});\n", html_text)
    assert m, "configuracion no encontrada"
    return json.loads(m.group(1))


def test_language_mapping_reuses_ui_language():
    assert V.voice_lang_code("es") == "es-CO"
    assert V.voice_lang_code("en") == "en-US"
    assert V.voice_lang_code("fr") == "es-CO"      # idioma desconocido -> espanol por defecto
    for lang, code in (("es", "es-CO"), ("en", "en-US")):
        cfg = _cfg(V.build_voice_widget_html(lang, _labels(lang)))
        assert cfg["lang"] == code and cfg["ui"] == lang


@pytest.mark.parametrize("lang", ["es", "en"])
def test_labels_present_in_both_languages(lang):
    for k in V.LABEL_KEYS:
        assert isinstance(TRANSLATIONS[lang].get(k), str) and TRANSLATIONS[lang][k].strip(), k
    cfg = _cfg(V.build_voice_widget_html(lang, _labels(lang)))
    assert cfg["labels"] == _labels(lang)
    assert t("voice_btn_start", "es") != t("voice_btn_start", "en")


def test_config_cannot_break_out_of_script():
    evil = {k: '</script><script>alert(1)</script>"&' for k in V.LABEL_KEYS}
    html_text = V.build_voice_widget_html("es", evil)
    assert html_text.count("</script>") == 1                    # solo el cierre propio
    assert _cfg(html_text)["labels"]["voice_btn_start"] == evil["voice_btn_start"]


def test_theme_change_recreates_widget():
    a = V.build_voice_widget_html("es", _labels("es"), "light")
    b = V.build_voice_widget_html("es", _labels("es"), "dark")
    assert a != b and _cfg(a)["theme"] == "light"


def test_browser_api_only_no_audio_storage_no_network_no_autosubmit():
    src = V._TEMPLATE
    assert "SpeechRecognition" in src and "webkitSpeechRecognition" in src
    for banned in ("MediaRecorder", "getUserMedia", "fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon",
                   "localStorage", "sessionStorage", "indexedDB", "requestSubmit", ".submit(", "KeyboardEvent",
                   ".click()", "speechSynthesis", "Blob"):
        assert banned not in src, banned
    # Errores y degradacion controlados.
    for code in ("not-allowed", "service-not-allowed", "audio-capture", "network", "no-speech", "aborted"):
        assert f'"{code}"' in src, code
    assert "isSecureContext" in src and '"unsupported"' in src
    # La transcripcion se anade al campo existente (no lo reemplaza) y solo con un evento input.
    assert 'new P.Event("input"' in src and 'cur.trim() ? cur.replace' in src


def test_module_is_independent_of_engine():
    with open(os.path.join(ROOT, "src", "voice_input.py"), encoding="utf-8") as f:
        code = f.read()
    imports = re.findall(r"^\s*(?:import|from)\s+(\w+)", code, re.M)
    assert imports == ["json"]


def test_app_integration_outside_form_and_before_query_execution():
    with open(os.path.join(ROOT, "app.py"), encoding="utf-8") as f:
        src = f.read()
    assert "_voice.QUERY_INPUT_LABEL" in src and V.QUERY_INPUT_LABEL == "Query input"
    form_at = src.index('with st.form(key="chat_form"')
    voice_at = src.index("_voice.build_voice_widget_html(")
    run_at = src.index("if query_to_run:\n    with st.status(")
    assert form_at < voice_at < run_at
    form_indent = len(src[:form_at].rsplit("\n", 1)[1])
    call_line = src[:src.rindex("components.html(", 0, voice_at)].rsplit("\n", 1)[1] + "x"
    call_indent = len(call_line) - len(call_line.lstrip())
    assert call_indent <= form_indent, "el control de voz no debe estar dentro del formulario"
    # El envio sigue siendo exclusivamente el boton del formulario.
    assert src.count("query_to_run = user_input.strip()") == 1


def test_help_text_describes_voice_and_privacy():
    es, en = t("sidebar_howto_ask_content", "es"), t("sidebar_howto_ask_content", "en")
    assert "Dictar" in es and "no graba ni guarda audio" in es
    assert "Dictate" in en and "does not record or store audio" in en

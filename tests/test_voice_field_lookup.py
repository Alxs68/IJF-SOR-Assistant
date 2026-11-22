"""Busqueda del campo de consulta por el control de voz, ejecutada en un navegador real (Chromium de Playwright).

Cada escenario monta un DOM con la estructura de Streamlit (barra lateral + area principal), el iframe real del
control (``build_voice_widget_html``) y un reconocimiento de voz simulado. Comprueba en que campo termina el texto
dictado: nunca en un campo administrativo, de contrasena, oculto o ambiguo; si no hay un campo inequivoco, el texto
se ofrece para copiarlo. Se ejecuta en PC y en Android emulado. Si Playwright o Chromium no estan disponibles (p. ej.
en el contenedor de produccion), las pruebas se omiten.
"""
import html
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import voice_input as V  # noqa: E402
from i18n import t  # noqa: E402

sync_api = pytest.importorskip("playwright.sync_api")

URL = "https://voz.test/"
TEXT = "cuanto dura un combate senior"
PH = "Escriba aquí su consulta sobre el reglamento IJF SOR..."
ANDROID_UA = ("Mozilla/5.0 (Linux; Android 14; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/131.0.0.0 Mobile Safari/537.36")
DEVICES = {
    "pc": dict(viewport={"width": 1440, "height": 900}),
    "android": dict(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, user_agent=ANDROID_UA),
}

FAKE_RECOGNITION = """<script>
window.SpeechRecognition = window.webkitSpeechRecognition = class {
  start() { setTimeout(() => { this.onstart && this.onstart();
    setTimeout(() => { this.onresult && this.onresult({ results: [{ 0: { transcript: "%s" }, isFinal: true, length: 1 }] });
      setTimeout(() => { this.onend && this.onend(); }, 50); }, 100); }, 50); }
  stop() {} abort() { this.onend && this.onend(); } };
</script>""" % TEXT


def _query(attrs='aria-label="Query input" placeholder="%s"' % PH, ident="q"):
    return ('<div data-testid="stForm"><div data-testid="stTextInput"><input id="%s" type="text" %s></div>'
            '<button>Enviar</button></div>' % (ident, attrs))


ADMIN_SIDEBAR_COLLAPSED = ('<details><summary>Administración</summary><div data-testid="stForm">'
                           '<div data-testid="stTextInput"><input id="admin" type="password" '
                           'aria-label="Token de Acceso Administrativo"></div></div></details>')
ADMIN_SIDEBAR_OPEN = ADMIN_SIDEBAR_COLLAPSED.replace("<details>", "<details open>")
ADMIN_TEXT_IN_MAIN = ('<div data-testid="stForm"><div data-testid="stTextInput"><input id="admin" type="password" '
                      'aria-label="Token de Acceso Administrativo"></div></div>')
HIDDEN_TOKEN = '<input id="token" type="hidden" name="token" value="">'
TEXT_TOKEN = ('<div data-testid="stForm"><div data-testid="stTextInput"><input id="token" type="text" '
              'aria-label="Token de acceso" autocomplete="one-time-code"></div></div>')

# (nombre, barra lateral, area principal, id esperado o None si debe ofrecerse copiar)
SCENARIOS = [
    ("normal", ADMIN_SIDEBAR_COLLAPSED, _query(), "q"),
    ("sin_etiqueta", ADMIN_SIDEBAR_COLLAPSED, _query('placeholder="%s"' % PH), "q"),
    ("etiqueta_distinta_placeholder", ADMIN_SIDEBAR_OPEN, _query('aria-label="Otro" placeholder="%s"' % PH), "q"),
    ("admin_visible_sin_etiqueta_ni_placeholder", ADMIN_SIDEBAR_OPEN, _query('aria-label="Otro"'), "q"),
    ("token_oculto", ADMIN_SIDEBAR_COLLAPSED, HIDDEN_TOKEN + _query('placeholder="%s"' % PH), "q"),
    ("token_texto_en_principal", ADMIN_SIDEBAR_COLLAPSED, TEXT_TOKEN + _query('aria-label="Otro"'), "q"),
    ("password_en_principal", "", ADMIN_TEXT_IN_MAIN + _query('aria-label="Otro"'), "q"),
    ("consulta_ausente", ADMIN_SIDEBAR_OPEN, "", None),
    ("solo_admin_en_principal", "", ADMIN_TEXT_IN_MAIN, None),
    ("varios_candidatos", ADMIN_SIDEBAR_COLLAPSED, _query('aria-label="Otro"', "a") + _query('aria-label="Otro2"', "b"),
     None),
    ("placeholder_duplicado", "", _query('placeholder="%s"' % PH, "a") + _query('placeholder="%s"' % PH, "b"), None),
    # Copias no utilizables (invisible o de solo lectura) con el mismo texto de ayuda: no cuentan como candidatos.
    ("duplicados_invisible_y_solo_lectura", ADMIN_SIDEBAR_OPEN,
     _query('placeholder="%s" style="visibility:hidden"' % PH, "inv") + _query('placeholder="%s" readonly' % PH, "ro")
     + _query(), "q"),
]

# Area principal de versiones antiguas de Streamlit (sin data-testid="stMain").
LEGACY_MAIN = "class='main'"


def _page_html(sidebar, main, template_html, main_attrs="data-testid='stMain'"):
    widget = html.escape(template_html, quote=True)
    return ("<!doctype html><html><head><meta charset='utf-8'>%s</head><body>"
            "<section data-testid='stSidebar'>%s</section>"
            "<section %s>%s<div data-testid='stElementContainer' style='height:46px'>"
            "<iframe id='voz' srcdoc=\"%s\" style='width:100%%;height:46px;border:0'></iframe></div></section>"
            "</body></html>" % (FAKE_RECOGNITION, sidebar, main_attrs, main, widget))


def _widget_html():
    return V.build_voice_widget_html("es", {k: t(k, "es") for k in V.LABEL_KEYS}, placeholder=PH)


@pytest.fixture(scope="module")
def browser():
    try:
        with sync_api.sync_playwright() as p:
            b = p.chromium.launch()
            yield b
            b.close()
    except Exception as e:  # Chromium no instalado
        pytest.skip(f"Chromium de Playwright no disponible: {e}")


def run_scenario(browser, device, sidebar, main, template_html, main_attrs="data-testid='stMain'"):
    """Devuelve (valores de todos los campos, estado del control, texto ofrecido para copiar, portapapeles)."""
    ctx = browser.new_context(**DEVICES[device])
    try:
        ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=URL.rstrip("/"))
        page = ctx.new_page()
        body = _page_html(sidebar, main, template_html, main_attrs)
        page.route(URL, lambda r: r.fulfill(status=200, content_type="text/html; charset=utf-8", body=body))
        page.goto(URL)
        frame = page.frame_locator("#voz")
        frame.locator("#mic").wait_for()
        frame.locator("#mic").click()
        page.wait_for_function(
            "() => { const d = document.getElementById('voz').contentDocument;"
            " return d && ['ready', 'error'].includes(d.body.dataset.state); }", timeout=5000)
        values = page.evaluate("Object.fromEntries([...document.querySelectorAll('input')].map(e => [e.id, e.value]))")
        state = frame.locator("body").get_attribute("data-state")
        offered = frame.locator("#copytext").inner_text() if frame.locator("body").get_attribute("data-copy") == "1" else ""
        clip = ""
        if offered:
            frame.locator("#copy").click()
            page.wait_for_timeout(200)
            clip = page.evaluate("navigator.clipboard.readText()")
        return values, state, offered, clip
    finally:
        ctx.close()


@pytest.mark.parametrize("device", sorted(DEVICES))
@pytest.mark.parametrize("name,sidebar,main,expected", SCENARIOS, ids=[s[0] for s in SCENARIOS])
def test_dictated_text_only_reaches_the_query_field(browser, device, name, sidebar, main, expected):
    values, state, offered, clip = run_scenario(browser, device, sidebar, main, _widget_html())
    # Ningun campo administrativo, de token u otro distinto del esperado recibe texto.
    for ident, value in values.items():
        if ident != expected:
            assert value == "", f"{name}/{device}: el texto termino en '{ident}'"
    if expected:
        assert values[expected] == TEXT and state == "ready" and not offered
    else:
        # Sin campo inequivoco no se escribe en ninguno: el texto se ofrece para copiarlo y el boton funciona.
        assert state == "error" and offered == TEXT and clip == TEXT


@pytest.mark.parametrize("device", sorted(DEVICES))
def test_legacy_streamlit_main_area(browser, device):
    # Con el area principal antigua (section.main) se sigue encontrando el campo y la barra lateral sigue excluida.
    values, state, offered, _ = run_scenario(browser, device, ADMIN_SIDEBAR_OPEN, _query('aria-label="Otro"'),
                                             _widget_html(), LEGACY_MAIN)
    assert values == {"admin": "", "q": TEXT} and state == "ready" and not offered

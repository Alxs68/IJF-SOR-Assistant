"""Restauracion de citas normativas interactivas en la UI (src/citation_render.py). Sin red ni modelos."""
import html
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import citation_render as C  # noqa: E402
from citation_resolver import RESOURCE_DETAILS  # noqa: E402
from response_structurer import clean_presentation_text, sanitize_presentation_html  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = C.SOR_PDF_URL
P152, P086, P042 = "SOR-2026-08-P152-S179", "SOR-2026-08-P086-S102", "SOR-2026-08-P042-S053"
CITS = [
    {"passage_id": P152, "article_id": "Art. 6", "page_number": 152, "exact_quote": "The contest duration",
     "text_snippet": "The contest duration", "title": "Duration of the Contest", "source_url": BASE},
    {"passage_id": P086, "article_id": "Article 6.5", "page_number": 86, "exact_quote": "", "title": "Penalties"},
]
TEXT = (f"El combate dura 4 minutos según el Artículo 6 (Pág. 152) [{P152}]({BASE}#page=152). "
        f"La sanción se rige por el Art. 6.5 [{P086}].")
TAG = re.compile(r"<[^>]+>")


def visible(h):
    return html.unescape(TAG.sub("", h))


def badges(h):
    return re.findall(r'<a class="ijf-cite-badge[^"]*" href="([^"]+)"[^>]*>([^<]*)</a>', h)


def norm(s):
    return re.sub(r"\s+([,.;:!?])", r"\1", re.sub(r"\s+", " ", s)).strip()


def render(text=TEXT, cits=CITS, comp=None, **kw):
    return C.render_rich_text(text, C.build_targets(cits), comp or {}, **kw)


# 1-2. Los enlaces [SOR-...] sobreviven al renderizado; el limpiador no los elimina con el gancho y sigue
# eliminandolos sin el (contrato AUD-05 intacto).
def test_sor_links_survive_render():
    out = render()
    hrefs = [u for u, _ in badges(out)]
    assert html.escape(f"{BASE}#page=152", quote=True) in hrefs
    assert html.escape(f"{BASE}#page=86", quote=True) in hrefs


def test_cleaner_hook_preserves_and_default_unchanged():
    seen = []
    out = clean_presentation_text(TEXT, link_token=lambda i, u: seen.append((i, u)) or "<<T>>")
    assert out.count("<<T>>") == 2 and [s[0] for s in seen] == [P152, P086]
    assert seen[0][1] == f"{BASE}#page=152" and seen[1][1] is None
    assert "SOR-2026-08" not in clean_presentation_text(TEXT)          # comportamiento por defecto: sin codigos
    assert clean_presentation_text(TEXT, link_token=lambda i, u: None) == clean_presentation_text(TEXT)


# 3. Enlaces invalidos: identificador no certificado, URL externa del texto, javascript:, Markdown del modelo.
def test_invalid_links_rejected():
    bad = ("Véase el Art. 9.9 [SOR-2026-08-P299-S999](https://evil.example/x) y "
           f"[{P152}](javascript:alert(1)) y [clic aquí](https://evil.example) y https://evil.example/y.")
    out = render(bad)
    assert 'href="https://evil' not in out and "javascript:" not in out
    assert "SOR-2026-08-P299" not in out
    # El enlace de P152 que escribio el texto (javascript:) se sustituye por el destino verificado.
    assert badges(out)[0][0] == html.escape(f"{BASE}#page=152", quote=True)
    assert "https<wbr>://evil.example/y" in out     # URL suelta neutralizada (no autoenlazable)
    assert "clic aquí" in out and "[clic" not in out


# 4. Resaltado visual distintivo de las referencias normativas.
def test_references_highlighted():
    out = render()
    assert re.search(r'<a class="ijf-ref" href="[^"]+#page=152"[^>]*>Artículo 6</a>', out)
    assert re.search(r'<a class="ijf-ref" href="[^"]+#page=86"[^>]*>Art\. 6\.5</a>', out)


def test_mention_not_linked_when_level1_rejects():
    out = render(reference_check=lambda mention, pid: False)
    assert '<span class="ijf-ref">Artículo 6</span>' in out and '<a class="ijf-ref"' not in out
    assert len(badges(out)) == 2                     # los distintivos de pagina siguen enlazados


def test_mention_linked_only_if_level1_confirms():
    # Nivel 1 real (solo lectura): 6.5.1 no esta en la pagina 86 -> resaltado sin enlace; 6.5 si.
    out = render(f"Se aplica el Art. 6.5.1 [{P086}].")
    assert '<span class="ijf-ref">Art. 6.5.1</span>' in out
    assert '<a class="ijf-ref"' in render(f"Se aplica el Art. 6.5 [{P086}].")


# 5-7. Pildoras: se renderizan, con articulo y pagina; sin pagina no se inventa.
def test_pills_built_with_article_page_and_document():
    pills = C.build_citation_pills(CITS)
    assert [p["text"] for p in pills] == ["📍 Art. 6 · Pág. 152", "📍 Art. 6.5 · Pág. 86"]
    assert all(p["doc"] == "IJF SOR 2026-08" and "IJF SOR 2026-08" in p["help"] for p in pills)
    assert pills[0]["quote"] == "The contest duration" and pills[0]["url"] == f"{BASE}#page=152"


def test_pills_deduplicated_and_unverified_excluded():
    dup = CITS + [dict(CITS[0], passage_id="SOR-2026-08-P152-S180"), "SOR-2026-08-P001-S001",
                  {"passage_id": "KUN-0001", "article_id": "x", "page_number": 3}]
    assert len(C.build_citation_pills(dup)) == 2


def test_no_page_is_never_invented():
    cits = [{"passage_id": P042, "article_id": "Art. 2.7.1", "page_number": None},
            {"passage_id": P086, "article_id": "Art. 6.5", "page_number": "abc"}]
    pills = C.build_citation_pills(cits)
    assert [p["text"] for p in pills] == ["📍 Art. 2.7.1", "📍 Art. 6.5"] and all(p["page"] is None for p in pills)
    out = render(f"Art. 2.7.1 [{P042}] y Art. 6.5 [{P086}].", cits)
    assert badges(out) == [] and "Pág" not in out and "#page" not in out
    assert C.valid_page(0) is None and C.valid_page(-3) is None and C.valid_page("12") == 12


def test_pills_render_in_streamlit_and_click_opens_viewer():
    from streamlit.testing.v1 import AppTest

    def app():
        import streamlit as st
        import citation_render as C2
        cits = [{"passage_id": "SOR-2026-08-P152-S179", "article_id": "Art. 6", "page_number": 152,
                 "exact_quote": "The contest duration"},
                {"passage_id": "SOR-2026-08-P042-S053", "article_id": "Art. 2.7.1", "page_number": None}]

        def sel(p):
            st.session_state.pdf_page, st.session_state.pdf_quote = p["page"], p["quote"]
        C2.render_pills(st, C2.build_citation_pills(cits), "ijf_cit_pills_0", "Citas", sel)

    at = AppTest.from_function(app)
    at.run()
    labels = [b.label for b in at.button]
    assert labels == ["📍 Art. 6 · Pág. 152", "📍 Art. 2.7.1"]
    assert at.button[1].disabled and not at.button[0].disabled
    at.button[0].click().run()
    assert at.session_state.pdf_page == 152 and at.session_state.pdf_quote == "The contest duration"


# 8-9. Normas complementarias: sin URL o con pagina de categoria -> sin enlace; documento concreto -> enlace.
def test_complementary_links():
    comp = C.build_complementary([
        {"id": "KUN-DIS-001", "name": "Código Disciplinario de la IJF", "url": RESOURCE_DETAILS["KUN-DIS-001"]["url"]},
        {"id": "KUN-NEW-001", "name": "Comunicado LA28", "url": RESOURCE_DETAILS["KUN-NEW-001"]["url"]},
        {"id": "KUN-0004", "name": "Manual Médico", "url": None},
        {"id": "KUN-0005", "name": "Evil", "url": "https://evil.example/doc.pdf"},
        {"id": "KUN-0006", "name": "Reglamento", "url": "https://www.ijf.org/x/regla.pdf", "is_clickable": False},
    ])
    assert comp["KUN-DIS-001"]["url"] is None                       # ijf.org/ijf/documents/3: categoria
    assert comp["KUN-NEW-001"]["url"] == RESOURCE_DETAILS["KUN-NEW-001"]["url"]
    assert comp["KUN-0004"]["url"] is None and comp["KUN-0005"]["url"] is None and comp["KUN-0006"]["url"] is None
    out = render("Ver [KUN-NEW-001] y [KUN-DIS-001](https://www.ijf.org/ijf/documents/3) y [KUN-0004].", comp=comp)
    assert f'href="{RESOURCE_DETAILS["KUN-NEW-001"]["url"]}"' in out and "📘 Comunicado LA28</a>" in out
    assert '<span class="ijf-cite-badge ijf-cite-nolink"' in out and "documents/3" not in out
    assert "📘 Manual Médico</span>" in out and "KUN-" not in out
    assert C.concrete_document_url("https://www.ijf.org/") is None
    assert C.concrete_document_url("http://www.ijf.org/a.pdf") is None


# 10. Ningun identificador tecnico, URL larga ni metadato llega al texto visible.
def test_no_technical_ids_visible():
    out = render(TEXT + f" Además [{P042}] (no certificado) y [KUN-9999].")
    assert "SOR-2026-08" not in out and "KUN-9999" not in out
    assert "rackcdn" not in visible(out)


def test_id_groups_never_visible():
    x = "SOR-2026-08-P299-S001"                                   # identificador no certificado
    cases = {f"Duración [{P152}, {P086}].": 2, f"Federation [{P152}, pág. 152] dice.": 1, f"Texto ({P152}).": 1,
             f"Grupo [{x}, {P152}] y [{x}].": 1, f"Judo [{P152} y {x}].": 1, f"Judo [{x} y {x}].": 0}
    for text, n in cases.items():
        out = render(text)
        assert "SOR-2026" not in out and len(badges(out)) == n, (text, out)
        shown = visible(out)                                       # los corchetes salen como entidades (D1)
        assert "[ y]" not in shown and "[, " not in shown and "[]" not in shown
    assert "dice" in render(f"Federation [{P152}, pág. 152] dice.")


# D1. El texto del modelo no puede crear enlaces ni imagenes Markdown, en ninguna forma de destino.
D1_CASES = [
    ("[texto]( javascript:alert(1) )", "texto"),
    ("[texto](javascript:alert(1))", "texto"),
    ("[texto]( <javascript:alert(1)> )", "texto"),
    ("[texto](https://evil.example)", "texto"),
    ("![imagen](javascript:alert(1))", "imagen"),
    ("![imagen](https://evil.example/a.png)", "imagen"),
    ('[texto](javascript:alert(1) "titulo")', "texto"),
    ("[texto](  https://evil.example/x  'titulo' )", "texto"),
    ("[texto]\t(javascript:alert(1))", "texto"),
    ('<a href="javascript:alert(1)">texto</a>', "texto"),
    ("[texto][ref]\n\n[ref]: javascript:alert(1)", "texto"),
]
ALLOWED_HREF = re.compile(r'href="(?:' + re.escape(html.escape(BASE, quote=True)) + r"#page=\d+|https://www\.ijf\.org/[^\"]*)\"")


def _assert_safe(out):
    low = out.lower()
    assert 'href="javascript' not in low and "href='javascript" not in low
    assert "<img" not in low and "evil.example" not in "".join(re.findall(r'href="[^"]*"', low))
    assert "[" not in out and "](" not in out                   # ninguna sintaxis Markdown de enlace sobrevive
    for h in re.findall(r'href="[^"]*"', out):
        assert ALLOWED_HREF.fullmatch(h), h
    assert set(re.findall(r"<\s*(\w+)", out)) <= {"a", "span", "strong", "em", "br", "wbr"}


@pytest.mark.parametrize("payload, label", D1_CASES)
def test_d1_model_markdown_cannot_create_links(payload, label):
    out = render(f"Antes {payload} después.")
    _assert_safe(out)
    assert label in visible(out) and "Antes" in out and "después" in out
    assert "<a " not in out                                       # sin citas certificadas: ningun enlace


@pytest.mark.parametrize("payload, label", D1_CASES)
def test_d1_certified_links_survive_next_to_payload(payload, label):
    out = render(f"El combate dura 4 minutos según el Artículo 6 (Pág. 152) [{P152}]({BASE}#page=152). "
                 f"{payload} La sanción se rige por el Art. 6.5 [{P086}].")
    _assert_safe(out)
    hrefs = sorted({html.unescape(u) for u, _ in badges(out)})
    assert hrefs == [f"{BASE}#page=152", f"{BASE}#page=86"]
    assert re.search(r'<a class="ijf-ref" href="[^"]+#page=152"[^>]*>Artículo 6</a>', out)
    assert re.search(r'<a class="ijf-ref" href="[^"]+#page=86"[^>]*>Art\. 6\.5</a>', out)


def test_d1_bare_external_urls_not_linkable():
    out = render("Véase https://evil.example/x, http://evil.example/y y www.evil.example/z.")
    _assert_safe(out)
    assert "https<wbr>://evil.example/x" in out and "http<wbr>://evil.example/y" in out and "www<wbr>.evil" in out
    assert visible(out) == "Véase https://evil.example/x, http://evil.example/y y www.evil.example/z."


def test_d1_verified_complementary_link_survives():
    comp = C.build_complementary([{"id": "KUN-NEW-001", "name": "Comunicado LA28",
                                   "url": RESOURCE_DETAILS["KUN-NEW-001"]["url"]}])
    out = render("Ver [KUN-NEW-001] y [x]( javascript:alert(1) ).", comp=comp)
    _assert_safe(out)
    assert f'href="{RESOURCE_DETAILS["KUN-NEW-001"]["url"]}"' in out


def test_d1_code_links_with_spaced_or_malicious_destination_use_verified_target():
    out = render(f"Artículo 6 [{P152}]( javascript:alert(1) ) y [{P086}](https://evil.example).")
    _assert_safe(out)
    assert sorted({html.unescape(u) for u, _ in badges(out)}) == [f"{BASE}#page=152", f"{BASE}#page=86"]


def test_d1_normative_text_intact_and_visible_brackets_preserved():
    txt = "Según la tabla [A] del Art. 6.5, el atleta [de 73 kg] queda descalificado (véase [texto](https://evil.example))."
    out = render(txt)
    _assert_safe(out)
    assert visible(out) == ("Según la tabla [A] del Art. 6.5, el atleta [de 73 kg] queda descalificado "
                            "(véase texto).")


# 11. Respuestas sin citas: identicas al renderizado anterior.
def test_answer_without_citations_unchanged():
    for t in ("El tiempo de combate es de cuatro minutos.", "Peso: 73 kg; 4 min; 50 %; 12/08/2026; pág. 5.",
              "**Respuesta**: sin referencias.\n\nSegundo párrafo.", ""):
        assert C.render_rich_text(t, {}, {}) == sanitize_presentation_html(clean_presentation_text(t))


# 12. El texto normativo no cambia: lo visible es lo de antes mas los distintivos de pagina.
def test_normative_text_not_modified():
    out = render()
    shown = visible(out)
    for _, lab in badges(out):
        shown = shown.replace(html.unescape(lab), "")
    assert norm(shown) == norm(visible(sanitize_presentation_html(clean_presentation_text(TEXT))))


def test_figures_not_highlighted():
    out = render("El judoka de 73 kg tiene 4 min y 30 seg; 50 % de 12.5 puntos el 12/08/2026 (pág. 152).", CITS)
    assert "ijf-ref" not in out


# 13-14. Tema claro y oscuro: tokens definidos en ambos, contraste AA, y app.py los incluye.
def _lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = (lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


@pytest.mark.parametrize("vars_, bg", [(C.THEME_VARS_LIGHT, "#ffffff"), (C.THEME_VARS_DARK, "#0e1117")])
def test_theme_tokens_and_contrast(vars_, bg):
    used = set(re.findall(r"var\((--ijf-ref-[a-z-]+)\)", C.CSS))
    defined = set(re.findall(r"(--ijf-ref-[a-z-]+):", vars_))
    assert used and used <= defined
    color = re.search(r"--ijf-ref-color:\s*(#[0-9a-fA-F]{6})", vars_).group(1)
    assert _contrast(color, bg) >= 4.5


def test_app_wires_theme_css_and_renderer():
    src = open(os.path.join(ROOT, "app.py"), encoding="utf-8").read()
    assert "light_theme_vars += _cr.THEME_VARS_LIGHT" in src and "dark_theme_vars += _cr.THEME_VARS_DARK" in src
    assert "_cr.CSS" in src and "_rich_html(_text, cite_ctx)" in src and "_cr.render_pills(" in src


# 15. Navegacion al PDF: el destino es el PDF oficial en la pagina de la cita (el mismo que format_citations).
def test_pdf_destination():
    official = RESOURCE_DETAILS["SOR-2026-08-14-ENG"]["url"]
    assert C.sor_page_url(152) == f"{official}#page=152"
    assert C.sor_page_url(5, "javascript:alert(1)") == f"{official}#page=5"
    assert C.sor_page_url(5, "https://evil.example/a.pdf") == f"{official}#page=5"
    assert C.sor_page_url(None) is None
    t = C.build_targets(CITS)
    assert t[P152]["url"] == f"{official}#page=152" and t[P086]["url"] == f"{official}#page=86"


# 16. XSS: el texto, las etiquetas, citas y titulos se escapan; los marcadores internos no se pueden falsificar.
def test_xss():
    cits = [dict(CITS[0], article_id='Art. 6"><img src=x onerror=alert(1)>', title="<script>x</script>",
                 exact_quote='"><svg onload=alert(1)>')]
    txt = (f'<script>alert(1)</script> <img src=x onerror=alert(2)> Artículo 6 [{P152}] '
           '  <a href="javascript:alert(3)">x</a>')
    out = C.render_rich_text(txt, C.build_targets(cits), {})
    assert "<script" not in out and "<img" not in out and "<svg" not in out and 'href="javascript' not in out
    assert not re.search("[-]", out)
    tags = re.findall(r"<(/?\w+)", out)
    assert set(tags) <= {"a", "/a", "span", "/span", "strong", "/strong", "em", "/em", "br", "wbr"}
    pills = C.build_citation_pills(cits)
    assert pills[0]["text"].startswith("📍 Art. 6\"><img")      # texto de boton: Streamlit lo muestra como texto


# 17. Las tarjetas de evidencia existentes no cambian (mismo codigo que antes).
def test_evidence_cards_untouched():
    src = open(os.path.join(ROOT, "app.py"), encoding="utf-8").read()
    card = src[src.index("def _render_evidence_card"):src.index("def _citation_context")]
    assert 'st.session_state.pdf_page = int(ev_item["page_number"])' in card and "_cr." not in card
    prep = src[src.index("def _prepare_item_view"):src.index("def _render_evidence_card")]
    assert "_cr." not in prep


# 18. ADA_UNIFIED_ANSWER: mismas secciones; ADA_CITATION_UI=0 devuelve exactamente el renderizado anterior.
def test_unified_answer_unchanged_and_kill_switch(monkeypatch):
    import answer_presentation as AP
    struct = {"answer_mode": "UNIFIED", "summary": TEXT, "normative_basis": "Ninguna", "limitations": "x"}
    assert [f for f, _, _ in AP.unified_sections(struct, "es")] == ["summary", "limitations"]
    monkeypatch.setenv("ADA_CITATION_UI", "0")
    assert not C.enabled()
    monkeypatch.setenv("ADA_CITATION_UI", "1")
    assert C.enabled()


def test_deterministic():
    assert render() == render()


# ---- Pregunta y comentarios del usuario: texto inerte (no Markdown) ---------------------------------------------
USER_PAYLOADS = [
    "¿Tolerancia? ![x](https://evil.example/x.png)",
    "[ver regla]( javascript:alert(1) )",
    '<img src="https://evil.example/y.png" onerror="alert(1)">',
    "<script>alert(1)</script> y <a href='javascript:alert(1)'>x</a>",
    "Peso $x^2$ y **negrita** `código`",
    "línea 1\n\n![x](https://evil.example/z.png)\r\n    bloque indentado",
    "[t][1]\n\n[1]: https://evil.example",
]


@pytest.mark.parametrize("raw", USER_PAYLOADS)
def test_user_text_is_inert(raw):
    out = C.plain_text_html(raw)
    assert out.startswith('<div class="user-text">') and out.endswith("</div>")
    assert "\n" not in out and "\r" not in out          # un solo bloque HTML: Markdown no procesa su contenido
    inner = out[len('<div class="user-text">'):-len("</div>")]
    assert set(TAG.findall(inner)) <= {"<br>"}         # la unica etiqueta emitida es el salto de linea
    assert visible(inner.replace("<br>", "\n")) == raw.replace("\r\n", "\n")   # el texto visible no cambia


def test_user_text_label_and_none():
    assert C.plain_text_html(None) == '<div class="user-text"></div>'
    out = C.plain_text_html("[a](javascript:x)", "Consulta <b>")
    assert out == '<div class="user-text"><strong>Consulta &lt;b&gt;:</strong> [a](javascript:x)</div>'


def test_app_renders_user_text_inert():
    with open(os.path.join(ROOT, "app.py"), encoding="utf-8") as f:
        src = f.read()
    assert "st.markdown(item['query'])" not in src
    assert "st.markdown(_cr.plain_text_html(item['query']), unsafe_allow_html=True)" in src
    assert "plain_text_html(rec.get('context', {}).get('query', 'N/A')" in src
    assert "plain_text_html(rec.get('user_comment', 'N/A')" in src


def test_user_text_css_auto_height_and_wrap():
    with open(os.path.join(ROOT, "app.py"), encoding="utf-8") as f:
        src = f.read()
    rule = re.search(r"\.user-text \{(.*?)\}", src, re.S)
    assert rule, "falta la regla CSS .user-text"
    body = rule.group(1)
    for decl in ("overflow-wrap: anywhere", "word-break: break-word", "height: auto", "max-width: 100%",
                 "white-space: normal", "overflow: visible"):
        assert decl in body
    assert "max-height" not in body and "nowrap" not in body

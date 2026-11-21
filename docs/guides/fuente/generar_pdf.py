"""Genera docs/guides/IJF_SOR_Assistant_Guia_Usuario.pdf desde guia_usuario.html (Chromium de Playwright).

Uso:  python docs/guides/fuente/generar_pdf.py [salida.pdf]
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "guia_usuario.html"
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "IJF_SOR_Assistant_Guia_Usuario.pdf"

FOOTER = (
    '<div style="width:100%;font-family:Segoe UI,Arial,sans-serif;font-size:8px;color:#64748b;'
    'padding:0 16mm;display:flex;justify-content:space-between">'
    '<span>IJF SOR Assistant 2026 · Guía de uso · v1.5.0</span>'
    '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>'
)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(SRC.as_uri(), wait_until="load")
    page.emulate_media(media="print")
    page.pdf(path=str(OUT), format="A4", print_background=True, prefer_css_page_size=True,
             display_header_footer=True, header_template="<span></span>", footer_template=FOOTER)
    browser.close()
print(OUT)

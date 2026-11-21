"""Enlaces PDF con un unico fragmento #page=N (defecto "#page=176#page=176" en la pestana de trazabilidad).
Sin red ni modelos."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from reference_manager import ReferenceManager, pdf_page_url  # noqa: E402
from citation_resolver import format_citations, resolve_url, _rrm_manager  # noqa: E402

SOR = ("https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/"
       "IJF_Sport_and_Organisation_Rul-1787430903.pdf")


@pytest.mark.parametrize("url, page, expected", [
    (SOR, 176, f"{SOR}#page=176"),                                     # sin fragmento
    (f"{SOR}#page=176", 176, f"{SOR}#page=176"),                       # fragmento correcto
    (f"{SOR}#page=176#page=176", 176, f"{SOR}#page=176"),              # duplicado
    (f"{SOR}#page=176#page=176", None, f"{SOR}#page=176"),             # duplicado sin pagina de contexto
    (f"{SOR}#page=79", 176, f"{SOR}#page=176"),                        # prevalece la pagina de la evidencia
    (f"{SOR}#page=79", "176", f"{SOR}#page=176"),                      # pagina como texto
    (f"{SOR}?dl=1&v=2#page=79", 176, f"{SOR}?dl=1&v=2#page=176"),      # se conserva la consulta
    (f"{SOR}#page=79&zoom=100", 176, f"{SOR}#page=176&zoom=100"),      # y otros parametros del fragmento
    (SOR, None, SOR),                                                  # sin pagina: sin fragmento artificial
    (SOR, 0, SOR),
    (f"{SOR}#page=None", None, SOR),                                   # "page=None" de una pagina ausente
    (f"{SOR}#page=None", 12, f"{SOR}#page=12"),
    ("https://example.com/Reglas%20IJF%20(2026)_ñ.PDF", 5,
     "https://example.com/Reglas%20IJF%20(2026)_ñ.PDF#page=5"),       # caracteres especiales y extension en mayusculas
    ("https://www.ijf.org/news/show/abc#page=3#page=3", 9,
     "https://www.ijf.org/news/show/abc#page=3#page=3"),             # no PDF: sin cambios
    ("", 3, ""),
    (None, 3, None),
])
def test_pdf_page_url(url, page, expected):
    assert pdf_page_url(url, page) == expected


def test_idempotent():
    once = pdf_page_url(f"{SOR}#page=190#page=190", 190)
    assert pdf_page_url(once, 190) == once and once.count("#page=") == 1


def _sor_kun(page, url):
    # Forma de los elementos de 'trazabilidad' (rag_engine): source_url ya trae "#page=N" desde rre_engine.
    return {"id_conocimiento": "SOR-2026-08-P0176-A", "fuente_origen": "SOR-2026-08-14-ENG",
            "referencia_especifica": "Article 18.1", "pdf_page_index": page, "source_url": url}


@pytest.mark.parametrize("page", [79, 176, 188, 190, 194])
def test_traceability_link_has_single_page_fragment(page):
    """Ruta real de la pestana de trazabilidad (app.py): _rrm_manager.resolve_reference(kid, kun)['url']."""
    res = _rrm_manager.resolve_reference("SOR-2026-08-P0176-A", _sor_kun(page, f"{SOR}#page={page}"))
    assert res["url"] == f"{SOR}#page={page}"
    assert res["is_clickable"] and res["url"].count("#") == 1


def test_traceability_link_without_page_and_without_source_url():
    res = ReferenceManager().resolve_reference("SOR-2026-08-X", _sor_kun(None, None))
    assert res["url"] == SOR
    res = ReferenceManager().resolve_reference("SOR-2026-08-X", _sor_kun(176, None))
    assert res["url"] == f"{SOR}#page=176"


def test_legacy_resolver_and_inline_citations():
    kun = _sor_kun(176, f"{SOR}#page=176")
    assert resolve_url(kun["id_conocimiento"], kun) == f"{SOR}#page=176"
    kun2 = dict(kun, id_conocimiento="KUN-7777")
    out = format_citations("Ver [KUN-7777].", [dict(kun2, source_id="SOR-2026-08-14-ENG")])
    assert f"({SOR}#page=176)" in out and "#page=176#page" not in out


def test_other_reference_branches_unchanged():
    """Las demas ramas del RRM ya sustituian el fragmento: siguen igual."""
    kun = {"id_conocimiento": "KUN-9999", "fuente_origen": "UNKNOWN", "referencia_especifica": "Seccion",
           "fuente": {"tipo": "pdf", "url": "https://example.com/unregistered.pdf", "pagina": 10}}
    assert ReferenceManager().resolve_reference("KUN-9999", kun)["url"] == "https://example.com/unregistered.pdf#page=10"

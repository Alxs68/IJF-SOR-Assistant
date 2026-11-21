"""Renderizado seguro de las referencias normativas en la interfaz (solo presentacion).

Restaura, sin tocar el texto verificado ni el flujo de generacion/verificacion:
  - enlaces clicables al PDF oficial del SOR en la pagina citada (distintivo "📄 Pág. N" donde el modelo puso el
    identificador tecnico, que nunca se muestra);
  - resaltado de las menciones normativas ("Artículo 6.4.2"), enlazadas a la pagina solo si el Nivel 1 de
    reference_integrity confirma que la etiqueta esta en el pasaje citado;
  - pildoras "📍 Art. X · Pág. N" construidas con las citas certificadas de la respuesta;
  - enlaces a normas complementarias solo si la URL resuelta es un documento concreto de un dominio permitido.

Reglas de seguridad:
  - el texto del modelo se escapa siempre (sanitize_presentation_html); el unico HTML que se anade lo construye este
    modulo con valores escapados;
  - ningun destino procede del texto: las URL se construyen con la base oficial y la pagina de las citas
    certificadas, o con la URL resuelta por el RRM para normas complementarias, y pasan una lista blanca;
  - un identificador que no esta entre las citas certificadas, o sin pagina conocida, no genera enlace ni pagina;
  - los enlaces Markdown y las URL sueltas que escriba el modelo se neutralizan (no se vuelven clicables).
Sin dependencias de Streamlit para poder probarse.
"""
import html
import os
import re
import urllib.parse

from response_structurer import clean_presentation_text, sanitize_presentation_html

SOR_PDF_URL = ("https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/"
               "IJF_Sport_and_Organisation_Rul-1787430903.pdf")
SOR_DOC_LABEL = "IJF SOR 2026-08"
SOR_PDF_HOSTS = frozenset({"78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com"})
COMPLEMENTARY_HOSTS = frozenset({"www.ijf.org", "ijf.org", "rules.ijf.org", "referee.ijf.org"}) | SOR_PDF_HOSTS
SOR_ID = re.compile(r"^SOR-2026-08-P\d{3}-S\d{3}$")
COMP_ID = re.compile(r"^(?:KUN|CHK)-[A-Za-z0-9_-]+$")
OK_VERDICTS = ("OK", "OK_REF_CRUZADA", "OK_ARTICULO_CLAUSULA")

# Marcadores internos (caracteres de uso privado: no los altera ni el limpiador ni el escapado HTML).
_C_OPEN, _C_CLOSE, _M_OPEN, _M_CLOSE = "", "", "", ""
_PRIVATE = re.compile("[--]")
_TOKEN = re.compile("([])([-]+)([])")
_RUN = re.compile("[-]+(?:[ \t]*[-]+)*")
_ANY_ID = re.compile(r"(?<![\w-])SOR-2026-08-P\d{3}-S\d{3}(?![\w-])")
_GROUP_ONLY_TOKENS = re.compile(
    r"\[\s*[-]+(?:(?:\s*[,;/]\s*|\s+(?:y|and|e|et)\s+|\s+)[-]+)*"
    r"\s*[,;/]?\s*\]")
# Enlace o imagen Markdown escritos por el modelo, en cualquier forma de destino: con o sin espacios, entre <>, con
# titulo ("t", 't' o (t)). Se sustituyen por su texto; los de codigos de recuperacion los trata link_token.
_MD_LINK = re.compile(r"(!?)\[([^\[\]\n]*)\]\(\s*(?:<[^<>\n]*>|(?:[^()\s]|\([^()\s]*\))*)"
                      r"(?:\s+(?:\"[^\"\n]*\"|'[^'\n]*'|\([^()\n]*\)))?\s*\)")
_CODE_ID = re.compile(r"^\s*(?:SOR-2026-08-P\d{3}-S\d{3}|KUN-[A-Za-z0-9_-]+|CHK-[A-Za-z0-9_-]+)\s*$")
_BARE_URL = re.compile(r"\b(https?|ftp|www)(:|\.)(?=\S)", re.IGNORECASE)
_SENT_END = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡(«\"“])|\n+")
_PAGE_NEAR = r"(?:p[áa]g(?:ina)?\.?|page|p\.)\s*{n}\b"

LABELS = {
    "es": {"page": "Pág.", "pdf": "PDF", "open": "Abrir {doc}, pág. {n}", "no_link": "sin enlace verificable",
           "doc": "Documento"},
    "en": {"page": "Page", "pdf": "PDF", "open": "Open {doc}, page {n}", "no_link": "no verifiable link",
           "doc": "Document"},
}


def enabled():
    """Interruptor de reversion: ADA_CITATION_UI=0 vuelve al renderizado anterior (sin enlaces ni pildoras)."""
    return os.environ.get("ADA_CITATION_UI", "1").strip() != "0"


def _lab(lang):
    return LABELS.get(lang if lang in LABELS else "es")


def _enc(n):
    return "".join(chr(0xE010 + int(d)) for d in str(n))


def _dec(s):
    return int("".join(str(ord(c) - 0xE010) for c in s))


def valid_page(value):
    """Pagina entera positiva o None (nunca se inventa una pagina)."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _safe_https(url, hosts):
    if not isinstance(url, str) or not url.strip():
        return None
    try:
        u = urllib.parse.urlsplit(url.strip())
    except ValueError:
        return None
    if u.scheme != "https" or u.username or u.password or u.port not in (None, 443):
        return None
    if (u.hostname or "").lower() not in hosts or any(c in url for c in "\"'<> \t\r\n\\"):
        return None
    return u


def sor_page_url(page, source_url=None):
    """URL del PDF oficial en la pagina indicada; solo con base de la lista blanca y pagina valida."""
    n = valid_page(page)
    if n is None:
        return None
    u = _safe_https(source_url, SOR_PDF_HOSTS) if source_url else None
    base = (urllib.parse.urlunsplit((u.scheme, u.netloc, u.path, "", "")) if u and u.path.lower().endswith(".pdf")
            else SOR_PDF_URL)
    return f"{base}#page={n}"


def concrete_document_url(url):
    """URL de una norma complementaria solo si es un documento concreto (PDF, o noticia individual) de un dominio
    permitido; las paginas de categoria o portada (p. ej. ijf.org/ijf/documents/3) devuelven None."""
    u = _safe_https(url, COMPLEMENTARY_HOSTS)
    if u is None:
        return None
    path = u.path or "/"
    if path.lower().endswith(".pdf") or re.fullmatch(r"/news/show/[A-Za-z0-9_-]+/?", path):
        return urllib.parse.urlunsplit((u.scheme, u.netloc, u.path, u.query, u.fragment))
    return None


def article_label(citation):
    raw = str(citation.get("article_id") or "").strip()
    if not raw:
        raw = str(citation.get("title") or "").strip()
    lab = re.sub(r"^(?:art\.?\s*)+article\s*", "Art. ", raw, flags=re.IGNORECASE)
    lab = re.sub(r"^article\s+", "Art. ", lab, flags=re.IGNORECASE)
    return (lab[:60].rsplit(" ", 1)[0] + "…") if len(lab) > 60 else lab


def build_targets(citations, evidence=()):
    """Destinos verificados por identificador SOR: citas certificadas de la respuesta y, como respaldo, los pasajes
    primarios certificados entregados al modelo (item['evidence']). Sin pagina valida no hay destino."""
    out = {}
    for c in list(citations or []) + list(evidence or ()):
        if not isinstance(c, dict):
            continue
        pid = str(c.get("passage_id") or "").strip()
        if not SOR_ID.match(pid) or pid in out:
            continue
        page = valid_page(c.get("page_number") if c.get("page_number") is not None
                          else c.get("page", c.get("pdf_page_index")))
        url = sor_page_url(page, c.get("source_url"))
        if url is None:
            continue
        out[pid] = {"page": page, "url": url, "label": article_label(c),
                    "title": str(c.get("title") or ""), "quote": str(c.get("exact_quote") or "")}
    return out


def build_complementary(entries):
    """entries: iterable de dicts {id, name, url, is_clickable} (resolucion del RRM). Devuelve id -> {name, url|None}."""
    out = {}
    for e in entries or ():
        if not isinstance(e, dict):
            continue
        cid = str(e.get("id") or "").strip()
        if not COMP_ID.match(cid):
            continue
        url = concrete_document_url(e.get("url")) if e.get("is_clickable", True) else None
        out[cid] = {"name": str(e.get("name") or cid), "url": url}
    return out


_INDEX = {"loaded": False, "idx": None}


def default_reference_check(mention, passage_id):
    """True si el Nivel 1 (reference_integrity, solo lectura) confirma la mencion frente al pasaje citado."""
    if not _INDEX["loaded"]:
        _INDEX["loaded"] = True
        try:
            import reference_integrity as R
            _INDEX["idx"] = R.default_index()
        except Exception:  # sin indice no se enlazan menciones (se siguen resaltando y enlazando los distintivos)
            _INDEX["idx"] = None
    idx = _INDEX["idx"]
    if idx is None:
        return False
    try:
        res = idx.check(mention, cited_ids=[passage_id])
    except Exception:
        return False
    return bool(res) and res[0].get("veredicto") in OK_VERDICTS


def _mentions(text):
    """Menciones normativas del texto limpio con el extractor del Nivel 1 (excluye cifras, fechas, pesos, paginas)."""
    try:
        import reference_integrity as R
    except Exception:
        return []
    refs, _ = R.extract_references(text)
    out = []
    for r in refs:
        if r.kind == "CLAUSULA":
            continue
        start = r.start
        if r.prefix:
            m = re.search(rf"(?i)\b{re.escape(r.prefix)}\s*(?:n\.?\s?[º°o]\s*)?$", text[:r.start])
            if m:
                start = m.start()
        out.append((start, r.end))
    return out


def render_rich_text(raw_text, targets, complementary=None, lang="es", reference_check=default_reference_check):
    """HTML seguro de un campo de la respuesta con referencias resaltadas y enlaces verificados."""
    if not raw_text or not isinstance(raw_text, str):
        return ""
    L = _lab(lang)
    complementary = complementary or {}
    text = _PRIVATE.sub("", raw_text)
    items = []

    def link_token(ident, _url_in_text):  # la URL del texto se ignora siempre
        if ident in targets:
            items.append(("cite", ident))
        elif ident in complementary:
            items.append(("comp", ident))
        else:
            return None
        return f"{_C_OPEN}{_enc(len(items) - 1)}{_C_CLOSE}"

    # D1: enlaces e imagenes Markdown del modelo -> solo su texto, ANTES de limpiar (el limpiador no los trata y su
    # paso de puntuacion pegaria el "!" de las imagenes). Los de codigos de recuperacion siguen intactos para link_token.
    text = _MD_LINK.sub(lambda m: m.group(0) if _CODE_ID.match(m.group(2)) else m.group(2), text)
    # Identificadores fuera de un corchete propio ("[SOR-A, SOR-B]", "[SOR-A, pág. 12]", "(SOR-A)"): se aíslan como
    # "[SOR-A]" para que reciban el mismo tratamiento (distintivo verificado o eliminación) y no queden visibles.
    text = _ANY_ID.sub(lambda m: m.group(0) if (m.string[m.start() - 1:m.start()] == "[" and
                                                m.string[m.end():m.end() + 1] == "]") else f"[{m.group(0)}]", text)
    cleaned = clean_presentation_text(text, link_token=link_token)
    # Restos de agrupaciones de codigos: "[ T, T]" -> "T T"; "[, ]" -> ""; "( T)" / "[ T, pág. 12]" sin espacio inicial.
    cleaned = re.sub(r"([(\[])\s+(?=)", r"\1", cleaned)
    cleaned = re.sub(r"\[\s*(?:[,;/]|(?:y|and|e|et)\s)\s*", "[", cleaned)
    cleaned = re.sub(r"(?<=)\s*(?:[,;/]|\s(?:y|and|e|et))\s*\]", "]", cleaned)
    cleaned = _GROUP_ONLY_TOKENS.sub(lambda m: " ".join(t.group(0) for t in _TOKEN.finditer(m.group(0))), cleaned)
    cleaned = re.sub(r"\s*\[[\s,;/]*(?:(?:y|and|e|et)[\s,;/]*)?\]", "", cleaned)

    # Menciones normativas -> marcador con su cita asociada (bloque de citas siguiente en la frase, si no el anterior).
    cite_pos = [(m.start(), m.end(), _dec(m.group(2))) for m in _TOKEN.finditer(cleaned) if m.group(1) == _C_OPEN]
    bounds = [0] + [m.end() for m in _SENT_END.finditer(cleaned)] + [len(cleaned) + 1]

    def sentence_of(pos):
        for a, b in zip(bounds, bounds[1:]):
            if a <= pos < b:
                return a, b
        return 0, len(cleaned) + 1

    def block(tokens, first):
        run = [first]
        for t in tokens[tokens.index(first) + 1:]:
            if cleaned[run[-1][1]:t[0]].strip(" \t,;") == "":
                run.append(t)
            else:
                break
        return run

    pieces, last = [], 0
    for a, b in _mentions(cleaned):
        sa, sb = sentence_of(a)
        after = [t for t in cite_pos if b <= t[0] < sb]
        before = [t for t in cite_pos if sa <= t[0] < a]
        cands = block(cite_pos, after[0]) if after else (block(cite_pos, before[-1]) if before else [])
        url = title = None
        mention = cleaned[a:b]
        for _, _, k in cands:
            kind, ident = items[k]
            if kind == "cite" and reference_check and reference_check(mention, ident):
                url = targets[ident]["url"]
                title = L["open"].format(doc=SOR_DOC_LABEL, n=targets[ident]["page"])
                break
        items.append(("mention", mention, url, title))
        pieces.append(cleaned[last:a])
        pieces.append(f"{_M_OPEN}{_enc(len(items) - 1)}{_M_CLOSE}")
        last = b
    pieces.append(cleaned[last:])
    marked = "".join(pieces)

    # Distintivos consecutivos hacia la misma pagina: uno solo.
    def dedupe_run(m):
        seen, keep = set(), []
        for t in _TOKEN.finditer(m.group(0)):
            kind, ident = items[_dec(t.group(2))]
            key = targets[ident]["url"] if kind == "cite" else ("comp", ident)
            if key not in seen:
                seen.add(key)
                keep.append(t.group(0))
        return " ".join(keep)

    marked = _RUN.sub(dedupe_run, marked)
    safe = sanitize_presentation_html(marked)
    # URL sueltas del modelo: <wbr> parte el esquema en dos nodos de texto y el Markdown de Streamlit no las
    # autoenlaza (una entidad como &#58; no basta: se decodifica antes del autoenlace). El texto visible no cambia.
    safe = _BARE_URL.sub(lambda m: f"{m.group(1)}<wbr>{m.group(2)}", safe)
    # D1: cualquier corchete que quede en el texto del modelo se emite como entidad. El Markdown de Streamlit no
    # reconoce "&#91;" como apertura de enlace o imagen, asi que ninguna forma de [texto](destino) que haya escapado
    # al filtro anterior puede crear un enlace. Se hace antes de expandir los marcadores: los enlaces del renderizador
    # (HTML propio, sin corchetes) no se ven afectados. El texto visible no cambia.
    safe = safe.replace("[", "&#91;").replace("]", "&#93;")

    def render_token(m):
        it = items[_dec(m.group(2))]
        if it[0] == "mention":
            _, mention, url, title = it
            if url:
                return (f'<a class="ijf-ref" href="{html.escape(url, quote=True)}" target="_blank" '
                        f'rel="noopener noreferrer" title="{html.escape(title, quote=True)}">{html.escape(mention)}</a>')
            return f'<span class="ijf-ref">{html.escape(mention)}</span>'
        if it[0] == "cite":
            tg = targets[it[1]]
            near = safe[max(0, m.start() - 48):m.start()] + " " + safe[m.end():m.end() + 24]
            shown = L["pdf"] if re.search(_PAGE_NEAR.format(n=tg["page"]), near, re.IGNORECASE) else f'{L["page"]} {tg["page"]}'
            title = L["open"].format(doc=SOR_DOC_LABEL, n=tg["page"])
            return (f'<a class="ijf-cite-badge" href="{html.escape(tg["url"], quote=True)}" target="_blank" '
                    f'rel="noopener noreferrer" title="{html.escape(title, quote=True)}">📄 {html.escape(shown)}</a>')
        comp = complementary[it[1]]
        if comp["url"]:
            return (f'<a class="ijf-cite-badge ijf-cite-comp" href="{html.escape(comp["url"], quote=True)}" '
                    f'target="_blank" rel="noopener noreferrer">📘 {html.escape(comp["name"])}</a>')
        return (f'<span class="ijf-cite-badge ijf-cite-nolink" title="{html.escape(L["no_link"], quote=True)}">'
                f'📘 {html.escape(comp["name"])}</span>')

    return _TOKEN.sub(render_token, safe)


def build_citation_pills(citations, lang="es"):
    """Pildoras de las citas certificadas de la respuesta: una por (articulo, pagina), sin inventar pagina."""
    L = _lab(lang)
    out, seen = [], set()
    for c in citations or []:
        if not isinstance(c, dict):
            continue
        pid = str(c.get("passage_id") or "").strip()
        if not SOR_ID.match(pid):
            continue
        label = article_label(c) or pid.split("-")[-2]
        page = valid_page(c.get("page_number") if c.get("page_number") is not None else c.get("page"))
        key = (label.lower(), page)
        if key in seen:
            continue
        seen.add(key)
        text = f"📍 {label} · {L['page']} {page}" if page else f"📍 {label}"
        quote = str(c.get("exact_quote") or "").strip()
        snippet = str(c.get("text_snippet") or quote).strip()
        help_txt = f"{L['doc']}: {SOR_DOC_LABEL}" + (f" — {snippet[:220]}" if snippet else "")
        out.append({"passage_id": pid, "label": label, "page": page, "text": text, "help": help_txt,
                    "quote": quote, "doc": SOR_DOC_LABEL, "url": sor_page_url(page, c.get("source_url"))})
    return out


def render_pills(st, pills, key, title, on_select):
    """Dibuja las pildoras con Streamlit ('st' se recibe para que el modulo no dependa de Streamlit al importarse).
    Cada pildora es un boton (sin pagina: deshabilitado); al pulsarla se llama on_select(pildora)."""
    if not pills:
        return
    with st.container(key=key):
        st.markdown(f'<div class="citation-title-label">{html.escape(title)}</div>', unsafe_allow_html=True)
        cols = st.columns(min(len(pills), 4))
        for k, pill in enumerate(pills):
            with cols[k % len(cols)]:
                if st.button(pill["text"], key=f"{key}_{k}", help=pill["help"], use_container_width=True,
                             disabled=pill["page"] is None):
                    on_select(pill)


# Estilos (tokens de tema en claro y oscuro; los usa app.py).
THEME_VARS_LIGHT = """
        --ijf-ref-color: #1d4ed8;
        --ijf-ref-bg: rgba(37, 99, 235, 0.08);
        --ijf-ref-border: rgba(37, 99, 235, 0.35);
        --ijf-ref-hover-bg: rgba(37, 99, 235, 0.16);
"""
THEME_VARS_DARK = """
        --ijf-ref-color: #93c5fd;
        --ijf-ref-bg: rgba(96, 165, 250, 0.14);
        --ijf-ref-border: rgba(147, 197, 253, 0.40);
        --ijf-ref-hover-bg: rgba(96, 165, 250, 0.26);
"""
CSS = """
    .ijf-ref {
        color: var(--ijf-ref-color) !important;
        font-weight: 600;
        background: var(--ijf-ref-bg);
        border-radius: 4px;
        padding: 0 3px;
    }
    a.ijf-ref {
        text-decoration: underline !important;
        text-decoration-thickness: 1px;
        text-underline-offset: 2px;
        cursor: pointer;
    }
    a.ijf-ref:hover { background: var(--ijf-ref-hover-bg); }
    .ijf-cite-badge {
        display: inline-block;
        font-size: 0.74rem;
        font-weight: 600;
        line-height: 1.35;
        padding: 0 7px;
        margin: 0 2px;
        border: 1px solid var(--ijf-ref-border);
        border-radius: 9999px;
        color: var(--ijf-ref-color) !important;
        background: var(--ijf-ref-bg);
        text-decoration: none !important;
        white-space: nowrap;
        vertical-align: 1px;
    }
    a.ijf-cite-badge:hover { background: var(--ijf-ref-hover-bg); }
    .ijf-cite-nolink { cursor: help; border-style: dashed; }
    div[class*="st-key-ijf_cit_pills"] div[data-testid="stButton"] button {
        border: 1px solid var(--ijf-ref-border) !important;
        border-radius: 9999px !important;
        background: var(--ijf-ref-bg) !important;
        color: var(--ijf-ref-color) !important;
        font-size: 0.8rem !important;
        padding: 0.2rem 0.7rem !important;
        min-height: 0 !important;
        opacity: 1 !important;
    }
    div[class*="st-key-ijf_cit_pills"] div[data-testid="stButton"] button:hover {
        background: var(--ijf-ref-hover-bg) !important;
    }
    div[class*="st-key-ijf_cit_pills"] div[data-testid="stButton"] button p { font-size: 0.8rem !important; }
"""

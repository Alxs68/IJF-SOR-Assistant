"""Control de integridad decisoria de ADA (Fase 9) - DIG v1.

Comprueba, de forma conservadora y GENERICA (sin reglas por consulta ni por articulo), si una
respuesta generada puede emitirse como respuesta normativa. Distingue cuatro niveles:

  A  cita SOR         : la cita pertenece al SOR primario entregado (lo verifica ADA antes)
  B  pertinencia      : las citas se relacionan con la pregunta  -> SOLO heuristica necesaria
  C  suficiencia      : la evidencia citada cubre la respuesta    -> controles estructurales
  D  respaldo efectivo: las afirmaciones se siguen de la evidencia -> NO VERIFICADO (sin entailment)

Ningun control de este modulo demuestra entailment. Una respuesta que los supera queda como
"respaldo literal verificado (heuristico)"; el nivel D se informa siempre como NO_VERIFICADO.
Cualquier fallo -> ABSTENER.

Controles (todos sobre la respuesta JSON del modelo, que debe incluir answerability,
evidence_quotes y evidence_conflicts; ver contrato en ADA):
  DIG-01 SUFICIENCIA_DECLARADA   answerability == "RESPALDADA"; evidence_conflicts vacio
  DIG-02 CITAS_CON_CITA_LITERAL  cada pasaje SOR citado tiene >=1 cita textual atribuida
  DIG-03 CITA_LITERAL            cada cita textual (>= MIN_QUOTE_WORDS palabras) es literal del pasaje
                                 al que se atribuye (espacios/comillas normalizados)
  DIG-04 CITA_NO_SHADOW          una cita textual no puede proceder solo del contexto SHADOW
  DIG-05 PERTINENCIA_MINIMA      cada pasaje citado tiene >=1 cita que comparte un termino de contenido
                                 con la consulta (o su proyeccion EN), y >=1 de ellas procede de
                                 evidencia directa (heuristica necesaria, no suficiente)
  DIG-06 CIFRAS_RESPALDADAS      toda cifra de summary/normative_basis/conditions figura en las citas
  DIG-07 TERMINOS_RESPALDADOS    terminos distintivos del corpus SOR usados en esos campos figuran en
                                 las citas o en la consulta
  DIG-08 SIN_INFLUENCIA_SHADOW   la respuesta no contiene cifras/terminos presentes solo en SHADOW
  DIG-09 EXCEPCIONES_CITADAS     las oraciones con marcador de excepcion de la misma unidad derivada
                                 (article_units_v1), en una ventana de +-2 oraciones, estan citadas
  DIG-10 REFERENCIAS_ENTREGADAS  las referencias cruzadas resueltas que aparecen DENTRO de una cita
                                 apuntan a pasajes entregados al modelo (v1.1: no se exigen las de
                                 oraciones vecinas)
  DIG-11 TERMINOS_DE_CONSULTA_EN_SOR  (consultas en ingles) ningun termino de contenido de la consulta
                                 esta ausente de todo el SOR; si lo esta, el SOR no puede responderla
                                 literalmente (condicion necesaria)
  DIG-12 CIFRA_PARA_PREGUNTA_CUANTITATIVA  si la consulta pide una cantidad (cuanto/how many...), las
                                 citas contienen al menos una cifra
v1.3 - DIG-05 se mantiene: >=1 termino distintivo compartido (frecuencia documental <= 15 %); la
variante ">=2 terminos <= 30 %" se evaluo y se descarto por aumentar el riesgo. DIG-09/10: una cita que cruza el marcador de salto de pagina del texto cosido se verifica por
segmentos en su pagina canonica. DIG-08: basta UN termino (>= 5 letras) presente solo en SHADOW.
v1.2 - DIG-09/DIG-10 localizan la cita en el texto CANONICO de la pagina (y paginas vecinas) del
corpus: el RRE puede entregar texto "cosido" de varias paginas, cuyo hash no coincide con el de la
unidad derivada; antes eso dejaba la cita sin unidad y provocaba abstenciones indebidas.
DIG-12 no se aplica a preguntas de duracion/frecuencia (how long / how often), que pueden
responderse sin cifra.
v1.1 - DIG-05 usa terminos DISTINTIVOS del corpus (frecuencia documental <= 15 % de paginas): un
termino generico (athlete, official, event...) no basta para considerar pertinente una cita.
Solo biblioteca estandar. No modifica corpus ni unidades derivadas (lectura).
"""
import hashlib
import json
import os
import re
import unicodedata
from bisect import bisect_right
from collections import Counter, defaultdict

DIG_BASE_VERSION = "DIG-1.3"
# Fase 11A: normalizacion de artefactos de formato en las cifras (DIG-06/08/12). "v1" = comportamiento
# original (por defecto); "v2" = variante evaluada en la Fase 11 (src/dig_number_normalization.py).
NUMBER_NORMALIZATION = os.environ.get("DIG_NUMBER_NORMALIZATION", "v1").strip().lower()
if NUMBER_NORMALIZATION not in ("v1", "v2"):
    NUMBER_NORMALIZATION = "v1"
# Correcciones v3 (2026-11-16), desactivadas por defecto (DIG_V3=1 las activa). Cada una corrige un falso
# positivo observado en la instancia experimental sin aceptar cifras ni citas no literales:
#   FIX_PERTINENCE_HEADING  DIG-05: el titulo de la unidad derivada (article_units_v1) que contiene la cita
#                           literal cuenta como contexto de pertinencia (p. ej. "Judogi Rules for Veterans").
#   FIX_HYPHEN_TERMS        DIG-07: las partes de un termino con guion citado respaldan el termino suelto
#                           ("osaekomi-waza" en la cita respalda "waza" en la respuesta); no al reves.
#   FIX_DIG08_LANGUAGE      DIG-08: si la respuesta no esta en ingles (idioma del SOR), las palabras
#                           ordinarias no se comparan con SHADOW (el solapamiento lexico entre idiomas no
#                           indica influencia); se siguen comprobando cifras y terminos con guion.
_V3 = os.environ.get("DIG_V3", "").strip() == "1"
FIX_PERTINENCE_HEADING = _V3
FIX_HYPHEN_TERMS = _V3
FIX_DIG08_LANGUAGE = _V3


def dig_version():
    v = DIG_BASE_VERSION + ("" if NUMBER_NORMALIZATION == "v1" else "+NUM-v2")
    fixes = [n for n, on in (("H", FIX_PERTINENCE_HEADING), ("G", FIX_HYPHEN_TERMS), ("L", FIX_DIG08_LANGUAGE)) if on]
    return v + ("+FIX-v3" + ("" if len(fixes) == 3 else "-" + "".join(fixes)) if fixes else "")


DIG_VERSION = dig_version()
DISTINCTIVE_MAX_DF = 0.15
# Regla de ">=2 terminos especificos (<=30 %)" EVALUADA y DESCARTADA en Fase 9.1: en dev anadia 2 falsos
# positivos y 5 SUCCESS con cita fuera de la evidencia minima frente a 2 aciertos (eval_decision_integrity,
# results_v1_3.json, threshold_sweep_DIG05). 0.0 la desactiva; se conserva el parametro para re-evaluarla.
SPECIFIC_MAX_DF = 0.0
PAGE_BREAK = re.compile(r"-{3}\s*\[page break:[^\]]*\]\s*-{3}", re.IGNORECASE)
MIN_QUOTE_WORDS = 6
WINDOW_SENTENCES = 2
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNITS_PATH = os.path.join(ROOT, "data", "derived", "article_units_v1", "units.jsonl")
SOR_ID = re.compile(r"SOR-[A-Za-z0-9]+-[A-Za-z0-9]+-P\d+-S\d+")
SHADOW_ID = re.compile(r"(?:CHK|KUN|SHU1)-[A-Za-z0-9_\-]+")
EXCEPTION_MARKER = re.compile(
    r"\b(?:except|exceptions?|unless|however|although|notwithstanding|nevertheless|does not apply|"
    r"no score or penalty|only if|only when|can only)\b", re.IGNORECASE)
STOP = set("""a al algo ante con como cual cuales cuando de del desde donde el ella en entre es esta este esto
estos fue ha han hay la las le les lo los mas mismo muy no o otra otro para pero por porque que se segun ser
si sin sobre son su sus tambien tiene un una uno y ya debe deben puede pueden cuanto cuantos cuantas
the of and in to is are for on by with at as from an or be it this that these those can could would should
what when where which who how does do did has have had not no any all may must shall will its their there
than then into out also such other only more most very being been was were""".split())
CLAIM_FIELDS = ("summary", "normative_basis", "conditions_and_exceptions")


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn")


def _clean_char(c):
    return {"’": "'", "‘": "'", "“": '"', "”": '"', " ": " "}.get(c, c)


def normalize_with_map(text):
    """Lowercase, typographic quotes -> ASCII, whitespace collapsed, 'N .N' -> 'N.N'.
    Returns (normalized, index_map) with index_map[i] = raw offset of normalized char i."""
    out, idx = [], []
    n = len(text)
    i = 0
    while i < n:
        c = _clean_char(text[i])
        if c.isspace():
            j = i
            while j < n and text[j].isspace():
                j += 1
            nxt = text[j] if j < n else ""
            prev = out[-1] if out else ""
            if (prev.isdigit() or prev.isalpha()) and nxt == "." and j + 1 < n and text[j + 1].isdigit():
                i = j
                continue
            if out and out[-1] != " " and j < n:
                out.append(" ")
                idx.append(i)
            i = j
            continue
        out.append(c.lower())
        idx.append(i)
        i += 1
    return "".join(out).strip(), idx


def norm(text):
    return normalize_with_map(text or "")[0]


def content_stems(text):
    toks = re.findall(r"[a-z0-9][a-z0-9\-]*", strip_accents(norm(text)))
    return {t[:5] for t in toks if len(t) >= 4 and t not in STOP and not t.isdigit()}


def numbers_in_v1(text):
    """Cifras de un texto (comportamiento original DIG-1.3)."""
    t = SOR_ID.sub(" ", text or "")
    t = SHADOW_ID.sub(" ", t)
    t = re.sub(r"\[[^\]]*\]", " ", t)
    t = re.sub(r"(?i)\b(?:p[aá]g(?:ina)?s?|pages?|pp?)\.?\s*\d+(?:\s*[-–]\s*\d+)?", " ", t)
    t = re.sub(r"(?i)\b(?:art[ií]culos?|articles?|arts?\.?|rules?|reglas?|secci[oó]n|section|appendix|ap[eé]ndice)\s*"
               r"[A-H]?\d+(?:\s?\.\s?\d+)*", " ", t)
    t = re.sub(r"\b[A-H]1(?:\s?\.\s?\d+)+\b", " ", t)
    # section labels such as "1 .2 .2" (spaced, as extracted from the PDF) or "1.2.2" (two or more dots)
    t = re.sub(r"\b\d+(?:\s\.\s?\d+)+\b|\b\d+(?:\.\d+){2,}\b", " ", t)
    out = set()
    for f in re.findall(r"\d+(?:[.,]\d+)?", t):
        v = f.replace(",", ".")
        if "." in v:
            v = v.rstrip("0").rstrip(".")
        out.add(v.lstrip("0") or "0")
    return out


def numbers_in_v2(text):
    """Variante Fase 11A: numbers_in_v1 tras quitar solo artefactos de formato (ver dig_number_normalization)."""
    try:
        from dig_number_normalization import normalize_formatting
    except ImportError:  # pragma: no cover - ejecucion como paquete
        from src.dig_number_normalization import normalize_formatting
    return numbers_in_v1(normalize_formatting(text, SOR_ID))


numbers_in = numbers_in_v2 if NUMBER_NORMALIZATION == "v2" else numbers_in_v1


_SENT_SEP = re.compile(r"(?<=[^\d][.!?;])\s+(?=[A-Z0-9“\"(•])|\s*•\s*|\n\s*(?=\d{1,3}\.\s|[a-z]\)\s|•)")


def sentence_spans(text):
    """Raw (start, end) spans of sentences; PDF line wraps do NOT split sentences."""
    text = text or ""
    spans, pos = [], 0
    for m in _SENT_SEP.finditer(text):
        if m.start() > pos:
            spans.append((pos, m.start()))
        pos = m.end()
    if pos < len(text):
        spans.append((pos, len(text)))
    out = []
    for a, b in spans:
        seg = text[a:b]
        lead = len(seg) - len(seg.lstrip())
        trail = len(seg.rstrip())
        if trail - lead > 3:
            out.append((a + lead, a + trail))
    return out


def sentences(text):
    return [text[a:b] for a, b in sentence_spans(text)]


_EN_FUNC = set("the of and is are what how when which who can does do for with in to may must should".split())
_ES_FUNC = set("el la de que qué cómo cuál cuánto cuántos cuántas en los las se un una por para es del al".split())
_QUANTITY = re.compile(
    r"\b(?:how\s+(?:many|much|old)|what\s+(?:\w+\s+){0,4}?(?:amount|number|fee|price|cost|age|minimum|maximum)s?|"
    r"cu[aá]nt[oa]s(?!\s+veces)|cu[aá]nt[oa](?!\s+tiempo)|qu[eé]\s+edad|a\s+qu[eé]\s+hora|"
    r"cu[aá]l\s+es\s+(?:el|la)\s+(?:\w+\s+){0,2}(?:n[uú]mero|importe|monto|edad|cantidad))\b", re.IGNORECASE)


def query_language(query):
    w = re.findall(r"[a-záéíóúñ]+", (query or "").lower())
    return "en" if sum(x in _EN_FUNC for x in w) > sum(x in _ES_FUNC for x in w) else "es"


def parse_answer(answer):
    if isinstance(answer, dict):
        return answer
    if not isinstance(answer, str):
        return None
    s = answer.strip()
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


class _UnitIndex:
    def __init__(self, path=UNITS_PATH):
        self.available = os.path.exists(path)
        self.leaves = defaultdict(list)
        self.by_id = {}
        if not self.available:
            return
        with open(path, encoding="utf-8") as fh:
            units = [json.loads(l) for l in fh]
        for u in units:
            self.by_id[u["unit_id"]] = u
        for u in units:
            if u["unit_level"] == 2 or not u.get("child_unit_ids"):
                self.leaves[u["page"]].append(u)
        for pg in self.leaves:
            self.leaves[pg].sort(key=lambda u: u["char_start"])

    def leaf_at(self, page, raw_offset):
        lst = self.leaves.get(page, [])
        starts = [u["char_start"] for u in lst]
        i = bisect_right(starts, raw_offset) - 1
        if 0 <= i < len(lst) and lst[i]["char_start"] <= raw_offset < max(lst[i]["char_end"], lst[i]["char_start"] + 1):
            return lst[i]
        return None


class DecisionIntegrityGate:
    def __init__(self, corpus_passages=None, units_path=UNITS_PATH, max_df=None, specific_max_df=None):
        self.max_df = DISTINCTIVE_MAX_DF if max_df is None else max_df
        self.specific_max_df = SPECIFIC_MAX_DF if specific_max_df is None else specific_max_df
        self.units = _UnitIndex(units_path)
        self.distinctive = set()
        self.stem_df, self.n_pages = Counter(), 0
        self.page_text = {}
        if corpus_passages:
            for p in corpus_passages:
                pg = p.get("pdf_page_index") or p.get("page")
                if pg is not None:
                    self.page_text.setdefault(int(pg), p.get("text_original") or "")
            self.distinctive = self.glossary_terms(corpus_passages)
            pages = {}
            for p in corpus_passages:
                pages.setdefault(p.get("pdf_page_index") or p.get("page"), p.get("text_original") or "")
            for t in pages.values():
                self.stem_df.update(content_stems(t))
            self.n_pages = len(pages)

    def pertinent(self, quote_stems, query_stems):
        """DIG-05 rule: >=1 shared distinctive stem, or >=2 shared specific stems. Without a corpus every
        shared stem counts as distinctive (documented fallback for synthetic fixtures)."""
        shared = quote_stems & query_stems
        if not self.n_pages:
            return bool(shared)
        df = lambda s: self.stem_df.get(s, 0) / self.n_pages
        if any(0 < df(s) <= self.max_df for s in shared):
            return True
        return bool(self.specific_max_df) and sum(1 for s in shared if 0 < df(s) <= self.specific_max_df) >= 2

    def distinctive_stems(self, stems):
        """Stems present in the SOR whose page frequency is <= DISTINCTIVE_MAX_DF. Without a corpus
        (n_pages == 0) every stem is kept (documented fallback, used only by synthetic fixtures)."""
        if not self.n_pages:
            return set(stems)
        return {s for s in stems if 0 < self.stem_df.get(s, 0) <= self.max_df * self.n_pages}

    @staticmethod
    def glossary_terms(corpus_passages):
        """Terminologia tecnica tomada del propio SOR (derivada de datos, no lista manual):
        - G1.1 Glossary of Japanese Terms / G1.2 Names of Judo Techniques: la grafia latina que
          precede a la grafia japonesa en cada entrada (misma linea o linea(s) previas de la caja);
        - G1.3 Penalty Codes: la columna 'Penalty given' que sigue a cada codigo PSn/HSn."""
        terms, seen = set(), set()
        jp = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]|\(No Kanji\)")
        latin = re.compile(r"^(?:\d+\s+)?([A-Za-z][A-Za-z\-]*(?:\s[A-Za-z][A-Za-z\-]*)?)")

        def add(phrase):
            for t in strip_accents(phrase.lower()).split():
                if len(t) >= 4 and t not in STOP:
                    terms.add(t)
        for p in corpus_passages:
            art = str(p.get("article_id") or "")
            pg = p.get("pdf_page_index") or p.get("page")
            if pg in seen or not art.startswith(("G1.1", "G1.2", "G1.3")):
                continue
            seen.add(pg)
            text = p.get("text_original") or ""
            if art.startswith("G1.3"):
                for m in re.finditer(r"\b[PH]S\d+\s+([A-Za-z][A-Za-z\-]+)", text):
                    add(m.group(1))
                continue
            buf = []
            for line in text.split("\n"):
                line = line.strip()
                m = jp.search(line)
                if not m:
                    if re.fullmatch(r"[A-Za-z][A-Za-z\-]*(?:\s[A-Za-z\-]+)?", line):
                        buf.append(line)
                    else:
                        buf = []
                    continue
                head = latin.match(line[:m.start()].strip())
                if head:
                    add(head.group(1))
                elif buf:
                    flat = lambda x: re.sub(r"[\s\-]", "", x.lower())
                    if len(buf) >= 2 and flat(buf[-2]) == flat(buf[-1]):
                        add(buf[-2])          # caja "Hansoku-make / Hansoku make / <kanji>"
                    elif "-" in buf[-1]:
                        add(buf[-1])
                buf = []
        return terms

    # ------------------------------------------------------------------ helpers
    def _locate(self, quote_n, passage):
        text = passage.get("text_original") or ""
        nt, imap = normalize_with_map(text)
        pos = nt.find(quote_n)
        if pos < 0:
            return None
        return {"raw_start": imap[pos], "raw_end": imap[min(pos + len(quote_n), len(imap)) - 1] + 1, "norm_text": nt}

    def _canonical(self, quote_n, passage):
        """(page, text, raw_start, raw_end) of the quote in the CANONICAL corpus page text: the passage
        page first, then neighbouring pages (stitched evidence spans several pages). Without a corpus,
        the delivered text itself is used."""
        page = passage.get("page") or passage.get("pdf_page_index")
        try:
            p0 = int(page)
        except (TypeError, ValueError):
            p0 = None
        if self.page_text and p0 is not None:
            for pg in [p0] + [p0 + d for k in range(1, 5) for d in (k, -k)]:
                t = self.page_text.get(pg)
                if t is None:
                    continue
                nt, imap = normalize_with_map(t)
                pos = nt.find(quote_n)
                if pos >= 0:
                    return pg, t, imap[pos], imap[min(pos + len(quote_n), len(imap)) - 1] + 1
            return None
        t = passage.get("text_original") or ""
        nt, imap = normalize_with_map(t)
        pos = nt.find(quote_n)
        if pos < 0:
            return None
        return p0, t, imap[pos], imap[min(pos + len(quote_n), len(imap)) - 1] + 1

    def _window(self, page, text, raw_start, raw_end):
        """Leaf unit containing the quote and the +-WINDOW sentence span inside that unit."""
        unit = self.units.leaf_at(page, raw_start) if self.units.available else None
        # The derived unit is usable only if it was cut from exactly this page text.
        if unit is None or unit.get("source_text_sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest():
            return None, []
        base = unit["char_start"]
        utext = text[base:unit["char_end"]]
        sents = [(base + a, base + b, utext[a:b]) for a, b in sentence_spans(utext)]
        hit = [i for i, (a, b, _s) in enumerate(sents) if a < raw_end and b > raw_start]
        if not hit:
            return unit, []
        lo, hi = max(0, hit[0] - WINDOW_SENTENCES), min(len(sents), hit[-1] + WINDOW_SENTENCES + 1)
        return unit, sents[lo:hi]

    def _heading_of_quote(self, quote_n, passage):
        """Titulo de la unidad derivada que contiene la cita literal en el texto canonico de su pagina
        (o el de su unidad padre). Solo si la unidad se corto de ese mismo texto. None si no hay."""
        if not self.units.available:
            return None
        canon = self._canonical(quote_n, passage)
        if canon is None:
            return None
        page, text, raw_start, _raw_end = canon
        unit = self.units.leaf_at(page, raw_start)
        if unit is None or unit.get("source_text_sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest():
            return None
        seen = 0
        while unit is not None and seen < 4:
            if unit.get("heading"):
                return unit["heading"]
            unit = self.units.by_id.get(unit.get("parent_unit_id")) if unit.get("parent_unit_id") else None
            seen += 1
        return None

    # ------------------------------------------------------------------ main
    def evaluate(self, answer, query, search_query_en, evidence, related, supplementary_texts=()):
        checks = []

        def check(code, ok, detail=""):
            checks.append({"code": code, "passed": bool(ok), "detail": detail})
            return ok

        obj = parse_answer(answer)
        delivered = {p.get("passage_id"): p for p in [*evidence, *related] if p.get("passage_id")}
        direct_ids = {p.get("passage_id") for p in evidence}
        if obj is None:
            check("DIG-00_JSON", False, "respuesta no es JSON estructurado")
            return self._result(checks)
        ans = str(obj.get("answerability", "")).strip().upper()
        conflicts = obj.get("evidence_conflicts") or []
        check("DIG-01_SUFICIENCIA_DECLARADA", ans == "RESPALDADA" and not conflicts,
              f"answerability={ans or 'AUSENTE'} conflicts={len(conflicts) if isinstance(conflicts, list) else conflicts}")
        quotes = obj.get("evidence_quotes") if isinstance(obj.get("evidence_quotes"), list) else []
        cited = set(SOR_ID.findall(json.dumps({k: obj.get(k) for k in ("summary", "normative_basis", "citations")}, ensure_ascii=False)))
        cited &= set(delivered)
        q_ids = {q.get("passage_id") for q in quotes if isinstance(q, dict)}
        check("DIG-02_CITAS_CON_CITA_LITERAL", bool(cited) and cited <= q_ids,
              f"citados={sorted(cited)} sin_cita_literal={sorted(cited - q_ids)}")
        supp_norm = [norm(s) for s in supplementary_texts if s]
        query_stems = content_stems(query) | content_stems(search_query_en or "")
        located, quote_texts, bad_literal, bad_shadow = [], [], [], []
        pertinent_by_pid = defaultdict(bool)
        for q in quotes:
            if not isinstance(q, dict):
                continue
            pid, qt = q.get("passage_id"), str(q.get("quote") or "")
            qn = norm(qt)
            if pid not in delivered or len(qn.split()) < MIN_QUOTE_WORDS:
                bad_literal.append(f"{pid}:{qt[:40]!r}")
                continue
            loc = self._locate(qn, delivered[pid])
            if loc is None:
                (bad_shadow if any(qn in s for s in supp_norm) else bad_literal).append(f"{pid}:{qt[:40]!r}")
                continue
            if self.pertinent(content_stems(qt), query_stems):
                pertinent_by_pid[pid] = True
            elif FIX_PERTINENCE_HEADING:
                heading = self._heading_of_quote(qn, delivered[pid])
                if heading and self.pertinent(content_stems(heading), query_stems):
                    pertinent_by_pid[pid] = True
            located.append((pid, qt, loc))
            quote_texts.append(qt)
        check("DIG-03_CITA_LITERAL", bool(located) and not bad_literal, f"no_literales={bad_literal}")
        check("DIG-04_CITA_NO_SHADOW", not bad_shadow, f"citas_procedentes_de_SHADOW={bad_shadow}")
        no_pert = sorted(pid for pid in cited if not pertinent_by_pid.get(pid))
        check("DIG-05_PERTINENCIA_MINIMA", bool(located) and not no_pert and any(pertinent_by_pid.get(pid) for pid in direct_ids),
              f"terminos_distintivos_consulta={sorted(self.distinctive_stems(query_stems))[:10]} pasajes_citados_sin_cita_pertinente={no_pert}; "
              "heuristica necesaria, no suficiente")
        claims = " ".join(str(obj.get(k) or "") for k in CLAIM_FIELDS)
        quotes_join = " ".join(quote_texts)
        nums_missing = sorted(numbers_in(claims) - numbers_in(quotes_join))
        check("DIG-06_CIFRAS_RESPALDADAS", not nums_missing, f"cifras_sin_respaldo={nums_missing}")
        q_terms = {t for t in re.findall(r"[a-z][a-z\-]{3,}", strip_accents(norm(quotes_join + " " + query + " " + (search_query_en or ""))))}
        c_terms = {t for t in re.findall(r"[a-z][a-z\-]{3,}", strip_accents(norm(SOR_ID.sub(" ", claims))))}
        if FIX_HYPHEN_TERMS:
            q_terms |= {part for t in q_terms if "-" in t for part in t.split("-") if len(part) >= 4}
        terms_missing = sorted(t for t in c_terms & self.distinctive if t not in q_terms)
        check("DIG-07_TERMINOS_RESPALDADOS", not terms_missing, f"terminos_sin_respaldo={terms_missing[:12]}")
        all_answer = SOR_ID.sub(" ", " ".join(str(obj.get(k) or "") for k in (*CLAIM_FIELDS, "extended_analysis")))
        prim_text = " ".join(p.get("text_original") or "" for p in delivered.values())
        prim_words = set(re.findall(r"[a-z0-9][a-z0-9\-]{2,}", strip_accents(norm(prim_text))))
        qwords = set(re.findall(r"[a-z0-9][a-z0-9\-]{2,}", strip_accents(norm(query + " " + (search_query_en or "")))))
        supp_words = set(re.findall(r"[a-z0-9][a-z0-9\-]{2,}", strip_accents(" ".join(supp_norm))))
        ans_words = set(re.findall(r"[a-z0-9][a-z0-9\-]{2,}", strip_accents(norm(all_answer))))
        leak = sorted(w for w in (ans_words & supp_words) - prim_words - qwords - STOP)
        supp_join = " ".join(supplementary_texts or ())
        leak_nums = sorted((numbers_in(all_answer) & numbers_in(supp_join)) - numbers_in(prim_text)
                           - numbers_in(query + " " + (search_query_en or "")))
        leak_nums += [w for w in leak if any(ch.isdigit() for ch in w) and w not in leak_nums]
        leak_words = [w for w in leak if not any(ch.isdigit() for ch in w) and len(w) >= 4]
        leak_words = [w for w in leak_words if len(w) >= 5]
        if FIX_DIG08_LANGUAGE and query_language(all_answer) != "en":
            leak_words = [w for w in leak_words if "-" in w]
        check("DIG-08_SIN_INFLUENCIA_SHADOW", not leak_nums and not leak_words,
              f"presentes_solo_en_SHADOW: cifras={leak_nums} terminos={leak_words}")
        missing_exc, missing_refs, no_unit = [], [], []
        qn_all = [norm(t) for t in quote_texts]
        for pid, qt, _loc in located:
            segments = [x.strip() for x in PAGE_BREAK.split(norm(qt)) if len(x.split()) >= 3]
            for seg in segments or [norm(qt)]:
                canon = self._canonical(seg, delivered[pid])
                if canon is None:
                    no_unit.append(pid)
                    continue
                cpage, ctext, cstart, cend = canon
                unit, window = self._window(cpage, ctext, cstart, cend)
                if unit is None:
                    no_unit.append(pid)
                    continue
                loc = {"raw_start": cstart, "raw_end": cend}
                for a, b, s in window:
                    if EXCEPTION_MARKER.search(s) and not any(norm(s)[:60] in qn or qn in norm(s) for qn in qn_all):
                        missing_exc.append(f"{unit['unit_id']}: {s[:70]!r}")
                for r in unit.get("cross_refs", []):
                    if r.get("type") == "FIGURE" or not (loc["raw_start"] <= r["char_start"] < loc["raw_end"]):
                        continue
                    targets = r.get("resolved_point_unit_ids") or r.get("resolved_unit_ids") or []
                    tpids = {x for t in targets for x in self.units.by_id.get(t, {}).get("original_passage_ids", [])}
                    if tpids and not (tpids & set(delivered)):
                        missing_refs.append(f"{unit['unit_id']}: {r['raw']}")
        check("DIG-09_EXCEPCIONES_CITADAS", self.units.available and not no_unit and not missing_exc,
              f"unidades_no_disponibles={no_unit} excepciones_no_citadas={sorted(set(missing_exc))[:6]}")
        check("DIG-10_REFERENCIAS_ENTREGADAS", self.units.available and not missing_refs,
              f"referencias_citadas_no_entregadas={sorted(set(missing_refs))}")
        if self.n_pages and query_language(query) == "en":
            absent = sorted(s for s in content_stems(query) if self.stem_df.get(s, 0) == 0)
            check("DIG-11_TERMINOS_DE_CONSULTA_EN_SOR", not absent, f"terminos_ausentes_del_SOR={absent}")
        else:
            check("DIG-11_TERMINOS_DE_CONSULTA_EN_SOR", True, "no evaluado (consulta no inglesa o sin corpus)")
        quantity = bool(_QUANTITY.search(query or ""))
        check("DIG-12_CIFRA_PARA_PREGUNTA_CUANTITATIVA", not quantity or bool(numbers_in(quotes_join)),
              f"pregunta_cuantitativa={quantity} cifras_en_citas={sorted(numbers_in(quotes_join))[:8]}")
        return self._result(checks)

    @staticmethod
    def _result(checks):
        failed = [c["code"] for c in checks if not c["passed"]]
        by = {c["code"]: c["passed"] for c in checks}
        lvl = lambda codes: ("SUPERADO" if all(by.get(c, False) for c in codes) else "FALLIDO")
        return {
            "version": dig_version(),
            "number_normalization": NUMBER_NORMALIZATION,
            "decision": "PERMITIR" if not failed else "ABSTENER",
            "failed_checks": failed,
            "levels": {
                "A_cita_sor": "VERIFICADO_POR_VALIDADOR_DE_CITAS",
                "B_pertinencia": lvl(["DIG-05_PERTINENCIA_MINIMA"]) + " (heuristica necesaria, no suficiente)",
                "C_suficiencia": lvl(["DIG-01_SUFICIENCIA_DECLARADA", "DIG-02_CITAS_CON_CITA_LITERAL", "DIG-03_CITA_LITERAL",
                                      "DIG-06_CIFRAS_RESPALDADAS", "DIG-07_TERMINOS_RESPALDADOS",
                                      "DIG-09_EXCEPCIONES_CITADAS", "DIG-10_REFERENCIAS_ENTREGADAS",
                                      "DIG-11_TERMINOS_DE_CONSULTA_EN_SOR", "DIG-12_CIFRA_PARA_PREGUNTA_CUANTITATIVA"]) + " (controles estructurales)",
                "D_respaldo_efectivo": "NO_VERIFICADO (sin verificacion de entailment)",
            },
            "checks": checks,
        }

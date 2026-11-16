"""Fase 8 / Etapa 1 - Capa derivada de segmentacion normativa (article_units_v1).

Capa DERIVADA y NO NORMATIVA. No modifica el corpus original, sus IDs ni el grafo.
Cada unidad es un corte literal (slice) del texto de una pagina del corpus original:
    derived_text == page_text[char_start:char_end]
por lo que el texto original es reconstruible exactamente.

Jerarquia:
    nivel 1  PAGE_HEADER | SEGMENT (ARTICLE / CONTINUATION / COVER) | EMPTY_PAGE
             -> particion exacta del texto de la pagina
    nivel 2  CLAUSE (INTRO / NUMBERED / LETTERED) dentro de un SEGMENT
             -> particion exacta del SEGMENT (solo si la numeracion es regular)

Reglas de segmentacion (deterministas, sin division por longitud):
  * Encabezados: lineas que empiezan por un rotulo de articulo/seccion. Se aceptan si
    (a) coinciden con el article_id/heading de un pasaje original de esa pagina, o
    (b) son "Article N" / "X1.N" que no existen en los metadatos (se registran como
        ADVERTENCIA, nunca se corrigen los metadatos).
    Las menciones de un rotulo que pertenece a otra pagina se rechazan (no son encabezados).
  * Clausulas: marcadores al inicio de linea "N." o "x)". Se usa el primer tipo encontrado
    como nivel superior y solo se divide si la secuencia es consecutiva; si no, el segmento
    queda NO_SEGMENTADA con motivo.
  * Una clausula que comienza con un conector de excepcion se une a la clausula anterior
    (no se separan condiciones de excepciones). Las listas con vinetas no se dividen.
  * Encabezado y referencias cruzadas se conservan como campos explicitos.

Uso:
    python scripts/build_article_units.py               # construye (no sobrescribe)
    python scripts/build_article_units.py --check       # reconstruye en memoria y compara
    python scripts/build_article_units.py --overwrite   # regenera artefactos existentes
Solo biblioteca estandar.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

PROCESSOR_NAME = "sor_article_unit_segmenter"
PROCESSOR_VERSION = "1.0.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_REL = "data/processed/rebuild_2026_08_corrected/passages_candidate.json"
OUT_REL = "data/derived/article_units_v1"
NORMATIVE_STATUS = "DERIVADA_NO_NORMATIVA"

HEADER_RE = re.compile(r"\A(?:Sport and Organisation Rules of the International Judo Federation\npage - \d+\n|"
                       r"page - \d+\nSport and Organisation Rules of the International Judo Federation\n)")
H_ARTICLE = re.compile(r"Article\s+(\d+(?:\s?\.\s?\d+)*)(?:\s?\.)?(?=\s+\S)")
H_APPX = re.compile(r"([A-H]1(?:\s?\.\s?\d+)+)(?:\s?\.)?(?=\s+[A-Z])")
H_NUM = re.compile(r"(\d+(?:\s?\.\s?\d+)+)(?:\s?\.)?(?=\s+[A-Z])")
NUM_MARK = re.compile(r"(\d{1,3})\.\s")
LET_MARK = re.compile(r"([a-z])\)\s")
BULLET = re.compile(r"(?:•|o\s|▪|-\s)")
EXCEPTION_CONNECTIVE = re.compile(
    r"(?:Although|However|Except|Exception|Unless|Notwithstanding|Nevertheless|In this situation|"
    r"In this case|This does not apply|The only exception)\b")
EXCEPTION_MARKER = re.compile(
    r"\b(?:except|exceptions?|unless|however|although|notwithstanding|nevertheless|does not apply|"
    r"no score or penalty|only if|only when|can only)\b", re.IGNORECASE)
REF_PATTERNS = [
    ("ARTICLE", re.compile(r"\bArticles?\s+(\d+(?:\s?\.\d+)*)(?:\s*,?\s*points?\s+(\d+))?")),
    ("APPENDIX_SECTION", re.compile(r"\b([A-H]1(?:\s?\.\s?\d+)+)")),
    ("TABLE", re.compile(r"\btable\s+(\d+(?:\s?\.\s?\d+)+)", re.IGNORECASE)),
    ("SECTION", re.compile(r"\b(?:refer to|see|section|chapter)\s+(\d+(?:\s?\.\s?\d+)+)", re.IGNORECASE)),
    ("FIGURE", re.compile(r"\b(?:pictures?|figures?)\s+(\d+(?:\s?\.\s?\d+)*(?:\s?-\s?\d+(?:\s?\.\s?\d+)*)?)", re.IGNORECASE)),
]


def sha256(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def norm_label(s):
    s = re.sub(r"\s*\.\s*", ".", (s or "").strip())
    s = re.sub(r"\s+", " ", s).rstrip(".")
    return s


def norm_text(s):
    return re.sub(r"\s+", " ", s or "").strip()


def iter_lines(text, start, end):
    """Yield (offset, line) for each line beginning inside [start, end)."""
    pos = start
    while pos < end:
        nl = text.find("\n", pos, end)
        line_end = end if nl == -1 else nl
        yield pos, text[pos:line_end]
        if nl == -1:
            break
        pos = nl + 1


def group_pages(passages):
    pages = defaultdict(list)
    for p in passages:
        pages[p["pdf_page_index"]].append(p)
    return dict(sorted(pages.items()))


def label_pages(passages):
    """normalized article label -> set of pages where the metadata places that label."""
    out = defaultdict(set)
    for p in passages:
        out[norm_label(p.get("article_id"))].add(p["pdf_page_index"])
    return out


def title_capitalized(rest):
    rest = rest.strip()
    return bool(rest) and rest[0].isupper()


def label_key(lab):
    """('Article', (18, 2)) | ('B', (1, 7)) | None for non-numbered labels."""
    m = re.fullmatch(r"Article (\d+(?:\.\d+)*)", lab or "")
    if m:
        return "Article", tuple(int(x) for x in m.group(1).split("."))
    m = re.fullmatch(r"([A-H])(\d+(?:\.\d+)*)", lab or "")
    if m:
        return m.group(1), tuple(int(x) for x in m.group(2).split("."))
    return None


def order_plausible(lab, page, label_to_pages):
    """A heading absent from metadata is accepted only if its page lies between the pages of the
    metadata labels that immediately precede and follow it in document numbering order."""
    k = label_key(lab)
    if not k:
        return False
    fam = sorted((label_key(l)[1], min(pg), max(pg)) for l, pg in label_to_pages.items()
                 if label_key(l) and label_key(l)[0] == k[0])
    prev = [f for f in fam if f[0] < k[1]]
    nxt = [f for f in fam if f[0] > k[1]]
    if not prev or not nxt:
        return False
    return prev[-1][2] <= page <= nxt[0][1]


def detect_headings(page, text, body_start, page_passages, label_to_pages, errors):
    """Return sorted boundaries: dict(offset, label, heading, source, anchored_passages)."""
    meta = defaultdict(list)
    titles = []
    for p in page_passages:
        lab = norm_label(p.get("article_id"))
        meta[lab].append(p["passage_id"])
        hp = (p.get("heading_path") or [""])[0]
        if lab in ("GENERAL", "GLOSSARY"):
            titles.append((norm_text(hp), p["passage_id"]))
    found, used = [], set()
    for off, line in iter_lines(text, body_start, len(text)):
        if not line.strip():
            continue
        # (1) metadata title headings (GENERAL / GLOSSARY cover headings, may wrap lines)
        rest = norm_text(text[off:off + 200])
        hit = None
        for title, pid in titles:
            if title and ("T:" + title) not in used and rest.startswith(title[:40]):
                hit = ("T:" + title, title, [q for t, q in titles if t == title])
                break
        if hit:
            used.add(hit[0])
            found.append({"offset": off, "label": hit[1], "heading": norm_text(line),
                          "source": "METADATA_TITLE", "anchored_passages": hit[2]})
            continue
        for kind, rx in (("ARTICLE", H_ARTICLE), ("APPX", H_APPX), ("NUM", H_NUM)):
            m = rx.match(line)
            if not m:
                continue
            lab = ("Article " + norm_label(m.group(1))) if kind == "ARTICLE" else norm_label(m.group(1))
            if lab in used:
                errors.append(_err("INFO", "HEADING_LIKE_LINE_REPEATED", page, f"'{line[:60]}' repite rotulo {lab}; tratado como mencion"))
                break
            if lab in meta:
                used.add(lab)
                found.append({"offset": off, "label": lab, "heading": norm_text(line),
                              "source": "METADATA_LABEL", "anchored_passages": meta[lab]})
            elif kind in ("ARTICLE", "APPX") and lab not in label_to_pages and \
                    title_capitalized(line[m.end():]) and order_plausible(lab, page, label_to_pages):
                used.add(lab)
                found.append({"offset": off, "label": lab, "heading": norm_text(line),
                              "source": "DETECTED_NOT_IN_METADATA", "anchored_passages": []})
                errors.append(_err("WARNING", "HEADING_NOT_IN_METADATA", page,
                                   f"encabezado '{norm_text(line)[:80]}' no figura en metadatos; metadatos NO corregidos"))
            else:
                errors.append(_err("INFO", "HEADING_LIKE_LINE_REJECTED", page,
                                   f"'{line[:60]}' -> rotulo {lab} pertenece a otra pagina; mencion, no encabezado"))
            break
    for lab, pids in meta.items():
        if lab in ("GENERAL", "GLOSSARY"):
            continue
        if lab not in used:
            errors.append(_err("INFO", "METADATA_LABEL_NOT_HEADING_ON_PAGE", page,
                               f"rotulo {lab} ({','.join(pids)}) sin encabezado en esta pagina (continuacion o metadato inexacto)"))
    for title, pid in titles:
        if ("T:" + title) not in used:
            errors.append(_err("WARNING", "METADATA_HEADING_NOT_FOUND", page,
                               f"heading de metadatos '{title[:60]}' ({pid}) no localizado como encabezado"))
    return sorted(found, key=lambda b: b["offset"])


def _err(severity, code, page, detail, unit_id=None):
    return {"severity": severity, "code": code, "page": page, "unit_id": unit_id, "detail": detail}


def find_markers(rx, text, start, end):
    return [(m.start(), m.group(0)) for m in rx.finditer(text, start, end)]


def find_refs(text, start, end):
    refs = []
    for kind, rx in REF_PATTERNS:
        for m in rx.finditer(text, start, end):
            if kind == "ARTICLE":
                target = "Article " + norm_label(m.group(1))
                point = m.group(2)
            else:
                target = norm_label(m.group(1)).replace(" ", "")
                point = None
            refs.append({"type": kind, "raw": norm_text(m.group(0)), "target": target, "point": point,
                         "char_start": m.start(), "char_end": m.end()})
    refs.sort(key=lambda r: (r["char_start"], r["type"]))
    return refs


def clause_split(text, seg_start, seg_end, body_start):
    """Return (clauses, status, reason). clauses: list of dict(start, end, type, label, merged)."""
    marks = []
    for off, line in iter_lines(text, body_start, seg_end):
        for kind, rx in (("NUMBERED", NUM_MARK), ("LETTERED", LET_MARK)):
            m = rx.match(line)
            if m:
                marks.append((off, kind, m.group(1)))
                break
    if not marks:
        return [], "VALIDADA", "SIN_MARCADORES_DE_CLAUSULA"
    top = marks[0][1]
    top_marks = [m for m in marks if m[1] == top]
    if len(top_marks) < 2:
        return [], "VALIDADA", "UNA_SOLA_CLAUSULA"
    seq = [int(m[2]) if top == "NUMBERED" else ord(m[2]) for m in top_marks]
    if any(b != a + 1 for a, b in zip(seq, seq[1:])):
        shown = [m[2] for m in top_marks]
        return [], "NO_SEGMENTADA", f"NUMERACION_IRREGULAR: {top} {shown}"
    clauses = []
    if top_marks[0][0] > seg_start:
        clauses.append({"start": seg_start, "end": top_marks[0][0], "type": "INTRO", "label": None, "merged": []})
    for i, (off, kind, lab) in enumerate(top_marks):
        end = top_marks[i + 1][0] if i + 1 < len(top_marks) else seg_end
        body = text[off:end]
        after_label = body[len(lab) + 2:].lstrip()
        if clauses and clauses[-1]["type"] in ("NUMBERED", "LETTERED") and EXCEPTION_CONNECTIVE.match(after_label):
            clauses[-1]["end"] = end
            clauses[-1]["merged"].append(lab)
            continue
        clauses.append({"start": off, "end": end, "type": kind, "label": lab, "merged": []})
    return clauses, "VALIDADA", f"CLAUSULAS_{top}"


def make_unit(uid, level, utype, page, text, start, end, src_sha, **kw):
    dt = text[start:end]
    u = {
        "unit_id": uid, "unit_level": level, "unit_type": utype, "page": page,
        "char_start": start, "char_end": end, "derived_text": dt,
        "source_text_sha256": src_sha, "derived_text_sha256": sha256(dt),
        "segmentation_method": f"{PROCESSOR_NAME}/{PROCESSOR_VERSION}:{kw.pop('method')}",
        "normative_status": NORMATIVE_STATUS,
        "relation_to_official": "Corte literal de la pagina PDF {} del documento oficial SOR 2026-08; "
                                "no constituye fuente normativa nueva".format(page),
        "exception_markers": [{"marker": m.group(0), "char_start": m.start()} for m in EXCEPTION_MARKER.finditer(text, start, end)],
        "list_item_count": sum(1 for _o, ln in iter_lines(text, start, end) if BULLET.match(ln)),
    }
    u.update(kw)
    return u


def segment_corpus(passages):
    """Pure function: passages -> (units, errors). Never mutates input."""
    pages = group_pages(passages)
    label_to_pages = label_pages(passages)
    units, errors = [], []
    carried = None
    for page, pps in pages.items():
        texts = {p["text_original"] for p in pps}
        if len(texts) != 1:
            errors.append(_err("ERROR", "PAGE_TEXT_INCONSISTENT", page, "pasajes de la misma pagina con textos distintos"))
            continue
        text = pps[0]["text_original"]
        src_sha = pps[0]["text_sha256"]
        page_pids = sorted(p["passage_id"] for p in pps)
        by_label = defaultdict(list)
        for p in pps:
            by_label[norm_label(p.get("article_id"))].append(p["passage_id"])
        common = {"page_passage_ids": page_pids}
        if not text:
            units.append(make_unit(f"AU1-P{page:03d}-000", 1, "EMPTY_PAGE", page, text, 0, 0, src_sha,
                                   method="empty_page", parent_unit_id=None, article_label=None, heading=None,
                                   original_passage_ids=page_pids, passage_relation="PAGE", clause_label=None,
                                   validation_status="NO_SEGMENTADA", non_segmentation_reason="TEXTO_ORIGINAL_VACIO",
                                   cross_refs=[], merged_exception_clauses=[], **common))
            errors.append(_err("WARNING", "EMPTY_PAGE_TEXT", page, "texto original vacio; unidad EMPTY_PAGE"))
            continue
        seq = 0
        m = HEADER_RE.match(text)
        body_start = m.end() if m else 0
        if m:
            units.append(make_unit(f"AU1-P{page:03d}-{seq:03d}", 1, "PAGE_HEADER", page, text, 0, m.end(), src_sha,
                                   method="page_header", parent_unit_id=None, article_label=None, heading=None,
                                   original_passage_ids=page_pids, passage_relation="PAGE", clause_label=None,
                                   validation_status="VALIDADA", non_segmentation_reason=None, cross_refs=[],
                                   merged_exception_clauses=[], **common))
        else:
            errors.append(_err("INFO", "NO_PAGE_HEADER", page, "pagina sin linea de cabecera estandar"))
        bounds = detect_headings(page, text, body_start, pps, label_to_pages, errors)
        segs = []
        first = bounds[0]["offset"] if bounds else len(text)
        if text[body_start:first].strip():
            segs.append({"start": body_start, "end": first, "kind": "CONTINUATION", "b": None})
        for i, b in enumerate(bounds):
            start = b["offset"] if (segs or i > 0) else body_start
            end = bounds[i + 1]["offset"] if i + 1 < len(bounds) else len(text)
            segs.append({"start": start, "end": end, "kind": "ARTICLE", "b": b})
        if not segs:  # whitespace-only body after header
            segs.append({"start": body_start, "end": len(text), "kind": "CONTINUATION", "b": None})
        for s in segs:
            seq += 1
            uid = f"AU1-P{page:03d}-{seq:03d}"
            b = s["b"]
            if b is None:
                label, heading = carried, None
                pids = by_label.get(label or "", [])
                relation = "ARTICLE_METADATA" if pids else "PAGE_FALLBACK"
                if not pids:
                    pids = page_pids
                    errors.append(_err("WARNING", "CONTINUATION_ARTICLE_NOT_IN_PAGE_METADATA", page,
                                       f"continuacion de '{carried}' sin pasaje con ese article_id; relacion por pagina", uid))
                method, heading_end = "continuation_of_previous_article", s["start"]
            else:
                label, heading = b["label"], b["heading"]
                pids = b["anchored_passages"] or by_label.get(label, [])
                relation = "ARTICLE_METADATA" if pids else "PAGE_FALLBACK"
                if not pids:
                    pids = page_pids
                    errors.append(_err("WARNING", "ARTICLE_PAGE_METADATA_MISMATCH", page,
                                       f"articulo detectado '{label}' sin pasaje con ese article_id; relacion por pagina "
                                       f"(article_id de metadatos: {sorted(by_label)})", uid))
                method = "heading_" + b["source"].lower()
                nl = text.find("\n", b["offset"], s["end"])
                heading_end = s["end"] if nl == -1 else nl + 1
            carried = label
            utype = "COVER" if (b and b["source"] == "METADATA_TITLE") else s["kind"]
            clauses, cstatus, creason = clause_split(text, s["start"], s["end"], heading_end)
            seg = make_unit(uid, 1, utype, page, text, s["start"], s["end"], src_sha, method=method,
                            parent_unit_id=None, article_label=label, heading=heading, original_passage_ids=sorted(pids),
                            passage_relation=relation, clause_label=None, validation_status=cstatus,
                            non_segmentation_reason=(creason if cstatus == "NO_SEGMENTADA" else None),
                            clause_structure=creason, cross_refs=find_refs(text, heading_end, s["end"]),
                            merged_exception_clauses=[], child_unit_ids=[], **common)
            units.append(seg)
            if cstatus == "NO_SEGMENTADA":
                errors.append(_err("WARNING", "CLAUSE_SEGMENTATION_UNSAFE", page, creason, uid))
            for j, c in enumerate(clauses, 1):
                cid = f"{uid}-C{j:02d}"
                body_from = heading_end if c["type"] == "INTRO" else c["start"]
                cu = make_unit(cid, 2, c["type"], page, text, c["start"], c["end"], src_sha,
                               method=f"clause_{c['type'].lower()}", parent_unit_id=uid, article_label=label,
                               heading=heading, original_passage_ids=sorted(pids), passage_relation=relation,
                               clause_label=c["label"], validation_status="VALIDADA", non_segmentation_reason=None,
                               cross_refs=find_refs(text, max(body_from, c["start"]), c["end"]),
                               merged_exception_clauses=c["merged"], **common)
                units.append(cu)
                seg["child_unit_ids"].append(cid)
                if c["merged"]:
                    errors.append(_err("INFO", "EXCEPTION_CLAUSE_MERGED", page,
                                       f"clausula(s) {c['merged']} unida(s) a {c['label']} (conector de excepcion)", cid))
    resolve_refs(units, errors)
    return units, errors


def resolve_refs(units, errors):
    seg_by_label = defaultdict(list)
    clause_by_label_point = defaultdict(list)
    for u in units:
        if u["unit_level"] == 1 and u.get("article_label"):
            lab = u["article_label"]
            seg_by_label[lab].append(u["unit_id"])
            seg_by_label[lab.replace("Article ", "")].append(u["unit_id"])
        if u["unit_level"] == 2 and u.get("clause_label"):
            for lab in (u["article_label"] or "",):
                for pt in [u["clause_label"]] + list(u.get("merged_exception_clauses") or []):
                    clause_by_label_point[(lab, pt)].append(u["unit_id"])
    for u in units:
        for r in u.get("cross_refs", []):
            if r["type"] == "FIGURE":
                r["resolved_unit_ids"], r["resolution"] = [], "NO_APLICA_FIGURA"
                continue
            ids = list(seg_by_label.get(r["target"], []))
            if r["point"]:
                pts = clause_by_label_point.get((r["target"], r["point"]), [])
                r["resolved_point_unit_ids"] = pts
            r["resolved_unit_ids"] = ids
            r["resolution"] = "RESUELTA" if ids else "NO_RESUELTA"


# --------------------------------------------------------------------------- validation
def validate(units, passages):
    """Independent structural validation. Returns list of errors (no auto-correction)."""
    errs = []
    pages = group_pages(passages)
    by_id = {u["unit_id"]: u for u in units}
    if len(by_id) != len(units):
        dup = [k for k, v in Counter(u["unit_id"] for u in units).items() if v > 1]
        errs.append(_err("ERROR", "DUPLICATE_UNIT_ID", None, f"IDs duplicados: {dup[:10]}"))
    all_pids = {p["passage_id"] for p in passages}
    units_by_page = defaultdict(list)
    for u in units:
        units_by_page[u["page"]].append(u)
    mapped = set()
    for page, pps in pages.items():
        text = pps[0]["text_original"]
        page_sha = pps[0]["text_sha256"]
        us = units_by_page.get(page, [])
        if not us:
            errs.append(_err("ERROR", "PAGE_WITHOUT_UNITS", page, "pagina sin unidades"))
            continue
        lvl1 = sorted([u for u in us if u["unit_level"] == 1], key=lambda u: u["char_start"])
        pos = 0
        for u in lvl1:
            if u["char_start"] != pos:
                errs.append(_err("ERROR", "COVERAGE_GAP_OR_OVERLAP", page, f"esperado inicio {pos}, hallado {u['char_start']}", u["unit_id"]))
            pos = u["char_end"]
        if pos != len(text):
            errs.append(_err("ERROR", "COVERAGE_INCOMPLETE", page, f"cubierto hasta {pos} de {len(text)}"))
        if "".join(u["derived_text"] for u in lvl1) != text:
            errs.append(_err("ERROR", "RECONSTRUCTION_MISMATCH", page, "nivel 1 no reconstruye el texto original"))
        leaf_exc = leaf_refs = 0
        for u in us:
            if u["page"] != page:
                errs.append(_err("ERROR", "PAGE_MISMATCH", page, "unidad en pagina incorrecta", u["unit_id"]))
            if u["source_text_sha256"] != page_sha or sha256(text) != page_sha:
                errs.append(_err("ERROR", "SOURCE_HASH_MISMATCH", page, "hash de texto original inconsistente", u["unit_id"]))
            if u["derived_text"] != text[u["char_start"]:u["char_end"]]:
                errs.append(_err("ERROR", "DERIVED_TEXT_NOT_LITERAL", page, "texto derivado no es corte literal", u["unit_id"]))
            if u["derived_text_sha256"] != sha256(u["derived_text"]):
                errs.append(_err("ERROR", "DERIVED_HASH_MISMATCH", page, "hash derivado inconsistente", u["unit_id"]))
            for pid in u["original_passage_ids"]:
                if pid not in all_pids:
                    errs.append(_err("ERROR", "UNKNOWN_PASSAGE_ID", page, pid, u["unit_id"]))
                elif pid not in u["page_passage_ids"]:
                    errs.append(_err("ERROR", "PASSAGE_NOT_ON_PAGE", page, pid, u["unit_id"]))
                mapped.add(pid)
            if not u["original_passage_ids"]:
                errs.append(_err("ERROR", "UNIT_WITHOUT_PASSAGE", page, "unidad sin pasaje original", u["unit_id"]))
            for r in u.get("cross_refs", []):
                if not (u["char_start"] <= r["char_start"] < r["char_end"] <= u["char_end"]):
                    errs.append(_err("ERROR", "REF_OUTSIDE_UNIT", page, r["raw"], u["unit_id"]))
                for rid in r.get("resolved_unit_ids", []) + r.get("resolved_point_unit_ids", []):
                    if rid not in by_id:
                        errs.append(_err("ERROR", "REF_TARGET_MISSING", page, rid, u["unit_id"]))
            is_leaf = u["unit_level"] == 2 or not u.get("child_unit_ids")
            if is_leaf:
                leaf_exc += len(u["exception_markers"])
                leaf_refs += len(u.get("cross_refs", []))
            kids = [by_id[k] for k in u.get("child_unit_ids", []) if k in by_id]
            if u.get("child_unit_ids"):
                if len(kids) != len(u["child_unit_ids"]):
                    errs.append(_err("ERROR", "CHILD_MISSING", page, "hijo inexistente", u["unit_id"]))
                kids.sort(key=lambda k: k["char_start"])
                cpos = u["char_start"]
                for k in kids:
                    if k["char_start"] != cpos:
                        errs.append(_err("ERROR", "CHILD_GAP_OR_OVERLAP", page, f"{cpos}!={k['char_start']}", k["unit_id"]))
                    cpos = k["char_end"]
                    if k["parent_unit_id"] != u["unit_id"]:
                        errs.append(_err("ERROR", "PARENT_LINK_BROKEN", page, "", k["unit_id"]))
                if cpos != u["char_end"] or "".join(k["derived_text"] for k in kids) != u["derived_text"]:
                    errs.append(_err("ERROR", "CHILD_RECONSTRUCTION_MISMATCH", page, "hijos no reconstruyen al padre", u["unit_id"]))
        page_exc = len(EXCEPTION_MARKER.findall(text))
        if page_exc != leaf_exc:
            errs.append(_err("ERROR", "EXCEPTION_MARKERS_LOST", page, f"pagina={page_exc} hojas={leaf_exc}"))
        body_refs = sum(len(u.get("cross_refs", [])) for u in lvl1)
        if body_refs != leaf_refs:
            errs.append(_err("ERROR", "CROSS_REFS_SPLIT", page, f"segmentos={body_refs} hojas={leaf_refs}"))
    for pid in sorted(all_pids - mapped):
        errs.append(_err("ERROR", "PASSAGE_NOT_TRACEABLE", None, pid))
    return errs


# --------------------------------------------------------------------------- artifacts
def build_artifacts(passages, corpus_bytes):
    units, seg_errors = segment_corpus(passages)
    val_errors = validate(units, passages)
    errors = seg_errors + val_errors
    trace_p2u = defaultdict(list)
    for u in units:
        for pid in u["original_passage_ids"]:
            trace_p2u[pid].append({"unit_id": u["unit_id"], "relation": u["passage_relation"]})
    pages = group_pages(passages)
    lvl1 = [u for u in units if u["unit_level"] == 1]
    lvl2 = [u for u in units if u["unit_level"] == 2]
    leaves = lvl2 + [u for u in lvl1 if not u.get("child_unit_ids")]
    total_chars = sum(len(pps[0]["text_original"]) for pps in pages.values())
    covered = sum(u["char_end"] - u["char_start"] for u in lvl1)
    refs = [r for u in lvl1 for r in u.get("cross_refs", [])]
    sev = Counter(e["severity"] for e in errors)
    stats = {
        "pages": len(pages), "original_passages": len(passages),
        "distinct_page_texts": len({pps[0]["text_sha256"] for pps in pages.values()}),
        "units_total": len(units), "units_level1": len(lvl1), "units_level2": len(lvl2), "leaf_units": len(leaves),
        "units_by_type": dict(sorted(Counter(u["unit_type"] for u in units).items())),
        "units_by_validation_status": dict(sorted(Counter(u["validation_status"] for u in units).items())),
        "passage_relation_level1": dict(sorted(Counter(u["passage_relation"] for u in lvl1).items())),
        "segments_with_clauses": sum(1 for u in lvl1 if u.get("child_unit_ids")),
        "no_segmentadas": [{"unit_id": u["unit_id"], "reason": u["non_segmentation_reason"]} for u in units if u["validation_status"] == "NO_SEGMENTADA"],
        "exception_clause_merges": sum(1 for u in lvl2 if u["merged_exception_clauses"]),
        "exception_markers_total": sum(len(u["exception_markers"]) for u in leaves),
        "cross_refs_total": len(refs),
        "cross_refs_by_type": dict(sorted(Counter(r["type"] for r in refs).items())),
        "cross_refs_resolution": dict(sorted(Counter(r["resolution"] for r in refs).items())),
        "text_chars_total": total_chars, "text_chars_covered_level1": covered,
        "coverage_ratio": (covered / total_chars) if total_chars else 1.0,
        "passages_traceable": sum(1 for p in passages if p["passage_id"] in trace_p2u),
        "leaf_chars": {"min": min(len(u["derived_text"]) for u in leaves), "max": max(len(u["derived_text"]) for u in leaves),
                       "mean": round(sum(len(u["derived_text"]) for u in leaves) / len(leaves), 1)},
        "errors_by_severity": dict(sorted(sev.items())),
        "errors_by_code": dict(sorted(Counter(e["code"] for e in errors).items())),
    }
    report = {
        "processor": PROCESSOR_NAME, "processor_version": PROCESSOR_VERSION,
        "accepted": sev.get("ERROR", 0) == 0,
        "checks": ["coverage", "no_textual_loss", "no_accidental_duplication", "page_article_correspondence",
                   "id_integrity", "exception_preservation", "reference_integrity", "hash_consistency"],
        "error_count": sev.get("ERROR", 0), "warning_count": sev.get("WARNING", 0), "info_count": sev.get("INFO", 0),
        "errors": [e for e in errors if e["severity"] == "ERROR"],
        "warnings": [e for e in errors if e["severity"] == "WARNING"],
    }
    metadata = {
        "processor": PROCESSOR_NAME, "processor_version": PROCESSOR_VERSION, "normative_status": NORMATIVE_STATUS,
        "description": "Capa derivada de unidades articulo/clausula. No es fuente normativa; cada unidad es un corte literal del texto original.",
        "input_corpus": CORPUS_REL, "input_corpus_file_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
        "source_pdf_sha256": sorted({p.get("source_sha256") for p in passages}),
        "source_version": sorted({str(p.get("source_version")) for p in passages}),
        "build_command": "python scripts/build_article_units.py",
        "id_scheme": "AU1-P<page>-<seq> (nivel 1); AU1-P<page>-<seq>-C<nn> (nivel 2)",
        "unit_fields": sorted(units[0].keys()) if units else [],
    }
    files = {
        "units.jsonl": "".join(json.dumps(u, ensure_ascii=False, sort_keys=True) + "\n" for u in units),
        "traceability_map.json": _dump({"passage_to_units": dict(sorted(trace_p2u.items())),
                                        "unit_to_passages": {u["unit_id"]: u["original_passage_ids"] for u in units},
                                        "page_to_units": {str(pg): [u["unit_id"] for u in units if u["page"] == pg] for pg in pages}}),
        "coverage_stats.json": _dump(stats),
        "validation_report.json": _dump(report),
        "errors.jsonl": "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in errors),
        "metadata.json": _dump(metadata),
    }
    files["hashes.json"] = _dump({"artifacts_sha256": {k: sha256(v) for k, v in sorted(files.items())},
                                  "input_corpus_file_sha256": metadata["input_corpus_file_sha256"],
                                  "processor_version": PROCESSOR_VERSION})
    return files, units, errors, stats, report


def _dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def load_corpus(root=ROOT):
    path = os.path.join(root, CORPUS_REL)
    with open(path, "rb") as fh:
        raw = fh.read()
    return json.loads(raw.decode("utf-8")), raw


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--check", action="store_true", help="reconstruye en memoria y compara con los artefactos existentes")
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    a = ap.parse_args(argv)
    passages, raw = load_corpus()
    before = hashlib.sha256(raw).hexdigest()
    files, _u, _e, stats, report = build_artifacts(passages, raw)
    _p, raw_after = load_corpus()
    if hashlib.sha256(raw_after).hexdigest() != before:
        print("ERROR: el corpus cambio durante la construccion", file=sys.stderr)
        return 3
    if a.check:
        diffs = []
        for name, content in files.items():
            fp = os.path.join(a.out, name)
            if not os.path.exists(fp):
                diffs.append(f"{name}: ausente")
                continue
            with open(fp, "rb") as fh:
                if fh.read().decode("utf-8").replace("\r\n", "\n") != content:
                    diffs.append(f"{name}: difiere")
        print("REPRODUCIBLE" if not diffs else "NO REPRODUCIBLE: " + "; ".join(diffs))
        return 0 if not diffs else 1
    if os.path.isdir(a.out) and os.listdir(a.out) and not a.overwrite:
        print(f"ERROR: {a.out} ya existe; use --check o --overwrite (no se sobrescribe por defecto)", file=sys.stderr)
        return 2
    os.makedirs(a.out, exist_ok=True)
    for name, content in files.items():
        with open(os.path.join(a.out, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    print(json.dumps({k: stats[k] for k in ("pages", "original_passages", "units_total", "units_level1", "units_level2",
                                            "coverage_ratio", "passages_traceable", "errors_by_severity")}, indent=1))
    print("ACEPTADA" if report["accepted"] else "NO ACEPTADA (ver validation_report.json)")
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    sys.exit(main())

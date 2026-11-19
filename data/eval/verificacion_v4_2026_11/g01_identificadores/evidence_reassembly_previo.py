"""Reparaciones deterministas de la atribucion y re-ensamblado dirigido de la evidencia.

Ninguna funcion de este modulo toma una decision ni cambia un control del DIG: solo corrige la FORMA de la
atribucion (identificador de pasaje, literalidad tipografica de una cita) o entrega al modelo pasajes reales del
SOR que la propia respuesta o el propio DIG senalan como necesarios. Toda respuesta resultante vuelve a pasar la
validacion de citas y TODOS los controles del DIG.

ADA_CITATION_REPAIR=1   Identificador gemelo: el modelo cita SOR-...-P042-S054 y se le entrego SOR-...-P042-S053,
                        de la MISMA pagina y con el MISMO texto en el corpus (los pasajes son por pagina). El
                        identificador se sustituye por el entregado solo si cada cita literal atribuida a el se
                        localiza en el texto entregado. Tambien pagina COSIDA: el pasaje entregado contiene el texto
                        de otra pagina de la seccion y muestra su identificador (marcador de salto de pagina); ese
                        identificador se sustituye por el del pasaje entregado si cada cita es literal en el.
ADA_QUOTE_REPAIR=1      Cita con diferencias solo tipograficas (vinetas, saltos de linea, puntuacion) o con
                        elipsis ("..."): se sustituye por el/los fragmento(s) LITERALES del pasaje que contienen
                        exactamente las mismas palabras en el mismo orden. Si algun fragmento no se localiza, la
                        cita no se toca (DIG-03 la rechazara).
ADA_TARGETED_REASSEMBLY=1  Si la respuesta se abstiene porque (a) cita un pasaje no entregado contiguo, de la misma
                        seccion, a uno entregado (p. ej. la pagina intermedia de una lista) o (b) DIG-10 detecta una
                        referencia cruzada citada cuyo destino no se entrego, se repite UNA vez el analisis
                        entregando ademas esos pasajes (maximo MAX_TARGETS). No cambia K ni la recuperacion.
"""
from __future__ import annotations

import json
import os
import re

from decision_integrity import MIN_QUOTE_WORDS, SOR_ID, norm, parse_answer, sentence_spans

MAX_TARGETS = 3
_ELLIPSIS = re.compile(r"\s*(?:\.{3,}|…)\s*")
_WORDS = re.compile(r"\w+", re.UNICODE)


def _on(name):
    return os.environ.get(name, "").strip() == "1"


def citation_repair_enabled():
    return _on("ADA_CITATION_REPAIR")


def quote_repair_enabled():
    return _on("ADA_QUOTE_REPAIR")


def reassembly_enabled():
    return _on("ADA_TARGETED_REASSEMBLY")


def _section(pid):
    m = re.search(r"-S(\d+)$", pid or "")
    return m.group(1) if m else None


def _page(pid):
    m = re.search(r"-P(\d+)-S\d+$", pid or "")
    return int(m.group(1)) if m else None


def _literal_in(quote, text):
    q = norm(quote)
    return bool(q) and q in norm(text)


# ---------------------------------------------------------------------------------------------- identificadores
def repair_citation_ids(answer, delivered, corpus):
    """Sustituye identificadores no entregados por su gemelo entregado (misma pagina, mismo texto de corpus).
    'delivered': {pid: pasaje entregado}; 'corpus': {pid: pasaje del corpus}. Devuelve (respuesta, cambios)."""
    obj = parse_answer(answer)
    if not isinstance(obj, dict):
        return answer, []
    raw = json.dumps(obj, ensure_ascii=False)
    cited = set(SOR_ID.findall(raw))
    changes = []
    for pid in sorted(cited - set(delivered)):
        quotes = [q for q in obj.get("evidence_quotes") or [] if isinstance(q, dict) and q.get("passage_id") == pid]

        def literal(d):
            return all(_literal_in(str(q.get("quote") or ""), delivered[d].get("text_original") or "") for q in quotes)
        src = corpus.get(pid)
        twins = [d for d in delivered if src and _page(d) == _page(pid) and d in corpus
                 and (corpus[d].get("text_original") or "") == (src.get("text_original") or "")]
        if len(twins) == 1 and literal(twins[0]):
            changes.append({"de": pid, "a": twins[0], "motivo": "misma pagina y mismo texto de corpus"})
            continue
        if twins or not quotes:
            continue
        # Pagina cosida: un pasaje entregado incluye el texto de la pagina 'pid' y muestra su identificador (marcador
        # de salto de pagina del PassageStitcher o 'stitched_kuns'). Se atribuye al pasaje entregado que contiene
        # literalmente todas sus citas (el de pagina mas proxima si hay varios: el texto citado es el mismo).
        hosts = [d for d, p in delivered.items()
                 if (pid in (p.get("stitched_kuns") or []) or pid in (p.get("text_original") or "")) and literal(d)]
        if hosts:
            host = min(hosts, key=lambda d: (abs((_page(d) or 0) - (_page(pid) or 0)), d))
            changes.append({"de": pid, "a": host, "motivo": "pagina incluida en el pasaje cosido entregado"})
    if not changes:
        return answer, []
    for c in changes:
        raw = raw.replace(c["de"], c["a"])
    obj = json.loads(raw)
    if isinstance(obj.get("citations"), list):
        obj["citations"] = list(dict.fromkeys(obj["citations"]))
    return json.dumps(obj, ensure_ascii=False), changes


# ---------------------------------------------------------------------------------------------------- citas
def _loose_span(segment, text):
    """Span bruto del pasaje con las MISMAS palabras que 'segment', en el mismo orden, separadas solo por
    caracteres no alfanumericos (espacios, saltos de linea, vinetas, puntuacion). None si no hay uno unico."""
    words = _WORDS.findall(segment.lower())
    if len(words) < 3:
        return None
    pat = re.compile(r"(?<!\w)" + r"\W+".join(re.escape(w) for w in words) + r"(?!\w)", re.IGNORECASE | re.UNICODE)
    hits = list(pat.finditer(text))
    if len(hits) != 1:
        return None
    return hits[0].span()


def _sentence_around(text, a, b):
    spans = [s for s in sentence_spans(text) if s[0] < b and s[1] > a]
    if not spans:
        return None
    return spans[0][0], spans[-1][1]


def _clean(raw):
    return re.sub(r"\s+", " ", raw).strip()


def repair_quotes(answer, delivered, gate):
    """Repara citas no literales solo por tipografia o elipsis. Devuelve (respuesta, reparaciones)."""
    obj = parse_answer(answer)
    if not isinstance(obj, dict) or not isinstance(obj.get("evidence_quotes"), list):
        return answer, []
    out, repairs = [], []
    for q in obj["evidence_quotes"]:
        if not isinstance(q, dict):
            out.append(q)
            continue
        pid, qt = q.get("passage_id"), str(q.get("quote") or "")
        passage = delivered.get(pid)
        if passage is None or gate._locate(norm(qt), passage) is not None:
            out.append(q)
            continue
        text = passage.get("text_original") or ""
        new = []
        for seg in [s for s in _ELLIPSIS.split(qt) if s.strip()]:
            if gate._locate(norm(seg), passage) is not None and len(norm(seg).split()) >= MIN_QUOTE_WORDS:
                new.append(_clean(seg))
                continue
            span = _loose_span(seg, text)
            if span is None:
                new = None
                break
            a, b = span
            if len(norm(text[a:b]).split()) < MIN_QUOTE_WORDS:
                around = _sentence_around(text, a, b)
                if around is None:
                    new = None
                    break
                a, b = min(a, around[0]), max(b, around[1])
            frag = _clean(text[a:b])
            if gate._locate(norm(frag), passage) is None or len(norm(frag).split()) < MIN_QUOTE_WORDS:
                new = None
                break
            new.append(frag)
        if not new:
            out.append(q)
            continue
        for frag in new:
            out.append(dict(q, quote=frag))
        repairs.append({"passage_id": pid, "original": qt[:200], "literal": [f[:200] for f in new]})
    if not repairs:
        return answer, []
    obj["evidence_quotes"] = out
    return json.dumps(obj, ensure_ascii=False), repairs


# --------------------------------------------------------------------------------------------- re-ensamblado
def _record(pid, corpus, seed, relation):
    p = corpus[pid]
    return {"passage_id": pid, "source_seed": seed, "relation": relation, "article_id": p.get("article_id"),
            "page": p.get("pdf_page_index"),
            "title": p.get("heading_path", [""])[0] if p.get("heading_path") else f"Art. {p.get('article_id')}",
            "source_url": f"{p.get('source_url', '')}#page={p.get('pdf_page_index')}",
            "text_original": p.get("text_original", "")}


def reassembly_targets(answer, decision_integrity, delivered, corpus, gate):
    """Pasajes reales del SOR que conviene entregar en un segundo intento. Devuelve [(pid, semilla, motivo)]."""
    out = []
    seen = set(delivered)
    obj = parse_answer(answer) if answer else None
    if isinstance(obj, dict):
        # (a) pasaje citado no entregado, de la misma seccion y a <= 2 paginas de uno entregado
        for pid in sorted(set(SOR_ID.findall(json.dumps(obj, ensure_ascii=False))) - seen):
            if pid not in corpus:
                continue
            near = [d for d in delivered if _section(d) == _section(pid) and _page(d) is not None
                    and _page(pid) is not None and abs(_page(d) - _page(pid)) <= 2]
            if near:
                out.append((pid, near[0], "continuidad de seccion citada por la respuesta"))
                seen.add(pid)
    # (b) destino no entregado de una referencia cruzada que figura dentro de una cita (DIG-10)
    for c in (decision_integrity or {}).get("checks") or []:
        if c.get("code") != "DIG-10_REFERENCIAS_ENTREGADAS" or c.get("passed"):
            continue
        for unit_id, ref in re.findall(r"(AU1-P\d+-\d+): ([^'\]]+?)(?=', '|'\]|$)", c.get("detail") or ""):
            unit = gate.units.by_id.get(unit_id) or {}
            for r in unit.get("cross_refs", []):
                if r.get("raw") != ref:
                    continue
                for t in r.get("resolved_point_unit_ids") or r.get("resolved_unit_ids") or []:
                    for pid in gate.units.by_id.get(t, {}).get("original_passage_ids", []):
                        if pid in corpus and pid not in seen:
                            seed = next(iter(unit.get("original_passage_ids") or []), "")
                            out.append((pid, seed, f"referencia cruzada citada: {ref}"))
                            seen.add(pid)
    return [_record(pid, corpus, seed, why) for pid, seed, why in out[:MAX_TARGETS]]

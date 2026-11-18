"""Experimento: segmentacion por APARTADOS normativos del SOR 2026-08 (capa experimental, no normativa).

Entrada (solo lectura):
  * data/processed/rebuild_2026_08_corrected/passages_candidate.json  (corpus canonico; texto de pagina)
  * data/derived/article_units_v1/units.jsonl  (Fase 8: segmentos ARTICLE/CONTINUATION por pagina, cortes literales)
  * PDF oficial (solo para la auditoria: numero de paginas y esquema/TOC; no se extrae texto de el)
Salida (solo en experiments/segmentacion_apartados_2026/):
  * audit.json                      auditoria de estructura y metadatos
  * units.jsonl                     apartados + tablas, con spans literales y trazabilidad
  * index/                          indice experimental en el formato que lee ReasoningRetrievalEngine
      passages_candidate.json, vector_index_candidate.json, knowledge_graph_candidate.json,
      dense_embeddings_candidate.npy (+ meta), windows_emb.npy, windows_meta.json
  * sparse_builder_fidelity.json    fidelidad del constructor TF-IDF reconstruido frente al indice original
  * build_report.json               estadisticas, validaciones y hashes

Reglas (deterministas, genericas; ninguna depende de una pregunta, un pasaje o un articulo concretos):
  1. Un APARTADO empieza en cada segmento ARTICLE de article_units_v1 y absorbe los segmentos CONTINUATION
     consecutivos con el mismo rotulo, aunque esten en paginas posteriores (apartados multipagina).
  2. Jerarquia por numeracion del rotulo (6.3.4 -> 6.3 -> 6); el padre es el apartado existente mas cercano.
  3. TABLAS: bloque de >= 3 lineas-fila (>= 2 numeros, densidad numerica >= 0,15, sin cierre de frase) con
     lineas-etiqueta cortas intercaladas; el titulo son las lineas-etiqueta inmediatamente anteriores (max. 3).
     La tabla se separa del texto del apartado, se guarda como unidad propia vinculada a su apartado
     (has_table / table_of) y a los apartados que la citan por su titulo ("see table: X", "refer to table N: X")
     (references_table); si el titulo se repite, solo se enlaza la tabla mas cercana en el documento.
  4. Texto = concatenacion literal de cortes de la pagina (spans verificables byte a byte); sin cabeceras.
Uso: python experiments/segmentacion_apartados_2026/build_sections.py
"""
import hashlib, json, math, os, re, sys, time
from collections import Counter, defaultdict
os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                   "GEMINI_API_KEY": "", "GOOGLE_API_KEY": "", "GROQ_API_KEY": ""})
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(HERE, "index")
D = os.path.join(ROOT, "data", "processed", "rebuild_2026_08_corrected")
AU = os.path.join(ROOT, "data", "derived", "article_units_v1")
PDF = os.path.join(ROOT, "data", "raw", "sor_2026_08_rebuild", "IJF_Sport_and_Organisation_Rules_2026_08_14.pdf")
PROTECTED = [os.path.join(D, f) for f in ("passages_candidate.json", "dense_embeddings_candidate.npy", "vector_index_candidate.json",
                                         "knowledge_graph_candidate.json", "dense_embeddings_meta.json")] + \
            [os.path.join(AU, "units.jsonl"), PDF]
SOURCE_SHA = "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620"
WIN, OVL, MAX_TOTAL = 220, 30, 254
NUM = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:[.,]\s?\d+)?")
TABLE_REF = re.compile(r"(?i)(?:see|refer to)\s+table\s*([0-9][0-9 .]*)?\s*:\s*([^)\n]+)")


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def norm_label(s):
    return re.sub(r"\s+", "", str(s or "")).rstrip(".").lower()


def norm_title(s):
    s = re.sub(r"^\s*(?:Article\s+)?[A-H]?\d+(?:\s?\.\s?\d+)*\s?\.?\s*", "", str(s or ""))
    return re.sub(r"\s+", " ", s).strip().lower()


def label_parents(label):
    parts = norm_label(label).split(".")
    return [".".join(parts[:i]) for i in range(len(parts) - 1, 0, -1)]


# ------------------------------------------------------------------ tablas
def lines_with_offsets(text, base):
    out, pos = [], 0
    for ln in text.split("\n"):
        out.append((base + pos, base + pos + len(ln), ln))
        pos += len(ln) + 1
    return out


def is_row(ln):
    """Linea-fila: >= 2 numeros, densidad numerica >= 0,15 por palabra y sin cierre de frase (las frases con cifras no son filas)."""
    s = ln.strip()
    w = s.split()
    n = len(NUM.findall(s))
    return n >= 2 and 0 < len(w) <= 30 and n / len(w) >= 0.15 and not s.endswith((".", ";", ":"))


def is_label(ln):
    s = ln.strip()
    return bool(s) and len(s.split()) <= 14 and not s.endswith((".", ";", ":", ",")) and not is_row(ln)


def find_tables(text, base):
    """Devuelve [(start, end, caption)] en coordenadas de pagina para el corte text=page[base:base+len]."""
    L = lines_with_offsets(text, base)
    tables, i = [], 0
    while i < len(L):
        if not is_row(L[i][2]):
            i += 1
            continue
        j, rows = i, 0
        while j < len(L):
            ln = L[j][2]
            if is_row(ln):
                rows += 1
                j += 1
            elif is_label(ln) and any(is_row(L[k][2]) for k in range(j + 1, min(len(L), j + 3))):
                j += 1
            else:
                break
        if rows >= 3:
            s = i
            while s > 0 and i - s < 3 and is_label(L[s - 1][2]):
                s -= 1
            caption = L[s][2].strip() if s < i else ""
            tables.append((L[s][0], L[j - 1][1], caption))
            i = j
        else:
            i += 1
    return tables


# ------------------------------------------------------------------ TF-IDF (reconstruccion del constructor original)
def strip_acc(s):
    return s.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")


def infer_stoplist(passages, idx):
    raw = Counter(t for p in passages for t in set(re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b",
                  strip_acc(((p.get("heading_path") or [""])[0]) + " " + p["text_original"]))))
    return sorted(t for t in raw if t not in idx["idf"])


def tfidf_build(docs, stop):
    toks = {}
    for pid, text in docs.items():
        out = []
        for t in re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", strip_acc(text)):
            if t in stop:
                continue
            out.append(t)
            if "-" in t:
                out += [x for x in t.split("-") if len(x) >= 2 and x not in stop]
        toks[pid] = out
    N = len(toks)
    df = Counter(t for d in toks.values() for t in set(d))
    idf = {t: math.log((1 + N) / (1 + n)) + 1 for t, n in df.items()}
    vecs = {}
    for pid, d in toks.items():
        if not d:
            vecs[pid] = {}
            continue
        c = Counter(d)
        v = {t: (n / len(d)) * idf[t] for t, n in c.items()}
        nr = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs[pid] = {t: x / nr for t, x in v.items()}
    return {"version": "exp-sections-2026-11", "source_sha256": SOURCE_SHA, "num_docs": N, "idf": idf, "vectors": vecs}


def main():
    t0 = time.perf_counter()
    hashes_before = {os.path.relpath(p, ROOT): sha_file(p) for p in PROTECTED}
    passages = json.load(open(os.path.join(D, "passages_candidate.json"), encoding="utf-8"))
    au_hashes = json.load(open(os.path.join(AU, "hashes.json"), encoding="utf-8"))
    assert au_hashes["input_corpus_file_sha256"] == hashes_before[os.path.join("data", "processed", "rebuild_2026_08_corrected", "passages_candidate.json")]
    assert au_hashes["artifacts_sha256"]["units.jsonl"] == hashes_before[os.path.join("data", "derived", "article_units_v1", "units.jsonl")]
    units = [json.loads(l) for l in open(os.path.join(AU, "units.jsonl"), encoding="utf-8")]
    page_text, page_pass = {}, defaultdict(list)
    for p in passages:
        page_text.setdefault(p["pdf_page_index"], p["text_original"])
        page_pass[p["pdf_page_index"]].append(p)
    src_meta = {k: passages[0][k] for k in ("source_id", "source_title", "source_version", "source_url", "source_sha256", "language_original")}

    # ---------------- auditoria
    import fitz
    pdf = fitz.open(PDF)
    toc = pdf.get_toc()
    au_err = Counter((e["severity"], e["code"]) for e in (json.loads(l) for l in open(os.path.join(AU, "errors.jsonl"), encoding="utf-8")))
    meta_heading_mismatch = []
    for p in passages:
        lab = norm_label(p.get("article_id"))
        head = (p.get("heading_path") or [""])[0]
        if lab and lab not in ("general",) and not norm_label(head).startswith(lab.replace(" ", "")) and lab not in norm_label(head):
            meta_heading_mismatch.append(p["passage_id"])
    lvl1 = sorted([u for u in units if u["unit_level"] == 1], key=lambda u: (u["page"], u["char_start"]))
    audit = {
        "pdf": {"paginas": pdf.page_count, "entradas_toc": len(toc), "sha256": hashes_before[os.path.relpath(PDF, ROOT)]},
        "corpus": {"pasajes": len(passages), "paginas_con_texto": len(page_text),
                   "paginas_pdf_sin_pasaje": sorted(set(range(1, pdf.page_count + 1)) - set(page_text)),
                   "pasajes_por_pagina": dict(sorted(Counter(Counter(p["pdf_page_index"] for p in passages).values()).items())),
                   "pasajes_que_comparten_texto_de_pagina": sum(1 for p in passages if len(page_pass[p["pdf_page_index"]]) > 1),
                   "review_status": dict(Counter(p.get("review_status") for p in passages)),
                   "approved_by_no_nulo": sum(1 for p in passages if p.get("approved_by")),
                   "article_id_vs_heading_incoherente": len(meta_heading_mismatch),
                   "unidad_real_del_pasaje": "pagina completa (text_original = texto de la pagina; los pasajes de una pagina solo difieren en metadatos)"},
        "article_units_v1": {"unidades": len(units), "nivel1_por_tipo": dict(Counter(u["unit_type"] for u in lvl1)),
                             "relacion_continuacion": dict(Counter(u["passage_relation"] for u in lvl1 if u["unit_type"] == "CONTINUATION")),
                             "avisos_fase8": {f"{k[0]}:{k[1]}": v for k, v in au_err.items()}},
    }

    # ---------------- apartados
    sections, open_sec = [], None
    for u in lvl1:
        t = u["unit_type"]
        if t in ("PAGE_HEADER", "EMPTY_PAGE"):
            continue
        lab = norm_label(u.get("article_label"))
        piece = {"page": u["page"], "char_start": u["char_start"], "char_end": u["char_end"], "au_unit": u["unit_id"],
                 "au_passages": u["original_passage_ids"], "au_relation": u["passage_relation"]}
        if t == "CONTINUATION" and open_sec is not None and lab and lab == open_sec["label"]:
            open_sec["pieces"].append(piece)
            continue
        if t == "ARTICLE" and open_sec is not None and lab and lab == open_sec["label"] and \
                open_sec["pieces"][-1]["page"] in (u["page"], u["page"] - 1):
            open_sec["pieces"].append(piece)          # rotulo repetido en la pagina siguiente: mismo apartado
            continue
        kind = {"ARTICLE": "APARTADO", "CONTINUATION": "CONTINUACION_SIN_INICIO", "COVER": "PORTADA"}.get(t, t)
        open_sec = {"label": lab, "label_display": (u.get("article_label") or "").strip(), "heading": u.get("heading") or u.get("article_label") or "",
                    "kind": kind, "pieces": [piece]}
        sections.append(open_sec)

    # ---------------- tablas y texto
    out_units, tables = [], []
    for n, s in enumerate(sections, 1):
        s["unit_id"] = f"SEC-{n:04d}"
        text_parts, spans = [], []
        for pc in s["pieces"]:
            pt = page_text[pc["page"]]
            seg = pt[pc["char_start"]:pc["char_end"]]
            cur = pc["char_start"]
            for (ts, te, cap) in find_tables(seg, pc["char_start"]):
                tables.append({"section": s, "page": pc["page"], "char_start": ts, "char_end": te, "caption": cap})
                if ts > cur:
                    spans.append((pc["page"], cur, ts))
                cur = te
            if pc["char_end"] > cur:
                spans.append((pc["page"], cur, pc["char_end"]))
        for (pg, a, b) in spans:
            frag = page_text[pg][a:b].strip("\n")
            if frag.strip():
                text_parts.append(frag)
        s["spans"] = [(pg, a, b) for (pg, a, b) in spans]
        s["text"] = "\n".join(text_parts)
    # resolucion de referencias a tablas por titulo
    for k, t in enumerate(tables, 1):
        t["unit_id"] = f"TAB-{k:04d}"
    cap_index = defaultdict(list)
    for t in tables:
        if t["caption"]:
            cap_index[re.sub(r"\s+", " ", t["caption"]).strip().lower()].append(t)
    refs = []
    for s in sections:
        for m in TABLE_REF.finditer(s["text"]):
            title = re.sub(r"\s+", " ", m.group(2)).strip().lower()
            cands = [t for c, ts in cap_index.items() if title and (c == title or (len(title) >= 25 and c.startswith(title))) for t in ts]
            # titulo repetido (p. ej. copias en el historial de versiones): se enlaza solo la tabla mas cercana en el documento
            p_ref = s["pieces"][0]["page"]
            dmin = min((abs(t["page"] - p_ref) for t in cands), default=None)
            hits = [t for t in cands if abs(t["page"] - p_ref) == dmin]
            refs.append({"from": s["unit_id"], "ref": m.group(0)[:120], "resolved": [t["unit_id"] for t in hits]})
            for t in hits:
                t.setdefault("referenced_by", set()).add(s["unit_id"])

    # ---------------- jerarquia y trazabilidad
    by_label = {}
    for s in sections:
        if s["kind"] == "APARTADO" and s["label"] and s["label"] not in by_label:
            by_label[s["label"]] = s["unit_id"]
    label_dups = [l for l, c in Counter(s["label"] for s in sections if s["kind"] == "APARTADO").items() if c > 1]
    pass_to_units = defaultdict(set)
    fallback_pass = defaultdict(set)
    for s in sections:
        pages = sorted({pc["page"] for pc in s["pieces"]})
        s["pages"] = pages
        s["parent_label"] = next((pl for pl in label_parents(s["label"]) if pl in by_label), None)
        s["parent_unit_id"] = by_label.get(s["parent_label"]) if s["parent_label"] else None
        precise = [p["passage_id"] for pg in pages for p in page_pass.get(pg, []) if norm_label(p.get("article_id")) == s["label"]]
        s["original_passage_ids"] = precise
        s["page_passage_ids"] = [p["passage_id"] for pg in pages for p in page_pass.get(pg, [])]
        for pid in precise:
            pass_to_units[pid].add(s["unit_id"])
        for pid in s["page_passage_ids"]:
            fallback_pass[pid].add(s["unit_id"])
    unmapped_precise = [p["passage_id"] for p in passages if not pass_to_units.get(p["passage_id"])]

    def heading_of(s):
        h = re.sub(r"\s+", " ", re.sub(r"(\d)\s+\.\s*(?=\d)", r"\1.", s["heading"])).strip()
        return h or s["label_display"]

    def mk(uid, kind, heading, text, spans, pages, **kw):
        return {"passage_id": uid, **src_meta, "pdf_page_index": pages[0], "page_end": pages[-1],
                "printed_page_label": f"page - {pages[0]}" + (f" a {pages[-1]}" if pages[-1] != pages[0] else ""),
                "article_id": kw.pop("article_id"), "section_id": uid, "heading_path": [heading],
                "text_original": text, "text_sha256": sha(text), "unit_type": kind,
                "source_spans": [{"page": pg, "char_start": a, "char_end": b} for (pg, a, b) in spans],
                "review_status": "experimental", "normative_status": "DERIVADA_EXPERIMENTAL_NO_NORMATIVA",
                "extraction_method": "segmentacion_apartados_exp_v1 sobre article_units_v1", "approved_by": None, **kw}

    for s in sections:
        out_units.append(mk(s["unit_id"], s["kind"], heading_of(s), s["text"], s["spans"], s["pages"],
                            article_id=s["label_display"] or s["label"], label=s["label"],
                            parent_label=s["parent_label"], parent_unit_id=s["parent_unit_id"],
                            original_passage_ids=s["original_passage_ids"], page_passage_ids=s["page_passage_ids"],
                            article_unit_ids=[pc["au_unit"] for pc in s["pieces"]],
                            table_unit_ids=[t["unit_id"] for t in tables if t["section"] is s]))
    for t in tables:
        s = t["section"]
        text = page_text[t["page"]][t["char_start"]:t["char_end"]]
        cap = t["caption"] or "(sin titulo)"
        out_units.append(mk(t["unit_id"], "TABLA", f"Table: {cap} [{heading_of(s)}]", text, [(t["page"], t["char_start"], t["char_end"])],
                            [t["page"]], article_id=s["label_display"] or s["label"], label=s["label"], caption=t["caption"],
                            parent_label=s["label"], parent_unit_id=s["unit_id"],
                            original_passage_ids=[p for p in s["original_passage_ids"] if p in {x["passage_id"] for x in page_pass[t["page"]]}],
                            page_passage_ids=[x["passage_id"] for x in page_pass[t["page"]]],
                            referenced_by=sorted(t.get("referenced_by", set()))))

    # ---------------- validaciones
    by_uid = {u["passage_id"]: u for u in out_units}
    span_ok = all(page_text[sp["page"]][sp["char_start"]:sp["char_end"]] in page_text[sp["page"]] for u in out_units for sp in u["source_spans"])
    covered = defaultdict(list)
    for u in out_units:
        for sp in u["source_spans"]:
            covered[sp["page"]].append((sp["char_start"], sp["char_end"]))
    overlap = 0
    for pg, iv in covered.items():
        iv.sort()
        overlap += sum(1 for a, b in zip(iv, iv[1:]) if b[0] < a[1])
    au_body = sum(u["char_end"] - u["char_start"] for u in lvl1 if u["unit_type"] not in ("PAGE_HEADER", "EMPTY_PAGE"))
    cov = sum(b - a for iv in covered.values() for a, b in iv)
    toc_titles = {}
    for lvl, title, pg in toc:
        m = re.match(r"^\s*((?:Article\s+)?[A-H]?\d+(?:\s?\.\s?\d+)*)\.?\s+(.*)$", title)
        if m:
            toc_titles[norm_label(m.group(1).replace("Article", ""))] = (pg, title)
    sec_ap = [u for u in out_units if u["unit_type"] == "APARTADO"]
    toc_match = [u for u in sec_ap if norm_label(str(u["label"]).replace("article", "")) in toc_titles]
    toc_page_ok = [u for u in toc_match if toc_titles[norm_label(str(u["label"]).replace("article", ""))][0] == u["pdf_page_index"]]
    toc_missing = sorted(set(toc_titles) - {norm_label(str(u["label"]).replace("article", "")) for u in sec_ap})
    validation = {
        "spans_literales_verificados": span_ok, "solapes_entre_unidades": overlap,
        "cobertura_caracteres_cuerpo_vs_article_units": round(cov / au_body, 4),
        "pasajes_originales_con_unidad_precisa": len(passages) - len(unmapped_precise),
        "pasajes_sin_unidad_precisa(solo por pagina)": len(unmapped_precise),
        "todos_los_pasajes_trazables_por_pagina": all(fallback_pass.get(p["passage_id"]) for p in passages),
        "rotulos_de_apartado_duplicados": label_dups,
        "apartados_en_toc_pdf": f"{len(toc_match)}/{len(sec_ap)}", "apartados_con_pagina_inicial_igual_toc": len(toc_page_ok),
        "entradas_toc_numeradas_sin_apartado": toc_missing[:40], "n_entradas_toc_numeradas_sin_apartado": len(toc_missing),
        "referencias_a_tabla": len(refs), "referencias_resueltas": sum(1 for r in refs if r["resolved"]),
        "referencias_no_resueltas": [r for r in refs if not r["resolved"]][:15],
    }

    # ---------------- indice experimental
    os.makedirs(IDX, exist_ok=True)
    with open(os.path.join(HERE, "units.jsonl"), "w", encoding="utf-8") as f:
        for u in out_units:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")
    json.dump(out_units, open(os.path.join(IDX, "passages_candidate.json"), "w", encoding="utf-8"), ensure_ascii=False)
    idx0 = json.load(open(os.path.join(D, "vector_index_candidate.json"), encoding="utf-8"))
    stop = set(infer_stoplist(passages, idx0))
    # fidelidad del constructor sobre el corpus original
    rebuilt = tfidf_build({p["passage_id"]: ((p.get("heading_path") or [""])[0]) + " " + p["text_original"] for p in passages}, stop)
    errs = [max([abs(rebuilt["vectors"][pid].get(t, 0) - v.get(t, 0)) for t in set(v) | set(rebuilt["vectors"][pid])] or [0])
            for pid, v in idx0["vectors"].items()]
    top_overlap = []
    for pid, v in idx0["vectors"].items():
        a = [t for t, _ in sorted(v.items(), key=lambda x: -x[1])[:10]]
        b = [t for t, _ in sorted(rebuilt["vectors"][pid].items(), key=lambda x: -x[1])[:10]]
        top_overlap.append(len(set(a) & set(b)) / 10)
    fidelity = {"stoplist_inferida": sorted(stop), "idf_rel_err_mediana": float(np.median([abs(rebuilt["idf"].get(t, 0) - w) / w for t, w in idx0["idf"].items()])),
                "vector_max_err_mediana": float(np.median(errs)), "vector_max_err_p95": float(np.percentile(errs, 95)),
                "solape_top10_terminos_medio": round(float(np.mean(top_overlap)), 3), "vocab_jaccard": round(len(set(rebuilt["idf"]) & set(idx0["idf"])) / len(set(rebuilt["idf"]) | set(idx0["idf"])), 4)}
    json.dump(rebuilt, open(os.path.join(HERE, "control_sparse_index_original_passages.json"), "w", encoding="utf-8"))
    json.dump(fidelity, open(os.path.join(HERE, "sparse_builder_fidelity.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sec_sparse = tfidf_build({u["passage_id"]: u["heading_path"][0] + " " + u["text_original"] for u in out_units}, stop)
    json.dump(sec_sparse, open(os.path.join(IDX, "vector_index_candidate.json"), "w", encoding="utf-8"))

    g0 = json.load(open(os.path.join(D, "knowledge_graph_candidate.json"), encoding="utf-8"))
    edges, seen = [], set()

    def add(s_, t_, rel, prov):
        if s_ != t_ and (s_, t_, rel) not in seen:
            seen.add((s_, t_, rel))
            edges.append({"source": s_, "target": t_, "relation_type": rel, "provenance": prov})
    for e in g0["edges"]:
        S = pass_to_units.get(e["source"]) or fallback_pass.get(e["source"], set())
        T = pass_to_units.get(e["target"]) or fallback_pass.get(e["target"], set())
        for s_ in sorted(S):
            for t_ in sorted(T):
                if by_uid[s_]["unit_type"] != "TABLA" and by_uid[t_]["unit_type"] != "TABLA":
                    add(s_, t_, e.get("relation_type", "references_article"), f"mapeo de {e['source']}->{e['target']}")
    for t in tables:
        add(t["section"]["unit_id"], t["unit_id"], "has_table", "tabla contenida en el apartado")
        add(t["unit_id"], t["section"]["unit_id"], "table_of", "apartado que contiene la tabla")
        for r in sorted(t.get("referenced_by", [])):
            add(r, t["unit_id"], "references_table", "cita por titulo de tabla")
    json.dump({"version": "exp-sections-2026-11", "source_id": src_meta["source_id"],
               "nodes": [{"id": u["passage_id"], "type": u["unit_type"]} for u in out_units], "edges": edges},
              open(os.path.join(IDX, "knowledge_graph_candidate.json"), "w", encoding="utf-8"), ensure_ascii=False)

    import glob
    from sentence_transformers import SentenceTransformer
    snap = sorted(glob.glob(os.path.expanduser("~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/*")), reverse=True)[0]
    model = SentenceTransformer(snap, local_files_only=True)
    tok = model.tokenizer
    texts = [u["heading_path"][0] + " " + u["text_original"] for u in out_units]
    t_enc = time.perf_counter()
    emb = model.encode(texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True).astype(np.float32)
    np.save(os.path.join(IDX, "dense_embeddings_candidate.npy"), emb)
    json.dump({"version": "exp-sections-2026-11", "source_sha256": SOURCE_SHA, "model_name": "sentence-transformers/all-MiniLM-L6-v2",
               "dimension": 384, "num_passages": len(out_units), "passage_ids": [u["passage_id"] for u in out_units],
               "texto_embebido": "heading_path[0] + ' ' + text_original (truncado por el modelo a 256 tokens)"},
              open(os.path.join(IDX, "dense_embeddings_meta.json"), "w", encoding="utf-8"), ensure_ascii=False)
    ntok = [len(tok(t, add_special_tokens=True)["input_ids"]) for t in texts]
    # ventanas (variante S_W): mismas reglas que experiments/ventanas_2026
    win_texts, win_meta = [], []
    for u in out_units:
        title, body = u["heading_path"][0], u["text_original"]
        enc = tok(body, add_special_tokens=False, return_offsets_mapping=True)
        ids, offs = enc["input_ids"], enc["offset_mapping"]
        t_ids = tok(title, add_special_tokens=False)["input_ids"]
        if len(t_ids) > MAX_TOTAL - 2 - WIN:
            title = tok.decode(t_ids[:MAX_TOTAL - 2 - WIN])
        starts = list(range(0, max(1, len(ids) - OVL), WIN - OVL)) if ids else [0]
        for s0 in starts:
            e0 = min(len(ids), s0 + WIN)
            chunk = body[offs[s0][0]:offs[e0 - 1][1]] if ids else ""
            text = f"{title} {chunk}".strip()
            while len(tok(text, add_special_tokens=True)["input_ids"]) > MAX_TOTAL and e0 > s0 + 1:
                e0 -= 1
                chunk = body[offs[s0][0]:offs[e0 - 1][1]]
                text = f"{title} {chunk}".strip()
            win_texts.append(text)
            win_meta.append({"passage_id": u["passage_id"], "token_inicio": s0, "token_fin": e0})
            if e0 >= len(ids):
                break
    W = model.encode(win_texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True).astype(np.float32)
    np.save(os.path.join(IDX, "windows_emb.npy"), W)
    json.dump({"win": WIN, "overlap": OVL, "max_total": MAX_TOTAL, "passage_ids_orden": [u["passage_id"] for u in out_units],
               "windows": win_meta}, open(os.path.join(IDX, "windows_meta.json"), "w", encoding="utf-8"))
    t1 = time.perf_counter()

    kinds = Counter(u["unit_type"] for u in out_units)
    multi = [u for u in out_units if u["page_end"] != u["pdf_page_index"]]
    hashes_after = {os.path.relpath(p, ROOT): sha_file(p) for p in PROTECTED}
    report = {
        "unidades": len(out_units), "por_tipo": dict(kinds), "apartados_multipagina": len(multi),
        "max_paginas_por_apartado": max(u["page_end"] - u["pdf_page_index"] + 1 for u in out_units),
        "tablas": len(tables), "tablas_con_titulo": sum(1 for t in tables if t["caption"]),
        "tokens_por_unidad": {"mediana": float(np.median(ntok)), "p90": float(np.percentile(ntok, 90)), "max": int(max(ntok)),
                              "superan_256": sum(1 for n in ntok if n > 256), "pct_superan_256": round(100 * sum(1 for n in ntok if n > 256) / len(ntok), 1)},
        "ventanas": len(win_meta), "aristas_grafo": dict(Counter(e["relation_type"] for e in edges)),
        "validacion": validation, "fidelidad_tfidf": fidelity,
        "tiempo_s": {"segmentacion_e_indices": round(t_enc - t0, 1), "embeddings": round(t1 - t_enc, 1)},
        "memoria_MB": {"denso": round(emb.nbytes / 2**20, 2), "ventanas": round(W.nbytes / 2**20, 2)},
        "integridad": {"sha256_antes": hashes_before, "sha256_despues": hashes_after, "identicos": hashes_before == hashes_after},
    }
    json.dump(audit, open(os.path.join(HERE, "audit.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(report, open(os.path.join(HERE, "build_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"audit": audit, **{k: v for k, v in report.items() if k != "integridad"},
                      "integridad_identicos": report["integridad"]["identicos"]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

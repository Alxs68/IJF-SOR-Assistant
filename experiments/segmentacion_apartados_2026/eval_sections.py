"""Evaluacion de recuperacion: apartados normativos frente a paginas (DEV, sin LLM, sin red).

Configuraciones (mismo ReasoningRetrievalEngine sin modificar; solo cambia base_dir o, en memoria, un canal):
  A     paginas, indices originales, R1 desactivado
  B     paginas, indices originales, R1 (RRE_CHANNEL_CHAMPIONS=1)                    <- referencia
  Bc    control: paginas + TF-IDF reconstruido con el mismo constructor que los apartados (en memoria), R1
  S0    apartados (index/), denso truncado, R1 desactivado
  S     apartados (index/), denso truncado, R1
  SW    apartados + denso por ventanas (maximo, 220/30) sustituido en memoria, R1
Criterio de acierto COMUN a todas: una unidad entregada satisface un ancla si su texto contiene el fragmento literal
del ancla (normalizado: espacios y apostrofos) y cubre la pagina del ancla. Se informa tambien el criterio por IDs
(expand) para A/B/Bc, que es el de los informes anteriores.
Uso (desde la raiz del repo): python experiments/segmentacion_apartados_2026/eval_sections.py -> eval_results.json
"""
import hashlib, json, os, re, sys, time
os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                   "GEMINI_API_KEY": "", "GOOGLE_API_KEY": "", "GROQ_API_KEY": ""})
for v in ("RRE_CHANNEL_CHAMPIONS", "RRE_ENABLE_SCOPE_PREFERENCE"):
    os.environ.pop(v, None)
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(HERE, "index")
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
os.chdir(ROOT)
D = os.path.join(ROOT, "data", "processed", "rebuild_2026_08_corrected")
PROTECTED = [os.path.join(D, f) for f in ("passages_candidate.json", "dense_embeddings_candidate.npy", "vector_index_candidate.json",
                                         "knowledge_graph_candidate.json", "dense_embeddings_meta.json")]
# Fragmentos SOLO para diagnosticar SCO-020 (no intervienen en la recuperacion)
SCO020_PROBES = {
    "6.1 sin tolerancia (oficial individual)": "there is no additional weight tolerance",
    "6.3 aleatorio <= 5 %": "cannot be more than 5 % higher than the official maximum weight limit",
    "tabla 6.3.4 (fila -48 kg aleatorio)": "Up to and including 48.0 kg  Up to and including 50.4 kg",
    "6.4.2 mixto +5 % (distractor)": "A +5% tolerance applies only to the minus weight categories",
}


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def norm(s):
    return " ".join(str(s).replace("’", "'").replace(" ", " ").split())


def window_dense(rre, W, win_pid_idx, STOPWORDS):
    pids = rre.dense_meta["passage_ids"]
    n = len(pids)

    def agg(q):
        out = np.full(n, -np.inf, dtype=np.float32)
        np.maximum.at(out, win_pid_idx, W @ q)
        return out

    def _dense_search(query, top_k=20):
        sims = agg(rre.dense_model.encode(query, normalize_embeddings=True))
        clean = query.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        eng = " ".join(rre.SPANISH_TO_ENGLISH_SYNONYMS.get(t, t) for t in re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", clean) if t not in STOPWORDS)
        if eng and eng != query:
            sims = np.maximum(sims, agg(rre.dense_model.encode(eng, normalize_embeddings=True)))
        top = np.argsort(sims)[::-1][:top_k]
        return [(pids[i], float(sims[i])) for i in top if float(sims[i]) > 0.15]
    return _dense_search


def main():
    hashes_before = {os.path.relpath(p, ROOT): sha_file(p) for p in PROTECTED}
    from experimental.benchmark_access import expand
    import rre_engine
    from rre_engine import ReasoningRetrievalEngine
    hardcoded = set(re.findall(r"SOR-2026-08-P\d{3}-S\d{3}", open(os.path.join(ROOT, "src", "rre_engine.py"), encoding="utf-8").read()))

    items = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(ROOT, "data", "eval", "benchmark_v2", "splits", "dev.jsonl"),
                                                              encoding="utf-8") if l.strip()}
    queries = json.load(open(os.path.join(ROOT, "data", "eval", "fase11", "retrieval_experiments_dev.json"), encoding="utf-8"))["per_query"]
    orig_pages = {}
    for p in json.load(open(os.path.join(D, "passages_candidate.json"), encoding="utf-8")):
        orig_pages.setdefault(p["pdf_page_index"], p["text_original"])
    anchor_found = [(it["id"], a["page"]) for it in items.values() for a in (it.get("minimum_evidence") or [])
                    if norm(a["snippet"]) not in norm(orig_pages.get(a["page"], ""))]

    t0 = time.perf_counter()
    rre_p = ReasoningRetrievalEngine(enable_ood_detector=True)
    t_p = time.perf_counter() - t0
    t0 = time.perf_counter()
    rre_s = ReasoningRetrievalEngine(base_dir=IDX, enable_ood_detector=True)
    t_s = time.perf_counter() - t0
    assert rre_s.operating_mode == "HYBRID", rre_s.degradation_reason
    units = rre_s.passages_by_id
    orig_sparse = rre_p.sparse_index
    ctrl_sparse = json.load(open(os.path.join(HERE, "control_sparse_index_original_passages.json"), encoding="utf-8"))
    s_dense = rre_s._dense_search
    wm = json.load(open(os.path.join(IDX, "windows_meta.json"), encoding="utf-8"))
    pos = {pid: i for i, pid in enumerate(rre_s.dense_meta["passage_ids"])}
    sw_dense = window_dense(rre_s, np.load(os.path.join(IDX, "windows_emb.npy")),
                            np.array([pos[w["passage_id"]] for w in wm["windows"]]), rre_engine.STOPWORDS)

    def pages_of(rec, eng):
        if eng is rre_s:
            u = units[rec["passage_id"]]
            return set(range(u["pdf_page_index"], u["page_end"] + 1))
        pg = {rec.get("page")} | {s.get("page") for s in rec.get("source_spans", []) if isinstance(s, dict)}
        return {p for p in pg if p is not None}

    def sat(rec, eng, anchor):
        return anchor["page"] in pages_of(rec, eng) and norm(anchor["snippet"]) in norm(rec.get("text_original", ""))

    CONFIGS = {"A": (rre_p, "0", None, None), "B": (rre_p, "1", None, None), "Bc": (rre_p, "1", ctrl_sparse, None),
               "S0": (rre_s, "0", None, None), "S": (rre_s, "1", None, None), "SW": (rre_s, "1", None, sw_dense)}
    rows, timing = [], {k: [] for k in CONFIGS}
    for q in queries:
        it = items[q["id"]]
        anchors = it.get("minimum_evidence") or []
        first_ids = expand(anchors[0]["passage_ids"]) if anchors else set()
        row = {"id": q["id"], "form": q["form"], "expected": q["expected_behavior"]}
        for name, (eng, flag, sparse, dense) in CONFIGS.items():
            os.environ["RRE_CHANNEL_CHAMPIONS"] = flag
            if eng is rre_p:
                rre_p.sparse_index = sparse or orig_sparse
            rre_s._dense_search = dense or s_dense
            out = {}
            for k in (5, 10):
                t = time.perf_counter()
                r = eng.retrieve(q["query_used"], top_k=k, domain_query=it["text"])
                timing[name].append(time.perf_counter() - t)
                ev = r.get("evidence", [])
                p_txt = next((i for i, e in enumerate(ev, 1) if sat(e, eng, anchors[0])), None) if anchors else None
                p_ids = next((i for i, e in enumerate(ev, 1) if e["passage_id"] in first_ids), None) if (anchors and eng is rre_p) else None
                out[k] = (r, ev, p_txt, p_ids)
            r5, ev5, _, _ = out[5]
            bundle = ev5 + r5.get("related_passages", [])
            row[name] = {"status": r5.get("status"), "reason": r5.get("reason"),
                         "top5": [e["passage_id"] for e in ev5], "top10": [e["passage_id"] for e in out[10][1]],
                         "related": [e["passage_id"] for e in r5.get("related_passages", [])],
                         "pos_k5": out[5][2], "pos_k10": out[10][2], "pos_k10_ids": out[10][3], "pos_k5_ids": out[5][3],
                         "bundle_hit": all(any(sat(e, eng, a) for e in bundle) for a in anchors) if anchors else None,
                         "bundle_hit_ids": (all(expand(a["passage_ids"]) & {e["passage_id"] for e in bundle} for a in anchors)
                                            if anchors and eng is rre_p else None),
                         "nonempty_top5": bool(ev5), "bundle_chars": sum(len(e.get("text_original", "")) for e in bundle),
                         "hardcoded_in_top5": sorted(hardcoded & {e["passage_id"] for e in ev5}) if eng is rre_p else []}
            if q["id"].endswith("SCO-020"):
                row[name]["sco020"] = {lab: [i for i, e in enumerate(bundle, 1) if norm(sn) in norm(e.get("text_original", ""))]
                                       for lab, sn in SCO020_PROBES.items()}
                row[name]["sco020_bundle"] = [(e["passage_id"], (units.get(e["passage_id"]) or rre_p.passages_by_id.get(e["passage_id"], {})).get("heading_path", [""])[0][:80])
                                              for e in bundle]
        rows.append(row)
    os.environ.pop("RRE_CHANNEL_CHAMPIONS", None)
    rre_p.sparse_index = orig_sparse
    rre_s._dense_search = s_dense

    ans = [r for r in rows if r["expected"] == "RESPONDER"]
    no_resp = [r for r in rows if r["expected"] != "RESPONDER"]
    tag = lambda r: f"{r['id']}/{r['form']}"

    def metrics(k, form=None, ids=False):
        R = [r[k] for r in ans if form is None or r["form"] == form]
        p5, p10, bh = ("pos_k5_ids", "pos_k10_ids", "bundle_hit_ids") if ids else ("pos_k5", "pos_k10", "bundle_hit")
        n = len(R)
        return {"n": n, "R@5": round(sum(1 for x in R if x[p5]) / n, 3), "R@10": round(sum(1 for x in R if x[p10]) / n, 3),
                "MRR@10": round(sum(1 / x[p10] for x in R if x[p10]) / n, 3), "paquete": round(sum(1 for x in R if x[bh]) / n, 3),
                "chars_paquete_medio": int(np.mean([x["bundle_chars"] for x in R]))}

    summary = {f: {k: metrics(k, None if f == "TOTAL" else f) for k in CONFIGS} for f in ("DICT", "LLM", "TOTAL")}
    summary_ids = {k: metrics(k, None, ids=True) for k in ("A", "B", "Bc")}

    def diff(a, b):
        return {"ganadas_paquete": sorted(tag(r) for r in ans if r[b]["bundle_hit"] and not r[a]["bundle_hit"]),
                "perdidas_paquete": sorted(tag(r) for r in ans if r[a]["bundle_hit"] and not r[b]["bundle_hit"]),
                "ganadas_R@5": sorted(tag(r) for r in ans if r[b]["pos_k5"] and not r[a]["pos_k5"]),
                "perdidas_R@5": sorted(tag(r) for r in ans if r[a]["pos_k5"] and not r[b]["pos_k5"]),
                "regresiones_pos_k10": sorted(f"{tag(r)}:{r[a]['pos_k10']}->{r[b]['pos_k10']}" for r in ans
                                              if r[a]["pos_k10"] and (not r[b]["pos_k10"] or r[b]["pos_k10"] > r[a]["pos_k10"])),
                "mejoras_pos_k10": sorted(f"{tag(r)}:{r[a]['pos_k10']}->{r[b]['pos_k10']}" for r in ans
                                          if r[b]["pos_k10"] and (not r[a]["pos_k10"] or r[b]["pos_k10"] < r[a]["pos_k10"])),
                "perdidas_con_regla_fija_en_B": sorted(tag(r) for r in ans if r[a]["bundle_hit"] and not r[b]["bundle_hit"] and r["B"]["hardcoded_in_top5"])}
    comps = {f"{b}_vs_{a}": diff(a, b) for a, b in (("B", "Bc"), ("B", "S"), ("B", "SW"), ("B", "S0"), ("Bc", "S"), ("Bc", "SW"), ("S", "SW"))}
    nonans = {k: {"top5_no_vacio": sum(1 for r in no_resp if r[k]["nonempty_top5"]),
                  "cambios_estado_vs_B": sorted(f"{tag(r)}:{r['B']['status']}->{r[k]['status']}" for r in no_resp if r[k]["status"] != r["B"]["status"]),
                  "nuevos_top5_no_vacios_vs_B": sorted(tag(r) for r in no_resp if r[k]["nonempty_top5"] and not r["B"]["nonempty_top5"]),
                  "estados": dict(__import__("collections").Counter(f"{r[k]['status']}:{r[k]['reason']}" for r in no_resp))} for k in CONFIGS}
    sco = {r["form"]: {k: {"probes_pos_en_paquete": r[k]["sco020"], "paquete": r[k]["sco020_bundle"], "pos_k10": r[k]["pos_k10"],
                           "bundle_hit": r[k]["bundle_hit"]} for k in CONFIGS} for r in rows if r["id"].endswith("SCO-020")}
    hashes_after = {os.path.relpath(p, ROOT): sha_file(p) for p in PROTECTED}
    out = {"summary": summary, "summary_criterio_ids": summary_ids, "comparaciones": comps, "no_respondibles": nonans,
           "n_no_respondibles": len(no_resp), "sco020": sco,
           "anclas_dev_sin_fragmento_en_su_pagina": anchor_found,
           "tiempo_ms_por_retrieve": {k: round(1000 * float(np.mean(v)), 1) for k, v in timing.items()},
           "tiempo_init_s": {"paginas": round(t_p, 1), "apartados": round(t_s, 1)},
           "modo_apartados": rre_s.operating_mode, "pdf_verificado_apartados": rre_s.source_sha256_verified,
           "reglas_fijas_por_id_en_rre": len(hardcoded),
           "integridad": {"sha256_antes": hashes_before, "sha256_despues": hashes_after, "identicos": hashes_before == hashes_after},
           "rows": rows}
    json.dump(out, open(os.path.join(HERE, "eval_results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"TOTAL": summary["TOTAL"], "ids": summary_ids, "integridad": out["integridad"]["identicos"],
                      "anclas_sin_fragmento": anchor_found}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

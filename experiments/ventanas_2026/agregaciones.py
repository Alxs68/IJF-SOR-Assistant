"""Ventanas semanticas: diagnostico de SCO-020 y comparacion de agregaciones de ventanas (DEV, sin LLM, sin red).

Configuraciones (todas con R1 = RRE_CHANNEL_CHAMPIONS=1 salvo A):
  A    actual sin R1 (referencia)        B    actual + R1
  D    ventanas, maximo (ag1)            T2   ventanas, media de las 2 mejores (ag2)
  T3   ventanas, media de las 3 mejores (ag3)
  DISP ventanas, maximo - LAMBDA * desviacion tipica de las ventanas del pasaje (ag4; LAMBDA fijado a priori = 0.5)
  DISP_0.25 / DISP_1.0  sensibilidad de LAMBDA (solo informativa; no se elige sobre DEV)
Si un pasaje tiene menos ventanas que k, se promedian las que tiene. Desviacion de un pasaje con 1 ventana = 0.
Generico: ninguna regla, palabra clave, identificador ni peso depende de una pregunta o un pasaje.
rre._dense_search se sustituye SOLO EN MEMORIA; el OODDetector conserva sus embeddings originales.
Uso (desde la raiz del repo): python experiments/ventanas_2026/agregaciones.py -> agregaciones_results.json
"""
import hashlib, json, os, re, sys, time
os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                   "GEMINI_API_KEY": "", "GOOGLE_API_KEY": "", "GROQ_API_KEY": ""})
for v in ("RRE_CHANNEL_CHAMPIONS", "RRE_ENABLE_SCOPE_PREFERENCE"):
    os.environ.pop(v, None)
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
os.chdir(ROOT)
D_DIR = os.path.join(ROOT, "data", "processed", "rebuild_2026_08_corrected")
PROTECTED = ["passages_candidate.json", "dense_embeddings_candidate.npy", "vector_index_candidate.json",
             "knowledge_graph_candidate.json", "dense_embeddings_meta.json"]
LAMBDA = 0.5
# Pasajes normativos de SCO-020 verificados en el corpus (solo para el DIAGNOSTICO; no intervienen en la recuperacion)
DIAG_PIDS = {
    "SOR-2026-08-P075-S086": "6.1 limites individuales: junior/senior sin tolerancia adicional (ANCLA)",
    "SOR-2026-08-P077-S090": "6.2.3 pesaje oficial: un dia antes de la competicion, 16:00",
    "SOR-2026-08-P079-S093": "6.3 pesaje aleatorio: dia de competicion, <= 5 % sobre el limite",
    "SOR-2026-08-P080-S098": "p.80 tabla 6.3.4 tolerancias del pesaje aleatorio (+5 %) [metadato 6.4]",
    "SOR-2026-08-P081-S100": "6.4.2 equipo mixto tras individual: +5 % solo categorias minus (distractor)",
    "SOR-2026-08-P082-S100": "6.4.2 continuacion (p.82)",
}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def build_aggregators(n_pass, win_pid_idx):
    nwin = np.bincount(win_pid_idx, minlength=n_pass)
    K = int(nwin.max())
    pad = np.full((n_pass, K), -1, dtype=int)
    fill = np.zeros(n_pass, dtype=int)
    for w, p in enumerate(win_pid_idx):
        pad[p, fill[p]] = w
        fill[p] += 1
    mask = pad >= 0

    def window_matrix(sw):
        M = np.where(mask, sw[np.clip(pad, 0, None)], -np.inf)
        return -np.sort(-M, axis=1)            # descendente por pasaje

    def topk_mean(k):
        def f(sw):
            M = window_matrix(sw)
            kk = np.minimum(nwin, k)
            S = np.where(np.arange(K)[None, :] < kk[:, None], M, 0.0).sum(axis=1)
            return S / kk
        return f

    def disp(lam):
        def f(sw):
            V = np.where(mask, sw[np.clip(pad, 0, None)], np.nan)   # cosenos de las ventanas reales del pasaje
            return np.nanmax(V, axis=1) - lam * np.nanstd(V, axis=1)
        return f

    return {"max": topk_mean(1), "top2": topk_mean(2), "top3": topk_mean(3),
            "disp": disp(LAMBDA), "disp_0.25": disp(0.25), "disp_1.0": disp(1.0)}, nwin, window_matrix


def make_dense(rre, W, agg, STOPWORDS):
    passage_ids = rre.dense_meta.get("passage_ids", [p["passage_id"] for p in rre.passages])

    def scores(query):
        sims = agg(W @ rre.dense_model.encode(query, normalize_embeddings=True))
        clean = query.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        eng = " ".join(rre.SPANISH_TO_ENGLISH_SYNONYMS.get(t, t) for t in re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", clean)
                       if t not in STOPWORDS)
        if eng and eng != query:
            sims = np.maximum(sims, agg(W @ rre.dense_model.encode(eng, normalize_embeddings=True)))
        return sims

    def _dense_search(query, top_k=20):
        if rre.dense_model is None:
            return []
        sims = scores(query)
        top = np.argsort(sims)[::-1][:top_k]
        return [(passage_ids[i], float(sims[i])) for i in top if float(sims[i]) > 0.15]

    _dense_search.scores = scores
    return _dense_search


def main():
    hashes_before = {f: sha(os.path.join(D_DIR, f)) for f in PROTECTED}
    from experimental.benchmark_access import expand
    import rre_engine
    from rre_engine import ReasoningRetrievalEngine

    items = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(ROOT, "data", "eval", "benchmark_v2", "splits", "dev.jsonl"),
                                                              encoding="utf-8") if l.strip()}
    queries = json.load(open(os.path.join(ROOT, "data", "eval", "fase11", "retrieval_experiments_dev.json"), encoding="utf-8"))["per_query"]
    rre = ReasoningRetrievalEngine(enable_ood_detector=True)
    original_dense = rre._dense_search
    ood_ref = rre.ood_detector.dense_embeddings

    meta = json.load(open(os.path.join(HERE, "windows_meta.json"), encoding="utf-8"))
    pids = list(rre.dense_meta.get("passage_ids", [p["passage_id"] for p in rre.passages]))
    assert meta["passage_ids_orden"] == pids
    pos_of = {p: i for i, p in enumerate(pids)}
    win_pid_idx = np.array([pos_of[w["passage_id"]] for w in meta["windows"]])
    W = np.load(os.path.join(HERE, "windows_emb.npy"))[[w["fila"] for w in meta["windows"]]]
    aggs, nwin, window_matrix = build_aggregators(len(pids), win_pid_idx)
    dense_fns = {k: make_dense(rre, W, a, rre_engine.STOPWORDS) for k, a in aggs.items()}

    CONFIGS = {"A": (original_dense, "0"), "B": (original_dense, "1"), "D": (dense_fns["max"], "1"),
               "T2": (dense_fns["top2"], "1"), "T3": (dense_fns["top3"], "1"), "DISP": (dense_fns["disp"], "1"),
               "DISP_0.25": (dense_fns["disp_0.25"], "1"), "DISP_1.0": (dense_fns["disp_1.0"], "1")}
    hist = lambda q, p: rre._query_requests_document_history(q) or not rre._is_version_history_passage(p)

    rows, timing = [], {k: [] for k in CONFIGS}
    for q in queries:
        it = items[q["id"]]
        anchors = it.get("minimum_evidence") or []
        first = expand(anchors[0]["passage_ids"]) if anchors else set()
        row = {"id": q["id"], "form": q["form"], "expected": q["expected_behavior"]}
        for name, (fn, flag) in CONFIGS.items():
            rre._dense_search = fn
            os.environ["RRE_CHANNEL_CHAMPIONS"] = flag
            out = {}
            for k in (5, 10):
                t = time.perf_counter()
                r = rre.retrieve(q["query_used"], top_k=k, domain_query=it["text"])
                timing[name].append(time.perf_counter() - t)
                ev = [e["passage_id"] for e in r.get("evidence", [])]
                out[k] = (r, ev, next((i for i, p in enumerate(ev, 1) if p in first), None) if first else None)
            r5, ev5, pos5 = out[5]
            bundle = ev5 + [e["passage_id"] for e in r5.get("related_passages", [])]
            d25 = [p for p, _ in fn(q["query_used"], top_k=25) if hist(q["query_used"], p)]
            row[name] = {"status": r5.get("status"), "top5": ev5, "top10": out[10][1], "bundle": bundle,
                         "pos_k5": pos5, "pos_k10": out[10][2],
                         "bundle_hit": all(expand(a["passage_ids"]) & set(bundle) for a in anchors) if anchors else None,
                         "dense25_rank": next((i for i, p in enumerate(d25, 1) if p in first), None) if first else None,
                         "nonempty_top5": bool(ev5),
                         "champions": (r5.get("channel_champions") or {})}
        rows.append(row)
    rre._dense_search = original_dense
    os.environ.pop("RRE_CHANNEL_CHAMPIONS", None)

    # ---------------- metricas
    ans = [r for r in rows if r["expected"] == "RESPONDER"]
    no_resp = [r for r in rows if r["expected"] != "RESPONDER"]
    tag = lambda r: f"{r['id']}/{r['form']}"

    def metrics(name, form=None):
        R = [r[name] for r in ans if form is None or r["form"] == form]
        n = len(R)
        return {"n": n, "R@5": round(sum(1 for x in R if x["pos_k5"]) / n, 3),
                "R@10": round(sum(1 for x in R if x["pos_k10"]) / n, 3),
                "MRR@10": round(sum(1 / x["pos_k10"] for x in R if x["pos_k10"]) / n, 3),
                "denso_top25": round(sum(1 for x in R if x["dense25_rank"]) / n, 3),
                "paquete": round(sum(1 for x in R if x["bundle_hit"]) / n, 3)}

    def diff(a, b):
        return {"ganadas_paquete": sorted(tag(r) for r in ans if r[b]["bundle_hit"] and not r[a]["bundle_hit"]),
                "perdidas_paquete": sorted(tag(r) for r in ans if r[a]["bundle_hit"] and not r[b]["bundle_hit"]),
                "regresiones_pos_k10": sorted(f"{tag(r)}:{r[a]['pos_k10']}->{r[b]['pos_k10']}" for r in ans
                                              if r[a]["pos_k10"] and (not r[b]["pos_k10"] or r[b]["pos_k10"] > r[a]["pos_k10"])),
                "mejoras_pos_k10": sorted(f"{tag(r)}:{r[a]['pos_k10']}->{r[b]['pos_k10']}" for r in ans
                                          if r[b]["pos_k10"] and (not r[a]["pos_k10"] or r[b]["pos_k10"] < r[a]["pos_k10"]))}

    summary = {f: {k: metrics(k, None if f == "TOTAL" else f) for k in CONFIGS} for f in ("DICT", "LLM", "TOTAL")}
    comparisons = {f"{b}_vs_{a}": diff(a, b) for b in CONFIGS for a in ("B", "D") if b not in ("A", a)}
    nonans = {k: {"top5_no_vacio": sum(1 for r in no_resp if r[k]["nonempty_top5"]),
                  "cambios_estado_vs_A": sorted(f"{tag(r)}:{r['A']['status']}->{r[k]['status']}" for r in no_resp if r[k]["status"] != r["A"]["status"]),
                  "cambios_estado_vs_B": sorted(f"{tag(r)}:{r['B']['status']}->{r[k]['status']}" for r in no_resp if r[k]["status"] != r["B"]["status"]),
                  "top5_distinto_vs_B": sum(1 for r in no_resp if r[k]["top5"] != r["B"]["top5"])} for k in CONFIGS}

    # ---------------- diagnostico SCO-020
    sco = [r for r in rows if r["id"].endswith("SCO-020")]
    qtext = next(q["query_used"] for q in queries if q["id"].endswith("SCO-020"))
    diag = {"query_used": {r["form"]: next(q["query_used"] for q in queries if q["id"] == r["id"] and q["form"] == r["form"]) for r in sco},
            "pasajes": DIAG_PIDS}
    sparse = [p for p, _ in rre._sparse_search(qtext, top_k=25)]
    diag["canal_sparse_rango"] = {p: (sparse.index(p) + 1 if p in sparse else None) for p in DIAG_PIDS}
    q_emb = rre.dense_model.encode(qtext, normalize_embeddings=True)
    orig_sims = rre.dense_embeddings @ q_emb
    ch = {}
    for name in ("orig",) + tuple(aggs):
        s = orig_sims if name == "orig" else aggs[name](W @ q_emb)
        order = list(np.argsort(s)[::-1])
        ch[name] = {"top10": [(pids[i], round(float(s[i]), 4), int(nwin[i])) for i in order[:10]],
                    "rangos": {p: order.index(pos_of[p]) + 1 for p in DIAG_PIDS},
                    "scores": {p: round(float(s[pos_of[p]]), 4) for p in DIAG_PIDS}}
    diag["canal_denso"] = ch
    sw = W @ q_emb
    diag["ventanas"] = {p: [{"token_inicio": w["token_inicio"], "token_fin": w["token_fin"], "cos": round(float(sw[j]), 4)}
                            for j, w in enumerate(meta["windows"]) if w["passage_id"] == p] for p in DIAG_PIDS}
    # pasajes que adelantan al ancla en el canal denso con 'max'
    anc = "SOR-2026-08-P075-S086"
    s_max = aggs["max"](sw)
    diag["adelantan_al_ancla_max"] = [{"pid": pids[i], "titulo": rre.passages_by_id[pids[i]]["heading_path"][0],
                                       "cos_orig": round(float(orig_sims[i]), 4), "cos_max_ventanas": round(float(s_max[i]), 4),
                                       "ganancia": round(float(s_max[i] - orig_sims[i]), 4), "n_ventanas": int(nwin[i])}
                                      for i in np.argsort(s_max)[::-1] if s_max[i] > s_max[pos_of[anc]]]
    diag["paquetes"] = {r["form"]: {k: {"top5": r[k]["top5"], "bundle": r[k]["bundle"], "pos_k10": r[k]["pos_k10"],
                                        "dense25_rank": r[k]["dense25_rank"], "champions": r[k]["champions"],
                                        "contiene": {p: (p in r[k]["bundle"]) for p in DIAG_PIDS}} for k in CONFIGS} for r in sco}
    # sesgo general del maximo: ganancia media de similitud (max ventanas - original) por numero de ventanas, en las 82 consultas
    gain = {}
    for q in queries:
        e = rre.dense_model.encode(q["query_used"], normalize_embeddings=True)
        g = aggs["max"](W @ e) - rre.dense_embeddings @ e
        for n in sorted(set(nwin.tolist())):
            gain.setdefault(str(n), []).append(float(g[nwin == n].mean()))
    diag["ganancia_media_max_por_n_ventanas"] = {n: round(float(np.mean(v)), 4) for n, v in gain.items()}

    ood_ok = rre.ood_detector.dense_embeddings is ood_ref is rre.dense_embeddings
    hashes_after = {f: sha(os.path.join(D_DIR, f)) for f in PROTECTED}
    out = {"lambda": LAMBDA, "summary": summary, "comparaciones": comparisons, "no_respondibles": nonans,
           "n_no_respondibles": len(no_resp), "sco020": diag,
           "tiempo_ms_por_retrieve": {k: round(1000 * float(np.mean(v)), 1) for k, v in timing.items()},
           "ood_detector_embeddings_originales": bool(ood_ok),
           "integridad": {"sha256_antes": hashes_before, "sha256_despues": hashes_after, "identicos": hashes_before == hashes_after},
           "rows": rows}
    json.dump(out, open(os.path.join(HERE, "agregaciones_results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"summary_TOTAL": summary["TOTAL"], "integridad": out["integridad"]["identicos"]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

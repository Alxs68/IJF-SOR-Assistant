"""Experimento ventanas semanticas + R1: evaluacion de recuperacion A/B/C/D (benchmark_v2 DEV, sin LLM, sin red).

A actual | B actual+R1 | C ventanas | D ventanas+R1 (RRE_CHANNEL_CHAMPIONS=1).
C/D sustituyen rre._dense_search SOLO EN MEMORIA: similitud de un pasaje = maxima de sus ventanas, con la misma
proyeccion ES->EN, el mismo umbral 0,15 y el mismo top_k. No se modifica src/, data/processed/ ni el benchmark.
El OODDetector conserva sus embeddings originales (recibe, como siempre, el top denso del canal activo).
Consultas: query_used DICT y LLM de data/eval/fase11/retrieval_experiments_dev.json (82, incl. no respondibles).
dev.jsonl se lee directamente (no se abre test_sealed).
Uso (desde la raiz del repo): python experiments/ventanas_2026/eval.py   -> experiments/ventanas_2026/results.json
"""
import hashlib, json, os, re, sys, time
os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                   "GEMINI_API_KEY": "", "GOOGLE_API_KEY": "", "GROQ_API_KEY": ""})
os.environ.pop("RRE_CHANNEL_CHAMPIONS", None)
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
os.chdir(ROOT)
D = os.path.join(ROOT, "data", "processed", "rebuild_2026_08_corrected")
PROTECTED = ["passages_candidate.json", "dense_embeddings_candidate.npy", "vector_index_candidate.json",
             "knowledge_graph_candidate.json"]
FOCUS = ["SCO-013", "SCO-014", "EXC-003", "MLG-002", "SCO-019", "SCO-020", "SCO-021", "SCO-022"]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def make_window_dense_search(rre, W, win_pid_idx, n_pass, STOPWORDS):
    """Replica de ReasoningRetrievalEngine._dense_search con similitud = max de ventanas por pasaje."""
    passage_ids = rre.dense_meta.get("passage_ids", [p["passage_id"] for p in rre.passages])

    def per_passage(q_emb):
        s = W @ q_emb
        out = np.full(n_pass, -np.inf, dtype=np.float32)
        np.maximum.at(out, win_pid_idx, s)
        return out

    def _dense_search(query, top_k=20):
        if rre.dense_model is None:
            return []
        q_emb = rre.dense_model.encode(query, normalize_embeddings=True)
        sims = per_passage(q_emb)
        clean = query.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        raw_tokens = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", clean)
        eng_parts = []
        for t in raw_tokens:
            if t not in STOPWORDS:
                eng_parts.append(rre.SPANISH_TO_ENGLISH_SYNONYMS.get(t, t))
        eng_query = " ".join(eng_parts)
        if eng_query and eng_query != query:
            sims = np.maximum(sims, per_passage(rre.dense_model.encode(eng_query, normalize_embeddings=True)))
        top_indices = np.argsort(sims)[::-1][:top_k]
        return [(passage_ids[i], float(sims[i])) for i in top_indices if float(sims[i]) > 0.15]

    return _dense_search


def main():
    hashes_before = {f: sha(os.path.join(D, f)) for f in PROTECTED}
    from experimental.benchmark_access import expand
    import rre_engine
    from rre_engine import ReasoningRetrievalEngine

    items = {}
    for line in open(os.path.join(ROOT, "data", "eval", "benchmark_v2", "splits", "dev.jsonl"), encoding="utf-8"):
        if line.strip():
            it = json.loads(line)
            items[it["id"]] = it
    queries = json.load(open(os.path.join(ROOT, "data", "eval", "fase11", "retrieval_experiments_dev.json"),
                             encoding="utf-8"))["per_query"]

    t0 = time.perf_counter()
    rre = ReasoningRetrievalEngine(enable_ood_detector=True)
    t_init = time.perf_counter() - t0
    original_dense = rre._dense_search
    ood_emb_ref = rre.ood_detector.dense_embeddings if rre.ood_detector else None
    ood_centroid = None if rre.ood_detector is None or rre.ood_detector.domain_centroid is None else np.array(rre.ood_detector.domain_centroid, copy=True)

    meta = json.load(open(os.path.join(HERE, "windows_meta.json"), encoding="utf-8"))
    W = np.load(os.path.join(HERE, "windows_emb.npy"))
    passage_ids = rre.dense_meta.get("passage_ids", [p["passage_id"] for p in rre.passages])
    assert meta["passage_ids_orden"] == list(passage_ids)
    pos_of = {pid: i for i, pid in enumerate(passage_ids)}
    win_pid_idx = np.array([pos_of[w["passage_id"]] for w in meta["windows"]])
    W = W[[w["fila"] for w in meta["windows"]]]
    window_dense = make_window_dense_search(rre, W, win_pid_idx, len(passage_ids), rre_engine.STOPWORDS)
    win_texts_len = len(meta["windows"])

    full_text = {p["passage_id"]: p.get("text_original", "") for p in rre.passages}
    stitched_text = {}
    if rre.stitcher:
        for p in rre.passages:
            try:
                stitched_text[p["passage_id"]] = rre.stitcher.stitch_evidence(p).get("text_original")
            except Exception:
                pass

    CONFIGS = {"A": (original_dense, "0"), "B": (original_dense, "1"), "C": (window_dense, "0"), "D": (window_dense, "1")}
    rows, timing, text_check = [], {k: [] for k in CONFIGS}, {"entregas": 0, "texto_original_completo": 0, "no_coinciden": []}
    for q in queries:
        it = items[q["id"]]
        anchors = it.get("minimum_evidence") or []
        answerable = q["expected_behavior"] == "RESPONDER"
        first = expand(anchors[0]["passage_ids"]) if anchors else set()
        row = {"id": q["id"], "form": q["form"], "expected": q["expected_behavior"]}
        for name, (dense_fn, flag) in CONFIGS.items():
            rre._dense_search = dense_fn
            os.environ["RRE_CHANNEL_CHAMPIONS"] = flag
            res = {}
            for k in (5, 10):
                t = time.perf_counter()
                r = rre.retrieve(q["query_used"], top_k=k, domain_query=it["text"])
                timing[name].append(time.perf_counter() - t)
                ev = [e["passage_id"] for e in r.get("evidence", [])]
                pos = next((i for i, pid in enumerate(ev, 1) if pid in first), None) if first else None
                res[k] = (r, ev, pos)
            r5, ev5, pos5 = res[5]
            r10, ev10, pos10 = res[10]
            bundle = ev5 + [e["passage_id"] for e in r5.get("related_passages", [])]
            for e in r5.get("evidence", []) + r5.get("related_passages", []):
                text_check["entregas"] += 1
                tx = e.get("text_original", "")
                if tx == full_text.get(e["passage_id"]) or tx == stitched_text.get(e["passage_id"]):
                    text_check["texto_original_completo"] += 1
                else:
                    text_check["no_coinciden"].append([name, q["id"], q["form"], e["passage_id"]])
            dense25 = [pid for pid, _ in dense_fn(q["query_used"], top_k=25)
                       if rre._query_requests_document_history(q["query_used"]) or not rre._is_version_history_passage(pid)]
            row[name] = {"status": r5.get("status"), "reason": r5.get("reason"), "top5": ev5, "pos_k5": pos5,
                         "pos_k10": pos10, "top10": ev10,
                         "bundle_hit": (all(expand(a["passage_ids"]) & set(bundle) for a in anchors) if anchors else None),
                         "dense25_hit": (bool(first & set(dense25)) if first else None),
                         "dense25_rank": next((i for i, pid in enumerate(dense25, 1) if pid in first), None),
                         "nonempty_top5": bool(ev5)}
        rows.append(row)
    rre._dense_search = original_dense
    os.environ.pop("RRE_CHANNEL_CHAMPIONS", None)

    def metrics(name, form):
        R = [r for r in rows if r["expected"] == "RESPONDER" and (form is None or r["form"] == form)]
        n = len(R)
        c = [r[name] for r in R]
        return {"n": n,
                "R@5": round(sum(1 for x in c if x["pos_k5"] and x["pos_k5"] <= 5) / n, 3),
                "R@10": round(sum(1 for x in c if x["pos_k10"] and x["pos_k10"] <= 10) / n, 3),
                "MRR@10": round(sum(1 / x["pos_k10"] for x in c if x["pos_k10"]) / n, 3),
                "denso_top25": round(sum(1 for x in c if x["dense25_hit"]) / n, 3),
                "paquete_final": round(sum(1 for x in c if x["bundle_hit"]) / n, 3)}

    summary = {f: {k: metrics(k, None if f == "TOTAL" else f) for k in CONFIGS} for f in ("DICT", "LLM", "TOTAL")}
    changes = {}
    for k in ("B", "C", "D"):
        ans = [r for r in rows if r["expected"] == "RESPONDER"]
        def tag(r): return f"{r['id']}/{r['form']}"
        changes[k] = {
            "ganadas_R@5": sorted(tag(r) for r in ans if (r[k]["pos_k5"] or 99) <= 5 < (r["A"]["pos_k5"] or 99)),
            "perdidas_R@5": sorted(tag(r) for r in ans if (r["A"]["pos_k5"] or 99) <= 5 < (r[k]["pos_k5"] or 99)),
            "ganadas_paquete": sorted(tag(r) for r in ans if r[k]["bundle_hit"] and not r["A"]["bundle_hit"]),
            "perdidas_paquete": sorted(tag(r) for r in ans if r["A"]["bundle_hit"] and not r[k]["bundle_hit"]),
            "regresiones_posicion": sorted(f"{tag(r)}:{r['A']['pos_k10']}->{r[k]['pos_k10']}" for r in ans
                                           if r["A"]["pos_k10"] and (not r[k]["pos_k10"] or r[k]["pos_k10"] > r["A"]["pos_k10"])),
        }
    no_resp = [r for r in rows if r["expected"] != "RESPONDER"]
    fp = {k: {"top5_no_vacio": sum(1 for r in no_resp if r[k]["nonempty_top5"]),
              "cambios_estado_vs_A": sorted(f"{r['id']}/{r['form']}:{r['A']['status']}->{r[k]['status']}" for r in no_resp
                                            if r[k]["status"] != r["A"]["status"]),
              "nuevos_top5_no_vacios_vs_A": sorted(f"{r['id']}/{r['form']}" for r in no_resp
                                                   if r[k]["nonempty_top5"] and not r["A"]["nonempty_top5"])}
          for k in CONFIGS}
    fp["n_no_respondibles"] = len(no_resp)
    focus = [{"id": r["id"], "form": r["form"],
              **{k: f"k5={r[k]['pos_k5']} k10={r[k]['pos_k10']} d25={r[k]['dense25_rank']} paq={r[k]['bundle_hit']}" for k in CONFIGS}}
             for r in rows if any(r["id"].endswith(f) for f in FOCUS)]
    ans = [r for r in rows if r["expected"] == "RESPONDER"]
    changes["D_vs_B"] = {
        "ganadas_paquete": sorted(f"{r['id']}/{r['form']}" for r in ans if r["D"]["bundle_hit"] and not r["B"]["bundle_hit"]),
        "perdidas_paquete": sorted(f"{r['id']}/{r['form']}" for r in ans if r["B"]["bundle_hit"] and not r["D"]["bundle_hit"])}
    ood_ok = (rre.ood_detector is not None and rre.ood_detector.dense_embeddings is ood_emb_ref
              and ood_emb_ref is rre.dense_embeddings and rre.dense_embeddings.shape == (385, 384)
              and (ood_centroid is None or np.array_equal(ood_centroid, rre.ood_detector.domain_centroid)))
    hashes_after = {f: sha(os.path.join(D, f)) for f in PROTECTED}
    out = {"summary": summary, "cambios_vs_A": changes, "no_respondibles": fp, "foco": focus,
           "texto_entregado": {**text_check, "no_coinciden": text_check["no_coinciden"][:20]},
           "tiempo_ms_por_consulta_retrieve": {k: round(1000 * float(np.mean(v)), 1) for k, v in timing.items()},
           "tiempo_init_rre_s": round(t_init, 2), "ventanas": win_texts_len,
           "ood_detector_embeddings_originales": ood_ok,
           "scope_preference_R3": os.environ.get("RRE_ENABLE_SCOPE_PREFERENCE", ""),
           "integridad": {"sha256_antes": hashes_before, "sha256_despues": hashes_after,
                          "sha256_identicos": hashes_before == hashes_after},
           "rows": rows}
    json.dump(out, open(os.path.join(HERE, "results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("rows",)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

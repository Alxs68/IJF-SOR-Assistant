"""Experimentos A (ablacion de reglas fijas del RRE) y B (expansion jerarquica generica sobre apartados).
DEV (82 consultas), sin LLM, sin red. Nada de src/ ni data/ se modifica: el RRE variante se genera en memoria
(rre_adapter.py) y las expansiones son post-proceso sobre la salida de SW.

Configuraciones
  B                 paginas, indices originales, R1                                  <- referencia
  B-sin-reglas      B con los 7 bloques con passage_id fijo desactivados
  B-sin-<BLOQUE>    ablacion individual (7 bloques por ID + 2 complementarios por pagina)
  B-sin-todo        B sin bloques por ID ni por pagina
  SW / SW-sin-...   lo mismo sobre apartados + denso por ventanas (experimento previo), R1
  SW-traducidas     DIAGNOSTICO: reglas por ID traducidas mecanicamente a la unidad-apartado que las contiene
  X+B1..B4          X + expansion jerarquica (limites fijados a priori: S=2 hermanos, MAX_ADD=8), X en EXP_BASES
  X+B2g..B4g        idem, hermanos solo si figuran en el top-20 de la misma recuperacion (S=todos, MAX_ADD=8)
  X+B4c             B4 compacto (S=2, MAX_ADD=4, con filtro top-20): elegido A POSTERIORI a partir de la rejilla sobre SW
Uso (desde la raiz del repo): python experiments/reglas_rre_expansion_2026/eval_reglas_expansion.py
"""
import collections, hashlib, json, os, re, sys, time
os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "GEMINI_API_KEY": "", "GOOGLE_API_KEY": "", "GROQ_API_KEY": ""})
for v in ("RRE_CHANNEL_CHAMPIONS", "RRE_ENABLE_SCOPE_PREFERENCE", "RRE_ENABLE_SEMANTIC_RANKER"):
    os.environ.pop(v, None)
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEG = os.path.join(ROOT, "experiments", "segmentacion_apartados_2026")
IDX = os.path.join(SEG, "index")
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), HERE, SEG]
os.chdir(ROOT)
D = os.path.join(ROOT, "data", "processed", "rebuild_2026_08_corrected")
PDF_SHA = "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620"
PROTECTED = ([os.path.join(D, f) for f in ("passages_candidate.json", "dense_embeddings_candidate.npy", "vector_index_candidate.json",
                                          "knowledge_graph_candidate.json", "dense_embeddings_meta.json")]
             + [os.path.join(ROOT, "data", "derived", "article_units_v1", "units.jsonl"), os.path.join(ROOT, "src", "rre_engine.py"),
                os.path.join(ROOT, "data", "eval", "benchmark_v2", "splits", "dev.jsonl"),
                os.path.join(ROOT, "data", "eval", "fase11", "retrieval_experiments_dev.json"), os.path.join(SEG, "units.jsonl")]
             + [os.path.join(IDX, f) for f in sorted(os.listdir(IDX))])
SCO = {"6.1": "SEC-0086", "6.2.3": "SEC-0090", "6.3": "SEC-0093", "6.3.4 (apartado)": "SEC-0097", "tabla 6.3.4": "TAB-0030", "6.4.2": "SEC-0100"}
MAX_ADD, S_DEFAULT, GATE_K = 8, 2, 20
EXP_BASES = ("SW", "SW-sin-reglas", "SW-sin-todo")  # salidas sobre las que se aplica la expansion


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    hashes_before = {os.path.relpath(p, ROOT): sha_file(p) for p in PROTECTED}
    from experimental.benchmark_access import expand as expand_ids
    from eval_sections import window_dense, norm, SCO020_PROBES
    import rre_engine
    import rre_adapter as AD

    mod, line_ranges, var_sha = AD.load_variant("abl")
    units_list = [json.loads(l) for l in open(os.path.join(SEG, "units.jsonl"), encoding="utf-8")]
    U = {u["passage_id"]: u for u in units_list}
    hard_ids = sorted(set(re.findall(r"SOR-2026-08-P\d{3}-S\d{3}", open(AD.SRC, encoding="utf-8").read())))
    id2unit = {}
    for pid in hard_ids:
        c = [u["passage_id"] for u in units_list if pid in u["original_passage_ids"] and u["unit_type"] == "APARTADO"]
        assert len(c) == 1, (pid, c)
        id2unit[pid] = c[0]
    modT, _, varT_sha = AD.load_variant("traducidas", translate_ids=id2unit)

    items = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(ROOT, "data", "eval", "benchmark_v2", "splits", "dev.jsonl"),
                                                              encoding="utf-8") if l.strip()}
    queries = json.load(open(os.path.join(ROOT, "data", "eval", "fase11", "retrieval_experiments_dev.json"), encoding="utf-8"))["per_query"]

    t0 = time.perf_counter()
    eng = {"P": mod.ReasoningRetrievalEngine(enable_ood_detector=True),
           "S": mod.ReasoningRetrievalEngine(base_dir=IDX, enable_ood_detector=True),
           "ST": modT.ReasoningRetrievalEngine(base_dir=IDX, enable_ood_detector=True),
           "P0": rre_engine.ReasoningRetrievalEngine(enable_ood_detector=True),
           "S0": rre_engine.ReasoningRetrievalEngine(base_dir=IDX, enable_ood_detector=True)}
    t_init = time.perf_counter() - t0
    for k in ("S", "ST", "S0"):
        assert eng[k].operating_mode == "HYBRID", eng[k].degradation_reason
    assert not any(e.enable_semantic_ranker for e in eng.values())
    wm = json.load(open(os.path.join(IDX, "windows_meta.json"), encoding="utf-8"))
    W = np.load(os.path.join(IDX, "windows_emb.npy"))
    for k in ("S", "ST", "S0"):
        e = eng[k]
        pos = {pid: i for i, pid in enumerate(e.dense_meta["passage_ids"])}
        e._dense_search = window_dense(e, W, np.array([pos[w["passage_id"]] for w in wm["windows"]]), rre_engine.STOPWORDS)
    modof = {"P": mod, "S": mod, "ST": modT, "P0": None, "S0": None}

    def pages_of(rec, ek):
        if ek in ("S", "ST", "S0"):
            u = U[rec["passage_id"]]
            return set(range(u["pdf_page_index"], u["page_end"] + 1))
        pg = {rec.get("page")} | {s.get("page") for s in rec.get("source_spans", []) if isinstance(s, dict)}
        return {p for p in pg if p is not None}

    def sat(rec, ek, a):
        return a["page"] in pages_of(rec, ek) and norm(a["snippet"]) in norm(rec.get("text_original", ""))

    # ---- 1. Equivalencia: variante sin ablacion == RRE original (paginas y apartados+ventanas, k=10, R1) ----
    os.environ["RRE_CHANNEL_CHAMPIONS"] = "1"
    equiv = {"P": 0, "S": 0, "n": len(queries), "difs": []}
    for q in queries:
        dq = items[q["id"]]["text"]
        for a, b in (("P", "P0"), ("S", "S0")):
            ra, rb = (eng[x].retrieve(q["query_used"], top_k=10, domain_query=dq) for x in (a, b))
            sig = lambda r: (r.get("status"), [(e["passage_id"], round(float(e.get("score", 0) or 0), 9)) for e in r.get("evidence", [])],
                             [e["passage_id"] for e in r.get("related_passages", [])])
            if sig(ra) == sig(rb):
                equiv[a] += 1
            else:
                equiv["difs"].append(f"{q['id']}/{q['form']}:{a}")
    del eng["P0"], eng["S0"]

    # ---- 2. Configuraciones de ablacion ----
    IDB, PGB = list(AD.ID_BLOCKS), list(AD.PAGE_BLOCKS)
    CONFIGS = {}
    for pre, ek in (("B", "P"), ("SW", "S")):
        CONFIGS[pre] = (ek, set())
        CONFIGS[f"{pre}-sin-reglas"] = (ek, set(IDB))
        for b in IDB + PGB:
            CONFIGS[f"{pre}-sin-{b}"] = (ek, {b})
        CONFIGS[f"{pre}-sin-todo"] = (ek, set(IDB + PGB))
    CONFIGS["SW-traducidas"] = ("ST", set())

    rows, timing = [], collections.defaultdict(list)
    for q in queries:
        it = items[q["id"]]
        anchors = it.get("minimum_evidence") or []
        first_ids = expand_ids(anchors[0]["passage_ids"]) if anchors else set()
        row = {"id": q["id"], "form": q["form"], "expected": q["expected_behavior"]}
        for name, (ek, abl) in CONFIGS.items():
            m, e = modof[ek], eng[ek]
            m._ABL.clear()
            m._ABL.update({b: True for b in abl})
            out = {}
            for k in ((5, 10, GATE_K) if name in EXP_BASES else (5, 10)):
                m._FIRED.clear()
                t = time.perf_counter()
                r = e.retrieve(q["query_used"], top_k=k, domain_query=it["text"])
                timing[name].append(time.perf_counter() - t)
                ev = r.get("evidence", [])
                out[k] = (r, ev, set(m._FIRED),
                          next((i for i, x in enumerate(ev, 1) if sat(x, ek, anchors[0])), None) if anchors else None,
                          next((i for i, x in enumerate(ev, 1) if x["passage_id"] in first_ids), None) if (anchors and ek == "P") else None)
            m._ABL.clear()
            r5, ev5, fired5 = out[5][0], out[5][1], out[5][2]
            rel = r5.get("related_passages", [])
            bundle = ev5 + [x for x in rel if x["passage_id"] not in {y["passage_id"] for y in ev5}]
            row[name] = {"status": r5.get("status"), "reason": r5.get("reason"),
                         "top5": [x["passage_id"] for x in ev5], "top10": [x["passage_id"] for x in out[10][1]],
                         "related": [x["passage_id"] for x in rel], "fired": sorted(fired5 | out[10][2]),
                         "pos_k5": out[5][3], "pos_k10": out[10][3], "pos_k5_ids": out[5][4], "pos_k10_ids": out[10][4],
                         "bundle": [x["passage_id"] for x in bundle],
                         "bundle_hit": all(any(sat(x, ek, a) for x in bundle) for a in anchors) if anchors else None,
                         "bundle_hit_ids": (all(expand_ids(a["passage_ids"]) & {x["passage_id"] for x in bundle} for a in anchors)
                                            if anchors and ek == "P" else None),
                         "nonempty_top5": bool(ev5), "bundle_chars": sum(len(x.get("text_original", "")) for x in bundle),
                         "hardcoded_in_top5": sorted(set(hard_ids) & {x["passage_id"] for x in ev5})}
            if name in EXP_BASES:
                row[name]["top20"] = [x["passage_id"] for x in out[GATE_K][1]]
        rows.append(row)
    os.environ.pop("RRE_CHANNEL_CHAMPIONS", None)

    # ---- 3. Expansion jerarquica generica (post-proceso sobre SW) ----
    secs = sorted((u for u in units_list if u["passage_id"].startswith("SEC-")), key=lambda u: int(u["passage_id"][4:]))
    order = {u["passage_id"]: i for i, u in enumerate(secs)}
    lab2u = {}
    for u in secs:
        if u["unit_type"] == "APARTADO":
            lab2u.setdefault(u["label"], u["passage_id"])
    prev_portada, last = {}, None
    for u in secs:
        prev_portada[u["passage_id"]] = last if u["unit_type"] != "PORTADA" else None
        if u["unit_type"] == "PORTADA":
            last = u["passage_id"]

    def sparent(pid):
        u = U[pid]
        if u.get("parent_unit_id"):
            return u["parent_unit_id"], "parent_unit_id"
        if u["unit_type"] != "APARTADO":
            return None, None
        mm = re.match(r"^(article|[a-z]{0,2})(\d+(?:\.\d+)+)$", u["label"])
        if mm:
            cand = mm.group(1) + mm.group(2).rsplit(".", 1)[0]
            if cand in lab2u and lab2u[cand] != pid:
                return lab2u[cand], "etiqueta"
        return prev_portada.get(pid), ("portada" if prev_portada.get(pid) else None)

    PARENT = {pid: sparent(pid) for pid in U}
    kids = collections.defaultdict(list)
    for pid in order:
        if U[pid]["unit_type"] == "APARTADO" and PARENT[pid][0]:
            kids[PARENT[pid][0]].append(pid)
    g = json.load(open(os.path.join(IDX, "knowledge_graph_candidate.json"), encoding="utf-8"))
    refs_table = collections.defaultdict(list)
    for e in g["edges"]:
        if e.get("relation_type") == "references_table":
            refs_table[e["source"]].append(e["target"])

    def siblings(pid, S, gate):
        if U[pid]["unit_type"] != "APARTADO" or not PARENT[pid][0]:
            return []
        sib = sorted((x for x in kids[PARENT[pid][0]] if x != pid), key=lambda x: abs(order[x] - order[pid]))
        if gate is not None:
            sib = [x for x in sib if x in gate]
        return sib if S is None else sib[:S]

    def expansion(bundle_ids, seeds, level, S, max_add, gate):
        seen, added = set(bundle_ids), []
        for seed in seeds:
            par = PARENT[seed][0]
            sib = siblings(seed, S, gate) if level >= 2 else []
            struct = [x for x in [seed, par] + sib if x]
            cands = ([par] if par else []) + sib
            if level >= 3:
                cands += [t for x in struct for t in (U[x].get("table_unit_ids") or [])]
            if level >= 4:
                cands += [t for x in struct for t in refs_table.get(x, [])]
            for c in cands:
                if c not in seen:
                    seen.add(c)
                    added.append(c)
                    if max_add is not None and len(added) >= max_add:
                        return added
        return added

    EXP = {}
    for bse in EXP_BASES:
        EXP.update({(bse, f"{bse}+B{l}"): (l, S_DEFAULT, MAX_ADD, False) for l in (1, 2, 3, 4)})
        EXP.update({(bse, f"{bse}+B{l}g"): (l, None, MAX_ADD, True) for l in (2, 3, 4)})
        # punto compacto de la rejilla (elegido A POSTERIORI tras ver la rejilla sobre SW; se etiqueta como tal)
        EXP[(bse, f"{bse}+B4c")] = (4, 2, 4, True)
    GRID = {("SW", f"SW+B4[S={s},max={m},gate={gt}]"): (4, s, m, gt) for s in (1, 2, None) for m in (4, 8, None) for gt in (False, True)}
    t_exp = collections.defaultdict(list)
    for row in rows:
        it = items[row["id"]]
        anchors = it.get("minimum_evidence") or []
        for (bse, name), (lvl, S, mx, gt) in {**EXP, **GRID}.items():
            base = row[bse]
            t = time.perf_counter()
            add = expansion(base["bundle"], base["top5"], lvl, S, mx, set(base["top20"]) if gt else None) if base["top5"] else []
            t_exp[name].append(time.perf_counter() - t)
            bundle = base["bundle"] + add
            recs = [U[x] for x in bundle]
            row[name] = {k: base[k] for k in ("status", "reason", "top5", "top10", "pos_k5", "pos_k10", "nonempty_top5", "related", "fired")}
            row[name].update({"added": add, "bundle": bundle, "bundle_chars": sum(len(x["text_original"]) for x in recs),
                              "bundle_hit": all(any(sat(x, "S", a) for x in recs) for a in anchors) if anchors else None})

    EXPN = [n for _, n in EXP]
    GRIDN = [n for _, n in GRID]
    ALL = list(CONFIGS) + EXPN
    ans = [r for r in rows if r["expected"] == "RESPONDER"]
    nonr = [r for r in rows if r["expected"] != "RESPONDER"]
    tag = lambda r: f"{r['id']}/{r['form']}"

    def metrics(k, form=None, ids=False):
        R = [r[k] for r in ans if form is None or r["form"] == form]
        p5, p10, bh = ("pos_k5_ids", "pos_k10_ids", "bundle_hit_ids") if ids else ("pos_k5", "pos_k10", "bundle_hit")
        n = len(R)
        return {"n": n, "R@5": round(sum(1 for x in R if x[p5]) / n, 3), "R@10": round(sum(1 for x in R if x[p10]) / n, 3),
                "MRR@10": round(sum(1 / x[p10] for x in R if x[p10]) / n, 3), "paquete": round(sum(1 for x in R if x[bh]) / n, 3),
                "chars_paquete_medio": int(np.mean([x["bundle_chars"] for x in R])),
                "unidades_paquete_medio": round(float(np.mean([len(x["bundle"]) for x in R])), 2)}

    summary = {f: {k: metrics(k, None if f == "TOTAL" else f) for k in ALL} for f in ("DICT", "LLM", "TOTAL")}
    summary_ids = {k: metrics(k, None, ids=True) for k in CONFIGS if CONFIGS[k][0] == "P"}
    grid = {k: metrics(k) for k in GRIDN}

    def diff(a, b):
        return {"ganadas_R@5": sorted(tag(r) for r in ans if r[b]["pos_k5"] and not r[a]["pos_k5"]),
                "perdidas_R@5": sorted(tag(r) for r in ans if r[a]["pos_k5"] and not r[b]["pos_k5"]),
                "ganadas_paquete": sorted(tag(r) for r in ans if r[b]["bundle_hit"] and not r[a]["bundle_hit"]),
                "perdidas_paquete": sorted(tag(r) for r in ans if r[a]["bundle_hit"] and not r[b]["bundle_hit"]),
                "mejoras_pos_k10": sorted(f"{tag(r)}:{r[a]['pos_k10']}->{r[b]['pos_k10']}" for r in ans
                                          if r[b]["pos_k10"] and (not r[a]["pos_k10"] or r[b]["pos_k10"] < r[a]["pos_k10"])),
                "regresiones_pos_k10": sorted(f"{tag(r)}:{r[a]['pos_k10']}->{r[b]['pos_k10']}" for r in ans
                                              if r[a]["pos_k10"] and (not r[b]["pos_k10"] or r[b]["pos_k10"] > r[a]["pos_k10"]))}
    comps = {f"{b}_vs_{a}": diff(a, b) for a, b in
             [("B", x) for x in CONFIGS if x.startswith("B-")] + [("SW", x) for x in CONFIGS if x.startswith("SW-")]
             + [("B", "SW"), ("B", "SW-sin-reglas"), ("B", "SW-sin-todo"), ("B", "SW-traducidas"), ("B-sin-reglas", "SW-sin-reglas"), ("B-sin-todo", "SW-sin-todo")]
             + [(b, n) for b, n in EXP] + [("B", n) for n in EXPN]}
    fired = {pre: dict(collections.Counter(b for r in rows for b in r[pre]["fired"])) for pre in ("B", "SW", "SW-traducidas")}
    fired_q = {pre: {tag(r): r[pre]["fired"] for r in rows if r[pre]["fired"]} for pre in ("B", "SW")}
    nonans = {k: {"top5_no_vacio": sum(1 for r in nonr if r[k]["nonempty_top5"]),
                  "cambios_estado_vs_B": sorted(f"{tag(r)}:{r['B']['status']}->{r[k]['status']}" for r in nonr if r[k]["status"] != r["B"]["status"]),
                  "estados": dict(collections.Counter(f"{r[k]['status']}:{r[k]['reason']}" for r in nonr)),
                  "chars_paquete_medio": int(np.mean([r[k]["bundle_chars"] for r in nonr]))} for k in ALL}

    def sco_view(r, k):
        bundle = r[k]["bundle"]
        txt = lambda pid: (U.get(pid) or eng["P"].passages_by_id.get(pid, {})).get("text_original", "")
        lab = lambda pid: (U.get(pid) or eng["P"].passages_by_id.get(pid, {})).get("heading_path", [""])[0][:70]
        return {"unidades": {n: (bundle.index(p) + 1 if p in bundle else None) for n, p in SCO.items()},
                "6.1_y_6.3_juntos": SCO["6.1"] in bundle and SCO["6.3"] in bundle,
                "6.1_6.3_y_tabla_6.3.4": all(SCO[n] in bundle for n in ("6.1", "6.3", "tabla 6.3.4")),
                "probes_pos": {n: [i for i, p in enumerate(bundle, 1) if norm(sn) in norm(txt(p))] for n, sn in SCO020_PROBES.items()},
                "paquete": [(p, lab(p)) for p in bundle], "pos_k10": r[k]["pos_k10"], "bundle_hit": r[k]["bundle_hit"],
                "chars": r[k]["bundle_chars"]}
    sco = {r["form"]: {k: sco_view(r, k) for k in ["B", "B-sin-reglas", "B-sin-todo", "SW", "SW-sin-reglas", "SW-sin-todo", "SW-traducidas"] + EXPN + GRIDN}
           for r in rows if r["id"].endswith("SCO-020")}
    focus = {tag(r): {k: {x: r[k].get(x) for x in ("status", "pos_k5", "pos_k10", "bundle_hit", "top5", "fired", "hardcoded_in_top5")}
                      for k in list(CONFIGS) + EXPN} for r in rows if r["id"].endswith(("EXC-005", "DIR-018"))}

    # ---- 4. Trazabilidad de toda unidad entregada en paquetes de apartados ----
    delivered = sorted({p for r in rows for k in ALL if k.startswith("SW") for p in r[k]["bundle"]})
    trace = {"unidades_entregadas": len(delivered), "fallos": []}
    for p in delivered:
        u = U[p]
        pages = {s.get("page") for s in u.get("source_spans", []) if isinstance(s, dict)}
        ok = (u.get("source_sha256") == PDF_SHA and bool(u.get("source_spans")) and pages and all(u["pdf_page_index"] <= x <= u["page_end"] for x in pages)
              and u.get("text_sha256") == hashlib.sha256(u["text_original"].encode("utf-8")).hexdigest())
        if not ok:
            trace["fallos"].append(p)
    struct_stats = {"padre_por": dict(collections.Counter(v[1] for v in PARENT.values())),
                    "padres_sco020": {n: PARENT[p] for n, p in SCO.items()},
                    "hermanos_6.1_orden": kids[PARENT[SCO["6.1"]][0]]}

    hashes_after = {os.path.relpath(p, ROOT): sha_file(p) for p in PROTECTED}
    out = {"equivalencia_variante_vs_original": equiv, "bloques_lineas_src": line_ranges, "sha_variante": var_sha, "sha_variante_traducida": varT_sha,
           "ids_fijas": hard_ids, "id_a_unidad": id2unit, "summary": summary, "summary_criterio_ids": summary_ids, "rejilla_B4": grid,
           "comparaciones": comps, "disparos_bloques": fired, "disparos_por_pregunta": fired_q, "no_respondibles": nonans,
           "sco020": sco, "foco_EXC005_DIR018": focus, "trazabilidad": trace, "jerarquia": struct_stats,
           "limites_expansion": {"MAX_ADD": MAX_ADD, "S": S_DEFAULT, "GATE_K": GATE_K},
           "tiempo_ms_por_retrieve": {k: round(1000 * float(np.mean(v)), 1) for k, v in timing.items()},
           "tiempo_ms_expansion": {k: round(1000 * float(np.mean(v)), 3) for k, v in t_exp.items() if k in EXPN},
           "tiempo_init_s": round(t_init, 1),
           "integridad": {"sha256_antes": hashes_before, "sha256_despues": hashes_after, "identicos": hashes_before == hashes_after},
           "rows": rows}
    json.dump(out, open(os.path.join(HERE, "results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"equiv": {k: v for k, v in equiv.items()}, "TOTAL": {k: summary["TOTAL"][k] for k in ALL},
                      "integridad": out["integridad"]["identicos"], "traza_fallos": len(trace["fallos"])}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

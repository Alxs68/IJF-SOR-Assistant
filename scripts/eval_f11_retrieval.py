#!/usr/bin/env python3
"""Fase 11B - Evaluacion INDIVIDUAL de las variantes de recuperacion R2-R5 frente a R0, SOLO en DEV.

R0   produccion: rre.retrieve(q, top_k=25, expand_graph=True, domain_query=original) (sin cambios)
R2   RRF(R0, unidades de articulo BM25)
R3   R0 reordenado por ambito de la consulta (beta 0.2 y 0.5, sensibilidad declarada de antemano)
R4   carril de referencias cruzadas resueltas anadido al top-5 de R0 (no cambia el ranking)
R5   RRF(R0, denso multilingue con la consulta original)  y  R5_SOLO (canal multilingue aislado)
Formas de consulta: DICT (proyeccion por diccionario de ADA) y LLM (traduccion registrada en la
corrida de la Fase 11, reproducida sin llamar al modelo). Si R0 se abstiene (OOD), todas las
variantes devuelven vacio: el control de dominio no se toca.
Metricas con equivalencia de pasajes duplicados: R@5, MRR, hit@10, precision@5 (pasajes dentro de
evidencia / excepcion / referencia esperadas), errores de ambito (distractor por encima de la
evidencia en top-10; distractor en top-5 sin la evidencia), consultas ganadas / perdidas y cambio de
rango de la primera evidencia. Para R4: cobertura de referencias y excepciones y precision del paquete.
Uso: python scripts/eval_f11_retrieval.py --llm-results data/eval/fase11/llm_dev_f11.json [--no-r5]
"""
import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict
from statistics import mean

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY"):
    os.environ[k] = ""
os.environ.setdefault("IJF_SOR_EDITION", "2026-08")
CORPUS = os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json")
OUT = os.path.join(ROOT, "data/eval/fase11/retrieval_experiments_dev.json")

from experimental.benchmark_access import expand, load_items  # noqa: E402
from experimental.retrieval_variants import (MultilingualDense, ScopeModel, UnitBM25, UnitCorpus,  # noqa: E402
                                             crossref_lane, rrf, scope_rerank)

DEPTH = 25


def sha_file(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def first(rk, S):
    return next((i for i, p in enumerate(rk, 1) if p in S), None)


def score(rk, it):
    ev = [expand(a["passage_ids"]) for a in it["minimum_evidence"]]
    E = set().union(*ev)
    allowed = E | set().union(*[expand(a["passage_ids"]) for a in it["exceptions_to_preserve"] + it["mandatory_cross_refs"]] or [set()])
    D = set().union(*[expand(a["passage_ids"]) for a in it["wrong_scope_distractors"]] or [set()]) - allowed
    f = first(rk, E)
    top5 = rk[:5]
    r = {"first": f, "r@5": sum(bool(s & set(top5)) for s in ev) / len(ev), "rr": 1 / f if f else 0.0,
         "hit@10": f is not None and f <= 10, "p@5": (sum(p in allowed for p in top5) / len(top5)) if top5 else 0.0}
    if D:
        fd = first(rk[:10], D)
        r["dist_above"] = fd is not None and (f is None or fd < f)
        r["dist_top5_wo_ev"] = bool(set(top5) & D) and not (set(top5) & E)
    return r


def agg(rows, var):
    xs = [r[var] for r in rows if var in r]
    if not xs:
        return None
    o = {"n": len(xs), "R@5": round(mean(x["r@5"] for x in xs), 3), "MRR": round(mean(x["rr"] for x in xs), 3),
         "hit@10": round(mean(x["hit@10"] for x in xs), 3), "P@5": round(mean(x["p@5"] for x in xs), 3)}
    sc = [x for x in xs if "dist_above" in x]
    if sc:
        o["scope_n"] = len(sc)
        o["dist_above_evidence"] = sum(x["dist_above"] for x in sc)
        o["dist_top5_without_evidence"] = sum(x["dist_top5_wo_ev"] for x in sc)
    if var != "R0":
        o["gained_vs_R0"] = sorted(r["id"] for r in rows if var in r and r[var]["r@5"] > r["R0"]["r@5"])
        o["lost_vs_R0"] = sorted(r["id"] for r in rows if var in r and r[var]["r@5"] < r["R0"]["r@5"])
        o["rank_changes"] = sorted(((r["id"], r["R0"]["first"], r[var]["first"]) for r in rows
                                    if var in r and r[var]["first"] != r["R0"]["first"]), key=lambda t: t[0])
    lat = [r["lat"].get(var) for r in rows if r["lat"].get(var) is not None]
    if lat:
        o["lat_ms_mean"] = round(mean(lat), 2)
    return o


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm-results", default=os.path.join(ROOT, "data/eval/fase11/llm_dev_f11.json"))
    ap.add_argument("--no-r5", action="store_true")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    items, meta = load_items("dev")
    before = sha_file(CORPUS)
    trans = {}
    if os.path.exists(a.llm_results):
        for row in json.load(open(a.llm_results, encoding="utf-8"))["per_run"][0]:
            trans[row["id"]] = row.get("translation")
    from ada_assistant import ArbitrationDecisionAssistant
    ada = ArbitrationDecisionAssistant()
    ada._call_llm = lambda prompt: (None, {})
    rre = ada.rre
    page_of = {pid: p.get("pdf_page_index") for pid, p in rre.passages_by_id.items()}
    t0 = time.perf_counter()
    uc = UnitCorpus()
    bm = UnitBM25(uc)
    scope = ScopeModel(uc)
    part_cache = {}

    def part_of_pid(pid):
        pg = page_of.get(pid)
        if pg not in part_cache:
            part_cache[pg] = uc.part_of_page(pg) if pg is not None else None
        return part_cache[pg]
    build = {"units": len(uc.docs), "scope_indicators": {t: sorted(p) for t, p in sorted(scope.indicator.items())},
             "build_s": round(time.perf_counter() - t0, 2)}
    mml = None
    if not a.no_r5:
        mml = MultilingualDense(uc)
        build["r5"] = mml.load()
        if not build["r5"]["loaded"]:
            mml = None
    rows = []
    for it in items:
        beh = it["auto_labels"]["expected_behavior"]
        forms = {"DICT": ada._translate_to_technical_english(it["text"])}
        if trans:
            forms["LLM"] = (trans.get(it["id"]) or "").strip() or it["text"]
        for form, q in forms.items():
            row = {"id": it["id"], "form": form, "language": it["language"], "category": it["category"],
                   "expected_behavior": beh, "query_used": q, "lat": {}}
            ts = time.perf_counter()
            res = rre.retrieve(q, top_k=DEPTH, expand_graph=True, domain_query=it["text"])
            row["lat"]["R0"] = (time.perf_counter() - ts) * 1000
            ok = res.get("status") == "SUCCESS"
            r0 = [e["passage_id"] for e in res.get("evidence", [])] if ok else []
            graph_rel = [x["passage_id"] for x in res.get("related_passages", [])] if ok else []
            ranks = {"R0": r0}
            if ok:
                ts = time.perf_counter()
                ranks["R2"] = rrf(r0, bm.passage_ranking(q, DEPTH))
                row["lat"]["R2"] = (time.perf_counter() - ts) * 1000
                parts = scope.query_parts(it["text"], q)
                row["scope_parts"] = sorted(parts)
                for beta in (0.2, 0.5):
                    ts = time.perf_counter()
                    ranks[f"R3_b{beta}"] = scope_rerank(r0, parts, part_of_pid, beta=beta)
                    row["lat"][f"R3_b{beta}"] = (time.perf_counter() - ts) * 1000
                if mml is not None:
                    ts = time.perf_counter()
                    ml = mml.passage_ranking(it["text"], DEPTH)
                    row["lat"]["R5_SOLO"] = (time.perf_counter() - ts) * 1000
                    ranks["R5"] = rrf(r0, ml)
                    ranks["R5_SOLO"] = ml
                    row["lat"]["R5"] = row["lat"]["R5_SOLO"]
            else:
                for v in ("R2", "R3_b0.2", "R3_b0.5") + (("R5", "R5_SOLO") if mml else ()):
                    ranks[v] = []
            row["top10"] = {v: rk[:10] for v, rk in ranks.items()}
            row["retrieve_status"] = res.get("status")
            if beh == "RESPONDER":
                for v, rk in ranks.items():
                    row[v] = score(rk, it)
                # R4: paquetes (no ranking)
                lane = crossref_lane(r0[:5], uc, page_of.get) if ok else []
                allowed = set().union(*[expand(x["passage_ids"]) for x in it["minimum_evidence"] + it["exceptions_to_preserve"] + it["mandatory_cross_refs"]])
                bundles = {"TOP5": r0[:5], "TOP5+GRAFO": list(dict.fromkeys(r0[:5] + graph_rel[:3])),
                           "TOP5+R4": list(dict.fromkeys(r0[:5] + [x["passage_id"] for x in lane]))}
                row["R4"] = {}
                for bname, b in bundles.items():
                    xr = [bool(expand(x["passage_ids"]) & set(b)) for x in it["mandatory_cross_refs"]]
                    ex = [bool(expand(x["passage_ids"]) & set(b)) for x in it["exceptions_to_preserve"]]
                    row["R4"][bname] = {"size": len(b), "precision": round(sum(p in allowed for p in b) / len(b), 3) if b else 0.0,
                                        "crossref_cov": xr, "exception_cov": ex}
                row["R4_lane"] = lane
            else:
                row["nonempty_top5"] = {v: bool(rk[:5]) for v, rk in ranks.items()}
            rows.append(row)
    variants = sorted({k for r in rows for k in r["top10"]})
    summary = {}
    for form in sorted({r["form"] for r in rows}):
        fr = [r for r in rows if r["form"] == form and r["expected_behavior"] == "RESPONDER"]
        summary[form] = {"global": {v: agg(fr, v) for v in variants}}
        for lang in sorted({r["language"] for r in fr}):
            summary[form][f"lang={lang}"] = {v: agg([r for r in fr if r["language"] == lang], v) for v in variants}
        for cat in sorted({r["category"] for r in fr}):
            summary[form][f"cat={cat}"] = {v: agg([r for r in fr if r["category"] == cat], v) for v in variants}
        r4 = {}
        for bname in ("TOP5", "TOP5+GRAFO", "TOP5+R4"):
            bs = [r["R4"][bname] for r in fr]
            xr = [c for b in bs for c in b["crossref_cov"]]
            ex = [c for b in bs for c in b["exception_cov"]]
            r4[bname] = {"mean_size": round(mean(b["size"] for b in bs), 2), "precision": round(mean(b["precision"] for b in bs), 3),
                         "crossref_covered": f"{sum(xr)}/{len(xr)}", "exception_covered": f"{sum(ex)}/{len(ex)}"}
        summary[form]["R4_bundles"] = r4
        nr = [r for r in rows if r["form"] == form and r["expected_behavior"] != "RESPONDER"]
        summary[form]["non_answerable_nonempty_top5"] = {v: sum(r["nonempty_top5"].get(v, False) for r in nr) for v in variants}
        summary[form]["non_answerable_n"] = len(nr)
    rep = {"benchmark": meta, "split": "dev", "build": build, "corpus_unchanged": before == sha_file(CORPUS),
           "llm_results": a.llm_results, "summary": summary, "per_query": rows,
           "note": "Solo dev. Equivalencia de pasajes duplicados. Etiquetas PENDING_EXPERT_REVIEW. Variantes evaluadas por separado."}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    for form, s in summary.items():
        print(f"== {form}")
        print(f"   {'variante':10} {'R@5':>5} {'MRR':>5} {'h@10':>5} {'P@5':>5} {'dAb':>3} {'d5':>3}  ganadas / perdidas")
        for v in variants:
            g = s["global"][v]
            if g:
                print(f"   {v:10} {g['R@5']:5.3f} {g['MRR']:5.3f} {g['hit@10']:5.3f} {g['P@5']:5.3f} {g.get('dist_above_evidence', '-'):>3} "
                      f"{g.get('dist_top5_without_evidence', '-'):>3}  {g.get('gained_vs_R0', '')} / {g.get('lost_vs_R0', '')}")
        print("   R4:", s["R4_bundles"])
        print("   no respondibles con top5 no vacio:", s["non_answerable_nonempty_top5"], "de", s["non_answerable_n"])
    print("build:", {k: v for k, v in build.items() if k != "scope_indicators"})
    print("indicadores de ambito:", build["scope_indicators"])
    print("corpus_unchanged=", rep["corpus_unchanged"], "resultados:", a.out)
    return 0 if rep["corpus_unchanged"] else 3


if __name__ == "__main__":
    sys.exit(main())

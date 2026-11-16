#!/usr/bin/env python3
"""Fase 11A - Recalculo OFFLINE (sin RRE ni LLM) de las metricas de DEV con equivalencia de pasajes.

Hallazgo: 87 de 136 anclas (evidencia minima + distractores) del benchmark_v2 tienen en la misma
pagina otros pasajes con text_original IDENTICO que el ancla no lista (solo difieren en metadatos).
Las metricas de la Fase 10 y del primer diagnostico de la Fase 11 contaban como fallo entregar uno
de esos duplicados. Este script recalcula, a partir de los resultados YA REGISTRADOS (top-10,
bundles), las metricas en modo ESTRICTO (Fase 10) y EQUIVALENTE, solo para dev.
Uso: python scripts/recompute_equivalence_f11.py
"""
import json
import os
import sys
from collections import Counter
from statistics import mean

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
from experimental.benchmark_access import equivalence_map, expand, load_items  # noqa: E402

RES = os.path.join(ROOT, "data/eval/benchmark_v2/results")
F11 = os.path.join(ROOT, "data/eval/fase11")


def anchor_sets(item, strict):
    f = (lambda a: set(a["passage_ids"])) if strict else (lambda a: expand(a["passage_ids"]))
    return [f(a) for a in item["minimum_evidence"]], [f(a) for a in item["wrong_scope_distractors"]]


def ranking_metrics(ranked, ev):
    E = set().union(*ev) if ev else set()
    first = next((i for i, p in enumerate(ranked, 1) if p in E), None)
    return {"r@5": sum(bool(s & set(ranked[:5])) for s in ev) / len(ev), "hit@10": first is not None,
            "rr": 1 / first if first else 0.0}


def main():
    items = {i["id"]: i for i in load_items("dev")[0]}
    eq = equivalence_map()
    n_anchor = n_dup = 0
    for it in items.values():
        for a in it["minimum_evidence"] + it["wrong_scope_distractors"]:
            n_anchor += 1
            n_dup += bool(expand(a["passage_ids"], eq) - set(a["passage_ids"]))
    out = {"dev_anchors": n_anchor, "dev_anchors_with_identical_duplicates": n_dup}

    # 1) linea base de la Fase 10 (eval_benchmark_v2_retrieval, modo produccion sin LLM)
    base = json.load(open(os.path.join(RES, "retrieval_all.json"), encoding="utf-8"))
    rows = [r for r in base["per_query"] if r["id"] in items and r["expected_behavior"] == "RESPONDER"]
    for mode in ("strict", "equivalent"):
        acc = {"r@5": [], "rr": [], "bundle_complete": [], "bundle_precision": [], "by_lang": {}}
        dist_wo_ev = 0
        for r in rows:
            it = items[r["id"]]
            ev, ds = anchor_sets(it, mode == "strict")
            m = ranking_metrics(r["top10"], ev)
            allowed = set().union(*ev)
            for a in it["mandatory_cross_refs"] + it["exceptions_to_preserve"]:
                allowed |= set(a["passage_ids"]) if mode == "strict" else expand(a["passage_ids"])
            comp = all(s & set(r["bundle"]) for s in ev)
            acc["r@5"].append(m["r@5"])
            acc["rr"].append(m["rr"])
            acc["bundle_complete"].append(comp)
            acc["bundle_precision"].append(sum(p in allowed for p in r["bundle"]) / len(r["bundle"]) if r["bundle"] else 0.0)
            acc["by_lang"].setdefault(r["language"], []).append(m["r@5"])
            D = (set().union(*ds) if ds else set()) - allowed
            if D and (set(r["bundle"]) & D) and not comp:
                dist_wo_ev += 1
        out[f"fase10_baseline_dev_{mode}"] = {
            "n": len(rows), "R@5": round(mean(acc["r@5"]), 3), "MRR": round(mean(acc["rr"]), 3),
            "bundle_complete": round(mean(acc["bundle_complete"]), 3),
            "bundle_precision": round(mean(acc["bundle_precision"]), 3),
            "R@5_by_language": {l: round(mean(v), 3) for l, v in sorted(acc["by_lang"].items())},
            "distractor_delivered_without_evidence": dist_wo_ev}

    # 2) diagnostico R0 vs R1 (diag_retrieval_f11, top-10 registrados)
    p = os.path.join(F11, "diag_retrieval_dev.json")
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        for form in ("DICT", "LLM"):
            rs = [r for r in d["per_query"] if r["form"] == form]
            if not rs:
                continue
            for mode in ("strict", "equivalent"):
                res = {}
                for v in ("r0", "r1"):
                    ms = [ranking_metrics(r[f"{v}_top10"], anchor_sets(items[r["id"]], mode == "strict")[0]) for r in rs]
                    res[v] = {"R@5": round(mean(m["r@5"] for m in ms), 3), "MRR": round(mean(m["rr"] for m in ms), 3),
                              "hit@10": round(mean(m["hit@10"] for m in ms), 3)}
                    res[v]["by_language"] = {l: round(mean(m["r@5"] for m, r in zip(ms, rs) if r["language"] == l), 3)
                                             for l in sorted({r["language"] for r in rs})}
                r0 = [ranking_metrics(r["r0_top10"], anchor_sets(items[r["id"]], mode == "strict")[0])["r@5"] for r in rs]
                r1 = [ranking_metrics(r["r1_top10"], anchor_sets(items[r["id"]], mode == "strict")[0])["r@5"] for r in rs]
                res["r1_gains"] = sorted(r["id"] for r, a, b in zip(rs, r0, r1) if b > a)
                res["r1_losses"] = sorted(r["id"] for r, a, b in zip(rs, r0, r1) if b < a)
                out[f"diag_{form}_{mode}"] = res

    # 3) corridas LLM: evidencia completa en el bundle entregado
    for name in ("llm_shadow_dev_rescored.json", os.path.join("..", "..", "fase11", "llm_dev_f11.json")):
        p = os.path.normpath(os.path.join(RES, name))
        if not os.path.exists(p):
            continue
        rep = json.load(open(p, encoding="utf-8"))
        c = Counter()
        for run in rep["per_run"]:
            for r in run:
                it = items.get(r["id"])
                if not it or it["auto_labels"]["expected_behavior"] != "RESPONDER":
                    continue
                for mode in ("strict", "equivalent"):
                    ev = anchor_sets(it, mode == "strict")[0]
                    c[(mode, all(s & set(r.get("bundle") or []) for s in ev))] += 1
        out[f"llm_bundle_complete::{os.path.basename(p)}"] = {f"{m}_{'completo' if k else 'incompleto'}": v
                                                            for (m, k), v in sorted(c.items())}
    os.makedirs(F11, exist_ok=True)
    with open(os.path.join(F11, "equivalence_dev.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Fase 10.3 - Evaluacion del detector experimental de ambiguedad sobre benchmark_v2.

Clase de referencia (desde auto_labels, PENDING_EXPERT_REVIEW):
  AMBIGUA -> AMBIGUA ; INCOMPLETA -> INCOMPLETA ; RESPONDER -> CLARA ;
  INSUFICIENTE / OOD -> se informan aparte (no entran en precision/recall).
Metricas: precision / recall de "requiere aclaracion", tasa de aclaracion innecesaria en
consultas claras (global y en AMBITO_DISTRACTOR), exactitud INCOMPLETA vs AMBIGUA, cobertura
de las candidatas de referencia (articulos) y latencia.
Ajuste: los parametros solo se exploran con --sweep sobre dev. Regla de seleccion declarada
de antemano: maxima precision con recall >= 0.8; desempate por menor tasa de aclaracion
innecesaria y despues por parametros por defecto. El resultado se guarda en
results/ambiguity_params_dev.json y test_sealed se evalua con --params-from ese archivo.
Proyeccion ES->EN: --projection ada usa ADA._translate_to_technical_english (solo lectura);
--projection none usa solo la consulta.
Uso: python scripts/eval_ambiguity_detector.py --split dev --sweep
     python scripts/eval_ambiguity_detector.py --split test_sealed --allow-test-sealed --params-from data/eval/benchmark_v2/results/ambiguity_params_dev.json
"""
import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from statistics import median

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY"):
    os.environ[k] = ""
OUT = os.path.join(ROOT, "data/eval/benchmark_v2/results/ambiguity_{split}.json")

from experimental.ambiguity_detector import AmbiguityDetector  # noqa: E402
from experimental.benchmark_access import load_items  # noqa: E402

GOLD = {"AMBIGUA": "AMBIGUA", "INCOMPLETA": "INCOMPLETA"}


def gold(it):
    if it["category"] in GOLD:
        return GOLD[it["category"]]
    return "CLARA" if it["auto_labels"]["expected_behavior"] == "RESPONDER" else "NO_RESPONDIBLE"


def nl(s):
    return re.sub(r"\s*\.\s*", ".", s or "").strip()


def evaluate(items, projections, det):
    rows = []
    for it in items:
        t0 = time.perf_counter()
        r = det.analyze(it["text"], projections.get(it["id"]))
        ms = (time.perf_counter() - t0) * 1000
        row = {"id": it["id"], "category": it["category"], "language": it["language"], "gold": gold(it),
               "pred": r["classification"], "dimension": r["dimension"], "clarification": r["clarification_proposal"],
               "candidates": [c["article_label"] for c in r["candidates"]], "latency_ms": round(ms, 2)}
        if it["category"] == "AMBIGUA":
            ref = {nl(c["article"]) for c in it["ambiguity"]["candidates"] if c.get("article")}
            row["reference_candidates"] = sorted(ref)
            row["candidate_coverage"] = round(len(ref & {nl(x) for x in row["candidates"]}) / len(ref), 3) if ref else None
        rows.append(row)
    return rows


def metrics(rows):
    ev = [r for r in rows if r["gold"] != "NO_RESPONDIBLE"]
    need = lambda x: x in ("AMBIGUA", "INCOMPLETA")
    tp = sum(need(r["gold"]) and need(r["pred"]) for r in ev)
    fp = sum(not need(r["gold"]) and need(r["pred"]) for r in ev)
    fn = sum(need(r["gold"]) and not need(r["pred"]) for r in ev)
    clear = [r for r in ev if r["gold"] == "CLARA"]
    scope = [r for r in clear if r["category"] == "AMBITO_DISTRACTOR"]
    flagged = [r for r in ev if need(r["gold"]) and need(r["pred"])]
    amb = [r for r in rows if r["gold"] == "AMBIGUA"]
    cov = [r["candidate_coverage"] for r in amb if r.get("candidate_coverage") is not None and r["pred"] == "AMBIGUA"]
    nr = [r for r in rows if r["gold"] == "NO_RESPONDIBLE"]
    lat = [r["latency_ms"] for r in rows]
    return {
        "n": len(rows), "confusion": {g: dict(Counter(r["pred"] for r in rows if r["gold"] == g))
                                      for g in ("AMBIGUA", "INCOMPLETA", "CLARA", "NO_RESPONDIBLE")},
        "clarification_precision": round(tp / (tp + fp), 3) if tp + fp else None,
        "clarification_recall": round(tp / (tp + fn), 3) if tp + fn else None,
        "unnecessary_clarification_rate": round(sum(need(r["pred"]) for r in clear) / len(clear), 3) if clear else None,
        "unnecessary_clarification_rate_scope_items": round(sum(need(r["pred"]) for r in scope) / len(scope), 3) if scope else None,
        "incomplete_vs_ambiguous_accuracy": round(sum(r["gold"] == r["pred"] for r in flagged) / len(flagged), 3) if flagged else None,
        "ambiguous_candidate_coverage_mean": round(sum(cov) / len(cov), 3) if cov else None,
        "unanswerable_flagged": dict(Counter(r["pred"] for r in nr)),
        "false_clarifications": [r["id"] for r in clear if need(r["pred"])],
        "missed": [r["id"] for r in ev if need(r["gold"]) and not need(r["pred"])],
        "latency_ms": {"p50": round(median(lat), 2), "max": round(max(lat), 2)} if lat else None,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=("dev", "test_sealed", "all"))
    ap.add_argument("--allow-test-sealed", action="store_true")
    ap.add_argument("--projection", default="ada", choices=("ada", "none"))
    ap.add_argument("--params", nargs=3, type=float, metavar=("MIN_INFO", "RATIO", "MAX_DF_DISC"), default=(3.0, 0.9, 0.3))
    ap.add_argument("--params-from", help="JSON con selected_params producido por --sweep sobre dev")
    ap.add_argument("--sweep", action="store_true", help="explora parametros (solo dev)")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    if a.sweep and a.split != "dev":
        print("ERROR: --sweep solo se permite sobre dev", file=sys.stderr)
        return 2
    items, meta = load_items(a.split, a.allow_test_sealed)
    if a.params_from:
        with open(a.params_from, encoding="utf-8") as fh:
            sp = json.load(fh)["selected_params"]
        a.params = (sp["min_info"], sp["ratio"], sp["max_df_discriminative"])
    proj, proj_status = {}, "none"
    if a.projection == "ada":
        try:
            from ada_assistant import ArbitrationDecisionAssistant
            ada = ArbitrationDecisionAssistant()
            proj = {it["id"]: ada._translate_to_technical_english(it["text"]) for it in items}
            proj_status = "ada"
        except Exception as e:
            proj_status = f"NO_DISPONIBLE ({type(e).__name__}: {str(e)[:120]}); se usa solo la consulta"
    t0 = time.perf_counter()
    det = AmbiguityDetector(min_info=a.params[0], ratio=a.params[1], max_df_discriminative=a.params[2])
    build_ms = round((time.perf_counter() - t0) * 1000, 1)
    rows = evaluate(items, proj, det)
    rep = {"benchmark": meta, "projection": proj_status, "params": {"min_info": a.params[0], "ratio": a.params[1], "max_df_discriminative": a.params[2]},
           "index_build_ms": build_ms, "metrics": metrics(rows),
           "by_language": {l: metrics([r for r in rows if r["language"] == l]) for l in sorted({r["language"] for r in rows})},
           "per_query": rows}
    if a.sweep:
        sweep = []
        for md in (2.0, 2.5, 3.0, 4.0, 5.0):
            for ra in (0.6, 0.7, 0.75, 0.8, 0.9):
                for dd in (0.15, 0.3):
                    d = AmbiguityDetector(min_info=md, ratio=ra, max_df_discriminative=dd)
                    m = metrics(evaluate(items, proj, d))
                    sweep.append({"min_info": md, "ratio": ra, "max_df_discriminative": dd,
                                  "precision": m["clarification_precision"] or 0.0, "recall": m["clarification_recall"] or 0.0,
                                  "unnecessary": m["unnecessary_clarification_rate"], "inc_vs_amb": m["incomplete_vs_ambiguous_accuracy"]})
        rep["sweep_dev"] = sweep
        ok = [s for s in sweep if s["recall"] >= 0.8] or sweep
        dflt = (3.0, 0.9, 0.3)
        sel = max(ok, key=lambda s: (s["precision"], -(s["unnecessary"] or 0),
                                     (s["min_info"], s["ratio"], s["max_df_discriminative"]) == dflt))
        rep["selected_params"] = {k: sel[k] for k in ("min_info", "ratio", "max_df_discriminative")}
        rep["selection_rule"] = "max precision con recall>=0.8 (dev); desempate: menor aclaracion innecesaria"
        pp = os.path.join(os.path.dirname(OUT), "ambiguity_params_dev.json")
        os.makedirs(os.path.dirname(pp), exist_ok=True)
        with open(pp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"selected_params": rep["selected_params"], "selection_rule": rep["selection_rule"],
                       "projection": proj_status, "benchmark": meta, "selected_metrics": sel}, fh, ensure_ascii=False, indent=2)
    path = a.out or OUT.format(split=a.split)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    m = rep["metrics"]
    print(f"proyeccion={proj_status} params={rep['params']} n={m['n']}")
    print("confusion:", m["confusion"])
    print(f"precision={m['clarification_precision']} recall={m['clarification_recall']} "
          f"innecesarias={m['unnecessary_clarification_rate']} (ambito: {m['unnecessary_clarification_rate_scope_items']}) "
          f"inc_vs_amb={m['incomplete_vs_ambiguous_accuracy']} cobertura={m['ambiguous_candidate_coverage_mean']}")
    print("falsas aclaraciones:", m["false_clarifications"])
    print("no detectadas:", m["missed"])
    if a.sweep:
        print("parametros seleccionados (dev):", rep["selected_params"])
    print("resultados:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Fase 8 / Etapa 0 - Linea base sobre benchmark_v1 SIN modificar el motor de produccion.

Ejecuta el camino de produccion actual en modo local (sin LLM):
  * Ranking: proj = ADA._translate_to_technical_english(q);
             RRE.retrieve(proj, top_k=10, expand_graph=False, domain_query=q)   (igual que ADA, sin grafo)
  * EvidenceBundle: ADA.analyze_situation(q, top_k=5) con _call_llm desactivado
    -> evidencia + related_passages entregados (opcion A conserva la evidencia en ABSTAIN).
No escribe en el corpus ni en indices. Escribe solo el informe de resultados.

Metricas (localizadores de pasaje; NO miden calidad normativa ni entailment):
  Recall@k : fraccion de anclas de evidencia minima cubiertas en top-k (un ancla se cubre si
             aparece alguno de sus passage_ids aceptables)
  Hit@k    : al menos un ancla cubierta en top-k
  MRR@10, P@1
  Bundle   : precision (entregados pertinentes / entregados), completitud (todas las anclas)
  Excepciones / referencias cruzadas: fraccion de anclas cubiertas en el bundle entregado
  OOD      : falso positivo si retrieve devuelve SUCCESS o el bundle entrega evidencia
  Ambiguas : se informan aparte (no entran en recall)
Uso:  python scripts/eval_benchmark_v1_baseline.py [--split dev|validation|test|all] [--out PATH]
"""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from collections import defaultdict
from statistics import mean, median

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY"):
    os.environ[k] = ""
os.environ.setdefault("IJF_SOR_EDITION", "2026-08")
BENCH = os.path.join(ROOT, "data/eval/benchmark_v1/benchmark_v1.jsonl")
CORPUS = os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json")


def sha_file(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))] if xs else None


def covered(anchor, ids):
    return bool(set(anchor["passage_ids"]) & set(ids))


def score_item(item, ranked, bundle, status, bundle_status):
    anchors = item["minimum_evidence"]
    rel = {pid for a in anchors for pid in a["passage_ids"]}
    allowed = rel | {pid for a in item["mandatory_cross_refs"] + item["exceptions_to_preserve"] for pid in a["passage_ids"]}
    r = {"id": item["id"], "language": item["language"], "category": item["category"], "split": item["split"],
         "retrieve_status": status, "bundle_status": bundle_status, "top10": ranked, "bundle": bundle}
    if item["category"] in ("FUERA_DE_DOMINIO", "AMBIGUA"):
        r["false_positive_retrieve"] = status == "SUCCESS"
        r["false_positive_bundle"] = bool(bundle)
        r["any_candidate_in_top10"] = None
        return r
    first = next((i for i, pid in enumerate(ranked, 1) if pid in rel), None)
    for k in (1, 5, 10):
        r[f"recall@{k}"] = sum(covered(a, ranked[:k]) for a in anchors) / len(anchors) if anchors else 0.0
        r[f"hit@{k}"] = any(covered(a, ranked[:k]) for a in anchors)
    r["rr"] = 1.0 / first if first else 0.0
    r["p@1"] = bool(ranked and ranked[0] in rel)
    r["first_rank"] = first
    r["bundle_size"] = len(bundle)
    r["bundle_precision"] = (sum(pid in allowed for pid in bundle) / len(bundle)) if bundle else 0.0
    r["bundle_complete"] = all(covered(a, bundle) for a in anchors)
    r["exception_recall"] = (sum(covered(a, bundle) for a in item["exceptions_to_preserve"]) / len(item["exceptions_to_preserve"])) if item["exceptions_to_preserve"] else None
    r["crossref_recall"] = (sum(covered(a, bundle) for a in item["mandatory_cross_refs"]) / len(item["mandatory_cross_refs"])) if item["mandatory_cross_refs"] else None
    r["ood_rejected"] = status == "ABSTAIN_OOD"
    return r


def aggregate(rows):
    ans = [r for r in rows if "recall@5" in r]
    neg = [r for r in rows if r["category"] == "FUERA_DE_DOMINIO"]
    amb = [r for r in rows if r["category"] == "AMBIGUA"]
    out = {"n_answerable": len(ans), "n_ood": len(neg), "n_ambiguous": len(amb)}
    if ans:
        for m in ("recall@1", "recall@5", "recall@10", "hit@5", "hit@10", "rr", "p@1", "bundle_precision", "bundle_complete", "bundle_size"):
            out[m if m != "rr" else "mrr@10"] = round(mean(float(r[m]) for r in ans), 3)
        ex = [r["exception_recall"] for r in ans if r["exception_recall"] is not None]
        xr = [r["crossref_recall"] for r in ans if r["crossref_recall"] is not None]
        out["exception_recall"] = round(mean(ex), 3) if ex else None
        out["n_items_exceptions"] = len(ex)
        out["crossref_recall"] = round(mean(xr), 3) if xr else None
        out["n_items_crossrefs"] = len(xr)
        out["answerable_rejected_as_ood"] = [r["id"] for r in ans if r["ood_rejected"]]
        out["answerable_without_hit@10"] = [r["id"] for r in ans if not r["hit@10"]]
    if neg:
        out["ood_false_positive_retrieve"] = [r["id"] for r in neg if r["false_positive_retrieve"]]
        out["ood_false_positive_bundle"] = [r["id"] for r in neg if r["false_positive_bundle"]]
        out["ood_fp_rate_bundle"] = round(sum(r["false_positive_bundle"] for r in neg) / len(neg), 3)
    if amb:
        out["ambiguous_with_bundle"] = sum(bool(r["bundle"]) for r in amb)
    lat_r = [r["latency_retrieve_ms"] for r in rows]
    lat_b = [r["latency_bundle_ms"] for r in rows]
    out["latency_retrieve_ms"] = {"mean": round(mean(lat_r), 1), "p50": round(median(lat_r), 1), "p95": round(pct(lat_r, 0.95), 1)}
    out["latency_bundle_ms"] = {"mean": round(mean(lat_b), 1), "p50": round(median(lat_b), 1), "p95": round(pct(lat_b, 0.95), 1)}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="all", choices=("dev", "validation", "test", "all"))
    ap.add_argument("--out", default=os.path.join(ROOT, "data/eval/benchmark_v1/baseline/baseline_results.json"))
    a = ap.parse_args(argv)
    corpus_before = sha_file(CORPUS)
    items = [json.loads(l) for l in open(BENCH, encoding="utf-8")]
    if a.split != "all":
        items = [i for i in items if i["split"] == a.split]
    from ada_assistant import ArbitrationDecisionAssistant
    ada = ArbitrationDecisionAssistant()
    ada._call_llm = lambda prompt: (None, {})
    rre = ada.rre
    env = {"python": sys.version.split()[0], "platform": platform.platform(),
           "dense_model": "OK" if getattr(rre, "dense_model", None) else "NONE",
           "rre_flags": {f: getattr(rre, f, None) for f in ("enable_ood_detector", "enable_negative_domain_anchors",
                                                             "enable_semantic_ranker", "enable_chunk_stitching", "operating_mode")}}
    try:
        env["git_head"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        env["git_dirty_files"] = len(subprocess.run(["git", "status", "--short"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines())
    except Exception:
        pass
    rows = []
    for it in items:
        q = it["text"]
        t0 = time.perf_counter()
        proj = ada._translate_to_technical_english(q)
        res = rre.retrieve(proj, top_k=10, expand_graph=False, domain_query=q)
        t1 = time.perf_counter()
        st = res.get("status")
        status = "ABSTAIN_OOD" if (st == "ABSTAIN" and res.get("reason") == "OUT_OF_DOMAIN") else st
        ranked = [e["passage_id"] for e in res.get("evidence", [])] if st == "SUCCESS" else []
        t2 = time.perf_counter()
        out = ada.analyze_situation(q, top_k=5)
        t3 = time.perf_counter()
        bundle = list(dict.fromkeys([e.get("passage_id") for e in (out.get("evidence") or []) + (out.get("related_passages") or [])]))
        row = score_item(it, ranked, bundle, status, out.get("status"))
        row["projection"] = proj
        row["latency_retrieve_ms"] = round((t1 - t0) * 1000, 1)
        row["latency_bundle_ms"] = round((t3 - t2) * 1000, 1)
        rows.append(row)
    groups = {"global": rows}
    for key in ("language", "category", "split"):
        for r in rows:
            groups.setdefault(f"{key}={r[key]}", []).append(r)
    summary = {g: aggregate(rs) for g, rs in sorted(groups.items())}
    corpus_after = sha_file(CORPUS)
    report = {"benchmark": "benchmark_v1", "benchmark_sha256": sha_file(BENCH), "split": a.split,
              "mode": "produccion local sin LLM (ranking: retrieve sin grafo top10; bundle: analyze_situation top5)",
              "environment": env, "corpus_sha256_before": corpus_before, "corpus_sha256_after": corpus_after,
              "corpus_unchanged": corpus_before == corpus_after, "summary": summary, "per_query": rows,
              "note": "Metricas por localizadores de pasaje; anotaciones PENDIENTE_REVISION_ARBITRAL; no miden entailment."}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(f"dense_model={env['dense_model']} corpus_unchanged={report['corpus_unchanged']} n={len(rows)}")
    hdr = f"{'grupo':42} {'n':>3} {'R@5':>5} {'R@10':>5} {'MRR':>5} {'P@1':>5} {'bPrec':>5} {'bComp':>5} {'Exc':>5} {'XRef':>5} {'OOD-FP':>6} {'lat ms':>7}"
    print(hdr)
    for g, s in summary.items():
        def f(k, s=s):
            return "  -  " if s.get(k) is None else f"{s[k]:5.2f}"
        fp = s.get("ood_fp_rate_bundle")
        fp_txt = "  -   " if fp is None else f"{fp:6.2f}"
        print(f"{g:42} {s['n_answerable']:>3} {f('recall@5')} {f('recall@10')} {f('mrr@10')} {f('p@1')} "
              f"{f('bundle_precision')} {f('bundle_complete')} {f('exception_recall')} {f('crossref_recall')} "
              f"{fp_txt} {s['latency_bundle_ms']['mean']:7.1f}")
    g = summary["global"]
    print("Respondibles rechazadas como OOD:", g.get("answerable_rejected_as_ood"))
    print("Respondibles sin acierto en top10:", g.get("answerable_without_hit@10"))
    print("OOD falsos positivos (bundle):", g.get("ood_false_positive_bundle"), "(retrieve):", g.get("ood_false_positive_retrieve"))
    print("Ambiguas con bundle entregado:", g.get("ambiguous_with_bundle"), "/", g.get("n_ambiguous"))
    print("Resultados:", a.out)
    return 0 if report["corpus_unchanged"] else 3


if __name__ == "__main__":
    sys.exit(main())

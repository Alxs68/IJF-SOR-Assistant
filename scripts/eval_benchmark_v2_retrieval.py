#!/usr/bin/env python3
"""Fase 10.1 - Metricas de recuperacion y de AMBITO sobre benchmark_v2 (sin LLM).

Ejecuta el camino productivo en modo local sin modelo generativo (igual que la linea base
de Fase 8): proyeccion ADA -> RRE.retrieve(top10, sin grafo) y ADA.analyze_situation(top5)
con _call_llm desactivado. No modifica ADA/RRE, ni el corpus, ni indices.

Metricas (localizadores de pasaje; NO miden entailment):
  recall@k, hit@k, MRR@10, P@1                         (items RESPONDER)
  pertinencia del bundle  = entregados dentro de evidencia/xref/excepcion / entregados
  suficiencia estructural = todas las anclas minimas entregadas
  cobertura excepciones / referencias cruzadas en el bundle
  AMBITO (items con wrong_scope_distractors separables a nivel de pasaje):
     scope_rank_error        : un distractor aparece en top10 antes que la primera evidencia
     distractor_delivered    : el bundle entrega un pasaje distractor
     distractor_without_ev   : el bundle entrega distractor y NO la evidencia completa
     inseparable             : distractor en el mismo pasaje que la evidencia (solo medible a nivel de cita)
  no respondibles: OOD (retrieve SUCCESS = FP), INSUFICIENTE / AMBIGUA / INCOMPLETA (bundle entregado)
Uso: python scripts/eval_benchmark_v2_retrieval.py [--split dev|test_sealed|all] [--allow-test-sealed]
"""
import argparse
import hashlib
import json
import os
import sys
import time
from statistics import mean, median

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY"):
    os.environ[k] = ""
os.environ.setdefault("IJF_SOR_EDITION", "2026-08")
CORPUS = os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json")
OUT = os.path.join(ROOT, "data/eval/benchmark_v2/results/retrieval_{split}.json")

from experimental.benchmark_access import expand, load_items  # noqa: E402

STRICT = False  # --strict: metrica de la Fase 10 (sin equivalencia de pasajes duplicados)


def ids_of(a):
    return set(a["passage_ids"]) if STRICT else expand(a["passage_ids"])


def sha_file(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))] if xs else None


def cov(a, ids):
    return bool(ids_of(a) & set(ids))


def score(item, ranked, bundle, status):
    beh = item["auto_labels"]["expected_behavior"]
    r = {"id": item["id"], "category": item["category"], "language": item["language"], "split": item["split"],
         "expected_behavior": beh, "retrieve_status": status, "top10": ranked, "bundle": bundle}
    if beh != "RESPONDER":
        r["bundle_delivered"] = bool(bundle)
        r["retrieve_success"] = status == "SUCCESS"
        return r
    ev = item["minimum_evidence"]
    E = {p for a in ev for p in ids_of(a)}
    allowed = E | {p for a in item["mandatory_cross_refs"] + item["exceptions_to_preserve"] for p in ids_of(a)}
    first = next((i for i, p in enumerate(ranked, 1) if p in E), None)
    for k in (1, 5, 10):
        r[f"recall@{k}"] = sum(cov(a, ranked[:k]) for a in ev) / len(ev)
        r[f"hit@{k}"] = any(cov(a, ranked[:k]) for a in ev)
    r["rr"] = 1.0 / first if first else 0.0
    r["p@1"] = bool(ranked and ranked[0] in E)
    r["bundle_precision"] = sum(p in allowed for p in bundle) / len(bundle) if bundle else 0.0
    r["bundle_complete"] = all(cov(a, bundle) for a in ev)
    exc, xr = item["exceptions_to_preserve"], item["mandatory_cross_refs"]
    r["exception_recall"] = sum(cov(a, bundle) for a in exc) / len(exc) if exc else None
    r["crossref_recall"] = sum(cov(a, bundle) for a in xr) / len(xr) if xr else None
    D = {p for a in item["wrong_scope_distractors"] for p in ids_of(a)} - E
    r["has_distractors"] = bool(item["wrong_scope_distractors"])
    r["distractor_separable"] = bool(D)
    if D:
        fd = next((i for i, p in enumerate(ranked, 1) if p in D), None)
        r["scope_rank_error"] = fd is not None and (first is None or fd < first)
        r["distractor_delivered"] = bool(set(bundle) & D)
        r["distractor_without_ev"] = r["distractor_delivered"] and not r["bundle_complete"]
    return r


def agg(rows):
    ans = [r for r in rows if "recall@5" in r]
    o = {"n": len(rows), "n_answerable": len(ans)}
    if ans:
        for m in ("recall@1", "recall@5", "recall@10", "hit@5", "rr", "p@1", "bundle_precision", "bundle_complete"):
            o["mrr@10" if m == "rr" else m] = round(mean(float(r[m]) for r in ans), 3)
        for m in ("exception_recall", "crossref_recall"):
            xs = [r[m] for r in ans if r[m] is not None]
            o[m] = round(mean(xs), 3) if xs else None
            o[f"n_{m}"] = len(xs)
        sc = [r for r in ans if r.get("distractor_separable")]
        o["scope"] = {
            "items_with_distractors": sum(r["has_distractors"] for r in ans),
            "separable_at_passage_level": len(sc),
            "inseparable_at_passage_level": sum(r["has_distractors"] and not r["distractor_separable"] for r in ans),
            "scope_rank_error": sum(r["scope_rank_error"] for r in sc),
            "distractor_delivered": sum(r["distractor_delivered"] for r in sc),
            "distractor_without_evidence": sum(r["distractor_without_ev"] for r in sc),
            "ids_distractor_without_evidence": [r["id"] for r in sc if r["distractor_without_ev"]],
        }
        o["answerable_without_hit@10"] = [r["id"] for r in ans if not r["hit@10"]]
    neg = [r for r in rows if "recall@5" not in r]
    for beh in ("ABSTENER_FUERA_DE_DOMINIO", "ABSTENER_INSUFICIENCIA", "SOLICITAR_ACLARACION"):
        xs = [r for r in neg if r["expected_behavior"] == beh]
        if xs:
            o[beh] = {"n": len(xs), "retrieve_success": sum(r["retrieve_success"] for r in xs),
                      "bundle_delivered": sum(r["bundle_delivered"] for r in xs)}
    lat = [r["latency_ms"] for r in rows]
    o["latency_ms"] = {"p50": round(median(lat), 1), "p95": round(pct(lat, 0.95), 1)}
    return o


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=("dev", "test_sealed", "all"))
    ap.add_argument("--allow-test-sealed", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--strict", action="store_true", help="sin equivalencia de pasajes de igual pagina y texto (Fase 10)")
    a = ap.parse_args(argv)
    global STRICT
    STRICT = a.strict
    items, meta = load_items(a.split, a.allow_test_sealed)
    before = sha_file(CORPUS)
    from ada_assistant import ArbitrationDecisionAssistant
    ada = ArbitrationDecisionAssistant()
    ada._call_llm = lambda prompt: (None, {})
    rows = []
    for it in items:
        q = it["text"]
        t0 = time.perf_counter()
        proj = ada._translate_to_technical_english(q)
        res = ada.rre.retrieve(proj, top_k=10, expand_graph=False, domain_query=q)
        st = res.get("status")
        ranked = [e["passage_id"] for e in res.get("evidence", [])] if st == "SUCCESS" else []
        out = ada.analyze_situation(q, top_k=5)
        bundle = list(dict.fromkeys(e.get("passage_id") for e in (out.get("evidence") or []) + (out.get("related_passages") or [])))
        row = score(it, ranked, bundle, st)
        row["projection"] = proj
        row["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        rows.append(row)
    groups = {"global": rows}
    for key in ("category", "language"):
        for r in rows:
            groups.setdefault(f"{key}={r[key]}", []).append(r)
    summary = {g: agg(rs) for g, rs in sorted(groups.items())}
    after = sha_file(CORPUS)
    rep = {"benchmark": meta, "mode": "produccion local sin LLM", "corpus_unchanged": before == after,
           "corpus_sha256": after, "summary": summary, "per_query": rows,
           "equivalence": "STRICT (Fase 10)" if STRICT else "pasajes de igual pagina y texto identico = misma evidencia (Fase 11A)",
           "note": "localizadores de pasaje; etiquetas PENDING_EXPERT_REVIEW; no mide entailment"}
    path = a.out or OUT.format(split=a.split)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    print(f"{'grupo':34} {'n':>3} {'R@5':>5} {'MRR':>5} {'bPrec':>5} {'bComp':>5} {'Exc':>5} {'XRef':>5} {'sep':>3} {'rkErr':>5} {'dDel':>4} {'dNoEv':>5}")
    for g, s in summary.items():
        f = lambda k: "  -  " if s.get(k) is None else f"{s[k]:5.2f}"
        sc = s.get("scope") or {}
        print(f"{g:34} {s['n_answerable']:>3} {f('recall@5')} {f('mrr@10')} {f('bundle_precision')} {f('bundle_complete')} "
              f"{f('exception_recall')} {f('crossref_recall')} {sc.get('separable_at_passage_level', '-'):>3} "
              f"{sc.get('scope_rank_error', '-'):>5} {sc.get('distractor_delivered', '-'):>4} {sc.get('distractor_without_evidence', '-'):>5}")
    g = summary["global"]
    for beh in ("ABSTENER_FUERA_DE_DOMINIO", "ABSTENER_INSUFICIENCIA", "SOLICITAR_ACLARACION"):
        print(beh, g.get(beh))
    print("corpus_unchanged=", rep["corpus_unchanged"], " resultados:", path)
    return 0 if rep["corpus_unchanged"] else 3


if __name__ == "__main__":
    sys.exit(main())

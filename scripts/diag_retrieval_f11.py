#!/usr/bin/env python3
"""Fase 11A/11B - Diagnostico de recuperacion sobre DEV (sin llamadas al LLM).

Para cada consulta respondible de dev y cada forma de consulta:
  DICT : proyeccion por diccionario de ADA (camino sin LLM)
  LLM  : traduccion ES->EN que produjo el LLM en la corrida registrada (--llm-results); se
         REPRODUCE desde el registro, no se vuelve a llamar al modelo. Si no hubo traduccion se usa
         la consulta tal cual (es lo que hace ADA).
compara:
  R0 = rre.retrieve (produccion) y R1 = fusion RRF sin reglas tematicas fijas (experimental),
y atribuye el fallo de cada consulta:
  OK_TOP5 | DESPLAZADO_POR_REGLAS_FIJAS | EN_CANAL_FUERA_DE_TOP5 | ABSTENCION_DE_RECUPERACION | AUSENTE_DE_CANALES
Tambien mide duplicacion de pagina en el top-10, posicion de distractores de ambito y
el bundle realmente entregado al LLM (de la corrida registrada).
Uso: python scripts/diag_retrieval_f11.py --llm-results data/eval/fase11/llm_dev_r1.json
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
    os.environ[k] = ""          # garantiza el camino por diccionario y ninguna llamada externa
os.environ.setdefault("IJF_SOR_EDITION", "2026-08")
CORPUS = os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json")
OUT = os.path.join(ROOT, "data/eval/fase11/diag_retrieval_dev.json")

from experimental.benchmark_access import expand, load_items  # noqa: E402
from experimental.scope_retriever import channel_ranks, clean_fusion  # noqa: E402


def sha_file(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def first_rank(ranked, targets):
    return next((i for i, p in enumerate(ranked, 1) if p in targets), None)


def attribute(r0, r1, ch, status):
    if r0 is not None and r0 <= 5:
        return "OK_TOP5"
    if r1 is not None and r1 <= 5:
        return "DESPLAZADO_POR_REGLAS_FIJAS"
    if status != "SUCCESS":
        return "ABSTENCION_DE_RECUPERACION"
    if (ch["sparse"] or 99) <= 25 or (ch["dense"] or 99) <= 25:
        return "EN_CANAL_FUERA_DE_TOP5"
    return "AUSENTE_DE_CANALES"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm-results", help="informe de eval_llm_shadow (dev) con traducciones registradas")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    items, meta = load_items("dev")
    before = sha_file(CORPUS)
    trans, bundles = {}, {}
    if a.llm_results:
        rep = json.load(open(a.llm_results, encoding="utf-8"))
        for row in rep["per_run"][0]:
            trans[row["id"]] = row.get("translation")
            bundles[row["id"]] = row.get("bundle") or []
    from ada_assistant import ArbitrationDecisionAssistant
    ada = ArbitrationDecisionAssistant()
    ada._call_llm = lambda prompt: (None, {})
    rre = ada.rre
    page_of = {pid: p.get("pdf_page_index") for pid, p in rre.passages_by_id.items()}
    rows = []
    for it in items:
        if it["auto_labels"]["expected_behavior"] != "RESPONDER":
            continue
        # equivalencia: pasajes de la misma pagina con texto identico (ver benchmark_access.equivalence_map)
        E = expand({p for x in it["minimum_evidence"] for p in x["passage_ids"]})
        D = expand({p for x in it["wrong_scope_distractors"] for p in x["passage_ids"]}) - E
        forms = {"DICT": ada._translate_to_technical_english(it["text"])}
        if a.llm_results:
            forms["LLM"] = (trans.get(it["id"]) or "").strip() or it["text"]
        for form, q in forms.items():
            t0 = time.perf_counter()
            res = rre.retrieve(q, top_k=10, expand_graph=False, domain_query=it["text"])
            lat0 = (time.perf_counter() - t0) * 1000
            st = res.get("status")
            r0 = [e["passage_id"] for e in res.get("evidence", [])] if st == "SUCCESS" else []
            t1 = time.perf_counter()
            r1 = clean_fusion(rre, q, top_k=10)["ranked"]
            lat1 = (time.perf_counter() - t1) * 1000
            ch = channel_ranks(rre, q, E)
            f0, f1 = first_rank(r0, E), first_rank(r1, E)
            pages0 = [page_of.get(p) for p in r0]
            row = {"id": it["id"], "language": it["language"], "category": it["category"], "form": form, "query_used": q,
                   "retrieve_status": st, "r0_first": f0, "r1_first": f1, "channels": ch,
                   "attribution": attribute(f0, f1, ch, st),
                   "r0_distinct_pages_top10": len(set(pages0)), "r0_top10": r0, "r1_top10": r1,
                   "lat_r0_ms": round(lat0, 1), "lat_r1_ms": round(lat1, 1)}
            if D:
                row["r0_distractor_first"] = first_rank(r0, D)
                row["r1_distractor_first"] = first_rank(r1, D)
            if form == "LLM" and it["id"] in bundles:
                b = bundles[it["id"]]
                row["llm_bundle_has_all_evidence"] = all(expand(x["passage_ids"]) & set(b) for x in it["minimum_evidence"])
                row["llm_bundle_has_distractor"] = bool(set(b) & D)
            rows.append(row)

    def agg(rs):
        if not rs:
            return None
        out = {"n": len(rs)}
        for v in ("r0", "r1"):
            fr = [r[f"{v}_first"] for r in rs]
            out[f"{v}_R@5"] = round(mean(1.0 if (f and f <= 5) else 0.0 for f in fr), 3)
            out[f"{v}_R@10"] = round(mean(1.0 if f else 0.0 for f in fr), 3)
            out[f"{v}_MRR"] = round(mean(1.0 / f if f else 0.0 for f in fr), 3)
        out["attribution"] = dict(Counter(r["attribution"] for r in rs))
        out["r1_gains_vs_r0"] = sorted(r["id"] for r in rs if (r["r1_first"] or 99) <= 5 < (r["r0_first"] or 99))
        out["r1_losses_vs_r0"] = sorted(r["id"] for r in rs if (r["r0_first"] or 99) <= 5 < (r["r1_first"] or 99))
        sc = [r for r in rs if "r0_distractor_first" in r]
        if sc:
            out["distractor_above_evidence_r0"] = sum((r["r0_distractor_first"] or 99) < (r["r0_first"] or 99) for r in sc)
            out["distractor_above_evidence_r1"] = sum((r["r1_distractor_first"] or 99) < (r["r1_first"] or 99) for r in sc)
            out["n_scope_separable"] = len(sc)
        out["mean_distinct_pages_top10_r0"] = round(mean(r["r0_distinct_pages_top10"] for r in rs), 2)
        lb = [r for r in rs if "llm_bundle_has_all_evidence" in r]
        if lb:
            out["llm_bundle_complete"] = sum(r["llm_bundle_has_all_evidence"] for r in lb)
            out["llm_bundle_with_distractor"] = sum(r["llm_bundle_has_distractor"] for r in lb)
        out["lat_ms_mean"] = {"r0": round(mean(r["lat_r0_ms"] for r in rs), 1), "r1": round(mean(r["lat_r1_ms"] for r in rs), 1)}
        return out
    groups = defaultdict(list)
    for r in rows:
        groups[f"{r['form']}|global"].append(r)
        groups[f"{r['form']}|lang={r['language']}"].append(r)
        groups[f"{r['form']}|cat={r['category']}"].append(r)
    summary = {g: agg(rs) for g, rs in sorted(groups.items())}
    rep = {"benchmark": meta, "split": "dev", "llm_results": a.llm_results, "corpus_unchanged": before == sha_file(CORPUS),
           "summary": summary, "per_query": rows,
           "note": "Diagnostico; localizadores de pasaje; etiquetas PENDING_EXPERT_REVIEW; sin llamadas al LLM."}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    print(f"{'grupo':34} {'n':>3} {'R0@5':>5} {'R1@5':>5} {'R0mrr':>5} {'R1mrr':>5}  atribucion")
    for g, s in summary.items():
        print(f"{g:34} {s['n']:>3} {s['r0_R@5']:5.2f} {s['r1_R@5']:5.2f} {s['r0_MRR']:5.2f} {s['r1_MRR']:5.2f}  {s['attribution']}")
    for f in ("DICT", "LLM"):
        g = summary.get(f"{f}|global")
        if g:
            print(f, "ganancias R1:", g["r1_gains_vs_r0"], "perdidas R1:", g["r1_losses_vs_r0"],
                  "distractor>evid R0/R1:", g.get("distractor_above_evidence_r0"), g.get("distractor_above_evidence_r1"),
                  "bundle LLM completo:", g.get("llm_bundle_complete"))
    print("corpus_unchanged=", rep["corpus_unchanged"], "resultados:", a.out)
    return 0 if rep["corpus_unchanged"] else 3


if __name__ == "__main__":
    sys.exit(main())

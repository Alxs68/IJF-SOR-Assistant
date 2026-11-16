"""Fase 8 (ampliacion SHADOW) - Evaluacion de recuperacion auxiliar y separacion de autoridad.

No modifica ADA/RRE ni datos. Escribe solo el informe de resultados.

Modo --sidecar-only (solo biblioteca estandar; ejecutable en la VM):
  MultisourceRetriever.search(q, top_k=3, min_score=2.0) con la consulta original
  (ADA ademas reintenta con la proyeccion EN; ese reintento solo se mide en modo completo).
  * benchmark_shadow_v1: Hit@3 / MRR auxiliar, recuperacion de fragmentos prohibidos como base,
    falsos positivos en SIN_EVIDENCIA_SUFICIENTE.
  * benchmark_v1 (combinado): ruido auxiliar = consultas SOR/OOD/ambiguas que reciben fragmentos SHADOW.
Modo completo (Windows, motor real, sin LLM real):
  * offline: ADA.analyze_situation -> evidencia primaria, supplementary_context.
  * sonda A (StubLLM cita SOLO los chunk_id SHADOW entregados en supplementary_context y su etiqueta [COMPLEMENTO-n]): debe quedar ABSTAIN y sin
    citas SHADOW (SHADOW no puede ser fundamento autonomo).
  * sonda B (StubLLM cita el primer pasaje SOR primario entregado): las citas solo pueden ser SOR y el
    contexto complementario debe ser decisive=False. Una SUCCESS en SOLO_AUXILIAR/SIN_EVIDENCIA indica
    que la validacion de citas no verifica pertinencia (no es entailment); se informa, no se corrige.
Uso: python scripts/eval_shadow_v1.py [--sidecar-only] [--out PATH]
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from statistics import mean

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "tests")]
for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY"):
    os.environ[k] = ""
os.environ.setdefault("IJF_SOR_EDITION", "2026-08")
SH_BENCH = os.path.join(ROOT, "data/eval/benchmark_shadow_v1/benchmark_shadow_v1.jsonl")
V1_BENCH = os.path.join(ROOT, "data/eval/benchmark_v1/benchmark_v1.jsonl")
SHADOW = os.path.join(ROOT, "data/corpus_multisource/processed/multisource_passages.json")
SOR = os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json")
CHK = re.compile(r"CHK-[A-Z0-9\-]+")


def shaf(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")]


def sidecar_eval(retriever, items, v1):
    rows = []
    for it in items:
        t0 = time.perf_counter()
        res = retriever.search(it["text"], top_k=3, min_score=2.0)
        lat = (time.perf_counter() - t0) * 1000
        got = [m["chunk_id"] for m in res.get("matches", [])]
        exp = [a["chunk_id"] for a in it["expected_auxiliary"]]
        forb = [a["chunk_id"] for a in it["forbidden_as_basis"]]
        first = next((i for i, c in enumerate(got, 1) if c in exp), None)
        rows.append({"id": it["id"], "language": it["language"], "evidence_class": it["evidence_class"], "matches": got,
                     "aux_hit@3": bool(first) if exp else None, "aux_rr": (1 / first if first else 0.0) if exp else None,
                     "forbidden_retrieved": bool(set(got) & set(forb)) if forb else None,
                     "any_match": bool(got), "latency_ms": round(lat, 2)})
    noise = []
    for it in v1:
        res = retriever.search(it["text"], top_k=3, min_score=2.0)
        noise.append({"id": it["id"], "category": it["category"], "matches": [m["chunk_id"] for m in res.get("matches", [])]})
    return rows, noise


def summarize_sidecar(rows, noise):
    def by(cls):
        return [r for r in rows if r["evidence_class"] == cls]
    with_aux = [r for r in rows if r["aux_hit@3"] is not None]
    s = {"n": len(rows),
         "aux_hit@3": round(mean(r["aux_hit@3"] for r in with_aux), 3), "aux_mrr@3": round(mean(r["aux_rr"] for r in with_aux), 3),
         "aux_hit@3_by_class": {c: round(mean(r["aux_hit@3"] for r in by(c) if r["aux_hit@3"] is not None), 3)
                                for c in ("PRIMARIA_CON_AUXILIAR", "SOLO_AUXILIAR_SIN_PRIMARIA") if by(c)},
         "aux_hit@3_by_language": {l: round(mean(r["aux_hit@3"] for r in with_aux if r["language"] == l), 3) for l in ("es", "en")},
         "forbidden_retrieved_rate": round(mean(r["forbidden_retrieved"] for r in by("AUXILIAR_NO_DEBE_FUNDAMENTAR")), 3),
         "sin_evidencia_false_positive": [r["id"] for r in by("SIN_EVIDENCIA_SUFICIENTE") if r["any_match"]],
         "aux_misses": [r["id"] for r in with_aux if not r["aux_hit@3"]],
         "latency_ms_mean": round(mean(r["latency_ms"] for r in rows), 2)}
    cats = Counter(n["category"] for n in noise)
    hit = Counter(n["category"] for n in noise if n["matches"])
    s["combined_benchmark_v1_sidecar_noise"] = {c: f"{hit.get(c, 0)}/{cats[c]}" for c in sorted(cats)}
    s["combined_noise_ids"] = {n["id"]: n["matches"] for n in noise if n["matches"]}
    return s


def full_eval(items):
    from ada_assistant import ArbitrationDecisionAssistant
    from _ada_contract_helpers import StubLLM, json_answer, supplementary_block, citation_ids
    ada = ArbitrationDecisionAssistant()
    catalog_tier = {d: (m.authority.name if hasattr(m.authority, "name") else str(m.authority))
                    for d, m in ada.doc_validator.catalog.items()}
    rows = []
    for it in items:
        q = it["text"]
        ada._call_llm = lambda prompt: (None, {})
        out = ada.analyze_situation(q, top_k=5)
        ev_ids = [e.get("passage_id") for e in (out.get("evidence") or []) + (out.get("related_passages") or [])]
        supp = out.get("supplementary_context") or []
        supp_ids = [s["chunk_id"] for s in supp]
        exp_aux = [a["chunk_id"] for a in it["expected_auxiliary"]]
        prim_ok = [bool(set(a["passage_ids"]) & set(ev_ids)) for a in it["expected_primary"]]
        # Sonda A: el "modelo" cita SOLO los fragmentos SHADOW realmente entregados (IDs reales de
        # supplementary_context y sus etiquetas [COMPLEMENTO-n]); el prompt no expone chunk_id (AUD-04.3).
        shadow_cites = supp_ids[:2]
        stub_a = StubLLM(analysis=lambda prompt, delivered, ids=shadow_cites: json_answer(
            (ids or []) + re.findall(r"COMPLEMENTO-\d+", supplementary_block(prompt))[:1]))
        ada._call_llm = stub_a
        out_a = ada.analyze_situation(q, top_k=5)
        shadow_in_block = bool(shadow_cites) and bool(stub_a.analysis_prompts) and \
            "COMPLEMENTO-" in supplementary_block(stub_a.analysis_prompts[-1])
        # Sonda B: el "modelo" cita el primer pasaje SOR entregado
        stub_b = StubLLM(analysis=lambda prompt, delivered: json_answer(delivered[:1]))
        ada._call_llm = stub_b
        out_b = ada.analyze_situation(q, top_k=5)
        cites_b = citation_ids(out_b)
        supp_b = out_b.get("supplementary_context") or []
        rows.append({
            "id": it["id"], "language": it["language"], "evidence_class": it["evidence_class"],
            "offline_status": out.get("status"), "primary_ids": ev_ids, "supplementary_ids": supp_ids,
            "primary_anchor_recall": (sum(prim_ok) / len(prim_ok)) if prim_ok else None,
            "aux_in_supplementary_context": (bool(set(exp_aux) & set(supp_ids)) if exp_aux else None),
            "forbidden_in_supplementary_context": bool(set(a["chunk_id"] for a in it["forbidden_as_basis"]) & set(supp_ids)) if it["forbidden_as_basis"] else None,
            "AUTH1_no_shadow_in_primary": not any(CHK.match(str(i or "")) for i in ev_ids),
            "AUTH2_supplementary_non_decisive": all(s.get("decisive") is False for s in supp + supp_b),
            "AUTH3_supplementary_not_tier1": all("TIER_1" not in str(catalog_tier.get(s.get("document_id"), "UNREGISTERED")) and s.get("document_id") in catalog_tier for s in supp + supp_b),
            "probeA_shadow_in_supplementary_block": shadow_in_block, "probeA_cited_shadow_ids": shadow_cites,
            "probeA_llm_called": bool(stub_a.analysis_prompts),
            "probeA_status": out_a.get("status"), "probeA_citations": citation_ids(out_a),
            "AUTH4_shadow_only_citation_rejected": out_a.get("status") != "SUCCESS" and not any(CHK.match(str(c or "")) for c in citation_ids(out_a)),
            "probeB_status": out_b.get("status"), "probeB_citations": cites_b,
            "AUTH5_citations_only_sor": not any(CHK.match(str(c or "")) for c in cites_b),
            "probeB_success_without_primary_basis": out_b.get("status") == "SUCCESS" and it["evidence_class"] in ("SOLO_AUXILIAR_SIN_PRIMARIA", "SIN_EVIDENCIA_SUFICIENTE"),
        })
    auth = {k: f"{sum(r[k] for r in rows)}/{len(rows)}" for k in ("AUTH1_no_shadow_in_primary", "AUTH2_supplementary_non_decisive",
                                                                   "AUTH3_supplementary_not_tier1", "AUTH4_shadow_only_citation_rejected",
                                                                   "AUTH5_citations_only_sor")}
    pr = [r["primary_anchor_recall"] for r in rows if r["primary_anchor_recall"] is not None]
    ax = [r["aux_in_supplementary_context"] for r in rows if r["aux_in_supplementary_context"] is not None]
    summary = {"authority_checks": auth,
               "authority_all_pass": all(r[k] for r in rows for k in ("AUTH1_no_shadow_in_primary", "AUTH2_supplementary_non_decisive",
                                                                       "AUTH3_supplementary_not_tier1", "AUTH4_shadow_only_citation_rejected",
                                                                       "AUTH5_citations_only_sor")),
               "primary_anchor_recall_bundle": round(mean(pr), 3) if pr else None,
               "aux_recall_in_supplementary_context": round(mean(ax), 3) if ax else None,
               "forbidden_in_supplementary_context": [r["id"] for r in rows if r["forbidden_in_supplementary_context"]],
               "probeA_with_shadow_delivered": sum(r["probeA_shadow_in_supplementary_block"] for r in rows),
               "probeA_effective_ids": [r["id"] for r in rows if r["probeA_shadow_in_supplementary_block"]],
               "probeA_effective_rejected": f"{sum(r['AUTH4_shadow_only_citation_rejected'] for r in rows if r['probeA_shadow_in_supplementary_block'])}/{sum(r['probeA_shadow_in_supplementary_block'] for r in rows)}",
               "probeB_success_without_primary_basis": [r["id"] for r in rows if r["probeB_success_without_primary_basis"]],
               "offline_status": dict(Counter(r["offline_status"] for r in rows))}
    return rows, summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sidecar-only", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    out = a.out or os.path.join(ROOT, "data/eval/benchmark_shadow_v1/results",
                                "shadow_sidecar_only.json" if a.sidecar_only else "shadow_full.json")
    before = {p: shaf(p) for p in (SOR, SHADOW, SH_BENCH, V1_BENCH)}
    items, v1 = load(SH_BENCH), load(V1_BENCH)
    from multisource_retriever import MultisourceRetriever
    retriever = MultisourceRetriever(passages_path=SHADOW)
    rows, noise = sidecar_eval(retriever, items, v1)
    report = {"benchmark": "benchmark_shadow_v1", "mode": "sidecar-only" if a.sidecar_only else "completo",
              "sidecar_eligible_chunks": len(retriever.passages), "sidecar_summary": summarize_sidecar(rows, noise),
              "sidecar_per_query": rows}
    if not a.sidecar_only:
        frows, fsum = full_eval(items)
        report["full_summary"], report["full_per_query"] = fsum, frows
    after = {p: shaf(p) for p in before}
    report["inputs_unchanged"] = before == after
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps({"sidecar_summary": report["sidecar_summary"], "full_summary": report.get("full_summary"),
                      "inputs_unchanged": report["inputs_unchanged"]}, ensure_ascii=False, indent=1))
    print("Resultados:", out)
    return 0 if report["inputs_unchanged"] else 3


if __name__ == "__main__":
    sys.exit(main())

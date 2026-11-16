"""Fase 9 / Etapa 6 - Simulacion fuera de linea de opciones para reducir el ruido SHADOW.

No modifica ADA, RRE, el sidecar ni documentos. Reutiliza:
  * bundles primarios reales: data/eval/benchmark_v1/baseline/baseline_results.json (per_query.bundle)
    y data/eval/benchmark_shadow_v1/results/shadow_full.json (full_per_query.primary_ids)
  * MultisourceRetriever (consulta original; ADA ademas reintenta con la proyeccion EN: no simulado)
  * anclaje articulo: shadow_units_v1 (unit_to_related_sor_units) -> article_units_v1 -> passage_ids
Opciones:
  N0 actual (min_score 2.0) | N1a min_score 3.0 | N1b min_score 4.0
  N2 anclaje: el fragmento solo se entrega si sus articulos SOR relacionados estan en el bundle primario
  N3 N2 + min_score 3.0
Uso: python scripts/eval_shadow_noise_options.py
"""
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, "src")]
from multisource_retriever import MultisourceRetriever  # noqa: E402

J = lambda p: json.load(open(os.path.join(ROOT, p), encoding="utf-8"))
L = lambda p: [json.loads(l) for l in open(os.path.join(ROOT, p), encoding="utf-8")]


def main():
    base = {r["id"]: r for r in J("data/eval/benchmark_v1/baseline/baseline_results.json")["per_query"]}
    shfull = {r["id"]: r for r in J("data/eval/benchmark_shadow_v1/results/shadow_full.json")["full_per_query"]}
    v1 = L("data/eval/benchmark_v1/benchmark_v1.jsonl")
    sh = L("data/eval/benchmark_shadow_v1/benchmark_shadow_v1.jsonl")
    au = {u["unit_id"]: u for u in L("data/derived/article_units_v1/units.jsonl")}
    rel = J("data/derived/shadow_units_v1/traceability_map.json")["unit_to_related_sor_units"]
    chunk_pids = {uid.replace("SHU1-", ""): {p for a in units for p in au[a]["original_passage_ids"]} for uid, units in rel.items()}
    r = MultisourceRetriever(passages_path=os.path.join(ROOT, "data/corpus_multisource/processed/multisource_passages.json"))
    options = {"N0_actual": (2.0, False), "N1a_min3": (3.0, False), "N1b_min4": (4.0, False),
               "N2_anclaje_articulo": (2.0, True), "N3_anclaje_min3": (3.0, True)}

    def deliver(q, primary, ms, anchor):
        got = [m["chunk_id"] for m in r.search(q, top_k=3, min_score=ms).get("matches", [])]
        return [c for c in got if not anchor or (chunk_pids.get(c, set()) & set(primary))]
    out = {}
    for name, (ms, anchor) in options.items():
        noise = Counter()
        tot = Counter(i["category"] for i in v1)
        for i in v1:
            if deliver(i["text"], base[i["id"]]["bundle"], ms, anchor):
                noise[i["category"]] += 1
        res = {"v1_with_shadow": f"{sum(noise.values())}/{len(v1)}",
               "v1_by_category": {c: f"{noise[c]}/{tot[c]}" for c in sorted(tot)}}
        cls = {}
        for i in sh:
            got = deliver(i["text"], shfull[i["id"]]["primary_ids"], ms, anchor)
            exp = {a["chunk_id"] for a in i["expected_auxiliary"]}
            forb = {a["chunk_id"] for a in i["forbidden_as_basis"]}
            c = cls.setdefault(i["evidence_class"], {"n": 0, "aux_hit": 0, "forbidden_delivered": 0, "any": 0})
            c["n"] += 1
            c["aux_hit"] += bool(exp & set(got))
            c["forbidden_delivered"] += bool(forb & set(got))
            c["any"] += bool(got)
        res["shadow_by_class"] = cls
        out[name] = res
    os.makedirs(os.path.join(ROOT, "data/eval/decision_integrity_v1"), exist_ok=True)
    with open(os.path.join(ROOT, "data/eval/decision_integrity_v1/shadow_noise_options.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

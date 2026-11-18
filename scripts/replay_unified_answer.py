#!/usr/bin/env python3
"""Respuesta unica y validacion integral - reproduccion OFFLINE sobre respuestas DEV ya almacenadas.

No llama al LLM, no modifica benchmarks ni capturas: lee las entradas exactas del DIG guardadas en las
evaluaciones previas (A/B, Fase 11, integracion R3) y compara, para la MISMA respuesta generada:
  ANTERIOR : DIG actual (DIG-1.3+NUM-v2+FIX-v3), que solo verifica summary/normative_basis/conditions.
  INTEGRAL : ADA_UNIFIED_ANSWER=1 sin poda (DIG verifica tambien extended_analysis y limitations).
  NUEVO    : INTEGRAL + poda de frases accesorias sin respaldo y nueva evaluacion completa.

Limitacion: las respuestas se generaron con el contrato anterior; el efecto del nuevo contrato del prompt
solo puede medirse con una evaluacion en vivo (scripts/eval_ab_dev.py --variants U0,U1).

Uso: python scripts/replay_unified_answer.py   (escribe data/eval/unified_answer/replay_unified.json)
"""
import copy
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DIG_NUMBER_NORMALIZATION", "v2")
os.environ.setdefault("DIG_V3", "1")
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "scripts")]

import decision_integrity as D  # noqa: E402
import post_ab_reanalysis as P  # noqa: E402
import eval_llm_shadow as E  # noqa: E402

CORPUS = os.path.join(ROOT, "data", "processed", "rebuild_2026_08_corrected", "passages_candidate.json")
BENCH = os.path.join(ROOT, "data", "eval", "benchmark_v2", "benchmark_v2.jsonl")
DEV = os.path.join(ROOT, "data", "eval", "benchmark_v2", "splits", "dev.jsonl")
SOURCES = [("data/eval/dig_v3/ab_dev.json", "AB"), ("data/eval/fase11/llm_dev_f11_capture.json", "F11"),
           ("data/eval/integracion_r3_dig/llm_dev_original.json", "INT-orig"),
           ("data/eval/integracion_r3_dig/llm_dev_experimental.json", "INT-exp")]
OUT = os.path.join(ROOT, "data", "eval", "unified_answer", "replay_unified.json")


def load_rows():
    rows = []
    for rel, tag in SOURCES:
        d = json.load(open(os.path.join(ROOT, rel), encoding="utf-8"))
        if "per_variant" in d:
            for v, rs in d["per_variant"].items():
                rows += [dict(r, src=f"{tag}-{v}") for r in rs]
        else:
            for run in d["per_run"]:
                rows += [dict(r, src=tag) for r in run]
    return rows


def evaluate(gate, di, answer=None):
    return gate.evaluate(answer or di["answer"], di["query"], di["search_query_en"], di["evidence"], di["related"],
                         di["supplementary_texts"], instruction_text=di.get("instruction_text", ""))


def main():
    ps = json.load(open(CORPUS, encoding="utf-8"))
    page_text = {}
    for p in ps:
        page_text.setdefault(p["pdf_page_index"], p["text_original"])
    items = {json.loads(l)["id"]: json.loads(l) for l in open(BENCH, encoding="utf-8") if l.strip()}
    dev = {json.loads(l)["id"] for l in open(DEV, encoding="utf-8") if l.strip()}
    gate = D.DecisionIntegrityGate(ps)
    per_case, outcomes, changes = [], {"ANTERIOR": Counter(), "INTEGRAL": Counter(), "NUEVO": Counter()}, []
    pruned_total = Counter()
    for r in load_rows():
        di = r.get("dig_input")
        if not di or r["id"] not in dev:
            continue
        it = items[r["id"]]
        D.FIX_ALL_VISIBLE_FIELDS = False
        old = evaluate(gate, di)
        D.FIX_ALL_VISIBLE_FIELDS = True
        full = evaluate(gate, di)
        new, pruned_answer, removed = full, di["answer"], []
        if full["decision"] != "PERMITIR" and set(full["failed_checks"]) <= {"DIG-06_CIFRAS_RESPALDADAS",
                                                                             "DIG-07_TERMINOS_RESPALDADOS"}:
            cand, removed = gate.prune_unsupported(di["answer"], di["query"], di["search_query_en"])
            if removed:
                re_eval = evaluate(gate, di, cand)
                if re_eval["decision"] == "PERMITIR":
                    new, pruned_answer = re_eval, cand
                else:
                    removed = []
        D.FIX_ALL_VISIBLE_FIELDS = False
        res = {}
        for name, dec, ans in (("ANTERIOR", old, di["answer"]), ("INTEGRAL", full, di["answer"]),
                               ("NUEVO", new, pruned_answer)):
            row = copy.deepcopy(r)
            row["llm_json"] = D.parse_answer(ans) or row.get("llm_json")
            sc = P.rescore(row, it, page_text, dec)
            res[name] = {"decision": dec["decision"], "failed": dec["failed_checks"], "outcome": sc["outcome"]}
            outcomes[name][sc["outcome"]] += 1
        for x in removed:
            pruned_total[x["field"]] += 1
        case = {"src": r["src"], "id": r["id"], "expected": it["auto_labels"]["expected_behavior"], **res,
                "pruned": removed}
        per_case.append(case)
        if len({res[k]["outcome"] for k in res}) > 1:
            changes.append({k: case[k] for k in ("src", "id", "expected")} |
                           {k: (res[k]["outcome"], res[k]["failed"]) for k in res} |
                           {"frases_retiradas": [f"{x['field']}: {x['sentence'][:90]}" for x in removed]})
    report = {"note": __doc__.split("\n\n")[1], "dig_version_new": D.DIG_BASE_VERSION + "+NUM-v2+FIX-v3+ALL",
              "rows": len(per_case), "outcomes": {k: dict(v) for k, v in outcomes.items()},
              "accepted_wrong": {k: sum(n for o, n in v.items() if o.startswith("RESPONDIDA_DEBIA")
                                        or o in ("ACEPTADA_SIN_EVIDENCIA_ESPERADA", "ACEPTADA_ERROR_DE_AMBITO"))
                                 for k, v in outcomes.items()},
              "pruned_sentences_by_field": dict(pruned_total), "changes": changes, "per_case": per_case}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(report, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: report[k] for k in ("rows", "outcomes", "accepted_wrong", "pruned_sentences_by_field")},
                     ensure_ascii=False, indent=1))
    for c in changes:
        print(json.dumps(c, ensure_ascii=False))


if __name__ == "__main__":
    main()

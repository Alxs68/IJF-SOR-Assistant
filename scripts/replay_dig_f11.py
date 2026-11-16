#!/usr/bin/env python3
"""Fase 11A - Reejecucion OFFLINE del DIG de produccion y de la variante experimental de cifras.

Entradas: informes de eval_llm_shadow sobre DEV.
  * modo CAPTURADO   (filas con dig_input, corrida con --capture-dig): entradas EXACTAS del DIG.
  * modo RECONSTRUIDO (corridas sin captura): respuesta = llm_json registrado, evidencia y
    relacionados = textos del corpus segun bundle_detail, sin documentacion SHADOW. Solo indicativo.
Pasos:
  1. Reproducibilidad: DIG de produccion (sin cambios) sobre las entradas -> decision y reglas
     fallidas identicas a las registradas?
  2. Variante: el mismo DIG con numbers_in_v2 (experimental.dig_variants.dig_variant) -> que
     decisiones cambian y por que. Cada caso desbloqueado se acompana de sus citas y de si la cita
     corresponde al ancla esperada; NO se considera correcto por desbloquearse.
  3. Adversarial: sobre cada respuesta capturada se inyectan cifras inventadas (7 estrategias) y se
     comprueba que DIG-06 las detecta con el DIG base y con la variante.
Nada se escribe fuera de data/eval/fase11/. El DIG de produccion no se modifica.
Uso: python scripts/replay_dig_f11.py data/eval/fase11/llm_dev_f11_capture.json [mas informes]
"""
import argparse
import copy
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "scripts")]
CORPUS = os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json")
BENCH = os.path.join(ROOT, "data/eval/benchmark_v2/benchmark_v2.jsonl")
OUT = os.path.join(ROOT, "data/eval/fase11/dig_replay_dev.json")

import decision_integrity as D  # noqa: E402
from experimental.dig_variants import dig_variant, numbers_in_v2  # noqa: E402


def load_inputs(paths, ptext, pmeta):
    cases = []
    for path in paths:
        if not os.path.exists(path):
            print("AVISO: no existe", path)
            continue
        rep = json.load(open(path, encoding="utf-8"))
        for run in rep["per_run"]:
            for r in run:
                if r.get("dig_input"):
                    di = r["dig_input"]
                    cases.append({"mode": "CAPTURADO", "row": r, "src": os.path.basename(path), **di})
                elif r.get("dig_decision") and r.get("llm_json"):
                    ev = [dict(pmeta[b["passage_id"]], text_original=ptext[b["passage_id"]])
                          for b in r.get("bundle_detail") or [] if b["lane"] == "evidence" and b["passage_id"] in ptext]
                    rel = [dict(pmeta[b["passage_id"]], text_original=ptext[b["passage_id"]])
                           for b in r.get("bundle_detail") or [] if b["lane"] == "related" and b["passage_id"] in ptext]
                    cases.append({"mode": "RECONSTRUIDO", "row": r, "src": os.path.basename(path),
                                  "answer": r["llm_json"], "query": None, "search_query_en": r.get("translation"),
                                  "evidence": ev, "related": rel, "supplementary_texts": [],
                                  "result": {"decision": r["dig_decision"], "failed_checks": r.get("dig_failed_checks") or []}})
    return cases


def run_gate(gate, c, variant=False):
    ans = c["answer"]
    if variant:
        with dig_variant():
            return gate.evaluate(ans, c["query"], c["search_query_en"], c["evidence"], c["related"], c["supplementary_texts"])
    return gate.evaluate(ans, c["query"], c["search_query_en"], c["evidence"], c["related"], c["supplementary_texts"])


def as_obj(answer):
    o = D.parse_answer(answer)
    return copy.deepcopy(o) if isinstance(o, dict) else None


def fresh_number(c, start=37):
    pool = " ".join(p.get("text_original") or "" for p in c["evidence"] + c["related"])
    o = as_obj(c["answer"]) or {}
    pool += " " + json.dumps(o, ensure_ascii=False) + " " + (c["query"] or "")
    have = D.numbers_in(pool) | numbers_in_v2(pool)
    n = start
    while str(n) in have:
        n += 1
    return n


ATTACKS = {
    "A1_SUSTITUIR_CIFRA_RESPALDADA": None,  # se construye aparte
    "A2_CIFRA_NUEVA": "The applicable limit is {N} kg.",
    "A3_CIFRA_EN_LISTA": "\n1. Athletes have {N} minutes to report.\n2. The rule applies to all events.",
    "A4_DECIMAL_TRAS_CAPITULO": "{N}.5 Kilograms are permitted for this category.",
    "A4b_ETIQUETA_REAL_CON_OTRO_TITULO": "6.3 Kilograms are permitted.",
    "A5_FECHA_DISTINTA_DE_LA_EDICION": "Registrations close on {D} August 2026.",
    "A6_ID_SOR_UNICODE_MAS_CIFRA": "(SOR‑2026‑08‑P079‑S093) The time limit is {N} minutes.",
}


def build_attacks(c):
    o = as_obj(c["answer"])
    if o is None:
        return []
    N = fresh_number(c)
    Dd = 20 if "20" not in D.numbers_in(json.dumps(o)) else 21
    out = []
    quotes = " ".join(str(q.get("quote") or "") for q in o.get("evidence_quotes") or [] if isinstance(q, dict))
    summ = str(o.get("summary") or "")
    supported = sorted(D.numbers_in(summ) & D.numbers_in(quotes), key=len, reverse=True)
    for name, tpl in ATTACKS.items():
        a = copy.deepcopy(o)
        if name == "A1_SUSTITUIR_CIFRA_RESPALDADA":
            hit = next((n for n in supported if re.search(rf"(?<![\d.,]){re.escape(n)}(?![\d])", summ)), None)
            if hit is None:
                continue
            a["summary"] = re.sub(rf"(?<![\d.,]){re.escape(hit)}(?![\d])", str(N), summ, count=1)
            target = str(N)
        else:
            txt = tpl.format(N=N, D=Dd)
            a["summary"] = (summ + " " + txt).strip()
            target = "6.3" if name.startswith("A4b") else (str(Dd) if name.startswith("A5") else
                                                           (f"{N}.5" if name.startswith("A4_") else str(N)))
        out.append((name, a, target))
    return out


def detected(res, target):
    """La cifra inyectada aparece en la lista de cifras sin respaldo de DIG-06."""
    det = next((ch for ch in res.get("checks", []) if ch["code"].startswith("DIG-06")), None)
    return bool(det and not det["passed"] and f"'{target}'" in det["detail"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("reports", nargs="+")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    ps = json.load(open(CORPUS, encoding="utf-8"))
    ptext = {p["passage_id"]: p["text_original"] for p in ps}
    pmeta = {p["passage_id"]: {"passage_id": p["passage_id"], "pdf_page_index": p["pdf_page_index"],
                               "page": p["pdf_page_index"], "article_id": p.get("article_id")} for p in ps}
    items = {json.loads(l)["id"]: json.loads(l) for l in open(BENCH, encoding="utf-8") if l.strip()}
    gate = D.DecisionIntegrityGate(ps)
    from eval_llm_shadow import span_hit
    page_text = {}
    for p in ps:
        page_text.setdefault(p["pdf_page_index"], p["text_original"])
    cases = load_inputs(a.reports, ptext, pmeta)
    rows, adv = [], Counter()
    adv_cases = []
    for c in cases:
        r = c["row"]
        it = items.get(r["id"], {})
        if c["query"] is None:
            c["query"] = it.get("text", "")
        base = run_gate(gate, c)
        var = run_gate(gate, c, variant=True)
        rec = c["result"]
        same = base["decision"] == rec["decision"] and set(base["failed_checks"]) == set(rec["failed_checks"] or [])
        o = as_obj(c["answer"]) or {}
        quotes = [q for q in o.get("evidence_quotes") or [] if isinstance(q, dict)]
        hit_ev = any(span_hit(page_text.get(x["page"]), q.get("quote"), x) for x in it.get("minimum_evidence", []) for q in quotes)
        hit_dis = any(span_hit(page_text.get(x["page"]), q.get("quote"), x) for x in it.get("wrong_scope_distractors", []) for q in quotes)
        d6b = next((ch["detail"] for ch in base["checks"] if ch["code"].startswith("DIG-06")), "")
        d6v = next((ch["detail"] for ch in var["checks"] if ch["code"].startswith("DIG-06")), "")
        rows.append({
            "id": r["id"], "run": r.get("run"), "src": c["src"], "mode": c["mode"], "category": it.get("category"),
            "expected_behavior": it.get("auto_labels", {}).get("expected_behavior"),
            "recorded": {"decision": rec["decision"], "failed": sorted(rec["failed_checks"] or [])},
            "base": {"decision": base["decision"], "failed": sorted(base["failed_checks"])},
            "variant": {"decision": var["decision"], "failed": sorted(var["failed_checks"])},
            "reproduced_exactly": same, "changed_by_variant": base["decision"] != var["decision"] or
            set(base["failed_checks"]) != set(var["failed_checks"]),
            "dig06_base": d6b, "dig06_variant": d6v,
            "quotes_hit_expected_evidence": hit_ev, "quotes_hit_scope_distractor": hit_dis,
            "quotes": [(q.get("passage_id"), str(q.get("quote") or "")[:220]) for q in quotes],
            "claims": {k: str(o.get(k) or "")[:600] for k in ("summary", "normative_basis", "conditions_and_exceptions")},
        })
        if c["mode"] == "CAPTURADO":
            for name, att, target in build_attacks(c):
                ac = dict(c, answer=att)
                rb, rv = run_gate(gate, ac), run_gate(gate, ac, variant=True)
                db, dv = detected(rb, target), detected(rv, target)
                adv[(name, "base", db)] += 1
                adv[(name, "variant", dv)] += 1
                adv_cases.append({"id": r["id"], "run": r.get("run"), "attack": name, "target": target,
                                  "base_detected": db, "variant_detected": dv,
                                  "base_decision": rb["decision"], "variant_decision": rv["decision"]})
    cap = [x for x in rows if x["mode"] == "CAPTURADO"]
    rec_ = [x for x in rows if x["mode"] == "RECONSTRUIDO"]
    unblocked = [x for x in rows if x["base"]["decision"] == "ABSTENER" and x["variant"]["decision"] == "PERMITIR"]
    newly_blocked = [x for x in rows if x["base"]["decision"] == "PERMITIR" and x["variant"]["decision"] == "ABSTENER"]
    attacks = {}
    for (name, which, ok), n in adv.items():
        attacks.setdefault(name, {}).setdefault(which, {"detected": 0, "missed": 0})["detected" if ok else "missed"] += n
    summary = {
        "cases": len(rows), "captured": len(cap), "reconstructed": len(rec_),
        "reproducibility_captured": f"{sum(x['reproduced_exactly'] for x in cap)}/{len(cap)}",
        "reproducibility_reconstructed": f"{sum(x['reproduced_exactly'] for x in rec_)}/{len(rec_)}",
        "variant_changed": sum(x["changed_by_variant"] for x in rows),
        "unblocked_by_variant": [{"id": x["id"], "run": x["run"], "mode": x["mode"], "hit_expected": x["quotes_hit_expected_evidence"],
                                  "hit_distractor": x["quotes_hit_scope_distractor"], "dig06_base": x["dig06_base"]}
                                 for x in unblocked],
        "newly_blocked_by_variant": [{"id": x["id"], "run": x["run"]} for x in newly_blocked],
        "failed_rule_counts_base": dict(Counter(f for x in rows for f in x["base"]["failed"])),
        "failed_rule_counts_variant": dict(Counter(f for x in rows for f in x["variant"]["failed"])),
        "adversarial": attacks,
        "adversarial_variant_misses": [x for x in adv_cases if x["base_detected"] and not x["variant_detected"]],
        "adversarial_base_misses": [x for x in adv_cases if not x["base_detected"]],
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"summary": summary, "cases": rows, "adversarial_cases": adv_cases,
                   "note": "Reejecucion offline; DIG de produccion sin cambios; la variante solo se aplica dentro de este proceso."},
                  fh, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=1)[:6000])
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Reejecucion OFFLINE: DIG actual vs DIG con las correcciones v3 (FIX_PERTINENCE_HEADING,
FIX_HYPHEN_TERMS, FIX_DIG08_INSTRUCTIONS) sobre entradas CAPTURADAS del DIG.

Informa: decisiones que cambian (con citas y si la cita toca la evidencia esperada / un distractor)
y ataques adversariales (cifras inventadas, termino distintivo inventado, fuga de cifra SHADOW):
toda deteccion del DIG actual debe mantenerse con v3. No escribe fuera de --out.
Uso: python scripts/replay_dig_v3.py <informes con dig_input> [--out ruta]
"""
import argparse
import copy
import json
import os
import sys
from collections import Counter
from contextlib import contextmanager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "scripts")]
import decision_integrity as D  # noqa: E402
import replay_dig_f11 as R  # noqa: E402

FLAGS = ("FIX_PERTINENCE_HEADING", "FIX_HYPHEN_TERMS", "FIX_DIG08_INSTRUCTIONS")


@contextmanager
def v3(on=True, only=None):
    old = {f: getattr(D, f) for f in FLAGS}
    try:
        for f in FLAGS:
            setattr(D, f, bool(on) and (only is None or f == only))
        yield
    finally:
        for f, v in old.items():
            setattr(D, f, v)


def ev(gate, c, answer=None, supp=None):
    return gate.evaluate(c["answer"] if answer is None else answer, c["query"], c["search_query_en"],
                         c["evidence"], c["related"], c["supplementary_texts"] if supp is None else supp,
                         instruction_text=c.get("instruction_text", ""))


def extra_attacks(gate, c):
    o = R.as_obj(c["answer"])
    if o is None:
        return []
    out = []
    # T1: termino distintivo del SOR ausente de citas y consulta (DIG-07)
    qt = " ".join(str(q.get("quote") or "") for q in o.get("evidence_quotes") or [] if isinstance(q, dict))
    have = set(D.re.findall(r"[a-z][a-z\-]{3,}", D.strip_accents(D.norm(qt + " " + (c["query"] or "") + " " +
                                                                         (c["search_query_en"] or "")))))
    cand = sorted(t for t in gate.distinctive if t not in have and "-" not in t and len(t) >= 5)
    if cand:
        a = copy.deepcopy(o)
        a["summary"] = (str(a.get("summary") or "") + f" Se aplica {cand[0]}.").strip()
        out.append(("T1_TERMINO_DISTINTIVO_INVENTADO", a, None, "DIG-07"))
    # T2: cifra presente solo en un texto SHADOW sintetico (DIG-08)
    N = R.fresh_number(c, start=73)
    a = copy.deepcopy(o)
    a["extended_analysis"] = (str(a.get("extended_analysis") or "") + f" El plazo es de {N} dias.").strip()
    out.append(("T2_CIFRA_SOLO_SHADOW", a, [f"Documento complementario: el plazo es de {N} dias."], "DIG-08"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("reports", nargs="+")
    ap.add_argument("--out", default=os.path.join(ROOT, "data/eval/dig_v3/replay_dig_v3.json"))
    a = ap.parse_args(argv)
    ps = json.load(open(R.CORPUS, encoding="utf-8"))
    ptext = {p["passage_id"]: p["text_original"] for p in ps}
    pmeta = {p["passage_id"]: {"passage_id": p["passage_id"], "pdf_page_index": p["pdf_page_index"],
                               "page": p["pdf_page_index"], "article_id": p.get("article_id")} for p in ps}
    items = {json.loads(l)["id"]: json.loads(l) for l in open(R.BENCH, encoding="utf-8") if l.strip()}
    from eval_llm_shadow import span_hit
    page_text = {}
    for p in ps:
        page_text.setdefault(p["pdf_page_index"], p["text_original"])
    gate = D.DecisionIntegrityGate(ps)
    cases = [c for c in R.load_inputs(a.reports, ptext, pmeta) if c["mode"] == "CAPTURADO"]
    rows, adv, adv_fail = [], Counter(), []
    for c in cases:
        it = items.get(c["row"]["id"], {})
        if c["query"] is None:
            c["query"] = it.get("text", "")
        with v3(False):
            base = ev(gate, c)
        with v3(True):
            new = ev(gate, c)
        per_fix = {}
        for f in FLAGS:
            with v3(True, only=f):
                per_fix[f] = ev(gate, c)["decision"]
        o = R.as_obj(c["answer"]) or {}
        quotes = [q for q in o.get("evidence_quotes") or [] if isinstance(q, dict)]
        hit_ev = any(span_hit(page_text.get(x["page"]), q.get("quote"), x) for x in it.get("minimum_evidence", []) for q in quotes)
        hit_dis = any(span_hit(page_text.get(x["page"]), q.get("quote"), x) for x in it.get("wrong_scope_distractors", []) for q in quotes)
        rows.append({"id": c["row"]["id"], "src": c["src"], "category": it.get("category"),
                     "expected_behavior": it.get("auto_labels", {}).get("expected_behavior"),
                     "base": {"decision": base["decision"], "failed": base["failed_checks"]},
                     "v3": {"decision": new["decision"], "failed": new["failed_checks"]},
                     "per_fix_decision": per_fix, "changed": base["decision"] != new["decision"],
                     "quotes_hit_expected_evidence": hit_ev, "quotes_hit_scope_distractor": hit_dis,
                     "quotes": [(q.get("passage_id"), str(q.get("quote") or "")[:200]) for q in quotes]})
        attacks = [(n, x, t, "DIG-06") for n, x, t in R.build_attacks(c)] + extra_attacks(gate, c)
        for att in attacks:
            name, ans, target_or_supp, rule = att
            supp = target_or_supp if isinstance(target_or_supp, list) else None
            with v3(False):
                rb = ev(gate, c, ans, supp)
            with v3(True):
                rv = ev(gate, c, ans, supp)
            if rule == "DIG-06":
                db, dv = R.detected(rb, target_or_supp), R.detected(rv, target_or_supp)
            else:
                db = rule in " ".join(rb["failed_checks"])
                dv = rule in " ".join(rv["failed_checks"])
            adv[(name, "base", db)] += 1
            adv[(name, "v3", dv)] += 1
            if db and not dv or (rb["decision"] == "ABSTENER" and rv["decision"] == "PERMITIR"):
                adv_fail.append({"id": c["row"]["id"], "attack": name, "base_detected": db, "v3_detected": dv,
                                 "base_decision": rb["decision"], "v3_decision": rv["decision"]})
    changed = [r for r in rows if r["changed"]]
    summ = {"cases": len(rows), "changed": len(changed),
            "unblocked": [{k: r[k] for k in ("id", "src", "category", "expected_behavior", "base", "per_fix_decision",
                                             "quotes_hit_expected_evidence", "quotes_hit_scope_distractor")}
                          for r in changed if r["v3"]["decision"] == "PERMITIR"],
            "newly_blocked": [r["id"] for r in changed if r["v3"]["decision"] == "ABSTENER"],
            "failed_rules_base": dict(Counter(x for r in rows for x in r["base"]["failed"])),
            "failed_rules_v3": dict(Counter(x for r in rows for x in r["v3"]["failed"])),
            "adversarial": {f"{n}|{m}|{'detectado' if d else 'NO_detectado'}": k for (n, m, d), k in sorted(adv.items())},
            "adversarial_regressions_v3": adv_fail}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump({"summary": summ, "rows": rows}, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(summ, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

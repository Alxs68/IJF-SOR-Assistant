#!/usr/bin/env python3
"""Reanalisis OFFLINE (sin llamadas al LLM) tras las correcciones posteriores a la evaluacion A/B.

Sobre las respuestas y entradas del DIG ya capturadas en data/eval/dig_v3/ab_dev.json:
  * ANTES   = DIG v3 de la evaluacion A/B (H, G, I, B) + evaluador anterior (resultados registrados).
  * EVAL    = mismas decisiones del DIG + evaluador nuevo (normalizacion del DIG) -> efecto del evaluador.
  * DESPUES = DIG con las correcciones nuevas (U: variantes tipograficas; X: DIG-08 entre idiomas)
              + evaluador nuevo -> efecto total.
Ademas: cambios de decision del DIG en TODAS las capturas disponibles y ataques adversariales (cifras,
termino inventado, fuga SHADOW numerica y lexica, cita alterada con caracteres tipograficos): ninguna
deteccion del DIG anterior puede perderse. Resultado: data/eval/dig_v3/post_ab_reanalysis.json
Limite: una decision que pasa a PERMITIR se cuenta como SUCCESS (el validador de citas ya habia pasado,
por eso existe la entrada del DIG); el formateo posterior de ADA no se reejecuta.
"""
import copy
import json
import os
import sys
from collections import Counter, defaultdict
from contextlib import contextmanager

os.environ.setdefault("DIG_NUMBER_NORMALIZATION", "v2")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "scripts")]
import decision_integrity as D  # noqa: E402
import eval_llm_shadow as E  # noqa: E402
import replay_dig_f11 as R  # noqa: E402

OLD = {"FIX_PERTINENCE_HEADING": True, "FIX_HYPHEN_TERMS": True, "FIX_DIG08_INSTRUCTIONS": True,
       "FIX_LINEBREAK_HYPHEN": True, "FIX_UNICODE_TYPO": False, "FIX_DIG08_CROSSLANG": False}
NEW = dict(OLD, FIX_UNICODE_TYPO=True, FIX_DIG08_CROSSLANG=True)
AB = os.path.join(ROOT, "data/eval/dig_v3/ab_dev.json")
OTHER = ["data/eval/fase11/llm_dev_f11_capture.json", "data/eval/integracion_r3_dig/llm_dev_original.json",
         "data/eval/integracion_r3_dig/llm_dev_experimental.json"]
OUT = os.path.join(ROOT, "data/eval/dig_v3/post_ab_reanalysis.json")


@contextmanager
def cfg(flags):
    old = {k: getattr(D, k) for k in flags}
    try:
        for k, v in flags.items():
            setattr(D, k, v)
        yield
    finally:
        for k, v in old.items():
            setattr(D, k, v)


def ev(gate, di, answer=None, supp=None):
    return gate.evaluate(di["answer"] if answer is None else answer, di["query"], di["search_query_en"], di["evidence"],
                         di["related"], di["supplementary_texts"] if supp is None else supp,
                         instruction_text=di.get("instruction_text", ""))


def rescore(row, item, page_text, new_decision=None):
    r = copy.deepcopy(row)
    if new_decision is not None and r.get("dig_input"):
        r["status"] = "SUCCESS" if new_decision["decision"] == "PERMITIR" else "ABSTAIN"
        r["dig_failed_checks"] = new_decision["failed_checks"]
    lj = r.get("llm_json") or {}
    quotes = [q for q in (lj.get("evidence_quotes") or []) if isinstance(q, dict)] or r.get("quotes") or []
    hits = lambda anchors: [any(E.span_hit(page_text.get(a["page"]), q.get("quote"), a) for q in quotes) for a in anchors]
    ev_, dis = item["minimum_evidence"], item["wrong_scope_distractors"]
    eh, dh = hits(ev_), hits(dis)
    r.update(quotes_hit_evidence=any(eh) if ev_ else None, quotes_hit_all_evidence=all(eh) if ev_ else None,
             quotes_hit_distractor=any(dh) if dis else None)
    r["scope_error"] = bool(dis and any(dh) and not any(eh))
    exc, xr = item["exceptions_to_preserve"], item["mandatory_cross_refs"]
    r["exceptions_quoted"] = (sum(hits(exc)) / len(exc)) if exc else None
    r["crossrefs_quoted"] = (sum(hits(xr)) / len(xr)) if xr else None
    if r["status"] == "SUCCESS":
        fields = {k: str(lj.get(k) or "") for k in ("summary", "normative_basis", "conditions_and_exceptions")}
        r["numbers_not_in_quotes"] = E.unsupported_numbers(fields, quotes, D.numbers_in)
        allowed = E.expand({p for a in ev_ + exc + xr for p in a["passage_ids"]})
        cited = [q.get("passage_id") for q in quotes]
        r["citations_outside_expected"] = [c for c in cited if c not in allowed] if allowed else cited
    E.classify(r, item["auto_labels"]["expected_behavior"])
    return r


def brief(s):
    return {"aceptadas_respondibles": s["answerable"]["success"],
            "con_evidencia_esperada": s["answerable"]["success_with_expected_evidence"],
            "falsos_bloqueos": s["outcomes"].get("ABSTENCION_CON_CITA_CORRECTA", 0),
            "incorrectas_aceptadas": sum(s["control_false_positives"].values()),
            "detalle_incorrectas": s["control_false_positives"],
            "abstenciones_legitimas": s["legitimate_abstentions"], "sin_generacion": s["outcomes"].get("ABSTENCION_SIN_GENERACION", 0),
            "dig_reglas_fallidas": s["dig_failed_checks"]}


def main():
    ps = json.load(open(R.CORPUS, encoding="utf-8"))
    page_text = {}
    for p in ps:
        page_text.setdefault(p["pdf_page_index"], p["text_original"])
    items = {json.loads(l)["id"]: json.loads(l) for l in open(R.BENCH, encoding="utf-8") if l.strip()}
    gate = D.DecisionIntegrityGate(ps)
    ab = json.load(open(AB, encoding="utf-8"))
    out = {"configuracion": {"antes": OLD, "despues": NEW}, "variantes": {}, "por_proveedor": {}, "cambios_decision_ab": []}
    for v in ("A", "B"):
        rows = ab["per_variant"][v]
        before = rows
        with cfg(OLD):
            evalnew = [rescore(r, items[r["id"]], page_text) for r in rows]
        with cfg(NEW):
            after = []
            for r in rows:
                nd = ev(gate, r["dig_input"]) if r.get("dig_input") else None
                after.append(rescore(r, items[r["id"]], page_text, nd))
                if nd and (nd["decision"], sorted(nd["failed_checks"])) != (r["dig_input"]["result"]["decision"],
                                                                         sorted(r["dig_input"]["result"]["failed_checks"] or [])):
                    out["cambios_decision_ab"].append({"variante": v, "id": r["id"], "proveedor": r["provider"],
                                                       "antes": r["dig_input"]["result"], "despues": {
                                                           "decision": nd["decision"], "failed_checks": nd["failed_checks"]}})
        out["variantes"][v] = {"antes": brief(E.summarize([before])), "evaluador_nuevo": brief(E.summarize([evalnew])),
                               "despues": brief(E.summarize([after]))}
        out["variantes"][v]["cambios_de_resultado"] = [
            {"id": b["id"], "proveedor": b["provider"], "antes": b["outcome"], "evaluador_nuevo": m["outcome"], "despues": a["outcome"]}
            for b, m, a in zip(before, evalnew, after) if len({b["outcome"], m["outcome"], a["outcome"]}) > 1]
        prov = defaultdict(Counter)
        for b, a in zip(before, after):
            prov[str(b["provider"])][f"{b['outcome']} -> {a['outcome']}"] += 1
        out["por_proveedor"][v] = {k: dict(c) for k, c in prov.items()}
    # mismas preguntas respondidas por Gemini en A y B (comparacion limpia)
    A = {r["id"]: r for r in ab["per_variant"]["A"]}
    B = {r["id"]: r for r in ab["per_variant"]["B"]}
    same = [i for i in A if A[i]["provider"] == "Gemini" and B[i]["provider"] == "Gemini"]
    out["pares_mismo_proveedor_gemini"] = len(same)
    # decisiones en el resto de capturas
    cases = R.load_inputs([os.path.join(ROOT, f) for f in OTHER], {p["passage_id"]: p["text_original"] for p in ps},
                          {p["passage_id"]: {"passage_id": p["passage_id"], "pdf_page_index": p["pdf_page_index"],
                                             "page": p["pdf_page_index"], "article_id": p.get("article_id")} for p in ps})
    cases = [c for c in cases if c["mode"] == "CAPTURADO"]
    abc = [{"row": dict(r, id=r["id"]), "src": "ab_dev.json", **r["dig_input"]} for v in ("A", "B")
           for r in ab["per_variant"][v] if r.get("dig_input")]
    changes, adv, regress = [], Counter(), []
    for c in cases + abc:
        if c.get("query") is None:
            c["query"] = items.get(c["row"]["id"], {}).get("text", "")
        with cfg(OLD):
            o = ev(gate, c)
        with cfg(NEW):
            n = ev(gate, c)
        if (o["decision"], sorted(o["failed_checks"])) != (n["decision"], sorted(n["failed_checks"])):
            changes.append({"src": c["src"], "id": c["row"]["id"], "antes": [o["decision"], o["failed_checks"]],
                            "despues": [n["decision"], n["failed_checks"]]})
        obj = R.as_obj(c["answer"])
        if obj is None:
            continue
        attacks = [(nme, a, t, "DIG-06", None) for nme, a, t in R.build_attacks(c)]
        qs = [q for q in obj.get("evidence_quotes") or [] if isinstance(q, dict) and len(str(q.get("quote") or "").split()) >= 8]
        if qs:   # T3: cita con guion tipografico Y una palabra cambiada -> DIG-03 debe seguir rechazandola
            a = copy.deepcopy(obj)
            w = str(qs[0]["quote"]).split()
            w[len(w) // 2] = w[len(w) // 2] + "x"
            for q in a["evidence_quotes"]:
                if q is not None and q.get("quote") == qs[0]["quote"]:
                    q["quote"] = " ".join(w).replace("-", "‑")
            attacks.append(("T3_CITA_ALTERADA_CON_TIPOGRAFIA", a, None, "DIG-03", None))
        N = R.fresh_number(c, start=73)
        a = copy.deepcopy(obj)
        a["extended_analysis"] = (str(a.get("extended_analysis") or "") + f" El plazo es de {N} dias.").strip()
        attacks.append(("T2_CIFRA_SOLO_SHADOW", a, None, "DIG-08", [f"Documento complementario: el plazo es de {N} dias."]))
        a = copy.deepcopy(obj)
        a["extended_analysis"] = (str(a.get("extended_analysis") or "") + " La congelacion se acordo en Ulaanbaatar.").strip()
        attacks.append(("T4_TERMINO_ES_SOLO_SHADOW", a, None, "DIG-08",
                        ["Acta complementaria: la congelacion se acordo en Ulaanbaatar."]))
        for nme, a, target, rule, supp in attacks:
            with cfg(OLD):
                ro = ev(gate, c, a, supp)
            with cfg(NEW):
                rn = ev(gate, c, a, supp)
            if rule == "DIG-06":
                do, dn = R.detected(ro, target), R.detected(rn, target)
            else:
                do, dn = rule in " ".join(ro["failed_checks"]), rule in " ".join(rn["failed_checks"])
            adv[(nme, "antes", do)] += 1
            adv[(nme, "despues", dn)] += 1
            if (do and not dn) or (ro["decision"] == "ABSTENER" and rn["decision"] == "PERMITIR"):
                regress.append({"id": c["row"]["id"], "src": c["src"], "ataque": nme})
    out["capturas_reevaluadas"] = len(cases) + len(abc)
    out["cambios_decision_todas_las_capturas"] = changes
    out["adversarial"] = {f"{n}|{m}|{'detectado' if d else 'NO_detectado'}": k for (n, m, d), k in sorted(adv.items())}
    out["adversarial_regresiones"] = regress
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("variantes", "capturas_reevaluadas", "adversarial", "adversarial_regresiones")},
                     ensure_ascii=False, indent=1))
    print("cambios de decision:", json.dumps(changes, ensure_ascii=False)[:3000])
    print("resultado:", OUT)


if __name__ == "__main__":
    main()

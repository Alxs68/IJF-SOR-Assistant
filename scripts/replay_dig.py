"""Reproduce SIN LLM la parte determinista del pipeline sobre respuestas ya generadas (eval_funcional).

  python scripts/replay_dig.py run.jsonl [--solo A01,B02] > replay.jsonl
Para cada registro con 'respuesta_llm': recupera de nuevo (RRE, misma consulta EN; los pasajes del contexto
registrado que falten se anaden desde el corpus), aplica con los flags del entorno la reparacion de identificadores,
la validacion de citas, la reparacion de citas, el completado de atribucion, el DIG y la poda, e imprime la
decision. Sirve para (a) comprobar que la reproduccion coincide con la ejecucion real y (b) medir alternativas
deterministas sobre las MISMAS respuestas del modelo, sin gastar cuota.
"""
import argparse
import contextlib
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--solo", default="")
    a = ap.parse_args(argv)
    solo = set(filter(None, a.solo.split(",")))
    import ada_assistant as A
    import evidence_attribution as attr
    import evidence_reassembly as reasm
    from rre_engine import ReasoningRetrievalEngine
    with contextlib.redirect_stdout(io.StringIO()):
        rre = ReasoningRetrievalEngine()
    corpus = rre.passages_by_id
    holder = type("H", (), {})()
    holder.rre = rre
    gate = A.ArbitrationDecisionAssistant._decision_integrity_gate(holder)
    unified = A._dig_mod.FIX_ALL_VISIBLE_FIELDS if hasattr(A, "_dig_mod") else True
    import decision_integrity as D
    unified = D.FIX_ALL_VISIBLE_FIELDS
    for line in open(a.run, encoding="utf-8"):
        r = json.loads(line)
        if (solo and r["id"] not in solo) or not r.get("respuesta_llm"):
            continue
        with contextlib.redirect_stdout(io.StringIO()):
            res = rre.retrieve(r["consulta_en"], top_k=5, expand_graph=True, domain_query=r["q"])
        ev, rel = res.get("evidence") or [], res.get("related_passages") or []
        have = {p["passage_id"] for p in ev + rel}
        for short in r.get("contexto") or []:
            pid = "SOR-2026-08-" + short
            if pid not in have and pid in corpus:
                rel.append(reasm._record(pid, corpus, "", "contexto registrado"))
        delivered = {p["passage_id"]: p for p in ev + rel}
        ans = r["respuesta_llm"]
        steps = {}
        if reasm.citation_repair_enabled():
            ans, steps["ids"] = reasm.repair_citation_ids(ans, delivered, corpus)
        valid = A.ArbitrationDecisionAssistant._validate_llm_citations(None, ans, ev, rel)
        out = {"id": r["id"], "respondible": r["respondible"], "real": r["estado"],
               "real_fallidos": (r.get("dig") or {}).get("fallidos"), "citas_validas": valid}
        if valid:
            if reasm.quote_repair_enabled():
                ans, steps["citas"] = reasm.repair_quotes(ans, delivered, gate)
            if attr.enabled():
                ans, steps["completado"] = attr.complete_quotes(ans, delivered, gate, r["q"], r["consulta_en"], unified=unified)
            dig = gate.evaluate(ans, r["q"], r["consulta_en"], ev, rel)
            failed0 = set(dig["failed_checks"])
            if unified and failed0 and failed0 <= A.PRUNABLE_CHECKS:
                cand, removed = gate.prune_unsupported(ans, r["q"], r["consulta_en"])
                if removed and A.ArbitrationDecisionAssistant._validate_llm_citations(None, cand, ev, rel):
                    d2 = gate.evaluate(cand, r["q"], r["consulta_en"], ev, rel)
                    if d2["decision"] == "PERMITIR":
                        dig, steps["poda"] = d2, removed
            out.update(decision=dig["decision"], fallidos=dig["failed_checks"],
                       detalle=[c for c in dig["checks"] if not c["passed"]],
                       pasos={k: len(v or []) for k, v in steps.items()})
        print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()

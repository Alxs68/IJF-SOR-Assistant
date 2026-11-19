"""Integridad de la verificacion V4 ante cifras alteradas (sin cambiar la aplicacion).

  python scripts/eval_mutaciones_v4.py run1.jsonl [run2.jsonl ...] --out mut.jsonl
Para cada respuesta registrada (eval_funcional) con una cifra en 'summary' que figura en sus citas, sustituye esa
cifra por otra que NO figura en las citas y pasa la respuesta alterada por answer_verification.verify() con el
verificador real (ADA_VERIFIER_MODEL). Resultado correcto: la frase alterada se retira o la respuesta se abstiene.
Instrumento de evaluacion: las respuestas proceden de los conjuntos existentes; no es un conjunto de pruebas nuevo.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
import answer_verification as V  # noqa: E402
import decision_integrity as D  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from llm_provider import GeminiClient
    ps = json.load(open(os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json"), encoding="utf-8"))
    corpus = {p["passage_id"]: dict(p, page=p.get("pdf_page_index")) for p in ps}
    gate = D.DecisionIntegrityGate(list(corpus.values()))

    def llm_call(prompt):
        cli = GeminiClient(model=V.verifier_model())
        text = cli.generate(prompt, json_mode=True)
        return text, dict(getattr(cli, "last_usage", {}) or {}), getattr(cli, "last_model_version", None) or cli.model

    with open(a.out, "w", encoding="utf-8") as fh:
        for run in a.runs:
            for line in open(run, encoding="utf-8"):
                r = json.loads(line)
                obj = D.parse_answer(r.get("respuesta_llm") or "")
                if not obj or str(obj.get("answerability", "")).upper() != "RESPALDADA":
                    continue
                qnums = set().union(*[D.numbers_in(str(q.get("quote") or "")) for q in obj.get("evidence_quotes") or []
                                      if isinstance(q, dict)] or [set()])
                summary = str(obj.get("summary") or "")
                m = next((m for m in re.finditer(r"(?<![\w.,-])(\d+)(?![\w.,])", D.SOR_ID.sub(lambda x: "#" * len(x.group(0)), summary))
                          if m.group(1) in qnums and int(m.group(1)) < 1000), None)
                if not m:
                    continue
                n = int(m.group(1))
                new = next(v for v in (n + 1, n + 2, n + 3, n * 2 + 1) if str(v) not in qnums)
                mutated = summary[:m.start(1)] + str(new) + summary[m.end(1):]
                obj["summary"] = mutated
                ctx = ["SOR-2026-08-" + c for c in (r.get("contexto") or []) if "SOR-2026-08-" + c in corpus]
                delivered = [corpus[p] for p in ctx]
                ans, rec = V.verify(json.dumps(obj, ensure_ascii=False), r["q"], r.get("consulta_en") or r["q"],
                                    delivered[:5], delivered[5:], gate, llm_call=llm_call)
                out = D.parse_answer(ans) or {}
                still = re.search(rf"(?<![\w.,-]){new}(?![\w.,])", D.SOR_ID.sub(" ", str(out.get("summary") or "")))
                caught = rec["decision"] == "ABSTENER" or not still
                fh.write(json.dumps({"run": os.path.basename(run), "id": r["id"], "mutacion": f"{n}->{new}",
                                     "decision": rec["decision"], "detectada": caught,
                                     "modo": rec["verification"]["mode"],
                                     "retirado": [x["reason"][:80] for x in rec["verification"]["removed"]],
                                     "verificador": rec["verification"].get("verifier")}, ensure_ascii=False) + "\n")
                fh.flush()
                print(r["id"], f"{n}->{new}", rec["decision"], "DETECTADA" if caught else "NO DETECTADA", flush=True)


if __name__ == "__main__":
    main()

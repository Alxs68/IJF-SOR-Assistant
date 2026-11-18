"""Evaluacion SOLO de recuperacion (sin LLM): misma consulta EN para todas las variantes.

  python scripts/eval_recuperacion.py --consultas tests/funcional/consultas_funcionales_v1.json \
      --traducciones run.jsonl [--traducciones otro.jsonl] --etiqueta X --out out.jsonl
Para cada consulta y cada fuente de traduccion (campo 'consulta_en' de una ejecucion de eval_funcional) se llama a
RRE.retrieve(top_k=5, expand_graph=True) con las variables de entorno vigentes y se registra si alguna pagina
esperada esta en la evidencia o en los relacionados, y en que posicion. K=5 (DEC-009).
"""
import argparse
import contextlib
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]


def page(pid):
    s = (pid or "").replace("SOR-2026-08-", "")
    return s[:4]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--consultas", required=True)
    ap.add_argument("--traducciones", action="append", default=[])
    ap.add_argument("--etiqueta", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    data = json.load(open(a.consultas, encoding="utf-8"))["consultas"]
    trans = []
    for path in a.traducciones:
        rs = {}
        for line in open(path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                rs[r["id"]] = r.get("consulta_en")
        trans.append((os.path.basename(path).replace(".jsonl", ""), rs))
    from rre_engine import ReasoningRetrievalEngine
    with contextlib.redirect_stdout(io.StringIO()):
        rre = ReasoningRetrievalEngine()
    with open(a.out, "w", encoding="utf-8") as fh:
        for c in data:
            exp = {page(x) for x in c["esperado"]}
            for src, rs in trans or [("original", {})]:
                q_en = rs.get(c["id"]) or c["q"]
                with contextlib.redirect_stdout(io.StringIO()):
                    res = rre.retrieve(q_en, top_k=5, expand_graph=True, domain_query=c["q"])
                ev = [e["passage_id"] for e in res.get("evidence") or []]
                rel = [e["passage_id"] for e in res.get("related_passages") or []]
                rank = next((i + 1 for i, p in enumerate(ev) if page(p) in exp), None)
                rec = {"etiqueta": a.etiqueta, "id": c["id"], "respondible": c["respondible"], "traduccion": src,
                       "consulta_en": q_en, "estado": res.get("status"), "evidencia": ev, "relacionados": rel,
                       "esperado": sorted(exp), "rango_esperado": rank,
                       "en_contexto": bool(exp & {page(p) for p in ev + rel}) if exp else None}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("FIN", a.etiqueta)


if __name__ == "__main__":
    main()

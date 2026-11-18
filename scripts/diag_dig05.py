"""Diagnostico estructural de DIG-05 (sin LLM, sin modificar el DIG).

Para cada consulta y su traduccion EN registrada en una ejecucion, calcula con el MISMO criterio de DIG-05
(DecisionIntegrityGate.pertinent): (1) los terminos distintivos de la consulta; (2) si ALGUNA frase de ALGUN pasaje
esperado podria ser cita pertinente ("oraculo"). Si (2) es falso, DIG-05 rechaza cualquier respuesta que cite la
evidencia correcta, sea cual sea su calidad.
  python scripts/diag_dig05.py consultas.json run.jsonl [run2.jsonl ...]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
import decision_integrity as D  # noqa: E402


def main(qpath, runs):
    ps = json.load(open(os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json"), encoding="utf-8"))
    gate = D.DecisionIntegrityGate(ps)
    by_page = {}
    for p in ps:
        by_page.setdefault(f"P{int(p['pdf_page_index']):03d}", p["text_original"] or "")
    qs = json.load(open(qpath, encoding="utf-8"))["consultas"]
    for run in runs:
        tr = {json.loads(l)["id"]: json.loads(l).get("consulta_en") for l in open(run, encoding="utf-8") if l.strip()}
        n = blocked = nodist = 0
        print(f"== {os.path.basename(run)}")
        for c in qs:
            if not c["esperado"]:
                continue
            q_en = tr.get(c["id"]) or ""
            qst = D.content_stems(c["q"]) | D.content_stems(q_en)
            dist = sorted(gate.distinctive_stems(qst))
            pages = {x[:4] for x in c["esperado"]}
            ok = any(gate.pertinent(D.content_stems(s), qst) for pg in pages for s in D.sentences(by_page.get(pg, "")))
            n += 1
            blocked += not ok
            nodist += not dist
            if not ok:
                print(f"  {c['id']} bloqueada  distintivos={dist}  en={q_en!r}")
        print(f"  consultas con evidencia esperada: {n}; sin termino distintivo: {nodist}; "
              f"DIG-05 imposible con la evidencia correcta: {blocked}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])

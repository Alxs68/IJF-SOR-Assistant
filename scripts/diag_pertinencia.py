"""Discriminacion del criterio de pertinencia de DIG-05 (diagnostico para decision del PO; NO modifica el DIG).

  python scripts/diag_pertinencia.py run.jsonl [run2.jsonl ...]
Para cada respuesta registrada cuyas citas son literales, evalua la regla de pertinencia de DIG-05 (cada pasaje
citado necesita >=1 cita pertinente) con:
  - la consulta VERDADERA (deberia aceptar si la respuesta es pertinente), y
  - consultas de OTROS temas del mismo conjunto (control negativo: deberia rechazar).
Variantes (calculadas aqui, fuera del DIG):
  'sin_titulo': solo terminos distintivos (df <= 15 %) en la cita (DIG-05 sin FIX_PERTINENCE_HEADING).
  'vigente':    regla de DIG v3 (terminos distintivos en la cita o en el titulo de su unidad derivada).
  'titulo':     candidata: 'vigente' y ademas el termino de contenido MAS RARO de la consulta (df <= 50 %),
                es decir, el elemento mas especifico de lo que se pregunta, aunque sea frecuente en el SOR.
"""
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
import decision_integrity as D  # noqa: E402


def main(runs):
    ps = json.load(open(os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json"), encoding="utf-8"))
    corpus = {p["passage_id"]: dict(p, page=p.get("pdf_page_index")) for p in ps}
    gate = D.DecisionIntegrityGate(list(corpus.values()))
    df = lambda s: gate.stem_df.get(s, 0) / gate.n_pages

    def key_stems(qst, variant):
        dist = {s for s in qst if 0 < df(s) <= gate.max_df}
        if variant in ("rara", "titulo"):
            present = [s for s in qst if 0 < df(s) <= 0.5]
            if present:
                dist.add(min(present, key=df))
        return dist

    def pertinent(quotes_by_pid, qst, variant):
        ks = key_stems(qst, variant)
        for pid, quotes in quotes_by_pid.items():
            ok = any(D.content_stems(q) & ks for q in quotes)
            if not ok and variant in ("vigente", "titulo"):
                for q in quotes:
                    h = gate._heading_of_quote(D.norm(q), corpus[pid])
                    if h and D.content_stems(h) & ks:
                        ok = True
                        break
            if not ok:
                return False
        return True

    recs = []
    for run in runs:
        for line in open(run, encoding="utf-8"):
            r = json.loads(line)
            try:
                obj = json.loads(r.get("respuesta_llm") or "")
            except (TypeError, ValueError):
                continue
            if not isinstance(obj, dict):
                continue
            cited = set(D.SOR_ID.findall(json.dumps({k: obj.get(k) for k in ("summary", "normative_basis", "citations")}, ensure_ascii=False)))
            qb = {}
            for q in obj.get("evidence_quotes") or []:
                if isinstance(q, dict) and q.get("passage_id") in corpus and gate._locate(D.norm(q.get("quote") or ""), corpus[q["passage_id"]]):
                    qb.setdefault(q["passage_id"], []).append(q["quote"])
            if not cited or not cited <= set(qb):
                continue
            recs.append({"run": os.path.basename(run), "id": r["id"], "resp": r["respondible"],
                         "qst": D.content_stems(r["q"]) | D.content_stems(r.get("consulta_en") or ""),
                         "quotes": {pid: qb[pid] for pid in cited}})
    rnd = random.Random(7)
    print(f"respuestas con citas literales evaluables: {len(recs)}")
    for variant in ("sin_titulo", "vigente", "titulo"):
        tp = sum(pertinent(x["quotes"], x["qst"], variant) for x in recs if x["resp"] != "NO")
        npos = sum(1 for x in recs if x["resp"] != "NO")
        neg = fa = 0
        for x in recs:
            others = [y for y in recs if y["id"][0] != x["id"][0] and not (set(y["quotes"]) & set(x["quotes"]))]
            for y in rnd.sample(others, min(5, len(others))):
                neg += 1
                fa += pertinent(x["quotes"], y["qst"], variant)
        print(f"  {variant:<8} acepta con su consulta: {tp}/{npos}   acepta con consulta de OTRO tema (falso positivo): {fa}/{neg}")


if __name__ == "__main__":
    main(sys.argv[1:])

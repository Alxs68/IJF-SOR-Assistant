"""Integridad comparable entre versiones CON y SIN DIG: cifras y terminos tecnicos del SOR afirmados en la respuesta
visible que no aparecen en NINGUN pasaje entregado (paginas del contexto y vecinas) ni en la consulta.
  python scripts/diag_respaldo.py run1.jsonl [run2.jsonl ...]
Es una cota inferior de errores (una cifra presente en el contexto puede estar mal aplicada)."""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
os.environ.setdefault("DIG06_REFS", "1")
os.environ.setdefault("DIG_NUMBER_NORMALIZATION", "v2")
import decision_integrity as D  # noqa: E402


def main(runs):
    ps = json.load(open(os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json"), encoding="utf-8"))
    gate = D.DecisionIntegrityGate(ps)
    page_text = {}
    for p in ps:
        page_text.setdefault(int(p["pdf_page_index"]), p["text_original"] or "")
    for run in runs:
        n = bad = 0
        detail = []
        for line in open(run, encoding="utf-8"):
            r = json.loads(line)
            if r["estado"] != "SUCCESS":
                continue
            fa = r.get("respuesta_final") or {}
            claims = " ".join(str(fa.get(k) or "") for k in ("summary", "normative_basis", "conditions_and_exceptions", "extended_analysis"))
            claims = re.sub(r"\(https?://[^)]*\)", " ", claims)
            pages = {int(c[1:4]) for c in r.get("contexto") or []}
            ctx = " ".join(page_text.get(p + d, "") for p in pages for d in (-1, 0, 1))
            nums = gate.claim_numbers(claims, r["q"]) - D.numbers_in(ctx) - D.numbers_in(r["q"] + " " + (r.get("consulta_en") or ""))
            words = set(re.findall(r"[a-z][a-z\-]{3,}", D.strip_accents(D.norm(D.SOR_ID.sub(" ", claims)))))
            ctx_words = set(re.findall(r"[a-z][a-z\-]{3,}", D.strip_accents(D.norm(ctx + " " + r["q"] + " " + (r.get("consulta_en") or "")))))
            ctx_words |= {x for w in ctx_words if "-" in w for x in w.split("-")}
            terms = sorted(t for t in words & gate.distinctive if t not in ctx_words)
            n += 1
            if nums or terms:
                bad += 1
                detail.append(f"{r['id']}: cifras={sorted(nums)} terminos={terms}")
        print(f"== {os.path.basename(run)}: respuestas {n}; con cifra o termino ausente del contexto entregado: {bad}")
        for d in detail:
            print("   ", d)


if __name__ == "__main__":
    main(sys.argv[1:])

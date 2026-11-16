#!/usr/bin/env python3
"""Fase 10.1 - Incorpora revisiones arbitrales al benchmark_v2 SIN modificar el original.

Lee  data/eval/benchmark_v2/benchmark_v2.jsonl  (nunca se escribe)
     uno o mas CSV de revision (formato review/review_template.csv)
Escribe data/eval/benchmark_v2/reviewed/benchmark_v2_reviewed.jsonl
        data/eval/benchmark_v2/reviewed/review_log.json

Reglas (REVIEW_PROTOCOL.md):
  * auto_labels nunca se modifican; las decisiones humanas van en human_labels.
  * ACEPTA / CORRIGE de >=1 revisor -> EXPERT_REVIEWED (si no hay conflicto).
  * Revisores con comportamientos esperados distintos -> REVIEW_CONFLICT.
  * RECHAZA -> REJECTED_BY_EXPERT ; DUDA o fila vacia -> sigue PENDING_EXPERT_REVIEW.
  * Filas con id desconocido, veredicto invalido o comportamiento invalido -> errores, no se aplican.
Solo stdlib.
"""
import argparse
import csv
import hashlib
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = os.path.join(ROOT, "data/eval/benchmark_v2/benchmark_v2.jsonl")
OUT_DIR = os.path.join(ROOT, "data/eval/benchmark_v2/reviewed")
VERDICTS = {"ACEPTA", "CORRIGE", "RECHAZA", "DUDA"}
BEHAVIORS = {"RESPONDER", "ABSTENER_INSUFICIENCIA", "ABSTENER_FUERA_DE_DOMINIO", "SOLICITAR_ACLARACION"}


def load_reviews(paths, known_ids):
    rows, errors = defaultdict(list), []
    for p in paths:
        with open(p, encoding="utf-8-sig", newline="") as fh:
            for n, row in enumerate(csv.DictReader(fh), 2):
                v = (row.get("verdict") or "").strip().upper()
                if not v:
                    continue
                rid = (row.get("id") or "").strip()
                where = f"{os.path.basename(p)}:{n}"
                if rid not in known_ids:
                    errors.append(f"{where}: id desconocido {rid!r}")
                    continue
                if v not in VERDICTS:
                    errors.append(f"{where}: veredicto invalido {v!r}")
                    continue
                if not (row.get("reviewer") or "").strip():
                    errors.append(f"{where}: falta reviewer")
                    continue
                hb = (row.get("human_expected_behavior") or "").strip().upper()
                if v == "CORRIGE":
                    if hb and hb not in BEHAVIORS:
                        errors.append(f"{where}: human_expected_behavior invalido {hb!r}")
                        continue
                    if not hb and not (row.get("human_expected_articles") or "").strip():
                        errors.append(f"{where}: CORRIGE sin correccion")
                        continue
                rows[rid].append({
                    "reviewer": row["reviewer"].strip(), "review_date": (row.get("review_date") or "").strip(),
                    "verdict": v, "expected_behavior": hb or None,
                    "expected_articles": [a.strip() for a in (row.get("human_expected_articles") or "").split(";") if a.strip()] or None,
                    "notes": (row.get("notes") or "").strip(), "source_file": os.path.basename(p),
                })
    return rows, errors


def merge(records, reviews):
    out, stats = [], defaultdict(int)
    for r in records:
        r = json.loads(json.dumps(r))  # copia profunda; el original no se toca
        revs = reviews.get(r["id"], [])
        decisive = [x for x in revs if x["verdict"] in ("ACEPTA", "CORRIGE")]
        if any(x["verdict"] == "RECHAZA" for x in revs) and not decisive:
            status = "REJECTED_BY_EXPERT"
        elif decisive:
            beh = {x["expected_behavior"] or r["auto_labels"]["expected_behavior"] for x in decisive}
            arts = {tuple(x["expected_articles"] or r["auto_labels"]["expected_articles"]) for x in decisive}
            rejected = any(x["verdict"] == "RECHAZA" for x in revs)
            status = "REVIEW_CONFLICT" if (len(beh) > 1 or len(arts) > 1 or rejected) else "EXPERT_REVIEWED"
            if status == "EXPERT_REVIEWED":
                r["human_labels"] = {"expected_behavior": beh.pop(), "expected_articles": list(arts.pop()),
                                     "reviewers": sorted({x["reviewer"] for x in decisive})}
        else:
            status = "PENDING_EXPERT_REVIEW"
        r["review_status"] = status
        r["reviews"] = revs
        stats[status] += 1
        out.append(r)
    return out, dict(stats)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("reviews", nargs="+")
    ap.add_argument("--bench", default=BENCH)
    ap.add_argument("--out-dir", default=OUT_DIR)
    a = ap.parse_args(argv)
    raw = open(a.bench, "rb").read()
    records = [json.loads(l) for l in raw.decode("utf-8").splitlines() if l.strip()]
    reviews, errors = load_reviews(a.reviews, {r["id"] for r in records})
    merged, stats = merge(records, reviews)
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "benchmark_v2_reviewed.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in merged))
    log = {"benchmark_sha256": hashlib.sha256(raw).hexdigest(), "review_files": [os.path.basename(p) for p in a.reviews],
           "status_counts": stats, "errors": errors}
    with open(os.path.join(a.out_dir, "review_log.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(log, fh, ensure_ascii=False, indent=2)
    print(json.dumps(log, ensure_ascii=False, indent=1))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())

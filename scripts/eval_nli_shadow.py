#!/usr/bin/env python3
"""Fase 10.2 - Evaluacion experimental de modelos NLI en CPU (modo SHADOW).

Dataset: data/eval/nli_shadow_v1/pairs.jsonl (derivado de benchmark_v2).
Metodologia:
  * Todas las probabilidades se calculan una vez por modelo.
  * El umbral de entailment se elige SOLO con pares dev (max F1 de la clase SUPPORTED);
    test_sealed se informa con ese umbral fijo (y con 0.5 como referencia).
  * Discriminacion de ambito por item: p(SUPPORT) > p(SCOPE_PREMISE) y p(SUPPORT) > p(SCOPE_CLAIM).
  * Rendimiento: tiempo de carga, RSS antes/despues, pico de RSS, latencia por par
    (lote 1) p50/p95, throughput en lote, y concurrencia (1/2/4 hilos) con verificacion de
    que las salidas coinciden con la ejecucion secuencial.
Nada de esto se conecta a ADA. Si un modelo no puede descargarse o cargarse se documenta.
Uso:
  python scripts/eval_nli_shadow.py --allow-test-sealed            (todos los modelos por defecto)
  python scripts/eval_nli_shadow.py --models lexical cross-encoder/nli-deberta-v3-xsmall --split dev
"""
import argparse
import hashlib
import json
import os
import platform
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from statistics import median

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
PAIRS = os.path.join(ROOT, "data/eval/nli_shadow_v1/pairs.jsonl")
CORPUS = os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json")
OUT = os.path.join(ROOT, "data/eval/nli_shadow_v1/results/nli_eval_{split}.json")
DEFAULT_MODELS = [
    "lexical",                                                  # linea base no semantica
    "cross-encoder/nli-deberta-v3-xsmall",                      # EN, ~70M
    "MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli",          # multilingue, ~107M
    "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7",  # multilingue, ~280M
]

from experimental.nli_shadow import NLIShadowEvaluator, lexical_scorer, peak_rss_mb, rss_mb  # noqa: E402


def sha_file(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))] if xs else None


def binary(rows, thr):
    tp = sum(r["label"] == "SUPPORTED" and r["p_ent"] >= thr for r in rows)
    fp = sum(r["label"] != "SUPPORTED" and r["p_ent"] >= thr for r in rows)
    fn = sum(r["label"] == "SUPPORTED" and r["p_ent"] < thr for r in rows)
    tn = len(rows) - tp - fp - fn
    p = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * rc / (p + rc) if p + rc else 0.0
    return {"n": len(rows), "precision": round(p, 3), "recall": round(rc, 3), "f1": round(f1, 3),
            "accuracy": round((tp + tn) / len(rows), 3) if rows else None,
            "confusion": {"TP": tp, "FP": fp, "FN": fn, "TN": tn}}


def best_threshold(rows):
    cands = sorted({round(r["p_ent"], 4) for r in rows} | {0.5})
    return max(cands, key=lambda t: (binary(rows, t)["f1"], -abs(t - 0.5))) if rows else 0.5


def report(rows, thr):
    o = {"threshold": thr, "binary": binary(rows, thr)}
    o["by_pair_type"] = {}
    for t in sorted({r["pair_type"] for r in rows}):
        xs = [r for r in rows if r["pair_type"] == t]
        acc = sum((r["p_ent"] >= thr) == (r["label"] == "SUPPORTED") for r in xs) / len(xs)
        o["by_pair_type"][t] = {"n": len(xs), "accuracy": round(acc, 3),
                                "accepted_as_supported": sum(r["p_ent"] >= thr for r in xs),
                                "mean_p_contradiction": round(sum(r["p_con"] for r in xs) / len(xs), 3)}
    o["by_language"] = {l: binary([r for r in rows if r["language"] == l], thr) for l in sorted({r["language"] for r in rows})}
    # discriminacion de ambito por item
    by_item = defaultdict(dict)
    for r in rows:
        by_item[r["item_id"]].setdefault(r["pair_type"], []).append(r["p_ent"])
    disc = {"SCOPE_PREMISE": [0, 0], "SCOPE_CLAIM": [0, 0], "NUMBER": [0, 0]}
    for d in by_item.values():
        if "SUPPORT" not in d:
            continue
        s = d["SUPPORT"][0]
        for t in disc:
            for v in d.get(t, []):
                disc[t][1] += 1
                disc[t][0] += s > v
    o["pairwise_discrimination"] = {t: {"n": n, "support_scored_higher": k, "rate": round(k / n, 3) if n else None}
                                    for t, (k, n) in disc.items()}
    o["wrong_scope_accepted"] = sorted(r["pair_id"] for r in rows if r["pair_type"] in ("SCOPE_PREMISE", "SCOPE_CLAIM") and r["p_ent"] >= thr)
    o["supported_rejected"] = sorted(r["pair_id"] for r in rows if r["label"] == "SUPPORTED" and r["p_ent"] < thr)
    return o


def run_model(name, pairs, batch, threads_list):
    ev = NLIShadowEvaluator(scorer=lexical_scorer) if name == "lexical" else NLIShadowEvaluator(name)
    info = dict(ev.load())
    res = {"model": name, "load": info}
    if not info["loaded"]:
        res["status"] = "NO_DISPONIBLE"
        return res, None
    # latencia lote 1
    lat, scores = [], []
    for p in pairs:
        t0 = time.perf_counter()
        scores.append(ev.score_pair(p["premise"], p["hypothesis"]))
        lat.append((time.perf_counter() - t0) * 1000)
    # throughput en lote
    t0 = time.perf_counter()
    batched = []
    for i in range(0, len(pairs), batch):
        batched += ev.score_batch([(p["premise"], p["hypothesis"]) for p in pairs[i:i + batch]])
    bt = time.perf_counter() - t0
    drift = max(abs(a["entailment"] - b["entailment"]) for a, b in zip(scores, batched))
    # concurrencia
    sub = pairs[:min(32, len(pairs))]
    conc = {}
    for th in threads_list:
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=th) as ex:
            outs = list(ex.map(lambda p: ev.score_pair(p["premise"], p["hypothesis"]), sub))
        wall = time.perf_counter() - t0
        conc[str(th)] = {"pairs": len(sub), "wall_s": round(wall, 3), "pairs_per_s": round(len(sub) / wall, 2),
                         "max_abs_diff_vs_sequential": round(max(abs(a["entailment"] - b["entailment"]) for a, b in zip(outs, scores)), 6)}
    try:
        import torch
        torch_threads = torch.get_num_threads()
    except Exception:
        torch_threads = None
    res.update(status="OK", performance={
        "latency_ms_batch1": {"p50": round(median(lat), 2), "p95": round(pct(lat, 0.95), 2), "max": round(max(lat), 2)},
        "batch": batch, "throughput_pairs_per_s": round(len(pairs) / bt, 2),
        "max_abs_diff_batch_vs_single": round(drift, 6), "concurrency": conc,
        "rss_after_inference_mb": rss_mb(), "peak_rss_mb": peak_rss_mb(), "torch_threads": torch_threads,
        "truncated_pairs": sum(bool(s.get("truncated")) for s in scores)})
    rows = [dict(item_id=p["item_id"], pair_id=p["pair_id"], pair_type=p["pair_type"], label=p["label"],
                 split=p["split"], language=p["language"], p_ent=s["entailment"], p_con=s["contradiction"],
                 p_neu=s["neutral"]) for p, s in zip(pairs, scores)]
    return res, rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    ap.add_argument("--split", default="all", choices=("dev", "test_sealed", "all"))
    ap.add_argument("--allow-test-sealed", action="store_true")
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--threads", nargs="+", type=int, default=[1, 2, 4])
    ap.add_argument("--out")
    ap.add_argument("--no-isolate", action="store_true", help="no lanzar un subproceso por modelo")
    ap.add_argument("--child-out", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.split in ("test_sealed", "all") and not a.allow_test_sealed:
        print("ERROR: test_sealed esta sellado; use --allow-test-sealed (solo evaluacion final)", file=sys.stderr)
        return 2
    corpus_before = sha_file(CORPUS)
    pairs = [json.loads(l) for l in open(PAIRS, encoding="utf-8") if l.strip()]
    if a.split != "all":
        pairs = [p for p in pairs if p["split"] == a.split]
    env = {"python": sys.version.split()[0], "platform": platform.platform(), "processor": platform.processor(),
           "cpu_count": os.cpu_count(), "rss_start_mb": rss_mb()}
    try:
        import torch
        import transformers
        env.update(torch=torch.__version__, transformers=transformers.__version__)
    except Exception as e:
        env["deps_error"] = f"{type(e).__name__}: {e}"
    results = []
    for m in a.models:
        print(f"== {m}", flush=True)
        if len(a.models) > 1 and not a.no_isolate:
            # un subproceso por modelo: memoria (RSS/pico) y carga medidas sin interferencias
            import subprocess
            import tempfile
            tmp = os.path.join(tempfile.gettempdir(), f"nli_child_{os.getpid()}.json")
            cmd = [sys.executable, os.path.abspath(__file__), "--models", m, "--split", a.split, "--batch", str(a.batch),
                   "--threads", *map(str, a.threads), "--child-out", tmp] + (["--allow-test-sealed"] if a.allow_test_sealed else [])
            cp = subprocess.run(cmd)
            if cp.returncode == 0 and os.path.exists(tmp):
                with open(tmp, encoding="utf-8") as fh:
                    results.append(json.load(fh)["models"][0])
                os.remove(tmp)
            else:
                results.append({"model": m, "status": "ERROR_SUBPROCESO", "returncode": cp.returncode})
            continue
        res, rows = run_model(m, pairs, a.batch, a.threads)
        if rows is not None:
            dev = [r for r in rows if r["split"] == "dev"]
            thr = best_threshold(dev) if dev else 0.5
            res["threshold_selected_on_dev"] = thr
            res["metrics"] = {s: {"at_dev_threshold": report([r for r in rows if r["split"] == s], thr),
                                  "at_0.5": report([r for r in rows if r["split"] == s], 0.5)}
                              for s in ("dev", "test_sealed") if any(r["split"] == s for r in rows)}
            res["per_pair"] = rows
            for s, mm in res["metrics"].items():
                b = mm["at_dev_threshold"]
                print(f"   {s:11} thr={thr:.3f} P={b['binary']['precision']:.2f} R={b['binary']['recall']:.2f} "
                      f"F1={b['binary']['f1']:.2f} scopeAccepted={len(b['wrong_scope_accepted'])} "
                      f"disc(prem/claim/num)={b['pairwise_discrimination']['SCOPE_PREMISE']['rate']}/"
                      f"{b['pairwise_discrimination']['SCOPE_CLAIM']['rate']}/{b['pairwise_discrimination']['NUMBER']['rate']}")
            pf = res["performance"]
            print(f"   load={res['load']['load_ms']}ms params={res['load'].get('n_parameters')} "
                  f"lat p50/p95={pf['latency_ms_batch1']['p50']}/{pf['latency_ms_batch1']['p95']}ms "
                  f"peakRSS={pf['peak_rss_mb']}MB conc={ {k: v['pairs_per_s'] for k, v in pf['concurrency'].items()} }")
        else:
            print("   NO DISPONIBLE:", res["load"]["error"])
        results.append(res)
    rep = {"dataset": PAIRS, "dataset_sha256": sha_file(PAIRS), "split": a.split, "environment": env,
           "corpus_unchanged": corpus_before == sha_file(CORPUS),
           "pairs": dict(Counter(p["pair_type"] for p in pairs)), "models": results,
           "note": ("Medicion EXPERIMENTAL en SHADOW; no conectada a ADA. Pares y afirmaciones PENDING_EXPERT_REVIEW. "
                    "Una alta probabilidad de entailment NO es prueba de entailment normativo. "
                    "Memoria medida en esta maquina; no extrapolable sin medir en el destino (OCI).")}
    path = a.child_out or a.out or OUT.format(split=a.split)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    print("corpus_unchanged=", rep["corpus_unchanged"], "resultados:", path)
    return 0 if rep["corpus_unchanged"] else 3


if __name__ == "__main__":
    sys.exit(main())

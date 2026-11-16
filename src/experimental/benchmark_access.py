"""Acceso controlado a benchmark_v2 (Fase 10).

El split test_sealed solo se entrega con allow_test_sealed=True; se verifica su hash
contra el manifiesto para detectar ediciones posteriores al sellado.
"""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BENCH_DIR = os.path.join(ROOT, "data", "eval", "benchmark_v2")


class SealedSplitError(RuntimeError):
    pass


def _read(path):
    with open(path, "rb") as fh:
        return fh.read()


def load_items(split="dev", allow_test_sealed=False, bench_dir=BENCH_DIR):
    """split: dev | test_sealed | all."""
    if split not in ("dev", "test_sealed", "all"):
        raise ValueError(f"split invalido: {split}")
    if split in ("test_sealed", "all") and not allow_test_sealed:
        raise SealedSplitError("test_sealed esta sellado: use allow_test_sealed=True (--allow-test-sealed) "
                               "solo para la evaluacion final, nunca para ajustar.")
    manifest = json.loads(_read(os.path.join(bench_dir, "manifest.json")).decode("utf-8"))
    sealed_raw = _read(os.path.join(bench_dir, "splits", "test_sealed.jsonl")).replace(b"\r\n", b"\n")
    sealed_ok = hashlib.sha256(sealed_raw).hexdigest() == manifest["split_policy"]["test_sealed_sha256"]
    if split in ("test_sealed", "all") and not sealed_ok:
        raise SealedSplitError("hash de test_sealed distinto al del manifiesto: el split fue modificado")
    names = ["dev", "test_sealed"] if split == "all" else [split]
    items = []
    for n in names:
        raw = _read(os.path.join(bench_dir, "splits", f"{n}.jsonl")).decode("utf-8")
        items += [json.loads(l) for l in raw.splitlines() if l.strip()]
    return items, {"benchmark_version": manifest["benchmark_version"], "split": split,
                   "test_sealed_hash_ok": sealed_ok, "n": len(items)}


# ---------------------------------------------------------------- equivalencia de pasajes (Fase 11)
CORPUS_PATH = os.path.join(ROOT, "data", "processed", "rebuild_2026_08_corrected", "passages_candidate.json")
_EQUIV = None


def equivalence_map(corpus_path=CORPUS_PATH):
    """passage_id -> conjunto de passage_ids de la MISMA pagina con texto IDENTICO.

    El corpus tiene 385 pasajes sobre 287 paginas: varios pasajes de una pagina comparten el
    mismo text_original y solo difieren en metadatos (article_id). Para el usuario y para el LLM
    entregar cualquiera de ellos es entregar la misma evidencia; las anclas del benchmark, en
    cambio, solo listan los que coinciden en metadatos de articulo. Sin esta equivalencia las
    metricas de recuperacion se subestiman (Fase 11A)."""
    global _EQUIV
    if _EQUIV is None or corpus_path != CORPUS_PATH:
        with open(corpus_path, encoding="utf-8") as fh:
            ps = json.load(fh)
        groups = {}
        for p in ps:
            groups.setdefault((p["pdf_page_index"], p["text_original"]), set()).add(p["passage_id"])
        m = {pid: g for g in groups.values() for pid in g}
        if corpus_path != CORPUS_PATH:
            return m
        _EQUIV = m
    return _EQUIV


def expand(pids, eq=None):
    eq = eq or equivalence_map()
    out = set()
    for p in pids:
        out |= eq.get(p, {p})
    return out

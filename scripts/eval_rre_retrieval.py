"""Read-only retrieval evaluation for RRE (Phase 6.2 baseline / 6.4 comparison).

Prints to stdout only; writes no files, calls no LLM, does not modify the corpus or indexes.

Modes
  ES-proj : current retrieve() on the dictionary projection of the Spanish query (offline path)
  EN      : current retrieve() on an English equivalent (proxy for the LLM-translator path)
  ES-pure : sparse+dense RRF fusion only (no topical/ID/page boosts) on the ES projection
  EN-pure : same pure fusion on the English equivalent

Pertinence targets are page/article locators taken from the existing tests; they are not
normative answers. English equivalents are evaluation inputs written for this harness.

Run:  python scripts/eval_rre_retrieval.py
"""
import os
import re
import sys
import time
from statistics import mean

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY"):
    os.environ[k] = ""
os.environ.setdefault("IJF_SOR_EDITION", "2026-08")

from ada_assistant import ArbitrationDecisionAssistant  # noqa: E402

K = 5
# (id, spanish, english, pages, article-substrings, min_pertinent)
ANSWERABLE = [
    ("D01", "¿Cuáles son las dimensiones del tatami de competición?", "What are the dimensions of the competition tatami?", (96,), ("8.7",), 1),
    ("D02", "Durante un combate, se aplica osaekomi-waza y la acción continúa desplazándose hasta sobrepasar completamente el área de seguridad. ¿Qué debe señalar el árbitro?",
     "During a contest osaekomi-waza is applied and the action keeps moving until it completely goes beyond the safety area. What must the referee announce?", (174,), ("article 17",), 1),
    ("D03", "En un combate de cadetes (17 años), Tori intenta una proyección y en la acción apoya la cabeza en el tatami de forma voluntaria. ¿Qué sanción corresponde y qué artículo lo regula?",
     "In a cadet contest Tori attempts a throw and voluntarily supports the head on the tatami. What penalty applies and which article regulates it?", (188,), ("18.1.4",), 1),
    ("D04", "¿Qué sanción se aplica a un judoka de 15 años en categoría cadete si usa la cabeza para lanzar?",
     "What penalty applies to a 15-year-old cadet judoka who uses the head to throw?", (188,), ("18.1.4",), 1),
    ("D05", "¿Cuál es la definición reglamentaria de osaekomi-waza y en qué condiciones se anuncia Osaekomi y Toketa?",
     "What is the regulatory definition of osaekomi-waza and under what conditions are Osaekomi and Toketa announced?", (173, 174), ("article 17",), 1),
    ("D08", "Si Uke hace un puente voluntario al caer de una proyeccion pero aterriza sobre el cuerpo de Tori sin tocar el tatami con la cabeza, ¿se otorga Ippon?",
     "If Uke makes a voluntary bridge when falling from a throw but lands on Tori's body without touching the tatami with the head, is Ippon awarded?", (166, 167), ("article 14",), 1),
    ("D09", "Procedimiento de control de judogi en relacion a las medidas de la manga con sokuteiki y colores autorizados.",
     "Judogi control procedure regarding sleeve measurements with sokuteiki and authorised colours.", (), ("c1",), 2),
    ("D10", "¿Cuáles son las reglas sobre los colores del judogi en las competiciones oficiales de la IJF?",
     "What are the rules regarding judogi colours in official IJF competitions?", (124,), ("c1.9",), 1),
    ("HDIV", "¿Cómo se sanciona el Head Diving?", "How is head diving penalised?", (190,), ("18.2.1",), 1),
    ("HDEF", "¿Se permite la defensa con la cabeza?", "Is defending with the head allowed?", (166, 167, 188), (), 1),
    ("BRDG", "¿Qué ocurre cuando Uke hace puente?", "What happens when Uke makes a bridge?", (166, 167), (), 1),
    ("CDEF", "¿Cómo se sanciona el uso de la cabeza para defenderse en cadetes?", "How is using the head to defend penalised in cadet competitions?", (188, 189), ("18.1.4",), 1),
    ("CHED", "apoyo voluntario de cabeza de tori al lanzar en cadetes", "voluntary head support by tori when throwing in cadet events", (188,), ("18.1.4",), 1),
    ("NW1", "continuidad de acciones de ne-waza y agarre en el suelo fuera del area de combate", "continuity of ne-waza actions and ground grips outside the contest area", (151, 152), (), 1),
    ("NW2", "ne-waza o kansetsu-waza fuera del area de seguridad sin que el arbitro haya cantado Mate", "ne-waza or kansetsu-waza outside the safety area without the referee announcing Mate", (152,), (), 1),
    ("Q05", "Puede tori continuar con un ataque en ne-waza si la accion se inicio dentro y uke sale fuera del tatami", "Can Tori continue a ne-waza attack if the action started inside and Uke goes outside the tatami?", (151,), (), 1),
    ("Q09", "En cadetes si un competidor se desmaya por estrangulacion puede continuar en la repesca", "In cadet events, if a competitor loses consciousness from a strangulation, can they continue in the repechage?", (199,), (), 1),
    ("SLV", "¿Cuáles son las reglas de medida de las mangas del judogi y el control con sokuteiki?", "What are the judogi sleeve measurement rules and the sokuteiki control?", (), ("c1.10",), 1),
]
OOD = [
    ("O1", "reglas de fuera de juego en baloncesto nba y formula 1"),
    ("O2", "penalizaciones por parada en boxes en formula 1"),
    ("O3", "¿Qué penalización aplica por superar el límite de velocidad en el pit lane en Fórmula 1?"),
    ("O4", "¿Cuál es la sanción por una falta personal y tiro libre en básquetbol?"),
    ("O5", "¿Cómo se calcula la tasa de interés compuesto anual en finanzas?"),
]


def pertinent(passage, pages, arts):
    article = str(passage.get("article_id", "")).lower()
    return passage.get("page") in pages or any(a in article for a in arts)


def pure_fusion(rre, query, k=K):
    """Generic sparse+dense RRF (same weights as retrieve()) with no topical/ID/page rules."""
    sparse = [h for h in rre._sparse_search(query, top_k=25) if h[1] >= 0.05 and not rre._is_version_history_passage(h[0])]
    dense = [h for h in rre._dense_search(query, top_k=25) if not rre._is_version_history_passage(h[0])]
    scores = {}
    for rank, (pid, _) in enumerate(sparse, 1):
        scores[pid] = scores.get(pid, 0.0) + 1.2 / (60 + rank)
    for rank, (pid, _) in enumerate(dense, 1):
        scores[pid] = scores.get(pid, 0.0) + 1.0 / (60 + rank)
    smap, dmap = dict(sparse), dict(dense)
    for pid in scores:
        if pid in smap and pid in dmap:
            scores[pid] = (scores[pid] + 0.035) * 1.35
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
    ev = []
    for pid, _ in ranked:
        p = rre.passages_by_id[pid]
        ev.append({"passage_id": pid, "page": p.get("pdf_page_index"), "article_id": p.get("article_id")})
    return {"status": "SUCCESS" if ev else "ABSTAIN", "reason": None, "evidence": ev, "related_passages": []}


def ood_debug(rre, query):
    vocab = rre.sparse_index.get("idf", {})
    clean = query.lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")):
        clean = clean.replace(a, b)
    toks = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", clean)
    in_vocab = [t for t in toks if t in vocab]
    sparse = rre._sparse_search(query, top_k=3)
    dense = rre._dense_search(query, top_k=3)
    ood = rre.ood_detector.evaluate_grounding(query, sparse_top=sparse[0][1] if sparse else 0.0,
                                              dense_top=dense[0][1] if dense else 0.0) if getattr(rre, "ood_detector", None) else None
    return (f"tokens_in_vocab={in_vocab} sparse_top={round(sparse[0][1], 3) if sparse else None} "
            f"dense_top={round(dense[0][1], 3) if dense else None} ood={ood}")


def score(res, pages, arts, need):
    ev = res.get("evidence", [])
    delivered = ev + res.get("related_passages", [])
    ranks = [i for i, p in enumerate(ev[:K], 1) if pertinent(p, pages, arts)]
    n_pert = sum(pertinent(p, pages, arts) for p in delivered)
    return {
        "ood": res.get("status") == "ABSTAIN" and res.get("reason") == "OUT_OF_DOMAIN",
        "abstain": res.get("status") != "SUCCESS",
        "recall": len(ranks) >= min(need, K) if ranks else False,
        "rr": (1.0 / ranks[0]) if ranks else 0.0,
        "p1": bool(ranks and ranks[0] == 1),
        "precision": (n_pert / len(delivered)) if delivered else 0.0,
        "delivered": len(delivered),
        "first_rank": ranks[0] if ranks else None,
    }


def main():
    ada = ArbitrationDecisionAssistant()
    ada._call_llm = lambda prompt: (None, {})
    rre = ada.rre
    print(f"RRE flags: ood_detector={rre.enable_ood_detector} neg_anchors={rre.enable_negative_domain_anchors} "
          f"semantic_ranker={rre.enable_semantic_ranker} referee_disamb={rre.enable_referee_disambiguation} "
          f"stitching={rre.enable_chunk_stitching} mode={rre.operating_mode} dense_model={'OK' if rre.dense_model else 'NONE'}")
    modes = {"ES-proj": [], "EN": [], "ES-pure": [], "EN-pure": []}
    cutoff_inputs = {"ES-proj": [], "EN": []}
    times = {m: [] for m in modes}
    print("\n=== ANSWERABLE (per query) ===")
    for cid, es, en, pages, arts, need in ANSWERABLE:
        proj = ada._translate_to_technical_english(es)
        runs = {}
        es_retrieve = lambda q, top_k, _es=es: rre.retrieve(q, top_k=top_k, domain_query=_es)
        for mode, fn, q in (("ES-proj", es_retrieve, proj), ("EN", rre.retrieve, en),
                            ("ES-pure", lambda q, top_k: pure_fusion(rre, q, top_k), proj),
                            ("EN-pure", lambda q, top_k: pure_fusion(rre, q, top_k), en)):
            t0 = time.perf_counter()
            res = fn(q, top_k=K)
            times[mode].append((time.perf_counter() - t0) * 1000)
            s = score(res, pages, arts, need)
            modes[mode].append((cid, s))
            runs[mode] = (res, s)
            if mode in ("ES-proj", "EN"):
                cutoff_inputs[mode].append((cid, res, pages, arts))
        line = " | ".join(
            f"{m}: {'OOD' if s['ood'] else ('ABST' if s['abstain'] else 'ok')} r1={s['first_rank']} prec={s['precision']:.2f}"
            for m, (_, s) in runs.items())
        print(f"{cid}: {line}")
        print(f"      proj={proj!r}")
        if runs["ES-proj"][1]["ood"]:
            print(f"      OOD-debug(ES-proj): {ood_debug(rre, proj)}")
    print("\n=== OOD (false acceptance check, current retrieve) ===")
    false_acc = {"ES-proj": [], "raw": []}
    for cid, q in OOD:
        proj = ada._translate_to_technical_english(q)
        for mode, qq in (("ES-proj", proj), ("raw", q)):
            res = rre.retrieve(qq, top_k=K, domain_query=q)
            if res.get("status") == "SUCCESS":
                false_acc[mode].append(cid)
        print(f"{cid}: proj={proj!r} -> {rre.retrieve(proj, top_k=K, domain_query=q).get('status')}")
    print("\n=== METRICS (answerable n=%d, k=%d) ===" % (len(ANSWERABLE), K))
    print("mode     | OOD-rechazadas | Recall@5 | MRR@5 | P@1  | precisión bundle | lat. media ms")
    for m, rows in modes.items():
        ss = [s for _, s in rows]
        print(f"{m:8} | {sum(s['ood'] for s in ss):14d} | {mean(s['recall'] for s in ss):.2f}     | "
              f"{mean(s['rr'] for s in ss):.2f}  | {mean(s['p1'] for s in ss):.2f} | {mean(s['precision'] for s in ss):.2f}             | {mean(times[m]):.1f}")
    for m, rows in modes.items():
        print(f"{m}: OOD-rechazadas={[c for c, s in rows if s['ood']]} sin-pertinente-en-top5={[c for c, s in rows if not s['recall']]}")
    print(f"Falsas aceptaciones OOD: ES-proj={false_acc['ES-proj'] or 'ninguna'} raw={false_acc['raw'] or 'ninguna'}")
    print("\n=== SIMULACIÓN DE RECORTE (post-hoc sobre retrieve actual; no cambia el sistema) ===")
    print("mode     | ratio | grafo | recall | precisión | pasajes medios")
    for m, items in cutoff_inputs.items():
        for ratio in (0.0, 0.5, 0.6, 0.7):
            for with_related in (True, False):
                rec, prec, size = [], [], []
                for _cid, res, pages, arts in items:
                    ev = res.get("evidence", [])
                    if not ev:
                        rec.append(0.0); prec.append(0.0); size.append(0); continue
                    top = ev[0].get("score", 0.0) or 0.0
                    kept = [e for e in ev if (e.get("score", 0.0) or 0.0) >= ratio * top]
                    kept_ids = {e["passage_id"] for e in kept}
                    rel = [r for r in res.get("related_passages", []) if r.get("source_seed") in kept_ids] if with_related else []
                    delivered = kept + rel
                    n = sum(pertinent(p, pages, arts) for p in delivered)
                    rec.append(1.0 if n else 0.0); prec.append(n / len(delivered)); size.append(len(delivered))
                print(f"{m:8} | {ratio:.1f}   | {'sí' if with_related else 'no'}    | {mean(rec):.2f}   | {mean(prec):.2f}      | {mean(size):.1f}")
    print("\n=== OPCIÓN A (ADA): antes = evidencia + grafo | después = solo evidencia directa ===")
    print("mode     | conjunto | recall entregado | precisión | pasajes medios | pertinentes entregados (total)")
    for m, items in cutoff_inputs.items():
        for label, use_rel in (("antes", True), ("después", False)):
            rec, prec, size, tot = [], [], [], 0
            for _cid, res, pages, arts in items:
                delivered = res.get("evidence", []) + (res.get("related_passages", []) if use_rel else [])
                n = sum(pertinent(x, pages, arts) for x in delivered)
                tot += n
                rec.append(1.0 if n else 0.0); prec.append(n / len(delivered) if delivered else 0.0); size.append(len(delivered))
            print(f"{m:8} | {label:8} | {mean(rec):.2f}             | {mean(prec):.2f}      | {mean(size):.1f}            | {tot}")
    print("\n=== VARIANTE A' (simulación): evidencia directa + referencias cruzadas del pasaje de rango 1 ===")
    print("mode     | recall entregado | precisión | pasajes medios | pertinentes entregados (total)")
    for m, items in cutoff_inputs.items():
        rec, prec, size, tot = [], [], [], 0
        kept_refs = []
        for cid, res, pages, arts in items:
            ev = res.get("evidence", [])
            rector = ev[0]["passage_id"] if ev else None
            refs = [r for r in res.get("related_passages", []) if r.get("source_seed") == rector]
            kept_refs += [f"{cid}:{r['passage_id']}<-{rector}" for r in refs]
            delivered = ev + refs
            n = sum(pertinent(x, pages, arts) for x in delivered)
            tot += n
            rec.append(1.0 if n else 0.0); prec.append(n / len(delivered) if delivered else 0.0); size.append(len(delivered))
        print(f"{m:8} | {mean(rec):.2f}             | {mean(prec):.2f}      | {mean(size):.1f}            | {tot}")
        print(f"   referencias conservadas ({len(kept_refs)}): {kept_refs}")
    print("\nReferencias cruzadas excluidas por la opción A (relación, objetivo pertinente?):")
    for m, items in cutoff_inputs.items():
        lost = []
        for cid, res, pages, arts in items:
            for r in res.get("related_passages", []):
                flag = "PERTINENTE" if pertinent(r, pages, arts) else "-"
                lost.append(f"{cid}:{r['passage_id']}<-{r.get('source_seed')} [{r.get('relation')}] {flag}")
        sole = [cid for cid, res, pages, arts in items
                if not any(pertinent(x, pages, arts) for x in res.get("evidence", []))
                and any(pertinent(x, pages, arts) for x in res.get("related_passages", []))]
        print(f"{m}: {len(lost)} excluidas; consultas cuya única evidencia pertinente venía del grafo: {sole or 'ninguna'}")
        for entry in lost:
            print(f"   {entry}")
    print("Nota: métricas de recuperación por localizadores; no miden calidad normativa ni entailment.")


if __name__ == "__main__":
    main()

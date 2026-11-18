#!/usr/bin/env python3
"""R1 - Reserva de campeones de canal: evaluacion de RECUPERACION sin LLM (benchmark_v2 DEV, test_sealed bloqueado).

Para cada pregunta DEV se recupera con el RRE real (modo HYBRID, R3 segun el entorno) usando las mismas consultas
ya registradas en el diagnostico de Fase 11 (forma DICT y forma LLM: no se traduce de nuevo, no hay llamadas a
proveedores), con RRE_CHANNEL_CHAMPIONS desactivado y activado. Se mide si la evidencia minima esperada (o un pasaje
de texto identico) llega al paquete entregado al modelo (evidencia directa + relacionada), igual que la evaluacion.

Uso: python scripts/eval_r1_channel_champions.py   ->  data/eval/fix3/r1_channel_champions_dev.json
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "scripts")]
import eval_llm_shadow as E  # noqa: E402

DIAG = os.path.join(ROOT, "data", "eval", "fase11", "diag_retrieval_dev.json")
OUT = os.path.join(ROOT, "data", "eval", "fix3", "r1_channel_champions_dev.json")


def main():
    items, meta = E.load_items("dev", False)
    by_id = {it["id"]: it for it in items}
    diag = json.load(open(DIAG, encoding="utf-8"))["per_query"]
    from rre_engine import ReasoningRetrievalEngine
    rre = ReasoningRetrievalEngine(enable_ood_detector=True)
    rows = []
    for q in diag:
        it = by_id.get(q["id"])
        if not it:
            continue
        res = {}
        for flag in ("0", "1"):
            os.environ["RRE_CHANNEL_CHAMPIONS"] = flag
            r = rre.retrieve(q["query_used"], top_k=5, domain_query=it["text"])
            bundle = [e["passage_id"] for e in r.get("evidence", [])] + [e["passage_id"] for e in r.get("related_passages", [])]
            anchors = it["minimum_evidence"]
            hit = all(E.expand(a["passage_ids"]) & set(bundle) for a in anchors) if anchors else None
            res[flag] = {"status": r.get("status"), "bundle": bundle, "hit": hit,
                         "champions": (r.get("channel_champions") or {})}
        rows.append({"id": q["id"], "form": q["form"], "expected": it["auto_labels"]["expected_behavior"],
                     "off": res["0"], "on": res["1"], "changed": res["0"]["bundle"] != res["1"]["bundle"]})
    os.environ.pop("RRE_CHANNEL_CHAMPIONS", None)
    ans = [r for r in rows if r["expected"] == "RESPONDER"]
    summ = {
        "consultas": len(rows), "respondibles": len(ans),
        "hit_off": sum(1 for r in ans if r["off"]["hit"]), "hit_on": sum(1 for r in ans if r["on"]["hit"]),
        "ganadas": sorted(f"{r['id']}/{r['form']}" for r in ans if r["on"]["hit"] and not r["off"]["hit"]),
        "perdidas": sorted(f"{r['id']}/{r['form']}" for r in ans if r["off"]["hit"] and not r["on"]["hit"]),
        "paquetes_cambiados": sum(1 for r in rows if r["changed"]),
        "paquetes_cambiados_no_respondibles": sorted(f"{r['id']}/{r['form']}" for r in rows if r["changed"] and r["expected"] != "RESPONDER"),
        "scope_preference_R3": os.environ.get("RRE_ENABLE_SCOPE_PREFERENCE", ""),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"benchmark": meta, "summary": summ, "rows": rows}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(summ, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

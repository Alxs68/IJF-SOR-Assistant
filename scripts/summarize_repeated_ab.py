#!/usr/bin/env python3
"""Resume varias corridas A/B (scripts/eval_ab_dev.py) de la misma configuracion para separar el efecto de los
cambios de la variabilidad del modelo. Sin llamadas al LLM.

Uso: python scripts/summarize_repeated_ab.py data/eval/fix3/ab_fix3_run1.json data/eval/fix3/ab_fix3_run2.json ...
     -> imprime y guarda data/eval/fix3/resumen_repetido.json
"""
import json
import os
import statistics
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import llm_cost as C  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOOD = "ACEPTADA_CON_EVIDENCIA_ESPERADA"
WRONG = ("RESPONDIDA_DEBIA_ABSTENERSE_O_ACLARAR", "ACEPTADA_EVIDENCIA_OTRO_AMBITO", "ACEPTADA_CIFRA_SIN_RESPALDO",
         "ACEPTADA_SIN_EVIDENCIA_ESPERADA", "ACLARACION_EN_PREGUNTA_RESPONDIBLE", "ACLARACION_EN_LUGAR_DE_ABSTENCION")


def metrics(rows):
    beh = lambda r: r["expected_behavior"]
    return {
        "respondibles_correctas": sum(1 for r in rows if beh(r) == "RESPONDER" and r["outcome"] == GOOD),
        "incorrectas_o_dudosas": sum(1 for r in rows if r["outcome"] in WRONG),
        "aclaraciones_correctas": sum(1 for r in rows if r["outcome"] == "ACLARACION_SOLICITADA"),
        "abstenciones_legitimas": sum(1 for r in rows if r["outcome"] == "ABSTENCION_LEGITIMA"),
        "sin_generacion": sum(1 for r in rows if r["outcome"] == "ABSTENCION_SIN_GENERACION"),
        "proveedores": dict(Counter(r.get("provider") for r in rows if r.get("provider"))),
    }


def main(paths):
    runs = [json.load(open(p, encoding="utf-8")) for p in paths]
    # Version efectiva del modelo y consumo por corrida. Dos corridas con versiones distintas NO son equivalentes:
    # se informan, pero se excluyen de la comparacion agregada.
    por_corrida = []
    for p, r in zip(paths, runs):
        rows = r["per_variant"]["A"] + r["per_variant"]["B"]
        vs = sorted(C.versions(rows))
        led = {v: C.ledger(r["per_variant"][v]) for v in ("A", "B")}
        led["total"] = C.ledger(rows)
        por_corrida.append({"archivo": p, "versiones_modelo": vs, "gemini_only": r.get("gemini_only"),
                            "bloqueada": r.get("blocked"), "completadas": r.get("completed_items"),
                            "consumo": {k: {x: v[x] for x in ("tokens_entrada", "tokens_salida", "tokens_razonamiento",
                                                               "coste_estimado_usd", "coste_estimado_cop")}
                                        for k, v in led.items()}})
    ref = por_corrida[0]["versiones_modelo"] if por_corrida else []
    homogeneas = [i for i, c in enumerate(por_corrida)
                  if c["versiones_modelo"] == ref and len(ref) == 1 and ref != ["version_desconocida"] and not c["bloqueada"]]
    excluidas = [por_corrida[i]["archivo"] for i in range(len(por_corrida)) if i not in homogeneas]
    runs = [runs[i] for i in homogeneas]
    paths = [paths[i] for i in homogeneas]
    if not runs:
        rep = {"por_corrida": por_corrida, "aviso": "Ninguna corrida homogenea (version unica y sin bloqueo): no se agrega."}
        print(json.dumps(rep, ensure_ascii=False, indent=1))
        return
    per = {v: [metrics(r["per_variant"][v]) for r in runs] for v in ("A", "B")}
    agg = {}
    for v, ms in per.items():
        agg[v] = {k: {"por_corrida": [m[k] for m in ms],
                      "media": round(statistics.mean(m[k] for m in ms), 2),
                      "min": min(m[k] for m in ms), "max": max(m[k] for m in ms)}
                  for k in ms[0] if k != "proveedores"}
        agg[v]["proveedores"] = [m["proveedores"] for m in ms]
    stab = defaultdict(lambda: {"A": [], "B": []})
    for r in runs:
        for v in ("A", "B"):
            for row in r["per_variant"][v]:
                stab[row["id"]][v].append(row["outcome"])
    estables = {"B_siempre_mejor": [], "B_siempre_peor": [], "variable": []}
    for qid, d in sorted(stab.items()):
        a = [o == GOOD for o in d["A"]]
        b = [o == GOOD for o in d["B"]]
        wa = [o in WRONG for o in d["A"]]
        wb = [o in WRONG for o in d["B"]]
        if all(b) and not any(a) or (not any(wb) and all(wa)):
            estables["B_siempre_mejor"].append(qid)
        elif all(a) and not any(b) or (all(wb) and not any(wa)):
            estables["B_siempre_peor"].append(qid)
        elif len(set(d["A"] + d["B"])) > 1:
            estables["variable"].append(qid)
    rep = {"corridas": paths, "por_corrida": por_corrida, "excluidas_por_version_o_bloqueo": excluidas,
           "version_modelo_comun": ref,
           "por_variante": agg, "estabilidad_por_pregunta": estables,
           "detalle": {k: v for k, v in sorted(stab.items())}}
    out = os.path.join(ROOT, "data", "eval", "fix3", "resumen_repetido.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(rep, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"por_corrida": por_corrida, "excluidas_por_version_o_bloqueo": excluidas,
                      "por_variante": agg, "estabilidad_por_pregunta": estables}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])

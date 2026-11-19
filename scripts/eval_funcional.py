"""Evaluacion funcional trazada del flujo completo CONSULTA -> RECUPERACION -> CONTEXTO -> LLM -> DIG -> RESPUESTA.

Se ejecuta con el directorio de trabajo en la raiz de la version a evaluar (base o candidata) y usa la misma via
que la interfaz (RagEngine.query). No lee ni muestra secretos: las claves llegan por el entorno del contenedor.
No usa test_sealed. Pausa entre consultas para respetar el limite de peticiones del proveedor.

  python eval_funcional.py --consultas consultas_funcionales_v1.json --out resultados.jsonl --etiqueta base
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import sys
import time

SOR_ID = re.compile(r"SOR-2026-08-(P\d+-S\d+)")


def short(pid):
    m = SOR_ID.search(pid or "")
    return m.group(1) if m else pid


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--consultas", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--etiqueta", required=True)
    ap.add_argument("--solo", default="", help="ids separados por coma")
    ap.add_argument("--pausa", type=float, default=12.0)
    a = ap.parse_args(argv)

    root = os.getcwd()
    sys.path[:0] = [root, os.path.join(root, "src")]
    os.environ.setdefault("IJF_SOR_EDITION", "2026-08")
    from rag_engine import RagEngine  # algunos modulos reconfiguran stdout al importarse: sin redireccion aqui
    eng = RagEngine(root)
    ada = eng.ada
    data = json.load(open(a.consultas, encoding="utf-8"))
    solo = {x.strip() for x in a.solo.split(",") if x.strip()}

    cap = {}
    orig_call, orig_retrieve, orig_analyze = ada._call_llm, ada.rre.retrieve, ada.analyze_situation

    def call(prompt):
        t0 = time.time()
        res = orig_call(prompt)
        text, meta = (res if isinstance(res, tuple) else (res, {}))
        kind = "analisis" if '"evidence_quotes"' in (prompt or "") or "Respuesta JSON" in (prompt or "") else (
            "traduccion" if "English translation" in (prompt or "") else "otra")
        meta = meta or {}
        cap.setdefault("llm", []).append({
            "tipo": kind, "s": round(time.time() - t0, 1), "proveedor": meta.get("successful_provider"),
            "modelo": meta.get("successful_model"), "fallback": meta.get("fallback_triggered"),
            # Solo tipo y codigo HTTP: el mensaje del proveedor podria contener la URL con la clave.
            "errores": {p: {"tipo": (e or {}).get("error_type"), "http": (e or {}).get("status_code")}
                        for p, e in (meta.get("errors") or {}).items()},
            "json_contract": meta.get("json_contract"), "texto": text})
        if kind == "analisis":
            cap["prompt_contexto_ids"] = sorted(set(SOR_ID.findall(prompt.split("POLÍTICA TRANSVERSAL")[0])))
        return res

    def retrieve(q, *args, **kw):
        r = orig_retrieve(q, *args, **kw)
        if kw.get("expand_graph", True):
            cap["rre"] = {"consulta_en": q, "estado": r.get("status"),
                          "evidencia": [short(e.get("passage_id")) for e in r.get("evidence", [])],
                          "relacionados": [short(e.get("passage_id")) for e in r.get("related_passages", [])],
                          "campeones": r.get("channel_champions")}
        return r

    def analyze(*args, **kw):
        r = orig_analyze(*args, **kw)
        cap["ada"] = r
        return r

    ada._call_llm, ada.rre.retrieve, ada.analyze_situation = call, retrieve, analyze

    with open(a.out, "w", encoding="utf-8") as fh:
        for c in data["consultas"]:
            if solo and c["id"] not in solo:
                continue
            cap.clear()
            t0 = time.time()
            err = None
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    ui = eng.query(c["q"], language="en" if c["lang"] == "en" else "es")
            except Exception as e:  # pragma: no cover - se registra
                ui, err = {}, f"{type(e).__name__}: {e}"[:300]
            r = cap.get("ada") or {}
            dig = r.get("decision_integrity") or {}
            sa = r.get("structured_answer") or {}
            ctx = [short(e.get("passage_id")) for e in [*(r.get("evidence") or []), *(r.get("related_passages") or [])]]
            analysis_calls = [x for x in cap.get("llm", []) if x["tipo"] == "analisis"]
            status = r.get("status")
            origen = ("SIN_RESPUESTA" if status != "SUCCESS" else
                      "LLM" if analysis_calls and analysis_calls[-1]["texto"] else "LOCAL")
            exp = set(c["esperado"])
            rec = {
                "etiqueta": a.etiqueta, "id": c["id"], "cat": c["cat"], "lang": c["lang"], "respondible": c["respondible"],
                "q": c["q"], "esperado": c["esperado"], "s": round(time.time() - t0, 1), "error": err,
                "consulta_en": (cap.get("rre") or {}).get("consulta_en"),
                "recuperado": (cap.get("rre") or {}).get("evidencia"),
                "relacionados": (cap.get("rre") or {}).get("relacionados"),
                "campeones": (cap.get("rre") or {}).get("campeones"),
                "contexto": ctx, "contexto_prompt": cap.get("prompt_contexto_ids"),
                "esperado_recuperado": sorted(exp & set((cap.get("rre") or {}).get("evidencia") or []) |
                                              exp & set((cap.get("rre") or {}).get("relacionados") or [])),
                "esperado_en_contexto": sorted(exp & set(ctx)),
                "llm": [{k: v for k, v in x.items() if k != "texto"} for x in cap.get("llm", [])],
                "respuesta_llm": analysis_calls[-1]["texto"] if analysis_calls else None,
                "dig": {"decision": dig.get("decision"), "fallidos": dig.get("failed_checks"),
                        "detalle": [ch for ch in dig.get("checks", []) if not ch.get("passed")],
                        "poda": dig.get("pruning"), "final": dig.get("final_visible_check"),
                        "reparaciones": dig.get("attribution_repairs"),
                        "completado": dig.get("attribution_completion"),
                        "verificacion": dig.get("verification")} if dig else None,
                "tokens": r.get("token_usage"),
                "reensamblado": r.get("reassembly"), "origen_respuesta": r.get("response_origin"),
                "estado": status, "modo": r.get("mode"), "origen": origen,
                "respuesta_final": {k: sa.get(k) for k in ("summary", "normative_basis", "conditions_and_exceptions",
                                                          "extended_analysis", "limitations")},
                "texto_ui": (ui or {}).get("answer"),
            }
            fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
            fh.flush()
            print(f"{c['id']} {status} origen={origen} dig={rec['dig'] and rec['dig']['decision']} "
                  f"fallidos={rec['dig'] and rec['dig']['fallidos']} esperado_ctx={rec['esperado_en_contexto']} "
                  f"prov={[x['proveedor'] for x in rec['llm']]} {rec['s']}s", flush=True)
            time.sleep(a.pausa)
    return 0


if __name__ == "__main__":
    sys.exit(main())

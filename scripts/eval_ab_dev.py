#!/usr/bin/env python3
"""Comparacion A/B controlada sobre las 41 preguntas DEV de benchmark_v2 (test_sealed bloqueado).

  A = version anterior (la desplegada en la instancia experimental: R3 + DIG v2 + DIG v3 + modo JSON)
  B = A + LLM_JSON_SCHEMA=1 (esquema estructurado, validacion, 1 reintento) + ADA_PROMPT_RIGOR=1 (regla 14)

Condiciones identicas: mismo proceso, mismo corpus, mismo DIG, MISMA traduccion y MISMA recuperacion
(la traduccion ES->EN se calcula una vez por pregunta y se reutiliza en A y B), y A y B se ejecutan
intercalados pregunta a pregunta para compartir el estado del proveedor. Solo cambia la generacion.
Se registran respuestas, evidencias, entradas EXACTAS del DIG, decisiones y errores (via
eval_llm_shadow.score_run). Si el proveedor falla de forma persistente se detiene y guarda lo hecho,
indicando las preguntas pendientes; no se estima nada.
Uso (con las variables de la instancia experimental activas):
  python scripts/eval_ab_dev.py --sleep 4 --out data/eval/dig_v3/ab_dev.json
"""
import argparse
import functools
import json
import os
import sys
import time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "scripts")]
import eval_llm_shadow as E  # noqa: E402
import llm_cost as C  # noqa: E402

# Errores que DETIENEN toda la evaluacion de inmediato (facturacion, cuota, saldo, autenticacion): seguir solo
# produciria abstenciones por API, gastaria tiempo y no mediria nada. Los 503 (saturacion temporal) no detienen.
STOP_STATUS = {401, 402, 403, 429}
STOP_TYPES = {"AUTH", "QUOTA"}
STOP_WORDS = ("billing", "prepay", "prepayment", "credits", "quota", "exceeded your current", "factura", "saldo")


def stop_reason(calls):
    for c in calls:
        for prov, e in ((c.get("meta") or {}).get("errors") or {}).items():
            msg = str((e or {}).get("message") or "").lower()
            if (e or {}).get("status_code") in STOP_STATUS or (e or {}).get("error_type") in STOP_TYPES \
                    or any(w in msg for w in STOP_WORDS):
                return f"{prov} HTTP {(e or {}).get('status_code')} {(e or {}).get('error_type')}: {msg[:200]}"
    return None

REQUIRED = {"DIG_V3": "1", "LLM_JSON_MODE": "1", "RRE_ENABLE_SCOPE_PREFERENCE": "1", "DIG_NUMBER_NORMALIZATION": "v2"}
VARIANT_SETS = {
    # A/B anterior: esquema JSON + regla 14
    "rigor": {"A": {"LLM_JSON_SCHEMA": "0", "ADA_PROMPT_RIGOR": "0", "ADA_UNIFIED_ANSWER": "0"},
              "B": {"LLM_JSON_SCHEMA": "1", "ADA_PROMPT_RIGOR": "1", "ADA_UNIFIED_ANSWER": "0"}},
    # Respuesta unica: A = comportamiento anterior (dos niveles), B = respuesta unica con validacion integral.
    # Ambas con el esquema JSON (conservado tras la evaluacion A/B) y sin la regla 14.
    "unified": {"A": {"LLM_JSON_SCHEMA": "1", "ADA_PROMPT_RIGOR": "0", "ADA_UNIFIED_ANSWER": "0"},
                "B": {"LLM_JSON_SCHEMA": "1", "ADA_PROMPT_RIGOR": "0", "ADA_UNIFIED_ANSWER": "1"}},
    # Correcciones de la auditoria de trazabilidad: A = experimental actual (esquema JSON), B = respuesta unica
    # + R1 (campeones de canal) + R2 (traduccion de cualquier idioma) + R5a (DIG-11 subordinado) + R5b (DIG-06
    # referencias e identificadores) + R6/R8 (contrato y aclaracion). Mismo proveedor y mismo DIG base.
    "fix3": {"A": {"LLM_JSON_SCHEMA": "1", "ADA_PROMPT_RIGOR": "0", "ADA_UNIFIED_ANSWER": "0", "RRE_CHANNEL_CHAMPIONS": "0",
                   "ADA_TRANSLATE_ANY_LANG": "0", "DIG_11_SUBORDINATE": "0", "DIG06_REFS": "0"},
             "B": {"LLM_JSON_SCHEMA": "1", "ADA_PROMPT_RIGOR": "0", "ADA_UNIFIED_ANSWER": "1", "RRE_CHANNEL_CHAMPIONS": "1",
                   "ADA_TRANSLATE_ANY_LANG": "1", "DIG_11_SUBORDINATE": "1", "DIG06_REFS": "1"}},
}
VARIANTS = VARIANT_SETS["rigor"]


def set_env(kv):
    for k, v in kv.items():
        os.environ[k] = v
    # ADA_UNIFIED_ANSWER se lee al importar decision_integrity: se aplica tambien al modulo ya cargado.
    import decision_integrity as _D
    _D.FIX_ALL_VISIBLE_FIELDS = os.environ.get("ADA_UNIFIED_ANSWER", "").strip() == "1"
    _D.FIX_DIG11_SUBORDINATE = os.environ.get("DIG_11_SUBORDINATE", "").strip() == "1"
    _D.FIX_DIG06_REFS = os.environ.get("DIG06_REFS", "").strip() == "1"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sleep", type=float, default=4.0)
    ap.add_argument("--max-items", type=int)
    ap.add_argument("--out", default=os.path.join(ROOT, "data/eval/dig_v3/ab_dev.json"))
    ap.add_argument("--resume", help="informe anterior incompleto: conserva sus preguntas completadas y sigue con las pendientes")
    ap.add_argument("--gemini-only", action="store_true",
                    help="solo Gemini: aborta si GROQ_API_KEY esta en el entorno y desactiva el respaldo en esta ejecucion")
    ap.add_argument("--set", choices=sorted(VARIANT_SETS), default="rigor",
                    help="rigor = A/B anterior (esquema + regla 14); unified = respuesta unica frente a la anterior")
    a = ap.parse_args(argv)
    global VARIANTS
    VARIANTS = VARIANT_SETS[a.set]
    bad = {k: os.environ.get(k) for k, v in REQUIRED.items() if os.environ.get(k) != v}
    if bad:
        print("ABORTO: faltan las variables de la version anterior (instancia experimental):", bad)
        return 2
    items, meta = E.load_items("dev", False)
    if a.max_items:
        items = items[: a.max_items]
    before = E.sha_file(E.CORPUS)
    from ada_assistant import ArbitrationDecisionAssistant
    import decision_integrity as D
    ada = ArbitrationDecisionAssistant()
    if a.gemini_only:
        # Solo en ESTE proceso (no cambia el .env ni la configuracion de la aplicacion): Gemini principal, sin
        # respaldo y sin clave de Groq. Hace falta anular la clave aqui porque src/llm_provider.py carga el .env al
        # importarse y rellena GROQ_API_KEY aunque se haya quitado de la sesion de PowerShell.
        os.environ["GROQ_API_KEY"] = ""
        ada.llm_manager.groq_api_key = None
        ada.llm_manager.primary_provider = "Gemini"
        ada.llm_manager.fallback_policy = "manual"
        if not ada.llm_manager.gemini_api_key:
            print("ABORTO: --gemini-only sin clave de Gemini.")
            return 5
        print("Solo Gemini: respaldo desactivado y clave de Groq anulada en este proceso.")
    status = E.sanitize(ada.llm_manager.get_provider_status())
    rec = E.Recorder(ada._call_llm)
    ada._call_llm = rec
    # misma traduccion para A y B (una llamada por pregunta)
    # La cache distingue el modo de traduccion (R2): con ADA_TRANSLATE_ANY_LANG distinto, A y B no comparten traduccion.
    _orig_tr, _tr_cache = ada._translate_to_technical_english, {}

    def _cached_translation(q):
        key = (q, os.environ.get("ADA_TRANSLATE_ANY_LANG", ""))
        if key not in _tr_cache:
            _tr_cache[key] = _orig_tr(q)
        return _tr_cache[key]
    ada._translate_to_technical_english = _cached_translation
    gate = ada._decision_integrity_gate()
    orig_eval, dig_calls = gate.evaluate, []

    def keep(p):
        return {k: p.get(k) for k in ("passage_id", "text_original", "pdf_page_index", "page", "article_id")}

    def capture(answer, query, search_query_en, evidence, related, supplementary_texts=(), **kw):
        res = orig_eval(answer, query, search_query_en, evidence, related, supplementary_texts=supplementary_texts, **kw)
        dig_calls.append({"answer": answer, "query": query, "search_query_en": search_query_en,
                          "evidence": [keep(p) for p in evidence], "related": [keep(p) for p in related],
                          "supplementary_texts": list(supplementary_texts or []),
                          "instruction_text": kw.get("instruction_text", ""),
                          "result": {"decision": res.get("decision"), "failed_checks": res.get("failed_checks"),
                                     "version": res.get("version")}})
        return res
    gate.evaluate = capture
    passages = json.load(open(E.CORPUS, encoding="utf-8"))
    page_text = {}
    for p in passages:
        page_text.setdefault(p["pdf_page_index"], p["text_original"])
    rows = {"A": [], "B": []}
    blocked, api_streak, done = None, 0, []
    if a.resume:
        prev = json.load(open(a.resume, encoding="utf-8"))
        keep_ids = [p["id"] for p in prev["pairs"]
                    if not (p["A"]["outcome"] == "ABSTENCION_SIN_GENERACION" and p["B"]["outcome"] == "ABSTENCION_SIN_GENERACION")]
        for v in ("A", "B"):
            rows[v] = [r for r in prev["per_variant"][v] if r["id"] in keep_ids]
        done = list(keep_ids)
        print("reanudando: conservadas", len(done), "preguntas; se repiten las que quedaron sin generacion en A y B")
    for it in items:
        if it["id"] in done:
            continue
        both_api = True
        for v in ("A", "B"):
            set_env(VARIANTS[v])
            n0, d0, t0 = len(rec.calls), len(dig_calls), time.perf_counter()
            try:
                out = ada.analyze_situation(it["text"], top_k=5)
            except Exception as e:
                out = {"status": "EXCEPTION", "error": E.sanitize(repr(e)[:300])}
            calls = rec.calls[n0:]
            row = E.score_run(it, out, calls, page_text, D.numbers_in)
            row["dig_input"] = E.sanitize(dig_calls[d0:][-1]) if dig_calls[d0:] else None
            row["variant"], row["run"] = v, 0
            row["json_contract"] = next(((c.get("meta") or {}).get("json_contract") for c in calls if c.get("is_analysis")), None)
            row["total_latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            rows[v].append(row)
            both_api = both_api and row["attribution"] == "API"
            print(f"[{v}] {it['id']:12} {row['status']:8} {row['outcome']:42} {row['attribution'] or ''} "
                  f"{'/'.join(row.get('model_versions') or [])}", flush=True)
            if a.gemini_only and any(p != "Gemini" for p in row.get("providers_used") or []):
                blocked = f"proveedor distinto de Gemini en {it['id']} ({row.get('providers_used')}): se detiene"
            why = stop_reason(calls)
            if why:
                blocked = "ERROR DE FACTURACION/CUOTA/AUTENTICACION: " + why
            if blocked:
                break
            time.sleep(a.sleep)
        if blocked:
            break
        done.append(it["id"])
        api_streak = api_streak + 1 if both_api else 0
        if api_streak >= 3:
            blocked = "3 preguntas seguidas sin generacion en A y B por el proveedor; se detiene sin estimar"
            break
    pending = [it["id"] for it in items if it["id"] not in done]
    summ = {v: E.summarize([rows[v]]) for v in rows}
    pairs = []
    order = {it["id"]: i for i, it in enumerate(items)}
    for v in ("A", "B"):
        rows[v].sort(key=lambda r: order.get(r["id"], 999))
    for ra, rb in zip(rows["A"], rows["B"]):
        pairs.append({"id": ra["id"], "category": ra["category"], "expected_behavior": ra["expected_behavior"],
                      "A": {"status": ra["status"], "outcome": ra["outcome"], "provider": ra["provider"],
                            "dig_failed": ra["dig_failed_checks"]},
                      "B": {"status": rb["status"], "outcome": rb["outcome"], "provider": rb["provider"],
                            "dig_failed": rb["dig_failed_checks"], "json_contract": rb.get("json_contract")},
                      "same_provider": ra["provider"] == rb["provider"] and ra["provider"] is not None})
    # reproducibilidad del DIG: las entradas capturadas, reevaluadas offline con el mismo DIG, deben dar la
    # misma decision y las mismas reglas fallidas (reutilizacion de entradas sin nuevas llamadas al LLM)
    repro = {"evaluadas": 0, "identicas": 0, "distintas": []}
    for v in ("A", "B"):
        set_env(VARIANTS[v])
        for r in rows[v]:
            di = r.get("dig_input")
            if not di:
                continue
            res = orig_eval(di["answer"], di["query"], di["search_query_en"], di["evidence"], di["related"],
                            supplementary_texts=di["supplementary_texts"], instruction_text=di.get("instruction_text", ""))
            repro["evaluadas"] += 1
            if (res["decision"], sorted(res["failed_checks"])) == (di["result"]["decision"], sorted(di["result"]["failed_checks"] or [])):
                repro["identicas"] += 1
            else:
                repro["distintas"].append(f"{v}:{r['id']}")
    trans = Counter(f"{p['A']['outcome']} -> {p['B']['outcome']}" for p in pairs if p["A"]["outcome"] != p["B"]["outcome"])
    consumo = {v: C.ledger(rows[v]) for v in ("A", "B")}
    consumo["total"] = C.ledger(rows["A"] + rows["B"])
    versiones = {v: C.versions(rows[v]) for v in ("A", "B")}
    todas = sorted({k for d in versiones.values() for k in d})
    rep = {"benchmark": meta, "variants": VARIANTS, "common_env": REQUIRED, "provider_status": status,
           "gemini_only": a.gemini_only,
           "consumo": consumo, "versiones_modelo": versiones, "version_unica": len(todas) == 1, "versiones_vistas": todas,
           "blocked": blocked, "pending_items": pending, "completed_items": len(done),
           "corpus_unchanged": before == E.sha_file(E.CORPUS), "summary": summ,
           "dig_reproducibility": repro,
           "transitions_A_to_B": dict(trans), "pairs": pairs, "per_variant": rows, "per_run": [rows["A"], rows["B"]],
           "note": "Una corrida por variante: el LLM no es determinista; las diferencias de pocos casos pueden ser ruido."}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(E.sanitize(rep), fh, ensure_ascii=False, indent=2)
    for v in ("A", "B"):
        s = summ[v]
        print(v, json.dumps({k: s[k] for k in ("answerable", "control_false_positives", "legitimate_abstentions",
                                                "n_unanswerable", "dig_failed_checks")}, ensure_ascii=False))
        print(v, "api:", json.dumps(s["api"], ensure_ascii=False), "tokens:", s["tokens_total"])
    print("reproducibilidad DIG:", json.dumps(repro, ensure_ascii=False))
    print("transiciones A->B:", json.dumps(dict(trans), ensure_ascii=False, indent=1))
    print("completadas:", len(done), "pendientes:", pending, "blocked=", blocked, "corpus_unchanged=", rep["corpus_unchanged"])
    print("versiones del modelo:", todas, "UNICA" if len(todas) == 1 else "*** VARIAN: corrida no homogenea ***")
    print("consumo medido / coste estimado:", json.dumps({k: {x: consumo[k][x] for x in ("tokens_entrada", "tokens_salida",
          "tokens_razonamiento", "coste_estimado_usd", "coste_estimado_cop")} for k in consumo}, ensure_ascii=False))
    print("resultados:", a.out)
    if not rep["corpus_unchanged"]:
        return 3
    return 4 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())

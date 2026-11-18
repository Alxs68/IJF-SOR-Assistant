#!/usr/bin/env python3
"""Fase 10.4 - Evaluacion del LLM REAL a traves del flujo ADA completo, en modo SHADOW.

  * Usa ArbitrationDecisionAssistant tal cual (proveedor real configurado en .env, sin mocks).
    El unico envoltorio es un REGISTRADOR alrededor de ada._call_llm que llama a la funcion
    original y guarda texto, metadatos y latencia; no altera prompt ni respuesta.
  * El DIG (decision_integrity) actua como en produccion; nada de este script cambia decisiones.
  * Nunca se escriben claves: los mensajes de error se sanean (valores de .env y patrones de clave).
  * El resultado se evalua contra benchmark_v2 (evidencia literal, distractores de ambito,
    excepciones, referencias) y se atribuye cada fallo a RECUPERACION / GENERACION / CONTROL /
    API / EVALUACION.
  * Opcional --nli-model: el evaluador NLI experimental puntua la respuesta frente a las citas;
    se guarda como campo shadow y NO se usa en ninguna decision ni metrica de aceptacion.
Uso:
  python scripts/eval_llm_shadow.py --split dev --runs 2
  python scripts/eval_llm_shadow.py --split test_sealed --allow-test-sealed --runs 2
Si no hay credenciales o el proveedor falla, se documenta (API_ERROR) y el script termina.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from statistics import median

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
os.environ.setdefault("IJF_SOR_EDITION", "2026-08")
CORPUS = os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json")
OUT = os.path.join(ROOT, "data/eval/benchmark_v2/results/llm_shadow_{split}.json")
KEY_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY")
KEY_PATTERNS = re.compile(r"(key=)[^&\s\"']+|AIza[0-9A-Za-z_\-]{20,}|gsk_[0-9A-Za-z]{20,}|Bearer\s+[0-9A-Za-z._\-]{16,}")

from experimental.benchmark_access import expand, load_items  # noqa: E402


def sha_file(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sanitize(obj):
    secrets = [os.environ.get(k) for k in KEY_VARS if os.environ.get(k)]

    def clean(s):
        for v in secrets:
            s = s.replace(v, "[REDACTED]")
        return KEY_PATTERNS.sub(lambda m: (m.group(1) or "") + "[REDACTED]", s)
    if isinstance(obj, str):
        return clean(obj)
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return obj


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))] if xs else None


class Recorder:
    """Llama a la funcion original y guarda lo ocurrido (sin modificar nada)."""

    def __init__(self, fn):
        self.fn, self.calls = fn, []

    def __call__(self, prompt):
        t0 = time.perf_counter()
        try:
            text, meta = self.fn(prompt)
            err = None
        except Exception as e:  # se re-lanza: el flujo productivo decide
            self.calls.append({"latency_ms": round((time.perf_counter() - t0) * 1000, 1), "exception": sanitize(repr(e)[:300]),
                               "is_analysis": "evidence_quotes" in prompt,
                               "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(), "prompt_chars": len(prompt)})
            raise
        self.calls.append({"latency_ms": round((time.perf_counter() - t0) * 1000, 1), "text": text, "meta": sanitize(meta or {}),
                           "is_analysis": "evidence_quotes" in prompt,
                           "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(), "prompt_chars": len(prompt),
                           "exception": err})
        return text, meta


def span_hit(page_text, quote, anchor):
    """El fragmento citado solapa el ancla (misma pagina): ambos localizados en el texto de la pagina.

    Usa la MISMA normalizacion que el DIG (decision_integrity.norm, con las correcciones activas en la
    corrida: comillas, espacios, 'N .N', guion de corte de linea, variantes tipograficas) y, como DIG-09,
    divide la cita por el marcador de salto de pagina del texto cosido. No relaja nada: la cita debe seguir
    apareciendo en el texto de la pagina y solapar el ancla."""
    if not quote or not page_text:
        return False
    import decision_integrity as D
    pt, a = D.norm(page_text), D.norm(anchor["snippet"])
    j = pt.find(a)
    if j < 0:
        return False
    qn = D.norm(quote)
    segments = [x.strip() for x in D.PAGE_BREAK.split(qn) if len(x.split()) >= 3] or [qn]
    for q in segments:
        i = pt.find(q)
        if i >= 0 and i < j + len(a) and j < i + len(q):
            return True
    return False


def score_run(item, out, rec_calls, page_text, numbers_in):
    beh = item["auto_labels"]["expected_behavior"]
    st = out.get("status")
    di = out.get("decision_integrity") or {}
    bundle = [e.get("passage_id") for e in (out.get("evidence") or []) + (out.get("related_passages") or [])]
    analysis = [c for c in rec_calls if c.get("is_analysis")]
    llm = analysis[-1] if analysis else None  # las llamadas de traduccion ES->EN no cuentan como generacion
    raw = (llm or {}).get("text")
    meta = (llm or {}).get("meta") or {}
    from decision_integrity import parse_answer
    parsed = parse_answer(raw) or {}
    # Respuesta unica: se puntua el contenido que vio el usuario (tras la poda y la validacion final), no el crudo.
    if isinstance(di.get("validated_answer"), dict):
        parsed = dict(parsed, **{k: v for k, v in di["validated_answer"].items()
                                 if k in ("summary", "normative_basis", "conditions_and_exceptions",
                                          "extended_analysis", "limitations")})
    quotes = [q for q in (parsed.get("evidence_quotes") or []) if isinstance(q, dict)]
    pages_of = {}
    for e in (out.get("evidence") or []) + (out.get("related_passages") or []):
        pages_of[e.get("passage_id")] = e.get("pdf_page_index") or e.get("page")

    def hits(anchors):
        res = []
        for a in anchors:
            res.append(any(span_hit(page_text.get(a["page"]), q.get("quote"), a) for q in quotes))
        return res
    r = {"id": item["id"], "category": item["category"], "language": item["language"], "expected_behavior": beh,
         "status": st, "dig_decision": di.get("decision"), "dig_failed_checks": di.get("failed_checks"),
         "llm_called": llm is not None, "llm_text_present": bool(raw),
         "provider": meta.get("successful_provider"), "model": meta.get("successful_model"),
         "api_errors": meta.get("errors") or {}, "token_usage": (out.get("token_usage") or meta.get("token_usage")),
         "llm_latency_ms": (llm or {}).get("latency_ms"), "answerability": parsed.get("answerability"),
         "n_quotes": len(quotes), "quotes": [{"passage_id": q.get("passage_id"), "quote": (q.get("quote") or "")[:400]} for q in quotes],
         "bundle": bundle, "auxiliary_llm_calls": len(rec_calls) - len(analysis),
         "summary": ((out.get("structured_answer") or {}).get("summary") or "")[:1500] if st == "SUCCESS" else None}
    # Registro por llamada (traduccion y analisis): proveedor, version real del modelo, tokens medidos y errores.
    # Los tokens son los que devolvio el proveedor (medidos); el coste se ESTIMA aparte (scripts/llm_cost.py).
    r["calls"] = []
    for c in rec_calls:
        cm = c.get("meta") or {}
        r["calls"].append({
            "kind": "analisis" if c.get("is_analysis") else "traduccion",
            "provider": cm.get("successful_provider"), "model": cm.get("successful_model"),
            "model_version": cm.get("model_version"), "model_versions_intentos": cm.get("model_versions"),
            "tokens": cm.get("token_usage"), "tokens_intentos": cm.get("attempts_token_usage"),
            "errors": {p: {"type": (e or {}).get("error_type"), "status": (e or {}).get("status_code")}
                       for p, e in (cm.get("errors") or {}).items()},
            "latency_ms": c.get("latency_ms"), "exception": c.get("exception")})
    r["model_versions"] = sorted({v for c in r["calls"] for v in [c["model_version"], *(c["model_versions_intentos"] or [])] if v})
    r["providers_used"] = sorted({c["provider"] for c in r["calls"] if c["provider"]})
    # Fase 11A: datos completos para el diagnostico de abstenciones (no cambian la clasificacion)
    aux = [c for c in rec_calls if not c.get("is_analysis")]
    r["translation"] = ((aux[0].get("text") or "")[:400]) if aux else None
    r["llm_json"] = {k: (v[:3000] if isinstance(v, str) else v) for k, v in parsed.items()
                     if k in ("answerability", "summary", "normative_basis", "conditions_and_exceptions", "extended_analysis",
                              "limitations", "citations", "evidence_quotes", "evidence_conflicts")} if parsed else None
    r["dig_checks"] = [{"code": c.get("code"), "detail": str(c.get("detail") or "")[:900]}
                       for c in (di.get("checks") or []) if not c.get("passed")]
    r["bundle_detail"] = [{"passage_id": e.get("passage_id"), "page": e.get("pdf_page_index") or e.get("page"),
                           "article_id": e.get("article_id"), "lane": lane}
                          for lane, lst in (("evidence", out.get("evidence") or []), ("related", out.get("related_passages") or []))
                          for e in lst]
    r["retrieval_status"] = out.get("status") if not di else None
    r["abstain_reason_text"] = ((out.get("structured_answer") or {}).get("limitations") or "")[:400] if st != "SUCCESS" else None
    ev, dis = item["minimum_evidence"], item["wrong_scope_distractors"]
    # Fase 11A: un pasaje de la misma pagina con texto identico cuenta como la misma evidencia
    ev_bundle = all(expand(a["passage_ids"]) & set(bundle) for a in ev) if ev else None
    ev_hit, dis_hit = hits(ev), hits(dis)
    r.update(evidence_in_bundle=ev_bundle, quotes_hit_evidence=any(ev_hit) if ev else None,
             quotes_hit_all_evidence=all(ev_hit) if ev else None, quotes_hit_distractor=any(dis_hit) if dis else None)
    r["scope_error"] = bool(dis and any(dis_hit) and not any(ev_hit))
    exc, xr = item["exceptions_to_preserve"], item["mandatory_cross_refs"]
    r["exceptions_quoted"] = (sum(hits(exc)) / len(exc)) if exc else None
    r["crossrefs_quoted"] = (sum(hits(xr)) / len(xr)) if xr else None
    if st == "SUCCESS":
        sa = out.get("structured_answer") or {}
        # Las cifras se comparan sobre los campos que GENERO el modelo (JSON crudo), no sobre el texto
        # ya formateado por ADA, que anade enlaces al PDF, paginas e identificadores (falso positivo v1).
        r["llm_fields"] = {k: str(parsed.get(k) or "")[:2000] for k in ("summary", "normative_basis", "conditions_and_exceptions")}
        r["numbers_not_in_quotes"] = unsupported_numbers(r["llm_fields"], quotes, numbers_in)
        # Control independiente sobre TODO lo visible (incluye extended_analysis y limitations); no cambia la clasificacion.
        r["visible_numbers_not_in_quotes"] = unsupported_numbers(
            {k: str(parsed.get(k) or "")[:3000] for k in ("summary", "normative_basis", "conditions_and_exceptions",
                                                          "extended_analysis")}, quotes, numbers_in)
        r["pruned_sentences"] = len((di.get("pruning") or {}).get("removed") or [])
        allowed = expand({p for a in ev + exc + xr for p in a["passage_ids"]})
        cited = [c.get("passage_id") for c in (sa.get("citations") or []) if isinstance(c, dict)]
        r["cited"] = cited
        r["citations_outside_expected"] = [c for c in cited if c not in allowed] if allowed else cited
    r["_llm_exception"] = bool((llm or {}).get("exception"))
    classify(r, beh)
    return r


_URL = re.compile(r"\(?https?://[^\s)\]]+\)?")


def unsupported_numbers(fields, quotes, numbers_in):
    text = _URL.sub(" ", " ".join(fields.values()))
    quoted = " ".join(q.get("quote") or "" for q in quotes)
    return sorted(set(numbers_in(text)) - set(numbers_in(quoted)))


def classify(r, beh):
    """Clasificacion del resultado y atribucion (reutilizable en --rescore)."""
    st = r["status"]
    if st == "CLARIFICATION_REQUIRED":  # respuesta unica: el asistente pidio precisar la consulta (no es dictamen)
        r["outcome"], r["attribution"] = {
            "SOLICITAR_ACLARACION": ("ACLARACION_SOLICITADA", None),
            "RESPONDER": ("ACLARACION_EN_PREGUNTA_RESPONDIBLE", "GENERACION"),
        }.get(beh, ("ACLARACION_EN_LUGAR_DE_ABSTENCION", "GENERACION"))
        return r
    if beh == "RESPONDER":
        if st == "SUCCESS":
            if r["scope_error"]:
                r["outcome"], r["attribution"] = "ACEPTADA_EVIDENCIA_OTRO_AMBITO", "CONTROL"
            elif r.get("numbers_not_in_quotes"):
                r["outcome"], r["attribution"] = "ACEPTADA_CIFRA_SIN_RESPALDO", "CONTROL"
            elif r["quotes_hit_evidence"]:
                r["outcome"], r["attribution"] = ("ACEPTADA_CON_EVIDENCIA_ESPERADA" if r["quotes_hit_all_evidence"]
                                                  else "ACEPTADA_EVIDENCIA_PARCIAL"), None
            else:
                r["outcome"], r["attribution"] = "ACEPTADA_SIN_EVIDENCIA_ESPERADA", "EVALUACION_O_CONTROL"
        else:
            if not r["llm_called"] or not r["llm_text_present"]:
                r["outcome"] = "ABSTENCION_SIN_GENERACION"
                r["attribution"] = "API" if (r["api_errors"] or r.get("_llm_exception")) else (
                    "RECUPERACION" if not r["evidence_in_bundle"] else "CONTROL_PREVIO")
            elif not r["evidence_in_bundle"]:
                r["outcome"], r["attribution"] = "ABSTENCION_EVIDENCIA_NO_RECUPERADA", "RECUPERACION"
            elif r["quotes_hit_evidence"] and not r["scope_error"]:
                r["outcome"], r["attribution"] = "ABSTENCION_CON_CITA_CORRECTA", "CONTROL (revisar: posible FN del DIG)"
            else:
                r["outcome"], r["attribution"] = "ABSTENCION_GENERACION_SIN_CITA_CORRECTA", "GENERACION"
    else:
        if st == "SUCCESS":
            r["outcome"], r["attribution"] = "RESPONDIDA_DEBIA_ABSTENERSE_O_ACLARAR", ("CONTROL" if r["llm_text_present"] else "RECUPERACION")
        else:
            r["outcome"], r["attribution"] = ("ABSTENCION_LEGITIMA" if beh != "SOLICITAR_ACLARACION"
                                              else "ABSTENCION_SIN_ACLARACION"), None
    return r


def rescore(path, numbers_in):
    """Reclasifica un informe existente SIN llamar al LLM. Para informes anteriores a llm_fields,
    las cifras se recalculan sobre el resumen almacenado sin enlaces (aproximacion documentada)."""
    rep = json.load(open(path, encoding="utf-8"))
    bench = os.path.join(ROOT, "data/eval/benchmark_v2/benchmark_v2.jsonl")
    items = {json.loads(l)["id"]: json.loads(l) for l in open(bench, encoding="utf-8") if l.strip()}
    basis = Counter()
    for run in rep["per_run"]:
        for r in run:
            ev = items[r["id"]]["minimum_evidence"]
            if ev:
                r["evidence_in_bundle_strict"] = r.get("evidence_in_bundle")
                r["evidence_in_bundle"] = all(expand(a["passage_ids"]) & set(r.get("bundle") or []) for a in ev)
            if r["status"] == "SUCCESS":
                if r.get("llm_fields"):
                    fields, b = r["llm_fields"], "llm_fields"
                else:
                    fields, b = {"summary": r.get("summary") or ""}, "summary_formateado_sin_enlaces"
                r["numbers_not_in_quotes_v1"] = r.get("numbers_not_in_quotes")
                r["numbers_not_in_quotes"] = unsupported_numbers(fields, r.get("quotes") or [], numbers_in)
                r["rescore_basis"] = b
                basis[b] += 1
            classify(r, r["expected_behavior"])
    rep["summary"] = summarize(rep["per_run"])
    rep["rescored"] = {"from": os.path.basename(path), "basis": dict(basis),
                       "reason": ("v1 contaba cifras de URLs/paginas anadidas por el formateo de ADA; "
                                  "v2 (Fase 11A) aplica equivalencia de pasajes de igual pagina y texto")}
    out = path.replace(".json", "_rescored.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    print(json.dumps(rep["summary"], ensure_ascii=False, indent=1))
    print("reclasificado:", out)
    return 0


def summarize(runs):
    rows = [r for run in runs for r in run]
    ans = [r for r in rows if r["expected_behavior"] == "RESPONDER"]
    neg = [r for r in rows if r["expected_behavior"] != "RESPONDER"]
    succ = [r for r in ans if r["status"] == "SUCCESS"]
    lat = [r["llm_latency_ms"] for r in rows if r.get("llm_latency_ms")]
    tok = [((r.get("token_usage") or {}).get("total_tokens") or 0) for r in rows]
    s = {
        "runs": len(runs), "items_per_run": len(runs[0]) if runs else 0, "n_evaluations": len(rows),
        "outcomes": dict(Counter(r["outcome"] for r in rows)),
        "attribution": dict(Counter(r["attribution"] for r in rows if r["attribution"])),
        "answerable": {"n": len(ans), "success": len(succ),
                       "success_with_expected_evidence": sum(r["outcome"] == "ACEPTADA_CON_EVIDENCIA_ESPERADA" for r in ans),
                       "false_negatives": sum(r["status"] != "SUCCESS" for r in ans)},
        "control_false_positives": {
            "wrong_scope_accepted": sum(r["outcome"] == "ACEPTADA_EVIDENCIA_OTRO_AMBITO" for r in rows),
            "unsupported_figures_accepted": sum(r["outcome"] == "ACEPTADA_CIFRA_SIN_RESPALDO" for r in rows),
            "accepted_without_expected_evidence": sum(r["outcome"] == "ACEPTADA_SIN_EVIDENCIA_ESPERADA" for r in rows),
            "answered_should_abstain_or_clarify": sum(r["outcome"] == "RESPONDIDA_DEBIA_ABSTENERSE_O_ACLARAR" for r in neg)},
        "literal_quote_compliance": {"llm_answers": sum(r["llm_text_present"] for r in rows),
                                     "with_quotes": sum(r["n_quotes"] > 0 for r in rows),
                                     "dig03_failed": sum("DIG-03" in (r["dig_failed_checks"] or []) for r in rows)},
        "out_of_expected_citations_in_success": sum(bool(r.get("citations_outside_expected")) for r in succ),
        "exceptions_omitted_in_success": sum(1 for r in succ if r["exceptions_quoted"] is not None and r["exceptions_quoted"] < 1),
        "crossrefs_omitted_in_success": sum(1 for r in succ if r["crossrefs_quoted"] is not None and r["crossrefs_quoted"] < 1),
        "legitimate_abstentions": sum(r["outcome"] in ("ABSTENCION_LEGITIMA", "ABSTENCION_SIN_ACLARACION") for r in neg),
        "n_unanswerable": len(neg),
        "dig_failed_checks": dict(Counter(c for r in rows for c in (r["dig_failed_checks"] or []))),
        "api": {"calls_with_errors": sum(bool(r["api_errors"]) for r in rows),
                "error_types": dict(Counter(e.get("error_type") for r in rows for e in (r["api_errors"] or {}).values()
                                            if isinstance(e, dict))),
                "providers": dict(Counter(r["provider"] for r in rows)), "models": dict(Counter(r["model"] for r in rows))},
        "llm_latency_ms": {"p50": round(median(lat), 1), "p95": round(pct(lat, 0.95), 1)} if lat else None,
        "tokens_total": sum(tok), "tokens_mean_per_eval": round(sum(tok) / len(tok), 1) if tok else None,
    }
    if len(runs) >= 2:
        by = {}
        for run in runs:
            for r in run:
                by.setdefault(r["id"], []).append(r)
        same_status = sum(len({r["status"] for r in v}) == 1 for v in by.values())
        same_outcome = sum(len({r["outcome"] for r in v}) == 1 for v in by.values())
        s["variability"] = {"items": len(by), "same_status_all_runs": same_status, "same_outcome_all_runs": same_outcome,
                            "unstable_items": sorted(k for k, v in by.items() if len({r["outcome"] for r in v}) > 1)}
    return s


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=("dev", "test_sealed", "all"))
    ap.add_argument("--allow-test-sealed", action="store_true")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--sleep", type=float, default=2.0, help="pausa entre llamadas (limites de cuota)")
    ap.add_argument("--max-items", type=int)
    ap.add_argument("--nli-model", help="modelo NLI experimental para puntuar en shadow (opcional)")
    ap.add_argument("--capture-dig", action="store_true",
                    help="Fase 11: registra las entradas EXACTAS de cada llamada al DIG para reejecucion offline")
    ap.add_argument("--out")
    ap.add_argument("--rescore", help="reclasifica un informe existente sin llamar al LLM")
    a = ap.parse_args(argv)
    if a.rescore:
        from decision_integrity import numbers_in
        return rescore(a.rescore, numbers_in)
    items, meta = load_items(a.split, a.allow_test_sealed)
    if a.max_items:
        items = items[: a.max_items]
    before = sha_file(CORPUS)
    from ada_assistant import ArbitrationDecisionAssistant
    from decision_integrity import numbers_in
    ada = ArbitrationDecisionAssistant()
    status = sanitize(ada.llm_manager.get_provider_status()) if hasattr(ada.llm_manager, "get_provider_status") else {}
    keys_present = [k for k in KEY_VARS if os.environ.get(k)]
    rec = Recorder(ada._call_llm)
    ada._call_llm = rec
    dig_calls = []
    if a.capture_dig:
        # Envoltorio transparente: llama al evaluate original del DIG con los mismos argumentos y
        # devuelve su resultado sin cambios; solo copia entradas y salida para la reejecucion offline.
        gate = ada._decision_integrity_gate()
        orig_eval = gate.evaluate

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
    passages = json.load(open(CORPUS, encoding="utf-8"))
    page_text = {}
    for p in passages:
        page_text.setdefault(p["pdf_page_index"], p["text_original"])
    nli = None
    if a.nli_model:
        from experimental.nli_shadow import NLIShadowEvaluator
        nli = NLIShadowEvaluator(a.nli_model)
        nli.load()
    runs, blocked = [], None
    for run_i in range(a.runs):
        rows = []
        for it in items:
            n0 = len(rec.calls)
            d0 = len(dig_calls)
            t0 = time.perf_counter()
            try:
                out = ada.analyze_situation(it["text"], top_k=5)
            except Exception as e:
                out = {"status": "EXCEPTION", "error": sanitize(repr(e)[:300])}
            row = score_run(it, out, rec.calls[n0:], page_text, numbers_in)
            if a.capture_dig:
                row["dig_input"] = sanitize(dig_calls[d0:][-1]) if dig_calls[d0:] else None
            row["run"] = run_i
            row["total_latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            if nli is not None and row["status"] == "SUCCESS":
                row["nli_shadow"] = nli.evaluate(it["text"], row["summary"] or "", [q["quote"] for q in row["quotes"]])
            rows.append(row)
            print(f"[run {run_i}] {it['id']:12} {row['status']:8} {row['outcome']:42} {row['attribution'] or ''}", flush=True)
            if run_i == 0 and len(rows) == 3 and all(r["attribution"] == "API" for r in rows):
                blocked = "las 3 primeras llamadas fallaron en el proveedor (credenciales o cuota); se detiene"
                break
            time.sleep(a.sleep)
        runs.append(rows)
        if blocked:
            break
    rep = {"benchmark": meta, "provider_status": status, "api_keys_present": keys_present,
           "blocked": blocked, "corpus_unchanged": before == sha_file(CORPUS), "summary": summarize(runs),
           "per_run": runs,
           "note": ("Flujo ADA real con DIG; sin mocks. Etiquetas PENDING_EXPERT_REVIEW. 'ACEPTADA_CON_EVIDENCIA_ESPERADA' "
                    "indica cita literal del ancla correcta, NO prueba de que la respuesta sea correcta ni de entailment.")}
    path = a.out or OUT.format(split=a.split)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(sanitize(rep), fh, ensure_ascii=False, indent=2)
    print(json.dumps(rep["summary"], ensure_ascii=False, indent=1))
    print("blocked=", blocked, " corpus_unchanged=", rep["corpus_unchanged"], " resultados:", path)
    return 0 if rep["corpus_unchanged"] else 3


if __name__ == "__main__":
    sys.exit(main())

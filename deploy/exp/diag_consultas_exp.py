#!/usr/bin/env python3
"""Diagnostico de consultas en la instancia experimental (solo lectura; no escribe archivos).

Para cada consulta muestra: estado final, si hubo llamada de analisis al LLM, proveedor/modelo
que respondio, errores de API por proveedor (tipo + mensaje saneado), tamano del prompt,
decision del DIG y las reglas que fallaron con su detalle. Las claves se enmascaran.
Uso (desde el PC):
  Get-Content deploy\\exp\\diag_consultas_exp.py | ssh -i <clave> ubuntu@<IP> "docker exec -i ijf-sor-assistant-exp python - 'consulta 1' 'consulta 2'"
"""
import os
import sys
import time

for p in ("/app", "/app/src", "/app/scripts"):
    if p not in sys.path:
        sys.path.insert(0, p)
os.chdir("/app")

from eval_llm_shadow import Recorder, sanitize  # noqa: E402
from ada_assistant import ArbitrationDecisionAssistant  # noqa: E402
import decision_integrity as D  # noqa: E402

SHOW_ALL = os.environ.get("DIAG_SHOW_ALL") == "1"
DEFAULT = ["¿Se hace pesaje aleatorio a los veteranos?",
           "¿Qué sanción se aplica a un judoka cadete que usa la cabeza para lanzar?",
           "¿Cuáles son las dimensiones del tatami de competición?"]


def main(queries):
    ada = ArbitrationDecisionAssistant()
    st = ada.llm_manager.get_provider_status() if hasattr(ada.llm_manager, "get_provider_status") else {}
    print("DIG:", D.DIG_VERSION, "| proveedores:", sanitize(st))
    print("claves presentes:", [k for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY") if os.environ.get(k)],
          "| LLM_PROVIDER:", os.environ.get("LLM_PROVIDER") or "-",
          "| GEMINI_MODEL:", os.environ.get("GEMINI_MODEL") or "-", "| GROQ_MODEL:", os.environ.get("GROQ_MODEL") or "-")
    rec = Recorder(ada._call_llm)
    ada._call_llm = rec
    for q in queries:
        n0 = len(rec.calls)
        t0 = time.perf_counter()
        try:
            out = ada.analyze_situation(q, top_k=5)
        except Exception as e:
            print("\n###", q, "\n  EXCEPCION:", sanitize(repr(e)[:300]))
            continue
        calls = rec.calls[n0:]
        print("\n###", q)
        print("  estado:", out.get("status"), "| segundos:", round(time.perf_counter() - t0, 1))
        print("  evidencia:", [e.get("passage_id") for e in (out.get("evidence") or [])][:6])
        for i, c in enumerate(calls):
            meta = c.get("meta") or {}
            kind = "ANALISIS" if c.get("is_analysis") else "traduccion/aux"
            print(f"  llamada {i} [{kind}] prompt_chars={c.get('prompt_chars')} ms={c.get('latency_ms')}"
                  f" respondio={meta.get('successful_provider')}/{meta.get('successful_model')}"
                  f" texto={'si' if c.get('text') else 'NO'} chars_respuesta={len(c.get('text') or '')}"
                  f" fin={meta.get('finish_reason')} tokens={meta.get('token_usage')}")
            for prov, err in (meta.get("errors") or {}).items():
                print(f"     error {prov}: {err.get('error_type')} - {str(sanitize(err.get('message')))[:220]}")
            if c.get("exception"):
                print("     excepcion:", c["exception"])
        if not any(c.get("is_analysis") for c in calls):
            print("  >> NO hubo llamada de analisis al LLM (abstencion previa a la generacion)")
        di = out.get("decision_integrity") or {}
        if di:
            print("  DIG:", di.get("decision"), "| fallidas:", di.get("failed_checks"))
            for ch in di.get("checks") or []:
                if not ch.get("passed"):
                    print("     ", ch.get("code"), "->", str(ch.get("detail"))[:260])
        ana = [c for c in calls if c.get("is_analysis") and c.get("text")]
        if ana and (out.get("status") != "SUCCESS" or SHOW_ALL):
            raw = ana[-1]["text"]
            o = D.parse_answer(raw)
            if not o:
                print("  respuesta LLM (no JSON, primeros 600):", raw[:600].replace("\n", " "))
                print("  ... ultimos 400:", raw[-400:].replace("\n", " "))
            else:
                for k in ("summary", "normative_basis", "conditions_and_exceptions"):
                    if o.get(k):
                        print(f"  LLM {k}:", str(o.get(k))[:700].replace("\n", " "))
                for q in o.get("evidence_quotes") or []:
                    if isinstance(q, dict):
                        print("  LLM cita", q.get("passage_id"), "->", repr(str(q.get("quote"))[:300]))
        lim = ((out.get("structured_answer") or {}).get("limitations") or "")
        if out.get("status") != "SUCCESS" and lim:
            print("  motivo mostrado:", lim[:300].replace("\n", " "))


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT)

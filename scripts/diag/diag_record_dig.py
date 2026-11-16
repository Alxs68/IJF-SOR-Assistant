"""Plugin de pytest SOLO DIAGNOSTICO (Fase 9.1). No modifica codigo de produccion en disco.

Uso:  python -m pytest tests -p diag_record_dig   (con PYTHONPATH=scripts/diag)
  DIAG_MODE=record   (defecto) registra cada analyze_situation con el control DIG actual
  DIAG_MODE=no_dig   ademas sustituye EN MEMORIA la compuerta DIG por una permisiva, para reproducir
                     el comportamiento previo a la Fase 9 y separar fallos preexistentes de los de DIG
Salida: data/eval/decision_integrity_v1/diag_<modo>.jsonl  (una linea por llamada; incluye el test)
"""
import functools
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODE = os.environ.get("DIAG_MODE", "record")
OUT = os.path.join(ROOT, "data", "eval", "decision_integrity_v1", f"diag_{MODE}.jsonl")


class _PermissiveGate:
    def evaluate(self, *a, **k):
        return {"version": "DIAG-NO-DIG", "decision": "PERMITIR", "failed_checks": [], "levels": {}, "checks": []}


def _wrap(cls):
    if getattr(cls, "_diag_wrapped", False):
        return
    orig = cls.analyze_situation

    @functools.wraps(orig)
    def analyze_situation(self, situation_query, *a, **k):
        res = orig(self, situation_query, *a, **k)
        di = res.get("decision_integrity") or {}
        meta = res.get("llm_meta") or {}
        rec = {
            "test": os.environ.get("PYTEST_CURRENT_TEST", "").split(" ")[0],
            "mode": MODE, "query": situation_query, "status": res.get("status"), "res_mode": res.get("mode"),
            "provider": meta.get("successful_provider"), "model": meta.get("successful_model"),
            "fallback": meta.get("fallback_triggered"),
            "dig_decision": di.get("decision"), "dig_failed": di.get("failed_checks"),
            "dig_detail": {c["code"]: c["detail"][:400] for c in di.get("checks", []) if not c["passed"]},
            "evidence": [e.get("passage_id") for e in res.get("evidence") or []],
            "related": [e.get("passage_id") for e in res.get("related_passages") or []],
            "citations": [c.get("passage_id") if isinstance(c, dict) else c
                          for c in (res.get("structured_answer") or {}).get("citations", [])],
        }
        with open(OUT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return res
    cls.analyze_situation = analyze_situation
    if MODE == "no_dig":
        cls._decision_integrity_gate = lambda self: _PermissiveGate()
    cls._diag_wrapped = True


def pytest_configure(config):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").close()
    sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
    for name in ("ada_assistant", "src.ada_assistant"):
        try:
            mod = __import__(name, fromlist=["ArbitrationDecisionAssistant"])
            _wrap(mod.ArbitrationDecisionAssistant)
        except Exception as e:  # pragma: no cover
            print(f"[diag] no se pudo envolver {name}: {e}")

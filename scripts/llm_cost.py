"""Consumo MEDIDO (tokens devueltos por el proveedor) y coste ESTIMADO (tarifas de config/llm_pricing.json).

El coste es siempre una estimacion: la cifra real solo esta en Google AI Studio (Usage / Billing). Si la tarifa del
modelo no esta configurada, el coste se informa como no calculable; nunca se inventa.
"""
import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRICING = os.path.join(ROOT, "config", "llm_pricing.json")


def load_pricing(path=PRICING):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _rate(pricing, version):
    m = (pricing.get("modelos") or {}).get(version or "")
    if not m or m.get("entrada_usd_por_millon") is None or m.get("salida_usd_por_millon") is None:
        return None
    return m


def ledger(rows, pricing=None):
    """Agrega por (proveedor, version, tipo de llamada) los tokens medidos y estima el coste."""
    pricing = pricing or load_pricing()
    agg = defaultdict(lambda: {"llamadas": 0, "entrada": 0, "salida": 0, "razonamiento": 0, "cache": 0})
    for r in rows:
        for c in r.get("calls") or []:
            t = c.get("tokens") or {}
            key = (c.get("provider") or "sin_proveedor", c.get("model_version") or "version_desconocida", c.get("kind"))
            a = agg[key]
            a["llamadas"] += 1
            a["entrada"] += int(t.get("prompt_tokens") or 0)
            a["salida"] += int(t.get("completion_tokens") or 0)
            a["razonamiento"] += int(t.get("thoughts_tokens") or 0)
            a["cache"] += int(t.get("cached_tokens") or 0)
    out, total, calculable = [], 0.0, True
    for (prov, ver, kind), a in sorted(agg.items()):
        m = _rate(pricing, ver)
        if m is None:
            cost, calculable = None, False
        else:
            cost = round((a["entrada"] * m["entrada_usd_por_millon"]
                          + (a["salida"] + a["razonamiento"]) * m["salida_usd_por_millon"]) / 1e6, 6)
            total += cost
        out.append({"proveedor": prov, "version_modelo": ver, "tipo": kind, **a,
                    "coste_estimado_usd": cost,
                    "tarifa_estado": (m or {}).get("estado", "SIN_TARIFA")})
    rate_cop = pricing.get("usd_a_cop")
    return {"medido_por_grupo": out,
            "tokens_entrada": sum(x["entrada"] for x in out), "tokens_salida": sum(x["salida"] for x in out),
            "tokens_razonamiento": sum(x["razonamiento"] for x in out),
            "coste_estimado_usd": round(total, 6) if calculable else None,
            "coste_estimado_cop": (round(total * rate_cop, 2) if (calculable and rate_cop) else None),
            "nota": "Tokens MEDIDOS por el proveedor; coste ESTIMADO con config/llm_pricing.json. El coste real: AI Studio > Usage."
                    + ("" if calculable else " Hay versiones sin tarifa configurada: coste no calculable.")}


def versions(rows):
    """Versiones de modelo efectivas por llamada (para detectar cambios del alias entre llamadas o corridas)."""
    vs = defaultdict(int)
    for r in rows:
        for c in r.get("calls") or []:
            for v in [c.get("model_version"), *(c.get("model_versions_intentos") or [])]:
                vs[v or "version_desconocida"] += 1
    return dict(vs)

#!/usr/bin/env python3
"""Comprobacion de disponibilidad de los proveedores LLM ANTES de una evaluacion (no escribe archivos).

Usa la MISMA configuracion que el asistente (MultiProviderLLMManager): proveedor principal, politica de
respaldo y modelo EFECTIVO de cada proveedor (si GEMINI_MODEL/GROQ_MODEL del .env no es un modelo
soportado, el asistente usa el modelo por defecto; aqui se informa de esa discrepancia).
Por proveedor: una llamada minima (~20 tokens) por el mismo cliente que usa el asistente, con el tipo de
error (QUOTA=429, TEMPORARY=503/5xx, REQUEST_TOO_LARGE=413, AUTH, NOT_FOUND...), la version que responde
y, para Groq, los limites que publica en sus cabeceras. Con --tokens-por-analisis (por defecto 8000,
tamano tipico medido de una llamada de analisis) informa si la capacidad por minuto alcanza para UNA
llamada de analisis. Gemini no publica la cuota restante: solo se sabe si la llamada pasa.
Nunca muestra claves. Uso: python scripts/check_llm_quota.py [--tokens-por-analisis 8000]
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
import llm_provider as L  # noqa: E402  (carga .env si existe)


def _post(url, payload, headers):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, {}
    except Exception as e:
        return None, {}, {"exc": type(e).__name__}


def probe(mgr, prov, tokens_needed):
    client = mgr._get_client(prov)
    env_var = mgr.SUPPORTED_PROVIDERS[prov]["env_model"]
    env_model = os.environ.get(env_var)
    info = {"modelo_efectivo": client.model, "modelo_en_entorno": env_model,
            "modelo_entorno_ignorado": bool(env_model) and env_model != client.model,
            "clave_presente": bool(client.api_key)}
    if not client.api_key:
        return dict(info, ok=False, error_tipo="AUTH", detalle="sin clave")
    try:
        text = client.generate(prompt="Responde solo: ok")
        info.update(ok=bool(text), error_tipo=None, http=200)
    except L.LLMProviderError as e:
        info.update(ok=False, error_tipo=e.error_type, http=getattr(e, "status_code", None),
                    reintentar_en_s=getattr(e, "retry_after", None))
    except Exception as e:
        info.update(ok=False, error_tipo="EXCEPCION", detalle=type(e).__name__)
    if prov == "Gemini":
        st, _h, body = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{client.model}:generateContent"
                             f"?key={client.api_key}", {"contents": [{"parts": [{"text": "ok"}]}],
                                                       "generationConfig": {"maxOutputTokens": 3}},
                             {"Content-Type": "application/json"})
        info["version_que_responde"] = body.get("modelVersion") if st == 200 else None
        info["capacidad_por_minuto"] = "no publicada por Gemini"
    else:
        st, h, body = _post("https://api.groq.com/openai/v1/chat/completions",
                            {"model": client.model, "messages": [{"role": "user", "content": "ok"}], "max_tokens": 3},
                            {"Content-Type": "application/json", "Authorization": f"Bearer {client.api_key}",
                             "User-Agent": L.GroqClient.DEFAULT_USER_AGENT})
        lim = {k: v for k, v in h.items() if k.startswith("x-ratelimit")}
        info["version_que_responde"] = body.get("model") if st == 200 else None
        info["limites"] = lim
        try:
            tpm = int(lim.get("x-ratelimit-limit-tokens"))
            info["capacidad_por_minuto"] = {"limite_tokens_min": tpm, "tokens_por_analisis": tokens_needed,
                                            "alcanza_para_un_analisis": tpm >= tokens_needed}
        except (TypeError, ValueError):
            info["capacidad_por_minuto"] = "desconocida"
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokens-por-analisis", type=int, default=8000)
    ap.add_argument("--proveedores", default="Gemini,Groq",
                    help="proveedores a comprobar, separados por comas (p. ej. --proveedores Gemini: no llama a Groq)")
    a = ap.parse_args()
    mgr = L.MultiProviderLLMManager()
    wanted = [p.strip().capitalize() for p in a.proveedores.split(",") if p.strip()]
    order = [p for p in [mgr.primary_provider] + [p for p in ("Gemini", "Groq") if p != mgr.primary_provider] if p in wanted]
    out = {"proveedor_principal": mgr.primary_provider, "politica_respaldo": mgr.fallback_policy}
    for prov in order:
        out[prov] = probe(mgr, prov, a.tokens_por_analisis)
    usable = [p for p in order if out[p].get("ok")]
    out["proveedor_efectivo"] = usable[0] if usable else None
    out["evaluacion_viable"] = bool(usable)
    if not usable:
        out["aviso"] = "Ningun proveedor responde: una evaluacion ahora daria solo abstenciones por API, no por el DIG."
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

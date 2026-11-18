"""Aislamiento de las pruebas automatizadas: ninguna prueba puede llamar a un proveedor real (Gemini, Groq).

1. Antes de importar cualquier modulo de prueba, las claves de los proveedores se fijan VACIAS en el entorno del
   proceso de pytest. Vacias y no eliminadas: src/llm_provider.py rellena desde el .env las variables que NO existen,
   y asi no puede volver a cargar las claves reales. No se toca el .env ni las variables persistentes de Windows.
2. urllib.request.urlopen queda protegido: una peticion a un host de proveedor lanza RealProviderCallBlocked.
   Las pruebas que simulan la red con patch/mock siguen funcionando (sustituyen temporalmente esta proteccion).
"""
import os
import urllib.request

PROVIDER_KEYS = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY")
PROVIDER_HOSTS = ("generativelanguage.googleapis.com", "api.groq.com")

for _k in PROVIDER_KEYS:
    os.environ[_k] = ""


class RealProviderCallBlocked(RuntimeError):
    """Una prueba intento conectarse a un proveedor real."""


_real_urlopen = urllib.request.urlopen


def _guarded_urlopen(req, *args, **kwargs):
    url = getattr(req, "full_url", None) or str(req)
    if any(h in url for h in PROVIDER_HOSTS):
        raise RealProviderCallBlocked("llamada real a proveedor bloqueada en pruebas: " + url.split("?")[0])
    return _real_urlopen(req, *args, **kwargs)


urllib.request.urlopen = _guarded_urlopen
urllib.request._ijf_guarded_urlopen = _guarded_urlopen

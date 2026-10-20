"""
LLM Provider Abstraction Layer for IJF-SOR-Assistant
====================================================
Provides a unified interface for Gemini and Groq with automatic fallback,
error classification, retry handling, and credential safety.
"""

import os
import json
import urllib.request
import urllib.error
import time
from typing import Dict, Any, Optional, Tuple

class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    def __init__(self, message: str, error_type: str, retry_after: Optional[int] = None, status_code: Optional[int] = None):
        super().__init__(message)
        self.error_type = error_type  # 'QUOTA', 'AUTH', 'NOT_FOUND', 'TEMPORARY', 'CONTENT', 'CONFIG'
        self.retry_after = retry_after
        self.status_code = status_code


class BaseLLMClient:
    """Abstract base class for LLM API providers."""
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        raise NotImplementedError


class GeminiClient(BaseLLMClient):
    """Native zero-dependency HTTP client for Google Gemini API."""
    DEFAULT_MODEL = "gemini-flash-latest"
    _UNSET = object()

    def __init__(self, api_key: Any = _UNSET, model: Optional[str] = None):
        key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")) if api_key is self._UNSET else api_key
        mod = model or os.environ.get("GEMINI_MODEL") or self.DEFAULT_MODEL
        super().__init__(api_key=key, model=mod)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise LLMProviderError("Clave GEMINI_API_KEY ausente o no configurada.", error_type="AUTH")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        full_text = prompt
        if system_prompt:
            full_text = f"{system_prompt}\n\n{prompt}"

        payload = {
            "contents": [{
                "parts": [{"text": full_text}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.95
            }
        }
        headers = {"Content-Type": "application/json"}

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                candidates = res_data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        return parts[0].get('text', '')
                raise LLMProviderError("Respuesta de Gemini sin contenido válido.", error_type="CONTENT")
        except urllib.error.HTTPError as e:
            code = e.code
            try:
                body = e.read().decode('utf-8')
                data = json.loads(body)
                msg = data.get("error", {}).get("message", str(e))
            except Exception:
                msg = str(e)

            retry_after = None
            if code == 429:
                # Try extracting retry delay
                err_type = "QUOTA"
                if "retryDelay" in msg:
                    # extract rough seconds if string like '35731s'
                    import re
                    m = re.search(r'(\d+)s', msg)
                    if m:
                        retry_after = int(m.group(1))
            elif code in (401, 403):
                err_type = "AUTH"
            elif code == 404:
                err_type = "NOT_FOUND"
            elif code in (500, 502, 503, 504):
                err_type = "TEMPORARY"
            else:
                err_type = "CONTENT"

            # Ensure API key is NEVER exposed in the exception
            if self.api_key and self.api_key in msg:
                msg = msg.replace(self.api_key, "[REDACTED_API_KEY]")

            raise LLMProviderError(f"Error Gemini HTTP {code}: {msg}", error_type=err_type, retry_after=retry_after, status_code=code)
        except urllib.error.URLError as e:
            raise LLMProviderError(f"Error de conexión con Gemini: {e.reason}", error_type="TEMPORARY")
        except Exception as e:
            raise LLMProviderError(f"Fallo inesperado de Gemini: {e}", error_type="CONTENT")


class GroqClient(BaseLLMClient):
    """Native zero-dependency HTTP client for Groq Cloud API (OpenAI Chat Completion compatible)."""
    DEFAULT_MODEL = "openai/gpt-oss-120b"
    DEFAULT_USER_AGENT = "IJF-SOR-Assistant/2.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    _UNSET = object()

    def __init__(self, api_key: Any = _UNSET, model: Optional[str] = None):
        key = os.environ.get("GROQ_API_KEY") if api_key is self._UNSET else api_key
        mod = model or os.environ.get("GROQ_MODEL") or self.DEFAULT_MODEL
        super().__init__(api_key=key, model=mod)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise LLMProviderError("Clave GROQ_API_KEY ausente o no configurada.", error_type="AUTH")

        url = "https://api.groq.com/openai/v1/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 2048
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": self.DEFAULT_USER_AGENT
        }

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                choices = res_data.get('choices', [])
                if choices:
                    return choices[0].get('message', {}).get('content', '')
                raise LLMProviderError("Respuesta de Groq sin choices válidos.", error_type="CONTENT")
        except urllib.error.HTTPError as e:
            code = e.code
            try:
                body = e.read().decode('utf-8')
                data = json.loads(body)
                msg = data.get("error", {}).get("message", str(e))
            except Exception:
                msg = str(e)

            retry_after = None
            if "retry-after" in e.headers:
                try:
                    retry_after = int(e.headers.get("retry-after"))
                except Exception:
                    pass

            if code == 429:
                err_type = "QUOTA"
            elif code in (401, 403):
                err_type = "AUTH"
            elif code == 404:
                err_type = "NOT_FOUND"
            elif code in (500, 502, 503, 504):
                err_type = "TEMPORARY"
            else:
                err_type = "CONTENT"

            if self.api_key and self.api_key in msg:
                msg = msg.replace(self.api_key, "[REDACTED_API_KEY]")

            raise LLMProviderError(f"Error Groq HTTP {code}: {msg}", error_type=err_type, retry_after=retry_after, status_code=code)
        except urllib.error.URLError as e:
            raise LLMProviderError(f"Error de conexión con Groq: {e.reason}", error_type="TEMPORARY")
        except Exception as e:
            raise LLMProviderError(f"Fallo inesperado de Groq: {e}", error_type="CONTENT")


class MultiProviderLLMManager:
    """
    Manages multi-provider LLM invocations with automatic or manual fallback policies,
    error tracking, and session resilience.
    """
    SUPPORTED_PROVIDERS = {
        "Gemini": {
            "models": ["gemini-flash-latest", "gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.5-pro", "gemini-1.5-pro"],
            "client_class": GeminiClient,
            "env_key": "GEMINI_API_KEY",
            "env_model": "GEMINI_MODEL"
        },
        "Groq": {
            "models": ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "allam-2-7b"],
            "client_class": GroqClient,
            "env_key": "GROQ_API_KEY",
            "env_model": "GROQ_MODEL"
        }
    }

    _UNSET = object()
    
    def __init__(
        self,
        primary_provider: Optional[str] = None,
        fallback_policy: str = "automatic",
        gemini_api_key: Any = _UNSET,
        groq_api_key: Any = _UNSET,
        gemini_model: Optional[str] = None,
        groq_model: Optional[str] = None
    ):
        # Determine primary provider: argument > env > default
        env_prov = os.environ.get("LLM_PROVIDER", "").capitalize()
        if primary_provider:
            self.primary_provider = primary_provider.capitalize()
        elif env_prov in self.SUPPORTED_PROVIDERS:
            self.primary_provider = env_prov
        else:
            self.primary_provider = "Gemini"

        self.fallback_policy = fallback_policy.lower()  # 'automatic' or 'manual'
        self.gemini_api_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")) if gemini_api_key is self._UNSET else gemini_api_key
        self.groq_api_key = os.environ.get("GROQ_API_KEY") if groq_api_key is self._UNSET else groq_api_key
        
        # Configure models with automatic fallback to supported default if deprecated model string provided
        g_cand = gemini_model or os.environ.get("GEMINI_MODEL")
        if g_cand and g_cand in self.SUPPORTED_PROVIDERS["Gemini"]["models"]:
            self.gemini_model = g_cand
        else:
            self.gemini_model = GeminiClient.DEFAULT_MODEL

        q_cand = groq_model or os.environ.get("GROQ_MODEL")
        if q_cand and q_cand in self.SUPPORTED_PROVIDERS["Groq"]["models"]:
            self.groq_model = q_cand
        else:
            self.groq_model = GroqClient.DEFAULT_MODEL

    def get_provider_status(self) -> Dict[str, Any]:
        """Returns safe inspection info without revealing secrets."""
        def mask(key: Optional[str]) -> str:
            if not key:
                return "No configurada"
            return key[:4] + "..." + key[-3:] if len(key) >= 10 else "Configurada"

        return {
            "primary_provider": self.primary_provider,
            "fallback_policy": self.fallback_policy,
            "providers": {
                "Gemini": {
                    "available": bool(self.gemini_api_key),
                    "masked_key": mask(self.gemini_api_key),
                    "model": self.gemini_model,
                },
                "Groq": {
                    "available": bool(self.groq_api_key),
                    "masked_key": mask(self.groq_api_key),
                    "model": self.groq_model,
                }
            }
        }

    def _get_client(self, provider_name: str) -> BaseLLMClient:
        prov = provider_name.capitalize()
        if prov == "Groq":
            return GroqClient(api_key=self.groq_api_key, model=self.groq_model)
        elif prov == "Gemini":
            return GeminiClient(api_key=self.gemini_api_key, model=self.gemini_model)
        else:
            raise ValueError(f"Proveedor desconocido: '{provider_name}'")

    def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Executes generation following the configured provider and fallback policy.
        Returns:
            Tuple of (generated_text, execution_metadata)
        """
        meta = {
            "primary_provider": self.primary_provider,
            "fallback_policy": self.fallback_policy,
            "attempted_providers": [],
            "successful_provider": None,
            "successful_model": None,
            "fallback_triggered": False,
            "fallback_reason": None,
            "errors": {}
        }

        # Candidate order
        candidates = [self.primary_provider]
        alternate = "Groq" if self.primary_provider == "Gemini" else "Gemini"
        if self.fallback_policy == "automatic":
            candidates.append(alternate)

        for i, prov in enumerate(candidates):
            meta["attempted_providers"].append(prov)
            client = self._get_client(prov)

            # Check key availability beforehand
            if not client.api_key:
                err_msg = f"Clave de API ausente para {prov}."
                meta["errors"][prov] = {"error_type": "AUTH", "message": err_msg}
                if i == 0 and self.fallback_policy == "automatic":
                    meta["fallback_attempted"] = True
                    meta["fallback_reason"] = f"Clave ausente en {prov}"
                    continue
                else:
                    break

            try:
                text = client.generate(prompt=prompt, system_prompt=system_prompt)
                if text:
                    meta["successful_provider"] = prov
                    meta["successful_model"] = client.model
                    if i > 0:
                        meta["fallback_triggered"] = True
                    return text, meta
            except LLMProviderError as e:
                meta["errors"][prov] = {
                    "error_type": e.error_type,
                    "message": str(e),
                    "status_code": e.status_code,
                    "retry_after": e.retry_after
                }

                # Decide if fallback is allowed (QUOTA, TEMPORARY, NOT_FOUND)
                # Note: AUTH (invalid key) does not trigger silent fallback unless key was missing
                if self.fallback_policy == "automatic" and i == 0 and e.error_type in ("QUOTA", "TEMPORARY", "NOT_FOUND"):
                    meta["fallback_attempted"] = True
                    meta["fallback_reason"] = f"{e.error_type} en {prov}: {e}"
                    continue
                else:
                    break

        # If fallback was attempted but no provider succeeded:
        meta["fallback_triggered"] = bool(meta.get("successful_provider") and meta["successful_provider"] != self.primary_provider)
        return None, meta

import os
import re
import json
import urllib.parse

# Mapeo de subpáginas SPA de rules.ijf.org al PDF correspondiente de explicación detallada
RULES_PDF_URL = "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2023/04/Detailed_Explanation_of_the_IJF_Judo_Refereeing_Rules_25.03.2023.pdf"

RULES_DEEP_LINKS = {
    "rules.ijf.org/gripping": f"{RULES_PDF_URL}#page=3",
    "rules.ijf.org/gripping/illegal": f"{RULES_PDF_URL}#page=12",
    "rules.ijf.org/scoring/osaekomi": f"{RULES_PDF_URL}#page=22",
    "rules.ijf.org/scoring/landing": f"{RULES_PDF_URL}#page=6",
    "rules.ijf.org/penalties/false-attack": f"{RULES_PDF_URL}#page=24",
    "rules.ijf.org/penalties/stepping-out": f"{RULES_PDF_URL}#page=24",
    "rules.ijf.org/penalties/diving": f"{RULES_PDF_URL}#page=21",
}

class ReferenceManager:
    def __init__(self, registry_path=None):
        if registry_path is None:
            # Ruta permanente por defecto
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            registry_path = os.path.join(base_dir, "data", "references", "reference_registry.json")
        
        self.registry_path = registry_path
        self.registry = {}
        self.load_registry()

    def load_registry(self):
        """Carga en memoria el registro de referencias operativas."""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    self.registry = json.load(f)
            except Exception as e:
                print(f"[RRM] Error al cargar registry: {e}")
                self.registry = {}
        else:
            print(f"[RRM] Warning: No se encontró el registro en {self.registry_path}. Usando fallback.")
            self.registry = {}

    def clean_url(self, url):
        """Limpia espacios en blanco y caracteres inválidos de una URL base."""
        if not url:
            return ""
        return url.strip()

    def append_query_param(self, url, param_name, param_value):
        """Añade un parámetro de consulta a una URL de forma segura."""
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed.query)
        query_params[param_name] = [str(param_value)]
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        return urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))

    def resolve_reference(self, kun_id, kun_data):
        """
        Resuelve una cita KUN a un payload RRM que contiene:
        - url: URL final construida o None
        - operational_status: Estado operativo (AVAILABLE, DELETED, etc.)
        - verification_status: Estado de verificación (VERIFIED, etc.)
        - is_clickable: Flag indicando si el enlace debe ser activo en la UI
        - ux_message: Mensaje explicativo para el tooltip o badge
        """
        if not kun_data:
            return {
                "url": None,
                "operational_status": "PENDING_REVIEW",
                "verification_status": "NOT_VERIFIED",
                "is_clickable": False,
                "ux_message": "Referencia no encontrada o sin datos."
            }

        ref_spec = kun_data.get("referencia_especifica", "").strip()
        norm_ref = re.sub(r'^https?://', '', ref_spec).rstrip('/')
        
        # 1. Interceptar SPA deep links de rules.ijf.org
        source_url = ""
        if "fuente" in kun_data and isinstance(kun_data["fuente"], dict):
            source_url = kun_data["fuente"].get("url") or ""
        norm_url = re.sub(r'^https?://', '', source_url).strip().rstrip('/')
        
        for link_key, deep_url in RULES_DEEP_LINKS.items():
            if (norm_ref and norm_ref.startswith(link_key)) or (norm_url and norm_url.startswith(link_key)):
                return {
                    "url": deep_url,
                    "operational_status": "AVAILABLE",
                    "verification_status": "VERIFIED",
                    "is_clickable": True,
                    "ux_message": "🟢 Cita interactiva (PDF de aclaraciones detalladas)"
                }

        # 2. Determinar la clave de búsqueda en el registro
        # Caso A: Si KUN tiene una URL explícita (ej: link directo de youtube)
        lookup_key = None
        if "fuente" in kun_data and isinstance(kun_data["fuente"], dict):
            lookup_key = self.clean_url(kun_data["fuente"].get("url"))
            
        # Caso B: Fallback a fuente_origen (ej: VID-004)
        if not lookup_key or lookup_key not in self.registry:
            lookup_key = kun_data.get("fuente_origen")

        # 3. Consultar en el catálogo RRM
        ref_record = self.registry.get(lookup_key)
        
        if not ref_record:
            # Fallback seguro a resolvedor clásico si no está registrado
            fallback_url = self._resolve_fallback_url(kun_data)
            return {
                "url": fallback_url,
                "operational_status": "AVAILABLE" if fallback_url else "DELETED",
                "verification_status": "NOT_VERIFIED",
                "is_clickable": True if fallback_url else False,
                "ux_message": "⚠️ Cita en modo compatibilidad" if fallback_url else "🔴 Cita no verificada"
            }

        op_status = ref_record.get("operational_status", "AVAILABLE")
        ver_status = ref_record.get("verification_status", "NOT_VERIFIED")
        
        # 4. Aplicar políticas RRM según el estado operativo
        if op_status == "DELETED":
            return {
                "url": None,
                "operational_status": op_status,
                "verification_status": ver_status,
                "is_clickable": False,
                "ux_message": f"🔴 Fuente dada de baja por la IJF (Cita histórica: {ref_record.get('url_original')})"
            }

        # Construir la URL operativa a partir de url_resolved
        base_url = self.clean_url(ref_record.get("url_resolved"))
        if not base_url:
            return {
                "url": None,
                "operational_status": "DELETED",
                "verification_status": ver_status,
                "is_clickable": False,
                "ux_message": "🔴 Recurso sin URL de resolución activa."
            }

        final_url = base_url

        # Aplicar marcas de tiempo o números de páginas
        fuente_struct = kun_data.get("fuente")
        if isinstance(fuente_struct, dict):
            # Formato estructurado moderno
            tipo = fuente_struct.get("tipo", "").lower()
            if tipo == "pdf":
                pagina = fuente_struct.get("pagina")
                if pagina is not None:
                    parsed = urllib.parse.urlparse(final_url)
                    final_url = urllib.parse.urlunparse((
                        parsed.scheme, parsed.netloc, parsed.path,
                        parsed.params, parsed.query, f"page={pagina}"
                    ))
            elif tipo == "video":
                inicio = fuente_struct.get("inicio_segundos")
                if inicio is not None:
                    final_url = self.append_query_param(final_url, "t", f"{inicio}s")
        else:
            # Fallback regex para marcas de tiempo / páginas
            if final_url.endswith(".pdf"):
                page_match = re.search(r'(?:pág|página|page)\.?\s*(\d+)', ref_spec, re.IGNORECASE)
                if page_match:
                    page_num = page_match.group(1)
                    parsed = urllib.parse.urlparse(final_url)
                    final_url = urllib.parse.urlunparse((
                        parsed.scheme, parsed.netloc, parsed.path,
                        parsed.params, parsed.query, f"page={page_num}"
                    ))
            elif "youtube.com" in final_url or "youtu.be" in final_url:
                ts_match = re.search(r'(\d{1,2}):(\d{2})', ref_spec)
                if ts_match:
                    mins = int(ts_match.group(1))
                    secs = int(ts_match.group(2))
                    total_secs = mins * 60 + secs
                    final_url = self.append_query_param(final_url, "t", f"{total_secs}s")

        # Generar mensajes UX contextualizados
        ux_messages = {
            "AVAILABLE": "🟢 Fuente oficial disponible en línea",
            "MIGRATED": "🟡 Ubicación actualizada (la IJF migró este archivo)",
            "FALLBACK_GENERAL": "🔵 Portal Interactivo (requiere navegación manual al clip)"
        }
        ux_msg = ux_messages.get(op_status, "🟢 Cita verificada")

        return {
            "url": final_url,
            "operational_status": op_status,
            "verification_status": ver_status,
            "is_clickable": True,
            "ux_message": ux_msg
        }

    def _resolve_fallback_url(self, kun_data):
        """Resolvedor de fallback clásico (copia exacta de la lógica de citation_resolver.py)."""
        # Solo para compatibilidad si un ID no está en el registro
        fuente_struct = kun_data.get("fuente")
        if isinstance(fuente_struct, dict):
            tipo = fuente_struct.get("tipo", "").lower()
            base_url = self.clean_url(fuente_struct.get("url"))
            if not base_url:
                return None
            if tipo == "pdf":
                pagina = fuente_struct.get("pagina")
                if pagina is not None:
                    parsed = urllib.parse.urlparse(base_url)
                    return urllib.parse.urlunparse((
                        parsed.scheme, parsed.netloc, parsed.path,
                        parsed.params, parsed.query, f"page={pagina}"
                    ))
                return base_url
            elif tipo == "video":
                inicio = fuente_struct.get("inicio_segundos")
                if inicio is not None:
                    return self.append_query_param(base_url, "t", f"{inicio}s")
                return base_url
        return None

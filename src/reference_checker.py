import os
import json
import re
import urllib.request
import urllib.error
from datetime import datetime

class ReferenceChecker:
    def __init__(self, registry_path=None):
        if registry_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            registry_path = os.path.join(base_dir, "data", "references", "reference_registry.json")
        
        self.registry_path = registry_path
        self.registry = {}
        self.load_registry()

    def load_registry(self):
        if os.path.exists(self.registry_path):
            with open(self.registry_path, "r", encoding="utf-8") as f:
                self.registry = json.load(f)

    def save_registry(self):
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)

    def check_url_status(self, url):
        """
        Comprueba la disponibilidad real de una URL por HTTP.
        Retorna (is_available, reason)
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
        }

        # Comprobar si es un video de YouTube
        is_youtube = "youtube.com" in url or "youtu.be" in url

        req = urllib.request.Request(url, headers=headers)
        try:
            # Para YouTube siempre hacemos GET completo; para otros podemos hacer GET con timeout
            # (Algunos CDNs bloquean peticiones HEAD, por lo que GET es más confiable)
            with urllib.request.urlopen(req, timeout=10) as response:
                if is_youtube:
                    html = response.read().decode('utf-8', errors='ignore')
                    
                    # Indicadores claros de que un video de YouTube no está disponible
                    unplayable_indicators = [
                        "\"status\":\"UNPLAYABLE\"",
                        "\"status\":\"ERROR\"",
                        "This video is unavailable",
                        "This video is private",
                        "Este video no está disponible",
                        "Este video es privado"
                    ]
                    for indicator in unplayable_indicators:
                        if indicator in html:
                            return False, f"YouTube video unplayable (found: '{indicator}')"
                    
                    # Si el título dice "YouTube" o no contiene información del video, puede estar caído
                    title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
                    if title_match:
                        title_text = title_match.group(1).strip()
                        if "Video no disponible" in title_text or "Private video" in title_text:
                            return False, f"YouTube video title indicates unplayable: '{title_text}'"

                return True, "HTTP 200 OK"
        except urllib.error.HTTPError as e:
            return False, f"HTTP Error {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            return False, f"URL Error: {e.reason}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def run_audit(self):
        """Recorre todas las referencias registradas, audita su estado y actualiza el JSON."""
        print(f"[Checker] Iniciando auditoría de referencias en {self.registry_path}...")
        now_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        changes_detected = 0

        for key, ref in self.registry.items():
            # Mapear URL de resolución
            url = ref.get("url_resolved")
            if not url:
                print(f"[Checker] Warning: Referencia '{key}' no tiene url_resolved.")
                continue

            print(f"[Checker] Analizando '{key}': {url} ...")
            is_available, reason = self.check_url_status(url)
            
            old_op_status = ref.get("operational_status", "AVAILABLE")
            old_ver_status = ref.get("verification_status", "NOT_VERIFIED")

            # Determinar nuevo estado propuesto
            new_op_status = old_op_status
            new_ver_status = "AUTO_VERIFIED"

            if not is_available:
                # Si no está disponible y no estaba marcado previamente como DELETED
                if old_op_status != "DELETED":
                    new_op_status = "DELETED"
                    new_ver_status = "MANUAL_REVIEW"
            else:
                # Si está disponible, pero estaba en DELETED o REVISION_REQUIRED
                if old_op_status in ["DELETED", "REVISION_REQUIRED"]:
                    new_op_status = "AVAILABLE"
                    new_ver_status = "AUTO_VERIFIED"

            # Actualizar timestamps y estado de validación
            ref["date_last_checked"] = now_str
            
            # Registrar cambio de estado en el historial si ocurrió
            if old_op_status != new_op_status:
                changes_detected += 1
                ref["operational_status"] = new_op_status
                ref["verification_status"] = new_ver_status
                ref["date_updated"] = now_str
                
                # Crear entrada de historial
                history_entry = {
                    "date": now_str,
                    "action": "STATUS_CHANGED",
                    "from": old_op_status,
                    "to": new_op_status,
                    "reason": reason
                }
                if "history" not in ref or not isinstance(ref["history"], list):
                    ref["history"] = []
                ref["history"].append(history_entry)
                print(f"  [CAMBIO] Estado de '{key}' cambió de {old_op_status} -> {new_op_status} (Motivo: {reason})")
            else:
                # Si no hubo cambio de estado pero sí validación exitosa
                ref["verification_status"] = new_ver_status

        if changes_detected > 0:
            self.save_registry()
            print(f"[Checker] Auditoría finalizada. Se guardaron {changes_detected} cambios en el registro.")
        else:
            # Guardamos para registrar la actualización de date_last_checked
            self.save_registry()
            print("[Checker] Auditoría finalizada. No se detectaron cambios de estado de red.")

if __name__ == "__main__":
    checker = ReferenceChecker()
    checker.run_audit()

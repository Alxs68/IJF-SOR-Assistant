import re
import urllib.parse
from reference_manager import ReferenceManager

# Catálogo oficial con detalles y URLs directas a los PDF/páginas de reglas de la IJF
# Mantenido aquí para compatibilidad con código legado y pruebas unitarias
RESOURCE_DETAILS = {
    "DOC-001": {
        "name": "Reglamento SOR 2026 (Sport and Organisation Rules)",
        "url": "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/IJF_Sport_and_Organisation_Rul-1769443746.pdf"
    },
    "DOC-004": {
        "name": "Manual Médico de Judo (PDF)",
        "url": "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/IJF_Sport_and_Organisation_Rul-1769443746.pdf"
    },
    "PAG-001": {
        "name": "Portal de Reglas Interactivas de la IJF",
        "url": "https://rules.ijf.org"
    },
    "PAG-002": {
        "name": "Portal de Reglas IJF: Sección Kumikata (Agarres)",
        "url": "https://rules.ijf.org/gripping"
    },
    "PAG-003": {
        "name": "Portal de Reglas IJF: Sección Scoring (Puntuaciones)",
        "url": "https://rules.ijf.org/scoring"
    },
    "PAG-004": {
        "name": "Portal de Reglas IJF: Sección Penalties (Faltas)",
        "url": "https://rules.ijf.org/penalties"
    },
    "PAG-005": {
        "name": "Portal Oficial de Arbitraje IJF",
        "url": "https://referee.ijf.org"
    },
    "VID-001": {
        "name": "Videoteca de Reglas y Seminarios de Arbitraje IJF",
        "url": "https://www.ijf.org/referee-videos"
    },
    "VID-002": {
        "name": "Video de Arbitraje IJF: Demostración de Agarre (Kumikata)",
        "url": "https://rules.ijf.org/gripping"
    },
    "VID-003": {
        "name": "Video de Arbitraje IJF: Criterio de Caídas Yuko",
        "url": "https://rules.ijf.org/scoring"
    },
    "VID-004": {
        "name": "Video de Arbitraje IJF: Seguridad en Ushiro-Sankaku-Gatame",
        "url": "https://rules.ijf.org/penalties"
    },
    "VID-005": {
        "name": "Video de Arbitraje IJF: Evasión y Pérdida de Tiempo",
        "url": "https://rules.ijf.org/penalties"
    },
    "PPT-001": {
        "name": "Presentación del Congreso de Tecnología",
        "url": "https://www.ijf.org/ijf/documents"
    },
    "PPT-002": {
        "name": "Presentación del Seminario de Arbitraje 2026",
        "url": "https://www.ijf.org/referee-commission"
    },
    "NEW-001": {
        "name": "Comunicado Oficial: Reglas de Arbitraje LA28 (Noticias IJF)",
        "url": "https://www.ijf.org/news/show/the-new-refereeing-rules-point-by-point"
    },
    "NEW-002": {
        "name": "Congreso IJF 2025: Evolución de Tecnología y Reglas (Noticias IJF)",
        "url": "https://www.ijf.org/news/show/ijf-congress-2025-tech-and-rule-evolution"
    },
    "NEW-003": {
        "name": "Reglas Confirmadas para la Temporada 2026 (Noticias IJF)",
        "url": "https://www.ijf.org/news/show/rules-confirmed-ahead-of-the-2026-season"
    },
    "IMG-001": {
        "name": "Diagrama Oficial del Área de Competencia y Tatami",
        "url": "https://www.ijf.org/ijf/documents"
    }
}

# Instanciar el singleton maestro del RRM
_rrm_manager = ReferenceManager()

def clean_url(url):
    return _rrm_manager.clean_url(url)

def append_query_param(url, param_name, param_value):
    return _rrm_manager.append_query_param(url, param_name, param_value)

def resolve_url(kun_id, kun_data):
    """Resuelve la URL operativa de una KUN delegando en el Reference Resolution Manager (RRM)."""
    res = _rrm_manager.resolve_reference(kun_id, kun_data)
    return res.get("url")

def format_citations(answer, retrieved_kuns):
    """
    Busca todas las citas [KUN-xxxx] en la respuesta y las convierte en enlaces clicables
    (o texto tachado si está DELETED) usando las resoluciones del RRM.
    """
    if not answer:
        return ""

    # Crear mapa de KUNs recuperadas para búsqueda rápida O(1)
    retrieved_map = {}
    for k in retrieved_kuns:
        if isinstance(k, dict) and "id_conocimiento" in k:
            retrieved_map[k["id_conocimiento"]] = k
        elif isinstance(k, str):
            retrieved_map[k] = {"id_conocimiento": k}

    def replace_citation(match):
        full_match = match.group(0) # ej. [KUN-0001]
        kun_id = match.group(1)     # ej. KUN-0001
        
        # Validar trazabilidad estricta
        if kun_id in retrieved_map:
            kun_data = retrieved_map[kun_id]
            res = _rrm_manager.resolve_reference(kun_id, kun_data)
            
            if res.get("is_clickable") and res.get("url"):
                return f"[{kun_id}]({res['url']})"
            elif res.get("operational_status") == "DELETED":
                # UX para referencias inhabilitadas/borradas
                return f"~~[{kun_id}]~~"
        
        return full_match

    # Reemplazar citas del tipo [KUN-xxxx]
    formatted = re.sub(r'\[(KUN-\d{4})\]', replace_citation, answer)
    return formatted

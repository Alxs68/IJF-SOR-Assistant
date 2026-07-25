import re
import urllib.parse

# Catálogo oficial con detalles y URLs directas a los PDF/páginas de reglas de la IJF
# Trasladado desde app.py para desacoplar el backend del frontend
RESOURCE_DETAILS = {
    "DOC-001": {
        "name": "Reglamento SOR 2026 (Sport and Organisation Rules)",
        "url": "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/IJF_Sport_and_Organisation_Rul-1769443746.pdf"
    },
    "DOC-004": {
        "name": "Manual Médico de Judo (PDF)",
        "url": "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/Medical_Manual_for_Judo_2026-1768917812.pdf"
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
        "url": "https://www.ijf.org/news"
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

def clean_url(url):
    """Limpia espacios en blanco y caracteres inválidos de una URL base."""
    if not url:
        return ""
    return url.strip()

def append_query_param(url, param_name, param_value):
    """Añade un parámetro de consulta a una URL de forma segura preservando los existentes."""
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

def resolve_url(kun_id, kun_data):
    """
    Resuelve la URL exacta para una KUN basándose en sus metadatos fuente.
    Soporta metadatos estructurados ('fuente') y fallback compatible basado en expresiones regulares.
    """
    if not kun_data:
        return None

    # Caso A: Metadatos Estructurados (Nuevo formato)
    if "fuente" in kun_data and isinstance(kun_data["fuente"], dict):
        fuente = kun_data["fuente"]
        tipo = fuente.get("tipo", "").lower()
        base_url = clean_url(fuente.get("url"))
        
        if not base_url:
            # Fallback a URL de catálogo si no se provee una URL explícita
            source_id = kun_data.get("fuente_origen")
            if source_id in RESOURCE_DETAILS:
                base_url = clean_url(RESOURCE_DETAILS[source_id]["url"])
        
        if not base_url:
            return None

        if tipo == "pdf":
            pagina = fuente.get("pagina")
            if pagina is not None:
                # Los PDFs abren en páginas específicas usando fragmentos del navegador (#page=N)
                parsed = urllib.parse.urlparse(base_url)
                return urllib.parse.urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    f"page={pagina}"
                ))
            return base_url

        elif tipo == "video":
            inicio = fuente.get("inicio_segundos")
            if inicio is not None:
                # El parámetro de tiempo de YouTube u otros portales se añade de forma segura
                return append_query_param(base_url, "t", f"{inicio}s")
            return base_url

        elif tipo == "web":
            return base_url

    # Caso B: Fallback de compatibilidad (Formato antiguo basado en expresiones regulares)
    source_id = kun_data.get("fuente_origen")
    ref_spec = kun_data.get("referencia_especifica", "")

    if source_id in RESOURCE_DETAILS:
        base_url = clean_url(RESOURCE_DETAILS[source_id]["url"])
        if not base_url:
            return None

        # Intento de extracción por regex de página para PDFs
        page_match = re.search(r'(?:pág|página|page)\.?\s*(\d+)', ref_spec, re.IGNORECASE)
        if page_match and base_url.endswith(".pdf"):
            page_num = page_match.group(1)
            parsed = urllib.parse.urlparse(base_url)
            return urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                f"page={page_num}"
            ))

        # Intento de extracción por regex de minutos/segundos para videos de YouTube
        ts_match = re.search(r'(\d{1,2}):(\d{2})', ref_spec)
        if ts_match and "youtube.com" in base_url:
            mins = int(ts_match.group(1))
            secs = int(ts_match.group(2))
            total_secs = mins * 60 + secs
            return append_query_param(base_url, "t", f"{total_secs}s")

        return base_url

    return None

def format_citations(answer, retrieved_kuns):
    """
    Busca todas las citas [KUN-xxxx] en la respuesta y las convierte en enlaces clicables
    si y solo si la KUN citada pertenece al conjunto de KUNs recuperadas.
    """
    if not answer:
        return ""

    # Crear mapa de KUNs recuperadas para búsqueda rápida O(1)
    retrieved_map = {}
    for k in retrieved_kuns:
        if isinstance(k, dict) and "id_conocimiento" in k:
            retrieved_map[k["id_conocimiento"]] = k
        elif isinstance(k, str):
            # Si solo es una cadena de ID, guardamos un dict vacío
            retrieved_map[k] = {"id_conocimiento": k}

    def replace_citation(match):
        full_match = match.group(0) # ej. [KUN-0001]
        kun_id = match.group(1)     # ej. KUN-0001
        
        # Validar trazabilidad estricta
        if kun_id in retrieved_map:
            kun_data = retrieved_map[kun_id]
            url = resolve_url(kun_id, kun_data)
            if url:
                return f"[{kun_id}]({url})"
        
        # Si no fue recuperada o no tiene URL, se queda como texto plano para evitar alucinaciones
        return full_match

    # Reemplazar citas del tipo [KUN-xxxx]
    formatted = re.sub(r'\[(KUN-\d{4})\]', replace_citation, answer)
    return formatted

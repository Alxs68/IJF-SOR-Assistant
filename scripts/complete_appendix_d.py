import os
import re
import sys
import json
import time
import urllib.request
import urllib.error
import subprocess

# Set python path to allow imports from src and scratch
sys.path.append("src")
sys.path.append("scratch")

# Predefined allowed tags catalog from taxonomy_tags.md
ALLOWED_TAGS = [
    "tatami", "dimensions", "safety-area", "age", "cadet", "senior", "men", "women",
    "weight-categories", "contest-duration", "time", "draw", "seeding", "world-ranking-list",
    "repechage", "bracket", "competition-system", "judogi", "color", "control", "sokuteiki",
    "backnumber", "uniform", "dress-code", "procedure", "weigh-in", "official-weigh-in",
    "random-weigh-in", "tolerance", "medical", "concussion", "bleeding", "shido", "hansoku-make",
    "safety", "head-defence", "time-wasting", "kumikata", "grip-breaking", "scoring", "yuko",
    "waza-ari", "ippon", "osaekomi", "ne-waza", "shime-waza", "bear-hug", "conduct", "referee",
    "coaches", "care-system", "portal", "index", "navigation", "documentation", "structure",
    "diagram", "layout", "video"
]

def get_api_key():
    key = None
    if os.path.exists(".env"):
        print("[LOG] Cargando API Key desde archivo .env local...")
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    parts = line.strip().split("=", 1)
                    if parts[0].strip() in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
                        key = parts[1].strip().strip('"').strip("'")
                        break
    if not key:
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    return key

def extract_appendix_d(pdf_path):
    import pypdf
    reader = pypdf.PdfReader(pdf_path)
    num_pages = len(reader.pages)
    
    start_page = None
    print("[LOG] Analizando páginas del PDF para localizar el inicio de 'APPENDIX D'...")
    for page_idx in range(num_pages):
        page_text = reader.pages[page_idx].extract_text() or ""
        if "APPENDIX D" in page_text and ("REFEREEING" in page_text or "Refereeing" in page_text):
            start_page = page_idx
            print(f"[LOG] ¡Apéndice D localizado en la página física {page_idx + 1}!")
            break
            
    if start_page is None:
        for page_idx in range(110, min(140, num_pages)):
            page_text = reader.pages[page_idx].extract_text() or ""
            if "Article 1" in page_text or "ARTICLE 1" in page_text:
                start_page = page_idx
                break
                
    if start_page is None:
        start_page = 124
        
    extracted_text = []
    end_page = start_page + 70
    if end_page > num_pages:
        end_page = num_pages
        
    for page_idx in range(start_page, end_page):
        page_text = reader.pages[page_idx].extract_text() or ""
        # Capture the physical page number inside the loop
        page_num_label = page_idx + 1 # 1-indexed physical page
        
        # Look for page - X inside text
        page_search = re.search(r'page\s*-\s*(\d+)', page_text)
        if page_search:
            page_num_label = int(page_search.group(1))
            
        if "APPENDIX E" in page_text and ("DAN" in page_text or "Grades" in page_text):
            break
            
        # Append page info to the text block so Gemini knows the exact page
        page_header = f"\n[PAGINA_SOR_{page_num_label}]\n"
        extracted_text.append(page_header + page_text)
        
    full_text = "\n".join(extracted_text)
    return full_text

def split_text_into_articles(text):
    # Regex matching "Article X.Y.Z" or "ARTICLE X.Y.Z"
    pattern = re.compile(r'(?:\n|\r\n|^)\s*(?:Article|ARTICLE)\s+([\d\.]+)\b', re.IGNORECASE)
    
    splits = []
    for match in pattern.finditer(text):
        splits.append((match.start(), match.group(1).strip()))
        
    if not splits:
        return [("1", text)]
        
    articles = []
    for idx in range(len(splits)):
        start_idx, art_num = splits[idx]
        end_idx = splits[idx+1][0] if idx + 1 < len(splits) else len(text)
        article_text = text[start_idx:end_idx].strip()
        articles.append((art_num, article_text))
        
    return articles

def call_gemini_to_extract_kuns(article_num, article_text, start_id, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
    # Try to extract the page label if present in the text segment
    page_nums = re.findall(r'\[PAGINA_SOR_(\d+)\]', article_text)
    page_str = f"Página {page_nums[0]}" if page_nums else "Apéndice D"
    
    prompt = f"""
Eres un extractor de datos de reglas oficiales de Judo para un sistema RAG.
Tu tarea es tomar el texto del Artículo {article_num} del Apéndice D (Reglas de Arbitraje) de la IJF y extraer CADA regla general, procedimiento, penalización y excepción en su propia ficha. No omitas ningún tema o división de este artículo.

Para cada regla o tema extraído, genera un objeto JSON conforme exactamente con este esquema:
{{
  "id_conocimiento": "KUN-{str(start_id).zfill(4)}", // Asigna IDs consecutivos comenzando en KUN-{str(start_id).zfill(4)}
  "titulo": "Título corto y claro en español",
  "tipo": "Uno de: REG (Regla), PEN (Penalización), EXC (Excepción), DEF (Definición), CAS (Caso Práctico)",
  "nivel_autoridad": "Norma",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "Texto original en inglés de esta regla específica del artículo",
  "contenido_traduccion": "Traducción formal y precisa al español",
  "interpretacion": "Explicación práctica detallada en español de cómo se aplica en el tatami para árbitros y entrenadores",
  "fuente_origen": "DOC-001",
  "referencia_especifica": "Artículo {article_num} - Apéndice D (Reglas de Arbitraje), {page_str}",
  "tags": ["lista", "de", "tags"], // Usa EXCLUSIVAMENTE tags de esta lista controlada: {json.dumps(ALLOWED_TAGS)}
  "relaciones": [] // Deja este array vacío []
}}

Reglas estrictas:
1. Genera IDs consecutivos (ej. KUN-{str(start_id).zfill(4)}, KUN-{str(start_id+1).zfill(4)}, etc.) para cada objeto que extraigas.
2. Si el artículo tiene sub-artículos o múltiples reglas, extrae cada una como un objeto JSON independiente dentro de la lista.
3. Devuelve ÚNICAMENTE un array JSON válido sin bloques markdown, sin texto introductorio ni explicaciones adicionales.

Texto a analizar:
{article_text}
"""
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "topP": 0.95
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode('utf-8'), 
                headers=headers,
                method='POST'
            )
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                candidates = res_data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        answer = parts[0].get('text', '')
                        return answer
        except urllib.error.HTTPError as e:
            if e.code == 429:
                err_msg = e.read().decode()
                print(f"[LOG] Intento {attempt + 1} falló con 429. Detalles: {err_msg[:200]}...")
                if "free_tier_requests" in err_msg and ("limit: 20" in err_msg or "limit: 0" in err_msg):
                    print("[LOG] Cuota de consultas diarias (RPD) totalmente agotada en Google Cloud. Abortando reintentos.")
                    return None
                wait_time = (attempt + 1) * 15
                print(f"[LOG] Límite por minuto (RPM) alcanzado. Esperando {wait_time} segundos para reintentar...")
                time.sleep(wait_time)
            else:
                print(f"[LOG] Error HTTP {e.code} al invocar la API para el Artículo {article_num}: {e}")
                return None
        except Exception as e:
            print(f"[LOG] Error inesperado en el Intento {attempt + 1} para el Artículo {article_num}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    return None

def clean_json_response(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def append_kuns_to_markdown(kuns, filepath):
    with open(filepath, "a", encoding="utf-8") as f:
        for kun in kuns:
            f.write("\n\n---\n\n")
            f.write(f"### {kun['id_conocimiento']}: {kun['titulo']}\n")
            f.write("```json\n")
            f.write(json.dumps(kun, indent=2, ensure_ascii=False))
            f.write("\n```\n")

def main():
    print("[LOG] ==================================================")
    print("[LOG] INICIANDO RECUPERACIÓN COMPLETA DEL APÉNDICE D")
    print("[LOG] ==================================================")
    
    api_key = get_api_key()
    if not api_key:
        print("[LOG] ERROR: No se detectó la clave API (GEMINI_API_KEY). Abortando.")
        sys.exit(1)
        
    pdf_path = os.path.join("data", "raw", "ijf_sor_2026.pdf")
    if not os.path.exists(pdf_path):
        print(f"[LOG] ERROR: No se encontró el PDF en {pdf_path}. Abortando.")
        sys.exit(1)
        
    # Read existing KUNs to find processed articles and next KUN ID
    markdown_file = os.path.join("data", "markdown", "kuns_doc_001.md")
    
    already_processed = set()
    highest_kun_id = 77
    
    if os.path.exists(markdown_file):
        with open(markdown_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Find processed articles
        for m in re.finditer(r'Apéndice D - Artículo ([\d\.]+)', content):
            already_processed.add(m.group(1).strip())
        for m in re.finditer(r'Artículo ([\d\.]+) - Apéndice D', content):
            already_processed.add(m.group(1).strip())
            
        # Find highest KUN ID
        kun_ids = re.findall(r'KUN-(\d+)', content)
        if kun_ids:
            highest_kun_id = max(highest_kun_id, max(int(kid) for kid in kun_ids))
            
    print(f"[LOG] Artículos ya procesados detectados: {sorted(list(already_processed))}")
    print(f"[LOG] Siguiente KUN ID disponible: KUN-{str(highest_kun_id + 1).zfill(4)}")
    
    current_id = highest_kun_id + 1
    
    # Extract and split text
    raw_text = extract_appendix_d(pdf_path)
    articles = split_text_into_articles(raw_text)
    
    processed_count = 0
    total_kuns_extracted = 0
    
    # Hardcoded target list of missing or failed articles to process in Appendix D
    TARGET_ARTICLES = ["8", "9", "10", "12", "14", "15", "16", "17", "18", "19", "20", "21"]
    
    for art_num, art_text in articles:
        if len(art_text) < 50:
            continue
            
        # Clean article number formatting for matching
        clean_art_num = art_num.strip()
        parent_art_num = clean_art_num.split('.')[0]
        
        if clean_art_num not in TARGET_ARTICLES and parent_art_num not in TARGET_ARTICLES:
            print(f"[LOG] Saltando Artículo {art_num} (no está en la lista de artículos pendientes).")
            continue
            
        print(f"[LOG] Procesando Artículo {art_num} (ID de inicio: KUN-{str(current_id).zfill(4)})...")
        
        raw_json_res = call_gemini_to_extract_kuns(art_num, art_text, current_id, api_key)
        
        # Sleep for 6 seconds after call to respect Gemini RPM rate limit
        time.sleep(6)
        
        if not raw_json_res:
            print(f"[LOG] [ADVERTENCIA] Falló la extracción para el Artículo {art_num}. Reintentando con espera...")
            time.sleep(12)
            raw_json_res = call_gemini_to_extract_kuns(art_num, art_text, current_id, api_key)
            time.sleep(6)
            
        if not raw_json_res:
            print(f"[LOG] [ERROR] No se pudo obtener respuesta del Artículo {art_num} tras reintento. Continuando...")
            continue
            
        clean_json_str = clean_json_response(raw_json_res)
        try:
            kuns_extracted = json.loads(clean_json_str)
            if not isinstance(kuns_extracted, list):
                if isinstance(kuns_extracted, dict):
                    kuns_extracted = [kuns_extracted]
                else:
                    raise ValueError("Formato JSON incorrecto.")
            
            # Filter and sanitize tags
            for kun in kuns_extracted:
                sanitized_tags = []
                for tag in kun.get("tags", []):
                    clean_tag = tag.strip().lower().replace("#", "")
                    if clean_tag in ALLOWED_TAGS:
                        sanitized_tags.append(clean_tag)
                kun["tags"] = sanitized_tags
                
            append_kuns_to_markdown(kuns_extracted, markdown_file)
            
            num_extracted = len(kuns_extracted)
            print(f"[LOG] ¡Éxito! Se extrajeron {num_extracted} KUNs del Artículo {art_num}.")
            
            current_id += num_extracted
            total_kuns_extracted += num_extracted
            processed_count += 1
            
        except Exception as e:
            print(f"[LOG] [ERROR] Error al procesar o parsear el Artículo {art_num}: {e}")
            print(f"[LOG] Contenido: {clean_json_str[:200]}...")
            
    print("[LOG] ==================================================")
    print(f"[LOG] COMPLETADO: {processed_count} nuevos artículos procesados.")
    print(f"[LOG] Total de nuevas KUNs ingresadas: {total_kuns_extracted}")
    print("[LOG] ==================================================")
    
    # Compile Graph
    print("[LOG] Iniciando compilación de Grafo...")
    try:
        from graph_manager import compile_graph_from_markdown
        kg = compile_graph_from_markdown(".")
        print("[LOG] Grafo compilado correctamente.")
    except Exception as e:
        print(f"[LOG] [ERROR] Falló la compilación del grafo: {e}")
        
    # Enforce reciprocity
    print("[LOG] Ejecutando corrección de reciprocidad del grafo...")
    try:
        from fix_graph_reciprocity import fix_reciprocity
        fix_reciprocity(".")
        print("[LOG] Reciprocidad de relaciones enlazada correctamente.")
    except Exception as e:
        print(f"[LOG] [ERROR] Falló la corrección de reciprocidad: {e}")
        
    # Compile Vector Store
    print("[LOG] Iniciando re-indexación del buscador semántico...")
    try:
        from vector_store import VectorStore
        vs = VectorStore()
        kg = compile_graph_from_markdown(".")
        vs.index_kun_corpus(kg.nodes, api_key=api_key)
        vector_index_path = os.path.join("scratch", "vector_store_index.json")
        vs.save_index(vector_index_path)
        print("[LOG] Buscador semántico indexado y guardado correctamente.")
    except Exception as e:
        print(f"[LOG] [ERROR] Falló la re-indexación: {e}")
        
    # Run audit
    print("[LOG] Iniciando auditoría del corpus oficial...")
    try:
        res = subprocess.run([sys.executable, "scratch/corpus_conformity_audit.py"], capture_output=True, text=True)
        print(res.stdout)
    except Exception as e:
        print(f"[LOG] [ERROR] Falló la ejecución de la auditoría: {e}")
        
    print("[LOG] ==================================================")
    print("[LOG] PROCESO DE COMPLETADO TERMINADO.")
    print("[LOG] ==================================================")

if __name__ == "__main__":
    main()

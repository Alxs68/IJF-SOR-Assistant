import os
import re
import sys
import json
import urllib.request
import urllib.error
import subprocess

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
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key and os.path.exists(".env"):
        print("[LOG] Cargando API Key desde archivo .env local...")
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    parts = line.strip().split("=", 1)
                    if parts[0].strip() in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
                        key = parts[1].strip().strip('"').strip("'")
                        break
    return key

def install_pypdf():
    try:
        import pypdf
        print("[LOG] La librería pypdf ya está disponible.")
    except ImportError:
        print("[LOG] pypdf no está instalado. Instalándolo vía pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf"])
        print("[LOG] pypdf instalado correctamente.")

def download_sor_pdf():
    pdf_url = "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/IJF_Sport_and_Organisation_Rul-1769443746.pdf"
    pdf_path = os.path.join("data", "raw", "ijf_sor_2026.pdf")
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    if not os.path.exists(pdf_path):
        print(f"[LOG] Descargando el SOR PDF oficial desde: {pdf_url}...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(pdf_url, headers=headers)
        with urllib.request.urlopen(req) as response, open(pdf_path, 'wb') as out_file:
            out_file.write(response.read())
        print("[LOG] Descarga del PDF finalizada con éxito.")
    else:
        print("[LOG] El PDF del SOR 2026 ya existe localmente.")
    return pdf_path

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
        print("[LOG] No se encontró el texto 'APPENDIX D'. Buscando por fallback de contenido 'Article 1' entre las páginas 110 y 140...")
        for page_idx in range(110, min(140, num_pages)):
            page_text = reader.pages[page_idx].extract_text() or ""
            if "Article 1" in page_text or "ARTICLE 1" in page_text:
                start_page = page_idx
                print(f"[LOG] Fallback: Se localizó el inicio en la página física {page_idx + 1}")
                break
                
    if start_page is None:
        start_page = 124
        print(f"[LOG] Fallback absoluto: Asumiendo que inicia en la página física {start_page + 1}")
        
    extracted_text = []
    end_page = start_page + 70
    if end_page > num_pages:
        end_page = num_pages
        
    print(f"[LOG] Extrayendo páginas físicas desde la {start_page + 1} hasta la {end_page}...")
    for page_idx in range(start_page, end_page):
        page_text = reader.pages[page_idx].extract_text() or ""
        if "APPENDIX E" in page_text and ("DAN" in page_text or "Grades" in page_text):
            print(f"[LOG] Se localizó el inicio de 'APPENDIX E' en la página física {page_idx + 1}. Deteniendo extracción.")
            break
        extracted_text.append(page_text)
        
    full_text = "\n".join(extracted_text)
    print(f"[LOG] Extracción de texto finalizada. Total de caracteres extraídos: {len(full_text)}")
    return full_text

def split_text_into_articles(text):
    # Split text on "Article X" or "ARTICLE X" patterns
    pattern = re.compile(r'(?:\n|\r\n|^)\s*(?:Article|ARTICLE)\s+(\d+)\b', re.IGNORECASE)
    
    splits = []
    for match in pattern.finditer(text):
        splits.append((match.start(), int(match.group(1))))
        
    if not splits:
        # Fallback: if no matches, return the text as a single large article
        print("[LOG] No se detectaron divisiones claras de artículos. Procesando todo el texto en un solo lote.")
        return [(1, text)]
        
    articles = []
    for idx in range(len(splits)):
        start_idx, art_num = splits[idx]
        end_idx = splits[idx+1][0] if idx + 1 < len(splits) else len(text)
        article_text = text[start_idx:end_idx].strip()
        articles.append((art_num, article_text))
        
    print(f"[LOG] Se identificaron {len(articles)} artículos independientes para procesar.")
    return articles

def call_gemini_to_extract_kuns(article_num, article_text, start_id, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
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
  "referencia_especifica": "Apéndice D - Artículo {article_num}",
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
    except Exception as e:
        print(f"[LOG] Error al invocar la API de Gemini para el Artículo {article_num}: {e}")
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
    print("[LOG] INICIANDO PIPELINE DE PROCESAMIENTO DEL APÉNDICE D")
    print("[LOG] ==================================================")
    
    api_key = get_api_key()
    if not api_key:
        print("[LOG] ERROR: No se detectó la clave API (GEMINI_API_KEY). Abortando.")
        sys.exit(1)
        
    # Step 1: Install pypdf
    install_pypdf()
    
    # Step 2: Download PDF
    pdf_path = download_sor_pdf()
    
    # Step 3: Extract Appendix D text
    raw_text = extract_appendix_d(pdf_path)
    
    # Step 4: Split into articles
    articles = split_text_into_articles(raw_text)
    
    # Determine the next available KUN ID
    current_id = 78
    markdown_file = os.path.join("data", "markdown", "kuns_doc_001.md")
    
    processed_count = 0
    total_kuns_extracted = 0
    
    for art_num, art_text in articles:
        if len(art_text) < 50:
            continue
            
        print(f"[LOG] Procesando Artículo {art_num} (ID de inicio: KUN-{str(current_id).zfill(4)})...")
        raw_json_res = call_gemini_to_extract_kuns(art_num, art_text, current_id, api_key)
        
        if not raw_json_res:
            print(f"[LOG] [ADVERTENCIA] Falló la extracción para el Artículo {art_num}. Reintentando una vez...")
            raw_json_res = call_gemini_to_extract_kuns(art_num, art_text, current_id, api_key)
            
        if not raw_json_res:
            print(f"[LOG] [ERROR] No se pudo obtener respuesta del Artículo {art_num}. Continuando con el siguiente...")
            continue
            
        clean_json_str = clean_json_response(raw_json_res)
        try:
            kuns_extracted = json.loads(clean_json_str)
            if not isinstance(kuns_extracted, list):
                if isinstance(kuns_extracted, dict):
                    kuns_extracted = [kuns_extracted]
                else:
                    raise ValueError("Formato JSON retornado no es lista ni diccionario.")
            
            # Filter and sanitize KUN tags
            for kun in kuns_extracted:
                sanitized_tags = []
                for tag in kun.get("tags", []):
                    clean_tag = tag.strip().lower().replace("#", "")
                    if clean_tag in ALLOWED_TAGS:
                        sanitized_tags.append(clean_tag)
                kun["tags"] = sanitized_tags
                
            append_kuns_to_markdown(kuns_extracted, markdown_file)
            
            num_extracted = len(kuns_extracted)
            print(f"[LOG] ¡Éxito! Se extrajeron e ingresaron {num_extracted} KUNs del Artículo {art_num}.")
            
            current_id += num_extracted
            total_kuns_extracted += num_extracted
            processed_count += 1
            
        except Exception as e:
            print(f"[LOG] [ERROR] Error al procesar o parsear el JSON de KUNs del Artículo {art_num}: {e}")
            print(f"[LOG] Contenido bruto recibido: {clean_json_str[:200]}...")
            
    print("[LOG] ==================================================")
    print(f"[LOG] EXTRACCIÓN FINALIZADA. {processed_count} artículos procesados.")
    print(f"[LOG] Total de nuevas KUNs ingresadas a kuns_doc_001.md: {total_kuns_extracted}")
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
    print("[LOG] PROCESO COMPLETADO SATISFACTORIAMENTE.")
    print("[LOG] ==================================================")

if __name__ == "__main__":
    main()

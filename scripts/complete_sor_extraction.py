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

def call_gemini_page_extraction(page_num, page_text, start_id, source_id, ref_prefix, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
    prompt = f"""
Eres un extractor de datos de reglas oficiales de Judo para un sistema RAG.
Tu tarea es tomar el texto de la página {page_num} del reglamento oficial de la IJF (SOR 2026) y extraer CADA regla general, procedimiento, penalización y excepción en su propia ficha. No omitas ningún tema o detalle de esta página.

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
  "contenido_original": "Texto original en inglés de esta regla específica de la página",
  "contenido_traduccion": "Traducción formal y precisa al español",
  "interpretacion": "Explicación práctica detallada en español de cómo se aplica esta regla en competencia para atletas, árbitros o entrenadores",
  "fuente_origen": "{source_id}",
  "referencia_especifica": "{ref_prefix}, Página {page_num}",
  "tags": ["lista", "de", "tags"], // Usa EXCLUSIVAMENTE tags de esta lista controlada: {json.dumps(ALLOWED_TAGS)}
  "relaciones": [] // Deja este array vacío []
}}

Reglas estrictas:
1. Genera IDs consecutivos (ej. KUN-{str(start_id).zfill(4)}, KUN-{str(start_id+1).zfill(4)}, etc.) para cada objeto que extraigas.
2. Si la página tiene múltiples reglas, subreglas o procedimientos, extrae cada uno como un objeto JSON independiente dentro de la lista.
3. Devuelve ÚNICAMENTE un array JSON válido sin bloques markdown (sin ```json ni ```), sin texto introductorio ni explicaciones adicionales.

Texto de la página a analizar:
{page_text}
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
                wait_time = (attempt + 1) * 20
                print(f"[LOG] Límite por minuto alcanzado. Esperando {wait_time} segundos para reintentar...")
                time.sleep(wait_time)
            else:
                print(f"[LOG] Error HTTP {e.code} al invocar la API para la Página {page_num}: {e}")
                return None
        except Exception as e:
            print(f"[LOG] Error inesperado en el Intento {attempt + 1} para la Página {page_num}: {e}")
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

def get_highest_kun_id():
    highest = 326
    markdown_dir = os.path.join("data", "markdown")
    if os.path.exists(markdown_dir):
        files = [f for f in os.listdir(markdown_dir) if f.startswith("kuns_") and f.endswith(".md")]
        for f in files:
            with open(os.path.join(markdown_dir, f), "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
            kun_ids = re.findall(r'KUN-(\d+)', content)
            if kun_ids:
                highest = max(highest, max(int(kid) for kid in kun_ids))
    return highest

def main():
    print("[LOG] ==================================================")
    print("[LOG] INICIANDO EXTRACCIÓN COMPLETA DEL REGLAMENTO IJF")
    print("[LOG] ==================================================")
    
    api_key = get_api_key()
    if not api_key:
        print("[LOG] ERROR: No se detectó la clave API (GEMINI_API_KEY). Abortando.")
        sys.exit(1)
        
    pdf_path = os.path.join("data", "raw", "ijf_sor_2026.pdf")
    if not os.path.exists(pdf_path):
        print(f"[LOG] ERROR: No se encontró el PDF en {pdf_path}. Abortando.")
        sys.exit(1)
        
    import pypdf
    reader = pypdf.PdfReader(pdf_path)
    
    highest_id = get_highest_kun_id()
    current_id = highest_id + 1
    print(f"[LOG] Siguiente KUN ID disponible: KUN-{str(current_id).zfill(4)}")
    
    # Define targets to process (page ranges are 1-indexed printed/physical pages)
    # We will use 0-indexed values for reading
    TARGET_SECTIONS = [
        {
            "name": "General Information (Sección 1)",
            "start": 11,
            "end": 20,
            "source_id": "DOC-001",
            "ref_prefix": "Sección 1 - Información General",
            "dest_file": os.path.join("data", "markdown", "kuns_doc_001.md")
        },
        {
            "name": "Competition Systems (Sección 2)",
            "start": 21,
            "end": 45,
            "source_id": "DOC-001",
            "ref_prefix": "Sección 2 - Sistemas de Competencia",
            "dest_file": os.path.join("data", "markdown", "kuns_doc_001.md")
        },
        {
            "name": "World Ranking Lists (Sección 3)",
            "start": 47,
            "end": 62,
            "source_id": "DOC-001",
            "ref_prefix": "Sección 3 - Clasificación Mundial (WRL)",
            "dest_file": os.path.join("data", "markdown", "kuns_doc_001.md")
        },
        {
            "name": "Weigh-in (Sección 6)",
            "start": 73,
            "end": 79,
            "source_id": "DOC-001",
            "ref_prefix": "Sección 6 - Reglamento de Pesaje",
            "dest_file": os.path.join("data", "markdown", "kuns_doc_001.md")
        },
        {
            "name": "Education and Coaching (Sección 7)",
            "start": 80,
            "end": 83,
            "source_id": "DOC-001",
            "ref_prefix": "Sección 7 - Educación y Entrenadores",
            "dest_file": os.path.join("data", "markdown", "kuns_doc_001.md")
        },
        {
            "name": "Competition Venue (Sección 8)",
            "start": 84,
            "end": 90,
            "source_id": "DOC-001",
            "ref_prefix": "Sección 8 - Instalaciones de Competencia",
            "dest_file": os.path.join("data", "markdown", "kuns_doc_001.md")
        },
        {
            "name": "Judogi Rules (Apéndice C)",
            "start": 107,
            "end": 123,
            "source_id": "DOC-001",
            "ref_prefix": "Apéndice C - Reglamento de Judogi",
            "dest_file": os.path.join("data", "markdown", "kuns_doc_001.md")
        },
        {
            "name": "Medical Handbook (Apéndice E)",
            "start": 192,
            "end": 195,
            "source_id": "DOC-004",
            "ref_prefix": "Apéndice E - Manual Médico y Antidopaje IJF",
            "dest_file": os.path.join("data", "markdown", "kuns_doc_004.md")
        }
    ]
    
    total_pages_processed = 0
    total_kuns_extracted = 0
    
    for section in TARGET_SECTIONS:
        print(f"\n[LOG] >>> PROCESANDO SECCIÓN: {section['name']} (Págs {section['start']} - {section['end']}) <<<")
        
        for page_num in range(section["start"], section["end"] + 1):
            # pypdf pages list is 0-indexed
            page_text = reader.pages[page_num - 1].extract_text() or ""
            
            if len(page_text.strip()) < 50:
                print(f"[LOG] Saltando Página {page_num} por texto insuficiente.")
                continue
                
            print(f"[LOG] Enviando Página {page_num} a Gemini (ID de inicio: KUN-{str(current_id).zfill(4)})...")
            
            raw_res = call_gemini_page_extraction(
                page_num, 
                page_text, 
                current_id, 
                section["source_id"], 
                section["ref_prefix"], 
                api_key
            )
            
            # Sleep 7.5 seconds to respect API rate limits (10 RPM)
            time.sleep(7.5)
            
            if not raw_res:
                print(f"[LOG] [ADVERTENCIA] Reintentando Página {page_num} tras espera...")
                time.sleep(15)
                raw_res = call_gemini_page_extraction(
                    page_num, 
                    page_text, 
                    current_id, 
                    section["source_id"], 
                    section["ref_prefix"], 
                    api_key
                )
                time.sleep(7.5)
                
            if not raw_res:
                print(f"[LOG] [ERROR] No se pudo obtener respuesta de la Página {page_num}. Continuando...")
                continue
                
            clean_json_str = clean_json_response(raw_res)
            try:
                kuns_extracted = json.loads(clean_json_str)
                if not isinstance(kuns_extracted, list):
                    if isinstance(kuns_extracted, dict):
                        kuns_extracted = [kuns_extracted]
                    else:
                        raise ValueError("Respuesta no es una lista ni diccionario.")
                
                # Sanitize and validate tags
                for kun in kuns_extracted:
                    sanitized = []
                    for t in kun.get("tags", []):
                        clean_t = t.strip().lower().replace("#", "")
                        if clean_t in ALLOWED_TAGS:
                            sanitized.append(clean_t)
                    kun["tags"] = sanitized
                    
                # Append to file
                append_kuns_to_markdown(kuns_extracted, section["dest_file"])
                
                num_kuns = len(kuns_extracted)
                print(f"[LOG] ¡Éxito! Página {page_num} procesada. {num_kuns} KUNs ingresadas.")
                
                current_id += num_kuns
                total_kuns_extracted += num_kuns
                total_pages_processed += 1
                
            except Exception as e:
                print(f"[LOG] [ERROR] Error al procesar o parsear el JSON de la Página {page_num}: {e}")
                print(f"[LOG] Respuesta bruta: {clean_json_str[:300]}...")
                
    print("\n[LOG] ==================================================")
    print(f"[LOG] EXTRACCIÓN SISTEMÁTICA COMPLETADA.")
    print(f"[LOG] Páginas procesadas: {total_pages_processed}")
    print(f"[LOG] Nuevas KUNs ingresadas: {total_kuns_extracted}")
    print(f"[LOG] Siguiente KUN ID: KUN-{str(current_id).zfill(4)}")
    print("[LOG] ==================================================")
    
    # Compile Graph
    print("[LOG] Recompilando Grafo de Conocimiento...")
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
    print("[LOG] Iniciando re-indexación de embeddings vectoriales...")
    try:
        from vector_store import VectorStore
        vs = VectorStore()
        kg = compile_graph_from_markdown(".")
        vs.index_kun_corpus(kg.nodes, api_key=api_key)
        vector_index_path = os.path.join("scratch", "vector_store_index.json")
        vs.save_index(vector_index_path)
        print("[LOG] Re-indexación semántica finalizada con éxito.")
    except Exception as e:
        print(f"[LOG] [ERROR] Falló la re-indexación: {e}")
        
    # Run audit
    print("[LOG] Iniciando auditoría final de conformidad del corpus...")
    try:
        res = subprocess.run([sys.executable, "scratch/corpus_conformity_audit.py"], capture_output=True, text=True)
        print(res.stdout)
    except Exception as e:
        print(f"[LOG] [ERROR] Falló la auditoría: {e}")
        
    print("[LOG] Pipeline completo de extracción y procesamiento finalizado.")

if __name__ == "__main__":
    main()

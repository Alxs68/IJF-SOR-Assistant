import sys
import os
import subprocess

# Set paths
sys.path.append("src")
sys.path.append("scratch")

def get_api_key():
    key = None
    if os.path.exists(".env"):
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

def main():
    api_key = get_api_key()
    if not api_key:
        print("[ERROR] GEMINI_API_KEY not found.")
        sys.exit(1)
        
    print("[LOG] Recompilando Grafo de Conocimiento...")
    from graph_manager import compile_graph_from_markdown
    kg = compile_graph_from_markdown(".")
    print("[LOG] Grafo compilado correctamente.")
    
    print("[LOG] Corrigiendo reciprocidad de relaciones...")
    from fix_graph_reciprocity import fix_reciprocity
    fix_reciprocity(".")
    print("[LOG] Reciprocidad corregida.")
    
    print("[LOG] Re-indexando buscador semántico en lotes...")
    from vector_store import VectorStore
    vs = VectorStore()
    kg = compile_graph_from_markdown(".")
    vs.index_kun_corpus(kg.nodes, api_key=api_key)
    vs.save_index(os.path.join("scratch", "vector_store_index.json"))
    print("[LOG] Buscador re-indexado correctamente.")
    
    print("[LOG] Ejecutando auditoría de conformidad...")
    res = subprocess.run([sys.executable, "scratch/corpus_conformity_audit.py"], capture_output=True, text=True)
    print(res.stdout)
    
if __name__ == "__main__":
    main()

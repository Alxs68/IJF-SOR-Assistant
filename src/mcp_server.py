import json
import os
import glob
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("IJF-SOR-Assistant")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
REF_REGISTRY_PATH = os.path.join(DATA_DIR, "references", "reference_registry.json")
MARKDOWN_DIR = os.path.join(DATA_DIR, "markdown")

@mcp.resource("file://reference_registry")
def get_reference_registry() -> str:
    """Read the official reference registry containing all known documents and URLs."""
    try:
        with open(REF_REGISTRY_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "{}"

@mcp.resource("file://kuns/{kun_id}")
def get_kun(kun_id: str) -> str:
    """Read a specific Knowledge Unit Node (KUN) markdown file. e.g. kuns_doc_001"""
    path = os.path.join(MARKDOWN_DIR, f"{kun_id}.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: KUN {kun_id} not found."

@mcp.tool()
def add_knowledge_unit(kun_data: str) -> str:
    """
    Ingest a new Knowledge Unit (KUN) structured as JSON.
    Expected JSON format:
    {
      "id_conocimiento": "KUN-VID-006",
      "titulo": "...",
      "tipo": "...",
      "contenido_original": "...",
      "contenido_traduccion": "...",
      "interpretacion": "...",
      "fuente_origen": "VID-006",
      "referencia_especifica": "Minuto 3:12",
      "tags": [...]
    }
    """
    try:
        data = json.loads(kun_data)
        kun_id = data.get("id_conocimiento")
        if not kun_id:
            return "Error: Missing 'id_conocimiento'."
            
        file_path = os.path.join(MARKDOWN_DIR, f"{kun_id.lower().replace('-', '_')}.md")
        
        # Build Markdown content
        md_content = "---\n"
        for key, value in data.items():
            if key == "tags":
                md_content += f"tags: {json.dumps(value)}\n"
            elif key == "relaciones":
                pass
            else:
                md_content += f"{key}: {value}\n"
        md_content += "---\n\n"
        md_content += f"# {data.get('titulo')}\n\n"
        md_content += f"**Original:**\n{data.get('contenido_original', '')}\n\n"
        md_content += f"**Traducción:**\n{data.get('contenido_traduccion', '')}\n\n"
        md_content += f"**Interpretación:**\n{data.get('interpretacion', '')}\n"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        return f"Successfully added KUN to {file_path}. Next, please update the reference registry if this is a new source."
    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

@mcp.tool()
def update_reference_registry(source_id: str, payload: str) -> str:
    """
    Update or add a source in the reference_registry.json.
    Provide the source_id (e.g. DOC-005, VID-006) and the JSON payload representing the source metadata.
    """
    try:
        new_source = json.loads(payload)
        registry = {}
        if os.path.exists(REF_REGISTRY_PATH):
            with open(REF_REGISTRY_PATH, "r", encoding="utf-8") as f:
                registry = json.load(f)
                
        registry[source_id] = new_source
        
        with open(REF_REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
            
        return f"Successfully updated reference registry for source {source_id}."
    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

if __name__ == "__main__":
    mcp.run()

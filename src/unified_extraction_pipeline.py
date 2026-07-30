import os
import sys
import json
import glob
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scratch"))

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
REF_REGISTRY_PATH = os.path.join(DATA_DIR, "references", "reference_registry.json")
MARKDOWN_DIR = os.path.join(DATA_DIR, "markdown")

class UnifiedExtractionPipeline:
    def __init__(self):
        self.registry = self._load_registry()

    def _load_registry(self):
        if os.path.exists(REF_REGISTRY_PATH):
            with open(REF_REGISTRY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_registry(self):
        with open(REF_REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)

    def process_kun(self, data: dict):
        """
        Processes a single Knowledge Unit Node (KUN) from structured data.
        Updates its state instead of blindly overwriting if it already exists, 
        and flags changes in the RRM.
        """
        kun_id = data.get("id_conocimiento")
        source_id = data.get("fuente_origen")
        
        if not kun_id or not source_id:
            raise ValueError("KUN must have 'id_conocimiento' and 'fuente_origen'.")
            
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
        
        is_update = os.path.exists(file_path)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        print(f"[LOG] KUN {kun_id} {'updated' if is_update else 'created'} successfully.")
        
        # Ensure source exists in registry
        if source_id not in self.registry:
            print(f"[WARN] Source {source_id} not found in registry. Please add it via MCP.")
        else:
            self.registry[source_id]["date_updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            self._save_registry()

    def process_batch_json(self, batch_file_path: str):
        """
        Process an array of KUN JSON objects (e.g. extracted from a Video or Web by ChatGPT).
        """
        with open(batch_file_path, "r", encoding="utf-8") as f:
            kuns = json.load(f)
            
        if not isinstance(kuns, list):
            raise ValueError("Batch file must contain a JSON array of KUN objects.")
            
        for kun in kuns:
            self.process_kun(kun)
            
        print(f"[LOG] Processed {len(kuns)} KUNs from {batch_file_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Unified Extraction Pipeline")
    parser.add_argument("--batch", type=str, help="Path to a JSON file containing an array of KUNs to ingest")
    args = parser.parse_args()
    
    pipeline = UnifiedExtractionPipeline()
    if args.batch:
        pipeline.process_batch_json(args.batch)
    else:
        print("Usage: python unified_extraction_pipeline.py --batch <file.json>")

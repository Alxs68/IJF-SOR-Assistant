import os
import json
import re
import math
from collections import Counter

# Lista de stopwords básicas en inglés y español para evitar falsos positivos por palabras vacías
STOPWORDS = {
    "de", "la", "el", "en", "y", "a", "los", "las", "un", "una", "por", "con", "para", "o",
    "the", "of", "and", "in", "to", "a", "is", "for", "on", "by", "with", "at", "as", "from"
}

class CandidateRAGAdapter:
    """
    Adaptador de RAG aislado para el nuevo corpus reconstruido (SOR 2026-08-14).
    Consume directamente passages_candidate.json, knowledge_graph_candidate.json
    y vector_index_candidate.json sin tocar el código productivo de src/.
    """
    def __init__(self, base_dir="data/processed/rebuild_2026_08"):
        self.base_dir = base_dir
        self.passages_path = os.path.join(base_dir, "passages_candidate.json")
        self.graph_path = os.path.join(base_dir, "knowledge_graph_candidate.json")
        self.index_path = os.path.join(base_dir, "vector_index_candidate.json")
        
        self.passages = []
        self.passages_by_id = {}
        self.graph = {}
        self.index = {}
        
        self.load_resources()

    def load_resources(self):
        with open(self.passages_path, "r", encoding="utf-8") as f:
            self.passages = json.load(f)
        self.passages_by_id = {p["passage_id"]: p for p in self.passages}
        
        with open(self.graph_path, "r", encoding="utf-8") as f:
            self.graph = json.load(f)
            
        with open(self.index_path, "r", encoding="utf-8") as f:
            self.index = json.load(f)

    def retrieve(self, query: str, top_k: int = 3, min_score: float = 0.12, expand_graph: bool = True):
        raw_tokens = re.findall(r"[a-zA-Z0-9_\-]+", query.lower())
        q_tokens = [t for t in raw_tokens if t not in STOPWORDS]
        
        # Si no quedan términos con contenido semántico, abstenerse inmediatamente
        if not q_tokens:
            return {
                "status": "ABSTAIN",
                "message": "Consulta no contiene términos con significancia semántica o normativa.",
                "evidence": [],
                "related_articles": []
            }
            
        q_counts = Counter(q_tokens)
        q_norm_sq = 0.0
        q_vec = {}
        idf = self.index.get("idf", {})
        
        for t, c in q_counts.items():
            w = (c / len(q_tokens)) * idf.get(t, 0.0)
            q_vec[t] = w
            q_norm_sq += w * w
            
        q_norm = math.sqrt(q_norm_sq) or 1.0
        q_vec = {t: w / q_norm for t, w in q_vec.items()}
        
        scores = []
        for pid, d_vec in self.index.get("vectors", {}).items():
            score = sum(q_vec[t] * d_vec.get(t, 0.0) for t in q_vec)
            if score >= min_score:
                scores.append((score, pid))
                
        scores.sort(reverse=True)
        top_hits = scores[:top_k]
        
        # Abstención si no hay evidencia por encima del umbral mínimo
        if not top_hits:
            return {
                "status": "ABSTAIN",
                "message": "No se encontró evidencia normativa suficiente en el SOR 2026-08-14 para responder a la consulta.",
                "evidence": [],
                "related_articles": []
            }
            
        retrieved_passages = []
        seed_ids = set()
        for score, pid in top_hits:
            p = self.passages_by_id.get(pid)
            if p:
                p_copy = dict(p)
                p_copy["relevance_score"] = round(score, 4)
                retrieved_passages.append(p_copy)
                seed_ids.add(pid)
                
        # Expansión acotada por grafo
        related_nodes = []
        if expand_graph:
            for edge in self.graph.get("edges", []):
                if edge["source"] in seed_ids and edge["target"] not in seed_ids:
                    target_p = self.passages_by_id.get(edge["target"])
                    if target_p:
                        related_nodes.append({
                            "relation": edge["relation_type"],
                            "target_article": edge["target_article"],
                            "passage_id": edge["target"],
                            "pdf_page_index": target_p["pdf_page_index"],
                            "title": target_p["heading_path"][0] if target_p["heading_path"] else ""
                        })
                        
        return {
            "status": "EVIDENCE_FOUND",
            "evidence": retrieved_passages,
            "related_articles": related_nodes[:3]
        }

if __name__ == "__main__":
    adapter = CandidateRAGAdapter()
    print("Adaptador candidato inicializado con éxito.")
    
    # Prueba 1: Consulta válida
    res1 = adapter.retrieve("cadet head defence shido")
    print("\n--- PRUEBA 1: 'cadet head defence shido' ---")
    print("Status:", res1["status"])
    for ev in res1["evidence"]:
        print(f" -> [{ev['passage_id']}] Pág {ev['pdf_page_index']} (Score: {ev['relevance_score']}): {ev['heading_path'][0]}")
        
    # Prueba 2: Consulta fuera de dominio (Abstención verificada)
    res2 = adapter.retrieve("reglas de fuera de juego en futbol soccer fifa")
    print("\n--- PRUEBA 2: 'reglas de fuera de juego en futbol soccer fifa' ---")
    print("Status:", res2["status"])
    if res2["status"] == "ABSTAIN":
        print("Message:", res2["message"])

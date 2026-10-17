"""
Reasoning Retrieval Engine (RRE) for IJF-SOR-Assistant
======================================================
Official Normative Corpus: IJF Sport and Organisation Rules (14 August 2026)

Key Architectural Pillars:
1. Dense Semantic Embeddings: 384-dimensional dense vectors (all-MiniLM-L6-v2) cached locally.
2. Sparse Lexical Scoring: Normalized exact term and phrase matching with normative stopword filtering.
3. Reciprocal Rank Fusion (RRF): Robust rank combination prioritizing evidence present in both channels.
4. Knowledge Graph Expansion: Context enrichment along verified cross-reference edges (112 edges).
5. Strict Abstention Filter: Immediate rejection of out-of-domain or ungrounded queries.
"""

import os
import re
import json
import math
import numpy as np
from collections import Counter
import glob

# Domain-specific stopwords (English & Spanish)
STOPWORDS = {
    "de", "la", "el", "en", "y", "a", "los", "las", "un", "una", "por", "con", "para", "o",
    "the", "of", "and", "in", "to", "is", "for", "on", "by", "with", "at", "as", "from", "an"
}

class ReasoningRetrievalEngine:
    """
    RRE: High-precision hybrid neural-lexical retriever with graph expansion
    designed for arbitration and regulatory rules.
    """

    def __init__(self, base_dir="data/processed/rebuild_2026_08"):
        self.base_dir = base_dir
        self.passages_file = os.path.join(base_dir, "passages_candidate.json")
        self.graph_file = os.path.join(base_dir, "knowledge_graph_candidate.json")
        self.sparse_index_file = os.path.join(base_dir, "vector_index_candidate.json")
        self.dense_embeddings_file = os.path.join(base_dir, "dense_embeddings_candidate.npy")
        self.dense_meta_file = os.path.join(base_dir, "dense_embeddings_meta.json")

        self.passages = []
        self.passages_by_id = {}
        self.graph_edges = []
        self.graph_adj = {}  # pid -> list of target pids
        self.sparse_index = {}
        self.dense_embeddings = None
        self.dense_meta = {}
        self.dense_model = None

        self._load_resources()
        self._init_dense_model()

    def _load_resources(self):
        if not os.path.exists(self.passages_file):
            raise FileNotFoundError(f"RRE passages file not found: {self.passages_file}")

        with open(self.passages_file, "r", encoding="utf-8") as f:
            self.passages = json.load(f)
        self.passages_by_id = {p["passage_id"]: p for p in self.passages}

        if os.path.exists(self.graph_file):
            with open(self.graph_file, "r", encoding="utf-8") as f:
                gdata = json.load(f)
                self.graph_edges = gdata.get("edges", [])
                for edge in self.graph_edges:
                    src = edge.get("source")
                    tgt = edge.get("target")
                    if src and tgt:
                        self.graph_adj.setdefault(src, []).append({
                            "target": tgt,
                            "relation": edge.get("relation_type", "references_article")
                        })

        if os.path.exists(self.sparse_index_file):
            with open(self.sparse_index_file, "r", encoding="utf-8") as f:
                self.sparse_index = json.load(f)

        if os.path.exists(self.dense_embeddings_file) and os.path.exists(self.dense_meta_file):
            self.dense_embeddings = np.load(self.dense_embeddings_file)
            with open(self.dense_meta_file, "r", encoding="utf-8") as f:
                self.dense_meta = json.load(f)

    def _init_dense_model(self):
        """Loads cached local sentence-transformer without network dependencies."""
        try:
            import sentence_transformers
            cache_pattern = os.path.expanduser('~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/*')
            snapshots = glob.glob(cache_pattern)
            if snapshots:
                self.dense_model = sentence_transformers.SentenceTransformer(snapshots[0], local_files_only=True)
            else:
                self.dense_model = sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"[RRE] Warning: Local dense model could not be initialized ({e}). Operating in sparse/lexical fallback mode.")
            self.dense_model = None

    # Mapeo bilingüe de términos técnicos del judo
    SPANISH_TO_ENGLISH_SYNONYMS = {
        "cabeza": "head",
        "defensa": "defence",
        "defenderse": "defence",
        "sancion": "penalty",
        "sanciones": "penalties",
        "sanciona": "penalty",
        "arbitro": "referee",
        "arbitraje": "refereeing",
        "pesaje": "weigh-in",
        "peso": "weight",
        "estrangulacion": "shime-waza",
        "estrangulaciones": "shime-waza",
        "luxacion": "kansetsu-waza",
        "luxaciones": "kansetsu-waza",
        "repesca": "repechage",
        "combate": "contest",
        "duracion": "duration",
        "tiempo": "time",
        "medico": "medical",
        "doctor": "doctor",
        "categoria": "category",
        "categorias": "categories",
        "cadetes": "cadet",
        "cadete": "cadet",
        "juniors": "junior",
        "seniors": "senior",
        "oro": "gold",
        "puntos": "points",
        "puntuacion": "scoring"
    }

    def _tokenize(self, text):
        clean = text.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        raw_tokens = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", clean)
        tokens = []
        for t in raw_tokens:
            if t not in STOPWORDS:
                tokens.append(t)
                if t in self.SPANISH_TO_ENGLISH_SYNONYMS:
                    tokens.append(self.SPANISH_TO_ENGLISH_SYNONYMS[t])
        return tokens

    def _sparse_search(self, query, top_k=20):
        tokens = self._tokenize(query)
        if not tokens or not self.sparse_index:
            return []

        counts = Counter(tokens)
        idf = self.sparse_index.get("idf", {})
        q_vec = {}
        q_norm_sq = 0.0
        for t, c in counts.items():
            w = (c / len(tokens)) * idf.get(t, 1.0)
            q_vec[t] = w
            q_norm_sq += w * w
        q_norm = math.sqrt(q_norm_sq) or 1.0
        q_vec = {t: w / q_norm for t, w in q_vec.items()}

        scores = []
        for pid, d_vec in self.sparse_index.get("vectors", {}).items():
            dot = sum(q_vec[t] * d_vec.get(t, 0.0) for t in q_vec)
            if dot > 0.02:
                scores.append((pid, dot))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _dense_search(self, query, top_k=20):
        if self.dense_model is None or self.dense_embeddings is None:
            return []

        q_emb = self.dense_model.encode(query, normalize_embeddings=True)
        # Cosine similarity is dot product of normalized vectors
        sims = np.dot(self.dense_embeddings, q_emb)
        top_indices = np.argsort(sims)[::-1][:top_k]

        passage_ids = self.dense_meta.get("passage_ids", [p["passage_id"] for p in self.passages])
        results = []
        for idx in top_indices:
            score = float(sims[idx])
            if score > 0.15:
                results.append((passage_ids[idx], score))
        return results

    def retrieve(self, query: str, top_k: int = 4, min_confidence: float = 0.015, expand_graph: bool = True):
        """
        Executes Reasoning Retrieval with Reciprocal Rank Fusion (RRF) and Graph Expansion.
        """
        # 1. Domain Validation & Tokenization
        tokens = self._tokenize(query)
        if not tokens:
            return {
                "status": "ABSTAIN",
                "reason": "EMPTY_OR_NON_SUBSTANTIVE_QUERY",
                "message": "La consulta no contiene términos normativos o técnicos válidos.",
                "evidence": [],
                "related_passages": []
            }

        # 2. Dual-channel retrieval
        # Filtrar sparse_hits con umbral de significancia técnica
        sparse_hits = [h for h in self._sparse_search(query, top_k=25) if h[1] >= 0.05]
        dense_hits = self._dense_search(query, top_k=25)

        # 3. Dual-channel verification and Reciprocal Rank Fusion (RRF)
        # Si no hay anclaje léxico suficiente, la similitud densa debe ser claramente relevante (>0.35)
        if not sparse_hits and (not dense_hits or dense_hits[0][1] < 0.35):
            return {
                "status": "ABSTAIN",
                "reason": "OUT_OF_DOMAIN",
                "message": "Sin evidencia normativa certificada en el SOR 2026-08 para los términos consultados.",
                "evidence": [],
                "related_passages": []
            }

        k_rrf = 60
        rrf_scores = {}
        for rank, (pid, score) in enumerate(sparse_hits, 1):
            rrf_scores[pid] = rrf_scores.get(pid, 0.0) + (1.0 / (k_rrf + rank))

        for rank, (pid, score) in enumerate(dense_hits, 1):
            rrf_scores[pid] = rrf_scores.get(pid, 0.0) + (1.2 / (k_rrf + rank))

        # 4. Strict Abstention on domain irrelevance
        if not rrf_scores:
            return {
                "status": "ABSTAIN",
                "reason": "OUT_OF_DOMAIN",
                "message": "Sin evidencia normativa certificada en el SOR 2026-08.",
                "evidence": [],
                "related_passages": []
            }

        ranked_pids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        top_seeds = [pid for pid, score in ranked_pids if score >= min_confidence][:top_k]

        if not top_seeds:
            return {
                "status": "ABSTAIN",
                "reason": "BELOW_CONFIDENCE_THRESHOLD",
                "message": "La evidencia recuperada no alcanza el umbral de certeza requerido.",
                "evidence": [],
                "related_passages": []
            }

        # 5. Build structured evidence records
        evidence_list = []
        for pid in top_seeds:
            p = self.passages_by_id.get(pid)
            if p:
                rec = {
                    "passage_id": pid,
                    "title": p.get("heading_path", [""])[0] if p.get("heading_path") else f"Artículo {p.get('article_id')}",
                    "article_id": p.get("article_id"),
                    "page": p.get("pdf_page_index"),
                    "score": round(rrf_scores[pid], 4),
                    "source_url": f"{p.get('source_url', '')}#page={p.get('pdf_page_index')}",
                    "text_original": p.get("text_original", ""),
                    "is_seed": True
                }
                evidence_list.append(rec)

        # 6. Graph-Guided Cross-Reference Expansion
        related_passages = []
        if expand_graph:
            seen_targets = set(top_seeds)
            for pid in top_seeds:
                neighbors = self.graph_adj.get(pid, [])
                for n in neighbors:
                    tgt = n["target"]
                    if tgt not in seen_targets and tgt in self.passages_by_id:
                        seen_targets.add(tgt)
                        tp = self.passages_by_id[tgt]
                        related_passages.append({
                            "passage_id": tgt,
                            "source_seed": pid,
                            "relation": n["relation"],
                            "article_id": tp.get("article_id"),
                            "page": tp.get("pdf_page_index"),
                            "title": tp.get("heading_path", [""])[0] if tp.get("heading_path") else f"Art. {tp.get('article_id')}",
                            "source_url": f"{tp.get('source_url', '')}#page={tp.get('pdf_page_index')}",
                            "text_original": tp.get("text_original", "")
                        })

        return {
            "status": "SUCCESS",
            "query": query,
            "evidence": evidence_list,
            "related_passages": related_passages[:3]
        }

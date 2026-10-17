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

    def __init__(self, base_dir="data/processed/rebuild_2026_08", allow_degraded: bool | None = None):
        self.base_dir = base_dir
        if allow_degraded is None:
            allow_degraded = os.environ.get("RRE_ALLOW_DEGRADED_LEXICAL", "").strip().lower() in {"1", "true", "yes", "on"}
        self.allow_degraded = bool(allow_degraded)
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
        self.operating_mode = "UNINITIALIZED"
        self.degradation_reason = None
        self.source_sha256_verified = False

        self._load_resources()
        self._validate_dense_matrix_and_meta()
        self._init_dense_model()
        self._determine_operating_mode()

        if not self.allow_degraded and self.operating_mode != "HYBRID":
            raise RuntimeError(
                f"Inicialización de RRE rechazada: Se requiere modo HYBRID pero el motor operaría en modo "
                f"'{self.operating_mode}' debido a: {self.degradation_reason}"
            )

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

        if os.path.exists(self.dense_embeddings_file):
            try:
                self.dense_embeddings = np.load(self.dense_embeddings_file)
            except Exception as e:
                raise ValueError(f"Error crítico al leer la matriz densa {self.dense_embeddings_file}: {e}")

        if os.path.exists(self.dense_meta_file):
            with open(self.dense_meta_file, "r", encoding="utf-8") as f:
                self.dense_meta = json.load(f)

    def _validate_dense_matrix_and_meta(self):
        """
        Validación exhaustiva de integridad matemática y referencial de la matriz densa.
        Si la matriz o sus metadatos están presentes pero presentan cualquier corrupción o desalineación,
        se lanza un ValueError explícito y accionable.
        """
        if self.dense_embeddings is None and not self.dense_meta:
            # Matriz no provista en absoluto (degradación léxica permitida únicamente si se solicita explícitamente)
            return

        if self.dense_embeddings is None and self.dense_meta:
            raise ValueError(
                f"Inconsistencia crítica en RRE: Existen metadatos ({self.dense_meta_file}) "
                f"pero no se encontró el archivo de matriz densa ({self.dense_embeddings_file})."
            )

        if self.dense_embeddings is not None and not self.dense_meta:
            raise ValueError(
                f"Inconsistencia crítica en RRE: La matriz densa existe ({self.dense_embeddings_file}) "
                f"pero faltan sus metadatos de procedencia ({self.dense_meta_file})."
            )

        # 1. Validación de forma y número de pasajes
        expected_rows = len(self.passages)
        expected_dim = 384
        if not isinstance(self.dense_embeddings, np.ndarray):
            raise TypeError("La matriz densa debe ser una instancia válida de numpy.ndarray.")

        if len(self.dense_embeddings.shape) != 2:
            raise ValueError(
                f"Forma inválida en matriz densa: Se esperaban 2 dimensiones, se obtuvieron {self.dense_embeddings.ndim}."
            )

        n_rows, n_cols = self.dense_embeddings.shape
        if n_rows != expected_rows:
            raise ValueError(
                f"Discrepancia en número de pasajes: El corpus contiene {expected_rows} pasajes "
                f"pero la matriz densa contiene {n_rows} filas."
            )

        if n_cols != expected_dim:
            raise ValueError(
                f"Discrepancia dimensional: Dimensión del modelo esperada {expected_dim}, "
                f"pero la matriz densa tiene dimensión {n_cols}."
            )

        # 2. Valores finitos (sin NaNs ni Infs)
        if not np.all(np.isfinite(self.dense_embeddings)):
            nan_count = int(np.sum(np.isnan(self.dense_embeddings)))
            inf_count = int(np.sum(np.isinf(self.dense_embeddings)))
            raise ValueError(
                f"Matriz densa corrupta: Contiene valores no finitos ({nan_count} NaNs, {inf_count} Infs)."
            )

        # 3. Coherencia de Metadatos
        meta_num = self.dense_meta.get("num_passages")
        if meta_num != expected_rows:
            raise ValueError(
                f"Metadatos inconsistentes: 'num_passages'={meta_num} != pasajes del corpus={expected_rows}."
            )

        meta_dim = self.dense_meta.get("dimension")
        if meta_dim != expected_dim:
            raise ValueError(
                f"Metadatos inconsistentes: 'dimension'={meta_dim} != dimensión esperada={expected_dim}."
            )

        meta_model = self.dense_meta.get("model_name")
        if meta_model != "sentence-transformers/all-MiniLM-L6-v2":
            raise ValueError(
                f"Metadatos incompatibles: Modelo de origen declarado '{meta_model}', se requiere 'sentence-transformers/all-MiniLM-L6-v2'."
            )

        # 4. Verificación exhaustiva 1:1 de passage_ids (longitud, duplicados y orden)
        meta_ids = self.dense_meta.get("passage_ids", [])
        if len(meta_ids) != expected_rows:
            raise ValueError(
                f"Longitud de passage_ids en metadatos ({len(meta_ids)}) difiere del corpus ({expected_rows})."
            )

        if len(set(meta_ids)) != len(meta_ids):
            duplicates = [item for item, count in Counter(meta_ids).items() if count > 1]
            raise ValueError(f"Identificadores duplicados en passage_ids de metadatos: {duplicates[:5]}.")

        corpus_ids = [p["passage_id"] for p in self.passages]
        if meta_ids != corpus_ids:
            # Buscar el primer índice discordante para mensaje de error preciso
            for i, (m_id, c_id) in enumerate(zip(meta_ids, corpus_ids)):
                if m_id != c_id:
                    raise ValueError(
                        f"Desalineación en orden de pasajes en índice {i}: "
                        f"Metadatos='{m_id}' vs Corpus='{c_id}'."
                    )
            raise ValueError("La lista de passage_ids de metadatos no coincide exactamente con el orden del corpus.")

        # 5. Integridad del hash del corpus declarado frente a fuente de verdad
        expected_sha = "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620"
        meta_sha = str(self.dense_meta.get("source_sha256", "")).lower()
        if meta_sha != expected_sha:
            raise ValueError(
                f"Discrepancia criptográfica en metadatos: source_sha256 declarado '{meta_sha}' "
                f"no coincide con la edición oficial SOR 2026-08 '{expected_sha}'."
            )

        # Comprobar si el PDF físico existe en disco para verificación efectiva
        pdf_candidate = os.path.join(os.path.dirname(os.path.dirname(self.base_dir)), "raw", "sor_2026_08_rebuild", "IJF_Sport_and_Organisation_Rules_2026_08_14.pdf")
        if os.path.exists(pdf_candidate):
            import hashlib
            h = hashlib.sha256()
            with open(pdf_candidate, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            real_sha = h.hexdigest().lower()
            if real_sha == expected_sha:
                self.source_sha256_verified = True
            else:
                raise ValueError(
                    f"Fallo de verificación criptográfica del PDF físico: SHA-256 calculado '{real_sha}' "
                    f"no coincide con el esperado '{expected_sha}'."
                )

    def _init_dense_model(self):
        """Load only an explicitly prepared local snapshot; never download during app startup."""
        configured_path = os.environ.get("RRE_MODEL_PATH", "").strip()
        candidates = []
        if configured_path:
            candidates.append(os.path.abspath(os.path.expanduser(configured_path)))

        cache_pattern = os.path.expanduser(
            "~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/*"
        )
        candidates.extend(sorted(glob.glob(cache_pattern), reverse=True))

        try:
            from sentence_transformers import SentenceTransformer
        except Exception as e:
            self.dense_model = None
            self.degradation_reason = f"No se pudo importar SentenceTransformer: {e}"
            return

        errors = []
        seen = set()
        for candidate in candidates:
            if candidate in seen or not os.path.isdir(candidate):
                continue
            seen.add(candidate)
            try:
                model = SentenceTransformer(candidate, local_files_only=True)
                dimension = model.get_sentence_embedding_dimension()
                if dimension != 384:
                    raise ValueError(
                        f"El modelo local devuelve dimensión {dimension}; se requieren 384."
                    )
                self.dense_model = model
                self.degradation_reason = None
                return
            except Exception as e:
                errors.append(f"{candidate}: {e}")

        self.dense_model = None
        self.degradation_reason = (
            "No se encontró un snapshot local verificado de "
            "sentence-transformers/all-MiniLM-L6-v2. Ejecute primero "
            "'python scripts/setup_model.py'."
        )
        if errors:
            self.degradation_reason += " Errores de carga local: " + " | ".join(errors[:2])

    def _determine_operating_mode(self):
        """Select HYBRID only when dense, sparse and graph resources are coherent."""
        expected_sha = "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620"
        corpus_ids = set(self.passages_by_id)

        # The lexical channel must always be usable; without it, neither mode can retrieve.
        index = self.sparse_index
        idf = index.get("idf") if isinstance(index, dict) else None
        vectors = index.get("vectors") if isinstance(index, dict) else None
        if not isinstance(idf, dict) or not idf or not isinstance(vectors, dict) or not vectors:
            raise RuntimeError(
                f"Índice léxico TF-IDF ausente o inválido: {self.sparse_index_file}. "
                "Reconstruya el índice antes de iniciar RRE."
            )
        if index.get("num_docs") != len(self.passages):
            raise ValueError(
                f"Número de documentos del índice léxico ({index.get('num_docs')}) "
                f"no coincide con los pasajes ({len(self.passages)})."
            )
        if str(index.get("source_sha256", "")).lower() != expected_sha:
            raise ValueError("El índice léxico no declara el SHA-256 de la edición oficial SOR 2026-08.")
        if set(vectors) != corpus_ids:
            missing = sorted(corpus_ids - set(vectors))
            extra = sorted(set(vectors) - corpus_ids)
            raise ValueError(
                f"IDs del índice léxico incompatibles con el corpus. Faltantes: {missing[:3]}; "
                f"no reconocidos: {extra[:3]}."
            )
        for term, weight in idf.items():
            if not isinstance(term, str) or not isinstance(weight, (int, float)) or not math.isfinite(weight):
                raise ValueError("El índice léxico contiene pesos IDF no válidos.")
        for pid, vector in vectors.items():
            if not isinstance(vector, dict) or not vector:
                raise ValueError(f"Vector léxico vacío o inválido para el pasaje {pid}.")
            if any(not isinstance(w, (int, float)) or not math.isfinite(w) for w in vector.values()):
                raise ValueError(f"El vector léxico del pasaje {pid} contiene pesos no válidos.")

        # A graph can be absent only in explicitly authorized lexical-degraded mode.
        graph_ok = bool(self.graph_edges)
        for edge in self.graph_edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src not in corpus_ids or tgt not in corpus_ids:
                raise ValueError(
                    f"El grafo normativo contiene una arista hacia/desde un pasaje inexistente: {src} -> {tgt}."
                )

        has_matrix = (
            isinstance(self.dense_embeddings, np.ndarray)
            and self.dense_embeddings.shape == (len(self.passages), 384)
        )
        has_model = self.dense_model is not None
        missing = []
        if not has_matrix:
            missing.append("matriz densa ausente")
        if not has_model:
            missing.append(self.degradation_reason or "modelo neuronal no disponible")
        if not graph_ok:
            missing.append("grafo normativo ausente o sin aristas válidas")

        if not missing:
            self.operating_mode = "HYBRID"
            self.degradation_reason = None
        else:
            self.operating_mode = "DEGRADED_LEXICAL"
            self.degradation_reason = "; ".join(missing)
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
                "related_passages": [],
                "operating_mode": self.operating_mode,
                "degradation_reason": self.degradation_reason,
                "source_sha256_verified": self.source_sha256_verified
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
                "related_passages": [],
                "operating_mode": self.operating_mode,
                "degradation_reason": self.degradation_reason,
                "source_sha256_verified": self.source_sha256_verified
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
                "related_passages": [],
                "operating_mode": self.operating_mode,
                "degradation_reason": self.degradation_reason,
                "source_sha256_verified": self.source_sha256_verified
            }

        ranked_pids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        top_seeds = [pid for pid, score in ranked_pids if score >= min_confidence][:top_k]

        if not top_seeds:
            return {
                "status": "ABSTAIN",
                "reason": "BELOW_CONFIDENCE_THRESHOLD",
                "message": "La evidencia recuperada no alcanza el umbral de certeza requerido.",
                "evidence": [],
                "related_passages": [],
                "operating_mode": self.operating_mode,
                "degradation_reason": self.degradation_reason,
                "source_sha256_verified": self.source_sha256_verified
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
            "related_passages": related_passages[:3],
            "operating_mode": self.operating_mode,
            "degradation_reason": self.degradation_reason,
            "source_sha256_verified": self.source_sha256_verified
        }

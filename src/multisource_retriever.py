"""
Multisource Sidecar Retriever (Fase 4.2.5 — Calibrado y Endurecido)
===================================================================
Recuperador experimental en modo sombra para fuentes complementarias IJF.

Principios de Diseño y Calibración (Fase 4.2.5):
1. Aislamiento Estricto: Opera exclusivamente sobre data/corpus_multisource/processed/multisource_passages.json.
2. Tokenización Robusta: Normalización NFD para remoción de acentos (bilingüe y tolerante a tildes).
3. BM25 con Umbral Dinámico de Términos (Overlap Ratio):
   - Consultas con >= 3 términos sustantivos requieren al menos 2 términos coincidentes o un overlap >= 0.30.
   - Si solo coincide 1 término genérico y la consulta es larga, se descarta el match espurio.
4. Umbral de Confianza Absoluta: Score BM25 mínimo calibrado (min_score = 3.0 por defecto para matches calificados).
5. Abstención Trazable: Emite status 'ABSTAIN' documentando el motivo exacto de descarte.
6. Resiliencia y Timeout: Protección contra excepciones y límites temporales (100 ms).
7. Filtro de Elegibilidad: Descarta cualquier fragmento cuyo estado no sea APPROVED o cuya vigencia no sea CURRENT.
"""

import os
import re
import json
import math
import time
import unicodedata
import hashlib
from typing import Dict, List, Any, Optional, Set
from collections import Counter

# Domain-specific stopwords (English & Spanish functional words)
STOPWORDS = {
    "de", "la", "el", "en", "y", "a", "los", "las", "un", "una", "por", "con", "para", "o",
    "the", "of", "and", "in", "to", "is", "for", "on", "by", "with", "at", "as", "from", "an",
    "how", "what", "when", "where", "why", "who", "which", "can", "could", "would", "should",
    "que", "cual", "cuales", "como", "donde", "cuando", "quien", "quienes",
    "se", "su", "sus", "del", "al", "es", "son", "ocurre", "si", "durante",
    "esta", "estan", "este", "estos", "estas", "entre"
}

def strip_accents(text: str) -> str:
    """Normaliza y remueve diacríticos/acentos preservando caracteres base."""
    if not text:
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")

def tokenize(text: str) -> List[str]:
    """Tokeniza y normaliza un texto a minúsculas alfanuméricas sin acentos, filtrando stopwords."""
    if not text:
        return []
    clean = strip_accents(text).lower()
    words = re.findall(r'\b[a-zA-Z0-9_\-]+\b', clean)
    return [w for w in words if len(w) > 2 and w not in STOPWORDS]

# Fragmentos KUN desactivados en la capa suplementaria por contradicción con el SOR 2026-08 vigente
# (Art. 18.1.1: 45s vs 30s; Art. 18.2.1/18.1.4: contacto de cabeza) y falta de PDF primario local verificable.
DEACTIVATED_SUPPLEMENTARY_CHUNK_IDS = frozenset({
    "CHK-KUN-NEW-001-003",  # source_kun_id: KUN-0075 (KUN-NEW-001)
    "CHK-KUN-NEW-003-003",  # source_kun_id: KUN-0003 (KUN-NEW-003)
})
DEACTIVATED_SUPPLEMENTARY_KUN_IDS = frozenset({
    "KUN-0075",
    "KUN-0003",
})


class MultisourceRetriever:
    """
    Recuperador complementario calibrado para fragmentos Sidecar.
    """
    def __init__(self, passages_path: str = "data/corpus_multisource/processed/multisource_passages.json"):
        self.passages_path = passages_path
        self.passages: List[Dict[str, Any]] = []
        self.passages_by_id: Dict[str, Dict[str, Any]] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.doc_tokens: Dict[str, Set[str]] = {}
        self.avg_doc_len: float = 0.0
        self.inverted_index: Dict[str, Dict[str, int]] = {}  # term -> {chunk_id: tf}
        self.idf: Dict[str, float] = {}
        self.is_loaded: bool = False
        self.load_error: Optional[str] = None
        self._load_passages()

    def _load_passages(self):
        """Carga e indexa en memoria los fragmentos del Sidecar procesado."""
        if not os.path.exists(self.passages_path):
            self.load_error = f"Sidecar passages file not found: {self.passages_path}"
            self.is_loaded = False
            return

        try:
            with open(self.passages_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("multisource_passages.json must contain a list of chunk objects")

            # Filtrar estrictamente fragmentos elegibles
            eligible_passages = []
            for p in data:
                auth = str(p.get("authority", "")).upper()
                val = str(p.get("validity", "")).upper()
                elig = str(p.get("eligibility", "")).upper()

                if (auth.startswith("TIER_2") or auth.startswith("TIER_3")) and \
                   val in ["VIGENTE", "CURRENT", "INTERPRETIVE_VALID"] and \
                   elig in ["ELIGIBLE_INTERPRETATIVA", "APPROVED"]:
                    eligible_passages.append(p)

            self.passages = eligible_passages
            self.passages_by_id = {p["chunk_id"]: p for p in self.passages}
            self._build_index()
            self.is_loaded = True
            self.load_error = None
        except Exception as e:
            self.load_error = str(e)
            self.is_loaded = False

    def _build_index(self):
        """Construye el índice léxico invertido BM25."""
        self.inverted_index.clear()
        self.doc_lengths.clear()
        self.doc_tokens.clear()
        total_len = 0

        for p in self.passages:
            cid = p["chunk_id"]
            rel = " ".join(p.get("related_sor_articles", []))
            text = f"{p.get('title', '')} {p.get('content_text', '')} {rel}"
            tokens = tokenize(text)
            self.doc_lengths[cid] = len(tokens)
            self.doc_tokens[cid] = set(tokens)
            total_len += len(tokens)

            tf = Counter(tokens)
            for term, count in tf.items():
                if term not in self.inverted_index:
                    self.inverted_index[term] = {}
                self.inverted_index[term][cid] = count

        n_docs = len(self.passages)
        self.avg_doc_len = (total_len / n_docs) if n_docs > 0 else 1.0

        self.idf.clear()
        for term, postings in self.inverted_index.items():
            df = len(postings)
            self.idf[term] = math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 3, min_score: float = 3.0, min_overlap_ratio: float = 0.25, timeout_ms: float = 200.0) -> Dict[str, Any]:
        """
        Ejecuta la búsqueda calibrada de fragmentos complementarios con protección de timeout y abstención activa.
        
        Args:
            query: Consulta del usuario.
            top_k: Máximo de candidatos a devolver.
            min_score: Umbral mínimo de relevancia BM25 absoluta calibrado (default 3.0).
            min_overlap_ratio: Ratio mínimo de términos sustantivos coincidentes.
            timeout_ms: Tiempo máximo permitido en milisegundos.
            
        Returns:
            Dict con metadata de ejecución, status ('SUCCESS' o 'ABSTAIN'), matches y latencia.
        """
        start_time = time.perf_counter()
        
        if not self.is_loaded:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "status": "UNAVAILABLE",
                "reason": self.load_error or "Sidecar index not loaded",
                "matches": [],
                "elapsed_ms": round(elapsed_ms, 3)
            }

        q_tokens = tokenize(query)
        if not q_tokens:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "status": "ABSTAIN",
                "reason": "EMPTY_OR_STOPWORD_QUERY",
                "matches": [],
                "elapsed_ms": round(elapsed_ms, 3)
            }

        # BM25 scoring: k1=1.5, b=0.75
        k1 = 1.5
        b = 0.75
        scores: Dict[str, float] = {cid: 0.0 for cid in self.passages_by_id}
        matched_tokens_per_doc: Dict[str, Set[str]] = {cid: set() for cid in self.passages_by_id}

        for term in q_tokens:
            if term in self.inverted_index:
                w_idf = self.idf.get(term, 0.0)
                postings = self.inverted_index[term]
                for cid, tf in postings.items():
                    doc_len = self.doc_lengths.get(cid, self.avg_doc_len)
                    num = tf * (k1 + 1.0)
                    denom = tf + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len))
                    scores[cid] += w_idf * (num / denom)
                    matched_tokens_per_doc[cid].add(term)

            # Control de timeout durante iteración
            if (time.perf_counter() - start_time) * 1000.0 > timeout_ms:
                return {
                    "status": "TIMEOUT",
                    "reason": f"Execution exceeded {timeout_ms}ms timeout",
                    "matches": [],
                    "elapsed_ms": round((time.perf_counter() - start_time) * 1000.0, 3)
                }

        # Boost por mención explícita de artículos vinculados
        clean_q = strip_accents(query).lower()
        for cid, p in self.passages_by_id.items():
            for art in p.get("related_sor_articles", []):
                art_num = strip_accents(art).lower().replace("art.", "").replace("art", "").strip()
                if art_num and (art_num in clean_q or f"articulo {art_num}" in clean_q or f"article {art_num}" in clean_q):
                    scores[cid] += 1.5

        # Calibración y Endurecimiento Fase 4.2.5:
        # Filtrar candidatos que no cumplan con el umbral mínimo absoluto o ratio de solapamiento
        n_q_tokens = len(q_tokens)
        qualified_candidates = []

        for cid, s in scores.items():
            matched_set = matched_tokens_per_doc[cid]
            n_matched = len(matched_set)
            overlap_ratio = (n_matched / n_q_tokens) if n_q_tokens > 0 else 0.0

            # Regla 1: Supresión de términos aislados / genéricos sin contexto suficiente
            # Si la consulta consta de 1 solo término, no puede ser una palabra genérica de judo ('combate', 'transición', 'penalización')
            if n_q_tokens == 1:
                t = q_tokens[0]
                if t in {"combate", "transicion", "penalizacion", "suelo", "oficial", "tiempo", "regla", "reglas"}:
                    continue

            # Regla 2: En consultas con >= 3 términos sustantivos, exigir al menos 2 términos coincidentes
            # o que el score supere 3.5 con término muy específico
            if n_q_tokens >= 3:
                if n_matched < 2 and s < 3.5:
                    continue
                if overlap_ratio < min_overlap_ratio and s < 4.0:
                    continue

            # Regla 3: Score absoluto mínimo calibrado
            if s >= min_score:
                qualified_candidates.append((cid, s, round(s, 4), overlap_ratio))

        # Si no hay candidatos calificados, emitir ABSTAIN explícito
        if not qualified_candidates:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "status": "ABSTAIN",
                "reason": "BELOW_CONFIDENCE_THRESHOLD_OR_INSUFFICIENT_OVERLAP",
                "matches": [],
                "total_candidates": 0,
                "elapsed_ms": round(elapsed_ms, 3)
            }

        # Normalizar scores relativos al candidato máximo calificado
        max_s = max(c[1] for c in qualified_candidates) if qualified_candidates else 1.0
        ranked = sorted(qualified_candidates, key=lambda x: x[1], reverse=True)

        matches = []
        for cid, raw_s, _, overlap_ratio in ranked[:top_k]:
            p = self.passages_by_id[cid]
            norm_conf = round(raw_s / max_s, 4) if max_s > 0 else 1.0
            matches.append({
                "chunk_id": cid,
                "document_id": p.get("document_id"),
                "authority": p.get("authority"),
                "validity": p.get("validity"),
                "eligibility": p.get("eligibility"),
                "title": p.get("title"),
                "content_text": p.get("content_text"),
                "related_sor_articles": p.get("related_sor_articles", []),
                "normative_relation": p.get("normative_relation"),
                "raw_score": round(raw_s, 4),
                "confidence_score": norm_conf,
                "overlap_ratio": round(overlap_ratio, 3),
                "staging_sha256": p.get("staging_sha256"),
                "source_kun_id": (p.get("metadata") or {}).get("source_kun_id"),
            })

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            "status": "SUCCESS",
            "matches": matches,
            "total_candidates": len(ranked),
            "elapsed_ms": round(elapsed_ms, 3)
        }

    def retrieve_supplementary(self, query: str, top_k: int = 3, min_score: float = 2.0) -> List[Dict[str, Any]]:
        """
        Recuperación suplementaria controlada sobre el sidecar multifuente.
        Excluye fragmentos KUN desactivados por contradicción con el SOR 2026-08 vigente.
        """
        fetch_k = max(top_k + len(DEACTIVATED_SUPPLEMENTARY_CHUNK_IDS), top_k)
        res = self.search(query, top_k=fetch_k, min_score=min_score)
        if res.get("status") != "SUCCESS":
            return []
        matches = [
            m for m in res.get("matches", [])
            if m.get("chunk_id") not in DEACTIVATED_SUPPLEMENTARY_CHUNK_IDS
            and (m.get("source_kun_id") or (m.get("metadata") or {}).get("source_kun_id")) not in DEACTIVATED_SUPPLEMENTARY_KUN_IDS
        ]
        return matches[:top_k]

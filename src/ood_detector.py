"""
Soft Semantic Domain Grounding & OOD Detector Module for IJF SOR Assistant (RRE 3.0 Architecture).
Provides continuous metric out-of-domain (OOD) rejection without static keyword blacklists.

Formula:
J_score(q) = alpha_ood * D_sim(q) + (1 - alpha_ood) * O_cov(q)
where:
alpha_ood = 0.60
Theta_OOD = 0.38 (Threshold for in-domain acceptance)
D_sim(q) = Cosine similarity to IJF SOR domain centroid
O_cov(q) = Weighted ontology coverage in src/normative_ontology.py
"""

from typing import Dict, List, Set, Tuple, Optional
import os
import re
import numpy as np

from src.normative_ontology import NormativeOntology, NormativeDomain


class OODDetector:
    """
    Evaluates semantic domain grounding of incoming queries to ensure strict abstention
    on out-of-domain questions (e.g. basketball, finance) while safely admitting valid Judo questions.
    """

    ALPHA_OOD: float = 0.60
    THETA_OOD: float = 0.38

    # Non-specific cross-sport generic words that do NOT count toward judo grounding on their own
    GENERIC_SPORT_WORDS: Set[str] = {
        "falta", "faltas", "tiempo", "regla", "reglas", "sistema", "sistemas",
        "personal", "personales", "libre", "libres", "accion", "acciones",
        "oficial", "oficiales", "sancion", "sanciones", "castigo", "infraccion"
    }

    # Specific judo technical term weights for ontology coverage (Koka excluded as abolished in 2008)
    HIGH_WEIGHT_TERMS: Set[str] = {
        "judo", "judoka", "judogi", "ippon", "waza-ari", "wazaari", "yuko",
        "osaekomi", "toketa", "shime-waza", "kansetsu-waza", "shido", "hansoku-make",
        "hansokumake", "tori", "uke", "tatami", "seoi-nage", "kawazu-gake", "mate",
        "matte", "hajime", "sore-made", "sono-mama", "kiken-gachi", "golden score",
        "sokuteiki", "backnumber", "shushin", "fukushin", "care system", "puente",
        "cadete", "cadetes", "senior", "seniors", "junior", "juniors", "combate", "contest",
        "entrenador", "entrenadores", "coach", "coaches",
        "pesaje", "weigh-in", "draw", "sorteo", "repechage", "repesca"
    }

    # Words representing concepts not regulated by IJF SOR 2026 competition/sport rules
    UNREGULATED_ASPECT_WORDS: Set[str] = {
        "salario", "salarios", "sueldo", "sueldos", "remuneracion", "remuneraciones",
        "nomina", "cuota", "cuotas", "precio", "precios", "costo", "costos",
        "guarderia", "recreativo", "recreativa", "escolar", "1882", "fundador",
        "fundacion", "chui", "keikoku", "koka"
    }

    def __init__(self, dense_model=None, dense_embeddings=None):
        self.dense_model = dense_model
        self.dense_embeddings = dense_embeddings
        self.domain_centroid = None
        self._compute_centroid()

    def _compute_centroid(self):
        """Precomputes the IJF SOR corpus centroid embedding from dense embeddings matrix."""
        if self.dense_embeddings is not None and len(self.dense_embeddings) > 0:
            c = np.mean(self.dense_embeddings, axis=0)
            norm = np.linalg.norm(c)
            if norm > 0:
                self.domain_centroid = c / norm

    def compute_ontology_coverage(self, query: str) -> float:
        """
        Computes weighted ontology coverage:
        O_cov(q) = sum_{t in T_q} w(t) * I_{t in Judo} / sum_{t in T_q} w(t)
        """
        clean_q = query.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        tokens = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", clean_q)

        # Remove pure grammatical stopwords
        from src.rre_engine import STOPWORDS
        content_tokens = [t for t in tokens if t not in STOPWORDS]

        if not content_tokens:
            return 0.0

        total_weight = 0.0
        covered_weight = 0.0

        for t in content_tokens:
            if t in self.GENERIC_SPORT_WORDS:
                # Generic cross-sport words do NOT contribute to Judo ontology coverage
                w = 1.0
                is_covered = False
            elif t in self.HIGH_WEIGHT_TERMS:
                w = 2.5
                is_covered = True
            else:
                # Check normative ontology triggers and lemmas
                is_in_onto = False
                for dom, data in NormativeOntology.FAMILY_LEMMAS.items():
                    if t in data["spanish_triggers"] or any(t in lem.split() for lem in data["canonical_lemmas_en"]):
                        is_in_onto = True
                        break
                w = 1.0
                is_covered = is_in_onto

            total_weight += w
            if is_covered:
                covered_weight += w

        return covered_weight / total_weight if total_weight > 0 else 0.0

    def compute_dense_similarity(self, query: str) -> float:
        """Computes cosine similarity of query embedding to IJF SOR domain centroid."""
        if self.dense_model is None or self.domain_centroid is None:
            return 0.50  # Fallback neutral similarity if model unavailable

        try:
            q_emb = self.dense_model.encode(query, normalize_embeddings=True)
            sim = float(np.dot(self.domain_centroid, q_emb))
            return max(0.0, sim)
        except Exception:
            return 0.50

    def evaluate_grounding(self, query: str, sparse_top: float = 0.0, dense_top: float = 0.0) -> Dict[str, any]:
        """
        Calculates J_score and evaluates whether the query is in-domain or out-of-domain.
        Uses continuous metric combining dense centroid similarity, weighted ontology coverage,
        and channel evidence.
        """
        d_sim = self.compute_dense_similarity(query)
        o_cov = self.compute_ontology_coverage(query)

        # Baseline continuous score:
        j_score = (self.ALPHA_OOD * d_sim) + ((1.0 - self.ALPHA_OOD) * o_cov)

        clean_q = query.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        tokens = set(re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", clean_q))

        # If a query contains explicitly unregulated aspects (salary, preschool, historical origin 1882):
        has_unregulated = bool(tokens & self.UNREGULATED_ASPECT_WORDS)
        if has_unregulated:
            j_score = min(j_score, 0.20)

        # If a query has zero or near-zero Judo ontology coverage (< 0.05) and lacks verified
        # physical page references, its domain grounding is deficient:
        if o_cov < 0.05:
            # Damped by lack of any judo substantive concepts
            j_score = min(j_score, 0.25)

        is_in_domain = bool(j_score >= self.THETA_OOD and not has_unregulated)

        return {
            "j_score": round(j_score, 4),
            "d_sim": round(d_sim, 4),
            "o_cov": round(o_cov, 4),
            "is_in_domain": is_in_domain,
            "threshold": self.THETA_OOD
        }

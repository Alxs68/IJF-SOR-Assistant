"""
Normative Semantic Ranker Module for IJF SOR Assistant (RRE 3.0 Architecture).
Provides calibrated post-fusion semantic re-ranking to resolve domain ambiguity,
such as technical landing evaluations (e.g. 90-degree lateral falls) vs tatami/infrastructure dimensions.

Formula:
S_final(q, p_i) = S_hyb(q, p_i) * [1 - lambda_infra * I_infra(p_i) * I_eval(q)] * [1 + gamma_match * I_intent_match(q, p_i)]
where:
lambda_infra = 0.65 (calibrated dampening for infrastructure during scoring/penalty queries)
gamma_match = 0.25 (intent alignment boost)
"""

from typing import Dict, List, Set, Tuple, Optional
import re


class NormativeSemanticRanker:
    """
    Reranks Top-K candidates after RRF / hybrid fusion based on query evaluation intent
    and passage structural taxonomy.
    """

    LAMBDA_INFRA: float = 0.65
    GAMMA_MATCH: float = 0.25

    # Evaluation and scoring intent triggers in queries
    EVALUATION_TRIGGERS: Set[str] = {
        "puntuacion", "puntuaciones", "puntua", "puntuar", "score", "scoring",
        "wazaari", "waza-ari", "ippon", "yuko", "sancion", "sanciones", "shido",
        "hansokumake", "hansoku-make", "descalificacion", "cae", "caida", "caer",
        "proyecta", "proyeccion", "proyecciones", "inmoviliza", "inmovilizacion",
        "toketa", "osaekomi", "derriba", "derribo", "valoracion", "valora",
        "perpendicular", "costado", "espalda", "codo", "brazo", "rodilla",
        "puente", "bridge"
    }

    # Strict inhibitors for pure infrastructure queries (preserving tatami measurements)
    PURE_INFRASTRUCTURE_TRIGGERS: Set[str] = {
        "medida", "medidas", "dimension", "dimensiones", "metro", "metros",
        "tamano", "tamaño", "ancho", "largo", "grosor", "espesor", "color",
        "colores", "superficie", "colchoneta", "colchonetas", "safety area",
        "distancia", "distancias"
    }

    # Infrastructure headings and article markers in passages
    INFRASTRUCTURE_MARKERS: Set[str] = {
        "field of play", "competition area", "facilities", "tatami specifications",
        "article 8", "appendix b", "b1.8", "area de competicion", "area de seguridad"
    }

    @classmethod
    def classify_query_intent(cls, query: str) -> Dict[str, any]:
        """
        Classifies query intent into evaluation intent vs pure infrastructure.
        """
        clean_q = query.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        tokens = set(re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", clean_q))

        has_eval_triggers = bool(tokens & cls.EVALUATION_TRIGGERS)
        has_pure_infra_triggers = bool(tokens & cls.PURE_INFRASTRUCTURE_TRIGGERS)

        # Inhibitor logic: if the query is asking about measurements, sizes, dimensions of tatami,
        # set is_eval to False so infrastructure passages are NOT dampened.
        if has_pure_infra_triggers and not ("puntuacion" in tokens or "sancion" in tokens or "waza-ari" in tokens or "wazaari" in tokens or "ippon" in tokens or "shido" in tokens):
            is_eval = False
            is_pure_infra = True
        else:
            is_eval = has_eval_triggers
            is_pure_infra = False

        # Specific domain detection
        target_domains = set()
        if any(t in tokens for t in ["waza-ari", "wazaari", "ippon", "puntuacion", "costado", "perpendicular"]):
            target_domains.add("SCORES")
        if any(t in tokens for t in ["shido", "falta", "sancion", "castigo"]):
            target_domains.add("SHIDO_PENALTIES")
        if any(t in tokens for t in ["hansoku-make", "hansokumake", "descalificacion", "diving"]):
            target_domains.add("HANSOKU_MAKE")
        if any(t in tokens for t in ["osaekomi", "inmovilizacion", "inmoviliza", "toketa"]):
            target_domains.add("HOLDINGS_NEWAZA")

        return {
            "is_eval": is_eval,
            "is_pure_infra": is_pure_infra,
            "target_domains": target_domains
        }

    @classmethod
    def is_infrastructure_passage(cls, passage: dict) -> bool:
        """
        Determines whether a passage belongs to facilities, competition area, or tatami specifications.
        """
        heading_path = [str(h).lower() for h in passage.get("heading_path", [])]
        heading_str = " ".join(heading_path)
        art_id = str(passage.get("article_id", "")).lower()
        page = passage.get("pdf_page_index", 0)

        # Appendix B and Section 8 (Field of Play & Tatami)
        if any(m in heading_str for m in cls.INFRASTRUCTURE_MARKERS):
            return True
        if art_id in ("8", "8.5", "8.6", "8.7", "8.8", "8.9", "b1.8"):
            return True
        if 94 <= page <= 98 or 111 <= page <= 113:
            return True

        return False

    @classmethod
    def is_intent_matching_passage(cls, passage: dict, target_domains: Set[str]) -> bool:
        """
        Checks if the passage directly answers the detected domain intent.
        """
        if not target_domains:
            return False

        art_id = str(passage.get("article_id", "")).lower()
        heading_str = " ".join([str(h).lower() for h in passage.get("heading_path", [])])
        page = passage.get("pdf_page_index", 0)

        if "SCORES" in target_domains:
            if art_id in ("14", "15") or "article 15" in heading_str or "article 14" in heading_str:
                return True
            if 166 <= page <= 172:
                return True

        if "SHIDO_PENALTIES" in target_domains:
            if "18.1" in art_id or "shido" in heading_str:
                return True
            if 175 <= page <= 189:
                return True

        if "HANSOKU_MAKE" in target_domains:
            if "18.2" in art_id or "hansoku" in heading_str:
                return True
            if 190 <= page <= 195:
                return True

        if "HOLDINGS_NEWAZA" in target_domains:
            if art_id in ("16", "17") or "osaekomi" in heading_str:
                return True
            if 172 <= page <= 175:
                return True

        return False

    @classmethod
    def rerank_scores(cls, query: str, rrf_scores: Dict[str, float], passages_by_id: Dict[str, dict]) -> Dict[str, float]:
        """
        Applies calibrated post-fusion semantic re-ranking.
        S_final = S_hyb * [1 - lambda_infra * I_infra * I_eval] * [1 + gamma_match * I_intent_match]
        """
        intent = cls.classify_query_intent(query)
        is_eval = intent["is_eval"]
        target_domains = intent["target_domains"]

        reranked_scores = dict(rrf_scores)

        for pid, score in rrf_scores.items():
            p = passages_by_id.get(pid)
            if not p:
                continue

            multiplier = 1.0

            # 1. Infrastructure dampening under evaluation query
            if is_eval and cls.is_infrastructure_passage(p):
                multiplier *= (1.0 - cls.LAMBDA_INFRA)

            # 2. Domain intent boost
            if cls.is_intent_matching_passage(p, target_domains):
                multiplier *= (1.0 + cls.GAMMA_MATCH)

            reranked_scores[pid] = score * multiplier

        return reranked_scores

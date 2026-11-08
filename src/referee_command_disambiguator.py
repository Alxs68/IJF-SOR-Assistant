"""
Referee Command Disambiguator Module for IJF SOR Assistant (RRE 3.0 Architecture).
Provides strict word-boundary regex detection and normative routing for official IJF
referee voice commands (Mate/Matte, Hajime, Sore-made, Sono-mama).
Differentiates verbal referee commands from descriptive, procedural, or textile occurrences.
"""

from typing import Dict, List, Set, Tuple, Optional
import re


class RefereeCommandDisambiguator:
    """
    Disambiguates official IJF referee commands from general sports or material terms.
    Enforces word-boundary patterns to prevent false positives with English words
    (e.g. 'mate' vs 'materials', 'maker label', 'estimate').
    """

    # Official referee commands recognized by IJF SOR 2026 (Articles 10, 11, 13)
    COMMAND_PATTERNS = {
        "MATE": {
            "regex": re.compile(r"\b(mate|matte)\b", re.IGNORECASE),
            "canonical_term": "Matte",
            "primary_articles": ["Article 11", "Article 10.1"],
            "primary_pages": [160, 161, 162, 163, 158]
        },
        "HAJIME": {
            "regex": re.compile(r"\b(hajime)\b", re.IGNORECASE),
            "canonical_term": "Hajime",
            "primary_articles": ["Article 10.1", "Article 11"],
            "primary_pages": [158, 160]
        },
        "SORE_MADE": {
            "regex": re.compile(r"\b(sore[- ]?made|soremade)\b", re.IGNORECASE),
            "canonical_term": "Sore-made",
            "primary_articles": ["Article 10.3", "Article 13"],
            "primary_pages": [159, 164, 165]
        },
        "SONO_MAMA": {
            "regex": re.compile(r"\b(sono[- ]?mama|sonomama)\b", re.IGNORECASE),
            "canonical_term": "Sono-mama",
            "primary_articles": ["Article 10.2", "Article 11"],
            "primary_pages": [159, 162]
        }
    }

    # Context indicators for verbal referee action intent
    VERBAL_ACTION_TRIGGERS: Set[str] = {
        "marca", "marcar", "dice", "decir", "voz", "grita", "gritar", "indica", "indicar",
        "detiene", "detener", "detencion", "parar", "para", "reanuda", "reanudar", "ordena",
        "orden", "ordenar", "arbitro", "referee", "shushin", "cuando", "situacion", "situaciones",
        "call", "calls", "stop", "resume", "signal", "gesto", "gestos"
    }

    # Context indicators for material, equipment, textile intent
    MATERIAL_EQUIPMENT_TRIGGERS: Set[str] = {
        "judogi", "traje", "uniforme", "kimono", "tela", "material", "materiales",
        "fabricante", "maker", "label", "etiqueta", "parche", "dorsal", "cinturon",
        "algodon", "poliester", "sokuteiki", "costura", "costuras"
    }

    @classmethod
    def analyze_query(cls, query: str) -> Dict[str, any]:
        """
        Analyzes a query to detect referee commands and their operational context.
        Returns:
            - detected_commands: list of command keys (e.g. ['MATE'])
            - intent_type: 'REFEREE_COMMAND_VERBAL', 'MATERIAL_EQUIPMENT', 'AMBIGUOUS_MIXED', or 'NONE'
            - boost_articles: list of article strings to prioritize
            - damp_appendix_c: boolean indicating whether Appendix C (equipment) should be dampened
        """
        clean_q = query.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        
        detected_commands = []
        for cmd_key, data in cls.COMMAND_PATTERNS.items():
            if data["regex"].search(clean_q):
                detected_commands.append(cmd_key)

        if not detected_commands:
            return {
                "detected_commands": [],
                "intent_type": "NONE",
                "boost_articles": [],
                "damp_appendix_c": False
            }

        # Analyze context
        tokens = set(re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", clean_q))
        has_verbal_intent = bool(tokens & cls.VERBAL_ACTION_TRIGGERS)
        has_material_intent = bool(tokens & cls.MATERIAL_EQUIPMENT_TRIGGERS)

        boost_articles = []
        for cmd in detected_commands:
            boost_articles.extend(cls.COMMAND_PATTERNS[cmd]["primary_articles"])

        if has_verbal_intent and not has_material_intent:
            intent_type = "REFEREE_COMMAND_VERBAL"
            damp_appendix_c = True
        elif has_material_intent and not has_verbal_intent:
            intent_type = "MATERIAL_EQUIPMENT"
            damp_appendix_c = False
            # When material is explicitly targeted, don't overboost Article 11 over equipment
            boost_articles = ["Appendix C", "Article C1.3"]
        elif has_verbal_intent and has_material_intent:
            intent_type = "AMBIGUOUS_MIXED"
            # Both rules apply (e.g. judogi adjustment leads to Matte under Art. 11/18.1.3)
            damp_appendix_c = False
            boost_articles.extend(["Article 18.1.3", "Article C1.3"])
        else:
            # Default for bare command like "mate" or "cuando se marca mate"
            intent_type = "REFEREE_COMMAND_VERBAL"
            damp_appendix_c = True

        return {
            "detected_commands": detected_commands,
            "intent_type": intent_type,
            "boost_articles": list(dict.fromkeys(boost_articles)),
            "damp_appendix_c": damp_appendix_c
        }

    @classmethod
    def apply_disambiguation(cls, rrf_scores: Dict[str, float], passages_by_id: Dict[str, dict], analysis: Dict[str, any]) -> Dict[str, float]:
        """
        Applies disambiguation re-weighting on RRF scores in-place or returning a modified dict.
        """
        if analysis["intent_type"] == "NONE":
            return rrf_scores

        boost_articles = [a.lower() for a in analysis.get("boost_articles", [])]
        damp_c = analysis.get("damp_appendix_c", False)

        for pid, score in list(rrf_scores.items()):
            p = passages_by_id.get(pid)
            if not p:
                continue

            art_id = str(p.get("article_id", "")).lower()
            heading = " ".join([str(h).lower() for h in p.get("heading_path", [])])
            page = p.get("pdf_page_index", 0)

            # Damp Appendix C if verbal referee intent was clearly diagnosed
            if damp_c and ("appendix c" in heading or "c1." in art_id or (114 <= page <= 133) or (198 <= page <= 212)):
                rrf_scores[pid] = score * 0.25

            # Boost target referee articles
            if "MATE" in analysis["detected_commands"] and analysis["intent_type"] in ("REFEREE_COMMAND_VERBAL", "AMBIGUOUS_MIXED"):
                if 160 <= page <= 163 or "article 11" in heading or art_id == "11":
                    rrf_scores[pid] = score + 0.15
            elif any(ba in heading or ba == art_id for ba in boost_articles):
                rrf_scores[pid] = score + 0.12

        return rrf_scores

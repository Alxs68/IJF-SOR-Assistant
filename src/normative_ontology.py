"""
Normative Ontology Module for IJF SOR Assistant (RRE 3.0 Architecture).
Provides structured domain taxonomy across 15 official IJF families,
cross-lingual lemma mapping (Spanish -> English), and dynamic procedural term dampening.
"""

from typing import Dict, List, Set, Tuple
import re

class NormativeDomain:
    ETHICS_AND_CONDUCT = "ETHICS_AND_CONDUCT"
    SCORES = "SCORES"
    HOLDINGS_NEWAZA = "HOLDINGS_NEWAZA"
    CHOKES_JOINTLOCKS = "CHOKES_JOINTLOCKS"
    HEAD_AND_SPINE = "HEAD_AND_SPINE"
    SHIDO_PENALTIES = "SHIDO_PENALTIES"
    HANSOKU_MAKE = "HANSOKU_MAKE"
    CADET_RESTRICTIONS = "CADET_RESTRICTIONS"
    WEIGH_IN = "WEIGH_IN"
    JUDOGI_EQUIPMENT = "JUDOGI_EQUIPMENT"
    TATAMI_CONTEST_AREA = "TATAMI_CONTEST_AREA"
    REFEREE_PROTOCOL = "REFEREE_PROTOCOL"
    MEDICAL_AND_INJURY = "MEDICAL_AND_INJURY"
    DRAW_AND_CONTEST_SYSTEM = "DRAW_AND_CONTEST_SYSTEM"
    OFFICIALS_AND_COMMISSIONS = "OFFICIALS_AND_COMMISSIONS"


class NormativeOntology:
    """
    Structured domain knowledge catalog for the International Judo Federation (IJF)
    Sport and Organisation Rules (SOR 2026-08).
    Maps multi-lingual query concepts into canonical normative lemmas and priority articles.
    """

    # 1. Official Canonical Lemmas by Family
    FAMILY_LEMMAS: Dict[str, Dict[str, any]] = {
        NormativeDomain.ETHICS_AND_CONDUCT: {
            "canonical_lemmas_en": [
                "against the spirit of judo", "spirit of judo", "behaviour", "misconduct",
                "insult", "insulting", "attack", "attacking", "violence", "aggression",
                "unsportsmanlike", "offensive", "disregard instructions", "disciplinary"
            ],
            "spanish_triggers": {
                "ofende": "insult insulting",
                "ofender": "insult insulting",
                "ofensa": "insult insulting",
                "ofensas": "insult insulting",
                "agrede": "attack attacking aggression",
                "agredir": "attack attacking aggression",
                "agresion": "attack aggression violence",
                "agresiones": "attack aggression violence",
                "insulto": "insult insulting derogatory",
                "insultos": "insult insulting derogatory",
                "insulta": "insult insulting",
                "insultar": "insult insulting",
                "violencia": "violence violent",
                "antideportiva": "unsportsmanlike",
                "antideportivo": "unsportsmanlike",
                "antijudo": "against the spirit of judo",
                "espiritu": "spirit of judo",
                "disciplina": "disciplinary committee discipline",
                "disciplinario": "disciplinary committee discipline",
                "disciplinaria": "disciplinary committee discipline",
                "desobedecer": "disregard instructions",
                "desobedece": "disregard instructions",
                "desacato": "disregard instructions refuse leave tatami"
            },
            "priority_articles": ["Article 18.2.2", "D1.1", "1.1.1", "1.2.1", "G1.3"]
        },

        NormativeDomain.HEAD_AND_SPINE: {
            "canonical_lemmas_en": [
                "head diving", "dive", "bridge", "cervical", "spine", "head defence",
                "head to throw", "head to defend", "landing on the body"
            ],
            "spanish_triggers": {
                "cabeza": "head",
                "buceo": "diving dive",
                "zambullida": "diving dive",
                "clavado": "diving dive",
                "puente": "bridge",
                "cervical": "cervical spine",
                "columna": "cervical spine"
            },
            "priority_articles": ["Article 18.2.1", "Article 14", "Article 18.1.4"]
        },

        NormativeDomain.CADET_RESTRICTIONS: {
            "canonical_lemmas_en": [
                "cadet", "cadets", "cadet events", "cadet competitions", "reverse seoi-nage"
            ],
            "spanish_triggers": {
                "cadete": "cadet",
                "cadetes": "cadet cadets",
                "inverso": "reverse",
                "inversa": "reverse"
            },
            "priority_articles": ["Article 18.1.4"]
        },

        NormativeDomain.SCORES: {
            "canonical_lemmas_en": [
                "ippon", "waza-ari", "yuko", "speed", "force", "on the back", "control", "rolling"
            ],
            "spanish_triggers": {
                "puntuacion": "score scoring",
                "puntuaciones": "scores scoring",
                "puntua": "score scoring",
                "wazaari": "waza-ari",
                "criterios": "criteria speed force",
                "velocidad": "speed",
                "fuerza": "force",
                "espalda": "back"
            },
            "priority_articles": ["Article 14", "Article 15"]
        },

        NormativeDomain.HOLDINGS_NEWAZA: {
            "canonical_lemmas_en": [
                "osaekomi", "toketa", "ne-waza", "holding", "outside contest area", "safety area"
            ],
            "spanish_triggers": {
                "inmovilizacion": "osaekomi holding",
                "inmovilizaciones": "osaekomi holding",
                "inmoviliza": "osaekomi holding",
                "suelo": "ne-waza",
                "escape": "toketa get away",
                "salida": "outside contest area"
            },
            "priority_articles": ["Article 16", "Article 11"]
        },

        NormativeDomain.CHOKES_JOINTLOCKS: {
            "canonical_lemmas_en": [
                "shime-waza", "kansetsu-waza", "choke", "joint lock", "arm lock", "strangle"
            ],
            "spanish_triggers": {
                "estrangulacion": "shime-waza choke",
                "estrangulaciones": "shime-waza choke",
                "luxacion": "kansetsu-waza joint lock arm lock",
                "luxaciones": "kansetsu-waza joint lock arm lock",
                "palanca": "kansetsu-waza arm lock"
            },
            "priority_articles": ["Article 17", "Article 18.2.2"]
        },

        NormativeDomain.SHIDO_PENALTIES: {
            "canonical_lemmas_en": [
                "shido", "non combativity", "false attack", "pull down", "wasting time",
                "negative position", "untidy judogi", "leave contest area"
            ],
            "spanish_triggers": {
                "falta": "shido penalty",
                "faltas": "shido penalties",
                "pasividad": "non combativity",
                "bloqueo": "negative position",
                "retraso": "wasting time"
            },
            "priority_articles": ["Article 18.1", "Article 18.1.1", "Article 18.1.2", "Article 18.1.3"]
        },

        NormativeDomain.HANSOKU_MAKE: {
            "canonical_lemmas_en": [
                "hansoku-make", "direct hansoku-make", "indirect hansoku-make", "disqualification",
                "can continue", "cannot continue", "dangerous techniques", "double hansoku-make"
            ],
            "spanish_triggers": {
                "descalificacion": "disqualification hansoku-make",
                "descalificado": "disqualification hansoku-make",
                "descalificar": "disqualification hansoku-make",
                "acumulacion": "accumulation of shido penalties"
            },
            "priority_articles": ["Article 18.2", "Article 18.2.1", "Article 18.2.2", "Article 18.3"]
        },

        NormativeDomain.WEIGH_IN: {
            "canonical_lemmas_en": [
                "weigh-in", "official weigh-in", "random weigh-in", "scales", "weight tolerance", "weight"
            ],
            "spanish_triggers": {
                "pesaje": "weigh-in",
                "peso": "weight weigh-in",
                "balanza": "scales",
                "bascula": "scales",
                "tolerancia": "tolerance"
            },
            "priority_articles": ["6.2", "6.3", "Article 1.7"]
        },

        NormativeDomain.JUDOGI_EQUIPMENT: {
            "canonical_lemmas_en": [
                "judogi", "sokuteiki"
            ],
            "spanish_triggers": {
                "kimono": "judogi",
                "chaqueta": "jacket",
                "pantalon": "trousers",
                "cinturon": "belt",
                "parche": "patch",
                "parches": "patches",
                "color": "colour blue white",
                "colores": "colour blue white",
                "dorsal": "backnumber"
            },
            "priority_articles": ["C1.1", "C1.9", "Article 3"]
        },

        NormativeDomain.TATAMI_CONTEST_AREA: {
            "canonical_lemmas_en": [
                "tatami", "contest area", "safety area", "dimensions", "meters", "metres"
            ],
            "spanish_triggers": {
                "medida": "dimensions metres meters",
                "medidas": "dimensions metres meters",
                "tamano": "dimensions metres meters",
                "dimension": "dimensions metres meters",
                "dimensiones": "dimensions metres meters",
                "area": "contest area safety area"
            },
            "priority_articles": ["8.5", "8.6", "8.7", "8.8", "8.9"]
        },

        NormativeDomain.REFEREE_PROTOCOL: {
            "canonical_lemmas_en": [
                "referee", "judges", "table jury", "commission", "care system", "signals", "gestures"
            ],
            "spanish_triggers": {
                "arbitro": "referee",
                "arbitros": "referees",
                "arbitraje": "refereeing referee",
                "juez": "judge judges",
                "jurado": "jury",
                "gesto": "gesture signal",
                "gestos": "gestures signals"
            },
            "priority_articles": ["Article 2", "Article 3", "Article 4", "7.1"]
        },

        NormativeDomain.MEDICAL_AND_INJURY: {
            "canonical_lemmas_en": [
                "doctor", "medical", "blood", "bleeding", "injury", "kiken-gachi", "concussion", "assistance", "treatment"
            ],
            "spanish_triggers": {
                "medico": "doctor medical",
                "medicos": "doctor doctors medical",
                "medica": "doctor medical treatment assistance",
                "medicas": "doctor medical treatment assistance",
                "intervencion": "medical treatment assistance occasions",
                "intervenciones": "medical treatment assistance occasions",
                "asistencia": "assistance medical treatment doctor",
                "atencion": "assistance medical treatment doctor",
                "doctor": "doctor medical",
                "sangre": "blood bleeding",
                "sangrado": "blood bleeding",
                "lesion": "injury",
                "lesiones": "injuries injury",
                "abandono": "kiken-gachi withdraw",
                "conmocion": "concussion"
            },
            "priority_articles": ["Article 20", "Article 20.1", "Article 20.2", "Article 20.3", "Article 20.3.1", "Article 20.3.2", "E1.5"]
        },

        NormativeDomain.DRAW_AND_CONTEST_SYSTEM: {
            "canonical_lemmas_en": [
                "draw", "repechage", "quarter-final", "mixed team", "teams", "direct knockout"
            ],
            "spanish_triggers": {
                "sorteo": "draw",
                "cuadro": "draw bracket",
                "repesca": "repechage",
                "eliminacion": "direct knockout",
                "equipos": "mixed teams"
            },
            "priority_articles": ["2.5", "2.7", "3.3"]
        },

        NormativeDomain.OFFICIALS_AND_COMMISSIONS: {
            "canonical_lemmas_en": [
                "education commission", "referee director", "supervisor", "executive committee"
            ],
            "spanish_triggers": {
                "comision": "commission committee",
                "educacion": "education commission",
                "director": "referee director",
                "supervisor": "referee supervisor"
            },
            "priority_articles": ["1.2.1", "1.2.2", "Article 21"]
        }
    }

    # Procedural generic words that frequently dominate BM25 ranking when specific verbs are present
    PROCEDURAL_DAMPEN_WORDS: Set[str] = {
        "athlete", "athletes", "competitor", "competitors", "competition", "competitions",
        "team", "teams", "event", "events", "rule", "rules", "system", "systems", "category", "categories"
    }

    @classmethod
    def expand_token_stream(cls, tokens: List[str]) -> Tuple[List[str], Set[str]]:
        """
        Expands raw token stream using normative family definitions.
        Returns:
            - augmented_tokens: original tokens + canonical domain lemmas in English
            - detected_domains: set of domain identifiers triggered by the query
        """
        augmented = list(tokens)
        detected_domains: Set[str] = set()
        existing_tokens = set(tokens)

        # Check each token against spanish triggers across all domains
        for t in tokens:
            t_clean = t.lower()
            for domain_name, data in cls.FAMILY_LEMMAS.items():
                triggers = data["spanish_triggers"]
                if t_clean in triggers:
                    detected_domains.add(domain_name)
                    syn_phrase = triggers[t_clean]
                    for w in syn_phrase.split():
                        if w not in existing_tokens:
                            augmented.append(w)
                            existing_tokens.add(w)

        # If domain detected, enrich with domain canonical lemmas to anchor dense and sparse channels
        for dom in detected_domains:
            lemmas = cls.FAMILY_LEMMAS[dom]["canonical_lemmas_en"]
            for lemma in lemmas:
                for w in lemma.split():
                    if w not in existing_tokens:
                        augmented.append(w)
                        existing_tokens.add(w)

        return augmented, detected_domains

    @classmethod
    def get_priority_articles(cls, detected_domains: Set[str]) -> List[str]:
        """Returns priority articles associated with the detected normative domains."""
        articles = []
        for dom in detected_domains:
            articles.extend(cls.FAMILY_LEMMAS.get(dom, {}).get("priority_articles", []))
        return list(dict.fromkeys(articles))

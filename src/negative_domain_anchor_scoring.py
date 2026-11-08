"""
Negative Domain Anchor Scoring Module (BK-01) for IJF SOR Assistant.
Part of Phase 4.2.1: Experimental Domain Disambiguation & Cross-Sport OOD Shield.

Provides calibrated detection of explicit non-judo sports and domain concepts
(e.g., basketball, tennis, swimming, football, athletics, combat striking) to prevent false normative
associations on shared generic vocabulary (points, time, distance, penalty, referee)
while strictly preserving judo technical terms (Ippon, Waza-ari, Shido, Mate, Tatami).
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from enum import Enum
import re
from pydantic import BaseModel, Field


class NegativeDomainCategory(str, Enum):
    BASKETBALL = "BASKETBALL"
    TENNIS = "TENNIS"
    SWIMMING = "SWIMMING"
    FOOTBALL = "FOOTBALL"
    ATHLETICS = "ATHLETICS"
    BOXING_STRIKING = "BOXING_STRIKING"
    MOTORSPORT = "MOTORSPORT"
    GENERAL_NON_SPORT = "GENERAL_NON_SPORT"
    UNREGULATED_JUDO = "UNREGULATED_JUDO"
    HISTORICAL_SUPERSEDED = "HISTORICAL_SUPERSEDED"
    FUTURE_CHANGES = "FUTURE_CHANGES"
    NONE = "NONE"


class NegativeDomainDecision(str, Enum):
    CONFIRMED_NEGATIVE_OOD = "CONFIRMED_NEGATIVE_OOD"   # High confidence non-judo sport
    SUSPECTED_NEGATIVE = "SUSPECTED_NEGATIVE"           # Moderate evidence of other sport
    NEUTRAL_INSUFFICIENT = "NEUTRAL_INSUFFICIENT"       # Ambiguous or no negative anchors
    CONFIRMED_JUDO = "CONFIRMED_JUDO"                   # Explicit judo technical presence (immunity)


class NegativeDomainResult(BaseModel):
    """
    Structured outcome of the Negative Domain Anchor Scoring evaluation.
    """
    detected_domains: List[str] = Field(default_factory=list, description="Categories of non-judo sports detected")
    matched_anchors: List[Dict[str, Any]] = Field(default_factory=list, description="Specific anchor matches found")
    negative_score: float = Field(0.0, ge=0.0, le=1.0, description="Normalized negative domain score (0.0 to 1.0)")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in non-judo classification")
    is_ood: bool = Field(False, description="True if negative evidence warrants OOD rejection")
    reason: str = Field("No negative domain anchors detected", description="Human-interpretable explanation")
    decision: NegativeDomainDecision = Field(NegativeDomainDecision.NEUTRAL_INSUFFICIENT, description="Final decision enum")
    has_judo_immunity: bool = Field(False, description="True if explicit judo terms prevent false OOD")
    version: str = Field("BK-01-v1.0.0", description="Algorithm version")


class NegativeDomainAnchorScorer:
    """
    Evaluates queries for explicit non-judo domain anchors using weighted multi-category patterns.
    Enforces conservative thresholds and explicit judo immunity to prevent false positives.
    """

    # Unambiguous technical terms exclusive to Judo that confer immunity against negative false alarms
    # Note: Koka is intentionally excluded as it was abolished in 2008 and is not valid in SOR 2026.
    JUDO_IMMUNITY_TERMS: Set[str] = {
        "judo", "judoka", "judoga", "judogi", "judogis", "ippon", "waza-ari", "wazaari", "yuko",
        "osaekomi", "toketa", "shime-waza", "kansetsu-waza", "shido", "hansoku-make", "hansokumake",
        "tori", "uke", "tatami", "tatamis", "seoi-nage", "kawazu-gake", "sore-made", "sono-mama",
        "kiken-gachi", "golden score", "sokuteiki", "backnumber", "shushin", "fukushin", "care system",
        "tachi-waza", "ne-waza", "ashi-waza", "te-waza", "koshi-waza", "kumikata", "judoist"
    }

    # Ambiguous terms that appear across sports and MUST NEVER trigger negative classification on their own
    AMBIGUOUS_SHARED_TERMS: Set[str] = {
        "mate", "tiempo", "tiempos", "puntos", "punto", "penalizacion", "penalizaciones",
        "falta", "faltas", "arbitro", "arbitros", "referee", "competicion", "torneo",
        "descalificacion", "regla", "reglas", "duracion", "categoria", "peso", "pesaje"
    }

    # Domain Anchor Catalog: Categorized patterns with assigned weights
    # weight 1.0 = Highly specific / unequivocal term
    # weight 0.6 = Moderate specificity (requires corroboration or supporting anchor)
    DOMAIN_ANCHORS: Dict[NegativeDomainCategory, List[Dict[str, Any]]] = {
        NegativeDomainCategory.BASKETBALL: [
            {"pattern": r"\b(?:baloncesto|basket|basquetbol|basquet)\b", "weight": 1.0, "desc": "basketball sport name"},
            {"pattern": r"\b(?:tiro\s+libre|tiros\s+libres|free\s+throw)\b", "weight": 1.0, "desc": "free throw"},
            {"pattern": r"\b(?:triple|triples|linea\s+de\s+tres)\b", "weight": 0.8, "desc": "three-pointer"},
            {"pattern": r"\b(?:driblar|dribla|driblando|drible|dribbling)\b", "weight": 1.0, "desc": "dribbling"},
            {"pattern": r"\b(?:canasta|canastas|tablero)\b", "weight": 0.7, "desc": "basket hoop"},
            {"pattern": r"\b(?:nba|acb|euroleague|fiba)\b", "weight": 1.0, "desc": "basketball league"},
            {"pattern": r"\b(?:pasos|dobles)\b", "weight": 0.5, "desc": "basketball violation"},
        ],
        NegativeDomainCategory.TENNIS: [
            {"pattern": r"\b(?:tenis|tennis)\b", "weight": 1.0, "desc": "tennis sport name"},
            {"pattern": r"\b(?:tie-break|tie\s+break|tiebreak|muerte\s+subita)\b", "weight": 1.0, "desc": "tie-break"},
            {"pattern": r"\b(?:saque\s+de\s+tenis|primer\s+servicio|segundo\s+servicio)\b", "weight": 1.0, "desc": "tennis serve"},
            {"pattern": r"\b(?:ace|aces)\b", "weight": 0.9, "desc": "tennis ace"},
            {"pattern": r"\b(?:deuce|ventaja\s+al\s+saque|match\s+point|break\s+point)\b", "weight": 1.0, "desc": "tennis score terms"},
            {"pattern": r"\b(?:raqueta|raquetas|fronton|wimbledon|roland\s+garros|us\s+open)\b", "weight": 1.0, "desc": "tennis gear/tournaments"},
            {"pattern": r"\b(?:drive|reves|slice|volea)\b", "weight": 0.6, "desc": "tennis shot"},
        ],
        NegativeDomainCategory.SWIMMING: [
            {"pattern": r"\b(?:natacion|nataci[oó]n|nadador|nadadora|swimming)\b", "weight": 1.0, "desc": "swimming sport name"},
            {"pattern": r"\b(?:patada\s+submarina|patada\s+de\s+mariposa|patada\s+de\s+delfin)\b", "weight": 1.0, "desc": "submerged kick"},
            {"pattern": r"\b(?:estilo\s+mariposa|estilo\s+espalda|estilo\s+braza|estilo\s+libre|crol)\b", "weight": 1.0, "desc": "swimming stroke"},
            {"pattern": r"\b(?:piscina\s+olimpica|piscina|alberca)\b", "weight": 0.8, "desc": "swimming pool"},
            {"pattern": r"\b(?:viraje|virajes|flip\s+turn)\b", "weight": 0.9, "desc": "swimming turn"},
            {"pattern": r"\b(?:bajo\s+el\s+agua|subacuatica|subacuatica)\b", "weight": 0.9, "desc": "underwater context"},
            {"pattern": r"\b(?:salida\s+anticipada)\b", "weight": 0.6, "desc": "false start swimming"},
        ],
        NegativeDomainCategory.FOOTBALL: [
            {"pattern": r"\b(?:futbol|f[uú]tbol|soccer|football)\b", "weight": 1.0, "desc": "football sport name"},
            {"pattern": r"\b(?:fuera\s+de\s+juego|offside)\b", "weight": 1.0, "desc": "offside rule"},
            {"pattern": r"\b(?:penalti|penal|penalty|tiro\s+penal)\b", "weight": 0.9, "desc": "penalty kick"},
            {"pattern": r"\b(?:corner|c[oó]rner|saque\s+de\s+esquina)\b", "weight": 1.0, "desc": "corner kick"},
            {"pattern": r"\b(?:tarjeta\s+roja|tarjeta\s+amarilla)\b", "weight": 0.8, "desc": "penalty cards"},
            {"pattern": r"\b(?:porteria|arquero|guardameta|portero)\b", "weight": 0.8, "desc": "goalkeeper"},
            {"pattern": r"\b(?:fifa|uefa|champions\s+league|copa\s+del\s+mundo)\b", "weight": 1.0, "desc": "football orgs"},
        ],
        NegativeDomainCategory.ATHLETICS: [
            {"pattern": r"\b(?:atletismo|athletics|track\s+and\s+field)\b", "weight": 1.0, "desc": "athletics sport name"},
            {"pattern": r"\b(?:salto\s+con\s+pertiga|garrocha|pole\s+vault)\b", "weight": 1.0, "desc": "pole vault"},
            {"pattern": r"\b(?:lanzamiento\s+de\s+disco|lanzamiento\s+de\s+jabalina|lanzamiento\s+de\s+martillo)\b", "weight": 1.0, "desc": "throwing events"},
            {"pattern": r"\b(?:salto\s+triple|triple\s+salto|salto\s+de\s+longitud)\b", "weight": 1.0, "desc": "jumping events"},
            {"pattern": r"\b(?:marat[oó]n|100\s+metros\s+planos|400\s+metros\s+vallas)\b", "weight": 1.0, "desc": "track events"},
            {"pattern": r"\b(?:relevos|testigo|carril\s+de\s+carrera)\b", "weight": 0.7, "desc": "relay context"},
        ],
        NegativeDomainCategory.BOXING_STRIKING: [
            {"pattern": r"\b(?:boxeo|boxing|boxeador|kickboxing|muay\s+thai)\b", "weight": 1.0, "desc": "striking combat sport"},
            {"pattern": r"\b(?:nocaut|knockout|k\.?o\.?|tko)\b", "weight": 1.0, "desc": "knockout"},
            {"pattern": r"\b(?:round|rounds|asalto|asaltos)\b", "weight": 0.7, "desc": "boxing rounds"},
            {"pattern": r"\b(?:guante\s+de\s+box|ring\s+de\s+boxeo|cuadrilatero)\b", "weight": 1.0, "desc": "boxing ring/gloves"},
            {"pattern": r"\b(?:jab|croche|uppercut|gancho\s+al\s+higado)\b", "weight": 1.0, "desc": "striking punches"},
        ],
        NegativeDomainCategory.MOTORSPORT: [
            {"pattern": r"\b(?:formula\s+1|f1|f[oó]rmula\s+1|motogp|rally|nascar)\b", "weight": 1.0, "desc": "motorsport category"},
            {"pattern": r"\b(?:pit\s+lane|boxes|parada\s+en\s+boxes|pit\s+stop)\b", "weight": 1.0, "desc": "pit lane / box stop"},
            {"pattern": r"\b(?:monoplaza|safety\s+car|coche\s+de\s+seguridad)\b", "weight": 0.9, "desc": "motorsport vehicle/safety car"},
        ],
        NegativeDomainCategory.GENERAL_NON_SPORT: [
            {"pattern": r"\b(?:outofmemoryerror|java|python|javascript|c\+\+|sql|software|programaci[oó]n|c[oó]digo\s+fuente)\b", "weight": 1.0, "desc": "software / programming"},
            {"pattern": r"\b(?:tasa\s+de\s+inter[eé]s|inter[eé]s\s+compuesto|inversiones\s+bancarias|hipoteca|acciones\s+en\s+bolsa)\b", "weight": 1.0, "desc": "finance / banking"},
            {"pattern": r"\b(?:ingredientes\s+para\s+preparar|receta|paella|cocinar|gastronom[ií]a)\b", "weight": 1.0, "desc": "cooking / culinary"},
            {"pattern": r"\b(?:distancia\s+media\s+entre\s+la\s+tierra\s+y\s+la\s+luna|astronom[ií]a|planeta|orbita|[oó]rbita|a[nñ]os\s+luz)\b", "weight": 1.0, "desc": "astronomy / space"},
        ],
        NegativeDomainCategory.UNREGULATED_JUDO: [
            {"pattern": r"\b(?:salario|sueldo|remuneraci[oó]n|n[oó]mina)\b", "weight": 1.0, "desc": "athlete salary/income"},
            {"pattern": r"\b(?:cuota\s+mensual|precio\s+de\s+afiliaci[oó]n|costo\s+de\s+inscripci[oó]n|cu[aá]nto\s+cuesta\s+la\s+cuota)\b", "weight": 1.0, "desc": "club membership fee"},
            {"pattern": r"\b(?:fund[oó]\s+jigoro\s+kano|a[nñ]o\s+en\s+que\s+se\s+fund[oó]|fundaci[oó]n\s+del\s+kodokan|en\s+qu[eé]\s+a[nñ]o\s+fund[oó]|1882)\b", "weight": 1.0, "desc": "kodokan foundation 1882 historical origin"},
            {"pattern": r"\b(?:guarder[ií]a|infantiles\s+de\s+guarder[ií]a|colegio\s+primario|recreativo\s+escolar)\b", "weight": 0.9, "desc": "preschool recreational judo"},
            {"pattern": r"\b(?:barcelona\s+1992|atlanta\s+1996|sidney\s+2000|atenas\s+2004|medallero\s+hist[oó]rico|medalla\s+de\s+oro\s+en\s+la\s+categor[ií]a\s+de\s+60\s+kg\s+en\s+los\s+juegos)\b", "weight": 1.0, "desc": "historical olympic medalists database"},
        ],
        NegativeDomainCategory.HISTORICAL_SUPERSEDED: [
            {"pattern": r"\b(?:koka)\b", "weight": 1.0, "desc": "repealed koka score abolished in 2008"},
            {"pattern": r"\b(?:chui|keikoku)\b", "weight": 1.0, "desc": "repealed traditional penalties chui/keikoku"},
            {"pattern": r"\b(?:2012|2010|2008|2004)\b", "weight": 1.0, "desc": "historical superseded regulation edition years"},
            {"pattern": r"\b(?:reglamento\s+(?:de\s+)?2012|reglas\s+(?:de\s+)?2012|reglamento\s+(?:de\s+)?2008|reglamento\s+(?:de\s+)?2010)\b", "weight": 1.0, "desc": "historical superseded regulation years"},
        ],
        NegativeDomainCategory.FUTURE_CHANGES: [
            {"pattern": r"\b(?:2030|2032|2036)\b", "weight": 1.0, "desc": "unincorporated future regulation years"},
            {"pattern": r"\b(?:ciclo\s+ol[ií]mpico\s+la28|los\s+[aá]ngeles\s+2028|la28)\b", "weight": 1.0, "desc": "future LA28 cycle not in SOR 2026"},
        ]
    }

    # Conservatively tuned threshold:
    # A single unequivocal term (weight 1.0) achieves score 0.75 -> triggers CONFIRMED_NEGATIVE_OOD
    # An isolated moderate term (weight 0.6) yields score 0.45 -> triggers SUSPECTED_NEGATIVE without auto-abstain
    OOD_DECISION_THRESHOLD: float = 0.65

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Normalizes query text preserving essential punctuation and lowercasing."""
        t = text.lower()
        t = t.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        return t

    @classmethod
    def check_judo_immunity(cls, query: str) -> Tuple[bool, List[str]]:
        """
        Determines whether the query contains explicit, unambiguous judo technical terms.
        If true, the query receives immunity against false positive negative domain penalties.
        """
        clean_q = cls.clean_text(query)
        found_immunity_terms = []
        for term in cls.JUDO_IMMUNITY_TERMS:
            # Word boundary search
            pattern = r"\b" + re.escape(term) + r"\b"
            if re.search(pattern, clean_q):
                found_immunity_terms.append(term)
        return len(found_immunity_terms) > 0, found_immunity_terms

    @classmethod
    def score_negative_domain(cls, query: str) -> NegativeDomainResult:
        """
        Main entry point for BK-01 evaluation.
        Analyzes query against domain anchors, checks for judo immunity, computes
        normalized negative score, and returns an explainable NegativeDomainResult.
        """
        if not query or not query.strip():
            return NegativeDomainResult(
                reason="Empty query",
                decision=NegativeDomainDecision.NEUTRAL_INSUFFICIENT
            )

        clean_q = cls.clean_text(query)

        # 1. Match anchors across negative categories
        detected_categories: Dict[NegativeDomainCategory, List[Dict[str, Any]]] = {}
        all_matches: List[Dict[str, Any]] = []

        for category, anchor_list in cls.DOMAIN_ANCHORS.items():
            cat_matches = []
            for anchor in anchor_list:
                pattern = anchor["pattern"]
                match = re.search(pattern, clean_q, re.IGNORECASE)
                if match:
                    match_info = {
                        "category": category.value,
                        "matched_text": match.group(0),
                        "weight": anchor["weight"],
                        "description": anchor["desc"]
                    }
                    cat_matches.append(match_info)
                    all_matches.append(match_info)
            if cat_matches:
                detected_categories[category] = cat_matches

        # 2. Check for Judo Immunity against traditional cross-sport false alarms
        has_immunity, immunity_terms = cls.check_judo_immunity(query)

        # Categories that cannot be immunized by generic judo mentions
        # (e.g., asking about salary of a judoka or koka score in judo cannot bypass OOD)
        non_immunizable = {
            NegativeDomainCategory.GENERAL_NON_SPORT,
            NegativeDomainCategory.MOTORSPORT,
            NegativeDomainCategory.UNREGULATED_JUDO,
            NegativeDomainCategory.HISTORICAL_SUPERSEDED,
            NegativeDomainCategory.FUTURE_CHANGES
        }
        has_non_immunizable_match = any(c in non_immunizable for c in detected_categories)

        if has_immunity and not has_non_immunizable_match:
            return NegativeDomainResult(
                negative_score=0.0,
                confidence=1.0,
                is_ood=False,
                reason=f"Judo technical immunity active: detected terms {immunity_terms}",
                decision=NegativeDomainDecision.CONFIRMED_JUDO,
                has_judo_immunity=True
            )

        # If no negative anchors matched
        if not all_matches:
            if has_immunity:
                return NegativeDomainResult(
                    negative_score=0.0,
                    confidence=1.0,
                    is_ood=False,
                    reason=f"Judo technical immunity active: detected terms {immunity_terms}",
                    decision=NegativeDomainDecision.CONFIRMED_JUDO,
                    has_judo_immunity=True
                )
            return NegativeDomainResult(
                negative_score=0.0,
                confidence=0.0,
                is_ood=False,
                reason="No negative sports domain anchors detected in query",
                decision=NegativeDomainDecision.NEUTRAL_INSUFFICIENT
            )

        # 3. Calculate category-level evidence
        # Category score = 1.0 - product(1.0 - 0.75 * w_i)
        # This rewards multiple corroborating matches within the same sport
        best_cat_score = 0.0
        primary_category = NegativeDomainCategory.NONE
        primary_matches = []

        for cat, matches in detected_categories.items():
            prod_unmatched = 1.0
            for m in matches:
                # Diminishing marginal penalty factor: 0.75 scaling per weight
                effective_weight = min(1.0, m["weight"])
                prod_unmatched *= (1.0 - 0.75 * effective_weight)
            cat_score = 1.0 - prod_unmatched
            if cat_score > best_cat_score:
                best_cat_score = cat_score
                primary_category = cat
                primary_matches = matches

        normalized_score = round(min(1.0, best_cat_score), 4)
        cat_names = [c.value for c in detected_categories.keys()]

        # 4. Formulate Decision
        if normalized_score >= cls.OOD_DECISION_THRESHOLD:
            decision = NegativeDomainDecision.CONFIRMED_NEGATIVE_OOD
            is_ood = True
            reason = (
                f"Definitive non-judo sports domain detected ({primary_category.value}) "
                f"with score {normalized_score} >= {cls.OOD_DECISION_THRESHOLD}. "
                f"Anchors: {[m['matched_text'] for m in primary_matches]}"
            )
        else:
            decision = NegativeDomainDecision.SUSPECTED_NEGATIVE
            is_ood = False  # Conservative: does NOT auto-abstain if evidence is marginal
            reason = (
                f"Suspected non-judo terminology in {primary_category.value} but evidence score "
                f"({normalized_score}) is below decisive threshold {cls.OOD_DECISION_THRESHOLD}."
            )

        return NegativeDomainResult(
            detected_domains=cat_names,
            matched_anchors=all_matches,
            negative_score=normalized_score,
            confidence=normalized_score,
            is_ood=is_ood,
            reason=reason,
            decision=decision,
            has_judo_immunity=False
        )

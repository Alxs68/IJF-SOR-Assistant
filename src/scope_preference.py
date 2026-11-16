"""R3 - Preferencia por ambito en la recuperacion (Fase 11, candidato integrado en modo EXPERIMENTAL).

Desactivado por defecto. Se activa con la variable de entorno RRE_ENABLE_SCOPE_PREFERENCE=1
(o enable_scope_preference=True en ReasoningRetrievalEngine). Con el flag apagado el RRE se comporta
exactamente como antes.

Funcionamiento (generico, derivado de datos; sin palabras clave, preguntas, articulos ni pasajes):
  * Las "partes" del SOR se toman de las unidades COVER de data/derived/article_units_v1.
  * Un termino del TITULO de una parte P es indicador de P si share = apariciones en P / totales >= 0.5,
    lift = (apariciones en P / unidades de P) / (totales / unidades) >= 4 y aparece >= 3 veces en P.
  * Si la consulta (original o proyectada) contiene indicadores de una parte, los candidatos de esa
    parte reciben un factor (1 + beta) sobre la puntuacion por rango 1/(60 + rango); sin indicadores
    el orden no cambia. Se aplica sobre un conjunto de hasta 25 candidatos y despues se recorta a top_k.
Copia fiel de ScopeModel / scope_rerank (src/experimental/retrieval_variants.py) evaluada en la Fase 11
(docs/audits/FASE_11_RECUPERACION_EXPERIMENTAL.md, R3); tests de equivalencia en
tests/test_scope_preference.py.
"""
import json
import os
import re
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNITS_PATH = os.path.join(ROOT, "data", "derived", "article_units_v1", "units.jsonl")
CONTENT = {"ARTICLE", "CONTINUATION"}
NON_RULE_PARTS = {"GLOSSARY", "DOCUMENT CONTROL"}
K_RANK = 60
POOL = 25
DEFAULT_BETA = 0.2

# palabras funcionales (gramatica, no dominio) ES/EN/FR/PT - identicas a las del detector de ambiguedad experimental de la Fase 10
STOP = set("""
a al algo alguna alguno ante como con cual cuales cuando cuanto cuantos cuantas de del donde e el ella ellas ellos en entre
es esa ese eso esta este esto ha hay la las le les lo los mas me mi muy no o para pero por que quien se sea segun ser si
sin sobre son su sus tiene tienen todo un una uno unos y ya debe deben puede pueden hace hacer qué cuál cuánto cuántos
cuántas cuándo dónde quién cómo está están
about after all an and any are as at be been before by can could did do does each for from had has have how if in into
is it its may might must of on or other shall should so than that the their them then there these they this those to
under up was we were what when where which while who whom why will with would you your
au aux avec ce ces dans de des du elle en est et il ils la le les leur lors ne ou par pas pour qu que qui sa se ses son
sont sur un une
ao aos com como da das de do dos e em ela ele na nas no nos o os ou para pela pelo por que se sua um uma
""".split())


def stems(text):
    out = []
    for w in re.findall(r"[a-záéíóúñüàâçèêëîïôûœ]+|\d+", (text or "").lower()):
        if w in STOP or (len(w) < 3 and not w.isdigit()):
            continue
        out.append(w[:5])
    return out


def flag_enabled(value=None):
    if value is not None:
        return bool(value)
    return os.environ.get("RRE_ENABLE_SCOPE_PREFERENCE", "").strip().lower() in {"1", "true", "yes", "on"}


def beta_from_env():
    try:
        return float(os.environ.get("RRE_SCOPE_BETA", DEFAULT_BETA))
    except ValueError:
        return DEFAULT_BETA


class ScopePreference:
    def __init__(self, units_path=UNITS_PATH, beta=None, min_share=0.5, min_lift=4.0, min_count=3):
        self.beta = beta_from_env() if beta is None else beta
        self.available = os.path.exists(units_path)
        self.indicator, self.page_part = {}, {}
        if not self.available:
            return
        with open(units_path, encoding="utf-8") as fh:
            units = [json.loads(l) for l in fh if l.strip()]
        docs, part, titles, heading_of = [], None, set(), {}
        for u in sorted(units, key=lambda u: (u["page"], u.get("char_start") or 0)):
            if u.get("unit_level") != 1:
                continue
            if u["unit_type"] == "COVER":
                part = u.get("article_label") or u.get("heading")
                titles.add(part)
            self.page_part.setdefault(u["page"], part)
            if u["unit_type"] not in CONTENT or not u.get("article_label") or part in NON_RULE_PARTS:
                continue
            lab = re.sub(r"\s*\.\s*", ".", u["article_label"]).strip()
            head = re.sub(r"\s+", " ", u.get("heading") or "").strip() or heading_of.get(lab, lab)
            heading_of.setdefault(lab, head)
            docs.append((part, f"{head}\n{u['derived_text']}"))
        self._pages = sorted(self.page_part)
        occ = defaultdict(Counter)
        size = Counter(p for p, _ in docs)
        for p, text in docs:
            for t in set(stems(text)):
                occ[t][p] += 1
        n = len(docs)
        for p in titles:
            if p in NON_RULE_PARTS or not p or not size[p]:
                continue
            for t in set(stems(p)):
                tot, inp = sum(occ[t].values()), occ[t][p]
                if not tot or inp < min_count:
                    continue
                if inp / tot >= min_share and (inp / size[p]) / (tot / n) >= min_lift:
                    self.indicator.setdefault(t, set()).add(p)

    def part_of_page(self, page):
        best = None
        for pg in self._pages:
            if page is not None and pg <= page:
                best = self.page_part[pg]
        return best

    def query_parts(self, *texts):
        parts = set()
        for tx in texts:
            for t in stems(tx or ""):
                parts |= self.indicator.get(t, set())
        return parts

    def rerank(self, ranking, parts, page_of, beta=None):
        """Reordena una lista de passage_id; sin partes devuelve el mismo orden."""
        if not parts or not self.available:
            return list(ranking)
        b = self.beta if beta is None else beta
        sc = {p: (1.0 / (K_RANK + i)) * ((1 + b) if self.part_of_page(page_of(p)) in parts else 1.0)
              for i, p in enumerate(ranking, 1)}
        return sorted(ranking, key=lambda p: -sc[p])

"""Fase 10.3 - Detector EXPERIMENTAL de ambiguedad / consulta incompleta (modo SHADOW).

Generico: no contiene reglas, palabras clave ni casos para preguntas concretas. Usa solo
estadisticas del corpus derivado (article_units_v1, solo lectura):
  1. INCOMPLETA  - la informacion de la consulta (suma de idf de sus terminos presentes en
                   el corpus) es menor que min_info: no hay referente identificable.
  2. AMBIGUA     - varias unidades con encabezados DISTINTOS puntuan de forma comparable
                   (score >= ratio * mejor) y la consulta no nombra ningun termino que
                   discrimine entre sus encabezados / secciones.
  3. CLARA       - en otro caso.
La dimension ambigua se describe con los encabezados y secciones de las candidatas y se
propone una aclaracion concreta construida a partir de ellos.

No forma parte de la ruta productiva: ADA no lo importa y su salida lleva
experimental_label = EXPERIMENTAL_NO_DECISORIO, decision_effect = NINGUNO.
"""
import json
import math
import os
import re
from collections import Counter, defaultdict

from . import EXPERIMENTAL_LABEL

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UNITS_PATH = os.path.join(ROOT, "data", "derived", "article_units_v1", "units.jsonl")
CONTENT_TYPES = {"ARTICLE", "CONTINUATION", "NUMBERED", "LETTERED", "INTRO"}
# partes estructurales que no contienen reglas (definiciones y control documental)
NON_RULE_PARTS = {"GLOSSARY", "DOCUMENT CONTROL"}

# palabras funcionales (gramatica, no dominio) ES/EN/FR/PT
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
ES_HINT = re.compile(r"[¿¡ñáéíóú]|\b(el|los|las|qué|cuál|cuántos|cuánto|una|del|para|se|hay)\b", re.I)


def stems(text):
    out = []
    for w in re.findall(r"[a-záéíóúñüàâçèêëîïôûœ]+|\d+", (text or "").lower()):
        if w in STOP or (len(w) < 3 and not w.isdigit()):
            continue
        out.append(w[:5])
    return out


class AmbiguityDetector:
    def __init__(self, units_path=UNITS_PATH, min_info=3.0, ratio=0.9, top_n=6, max_df_discriminative=0.3,
                 k1=1.2, b=0.75):
        self.min_info, self.ratio, self.top_n, self.k1, self.b = min_info, ratio, top_n, k1, b
        self.max_df_discriminative = max_df_discriminative
        self.docs = []
        part = None
        heading_of = {}
        with open(units_path, encoding="utf-8") as fh:
            units = [json.loads(l) for l in fh if l.strip()]
        for u in sorted(units, key=lambda u: (u["page"], u.get("char_start") or 0)):
            if u.get("unit_level") != 1:
                continue
            if u["unit_type"] == "COVER":
                part = u.get("article_label") or u.get("heading")
                continue
            if u["unit_type"] not in CONTENT_TYPES or not u.get("article_label") or part in NON_RULE_PARTS:
                continue
            label = re.sub(r"\s*\.\s*", ".", u["article_label"]).strip()
            heading = re.sub(r"\s+", " ", u.get("heading") or "").strip() or heading_of.get(label, label)
            heading_of.setdefault(label, heading)
            toks = stems(f"{heading} {u['derived_text']}")
            self.docs.append({"article_label": label, "heading": heading,
                              "part": part, "page": u["page"], "tf": Counter(toks), "len": len(toks)})
        self.N = len(self.docs)
        self.avgdl = sum(d["len"] for d in self.docs) / max(1, self.N)
        self.df = Counter(t for d in self.docs for t in d["tf"])

    # --------------------------------------------------------------- BM25
    def _idf(self, t):
        n = self.df.get(t, 0)
        return math.log(1 + (self.N - n + 0.5) / (n + 0.5))

    def _bm25(self, q, d):
        s = 0.0
        for t in q:
            f = d["tf"].get(t, 0)
            if f:
                s += self._idf(t) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * d["len"] / self.avgdl))
        return s

    # --------------------------------------------------------------- analisis
    def analyze(self, query, query_en=None):
        lang = "es" if ES_HINT.search(query or "") else "en"
        q = list(dict.fromkeys(stems(query) + stems(query_en)))
        known = [t for t in q if t in self.df]
        info = round(sum(self._idf(t) for t in known), 3)
        rep = {"experimental_label": EXPERIMENTAL_LABEL, "decision_effect": "NINGUNO", "classification": "CLARA",
               "dimension": None, "candidates": [], "clarification_proposal": None,
               "signals": {"query_terms": q, "known_terms": known, "information": info,
                           "params": {"min_info": self.min_info, "ratio": self.ratio}}}
        if info < self.min_info:
            rep["classification"] = "INCOMPLETA"
            rep["dimension"] = {"type": "OBJETO_O_CONTEXTO_AUSENTE"}
            rep["clarification_proposal"] = (
                "Indique la regla o situación concreta y el ámbito (tipo de evento, grupo de edad o modalidad) al que se refiere."
                if lang == "es" else
                "Please state the specific rule or situation and its scope (event type, age group or discipline).")
            return rep
        best = {}
        for d in self.docs:
            s = self._bm25(known, d)
            key = (d["article_label"], d["heading"])
            if s > 0 and (key not in best or s > best[key]["score"]):
                best[key] = {"article_label": d["article_label"], "heading": d["heading"], "part": d["part"],
                             "page": d["page"], "score": round(s, 3)}
        ranked = sorted(best.values(), key=lambda c: -c["score"])
        if not ranked:
            rep["classification"] = "INCOMPLETA"
            rep["dimension"] = {"type": "SIN_CANDIDATAS"}
            return rep
        top = ranked[0]["score"]
        cands = [c for c in ranked if c["score"] >= self.ratio * top][: self.top_n]
        rep["candidates"] = cands
        rep["signals"]["top_score"] = top
        if len({c["heading"] for c in cands}) < 2:
            return rep
        # terminos que distinguen el encabezado/seccion de cada candidata
        H = [{t for t in stems(f"{c['heading']} {c['part'] or ''}")
              if not t.isdigit() and self.df.get(t, 0) / self.N <= self.max_df_discriminative} for c in cands]
        disc = [H[i] - set().union(*(H[j] for j in range(len(H)) if j != i)) for i in range(len(H))]
        qs = set(q)
        named = [i for i in range(len(cands)) if disc[i] & qs]
        rep["signals"]["named_candidates"] = [cands[i]["article_label"] for i in named]
        if len(named) == 1:
            return rep
        pool = [cands[i] for i in named] if named else cands
        if len({c["heading"] for c in pool}) < 2:
            return rep
        rep["classification"] = "AMBIGUA"
        parts = sorted({c["part"] for c in pool if c["part"]})
        rep["dimension"] = {"type": "SECCION/AMBITO" if len(parts) > 1 else "SUBAPARTADO",
                            "parts": parts, "headings": [c["heading"] for c in pool]}
        opts = [f"{c['heading']} ({c['article_label']})" for c in pool]
        joined = ", ".join(opts[:-1]) + (" o " if lang == "es" else " or ") + opts[-1]
        rep["clarification_proposal"] = (f"¿A cuál de estos supuestos se refiere: {joined}?" if lang == "es"
                                         else f"Which of these cases do you mean: {joined}?")
        return rep

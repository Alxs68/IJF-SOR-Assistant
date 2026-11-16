"""Fase 11B - Variantes EXPERIMENTALES de recuperacion R2-R5 (modo SHADOW, solo evaluacion offline).

Todas parten del ranking de produccion R0 (rre.retrieve, sin modificar) y anaden UNA señal generica
derivada de los datos; no contienen palabras clave, preguntas, articulos ni pasajes escritos a mano.

  R2  unidades de articulo (article_units_v1): BM25 sobre encabezado + texto de cada unidad de nivel 1;
      cada unidad devuelve sus pasajes SOR originales; fusion RRF con R0.
  R3  preferencia por ambito: las "partes" del SOR se derivan de las unidades COVER; un termino es
      indicador de ambito si aparece en el TITULO de una parte y >= 60 % de sus apariciones en
      unidades estan en esa parte. Si la consulta contiene indicadores de una parte, los candidatos
      de esa parte reciben un factor (1 + beta). Sin indicadores, el ranking no cambia.
  R4  carril de referencias cruzadas: destinos RESUELTA de las unidades de los 5 primeros pasajes
      (como maximo 3 pasajes), en un carril separado; no altera el ranking.
  R5  canal denso MULTILINGUE (paraphrase-multilingual-MiniLM-L12-v2) sobre las unidades, con la
      consulta en su idioma original; fusion RRF con R0. Embeddings en cache experimental propia.
Las salidas son listas de passage_id del corpus SOR primario: la autoridad no cambia.
"""
import json
import math
import os
import re
from collections import Counter, defaultdict

from . import EXPERIMENTAL_LABEL
from .ambiguity_detector import stems

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UNITS_PATH = os.path.join(ROOT, "data", "derived", "article_units_v1", "units.jsonl")
CACHE_DIR = os.path.join(ROOT, "data", "eval", "fase11", "cache")
MML_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
K_RRF = 60
CONTENT = {"ARTICLE", "CONTINUATION"}
NON_RULE_PARTS = {"GLOSSARY", "DOCUMENT CONTROL"}


def rrf(*rankings, weights=None, k=K_RRF):
    weights = weights or [1.0] * len(rankings)
    sc = defaultdict(float)
    for w, rk in zip(weights, rankings):
        for i, pid in enumerate(rk, 1):
            sc[pid] += w / (k + i)
    return sorted(sc, key=lambda p: -sc[p])


class UnitCorpus:
    """Unidades de nivel 1 con encabezado heredado y parte (seccion COVER) del SOR."""

    def __init__(self, units_path=UNITS_PATH):
        with open(units_path, encoding="utf-8") as fh:
            units = [json.loads(l) for l in fh if l.strip()]
        self.by_id = {u["unit_id"]: u for u in units}
        self.docs, part, heading_of = [], None, {}
        self.part_title = {}
        self.page_part = {}
        for u in sorted(units, key=lambda u: (u["page"], u.get("char_start") or 0)):
            if u.get("unit_level") != 1:
                continue
            if u["unit_type"] == "COVER":
                part = u.get("article_label") or u.get("heading")
                self.part_title[part] = part
            self.page_part.setdefault(u["page"], part)
            if u["unit_type"] not in CONTENT or not u.get("article_label") or part in NON_RULE_PARTS:
                continue
            lab = re.sub(r"\s*\.\s*", ".", u["article_label"]).strip()
            head = re.sub(r"\s+", " ", u.get("heading") or "").strip() or heading_of.get(lab, lab)
            heading_of.setdefault(lab, head)
            self.docs.append({"unit_id": u["unit_id"], "label": lab, "heading": head, "part": part, "page": u["page"],
                              "pids": list(u.get("original_passage_ids") or u.get("page_passage_ids") or []),
                              "text": f"{head}\n{u['derived_text']}", "cross_refs": u.get("cross_refs") or []})
        # los pasajes SOR son de pagina: todas las unidades de una pagina pertenecen a sus pasajes
        self.units_of_page = defaultdict(list)
        for d in self.docs:
            self.units_of_page[d["page"]].append(d)

    def part_of_page(self, page):
        best = None
        for pg in sorted(self.page_part):
            if pg <= page:
                best = self.page_part[pg]
        return best


class UnitBM25:
    def __init__(self, uc: UnitCorpus, k1=1.2, b=0.75):
        self.uc, self.k1, self.b = uc, k1, b
        self.tf = [Counter(stems(d["text"])) for d in uc.docs]
        self.len = [sum(t.values()) for t in self.tf]
        self.avg = sum(self.len) / max(1, len(self.len))
        self.df = Counter(t for tf in self.tf for t in tf)
        self.N = len(self.tf)

    def search_units(self, query, k=25):
        q = list(dict.fromkeys(stems(query)))
        sc = []
        for i, tf in enumerate(self.tf):
            s = 0.0
            for t in q:
                f = tf.get(t, 0)
                if f:
                    idf = math.log(1 + (self.N - self.df[t] + 0.5) / (self.df[t] + 0.5))
                    s += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
            if s > 0:
                sc.append((i, s))
        sc.sort(key=lambda x: -x[1])
        return sc[:k]

    def passage_ranking(self, query, k=25):
        out = []
        for i, _s in self.search_units(query, k):
            for p in self.uc.docs[i]["pids"]:
                if p not in out:
                    out.append(p)
        return out[:k]


class ScopeModel:
    """Indicadores de ambito derivados de los titulos de las partes del SOR (sin listas manuales)."""

    def __init__(self, uc: UnitCorpus, min_share=0.5, min_lift=4.0, min_count=3):
        """t (termino del titulo de una parte P) es indicador de P si:
        share = apariciones_en_P / apariciones_totales >= min_share   (el termino 'pertenece' a P) y
        lift  = (apariciones_en_P / unidades_de_P) / (apariciones_totales / unidades) >= min_lift
        (concentracion corregida por el tamano de la parte), con >= min_count apariciones en P."""
        occ = defaultdict(Counter)
        size = Counter(d["part"] for d in uc.docs)
        for d in uc.docs:
            for t in set(stems(d["text"])):
                occ[t][d["part"]] += 1
        N = len(uc.docs)
        self.indicator, self.stats = {}, {}
        for part in uc.part_title:
            if part in NON_RULE_PARTS or not part or not size[part]:
                continue
            for t in set(stems(part)):
                tot = sum(occ[t].values())
                inp = occ[t][part]
                if not tot or inp < min_count:
                    continue
                share, lift = inp / tot, (inp / size[part]) / (tot / N)
                self.stats[(t, part)] = (round(share, 3), round(lift, 2))
                if share >= min_share and lift >= min_lift:
                    self.indicator.setdefault(t, set()).add(part)
        self.uc = uc

    def query_parts(self, *texts):
        parts = set()
        for tx in texts:
            for t in stems(tx or ""):
                parts |= self.indicator.get(t, set())
        return parts


def scope_rerank(ranking, parts, part_of_pid, beta=0.2, k=K_RRF):
    if not parts:
        return list(ranking)
    sc = {p: (1.0 / (k + i)) * (1 + beta if part_of_pid(p) in parts else 1.0) for i, p in enumerate(ranking, 1)}
    return sorted(ranking, key=lambda p: -sc[p])


def crossref_lane(top_pids, uc: UnitCorpus, page_of, max_add=3):
    lane = []
    seen = set(top_pids)
    for p in top_pids:
        for d in uc.units_of_page.get(page_of(p), []):
            for r in d["cross_refs"]:
                if r.get("resolution") != "RESUELTA":
                    continue
                for tu in r.get("resolved_point_unit_ids") or r.get("resolved_unit_ids") or []:
                    for tp in (uc.by_id.get(tu) or {}).get("original_passage_ids") or []:
                        if tp not in seen and len(lane) < max_add:
                            seen.add(tp)
                            lane.append({"passage_id": tp, "from": p, "ref": r.get("raw"),
                                         "experimental_label": EXPERIMENTAL_LABEL})
    return lane


class MultilingualDense:
    """Canal denso multilingue experimental (solo local). Carga perezosa; cache en data/eval/fase11/cache."""

    def __init__(self, uc: UnitCorpus, model_name=MML_MODEL, max_seq=256):
        self.uc, self.model_name, self.max_seq = uc, model_name, max_seq
        self.model = self.emb = None
        self.info = {"model": model_name, "loaded": False, "error": None}

    def load(self):
        import hashlib
        import time
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer
            t0 = time.perf_counter()
            self.model = SentenceTransformer(self.model_name, device="cpu")
            self.model.max_seq_length = self.max_seq
            texts = [d["text"] for d in self.uc.docs]
            key = hashlib.sha256((self.model_name + str(self.max_seq) + "".join(texts)).encode("utf-8")).hexdigest()[:16]
            os.makedirs(CACHE_DIR, exist_ok=True)
            path = os.path.join(CACHE_DIR, f"mml12_units_{key}.npy")
            if os.path.exists(path):
                self.emb = np.load(path)
                self.info["cache"] = "HIT"
            else:
                self.emb = self.model.encode(texts, batch_size=16, normalize_embeddings=True, show_progress_bar=False)
                np.save(path, self.emb)
                self.info["cache"] = "BUILT"
            self.np = np
            self.info.update(loaded=True, load_s=round(time.perf_counter() - t0, 1), cache_file=os.path.basename(path),
                             n_units=len(texts))
        except Exception as e:
            self.info["error"] = f"{type(e).__name__}: {str(e)[:300]}"
        return self.info

    def passage_ranking(self, query, k=25):
        if self.emb is None:
            return []
        q = self.model.encode(query, normalize_embeddings=True)
        sims = self.emb @ q
        out = []
        for i in self.np.argsort(-sims)[: k * 2]:
            for p in self.uc.docs[int(i)]["pids"]:
                if p not in out:
                    out.append(p)
        return out[:k]

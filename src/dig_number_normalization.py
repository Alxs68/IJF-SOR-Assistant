"""Fase 11A - Normalizacion de artefactos de formato en las cifras del DIG (variante "v2").

Desactivada por defecto: decision_integrity solo la usa con DIG_NUMBER_NORMALIZATION=v2.
Copia fiel de la normalizacion evaluada en la Fase 11 (src/experimental/dig_variants.py)
(docs/audits/FASE_11_CALIBRACION_DIG.md): 6 desbloqueos en dev con cita del ancla esperada,
0 bloqueos nuevos y 130/130 cifras inventadas detectadas.

Elimina SOLO estos patrones (genericos, derivados de la configuracion y del corpus):
  1. identificadores SOR escritos con guiones Unicode (se normaliza el guion y se aplica SOR_ID);
  2. la fecha de EDICION de corpus_config ("14 August 2026", "14 de agosto de 2026") y "SOR 2026[-08]";
  3. numeracion de LISTAS "N." / "N)" al inicio de linea o tras una cita "[...]." que forma la
     secuencia 1..k con k >= 2;
  4. etiquetas de SECCION seguidas de SU PROPIO titulo ("6.3 Random Weigh-in"), segun article_units_v1.
Puntos ciegos aceptados: una cifra inventada identica a la fecha de edicion, a una etiqueta seguida de
su propio titulo o a la numeracion 1..k de una lista no se distingue.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNITS = os.path.join(ROOT, "data", "derived", "article_units_v1", "units.jsonl")

_DASHES = re.compile(r"[‐‑‒–—―−]")
_SPACES = re.compile(r"[   ]")
_MONTHS = {"january": "enero", "february": "febrero", "march": "marzo", "april": "abril", "may": "mayo",
           "june": "junio", "july": "julio", "august": "agosto", "september": "septiembre",
           "october": "octubre", "november": "noviembre", "december": "diciembre"}
_ENUM_CAND = re.compile(r"(^|\n|\]\s*\.?\s+)\s*(\d{1,2})[.)]\s+(?=[A-ZÁÉÍÓÚÑ¿¡])")
_LABEL_TITLE = re.compile(r"\b((?:[A-H]\d+|\d+)(?:\.\d+)+)\s+((?:[A-Za-z][\w'’-]*\s*){1,3})")
_cache = {}


def _edition_pattern():
    if "edition" not in _cache:
        label = ""
        try:
            try:
                from corpus_config import get_active_corpus_config  # type: ignore
            except ImportError:
                from src.corpus_config import get_active_corpus_config  # type: ignore
            label = get_active_corpus_config().get("version_label", "")
        except Exception:
            label = ""
        m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(20\d\d)", label or "")
        alts = []
        if m:
            d, mon, y = m.group(1), m.group(2).lower(), m.group(3)
            alts.append(rf"\b{d}\s+(?:de\s+)?{mon}\s+(?:de\s+)?{y}\b")
            if mon in _MONTHS:
                alts.append(rf"\b(?:edici[oó]n\s+(?:del?\s+)?)?{d}\s+de\s+{_MONTHS[mon]}\s+de\s+{y}\b")
            alts.append(rf"\bSOR\s*[- ]?\s*{y}(?:\s*[- ]\s*\d\d)?\b")
        _cache["edition"] = re.compile("|".join(alts), re.I) if alts else None
    return _cache["edition"]


def _labels():
    if "labels" not in _cache:
        heads = {}
        if os.path.exists(UNITS):
            with open(UNITS, encoding="utf-8") as fh:
                for line in fh:
                    u = json.loads(line)
                    lab = re.sub(r"\s*\.\s*", ".", u.get("article_label") or "").strip()
                    h = re.sub(r"\s+", " ", u.get("heading") or "").strip()
                    h = re.sub(r"^\s*(?:[A-H]\d+|\d+)(?:\s*\.\s*\d+)*\s*\.?\s*", "", h)
                    if lab and h and lab not in heads:
                        heads[lab] = h.lower()
        _cache["labels"] = heads
    return _cache["labels"]


def _strip_list_numbering(t):
    cands = list(_ENUM_CAND.finditer(t))
    nums = [int(m.group(2)) for m in cands]
    if len(nums) < 2 or sorted(set(nums)) != list(range(1, max(nums) + 1)):
        return t
    out, last = [], 0
    for m in cands:
        out.append(t[last:m.start(2)])
        last = m.end(2) + 1
    out.append(t[last:])
    return "".join(out)


def _strip_section_titles(t):
    heads = _labels()

    def rep(m):
        lab, words = m.group(1), m.group(2).strip().lower()
        h = heads.get(lab)
        if h and words and h.startswith(words.split()[0]) and (len(words.split()) == 1 or h.startswith(" ".join(words.split()[:2]))):
            return " " + m.group(2)
        return m.group(0)
    return _LABEL_TITLE.sub(rep, t)


def normalize_formatting(text, sor_id_regex):
    t = _SPACES.sub(" ", text or "")
    t = _DASHES.sub("-", t)
    t = sor_id_regex.sub(" ", t)
    ed = _edition_pattern()
    if ed is not None:
        t = ed.sub(" ", t)
    t = _strip_list_numbering(t)
    t = _strip_section_titles(t)
    return t

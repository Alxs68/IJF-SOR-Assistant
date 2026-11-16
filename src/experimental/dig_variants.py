"""Fase 11 - Variante EXPERIMENTAL de normalizacion de cifras del DIG (no conectada a produccion).

Motivacion (docs/audits/FASE_11_DIAGNOSTICO_ABSTENCIONES.md, seccion 4.1, M1): en respuestas
reales del LLM, DIG-06 / DIG-08 cuentan como "cifras" elementos que no son afirmaciones normativas.
numbers_in_v2 elimina SOLO estos patrones, todos genericos y derivados de datos del propio corpus
(nunca de preguntas, pasajes concretos ni del benchmark):

  1. identificadores SOR escritos con guiones Unicode (U+2010..U+2015, U+2212): se normaliza el
     guion y se aplica el mismo patron SOR_ID del DIG.
  2. la fecha de EDICION del documento, tomada de corpus_config (version_label, p. ej.
     "14 August 2026"), en ingles o espanol, y la mencion "SOR 2026[-08]". Otras fechas se conservan.
  3. numeracion de LISTAS: marcadores "N." / "N)" al inicio de linea o tras una cita "[...]." que
     forman una secuencia 1..k con k >= 2. Un numero aislado con punto no se elimina.
  4. etiquetas de SECCION seguidas de SU PROPIO titulo: "6.3 Random Weigh-in" solo si 6.3 es una
     etiqueta del corpus (article_units_v1) y las palabras siguientes coinciden con el inicio de su
     encabezado. "6.3 Kilograms" se conserva.
Todo lo demas lo decide decision_integrity.numbers_in sin cambios.

VARIANT_ACTIVE / dig_variant() permiten reejecutar el DIG de produccion OFFLINE con esta
normalizacion, sustituyendo temporalmente la funcion del modulo en el proceso de evaluacion y
restaurandola siempre al salir. Ningun modulo productivo importa este archivo.
"""
import contextlib
import json
import os
import re

import decision_integrity as _dig
from decision_integrity import SOR_ID, numbers_in

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UNITS = os.path.join(ROOT, "data", "derived", "article_units_v1", "units.jsonl")
_ORIG_NUMBERS_IN = _dig.numbers_in

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
            from corpus_config import get_active_corpus_config  # type: ignore
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
        _cache["edition_label"] = label
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
                    h = re.sub(r"^\s*(?:[A-H]\d+|\d+)(?:\s*\.\s*\d+)*\s*\.?\s*", "", h)  # quitar la etiqueta del encabezado
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
        last = m.end(2) + 1  # quitar "N." / "N)"
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


def normalize_formatting(text):
    t = _SPACES.sub(" ", text or "")
    t = _DASHES.sub("-", t)
    t = SOR_ID.sub(" ", t)
    ed = _edition_pattern()
    if ed is not None:
        t = ed.sub(" ", t)
    t = _strip_list_numbering(t)
    t = _strip_section_titles(t)
    return t


def numbers_in_v2(text):
    return _ORIG_NUMBERS_IN(normalize_formatting(text))


def formatting_artifacts(answer_text, missing_numbers):
    """Cifras senaladas por DIG-06 que desaparecen al quitar solo artefactos de formato."""
    remaining = numbers_in_v2(answer_text)
    return sorted(n for n in missing_numbers if n not in remaining)


@contextlib.contextmanager
def dig_variant():
    """Solo para reejecucion OFFLINE: el DIG usa numbers_in_v2 dentro del bloque y se restaura al salir."""
    _dig.numbers_in = numbers_in_v2
    try:
        yield
    finally:
        _dig.numbers_in = _ORIG_NUMBERS_IN

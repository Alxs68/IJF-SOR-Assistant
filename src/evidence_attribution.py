"""Completado determinista de la atribucion literal (ADA_EVIDENCE_COMPLETION=1).

Problema que corrige (falso rechazo tipo D): el modelo escribe una cifra o un termino tecnico del SOR que SI
figura en un pasaje que el mismo cita, pero no lo incluye en sus 'evidence_quotes'; DIG-06/DIG-07 rechazan entonces
una respuesta respaldada. Aqui, ANTES del DIG, para cada cifra o termino distintivo sin cita se busca en los pasajes
que la respuesta cita una frase que (a) lo contiene literalmente y (b) comparte con la afirmacion al menos otro
concepto (termino, cifra o equivalente del diccionario ES->EN del proyecto). Esa frase, copiada literalmente del
pasaje, se anade como cita con la marca "[atribucion automatica]".

No cambia ningun control del DIG: la respuesta completada se evalua con TODOS los controles (literalidad DIG-03,
pertinencia DIG-05, excepciones DIG-09, referencias DIG-10...). No anade texto a la respuesta visible ni cita
pasajes que la respuesta no cite. No anade nunca frases de excepcion para satisfacer DIG-09: si la frase elegida
tiene una excepcion cercana no citada, DIG-09 la rechaza igual que si la hubiera citado el modelo.
"""
from __future__ import annotations

import json
import os
import re

from decision_integrity import (CLAIM_FIELDS, EXCEPTION_MARKER, EXTRA_CLAIM_FIELDS, LIMITATION_FIELD, MIN_QUOTE_WORDS,
                                SOR_ID, STOP, concept_in_primary, norm, numbers_in, parse_answer, prune_units,
                                sentence_spans, strip_accents)

MAX_ADDED = 8
TAG = "[atribucion automatica]"
_WORD = re.compile(r"[a-z][a-z\-]{3,}")


def enabled():
    return os.environ.get("ADA_EVIDENCE_COMPLETION", "").strip() == "1"


def _words(text):
    return {w for w in _WORD.findall(strip_accents(norm(SOR_ID.sub(" ", text or "")))) if w not in STOP}


def _passage_sentences(passage):
    text = passage.get("text_original") or ""
    spans = sentence_spans(text)
    out = []
    for i, (a, b) in enumerate(spans):
        raw = re.sub(r"\s+", " ", text[a:b]).strip()
        if len(norm(raw).split()) < MIN_QUOTE_WORDS or "page break" in raw.lower():
            continue
        near = [text[x:y] for x, y in spans[max(0, i - 2):i] + spans[i + 1:i + 3]]
        out.append({"raw": raw, "words": _words(raw), "nums": numbers_in(raw),
                    "exception_near": any(EXCEPTION_MARKER.search(s) for s in near) and not EXCEPTION_MARKER.search(raw)})
    return out


def _anchored(claim_words, claim_nums, item, sent):
    """La frase comparte con la afirmacion al menos un concepto distinto del propio elemento."""
    others = {w for w in claim_words if w != item}
    if others & sent["words"] or (set(claim_nums) - {item}) & sent["nums"]:
        return True
    return any(len(w) >= 5 and concept_in_primary(w, sent["words"]) for w in others)


def complete_quotes(answer, delivered, gate, query, search_query_en, unified=True):
    """Devuelve (respuesta_json, anadidas). 'delivered' = {passage_id: pasaje entregado al modelo}."""
    obj = parse_answer(answer)
    if not isinstance(obj, dict):
        return answer, []
    fields = CLAIM_FIELDS + (EXTRA_CLAIM_FIELDS + (LIMITATION_FIELD,) if unified else ())
    visible = {f: str(obj.get(f) or "") for f in fields}
    cited = set(SOR_ID.findall(json.dumps({**visible, "citations": obj.get("citations")}, ensure_ascii=False)))
    cited &= set(delivered)
    if not cited:
        return answer, []
    quotes = [q for q in (obj.get("evidence_quotes") or []) if isinstance(q, dict)]
    quote_nums, q_terms = gate._quote_support({"evidence_quotes": quotes}, query, search_query_en)
    sents = {pid: _passage_sentences(delivered[pid]) for pid in sorted(cited)}
    added = []
    for field, text in visible.items():
        for unit in prune_units(text) or ([text] if text.strip() else []):
            extra = numbers_in(query + " " + (search_query_en or "")) if field == LIMITATION_FIELD else frozenset()
            nums, terms = gate._unsupported(unit, quote_nums, q_terms, extra_nums=extra, query=query)
            if not nums and not terms:
                continue
            claim_words, claim_nums = _words(unit), numbers_in(unit)
            here = [p for p in SOR_ID.findall(unit) if p in sents]
            order = here + [p for p in sorted(sents) if p not in here]
            for kind, item in [("cifra", n) for n in nums] + [("termino", t) for t in terms]:
                if len(added) >= MAX_ADDED:
                    break
                best = None
                for pid in order:
                    for s in sents[pid]:
                        has = item in s["nums"] if kind == "cifra" else (
                            item in s["words"] or any(item in w.split("-") for w in s["words"] if "-" in w))
                        if not has or not _anchored(claim_words, claim_nums, item, s):
                            continue
                        key = (s["exception_near"], pid not in here, len(s["raw"]))
                        if best is None or key < best[0]:
                            best = (key, pid, s)
                    if best and best[1] in here and not best[0][0]:
                        break
                if best is None:
                    continue
                _k, pid, s = best
                if not any(q.get("passage_id") == pid and norm(q.get("quote") or "") == norm(s["raw"]) for q in quotes):
                    q = {"passage_id": pid, "quote": s["raw"], "supports": f"{TAG} {kind}: {item}"}
                    quotes.append(q)
                    added.append({"campo": field, "tipo": kind, "elemento": item, "passage_id": pid, "cita": s["raw"][:160]})
                quote_nums, q_terms = gate._quote_support({"evidence_quotes": quotes}, query, search_query_en)
    if not added:
        return answer, []
    obj["evidence_quotes"] = quotes
    return json.dumps(obj, ensure_ascii=False), added

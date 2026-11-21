"""Integridad de referencias normativas (F1, experimental; NO integrado en V4 ni en el DIG).

Problema (experiments/optimizacion_tokens_2026/AUDITORIA_REFERENCIAS_NORMATIVAS.md): una frase que cita
"Art. 19.1.1" cuando el pasaje citado es el 18.1.1 no la detecta ninguna capa. numbers_in (DIG-06 y V4 1c)
elimina siempre las referencias documentales y el prompt del verificador ordena ignorarlas.

Este modulo compara cada referencia normativa EXPLICITA de una frase con la ESTRUCTURA de los pasajes que la propia
frase cita (encabezados numerados del texto, article_id, unidades derivadas article_units_v1, continuaciones de
pagina y referencias cruzadas). No compara "todos los numeros": cantidades, tiempos, pesos, porcentajes, fechas,
paginas, figuras, tablas y codigos se excluyen antes de extraer.

Determinista, sin red, sin modelos, sin Streamlit; solo lee datos locales (passages_candidate.json y units.jsonl).
No retira nada: devuelve veredictos con su motivo y la accion que recomendaria.

API:
    idx = ReferenceIndex.load()                      # o ReferenceIndex(passages, units) en pruebas
    idx.check(sentence, cited_ids, answer_ids=None)  -> list[dict]
Veredictos: OK, OK_REF_CRUZADA, OK_ARTICULO_CLAUSULA, INEXISTENTE, DISCREPANCIA, SIN_CITA, NO_EVALUABLE.
"""
import json
import os
import re
from dataclasses import asdict, dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASSAGES_PATH = os.path.join(ROOT, "data", "processed", "rebuild_2026_08_corrected", "passages_candidate.json")
UNITS_PATH = os.path.join(ROOT, "data", "derived", "article_units_v1", "units.jsonl")

SOR_ID = re.compile(r"SOR-[A-Za-z0-9]+-[A-Za-z0-9]+-P\d+-S\d+")
# Etiqueta estructural: letra de apendice opcional, 1-2 digitos por componente, hasta 5 componentes; espacios
# irregulares alrededor del punto ("18 .1 .1", como en el texto extraido del PDF).
_COMP = r"\d{1,2}"
LABEL = rf"[A-Ha-h]?{_COMP}(?:[ \t]?\.[ \t]?{_COMP}){{0,4}}"
_UNIT_AFTER = r"(?:kg|g|cm|mm|m|km|%|min|mins|minutos?|minutes?|seg|segundos?|seconds?|s|h|horas?|hours?|pts?|puntos?|points?|años|years?)\b"

# ---- exclusiones previas (se enmascaran con espacios para conservar posiciones) -------------------------------------
_MONTHS = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|"
           r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|"
           r"setiembre|octubre|noviembre|diciembre|janeiro|fevereiro|março|marco|maio|junho|julho|setembro|outubro|"
           r"novembro|dezembro)")
EXCLUSIONS = [
    ("identificador SOR", SOR_ID),
    ("fecha", re.compile(rf"(?i)\b\d{{1,2}}\s+(?:de\s+)?{_MONTHS}\s+(?:de\s+)?\d{{4}}\b|\b{_MONTHS}\s+\d{{1,2}},?\s+\d{{4}}\b|"
                         r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}[/.]\d{1,2}[/.]\d{2,4}\b")),
    ("edicion SOR", re.compile(r"(?i)\bSOR\s*[- ]?\s*20\d\d(?:\s*[-/]\s*\d\d)?\b")),
    ("pagina", re.compile(r"(?i)\b(?:p[aá]g(?:ina)?s?|pages?|pp?)\.?\s*\d+(?:\s*(?:[-–]|y|and|e|a|to)\s*\d+)*")),
    ("figura/tabla", re.compile(rf"(?i)\b(?:pictures?|figures?|figuras?|figs?\.?|im[aá]gen(?:es)?|imagens?|fotos?|"
                                rf"photos?|tablas?|tables?|tabelas?|quadros?|cuadros?|diagram(?:a|s)?)\s*(?:n\.?\s?[º°o]\s*)?"
                                rf"{LABEL}(?:\s*[-–]\s*{LABEL})?")),
    ("codigo", re.compile(r"(?i)\b(?:pantone|ref(?:erencia|erence)?\.?|c[oó]digo|code|n\.?\s?[º°o]|nº|no\.)\s*\d[\w\-()./]*")),
    ("categoria de peso", re.compile(r"(?i)[-+−]\s?\d+(?:[.,]\d+)?\s?kg\b|\bU\s?\d{2}\b")),
    ("tiempo", re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")),
]

# ---- extraccion -----------------------------------------------------------------------------------------------------
_PREFIX = (r"art[ií]culos?|articles?|artigos?|arts?\.?|secci[oó]n(?:es)?|sections?|se[cç](?:[aã]o|[oõ]es)|"
           r"reglas?|rules?|regras?|ap[eé]ndices?|appendix|appendices|anexos?")
_CONNECT = r"(?:,|;|/|[-–]|\by\b|\be\b|\bo\b|\bou\b|\band\b|\bor\b|\bto\b|\ba\b|\bal\b)"
# letra pegada a la etiqueta ("13.3.b", "13.3b"), nunca separada por espacio ("6.4.1 y" no es "6.4.1.y")
_LETTER = r"(?:\.?(?P<letter>[a-z])(?![A-Za-z]))?"
EXPLICIT = re.compile(rf"(?i)\b(?P<prefix>{_PREFIX})\s*(?:n\.?\s?[º°o]\s*)?(?P<label>{LABEL})(?-i:{_LETTER})(?!\s*{_UNIT_AFTER})(?![\d])")
# "apartado 6.2.5.4" es una seccion; "apartado 4" es una clausula
APARTADO_SECTION = re.compile(rf"(?i)\b(?P<prefix>apartados?|subapartados?|ep[ií]grafes?)\s+(?P<label>{_COMP}(?:[ \t]?\.[ \t]?{_COMP}){{1,4}})(?![\d])")
LIST_ITEM = re.compile(rf"\s*{_CONNECT}\s*(?P<label>[A-Ha-h]?{_COMP}(?:[ \t]?\.[ \t]?{_COMP}){{1,4}})(?-i:{_LETTER})(?!\s*{_UNIT_AFTER})(?![\d])")
BARE = re.compile(rf"(?<![\w.\-/,])(?P<label>(?:[A-H]{_COMP}(?:[ \t]?\.[ \t]?{_COMP}){{1,4}})|(?:{_COMP}(?:[ \t]?\.[ \t]?{_COMP}){{2,4}}))"
                  rf"(?![\w]|[.,]\d)(?!\s*{_UNIT_AFTER})")
CLAUSE = re.compile(r"(?i)\b(?P<prefix>apartados?|p[aá]rrafos?|puntos?|paragraphs?|points?|par[aá]grafos?|incisos?|"
                    r"cl[aá]usulas?|clauses?)\s+(?P<label>\d{1,2})(?![\d]|[ \t]?\.[ \t]?\d)(?:\s*(?:\(|,)?\s*(?:letra\s+)?(?P<letter>[a-z])\))?")

# encabezado numerado de una linea del pasaje: "Article 18 .1 .1 Shido…", "6 .4 .1 . Standalone…", "C1 .11 T-shirt"
HEADING = re.compile(rf"(?m)^[ \t]*(?P<art>Article[ \t]+)?(?P<label>[A-H]?{_COMP}(?:[ \t]?\.[ \t]?{_COMP}){{0,4}})(?:[ \t]?\.)?[ \t]+"
                     rf"(?!(?:kg|Kg|KG|cm|mm|m|min|sec|s|%)\b)(?=[A-Z(])")
MENTION = re.compile(rf"(?i)\b(?:article|section|appendix|rule|see)\s+(?P<label>{LABEL})(?![\d])")
NUMBERED_LINE = re.compile(r"(?m)^[ \t]*(?P<n>\d{1,2})\.[ \t]+\S")
LETTERED_LINE = re.compile(r"(?m)^[ \t]*(?P<l>[a-z])\)[ \t]+\S")

VERDICTS = ("OK", "OK_REF_CRUZADA", "OK_ARTICULO_CLAUSULA", "INEXISTENTE", "DISCREPANCIA", "SIN_CITA", "NO_EVALUABLE")
ACTION = {"OK": "NINGUNA", "OK_REF_CRUZADA": "NINGUNA", "OK_ARTICULO_CLAUSULA": "NINGUNA",
          "INEXISTENTE": "RETIRAR_FRASE", "DISCREPANCIA": "RETIRAR_FRASE", "SIN_CITA": "REGISTRAR",
          "NO_EVALUABLE": "REGISTRAR"}


def canon(label):
    """'Article 18 .1 .1' -> '18.1.1'; '6.4.2.' -> '6.4.2'; 'c1 .11' -> 'C1.11'."""
    s = re.sub(rf"(?i)^\s*(?:{_PREFIX})\s*", "", str(label or "").strip())
    s = re.sub(r"\s*\.\s*", ".", s).strip(" .")
    return s[:1].upper() + s[1:] if s[:1].isalpha() else s


def ancestors(label):
    parts = label.split(".")
    return {".".join(parts[:i]) for i in range(1, len(parts) + 1)}


def _is_structural(label, has_article_prefix=False):
    return bool(re.search(r"\d", label)) and ("." in label or has_article_prefix)


def mask_exclusions(text):
    """Texto con las exclusiones sustituidas por espacios (mismas posiciones) y lista de lo excluido."""
    t, excluded = text or "", []
    for name, rx in EXCLUSIONS:
        def _sub(m, name=name):
            excluded.append({"tipo": name, "texto": m.group(0)})
            return " " * len(m.group(0))
        t = rx.sub(_sub, t)
    return t, excluded


@dataclass
class Reference:
    raw: str
    label: str
    letter: str
    kind: str          # EXPLICITA | DESNUDA | CLAUSULA
    start: int
    end: int
    prefix: str = ""


def extract_references(sentence):
    """Referencias normativas de una frase (nunca cifras sueltas). Devuelve (referencias, exclusiones)."""
    t, excluded = mask_exclusions(sentence)
    refs, taken = [], []

    def free(a, b):
        return not any(a < y and x < b for x, y in taken)

    def add(m, kind, label, letter, prefix=""):
        a, b = m.start("label"), m.end("label") + (len(m.group("letter")) + 1 if m.groupdict().get("letter") else 0)
        if free(a, b):
            refs.append(Reference(raw=sentence[a:b].strip(), label=canon(label), letter=(letter or "").lower(), kind=kind,
                                  start=a, end=b, prefix=prefix))
            taken.append((a, b))

    for rx in (APARTADO_SECTION, EXPLICIT):
        for m in rx.finditer(t):
            if not free(m.start(), m.end()):
                continue
            add(m, "EXPLICITA", m.group("label"), m.groupdict().get("letter"), m.group("prefix"))
            pos = m.end()
            while True:                       # "Arts. 6.4.2 y 6.4.3", "18.1.1–18.1.3", "6.4.1, 6.4.2 and 6.4.3"
                li = LIST_ITEM.match(t, pos)
                if not li:
                    break
                add(li, "EXPLICITA", li.group("label"), li.group("letter"), m.group("prefix"))
                pos = li.end()
    for m in CLAUSE.finditer(t):
        if free(m.start("label"), m.end("label")):
            refs.append(Reference(raw=m.group(0).strip(), label=m.group("label"), letter=(m.group("letter") or "").lower(),
                                  kind="CLAUSULA", start=m.start(), end=m.end(), prefix=m.group("prefix")))
            taken.append((m.start(), m.end()))
    for m in BARE.finditer(t):
        if free(m.start(), m.end()):
            add(m, "DESNUDA", m.group("label"), None)
    refs.sort(key=lambda r: r.start)
    return refs, excluded


@dataclass
class Verdict:
    referencia: str
    etiqueta: str
    tipo: str
    pasajes_citados: list
    etiquetas_estructurales: list
    veredicto: str
    motivo: str
    confianza: str
    accion_recomendada: str
    ubicacion_en_corpus: list = field(default_factory=list)
    veredicto_con_citas_respuesta: str = None

    def to_dict(self):
        return asdict(self)


class ReferenceIndex:
    """Indice estructural del corpus, construido una vez y en solo lectura."""

    def __init__(self, passages, units):
        self.passages = {p["passage_id"]: p for p in passages if p.get("passage_id")}
        self.labels = {}          # pid -> etiquetas estructurales (sin ancestros)
        self.mentions = {}        # pid -> referencias cruzadas / menciones a otras etiquetas
        # Dos numeraciones conviven en el SOR: 'Article N' (reglas de arbitraje) y las secciones/apendices ('6.3',
        # 'C1.11'). '6' puede ser el Article 6 o la seccion 6: las clausulas se indexan por (espacio, etiqueta).
        self.ns_labels = {}       # pid -> {(espacio, etiqueta)} con espacio 'ART' o 'SEC'
        self.clauses = {}         # (espacio, etiqueta) -> clausulas numeradas/letradas
        self.where = {}           # etiqueta -> pasajes que la contienen
        unit_labels, unit_xrefs, cont_label = {}, {}, {}
        for u in units:
            lab = canon(u.get("article_label") or "")
            ns = "ART" if str(u.get("article_label") or "").lower().startswith("article") else "SEC"
            for pid in u.get("original_passage_ids") or []:
                if lab and _is_structural(lab, ns == "ART"):
                    unit_labels.setdefault(pid, set()).add((ns, lab))
                    if u.get("unit_type") == "CONTINUATION":
                        cont_label.setdefault(pid, (ns, lab))
                for r in u.get("cross_refs") or []:
                    if r.get("type") in ("ARTICLE", "SECTION", "APPENDIX_SECTION") and r.get("target"):
                        unit_xrefs.setdefault(pid, set()).add(canon(r["target"]))
            if lab and u.get("clause_label"):
                self.clauses.setdefault((ns, lab), set()).add(str(u["clause_label"]).lower())
        for pid, p in self.passages.items():
            text = p.get("text_original") or ""
            nlabs = set(unit_labels.get(pid, set()))
            aid = canon(p.get("article_id") or "")
            aid_ns = "ART" if str(p.get("article_id") or "").lower().startswith("article") else "SEC"
            if aid and _is_structural(aid, aid_ns == "ART"):
                nlabs.add((aid_ns, aid))
            heads = []
            for m in HEADING.finditer(text):
                lab = canon(m.group("label"))
                if _is_structural(lab, bool(m.group("art"))):
                    key = ("ART" if m.group("art") else "SEC", lab)
                    nlabs.add(key)
                    heads.append((m.start(), key))
            self.ns_labels[pid] = nlabs
            labs = {lab for _, lab in nlabs}
            self.labels[pid] = labs
            ments = set(unit_xrefs.get(pid, set()))
            for m in MENTION.finditer(text):
                lab = canon(m.group("label"))
                if re.search(r"\d", lab) and lab not in labs:
                    ments.add(lab)
            self.mentions[pid] = ments
            # clausulas del texto, atribuidas a la etiqueta que gobierna su posicion (o la heredada de la pagina)
            inherited = cont_label.get(pid) or ((aid_ns, aid) if aid else None)
            for rx, key in ((NUMBERED_LINE, "n"), (LETTERED_LINE, "l")):
                for m in rx.finditer(text):
                    gov = next((lab for pos, lab in reversed(heads) if pos <= m.start()), inherited)
                    if gov:
                        self.clauses.setdefault(gov, set()).add(m.group(key).lower())
        for pid, labs in self.labels.items():
            for lab in labs:
                self.where.setdefault(lab, set()).add(pid)
        self.known = set()
        for labs in self.labels.values():
            for lab in labs:
                self.known |= ancestors(lab)

    @classmethod
    def load(cls, passages_path=PASSAGES_PATH, units_path=UNITS_PATH):
        with open(passages_path, encoding="utf-8") as fh:
            passages = json.load(fh)
        passages = passages if isinstance(passages, list) else passages.get("passages", [])
        with open(units_path, encoding="utf-8") as fh:
            units = [json.loads(line) for line in fh if line.strip()]
        return cls(passages, units)

    # ---- juicio ---------------------------------------------------------------------------------------------------
    def structural_labels(self, cited):
        labs = set()
        for pid in cited:
            labs |= self.labels.get(pid, set())
        return labs

    def _judge(self, ref, cited):
        cited = sorted(set(cited or ()))
        labs = self.structural_labels(cited)
        base = dict(referencia=ref.raw, etiqueta=ref.label + (f".{ref.letter}" if ref.letter else ""), tipo=ref.kind,
                    pasajes_citados=cited, etiquetas_estructurales=sorted(labs))

        def v(verdict, why, conf):
            return Verdict(veredicto=verdict, motivo=why, confianza=conf, accion_recomendada=ACTION[verdict],
                           ubicacion_en_corpus=sorted(self.where.get(ref.label, set()))[:6], **base)

        if not cited:
            return v("SIN_CITA", "la frase no cita ningun pasaje", "BAJA")
        unknown = [pid for pid in cited if pid not in self.passages]
        if unknown and not labs:
            return v("NO_EVALUABLE", f"pasajes citados fuera del indice: {unknown}", "BAJA")
        anc_ns = self.ns_ancestors(cited)
        if ref.kind == "CLAUSULA":
            found = any(ref.label in self.clauses.get(key, set()) for key in anc_ns)
            return v("NO_EVALUABLE", "referencia a clausula: solo registro (segmentacion de clausulas incompleta en "
                     f"continuaciones); {'localizada' if found else 'no localizada'} en los articulos citados", "BAJA")
        if not labs:
            return v("NO_EVALUABLE", "los pasajes citados no tienen etiqueta estructural", "BAJA")
        anc = self.known_ancestors(labs)
        conf = "ALTA" if ref.kind == "EXPLICITA" else "MEDIA"
        if ref.label in anc:
            return v("OK", "la etiqueta (o un nivel superior) es un encabezado de los pasajes citados", conf)
        ments = set().union(*[self.mentions.get(pid, set()) for pid in cited])
        if ref.label in ments or any(ref.label in ancestors(m) for m in ments):
            return v("OK_REF_CRUZADA", "los pasajes citados remiten expresamente a esa etiqueta", conf)
        head, _, last = ref.label.rpartition(".")
        if head and any((ns, head) in anc_ns and last.lower() in self.clauses.get((ns, head), set()) for ns in ("ART", "SEC")):
            return v("OK_ARTICULO_CLAUSULA", f"forma compuesta: {head} (encabezado citado) + clausula {last}"
                     + (f" letra {ref.letter}" if ref.letter else ""), "MEDIA")
        if unknown:
            return v("NO_EVALUABLE", "no figura en los pasajes indexados y hay pasajes citados fuera del indice: "
                     f"{unknown}", "BAJA")
        if ref.label not in self.known:
            return v("INEXISTENTE", "la etiqueta no existe en el corpus SOR", conf)
        return v("DISCREPANCIA", "la etiqueta existe en el corpus pero no en los pasajes que cita la frase", conf)

    def ns_ancestors(self, cited):
        out = set()
        for pid in cited:
            for ns, lab in self.ns_labels.get(pid, set()):
                out |= {(ns, a) for a in ancestors(lab)}
        return out

    def known_ancestors(self, labs):
        out = set()
        for lab in labs:
            out |= ancestors(lab)
        return out

    def check(self, sentence, cited_ids=None, answer_ids=None):
        """Veredicto de cada referencia normativa de 'sentence' frente a los pasajes que cita (cited_ids; si es None,
        los identificadores SOR escritos en la propia frase). Si la frase no cita nada y se da 'answer_ids', se anade
        el veredicto con las citas de toda la respuesta (solo informativo)."""
        if cited_ids is None:
            cited_ids = SOR_ID.findall(sentence or "")
        refs, _ = extract_references(sentence)
        out = []
        for ref in refs:
            ver = self._judge(ref, cited_ids)
            if ver.veredicto == "SIN_CITA" and answer_ids:
                ver.veredicto_con_citas_respuesta = self._judge(ref, answer_ids).veredicto
            out.append(ver.to_dict())
        return out


_DEFAULT = None


def default_index():
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = ReferenceIndex.load()
    return _DEFAULT


def check(sentence, cited_ids=None, answer_ids=None):
    """Atajo con el indice del corpus local por defecto."""
    return default_index().check(sentence, cited_ids, answer_ids)

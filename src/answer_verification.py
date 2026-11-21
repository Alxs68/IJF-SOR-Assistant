"""Verificacion de respuestas V4 (ADA_VERIFICATION_V4=1; desactivada por defecto).

Sustituye la DECISION bloqueante del DIG (una sola falla -> abstencion de toda la respuesta) por una verificacion
que CORRIGE antes de rechazar. Diseno: docs/audits/DISENO_VERIFICACION_RESPUESTAS_2026-11-18.md. Todas las reglas son
genericas: no hay condiciones por consulta, articulo, pagina ni identificador.

Capa 1 (determinista, por cita y por frase):
  - una cita corta (< MIN_QUOTE_WORDS) se amplia a su renglon completo del pasaje (fila de tabla, elemento de lista);
  - una cita es valida si es literal de un pasaje SOR ENTREGADO (las de SHADOW no lo son);
  - un pasaje citado sin cita valida se retira: se quita su identificador y las frases que solo se apoyaban en el;
  - una frase con una cifra afirmada que no figura en los pasajes citados (ni en la consulta) se retira.
  - capa 1d (ADA_REFERENCE_CHECK=shadow; desactivada por defecto): integridad de las referencias normativas
    (src/reference_integrity.py). SOLO REGISTRO en registro['verification']['references']: no modifica la respuesta,
    ni la decision, ni el verificador LLM. Separada de la capa 1c (cifras, DIG-06): no reutiliza ni altera su logica.
Capa 2 (verificador LLM, una llamada): pertinencia de cada cita, respaldo de cada frase CONTRA LOS PASAJES CITADOS
  (condiciones invertidas, cifras, alcance) y si la respuesta contesta la pregunta. Se retiran las citas no
  pertinentes y las frases sin respaldo.
Capa 3 (completado): las oraciones con excepcion de la misma unidad derivada que la capa 2 juzga pertinentes se
  ANADEN a 'conditions_and_exceptions' con su cita literal; nunca provocan abstencion (sustituye a DIG-09).
Respuestas negativas: una respuesta EVIDENCIA_INSUFICIENTE se emite si solo declara lo que los pasajes no contienen
  (sin cifras) y el verificador la considera respaldada.
Controles duros que se conservan del DIG: respuesta JSON y ausencia de influencia SHADOW (DIG-04, DIG-08).
Modo degradado (sin verificador LLM): capa 1 y despues DECIDE EL DIG COMPLETO sobre la respuesta ya corregida
  (comportamiento conservador: sin verificacion semantica no se relaja ningun control); se marca 'REDUCIDA'.
  Una primera version usaba solo similitud semantica (coseno >= 0,45) y emitia respuestas de otro tema que el DIG
  rechazaba (pruebas adversariales, 2026-11-18); por eso se sustituyo.
"""
import json
import os
import re
import time

import decision_integrity as D

FIELDS = ("summary", "normative_basis", "conditions_and_exceptions", "extended_analysis", "limitations")
CLAIM_FIELDS = ("summary", "normative_basis", "conditions_and_exceptions", "extended_analysis")
PLACEHOLDERS = {"", "no aplica", "not applicable", "n/a", "ninguna", "none", "nenhuma", "não se aplica", "nao se aplica"}
HARD_CHECKS = ("DIG-04_CITA_NO_SHADOW", "DIG-08_SIN_INFLUENCIA_SHADOW")
MAX_EXCEPTIONS = 6
DEFAULT_VERIFIER_MODEL = "gemini-flash-latest"
# Nombre del documento con su edicion ("SOR 2026", "Sport and Organisation Rules 2026"): es una referencia, no una
# cifra afirmada (igual que los identificadores de cita).
_DOC_NAME = re.compile(r"\b(?:SOR|Sport\s+and\s+Organi[sz]ation\s+Rules)(?:[\s\-]+\(?20\d{2}\)?)?", re.IGNORECASE)

PROMPT = """You are a strict verifier for a judo rules assistant (IJF Sport and Organisation Rules, SOR 2026).
You receive a user QUESTION, the full text of the SOR PASSAGES cited by an answer, numbered literal QUOTES taken from them, numbered candidate EXCEPTIONS (sentences near the quotes) and the numbered SENTENCES of the ANSWER (the answer may be in Spanish, Portuguese or English; the SOR is in English).

Judge ONLY with the passages. Do not use outside knowledge. Article or page numbers mentioned in the answer are references, not facts: ignore them.
1. For each quote: "pertinent" = true if the quote states a rule that helps answer the QUESTION (same subject matter as what is asked), false otherwise.
2. For each sentence: "supported" = true if every fact in it (numbers, durations, sanctions, conditions, who/what/when) is stated or directly implied by the PASSAGES; false if any element is missing from, or contradicts, the passages (pay special attention to inverted conditions, wrong numbers, wrong scope such as a rule for one category or event generalised to all). A sentence saying that the passages do not contain some information counts as supported. List the unsupported elements.
3. For each exception: "relevant" = true only if it limits or changes the answer to THIS question.
4. "answers_question" = true if the answer as a whole addresses what the QUESTION asks (stating that the passages do not contain the requested information also counts).

Return ONLY JSON: {{"quotes":[{{"n":1,"pertinent":true}}],"sentences":[{{"n":1,"supported":true,"unsupported":""}}],"exceptions":[{{"n":1,"relevant":false}}],"answers_question":true}}

QUESTION: {question}

PASSAGES:
{passages}

QUOTES:
{quotes}

EXCEPTIONS:
{exceptions}

ANSWER SENTENCES:
{sentences}
"""


def enabled():
    return os.environ.get("ADA_VERIFICATION_V4", "").strip() == "1"


# Capa 1d: unico modo implementado. Cualquier otro valor (incluido '1') deja la capa desactivada.
REFERENCE_CHECK_MODES = ("shadow",)
# Campos de cada resultado que se registran: identificadores, etiquetas y veredicto; nunca el texto de la frase.
REFERENCE_LOG_FIELDS = ("referencia", "etiqueta", "tipo", "pasajes_citados", "veredicto", "motivo", "confianza",
                        "accion_recomendada", "ubicacion_en_corpus", "veredicto_con_citas_respuesta")


def reference_check_mode():
    """ADA_REFERENCE_CHECK: 'shadow' -> 'shadow'; ausente, vacia o cualquier otro valor -> None (desactivada)."""
    mode = os.environ.get("ADA_REFERENCE_CHECK", "").strip().lower()
    return mode if mode in REFERENCE_CHECK_MODES else None


def reference_shadow(obj):
    """Capa 1d en modo shadow: valida las referencias normativas de cada frase y devuelve SOLO un registro.

    No recibe ni devuelve la respuesta: lee los campos de 'obj' y nunca los escribe. Cualquier excepcion del modulo
    se registra y no interrumpe la verificacion."""
    t0 = time.perf_counter()
    log = {"mode": "shadow", "sentences": 0, "findings": [], "counts": {}}
    try:
        import reference_integrity as R   # importacion diferida: con la capa desactivada el modulo no se carga
        answer_ids = sorted(set(D.SOR_ID.findall(" ".join(str(obj.get(f) or "") for f in FIELDS))))
        for field in FIELDS:
            for n, unit in enumerate(_units(obj.get(field)), 1):
                log["sentences"] += 1
                for v in R.check(unit, None, answer_ids):
                    log["findings"].append({"field": field, "n": n, **{k: v.get(k) for k in REFERENCE_LOG_FIELDS}})
                    log["counts"][v.get("veredicto")] = log["counts"].get(v.get("veredicto"), 0) + 1
    except Exception as e:  # noqa: BLE001 - la capa shadow nunca interrumpe la verificacion
        log["error"] = re.sub(r"key=[^&\s'\"]+", "key=REDACTED", f"{type(e).__name__}: {e}")[:200]
    log["secs"] = round(time.perf_counter() - t0, 4)
    return log


def verifier_model():
    return os.environ.get("ADA_VERIFIER_MODEL", "").strip() or DEFAULT_VERIFIER_MODEL


def _placeholder(text):
    return str(text or "").strip().strip(".").strip().lower() in PLACEHOLDERS


def _units(text):
    return [] if _placeholder(text) else (D.prune_units(str(text)) or [str(text)])


def _claim_numbers(text, query):
    return D.DecisionIntegrityGate.claim_numbers(_DOC_NAME.sub(" ", D.SOR_ID.sub(" ", text or "")), query)


def _ptext(p):
    return p.get("text_original") or p.get("text") or ""


def expand_short_quote(quote, passage, gate):
    """Cita literal corta -> su renglon completo del pasaje. Devuelve (cita, ampliada?)."""
    qn = D.norm(quote)
    if len(qn.split()) >= D.MIN_QUOTE_WORDS:
        return quote, False
    loc = gate._locate(qn, passage)
    if not loc:
        return quote, False
    text = _ptext(passage)
    a = text.rfind("\n", 0, loc["raw_start"]) + 1
    b = text.find("\n", loc["raw_end"])
    line = text[a:(len(text) if b < 0 else b)].strip()
    if len(D.norm(line).split()) < 2 or not gate._locate(D.norm(line), passage):
        return quote, False
    return line, line != quote.strip()


def _quote_valid(quote, passage, gate):
    """Literal del pasaje entregado y con extension suficiente (>= MIN_QUOTE_WORDS palabras o un renglon completo
    de al menos 2 palabras)."""
    qn = D.norm(quote)
    if not qn or not gate._locate(qn, passage):
        return False
    if len(qn.split()) >= D.MIN_QUOTE_WORDS:
        return True
    lines = {D.norm(x).strip(" .:;") for x in _ptext(passage).split("\n")}
    return len(qn.split()) >= 2 and qn.strip(" .:;") in lines


def _strip_ids(text, pids):
    """Quita de 'text' los identificadores 'pids' y limpia los corchetes o separadores que quedan vacios."""
    for pid in pids:
        text = text.replace(pid, "")
    # Separadores repetidos que deja un identificador intermedio ("[A, , C]" -> "[A, C]"), solo dentro de [] o ().
    text = re.sub(r"[\[(][^\[\]()]*[\])]",
                  lambda m: re.sub(r"([,;/|])(?:\s*[,;/|])+", r"\1", m.group(0)), text)
    text = re.sub(r"([\[(])\s*(?:[,;/|]\s*)+", r"\1", text)
    text = re.sub(r"(?:\s*[,;/|])+\s*([\])])", r"\1", text)
    text = re.sub(r"\s*(?:\[\s*\]|\(\s*\))", "", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def _remove_citations(obj, pids, removed, reason):
    """Retira las frases cuyas UNICAS citas son 'pids'; en las demas solo quita esos identificadores."""
    if not pids:
        return
    for field in FIELDS:
        units = _units(obj.get(field))
        if not units:
            continue
        kept = []
        for u in units:
            ids = set(D.SOR_ID.findall(u))
            if ids and ids <= pids:
                removed.append({"field": field, "sentence": u, "reason": reason})
                continue
            kept.append(_strip_ids(u, ids & pids) if ids & pids else u)
        obj[field] = " ".join(kept).strip()
    obj["citations"] = [c for c in (obj.get("citations") or [])
                        if not (set(D.SOR_ID.findall(json.dumps(c, ensure_ascii=False))) & pids)]


def _exception_candidates(quotes, delivered, gate):
    """Oraciones con marcador de excepcion de la unidad derivada de cada cita (ventana de DIG-09), literales en el
    MISMO pasaje entregado y aun no citadas."""
    out, seen = [], set()
    quoted = [D.norm(q["quote"]) for q in quotes]
    for q in quotes:
        passage = delivered[q["passage_id"]]
        canon = gate._canonical(D.norm(q["quote"]), passage)
        if canon is None:
            continue
        page, text, a, b = canon
        _unit, window = gate._window(page, text, a, b)
        for _s, _e, sent in window:
            s = " ".join(sent.split())
            sn = D.norm(s)
            if (not D.EXCEPTION_MARKER.search(s) or len(sn.split()) < 4 or sn in seen
                    or any(sn[:60] in x or x in sn for x in quoted) or not gate._locate(sn, passage)):
                continue
            seen.add(sn)
            out.append({"passage_id": q["passage_id"], "sentence": s})
            if len(out) >= MAX_EXCEPTIONS:
                return out
    return out


def _parse_json(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None


def _verdict_complete(verdict, n_sentences):
    """El veredicto juzga CADA frase de la respuesta (n = 1..N). Un JSON vacio, de error o parcial no cuenta como
    verificacion: sin este control, una frase sin juicio se conservaria y se emitiria como verificada."""
    items = verdict.get("sentences")
    if not isinstance(items, list):
        return False
    seen = set()
    for x in items:
        try:
            seen.add(int(x.get("n", 0)))
        except (AttributeError, TypeError, ValueError):
            continue
    return set(range(1, n_sentences + 1)) <= seen


def build_prompt(question, passages, quotes, exceptions, sentences):
    return PROMPT.format(
        question=question,
        passages="\n\n".join(f"<<{pid}>>\n{_ptext(p)}" for pid, p in passages.items()),
        quotes="\n".join(f"[{i + 1}] {q['quote']}" for i, q in enumerate(quotes)) or "(none)",
        exceptions="\n".join(f"[{i + 1}] {e['sentence']}" for i, e in enumerate(exceptions)) or "(none)",
        sentences="\n".join(f"[{i + 1}] {s['text']}" for i, s in enumerate(sentences)) or "(none)")


def verify(answer, query, search_query_en, evidence, related, gate, llm_call=None,
           supplementary_texts=(), instruction_text=""):
    """Verifica y corrige 'answer' (JSON del contrato). Devuelve (respuesta_json, registro).

    llm_call(prompt) -> (texto, usage_dict, modelo) o lanza excepcion.
    registro['decision'] es 'PERMITIR' o 'ABSTENER' (compatible con el flujo de ADA); el detalle va en
    registro['verification']."""
    rec = {"version": "V4", "mode": "LLM", "removed": [], "expanded_quotes": [], "added_exceptions": [],
           "negative": False, "verifier": None, "reasons": []}

    def result(decision, ans):
        failed = [] if decision == "PERMITIR" else (rec["reasons"] or ["verificacion_v4"])
        return ans, {"decision": decision, "failed_checks": failed, "verification": rec, "version": "V4"}

    obj = D.parse_answer(answer)
    if obj is None:
        rec["reasons"].append("DIG-00_JSON")
        return result("ABSTENER", answer)
    obj = dict(obj)
    delivered = {p.get("passage_id"): p for p in [*evidence, *related] if p.get("passage_id")}
    negative = str(obj.get("answerability", "")).strip().upper() == "EVIDENCIA_INSUFICIENTE"
    rec["negative"] = negative

    # ---- Capa 1a: citas literales (ampliacion de citas cortas) -------------------------------------------------
    quotes = []
    for q in obj.get("evidence_quotes") or []:
        if not isinstance(q, dict) or q.get("passage_id") not in delivered:
            continue
        text, expanded = expand_short_quote(str(q.get("quote") or ""), delivered[q["passage_id"]], gate)
        if _quote_valid(text, delivered[q["passage_id"]], gate):
            if expanded:
                rec["expanded_quotes"].append({"passage_id": q["passage_id"], "from": q.get("quote"), "to": text})
            quotes.append(dict(q, quote=text))
    # ---- Capa 1b: pasajes citados sin cita valida ---------------------------------------------------------------
    visible = json.dumps({k: obj.get(k) for k in (*FIELDS, "citations")}, ensure_ascii=False)
    cited = set(D.SOR_ID.findall(visible))
    with_quote = {q["passage_id"] for q in quotes}
    _remove_citations(obj, cited - with_quote, rec["removed"], "pasaje citado sin cita literal valida")
    # ---- Capa 1c: cifras afirmadas sin respaldo en los pasajes citados ------------------------------------------
    support_text = " ".join(_ptext(delivered[pid]) for pid in with_quote)
    ok_nums = D.numbers_in(support_text) | D.numbers_in(f"{query} {search_query_en or ''}")
    for field in FIELDS:
        units = _units(obj.get(field))
        if not units:
            continue
        kept = []
        for u in units:
            nums = _claim_numbers(u, query) - ok_nums
            if nums:
                rec["removed"].append({"field": field, "sentence": u, "reason": f"cifras sin respaldo {sorted(nums)}"})
            else:
                kept.append(u)
        obj[field] = " ".join(kept).strip()
    # ---- Capa 1d: referencias normativas (solo registro, ADA_REFERENCE_CHECK=shadow) ----------------------------
    if reference_check_mode() == "shadow":
        rec["references"] = reference_shadow(obj)

    # ---- Capa 2: verificador LLM --------------------------------------------------------------------------------
    sentences = [{"field": f, "text": u} for f in FIELDS for u in _units(obj.get(f))]
    exceptions = _exception_candidates(quotes, delivered, gate) if quotes else []
    passages = {pid: delivered[pid] for pid in dict.fromkeys(q["passage_id"] for q in quotes)}
    verdict = None
    if llm_call is not None and sentences:
        prompt = build_prompt(query, passages, quotes, exceptions, sentences)
        t0 = time.time()
        try:
            text, usage, model = llm_call(prompt)
            verdict = _parse_json(text)
            parsed = verdict is not None
            if parsed and not _verdict_complete(verdict, len(sentences)):
                verdict = None   # veredicto vacio o parcial: modo reducido (decide el DIG completo)
            rec["verifier"] = {"model": model, "usage": usage or {}, "secs": round(time.time() - t0, 2),
                               "parsed": parsed, "complete": verdict is not None}
        except Exception as e:  # noqa: BLE001 - cualquier fallo del proveedor activa el modo degradado
            rec["verifier"] = {"model": None, "usage": {}, "secs": round(time.time() - t0, 2),
                               "error": re.sub(r"key=[^&\s'\"]+", "key=REDACTED", f"{type(e).__name__}: {e}")[:200]}
    answers_question = True
    if verdict is not None:
        qv = {int(x.get("n", 0)): bool(x.get("pertinent")) for x in verdict.get("quotes") or [] if isinstance(x, dict)}
        sv = {int(x.get("n", 0)): x for x in verdict.get("sentences") or [] if isinstance(x, dict)}
        ev = {int(x.get("n", 0)): bool(x.get("relevant")) for x in verdict.get("exceptions") or [] if isinstance(x, dict)}
        answers_question = bool(verdict.get("answers_question", True))
        # Frases sin respaldo (una frase sin veredicto se conserva: solo se retira lo que el verificador rechaza).
        drop = {i for i, s in enumerate(sentences, 1) if i in sv and not sv[i].get("supported", True)}
        for i in sorted(drop):
            rec["removed"].append({"field": sentences[i - 1]["field"], "sentence": sentences[i - 1]["text"],
                                   "reason": "sin respaldo en los pasajes: " + str(sv[i].get("unsupported") or "")[:200]})
        for field in FIELDS:
            kept = [s["text"] for i, s in enumerate(sentences, 1) if s["field"] == field and i not in drop]
            if _units(obj.get(field)):
                obj[field] = " ".join(kept).strip()
        # Citas no pertinentes; los pasajes que se quedan sin cita pertinente dejan de citarse.
        quotes = [q for i, q in enumerate(quotes, 1) if qv.get(i, True)]
        pertinent_pids = {q["passage_id"] for q in quotes}
        _remove_citations(obj, with_quote - pertinent_pids, rec["removed"], "pasaje citado sin cita pertinente")
        # Capa 3: excepciones pertinentes -> se anaden con su cita literal.
        added = [e for i, e in enumerate(exceptions, 1) if ev.get(i)]
        if added:
            extra = " ".join(f"Excepción: «{e['sentence']}» [{e['passage_id']}]." for e in added)
            base = "" if _placeholder(obj.get("conditions_and_exceptions")) else str(obj.get("conditions_and_exceptions"))
            obj["conditions_and_exceptions"] = f"{base} {extra}".strip()
            quotes += [{"passage_id": e["passage_id"], "quote": e["sentence"], "supports": "excepción"} for e in added]
            rec["added_exceptions"] = added
    else:
        # Sin verificador: la pertinencia y el resto de controles los decide el DIG completo (mas abajo).
        rec["mode"] = "REDUCIDA" if (llm_call is None or sentences) else "SIN_CONTENIDO"
        answers_question = bool(quotes) or negative

    for field in FIELDS:
        if not str(obj.get(field) or "").strip():
            obj[field] = "No aplica" if field != "limitations" else "Ninguna"
    obj["evidence_quotes"] = quotes
    remaining_ids = set(D.SOR_ID.findall(json.dumps({k: obj.get(k) for k in FIELDS}, ensure_ascii=False)))
    fixed = json.dumps(obj, ensure_ascii=False)

    # ---- Decision ---------------------------------------------------------------------------------------------
    if _placeholder(obj.get("summary")):
        rec["reasons"].append("sin_respuesta_respaldada")
    if not answers_question:
        rec["reasons"].append("no_responde_la_pregunta")
    if not negative and not (remaining_ids & {q["passage_id"] for q in quotes}):
        rec["reasons"].append("sin_cita_pertinente")
    if negative:
        if _claim_numbers(obj.get("summary") or "", query):
            rec["reasons"].append("respuesta_negativa_con_cifras")
        if verdict is None:
            rec["reasons"].append("respuesta_negativa_sin_verificador")
    hard = gate.evaluate(fixed, query, search_query_en, evidence, related,
                         supplementary_texts=supplementary_texts, instruction_text=instruction_text)
    rec["hard_checks"] = {c["code"]: c["passed"] for c in hard["checks"] if c["code"] in HARD_CHECKS}
    rec["reasons"] += [c for c, ok in rec["hard_checks"].items() if not ok]
    if verdict is None and hard.get("decision") != "PERMITIR":
        # Modo reducido: sin verificacion semantica decide el DIG (sobre la respuesta ya corregida por la capa 1).
        rec["dig_fallback"] = list(hard.get("failed_checks") or [])
        rec["reasons"] += [c for c in rec["dig_fallback"] if c not in rec["reasons"]] or ["DIG"]
    if rec["reasons"]:
        return result("ABSTENER", fixed)
    if negative:
        obj["answerability"] = "RESPALDADA"   # respuesta negativa verificada: se presenta como respuesta
        obj["response_kind"] = "NO_CUBIERTA"
        fixed = json.dumps(obj, ensure_ascii=False)
    return result("PERMITIR", fixed)

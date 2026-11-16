"""Deterministic helpers for ADA evidence/abstention/citation contract tests.

No network and no real LLM: ``StubLLM`` replaces ``ArbitrationDecisionAssistant._call_llm``.

* The translation call and the analysis call are told apart explicitly by the translation
  prompt marker. The translation call returns no text, so ADA uses its deterministic
  dictionary projection for retrieval (the same path as an unavailable generator).
* In the analysis call the stub can only cite identifiers read from the certified primary
  block of the prompt it actually received (``delivered_primary_ids``), so a test can never
  cite something that was not delivered to the model.
* Stub answers carry no normative content: they only cite identifiers. These tests verify
  evidence, abstention and citation contracts; they do not verify semantic entailment.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import decision_integrity as _dig  # noqa: E402

ZERO_USAGE = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
TRANSLATION_MARKER = "official IJF (International Judo Federation) translator"
PRIMARY_BLOCK_START = "CONTEXTO NORMATIVO CERTIFICADO"
PRIMARY_BLOCK_ENDS = ("CONTEXTO DOCUMENTAL COMPLEMENTARIO", "CONTRATO OBLIGATORIO DE RESPUESTA")
SUPPLEMENTARY_BLOCK_START = "CONTEXTO DOCUMENTAL COMPLEMENTARIO"
SOR_ID = re.compile(r"SOR-[A-Za-z0-9]+-[A-Za-z0-9]+-P\d+-S\d+")
ABSTENTION_MARKER = "Abstención Normativa Oficial"


def is_translation_prompt(prompt):
    return TRANSLATION_MARKER in prompt


def primary_block(prompt):
    start = prompt.find(PRIMARY_BLOCK_START)
    if start < 0:
        return ""
    ends = [prompt.find(marker, start) for marker in PRIMARY_BLOCK_ENDS]
    ends = [e for e in ends if e > start]
    return prompt[start:min(ends) if ends else len(prompt)]


def supplementary_block(prompt):
    start = prompt.find(SUPPLEMENTARY_BLOCK_START)
    if start < 0:
        return ""
    end = prompt.find("CONTRATO OBLIGATORIO DE RESPUESTA", start)
    return prompt[start:end if end > start else len(prompt)]


def delivered_primary_ids(prompt):
    """SOR passage IDs present in the certified primary block, in order of appearance."""
    return list(dict.fromkeys(SOR_ID.findall(primary_block(prompt))))


class StubLLM:
    """Callable stand-in for ``_call_llm``.

    ``analysis`` is ``None`` (generator unavailable) or ``callable(prompt, delivered_ids) -> str``.
    ``translation`` is ``None`` (translator unavailable) or the simulated technical-English query.
    """

    def __init__(self, analysis=None, translation=None):
        self.analysis = analysis
        self.translation = translation
        self.translation_prompts = []
        self.analysis_prompts = []

    def __call__(self, prompt):
        if is_translation_prompt(prompt):
            self.translation_prompts.append(prompt)
            # translation=None -> no translator (deterministic dictionary projection is used);
            # a string simulates the translator output (a query, never normative content).
            return self.translation, {"token_usage": dict(ZERO_USAGE)}
        self.analysis_prompts.append(prompt)
        if self.analysis is None:
            return None, {"successful_provider": None, "token_usage": dict(ZERO_USAGE)}
        answer = self.analysis(prompt, delivered_primary_ids(prompt))
        return answer, {"successful_provider": "Stub", "successful_model": "stub", "token_usage": dict(ZERO_USAGE)}


def json_answer(ids, extra_text=""):
    """A structured answer with no normative content that only cites ``ids`` (no literal quotes:
    under the Phase 9 contract it must be rejected by the decision-integrity gate)."""
    body = "Respuesta de prueba. Pasajes citados: " + ", ".join(f"[{i}]" for i in ids) + "." + extra_text
    return json.dumps({
        "summary": body,
        "normative_basis": body,
        "citations": list(ids),
        "conditions_and_exceptions": "No aplica",
        "extended_analysis": "No aplica",
        "limitations": "Ninguna",
    }, ensure_ascii=False)


USER_QUERY = re.compile(r"Consulta del usuario / User query: (.*)")
TECH_QUERY = re.compile(r"Consulta técnica normalizada \(EN[^)]*\): (.*)")


def _query_stems(prompt):
    """Content stems of the user query plus the technical EN projection shown in the prompt."""
    text = " ".join(m.group(1) for m in (USER_QUERY.search(prompt), TECH_QUERY.search(prompt)) if m)
    return _dig.content_stems(text)


def primary_passages(prompt):
    """{passage_id: text} of the certified primary block actually delivered in ``prompt``."""
    out = {}
    for block in primary_block(prompt).split("\n\n---\n\n"):
        m = re.match(r"\s*(?:CONTEXTO NORMATIVO CERTIFICADO[^\n]*\n)?\[(SOR-[^\]]+)\][^\n]*\n(.*)", block, re.DOTALL)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def grounded_quotes(pid, text, query_text, max_related=3):
    """Literal quotes of ``text`` for ``pid``: the sentences sharing most content terms with
    ``query_text`` (up to ``max_related``) plus every sentence carrying an exception marker."""
    qstems = _dig.content_stems(query_text)
    sents = [x for x in _dig.sentences(text) if len(_dig.norm(x).split()) >= _dig.MIN_QUOTE_WORDS]
    if not sents:
        return []
    ranked = sorted(sents, key=lambda x: -len(_dig.content_stems(x) & qstems))
    chosen = [ranked[0]] + [x for x in ranked[1:max_related] if _dig.content_stems(x) & qstems]
    chosen += [x for x in sents if x not in chosen and _dig.EXCEPTION_MARKER.search(x)]
    return [{"passage_id": pid, "quote": x, "supports": "cita de prueba"} for x in chosen]


def cite_best_delivered(prompt, delivered):
    """Contract-compliant stub citing the delivered passage most related to the query."""
    best = best_delivered_passage(prompt)
    return grounded_answer(prompt, [best] if best else delivered[:1])


def grounded_answer(prompt, ids, extra_text="", max_related=3):
    """Contract-compliant stub answer (Phase 9/9.1): cites ``ids`` and, for each, quotes LITERALLY the
    sentences of the delivered passage that share most content terms with the query and its technical
    projection (up to ``max_related``), plus every sentence carrying an exception marker. It carries no
    normative conclusion and does NOT demonstrate entailment: it only exercises the DIG contract."""
    texts = primary_passages(prompt)
    qtext = " ".join(m.group(1) for m in (USER_QUERY.search(prompt), TECH_QUERY.search(prompt)) if m)
    quotes = []
    for pid in ids:
        quotes += grounded_quotes(pid, texts.get(pid, ""), qtext, max_related)
    obj = json.loads(json_answer(ids, extra_text))
    obj.update({"answerability": "RESPALDADA", "evidence_quotes": quotes, "evidence_conflicts": []})
    return json.dumps(obj, ensure_ascii=False)


def best_delivered_passage(prompt):
    """ID of the delivered primary passage whose best sentence shares most content terms with the
    query (simulates a generator that quotes the most related passage; used by evaluators)."""
    texts = primary_passages(prompt)
    qstems = _query_stems(prompt)
    best, score = None, -1
    for pid, text in texts.items():
        for x in _dig.sentences(text):
            sc = len(_dig.content_stems(x) & qstems)
            if sc > score and len(_dig.norm(x).split()) >= _dig.MIN_QUOTE_WORDS:
                best, score = pid, sc
    return best


def answer_citing(select):
    """``select(delivered_ids) -> list of ids`` (or a fixed list) to cite in a contract-compliant answer."""
    def _build(prompt, delivered):
        ids = select(delivered) if callable(select) else list(select)
        return grounded_answer(prompt, ids)
    return _build


def cite_first_delivered(prompt, delivered):
    return grounded_answer(prompt, delivered[:1])


def citation_ids(result):
    return [c.get("passage_id") if isinstance(c, dict) else c
            for c in result.get("structured_answer", {}).get("citations", [])]


def delivered_ids_in_result(result):
    return [e["passage_id"] for e in result.get("evidence", []) + result.get("related_passages", [])]

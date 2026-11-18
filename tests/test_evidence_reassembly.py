"""Reparaciones de la atribucion y re-ensamblado dirigido (evidence_reassembly). Las pruebas usan pasajes del
corpus solo como material: comprueban propiedades GENERALES (literalidad del resultado, no inventar texto, no citar
pasajes ajenos), no respuestas a consultas concretas."""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]

import decision_integrity as D  # noqa: E402
import evidence_reassembly as R  # noqa: E402


@pytest.fixture(scope="module")
def corpus():
    ps = json.load(open(os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json"),
                        encoding="utf-8"))
    return {p["passage_id"]: dict(p, page=p.get("pdf_page_index")) for p in ps}


@pytest.fixture(scope="module")
def gate(corpus):
    return D.DecisionIntegrityGate(list(corpus.values()))


def _ans(pid, quotes, extra_ids=()):
    ids = [pid, *extra_ids]
    return json.dumps({"summary": " ".join(f"Texto [{i}]." for i in ids), "normative_basis": f"[{pid}]",
                       "citations": ids, "answerability": "RESPALDADA",
                       "evidence_quotes": [{"passage_id": q[0], "quote": q[1], "supports": "x"} for q in quotes]},
                      ensure_ascii=False)


def _sentence_pair(text):
    """Dos frases consecutivas del pasaje con >= 8 palabras cada una (material de prueba)."""
    s = [text[a:b] for a, b in D.sentence_spans(text)]
    for x, y in zip(s, s[1:]):
        if len(x.split()) >= 8 and len(y.split()) >= 8 and "\n" not in x[:3]:
            return x, y
    pytest.skip("pasaje sin dos frases largas consecutivas")


def _a_passage(corpus):
    for pid, p in corpus.items():
        t = p.get("text_original") or ""
        if len(t) > 1500 and "page break" not in t.lower():
            return pid, p
    pytest.skip("sin pasaje largo")


def test_ellipsis_quote_becomes_literal_fragments(corpus, gate):
    pid, p = _a_passage(corpus)
    x, y = _sentence_pair(p["text_original"])
    quote = " ".join(x.split()) + " ... " + " ".join(y.split())
    out, rep = R.repair_quotes(_ans(pid, [(pid, quote)]), {pid: p}, gate)
    qs = json.loads(out)["evidence_quotes"]
    assert rep and len(qs) == 2
    assert all(gate._locate(D.norm(q["quote"]), p) is not None for q in qs)


def test_typographic_variant_is_replaced_by_literal_span(corpus, gate):
    pid, p = _a_passage(corpus)
    x, _y = _sentence_pair(p["text_original"])
    words = x.split()
    quote = " ".join(words[:4]) + " • " + " ".join(words[4:])  # vineta ajena al texto
    assert gate._locate(D.norm(quote), p) is None
    out, rep = R.repair_quotes(_ans(pid, [(pid, quote)]), {pid: p}, gate)
    q = json.loads(out)["evidence_quotes"][0]["quote"]
    assert rep and gate._locate(D.norm(q), p) is not None
    assert [w.lower() for w in R._WORDS.findall(q)] == [w.lower() for w in R._WORDS.findall(quote)]


def test_changed_words_are_never_repaired(corpus, gate):
    pid, p = _a_passage(corpus)
    x, _y = _sentence_pair(p["text_original"])
    words = x.split()
    words[len(words) // 2] = "zzzinventado"
    ans = _ans(pid, [(pid, " ".join(words))])
    out, rep = R.repair_quotes(ans, {pid: p}, gate)
    assert rep == [] and out == ans


def test_quote_of_undelivered_passage_is_not_touched(corpus, gate):
    pid, p = _a_passage(corpus)
    x, _y = _sentence_pair(p["text_original"])
    ans = _ans(pid, [(pid, x + " ...")])
    out, rep = R.repair_quotes(ans, {}, gate)
    assert rep == [] and out == ans


def _twins(corpus):
    by = {}
    for pid, p in corpus.items():
        by.setdefault((p["page"], p.get("text_original")), []).append(pid)
    for ids in by.values():
        if len(ids) >= 2:
            return sorted(ids)[:2]
    pytest.skip("sin pasajes gemelos")


def test_twin_identifier_is_mapped_only_with_literal_quotes(corpus):
    a, b = _twins(corpus)
    text = corpus[a]["text_original"]
    x = next(s for s in D.sentences(text) if len(s.split()) >= 8)
    out, ch = R.repair_citation_ids(_ans(b, [(b, x)]), {a: corpus[a]}, corpus)
    assert ch and ch[0]["de"] == b and ch[0]["a"] == a
    assert b not in out and a in out
    # cita que no esta en el texto entregado: no se cambia el identificador
    out2, ch2 = R.repair_citation_ids(_ans(b, [(b, "frase que no existe en ningun pasaje del corpus")]), {a: corpus[a]}, corpus)
    assert ch2 == [] and b in out2


def test_non_twin_identifier_is_never_mapped(corpus):
    a, b = sorted(corpus)[100], sorted(corpus)[200]
    assert corpus[a]["page"] != corpus[b]["page"]
    ans = _ans(b, [])
    out, ch = R.repair_citation_ids(ans, {a: corpus[a]}, corpus)
    assert ch == [] and out == ans


def test_reassembly_targets_only_contiguous_same_section(corpus, gate):
    by_sec = {}
    for pid in corpus:
        by_sec.setdefault(R._section(pid), []).append(pid)
    sec = next(s for s, ids in by_sec.items() if len({R._page(i) for i in ids}) >= 3)
    ids = sorted(by_sec[sec], key=R._page)
    first, mid = ids[0], ids[1]
    far = next(p for p in sorted(corpus, key=R._page) if R._section(p) != sec and abs(R._page(p) - R._page(first)) > 5)
    t = R.reassembly_targets(_ans(first, [], extra_ids=[mid, far]), None, {first: corpus[first]}, corpus, gate)
    got = [x["passage_id"] for x in t]
    assert mid in got and far not in got
    assert len(got) <= R.MAX_TARGETS


def test_flags_off_by_default(monkeypatch):
    for f in ("ADA_CITATION_REPAIR", "ADA_QUOTE_REPAIR", "ADA_TARGETED_REASSEMBLY"):
        monkeypatch.delenv(f, raising=False)
    assert not (R.citation_repair_enabled() or R.quote_repair_enabled() or R.reassembly_enabled())

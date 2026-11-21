"""F3 - Capa 1d de V4 en modo shadow (ADA_REFERENCE_CHECK=shadow): integracion de reference_integrity, sin red.

El verificador LLM es un stub determinista que cuenta sus llamadas. Los pasajes son pasajes REALES del corpus
(P177: Article 18.1.1; P188: Article 18.1.3 final y 18.1.4), porque el modulo valida contra el indice del corpus.
Lo que se demuestra: con el flag desactivado el modulo no se ejecuta; con 'shadow' se ejecuta y registra, y la
respuesta, la decision, el verificador LLM y los controles DIG quedan EXACTAMENTE iguales que sin flag.
"""
import copy
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "tests")]
for _k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY"):
    os.environ[_k] = ""

import answer_verification as V  # noqa: E402
import decision_integrity as D  # noqa: E402
import reference_integrity as R  # noqa: E402

P177 = "SOR-2026-08-P177-S193"   # Article 18.1.1
P188 = "SOR-2026-08-P188-S196"   # Article 18.1.3 (final) y 18.1.4
QUOTE = "Negative positions, against the fighting spirit, will be penalised by shido"
QUERY = "¿Qué se sanciona con shido por falta de combatividad?"


@pytest.fixture(scope="module")
def passages():
    idx = R.default_index()
    return [dict(idx.passages[P177], passage_id=P177), dict(idx.passages[P188], passage_id=P188)]


@pytest.fixture(scope="module")
def gate(passages):
    return D.DecisionIntegrityGate(passages)


def answer(ref="18.1.1"):
    return json.dumps({
        "summary": f"Las posiciones negativas contrarias al espíritu de lucha se sancionan con shido según el "
                   f"Art. {ref} [{P177}].",
        "normative_basis": f"Artículo {ref} [{P177}].",
        "conditions_and_exceptions": "No aplica", "extended_analysis": "No aplica", "limitations": "Ninguna",
        "answerability": "RESPALDADA", "citations": [], "evidence_conflicts": [],
        "evidence_quotes": [{"passage_id": P177, "quote": QUOTE}]}, ensure_ascii=False)


class StubLLM:
    """Verificador determinista: todo respaldado y pertinente (o frases rechazadas por numero). Cuenta llamadas."""

    def __init__(self, reject=()):
        self.calls, self.prompts, self.reject = 0, [], set(reject)

    def __call__(self, prompt):
        self.calls += 1
        self.prompts.append(prompt)
        n_s = prompt.split("ANSWER SENTENCES:")[1].count("\n[") + 1
        n_q = prompt.split("QUOTES:")[1].split("EXCEPTIONS:")[0].count("\n[")
        obj = {"quotes": [{"n": i, "pertinent": True} for i in range(1, n_q + 1)],
               "sentences": [{"n": i, "supported": i not in self.reject, "unsupported": "x"} for i in range(1, n_s + 1)],
               "exceptions": [], "answers_question": True}
        return json.dumps(obj), {"prompt_tokens": 100, "completion_tokens": 20}, "stub-verifier"


def run(gate, passages, ans, monkeypatch, mode, llm=None):
    if mode is None:
        monkeypatch.delenv("ADA_REFERENCE_CHECK", raising=False)
    else:
        monkeypatch.setenv("ADA_REFERENCE_CHECK", mode)
    return V.verify(ans, QUERY, QUERY, passages[:1], passages[1:], gate, llm_call=llm)


def comparable(rec):
    """Registro sin la parte shadow ni los tiempos medidos (lo unico que puede variar entre ejecuciones)."""
    rec = copy.deepcopy(rec)
    rec["verification"].pop("references", None)
    if rec["verification"].get("verifier"):
        rec["verification"]["verifier"].pop("secs", None)
    return rec


@pytest.fixture
def spy(monkeypatch):
    calls = []
    real = R.check

    def wrapped(*a, **k):
        calls.append(a)
        return real(*a, **k)
    monkeypatch.setattr(R, "check", wrapped)
    return calls


def findings(rec):
    return [(f["etiqueta"], f["veredicto"]) for f in rec["verification"]["references"]["findings"]]


# 1 -------------------------------------------------------------------------------------------------------------
def test_1_flag_desactivado_no_ejecuta_el_modulo(gate, passages, monkeypatch, spy):
    out, rec = run(gate, passages, answer("18.1.4"), monkeypatch, None, StubLLM())
    assert spy == [] and "references" not in rec["verification"]


# 2 -------------------------------------------------------------------------------------------------------------
def test_2_shadow_ejecuta_el_modulo(gate, passages, monkeypatch, spy):
    out, rec = run(gate, passages, answer(), monkeypatch, "shadow", StubLLM())
    ref = rec["verification"]["references"]
    assert spy and ref["mode"] == "shadow" and ref["sentences"] == 2 and "error" not in ref


# 3 -------------------------------------------------------------------------------------------------------------
def test_3_referencia_incorrecta_genera_auditoria(gate, passages, monkeypatch):
    out, rec = run(gate, passages, answer("18.1.4"), monkeypatch, "shadow", StubLLM())
    ref = rec["verification"]["references"]
    assert findings(rec) == [("18.1.4", "DISCREPANCIA"), ("18.1.4", "DISCREPANCIA")]
    assert ref["counts"] == {"DISCREPANCIA": 2}
    assert all(f["accion_recomendada"] == "RETIRAR_FRASE" and P188 in f["ubicacion_en_corpus"] for f in ref["findings"])
    _, rec_d = run(gate, passages, answer("19.1.1"), monkeypatch, "shadow", StubLLM())   # mutacion D
    assert {v for _, v in findings(rec_d)} == {"INEXISTENTE"}


# 4 -------------------------------------------------------------------------------------------------------------
def test_4_referencia_correcta_no_genera_discrepancia(gate, passages, monkeypatch):
    out, rec = run(gate, passages, answer("18.1.1"), monkeypatch, "shadow", StubLLM())
    assert findings(rec) == [("18.1.1", "OK"), ("18.1.1", "OK")]
    assert {f["accion_recomendada"] for f in rec["verification"]["references"]["findings"]} == {"NINGUNA"}


# 5 y 6 ---------------------------------------------------------------------------------------------------------
CASES = [("18.1.1", ()), ("18.1.4", ()), ("19.1.1", ()), ("18.1.4", (1,))]


@pytest.mark.parametrize("ref,reject", CASES)
@pytest.mark.parametrize("with_llm", [True, False], ids=["llm", "reducida"])
def test_5_shadow_no_modifica_la_respuesta(gate, passages, monkeypatch, ref, reject, with_llm):
    off, _ = run(gate, passages, answer(ref), monkeypatch, None, StubLLM(reject) if with_llm else None)
    on, rec = run(gate, passages, answer(ref), monkeypatch, "shadow", StubLLM(reject) if with_llm else None)
    assert on == off   # byte a byte
    assert "references" in rec["verification"]


@pytest.mark.parametrize("ref,reject", CASES)
@pytest.mark.parametrize("with_llm", [True, False], ids=["llm", "reducida"])
def test_6_shadow_no_modifica_el_veredicto_v4(gate, passages, monkeypatch, ref, reject, with_llm):
    _, rec_off = run(gate, passages, answer(ref), monkeypatch, None, StubLLM(reject) if with_llm else None)
    _, rec_on = run(gate, passages, answer(ref), monkeypatch, "shadow", StubLLM(reject) if with_llm else None)
    assert rec_on["decision"] == rec_off["decision"] and rec_on["failed_checks"] == rec_off["failed_checks"]
    assert comparable(rec_on) == comparable(rec_off)


def test_6b_referencia_incorrecta_no_cambia_la_decision(gate, passages, monkeypatch):
    """En shadow una DISCREPANCIA solo se registra: la respuesta se sigue permitiendo como sin el flag."""
    _, rec = run(gate, passages, answer("18.1.4"), monkeypatch, "shadow", StubLLM())
    assert rec["decision"] == "PERMITIR" and rec["verification"]["references"]["counts"] == {"DISCREPANCIA": 2}


# 7 -------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("ref", ["18.1.1", "18.1.4"])
def test_7_mismas_llamadas_al_llm(gate, passages, monkeypatch, ref):
    llm_off, llm_on = StubLLM(), StubLLM()
    run(gate, passages, answer(ref), monkeypatch, None, llm_off)
    run(gate, passages, answer(ref), monkeypatch, "shadow", llm_on)
    assert llm_off.calls == llm_on.calls == 1
    assert llm_on.prompts == llm_off.prompts   # el prompt del verificador tampoco cambia


# 8 -------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("dig06", [None, "1"])
def test_8_no_afecta_a_dig06(gate, passages, monkeypatch, dig06):
    if dig06 is None:
        monkeypatch.delenv("DIG06_REFS", raising=False)
    else:
        monkeypatch.setenv("DIG06_REFS", dig06)
    seen = {}
    real = gate.evaluate

    def spy_eval(*a, **k):
        seen.setdefault(os.environ.get("ADA_REFERENCE_CHECK"), []).append((a, k))
        return real(*a, **k)
    monkeypatch.setattr(gate, "evaluate", spy_eval)
    text = f"Art. 18.1.4 [{P177}] 3 shido, 20 segundos"
    before = (D.numbers_in(text), D.numbers_in_v1(text) if hasattr(D, "numbers_in_v1") else None)
    _, rec_off = run(gate, passages, answer("18.1.4"), monkeypatch, None, StubLLM())
    _, rec_on = run(gate, passages, answer("18.1.4"), monkeypatch, "shadow", StubLLM())
    after = (D.numbers_in(text), D.numbers_in_v1(text) if hasattr(D, "numbers_in_v1") else None)
    assert seen[None] == seen["shadow"]                       # el DIG recibe exactamente la misma respuesta
    assert rec_on["verification"]["hard_checks"] == rec_off["verification"]["hard_checks"]
    assert rec_on["verification"]["removed"] == rec_off["verification"]["removed"]   # capa 1c (cifras) igual
    assert before == after                                    # sin estado global alterado en DIG-06


def test_8b_modulo_independiente_de_dig():
    src = open(R.__file__, encoding="utf-8").read()
    assert "decision_integrity" not in src and "dig_number_normalization" not in src


# 9 -------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("fallo", ["check", "indice", "import"])
def test_9_excepciones_del_modulo_no_interrumpen_v4(gate, passages, monkeypatch, fallo):
    off, rec_off = run(gate, passages, answer("18.1.4"), monkeypatch, None, StubLLM())

    def boom(*a, **k):
        raise RuntimeError("fallo simulado key=SECRETO")
    if fallo == "check":
        monkeypatch.setattr(R, "check", boom)
    elif fallo == "indice":
        monkeypatch.setattr(R, "_DEFAULT", None)
        monkeypatch.setattr(R.ReferenceIndex, "load", classmethod(lambda cls, *a, **k: boom()))
    else:
        monkeypatch.setitem(sys.modules, "reference_integrity", None)   # import -> ImportError
    on, rec_on = run(gate, passages, answer("18.1.4"), monkeypatch, "shadow", StubLLM())
    ref = rec_on["verification"]["references"]
    assert on == off and comparable(rec_on) == comparable(rec_off)
    assert ref["error"] and "SECRETO" not in ref["error"] and ref["findings"] == []


# 10 ------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("value,expected", [(None, None), ("", None), ("  ", None), ("shadow", "shadow"),
                                            (" SHADOW ", "shadow"), ("1", None), ("active", None), ("on", None)])
def test_10_configuracion_del_flag(monkeypatch, value, expected):
    if value is None:
        monkeypatch.delenv("ADA_REFERENCE_CHECK", raising=False)
    else:
        monkeypatch.setenv("ADA_REFERENCE_CHECK", value)
    assert V.reference_check_mode() == expected


@pytest.mark.parametrize("value", [None, "1", "active"])
def test_10b_sin_variable_o_valor_no_implementado_no_hay_capa(gate, passages, monkeypatch, spy, value):
    out, rec = run(gate, passages, answer("18.1.4"), monkeypatch, value, StubLLM())
    assert spy == [] and "references" not in rec["verification"]


# Registro sin texto de la respuesta -------------------------------------------------------------------------------
def test_registro_sin_texto_de_frases(gate, passages, monkeypatch):
    ans = answer("18.1.4")
    _, rec = run(gate, passages, ans, monkeypatch, "shadow", StubLLM())
    ref = rec["verification"]["references"]
    assert all(set(f) == {"field", "n", *V.REFERENCE_LOG_FIELDS} for f in ref["findings"])
    dumped = json.dumps(ref, ensure_ascii=False)
    assert "posiciones negativas" not in dumped and QUOTE not in dumped

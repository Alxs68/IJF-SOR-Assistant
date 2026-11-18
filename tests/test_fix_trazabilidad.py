"""Correcciones de la auditoria de trazabilidad RRE -> Gemini -> DIG (todas desactivadas por defecto).

R1  RRE_CHANNEL_CHAMPIONS=1  reserva en el paquete el pasaje que cada canal situa en cabeza.
R2  ADA_TRANSLATE_ANY_LANG=1 traduce toda consulta no inglesa, con traduccion fiel.
R5a DIG_11_SUBORDINATE=1     DIG-11 solo rechaza si ninguna cita es pertinente (DIG-05 fallido).
R5b DIG06_REFS=1             DIG-06 no cuenta referencias documentales ni identificadores de categoria de la consulta.
R6  contrato unificado       criterio explicito de aclaracion y prohibicion de generalizar ausencias.
R8  verify_clarification     solo cuentan como respaldo las citas localizadas literalmente.
Ninguna toca DIG-05 ni DIG-09; con los interruptores apagados el comportamiento es el anterior.
"""
import json
import os
import sys
from contextlib import contextmanager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "tests")]
import decision_integrity as D  # noqa: E402
from test_dig_v3_fixes import BY, GATE, JUDOGI_EN, JUDOGI_PIDS, JUDOGI_Q, ev, fixes, judogi_answer, run  # noqa: E402


@contextmanager
def flags(**kv):
    old = {k: getattr(D, k) for k in kv}
    try:
        for k, v in kv.items():
            setattr(D, k, v)
        with fixes(True):
            yield
    finally:
        for k, v in old.items():
            setattr(D, k, v)


@contextmanager
def env(**kv):
    old = {k: os.environ.get(k) for k in kv}
    try:
        for k, v in kv.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# ---------------- R5a DIG-11 subordinado ----------------
EN_Q = "Which rules must the judogi of veterans conform to, regarding the zzqxv?"   # termino inexistente en el SOR


def test_dig11_blocks_by_default_with_absent_query_term():
    with flags(FIX_DIG11_SUBORDINATE=False):
        res = run(judogi_answer(), EN_Q, EN_Q, JUDOGI_PIDS)
        assert "DIG-11_TERMINOS_DE_CONSULTA_EN_SOR" in res["failed_checks"]


def test_dig11_subordinate_passes_when_quote_is_pertinent():
    with flags(FIX_DIG11_SUBORDINATE=True):
        res = run(judogi_answer(), EN_Q, EN_Q, JUDOGI_PIDS)
        by = {c["code"]: c for c in res["checks"]}
        assert by["DIG-05_PERTINENCIA_MINIMA"]["passed"]
        assert by["DIG-11_TERMINOS_DE_CONSULTA_EN_SOR"]["passed"] and "no bloquea" in by["DIG-11_TERMINOS_DE_CONSULTA_EN_SOR"]["detail"]


def test_dig11_subordinate_still_blocks_without_pertinent_quote():
    q = "What is the zzqxv fee for heel hooks in IBJJF?"
    with flags(FIX_DIG11_SUBORDINATE=True):
        res = run(judogi_answer(), q, q, JUDOGI_PIDS)
        assert "DIG-05_PERTINENCIA_MINIMA" in res["failed_checks"]
        assert "DIG-11_TERMINOS_DE_CONSULTA_EN_SOR" in res["failed_checks"]


# ---------------- R5b DIG-06 referencias e identificadores ----------------
def test_claim_numbers_off_is_numbers_in():
    with flags(FIX_DIG06_REFS=False):
        t = "Art. 6.5, pág. 81 para -66 kg"
        assert D.DecisionIntegrityGate.claim_numbers(t, "-66 kg") == set(D.numbers_in(t))


def test_claim_numbers_excludes_references_and_query_categories_only():
    q = "¿Qué falda debe tener un atleta de -66 kg U18?"
    with flags(FIX_DIG06_REFS=True):
        cn = D.DecisionIntegrityGate.claim_numbers
        assert cn("Art. 6.5 y 6.4.2 [SOR-2026-08-P086-S102]", q) == set()
        assert cn("Págs. 81-82 [SOR‑2026‑08‑P081‑S100]", q) == set()
        assert cn("Para -66 kg y U18 se exigen 20 cm", q) == set(D.numbers_in("20"))
        assert cn("Para -73 kg", q) == set(D.numbers_in("-73 kg"))      # categoria NO escrita por el usuario
        assert cn("5 minutos, Regla 7", q) == set(D.numbers_in("5"))     # cifra normativa: sigue contando


def test_dig06_still_rejects_invented_figure_with_refs_flag():
    a = judogi_answer(" El cinturón debe medir 987 cm (Art. C1.12).")
    with flags(FIX_DIG06_REFS=True):
        res = run(a, JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)
        assert "DIG-06_CIFRAS_RESPALDADAS" in res["failed_checks"] and "987" in json.dumps(res["checks"])


def test_dig06_accepts_article_reference_with_flag():
    a = judogi_answer(" Reglas del SOR, secciones 6.5 y 6.4.2.")
    with flags(FIX_DIG06_REFS=False):
        assert "DIG-06_CIFRAS_RESPALDADAS" in run(a, JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)["failed_checks"]
    with flags(FIX_DIG06_REFS=True):
        assert "DIG-06_CIFRAS_RESPALDADAS" not in run(a, JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)["failed_checks"]


def test_version_marks_flags():
    with flags(FIX_DIG11_SUBORDINATE=True, FIX_DIG06_REFS=True):
        assert D.dig_version().endswith("+D11S+D06R")
    with flags(FIX_DIG11_SUBORDINATE=False, FIX_DIG06_REFS=False):
        assert "D11S" not in D.dig_version() and "D06R" not in D.dig_version()


def test_dig05_dig09_untouched():
    a = judogi_answer()
    with flags(FIX_DIG11_SUBORDINATE=False, FIX_DIG06_REFS=False):
        before = {c["code"]: c["passed"] for c in run(a, JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)["checks"]}
    with flags(FIX_DIG11_SUBORDINATE=True, FIX_DIG06_REFS=True):
        after = {c["code"]: c["passed"] for c in run(a, JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)["checks"]}
    for code in ("DIG-05_PERTINENCIA_MINIMA", "DIG-09_EXCEPCIONES_CITADAS"):
        assert before[code] == after[code]


# ---------------- R8 aclaracion con citas literales ----------------
def test_clarification_figures_need_literal_quote():
    pid = JUDOGI_PIDS[0]
    q = "¿Qué reglas aplican?"
    real = "All athletes MUST compete wearing a white or blue IJF approved judogi and belt"
    fake = "All athletes MUST wear 987 approved belts during the weigh-in procedure"
    base = {"answerability": "REQUIERE_ACLARACION", "summary": "¿Se refiere a los 987 cinturones o al judogi blanco o azul?"}
    passages = {pid: ev([pid])[0]}
    ok_fake = GATE.verify_clarification(json.dumps(dict(base, evidence_quotes=[{"passage_id": pid, "quote": fake}])), q, "", passages)
    assert ok_fake[0] is False          # cita inventada: no respalda la cifra
    only_ids = GATE.verify_clarification(json.dumps(dict(base, evidence_quotes=[{"passage_id": pid, "quote": fake}])), q, "", [pid])
    assert only_ids[0] is False         # sin textos no cuenta ninguna cita
    no_fig = dict(base, summary="¿Se refiere al judogi blanco o azul?", evidence_quotes=[{"passage_id": pid, "quote": real}])
    with flags():
        assert GATE.verify_clarification(json.dumps(no_fig), q, "", passages)[0] is True


# ---------------- R1 campeones de canal (sin modelo denso) ----------------
def _engine():
    from rre_engine import ReasoningRetrievalEngine
    eng = ReasoningRetrievalEngine.__new__(ReasoningRetrievalEngine)
    eng.passages_by_id = {k: {"text_original": f"texto {k}"} for k in "ABCDEFGH"}
    return eng


def test_channel_champions_reserves_dense_and_sparse_heads():
    eng = _engine()
    seeds, info = eng._reserve_channel_champions(["A", "B", "C", "D", "E"], [("G", 3.0)], [("F", 0.62), ("H", 0.40)], 5)
    assert seeds[0] == "A" and "F" in seeds and "G" in seeds and len(seeds) == 5
    assert set(info["added"]) == {"F", "G"} and set(info["replaced"]) == {"D", "E"}
    assert "H" not in seeds          # similitud densa por debajo del umbral


def test_channel_champions_noop_when_present_or_duplicate():
    eng = _engine()
    eng.passages_by_id["F"]["text_original"] = "texto B"          # mismo texto que B
    seeds, info = eng._reserve_channel_champions(["A", "B", "C"], [("A", 2.0)], [("F", 0.9)], 5)
    assert seeds == ["A", "B", "C"] and info["added"] == []


def test_channel_champions_off_by_default():
    import rre_engine
    with env(RRE_CHANNEL_CHAMPIONS=None):
        assert rre_engine.channel_champions_enabled() is False
    with env(RRE_CHANNEL_CHAMPIONS="1"):
        assert rre_engine.channel_champions_enabled() is True


# ---------------- R2 traduccion de cualquier idioma ----------------
def _ada_translator(prompts):
    import ada_assistant as A
    ada = A.ArbitrationDecisionAssistant.__new__(A.ArbitrationDecisionAssistant)
    ada._call_llm = lambda p: (prompts.append(p) or ("translated query", {}))
    return ada


def test_translation_off_keeps_previous_behaviour():
    prompts = []
    ada = _ada_translator(prompts)
    with env(ADA_TRANSLATE_ANY_LANG=None):
        assert ada._translate_to_technical_english("Quantos atletas compõem uma equipa mista?") == "Quantos atletas compõem uma equipa mista?"
        assert ada._translate_to_technical_english("¿Cuántos atletas tiene un equipo?") == "translated query"
    assert "from Spanish into" in prompts[0] and "Faithful translation" not in prompts[0]


def test_translation_any_language_and_faithful():
    prompts = []
    ada = _ada_translator(prompts)
    with env(ADA_TRANSLATE_ANY_LANG="1"):
        assert ada._translate_to_technical_english("Quantos atletas compõem uma equipa mista?") == "translated query"
        assert ada._translate_to_technical_english("How many athletes form a mixed team?") == "How many athletes form a mixed team?"
    assert len(prompts) == 1 and "from its original language" in prompts[0] and "Faithful translation" in prompts[0]


# ---------------- R6 contrato unificado ----------------
def test_unified_contract_has_clarification_criterion_and_absence_rule():
    import ada_assistant as A
    T = A.ArbitrationDecisionAssistant._contract_texts(True)
    assert "NO indica la modalidad, el tipo de evento, la categoría o la situación" in T["answerability"]
    assert "Ausencias: no afirmes que el SOR" in T["rule13"]
    old = A.ArbitrationDecisionAssistant._contract_texts(False)
    assert "Ausencias" not in old["rule13"] and "REQUIERE_ACLARACION" not in old["answerability"]

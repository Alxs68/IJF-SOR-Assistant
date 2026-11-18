"""Correcciones v3 del DIG (FIX_PERTINENCE_HEADING, FIX_HYPHEN_TERMS, FIX_DIG08_INSTRUCTIONS) y modo JSON
del LLM (LLM_JSON_MODE). Todas desactivadas por defecto; con ellas activas no se aceptan cifras,
terminos ni citas que el DIG actual rechaza por falta de respaldo."""
import json
import os
import sys
from contextlib import contextmanager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
import decision_integrity as D  # noqa: E402

CORPUS = os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json")
PS = json.load(open(CORPUS, encoding="utf-8"))
BY = {p["passage_id"]: p for p in PS}
GATE = D.DecisionIntegrityGate(PS)
FLAGS = ("FIX_PERTINENCE_HEADING", "FIX_HYPHEN_TERMS", "FIX_DIG08_INSTRUCTIONS", "FIX_LINEBREAK_HYPHEN",
         "FIX_UNICODE_TYPO", "FIX_DIG08_CROSSLANG")


@contextmanager
def fixes(on=True):
    old = {f: getattr(D, f) for f in FLAGS}
    try:
        for f in FLAGS:
            setattr(D, f, on)
        yield
    finally:
        for f, v in old.items():
            setattr(D, f, v)


def ev(pids):
    return [dict(BY[p], page=BY[p]["pdf_page_index"]) for p in pids]


def run(answer, query, query_en, pids, supp=()):
    return GATE.evaluate(json.dumps(answer, ensure_ascii=False), query, query_en, ev(pids), [], supp)


def failed(res, code):
    return any(c.startswith(code) for c in res["failed_checks"])


JUDOGI_Q = "Que reglas debe cumplir el judogi de los veteranos?"
JUDOGI_EN = "What rules must the judogi of the veterans division comply with?"
JUDOGI_PIDS = ["SOR-2026-08-P105-S131", "SOR-2026-08-P103-S124", "SOR-2026-08-P101-S121"]
JUDOGI_QUOTE = ("All athletes MUST compete wearing a white or blue IJF approved judogi and belt (see IJF website for "
                "the list of suppliers). The judogi and belt must conform to the rules in Appendix C.")


def judogi_answer(summary_extra=""):
    return {"answerability": "RESPALDADA", "evidence_conflicts": [],
            "summary": "Los veteranos deben competir con judogi y cinturon blanco o azul aprobados por la IJF, "
                       "conformes al Apendice C [SOR-2026-08-P105-S131]." + summary_extra,
            "normative_basis": "A1.11 Judogi Rules for Veterans [SOR-2026-08-P105-S131]",
            "conditions_and_exceptions": "No aplica", "extended_analysis": "", "limitations": "",
            "citations": ["SOR-2026-08-P105-S131"],
            "evidence_quotes": [{"passage_id": "SOR-2026-08-P105-S131", "quote": JUDOGI_QUOTE, "supports": "regla"}]}


def test_flags_off_by_default():
    if os.environ.get("DIG_V3") == "1":
        return
    assert not any(getattr(D, f) for f in FLAGS)
    assert "+FIX" not in D.dig_version()


def test_heading_makes_correct_veterans_judogi_answer_pertinent():
    with fixes(False):
        base = run(judogi_answer(), JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)
    with fixes(True):
        new = run(judogi_answer(), JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)
    assert failed(base, "DIG-05")
    assert not failed(new, "DIG-05"), new["failed_checks"]


def test_heading_does_not_rescue_invented_figures():
    with fixes(True):
        res = run(judogi_answer(" El cinturon debe medir 37 cm."), JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)
    assert failed(res, "DIG-06") and res["decision"] == "ABSTENER"


def test_heading_needs_the_quote_to_be_literal():
    a = judogi_answer()
    a["evidence_quotes"][0]["quote"] = "All veterans must compete wearing a red judogi chosen by the coach."
    with fixes(True):
        res = run(a, JUDOGI_Q, JUDOGI_EN, JUDOGI_PIDS)
    assert failed(res, "DIG-03") and res["decision"] == "ABSTENER"


def test_heading_of_unrelated_unit_does_not_count():
    # misma pagina, otra unidad: la cita de pesaje de veteranos no hace pertinente una consulta de tatami
    pid = "SOR-2026-08-P105-S131"
    with fixes(True):
        h = GATE._heading_of_quote(D.norm(JUDOGI_QUOTE), dict(BY[pid], page=105))
    assert h and "Judogi" in h
    assert not GATE.pertinent(D.content_stems(h), D.content_stems("What are the dimensions of the tatami surface?"))


def _hyphen_case(claim):
    quote_pid = "SOR-2026-08-P167-S187"
    quote = ("When an athlete holds with osaekomi-waza the other athlete, who is unable to get away for 20 seconds "
             "after the announcement of")
    return {"answerability": "RESPALDADA", "evidence_conflicts": [], "summary": claim + f" [{quote_pid}]",
            "normative_basis": f"Article 14 [{quote_pid}]", "conditions_and_exceptions": "", "extended_analysis": "",
            "limitations": "", "citations": [quote_pid],
            "evidence_quotes": [{"passage_id": quote_pid, "quote": quote, "supports": "x"}]}, [quote_pid]


def test_hyphen_part_supported_only_by_quoted_hyphenated_term():
    ans, pids = _hyphen_case("Es ippon en ne waza si se inmoviliza 20 segundos con una tecnica waza.")
    q = "Cuando se otorga ippon en suelo?"
    with fixes(False):
        base = run(ans, q, "When is ippon awarded on the ground?", pids)
    with fixes(True):
        new = run(ans, q, "When is ippon awarded on the ground?", pids)
    assert failed(base, "DIG-07")
    assert not failed(new, "DIG-07"), new["checks"]
    ans2, _ = _hyphen_case("Es ippon si se aplica shime-waza durante 20 segundos.")
    with fixes(True):
        res = run(ans2, q, "When is ippon awarded on the ground?", pids)
    # un termino con guion no citado ("shime-waza") sigue sin respaldo si es distintivo
    assert "shime-waza" in GATE.distinctive and failed(res, "DIG-07")


def _dig08(summary, extended, supp, instruction_text="", query="Cuanto dura el combate?"):
    pid = "SOR-2026-08-P152-S179"
    text = BY[pid]["text_original"]
    i = text.find("Article 7")
    quote = " ".join(text[max(0, i - 200):i].split()[-12:]) if i > 0 else " ".join(text.split()[20:32])
    a = {"answerability": "RESPALDADA", "evidence_conflicts": [], "summary": summary + f" [{pid}]",
         "normative_basis": f"Article 6 [{pid}]", "conditions_and_exceptions": "", "extended_analysis": extended,
         "limitations": "", "citations": [pid], "evidence_quotes": [{"passage_id": pid, "quote": quote, "supports": "x"}]}
    return GATE.evaluate(json.dumps(a, ensure_ascii=False), query, "How long does the contest last?",
                         ev([pid]), [], supp, instruction_text=instruction_text)


INSTR = "Reglas Generales y Reglas Especiales: expon cada una con su propia cita."


def test_dig08_instruction_vocabulary_is_not_shadow_footprint():
    supp = ["Estas reglas complementarias del documento tratan otros asuntos administrativos."]
    with fixes(False):
        base = _dig08("Segun las reglas oficiales del combate.", "", supp, INSTR)
    with fixes(True):
        new = _dig08("Segun las reglas oficiales del combate.", "", supp, INSTR)
        D.FIX_DIG08_CROSSLANG = False  # aqui se aisla la correccion por texto de instrucciones
        no_instr = _dig08("Segun las reglas oficiales del combate.", "", supp, "")
    assert failed(base, "DIG-08")
    assert not failed(new, "DIG-08"), new["checks"]
    assert failed(no_instr, "DIG-08")  # sin texto de instrucciones no se excluye nada


def test_dig08_real_shadow_leaks_still_detected_with_fix():
    supp = ["Congelacion decidida: las listas quedaron locked tras Ulaanbaatar; el plazo es de 73 dias."]
    with fixes(True):
        words = _dig08("Segun las reglas oficiales.", "Las listas quedaron locked tras Ulaanbaatar.", supp, INSTR)
        nums = _dig08("Segun las reglas oficiales.", "El plazo es de 73 dias.", supp, INSTR)
    assert failed(words, "DIG-08") and failed(nums, "DIG-08")


def test_json_mode_only_for_analysis_calls(monkeypatch=None):
    sys.path.insert(0, os.path.join(ROOT, "src"))
    import ada_assistant as A
    calls = []

    class Mgr:
        gemini_api_key = None

        def generate_with_fallback(self, prompt, **kw):
            calls.append(kw)
            return "x", {}
    ada = A.ArbitrationDecisionAssistant.__new__(A.ArbitrationDecisionAssistant)
    ada.llm_manager = Mgr()
    old = os.environ.get("LLM_JSON_MODE")
    old_schema = os.environ.pop("LLM_JSON_SCHEMA", None)  # este test cubre solo el modo JSON simple
    try:
        os.environ.pop("LLM_JSON_MODE", None)
        ada._call_llm('{"evidence_quotes": []}')
        os.environ["LLM_JSON_MODE"] = "1"
        ada._call_llm("Translate this query")
        ada._call_llm('Contrato: {"evidence_quotes": []} Respuesta JSON:')
    finally:
        if old is None:
            os.environ.pop("LLM_JSON_MODE", None)
        else:
            os.environ["LLM_JSON_MODE"] = old
        if old_schema is not None:
            os.environ["LLM_JSON_SCHEMA"] = old_schema
    assert calls == [{}, {}, {"json_mode": True}]


def test_provider_payloads_json_mode():
    import llm_provider as L
    import inspect
    assert "json_mode" in inspect.signature(L.GeminiClient.generate).parameters
    assert "json_mode" in inspect.signature(L.GroqClient.generate).parameters
    assert "json_mode" in inspect.signature(L.MultiProviderLLMManager.generate_with_fallback).parameters


TAP = ('b) When an athlete gives up by tapping twice (2) or more with his hand or foot or says \u201cMaitta!\u201d '
       '(I give up!) generally because of osaekomi-waza, shime-waza or kansetsu-waza.')


def test_linebreak_hyphen_quote_is_literal_only_with_fix():
    p = dict(BY["SOR-2026-08-P167-S187"], page=167)
    with fixes(False):
        base = GATE._locate(D.norm(TAP), p)
    with fixes(True):
        new = GATE._locate(D.norm(TAP), p)
        altered = GATE._locate(D.norm(TAP.replace("kansetsu-waza", "kansetsu-wazas")), p)
        changed = GATE._locate(D.norm(TAP.replace("twice (2)", "three times (3)")), p)
    assert base is None and new is not None
    assert altered is None and changed is None

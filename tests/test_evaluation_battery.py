"""
Comprehensive Evaluation Battery for IJF SOR Assistant (diagnostic, contract-based)
==================================================================================
Covers the 10 core dimensions defined in the Plan Rector, with the original questions:
1. Direct factual queries (e.g. tatami dimensions)
2. Complex refereeing scenarios (e.g. osaekomi beyond safety boundary)
3. Cadets vs Adults rules (head use when throwing in cadets)
4. Spanish language queries (diacritics, ñ, technical terms)
5. Japanese terminology (osaekomi, toketa)
6. Ambiguous / underspecified queries (no false assumptions)
7. Information insufficiency / out-of-domain (strict abstention)
8. Regulatory exceptions (e.g. Art. 14.2 bridge exception landing on Tori's body)
9. Multi-article cross-referencing (rules across different pages/sections)
10. Language consistency (English query)

What is evaluated, separately (no real LLM; ``StubLLM`` from tests/_ada_contract_helpers.py):
* Retrieval and pertinence: whether the passages the original battery targeted (pages/articles)
  are among the certified evidence delivered for each question. Targets are locators taken from
  the original battery, never normative answers.
* Abstention without LLM (option A): always ABSTAIN, no citations; classified as correct
  (insufficiency, pertinent evidence kept) or incorrect (retrieval failure / OOD rejection).
* Simulated generator: SUCCESS only by citing a delivered primary passage; classified as
  supported by pertinent evidence or as SUCCESS with irrelevant/insufficient evidence.
* Citation integrity: every citation belongs to the delivered evidence.

A valid citation is never treated as proof of entailment: "supported" here only means the cited
passage is one of the passages the question targets.

Layers:
* Contract tests (must always pass): offline abstention, citation integrity, OOD handling.
* Quality tests (fail when retrieval/ranking fails): pertinence of delivered evidence and of the
  top-ranked passage a generator would cite. Failures are real findings, not test errors.
* ``test_zz_evaluation_metrics_report``: prints per-case classification and metrics (run with -s).
"""

import functools
import os
import sys
from dataclasses import dataclass, field
from unittest.mock import patch

import pytest

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from ada_assistant import ArbitrationDecisionAssistant
from llm_provider import MultiProviderLLMManager
from tests._ada_contract_helpers import (
    StubLLM, cite_first_delivered, citation_ids, delivered_primary_ids, ABSTENTION_MARKER,
)


@dataclass(frozen=True)
class Case:
    cid: str
    dimension: str
    query: str
    kind: str                      # "answerable" | "underspecified" | "ood"
    pages: tuple = ()              # pertinence targets (locators from the original battery)
    articles: tuple = ()           # lower-case substrings of article_id
    min_pertinent: int = 1
    language: str = None
    translation: str = None


CASES = [
    Case("D01", "Direct factual", "¿Cuáles son las dimensiones del tatami de competición?",
         "answerable", pages=(96,), articles=("8.7",),
         translation="What are the official contest area and safety area measurements of the competition tatami?"),
    Case("D02", "Complex scenario", "Durante un combate, se aplica osaekomi-waza y la acción continúa desplazándose hasta sobrepasar completamente el área de seguridad. ¿Qué debe señalar el árbitro?",
         "answerable", pages=(174,), articles=("article 17",)),
    Case("D03", "Cadets vs adults", "En un combate de cadetes (17 años), Tori intenta una proyección y en la acción apoya la cabeza en el tatami de forma voluntaria. ¿Qué sanción corresponde y qué artículo lo regula?",
         "answerable", pages=(188,), articles=("18.1.4",)),
    Case("D04", "Spanish diacritics", "¿Qué sanción se aplica a un judoka de 15 años en categoría cadete si usa la cabeza para lanzar?",
         "answerable", pages=(188,), articles=("18.1.4",),
         translation="What penalty applies to a 15-year-old judoka in cadet category if they use the head to throw?"),
    Case("D05", "Japanese terminology", "¿Cuál es la definición reglamentaria de osaekomi-waza y en qué condiciones se anuncia Osaekomi y Toketa?",
         "answerable", pages=(173, 174), articles=("article 17",)),
    Case("D06", "Underspecified", "El judoka cometió una falta con el agarre.", "underspecified"),
    Case("D07", "Out of domain", "reglas de fuera de juego en baloncesto nba y formula 1", "ood"),
    Case("D08", "Regulatory exception", "Si Uke hace un puente voluntario al caer de una proyeccion pero aterriza sobre el cuerpo de Tori sin tocar el tatami con la cabeza, ¿se otorga Ippon?",
         "answerable", pages=(166, 167), articles=("article 14",)),
    Case("D09", "Multi-article", "Procedimiento de control de judogi en relacion a las medidas de la manga con sokuteiki y colores autorizados.",
         "answerable", articles=("c1",), min_pertinent=2),
    Case("D10", "English query", "What are the rules regarding judogi colours in official IJF competitions?",
         "answerable", pages=(124,), articles=("c1.9",), language="en"),
]
ANSWERABLE = [c for c in CASES if c.kind == "answerable"]


def _is_pertinent(case, passage):
    article = str(passage.get("article_id", "")).lower()
    return passage.get("page") in case.pages or any(a in article for a in case.articles)


@dataclass
class CaseRun:
    case: Case
    projection: str = ""
    rre_status: str = ""
    rre_reason: str = None
    offline: dict = field(default_factory=dict)
    generator: dict = field(default_factory=dict)
    generator_prompts: list = field(default_factory=list)
    delivered: list = field(default_factory=list)        # passages kept/delivered (offline run)
    pertinent_ids: list = field(default_factory=list)

    @property
    def generator_delivered_ids(self):
        return delivered_primary_ids(self.generator_prompts[0]) if self.generator_prompts else []

    def classify_offline(self):
        c = self.case
        if c.kind == "ood":
            ok = self.offline["status"] == "ABSTAIN" and not self.delivered
            return "ABSTAIN correcto (fuera de dominio)" if ok else "ERROR: consulta OOD admitida"
        if self.offline["status"] != "ABSTAIN":
            return "ERROR: SUCCESS sin LLM"
        if not self.delivered:
            why = "rechazo OOD" if self.rre_reason == "OUT_OF_DOMAIN" else f"RRE {self.rre_status}/{self.rre_reason}"
            return f"ABSTAIN incorrecto: fallo de recuperación ({why})"
        if c.kind == "underspecified":
            return "ABSTAIN correcto por insuficiencia (consulta indeterminada)"
        if len(self.pertinent_ids) < c.min_pertinent:
            return "ABSTAIN con evidencia incorrecta o insuficiente"
        return "ABSTAIN correcto por insuficiencia (sin verificador; evidencia pertinente conservada)"

    def classify_generator(self):
        if not self.generator_prompts:
            return "ABSTAIN (no se llegó al generador)"
        if self.generator["status"] != "SUCCESS":
            return "ABSTAIN tras generador"
        if self.case.kind != "answerable":
            return "SUCCESS sin objetivo de pertinencia definido"
        cited = citation_ids(self.generator)
        if cited and all(pid in self.pertinent_ids for pid in cited):
            return "SUCCESS respaldado por evidencia pertinente (cita válida; no prueba entailment)"
        return "SUCCESS con evidencia irrelevante o insuficiente"


@pytest.fixture(scope="module")
def ada():
    return ArbitrationDecisionAssistant(llm_manager=MultiProviderLLMManager(gemini_api_key=None, groq_api_key=None))


@pytest.fixture(scope="module")
def runs(ada):
    @functools.lru_cache(maxsize=None)
    def _run(cid):
        case = next(c for c in CASES if c.cid == cid)
        run = CaseRun(case)
        with patch.object(ada, "_call_llm", StubLLM()):
            run.projection = ada._translate_to_technical_english(case.query)
            rre_res = ada.rre.retrieve(run.projection, top_k=5)
            run.offline = ada.analyze_situation(case.query, language=case.language)
        run.rre_status, run.rre_reason = rre_res.get("status"), rre_res.get("reason")
        run.delivered = run.offline.get("evidence", []) + run.offline.get("related_passages", [])
        run.pertinent_ids = [p["passage_id"] for p in run.delivered if _is_pertinent(case, p)]
        stub = StubLLM(cite_first_delivered, translation=case.translation)
        with patch.object(ada, "_call_llm", stub):
            run.generator = ada.analyze_situation(case.query, language=case.language)
        run.generator_prompts = stub.analysis_prompts
        return run
    return _run


# ---------------------------------------------------------------- contract tests (must pass)
@pytest.mark.parametrize("case", CASES, ids=[c.cid for c in CASES])
def test_offline_abstention_contract(runs, case):
    """Without LLM: always ABSTAIN with the abstention message and no citations."""
    run = runs(case.cid)
    assert run.offline["status"] == "ABSTAIN", run.classify_offline()
    assert run.offline["structured_answer"]["citations"] == []
    assert ABSTENTION_MARKER in run.offline["structured_answer"]["summary"]


def test_out_of_domain_strict_abstention(runs):
    """D07: rejected with no evidence and the generator is never reached."""
    run = runs("D07")
    assert run.offline["status"] == "ABSTAIN" and run.offline["evidence"] == []
    assert run.generator["status"] == "ABSTAIN" and run.generator_prompts == []
    assert citation_ids(run.generator) == []


@pytest.mark.parametrize("case", CASES, ids=[c.cid for c in CASES])
def test_generator_citation_integrity(runs, case):
    """Simulated generator: SUCCESS only when citing delivered primary passages; nothing else cited."""
    run = runs(case.cid)
    if not run.generator_prompts:
        assert run.generator["status"] == "ABSTAIN"
        assert citation_ids(run.generator) == []
        return
    delivered = run.generator_delivered_ids
    assert delivered, "analysis prompt reached without certified primary evidence"
    # Fase 9.1: SUCCESS solo con autorizacion del control de integridad; si no, ABSTAIN sin citas.
    di = run.generator.get("decision_integrity") or {}
    if run.generator["status"] != "SUCCESS":
        assert di.get("decision") == "ABSTENER" and di.get("failed_checks")
        assert citation_ids(run.generator) == []
        return
    assert di.get("decision") == "PERMITIR"
    assert citation_ids(run.generator) == delivered[:1]
    assert set(citation_ids(run.generator)) <= {p["passage_id"] for p in run.generator["evidence"] + run.generator["related_passages"]}


# ---------------------------------------------------------------- quality tests (real findings)
@pytest.mark.parametrize("case", ANSWERABLE, ids=[c.cid for c in ANSWERABLE])
def test_retrieval_delivers_pertinent_evidence(runs, case):
    """The passages the question targets are retrieved and kept as certified evidence."""
    run = runs(case.cid)
    assert len(run.pertinent_ids) >= case.min_pertinent, (
        f"{case.cid} {run.classify_offline()} | projection={run.projection!r} | "
        f"delivered={[p['passage_id'] for p in run.delivered]}"
    )


@pytest.mark.parametrize("case", ANSWERABLE, ids=[c.cid for c in ANSWERABLE])
def test_generator_success_is_backed_by_pertinent_evidence(runs, case):
    """A generator citing the top-ranked delivered passage must cite a pertinent one; otherwise the
    SUCCESS would rest on irrelevant or insufficient evidence (detected here, not by the validator)."""
    run = runs(case.cid)
    assert run.classify_generator().startswith("SUCCESS respaldado"), (
        f"{case.cid} {run.classify_generator()} | cited={citation_ids(run.generator)} | "
        f"pertinent={run.pertinent_ids} | offline={run.classify_offline()}"
    )


# ---------------------------------------------------------------- metrics report
def test_zz_evaluation_metrics_report(runs):
    """Prints per-case classification and metrics. Asserts only that every case was evaluated."""
    all_runs = [runs(c.cid) for c in CASES]
    answerable = [r for r in all_runs if r.case.kind == "answerable"]
    retrieved = [r for r in answerable if r.delivered]
    pertinent = [r for r in answerable if len(r.pertinent_ids) >= r.case.min_pertinent]
    ood_rejected_valid = [r.case.cid for r in all_runs if r.case.kind != "ood" and r.rre_reason == "OUT_OF_DOMAIN"]
    wrong_evidence = [r.case.cid for r in answerable if r.delivered and len(r.pertinent_ids) < r.case.min_pertinent]
    supported = [r for r in answerable if r.classify_generator().startswith("SUCCESS respaldado")]
    irrelevant = [r for r in answerable if r.classify_generator() == "SUCCESS con evidencia irrelevante o insuficiente"]
    integrity_violations = [
        r.case.cid for r in all_runs
        if not set(citation_ids(r.generator)) <= {p["passage_id"] for p in r.generator["evidence"] + r.generator["related_passages"]}
    ]

    lines = ["", "=== EVALUATION BATTERY — per case ==="]
    for r in all_runs:
        lines.append(
            f"{r.case.cid} [{r.case.dimension}] RRE={r.rre_status}/{r.rre_reason} "
            f"delivered={len(r.delivered)} pertinent={len(r.pertinent_ids)} | "
            f"sin LLM: {r.classify_offline()} | generador: {r.classify_generator()}"
        )
        lines.append(f"     proyección: {r.projection!r}")
    n = len(answerable)
    lines += [
        "=== METRICS ===",
        f"Recuperación (preguntas respondibles con evidencia entregada): {len(retrieved)}/{n}",
        f"Pertinencia (con pasajes objetivo entregados): {len(pertinent)}/{n}",
        f"Abstención sin LLM: {sum(r.offline['status'] == 'ABSTAIN' for r in all_runs)}/{len(all_runs)}",
        f"ABSTAIN correcto por insuficiencia: {sum(r.classify_offline().startswith('ABSTAIN correcto') for r in all_runs)}",
        f"ABSTAIN incorrecto por fallo de recuperación: {sum(r.classify_offline().startswith('ABSTAIN incorrecto') for r in all_runs)}",
        f"Preguntas válidas rechazadas por OOD: {ood_rejected_valid or 'ninguna'}",
        f"Preguntas con evidencia incorrecta o insuficiente: {wrong_evidence or 'ninguna'}",
        f"Generador: SUCCESS respaldado {len(supported)}/{n}; SUCCESS con evidencia irrelevante {len(irrelevant)}/{n}",
        f"Violaciones de integridad de citas: {integrity_violations or 'ninguna'}",
        "Nota: una cita válida no demuestra entailment semántico.",
    ]
    print("\n".join(lines))
    assert len(all_runs) == len(CASES)

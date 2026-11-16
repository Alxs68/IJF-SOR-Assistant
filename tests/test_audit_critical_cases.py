import sys
import os
from types import SimpleNamespace
import pytest

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("src"))

from src.ada_assistant import ArbitrationDecisionAssistant
from src.response_structurer import build_deterministic_structured_answer
from unittest.mock import patch
from tests._ada_contract_helpers import (
    StubLLM, answer_citing, cite_first_delivered, cite_best_delivered, citation_ids,
    delivered_ids_in_result, delivered_primary_ids, ABSTENTION_MARKER, TRANSLATION_MARKER, json_answer, primary_block, supplementary_block,
)


@pytest.fixture(scope="module")
def ada():
    return ArbitrationDecisionAssistant()


_CRITICAL_QUERIES = [
    ("Q03", "Si uke es inmovilizado durante 14 segundos en osaekomi que puntuacion corresponde"),
    ("Q05", "Puede tori continuar con un ataque en ne-waza si la accion se inicio dentro y uke sale fuera del tatami"),
    ("Q09", "En cadetes si un competidor se desmaya por estrangulacion puede continuar en la repesca"),
    ("Q13", "existe la puntuacion de yuko en judo actualmente en la temporada 2026"),
]

# Terms carried by the removed hard-coded Policy 10 instructions (AUD-01). The policy section of
# the analysis prompt must not contain them; the user query and certified passages may.
_REMOVED_POLICY_TERMS = ("14 segundos", "yuko", "repesca", "repechage", "conocimiento",
                         "consciousness", "p199", "p151", "art. 5", "art. 7", "art. 15")


def _policy_section(prompt):
    return prompt[prompt.index("POLÍTICA TRANSVERSAL"):prompt.index("Consulta del usuario")].lower()


@pytest.mark.parametrize("qid,query", _CRITICAL_QUERIES)
def test_critical_query_without_generator_abstains(ada, qid, query):
    """Q03/Q05/Q09/Q13 without a generator: ABSTAIN, no citations, no conclusion; evidence kept."""
    with patch.object(ada, "_call_llm", StubLLM()):
        res = ada.analyze_situation(query, top_k=5)
    assert res["status"] == "ABSTAIN", qid
    assert citation_ids(res) == [], qid
    assert ABSTENTION_MARKER in res["structured_answer"]["summary"], qid


@pytest.mark.parametrize("qid,query", _CRITICAL_QUERIES)
def test_critical_query_with_generator_cites_only_delivered_primary(ada, qid, query):
    """Q03/Q05/Q09/Q13 with a stub generator: the prompt policy carries no Q-specific conclusion and
    the answer can only succeed by citing a certified primary passage actually delivered."""
    stub = StubLLM(cite_first_delivered)
    with patch.object(ada, "_call_llm", stub):
        res = ada.analyze_situation(query, top_k=5)
    if not stub.analysis_prompts:
        # Retrieval/bundle abstained before the generator: nothing may be cited.
        assert res["status"] == "ABSTAIN", qid
        assert citation_ids(res) == [], qid
        return
    prompt = stub.analysis_prompts[0]
    assert [term for term in _REMOVED_POLICY_TERMS if term in _policy_section(prompt)] == [], qid
    delivered = delivered_primary_ids(prompt)
    assert delivered, qid
    # Fase 9.1: citar el primer pasaje entregado ya no basta (era la vulnerabilidad de la sonda B).
    # SUCCESS solo si el control de integridad lo permite; si no, ABSTAIN sin citas y con motivo.
    di = res.get("decision_integrity") or {}
    if res["status"] == "SUCCESS":
        assert di.get("decision") == "PERMITIR", qid
        assert citation_ids(res) == delivered[:1], qid
    else:
        assert di.get("decision") == "ABSTENER" and di.get("failed_checks"), qid
        assert citation_ids(res) == [], qid


@pytest.mark.parametrize("qid,query", _CRITICAL_QUERIES)
def test_critical_query_citing_most_related_delivered_passage(ada, qid, query):
    """Fase 9.1: un generador conforme que cita el pasaje entregado mas afin a la consulta, con citas
    literales, solo puede citar evidencia primaria entregada; si DIG lo permite queda SUCCESS etiquetado
    sin entailment. (Mock: no prueba la correccion normativa.)"""
    stub = StubLLM(cite_best_delivered)
    with patch.object(ada, "_call_llm", stub):
        res = ada.analyze_situation(query, top_k=5)
    if not stub.analysis_prompts:
        assert res["status"] == "ABSTAIN", qid
        return
    delivered = delivered_primary_ids(stub.analysis_prompts[0])
    assert set(citation_ids(res)) <= set(delivered), qid
    if res["status"] == "SUCCESS":
        assert res["decision_integrity"]["levels"]["D_respaldo_efectivo"].startswith("NO_VERIFICADO"), qid
        assert "sin entailment" in res["mode"], qid







def test_uncertified_sidecar_is_removed_before_reasoning_context():
    """Retrieved sidecar material is only usable when present in the certified lane."""
    bundle = SimpleNamespace(
        primary_normative_evidence=[SimpleNamespace(evidence_id="SOR-2026-08-P151-S178")],
        interpretive_evidence=[SimpleNamespace(evidence_id="CHK-ALLOWED-001")],
    )
    evidence, related, supplementary = ArbitrationDecisionAssistant._filter_certified_evidence(
        [{"passage_id": "SOR-2026-08-P151-S178"}, {"passage_id": "SOR-2026-08-P999-S999"}],
        [{"passage_id": "SOR-2026-08-P999-S999"}],
        [{"chunk_id": "CHK-ALLOWED-001"}, {"chunk_id": "CHK-REJECTED-001"}],
        bundle,
    )

    assert [item["passage_id"] for item in evidence] == ["SOR-2026-08-P151-S178"]
    assert related == []
    assert [item["chunk_id"] for item in supplementary] == ["CHK-ALLOWED-001"]


def test_deterministic_fallback_does_not_invent_shime_waza_cadet_conclusion():
    """A query alone must not trigger the former hard-coded medical conclusion."""
    answer = build_deterministic_structured_answer(
        query="Un cadete inconsciente tras shime-waza puede disputar el repechage?",
        evidence=[{
            "passage_id": "SOR-2026-08-P188-S196",
            "article_id": "Article 18.1.4",
            "page": 188,
            "title": "Cadet penalties",
            "text_original": "Article 18.1.4\nCadet competition penalties are listed in this section.",
        }],
        related=[],
        version_label="14 August 2026 (Official)",
    )

    assert "no puede continuar" not in answer.summary.lower()
    assert "repesca" not in answer.summary.lower()


def test_ada_abstains_when_retrieved_evidence_is_not_certified_sufficient():
    """A non-empty RRE result cannot bypass an insufficient EvidenceBundle."""
    ada = ArbitrationDecisionAssistant.__new__(ArbitrationDecisionAssistant)
    ada.config = {"version_label": "14 August 2026 (Official)"}
    ada._translate_to_technical_english = lambda query: f"{query} {_STATUS_QUERY_EN}"
    ada.rre = SimpleNamespace(
        retrieve=lambda *args, **kwargs: {
            "status": "SUCCESS",
            "evidence": [{
                "passage_id": "SOR-2026-08-P175-S191",
                "text_original": "Unrelated penalty text.",
                "score": 0.9,
                "article_id": "Article 18",
                "page": 175,
                "title": "Penalties",
                "source_url": "https://example.invalid/sor.pdf#page=175",
            }],
            "related_passages": [],
            "operating_mode": "HYBRID",
            "source_sha256_verified": True,
        },
        retrieve_supplementary=lambda *args, **kwargs: [],
    )
    ada.doc_validator = SimpleNamespace(
        build_certified_bundle=lambda **kwargs: SimpleNamespace(
            abstention_required=True,
            is_sufficient_for_decision=False,
            abstention_reason="Evidencia primaria insuficiente para la consulta.",
            model_dump=lambda: {"is_sufficient_for_decision": False},
        )
    )

    result = ada.analyze_situation("Consulta normativa sin respaldo sustantivo")

    assert result["status"] == "ABSTAIN"
    assert result["evidence"] == []
    assert result["structured_answer"]["citations"] == []



# ---------------------------------------------------------------------------
# AUD-02: deterministic fallback and query-expansion contracts (no LLM calls)
# ---------------------------------------------------------------------------
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Outcome vocabulary: sanctions, scores, results, numeric thresholds and article numbers.
_OUTCOME = re.compile(
    r"hansoku|shido|ippon|waza-ari|wazaari|yuko|fusen-gachi|kiken|no score"
    r"|\b\d+\s*(?:%|s\b|sec|second|segundo|m\b|cm|min)|\d+-second|article\s*\d|\ba\d\.\d",
    re.IGNORECASE,
)
# Term-to-term equivalences whose key already names the outcome term itself.
_TERM_KEYS = ("fusen",)


def _literal_dict_pairs(rel_path, name):
    tree = ast.parse((ROOT / rel_path).read_text(encoding="utf-8"))
    pairs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            names = {getattr(t, "id", getattr(t, "attr", None)) for t in node.targets}
            if name in names:
                pairs.extend(
                    (ast.literal_eval(k), ast.literal_eval(v))
                    for k, v in zip(node.value.keys, node.value.values)
                )
    return pairs


@pytest.mark.parametrize("rel_path,name", [
    ("src/rre_engine.py", "SPANISH_TO_ENGLISH_SYNONYMS"),
    ("src/response_structurer.py", "SYNONYM_EXPANSIONS"),
])
def test_query_expansion_does_not_inject_normative_outcomes(rel_path, name):
    """Expansions may translate terms, but must not attach sanctions, scores or values to situations."""
    pairs = _literal_dict_pairs(rel_path, name)
    assert pairs, f"{name} not found in {rel_path}"
    offenders = []
    for key, value in pairs:
        if str(key).startswith(_TERM_KEYS):
            continue
        text = " ".join(value) if isinstance(value, list) else str(value)
        if _OUTCOME.search(text):
            offenders.append((key, text))
    assert offenders == [], f"Expansion entries anticipate normative outcomes: {offenders}"


def test_translation_glossary_does_not_attach_outcomes_to_situations():
    """The translation prompt glossary must map terminology only."""
    ada = ArbitrationDecisionAssistant.__new__(ArbitrationDecisionAssistant)
    captured = {}

    def fake_llm(prompt):
        captured["prompt"] = prompt
        return ("cadet reverse seoi-nage head defence", {})

    ada._call_llm = fake_llm
    ada._translate_to_technical_english("cadetes reverse seoi-nage y defensa con la cabeza")

    glossary = [line for line in captured["prompt"].splitlines() if "->" in line]
    assert glossary, "Translation glossary not found in prompt"
    offenders = [line for line in glossary if _OUTCOME.search(line.split("->", 1)[1])]
    assert offenders == [], f"Glossary attaches outcomes to situations: {offenders}"


def _passage(pid, article, page, title, text):
    return {
        "passage_id": pid, "article_id": article, "page": page, "title": title,
        "text_original": text, "source_url": "https://example.invalid/sor.pdf", "relation": "test",
    }


@pytest.mark.parametrize("query,passage,forbidden", [
    (
        "cual es el tiempo de tolerancia para presentarse en el tatami",
        _passage("SOR-TEST-P195-S001", "19.1", 195, "Default",
                 "Article 19.1\nThe athletes must be ready at the edge of the contest area when called."),
        ["30", "fusen", "treinta"],
    ),
    (
        "cuales son los colores autorizados del judogi",
        _passage("SOR-TEST-P124-S001", "C1.9", 124, "Commercial markings",
                 "C1.9 Commercial Markings\nAdvertising on the judogi is regulated by the IJF marketing rules."),
        ["blanco", "white", "azul", "blue", "pantone", "reversible"],
    ),
    (
        "puede continuar en la competicion despues de head diving",
        _passage("SOR-TEST-P190-S001", "18.2.1", 190, "Dangerous actions",
                 "Article 18.2.1\nThe following list describes actions examined in this section."),
        ["puede continuar", "hansoku", "sí puede"],
    ),
    (
        "dedos entrelazados en la manga",
        _passage("SOR-TEST-P185-S001", "18.1.2", 185, "Grips",
                 "12. Fingers interlocked inside the opponent's sleeve during kumi-kata."),
        ["shido", "penalised"],
    ),
])
def test_fallback_answer_only_restates_rector_passage(query, passage, forbidden):
    """Summary and analysis come from the rector passage; no conclusion is added from the query."""
    answer = build_deterministic_structured_answer(
        query=query, evidence=[passage], related=[], version_label="14 August 2026 (Official)"
    )
    produced = " ".join([answer.summary, answer.extended_analysis, answer.conditions_and_exceptions]).lower()
    assert passage["passage_id"] in answer.summary
    assert answer.citations == [passage["passage_id"]]
    for token in forbidden:
        assert token not in produced, f"Fallback introduced '{token}' not present in the rector passage"


def test_fallback_without_evidence_marks_sufficiency_not_established():
    answer = build_deterministic_structured_answer(
        query="consulta sin evidencia", evidence=[], related=[], version_label="14 August 2026 (Official)"
    )
    assert answer.citations == []
    assert answer.sufficiency_established is False



# ---------------------------------------------------------------------------
# AUD-03: status contract (no real LLM calls; the generator is a stub)
# Citation validation checks identifiers/articles/codes against certified evidence.
# It is not, and these tests do not claim it is, a semantic entailment check.
# ---------------------------------------------------------------------------
import json

_SOR_PID = "SOR-2026-08-P195-S203"
_STATUS_QUERY = "que ocurre si un atleta no se presenta al combate"


def _real_text(pid):
    """Real certified text of ``pid`` (Phase 9: the decision-integrity gate verifies literal quotes
    against the delivered text and the derived units built from the same text)."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "processed", "rebuild_2026_08_corrected", "passages_candidate.json")
    with open(path, encoding="utf-8") as fh:
        return next(p["text_original"] for p in json.load(fh) if p["passage_id"] == pid)


# Simulated technical-English projection for the stubbed ADA (a query, never normative content).
_STATUS_QUERY_EN = "athlete does not appear for the contest"


def _grounded_fields(pid, text, query):
    """Phase 9 contract fields for a stub answer citing ``pid``: literal quotes only (best sentence
    by query-term overlap + sentences with exception markers). No entailment is implied."""
    import decision_integrity as dig
    sents = [x for x in dig.sentences(text) if len(dig.norm(x).split()) >= dig.MIN_QUOTE_WORDS]
    qs = dig.content_stems(query)
    best = max(sents, key=lambda x: len(dig.content_stems(x) & qs))
    quotes = [{"passage_id": pid, "quote": best}] + [
        {"passage_id": pid, "quote": x} for x in sents if x != best and dig.EXCEPTION_MARKER.search(x)]
    return {"answerability": "RESPALDADA", "evidence_quotes": quotes, "evidence_conflicts": []}


def _sor_passage():
    return {
        "passage_id": _SOR_PID,
        "text_original": _real_text(_SOR_PID),
        "score": 0.9,
        "article_id": "19.1",
        "page": 195,
        "title": "Default",
        "source_url": "https://example.invalid/sor.pdf#page=195",
    }


def _stub_ada(llm_answer):
    ada_module = sys.modules[ArbitrationDecisionAssistant.__module__]
    ada = ArbitrationDecisionAssistant.__new__(ArbitrationDecisionAssistant)
    ada.config = {"version_label": "14 August 2026 (Official)"}
    ada._translate_to_technical_english = lambda query: f"{query} {_STATUS_QUERY_EN}"
    ada.rre = SimpleNamespace(
        retrieve=lambda *args, **kwargs: {
            "status": "SUCCESS",
            "evidence": [_sor_passage()],
            "related_passages": [],
            "operating_mode": "HYBRID",
            "source_sha256_verified": True,
        },
        retrieve_supplementary=lambda *args, **kwargs: [],
    )
    ada.doc_validator = ada_module.DocumentValidator()
    ada._call_llm = lambda prompt: (
        llm_answer,
        {"successful_provider": "Stub", "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}},
    )
    return ada


def _llm_json(summary, citations, grounded=False):
    obj = {
        "summary": summary,
        "normative_basis": summary,
        "citations": citations,
        "conditions_and_exceptions": "No aplica",
        "extended_analysis": "No aplica",
        "limitations": "Ninguna",
    }
    if grounded:
        obj.update(_grounded_fields(_SOR_PID, _sor_passage()["text_original"], _STATUS_QUERY_EN))
    return json.dumps(obj, ensure_ascii=False)


def _citation_ids(result):
    return [c.get("passage_id") if isinstance(c, dict) else c
            for c in result["structured_answer"].get("citations", [])]


def test_without_llm_abstains_and_keeps_retrieved_evidence():
    """Option A: no generator -> ABSTAIN, no normative citations, evidence kept for consultation."""
    result = _stub_ada(None).analyze_situation(_STATUS_QUERY)
    assert result["status"] == "ABSTAIN"
    assert _citation_ids(result) == []
    assert [e["passage_id"] for e in result["evidence"]] == [_SOR_PID]
    assert "Abstención" in result["structured_answer"]["summary"]


@pytest.mark.parametrize("summary,citations", [
    ("Los atletas deben estar listos cuando se les llama.", []),
    ("Según [SOR-2026-08-P999-S999], los atletas deben estar listos.", ["SOR-2026-08-P999-S999"]),
    ("Según [CHK-EXTERNAL-001], los atletas deben estar listos.", ["CHK-EXTERNAL-001"]),
])
def test_llm_answer_without_certified_primary_citation_abstains(summary, citations):
    """No citation, a citation outside the delivered evidence, or a non-SOR-only citation -> ABSTAIN."""
    result = _stub_ada(_llm_json(summary, citations)).analyze_situation(_STATUS_QUERY)
    assert result["status"] == "ABSTAIN"
    assert _citation_ids(result) == []
    assert summary not in result["structured_answer"]["summary"]


def test_llm_answer_citing_certified_primary_passage_succeeds():
    """A generated answer citing a certified primary passage delivered to the model may be SUCCESS."""
    summary = f"Según [{_SOR_PID}], el pasaje certificado regula esta situación."
    result = _stub_ada(_llm_json(summary, [_SOR_PID], grounded=True)).analyze_situation(_STATUS_QUERY)
    assert result["status"] == "SUCCESS", result.get("decision_integrity")
    assert _SOR_PID in _citation_ids(result)
    assert set(_citation_ids(result)) <= {e["passage_id"] for e in result["evidence"]}
    assert "citas SOR validadas" in result["mode"]


def test_validator_rejects_article_absent_from_evidence():
    """No article is valid by default: a reference must be grounded in the delivered passages."""
    ada_module = sys.modules[ArbitrationDecisionAssistant.__module__]
    validator = ada_module.NormativeValidator(evidence_passages=[_sor_passage()])
    verif = validator.validate_text("Conforme al Artículo 21 se debe consultar al supervisor.")
    assert "21" in verif.hallucinated_articles
    assert validator.validate_text("Conforme al Artículo 19.1 el atleta debe estar listo.").hallucinated_articles == []



# ---------------------------------------------------------------------------
# AUD-01: policy section of the analysis prompt (unconditional, stubbed RRE)
# ---------------------------------------------------------------------------
def test_analysis_prompt_policy_has_no_removed_hardcodes():
    stub = StubLLM(cite_first_delivered)
    ada = _stub_ada(None)
    ada._call_llm = stub
    ada.analyze_situation(_STATUS_QUERY)
    assert stub.analysis_prompts, "analysis prompt was not built"
    policy = _policy_section(stub.analysis_prompts[0])
    assert [term for term in _REMOVED_POLICY_TERMS if term in policy] == []
    for removed in ("head diving al intentar", "prohibición de lagunas", "blanco y azul según", "puente y criterio de ippon"):
        assert removed not in policy


# ---------------------------------------------------------------------------
# AUD-04: supplementary evidence governance (stubbed RRE and generator, real catalogue)
# ---------------------------------------------------------------------------
_REGISTERED_DOC = "KUN-PPT-002"        # catalogue: TIER_3, APROBADO_CONDICIONADO
_SUPP_TEXT = "Texto complementario de prueba sobre la llamada de los atletas al tatami."


def _supp(chunk_id, document_id, text=_SUPP_TEXT):
    # The chunk claims Tier 1 on purpose: authority must come from the catalogue, not the chunk.
    return {
        "chunk_id": chunk_id, "document_id": document_id, "authority": "TIER_1_NORMATIVE_PRIMARY",
        "validity": "VIGENTE", "eligibility": "ELIGIBLE_INTERPRETATIVA",
        "title": "Complemento de prueba", "content_text": text, "confidence_score": 0.9,
    }


def _stub_ada_with(evidence, supplementary, stub, retrieve_status="SUCCESS"):
    ada_module = sys.modules[ArbitrationDecisionAssistant.__module__]
    ada = ArbitrationDecisionAssistant.__new__(ArbitrationDecisionAssistant)
    ada.config = {"version_label": "14 August 2026 (Official)"}
    ada._translate_to_technical_english = lambda query: f"{query} {_STATUS_QUERY_EN}"
    ada.rre = SimpleNamespace(
        retrieve=lambda *args, **kwargs: {
            "status": retrieve_status, "evidence": [dict(e) for e in evidence], "related_passages": [],
            "operating_mode": "HYBRID", "source_sha256_verified": True,
        },
        retrieve_supplementary=lambda *args, **kwargs: [dict(s) for s in supplementary],
    )
    ada.doc_validator = ada_module.DocumentValidator()
    ada._call_llm = stub
    return ada


def test_ood_query_is_not_admitted_by_supplementary_results():
    """AUD-04.1: supplementary hits never turn an out-of-domain query into a normative one."""
    stub = StubLLM(cite_first_delivered)
    ada = _stub_ada_with([], [_supp("CHK-PPT-OOD-1", _REGISTERED_DOC)], stub, retrieve_status="ABSTAIN")
    res = ada.analyze_situation("penalizaciones por parada en boxes en formula 1")
    assert res["status"] == "ABSTAIN"
    assert res["evidence"] == [] and citation_ids(res) == []
    assert stub.analysis_prompts == []


def test_supplementary_without_primary_evidence_abstains():
    """AUD-04.1: in-domain query with supplementary hits but no primary SOR evidence -> ABSTAIN."""
    stub = StubLLM(cite_first_delivered)
    ada = _stub_ada_with([], [_supp("CHK-PPT-ONLY-1", _REGISTERED_DOC)], stub)
    res = ada.analyze_situation(_STATUS_QUERY)
    assert res["status"] == "ABSTAIN"
    assert res["evidence"] == [] and citation_ids(res) == []
    assert stub.analysis_prompts == []


def test_supplementary_authority_comes_from_catalogue_and_unregistered_is_dropped():
    """AUD-04.2: authority/validity from the catalogue (no promotion); unregistered docs discarded."""
    stub = StubLLM(cite_first_delivered)
    ada = _stub_ada_with(
        [_sor_passage()],
        [_supp("CHK-PPT-REG-1", _REGISTERED_DOC), _supp("CHK-UNREG-1", "KUN-NOT-IN-CATALOGUE-999")],
        stub,
    )
    res = ada.analyze_situation(_STATUS_QUERY)
    bundle = res["certified_bundle"]
    assert [i["evidence_id"] for i in bundle["primary_normative_evidence"]] == [_SOR_PID]
    interpretive = bundle["interpretive_evidence"]
    assert [i["evidence_id"] for i in interpretive] == ["CHK-PPT-REG-1"]
    assert interpretive[0]["authority"] == "TIER_3_REFEREEING_INTERPRETATION"
    assert interpretive[0]["role"] == "COMPLEMENTO_INTERPRETATIVO"
    assert [s["chunk_id"] for s in res["supplementary_context"]] == ["CHK-PPT-REG-1"]
    assert all(s["decisive"] is False for s in res["supplementary_context"])
    assert "KUN-NOT-IN-CATALOGUE-999" not in stub.analysis_prompts[0]


def test_prompt_separates_supplementary_as_non_decisive_and_non_citable():
    """AUD-04.3: supplementary text only in its own NO DECISORIO block, without citable IDs."""
    stub = StubLLM(cite_first_delivered)
    ada = _stub_ada_with([_sor_passage()], [_supp("CHK-PPT-SEP-1", _REGISTERED_DOC)], stub)
    ada.analyze_situation(_STATUS_QUERY)
    prompt = stub.analysis_prompts[0]
    assert _SUPP_TEXT not in primary_block(prompt)
    supp_section = supplementary_block(prompt)
    assert _SUPP_TEXT in supp_section and "NO DECISORIO" in supp_section
    assert "CHK-PPT-SEP-1" not in prompt and _REGISTERED_DOC not in prompt
    assert delivered_primary_ids(prompt) == [_SOR_PID]


@pytest.mark.parametrize("cited,extra", [
    ([_SOR_PID, "CHK-PPT-CIT-1"], ""),
    ([_SOR_PID], f" Véase {_REGISTERED_DOC}."),
])
def test_supplementary_or_document_id_citation_invalidates_answer(cited, extra):
    """AUD-04.4: citing a supplementary chunk or a document_id is never a valid normative citation."""
    stub = StubLLM(lambda prompt, delivered: json_answer(cited, extra_text=extra))
    ada = _stub_ada_with([_sor_passage()], [_supp("CHK-PPT-CIT-1", _REGISTERED_DOC)], stub)
    res = ada.analyze_situation(_STATUS_QUERY)
    assert res["status"] == "ABSTAIN"
    assert citation_ids(res) == []


def test_validator_does_not_use_supplementary_text_as_ground_truth():
    """AUD-04.5: an article present only in supplementary text is not grounded."""
    supp_text = "El Artículo 77 del documento complementario describe la llamada al tatami."
    stub = StubLLM(lambda prompt, delivered: json_answer([_SOR_PID], extra_text=" Conforme al Artículo 77."))
    ada = _stub_ada_with([_sor_passage()], [_supp("CHK-PPT-VAL-1", _REGISTERED_DOC, supp_text)], stub)
    res = ada.analyze_situation(_STATUS_QUERY)
    assert res["status"] == "ABSTAIN"
    ada_module = sys.modules[ArbitrationDecisionAssistant.__module__]
    with pytest.raises(TypeError):
        ada_module.NormativeValidator(evidence_passages=[_sor_passage()], supplementary_passages=[])


def test_citations_are_only_cited_and_delivered_primary_passages():
    """AUD-04.4: undelivered dict citations are dropped and uncited evidence is never added."""
    second = dict(_sor_passage(), passage_id="SOR-2026-08-P195-S202", article_id="Article 19")
    inline_only = json.dumps({
        "summary": f"Respuesta de prueba [{second['passage_id']}].", "normative_basis": "",
        "citations": [], "conditions_and_exceptions": "No aplica",
        "extended_analysis": "No aplica", "limitations": "Ninguna",
        **_grounded_fields(second["passage_id"], second["text_original"], _STATUS_QUERY_EN),
    }, ensure_ascii=False)
    res = _stub_ada_with([_sor_passage(), second], [], StubLLM(lambda p, d: inline_only)).analyze_situation(_STATUS_QUERY)
    assert res["status"] == "SUCCESS"
    assert citation_ids(res) == [second["passage_id"]]

    with_dict = json.dumps({
        "summary": f"Respuesta de prueba [{_SOR_PID}].", "normative_basis": "",
        "citations": [_SOR_PID, {"passage_id": "FAKE-NOT-DELIVERED"}],
        "conditions_and_exceptions": "No aplica", "extended_analysis": "No aplica", "limitations": "Ninguna",
        **_grounded_fields(_SOR_PID, _sor_passage()["text_original"], _STATUS_QUERY_EN),
    }, ensure_ascii=False)
    res = _stub_ada_with([_sor_passage()], [], StubLLM(lambda p, d: with_dict)).analyze_situation(_STATUS_QUERY)
    assert res["status"] == "SUCCESS"
    assert citation_ids(res) == [_SOR_PID]

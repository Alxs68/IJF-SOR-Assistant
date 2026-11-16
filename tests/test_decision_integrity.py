"""Fase 9 - pruebas adversariales del control de integridad decisoria (DIG), a nivel de compuerta.

Usan pasajes REALES del corpus SOR y respuestas sinteticas. Verifican el COMPORTAMIENTO del control
(permitir / abstener y que control falla); no codifican respuestas normativas y NO demuestran
entailment: una respuesta que supera DIG queda con nivel D = NO_VERIFICADO.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import decision_integrity as dig  # noqa: E402

CORPUS = os.path.join(ROOT, "data", "processed", "rebuild_2026_08_corrected", "passages_candidate.json")
SHADOW = os.path.join(ROOT, "data", "corpus_multisource", "processed", "multisource_passages.json")


@pytest.fixture(scope="module")
def env():
    if not os.path.exists(CORPUS) or not os.path.exists(dig.UNITS_PATH):
        pytest.skip("corpus o unidades derivadas no disponibles")
    with open(CORPUS, encoding="utf-8") as fh:
        ps = json.load(fh)
    by_page_art = {}
    for p in ps:
        by_page_art[(p["pdf_page_index"], p["article_id"])] = dict(p, page=p["pdf_page_index"])
    with open(SHADOW, encoding="utf-8") as fh:
        shadow = {c["chunk_id"]: c["content_text"] for c in json.load(fh)}
    return dig.DecisionIntegrityGate(ps), by_page_art, shadow


def P(env, page, art):
    return env[1][(page, art)]


def sentence(p, startswith):
    s = next(x for x in dig.sentences(p["text_original"]) if dig.norm(startswith) in dig.norm(x))
    return s


def answer(summary, quotes, answerability="RESPALDADA", conflicts=(), cite=None, **extra):
    obj = {"summary": summary, "normative_basis": "", "citations": cite if cite is not None else sorted({q[0] for q in quotes}),
           "conditions_and_exceptions": "No aplica", "extended_analysis": "No aplica", "limitations": "Ninguna",
           "answerability": answerability, "evidence_quotes": [{"passage_id": a, "quote": b} for a, b in quotes],
           "evidence_conflicts": list(conflicts)}
    obj.update(extra)
    return json.dumps(obj, ensure_ascii=False)


def run(env, ans, query, query_en, evidence, related=(), supp=()):
    return env[0].evaluate(ans, query, query_en, list(evidence), list(related), supplementary_texts=list(supp))


def failed(res):
    return set(res["failed_checks"])


# ------------------------------------------------------------------ control positivo
def test_positive_control_grounded_answer_is_permitted_but_not_entailed(env):
    art7 = P(env, 152, "Article 7")
    q = sentence(art7, "b) Waza-ari")
    res = run(env, answer(f"Waza-ari: de 10 a 19 segundos [{art7['passage_id']}].", [(art7["passage_id"], q)]),
              "¿Cuántos segundos de osaekomi se necesitan para waza-ari?", "how many seconds of osaekomi for waza-ari", [art7])
    assert res["decision"] == "PERMITIR", res["failed_checks"]
    assert res["levels"]["D_respaldo_efectivo"].startswith("NO_VERIFICADO")


# ------------------------------------------------------------------ escenarios adversariales
def test_question_without_sor_answer_fabricated_figure_abstains(env):
    art1 = P(env, 135, "Article 1")
    q = sentence(art1, "The ages limits for continental referee examinations")
    res = run(env, answer(f"Los árbitros cobran 200 euros por día [{art1['passage_id']}].", [(art1["passage_id"], q)]),
              "What daily fee is paid to referees at a Grand Prix?", "daily fee referees grand prix", [art1])
    assert res["decision"] == "ABSTENER" and "DIG-06_CIFRAS_RESPALDADAS" in failed(res)


def test_question_without_sor_answer_declared_insufficient_abstains(env):
    art1 = P(env, 135, "Article 1")
    q = sentence(art1, "The ages limits for continental referee examinations")
    res = run(env, answer(f"No consta [{art1['passage_id']}].", [(art1["passage_id"], q)], answerability="EVIDENCIA_INSUFICIENTE"),
              "What daily fee is paid to referees at a Grand Prix?", "daily fee referees", [art1])
    assert "DIG-01_SUFICIENCIA_DECLARADA" in failed(res) and res["decision"] == "ABSTENER"


def test_correct_answer_with_irrelevant_citation_abstains(env):
    art7, venue = P(env, 152, "Article 7"), P(env, 93, "8.1")
    q = sentence(venue, "For the Olympic Games the seating capacity")
    res = run(env, answer(f"Ippon se obtiene con 20 segundos [{venue['passage_id']}].", [(venue["passage_id"], q)]),
              "¿Cuántos segundos de osaekomi dan ippon?", "osaekomi seconds ippon", [art7, venue])
    assert res["decision"] == "ABSTENER"
    assert {"DIG-05_PERTINENCIA_MINIMA", "DIG-06_CIFRAS_RESPALDADAS"} <= failed(res)


def test_plausible_but_unsupported_sanction_abstains(env):
    p188 = P(env, 188, "Article 18.1.4")
    q = sentence(p188, "33. In cadet events athletes are not allowed to use the head to throw")
    res = run(env, answer(f"Uke será sancionado con hansoku-make [{p188['passage_id']}].", [(p188["passage_id"], q)]),
              "En cadetes, ¿qué sanción recibe uke por defender con la cabeza?", "cadet uke head defend penalty", [p188])
    assert res["decision"] == "ABSTENER" and "DIG-07_TERMINOS_RESPALDADOS" in failed(res)


def test_mixed_evidence_and_unsupported_inference_abstains(env):
    art7 = P(env, 152, "Article 7")
    q = sentence(art7, "c) Yuko")
    res = run(env, answer(f"Yuko de 5 a 9 segundos; además 15 segundos dan kiken-gachi [{art7['passage_id']}].", [(art7["passage_id"], q)]),
              "¿Cuántos segundos de osaekomi dan yuko?", "osaekomi seconds yuko", [art7])
    assert res["decision"] == "ABSTENER"
    assert {"DIG-06_CIFRAS_RESPALDADAS", "DIG-07_TERMINOS_RESPALDADOS"} <= failed(res)


def test_answer_quoting_only_shadow_abstains(env):
    p177 = P(env, 177, "Article 18.1.1")
    shadow_txt = env[2]["CHK-KUN-NEW-001-003"]
    res = run(env, answer(f"Límite de kumikata [{p177['passage_id']}].", [(p177["passage_id"], shadow_txt)]),
              "¿Cuánto tiempo puede mantenerse el kumikata sin atacar?", "kumikata time without attack", [p177], supp=[shadow_txt])
    assert res["decision"] == "ABSTENER" and "DIG-04_CITA_NO_SHADOW" in failed(res)


def test_shadow_influenced_answer_citing_sor_abstains(env):
    p177 = P(env, 177, "Article 18.1.1")
    q = sentence(p177, "The time between conventional kumikata")
    shadow_txt = env[2]["CHK-KUN-NEW-001-003"]
    res = run(env, answer(f"El kumikata sin ataque tiene un límite de 30 segundos [{p177['passage_id']}].", [(p177["passage_id"], q)]),
              "¿Cuánto tiempo puede mantenerse el kumikata sin atacar?", "kumikata time without attack", [p177], supp=[shadow_txt])
    assert res["decision"] == "ABSTENER" and "DIG-06_CIFRAS_RESPALDADAS" in failed(res)
    if "30" not in dig.numbers_in(p177["text_original"]):
        assert "DIG-08_SIN_INFLUENCIA_SHADOW" in failed(res)


def test_shadow_terms_in_analysis_abstain(env):
    art7 = P(env, 152, "Article 7")
    q = sentence(art7, "b) Waza-ari")
    supp = [env[2]["CHK-KUN-NEW-001-001"]]
    res = run(env, answer(f"Waza-ari de 10 a 19 segundos [{art7['passage_id']}].", [(art7["passage_id"], q)],
                          extended_analysis="Estas reglas quedaron locked tras Ulaanbaatar."),
              "¿Cuántos segundos para waza-ari?", "seconds osaekomi waza-ari", [art7], supp=supp)
    assert "DIG-08_SIN_INFLUENCIA_SHADOW" in failed(res)


def test_declared_contradictory_evidence_abstains(env):
    art7 = P(env, 152, "Article 7")
    q = sentence(art7, "b) Waza-ari")
    res = run(env, answer(f"Waza-ari [{art7['passage_id']}].", [(art7["passage_id"], q)], conflicts=["dos pasajes fijan tiempos distintos"]),
              "¿Cuántos segundos para waza-ari?", "seconds osaekomi waza-ari", [art7])
    assert "DIG-01_SUFICIENCIA_DECLARADA" in failed(res) and res["decision"] == "ABSTENER"


def test_partial_evidence_cited_without_quote_abstains(env):
    art7, art6 = P(env, 152, "Article 7"), P(env, 152, "Article 6")
    q = sentence(art7, "b) Waza-ari")
    res = run(env, answer(f"Waza-ari [{art7['passage_id']}] y duración [{art6['passage_id']}].", [(art7["passage_id"], q)],
                          cite=[art7["passage_id"], art6["passage_id"]]),
              "¿Cuántos segundos para waza-ari?", "seconds osaekomi waza-ari", [art7, art6])
    assert "DIG-02_CITAS_CON_CITA_LITERAL" in failed(res)


def test_omitted_exception_abstains_and_cited_exception_passes(env):
    art8 = P(env, 153, "Article 8")
    rule = sentence(art8, "Any immediate result of a technique")
    exc = sentence(art8, "Although a throwing technique")
    query, query_en = "¿Es válida una técnica iniciada en el último segundo?", "technique last second valid time signal"
    omitted = run(env, answer(f"Es válida [{art8['passage_id']}].", [(art8["passage_id"], rule)]), query, query_en, [art8])
    assert "DIG-09_EXCEPCIONES_CITADAS" in failed(omitted)
    full = run(env, answer(f"Es válida, con la excepción citada [{art8['passage_id']}].",
                           [(art8["passage_id"], rule), (art8["passage_id"], exc)]), query, query_en, [art8])
    assert "DIG-09_EXCEPCIONES_CITADAS" not in failed(full)


def test_required_cross_reference_not_delivered_abstains(env):
    p190, p188 = P(env, 190, "Article 18.2.1"), P(env, 188, "Article 18.1.4")
    q = sentence(p190, "Tori can continue in the competition (see also Article 18")
    query, query_en = "¿Puede tori continuar en la competición tras head diving?", "tori continue competition head diving"
    missing = run(env, answer(f"Puede continuar [{p190['passage_id']}].", [(p190["passage_id"], q)]), query, query_en, [p190])
    assert "DIG-10_REFERENCIAS_ENTREGADAS" in failed(missing) and missing["decision"] == "ABSTENER"
    delivered = run(env, answer(f"Puede continuar [{p190['passage_id']}].", [(p190["passage_id"], q)]), query, query_en, [p190], related=[p188])
    assert "DIG-10_REFERENCIAS_ENTREGADAS" not in failed(delivered)


def test_answer_exceeding_source_content_abstains(env):
    p195 = P(env, 195, "Article 19.1")
    q = sentence(p195, "An athlete wins by fusen-gachi")
    res = run(env, answer(f"Gana por fusen-gachi y el rival queda con hansoku-make [{p195['passage_id']}].", [(p195["passage_id"], q)]),
              "¿Qué pasa si el rival no se presenta?", "opponent does not appear contest", [p195])
    assert "DIG-07_TERMINOS_RESPALDADOS" in failed(res)


def test_non_literal_quote_abstains(env):
    art7 = P(env, 152, "Article 7")
    res = run(env, answer(f"Waza-ari [{art7['passage_id']}].", [(art7["passage_id"], "Waza-ari is awarded for holds between ten and nineteen seconds")]),
              "¿Cuántos segundos para waza-ari?", "seconds osaekomi waza-ari", [art7])
    assert "DIG-03_CITA_LITERAL" in failed(res)


def test_non_json_answer_abstains(env):
    res = run(env, "Respuesta libre sin estructura [SOR-2026-08-P152-S180].", "x", "x", [P(env, 152, "Article 7")])
    assert res["decision"] == "ABSTENER" and "DIG-00_JSON" in failed(res)


def test_quote_absent_from_canonical_corpus_is_not_verifiable(env):
    """Una cita literal del texto entregado pero inexistente en el texto canonico del SOR (pagina o
    vecinas) no puede vincularse a una unidad derivada: el control se abstiene (DIG-09)."""
    art7 = dict(P(env, 152, "Article 7"))
    q = "Synthetic sentence that does not exist anywhere in the official rules text."
    art7["text_original"] = art7["text_original"] + "\n" + q
    res = run(env, answer(f"Waza-ari [{art7['passage_id']}].", [(art7["passage_id"], q)]), "segundos waza-ari", "seconds waza-ari", [art7])
    assert "DIG-09_EXCEPCIONES_CITADAS" in failed(res)


def test_stitched_multi_page_text_is_resolved_on_canonical_page(env):
    """9.1-G1: el RRE entrega texto cosido de varias paginas; una cita literal procedente de la pagina
    siguiente se localiza en su pagina canonica y su unidad derivada (antes: unidad no disponible)."""
    p188, p189 = P(env, 188, "Article 18.1.4"), P(env, 189, "Article 18.1.4")
    stitched = dict(p188, text_original=p188["text_original"] + "\n\n--- [PAGE BREAK: P188 -> P189] ---\n\n" + p189["text_original"])
    q = sentence(p189, "In cadet events there will be no score for reverse seoi-nage")
    exc = sentence(p189, "The application of seoi-nage techniques when uke can perform ukemi")
    res = run(env, answer(f"Sin puntuación y shido para tori en cadetes [{p188['passage_id']}].",
                          [(p188["passage_id"], q), (p188["passage_id"], exc)]),
              "In cadet events, is reverse seoi-nage scored?", "cadet reverse seoi-nage score shido", [stitched])
    assert "DIG-09_EXCEPCIONES_CITADAS" not in failed(res), res["checks"]


def test_duration_question_without_figure_is_not_forced(env):
    """9.1-G2: 'how long' puede responderse sin cifra; DIG-12 no aplica."""
    assert not dig._QUANTITY.search("In a veterans round robin that goes into golden score, how long can osaekomi-waza be held?")
    assert dig._QUANTITY.search("How many kata pairs are seeded in the draw?")


def test_missing_units_layer_is_conservative(env, tmp_path=None):
    gate = dig.DecisionIntegrityGate(None, units_path=os.path.join(ROOT, "no", "existe.jsonl"))
    art7 = P(env, 152, "Article 7")
    q = sentence(art7, "b) Waza-ari")
    res = gate.evaluate(answer(f"Waza-ari [{art7['passage_id']}].", [(art7["passage_id"], q)]),
                        "segundos waza-ari", "seconds waza-ari", [art7], [])
    assert res["decision"] == "ABSTENER"


def test_no_query_specific_rules_in_gate():
    src = open(os.path.join(ROOT, "src", "decision_integrity.py"), encoding="utf-8").read()
    for forbidden in ("SOR-2026-08-P", "18.1.4", "head diving", "kumikata", "Article 1", "fusen"):
        assert forbidden not in src


# ------------------------------------------------------------------ regresiones Fase 9.1
def test_generic_term_overlap_is_not_pertinence(env):
    """9.1-D2: una cita de otro articulo que solo comparte terminos genericos (official, events) con la
    consulta no es pertinente (caso B1-EN-001 -> 1.6 IJF Calendar)."""
    cal = P(env, 18, "1.6")
    q = sentence(cal, "The IJF Executive Committee will agree and approve the schedule for all IJF events")
    res = run(env, answer(f"Respuesta [{cal['passage_id']}].", [(cal["passage_id"], q)]),
              "What is the minimum age to compete in official IJF events?", "minimum age compete official IJF events", [cal])
    assert "DIG-05_PERTINENCIA_MINIMA" in failed(res)


def test_neighbouring_reference_not_quoted_is_not_required(env):
    """9.1-D3: no se exige una referencia que esta en una oracion vecina y no en la cita
    (caso fusen-gachi: E1.3 / C1.1.5 en la introduccion del Article 19)."""
    p195 = P(env, 195, "Article 19.1")
    q = sentence(p195, "An athlete wins by fusen-gachi (win by default)")
    res = run(env, answer(f"Gana por fusen-gachi [{p195['passage_id']}].", [(p195["passage_id"], q)]),
              "When is a contest won by fusen-gachi?", "contest won fusen-gachi default", [p195])
    assert "DIG-10_REFERENCIAS_ENTREGADAS" not in failed(res), res["checks"]


def test_english_query_with_terms_absent_from_sor_abstains(env):
    """9.1-D5: si la consulta (EN) nombra algo que no aparece en todo el SOR, no puede responderse."""
    art8 = P(env, 96, "8.7")
    q = next(x for x in dig.sentences(art8["text_original"]) if len(dig.norm(x).split()) >= 8 and "contest area" in x)
    res = run(env, answer(f"Dimensiones [{art8['passage_id']}].", [(art8["passage_id"], q)]),
              "What are the dimensions of a sumo dohyo?", "dimensions sumo dohyo", [art8])
    assert "DIG-11_TERMINOS_DE_CONSULTA_EN_SOR" in failed(res) and res["decision"] == "ABSTENER"


def test_quantity_question_without_figure_in_quotes_abstains(env):
    """9.1-D6: una pregunta cuantitativa no puede respaldarse con citas sin ninguna cifra."""
    p15 = P(env, 15, "1.2.2")
    q = sentence(p15, "The integrity of sport depends on the outcome")
    res = run(env, answer(f"Respuesta [{p15['passage_id']}].", [(p15["passage_id"], q)]),
              "What is the exact fine amount for match fixing?", "exact fine amount match fixing integrity sport", [p15])
    assert "DIG-12_CIFRA_PARA_PREGUNTA_CUANTITATIVA" in failed(res)


def test_shadow_title_words_count_as_shadow_footprint(env):
    """9.1-D4: los titulos SHADOW tambien se entregan al modelo; sus terminos cuentan para DIG-08."""
    art7 = P(env, 152, "Article 7")
    q = sentence(art7, "b) Waza-ari")
    supp = ["Congelación Ulaanbaatar Locked " + env[2]["CHK-KUN-NEW-001-001"]]
    res = run(env, answer(f"Waza-ari de 10 a 19 segundos [{art7['passage_id']}].", [(art7["passage_id"], q)],
                          extended_analysis="Congelación decidida en Ulaanbaatar."),
              "¿Cuántos segundos para waza-ari?", "seconds osaekomi waza-ari", [art7], supp=supp)
    assert "DIG-08_SIN_INFLUENCIA_SHADOW" in failed(res)


# ------------------------------------------------------------------ regresiones Fase 9.1 (DIG-1.3)
def test_pertinence_requires_a_distinctive_term_not_only_common_ones(env):
    """9.1: DIG-05 exige >=1 termino distintivo (<=15 %). La variante '>=2 terminos <=30 %' se evaluo y
    se descarto (mas SUCCESS con cita fuera de la evidencia minima); terminos frecuentes no bastan."""
    gate = env[0]
    assert gate.specific_max_df == 0.0
    assert not gate.pertinent(dig.content_stems("cadet events head"), dig.content_stems("cadete cadet head penalty"))
    assert not gate.pertinent(dig.content_stems("official IJF events schedule"), dig.content_stems("minimum age official IJF events"))
    assert gate.pertinent(dig.content_stems("use the head to throw"), dig.content_stems("cadet head throw"))


def test_quote_across_stitched_page_break_is_verified_by_segments(env):
    """9.1-H1: una cita que cruza el marcador de salto de pagina del texto cosido se verifica por
    segmentos en su pagina canonica (antes: unidad no disponible)."""
    p173, p174 = P(env, 173, "Article 17"), P(env, 174, "Article 17")
    marker = "\n\n--- [PAGE BREAK: P173 -> P174 | Article 17] ---\n\n"
    stitched = dict(p173, text_original=p173["text_original"] + marker + p174["text_original"])
    tail = dig.sentences(p173["text_original"])[-1]
    head = next(x for x in dig.sentences(p174["text_original"]) if len(dig.norm(x).split()) >= 6 and "page -" not in x)
    raw = stitched["text_original"]
    q = raw[raw.index(tail):raw.index(head) + len(head)]
    res = run(env, answer(f"Osaekomi [{p173['passage_id']}].", [(p173["passage_id"], q)]),
              "osaekomi-waza fuera del área", "osaekomi-waza outside contest area safety area", [stitched])
    assert not any("unidades_no_disponibles=['" in c["detail"] for c in res["checks"] if c["code"] == "DIG-09_EXCEPCIONES_CITADAS"), res["checks"]


def test_single_shadow_only_term_is_influence(env):
    """9.1-H3: un unico termino (>=5 letras) presente solo en SHADOW basta para DIG-08."""
    art7 = P(env, 152, "Article 7")
    q = sentence(art7, "b) Waza-ari")
    supp = [env[2]["CHK-KUN-NEW-001-002"]]
    res = run(env, answer(f"Waza-ari de 10 a 19 segundos [{art7['passage_id']}].", [(art7["passage_id"], q)],
                          extended_analysis="Además, ya está re-allowed."),
              "¿Cuántos segundos para waza-ari?", "seconds osaekomi waza-ari", [art7], supp=supp)
    assert "DIG-08_SIN_INFLUENCIA_SHADOW" in failed(res)

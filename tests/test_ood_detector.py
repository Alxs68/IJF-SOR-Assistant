import pytest
from src.ood_detector import OODDetector


def test_ood_detection_basketball():
    ood = OODDetector()
    query = "¿Cuál es la sanción por una falta personal y tiro libre en básquetbol?"
    eval_res = ood.evaluate_grounding(query)
    assert eval_res["is_in_domain"] is False
    assert eval_res["o_cov"] == 0.0


def test_ood_detection_finance():
    ood = OODDetector()
    query = "¿Cómo se calcula la tasa de interés compuesto anual en finanzas?"
    eval_res = ood.evaluate_grounding(query)
    assert eval_res["is_in_domain"] is False
    assert eval_res["o_cov"] == 0.0


def test_judo_in_domain_acceptance():
    ood = OODDetector()
    query = "Tori proyecta a Uke aplicando una técnica con fuerza y velocidad, pero Uke cae sobre un costado con el cuerpo perpendicular al tatami. ¿Qué puntuación corresponde?"
    cov = ood.compute_ontology_coverage(query)
    assert cov > 0.40

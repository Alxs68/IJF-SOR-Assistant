"""Integridad de referencias normativas (src/reference_integrity.py, F1). Sin red ni modelos.

Matriz de AUDITORIA_REFERENCIAS_NORMATIVAS.md: P1-P10 (positivos), N1-N7 (negativos), X1-X10 (no intervencion),
mas formatos, continuaciones, encabezados con guion, varios articulos por pagina, referencias cruzadas y exclusiones.
Usa el corpus local (passages_candidate.json, article_units_v1) en solo lectura."""
import os
import re
import socket
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
import reference_integrity as R  # noqa: E402

P177 = "SOR-2026-08-P177-S193"   # Article 18.1.1 (remite a Article 10 y Article 5)
P188 = "SOR-2026-08-P188-S196"   # Article 18.1.3 (final) y Article 18.1.4
P082 = "SOR-2026-08-P082-S100"   # continuacion de 6.4.2 (sin encabezado propio al inicio)
P083 = "SOR-2026-08-P083-S101"   # 6.4.3
P085 = "SOR-2026-08-P085-S102"   # 6.5.2
P086 = "SOR-2026-08-P086-S102"   # 6.5.2.1-6.5.2.3
P126 = "SOR-2026-08-P126-S167"   # C1.10 (continuacion), "C1 .11 T-shirt" (titulo con guion), C1.12
P163 = "SOR-2026-08-P163-S186"   # Article 13, clausulas 1-3
P164 = "SOR-2026-08-P164-S186"   # continuacion de Article 13 (clausula 3 b-c, clausulas 4-5)
P042 = "SOR-2026-08-P042-S052"   # 2.6.2, 2.7, 2.7.1 en la misma pagina


@pytest.fixture(scope="module")
def idx():
    return R.ReferenceIndex.load()


def verdicts(idx, sentence, cited=None):
    return [(v["etiqueta"], v["veredicto"]) for v in idx.check(sentence, cited)]


def refs(sentence):
    return [r.label + (f".{r.letter}" if r.letter else "") for r in R.extract_references(sentence)[0]]


# ---- P: positivos ---------------------------------------------------------------------------------------------------
def test_P1_referencia_correcta(idx):
    assert verdicts(idx, f"Se sanciona con shido según el Art. 18.1.1 [{P177}].") == [("18.1.1", "OK")]


@pytest.mark.parametrize("fmt", ["Article 18.1.1", "artículo 18.1.1", "Art 18 .1 .1", "art.18.1.1", "Art. 18. 1. 1",
                                 "ARTÍCULO 18.1.1", "el 18.1.1"])
def test_P2_formatos(idx, fmt):
    assert verdicts(idx, f"Regla aplicable: {fmt} [{P177}].") == [("18.1.1", "OK")]


@pytest.mark.parametrize("sentence", [f"Conforme al artículo 18.1.1 [{P177}].", f"According to Article 18.1.1 [{P177}].",
                                      f"Segundo o artigo 18.1.1 [{P177}].", f"Ver la sección 2.7.1 [{P042}].",
                                      f"See Section 2.7 [{P042}].", f"Conforme a regra 2.6.2 [{P042}]."])
def test_P3_idiomas(idx, sentence):
    assert [v for _, v in verdicts(idx, sentence)] == ["OK"]


def test_P4_pasaje_con_varios_articulos(idx):
    assert verdicts(idx, f"Arts. 18.1.3 y 18.1.4 [{P188}].") == [("18.1.3", "OK"), ("18.1.4", "OK")]
    assert verdicts(idx, f"Los apartados 2.6.2, 2.7 y 2.7.1 [{P042}].") == [("2.6.2", "OK"), ("2.7", "OK"), ("2.7.1", "OK")]


def test_P5_varios_numerales_y_pasajes(idx):
    assert verdicts(idx, f"Arts. 6.4.2 y 6.4.3 [{P082}, {P083}].") == [("6.4.2", "OK"), ("6.4.3", "OK")]


def test_P6_continuacion_de_articulo(idx):
    assert verdicts(idx, f"Art. 6.4.2 [{P082}].") == [("6.4.2", "OK")]
    assert verdicts(idx, f"Art. C1.10 [{P126}].") == [("C1.10", "OK")]


def test_P7_nivel_superior(idx):
    assert verdicts(idx, f"Artículo 18 [{P177}].") == [("18", "OK")]
    assert verdicts(idx, f"Section 6.5 [{P086}].") == [("6.5", "OK")]


def test_P8_referencia_cruzada(idx):
    assert verdicts(idx, f"Las sanciones remiten al Article 10 [{P177}].") == [("10", "OK_REF_CRUZADA")]


def test_P9_compuesta_articulo_clausula_letra(idx):
    assert verdicts(idx, f"Regla aplicable: Artículo 13.3.b [{P164}], página 164.") == [("13.3.b", "OK_ARTICULO_CLAUSULA")]
    assert verdicts(idx, f"Art. 13.3.b [{P163}].") == [("13.3.b", "OK_ARTICULO_CLAUSULA")]


def test_P10_encabezado_con_guion(idx):
    assert "C1.11" in idx.labels[P126]
    assert verdicts(idx, f"Art. C1.11 [{P126}].") == [("C1.11", "OK")]


# ---- N: negativos ---------------------------------------------------------------------------------------------------
def test_N1_articulo_alterado_mutacion_D(idx):
    s = ("Salir intencionadamente del área de competición en tachi-waza sin haber iniciado un ataque en una posición "
         f"válida se sanciona con Shido segun el Art. 19.1.1 [{P177}].")
    out = idx.check(s)
    assert [(v["etiqueta"], v["veredicto"], v["accion_recomendada"]) for v in out] == [("19.1.1", "INEXISTENTE", "RETIRAR_FRASE")]


def test_N1b_mutacion_F(idx):
    s = ("La respuesta se fundamenta en el Artículo 19.1.4 del SOR 2026 sobre penalizaciones (Shido) en competiciones "
         f"de cadetes [{P188}], el cual establece la prohibición específica para uke.")
    assert verdicts(idx, s) == [("19.1.4", "INEXISTENTE")]
    assert verdicts(idx, s.replace("19.1.4", "18.1.4")) == [("18.1.4", "OK")]


def test_N2_numeral_alterado(idx):
    out = idx.check(f"Se sanciona con shido según el Art. 18.1.4 [{P177}].")
    assert out[0]["veredicto"] == "DISCREPANCIA" and P188 in out[0]["ubicacion_en_corpus"]


def test_N3_subnumeral_alterado(idx):
    assert verdicts(idx, f"Art. 6.5.2 [{P085}].") == [("6.5.2", "OK")]
    assert verdicts(idx, f"Art. 6.5.2.3 [{P085}].") == [("6.5.2.3", "DISCREPANCIA")]
    assert verdicts(idx, f"Art. 6.5.2.9 [{P086}].") == [("6.5.2.9", "INEXISTENTE")]


def test_N4_referencia_inexistente(idx):
    assert verdicts(idx, f"Según el Artículo 18.9.9 [{P177}].") == [("18.9.9", "INEXISTENTE")]
    assert verdicts(idx, f"Según la sección 2.99 [{P042}].") == [("2.99", "INEXISTENTE")]


def test_N5_cita_a_otro_articulo_regresion_real_V23_L03(idx):
    s = (f"Los pasajes establecen las categorías para eventos de equipos mixtos en los Art. 6.4.1 y 6.4.2 [{P082}], y "
         f"para eventos de equipos femeninos y masculinos en el Art. 6.5.1 [{P086}].")
    # cada referencia se juzga contra TODOS los pasajes que cita la frase
    assert verdicts(idx, s) == [("6.4.1", "DISCREPANCIA"), ("6.4.2", "OK"), ("6.5.1", "DISCREPANCIA")]


def test_N6_referencia_multiple_parcialmente_erronea(idx):
    assert verdicts(idx, f"Arts. 6.4.2 y 6.4.9 [{P082}].") == [("6.4.2", "OK"), ("6.4.9", "INEXISTENTE")]


def test_N7_nivel2_pendiente_falso_negativo_conocido(idx):
    """Nivel 1 (por pasaje): "Art. 18.1.3" para una regla de cadetes citada de 18.1.4 en la MISMA pagina pasa como OK.
    Detectarlo exige el nivel 2 (encabezado que gobierna la cita literal), fuera del alcance de F1."""
    assert verdicts(idx, f"En cadetes se sanciona con shido según el Art. 18.1.3 [{P188}].") == [("18.1.3", "OK")]


# ---- X: no intervencion ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("sentence", [
    "El combate dura 4 minutos y el golden score 3 minutos.",                      # X1 tiempos
    "Categorías -66 kg, +100 kg y U18; tolerancia de 2.5 kg.",                      # X2 pesos
    "Un 5 % de tolerancia; 1.5 m; 2,5 kg; 0.5 s.",                                  # X3 porcentajes, decimales
    "Edición del 14 August 2026 (SOR 2026-08); 14 de agosto de 2026; 2026-08-14.",  # X4 fechas
    "Ippon, waza-ari 1 y shido 3; marcador 10-0.",                                  # X5 puntuaciones
    "Equipos de 6 atletas, mínimo 4, en 4 combates y 3 rondas.",                    # X6 cantidades
    "Ver pág. 177, página 164, pp. 81-83 y page 12.",                               # X7 paginas
    "Pictures 18.59–18.60, figura 4.2, tabla 4.2, Table 6.1.2 y Pantone n°18-4051TCX(TPX).",  # X8 figuras, tablas, codigos
    "Dura 3:00 minutos y empieza a las 10:30.",                                     # tiempos con dos puntos
])
def test_X_sin_referencias(idx, sentence):
    assert refs(sentence) == []
    assert idx.check(sentence + f" [{P177}]") == []


def test_X9_clausula_solo_registro(idx):
    out = idx.check(f"Article 13 End of the Contest, paragraph 4 [{P164}].")
    assert [(v["etiqueta"], v["tipo"], v["veredicto"], v["accion_recomendada"]) for v in out] == [
        ("13", "EXPLICITA", "OK", "NINGUNA"), ("4", "CLAUSULA", "NO_EVALUABLE", "REGISTRAR")]


def test_X10_conjuncion_no_es_letra(idx):
    assert refs("Art. 6.4.1 y 6.4.2") == ["6.4.1", "6.4.2"]
    assert refs("Art. 6.4.1 e 6.4.2") == ["6.4.1", "6.4.2"]


# ---- casos adicionales ----------------------------------------------------------------------------------------------
def test_apartado_con_etiqueta_es_seccion_y_sin_ella_es_clausula():
    assert [(r.label, r.kind) for r in R.extract_references("el apartado 6.2.5.4 y el apartado 3")[0]] == [
        ("6.2.5.4", "EXPLICITA"), ("3", "CLAUSULA")]


def test_rango_de_referencias(idx):
    assert verdicts(idx, f"Arts. 18.1.3–18.1.4 [{P188}].") == [("18.1.3", "OK"), ("18.1.4", "OK")]


def test_desnuda_requiere_dos_puntos_o_letra_de_apendice():
    assert refs("conforme al 18.1.1") == ["18.1.1"]
    assert refs("según E1.6.3.1") == ["E1.6.3.1"]
    assert refs("una tolerancia de 6.5 y 2.5") == []          # un solo punto sin rotulo: decimal, no referencia


def test_identificador_sor_no_es_referencia():
    assert refs(f"[{P177}] [SOR-2026-08-P042-S052]") == []


def test_sin_cita_y_citas_de_la_respuesta(idx):
    out = idx.check("La regla del Art. 18.1.1 se aplica.", [], answer_ids=[P177])
    assert out[0]["veredicto"] == "SIN_CITA" and out[0]["veredicto_con_citas_respuesta"] == "OK"
    assert out[0]["accion_recomendada"] == "REGISTRAR"


def test_pasaje_fuera_del_indice_no_evaluable(idx):
    assert verdicts(idx, "Art. 18.1.1 [SOR-2026-08-P999-S999].") == [("18.1.1", "NO_EVALUABLE")]


def test_resultado_estructurado_y_explicable(idx):
    v = idx.check(f"Art. 18.1.4 [{P177}].")[0]
    assert set(v) >= {"referencia", "etiqueta", "tipo", "pasajes_citados", "etiquetas_estructurales", "veredicto",
                      "motivo", "confianza", "accion_recomendada"}
    assert v["pasajes_citados"] == [P177] and v["etiquetas_estructurales"] == ["18.1.1"] and v["confianza"] == "ALTA"
    assert set(R.VERDICTS) == {"OK", "OK_REF_CRUZADA", "OK_ARTICULO_CLAUSULA", "INEXISTENTE", "DISCREPANCIA",
                               "SIN_CITA", "NO_EVALUABLE"}


def test_indice_sintetico_independiente_del_corpus():
    passages = [{"passage_id": "SOR-X-Y-P001-S001", "article_id": "Article 7",
                 "text_original": "Article 7 Weigh-in\n1. Rule one\n7 .2 Re-check\nsee Article 3\n"},
                {"passage_id": "SOR-X-Y-P002-S002", "article_id": "3.1", "text_original": "3 .1 Draw\n"}]
    ix = R.ReferenceIndex(passages, [])
    assert ix.labels["SOR-X-Y-P001-S001"] == {"7", "7.2"}
    assert [(v["etiqueta"], v["veredicto"]) for v in ix.check("Art. 7.2 y 7.1 [SOR-X-Y-P001-S001]")] == [
        ("7.2", "OK"), ("7.1", "OK_ARTICULO_CLAUSULA")]
    assert [v["veredicto"] for v in ix.check("Artículo 3 [SOR-X-Y-P001-S001]")] == ["OK_REF_CRUZADA"]
    assert [v["veredicto"] for v in ix.check("Section 3.1 [SOR-X-Y-P001-S001]")] == ["DISCREPANCIA"]


def test_determinista(idx):
    s = f"Arts. 6.4.1 y 6.4.2 [{P082}], Art. 19.1.1 [{P177}] y Article 13.3.b [{P164}]."
    assert idx.check(s) == idx.check(s) == R.ReferenceIndex.load().check(s)


def test_sin_red_ni_modelos(monkeypatch):
    def _blocked(*a, **k):
        raise AssertionError("conexion de red durante reference_integrity")
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    ix = R.ReferenceIndex.load()
    assert ix.check(f"Art. 18.1.1 [{P177}]")[0]["veredicto"] == "OK"
    src = open(R.__file__, encoding="utf-8").read()
    for mod in ("urllib", "requests", "socket", "http", "google", "groq", "streamlit", "llm_provider",
                "decision_integrity", "answer_verification", "ada_assistant"):
        assert not re.search(rf"^\s*(?:import|from)\s+{mod}\b", src, re.M), mod

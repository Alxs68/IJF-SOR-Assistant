"""
Adversarial Regression Test Suite for Normative Hallucination Prevention.
Covers 10 mandatory adversarial scenarios defined in the audit requirements:

1. Infracción con código explícito en el corpus (PS34 / Head defence cadetes).
2. Penalización con código inventado/no respaldado en pasajes (código alucinado PS99).
3. Regla de cadetes cuya aplicabilidad a seniors no está demostrada.
4. Consulta sobre acumulación de Shidos y Hansoku-make.
5. Procedimiento administrativo o disciplinario no mencionado en la norma (formulario inexistente/comisión ad hoc no convocada).
6. Referencia a un artículo que no respalda la afirmación (Art. 21 citado para shido ordinario).
7. Pregunta que requiere varios apartados normativos simultáneos.
8. Consulta legítima con paráfrasis fiel sin repetición literal.
9. Consulta fuera de alcance o con evidencia insuficiente (Abstención estricta).
10. Respuesta de proveedor que inventa una cita de pasaje inexistente (SOR-2026-08-P999-S999).
"""

import unittest
import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from normative_validator import NormativeValidator
from response_structurer import StructuredAnswer, parse_structured_response
from ada_assistant import ArbitrationDecisionAssistant
from llm_provider import MultiProviderLLMManager


class TestNormativeHallucinationPrevention(unittest.TestCase):

    def setUp(self):
        self.mock_evidence = [
            {
                "passage_id": "SOR-2026-08-P255-S269",
                "article_id": "G1.3",
                "page": 255,
                "title": "G1.3 Penalty Codes",
                "text_original": (
                    "Using the head to defend in cadet events PS34 Shido 18.1.4 34\n"
                    "Reverse seoi-nage in cadet events PS35 Shido 18.1.4 35\n"
                    "Head dive PH1 Hansoku-make (H) 18.2.1 1"
                ),
                "source_url": "https://example.com/sor.pdf#page=255"
            },
            {
                "passage_id": "SOR-2026-08-P189-S196",
                "article_id": "18.1.4",
                "page": 189,
                "title": "Article 18.1.4 Penalties in Cadet Competitions",
                "text_original": "35. In cadet events there will be no score for reverse seoi-nage and TORI will be penalised with shido.",
                "source_url": "https://example.com/sor.pdf#page=189"
            }
        ]
        self.validator = NormativeValidator(evidence_passages=self.mock_evidence)

    def test_case_01_explicit_code_supported(self):
        """1. Penalización con código explícito en el corpus."""
        text = "En cadetes la defensa con cabeza se penaliza con shido código PS34."
        verif = self.validator.validate_text(text)
        self.assertTrue(verif.is_valid)
        self.assertEqual(len(verif.hallucinated_codes), 0)

    def test_case_02_unsupported_penalty_code_blocked(self):
        """2. Penalización cuyo código no esté respaldado por los pasajes recuperados."""
        text = "Esta acción recibe una sanción grave con código PX99 y Shido código PS88."
        verif = self.validator.validate_text(text)
        self.assertFalse(verif.is_valid)
        self.assertIn("PX99", verif.hallucinated_codes)
        self.assertIn("PS88", verif.hallucinated_codes)

        # Verificar desinfección en structured answer
        struct = StructuredAnswer(
            summary="Sanción con código PX99 aplicada.",
            extended_analysis="El árbitro registra PS88."
        )
        sanitized = self.validator.sanitize_structured_answer(struct)
        self.assertNotIn("PX99", sanitized.summary)
        self.assertIn("[Código no verificado en evidencia]", sanitized.summary)
        self.assertIn("Control de Rigor Normativo", sanitized.limitations)

    def test_case_03_cadet_rule_scope_distinction(self):
        """3. Regla aplicable a cadetes cuya aplicabilidad a otras categorías no esté demostrada."""
        struct = StructuredAnswer(
            summary="En eventos de cadetes aplica PS34 (Shido).",
            extended_analysis="No se extiende automáticamente a seniors sin disposición expresa.",
            limitations="Válido exclusivamente para categoría cadetes según G1.3."
        )
        sanitized = self.validator.sanitize_structured_answer(struct)
        self.assertIn("PS34", sanitized.summary)
        self.assertIn("cadetes", sanitized.limitations)

    def test_case_04_shido_accumulation_consistency(self):
        """4. Consulta sobre acumulación de Shidos y Hansoku-make."""
        text = "La acumulación de shidos no inventa códigos ni autoridades."
        verif = self.validator.validate_text(text)
        self.assertTrue(verif.is_valid)

    def test_case_05_unsupported_administrative_procedure_flagged(self):
        """5. Consulta sobre procedimientos administrativos no mencionados en la norma."""
        text = "El árbitro remite el caso a la comisión ad hoc para abrir un formulario de informe disciplinario."
        verif = self.validator.validate_text(text)
        self.assertFalse(verif.is_valid)
        self.assertTrue(any("comisión ad hoc" in c for c in verif.unsupported_claims))

        struct = StructuredAnswer(
            summary="El árbitro decide.",
            extended_analysis="Se convoca a la comisión ad hoc para resolver."
        )
        sanitized = self.validator.sanitize_structured_answer(struct)
        self.assertIn("Control de Rigor Normativo", sanitized.limitations)
        self.assertIn("comisión ad hoc", sanitized.limitations)

    def test_case_06_unsupported_article_citation_detected(self):
        """6. Consulta con una referencia a un artículo que no respalda la afirmación."""
        text = "Conforme al Artículo 21 se debe consultar al supervisor."
        verif = self.validator.validate_text(text)
        self.assertFalse(verif.is_valid)
        self.assertIn("21", verif.hallucinated_articles)

        struct = StructuredAnswer(
            summary="Aplicable según Art. 21 del SOR.",
            extended_analysis="Detalles bajo Article 21."
        )
        sanitized = self.validator.sanitize_structured_answer(struct)
        self.assertIn("[Art. 21 no presente en contexto oficial]", sanitized.summary)
        self.assertIn("Artículos invocados sin respaldo", sanitized.limitations)

    def test_case_07_multi_passage_coordination(self):
        """7. Pregunta cuya respuesta requiera varios apartados."""
        text = "Aplica Art. 18.1.4 y Art. G1.3 con código PS35."
        verif = self.validator.validate_text(text)
        self.assertTrue(verif.is_valid)
        self.assertEqual(len(verif.hallucinated_codes), 0)
        self.assertEqual(len(verif.hallucinated_articles), 0)

    def test_case_08_legitimate_paraphrase_accepted(self):
        """8. Consulta legítima con paráfrasis fiel sin repetición literal."""
        text = "Si un competidor de categoría cadete utiliza la testa para salvaguardarse, se le impondrá una penalización leve."
        verif = self.validator.validate_text(text)
        self.assertTrue(verif.is_valid)

    def test_case_09_strict_abstention_on_out_of_scope(self):
        """9. Consulta fuera de alcance o con evidencia insuficiente."""
        mgr = MultiProviderLLMManager(gemini_api_key=None, groq_api_key=None)
        ada = ArbitrationDecisionAssistant(llm_manager=mgr)
        res = ada.analyze_situation("reglamento de pit-lane y parada en boxes fórmula 1")
        self.assertEqual(res["status"], "ABSTAIN")
        self.assertIn("Abstención Normativa Oficial", res["structured_answer"]["summary"])
        self.assertEqual(len(res["evidence"]), 0)

    def test_case_10_hallucinated_passage_id_stripped(self):
        """10. Respuesta de proveedor que invente una cita de pasaje inexistente."""
        struct = StructuredAnswer(
            summary="Regla aplicable [SOR-2026-08-P999-S999].",
            citations=["SOR-2026-08-P255-S269", "SOR-2026-08-P999-S999"]
        )
        sanitized = self.validator.sanitize_structured_answer(struct)
        self.assertIn("SOR-2026-08-P255-S269", sanitized.citations)
        self.assertNotIn("SOR-2026-08-P999-S999", sanitized.citations)

    def test_case_11_authentic_code_semantic_mismatch_detected(self):
        """11. Código auténtico (PS34) aplicado erróneamente a una infracción diferente (falso ataque)."""
        text = "El falso ataque reiterado se sanciona de inmediato con el código PS34."
        verif = self.validator.validate_text(text)
        self.assertFalse(verif.is_valid)
        self.assertTrue(any("Incoherencia semántica" in m for m in verif.semantic_mismatches))

        struct = StructuredAnswer(
            summary="El falso ataque se penaliza con PS34.",
            extended_analysis="Infracción de falso ataque."
        )
        sanitized = self.validator.sanitize_structured_answer(struct)
        self.assertIn("Inconsistencia semántica detectada", sanitized.limitations)

    def test_case_12_cadet_rule_extrapolated_to_seniors_detected(self):
        """12. Regla específica de cadetes extrapolada indebidamente a seniors."""
        text = "La prohibición de usar la cabeza aplica también a seniors y en todas las edades con PS34."
        verif = self.validator.validate_text(text)
        self.assertFalse(verif.is_valid)
        self.assertTrue(any("Extrapolación no demostrada" in s or "exclusivo de cadetes" in s for s in verif.scope_violations))

        struct = StructuredAnswer(
            summary="Aplica también a seniors en todas las edades.",
            extended_analysis="Prohibición general para seniors con PS34."
        )
        sanitized = self.validator.sanitize_structured_answer(struct)
        self.assertIn("Discrepancia de categoría o ámbito", sanitized.limitations)

    def test_case_13_incorrect_shido_to_hansoku_make_progression_detected(self):
        """13. Detección adversarial: Afirmar falsamente que el segundo Shido conlleva Hansoku-make."""
        text = "Si un judoka comete una falta leve recibe Shido, y un segundo shido conlleva hansoku-make directo."
        verif = self.validator.validate_text(text)
        self.assertFalse(verif.is_valid)
        self.assertTrue(any("Error normativo crítico en progresión de sanciones" in m for m in verif.semantic_mismatches))
        self.assertTrue(any("TERCER" in m for m in verif.semantic_mismatches))

        struct = StructuredAnswer(
            summary="El segundo shido conlleva hansoku-make.",
            extended_analysis="Dos shidos conllevan hansoku-make en el combate."
        )
        sanitized = self.validator.sanitize_structured_answer(struct)
        self.assertIn("Inconsistencia semántica detectada", sanitized.limitations)
        self.assertIn("TERCER (3er) Shido", sanitized.limitations)

    def test_case_14_wasting_time_first_occurrence_warning_procedure(self):
        """14. Procedimiento de pérdida de tiempo: no sancionar con Shido en la primera ocurrencia."""
        # Afirmación incorrecta: primera vez se sanciona con Shido
        incorrect_text = "En la primera infracción por perder tiempo la primera vez se sanciona con shido de inmediato."
        verif_bad = self.validator.validate_text(incorrect_text)
        self.assertFalse(verif_bad.is_valid)
        self.assertTrue(any("primera ocurrencia de pérdida de tiempo" in m for m in verif_bad.semantic_mismatches))

        # Afirmación correcta conforme al SOR (Art. 18.1.3): advertencia en la primera vez, Shido a la segunda
        correct_text = (
            "Deliberate time-wasting includes failing to return to starting position. "
            "The first occurrence will not result in a penalty, the referee will give a warning. "
            "Any subsequent occurrence will result in a shido."
        )
        verif_good = self.validator.validate_text(correct_text)
        self.assertTrue(verif_good.is_valid)


if __name__ == "__main__":
    unittest.main()

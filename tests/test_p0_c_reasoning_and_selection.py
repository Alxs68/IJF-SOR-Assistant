"""
Unit tests for Phase P0-C: Evidence Selection Contract, Intent Profiles, Sufficiency, and Traceability.
Verifies:
1. Classification of intent profiles (SANCTION, SCORE, MEASUREMENT_TIME, EXCEPTION, PROCEDURE, DEFINITION, GENERAL).
2. Qualitative sufficiency evaluation across all seven intent profiles.
3. Selection contract: rank-independent promotion of superior candidate passages (overcoming Top-1 rigidity).
4. Tie-breaking behavior: preservation of initial rank when scores are tied.
5. Complementary evidence: preservation of unselected candidates as secondary references.
6. Prevention of false promotion by shallow lexical overlap.
7. Conflict detection and non-contradiction gating in EvidenceBundle.
8. End-to-end integration across EvidenceBundle, DocumentValidator, and ResponseStructurer.
"""

import unittest
import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(root_dir, "src"))

from response_structurer import (
    IntentProfileEvaluator,
    select_rector_evidence,
    build_deterministic_structured_answer
)
from document_governance import (
    EvidenceItem,
    EvidenceRole,
    DocumentAuthority,
    ValidityStatus,
    EligibilityStatus
)
from document_validator import DocumentValidator
from rag_engine import RagEngine
from llm_provider import MultiProviderLLMManager


class TestP0CReasoningAndSelection(unittest.TestCase):

    def test_01_intent_profile_classification(self):
        """Verify query intent is correctly categorized into operational profiles."""
        evaluator = IntentProfileEvaluator()
        
        self.assertEqual(evaluator.classify_intent("¿Qué sanción aplica por agarrar la pierna?"), "SANCTION")
        self.assertEqual(evaluator.classify_intent("¿Se penaliza con Shido el agarre de solapa?"), "SANCTION")
        self.assertEqual(evaluator.classify_intent("¿Cómo se puntúa una proyección de espaldas?"), "SCORE")
        self.assertEqual(evaluator.classify_intent("¿Qué puntuación técnica se otorga si cae sobre dos codos?"), "SCORE")
        self.assertEqual(evaluator.classify_intent("¿Cuáles son las medidas oficiales del tatami?"), "MEASUREMENT_TIME")
        self.assertEqual(evaluator.classify_intent("¿Cuántos segundos dura la inmovilización?"), "MEASUREMENT_TIME")
        self.assertEqual(evaluator.classify_intent("¿Existe alguna excepción a la regla de salida de área?"), "EXCEPTION")
        self.assertEqual(evaluator.classify_intent("¿Qué procedimiento sigue el árbitro al anunciar Mate?"), "PROCEDURE")
        self.assertEqual(evaluator.classify_intent("¿Qué es un contrallance o kaeshi-waza?"), "DEFINITION")
        self.assertEqual(evaluator.classify_intent("Consideraciones sobre el espíritu de combate en judo."), "GENERAL")

    def test_02_sufficiency_evaluation_all_seven_profiles(self):
        """Verify qualitative sufficiency evaluation across all seven intent profiles."""
        evaluator = IntentProfileEvaluator()

        # 1. Sanction: sufficient vs insufficient
        suff_sanction, _ = evaluator.evaluate_sufficiency(
            "SANCTION",
            "In tachi-waza it is not allowed to grip inside the bottom of the trouser leg, and will be penalised with shido.",
            "¿Se sanciona el agarre de pantalón?"
        )
        self.assertTrue(suff_sanction)

        insuff_sanction, note_sanction = evaluator.evaluate_sufficiency(
            "SANCTION",
            "The athlete grips the trousers of the opponent.",
            "¿Qué sanción aplica?"
        )
        self.assertFalse(insuff_sanction)
        self.assertIn("no explicita la sanción", note_sanction)

        # 2. Score: sufficient vs insufficient
        suff_score, _ = evaluator.evaluate_sufficiency(
            "SCORE",
            "Ippon will be given when the athlete throws his opponent on his back with speed and force.",
            "¿Cómo se califica el lance?"
        )
        self.assertTrue(suff_score)

        insuff_score, note_score = evaluator.evaluate_sufficiency(
            "SCORE",
            "The athlete executes a throwing technique onto the mat.",
            "¿Qué puntuación recibe?"
        )
        self.assertFalse(insuff_score)
        self.assertIn("no explicita la valoración", note_score)

        # 3. Measurement / Time: sufficient vs insufficient
        suff_meas, _ = evaluator.evaluate_sufficiency(
            "MEASUREMENT_TIME",
            "The contest area must be a minimum of 8 m x 8 m with safety area of 3 m.",
            "¿Cuáles son las medidas?"
        )
        self.assertTrue(suff_meas)

        insuff_meas, note_meas = evaluator.evaluate_sufficiency(
            "MEASUREMENT_TIME",
            "The contest area should be large enough to host the match.",
            "¿Cuánto mide el área de combate?"
        )
        self.assertFalse(insuff_meas)
        self.assertIn("valor numérico y unidad", note_meas)

        # 4. Exception: sufficient vs insufficient
        suff_exc, _ = evaluator.evaluate_sufficiency(
            "EXCEPTION",
            "No score or penalty will be awarded except if the landing happens outside the safety area.",
            "¿Existe excepción a la caída?"
        )
        self.assertTrue(suff_exc)

        insuff_exc, note_exc = evaluator.evaluate_sufficiency(
            "EXCEPTION",
            "A bridge during landing is always penalised with direct Ippon.",
            "¿Cuándo no se aplica la penalización?"
        )
        self.assertFalse(insuff_exc)
        self.assertIn("condición o cláusula de excepción", note_exc)

        # 5. Procedure: sufficient vs insufficient
        suff_proc, _ = evaluator.evaluate_sufficiency(
            "PROCEDURE",
            "The referee shall announce Mate! and indicate with the official hand signal.",
            "¿Cómo actúa el árbitro?"
        )
        self.assertTrue(suff_proc)

        insuff_proc, note_proc = evaluator.evaluate_sufficiency(
            "PROCEDURE",
            "Judokas must maintain a respectful attitude.",
            "¿Qué protocolo sigue el árbitro?"
        )
        self.assertFalse(insuff_proc)
        self.assertIn("secuencia procedimental", note_proc)

        # 6. Definition: sufficient vs insufficient
        suff_def, _ = evaluator.evaluate_sufficiency(
            "DEFINITION",
            "Normal kumikata is defined as taking hold of the collar and sleeve.",
            "¿Qué es kumi-kata normal?"
        )
        self.assertTrue(suff_def)

        insuff_def, note_def = evaluator.evaluate_sufficiency(
            "DEFINITION",
            "Kumikata is used during the fight.",
            "¿Cuál es la definición reglamentaria de kumi-kata?"
        )
        self.assertFalse(insuff_def)
        self.assertIn("definición técnica o alcance", note_def)

        # 7. General: sufficient vs insufficient
        suff_gen, _ = evaluator.evaluate_sufficiency(
            "GENERAL",
            "Athletes must strictly follow the IJF sporting code of conduct during official tournaments.",
            "Código de conducta general"
        )
        self.assertTrue(suff_gen)

        insuff_gen, note_gen = evaluator.evaluate_sufficiency(
            "GENERAL",
            "Rules apply.",
            "Reglas generales"
        )
        self.assertFalse(insuff_gen)
        self.assertIn("breve o fragmentaria", note_gen)

    def test_03_selection_contract_promotes_rank2_over_rank1(self):
        """Verify that a specific matching candidate at rank 2 is promoted to rector evidence over a generic rank 1."""
        ev_knee_break = {
            'passage_id': 'SOR-2026-08-P182-S194',
            'title': 'Article 18.1.2 Shido for an Illegal Move',
            'article_id': 'Article 18.1.2',
            'page': 182,
            'text_original': 'Pictures 18.26-18.27. 16. To break the grip of the opponent with the knee or leg.'
        }
        ev_cross_grip = {
            'passage_id': 'SOR-2026-08-P178-S194',
            'title': 'Article 18.1.2 Shido for an Illegal Move',
            'article_id': 'Article 18.1.2',
            'page': 178,
            'text_original': '7. Collar and lapel, one side, cross grip, belt grip, pocket and pistol grips are allowed when the attitude of the athlete is positive.'
        }

        query = '¿Está permitido el cross grip o agarre cruzado si hay preparación positiva para atacar?'
        
        # Test selection function directly
        reordered = select_rector_evidence(query, [ev_knee_break, ev_cross_grip])
        self.assertEqual(reordered[0]['passage_id'], 'SOR-2026-08-P178-S194')
        self.assertEqual(reordered[1]['passage_id'], 'SOR-2026-08-P182-S194')

        # Test end-to-end deterministic structured answer
        ans = build_deterministic_structured_answer(query, [ev_knee_break, ev_cross_grip], [], '2026-08')
        self.assertIn('SOR-2026-08-P178-S194', ans.summary)
        self.assertIn('cross grip', ans.summary)
        self.assertIn('allowed when the attitude of the athlete is positive', ans.summary)

    def test_04_selection_contract_preserves_rank1_when_already_optimal(self):
        """Verify that when rank 1 is already optimal, the order is preserved without disturbance."""
        ev_tatami = {
            'passage_id': 'SOR-2026-08-P096-S114',
            'title': 'Field of Play',
            'article_id': '8.7',
            'page': 96,
            'text_original': 'The contest area shall be a minimum of 8 m x 8 m and a maximum of 10 m x 10 m.'
        }
        ev_safety = {
            'passage_id': 'SOR-2026-08-P095-S113',
            'title': 'Tatami Safety',
            'article_id': '8.6',
            'page': 95,
            'text_original': 'The safety area must be 3 m minimum.'
        }

        query = '¿Cuáles son las dimensiones del tatami de combate?'
        reordered = select_rector_evidence(query, [ev_tatami, ev_safety])
        self.assertEqual(reordered[0]['passage_id'], 'SOR-2026-08-P096-S114')

    def test_05_selection_contract_tie_breaking(self):
        """Verify tie-breaking: when two candidates have equal relevance scores, initial rank 0 is preserved."""
        ev_a = {
            'passage_id': 'SOR-2026-08-P100-S001',
            'title': 'General Judo Rules',
            'article_id': '1.1',
            'page': 100,
            'text_original': 'General guidelines for competition conduct and athletes.'
        }
        ev_b = {
            'passage_id': 'SOR-2026-08-P101-S002',
            'title': 'General Judo Guidelines',
            'article_id': '1.2',
            'page': 101,
            'text_original': 'General guidelines for competition conduct and athletes.'
        }
        query = 'pautas generales de competicion'
        reordered = select_rector_evidence(query, [ev_a, ev_b])
        # Rank 0 must remain at index 0 because of strict tie preservation
        self.assertEqual(reordered[0]['passage_id'], 'SOR-2026-08-P100-S001')

    def test_06_selection_contract_complementary_evidence_preservation(self):
        """Verify complementary evidence preservation: secondary candidates are retained and referenced."""
        ev_primary = {
            'passage_id': 'SOR-2026-08-P180-S194',
            'title': 'Article 18.1.2 Shido for an Illegal Move',
            'article_id': 'Article 18.1.2',
            'page': 180,
            'text_original': 'In tachi-waza it is allowed to grip inside the sleeve as tori and as uke.'
        }
        ev_secondary = {
            'passage_id': 'SOR-2026-08-P184-S194',
            'title': 'Article 18.1.2 Shido for an Illegal Move',
            'article_id': 'Article 18.1.2',
            'page': 184,
            'text_original': 'Supplementary sleeve and belt checking rules.'
        }
        query = '¿Se permite el agarre de bocamanga en tachi-waza?'
        ans = build_deterministic_structured_answer(query, [ev_primary, ev_secondary], [], '2026-08')
        
        # Primary is cited in summary
        self.assertIn('SOR-2026-08-P180-S194', ans.summary)
        # Secondary is preserved as complementary in summary
        self.assertIn('Disposiciones complementarias aplicables en Art. Article 18.1.2 (Pág. 184)', ans.summary)
        # Both appear in normative basis
        self.assertIn('SOR-2026-08-P180-S194', ans.normative_basis)
        self.assertIn('SOR-2026-08-P184-S194', ans.normative_basis)

    def test_07_shallow_lexical_overlap_prevents_false_promotion(self):
        """Verify that shallow unigram frequency (keyword stuffing) does NOT falsely promote an irrelevant candidate."""
        ev_relevant_rank0 = {
            'passage_id': 'SOR-2026-08-P177-S193',
            'title': 'Article 18.1.1 Non-Combativity',
            'article_id': '18.1.1',
            'page': 177,
            'text_original': 'The time between conventional kumikata and making an attack is 45 seconds if there is a positive progression.'
        }
        # Candidate at rank 1 has repeated generic words ("time", "judoka", "combat") but lacks the specific rule
        ev_shallow_rank1 = {
            'passage_id': 'SOR-2026-08-P010-S010',
            'title': 'Introduction and History',
            'article_id': '1.0',
            'page': 10,
            'text_original': 'Time after time during combat, judo athletes must manage their time in combat.'
        }
        query = '¿En qué momento se sanciona la falta de combatividad y cuántos segundos deben transcurrir?'
        reordered = select_rector_evidence(query, [ev_relevant_rank0, ev_shallow_rank1])
        # ev_relevant_rank0 must NOT be displaced by the shallow repetitive candidate
        self.assertEqual(reordered[0]['passage_id'], 'SOR-2026-08-P177-S193')

    def test_08_conflict_detection_prevents_contradictory_synthesis(self):
        """Verify DocumentValidator detects substantive conflict between contradictory evidence."""
        validator = DocumentValidator()
        prim = EvidenceItem(
            evidence_id="CHK-SOR-17-001",
            document_id="DOC-SOR-2026-08",
            content_text="Osaekomi of 20 seconds is awarded Ippon.",
            role=EvidenceRole.NORMA_PRIMARIA,
            authority=DocumentAuthority.TIER_1_NORMATIVE_PRIMARY,
            validity=ValidityStatus.VIGENTE,
            eligibility=EligibilityStatus.ELIGIBLE_DECISORIA,
            semantic_relevance_score=0.9
        )
        supp = EvidenceItem(
            evidence_id="CHK-HIST-001",
            document_id="DOC-IJF-REF-2016",
            content_text="Osaekomi of 15 seconds is awarded Ippon.",
            role=EvidenceRole.COMPLEMENTO_INTERPRETATIVO,
            authority=DocumentAuthority.TIER_2_OFFICIAL_AMENDMENT,
            validity=ValidityStatus.HISTORICO_DEROGADO,
            eligibility=EligibilityStatus.NO_ELEGIBLE,
            semantic_relevance_score=0.7
        )
        has_conflict, note = validator.detect_conflict(prim, supp)
        self.assertTrue(has_conflict)
        self.assertIn("Conflict", note)

    def test_09_end_to_end_evidence_bundle_rag_integration(self):
        """Verify effective integration of EvidenceBundle, DocumentValidator, and RagEngine in the live query flow."""
        local_mgr = MultiProviderLLMManager(gemini_api_key=None, groq_api_key=None)
        engine = RagEngine(root_dir, llm_manager=local_mgr)

        query = "¿Cuáles son las medidas oficiales del área de combate y el área de seguridad del tatami?"
        res = engine.query(query)

        self.assertIn('answer', res)
        self.assertIn('structured_answer', res)
        self.assertIn('retrieved_kuns', res)
        self.assertIn('certified_bundle', res)

        bundle = res['certified_bundle']
        self.assertIsNotNone(bundle)
        self.assertIn('bundle_id', bundle)
        self.assertTrue(bundle.get('is_sufficient_for_decision', False))
        self.assertFalse(bundle.get('has_unresolved_conflict', True))
        self.assertFalse(bundle.get('abstention_required', True))
        self.assertTrue(len(bundle.get('primary_normative_evidence', [])) > 0)


if __name__ == "__main__":
    unittest.main()

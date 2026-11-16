"""
Test Suite: Discrimination of Newaza and Safety Boundary Rules vs Time Wasting
=============================================================================
Verifies:
1. Osaekomi-waza extending beyond safety area limit -> Article 17, Page 174 (Ippon Sore-Made).
2. General ne-waza continuation outside contest area -> Article 5(b)/(c), Page 151 (progression).
3. Kansetsu-waza / shime-waza / ne-waza outside safety area without Mate -> Article 5(d), Page 152 (Consultation).
4. Deliberate time wasting / failing to return to starting position -> Article 18.1.3 (P188/P165/P176, Shido progression).
5. Exact quote and text snippet relevance for highlighted citations in Split View.
"""

import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from rre_engine import ReasoningRetrievalEngine
from ada_assistant import ArbitrationDecisionAssistant
from response_structurer import build_deterministic_structured_answer
from unittest.mock import patch
from tests._ada_contract_helpers import (
    StubLLM, answer_citing, cite_first_delivered, citation_ids,
    delivered_ids_in_result, delivered_primary_ids, ABSTENTION_MARKER, TRANSLATION_MARKER,
)


class TestNewazaBoundaryRules(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rre = ReasoningRetrievalEngine()
        cls.ada = ArbitrationDecisionAssistant()

    def test_01_osaekomi_beyond_safety_area_retrieves_p174_top1(self):
        """Osaekomi-waza beyond safety area must retrieve Article 17 P174 as Top-1 evidence."""
        query = "concesion de Ippon cuando una accion de ne-waza o inmovilizacion osaekomi alcanza o sobrepasa el limite exterior del area de seguridad"
        res = self.rre.retrieve(query, top_k=4)

        self.assertEqual(res["status"], "SUCCESS")
        self.assertTrue(len(res["evidence"]) > 0)

        top_ev = res["evidence"][0]
        self.assertEqual(top_ev["passage_id"], "SOR-2026-08-P174-S190")
        self.assertEqual(top_ev["page"], 174)
        normalized_text = " ".join(top_ev["text_original"].lower().split())
        self.assertIn("beyond the limit of the safety area", normalized_text)

    def test_02_osaekomi_beyond_safety_area_answer_and_quote(self):
        """Safety-boundary passage P174 is delivered; no generator -> ABSTAIN without citations;
        a generator citing the delivered P174 -> SUCCESS whose citation quotes the boundary rule."""
        query = "concesion de Ippon cuando una accion de ne-waza o inmovilizacion osaekomi alcanza o sobrepasa el limite exterior del area de seguridad"
        p174 = "SOR-2026-08-P174-S190"

        with patch.object(self.ada, "_call_llm", StubLLM()):
            offline = self.ada.analyze_situation(query)
        self.assertEqual(offline["status"], "ABSTAIN")
        self.assertEqual(offline["structured_answer"]["citations"], [])
        delivered = {e["passage_id"]: e for e in offline["evidence"] + offline["related_passages"]}
        self.assertIn(p174, delivered)
        normalized_text = " ".join(delivered[p174]["text_original"].lower().split())
        self.assertIn("beyond the limit of the safety area", normalized_text)

        stub = StubLLM(answer_citing([p174]))
        with patch.object(self.ada, "_call_llm", stub):
            res = self.ada.analyze_situation(query)
        self.assertIn(p174, delivered_primary_ids(stub.analysis_prompts[0]))
        self.assertEqual(res["status"], "SUCCESS")
        struct = res["structured_answer"]
        self.assertEqual(citation_ids(res), [p174])
        # Exact quote and snippet for the P174 citation must capture the safety area boundary sentence
        cit = struct["citations"][0]
        quote_and_snippet = cit["exact_quote"].lower() + " " + cit["text_snippet"].lower()
        self.assertIn("beyond", quote_and_snippet)
        self.assertIn("safety area", quote_and_snippet)
        self.assertIn("ippon", cit["text_snippet"].lower())
        self.assertNotIn("pérdida de tiempo", struct["extended_analysis"].lower())

    def test_03_general_newaza_continuity_outside_contest_area(self):
        """Ne-waza continuity outside contest area (within safety area) references Article 5."""
        query = "continuidad de acciones de ne-waza y agarre en el suelo fuera del area de combate"
        res = self.rre.retrieve(query, top_k=5)

        self.assertEqual(res["status"], "SUCCESS")
        retrieved_pids = [e["passage_id"] for e in res["evidence"]]
        # Must include Article 5 page 151 or 152
        self.assertTrue("SOR-2026-08-P151-S178" in retrieved_pids or "SOR-2026-08-P152-S179" in retrieved_pids)

    def test_04_kansetsu_shime_outside_safety_area_consultation(self):
        """Kansetsu/shime or newaza outside safety area without Mate requires consultation with IJF Referee Directors."""
        query = "ne-waza o kansetsu-waza fuera del area de seguridad sin que el arbitro haya cantado Mate"
        res = self.rre.retrieve(query, top_k=4)

        self.assertEqual(res["status"], "SUCCESS")
        retrieved_pids = [e["passage_id"] for e in res["evidence"]]
        self.assertIn("SOR-2026-08-P152-S179", retrieved_pids)

        p152 = next(e for e in res["evidence"] if e["passage_id"] == "SOR-2026-08-P152-S179")
        self.assertIn("consultation with the ijf head referee director", p152["text_original"].lower())

    def test_05_time_wasting_shido_progression(self):
        """Time-wasting query: no generator, or a generator that cites nothing -> ABSTAIN with no
        sanction stated; retrieved evidence is kept for consultation and no conclusion is invented."""
        query = "Si un competidor no regresa a la posicion de inicio que le corresponde, quedandose en el suelo y perdiendo tiempo, que debe realizar el arbitro?"
        forbidden = ("primera ocurrencia", "segunda ocurrencia", "shido", "hansoku-make")

        for stub in (StubLLM(), StubLLM(answer_citing([]))):
            with patch.object(self.ada, "_call_llm", stub):
                res = self.ada.analyze_situation(query)
            self.assertEqual(res["status"], "ABSTAIN")
            struct = res["structured_answer"]
            self.assertEqual(struct["citations"], [])
            produced = (struct["summary"] + " " + struct["extended_analysis"]).lower()
            for token in forbidden:
                self.assertNotIn(token, produced)
            self.assertNotIn("beyond the limit of the safety area", struct["extended_analysis"].lower())
            self.assertTrue(len(res["evidence"]) > 0)

if __name__ == "__main__":
    unittest.main()

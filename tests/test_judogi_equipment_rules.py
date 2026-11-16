import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from rag_engine import RagEngine
from rre_engine import ReasoningRetrievalEngine
from response_structurer import build_deterministic_structured_answer
from unittest.mock import patch
from tests._ada_contract_helpers import (
    StubLLM, answer_citing, cite_first_delivered, citation_ids,
    delivered_ids_in_result, delivered_primary_ids, ABSTENTION_MARKER, TRANSLATION_MARKER,
)


class TestJudogiEquipmentRules(unittest.TestCase):
    """
    Test suite for Judogi equipment and color rules verification (SOR 2026-08).
    Ensures precise retrieval, two-tier answer pertinence, and segregation of related rules.
    """

    @classmethod
    def setUpClass(cls):
        cls.brain_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.engine = RagEngine(cls.brain_path)
        cls.rre = cls.engine.rre

    def test_judogi_color_query_retrieval(self):
        """¿Cuáles son las reglas de color de Judogi? must retrieve C1.9 Judogi Colour in Top-1."""
        query = "¿Cuáles son las reglas de color de Judogi?"
        res = self.rre.retrieve(query, top_k=3)
        self.assertEqual(res.get("status"), "SUCCESS")
        evidence = res.get("evidence", [])
        self.assertGreaterEqual(len(evidence), 1)
        top1 = evidence[0]
        self.assertEqual(top1.get("passage_id"), "SOR-2026-08-P124-S164")
        self.assertEqual(top1.get("article_id"), "C1.9")
        self.assertEqual(top1.get("page"), 124)

    def test_allowed_judogi_colors_query_retrieval(self):
        """¿Qué colores de judogi están permitidos? must retrieve C1.9 Judogi Colour in Top-1."""
        query = "¿Qué colores de judogi están permitidos?"
        res = self.rre.retrieve(query, top_k=3)
        self.assertEqual(res.get("status"), "SUCCESS")
        top1 = res.get("evidence", [])[0]
        self.assertEqual(top1.get("passage_id"), "SOR-2026-08-P124-S164")
        self.assertEqual(top1.get("article_id"), "C1.9")

    def test_reversible_judogi_query_retrieval(self):
        """¿Puede utilizarse un judogi reversible blanco y azul? must retrieve C1.1 (p. 115) forbidding reversibles."""
        query = "¿Puede utilizarse un judogi reversible blanco y azul?"
        res = self.rre.retrieve(query, top_k=3)
        self.assertEqual(res.get("status"), "SUCCESS")
        top1 = res.get("evidence", [])[0]
        self.assertIn("115", str(top1.get("page")))
        self.assertIn("C1.1", str(top1.get("article_id")))

    def test_marks_and_patches_query_retrieval(self):
        """¿Qué requisitos existen para las marcas y los parches del judogi? must retrieve marking/patch rules."""
        query = "¿Qué requisitos existen para las marcas y los parches del judogi?"
        res = self.rre.retrieve(query, top_k=3)
        self.assertEqual(res.get("status"), "SUCCESS")
        top1 = res.get("evidence", [])[0]
        self.assertIn(top1.get("article_id"), ["C1.7", "C1.3", "C1.2", "C1.6"])

    def test_sleeve_measurements_sokuteiki_retrieval(self):
        """¿Cuáles son las reglas de medida de las mangas del judogi y el control con sokuteiki? must retrieve C1.10."""
        query = "¿Cuáles son las reglas de medida de las mangas del judogi y el control con sokuteiki?"
        res = self.rre.retrieve(query, top_k=3)
        self.assertEqual(res.get("status"), "SUCCESS")
        top1 = res.get("evidence", [])[0]
        self.assertEqual(top1.get("article_id"), "C1.10")
        self.assertEqual(top1.get("page"), 124)

    def test_belt_colors_query_retrieval(self):
        """¿Qué colores están permitidos para el cinturón? must retrieve belt regulation (C1.1/C1.2), not Judogi Colour."""
        query = "¿Qué colores están permitidos para el cinturón?"
        res = self.rre.retrieve(query, top_k=3)
        self.assertEqual(res.get("status"), "SUCCESS")
        top_articles = [e.get("article_id") for e in res.get("evidence", [])]
        self.assertTrue(any("C1.1" in str(a) or "C1.2" in str(a) for a in top_articles))
        # Ensure C1.9 (Judogi Colour) is not misattributed as top-1 for belt color
        self.assertNotEqual(res.get("evidence", [])[0].get("article_id"), "C1.9")

    def test_judogi_color_answer_pertinence_and_segregation(self):
        """Judogi colour query: C1.9 (p. 124, White/Blue) is the top delivered passage. No generator ->
        ABSTAIN; a generator citing it -> SUCCESS whose only citation is C1.9 on page 124."""
        query = "¿Cuáles son las reglas de color de Judogi?"
        c19 = "SOR-2026-08-P124-S164"
        with patch.object(self.engine.ada, "_call_llm", StubLLM()):
            res = self.engine.query(query, k=3, min_score=0.10)
        self.assertIn("answer", res)
        self.assertIn(ABSTENTION_MARKER, res["answer"])
        self.assertEqual(res["structured_answer"]["citations"], [])
        top = res["retrieved_kuns_data"][0]
        self.assertEqual(top["id_conocimiento"], c19)
        self.assertEqual(top["article_id"], "C1.9")
        top_text = top["contenido_traduccion"].lower()
        self.assertIn("white", top_text)
        self.assertIn("blue", top_text)

        stub = StubLLM(answer_citing(lambda delivered: [c19] if c19 in delivered else []))
        with patch.object(self.engine.ada, "_call_llm", stub):
            res = self.engine.query(query, k=3, min_score=0.10)
        struct = res.get("structured_answer")
        self.assertIsNotNone(struct)
        self.assertEqual(citation_ids(res), [c19])
        cit = struct["citations"][0]
        self.assertIn("C1.9", str(cit["article_id"]))
        self.assertEqual(cit["page_number"], 124)

    def test_deterministic_generator_judogi_color(self):
        """Deterministic fallback formats C1.9 from the passage itself: White/Blue/Pantone come from
        the passage text and nothing outside it (e.g. reversible-judogi rule of C1.1) is added."""
        p124 = self.rre.passages_by_id["SOR-2026-08-P124-S164"]
        ev = [{
            "passage_id": p124["passage_id"],
            "title": p124.get("heading_path", [""])[0],
            "article_id": p124.get("article_id"),
            "page": p124.get("pdf_page_index"),
            "text_original": p124.get("text_original", "")
        }]
        source_text = p124.get("text_original", "")
        ans = build_deterministic_structured_answer("¿Cuáles son las reglas de color de Judogi?", ev, [], "14 August 2026")
        self.assertIn("White", ans.summary)
        self.assertIn("Blue", ans.summary)
        self.assertIn("C1.9", ans.summary)
        self.assertIn("124", ans.summary)
        self.assertIn("Pantone", ans.extended_analysis)
        self.assertIn("Snow white", ans.extended_analysis)
        self.assertEqual(ans.citations, ["SOR-2026-08-P124-S164"])
        # Content absent from the passage must not appear in the fallback output
        self.assertNotIn("reversible", source_text.lower())
        self.assertNotIn("reversible", (ans.summary + ans.extended_analysis).lower())

if __name__ == "__main__":
    unittest.main()

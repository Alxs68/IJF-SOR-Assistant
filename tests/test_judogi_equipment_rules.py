import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from rag_engine import RagEngine
from rre_engine import ReasoningRetrievalEngine
from response_structurer import build_deterministic_structured_answer


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
        """The answer to judogi color query must state White and Blue first, cite C1.9, and segregate unrelated rules."""
        query = "¿Cuáles son las reglas de color de Judogi?"
        res = self.engine.query(query, k=3, min_score=0.10)
        self.assertIn("answer", res)
        answer = res["answer"].lower()
        self.assertIn("blanco", answer)
        self.assertIn("azul", answer)
        self.assertIn("c1.9", answer)

        # Check structured answer
        struct = res.get("structured_answer")
        self.assertIsNotNone(struct)
        summary = struct.get("summary", "").lower()
        self.assertTrue(any(w in summary for w in ["blanco", "white"]))
        self.assertTrue(any(w in summary for w in ["azul", "blue"]))
        self.assertIn("c1.9", summary)
        self.assertIn("124", summary)

    def test_deterministic_generator_judogi_color(self):
        """Deterministic fallback must format C1.9 with white/blue specifications cleanly."""
        p124 = self.rre.passages_by_id["SOR-2026-08-P124-S164"]
        ev = [{
            "passage_id": p124["passage_id"],
            "title": p124.get("heading_path", [""])[0],
            "article_id": p124.get("article_id"),
            "page": p124.get("pdf_page_index"),
            "text_original": p124.get("text_original", "")
        }]
        ans = build_deterministic_structured_answer("¿Cuáles son las reglas de color de Judogi?", ev, [], "14 August 2026")
        self.assertIn("White", ans.summary)
        self.assertIn("Blue", ans.summary)
        self.assertIn("C1.9", ans.summary)
        self.assertIn("124", ans.summary)
        self.assertIn("Pantone", ans.extended_analysis)
        self.assertIn("Reversible", ans.extended_analysis)


if __name__ == "__main__":
    unittest.main()

"""
Pruebas de regresión y precisión funcional para consultas en lenguaje coloquial de judo.
Paso 2 de la Reorientación Lean: Expansión Léxica de Términos Coloquiales de Judo.
Supervisión y Aprobación: Alexis Oliveros Lozano.
"""

import unittest
from src.rre_engine import ReasoningRetrievalEngine


class TestColloquialJudoSynonyms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rre = ReasoningRetrievalEngine()

    def test_01_rodilla_palanca_ne_waza_retrieval(self):
        """Consulta coloquial sobre palanca a la rodilla en ne-waza debe recuperar Art. 18.2.2 (p. 191)."""
        query = "rodilla palanca en ne-waza"
        res = self.rre.retrieve(query, top_k=3)
        self.assertEqual(res.get("status"), "SUCCESS")
        evidence = res.get("evidence", [])
        self.assertTrue(len(evidence) > 0)
        top1 = evidence[0]
        self.assertIn("18.2.2", str(top1.get("article_id")))
        self.assertEqual(top1.get("page"), 191)

    def test_02_estrangular_pretina_faldon_desatado_retrieval(self):
        """Consulta sobre estrangular con la pretina o faldón desatado debe recuperar Art. 18.1.2 (p. 184)."""
        query = "estrangular con la pretina o faldon desatado"
        res = self.rre.retrieve(query, top_k=3)
        self.assertEqual(res.get("status"), "SUCCESS")
        evidence = res.get("evidence", [])
        self.assertTrue(len(evidence) > 0)
        top1 = evidence[0]
        self.assertIn("18.1.2", str(top1.get("article_id")))
        self.assertEqual(top1.get("page"), 184)

    def test_03_meter_pie_solapa_cinturon_retrieval(self):
        """Consulta sobre meter el pie en la solapa o cinturón debe recuperar Art. 18.1.2 (p. 184)."""
        query = "meter el pie en la solapa o cinturon"
        res = self.rre.retrieve(query, top_k=3)
        self.assertEqual(res.get("status"), "SUCCESS")
        evidence = res.get("evidence", [])
        self.assertTrue(len(evidence) > 0)
        top1 = evidence[0]
        self.assertIn("18.1.2", str(top1.get("article_id")))
        self.assertEqual(top1.get("page"), 184)

    def test_04_tirarse_cabeza_voluntario_retrieval(self):
        """Consulta sobre tirarse de cabeza voluntario debe recuperar Art. 18.2.1 (p. 190)."""
        query = "tirarse de cabeza voluntario"
        res = self.rre.retrieve(query, top_k=3)
        self.assertEqual(res.get("status"), "SUCCESS")
        evidence = res.get("evidence", [])
        self.assertTrue(len(evidence) > 0)
        top1 = evidence[0]
        self.assertIn("18.2.1", str(top1.get("article_id")))
        self.assertEqual(top1.get("page"), 190)


if __name__ == "__main__":
    unittest.main()

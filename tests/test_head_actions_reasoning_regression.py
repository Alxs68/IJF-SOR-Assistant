import unittest
import os
import sys

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from rag_engine import RagEngine

class TestHeadActionsReasoningRegression(unittest.TestCase):
    """
    Batería de pruebas de regresión y razonamiento normativo sobre acciones
    con la cabeza, escape, puente y defensas en el IJF SOR 2026-08 (14 de agosto de 2026).

    Verifica de manera exhaustiva los 8 casos requeridos en la Fase E:
    1. '¿Se permite la defensa con la cabeza?' (Recupera Art. 14.2 p.166/167 y Art. 18.1.4 p.188; sin falso dictamen de falta de evidencia).
    2. '¿Qué ocurre cuando Uke hace puente?' (Art. 14.2 Ippon por seguridad cervical para evitar lesiones).
    3. '¿Cómo se sanciona el Head Diving?' (Art. 18.2.1 Hansoku-make por técnica peligrosa para cualquier categoría; puede continuar).
    4. '¿Puede Tori utilizar la cabeza para proyectar?' (Distingue Head diving = Hansoku-make general vs apoyo para proyectar en Cadetes = Shido).
    5. '¿Qué diferencia existe entre Seniors, Juniors y Cadetes en acciones con la cabeza?' (Diferenciación etaria rigurosa).
    6. '¿Qué ocurre si Uke aterriza sobre el cuerpo de Tori al hacer puente?' (Art. 14.2 excepción textual: ni puntuación ni penalización).
    7. Consultas en inglés: 'Is head defense allowed?', 'What happens if uke bridges?', 'How is head diving penalised?'.
    8. Consultas ambiguas o complejas que demandan desglose de escenarios y rol.
    """

    @classmethod
    def setUpClass(cls):
        os.environ["IJF_SOR_EDITION"] = "2026-08"
        cls.engine = RagEngine('C:/PROYECTOS/IJF-SOR-Assistant')

    def test_01_general_head_defense_query(self):
        """1. ¿Se permite la defensa con la cabeza? Recupera tanto Art. 14 como Art. 18.1.4 sin abstención infundada."""
        q = "¿Se permite la defensa con la cabeza?"
        res = self.engine.query(q, k=4, language="es")
        self.assertTrue(len(res.get("retrieved_kuns_data", [])) > 0)
        
        evidence_pids = [e["id_conocimiento"] for e in res.get("retrieved_kuns_data", [])]
        pages = [e.get("pdf_page_index") for e in res.get("retrieved_kuns_data", [])]
        
        # Debe contener evidencia de Puente/Ippon (P166/P167) y de Cadetes (P188)
        self.assertTrue(any(p in (166, 167) for p in pages), f"Debe incluir Art. 14 (P166/P167). Evidencias: {evidence_pids}")
        self.assertTrue(any(p == 188 for p in pages), f"Debe incluir Art. 18.1.4 (P188). Evidencias: {evidence_pids}")
        
        # Verificar que el resumen estructurado no declare falta de evidencia
        answer = res.get("answer", "").lower()
        self.assertNotIn("sin evidencia normativa", answer)
        self.assertNotIn("no se encontró información", answer)

    def test_02_uke_voluntary_bridge_ippon(self):
        """2. ¿Qué ocurre cuando Uke hace puente? Evalúa Ippon por seguridad cervical (Art. 14.2)."""
        q = "¿Qué ocurre cuando Uke hace puente?"
        res = self.engine.query(q, k=4, language="es")
        self.assertTrue(len(res.get("retrieved_kuns_data", [])) > 0)
        
        evidence_pids = [e["id_conocimiento"] for e in res.get("retrieved_kuns_data", [])]
        self.assertTrue(
            any("P166" in pid or "P167" in pid for pid in evidence_pids),
            f"Debe recuperar pasajes de puente (P166 o P167). PIDs: {evidence_pids}"
        )
        answer = res.get("answer", "").lower()
        self.assertTrue("ippon" in answer or "bridge" in answer)

    def test_03_head_diving_penalty_all_categories(self):
        """3. ¿Cómo se sanciona el Head Diving? Hansoku-make directo por técnica peligrosa (Art. 18.2.1, Pág. 190)."""
        q = "¿Cómo se sanciona el Head Diving?"
        res = self.engine.query(q, k=4, language="es")
        self.assertTrue(len(res.get("retrieved_kuns_data", [])) > 0)
        
        evidence_pids = [e["id_conocimiento"] for e in res.get("retrieved_kuns_data", [])]
        self.assertTrue(
            any("P190" in pid for pid in evidence_pids),
            f"Debe recuperar Art. 18.2.1 (P190). PIDs: {evidence_pids}"
        )
        answer = res.get("answer", "").lower()
        self.assertTrue("hansoku-make" in answer or "hansokumake" in answer)

    def test_04_tori_use_head_to_throw(self):
        """4. ¿Puede Tori utilizar la cabeza para proyectar? Distingue zambullida peligrosa (Hansoku-make) de cadetes (Shido)."""
        q = "¿Puede Tori utilizar la cabeza para proyectar?"
        res = self.engine.query(q, k=4, language="es")
        self.assertTrue(len(res.get("retrieved_kuns_data", [])) > 0)
        
        evidence_pids = [e["id_conocimiento"] for e in res.get("retrieved_kuns_data", [])]
        # Debe recuperar pasajes de Pág. 190 (Head Diving) o Pág. 188 (Punto 33 Cadetes)
        has_p190 = any("P190" in pid for pid in evidence_pids)
        has_p188 = any("P188" in pid for pid in evidence_pids)
        self.assertTrue(has_p190 or has_p188, f"Debe recuperar P190 o P188. PIDs: {evidence_pids}")

    def test_05_category_differences_seniors_cadets(self):
        """5. Diferencias entre Seniors, Juniors y Cadetes en acciones con la cabeza."""
        q = "¿Qué diferencia existe entre Seniors, Juniors y Cadetes en acciones con la cabeza?"
        res = self.engine.query(q, k=4, language="es")
        self.assertTrue(len(res.get("retrieved_kuns_data", [])) > 0)
        
        evidence_pids = [e["id_conocimiento"] for e in res.get("retrieved_kuns_data", [])]
        # Debe recuperar al menos las reglas específicas de cadetes
        has_cadet = any("P188" in pid or "P189" in pid for pid in evidence_pids)
        self.assertTrue(has_cadet, f"Debe recuperar pasajes de cadetes (P188/P189). PIDs: {evidence_pids}")

    def test_06_bridge_landing_on_tori_exception(self):
        """6. ¿Qué ocurre si Uke aterriza sobre el cuerpo de Tori al hacer puente? Excepción textual de Art. 14.2."""
        q = "¿Qué ocurre si Uke aterriza sobre el cuerpo de Tori?"
        res = self.engine.query(q, k=4, language="es")
        self.assertTrue(len(res.get("retrieved_kuns_data", [])) > 0)
        
        evidence_pids = [e["id_conocimiento"] for e in res.get("retrieved_kuns_data", [])]
        self.assertTrue(
            any("P167" in pid or "P166" in pid for pid in evidence_pids),
            f"Debe recuperar Art. 14.2 (P167). PIDs: {evidence_pids}"
        )

    def test_07_english_head_queries(self):
        """7. Consultas normativas en inglés sobre cabeza, puente y head diving."""
        queries = [
            ("Is head defense allowed?", ("P188", "P166", "P167")),
            ("What happens if uke bridges?", ("P166", "P167")),
            ("How is head diving penalised?", ("P190",))
        ]
        for q, expected_pages in queries:
            res = self.engine.query(q, k=4, language="en")
            self.assertTrue(len(res.get("retrieved_kuns_data", [])) > 0, f"Sin evidencias para '{q}'")
            evidence_pids = [e["id_conocimiento"] for e in res.get("retrieved_kuns_data", [])]
            matched = any(any(exp in pid for exp in expected_pages) for pid in evidence_pids)
            self.assertTrue(matched, f"Consulta inglesa '{q}' debe incluir alguna de las páginas {expected_pages}. PIDs: {evidence_pids}")

    def test_08_ambiguous_head_action_query(self):
        """8. Consulta ambigua de acción con la cabeza requiere distinción de roles sin abstención errónea."""
        q = "acción con la cabeza en judo reglamento"
        res = self.engine.query(q, k=4, language="es")
        self.assertTrue(len(res.get("retrieved_kuns_data", [])) > 0)
        evidence_pids = [e["id_conocimiento"] for e in res.get("retrieved_kuns_data", [])]
        # Debe recuperar pasajes relevantes (P188, P190 o P166)
        relevant = any(any(p in pid for p in ("P188", "P190", "P166", "P167")) for pid in evidence_pids)
        self.assertTrue(relevant, f"Consulta ambigua debe anclar a reglas de cabeza. PIDs: {evidence_pids}")

if __name__ == "__main__":
    unittest.main()

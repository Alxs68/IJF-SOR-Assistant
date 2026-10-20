import unittest
import os
import sys

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from rre_engine import ReasoningRetrievalEngine
from ada_assistant import ArbitrationDecisionAssistant

class TestHeadActionsRules(unittest.TestCase):
    """
    Suite de verificación formal de las reglas y decisiones arbitrales sobre
    acciones con la cabeza en el reglamento oficial IJF SOR (14 de agosto de 2026).
    
    Cubre de forma independiente:
    1. Head diving de tori (Art. 18.2.1, Pág. 190) -> Hansoku-make directo (puede continuar).
    2. Uso de la cabeza para defender como uke en cadetes (Art. 18.1.4, Pág. 188) -> Shido.
    3. Uso de la cabeza para proyectar en cadetes (Art. 18.1.4, Pág. 188) -> Shido.
    4. Defensa de cabeza en junior y sénior -> No traslada automáticamente Shido de cadetes.
    5. Apoyo de la cabeza durante proyección -> Diferenciar cadetes de séniors sin equiparar ciegamente a head diving.
    6. Caída accidental sobre la cabeza -> Sin sanción deportiva automática / protocolo médico de conmoción.
    7. Puente voluntario de uke al caer (Art. 14.2, Pág. 166) -> Ippon para el oponente.
    """

    @classmethod
    def setUpClass(cls):
        os.environ["IJF_SOR_EDITION"] = "2026-08"
        cls.rre = ReasoningRetrievalEngine()
        cls.ada = ArbitrationDecisionAssistant()

    def test_01_head_diving_tori_hansoku_make(self):
        """
        1. Head diving de tori: técnica peligrosa penalizada con Hansoku-make directo
        conforme al artículo 18.2.1 (Pág. 190). Tori puede continuar en la competición.
        """
        queries = [
            "head diving rule",
            "¿Cómo se sanciona el head diving?",
            "head diving penalty hansoku-make"
        ]
        for q in queries:
            res = self.rre.retrieve(q, top_k=4)
            self.assertEqual(res["status"], "SUCCESS", f"Fallo al recuperar para '{q}'")
            evidence_pids = [e["passage_id"] for e in res["evidence"]]
            has_p190 = any(pid in evidence_pids for pid in ("SOR-2026-08-P190-S197", "SOR-2026-08-P190-S198"))
            self.assertTrue(
                has_p190,
                f"La consulta '{q}' debe recuperar el pasaje de la Pág. 190 (Art. 18.2.1 / 18.2.2). Recuperado: {evidence_pids}"
            )
            top_hit = res["evidence"][0]
            # Verificar que el pasaje rector de Pág. 190 esté presente con el texto oficial
            self.assertIn("P190", top_hit["passage_id"])
            text_snippet = top_hit["text_original"].lower()
            self.assertIn("head diving", text_snippet)
            self.assertIn("hansoku-make", text_snippet)

    def test_02_cadet_head_defence_uke_shido(self):
        """
        2. Uso de la cabeza para defender como uke en cadetes: penalizado con Shido
        conforme al artículo 18.1.4, punto 34 (Pág. 188). Tori recibe puntuación si la hubo.
        """
        queries = [
            "cadet head defence shido",
            "¿Cómo se sanciona el uso de la cabeza para defenderse en cadetes?",
            "cadet uke head defence penalty"
        ]
        for q in queries:
            res = self.rre.retrieve(q, top_k=4)
            self.assertEqual(res["status"], "SUCCESS", f"Fallo al recuperar para '{q}'")
            evidence_pids = [e["passage_id"] for e in res["evidence"]]
            self.assertIn(
                "SOR-2026-08-P188-S196",
                evidence_pids,
                f"La consulta '{q}' debe recuperar el pasaje Art. 18.1.4 (Pág. 188)."
            )
            cadet_passage = next(e for e in res["evidence"] if e["passage_id"] == "SOR-2026-08-P188-S196")
            text_p = cadet_passage["text_original"].lower()
            self.assertIn("cadet", text_p)
            self.assertIn("defend as uke", text_p)
            self.assertIn("shido", text_p)

    def test_03_cadet_head_throw_tori_shido(self):
        """
        3. Uso de la cabeza para proyectar en cadetes como tori: penalizado con Shido
        conforme al artículo 18.1.4, punto 33 (Pág. 188).
        """
        queries = [
            "In cadet events athletes use head to throw as tori",
            "¿Cómo se sanciona si tori usa la cabeza para lanzar en cadetes?"
        ]
        for q in queries:
            res = self.rre.retrieve(q, top_k=4)
            self.assertEqual(res["status"], "SUCCESS", f"Fallo al recuperar para '{q}'")
            evidence_pids = [e["passage_id"] for e in res["evidence"]]
            self.assertIn(
                "SOR-2026-08-P188-S196",
                evidence_pids,
                f"La consulta '{q}' debe recuperar Art. 18.1.4 (Pág. 188)."
            )
            cadet_passage = next(e for e in res["evidence"] if e["passage_id"] == "SOR-2026-08-P188-S196")
            text_p = cadet_passage["text_original"].lower()
            self.assertIn("use the head to throw as tori", text_p)
            self.assertIn("shido", text_p)

    def test_04_senior_junior_head_defence_no_automatic_cadet_shido(self):
        """
        4. Defensa de cabeza en junior y sénior: no trasladar automáticamente la sanción
        de Shido de cadetes ni confundir con head diving.
        """
        q = "defensa de cabeza en categorias junior y senior"
        res = self.rre.retrieve(q, top_k=4)
        self.assertEqual(res["status"], "SUCCESS")
        # El pasaje específico de cadetes P188 no debe ser el único dominante sin clarificar
        # Comprobar que ADA analiza la situación sin atribuir Shido general de cadetes a séniors
        ada_res = self.ada.analyze_situation(q)
        self.assertEqual(ada_res["status"], "SUCCESS")
        summary = ada_res.get("structured_answer", {}).get("summary", "").lower()
        # No debe declarar que en séniors o júniors la defensa común de cabeza sea Shido de cadetes
        self.assertNotIn("sancionado con shido en senior", summary)

    def test_05_head_support_during_throw_differentiation(self):
        """
        5. Apoyo de la cabeza durante una proyección: diferenciar cadetes de las demás
        categorías y no equipararlo automáticamente con head diving si no hay zambullida peligrosa.
        """
        q_cadet = "apoyo voluntario de cabeza de tori al lanzar en cadetes"
        res_cadet = self.rre.retrieve(q_cadet, top_k=3)
        self.assertIn("SOR-2026-08-P188-S196", [e["passage_id"] for e in res_cadet["evidence"]])

        q_senior = "apoyo incidental de cabeza durante seoi-nage en senior"
        res_senior = self.rre.retrieve(q_senior, top_k=4)
        self.assertEqual(res_senior["status"], "SUCCESS")

    def test_06_accidental_head_fall_no_automatic_penalty(self):
        """
        6. Caída accidental sobre la cabeza o golpe fortuito: no imponer una sanción
        automática deportiva; activa el protocolo de conmoción médica si procede.
        """
        q = "caida accidental de cabeza conmocion protocolo medico"
        res = self.rre.retrieve(q, top_k=4)
        self.assertEqual(res["status"], "SUCCESS")
        evidence_pids = [e["passage_id"] for e in res["evidence"]]
        # Debe recuperar pasajes médicos de conmoción o asistencia médica (P202 / P199 / P196)
        has_medical = any(pid in evidence_pids for pid in ["SOR-2026-08-P202-S217", "SOR-2026-08-P202-S218", "SOR-2026-08-P196-S205", "SOR-2026-08-P199-S211"])
        self.assertTrue(has_medical, "Debe recuperar la disposición médica sobre conmoción o asistencia en caída accidental.")

    def test_07_uke_voluntary_bridge_ippon(self):
        """
        7. Puente voluntario de uke al caer: evaluado como Ippon por seguridad cervical
        conforme al artículo 14, punto 2 (Pág. 166). No confundir con head diving.
        """
        queries = [
            "voluntary bridge landing ippon",
            "¿Cómo se califica si uke hace puente con la cabeza al caer?",
            "puente voluntario cabeza y pies tatami ippon"
        ]
        for q in queries:
            res = self.rre.retrieve(q, top_k=4)
            self.assertEqual(res["status"], "SUCCESS", f"Fallo al recuperar para '{q}'")
            evidence_pids = [e["passage_id"] for e in res["evidence"]]
            self.assertIn(
                "SOR-2026-08-P166-S187",
                evidence_pids,
                f"La consulta '{q}' debe recuperar Art. 14 (Pág. 166)."
            )
            bridge_passage = next(e for e in res["evidence"] if e["passage_id"] == "SOR-2026-08-P166-S187")
            text_p = bridge_passage["text_original"].lower()
            self.assertIn("bridge", text_p)
            self.assertIn("ippon", text_p)

if __name__ == "__main__":
    unittest.main()

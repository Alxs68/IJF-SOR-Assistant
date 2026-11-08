"""
Suite de pruebas End-to-End para la Fase P1-B: Configuración y regresión end-to-end.
IJF SOR Assistant 2026.

Verifica el contrato entre interfaz (UI), RagEngine, RRE, ADA, CitationResolver y DocumentValidator:
1. Matriz de configuración efectiva y propagación de parámetros.
2. Identificación y evaluación empírica de controles ambiguos/inoperantes (min_score).
3. Propagación real del parámetro k (top_k).
4. Propagación de idioma (es / en).
5. Exactitud normativa y trazabilidad física de citas (páginas 1 a 298 del PDF canónico).
6. Certificación del EvidenceBundle en el flujo E2E por DocumentValidator.
7. Comportamiento E2E de abstención y detección OOD.
8. Contrato de respuesta en dos niveles (Nivel 1 operativo / Nivel 2 fundamentación).
"""

import os
import sys
import unittest
import inspect
from typing import Dict, Any

# Asegurar src en sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(root_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from rag_engine import RagEngine
from llm_provider import MultiProviderLLMManager
from corpus_config import get_active_corpus_config, ACTIVE_EDITION
from document_validator import DocumentAuthority, ValidityStatus


class TestP1BConfiguracionE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.brain_path = root_dir
        cls.engine = RagEngine(cls.brain_path)

    def test_01_effective_configuration_matrix_and_active_edition(self):
        """Verifica que la configuración activa corresponde inexorablemente a la edición oficial 2026-08."""
        cfg = get_active_corpus_config()
        self.assertEqual(ACTIVE_EDITION, "2026-08")
        self.assertEqual(cfg["version_label"], "14 August 2026 (Official)")
        self.assertEqual(cfg["source_id"], "SOR-2026-08-14-ENG")
        self.assertFalse(cfg["is_legacy"])
        
        # Verificar que el motor RAG haya cargado exactamente 385 pasajes/nodos canónicos
        self.assertEqual(len(self.engine.kg.nodes), 385)
        self.assertIsNotNone(self.engine.rre)
        self.assertEqual(len(self.engine.rre.passages), 385)
        self.assertTrue(self.engine.is_2026_08)
        self.assertIsNotNone(self.engine.ada)

    def test_02_llm_manager_injection_and_propagation(self):
        """Verifica que el MultiProviderLLMManager se inyecte y sincronice entre RagEngine y ADA."""
        custom_llm = MultiProviderLLMManager(
            primary_provider="Gemini",
            fallback_policy="manual",
            gemini_model="gemini-flash-latest"
        )
        self.engine.llm_manager = custom_llm
        self.engine.ada.llm_manager = custom_llm

        self.assertIs(self.engine.llm_manager, custom_llm)
        self.assertIs(self.engine.ada.llm_manager, custom_llm)
        self.assertEqual(self.engine.ada.llm_manager.primary_provider, "Gemini")
        self.assertEqual(self.engine.ada.llm_manager.fallback_policy, "manual")

    def test_03_top_k_parameter_propagation(self):
        """Verifica que el slider k de la UI modifique el número de evidencias primarias evaluadas."""
        query = "¿Cuáles son las medidas oficiales del área de combate y el área de seguridad del tatami?"
        
        res_k1 = self.engine.query(query, k=1)
        res_k4 = self.engine.query(query, k=4)

        # En k=1 debe retornar exactamente 1 evidencia primaria en ada_res["evidence"]
        ev_k1 = [item for item in res_k1.get("retrieved_kuns_data", []) if "Referencia Cruzada" not in item.get("interpretacion", "")]
        self.assertEqual(len(ev_k1), 1, f"Con k=1 se esperaban 1 evidencia directa, obtenidas: {len(ev_k1)}")

        # En k=4 debe retornar hasta 4 evidencias primarias
        ev_k4 = [item for item in res_k4.get("retrieved_kuns_data", []) if "Referencia Cruzada" not in item.get("interpretacion", "")]
        self.assertGreater(len(ev_k4), 1, f"Con k=4 se esperaban más de 1 evidencias directas, obtenidas: {len(ev_k4)}")
        self.assertLessEqual(len(ev_k4), 4)

    def test_04_ambiguous_control_min_score_evaluation(self):
        """
        Evaluación de control inoperante/ambiguo:
        Demuestra empíricamente que en la ruta SOR 2026-08 (ADA + RRE), el parámetro min_score
        no altera los resultados devueltos, ya que RRE aplica su propio ranking denso/sparse/RRF
        y umbral interno normativo (0.12).
        """
        query = "¿Cuáles son las medidas oficiales del área de combate y el área de seguridad del tatami?"
        
        res_low_score = self.engine.query(query, k=3, min_score=0.05)
        res_high_score = self.engine.query(query, k=3, min_score=0.50)

        # Los IDs de pasajes recuperados son exactamente los mismos porque min_score no se propaga a RRE
        self.assertEqual(
            res_low_score["retrieved_kuns"],
            res_high_score["retrieved_kuns"],
            "Hallazgo P1-B: min_score no afecta la ruta 2026-08 activa (control inoperante en UI)."
        )

    def test_05_language_parameter_propagation(self):
        """Verifica que el parámetro language ('es' vs 'en') se propague a ADA y se preserve en el contrato."""
        query_es = "¿Cuáles son las medidas oficiales del tatami?"
        res_es = self.engine.query(query_es, k=3, language="es")
        self.assertIsNotNone(res_es.get("structured_answer"))
        self.assertEqual(res_es.get("query"), query_es)

        query_en = "What are the official dimensions of the tatami contest area?"
        res_en = self.engine.query(query_en, k=3, language="en")
        self.assertIsNotNone(res_en.get("structured_answer"))
        self.assertEqual(res_en.get("query"), query_en)

    def test_06_end_to_end_citation_traceability_physical_pages(self):
        """Verifica que las citas generadas tengan trazabilidad física a las 298 páginas del PDF oficial."""
        query = "¿Cuáles son las medidas oficiales del área de combate y el área de seguridad del tatami?"
        res = self.engine.query(query, k=3)
        
        struct = res.get("structured_answer", {})
        citations = struct.get("citations", [])
        self.assertTrue(len(citations) > 0, "Debe retornar citas enriquecidas.")

        for cit in citations:
            if isinstance(cit, dict):
                passage_id = cit.get("passage_id")
                page_num = cit.get("page_number")
                article_id = cit.get("article_id")
                url = cit.get("source_url")

                self.assertTrue(passage_id.startswith("SOR-2026-08-"), f"ID inválido: {passage_id}")
                self.assertIsNotNone(page_num, f"Cita sin página física: {cit}")
                self.assertGreaterEqual(int(page_num), 1, "Página física menor a 1")
                self.assertLessEqual(int(page_num), 298, "Página física excede 298")
                self.assertIn("IJF_Sport_and_Organisation_Rul", url, "URL no canónica")

    def test_07_end_to_end_document_validator_certification(self):
        """Verifica que DocumentValidator certifique el bundle de evidencias en el flujo E2E."""
        query = "¿Cuáles son las dimensiones oficiales del área de combate?"
        res = self.engine.query(query, k=3)

        certified_bundle = res.get("certified_bundle")
        self.assertIsNotNone(certified_bundle, "Debe existir un certified_bundle en la respuesta E2E.")
        self.assertFalse(certified_bundle.get("abstention_required"), "No debe abstenerse para tatami.")
        self.assertTrue(certified_bundle.get("is_sufficient_for_decision"), "Debe ser suficiente para decisión.")
        
        items = certified_bundle.get("primary_normative_evidence", [])
        self.assertTrue(len(items) > 0, "Debe incluir ítems normativos primarios certificados Tier 1.")
        for it in items:
            self.assertEqual(it.get("authority"), DocumentAuthority.TIER_1_NORMATIVE_PRIMARY.value)
            self.assertEqual(it.get("validity"), ValidityStatus.VIGENTE.value)

    def test_08_end_to_end_abstention_ood(self):
        """Verifica el flujo E2E completo ante una consulta fuera de dominio (OOD)."""
        ood_query = "¿Cuál es el tiempo reglamentario de posesión en baloncesto FIBA?"
        res = self.engine.query(ood_query, k=3)

        # Debe responder con abstención
        self.assertIn("Abstención Normativa Oficial", res["answer"])
        struct = res.get("structured_answer", {})
        self.assertIn("Abstención Normativa Oficial", struct.get("summary", ""))
        self.assertEqual(len(res.get("retrieved_kuns", [])), 0)

    def test_09_two_tier_response_presentation_contract(self):
        """Verifica el contrato de dos niveles: Nivel 1 (summary operativo) y Nivel 2 (fundamentación)."""
        query = "¿Cuáles son las medidas oficiales del área de combate y el área de seguridad del tatami?"
        res = self.engine.query(query, k=3)

        struct = res.get("structured_answer", {})
        self.assertTrue(struct.get("is_structured"), "La respuesta debe ser estructurada.")
        
        # Nivel 1
        summary = struct.get("summary", "")
        self.assertTrue(len(summary) > 0, "El Nivel 1 summary no puede estar vacío.")
        self.assertNotIn("A continuación se expone el razonamiento", summary)
        self.assertNotIn("El análisis arbitral determina", summary)

        # Nivel 2
        normative_basis = struct.get("normative_basis", "")
        self.assertTrue(len(normative_basis) > 0, "El Nivel 2 normative_basis debe contener artículos y citas.")
        self.assertIn("SOR-2026-08-", normative_basis)

    def test_10_canonical_k5_default_configuration(self):
        """
        DEC-009: Verifica que la configuración canónica K=5 y min_score=None
        esté implementada por defecto en las firmas e instancias de RagEngine,
        ArbitrationDecisionAssistant (ADA) y ReasoningRetrievalEngine (RRE).
        """
        from rag_engine import RagEngine
        from ada_assistant import ArbitrationDecisionAssistant
        from rre_engine import ReasoningRetrievalEngine

        # 1. Firmas de métodos clave
        sig_rag_query = inspect.signature(RagEngine.query)
        self.assertEqual(sig_rag_query.parameters["k"].default, 5, "RagEngine.query debe tener k=5 por defecto.")
        self.assertIsNone(sig_rag_query.parameters["min_score"].default, "RagEngine.query debe preservar min_score=None.")

        sig_rag_retrieve = inspect.signature(RagEngine.retrieve_context)
        self.assertEqual(sig_rag_retrieve.parameters["k"].default, 5, "RagEngine.retrieve_context debe tener k=5 por defecto.")

        sig_ada = inspect.signature(ArbitrationDecisionAssistant.analyze_situation)
        self.assertEqual(sig_ada.parameters["top_k"].default, 5, "ADA.analyze_situation debe tener top_k=5 por defecto.")

        sig_rre = inspect.signature(ReasoningRetrievalEngine.retrieve)
        self.assertEqual(sig_rre.parameters["top_k"].default, 5, "RRE.retrieve debe tener top_k=5 por defecto.")

        # 2. Ejecución con defaults en la instancia activa
        query = "¿Cuáles son las medidas oficiales del área de combate y el área de seguridad del tatami?"
        
        # Ejecución por defecto en RRE
        res_rre = self.engine.rre.retrieve(query)
        self.assertEqual(res_rre["status"], "SUCCESS")
        self.assertLessEqual(len(res_rre["evidence"]), 5)
        self.assertGreaterEqual(len(res_rre["evidence"]), 1)

        # Ejecución por defecto en ADA
        res_ada = self.engine.ada.analyze_situation(query)
        self.assertEqual(res_ada["status"], "SUCCESS")
        self.assertLessEqual(len(res_ada["evidence"]), 5)

        # Ejecución por defecto en RagEngine.query (como es invocado en app.py)
        res_rag = self.engine.query(query)
        self.assertIn("SOR-2026-08-P096-S114", res_rag["retrieved_kuns"])
        ev_direct = [item for item in res_rag.get("retrieved_kuns_data", []) if "Referencia Cruzada" not in item.get("interpretacion", "")]
        self.assertLessEqual(len(ev_direct), 5)
        self.assertGreaterEqual(len(ev_direct), 1)


if __name__ == '__main__':
    unittest.main()

import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from rre_engine import ReasoningRetrievalEngine
from ada_assistant import ArbitrationDecisionAssistant
from corpus_config import EDITION_2026_08

class TestRREAndADAArchitecture(unittest.TestCase):
    """
    Suite de verificación formal de la nueva arquitectura RRE (Reasoning Retrieval Engine)
    y ADA (Arbitration Decision Assistant) para el corpus IJF SOR 2026-08.
    """

    @classmethod
    def setUpClass(cls):
        os.environ['IJF_SOR_EDITION'] = EDITION_2026_08
        cls.rre = ReasoningRetrievalEngine()
        cls.ada = ArbitrationDecisionAssistant()

    def test_01_rre_dual_channel_and_rrf_retrieval(self):
        """Verifica que RRE opere con canales duales (denso y sparse) y fusión RRF."""
        self.assertIsNotNone(self.rre.dense_model)
        self.assertIsNotNone(self.rre.dense_embeddings)
        self.assertEqual(len(self.rre.passages), 554)
        
        # Consulta sobre puntuación WRL
        res = self.rre.retrieve("World Ranking List Grand Slam points", top_k=3)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertTrue(len(res["evidence"]) > 0)
        top_hit = res["evidence"][0]
        self.assertIn("passage_id", top_hit)
        self.assertIn("score", top_hit)
        self.assertIn("page", top_hit)
        self.assertTrue(top_hit["source_url"].startswith("https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/"))

    def test_02_rre_graph_guided_expansion(self):
        """Verifica que RRE expanda el contexto a través de aristas cruzadas del grafo."""
        res = self.rre.retrieve("cadet head defence shido", top_k=3, expand_graph=True)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertTrue(len(res.get("related_passages", [])) > 0)
        rel = res["related_passages"][0]
        self.assertIn("relation", rel)
        self.assertIn("source_seed", rel)

    def test_03_rre_strict_domain_abstention(self):
        """Verifica que RRE descarte consultas completamente ajenas al reglamento."""
        res = self.rre.retrieve("reglas de fuera de juego en baloncesto nba y formula 1")
        self.assertEqual(res["status"], "ABSTAIN")
        self.assertEqual(res["reason"], "OUT_OF_DOMAIN")
        self.assertEqual(len(res["evidence"]), 0)

    def test_04_ada_arbitration_situation_analysis(self):
        """Verifica que ADA estructure resúmenes normativos a partir de evidencias de RRE."""
        res = self.ada.analyze_situation("¿Cómo se sanciona el uso de la cabeza para defenderse en cadetes?")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["engine"], "ADA-RRE-v2")
        self.assertTrue(len(res["evidence"]) > 0)
        self.assertIn("SOR-2026-08", res["analysis"])
        self.assertTrue("Resumen de Evidencias Normativas" in res["analysis"] or "Síntesis Analítica IA" in res["analysis"])

    def test_05_ada_abstention_handling(self):
        """Verifica que ADA formule una abstención justificada ante consultas out-of-domain."""
        res = self.ada.analyze_situation("penalizaciones por parada en boxes en formula 1")
        self.assertEqual(res["status"], "ABSTAIN")
        self.assertIn("Abstención", res["analysis"])
        self.assertEqual(len(res["evidence"]), 0)

    def test_06_dense_matrix_alignment_and_integrity(self):
        """Verifica que la matriz densa pre-computada coincida 1:1 con los 554 pasajes normativos."""
        self.assertEqual(self.rre.dense_embeddings.shape, (554, 384))
        self.assertEqual(self.rre.dense_meta.get("num_passages"), 554)
        self.assertEqual(self.rre.dense_meta.get("dimension"), 384)
        self.assertEqual(self.rre.dense_meta.get("source_sha256").lower(), "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620")
        self.assertEqual(len(self.rre.dense_meta.get("passage_ids", [])), 554)
        # Verificar alineación de los primeros y últimos IDs
        self.assertEqual(self.rre.dense_meta["passage_ids"][0], self.rre.passages[0]["passage_id"])
        self.assertEqual(self.rre.dense_meta["passage_ids"][-1], self.rre.passages[-1]["passage_id"])

    def test_07_rag_engine_separation_for_2026_08(self):
        """Verifica que RagEngine delegue a RRE sin inicializar vector store legacy para 2026-08."""
        from rag_engine import RagEngine
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        engine = RagEngine(repo_root)
        self.assertTrue(engine.is_2026_08)
        self.assertIsNotNone(engine.ada)
        self.assertIsNotNone(engine.rre)
        self.assertIsNone(engine.vs)  # Legacy VectorStore no debe instanciarse para agosto 2026
        
        # Test query delegación
        query_res = engine.query("¿Cuáles son las dimensiones del tatami?")
        self.assertIn("query", query_res)
        self.assertTrue(len(query_res["retrieved_kuns"]) > 0)
        self.assertIn("SOR-2026-08", query_res["answer"])
        self.assertEqual(query_res.get("rre_operating_mode"), "HYBRID")

    def test_08_rre_rejects_corrupted_or_non_finite_matrix(self):
        """Verifica que RRE lance ValueError accionable ante matrices corruptas o con valores no finitos (NaN)."""
        import tempfile
        import shutil
        import numpy as np

        temp_dir = tempfile.mkdtemp()
        try:
            # Copiar archivos base
            shutil.copy(self.rre.passages_file, os.path.join(temp_dir, "passages_candidate.json"))
            shutil.copy(self.rre.dense_meta_file, os.path.join(temp_dir, "dense_embeddings_meta.json"))

            # 1. Matriz con NaNs
            bad_matrix = np.ones((554, 384), dtype=np.float32)
            bad_matrix[10, 5] = np.nan
            np.save(os.path.join(temp_dir, "dense_embeddings_candidate.npy"), bad_matrix)

            with self.assertRaises(ValueError) as ctx:
                ReasoningRetrievalEngine(base_dir=temp_dir)
            self.assertIn("no finitos", str(ctx.exception).lower())

            # 2. Matriz con forma dimensional incorrecta (554, 128 en vez de 384)
            bad_shape_matrix = np.ones((554, 128), dtype=np.float32)
            np.save(os.path.join(temp_dir, "dense_embeddings_candidate.npy"), bad_shape_matrix)
            with self.assertRaises(ValueError) as ctx:
                ReasoningRetrievalEngine(base_dir=temp_dir)
            self.assertIn("discrepancia dimensional", str(ctx.exception).lower())

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_09_rre_rejects_mismatched_passage_ids_order(self):
        """Verifica que RRE detecte desalineación en el orden o duplicación de passage_ids en metadatos."""
        import tempfile
        import shutil
        import json

        temp_dir = tempfile.mkdtemp()
        try:
            shutil.copy(self.rre.passages_file, os.path.join(temp_dir, "passages_candidate.json"))
            shutil.copy(self.rre.dense_embeddings_file, os.path.join(temp_dir, "dense_embeddings_candidate.npy"))

            with open(self.rre.dense_meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)

            # Invertir el orden de los dos primeros passage_ids
            meta["passage_ids"][0], meta["passage_ids"][1] = meta["passage_ids"][1], meta["passage_ids"][0]
            with open(os.path.join(temp_dir, "dense_embeddings_meta.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f)

            with self.assertRaises(ValueError) as ctx:
                ReasoningRetrievalEngine(base_dir=temp_dir)
            self.assertIn("desalineación en orden", str(ctx.exception).lower())

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_10_rre_rejects_incompatible_metadata_hash_and_model(self):
        """Verifica que RRE rechace metadatos con SHA-256 discordante o modelo incompatible."""
        import tempfile
        import shutil
        import json

        temp_dir = tempfile.mkdtemp()
        try:
            shutil.copy(self.rre.passages_file, os.path.join(temp_dir, "passages_candidate.json"))
            shutil.copy(self.rre.dense_embeddings_file, os.path.join(temp_dir, "dense_embeddings_candidate.npy"))

            # 1. SHA-256 no oficial
            with open(self.rre.dense_meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            meta["source_sha256"] = "1111111111111111111111111111111111111111111111111111111111111111"
            with open(os.path.join(temp_dir, "dense_embeddings_meta.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f)

            with self.assertRaises(ValueError) as ctx:
                ReasoningRetrievalEngine(base_dir=temp_dir)
            self.assertIn("discrepancia criptográfica", str(ctx.exception).lower())

            # 2. Modelo de embeddings incompatible
            meta["source_sha256"] = "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620"
            meta["model_name"] = "unsupported-model-v1"
            with open(os.path.join(temp_dir, "dense_embeddings_meta.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f)

            with self.assertRaises(ValueError) as ctx:
                ReasoningRetrievalEngine(base_dir=temp_dir)
            self.assertIn("metadatos incompatibles", str(ctx.exception).lower())

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_11_rre_explicit_operating_mode_hybrid_vs_degraded(self):
        """Verifica que RRE reporte explícitamente HYBRID cuando todo está íntegro y DEGRADED_LEXICAL si falta el modelo."""
        # En el entorno actual debe ser HYBRID
        self.assertEqual(self.rre.operating_mode, "HYBRID")
        self.assertIsNone(self.rre.degradation_reason)

        # Simular ausencia de modelo neuronal manteniendo la matriz
        original_model = self.rre.dense_model
        try:
            self.rre.dense_model = None
            self.rre._determine_operating_mode()
            self.assertEqual(self.rre.operating_mode, "DEGRADED_LEXICAL")
            self.assertIn("no disponible", self.rre.degradation_reason)

            # Verificar que si allow_degraded=False, se rechaza la inicialización con RuntimeError
            import tempfile, shutil
            td = tempfile.mkdtemp()
            try:
                # Copiar solo pasajes y grafo (sin matriz densa)
                shutil.copy(self.rre.passages_file, os.path.join(td, "passages_candidate.json"))
                shutil.copy(self.rre.graph_file, os.path.join(td, "knowledge_graph_candidate.json"))
                with self.assertRaises(RuntimeError) as ctx:
                    ReasoningRetrievalEngine(base_dir=td, allow_degraded=False)
                self.assertIn("se requiere modo hybrid", str(ctx.exception).lower())
            finally:
                shutil.rmtree(td, ignore_errors=True)
        finally:
            self.rre.dense_model = original_model
            self.rre._determine_operating_mode()
            self.assertEqual(self.rre.operating_mode, "HYBRID")

    def test_12_rre_bilingual_and_edge_cases(self):
        """Evalúa consultas vacías, de baja confianza y términos técnicos bilingües."""
        # Consulta vacía
        res_empty = self.rre.retrieve("   ")
        self.assertEqual(res_empty["status"], "ABSTAIN")
        self.assertEqual(res_empty["reason"], "EMPTY_OR_NON_SUBSTANTIVE_QUERY")

        # Consulta técnica en español con mapeo de sinónimos judo
        res_es = self.rre.retrieve("tiempo de combate y duracion golden score")
        self.assertEqual(res_es["status"], "SUCCESS")
        self.assertTrue(len(res_es["evidence"]) > 0)
        self.assertEqual(res_es["operating_mode"], "HYBRID")

if __name__ == '__main__':
    unittest.main()

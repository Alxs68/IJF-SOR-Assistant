import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from rre_engine import ReasoningRetrievalEngine
from ada_assistant import ArbitrationDecisionAssistant
from corpus_config import EDITION_2026_08
from unittest.mock import patch
from tests._ada_contract_helpers import (
    StubLLM, answer_citing, cite_first_delivered, citation_ids, grounded_answer,
    delivered_ids_in_result, delivered_primary_ids, ABSTENTION_MARKER, TRANSLATION_MARKER,
)

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
        self.assertEqual(len(self.rre.passages), 385)
        
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
        trace = res["evidence"] + res.get("related_passages", [])
        self.assertTrue(
            any("18.1.4" in str(item.get("article_id", "")) for item in trace),
            f"La consulta sobre defensa con la cabeza en cadetes debe enlazar el artículo 18.1.4; "
            f"evidencia={[(item.get('passage_id'), item.get('article_id')) for item in trace]}"
        )
        rel = res["related_passages"][0]
        self.assertIn("relation", rel)
        self.assertIn("source_seed", rel)

    def test_03_rre_strict_domain_abstention(self):
        """Verifica que RRE descarte consultas completamente ajenas al reglamento."""
        res = self.rre.retrieve("reglas de fuera de juego en baloncesto nba y formula 1")
        self.assertEqual(res["status"], "ABSTAIN")
        self.assertEqual(res["reason"], "OUT_OF_DOMAIN")
        self.assertEqual(len(res["evidence"]), 0)
        self.assertEqual(res.get("operating_mode"), self.rre.operating_mode)
        self.assertEqual(res.get("degradation_reason"), self.rre.degradation_reason)
        self.assertEqual(res.get("source_sha256_verified"), self.rre.source_sha256_verified)

    def test_04_ada_arbitration_situation_analysis(self):
        """ADA builds on RRE evidence: without LLM -> ABSTAIN, no citations; with a simulated
        translator and generator citing a delivered primary passage -> SUCCESS (IA synthesis) with
        citations limited to delivered IDs. (Offline retrieval for this query depends on the
        dictionary projection, which is outside AUD-01..04; see audit report.)"""
        q = "¿Cómo se sanciona el uso de la cabeza para defenderse en cadetes?"
        with patch.object(self.ada, "_call_llm", StubLLM()):
            offline = self.ada.analyze_situation(q)
        self.assertEqual(offline["status"], "ABSTAIN")
        self.assertEqual(offline["engine"], "ADA-RRE-v2")
        self.assertIn("Abstención", offline["analysis"])
        self.assertEqual(offline["structured_answer"]["citations"], [])

        # Simulated LLM = simulated translator + simulated generator (deterministic, no network).
        stub = StubLLM(cite_first_delivered,
                       translation="How is using the head to defend penalised in cadet competitions?")
        with patch.object(self.ada, "_call_llm", stub):
            res = self.ada.analyze_situation(q)
        self.assertEqual(len(stub.translation_prompts), 1)
        self.assertEqual(len(stub.analysis_prompts), 1)
        delivered = delivered_primary_ids(stub.analysis_prompts[0])
        self.assertTrue(delivered)
        self.assertTrue(len(res["evidence"]) > 0)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["engine"], "ADA-RRE-v2")
        self.assertIn("SOR-2026-08", res["analysis"])
        self.assertIn("Síntesis Analítica IA", res["analysis"])
        self.assertEqual(citation_ids(res), delivered[:1])

    def test_05_ada_abstention_handling(self):
        """Verifica que ADA formule una abstención justificada ante consultas out-of-domain."""
        res = self.ada.analyze_situation("penalizaciones por parada en boxes en formula 1")
        self.assertEqual(res["status"], "ABSTAIN")
        self.assertIn("Abstención", res["analysis"])
        self.assertEqual(len(res["evidence"]), 0)
        self.assertEqual(res.get("rre_operating_mode"), self.ada.rre.operating_mode)
        self.assertEqual(res.get("source_sha256_verified"), self.ada.rre.source_sha256_verified)

    def test_06_llm_output_requires_retrieved_official_citations(self):
        """Reject generated analysis when it cites a passage absent from the delivered evidence."""
        query = "¿Cuáles son las dimensiones del tatami?"
        stub = StubLLM(lambda prompt, delivered: "La conclusión inventada es definitiva [SOR-2026-08-P999-S999].")
        with patch.object(self.ada, "_call_llm", stub):
            result = self.ada.analyze_situation(query)
        self.assertEqual(len(stub.translation_prompts), 1)
        self.assertEqual(len(stub.analysis_prompts), 1)
        self.assertNotIn("SOR-2026-08-P999-S999", delivered_primary_ids(stub.analysis_prompts[0]))
        self.assertEqual(result["status"], "ABSTAIN")
        self.assertIn("validación de citas", result["mode"])
        self.assertNotIn("P999-S999", result["analysis"])
        self.assertEqual(result["structured_answer"]["citations"], [])
        self.assertTrue(len(result["evidence"]) > 0)

    def test_07_llm_output_accepts_citation_from_retrieved_evidence(self):
        """Accept generated analysis when it cites a passage delivered to the model.

        The translation call and the analysis call are distinguished explicitly, so the mock never
        replaces the retrieval query; the cited ID is read from the analysis prompt actually received.
        """
        query = "¿Cuáles son las dimensiones del tatami?"
        # Fase 9.1: el stub responde con el contrato vigente (JSON + citas literales del pasaje citado);
        # una frase libre con un ID ya no es una respuesta normativa aceptable (DIG-00).
        stub = StubLLM(lambda prompt, delivered: grounded_answer(prompt, delivered[:1]) if delivered else "Sin evidencia.")
        with patch.object(self.ada, "_call_llm", stub):
            result = self.ada.analyze_situation(query)
        self.assertEqual(len(stub.translation_prompts), 1)
        self.assertEqual(len(stub.analysis_prompts), 1)
        self.assertNotIn(TRANSLATION_MARKER, stub.analysis_prompts[0])
        delivered = delivered_primary_ids(stub.analysis_prompts[0])
        self.assertTrue(delivered)
        valid_id = delivered[0]
        self.assertIn(valid_id, [e["passage_id"] for e in result["evidence"] + result["related_passages"]])
        self.assertEqual(result["status"], "SUCCESS")
        self.assertIn("citas SOR validadas", result["mode"])
        self.assertIn(valid_id, result["analysis"])
        self.assertEqual(citation_ids(result), [valid_id])

    def test_08_dense_matrix_alignment_and_integrity(self):
        """Verifica que la matriz densa pre-computada coincida 1:1 con los 385 pasajes normativos."""
        self.assertEqual(self.rre.dense_embeddings.shape, (385, 384))
        self.assertEqual(self.rre.dense_meta.get("num_passages"), 385)
        self.assertEqual(self.rre.dense_meta.get("dimension"), 384)
        self.assertEqual(self.rre.dense_meta.get("source_sha256").lower(), "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620")
        self.assertEqual(len(self.rre.dense_meta.get("passage_ids", [])), 385)
        # Verificar alineación de los primeros y últimos IDs
        self.assertEqual(self.rre.dense_meta["passage_ids"][0], self.rre.passages[0]["passage_id"])
        self.assertEqual(self.rre.dense_meta["passage_ids"][-1], self.rre.passages[-1]["passage_id"])

    def test_09_rag_engine_separation_for_2026_08(self):
        """Verifica que RagEngine delegue a RRE sin inicializar vector store legacy para 2026-08."""
        from rag_engine import RagEngine
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        engine = RagEngine(repo_root)
        self.assertTrue(engine.is_2026_08)
        self.assertIsNotNone(engine.ada)
        self.assertIsNotNone(engine.rre)
        self.assertIsNone(engine.vs)  # Legacy VectorStore no debe instanciarse para agosto 2026

        # Delegation without a generator: abstention, retrieved SOR evidence kept for the UI
        with patch.object(engine.ada, "_call_llm", StubLLM()):
            query_res = engine.query("¿Cuáles son las dimensiones del tatami?")
        self.assertIn("query", query_res)
        self.assertTrue(len(query_res["retrieved_kuns"]) > 0)
        self.assertTrue(all(pid.startswith("SOR-2026-08") for pid in query_res["retrieved_kuns"]))
        self.assertIn(ABSTENTION_MARKER, query_res["answer"])
        self.assertEqual(query_res.get("rre_operating_mode"), "HYBRID")

        # Delegation with a generator citing a delivered passage: the answer carries the SOR citation
        with patch.object(engine.ada, "_call_llm", StubLLM(cite_first_delivered)):
            query_res = engine.query("¿Cuáles son las dimensiones del tatami?")
        self.assertIn("SOR-2026-08", query_res["answer"])
        self.assertNotIn(ABSTENTION_MARKER, query_res["answer"])
        self.assertEqual(query_res.get("rre_operating_mode"), "HYBRID")

    def test_10_rre_rejects_corrupted_or_non_finite_matrix(self):
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
            bad_matrix = np.ones((385, 384), dtype=np.float32)
            bad_matrix[10, 5] = np.nan
            np.save(os.path.join(temp_dir, "dense_embeddings_candidate.npy"), bad_matrix)

            with self.assertRaises(ValueError) as ctx:
                ReasoningRetrievalEngine(base_dir=temp_dir)
            self.assertIn("no finitos", str(ctx.exception).lower())

            # 2. Matriz con forma dimensional incorrecta (385, 128 en vez de 384)
            bad_shape_matrix = np.ones((385, 128), dtype=np.float32)
            np.save(os.path.join(temp_dir, "dense_embeddings_candidate.npy"), bad_shape_matrix)
            with self.assertRaises(ValueError) as ctx:
                ReasoningRetrievalEngine(base_dir=temp_dir)
            self.assertIn("discrepancia dimensional", str(ctx.exception).lower())

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_11_rre_rejects_mismatched_passage_ids_order(self):
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

    def test_12_rre_rejects_incompatible_metadata_hash_and_model(self):
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

    def test_13_rre_explicit_operating_mode_hybrid_vs_degraded(self):
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
                shutil.copy(self.rre.sparse_index_file, os.path.join(td, "vector_index_candidate.json"))
                with self.assertRaises(RuntimeError) as ctx:
                    ReasoningRetrievalEngine(base_dir=td, allow_degraded=False)
                self.assertIn("se requiere modo hybrid", str(ctx.exception).lower())
            finally:
                shutil.rmtree(td, ignore_errors=True)
        finally:
            self.rre.dense_model = original_model
            self.rre._determine_operating_mode()
            self.assertEqual(self.rre.operating_mode, "HYBRID")

    def test_14_rre_bilingual_and_edge_cases(self):
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


    def test_15_model_startup_never_downloads_and_degradation_is_opt_in(self):
        """A startup without a local snapshot must not call the remote model loader."""
        from unittest.mock import patch
        import sentence_transformers

        with patch.dict(os.environ, {"RRE_MODEL_PATH": "", "RRE_ALLOW_DEGRADED_LEXICAL": ""}, clear=False):
            with patch("rre_engine.glob.glob", return_value=[]):
                with patch.object(sentence_transformers, "SentenceTransformer") as model_loader:
                    with self.assertRaises(RuntimeError):
                        ReasoningRetrievalEngine()
                    model_loader.assert_not_called()

            with patch("rre_engine.glob.glob", return_value=[]):
                with patch.object(sentence_transformers, "SentenceTransformer") as model_loader:
                    degraded = ReasoningRetrievalEngine(allow_degraded=True)
                    model_loader.assert_not_called()
                    self.assertEqual(degraded.operating_mode, "DEGRADED_LEXICAL")
                    self.assertIn("scripts/setup_model.py", degraded.degradation_reason)

    def test_16_hybrid_requires_a_valid_sparse_index_and_graph(self):
        """HYBRID requires usable lexical vectors and graph edges; broken sparse index is never accepted."""
        original_index = self.rre.sparse_index
        original_edges = self.rre.graph_edges
        original_allow = self.rre.allow_degraded
        try:
            self.rre.sparse_index = {}
            with self.assertRaises(RuntimeError):
                self.rre._determine_operating_mode()

            self.rre.sparse_index = original_index
            self.rre.graph_edges = []
            self.rre.allow_degraded = True
            self.rre._determine_operating_mode()
            self.assertEqual(self.rre.operating_mode, "DEGRADED_LEXICAL")
            self.assertIn("grafo", self.rre.degradation_reason.lower())
        finally:
            self.rre.sparse_index = original_index
            self.rre.graph_edges = original_edges
            self.rre.allow_degraded = original_allow
            self.rre._determine_operating_mode()
            self.assertEqual(self.rre.operating_mode, "HYBRID")

if __name__ == '__main__':
    unittest.main()

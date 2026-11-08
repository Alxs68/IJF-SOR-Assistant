"""
Suite de Pruebas de Interfaz y Mecanismo de Novedades (Fase P1-B Post-Ajustes).
IJF SOR Assistant 2026.

Verifica:
1. Retiro efectivo de los controles técnicos de búsqueda (K y min_score) de app.py.
2. Invocación de consultas con la configuración predeterminada efectiva (k=3, min_score=None).
3. Registro persistente simplificado de novedades (clasificación oficial en 7 tipos).
4. Persistencia segura de pregunta, respuesta, observación y sesión en context.
5. Exportación de novedades en formato CSV para análisis administrativo.
6. Cálculo de indicadores y métricas de participación para el administrador.
"""

import os
import sys
import unittest
import json
import io

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(root_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from rag_engine import RagEngine
from feedback_manager import (
    record_observation,
    list_observations_protected,
    export_observations_csv,
    get_feedback_metrics,
    TIPOS_NOVEDAD
)


class TestUIControlsAndNovedades(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.brain_path = root_dir
        cls.engine = RagEngine(cls.brain_path)
        cls.admin_token = "SuperSecretAdminToken2026!"
        os.environ["FEEDBACK_ADMIN_TOKEN"] = cls.admin_token

    def test_01_search_controls_removed_from_ui(self):
        """Verifica que los sliders de k y min_score fueron retirados de app.py."""
        app_path = os.path.join(root_dir, "app.py")
        with open(app_path, "r", encoding="utf-8") as f:
            code = f.read()

        self.assertNotIn("k_param = st.slider", code, "El slider de k aún se encuentra en app.py")
        self.assertNotIn("min_score_param = st.slider", code, "El slider de min_score aún se encuentra en app.py")
        self.assertNotIn("search_settings_title", code, "La sección de configuración de búsqueda aún está presente en app.py")
        self.assertIn("res = engine.query(query_to_run, language=lang)", code, "La llamada a engine.query no usa defaults")

    def test_02_default_query_execution_works_normally(self):
        """Verifica que la consulta normal funcione con los valores por defecto del sistema."""
        query = "¿Cuáles son las medidas oficiales del área de combate y el área de seguridad del tatami?"
        res = self.engine.query(query)

        self.assertEqual(res["query"], query)
        self.assertTrue(len(res.get("retrieved_kuns", [])) > 0)
        self.assertIn("SOR-2026-08-P096-S114", res["retrieved_kuns"])
        self.assertIn("structured_answer", res)
        self.assertTrue(res["structured_answer"].get("is_structured"))

    def test_03_record_novedad_with_simplified_classification(self):
        """Verifica el registro de novedades con los tipos autorizados por Alexis."""
        for tipo in TIPOS_NOVEDAD:
            res = record_observation(
                tipo_novedad=tipo,
                comentario=f"Prueba de observación para tipo: {tipo}",
                query="¿Pregunta de prueba?",
                response_summary="Respuesta generada de prueba.",
                session_id="sess-auto-test-001"
            )
            self.assertTrue(res["success"])
            self.assertTrue(res["observation_id"].startswith("OBS-"))

    def test_04_export_observations_csv_protected(self):
        """Verifica la exportación a CSV de las novedades registradas."""
        ok, csv_data, err = export_observations_csv(self.admin_token)
        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertIn("ID,Fecha,Tipo,Pregunta,Respuesta,Observacion,Estado,Tiene_Adjunto", csv_data)
        
        # Con token erróneo debe denegar acceso
        ok_bad, _, err_bad = export_observations_csv("bad_token")
        self.assertFalse(ok_bad)
        self.assertIn("Acceso no autorizado", err_bad)

    def test_05_feedback_metrics_participation(self):
        """Verifica el cálculo de métricas de participación para el administrador."""
        metrics = get_feedback_metrics(self.admin_token)
        self.assertTrue(metrics["success"])
        self.assertGreaterEqual(metrics["total"], 7)
        self.assertIn("Posible error o inconsistencia normativa", metrics["by_type"])
        self.assertGreaterEqual(metrics["recent_7d"], 1)


if __name__ == '__main__':
    unittest.main()

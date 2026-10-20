import unittest
import os
import sys

# Add src to system path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from rag_engine import RagEngine

class TestGoldenDataset(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        os.environ["IJF_SOR_EDITION"] = "2026-08"
        cls.brain_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.engine = RagEngine(cls.brain_path)

        # Historical Golden QA Dataset (Edición previa 2026-01 para trazabilidad)
        cls.historical_golden_pairs_2026_01 = [
            ("Defensa de cabeza hansoku-make", "KUN-0001"),
            ("Acción involuntaria de cabeza en proyección", "KUN-0003"),
            ("Video de defensa de cabeza durante seoi-nage", "KUN-0004"),
            ("Dimensiones oficiales del tatami y área de seguridad", "KUN-0007"),
            ("Tolerancia de peso en sorteo de pesaje aleatorio matutino", "KUN-0010"),
            ("Duración del combate en categorías senior y cadet", "KUN-0011"),
            ("Medidas del judogi con el calibrador Sokuteiki", "KUN-0013"),
            ("Agarre Ushiro-sangaku con riesgo cervical en suelo", "KUN-0285"),
            ("Límite máximo de intervenciones médicas por combate", "KUN-0048"),
            ("Proyección de seoi-nage inverso permitida en seniors", "KUN-0073"),
            ("Incorporación de uniformes inteligentes Smart Judogi NFC", "KUN-0076"),
            ("Uso de Inteligencia Artificial para arbitraje por la IJF", "KUN-0077")
        ]

        # Active Golden QA Dataset (Edición oficial vigente SOR 2026-08)
        cls.golden_pairs = [
            ("Defensa de cabeza hansoku-make", "SOR-2026-08-P190-S198"),
            ("Acción involuntaria de cabeza en proyección", "SOR-2026-08-P202-S218"),
            ("Video de defensa de cabeza durante seoi-nage", "SOR-2026-08-P189-S196"),
            ("Dimensiones oficiales del tatami y área de seguridad", "SOR-2026-08-P096-S114"),
            ("Tolerancia de peso en sorteo de pesaje aleatorio matutino", "SOR-2026-08-P077-S090"),
            ("Duración del combate en categorías senior y cadet", "SOR-2026-08-P152-S179"),
            ("Medidas del judogi con el calibrador Sokuteiki", "SOR-2026-08-P124-S165"),
            ("Agarre Ushiro-sangaku con riesgo cervical en suelo", "SOR-2026-08-P180-S194"),
            ("Límite máximo de intervenciones médicas por combate", "SOR-2026-08-P196-S206"),
            ("Proyección de seoi-nage inverso permitida en seniors", "SOR-2026-08-P189-S196"),
            ("Incorporación de uniformes inteligentes Smart Judogi NFC", "SOR-2026-08-P115-S149"),
            ("Uso de Inteligencia Artificial para arbitraje por la IJF", "SOR-2026-08-P132-S172")
        ]

    def test_golden_dataset_retrieval(self):
        print("\n=== EJECUTANDO VALIDACIÓN DE DATASET DE ORO (GOLDEN DATASET) ===")
        success_count = 0
        total = len(self.golden_pairs)
        
        report_lines = [
            "# Reporte de Validación de Dataset de Oro (Etapa 3.5)",
            "## Métricas de Precisión del Buscador Híbrido",
            "",
            "| ID | Consulta de Prueba | KUN Esperada | KUNs Recuperadas | ¿Éxito? |",
            "| :--- | :--- | :---: | :--- | :---: |"
        ]
        
        for idx, (query, expected_id) in enumerate(self.golden_pairs, 1):
            res = self.engine.query(query, k=3)
            retrieved = res['retrieved_kuns']
            
            # Check if expected KUN is present in retrieval set
            is_success = expected_id in retrieved
            status_char = "🟢 SÍ" if is_success else "🔴 NO"
            
            if is_success:
                success_count += 1
                
            retrieved_str = ", ".join(retrieved)
            report_lines.append(
                f"| {idx:02d} | \"{query}\" | **{expected_id}** | {retrieved_str} | {status_char} |"
            )
            
            print(f"Test {idx:02d}: Query='{query}' -> Expected='{expected_id}' -> Got={retrieved} -> Success={is_success}")
            
        success_rate = (success_count / total) * 100
        print(f"\nTasa de Éxito del Buscador Híbrido: {success_rate:.2f}% ({success_count}/{total})")
        
        report_lines.append("")
        report_lines.append(f"### Tasa de Éxito de Recuperación Semántica/Relacional: **{success_rate:.2f}%**")
        report_lines.append(f"* **Consultas Exitosas:** {success_count} / {total}")
        report_lines.append("* **Criterio de Aceptación:** > 80% de éxito.")
        report_lines.append("* **Resultado Final:** 🟢 **APROBADO**" if success_rate >= 80.0 else "🔴 **RECHAZADO**")
        
        # Save validation report
        report_path = os.path.join(self.brain_path, 'scratch', 'golden_validation_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
            
        print(f"Reporte de validación generado en: {report_path}")
        
        # Assert target success rate is met
        self.assertTrue(success_rate >= 80.0, f"Tasa de éxito {success_rate:.2f}% es inferior al 80% requerido.")

if __name__ == '__main__':
    unittest.main()

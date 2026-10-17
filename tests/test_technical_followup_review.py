import unittest
import json
import os
import csv

class TestTechnicalFollowupReview(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.review_dir = os.path.join(cls.base_dir, 'docs', 'reports', 'coverage_audit_2026_08', 'followup_review')
        cls.audit_dir = os.path.join(cls.base_dir, 'docs', 'reports', 'coverage_audit_2026_08')
        
        # Load corrected tables
        corrected_json = os.path.join(cls.review_dir, 'reconstructed_complex_tables_corrected.json')
        with open(corrected_json, 'r', encoding='utf-8') as f:
            cls.corrected_data = json.load(f)
            
    def test_wrl_matrix_structure_and_null_cells(self):
        """Verifica que la tabla WRL contenga exactamente 9 filas y 8 competiciones, con null en Olympic Games para 1 win y Participation."""
        wrl = self.corrected_data['WRL_POINTS_ALLOCATION_MATRIX']
        records = wrl['records']
        self.assertEqual(len(records), 9, "La matriz WRL debe tener exactamente 9 posiciones")
        
        expected_comps = [
            'Continental Opens', 'Continental Championships', 'Junior World Championships',
            'Grand Prix', 'Grand Slam', 'Masters', 'World Championships', 'Olympic Games'
        ]
        
        for r in records:
            allocs = r['points_by_competition']
            self.assertEqual(len(allocs), 8, f"La posición {r['placing']} debe tener exactamente 8 categorías de competencia")
            for c in expected_comps:
                self.assertIn(c, allocs, f"Falta la competición {c} en la posición {r['placing']}")
                
        # Verificar específicamente las celdas nulas en JJ.OO.
        r_1win = next(r for r in records if r['placing'] == '1 contest won')
        self.assertIsNone(r_1win['points_by_competition']['Olympic Games'], "1 contest won en JJ.OO. debe ser null (no otorga puntos)")
        self.assertEqual(r_1win['points_by_competition']['Grand Slam'], '100')
        
        r_part = next(r for r in records if r['placing'] == 'Participation')
        self.assertIsNone(r_part['points_by_competition']['Olympic Games'], "Participation en JJ.OO. debe ser null (no otorga puntos)")
        self.assertEqual(r_part['points_by_competition']['Masters'], '100')
        self.assertEqual(r_part['points_by_competition']['Continental Opens'], '2')

    def test_weight_categories_distinction_and_completeness(self):
        """Verifica que las categorías individuales contengan 32 registros distinguiendo Senior/Junior vs Cadet."""
        indiv = self.corrected_data['WEIGHT_CATEGORIES_INDIVIDUAL']['records']
        self.assertEqual(len(indiv), 32, "Debe haber exactamente 32 categorías individuales en la página 33")
        
        senior_women = [r for r in indiv if r['division'] == 'Senior and Junior' and r['gender'] == 'Women']
        cadet_women = [r for r in indiv if 'Cadet' in r['division'] and r['gender'] == 'Women']
        senior_men = [r for r in indiv if r['division'] == 'Senior and Junior' and r['gender'] == 'Men']
        cadet_men = [r for r in indiv if 'Cadet' in r['division'] and r['gender'] == 'Men']
        
        self.assertEqual(len(senior_women), 8, "Debe haber 8 categorías Senior/Junior Women")
        self.assertEqual(len(cadet_women), 8, "Debe haber 8 categorías Cadet Women")
        self.assertEqual(len(senior_men), 8, "Debe haber 8 categorías Senior/Junior Men")
        self.assertEqual(len(cadet_men), 8, "Debe haber 8 categorías Cadet Men")
        
        # Verificar pesos clave
        self.assertIn('-40 kg', [r['weight_category'] for r in cadet_women])
        self.assertIn('-48 kg', [r['weight_category'] for r in senior_women])
        self.assertIn('-50 kg', [r['weight_category'] for r in cadet_men])
        self.assertIn('-60 kg', [r['weight_category'] for r in senior_men])

    def test_table_inventory_reconciliation(self):
        """Verifica que el inventario contenga 449 tablas únicas y que las categorías sumen exactamente 449."""
        inv_csv = os.path.join(self.audit_dir, 'SOR_TABLE_INVENTORY_2026_08.csv')
        with open(inv_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        self.assertEqual(len(rows), 449, "El inventario CSV debe tener exactamente 449 filas de tablas")
        unique_ids = set(r['table_id'] for r in rows)
        self.assertEqual(len(unique_ids), 449, "No debe haber identificadores de tabla duplicados")
        
        substantive_count = sum(1 for r in rows if r['is_substantive'] == 'True')
        minor_count = sum(1 for r in rows if r['is_substantive'] == 'False')
        self.assertEqual(substantive_count, 152, "Las tablas sustantivas deben ser exactamente 152")
        self.assertEqual(minor_count, 297, "Los recuadros menores deben ser exactamente 297")
        self.assertEqual(substantive_count + minor_count, 449)

    def test_coverage_matrix_reconciliation(self):
        """Verifica que la matriz de cobertura contenga 272 filas únicas y que la suma de estados sea 272."""
        cov_csv = os.path.join(self.audit_dir, 'SOR_COVERAGE_MATRIX_2026_08.csv')
        with open(cov_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        self.assertEqual(len(rows), 272, "La matriz de cobertura debe tener 272 secciones")
        unique_sec = set(r['item_id'] for r in rows)
        self.assertEqual(len(unique_sec), 272, "No debe haber secciones duplicadas")
        
        verified = sum(1 for r in rows if r['coverage_status'] == 'COMPLETO_VERIFICADO')
        partial = sum(1 for r in rows if r['coverage_status'] == 'PARCIAL')
        absent = sum(1 for r in rows if r['coverage_status'] == 'AUSENTE')
        
        self.assertEqual(verified, 238, "Las secciones verificadas completas deben ser 238 (87.50%)")
        self.assertEqual(partial, 34, "Las secciones parciales diagramáticas deben ser 34 (12.50%)")
        self.assertEqual(absent, 0, "No debe haber secciones ausentes (0.00%)")
        self.assertEqual(verified + partial + absent, 272)

if __name__ == '__main__':
    unittest.main()

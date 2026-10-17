# VALIDACIÓN Y CONCILIACIÓN DE COBERTURA NORMATIVA — IJF SOR 2026-08
**Documento ID:** AUD-COVERAGE-RECONCILIATION-2026-08  
**Fecha:** 17 de octubre de 2026  
**Rama:** `audit/rebuild-sor-2026-08`  
**Directorio:** `docs/reports/coverage_audit_2026_08/followup_review/`  

---

## 1. COMPROBACIÓN MATEMÁTICA Y DENOMINADORES EXPLÍCITOS

Se verificó el archivo `docs/reports/coverage_audit_2026_08/SOR_COVERAGE_MATRIX_2026_08.csv` contra el índice oficial de 272 secciones del IJF SOR:

- **Filas en matriz de cobertura (excluyendo cabecera):** exactamente **272 filas**.
- **Identificadores únicos de sección (`item_id`):** exactamente **272 identificadores únicos** (`SEC-001` a `SEC-272`).
- **Suma de los estados:**
  - `COMPLETO_VERIFICADO`: **238 secciones** ($87.50\%$)
  - `PARCIAL`: **34 secciones** ($12.50\%$)
  - `AUSENTE`: **0 secciones** ($0.00\%$)
  - `PENDIENTE_VALIDACION`: **0 secciones** ($0.00\%$)
  - `NO_APLICA`: **0 secciones** ($0.00\%$)
  - **Total:** $238 + 34 + 0 = \mathbf{272}$ secciones ($100.00\%$).

---

## 2. TRATAMIENTO DEL APÉNDICE F (PÁGINAS 208 A 240) Y PRECISIÓN TERMINOLÓGICA

### A. Localización Exacta de las 34 Secciones `PARCIAL`
Todas y cada una de las 34 secciones clasificadas como `PARCIAL` pertenecen exclusivamente al **Apéndice F1.3** (Standard Forms for IJF Events, páginas 208 a 240):
- Desde `SEC-203`: `F1.3 Standard Forms for IJF Events` (Pág. 208)
- Pasando por `SEC-204`: `F1.3.1 Delegation Control List` (Pág. 208)
- Hasta `SEC-236`: `F1.3.33 Exceptional Registration Request Form` (Pág. 240)

### B. Distinción entre Texto Normativo y Estructuras Visuales
1. **Evidencia de Extracción y Presencia:**  
   El texto descriptivo, los títulos oficiales, las instrucciones administrativas y las tablas que acompañan a estos formularios **sí están extraídos y preservados** en los 554 pasajes del corpus (ej. pasajes `SOR-2026-08-P208-S224` a `SOR-2026-08-P240-S253`).
2. **Motivo de la Clasificación `PARCIAL`:**  
   No se asigna `COMPLETO_VERIFICADO` porque los diagramas de llaves de eliminación (eliminatorias directas, cuadros de repesca de 64, 32, 16 y 8 atletas) contienen flechas y relaciones gráficas entre cuadros que no deben considerarse plenamente certificadas por un proceso de extracción puramente textual.
3. **Corrección de Redacción Ejecutiva:**  
   Se ratifica que **no se declara el 100% verificado en la totalidad del documento**, sino un **87.50% verificado** con **12.50% delimitado como dependiente de inspección visual directa**.

---

## 3. AUDITORÍA DE EVIDENCIA EN SECCIONES DECLARADAS COMPLETAS

Para las 238 secciones con dictamen `COMPLETO_VERIFICADO`:
- **Presencia en fuente:** Cada sección tiene su correspondencia en páginas físicas de la fuente PDF oficial (SHA-256: `9426B10D...`).
- **Representación en pasajes:** Cada una cuenta con entre 1 y 12 pasajes normativos asignados directamente en `passages_candidate.json`.
- **Indexación verificada:** El 100% de los identificadores de pasajes asociados figura dentro del conjunto de 554 documentos indexados en `vector_index_candidate.json` y en los 554 nodos de `knowledge_graph_candidate.json`.

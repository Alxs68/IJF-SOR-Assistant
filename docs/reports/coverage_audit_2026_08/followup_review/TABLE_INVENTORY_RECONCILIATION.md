# CONCILIACIÓN DEL INVENTARIO DE TABLAS — IJF SOR 2026-08
**Documento ID:** AUD-TABLE-RECONCILIATION-2026-08  
**Fecha:** 17 de octubre de 2026  
**Rama:** `audit/rebuild-sor-2026-08`  
**Fuente:** PDF oficial de 14 de agosto de 2026 (298 páginas)  
**Directorio:** `docs/reports/coverage_audit_2026_08/followup_review/`  

---

## 1. RECONCILIACIÓN MATEMÁTICA Y UNICIDAD DE IDENTIFICADORES

Se auditó el archivo `docs/reports/coverage_audit_2026_08/SOR_TABLE_INVENTORY_2026_08.csv` contrastándolo con los bloques detectados por PyMuPDF:

- **Total de filas en el CSV (excluyendo cabecera):** exactamente **449 filas**.
- **Identificadores únicos de tabla (`table_id`):** exactamente **449 identificadores únicos**.
  - Formato: `TAB-P{página:03d}-{índice:02d}` (ej. `TAB-P001-01` a `TAB-P296-01`).
  - **Identificadores duplicados:** **0**.
  - **Doctrina de no forzamiento de datos:** Las 449 entradas representan la suma exacta de los bloques delimitados geométricamente en el PDF.

---

## 2. ARQUITECTURA DE CLASIFICACIÓN Y MUTUA EXCLUSIVIDAD

Para resolver la duda técnica sobre si las categorías son mutuamente excluyentes o jerárquicas:

> **Regla de clasificación formal:**  
> Las categorías asignadas en la columna `table_category` del inventario CSV son **estrictamente mutuamente excluyentes**. La suma de los conteos por categoría da exactamente el total de 449 tablas:

$$\text{Total Tablas (449)} = \text{Substantivas (152)} + \text{Formato Menor (297)}$$

### Desglose Completo por Categoría:

| Categoría en CSV | ¿Es Sustantiva? | Cantidad | Descripción Técnica y Criterio de Inclusión |
| :--- | :---: | :---: | :--- |
| **`MINOR_OR_FORMATTING`** | **No** (`False`) | **297** | Cajas de advertencia, marcos de notas, encabezados decorativos enmarcados o tablas de 1 fila/1 columna sin datos matriciales. |
| **`FORM_DIAGRAM_TABLE`** | **Sí** (`True`) | **70** | Cuadrículas y esquemas de los formularios administrativos F1.3 (Págs. 208–240), catalogados en cola de validación visual. |
| **`STANDARD`** | **Sí** (`True`) | **35** | Tablas reglamentarias estándar con $\ge 2$ filas y $\ge 2$ columnas (ej. cronogramas, delegaciones, tatamis). |
| **`MULTILEVEL_COMPLEX`** | **Sí** (`True`) | **15** | Tablas con encabezados multinivel y celdas combinadas generales no pertenecientes a las categorías deportivas específicas. |
| **`POINTS_HIERARCHICAL_TABLE`** | **Sí** (`True`) | **13** | Tablas de puntos WRL (Sénior, Júnior, Cadetes, escalas 100%, 50%, expiración en págs. 51 a 57). |
| **`WEIGHT_CATEGORIES_HIERARCHICAL`** | **Sí** (`True`) | **11** | Tablas jerárquicas de categorías de peso por edad, género y tolerancias (págs. 33–36, 75–76, 103–104). |
| **`COMPETITION_SYSTEM_CONDITIONAL`** | **Sí** (`True`) | **4** | Tablas de baremos condicionales y fórmulas de torneo según cantidad de inscritos (págs. 37 a 45). |
| **`PENALTY_CLASSIFICATION_TABLE`** | **Sí** (`True`) | **4** | Tablas de baremos de arbitraje y códigos de sanciones G1.3 (págs. 175–194, 254–256). |
| **TOTAL** | — | **449** | **Conciliación matemática perfecta al 100%.** |

---

## 3. ACLARACIÓN SOBRE LAS "15 TABLAS JERÁRQUICAS" Y LAS 70 CUADRÍCULAS DE FORMULARIOS

1. **Las 15 tablas `MULTILEVEL_COMPLEX`:**  
   Son una **subcategoría directa** dentro de las 152 tablas sustantivas, correspondiente a aquellas matrices con encabezados con saltos de línea y celdas combinadas que no caen en los módulos reglamentarios especializados. No son un grupo externo independiente.
2. **Las 70 cuadrículas `FORM_DIAGRAM_TABLE`:**  
   Se concentran exclusivamente entre las páginas físicas 208 y 240 (donde coexisten 70 formularios sustantivos y 49 recuadros menores, totalizando 119 bloques tabulares en esa sección). Están debidamente aisladas en la cola `SOR_TABLE_VALIDATION_QUEUE_2026_08.csv`.
3. **Ausencia de dobles conteos:**  
   Cada tabla posee una coordenada `bbox` única y una sola asignación de categoría en el archivo maestro.

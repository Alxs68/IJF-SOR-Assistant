# INFORME DE REVISIÓN TÉCNICA FOCALIZADA — IJF SOR 2026-08
**Documento ID:** AUD-FOLLOWUP-TECHNICAL-REVIEW-2026-08  
**Fecha:** 17 de octubre de 2026  
**Rama de Trabajo:** `audit/rebuild-sor-2026-08`  
**Rama Base:** `main` (commit inalterado: `afb5b11`)  
**Fuente Oficial:** PDF IJF Sport and Organisation Rules (14 de agosto de 2026, 298 páginas, SHA-256: `9426B10D11C21A4CB9EB23150C2C4FC95BFCD463511E66BA451D2CFF005AE620`)  
**Directorio de Entrega:** `docs/reports/coverage_audit_2026_08/followup_review/`  

---

## 1. RESUMEN EJECUTIVO Y OBJETIVO

Se realizó una revisión técnica exhaustiva y focalizada para contrastar directamente contra el PDF oficial las inconsistencias potenciales señaladas en la matriz WRL, las categorías de peso, el inventario de tablas y la cobertura normativa.

Todos los hallazgos fueron diagnosticados en el código y en el PDF, corrigiendo los defectos confirmados en un conjunto de datos independiente en `followup_review/` sin sobrescribir las evidencias previas.

---

## 2. HALLAZGOS TÉCNICOS, EVIDENCIA Y CONCLUSIONES

### 2.1 Matriz WRL (Página física 52)
- **Inconsistencia detectada:** En `reconstructed_complex_tables.json`, los registros `1 contest won` y `Participation` poseían solo 7 valores en `points_by_competition`, mientras que las otras 7 posiciones tenían 8.
- **Inspección en PDF:** En la página física 52, la columna `Olympic Games` para las filas `1 contest won` y `Participation` está **físicamente en blanco** (no se asignan puntos WRL olímpicos por ganar 1 solo combate o por participar, a diferencia de los torneos WJT y Mundiales).
- **Diagnóstico:** El extractor preliminar omitió la clave en el diccionario JSON al encontrar una cadena vacía en lugar de preservarla explícitamente como celda vacía o nula.
- **Severidad:** Media (integridad estructural de datos).
- **Acción y Corrección:** Se generó `reconstructed_complex_tables_corrected.json` y `WRL_RECONCILIATION.csv`, donde todas las 9 posiciones poseen exactamente las 8 columnas oficiales, registrando `"Olympic Games": null` para las dos posiciones afectadas con su debida justificación.

---

### 2.2 Categorías de Peso (Páginas físicas 33 y 34)
- **Inconsistencia detectada:** Agrupación conjunta de Senior y Junior bajo un solo campo y omisión de la distinción formal de las 16 categorías de Cadetes de la página 33.
- **Inspección en PDF:** La página física 33 contiene cuatro cuadrículas en la tabla 2.2.1:
  1. `Senior and Junior Women`: 8 categorías (`-48 kg` a `Open`).
  2. `Cadet Women (under 18 years)`: 8 categorías (`-40 kg` a `+70 kg`).
  3. `Senior and Junior Men`: 8 categorías (`-60 kg` a `Open`).
  4. `Cadet Men (under 18 years)`: 8 categorías (`-50 kg` a `+90 kg`).
- **Diagnóstico:** El extractor preliminar sobreescribió la división de Cadetes asignándoles la cabecera anterior "Senior and Junior", generando duplicados de nombres de categoría (`-48 kg`, `-52 kg`, etc.) sin su división de edad.
- **Severidad:** Media.
- **Acción y Corrección:** Se normalizó la estructura en 32 categorías individuales completas y 18 categorías de equipos mixtos (Senior/Junior, JJ.OO. y Cadetes) en `WEIGHT_CATEGORIES_RECONCILIATION.csv` y en el JSON corregido, preservando las reglas de peso inclusivo/exclusivo y la elegibilidad para equipos mixtos.

---

### 2.3 Conciliación del Inventario de Tablas (449 Tablas)
- **Inconsistencia señalada:** Duda sobre si las categorías del inventario son mutuamente excluyentes o jerárquicas y sobre el conteo de las 15 tablas jerárquicas y las 70 cuadrículas de formularios.
- **Verificación en CSV:** El archivo `SOR_TABLE_INVENTORY_2026_08.csv` cuenta con **449 filas exactas** (excluyendo cabecera) y **449 identificadores únicos**.
- **Regla de Clasificación Demostrada:** Las categorías son **estrictamente mutuamente excluyentes**:
  $$\text{Substantivas (152)} + \text{Formato Menor (297)} = \mathbf{449}$$
  - `MINOR_OR_FORMATTING`: 297 tablas (no sustantivas).
  - `FORM_DIAGRAM_TABLE`: 70 cuadrículas (formularios F1.3, páginas 208–240).
  - `STANDARD`: 35 tablas sustantivas estándar.
  - `MULTILEVEL_COMPLEX`: 15 tablas complejas generales (subcategoría directa de las 152 sustantivas).
  - `POINTS_HIERARCHICAL_TABLE`: 13 tablas de puntos WRL.
  - `WEIGHT_CATEGORIES_HIERARCHICAL`: 11 tablas de categorías de peso.
  - `COMPETITION_SYSTEM_CONDITIONAL`: 4 tablas de baremos de competición.
  - `PENALTY_CLASSIFICATION_TABLE`: 4 tablas de códigos de sanciones.
- **Conclusión:** Se descartan dobles conteos o inconsistencias numéricas. Se documentó formalmente en `TABLE_INVENTORY_RECONCILIATION.md`.

---

### 2.4 Cobertura Normativa y Tratamiento del Apéndice F
- **Verificación en Matriz:** `SOR_COVERAGE_MATRIX_2026_08.csv` contiene **272 secciones oficiales** exactas con identificadores únicos (`SEC-001` a `SEC-272`).
- **Estados:**
  - `COMPLETO_VERIFICADO`: 238 secciones ($87.50\%$).
  - `PARCIAL`: 34 secciones ($12.50\%$).
  - `AUSENTE`: 0 secciones ($0.00\%$).
  - Total: 272 secciones ($100.00\%$).
- **Tratamiento del Apéndice F:** Las 34 secciones parciales corresponden estrictamente a los formularios F1.3.1 a F1.3.33 (páginas 208 a 240). Se ratifica la distinción entre texto normativo (extraído en pasajes) y estructura diagramática (en cola de validación visual).

---

## 3. ARTEFACTOS GENERADOS EN LA REVISIÓN

1. `FOLLOWUP_TECHNICAL_REVIEW.md`: El presente dictamen detallado.
2. `WRL_RECONCILIATION.csv`: Matriz celda por celda comparando valores del PDF vs reconstrucción preliminar vs corregida.
3. `WEIGHT_CATEGORIES_RECONCILIATION.csv`: Inventario de las 50 categorías (32 individuales y 18 mixtas) con división, género, límites y elegibilidad.
4. `TABLE_INVENTORY_RECONCILIATION.md`: Conciliación matemática de las 449 tablas y reglas de clasificación.
5. `COVERAGE_RECONCILIATION.md`: Validación matemática y metodológica de las 272 secciones del reglamento.
6. `CORRECTIONS_LOG.md`: Registro de los tres defectos confirmados con evidencia antes/después.
7. `TEST_RESULTS.md`: Reporte de ejecución de la suite de 40 pruebas unitarias aprobadas al 100%.
8. `reconstructed_complex_tables_corrected.json`: Dataset estructurado corregido.

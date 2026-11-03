# INFORME DE AUDITORÍA DE TABLAS — IJF SOR 14 DE AGOSTO DE 2026
**Documento ID:** AUD-TABLES-2026-08-VAL  
**Fecha:** 17 de octubre de 2026  
**Ámbito:** Todas las tablas, matrices de datos y formularios tabulares en las 298 páginas del PDF oficial  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant` (rama: `audit/rebuild-sor-2026-08`)  

---

## 1. RESUMEN DEL INVENTARIO DE TABLAS

Mediante extracción geométrica y estructural con PyMuPDF (`find_tables` y análisis de celdas delimitadas por líneas vectoriales), se auditó el documento íntegro de 298 páginas:

| Clasificación de Tablas | Cantidad | Porcentaje | Descripción |
| :--- | :---: | :---: | :--- |
| **Tablas Detectadas Totales** | **449** | 100.0% | Cuadrículas estructurales y bloques tabulares en el PDF. |
| **Tablas Sustantivas** | **152** | 33.85% | Tablas con $\ge 2$ filas, $\ge 2$ columnas y $\ge 4$ celdas con contenido normativo. |
| **Cajas / Bloques de Formato Menor** | **297** | 66.15% | Recuadros de advertencia, notas, encabezados decorativos o divisores de una fila. |

### 1.1 Desglose de Tablas Sustantivas por Categoría Normativa
1. **Puntajes y Clasificación Mundial WRL (`POINTS_HIERARCHICAL_TABLE`):** 13 tablas (Págs. 51 a 57).
2. **Categorías de Edad, Peso y Género (`WEIGHT_CATEGORIES_HIERARCHICAL`):** 11 tablas (Págs. 33 a 36, 75 a 76, 103 a 104).
3. **Sistemas de Competición y Medallero (`COMPETITION_SYSTEM_CONDITIONAL`):** 4 tablas (Págs. 37 a 45).
4. **Códigos y Baremos de Sanciones (`PENALTY_CLASSIFICATION_TABLE`):** 4 tablas (Págs. 175 a 194, 254 a 256).
5. **Tablas Estándar Reguladoras (`STANDARD`):** 35 tablas (Págs. 13 a 207, 243 a 298).
6. **Formularios y Diagramas de Flujo F1.3 (`FORM_DIAGRAM_TABLE`):** 70 cuadrículas correspondientes a los formularios oficiales F1.3.1 a F1.3.33 (Págs. 208 a 240).

---

## 2. RECONSTRUCCIÓN DE TABLAS COMPLEJAS Y JERÁRQUICAS (FASE 4)

Se generó la estructura normalizada en JSON (`scratch/reconstructed_complex_tables.json` y embebida en `docs/reports/coverage_audit_2026_08/SOR_COVERAGE_EVIDENCE_2026_08.json`), resolviendo:

### A. Escala de Puntos WRL (`WRL_POINTS_ALLOCATION_MATRIX`, Pág. 52)
- **Problema en extracción plana:** Cabeceras en dos líneas combinadas y columnas por nivel de torneo (Continental Open, Continental Championships, Junior World Ch., Grand Prix, Grand Slam, Masters, World Championships, Olympic Games).
- **Estructura Reconstruida:** Mapeo jerárquico `Placing` $\to$ `points_by_competition`.
- **Valores certificados:**
  - 1.er lugar: Olympic Games = **2200 pts**, World Ch. = **2000 pts**, Masters = **1800 pts**, Grand Slam = **1000 pts**, Grand Prix / Junior World Ch. = **700 pts**, Continental Ch. = **800 pts**, Continental Open = **100 pts**.
  - 2.º lugar: Olympic Games = **1540 pts**, World Ch. = **1400 pts**, Masters = **1260 pts**, etc.

### B. Categorías de Peso Individual y Equipos Mixtos (Págs. 33 y 34)
- **Problema:** Encabezados combinados verticalmente ("Senior and Junior Women", "Senior and Junior Men") seguidos de subfilas de peso y clasificación.
- **Estructura Reconstruida:** Registros desagregados con claves explícitas: `division`, `gender`, `weight_category`, `classification_name` (ej. Femenino: `-48 kg` Extra-lightweight, `-52 kg` Half-lightweight, etc.). En Equipos Mixtos, se mapea la correspondencia de pesos individuales elegibles para `-57 kg`, `-70 kg`, `+70 kg` (mujeres) y `-73 kg`, `-90 kg`, `+90 kg` (hombres).

### C. Códigos de Penalización y Arbitraje (Apéndice G1.3, Págs. 254–256)
- **Estructura Reconstruida:** 55 registros completos mapeando `code_or_article`, `description` y `sanction` (ej. Códigos de shido por no combatividad, salidas de tatami, agarres ilegales y hansoku-make directo/indirecto).

---

## 3. VALIDACIÓN DE RECUPERACIÓN SEMÁNTICA Y RAG (FASE 5)

Se ejecutaron pruebas directas sobre el motor productivo `RagEngine` en modo `14 August 2026 (Official)`:

1. **Consulta:** `"Olympic Games 1st place 2200 points WRL"`  
   - **Pasajes recuperados:** `SOR-2026-08-P052-S064`, `SOR-2026-08-P052-S065`, `SOR-2026-08-P052-S066`.  
   - **Resultado:** 🟢 **Aprobado**. Recuperó con éxito el valor exacto de 2200 puntos y el contexto de la tabla WRL.
2. **Consulta:** `"Penalty code non combativity shido"`  
   - **Pasajes recuperados:** `SOR-2026-08-P254-S268`, `SOR-2026-08-P254-S269`.  
   - **Resultado:** 🟢 **Aprobado**. Recuperó el código y la descripción normativa de no combatividad.
3. **Consulta:** `"Double repechage 16 athletes"`  
   - **Pasajes recuperados:** `SOR-2026-08-P222-S244`, `SOR-2026-08-P222-S245`, `SOR-2026-08-P217-S239`.  
   - **Resultado:** 🟢 **Aprobado**. Enlazó al sistema de doble repesca correspondiente.

---

## 4. COLA DE VALIDACIÓN VISUAL PENDIENTE (PÁGINAS 208–240)

- **Identificación:** Se clasificaron 70 cuadrículas y formularios en `SOR_TABLE_VALIDATION_QUEUE_2026_08.csv`.
- **Naturaleza técnica:** Son formatos gráficos (hojas de pesaje, llaves de eliminación, organigramas de doble repesca F1.3.1 a F1.3.33). Aunque el texto instructivo está extraído, los árboles geométricos de las llaves no deben sustituirse por parseos heurísticos sin certificación visual humana.
- **Estado de cola:** `PENDIENTE_VALIDACION_VISUAL`.

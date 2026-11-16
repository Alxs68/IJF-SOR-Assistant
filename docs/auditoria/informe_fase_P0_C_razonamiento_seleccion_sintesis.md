# INFORME TÉCNICO FASE P0-C — CALIDAD DEL RAZONAMIENTO, SELECCIÓN, SUFICIENCIA Y SÍNTESIS CONTROLADAS
## IJF Sport and Organisation Rules (SOR) Assistant 2026

> **Proyecto:** IJF SOR Assistant 2026  
> **Fase:** P0-C (Selección, Suficiencia y Síntesis Controladas)  
> **Fecha:** 7 de noviembre de 2026  
> **Rama:** `integration/ijf-sor-2026-08-merge`  
> **Ejecutor Técnico:** Antigravity  
> **Supervisor Metodológico y Auditor Independiente:** ChatGPT  
> **Product Owner y Autoridad Normativa:** Alexis Oliveros Lozano  
> **Corpus Oficial:** *IJF Sport and Organisation Rules 2026* (14 de agosto de 2026, 298 páginas físicas, SHA-256 `9426b10d...`)

---

## 1. Estado Inicial del Repositorio

1. **Línea Base Heredada:**  
   La fase previa **P0-B** (Recuperación localizada y alineación de kumi-kata) alcanzó cierre funcional satisfactorio, logrando 10/10 PASS en la batería focal CGPT-06 y 11/11 PASS en la suite de regresión de casos ratificados por Alexis Oliveros.
2. **Suite de Pruebas Inicial:**  
   271 pruebas unitarias e integrales en verde (`271 passed in 66.49s`).
3. **Restricción de Operación:**  
   Operación 100% local desconectada en `C:\PROYECTOS\IJF-SOR-Assistant`. Prohibido crear commits, hacer push, publicar Release o realizar despliegues en OCI (`https://sor.alxol.com`).

---

## 2. Definición y Alcance Encontrado de P0-C

En la inspección estática del repositorio se localizó la definición y mandato formal de P0-C en [`docs/plan_correctivo_p0_p1.md`](file:///c:/PROYECTOS/IJF-SOR-Assistant/docs/plan_correctivo_p0_p1.md), Secciones 5, 6 y 7:

* **Objetivo Canónico:**  
  *«Evitar la dependencia mecánica de Top-1 y la mezcla ciega de Top-K.»*
* **Entregables Definidos:**  
  1. **Contrato de selección:** Romper la suposición estática de que `evidence[0]` domina obligatoriamente la estructuración.
  2. **Perfiles por intención:** Calificar la suficiencia de la evidencia según la naturaleza de la consulta (*Sanción*, *Puntuación*, *Medida/Tiempo*, *Excepción*, *Procedimiento*, *Definición*).
  3. **Pruebas de conflicto y no-contradicción:** Impedir la mezcla acrítica de evidencias divergentes o derogadas.
  4. **Síntesis trazable:** Asegurar que cada afirmación en Nivel 1 esté directamente soportada por la norma primaria oficial.
* **Criterio de Aceptación:**  
  *Afirmaciones soportadas y excepciones preservadas; una respuesta correcta no se penaliza por haber sido recuperada en un rango distinto de uno (rank > 0).*
* **Regla Negativa ("No hacer"):**  
  No imponer requisitos lexicográficos universales rígidos ni mezclar autoridades documentales.

---

## 3. Mapeo de Componentes Existentes e Identificación de Brechas

| Área del Flujo | Componentes Involucrados | Brecha o Defecto Real Identificado |
|---|---|---|
| **Retrieval y Selección** | `src/rre_engine.py`<br>`src/response_structurer.py` | **Dependencia Mecánica de Top-1:** En `build_deterministic_structured_answer`, el código establecía rígidamente `top_ev = evidence[0]`. Si la evidencia rectora específica se encontraba en `evidence[1]` o `evidence[2]` (Top-K candidatos), el estructurador la ignoraba y forzaba la extracción desde el primer nodo, degradando la respuesta. |
| **EvidenceBundle y Gobernanza** | `src/document_governance.py`<br>`src/document_validator.py` | En `document_validator.py`, la propiedad `is_sufficient_for_decision` se evaluaba como una condición binaria cuantitativa (`len(primary_lane) > 0 and not has_conflict`), sin validar si el contenido satisfacía los requisitos del perfil de intención consultado. |
| **Interpretación y Razonamiento** | `src/ada_assistant.py` | El prompt de ADA contenía directrices de razonamiento sólidas para modo conectado, pero en modo local desconectado no existía un clasificador de intención que garantizara que la cláusula extraída cumpliera el estándar deóntico. |
| **Estructuración de Respuestas** | `src/response_structurer.py` | `SYNONYM_EXPANSIONS` estaba encapsulado localmente dentro de una función, impidiendo su reutilización modular en el contrato de selección y verificación de suficiencia. |
| **Validación y Citas** | `src/normative_validator.py` | Validaba artículos y códigos de penalización contra texto recuperado, pero carecía de una prueba unitaria específica de rango independiente para candidatos múltiples. |

---

## 4. Cambios Implementados

### 4.1. Contrato de Selección de Candidatos (`select_rector_evidence`)
Se implementó en [`src/response_structurer.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/src/response_structurer.py) el evaluador de candidatos Top-K:
- Analiza todos los pasajes candidatos recuperados en `evidence` (`ev_0, ev_1, ..., ev_k`).
- Segmenta y califica las cláusulas sustantivas de cada candidato contra la consulta, expansiones ontológicas y bonificaciones de precisión de frase.
- Si un candidato en rango superior a 0 (`rank > 0`) contiene una cláusula con especificidad demonstrablemente superior a `evidence[0]`, es promovido dinámicamente a **evidencia rectora primaria** (`top_ev`), preservando las restantes como referencias complementarias.
- Si `evidence[0]` ya es óptimo o existe empate, se preserva el orden natural del ranker RRE.

### 4.2. Evaluador de Perfiles de Intención y Suficiencia (`IntentProfileEvaluator`)
Se incorporó el evaluador cualitativo conforme a la Sección 5 del plan maestro:
- **Perfiles clasificados:** `SANCTION`, `SCORE`, `MEASUREMENT_TIME`, `EXCEPTION`, `PROCEDURE`, `DEFINITION`, `GENERAL`.
- **Evaluación de suficiencia:**
  * *Sanción:* Verifica la presencia de la conducta y la consecuencia deóntica (*Shido*, *Hansoku-make*, *allowed*, *valid*).
  * *Puntuación:* Verifica la acción técnica y la valoración técnica (*Ippon*, *Waza-ari*, *Yuko*).
  * *Medida/Tiempo:* Verifica la co-ocurrencia de valor numérico y unidad de medida (*m, cm, segundos, minutos*).
- Si la cláusula es parcialmente suficiente o carece de consecuencia explícita, se inyecta una advertencia precisa de suficiencia en `limitations`.

### 4.3. Exposición Modular de Ontología de Sinónimos
Se elevó `SYNONYM_EXPANSIONS` al ámbito de módulo en `src/response_structurer.py` para permitir su uso compartido en selección de evidencia, evaluación de suficiencia y pruebas unitarias.

---

## 5. Pruebas Ejecutadas y Resultados

### 5.1. Nueva Suite de Pruebas P0-C (`tests/test_p0_c_reasoning_and_selection.py`)
Se crearon 5 pruebas formales para blindar el contrato P0-C:
* `test_01_intent_profile_classification`: Clasificación correcta de los 7 perfiles de intención (PASS).
* `test_02_sufficiency_evaluation`: Detección cualitativa de suficiencia vs. insuficiencia en sanciones, puntuación y medidas (PASS).
* `test_03_selection_contract_promotes_rank2_over_rank1`: Verificación de que un candidato específico en rango 2 (`P178` cross grip) es promovido sobre un rango 1 genérico (`P182` breaking grip with knee) (PASS).
* `test_04_selection_contract_preserves_rank1_when_already_optimal`: Verificación de estabilidad cuando rango 1 ya es la norma óptima (PASS).
* `test_05_conflict_detection_prevents_contradictory_synthesis`: Verificación de detección de conflicto normativo entre fuente derogada y SOR 2026 vigente (PASS).

**Resultado:** **5/5 PASS en 0.87s.**

### 5.2. Regresión de Casos Ratificados por Alexis Oliveros
Ejecución de `scratch/test_regression_11_cases.py`:
* VF01-01, VF01-07, VF01-09, VF01-14, VF01-23, VF01-24, VF01-25 (Abstención OOD), VF01-29, VF01-30, VF01-42, VF01-48.
* **Resultado:** **11/11 PASS (100%)**.

### 5.3. Batería Focal CGPT-06 (10 Escenarios de Kumi-kata)
Ejecución de `scratch/dump_p0b_evidence.py`:
* ESC-01 a ESC-10.
* **Resultado:** **10/10 PASS (100%)**.

### 5.4. Suite Completa del Sistema
* **Comando:** `python -m pytest tests/`
* **Resultado:** **276 passed in 56.89s (0 fallos, 0 errores, 0 skips)**.

---

## 6. Evidencias Reproducibles

1. **Código fuente modificado:**
   * [`src/response_structurer.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/src/response_structurer.py) (Adición de `IntentProfileEvaluator`, `select_rector_evidence` y reordenamiento dinámico).
2. **Suite de pruebas unitarias P0-C:**
   * [`tests/test_p0_c_reasoning_and_selection.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/tests/test_p0_c_reasoning_and_selection.py).
3. **Scripts de verificación y resultados:**
   * `scratch/test_apply_p0c.py` (Demostración de promoción de candidato rank > 0).
   * `scratch/evidencias_p0b_focales.json` (10/10 escenarios intactos).
   * `scratch/evidencias_p0b_regresion.json` (11/11 casos ratificados intactos).
   * Log del sistema: `task-1856.log` (276 tests pasando limpiamente).

---

## 7. Limitaciones Pendientes

1. **Modo Conectado (LLM API) vs. Modo Local Desconectado:**  
   En modo local desconectado, la síntesis se realiza mediante el estructurador determinista certificado. La síntesis generativa fluida multi-párrafo sigue reservada al modo conectado con claves API activas (Gemini/Groq).
2. **Consultas con Premisas Falsas o Fuera de Dominio (OOD):**  
   El tratamiento de consultas ambiguas o con premisas inexistentes está cubierto por el detector OOD y la abstención formal de `DocumentValidator`, cuya calibración exhaustiva forma parte de la siguiente fase planificada (**P1-A / P1-B**).

---

## 8. Dictamen Técnico y Recomendación

### Dictamen Técnico:
* El defecto de dependencia rígida del Top-1 (`top_ev = evidence[0]`) ha sido resuelto mediante el contrato de selección de candidatos de P0-C.
* Se incorporaron perfiles de intención y evaluación cualitativa de suficiencia conforme al diseño maestro.
* Se preservaron íntegramente los 11 criterios ratificados por Alexis Oliveros y los 10 escenarios focales de P0-B.
* Los 276 tests de la suite general pasan al 100%.

> **Conforme a la restricción fundamental:**  
> Como Ejecutor Técnico, Antigravity **NO declara el cierre unilateral definitivo de P0-C**. Entrega el expediente técnico completo con evidencia auditable para el dictamen y ratificación independiente de **ChatGPT** y **Alexis Oliveros Lozano**.

### Recomendación del Siguiente Paso:
Una vez que el auditor independiente ChatGPT revise y dictamine la conformidad de P0-C:
1. Proceder a la fase **P1-A (Calibración de Abstención y Detección OOD)** conforme a la secuencia del Plan Correctivo P0/P1.
2. Mantener la prohibición estricta de commit, push y despliegue OCI hasta la culminación formal de la batería P1.

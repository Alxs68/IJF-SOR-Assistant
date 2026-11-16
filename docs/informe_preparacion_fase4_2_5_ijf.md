# Informe de Preparación — Fase 4.2.5: Calibración y Endurecimiento Multifuente
**Proyecto:** IJF SOR Assistant  
**Fase:** 4.2.5 — Calibración y Endurecimiento de la Recuperación Multifuente Sidecar  
**Supervisor:** Alexis Oliveros Lozano  
**Arquitectura y Auditoría:** ChatGPT  
**Ejecutor:** Antigravity  
**Fecha:** 2026-11-05  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Branch:** `integration/ijf-sor-2026-08-merge`  
**Estado:** **PREPARACIÓN COMPLETADA — SIN MODIFICACIÓN DE CÓDIGO FUNCIONAL**

---

## 1. Identificación y Cumplimiento del Mandato

En cumplimiento estricto de la **Orden de Preparación de la Fase 4.2.5**, Antigravity ha completado exclusivamente las tareas de planificación técnica, análisis estático y diseño metodológico requeridas, **sin modificar código funcional, sin alterar archivos del corpus SOR ni del Sidecar, y sin activar flags en el sistema**.

El presente informe consolida los entregables de planificación para la revisión de **Alexis Oliveros** y la auditoría técnica de **ChatGPT**.

---

## 2. Inventario de Documentos Creados en esta Preparación

Todos los documentos requeridos fueron creados bajo estándares autocontenidos y rigurosos en el directorio `docs/`:

| Documento Creado | Ruta en el Repositorio | Propósito / Alcance |
| :--- | :--- | :--- |
| **Plan Maestro 4.2.5** | `docs/plan_fase4_2_5_calibracion_multifuente_ijf.md` | Marco metodológico, análisis matemático de BM25, alternativas de corte, gobernanza e invarianza. |
| **Benchmark Ampliado** | `docs/benchmark_fase4_2_5_multifuente_ijf.md` | Matriz detallada de 40 consultas etiquetadas en 8 categorías funcionales y adversariales. |
| **Criterios de Aceptación** | `docs/criterios_aceptacion_fase4_2_5_ijf.md` | Definición operacional de métricas, fórmulas, dataset y umbrales propuestos para aprobación. |
| **Orden de Ejecución** | `docs/orden_ejecucion_fase4_2_5_ijf.md` | Borrador de orden técnica formal delimitando el alcance exacto para cuando Alexis autorice. |
| **Informe de Preparación** | `docs/informe_preparacion_fase4_2_5_ijf.md` | Este informe de cierre técnico de la fase preparatoria. |

---

## 3. Análisis Técnico de la Situación Actual

### 3.1. Diagnóstico del Comportamiento de BM25 en Corpus Pequeño
A partir de la inspección de sólo lectura de `src/multisource_retriever.py`:
- El Sidecar opera con $N = 8$ documentos y una longitud promedio $\text{avgdl} \approx 18.0$ tokens.
- El $\text{IDF}$ máximo posible para cualquier término es $\approx 1.7918$.
- Cuando una consulta comparte un término genérico aislado ("combate", "penalización", "área"), la fórmula estándar de BM25 genera un score de entre $1.60$ y $2.70$.
- La hipótesis previa de fijar un umbral estático de $score \ge 3.0$ resulta **insuficiente y matemáticamente vulnerable**, ya que:
  a) Penaliza consultas legítimas breves y ultra-específicas de 1 término clave (e.g. "¿Qué es Yuko?").
  b) No previene que consultas largas con múltiples palabras genéricas acumulen puntajes espurios mayores a $3.0$.

### 3.2. Solución de Diseño Propuesta
Se propone un **filtro compuesto de dos etapas**:
1. **Filtro de Cobertura de Términos (Overlap Ratio):** La consulta debe tener al menos el $50\%$ de sus términos sustantivos presentes en el fragmento candidato para ser admitida (en consultas de $\ge 2$ términos sustantivos).
2. **Normalización por IDF Teórico Máximo:** El score se evalúa como la fracción de relevancia obtenida frente al IDF acumulado de los términos de la consulta. Si el ratio es inferior a $0.35$, el Sidecar emite `status: "ABSTAIN"` y descarta el candidato.

---

## 4. Criterios de Aceptación y Decisiones Pendientes de Alexis

Se han formulado los siguientes objetivos para la futura ejecución:
- **Recall@1 Dirigido:** $\ge 95.0\%$.
- **Falsos Positivos Normativos:** $0$ en consultas canónicas puras y OOD.
- **Invarianza Primaria del SOR:** $100.0\%$ (equivalencia bit a bit de `evidence`).
- **Gobernanza Criptográfica:** $100.0\%$ de trazabilidad con hashes de 64 caracteres.
- **Regresión Global:** $100\%$ PASS ($\ge 261$ pruebas en `tests/`).

### Decisiones Pendientes que Requieren Aprobación del Supervisor:
1. **Aprobación de la Matriz de 40 Consultas:** Confirmar si el dataset ampliado cubre adecuadamente los casos adversariales y bilingües.
2. **Aprobación del Filtro de Overlap vs Umbral Fijo:** Validar la adopción de la alternativa compuesta (cobertura de términos + normalización IDF) frente a la regla fija de $score \ge 3.0$.
3. **Autorización Expresa para Ejecutar:** Emitir la orden técnica definitiva para iniciar la implementación de código en `src/multisource_retriever.py` y las nuevas pruebas.

---

## 5. Evidencia de No-Modificación de Código e Integridad del Repositorio

Se certifica mediante verificación de estado en Git y cálculo criptográfico que **ningún archivo funcional de código, corpus o configuración fue alterado** durante esta actividad:

### 5.1. Estado de Archivos Funcionales en Git
- `src/rre_engine.py`: Conserva intacta la implementación de Fase 4.2.3.
- `src/multisource_retriever.py`: Conserva intacta la implementación de Fase 4.2.3.
- `tests/test_multisource_evaluation.py`: Conserva intacta la implementación de Fase 4.2.4.
- `data/corpus_multisource/`: Sin nuevos archivos procesados ni manifiestos alterados.

### 5.2. Matriz Criptográfica de Invariabilidad del SOR Primario

| Componente Canónico SOR | Ruta en Repositorio | SHA-256 Verificado | Estado |
| :--- | :--- | :--- | :--- |
| **PDF SOR 2026** | `data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf` | `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620` | **MATCH (INMUTABLE)** |
| **Passages SOR** | `data/processed/rebuild_2026_08_corrected/passages_candidate.json` | `7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b` | **MATCH (INMUTABLE)** |
| **Vector Index SOR** | `data/processed/rebuild_2026_08_corrected/vector_index_candidate.json` | `e182c77e0775472eb73d22ab92b15d026d067cbf6264fb8b25b207479c4668eb` | **MATCH (INMUTABLE)** |
| **Dense Meta SOR** | `data/processed/rebuild_2026_08_corrected/dense_embeddings_meta.json` | `c96b214bc14801ad903d58e0245d48c008d65ac051d339fd4e6b65e30709160e` | **MATCH (INMUTABLE)** |
| **Knowledge Graph** | `data/processed/rebuild_2026_08_corrected/knowledge_graph_candidate.json` | `95d5a67936cf48d3bc79b69bf370bb1a83a255f938a7322e0dae256450dde215` | **MATCH (INMUTABLE)** |

---

## 6. Dictamen Preliminar del Ejecutor

> **PREPARACIÓN TÉCNICA Y DOCUMENTAL EXITOSA Y CONFORME.**
> 
> La planificación de la Fase 4.2.5 proporciona una base rigurosa, matemáticamente fundada y criptográficamente controlada para endurecer la recuperación Sidecar sin arriesgar la estabilidad del RRE 2026.
> 
> **Confirmación de Cierre:** No se implementó código de la fase. Se remite el compendio documental completo a la auditoría de **ChatGPT** y a la decisión formal de **Alexis Oliveros Lozano**.

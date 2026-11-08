# INFORME TÉCNICO DE IMPLEMENTACIÓN LOCAL K=5 CANÓNICO (RRE 3.0)
## IJF SOR Assistant 2026 — Ejecución Soberana DEC-009

**Fecha:** 8 de noviembre de 2026  
**Autoridad Normativa y Product Owner:** Alexis Oliveros Lozano  
**Planificador, Supervisor Metodológico y Auditor Independiente:** ChatGPT  
**Ejecutor Técnico Local:** Antigravity  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Rama Activa:** `integration/ijf-sor-2026-08-merge`  
**Decisión de Respaldo:** DEC-009 (`docs/DECISIONES.md`)  
**Estado:** IMPLEMENTACIÓN LOCAL COMPLETADA Y VALIDADA AL 100% (SIN MODIFICACIÓN EN PRODUCCIÓN)

---

## 1. DIAGNÓSTICO DE CONFIGURACIÓN INICIAL

Con anterioridad a la ratificación formal de la decisión **DEC-009**, el parámetro de recuperación $K$ presentaba divergencias y valores residuales en las diferentes capas del código fuente del backend:

1. **`src/rag_engine.py`**:
   - `retrieve_context(self, query, k=3, min_score=None, depth=1)`: valor por defecto en $K=3$.
   - `query(self, user_query, k=3, min_score=None, language=None)`: valor por defecto en $K=3$.
2. **`src/ada_assistant.py`**:
   - `analyze_situation(self, situation_query: str, top_k: int = 4, language=None)`: valor por defecto en `top_k=4`.
3. **`src/rre_engine.py`**:
   - `retrieve(self, query: str, top_k: int = 4, min_confidence: float = 0.015, expand_graph: bool = True)`: firma canónica en `top_k=4`.
4. **`app.py` (Interfaz de usuario Streamlit)**:
   - Invoca directamente `res = engine.query(query_to_run, language=lang)` sin pasar argumentos explícitos de $K$ ni `min_score`. Al delegar en los valores por defecto del backend, heredaba la discrepancia previa ($K=3$). Los sliders manuales de $K$ y `min_score` habían sido retirados en cumplimiento de P1-B y DEC-008.

**Fundamento empírico:** El experimento comparativo multidimensional ($K=3$ vs $K=5$ vs $K=8$), documentado en `docs/auditoria/experimento_comparativo_k_rre_2026_11.md`, evidenció que $K=5$ maximiza la completitud normativa (+30.6% de evidencia relevante complementaria, 128 vs 98 pasajes) y resuelve el déficit de fundamentación en el 33.9% de las consultas complejas, con 100% de exactitud y 0% de falsas aceptaciones OOD. Consecuentemente, el Product Owner ratificó $K=5$ como parámetro canónico universal mediante DEC-009.

---

## 2. ARCHIVOS MODIFICADOS Y JUSTIFICACIÓN TÉCNICA

| Archivo | Ubicación | Modificación | Justificación Técnica |
| :--- | :--- | :--- | :--- |
| `src/rag_engine.py` | L129, L199 | `k=3` $\rightarrow$ `k=5` | Establece $K=5$ como valor canónico por defecto en la puerta de entrada de consultas (`query`) y en la función de recuperación contextual (`retrieve_context`). Preserva `min_score=None`. |
| `src/ada_assistant.py` | L83 | `top_k: int = 4` $\rightarrow$ `top_k: int = 5` | Sincroniza la firma de análisis arbitral en ADA para que, ante invocaciones sin parámetro explícito, transfiera exactamente $K=5$ semillas a RRE. |
| `src/rre_engine.py` | L752 | `top_k: int = 4` $\rightarrow$ `top_k: int = 5` | Establece $K=5$ en el núcleo del Reasoning Retrieval Engine (RRE 3.0), garantizando que el corte de semillas normativas directas (`top_seeds`) extraiga hasta 5 evidencias de máxima afinidad semántica. |
| `tests/test_p1_b_configuracion_e2e.py` | L200-L235 | Nueva prueba `test_10_canonical_k5_default_configuration` | Garantiza mediante inspección reflexiva (`inspect.signature`) y ejecución empírica que los valores por defecto de `RagEngine`, `ADA` y `RRE` sean idénticos a $K=5$ y `min_score=None`. |

---

## 3. DESCRIPCIÓN DE LA IMPLEMENTACIÓN TÉCNICA

### 3.1. Cadena de Propagación Canónica
La propagación de $K=5$ opera de manera unificada y transparente en toda la arquitectura del sistema:
```
[app.py (Streamlit UI)]
       │
       ▼ (invoca engine.query(query_to_run, language=lang) sin parámetros manuales)
[RagEngine.query(..., k=5, min_score=None)]
       │
       ▼ (transfiere top_k=k = 5)
[ArbitrationDecisionAssistant.analyze_situation(..., top_k=5)]
       │
       ▼ (transfiere top_k=top_k = 5)
[ReasoningRetrievalEngine.retrieve(..., top_k=5, min_confidence=0.015)]
       │
       ├─ Sparse Search (BM25) -> top 25
       ├─ Dense Search (MiniLM 384d) -> top 25
       ├─ Reciprocal Rank Fusion (RRF) & Penalizaciones
       ├─ Deduplicación textual y corte estricto: if len(top_seeds) >= top_k (5) -> break
       └─ Expansión acotada por grafo de conocimiento (Knowledge Graph)
```

### 3.2. Preservación Estricta de `min_score=None`
Se conservó `min_score=None` en todas las firmas del backend. En el motor activo SOR 2026-08 (ADA + RRE), el filtrado de calidad no depende de un umbral cosénico genérico de UI (el cual demostró ser un control ambiguo e inoperante en P1-B), sino de:
1. `min_confidence: float = 0.015` en RRE.
2. Umbral de abstención normativo de 0.12 en la certidumbre de evidencia primaria.
3. Validación de pertinencia ontológica y gobernanza documental en `DocumentValidator`.

### 3.3. Estado de la Interfaz de Usuario (`app.py`)
Se ratificó que en `app.py`:
- Los sliders `k_param = st.slider` y `min_score_param = st.slider` permanecen retirados.
- La invocación es limpia y determinista: `res = engine.query(query_to_run, language=lang)`.
- El usuario final recibe automáticamente la experiencia calibrada $K=5$, sin controles confusos ni riesgo de descalibración arbitral.

---

## 4. PRUEBAS EJECUTADAS, RESULTADOS Y EVIDENCIAS NUMÉRICAS

Todas las suites de prueba fueron ejecutadas localmente en el entorno real del repositorio, arrojando un **100% de éxito (cero fallos)**:

| Suite / Script de Validación | Propósito / Alcance | Casos Evaluados | Resultado | Tasa de Éxito |
| :--- | :--- | :---: | :---: | :---: |
| `tests/test_p1_b_configuracion_e2e.py` | Configuración E2E, firmas reflexivas $K=5$, `min_score=None`, abstención, contratos N1/N2. | 10 | 10 PASS, 0 FAIL | **100.0%** |
| `scratch/test_regression_11_cases.py` | Regresión normativa oficial de los 11 casos ratificados por Alexis (VF01). | 11 | 11 PASS, 0 FAIL | **100.0%** |
| `scratch/test_focal_cgpt06_queries.py` | Consultas focales de alta especialización técnica arbitral (Kumi-kata y agarres ilegales). | 10 | 10 PASS, 0 FAIL | **100.0%** |
| `scratch/benchmark_p1a_ood_dataset.py` | Benchmark balanceado P1-A (15 casos in-domain + 25 casos OOD en 5 subcategorías). | 40 | 40 PASS, 0 FAIL | **100.0%** |
| `tests/test_p0_c_reasoning_and_selection.py` | Razonamiento arbitral P0-C, desambiguación de comandos y jerarquía normativa. | 9 | 9 PASS, 0 FAIL | **100.0%** |
| `tests/test_p1_a_abstention_ood.py` | Detección determinista de fuera de dominio y abstención obligatoria P1-A. | 10 | 10 PASS, 0 FAIL | **100.0%** |
| `tests/test_ui_controls_and_novedades.py` | Retiro de controles de UI, registro de novedades operativas y exportación CSV. | 5 | 5 PASS, 0 FAIL | **100.0%** |
| `tests/test_document_governance.py` | Validación de gobernanza documental, jerarquías Tier 1 y contratos EvidenceBundle. | 15 | 15 PASS, 0 FAIL | **100.0%** |
| `tests/test_negative_domain_anchor_scoring.py` | Detección y penalización por anclas semánticas negativas (BK-01). | 25 | 25 PASS, 0 FAIL | **100.0%** |
| `tests/test_feedback_manager.py` | Gestión de retroalimentación de usuario y persistencia de novedades. | 13 | 13 PASS, 0 FAIL | **100.0%** |
| **TOTAL CONSOLIDADO** | **Evaluación integral de estabilidad y regresión** | **148** | **148 PASS, 0 FAIL** | **100.0%** |

### 4.1. Desglose Numérico del Benchmark P1-A (40 casos)
- **Precisión dentro de dominio (In-Domain Accuracy):** 100.0% (15/15).
- **Tasa de falsas abstenciones (False Abstentions):** 0.0% (0/15).
- **Tasa de abstención OOD correcta (OOD Abstention Rate):** 100.0% (25/25).
- **Tasa de falsas aceptaciones OOD (False Acceptances):** 0.0% (0/25).
- **Tiempo de inferencia promedio:** < 45 ms por consulta.

---

## 5. PRUEBAS PENDIENTES O FALLIDAS

- **Pruebas fallidas:** 0.
- **Pruebas pendientes en entorno local:** Ninguna. Todas las suites unitarias, de integración, regresión y benchmarks han concluido exitosamente.

---

## 6. CONFIRMACIÓN DE RESTRICCIONES RESPETADAS

1. **Integridad del Corpus SOR 2026-08:** Inalterado.
   - 385 pasajes / nodos normativos oficiales cargados.
   - Hash SHA-256 verificado: `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620`.
2. **Índices y Embeddings:** Inalterados. Se conservan intactos los índices `all-MiniLM-L6-v2` (384 dimensiones) y TF-IDF precalculados.
3. **Criterios Normativos VF01:** Inalterados. Los 11 casos ratificados por Alexis mantienen dictamen y trazabilidad exacta (11/11 PASS).
4. **Criterios P0-C y P1-A:** Preservados sin regresión.
5. **K Adaptativo:** NO implementado. Se mantuvo estrictamente la arquitectura estática determinista $K=5$.
6. **Git y Control de Versiones:** NO se han realizado commits, pushes, merges, tags ni releases. Todos los cambios permanecen en el working tree local de la rama `integration/ijf-sor-2026-08-merge`.
7. **Infraestructura de Producción (OCI):** NO se ha realizado ninguna conexión SSH ni modificación sobre la máquina virtual en Oracle Cloud ni el servicio activo en `https://sor.alxol.com`.

---

## 7. RIESGOS E INCONSISTENCIAS DETECTADAS

1. **Discrepancia temporal Local vs Producción:**
   - En el entorno local, $K=5$ está 100% implementado y verificado.
   - En el servidor de producción (`https://sor.alxol.com`), la aplicación se encuentra corriendo bajo el commit `61afc1b` (el cual opera con los defaults preexistentes de $K=3$).
   - *Riesgo:* Inconsistencia de respuestas entre pruebas en producción y pruebas locales si un usuario externo ejecuta consultas antes del despliegue oficial.
   - *Mitigación:* Se encuentra claramente documentado en `docs/deployment/PRODUCTION_MANIFEST.md` y `PROJECT_STATUS.md` que producción permanece en versión previa hasta la ratificación del release.

---

## 8. ESTADO FINAL DE LA IMPLEMENTACIÓN LOCAL

- **Estado técnico:** Completado exitosamente.
- **Parámetro canónico efectivo:** $K=5$.
- **Umbral de relevancia:** `min_score=None` (calibrado internamente en RRE).
- **Interfaz Streamlit:** Limpia, sin sliders técnicos, consumiendo directamente $K=5$.
- **Cobertura de pruebas:** 148/148 casos evaluados superados con 100% de precisión y cero regresiones.

---

## 9. RECOMENDACIÓN TÉCNICA PARA LA SIGUIENTE ETAPA

1. **Someter a Auditoría de ChatGPT:** Entregar este informe a ChatGPT para su revisión metodológica independiente.
2. **Autorización Expresa del Product Owner (Alexis):** Una vez aprobado por ChatGPT, solicitar a Alexis la autorización para:
   - Crear el commit atómico local en `integration/ijf-sor-2026-08-merge` que consolide formalmente los cambios de DEC-009 y K=5.
   - Actualizar los índices documentales y manifiestos de gobernanza.
   - Planificar la ventana de despliegue controlado en Oracle Cloud Infrastructure (OCI).

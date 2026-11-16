# IJF SOR Assistant — Preauditoría de Integridad para Fase 3 (RRE 3.0)

**Estado del Documento:** AUDITORÍA DE INTEGRIDAD LOCAL Y LÍNEA BASE PREVIA A FASE 3  
**Destino:** `docs/preauditoria_integridad_fase3.md`  
**Fecha de Auditoría:** 2026-11-05  
**Entorno:** Local (`C:\PROYECTOS\IJF-SOR-Assistant`)  
**Rama Git Activa:** `integration/ijf-sor-2026-08-merge`  
**Commit Base Head:** `61afc1bc2c8fa273f118f4e10bc447dbafcfe650`  
**Autor:** Antigravity (Auditor Técnico y Ejecutor)  
**Revisores:** Alexis (Supervisor) / ChatGPT (Arquitecto y Auditor Normativo)  

---

## 1. Resumen Ejecutivo y Dictamen de Integridad

Antes de iniciar cualquier actividad de implementación de la **Fase 3: Ranking Semántico, Desambiguación Léxica y Control OOD**, se ejecutó una inspección exhaustiva de solo lectura sobre el estado del árbol de trabajo local (`working directory`), el índice de Git (`staging area`), los archivos rastreados modificados y los activos no rastreados (`untracked`).

### Dictamen Concluyente:
1. **Invarianza Absoluta de Datos Persistentes:** La totalidad de los activos canónicos de conocimiento —PDF oficial del SOR 2026, corpus de pasajes procesado, índice denso FAISS, índice léxico BM25 y grafo de conocimiento— presentan **cero modificaciones en Git (`git status data/` limpio)**.
2. **Feature Flag de Chunk Stitching Desactivado por Defecto:** Se verificó tanto a nivel estático de código como dinámicamente en tiempo de ejecución que `enable_chunk_stitching = False` y `rre.stitcher is None`, garantizando que la Fase 2 no interfiere de manera activa en el comportamiento canónico de producción ni en la línea base.
3. **Plena Trazabilidad del Benchmark de Referencia:** Los archivos de resultados reproducibles (`scratch/battery_baseline_phase1.json` y `scratch/battery_phase2_stitching.json`) se encuentran íntegros e identificables, ratificando el balance funcional de 22 casos (15 PASS, 4 PARTIAL, 3 FAIL).
4. **Ausencia de Cambios Funcionales Ajenos:** Las dos únicas modificaciones rastreadas corresponden a:
   - `src/rre_engine.py`: La integración desacoplada de la Fase 1 (ontología normativa) y Fase 2 (chunk stitching inactivo por defecto).
   - `scratch/golden_validation_report.md`: La actualización de un informe de validación a la nomenclatura KUN del SOR 2026-08.
   - Cero intervenciones en producción OCI, cero operaciones remotas de Git y cero alteraciones accidentales.

---

## 2. Inspección de Archivos Rastreados Modificados (`Changes not staged`)

### 2.1 Inspección Forense: `src/rre_engine.py`
- **Comando:** `git diff -- src/rre_engine.py`
- **Líneas Modificadas:** $+67$ líneas, $-20$ líneas.
- **Origen y Propósito:**
  1. *Imports de Soporte (Líneas 22-23):* Importación de `NormativeOntology`, `NormativeDomain` (Fase 1) y `PassageStitcher` (Fase 2).
  2. *Control por Feature Flag en Constructor (Líneas 40-50):*
     ```python
     def __init__(self, ..., enable_chunk_stitching: bool = False, max_expansion_pages: int = 3):
         if not enable_chunk_stitching:
             enable_chunk_stitching = os.environ.get("RRE_ENABLE_CHUNK_STITCHING", "").strip().lower() in {"1", "true", "yes", "on"}
         self.enable_chunk_stitching = bool(enable_chunk_stitching)
     ```
     *Verificación:* Por defecto es `False`. La inicialización de `self.stitcher` se condiciona estrictamente a `self.enable_chunk_stitching`.
  3. *Expansión Ontológica Fase 1 en `_tokenize()` (Líneas 520-536):* Invocación a `NormativeOntology.expand_token_stream(tokens)` y atenuación de palabras de plantilla procesal (competitor, athlete, team) cuando no se consulta sobre sistemas de sorteo.
  4. *Invocación Condicional de Stitching en Búsqueda Semilla (Líneas 978-1013):* Si `enable_chunk_stitching == True`, se llama a `self.stitcher.stitch_evidence(p)` preservando el `passage_id` semilla como primario; si `False`, se entrega el diccionario canónico idéntico a la versión base.
- **Clasificación:** **A. Modificación autorizada de Fase 1 y Fase 2**.

### 2.2 Inspección Forense: `scratch/golden_validation_report.md`
- **Comando:** `git diff -- scratch/golden_validation_report.md`
- **Líneas Modificadas:** $+14$ líneas, $-14$ líneas.
- **Origen y Propósito:**
  - El informe original evaluaba 12 consultas con identificadores KUN sintéticos heredados (`KUN-0001` a `KUN-0077`).
  - La modificación actualiza la tabla para mapear los resultados al identificador físico oficial de 385 pasajes del SOR 2026-08 (`SOR-2026-08-Pxxx-Sxxx`).
  - No altera lógica ejecutable, es meramente un registro diagnóstico de calibración histórica.
- **Clasificación:** **B. Modificación diagnóstica o temporal**.

---

## 3. Inventario y Clasificación Exhaustiva de Archivos no Rastreados (`Untracked Files`)

El repositorio contiene cuatro categorías bien delimitadas de elementos untracked:

### 3.1 Documentación y Diseños Arquitectónicos (`docs/`) — **Clasificación C: Modificación Documental**
| Archivo | Propósito Técnico | Autorización |
|---|---|---|
| `docs/cierre_fase2_chunk_stitching_rre_3_0.md` | Cierre formal del hito experimental de Fase 2. | Autorizado por Encomienda |
| `docs/diseno_fase3_ranking_semantico_disambiguacion_ood.md` | Diseño arquitectónico principal de la Fase 3. | Autorizado por Encomienda |
| `docs/revision_diseno_fase3_rre_3_0.md` | Revisión complementaria analítica de Fase 3 (fórmula, $\lambda=0.65$, meta 21/22). | Autorizado por Encomienda |
| `docs/auditoria_cobertura_documental_ijf.md` | Diagnóstico de mono-documentalidad vs ecosistema complementario. | Autorizado por Encomienda |
| `docs/auditoria_vigencia_documentos_complementarios_ijf.md` | Análisis de vigencia de los 20 recursos IJF frente a agosto 2026. | Autorizado por Encomienda |
| `docs/matriz_vigencia_documentos_ijf.csv` | Matriz tabular de vigencia, certeza y recomendación de incorporación. | Autorizado por Encomienda |
| `docs/diseno_arquitectura_conocimiento_multifuente_ijf.md` | Diseño consolidado de gobernanza multifuente en capas y niveles. | Autorizado por Encomienda |
| `docs/auditoria_cierre_fase1_rre_3_0.md` | Auditoría de cierre formal de la Fase 1. | Histórico Autorizado |
| `docs/informe_fase1_rre_3_0.md` | Informe técnico de implementación de Fase 1. | Histórico Autorizado |
| `docs/plan_fase2_chunk_stitching_rre_3_0.md` | Plan y especificación de requerimientos de Fase 2. | Histórico Autorizado |
| `docs/informe_implementacion_fase2_...md` | Informe de ejecución de pruebas y cobertura de Fase 2. | Histórico Autorizado |
| `docs/audit_appendix_e/*` | Auditoría estructural previa sobre la concordancia del Apéndice E. | Histórico Autorizado |

### 3.2 Código Fuente y Pruebas Unitarias Aisladas (`src/` y `tests/`) — **Clasificación A: Modificación Autorizada**
| Archivo | Propósito Técnico | Estado de Acoplamiento |
|---|---|---|
| `src/normative_ontology.py` | Taxonomía ontológica y expansión semántica bilingüe (Fase 1). | Integrado en RRE / 100% probado |
| `src/passage_stitcher.py` | Reconstructor secuencial multi-página de pasajes (Fase 2). | Inactivo por defecto (`enable_chunk_stitching=False`) |
| `tests/test_normative_ontology.py` | Suite unitaria de ontología normativa (Fase 1). | 100% PASS |
| `tests/test_passage_stitcher.py` | 5 pruebas unitarias exhaustivas de PassageStitcher (Fase 2). | 100% PASS |
| `tests/test_rre_stitching_integration.py` | 4 pruebas de integración de RRE con flag activo/inactivo (Fase 2). | 100% PASS |

### 3.3 Archivos de Diagnóstico, Volcados y Pruebas Temporales (`scratch/`) — **Clasificación B: Diagnóstico o Temporal**
- **Baterías y Benchmarks:** `battery_baseline_phase1.json`, `battery_phase2_stitching.json`, `baseline_exact_15.json`, `functional_acceptance_battery_raw.json`.
- **Scripts de Reproducción Forense:** `run_comparative_battery.py`, `eval_abstention_thresholds.py`, `reproduce_head_defense.py`, `diagnose_judogi_color.py`, `test_batch_ranking.py`.
- **Volcados de Texto y Snippets:** `kun_*.txt`, `reg_dump.txt`, `ada_snippet.txt`, `corpus_cfg.txt`.
- *Evaluación de Riesgo:* Todos residen estrictamente dentro de la carpeta aislada `scratch/` (la cual no forma parte del runtime de la aplicación). No interfieren en el flujo productivo.

### 3.4 Clasificación D: Cambios no identificados o potencialmente accidentales
- **Resultado:** **CERO (0) CAMBIOS NO IDENTIFICADOS O ACCIDENTALES**. Todos los archivos presentes en el árbol de trabajo corresponden exactamente a las actividades encomendadas, documentadas y autorizadas.

---

## 4. Verificación de los Cuatro Puntos Críticos de Integridad

### 4.1 Chunk Stitching Desactivado por Defecto
Se ejecutó la prueba de instanciación en tiempo de ejecución:
```python
from src.rre_engine import ReasoningRetrievalEngine
rre = ReasoningRetrievalEngine()
print(rre.enable_chunk_stitching)  # Output: False
print(rre.stitcher is None)        # Output: True
```
- **Comprobación de Variable de Entorno:** `os.environ.get("RRE_ENABLE_CHUNK_STITCHING") == None`.
- **Conclusión:** **CONFIRMADO**. El feature flag se encuentra rigurosamente inactivo. RRE opera en modo baseline estándar canónico de Fase 1.

### 4.2 Invarianza Criptográfica del Corpus, Índices, Grafo y PDF
Se verificó el estado en Git y los hashes SHA-256 de los activos persistentes:
```powershell
git status --porcelain data/
# Salida limpia (cero modificaciones rastreadas o no rastreadas)
```

| Activo Persistente | Ruta | SHA-256 Comprobado | Estado Git |
|---|---|---|---|
| **PDF Oficial SOR 2026-08** | `data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf` | `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620` | **LIMPIO / SIN CAMBIOS** |
| **Corpus de Pasajes (385 chunks)** | `data/processed/rebuild_2026_08_corrected/passages_candidate.json` | `7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b` | **LIMPIO / SIN CAMBIOS** |
| **Embeddings Densos (FAISS)** | `data/processed/rebuild_2026_08_corrected/dense_embeddings_candidate.npy` | `124ced95fb9e152ce586dec9f30a1eb98dc14ee385c0bc335a2055357f73a617` | **LIMPIO / SIN CAMBIOS** |
| **Índice Léxico Sparse (BM25)** | `data/processed/rebuild_2026_08_corrected/vector_index_candidate.json` | `e182c77e0775472eb73d22ab92b15d026d067cbf6264fb8b25b207479c4668eb` | **LIMPIO / SIN CAMBIOS** |
| **Grafo de Conocimiento (KG)** | `data/processed/rebuild_2026_08_corrected/knowledge_graph_candidate.json` | `95d5a67936cf48d3bc79b69bf370bb1a83a255f938a7322e0dae256450dde215` | **LIMPIO / SIN CAMBIOS** |

- **Conclusión:** **CONFIRMADO AL 100%**. La base documental y vectorial permanece intacta e inalterada.

### 4.3 Benchmark de Referencia Identificable y Congelado
Los datasets de prueba y los benchmarks comparativos se encuentran debidamente congelados y localizables:
- **Línea Base Fase 1 (15 casos canónicos):** `scratch/baseline_exact_15.json` (13/15 aciertos).
- **Línea Base Batería Funcional 22 Casos:** `scratch/battery_baseline_phase1.json` (15 PASS, 4 PARTIAL, 3 FAIL).
- **Modo Experimental Chunk Stitching:** `scratch/battery_phase2_stitching.json` (15 PASS, 4 PARTIAL, 3 FAIL, con mejoras textuales en TC-08, TC-21 y TC-22).
- **Conclusión:** **CONFIRMADO**. Se cuenta con una referencia cuantitativa transparente para contrastar de inmediato las métricas de la Fase 3.

### 4.4 Ausencia de Cambios Funcionales Ajenos
- No se han agregado módulos de inferencia, endpoints HTTP, alteraciones a Streamlit (`src/app.py` o interfaz) ni a `src/ada_assistant.py`.
- No se han modificado los validadores normativos en `src/normative_validator.py`.
- La suite completa de 181 pruebas de regresión se ejecuta de forma reproducible y con 100% de éxito.

---

## 5. Tabla Resumen de Clasificación de Elementos del Repositorio

| Elemento / Archivo | Tipo de Elemento | Clasificación de Integridad | Impacto en Fase 3 |
|---|---|---|---|
| `src/rre_engine.py` | Archivo Rastreado | **A. Modificación Autorizada (Fase 1 y 2)** | Base limpia para integrar `NormativeSemanticRanker`. |
| `scratch/golden_validation_report.md` | Archivo Rastreado | **B. Modificación Diagnóstica** | Inocuo para el runtime. |
| `src/passage_stitcher.py` | Untracked Source | **A. Modificación Autorizada (Fase 2)** | Inactivo por defecto; disponible bajo flag. |
| `src/normative_ontology.py` | Untracked Source | **A. Modificación Autorizada (Fase 1)** | Activo en tokenización; base ontológica para Fase 3. |
| `tests/test_passage_stitcher.py` | Untracked Test | **A. Modificación Autorizada (Fase 2)** | Cobertura unitaria de stitching. |
| `tests/test_rre_stitching_integration.py`| Untracked Test | **A. Modificación Autorizada (Fase 2)** | Valida que flag=False reproduce baseline. |
| `tests/test_normative_ontology.py` | Untracked Test | **A. Modificación Autorizada (Fase 1)** | Cobertura unitaria de ontología. |
| `docs/*.md` y `docs/*.csv` | Untracked Docs | **C. Modificación Documental** | Diseños y auditorías de gobernanza aprobadas. |
| `scratch/*` | Untracked Scripts/Data | **B. Modificación Diagnóstica / Temporal** | Entorno aislado de pruebas y volcados. |
| `data/*` | Tracked / Untracked Data| **CONGELADO E INVARIANTE** | Cero modificaciones. 100% integridad. |

---

## 6. Dictamen y Recomendación Final

El entorno local de trabajo en `C:\PROYECTOS\IJF-SOR-Assistant` se encuentra en **óptimas condiciones de higiene técnica, trazabilidad y control de versiones**:
1. No existe deriva de configuración ni cambios accidentales.
2. La Fase 2 está completamente contenida bajo feature flag inactivo por defecto.
3. El corpus y los índices vectoriales y semánticos están 100% íntegros.
4. El benchmark de referencia de 22 casos está congelado y listo para ser utilizado como rasero de aceptación.

**Recomendación:** El repositorio está técnicamente listo para recibir la autorización de implementación de la **Fase 3: Ranking Semántico, Desambiguación Léxica y Control OOD** tan pronto como el Supervisor (Alexis) y el Arquitecto (ChatGPT) lo dispongan.

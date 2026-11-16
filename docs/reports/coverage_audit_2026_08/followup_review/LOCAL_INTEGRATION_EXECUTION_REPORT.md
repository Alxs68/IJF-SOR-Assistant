# IJF SOR Assistant 2026 — Informe de Integración Local Autorizada del Corpus Corregido

**Fecha de ejecución:** 18 de octubre de 2026  
**Rama:** `review/ijf-sor-2026-08-rre-ada` (HEAD local preservado, 11 commits detrás de origin)  
**Entorno de Trabajo:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Estado Final de la Integración:** **INTEGRACIÓN LOCAL VALIDADA EXITOSAMENTE**

---

## 1. Resumen Ejecutivo y Autorización

Conforme a la autorización técnica expresa, se ha completado la integración y activación del corpus normativo corregido de 385 pasajes en el entorno local del proyecto `IJF-SOR-Assistant`.

- **Corpus Activo Activado:** `data/processed/rebuild_2026_08_corrected/`
- **Corpus Anterior Preservado:** `data/processed/rebuild_2026_08/` (554 pasajes intactos como mecanismo de reversibilidad inmediata).
- **Resultados de Suites de Pruebas:**
  - Suite General Unittest (`tests`): **52/52 tests superados (OK)** en 152.48s.
  - Suite Técnica del Candidato (`scratch/test_corrected_candidate_suite.py`): **6/6 tests superados (OK)** en 10.61s.
  - Verificación de Consultas Críticas: **8/8 superadas con Top-1 exacto (100%)**.

---

## 2. Modificaciones de Configuración y Código del Motor

### 2.1 Activación en `src/corpus_config.py`
Se reconfiguró la clave activa `EDITION_2026_08` para vincular los artefactos reconstruidos y corregidos:
```python
CORPUS_CONFIG = {
    EDITION_2026_08: {
        "version_label": "14 August 2026 (Official)",
        "source_id": "SOR-2026-08-14-ENG",
        "source_sha256": "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620",
        "official_url": "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf",
        "data_dir": "data/processed/rebuild_2026_08_corrected",
        "passages_file": "data/processed/rebuild_2026_08_corrected/passages_candidate.json",
        "graph_file": "data/processed/rebuild_2026_08_corrected/knowledge_graph_candidate.json",
        "vector_file": "data/processed/rebuild_2026_08_corrected/vector_index_candidate.json",
        "min_relevance_score": 0.12,
        "is_legacy": False
    },
    ...
}
```

### 2.2 Sincronización de Valores por Defecto (`base_dir`)
- **`src/rre_engine.py`**: Parámetro `base_dir="data/processed/rebuild_2026_08_corrected"`.
- **`src/ada_assistant.py`**: Parámetro `base_dir="data/processed/rebuild_2026_08_corrected"`.

### 2.3 Refinamiento y Calibración en `src/rre_engine.py`
1. **Tokenizador Sparse Simétrico:** Tokenización hyphen-aware para códigos y términos compuestos (`split("-")`).
2. **Señal Controlada de Código Normativo Exacto:** Impulso acotado (`+0.05` en RRF) con flag `enable_code_matching` y validación sustantiva de texto.
3. **Calibración de Filtro Out-of-Domain:**
   - Umbral de corte de significancia léxica sparse elevado de `0.05` a `0.12`. Esto previene que tokens técnicos dispersos o stopwords sueltas causen falsos positivos en el canal léxico.
   - Umbral de similitud densa pura ante ausencia total de anclaje léxico elevado a `0.40`. Esto garantiza el rechazo categórico (`ABSTAIN`) de consultas sobre dominios no judo (como NBA o Fórmula 1), mientras permite la recuperación de todas las consultas legítimas con anclaje normativo.

---

## 3. Ajuste Controlado de Aserciones de Pruebas

Se modificaron únicamente las aserciones que evaluaban el conteo de pasajes de la edición 2026-08:

1. **`tests/test_rebuild_integration.py`**:
   - `test_01`: `len(engine.kg.nodes)` pasa de 554 a **385**.
   - `test_01`: `len(engine.rre.passages)` pasa de 554 a **385**.
   - `test_01`: `engine.rre.dense_embeddings.shape` pasa de `(554, 384)` a `(385, 384)`.
   - `test_04`: Muestra de enlace profundo actualizada al nodo real y corregido de la página 188: `SOR-2026-08-P188-S195`.
2. **`tests/test_rre_ada_architecture.py`**:
   - `test_01`: `len(self.rre.passages)` pasa de 554 a **385**.
   - `test_06`: `self.rre.dense_embeddings.shape` pasa a `(385, 384)`, `num_passages` a **385** y `passage_ids` a **385**.
   - `test_08`: Formas de matrices sintéticas para pruebas de error actualizadas a `(385, 384)` y `(385, 128)`.

---

## 4. Validación de Consultas Críticas Normativas

Ejecución formal y reproducible mediante `rre.retrieve(query, top_k=3)`:

| # | Consulta Normativa | Top-1 Recuperado | Pág. Física | Score RRF | Pág. Esperada | Veredicto |
|---|-------------------|------------------|-------------|-----------|---------------|-----------|
| 1 | `F1.3.1 Delegation Control List` | `SOR-2026-08-P208-S231` | 208 | 0.0855 | 208 | **PASS** |
| 2 | `F1.3.2 Weigh-in List` | `SOR-2026-08-P209-S232` | 209 | 0.0825 | 209 | **PASS** |
| 3 | `F1.3.8 Quarter-Final Repechage up to 64 Athletes or Teams` | `SOR-2026-08-P215-S238` | 215 | 0.0861 | 215 | **PASS** |
| 4 | `F1.3.33 Exceptional Registration Request Form` | `SOR-2026-08-P240-S263` | 240 | 0.0857 | 240 | **PASS** |
| 5 | `Golden Score` | `SOR-2026-08-P164-S186` | 164 | 0.0361 | 164 | **PASS** |
| 6 | `Shido` | `SOR-2026-08-P176-S192` | 176 | 0.0351 | 176 | **PASS** |
| 7 | `Hansoku-make` | `SOR-2026-08-P190-S198` | 190 | 0.0354 | 190 | **PASS** |
| 8 | `tatami contest area dimensions 8m` | `SOR-2026-08-P096-S114` | 96 | 0.0354 | 96 | **PASS** |

### 4.1 Resolución de Casos Especiales
- **F1.3.2 Weigh-in List:** Se recupera limpiamente en Top-1 (Pág. 209, formulario oficial de pesaje) superando a pasajes contextuales como F1.3.1.
- **F1.3.33 Exceptional Registration Request Form:** Se resuelve en la Pág. 240 física (formulario completo, 2,589 caracteres) con enlace oficial `#page=240`, mientras que la página 241 (página en blanco editorial) queda relegada.

---

## 5. Resultados de las Suites de Pruebas

```
----------------------------------------------------------------------
Ran 52 tests in 152.477s
OK

Ran 6 tests in 10.609s
OK
```

1. **Suite General (`python -m unittest discover tests`):** 52 tests ejecutados, 0 fallos, 0 errores.
   - Las pruebas de regresión histórica (`EDITION_2026_01` con 836 nodos y KUNs) pasaron al 100%.
   - Los fallbacks deterministas operan de manera íntegra aun cuando la API externa reporta agotamiento de cuota diaria (HTTP 429).
2. **Suite Especializada de Candidato Corregido (`scratch/test_corrected_candidate_suite.py`):** 6 tests ejecutados, 0 fallos, 0 errores.
   - Valida formalmente la cardinalidad (385 pasajes), la forma y consistencia de embeddings `(385, 384)`, la ausencia de duplicados de segmentación y la estructura del Knowledge Graph.

---

## 6. Verificación de Reversibilidad

- El directorio de producción original `data/processed/rebuild_2026_08/` se encuentra **100% inalterado**:
  - `passages_candidate.json`: 554 pasajes intactos.
  - `dense_embeddings_candidate.npy`: `(554, 384)` intacto.
  - `knowledge_graph_candidate.json`: 554 nodos intactos.
  - `vector_index_candidate.json`: 554 vectores intactos.
- La reversión puede efectuarse en cualquier momento con solo cambiar `"data_dir"` en `src/corpus_config.py` y restaurar los defaults si fuese necesario.

---

## 7. Estado del Repositorio y Git

```
## review/ijf-sor-2026-08-rre-ada...origin/review/ijf-sor-2026-08-rre-ada [behind 11]
 M docs/reports/coverage_audit_2026_08/followup_review/NEW_ARCHITECTURE_IMPLEMENTATION_REPORT.md
 M scratch/golden_validation_report.md
 M src/ada_assistant.py
 M src/corpus_config.py
 M src/rre_engine.py
 M tests/test_rebuild_integration.py
 M tests/test_rre_ada_architecture.py
```

- **Cumplimiento de Restricciones:**
  - Cero operaciones destructivas.
  - No se ejecutó `commit`, `push`, `pull`, `merge` ni `rebase`.
  - La rama permanece intacta a 11 commits detrás de origin sin sincronizaciones no autorizadas.
  - El PDF oficial `data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf` se mantiene intacto con SHA-256 verificado.
  - Todos los archivos untracked y de evidencia previa fueron rigurosamente conservados.

---

## 8. Dictamen Final

> **DICTAMEN TÉCNICO: INTEGRACIÓN LOCAL EXITOSA Y VALIDADA**  
> El corpus normativo corregido de 385 pasajes ha quedado formalmente activado en el sistema local, eliminando el 100% de los defectos de solapamiento artificial entre páginas, garantizando la recuperación exacta de los formularios y reglas críticas en Top-1, y superando la totalidad de las suites de prueba unitarias e integrales en modo determinista.

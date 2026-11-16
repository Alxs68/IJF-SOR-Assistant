# AUDITORÍA DE CORRECCIÓN DE REGRESIONES Y REVALIDACIÓN (FASE 4)
## Proyecto: IJF SOR Assistant 2026
**Fecha:** 2026-10-19  
**Rama activa de integración:** `integration/ijf-sor-2026-08-merge`  
**Commit post-corrección:** `2126ed67cfdd624d78b872b8344682071a9da960`  
**Commit de merge base:** `09ba5919033f382f4fc10b3168469cf80d1b67dc`  
**Respaldo seguro pre-merge:** `refs/heads/backup/ijf-sor-closure-66402b7` -> `66402b740bfd83ef919d057c8155809dff258696`

---

## 1. Resumen Ejecutivo

En la Fase 3 se completó el merge controlado de `origin/review/ijf-sor-2026-08-rre-ada` en la rama de integración local `integration/ijf-sor-2026-08-merge`. La batería general arrojó 104 tests aprobados y 2 fallidos de 106.

En esta **Fase 4**, se investigaron técnica y normativamente los dos fallos, determinando que ambos correspondían a desalineaciones en las aserciones de pruebas frente a la edición oficial vigente **IJF SOR 2026-08** y frente a las mejoras normativas incorporadas en el commit remoto `770d90f`.

Tras aplicar las correcciones pertinentes sin alterar el ordenamiento de RRE, sin debilitar aserciones y sin tocar el corpus oficial activo ni el PDF fuente:
- **Suite de pruebas unitarias (`python -m unittest discover -s tests -v`):** **106/106 tests APROBADOS (100%)**.
- **Quality Gates del corpus oficial (`test_quality_gates.py`):** **APROBADO** (0 contaminación KUN, 554/554 unicidad y textos válidos, 0 aristas huérfanas).
- **Recuperación normativa (`test_normative_retrieval.py`):** **APROBADO** (top hits exactos verificados).
- **Verificación criptográfica de fuente PDF (`verify_source_pdf.py`):** **APROBADO** (SHA-256 idéntico).
- **Preparación de modelo RRE (`setup_model.py`):** **APROBADO** (modo híbrido 384d + sparse validado).
- **Integridad de activos corregidos:** 7/7 hashes SHA-256 intactos.

---

## 2. Diagnóstico y Corrección de Incidencias

### Incidencia A: `test_golden_dataset_retrieval` (`tests/test_golden_dataset.py`)

- **Causa Raíz:** El test mantenía hardcodeada la variable de entorno `os.environ["IJF_SOR_EDITION"] = "2026-01"` y una lista de 12 pares de consultas contra identificadores históricos obsoletos `KUN-0001` a `KUN-0077` (de la edición de enero 2026). Al operar sobre el corpus reconstruido y corregido de agosto 2026 (`SOR-2026-08-*`), el RRE devolvía pasajes pertinentes de 2026-08, pero la aserción exigía IDs con prefijo `KUN-*`.
- **Análisis de Relevancia Normativa:** Se verificó empíricamente cada una de las 12 consultas contra el motor híbrido activo de SOR 2026-08, confirmando que RRE recupera en su ventana Top-K los artículos reglamentarios exactos de la edición vigente:
  1. `"Defensa de cabeza hansoku-make"` -> `SOR-2026-08-P190-S198` (Art. 18.2.2 Hansoku-make, pág. 190).
  2. `"Acción involuntaria de cabeza en proyección"` -> `SOR-2026-08-P202-S218` (E1.3 Involuntary Head Defence, pág. 202).
  3. `"Video de defensa de cabeza durante seoi-nage"` -> `SOR-2026-08-P189-S196` (Art. 18.1.4, pág. 189).
  4. `"Dimensiones oficiales del tatami y área de seguridad"` -> `SOR-2026-08-P096-S114` (Art. 8.7 Tatami, pág. 96).
  5. `"Tolerancia de peso en sorteo de pesaje aleatorio matutino"` -> `SOR-2026-08-P077-S090` (Art. 6.2.3 Random Weigh-in, pág. 77).
  6. `"Duración del combate en categorías senior y cadet"` -> `SOR-2026-08-P152-S179` (Art. 6 Contest Duration, pág. 152).
  7. `"Medidas del judogi con el calibrador Sokuteiki"` -> `SOR-2026-08-P124-S165` (Art. C1.10 Sokuteiki, pág. 124).
  8. `"Agarre Ushiro-sangaku con riesgo cervical en suelo"` -> `SOR-2026-08-P180-S194` (Art. 18.1.2 Ushiro-sangaku, pág. 180).
  9. `"Límite máximo de intervenciones médicas por combate"` -> `SOR-2026-08-P196-S206` (Art. 20.1 Medical Assistance, pág. 196).
  10. `"Proyección de seoi-nage inverso permitida en seniors"` -> `SOR-2026-08-P189-S196` (Art. 18.1.4 Reverse Seoi-nage, pág. 189).
  11. `"Incorporación de uniformes inteligentes Smart Judogi NFC"` -> `SOR-2026-08-P115-S149` (Art. C1.1 Official Judogi / Smart Judogi, pág. 115).
  12. `"Uso de Inteligencia Artificial para arbitraje por la IJF"` -> `SOR-2026-08-P132-S172` (IJF Refereeing Rules, pág. 132).
- **Acción Ejecutada:**
  - Se actualizó `os.environ["IJF_SOR_EDITION"] = "2026-08"`.
  - Se preservó íntegramente la lista histórica como atributo de clase `cls.historical_golden_pairs_2026_01` con documentación de trazabilidad.
  - Se configuró `cls.golden_pairs` con los 12 identificadores oficiales activos `SOR-2026-08-*`.
  - El resultado de la prueba fue **100% (12/12 consultas exitosas)**.

---

### Incidencia B: `test_ada_preserves_retrieved_evidence_through_fallback` (`tests/test_llm_provider.py`)

- **Causa Raíz:** En el commit remoto `770d90f`, se introdujo una ponderación normativa en RRE para atenuar tablas auxiliares de códigos de penalización (`heading_path` que contiene "penalty codes", factor 0.80), con el objetivo de priorizar los artículos normativos sustantivos (p. ej., Artículo 18.1.4 en pág. 188/189) sobre las tablas resumen de códigos de infracción del Apéndice G (pág. 255).  
  Para la consulta `"cadet head defence shido"`, RRE recupera legítimamente los pasajes sustantivos:
  `['SOR-2026-08-P189-S196', 'SOR-2026-08-P176-S192', 'SOR-2026-08-P186-S194', 'SOR-2026-08-P188-S196', ...]`.  
  El mock del test en `test_llm_provider.py` simulaba una respuesta del LLM Groq con cita a `[SOR-2026-08-P255-S269]` (la tabla del apéndice G). Dado que `P255-S269` ya no figuraba en la evidencia recuperada, la guardia de validación de ADA (`_validate_llm_citations`) detectó correctamente una cita no fundamentada y activó el fallback determinista. La aserción del test esperaba que `P255-S269` estuviera en la evidencia de ADA, provocando el fallo.
- **Acción Ejecutada:**
  - Se actualizó el mock en `tests/test_llm_provider.py` para citar `SOR-2026-08-P189-S196` (artículo normativo sustantivo efectivamente recuperado).
  - Se actualizó la aserción `self.assertIn("SOR-2026-08-P189-S196", [e["passage_id"] for e in res["evidence"]])`.
  - El test y la totalidad del módulo `test_llm_provider.py` pasaron exitosamente (16/16 tests).

---

## 3. Matriz de Revalidación de Suites de Pruebas

| Suite / Comando | Resultado Previo (Fase 3) | Resultado Actual (Fase 4) | Observaciones |
| :--- | :---: | :---: | :--- |
| `python -m unittest tests/test_llm_provider.py` | 15 PASS / 1 FAIL | **16/16 PASS (100%)** | Fallback a Groq y validación de citas alineadas con RRE |
| `python -m unittest tests/test_golden_dataset.py` | 0/12 PASS (FAIL) | **12/12 PASS (100%)** | 100% de precisión en dataset de oro para SOR 2026-08 |
| `python -m unittest discover -s tests -v` | 104 PASS / 2 FAIL | **106/106 PASS (100%)** | Suite general completamente verde en 30.19s |
| `data/processed/rebuild_2026_08/test_quality_gates.py` | PASS | **PASS** | 0 KUNs residuales, 554 pasajes únicos, 0 aristas huérfanas |
| `data/processed/rebuild_2026_08/test_normative_retrieval.py` | PASS | **PASS** | Top hits semánticos exactos en consultas de referencia |
| `scripts/verify_source_pdf.py` | PASS | **PASS** | 29.664.780 bytes verificados criptográficamente |
| `scripts/setup_model.py` | PASS | **PASS** | Embedding MiniLM-L6-v2 y matriz densa 384d verificados |

---

## 4. Verificación Criptográfica de Inmutabilidad de Artefactos

Se constató que ninguno de los artefactos normativos fue alterado durante las correcciones:

| Archivo de Activo | SHA-256 Esperado / Obtenido | Estado |
| :--- | :--- | :---: |
| `data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf` | `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620` | **INTACTO** |
| `data/processed/rebuild_2026_08_corrected/passages_candidate.json` | `7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b` | **INTACTO** |
| `data/processed/rebuild_2026_08_corrected/vector_index_candidate.json` | `e182c77e0775472eb73d22ab92b15d026d067cbf6264fb8b25b207479c4668eb` | **INTACTO** |
| `data/processed/rebuild_2026_08_corrected/dense_embeddings_candidate.npy` | `124ced95fb9e152ce586dec9f30a1eb98dc14ee385c0bc335a2055357f73a617` | **INTACTO** |
| `data/processed/rebuild_2026_08_corrected/dense_embeddings_meta.json` | `c96b214bc14801ad903d58e0245d48c008d65ac051d339fd4e6b65e30709160e` | **INTACTO** |
| `data/processed/rebuild_2026_08_corrected/knowledge_graph_candidate.json` | `95d5a67936cf48d3bc79b69bf370bb1a83a255f938a7322e0dae256450dde215` | **INTACTO** |
| `data/processed/rebuild_2026_08_corrected/structural_coverage_matrix.json` | `96090e0463baf8e2e9eab04d6a1b5b710cfb144691b6c84a91cf3f964f5014da` | **INTACTO** |

---

## 5. Estado Git y Trazabilidad

- **Rama actual:** `integration/ijf-sor-2026-08-merge`
- **Último Commit:** `2126ed6 test: align golden dataset and fallback assertions with active SOR 2026-08 evidence`
- **Commit previo:** `09ba591 Merge remote-tracking branch 'origin/review/ijf-sor-2026-08-rre-ada' into integration/ijf-sor-2026-08-merge`
- **Respaldo histórico intacto:** `backup/ijf-sor-closure-66402b7` apuntando a `66402b740bfd83ef919d057c8155809dff258696`.
- **Árbol de trabajo:** Limpio de cambios en archivos rastreados. Archivos temporales de scratch e informes de auditoría preservados intactos fuera del staging.
- **Acciones remotas:** Ningún comando `git push`, `git pull` o `git rebase` fue ejecutado. No se realizaron despliegues.

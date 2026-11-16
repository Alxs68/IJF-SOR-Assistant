# Orden Técnica de Ejecución — Fase 4.2.5 (Borrador Propuesto)
**Proyecto:** IJF SOR Assistant  
**Fase:** 4.2.5 — Calibración y Endurecimiento del Retrieval Multifuente  
**Supervisor:** Alexis Oliveros Lozano  
**Arquitectura y Auditoría:** ChatGPT  
**Ejecutor Técnico:** Antigravity  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Branch:** `integration/ijf-sor-2026-08-merge`  
**Estado:** **PROPUESTA TÉCNICA — PENDIENTE DE AUTORIZACIÓN EXPRESA DE ALEXIS**

---

## 1. Mandato y Alcance Autorizado (Sujeto a Firma)

Una vez que el supervisor **Alexis Oliveros** apruebe formalmente el inicio de esta fase, se autorizará a Antigravity a ejecutar las siguientes tareas técnicas delimitadas:

1. **Implementación del Normalizador de Puntuación y Umbral Dinámico:**
   - Modificar de manera controlada `src/multisource_retriever.py` para calcular el score normalizado relativo a la suma de IDF de los términos sustantivos de la consulta.
   - Incorporar el filtro de coincidencia mínima de términos sustantivos ($\ge 50\%$ de overlap en consultas multi-término) para suprimir matches espurios por una sola palabra aislada.
2. **Endurecimiento de Abstención en Sidecar:**
   - Implementar la emisión del estado `status: "ABSTAIN"` en el Sidecar cuando el candidato Top-1 no supere el umbral normalizado o cuando se detecte ambigüedad por margen insuficiente ($\text{Score}_{\text{Top1}} - \text{Score}_{\text{Top2}} < \epsilon$).
3. **Ejecución del Benchmark Ampliado de 40 Consultas:**
   - Crear el script ejecutable `scratch/run_fase4_2_5_benchmark.py` con los 40 casos formalizados en `docs/benchmark_fase4_2_5_multifuente_ijf.md`.
4. **Actualización de Suites de Pruebas:**
   - Crear `tests/test_multisource_calibration.py` para verificar los filtros de endurecimiento, la supresión de falsos positivos y la invarianza del SOR 2026.
   - Ejecutar la suite global de regresión (`tests/`).
5. **Generación de Reportes Técnicos:**
   - Generar `docs/informe_implementacion_fase4_2_5_ijf.md` y someterlo a auditoría externa de ChatGPT.

---

## 2. Restricciones y Prohibiciones Invariables

Durante la ejecución de la Fase 4.2.5 queda terminantemente prohibido:
- Modificar el PDF oficial del SOR 2026 (`data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf`).
- Modificar o regenerar `passages_candidate.json`, `vector_index_candidate.json`, `dense_embeddings_meta.json` o `knowledge_graph_candidate.json`.
- Modificar los fragmentos procesados del Sidecar en `data/corpus_multisource/processed/multisource_passages.json`.
- Exponer evidencias o respuestas del Sidecar en la interfaz visible de ADA.
- Habilitar el feature flag `enable_shadow_mode_multisource` como `True` por defecto en el constructor de `ReasoningRetrievalEngine`.
- Realizar despliegues en OCI o comandos remotos de Git (`git push`, `git merge`).

---

## 3. Entregables Comprometidos al Cierre de la Fase

1. Código fuente de calibración en `src/multisource_retriever.py`.
2. Nueva suite de pruebas automatizadas `tests/test_multisource_calibration.py`.
3. Script reproducible de benchmark `scratch/run_fase4_2_5_benchmark.py`.
4. Resultados detallados del benchmark ampliado de 40 consultas (con desglose PASS/PARTIAL/FAIL).
5. Certificado criptográfico de hashes de los artefactos primarios del SOR.
6. Informe técnico de implementación autocontenido.

# Registro de Ejecución y Salidas de Pruebas — Auditoría Apéndice E

**Entorno de ejecución:** Windows 11 / PowerShell 7 (pwsh) / Python 3.12.10 (64-bit)  
**Fecha:** 2026-10-17  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Rama:** `review/ijf-sor-2026-08-rre-ada`  

---

## 1. Suite Completa de Regresión del Proyecto (pytest)

- **Comando:** `python -m pytest -v`
- **Fecha y Hora:** 2026-10-17 16:53:28 UTC-5
- **Código de salida:** `0` (Exitoso)
- **Duración:** 60.68 segundos
- **Resumen:** **52 pruebas recolectadas, 52 pruebas aprobadas (100% OK), 0 fallos, 1 warning (deprecation utcnow en reference_checker)**

### Detalle de módulos verificados:
- `tests/test_citations.py` (10 tests): Formato, deep links, consistencia de URLs con anclajes `#page=X`.
- `tests/test_golden_dataset.py` (1 test): Recuperación sobre dataset de evaluación dorada.
- `tests/test_graph_manager.py` (3 tests): Serialización, métricas y relaciones del grafo de conocimiento.
- `tests/test_rag_engine.py` (3 tests): Flujo de consulta y recuperación contextual.
- `tests/test_rebuild_integration.py` (5 tests): Inicialización de edición 2026-08, enlace criptográfico, consultas normativas, abstención estricta fuera de dominio.
- `tests/test_reference_checker.py` (4 tests): Control de integridad de URLs y detección de recursos multimedia.
- `tests/test_reference_manager.py` (7 tests): Resolución de fallbacks y compatibilidad de referencias.
- `tests/test_rre_ada_architecture.py` (12 tests):
  - `test_01_rre_dual_channel_and_rrf_retrieval`: PASSED
  - `test_02_rre_graph_guided_expansion`: PASSED
  - `test_03_rre_strict_domain_abstention`: PASSED
  - `test_04_ada_arbitration_situation_analysis`: PASSED
  - `test_05_ada_abstention_handling`: PASSED
  - `test_06_dense_matrix_alignment_and_integrity`: PASSED
  - `test_07_rag_engine_separation_for_2026_08`: PASSED
  - `test_08_rre_rejects_corrupted_or_non_finite_matrix`: PASSED
  - `test_09_rre_rejects_mismatched_passage_ids_order`: PASSED
  - `test_10_rre_rejects_incompatible_metadata_hash_and_model`: PASSED
  - `test_11_rre_explicit_operating_mode_hybrid_vs_degraded`: PASSED
  - `test_12_rre_bilingual_and_edge_cases`: PASSED
- `tests/test_technical_followup_review.py` (4 tests): Reconciliación de tablas complejas, categorías de peso y WRL.
- `tests/test_vector_store.py` (3 tests): Indexación, persistencia y tokenización.

---

## 2. Batería de Control de Calidad del Corpus Reconstruido

- **Comando:** `python data/processed/rebuild_2026_08/test_quality_gates.py`
- **Fecha y Hora:** 2026-10-17 16:54:54 UTC-5
- **Código de salida:** `0` (Exitoso)
- **Salida estándar:**
```text
1. Prueba de Cero Contaminación (KUN heredados): 0 hallazgos. (Esperado: 0)
2. Prueba de Unicidad de IDs: 554/554 únicos.
3. Cobertura de páginas físicas con texto normativo: 284 páginas.
4. Prueba de Integridad de SHA-256 de texto: 0 errores. (Esperado: 0)
5. Integridad Referencial del Grafo: 112 aristas, 0 aristas huérfanas.
=== BATERÍA DE PRUEBAS DE CALIDAD SUPERADA CON ÉXITO ===
```

---

## 3. Control de Recuperación Léxica y Vinculación Normativa

- **Comando:** `python data/processed/rebuild_2026_08/test_normative_retrieval.py`
- **Fecha y Hora:** 2026-10-17 16:55:01 UTC-5
- **Código de salida:** `0` (Exitoso)
- **Salida estándar:**
```text
1. Vinculación del Índice con SHA-256 de la fuente: True

2. Evaluación de Consultas Normativas:
Query: 'cadet head defence shido'
   -> Top Hit: SOR-2026-08-P254-S269 (Score: 0.2328)
   -> Artículo: G1.3 | Pág: 254 | Heading: G1.3 Penalty Codes
Query: 'tatami contest area dimensions 8m 10m'
   -> Top Hit: SOR-2026-08-P151-S178 (Score: 0.1950)
   -> Artículo: Article 5 | Pág: 151 | Heading: Article 5 Location (Valid Areas)
Query: 'osaekomi time 20 seconds ippon 10 seconds waza-ari'
   -> Top Hit: SOR-2026-08-P152-S180 (Score: 0.3860)
   -> Artículo: Article 7 | Pág: 152 | Heading: Article 7 Osaekomi Time
Query: 'sokuteiki judogi control measurement'
   -> Top Hit: SOR-2026-08-P114-S148 (Score: 0.2956)
   -> Artículo: GENERAL | Pág: 114 | Heading: IJF JUDOGI RULES
Query: 'medical intervention unconsciousness concussion doctor'
   -> Top Hit: SOR-2026-08-P294-S272 (Score: 0.2822)
   -> Artículo: H1.1 | Pág: 294 | Heading: H1.1 Document Version History

=== AUDITORÍA D: ÍNDICE Y RECUPERACIÓN NORMATIVA EXITOSA ===
```

---

## 4. Pruebas Específicas de Recuperación y ADA para el Apéndice E (Páginas 208–240)

- **Comando:** `python scratch/test_appendix_e_retrieval.py`
- **Fecha y Hora:** 2026-10-17 16:52:28 UTC-5
- **Código de salida:** `0` (Exitoso)
- **Modo operativo validado:** `HYBRID` (Embeddings densos 384d MiniLM + BM25 léxico + Grafo)
- **Hash de la fuente verificado:** `source_sha256_verified = True`

### Resultados por Consulta:

1. **Consulta:** *"Where is the Article 18 Direct Hansoku-make Form and what signatures are required?"*
   - **Top evidencias recuperadas:**
     - `SOR-2026-08-P190-S198` (Art. 18.2.2, Pág. 190)
     - `SOR-2026-08-P190-S197` (Art. 18.2.1, Pág. 190)
     - `SOR-2026-08-P237-S260` (Art. F1.3.30, Pág. 237 — *Article 18 Direct Hansoku-make Form*)
   - **Resultado:** ADA identifica el formulario oficial en la pág. 237 y las firmas requeridas (Árbitro, Supervisor IJF, Director Deportivo IJF, Miembro responsable del equipo de TI).

2. **Consulta:** *"What are the conditions for using the Exceptional Registration Request Form?"*
   - **Top evidencias recuperadas:**
     - `SOR-2026-08-P240-S262` (Pág. 240)
     - `SOR-2026-08-P240-S263` (Art. F1.3.33, Pág. 240 — *Exceptional Registration Request Form*)
   - **Resultado:** ADA sintetiza las 5 condiciones normativas (imposibilidad técnica, diligenciamiento electrónico obligatorio, envío previo a la fecha límite a `registration@ijf.org`, no garantía automática y pago antes de acreditación).

3. **Consulta:** *"Coach suspension form procedure and referee responsibility"*
   - **Top evidencias recuperadas:**
     - `SOR-2026-08-P236-S258` (Pág. 236)
     - `SOR-2026-08-P236-S259` (Art. F1.3.29, Pág. 236 — *Coach Suspension Form*)
   - **Resultado:** ADA recupera las obligaciones inmediatas del árbitro (llenar y firmar, llevar al supervisor del tatami, entregar al responsable de la competición y archivo por la secretaría de la Comisión de Arbitraje).

4. **Consulta:** *"What form is used for coaches request to review action on video in judogi control?"*
   - **Top evidencias recuperadas:**
     - `SOR-2026-08-P090-S105` (Art. 7.2, Pág. 90)
     - `SOR-2026-08-P090-S106` (Art. 7.3, Pág. 90)
     - `SOR-2026-08-P238-S261` (Art. F1.3.31, Pág. 238 — *Coaches Request to Review Action*)
   - **Resultado:** ADA identifica el formulario F1.3.31 en la pág. 238 para entrega en la mesa de control de judogi.

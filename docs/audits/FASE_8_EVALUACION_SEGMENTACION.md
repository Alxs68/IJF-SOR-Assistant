# FASE 8 — Evaluación y segmentación normativa (Etapas 0 y 1)

Fecha: 2026-11-15 · Alcance: benchmark versionado + línea base (Etapa 0) y capa derivada de segmentación (Etapa 1).
Restricciones respetadas: sin cambios en recuperación, ADA, RRE, EvidenceBundle, embeddings, corpus, IDs, grafo, `.env` ni configuración; sin commit, push ni despliegue OCI.

## 1. Resumen ejecutivo

- **Etapa 1 — ACEPTADA.** Se generó `data/derived/article_units_v1/` con 851 unidades derivadas (710 de nivel 1 y 141 cláusulas). El 100 % del texto original queda cubierto y se puede reconstruir byte a byte. Los 385 pasajes originales son trazables, la validación da 0 errores y los avisos se registran sin autocorrección. La reconstrucción es reproducible (`--check` → REPRODUCIBLE).
- **Etapa 0 — benchmark CONSTRUIDO y línea base EJECUTADA (Windows, sin LLM, dense_model=OK, corpus_unchanged=True).** `benchmark_v1` tiene 150 consultas: 60 ordinarias ES, 30 ordinarias EN, 30 de excepción/condición/referencia, 15 fuera de dominio y 15 ambiguas. Las 139 anclas se verificaron literalmente contra el corpus. La partición dev/validación/test es disjunta por grupo semántico.
  - Línea base global (120 respondibles): Recall@5 0,49 · Recall@10 0,56 · MRR 0,40 · P@1 0,32 · precisión del bundle 0,09 · completitud 0,50 · recall de excepciones 0,64 · recall de referencias cruzadas 0,20 · falsos positivos OOD 6/15.
  - Estas cifras están muy por debajo de la batería de 18 consultas de la Fase 6 (R@5 1,00). Detalle en §4.
- **Ampliación SHADOW (§15) — ACEPTADA.** 18 unidades auxiliares en `data/derived/shadow_units_v1/`, separadas del corpus SOR, con trazabilidad completa y ninguna autoridad normativa. Hay además un benchmark auxiliar de 24 casos (`benchmark_shadow_v1`) y una evaluación de separación de autoridad.
- **Revisión humana: ninguna.** Ningún ítem está certificado por árbitros (`PENDIENTE_REVISION_ARBITRAL` en los 150).
- Integridad: el SHA-256 de `passages_candidate.json` es idéntico antes y después (`7d46342889…1167b`). No se modificó ningún archivo de `src/`, `app.py` ni la configuración durante la fase.

## 2. Benchmark y cobertura

Archivos: `scripts/build_benchmark_v1.py` (constructor y verificador), `data/eval/benchmark_v1/{benchmark_v1.jsonl, splits/dev|validation|test.jsonl, manifest.json, hashes.json}`.

| Categoría | n | Idioma |
|---|---|---|
| ORDINARIA_ES | 60 | es |
| ORDINARIA_EN | 30 | en (15 equivalentes de consultas ES con el mismo grupo semántico, 15 propias) |
| EXCEPCION_CONDICION_REFERENCIA | 30 | 16 es / 14 en |
| FUERA_DE_DOMINIO | 15 | 9 es / 6 en; 5 son de deportes de combate cercanos (lucha, taekwondo, sumo, karate, BJJ) |
| AMBIGUA | 15 | 10 es / 5 en |

Cada ítem incluye: ID estable `B1-…`, texto, idioma, categoría, dificultad, artículos esperados, pasajes originales pertinentes (IDs y fragmento literal), evidencia mínima, referencias cruzadas obligatorias, excepciones que deben conservarse, si es respondible, justificación, estado de anotación, estado de revisión humana, grupo semántico y split.

Cobertura del corpus: las consultas respondibles cubren las secciones 1–8, los anexos A, B, C y E y los Articles 1, 5, 7, 8 y 11–20 de las reglas de arbitraje. No cubren los formularios F1.3.x, el glosario G1.x ni el historial H1.1, que no tienen reglas que consultar.

Partición estratificada por categoría y por grupo semántico, con orden sha256(versión+grupo): dev 78 / validación 30 / test 42.
- Los pares ES/EN y los ítems que comparten un ancla idéntica se fusionan automáticamente en un mismo grupo (132 grupos y 16 grupos bilingües), así que nunca quedan repartidos entre splits.
- El control de casi-duplicados por Jaccard ≥ 0,8 entre splits no encontró ninguno.
- **El test es reservado: no debe usarse para ajustar reglas, umbrales, prompts ni anclas.**

## 3. Estado de las anotaciones humanas

| Estado de anotación | n |
|---|---|
| VERIFICADA_TEXTUALMENTE (fragmento literal localizado y artículo presente en los metadatos de la página) | 112 |
| VERIFICADA_TEXTUALMENTE_CON_ARTICULO_PENDIENTE (fragmento localizado, pero la página no tiene ese article_id en metadatos: texto de continuación) | 8 |
| VERIFICADA_SIN_EVIDENCIA_ESPERADA (OOD) | 15 |
| PENDIENTE (ambiguas: artículos esperados sin determinar; candidatas no verificadas) | 15 |

- Origen de todas las anotaciones: `ASISTIDA_IA_ANCLADA_A_TEXTO_LITERAL`.
- **Revisión arbitral: 0/150.** La verificación automática solo demuestra que el fragmento existe literalmente en la página. No demuestra que sea la evidencia normativa correcta ni suficiente. Antes de usar el benchmark para decisiones de producción hace falta revisión arbitral, como mínimo de las 30 consultas de excepción y de las 8 con artículo pendiente.
- No se incluyen respuestas normativas, solo localizadores de evidencia.

## 4. Métricas de línea base

Ejecución: Windows, `python scripts/eval_benchmark_v1_baseline.py`, sin LLM. Resultado: `dense_model=OK`, `corpus_unchanged=True`, n=150. El detalle por consulta está en `data/eval/benchmark_v1/baseline/baseline_results.json`.
- Ranking: `retrieve` top-10 sin grafo.
- Bundle: `analyze_situation` top-5, con evidencia y grafo.
- La latencia es la media de `analyze_situation` por consulta.

| Grupo | n | R@5 | R@10 | MRR | P@1 | Prec. bundle | Compl. bundle | Exc. | XRef | OOD-FP | Lat. ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **global** | 120 | 0,49 | 0,56 | 0,40 | 0,32 | 0,09 | 0,50 | 0,64 | 0,20 | 0,40 | 43,5 |
| ORDINARIA_ES | 60 | 0,38 | 0,45 | 0,30 | 0,23 | 0,07 | 0,38 | – | – | – | 35,6 |
| ORDINARIA_EN | 30 | 0,57 | 0,67 | 0,51 | 0,43 | 0,10 | 0,57 | – | – | – | 47,4 |
| EXCEPCION_CONDICION_REFERENCIA | 30 | 0,63 | 0,67 | 0,49 | 0,37 | 0,12 | 0,67 | 0,64 | 0,20 | – | 57,0 |
| FUERA_DE_DOMINIO | 15 | – | – | – | – | – | – | – | – | 0,40 | 39,3 |
| AMBIGUA | 15 | – | – | – | – | – | – | – | – | – | 44,7 |
| idioma es | 77 | 0,43 | 0,48 | 0,35 | 0,29 | 0,08 | 0,43 | 0,62 | 0,25 | 0,22 | 40,8 |
| idioma en | 43 | 0,60 | 0,70 | 0,49 | 0,37 | 0,11 | 0,63 | 0,67 | 0,00 | 0,67 | 48,2 |
| split dev | 62 | 0,40 | 0,47 | 0,34 | 0,27 | 0,07 | 0,40 | 0,62 | 0,50 | 0,25 | 46,2 |
| split validación | 24 | 0,58 | 0,67 | 0,42 | 0,29 | 0,10 | 0,58 | 1,00 | – | 0,67 | 41,6 |
| split test (reservado) | 34 | 0,59 | 0,65 | 0,48 | 0,41 | 0,11 | 0,62 | 0,60 | 0,00 | 0,50 | 39,8 |

Hallazgos (localizadores de pasaje; no miden calidad normativa):
1. **Brecha de idioma**: ES ordinarias R@5 0,38 frente a EN 0,57. Con los mismos grupos semánticos, la proyección por diccionario (camino sin LLM) pierde recuperación.
2. **7 respondibles rechazadas como OOD**: B1-EN-003, B1-ES-007, -008, -026, -027, -039 y -042. Son consultas legítimas de organización (pasaporte, cancelaciones, acreditación, sede, medallas) que el filtro OOD rechaza.
3. **54/120 sin acierto en top-10.** El fallo se concentra en las secciones 1–8 y los anexos A, B y C, fuera de las reglas de arbitraje que cubren las reglas manuales.
4. **Precisión del bundle 0,09**: el bundle entrega muchos pasajes (cosido de páginas y grafo) y pocos pertinentes. La completitud es 0,50.
5. **Referencias cruzadas 0,20** (5 ítems) y **excepciones 0,64** (14 ítems): la evidencia condicionante se pierde a menudo.
6. **6/15 falsos positivos OOD**: B1-OOD-008 a 012 (lucha, taekwondo, sumo, karate, BJJ) y 014 (peso del equipaje). Las 9 OOD lejanas se rechazan correctamente.
7. **Ambiguas: 12/15 reciben bundle** sin que se pida aclaración (no es un objetivo del motor actual; se informa).
8. **Contraste con la Fase 6**: la batería de 18 consultas (R@5 1,00) procedía de casos ya cubiertos por reglas manuales. El benchmark amplio indica que esas cifras **no se generalizan**.
9. Diferencias entre splits (dev 0,40 frente a test 0,59): con n pequeños, reflejan la composición de cada split, no un sobreajuste. El test sigue reservado.

## 5. Diseño de la segmentación

Archivo: `scripts/build_article_units.py` (solo biblioteca estándar, procesador `sor_article_unit_segmenter` 1.0.0).

- **Unidad = corte literal**: `derived_text == texto_página[char_start:char_end]`. No se normaliza, traduce ni resume nada. `normative_status = DERIVADA_NO_NORMATIVA`.
- **Nivel 1** (partición exacta de cada página): `PAGE_HEADER`, `ARTICLE` (empieza en un encabezado), `CONTINUATION` (texto previo al primer encabezado, atribuido al último artículo de la página anterior), `COVER` (portadas de sección) y `EMPTY_PAGE`.
- **Nivel 2** (partición exacta de un segmento): `INTRO` (encabezado y entradilla), `NUMBERED` («N.») y `LETTERED` («x)»), con el primer tipo encontrado como nivel superior. **Solo se divide si la secuencia es consecutiva**. Si no lo es, el segmento queda `NO_SEGMENTADA` con el motivo `NUMERACION_IRREGULAR`.
- **Encabezados**: se acepta una línea con rótulo si coincide con el article_id o el heading de un pasaje de esa página. Una línea «Article N»/«X1.N» ausente de los metadatos se acepta solo si el título empieza en mayúscula y la página está entre las de sus rótulos vecinos en orden documental. En ese caso queda como ADVERTENCIA y **los metadatos no se corrigen**. Las menciones a rótulos de otras páginas se rechazan y se registran.
- **Excepciones**: una cláusula que empieza con un conector de excepción (Although, However, Except, Unless, …) se une a la anterior. Las viñetas no se dividen. Los marcadores de excepción se registran por unidad.
- **Referencias cruzadas**: Article/punto, apartado de anexo, tabla, sección y figura, con desplazamiento. Se resuelven a unidades (y a la cláusula, si hay «point N»). Las figuras se marcan `NO_APLICA_FIGURA`.
- **Sin división por longitud.** El grafo y los IDs originales no se tocan: las unidades referencian `original_passage_ids` y `page_passage_ids`.
- No sobrescribe por defecto (código de salida 2); `--overwrite` es explícito y `--check` verifica la reproducibilidad.

Campos de cada unidad: `unit_id, unit_level, unit_type, parent_unit_id, child_unit_ids, page, article_label, heading, clause_label, char_start, char_end, derived_text, source_text_sha256, derived_text_sha256, original_passage_ids, page_passage_ids, passage_relation, segmentation_method, validation_status, non_segmentation_reason, clause_structure, exception_markers, merged_exception_clauses, list_item_count, cross_refs, normative_status, relation_to_official`.

## 6. Estadísticas de unidades

| Métrica | Valor |
|---|---|
| Páginas / pasajes originales / textos distintos | 287 / 385 / 287 |
| Unidades totales (nivel 1 / nivel 2 / hojas) | 851 (710 / 141 / 815) |
| Por tipo | ARTICLE 258 · CONTINUATION 171 · COVER 16 · PAGE_HEADER 264 · EMPTY_PAGE 1 · INTRO 29 · NUMBERED 77 · LETTERED 35 |
| Segmentos con cláusulas | 36 |
| NO_SEGMENTADA | 10 (P131 vacía; P161, P164, P167, P180, P182, P231×2, P289, P292 con numeración irregular) |
| Fusiones por excepción | 2 (Article 8 cl. 2 → 1; Article 18.1.1 cl. 3 → 2) |
| Longitud de las hojas (caracteres) | mínimo 0 · media 597,9 · máximo 3 900 |
| Relación de las unidades de nivel 1 con los pasajes | ARTICLE_METADATA 379 · PAGE (cabeceras) 265 · PAGE_FALLBACK 66 |

## 7. Cobertura textual

Hay 487 328 caracteres originales y 487 328 cubiertos en el nivel 1 (ratio 1,0). En las 287 páginas, la concatenación del nivel 1 es igual al texto original, y la de los hijos es igual al texto del segmento padre. No hay huecos, solapamientos ni duplicación accidental. No hay pérdida textual.

## 8. Trazabilidad

- `traceability_map.json` contiene pasaje → unidades (con relación), unidad → pasajes y página → unidades. Los 385 pasajes están mapeados. Ninguna unidad carece de pasaje, y todos los IDs referenciados existen y pertenecen a la página de la unidad.
- Con `PAGE_FALLBACK` (66 segmentos) el artículo del texto no figura en los metadatos de esa página, de modo que la unidad se vincula a todos los pasajes de la página, con aviso. Son 63 continuaciones y 3 encabezados ausentes de los metadatos.
- Discrepancias de metadatos documentadas, no corregidas:
  - P155–159: heading «waza (B)», article_id GENERAL, cuando el texto es el **Article 10**.
  - P111: **B1.7** ausente.
  - P190: **Article 18.2** ausente.
- Hashes: `source_text_sha256` coincide con el `text_sha256` del pasaje y `derived_text_sha256` coincide con el SHA-256 del corte, en todas las unidades. `hashes.json` contiene el SHA-256 de cada artefacto y del archivo de entrada.

## 9. Excepciones y referencias

- Los 107 marcadores de excepción por página son iguales a la suma de los de las hojas: ninguno cae en un corte.
- Hay 242 referencias cruzadas: ARTICLE 54, APPENDIX_SECTION 19, SECTION 27, TABLE 1, FIGURE 141. De las que no son figura, 98 se resuelven y 3 no:
  - «Article 13.5» (P136) y «Article 4.7» (P162) apuntan a subnúmeros que no son encabezados en el corpus.
  - «Article 18 .1 .5» (P289) está dentro del historial de versiones.
- Caso de control: P190 «see also Article 18.1.4 point 34» → `AU1-P188-002-C03`, que es la cláusula 34 literal. Es la relación que la opción A de la Fase 6.5 perdía.
- Todas las referencias resueltas apuntan a unidades existentes, y ninguna referencia queda partida entre hojas.

## 10. Tests y resultados

- `tests/test_article_units.py`: 14 pruebas estructurales más 1 de reproducibilidad de artefactos. Cubren: página multi-artículo, artículo con varias cláusulas, enumeraciones, excepciones, referencias, encabezados, texto no segmentable, formato irregular, duplicados originales, reconstrucción, trazabilidad, integridad de hashes, preservación de IDs y de la entrada, y cobertura total con validación.
- `tests/test_benchmark_v1.py`: 5 pruebas sobre composición y campos, ausencia de certificación arbitral, anclas literales o PENDIENTE, splits disjuntos y reproducibilidad.
- Windows (pytest): **20 passed** en 5,35 s (`tests/test_article_units.py` y `tests/test_benchmark_v1.py`).
- Ninguna prueba verifica respuestas normativas.

## 11. Limitaciones

- Línea base solo en modo local sin LLM: no mide el camino con traductor LLM ni la calidad de la respuesta.
- Benchmark sin revisión arbitral. Las consultas fueron redactadas con asistencia de IA, así que pueden reflejar sesgos de redacción y tener cobertura desigual entre artículos.
- La segmentación de cláusulas es conservadora: solo 36 segmentos se dividen. Las tablas, las listas anidadas que reinician la numeración y los artículos largos con imágenes (18.1.2 páginas 180 y 182, 13, 14, 11) quedan sin dividir o como NO_SEGMENTADA.
- La atribución de continuaciones asume el orden de páginas. Las 63 continuaciones heredan el artículo de la página anterior, sin confirmación en los metadatos.
- La detección de excepciones es léxica y sirve solo como control de preservación. No interpreta el alcance de una excepción.
- La partición por hash con categorías pequeñas deja proporciones aproximadas (por ejemplo, 3 OOD en validación).

## 12. Riesgos

- Usar el benchmark como «verdad» sin revisión arbitral fijaría errores de anotación.
- Ajustar sobre test invalidaría la evaluación futura.
- Las unidades con `PAGE_FALLBACK` y las páginas P155–159 tienen la relación artículo-pasaje débil. Si se usan en producción sin tratamiento explícito, la cita de artículos podría quedar mal atribuida.
- Si las unidades derivadas se usan sin respetar `DERIVADA_NO_NORMATIVA`, podrían presentarse como fuente. Deben citarse siempre por el `passage_id` original.

## 13. Dictamen por etapa

| Etapa | Dictamen |
|---|---|
| 0 — Benchmark | **APTO como benchmark de desarrollo** (versionado, anclado, partición disjunta). **NO certificado**: requiere revisión arbitral. |
| 0 — Línea base | **EJECUTADA Y REPRODUCIBLE** (script de solo lectura; corpus inalterado). Muestra limitaciones de recuperación relevantes (§4). |
| Ampliación SHADOW | **ACEPTADA**: inventario, segmentación separada y benchmark auxiliar. Separación de autoridad verificada: AUTH1–5 24/24, con 15/15 sondas efectivas rechazadas. Riesgo abierto: validación de citas sin pertinencia (sonda B) (§15). |
| 1 — Segmentación | **ACEPTADA**: 100 % de unidades trazables, 100 % del texto contabilizado, sin pérdida, corpus inalterado, referencias y excepciones conservadas, segmentación insegura marcada, artefactos reconstruibles. Hay 84 avisos documentados. |

## 14. Recomendaciones

1. Usar §4 como referencia. Las mejoras deben medirse solo en dev y validación, priorizando la brecha ES/EN, los falsos OOD en consultas organizativas y la precisión del bundle.
2. Revisión arbitral, como prioridad, de las 30 consultas de excepción, las 8 con artículo pendiente y las 15 ambiguas. Registrar al revisor y la fecha en `human_review_status`.
3. Siguiente fase, en sombra y con autorización: medir la recuperación sobre unidades derivadas que se mapean al `passage_id` padre, comparando contra esta línea base solo en dev y validación.
4. Decidir con un humano cómo tratar las discrepancias de metadatos (Article 10, B1.7, 18.2) en una revisión del corpus versionada aparte, sin modificar este corpus.

## 15. Documentación complementaria SHADOW

### 15.1 Inventario y cobertura

Fuentes (solo lectura): `docs/registro_documental_multifuente_ijf.csv` (catálogo de autoridad), `data/corpus_multisource/{sidecar_registry.json, manifests/BATCH-MULTI-2026-11-02.json (activo), processed/multisource_passages.json, staging/*_staged.md}`, `data/raw/complementary/*.pdf`. El inventario completo está en `data/derived/shadow_units_v1/inventory.json`.

| Estado en inventario | Documentos |
|---|---|
| CORPUS_PRIMARIO_SOR (TIER_1) | 1 (DOC-SOR-2026-08) |
| INGESTADO_SIDECAR | 6: KUN-PPT-002 (TIER_3), KUN-NEW-001, KUN-NEW-003, KUN-DIS-001, KUN-ETH-001, KUN-QSY-001 (TIER_2) |
| REGISTRADO_NO_INGESTADO | 21 (portales web, vídeos, presentaciones, comunicados de origen y PDFs DOC-DIS/ETH/QSY) |
| HISTORICO_NO_INGESTADO | 2 · RECHAZADO 1 (REF-VID-004-YOUTUBE) |

- **Fragmentos vigentes: 18**, todos elegibles según el mismo filtro de `MultisourceRetriever`.
- Coherencia del registro del sidecar: el hash de `multisource_passages.json` (`8c5365f0…`) y el del corpus SOR (`7d463428…`) coinciden con el registro, y hay 18 fragmentos declarados.
- Trazabilidad de cada fragmento: fragmento → documento del catálogo → manifiesto activo → espejo de staging. El SHA-256 del staging es igual al `hash_integridad` del catálogo y al del manifiesto.
- En los 18 casos el texto aparece **literalmente** en su espejo, dentro de su bloque KUN declarado.
- **Procedencia original (no verificable de forma completa)**:
  - Con `--verify-upstream` (pypdf 6.21.2), ninguno de los 18 fragmentos aparece literal completo en los PDFs locales. Solo 3 coinciden en el prefijo de 60 caracteres: DIS-001-001 (pág. 2), DIS-001-003 (pág. 3) y ETH-001-001 (pág. 3).
  - Para PPT-002, NEW-001 y NEW-003 no hay original local (fuentes web o presentaciones).
  - Conclusión: los fragmentos son **extractos o paráfrasis curadas**, no citas literales de la fuente oficial.
- `IJF_LA28_Olympic_Qualification_FAQ_2026_06_12.pdf` está en local pero **no figura en el catálogo** (aviso). No se ingiere.
- No se inventaron documentos ni fragmentos.

### 15.2 Segmentación derivada

`scripts/build_shadow_units.py` (1.0.0, solo biblioteca estándar) genera `data/derived/shadow_units_v1/`:
- Artefactos: `units.jsonl`, `inventory.json`, `traceability_map.json`, `coverage_stats.json`, `validation_report.json`, `errors.jsonl`, `metadata.json`, `hashes.json` y, opcional, `upstream_verification.json`.
- El directorio está separado de `data/derived/article_units_v1/` y del corpus.
- **Método `chunk_identity`**: cada fragmento sidecar ya es un enunciado KUN atómico, así que se crea una unidad por fragmento, sin dividir ni fusionar. El texto es idéntico al fragmento y se guarda su offset y línea en el espejo.
- **18 unidades** `SHU1-<chunk_id>`: TIER_2 16, TIER_3 2. Por documento: QSY 4, DIS 3, ETH 3, NEW-001 3, NEW-003 3, PPT 2.
- Se conservan `chunk_id`, `document_id`, `source_kun_id`, el encabezado del bloque KUN, la ruta y el hash del espejo, y los metadatos del catálogo (autoridad, vigencia, aprobación, relación normativa, fuente y URL).
- Artículos SOR relacionados: el texto libre se analiza y se resuelve a unidades `AU1-…`. Las 45 referencias se resuelven, y es un vínculo de contexto, no de autoridad.
- Validación: 0 errores, 1 aviso (el PDF sin catálogo). `--check` → REPRODUCIBLE.
- Los archivos originales SHADOW tienen el mismo hash antes y después: se comprobaron por SHA-256 `data/corpus_multisource/`, `data/raw/complementary/`, `data/markdown/` y el catálogo.

### 15.3 Evaluación de recuperación auxiliar

`benchmark_shadow_v1` (`scripts/build_benchmark_shadow_v1.py`, `data/eval/benchmark_shadow_v1/`) tiene 24 casos: 13 es / 11 en.
- Todos llevan `auxiliary_use_policy = CONTEXTO_NO_DECISORIO`.
- Revisión arbitral: 0/24. No se declara revisión inexistente.

| Clase de evidencia | n | Base normativa esperada |
|---|---|---|
| PRIMARIA_CON_AUXILIAR | 8 | SOR; SHADOW como contexto útil |
| SOLO_AUXILIAR_SIN_PRIMARIA | 6 | ninguna: abstención normativa; SHADOW solo informativo (LA28, prescripción disciplinaria, congelación de reglas) |
| AUXILIAR_NO_DEBE_FUNDAMENTAR | 6 | SOR; el fragmento SHADOW no puede fundamentar |
| SIN_EVIDENCIA_SUFICIENTE | 4 | ninguna |

Anclas: las SOR se verifican literalmente con el mismo verificador de `benchmark_v1`; SH-007 queda con «artículo pendiente» (Article 10 / metadatos GENERAL). Las SHADOW se verifican literalmente contra `content_text`. Cubren 17 de 18 fragmentos (falta DIS-001-001).

Observaciones textuales (literales, **pendientes de revisión arbitral**; no son juicios normativos):
- SH-015: el SOR 18.1.1 dice «45 seconds»; CHK-KUN-NEW-001-003 dice «30-second time limit».
- SH-017: CHK-KUN-NEW-003-003 formula una excepción («Involuntary head contact … not subject to penalization») que no se localiza literalmente en el SOR.
- SH-016: el SOR regula el seoi-nage inverso en cadetes; CHK-KUN-NEW-001-002 habla de seniors.

**Resultados — corpus complementario** (`python scripts/eval_shadow_v1.py --sidecar-only`; `MultisourceRetriever.search(top_k=3, min_score=2.0)` con la consulta original; VM; entradas inalteradas):

| Métrica | Valor |
|---|---|
| Hit@3 auxiliar (14 ítems con fragmento esperado) | 0,93 (PRIMARIA_CON_AUXILIAR 0,875 · SOLO_AUXILIAR 1,00) |
| MRR@3 auxiliar | 0,86 |
| Hit@3 por idioma | es 0,86 · en 1,00 |
| Fallos | SH-008 (arrastre a ne-waza, ES) |
| Fragmento «no debe fundamentar» recuperado | 5/6 (0,83): se recupera como contexto; lo que debe impedirse es su uso como base (§15.4) |
| Falsos positivos en SIN_EVIDENCIA | 2/4 (SH-021 Brisbane 2032 → fragmentos LA28; SH-023 → fragmento Ulaanbaatar) |
| Latencia media | 0,16 ms |

**Resultados — combinados** (ruido SHADOW sobre las 150 consultas de `benchmark_v1`): reciben algún fragmento SHADOW 11/60 ordinarias ES, 8/30 EN, 9/30 de excepción, 3/15 ambiguas y 1/15 OOD (B1-OOD-014, peso del equipaje → fragmentos LA28). En total 32/150 consultas primarias reciben contexto auxiliar, en su mayoría no pertinente. Ejemplos:
- B1-EN-004 (tamaño del equipo mixto) → cuotas LA28.
- B1-ES-001 (agresión) → sanciones disciplinarias, que sí está relacionado.

Este contexto no altera la evidencia primaria, porque es un bloque separado y no decisorio, pero añade ruido al prompt.

**Resultados — corpus primario**: ver §4. La ampliación SHADOW no cambia la línea base primaria.

### 15.4 Separación de autoridad

Controles vigentes en ADA/RRE (AUD-04, Fases 4–5), **sin modificar**:
- La autoridad sale del catálogo y lo no registrado se descarta.
- El material complementario va en un bloque «CONTEXTO DOCUMENTAL COMPLEMENTARIO — INFORMATIVO Y NO DECISORIO».
- Cada elemento de `supplementary_context` lleva `decisive=False`.
- La validación de citas exige al menos un ID SOR primario entregado y rechaza cualquier otro identificador.
- `NormativeValidator` usa como verdad solo la evidencia primaria.

Evidencia en esta fase:
- **Estructural (VM, verificado)**: 18/18 unidades con `normative_status=AUXILIAR_NO_NORMATIVA`, `decisive=False`, `citable_as_sor=False` y `may_substitute_sor=False`. Ninguna es TIER_1. Ningún ID `SHU1-`/`CHK-` coincide con IDs `SOR-`/`AU1-`, y no aparece ningún `CHK-` dentro de `article_units_v1`.
- **Comportamiento (Windows, `python scripts/eval_shadow_v1.py`, 24 casos, sin LLM real; entradas inalteradas):**

| Control | Resultado |
|---|---|
| AUTH1 — ningún fragmento SHADOW en la evidencia primaria (evidence + related) | 24/24 |
| AUTH2 — todo `supplementary_context` con `decisive=False` | 24/24 |
| AUTH3 — contexto complementario catalogado y no TIER_1 | 24/24 |
| AUTH5 — con una cita SOR (sonda B), las citas solo son SOR | 24/24 |
| AUTH4 — una respuesta que cita solo SHADOW queda en ABSTAIN y sin citas SHADOW | **15/15 sondas efectivas rechazadas** (24/24 en total; en 9 casos no se entregó SHADOW y la sonda no aplica) |

- **Corrección de medición (AUTH4).** La primera ejecución dio 24/24, pero `probeA_with_shadow_delivered = 0`. ADA no expone el `chunk_id` en el bloque complementario, solo «[COMPLEMENTO-n]», que es precisamente el control AUD-04.3. La sonda buscaba IDs `CHK-` en el prompt, no encontraba ninguno y citaba un ID inexistente. El resultado era **vacuo**.
  - Se corrigió la sonda en `scripts/eval_shadow_v1.py` y en `test_ada_rejects_shadow_as_autonomous_basis`. Ahora cita los `chunk_id` realmente entregados en `supplementary_context` y su etiqueta `[COMPLEMENTO-n]`, y exige que el bloque complementario haya llegado al prompt.
  - No se modificó el código de producción.
  - Segunda ejecución: `probeA_with_shadow_delivered = 15` (SH-001, 002, 003, 004, 006, 007, 008, 011, 015, 016, 017, 018, 019, 020 y 023). `probeA_effective_rejected = 15/15`: todas terminan en ABSTAIN y sin citas SHADOW.
  - **Conclusión: ningún fragmento SHADOW puede ser fundamento normativo autónomo en ADA.** Esto vale para la cita explícita. El uso implícito del contexto por un modelo real no queda cubierto (ver sonda B).
- Bundle primario en los casos con ancla SOR (sin LLM): recall de anclas 0,64.
- Fragmento auxiliar esperado presente en `supplementary_context`: 0,57. Es menor que el Hit@3 del sidecar aislado (0,93) porque ADA filtra por el catálogo y aplica su propio umbral y reintento.
- **Fragmentos «no debe fundamentar» entregados como contexto: 6/6** (SH-015 a SH-020). Siempre con `decisive=False` y fuera del bloque primario, pero llegan al modelo, incluidos los tres que difieren literalmente del SOR.
- **Sonda B: SUCCESS sin base primaria en SH-011, SH-022, SH-023 y SH-024.** En consultas sin respuesta en el SOR (prescripción disciplinaria, multa por amaño, patrocinadores, honorarios), un «modelo» que cita el primer pasaje SOR entregado supera la validación de citas.
  - Confirma que la validación comprueba **procedencia, no pertinencia ni entailment** (limitación ya declarada).
  - Con un modelo real, el riesgo es una respuesta aparentemente normativa con una cita SOR no pertinente, mientras el contenido real lo aportaría el contexto SHADOW. No se corrige en esta fase porque requiere cambiar ADA, y eso no está autorizado.

### 15.5 Riesgos y limitaciones

- **Procedencia**: los fragmentos son paráfrasis curadas, no verificables literalmente contra los PDFs. Su fidelidad a la fuente oficial requiere revisión humana.
- **Contenido discrepante con el SOR** (SH-015, SH-016, SH-017): está bien contenido como no decisorio. Pero si se mostrara al usuario sin advertencia, podría inducir a error. Conviene revisarlo con árbitros y valorar retirarlo o anotarlo en el catálogo, en una decisión fuera de esta fase.
- **Falsos positivos léxicos** del sidecar (LA28 para Brisbane 2032, equipaje → cuotas): el umbral BM25 no distingue el contexto temporal o temático.
- 32/150 consultas primarias reciben contexto auxiliar, casi siempre irrelevante: ruido en el prompt.
- La medición sin LLM no evalúa si un modelo real usaría el contexto SHADOW como argumento implícito, aunque no lo cite. La sonda B (4 SUCCESS sin base primaria) muestra que la validación de citas no lo impediría: verifica procedencia, no entailment.
- Los fragmentos discrepantes con el SOR llegan al modelo como contexto (6/6 casos «no debe fundamentar»).
- El benchmark auxiliar es pequeño (24 casos, sin splits) y no tiene revisión arbitral. No debe usarse para ajustar umbrales.
- El PDF de FAQ LA28 está sin catalogar.

### 15.6 Tests y resultados

- `tests/test_shadow_units.py` (9 pruebas): trazabilidad completa, unidades idénticas a los fragmentos, separación de corpus, ausencia de autoridad normativa, resolución de artículos SOR relacionados a unidades primarias existentes, originales inalterados, reproducibilidad de artefactos, estructura del benchmark auxiliar y rechazo en ADA de SHADOW como base autónoma (con StubLLM).
- Windows (pytest): **29 passed** en 15,72 s (`test_shadow_units`, `test_article_units` y `test_benchmark_v1`). Tras corregir la sonda: **`test_shadow_units` 9 passed** en 10,21 s, con el test de ADA ejecutándose de forma efectiva sobre contexto SHADOW entregado.
- Integridad al cierre:
  - Corpus SOR con SHA-256 inalterado.
  - Archivos SHADOW originales inalterados (comparación de SHA-256 sobre todos).
  - Sin cambios en `src/`, `app.py`, configuración ni `.env`.
  - La ejecución en la VM dejó dos `.pyc` de Python 3.10 en `__pycache__` (ignorados por git, sin efecto en el Python 3.12 de Windows), que no se pudieron borrar por falta de permiso.
  - Sin commit, push ni despliegue OCI.

### 15.7 Recomendaciones SHADOW (requieren autorización; no implementadas)

1. Revisión arbitral de CHK-KUN-NEW-001-003, NEW-001-002 y NEW-003-003 (difieren literalmente del SOR), con decisión en el catálogo: anotar, restringir o retirar.
2. Evaluar con autorización un control de pertinencia de la base primaria, más allá de la procedencia de la cita, para el patrón de la sonda B (SUCCESS sin base SOR pertinente).
3. Catalogar o descartar `IJF_LA28_Olympic_Qualification_FAQ_2026_06_12.pdf`.
4. Reducir el ruido del sidecar (32/150 consultas primarias reciben contexto auxiliar), midiéndolo con `benchmark_shadow_v1` y sin usar el test de `benchmark_v1`.

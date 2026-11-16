# Fase 7 — Plan de arquitectura de recuperación multilingüe (RRE)

**Proyecto:** IJF SOR Assistant 2026 · **Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`
**Fecha:** 2026-11-15 · **Alcance:** diagnóstico y plan. No se modificó código, corpus, índices, tests ni configuración.

> Las métricas citadas provienen de `scripts/eval_rre_retrieval.py` (18 consultas respondibles + 5 OOD) y de las suites ejecutadas en Windows durante la Fase 6. Es un conjunto pequeño: sirve para orientar, **no** como evidencia definitiva. Las métricas de recuperación miden si llega un pasaje con la página/artículo objetivo; **no** miden suficiencia normativa ni entailment.

---

## 1. Resumen ejecutivo

1. **La unidad de recuperación es una página completa del PDF, no un artículo.** Los 385 pasajes son texto de página extraído con `pypdf` (`full_page_text`); solo hay 287 textos distintos. 158 pasajes comparten texto idéntico con otro (60 grupos, hasta 7 IDs por página). Esto genera ruido estructural, ambigüedad de artículo y duplicados en el contexto.
2. **El canal denso es solo inglés** (`all-MiniLM-L6-v2`, 384 d) sobre un corpus solo inglés (`text_es` vacío en 385/385). El español depende del traductor LLM o de una proyección por diccionario.
3. **La pertinencia actual depende de reglas manuales.** `retrieve()` contiene 35 listas de palabras clave, 18 IDs de pasaje fijados (32 apariciones) y ~19 condiciones por página. Sin ellas (fusión pura), Recall@5 cae de 1.00 a 0.72 (ES) y 0.78 (EN); MRR de 0.94 a 0.50 (ES).
4. **El contexto entregado al LLM es ruidoso:** precisión ≈ 0.25 (7.1 pasajes de media) y el *stitching* añade hasta 3 páginas por lado; en HDIV el bloque primario contenía 16 IDs de página.
5. **Las referencias cruzadas son necesarias:** la Fase 6.5 demostró que excluirlas pierde reglas especiales (P190 → P188, Art. 18.1.4 punto 34; excepción *Sono-mama* en P175).
6. **Producción es CPU-only, ARM64, 1 OCPU, 5.8 GiB RAM.** Cualquier modelo adicional debe medirse en ese hardware antes de adoptarse.

**Recomendación:** arquitectura combinada por etapas, empezando por (0) un conjunto de evaluación anotado por árbitros con casos de excepción, (1) un **índice derivado de sub-unidades (artículo/cláusula) mapeado a los IDs de pasaje existentes**, (2) un **canal denso multilingüe adicional en modo sombra**, (3) lexical BM25 sobre sub-unidades, y (4) reranker solo si cabe en el presupuesto de latencia. La retirada de reglas manuales se hace **al final**, por grupos, con regresión de excepciones obligatoria.

**Dictamen:** **APTO** para iniciar las Etapas 0–1 (evaluación y derivados en modo sombra). **NO APTO** para cambiar la recuperación en producción o retirar reglas manuales hasta cumplir los criterios de la sección 7.

---

## 2. Arquitectura actual verificada

### 2.1 Corpus y artefactos derivados (`data/processed/rebuild_2026_08_corrected/`)

| Artefacto | Contenido verificado | Tamaño |
|---|---|---|
| `passages_candidate.json` | 385 pasajes; `language_original=en`; `extraction_method=pypdf_page_physical`; `source_span.method=full_page_text`; `text_es` vacío; `translation_status=not_started`; `review_status=extracted`; 257 `article_id` distintos (p. ej. `H1.1`×40, `GENERAL`×20) | 1.2 MB |
| `dense_embeddings_candidate.npy` | Matriz 385 × 384 (float32), alineada 1:1 con `passage_ids`; `source_sha256=9426b10d…ae620` | 0.59 MB |
| `dense_embeddings_meta.json` | `model_name=sentence-transformers/all-MiniLM-L6-v2`, `dimension=384`, `num_passages=385` | 12 KB |
| `vector_index_candidate.json` | Índice léxico TF-IDF: `idf` + `vectors` por pasaje (no BM25) | 1.9 MB |
| `knowledge_graph_candidate.json` | 385 nodos, 68 aristas, todas `references_article` con `provenance: Explicit citation in text`; 52 orígenes, 18 destinos; más referenciados: P175-S191 (20), P196-S205 (12), P195-S202 (8) | 91 KB |

**Granularidad:** 287 textos distintos para 385 IDs; los 60 grupos duplicados están siempre en la misma página (p. ej. P105-S128…S134 con `article_id` A1.8…A1.14 y texto idéntico). No hay marcadores `[PAGE BREAK]` en los textos.

### 2.2 Recuperación (`src/rre_engine.py`, `retrieve()`)

| Componente | Implementación verificada |
|---|---|
| Tokenización | minúsculas, elimina acentos, `[a-zA-Z0-9_-]{2,}`, stopwords; añade sinónimos de `SPANISH_TO_ENGLISH_SYNONYMS` y expansión `NormativeOntology` **dentro** del tokenizador |
| Lexical | coseno TF-IDF sobre `vector_index` (top 25, umbral 0.05) |
| Denso | `all-MiniLM-L6-v2` sobre la consulta y sobre una re-proyección por diccionario; se toma el máximo de ambas similitudes (top 25, umbral 0.15) |
| Fusión | RRF k = 60 (peso léxico 1.2, denso 1.0) + bonificación multi-canal (+0.035, ×1.35) |
| Reglas manuales | 35 condiciones por palabras clave; 18 IDs fijados (32 apariciones; p. ej. P174, P151/P152, P166/P167, P190, P188/P189, P193, P168/P169, P038/P039); ~19 condiciones por página/rango (p. ej. 137–151, 115–127, 178–185, 250–275, 259–298); inyección de pasajes no recuperados (score 0.025–0.04); mapa `f1_to_sec2` para referencias explícitas a páginas de plantillas F1.3 |
| Componentes opcionales activos | `semantic_ranker`, `referee_disambiguation`, `ood_detector`, `negative_domain_anchors`, `chunk_stitching` (todos `True` en el entorno evaluado) |
| OOD | (1) anclas negativas (desde Fase 6 C1, sobre la consulta original); (2) `OODDetector` (centroide denso + cobertura ontológica, θ = 0.38); (3) anclaje léxico `substantive_in_vocab` + `JUDO_TECHNICAL_IMMUNITY` + umbrales densos 0.45/0.35 |
| Selección | top-k = 5 semillas con deduplicación por texto (>85 % de solapamiento) + expansión por grafo (hasta 3 `related_passages`) |
| Stitching | `PassageStitcher(max_expansion_pages=3)`: puede reconstruir hasta 3 páginas hacia delante y hacia atrás |

### 2.3 Traducción y ADA (`src/ada_assistant.py`)

- **Con LLM:** prompt-glosario de traducción técnica (Fase 2 lo dejó sin conclusiones normativas).
- **Sin LLM:** proyección por diccionario (Fase 6 C2: tokens con acentos, palabras funcionales ES, deduplicación). Las palabras sin entrada quedan en español.
- **EvidenceBundle:** evidencia directa + relacionada por grafo → carril primario certificado; complementarios en carril interpretativo, separados y no decisorios (AUD-04); abstención sin LLM (opción A); validación de citas contra evidencia primaria entregada (AUD-03/04). No hay verificación semántica.

### 2.4 Recursos

| Entorno | Datos verificados |
|---|---|
| Producción (OCI, según `docs/auditoria/auditoria_pre_deployment_oci_2026_11.md`) | ARM64 Ampere Altra (Neoverse-N1), **1 OCPU**, 5.8 GiB RAM total (≈3.8 GiB libres), sin GPU, Ubuntu 24.04, Docker `python:3.12-slim` |
| Desarrollo (Windows) | Latencia media de `retrieve()`: 37–49 ms con reglas; 22–30 ms fusión pura (no medido en ARM) |
| Dependencias | `torch>=2.0`, `sentence-transformers>=3.0`, `numpy` (ya presentes); el modelo se carga solo desde snapshot local (`RRE_MODEL_PATH` o caché HF) |

### 2.5 Línea base de recuperación (Fase 6, tras C1/C2; 18 respondibles, k = 5)

| Modo | OOD válidas rechazadas | Recall@5 | MRR@5 | P@1 | Precisión entregada |
|---|---|---|---|---|---|
| ES (proyección, reglas activas) | 0 | 1.00 | 0.94 | 0.89 | 0.25 |
| EN (reglas activas) | 0 | 1.00 | 0.93 | 0.89 | 0.26 |
| ES fusión pura (sin reglas) | 0 | 0.72 | 0.50 | 0.39 | 0.23 |
| EN fusión pura (sin reglas) | 0 | 0.78 | 0.62 | 0.56 | 0.27 |

OOD: 0 falsas aceptaciones en 5 consultas negativas.

---

## 3. Problemas estructurales identificados

| # | Problema | Evidencia | Efecto |
|---|---|---|---|
| P1 | **Granularidad de página** | 385 IDs / 287 textos; páginas con hasta 7 artículos y el mismo texto | Ruido en el contexto; el `article_id` no delimita el texto; duplicados (p. ej. P152-S179 = P152-S180) |
| P2 | **Canal denso monolingüe** | MiniLM-L6 inglés; `text_es` vacío | El español sin traductor depende de un diccionario; el OOD denso también se degrada |
| P3 | **Expansión léxica acoplada al tokenizador** | Sinónimos y ontología se inyectan en el tokenizador; proyecciones como «assigned correct», «tatami competition area» | Ruido léxico; difícil de evaluar por separado |
| P4 | **Dependencia de reglas manuales** | +0.22–0.28 de Recall@5 y +0.31–0.44 de MRR atribuibles a reglas; IDs y páginas fijados | Sobreajuste a preguntas conocidas; mantenimiento frágil; atajos normativos por página |
| P5 | **OOD heurístico en tres filtros** | Listas de inmunidad y anclas; caso «penalty» (Fase 6) | Rechazos espurios ante cambios de vocabulario; calibración ligada al modelo inglés |
| P6 | **Contexto excesivo** | Precisión ≈ 0.25; stitching de hasta 7 páginas; HDIV: 16 IDs en el bloque primario | El LLM recibe mucho texto no pertinente; riesgo de desviación |
| P7 | **Referencias cruzadas a nivel de página** | 68 aristas página → página; P175 es destino de 20 | Se arrastra la página completa cuando solo se necesita una cláusula (p. ej. «18.1.4 punto 34») |
| P8 | **Evaluación insuficiente** | 18 + 5 consultas; objetivos por localizador; equivalentes EN redactados para el script | No permite afirmar mejoras generales ni medir suficiencia o respaldo |

---

## 4. Alternativas comparadas

| | A. Embeddings multilingües | B. Híbrido léxico + vectorial mejorado | C. Cross-encoder reranker | D. Combinada (A + B + C) | E1. Sub-unidades derivadas (artículo/cláusula) |
|---|---|---|---|---|---|
| **Beneficio principal** | Consultas ES sin traductor; OOD denso multilingüe | BM25 con normalización; expansión separada y medible | Mejor ordenación del top-k (P@1, MRR) | Máxima cobertura y ordenación | Elimina la causa raíz del ruido (P1, P6, P7) |
| **Limitación** | Requiere re-codificar el corpus (derivado); posible pérdida en EN; recalibrar OOD | No resuelve la brecha de idioma por sí solo | Coste por consulta; los multilingües pesan | Complejidad y coste acumulados | Requiere segmentación verificable; los IDs nuevos deben mapear a los existentes |
| **Coste computacional** (estimación, a medir en ARM 1 OCPU) | Modelo de ~120 M parámetros (~0.5 GB); re-codificar ≈ 400–1 500 unidades: minutos | Despreciable | ~20–50 pares/consulta; latencia a medir (probablemente cientos de ms a >1 s en 1 OCPU) | Suma de A + C | Script offline; índices algo mayores |
| **Complejidad** | Media | Baja–media | Media | Alta | Media |
| **Impacto en excepciones** | Neutro o positivo si las sub-unidades conservan las cláusulas | Neutro | Riesgo: puede degradar cláusulas de excepción poco similares a la consulta | Depende de C | **Positivo:** permite entregar la cláusula exacta («punto 34») en vez de la página |
| **Riesgo de pérdida de evidencia** | Medio (cambio de espacio vectorial) | Bajo | Medio (recorte del top-k) | Medio | Bajo–medio (errores de segmentación) → mitigado con mapeo y verificación de cobertura |
| **Compatibilidad** | Alta si se añade como canal adicional versionado | Alta | Alta (post-proceso) | Media | Alta si la cita sigue siendo el `passage_id` padre |

**E2 — Traducción LLM con caché como vía principal ES→EN:** el camino EN ya alcanza Recall@5 = 1.00. Es barato de integrar, pero depende de la disponibilidad del LLM; sin LLM la opción A de abstención ya se aplica. Útil como complemento, no como sustituto.

**E3 — Traducción derivada del corpus (`text_es`) para indexación:** permitiría un índice léxico ES. Riesgo normativo: una traducción no oficial podría filtrarse a respuestas. Solo aceptable como índice de recuperación, nunca citable ni mostrado, y tras revisión. Menor prioridad que A.

**Descartado por recursos:** modelos grandes (p. ej. 1024 d, >2 GB) no son viables en 1 OCPU / 5.8 GiB junto con la aplicación.

---

## 5. Recomendación técnica

Arquitectura **D por etapas, anclada en E1**:

1. **Sub-unidades derivadas (E1):** segmentar cada página en unidades de artículo, apartado o punto numerado, usando la estructura visible del texto (encabezados `Article N`, `N.N.N`, puntos numerados). Cada sub-unidad conserva `parent_passage_id`, offsets de carácter y `text_sha256`. **La cita normativa sigue siendo el `passage_id` padre**; la sub-unidad solo delimita el texto que se entrega al LLM.
2. **Canal denso multilingüe adicional (A)**, en modo sombra, sobre sub-unidades. Mantener MiniLM-L6 en paralelo hasta demostrar paridad o mejora. Candidatos de 384 d y ~0.5 GB (p. ej. variantes *multilingual MiniLM-L12* o *multilingual-e5-small*), a seleccionar con benchmark propio y verificación de licencia.
3. **Lexical BM25 sobre sub-unidades (B)**, con la expansión de sinónimos fuera del tokenizador y medible por separado.
4. **Reranker (C) solo si** la latencia p95 en ARM 1 OCPU cabe en el presupuesto acordado y la recuperación de excepciones no empeora.
5. **Referencias cruzadas a nivel de cláusula:** cuando una sub-unidad cita «Article 18.1.4 point 34», entregar la sub-unidad destino (punto 34), no la página completa. Las aristas actuales se conservan; se añade una resolución derivada a sub-unidad.
6. **Retirada de reglas manuales al final**, por grupos temáticos, cada uno con regresión obligatoria sobre su subconjunto de excepciones.

---

## 6. Plan de implementación por etapas

| Etapa | Contenido | Entrada | Salida / criterio para avanzar |
|---|---|---|---|
| **0. Evaluación** | Conjunto *gold* ≥ 150 consultas ES/EN (pares equivalentes), ≥ 30 casos de excepción o regla especial, ≥ 30 OOD; anotación por árbitro de: pasajes requeridos (incluidas excepciones y referencias), suficiencia y respuesta de referencia. Ampliar `scripts/eval_rre_retrieval.py` con R@10, métricas por subconjunto y latencia p50/p95 | Autorización | Gold set revisado y congelado (versionado con hash); línea base registrada |
| **1. Sub-unidades (sombra)** | Script offline de segmentación → nuevo artefacto en carpeta derivada separada; informe de cobertura (100 % del texto de página asignado a alguna sub-unidad; sin solapamientos no declarados) | Etapa 0 | Cobertura verificada; ningún pasaje padre sin sub-unidades; recall en sombra ≥ línea base |
| **2. Denso multilingüe (sombra)** | Codificar sub-unidades con el modelo candidato (artefacto nuevo y versionado); canal adicional en RRF solo en modo evaluación | Etapa 1 | Recall@5 ES ≥ EN − 0.02; excepciones sin regresión; OOD sin falsas aceptaciones; latencia y RAM medidas en ARM |
| **3. BM25 + expansión desacoplada** | Lexical sobre sub-unidades; sinónimos como canal medible | Etapa 1 | Mejora o paridad en MRR sin regresión de excepciones |
| **4. Reranker (opcional)** | Cross-encoder sobre top-20 | Etapas 2–3 | p95 dentro del presupuesto en ARM; P@1 mejora; excepciones sin regresión |
| **5. Contexto y referencias** | Entrega por sub-unidad; referencias a cláusula; límite de stitching | Etapas 1–3 | Precisión entregada ≥ 0.5 sin pérdida de evidencia requerida (incluidas excepciones) |
| **6. Retirada de reglas** | Por grupos (frontera/ne-waza, cabeza/puente, cadetes, conducta, kumikata, judogi, páginas) | Etapas 1–5 | Cada grupo retirado sin regresión en su subconjunto y en el global |
| **7. Activación** | Cambio de canal por bandera de configuración, con reversión inmediata | Todas | Aprobación explícita; despliegue fuera de este plan |

---

## 7. Benchmarks y criterios de aceptación

Distinguir tres niveles (no intercambiables):

1. **Artículo correcto recuperado** — automático por localizador (R@5, R@10, MRR, P@1).
2. **Evidencia suficiente** — todos los pasajes requeridos del caso anotado (regla general + excepciones + referencias) entregados. Métrica: *recall de conjunto requerido* por caso (1 si están todos).
3. **Evidencia que respalda la respuesta** — juicio humano del árbitro sobre si lo entregado basta para la respuesta de referencia. **No** se automatiza ni se infiere de citas válidas; no equivale a entailment del texto generado.

| Métrica | Definición | Criterio propuesto (a confirmar) |
|---|---|---|
| R@5 / R@10 (ES, EN) | Algún pasaje requerido en top-k | ES ≥ EN − 0.02; sin caída respecto a la línea base |
| MRR, P@1 | Rango del primer requerido | No inferior a la línea base |
| Recall de conjunto requerido | Todos los requeridos entregados | 100 % en el subconjunto de excepciones; ≥ línea base global |
| Excepciones y referencias | Casos donde la decisión depende de una regla especial o remisión | **Ninguna regresión** (criterio bloqueante) |
| Precisión entregada | Requeridos / unidades entregadas | Mejora, solo si los dos criterios anteriores se cumplen |
| OOD | Falsas aceptaciones / falsos rechazos | 0 falsas aceptaciones; falsos rechazos ≤ línea base |
| Recursos | Latencia p50/p95 y RAM en ARM 1 OCPU | Presupuesto a fijar (propuesta: p95 de recuperación ≤ 1 s, RAM total ≤ 3 GiB) |

Reproducibilidad: gold set congelado con hash, semillas fijas, versión de modelo y artefacto registradas, ejecución sin LLM real (stubs) para recuperación; la evaluación de respaldo humano se documenta aparte.

---

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Segmentación errónea que corta una excepción | Verificación de cobertura del 100 % del texto; las sub-unidades nunca sustituyen al padre como cita; regresión de excepciones |
| El modelo multilingüe empeora en inglés | Canal adicional en RRF (no reemplazo) hasta demostrar paridad |
| Recalibración OOD (centroide denso) | Mantener los filtros actuales; recalibrar en sombra con el gold set de OOD |
| Latencia y RAM en ARM 1 OCPU | Medir antes de adoptar; reranker opcional; modelos ≤ ~0.5 GB |
| Sobreajuste al gold set | Separar desarrollo y prueba; consultas redactadas por árbitros, no por el equipo de desarrollo |
| Pérdida de evidencia al retirar reglas | Retirada por grupos con criterio bloqueante de excepciones |
| Confundir recuperación con respaldo | Tres niveles de métrica (sección 7); el respaldo solo se evalúa por juicio humano |
| Licencias de modelos | Verificar la licencia de cada candidato antes de su uso |

---

## 9. Recursos computacionales requeridos (estimaciones; verificar)

| Componente | Tamaño aproximado | Uso | Observación |
|---|---|---|---|
| MiniLM-L6 (actual) | ~90 MB | Consulta en línea | Se mantiene durante la transición |
| Denso multilingüe 384 d (candidato) | ~0.5 GB | Consulta en línea + codificación offline | Medir RAM y latencia en ARM |
| Cross-encoder multilingüe pequeño (opcional) | ~0.5 GB | 20–50 pares por consulta | Puede no caber en el presupuesto de 1 OCPU |
| Artefactos derivados nuevos | Unos pocos MB | Disco | Carpeta separada y versionada |

Con 5.8 GiB totales (≈3.8 GiB libres), un modelo adicional parece viable; dos modelos adicionales (denso + reranker) requieren medición. Las cifras de esta tabla son aproximadas y deben verificarse con los modelos concretos elegidos.

---

## 10. Archivos y componentes que se modificarían en futuras fases

- `scripts/` — nuevo constructor de sub-unidades y de índices derivados; ampliación de `eval_rre_retrieval.py`.
- `data/processed/<nueva carpeta derivada versionada>/` — sub-unidades, embeddings multilingües y BM25 (sin sobrescribir los artefactos actuales).
- `src/rre_engine.py` — canales adicionales, fusión, retirada progresiva de reglas, resolución de referencias a sub-unidad.
- `src/passage_stitcher.py` — límite y reemplazo por entrega a nivel de sub-unidad.
- `src/ood_detector.py` — recalibración con el nuevo espacio vectorial.
- `src/ada_assistant.py` — composición del contexto por sub-unidad (manteniendo la cita al `passage_id` padre y la gobernanza AUD).
- `src/corpus_config.py`, `Dockerfile`, `requirements.txt` — rutas y snapshots de modelo (solo si se aprueba un modelo nuevo).
- `tests/` — nuevos tests de cobertura de segmentación, excepciones y canales; los actuales se mantienen.

## 11. Qué debe permanecer inalterado

- `passages_candidate.json`: textos, `passage_id`, `text_sha256`, `source_sha256`.
- `knowledge_graph_candidate.json`: aristas existentes (se añaden resoluciones derivadas, no se eliminan).
- Matriz densa y meta actuales, hasta que su sustitución esté validada (convivencia versionada).
- Gobernanza AUD-01..04: separación primaria/complementaria, abstención opción A, validación de citas contra evidencia primaria entregada, ausencia de hardcodes normativos.
- La cita normativa siempre es un `passage_id` del corpus oficial; los derivados nunca son fuente normativa.

## 12. Dictamen

**APTO para iniciar la implementación de las Etapas 0 y 1** (conjunto de evaluación anotado y sub-unidades derivadas en modo sombra), porque no alteran el corpus ni la producción y son prerrequisito de cualquier mejora medible.

**NO APTO para modificar la recuperación en producción, introducir modelos nuevos en línea o retirar reglas manuales** hasta disponer del gold set anotado, de mediciones en ARM 1 OCPU y de resultados que cumplan los criterios bloqueantes de la sección 7 (sin regresión de excepciones ni de OOD).

---

### Anexo — Archivos inspeccionados (solo lectura)

`src/rre_engine.py`, `src/ada_assistant.py`, `src/response_structurer.py`, `src/document_validator.py`, `src/document_governance.py`, `src/normative_validator.py`, `src/negative_domain_anchor_scoring.py`, `src/ood_detector.py`, `src/passage_stitcher.py`, `src/normative_semantic_ranker.py`, `src/referee_command_disambiguator.py`, `src/multisource_retriever.py`, `src/rag_engine.py`, `src/llm_provider.py`, `src/corpus_config.py`; `data/processed/rebuild_2026_08_corrected/` (`passages_candidate.json`, `dense_embeddings_candidate.npy`, `dense_embeddings_meta.json`, `vector_index_candidate.json`, `knowledge_graph_candidate.json`); `docs/registro_documental_multifuente_ijf.csv`; `data/corpus_multisource/processed/multisource_passages.json`; `requirements.txt`; `Dockerfile`; `docker-compose.yml`; `docs/auditoria/auditoria_pre_deployment_oci_2026_11.md`; `docs/auditoria/despliegue_oci_3e86a08_2026_11.md`; `scripts/eval_rre_retrieval.py`; suites de `tests/`.

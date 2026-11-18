# Auditoría integral del procesamiento documental y la recuperación

**Proyecto:** IJF SOR Assistant 2026
**Fecha:** 17 de noviembre de 2026
**Tipo:** diagnóstico, solo lectura
**Rama y commit inspeccionados:** `exp/r3-dig-v2`, `d126873` (más los cambios FIX3 sin commit, que no afectan al corpus ni a los índices)

---

## 1. Resumen ejecutivo

**Dónde está el problema.** Los datos del benchmark (dev, 31 preguntas respondibles) muestran que el sistema casi siempre encuentra la evidencia: en 30 de las 31 preguntas, la página correcta aparece entre los 25 primeros resultados de al menos uno de los dos canales, el denso o el léxico. Sin embargo, solo llega a los 5 pasajes que se entregan al LLM en 18 casos (métrica estricta) o en 24 casos (contando como acierto cualquiera de los pasajes duplicados de la misma página). **La mayor parte de la pérdida ocurre después de la búsqueda: en la fusión de los dos canales y en las reglas fijas que la siguen.**

**Lo que funciona bien.**
* **Extracción del PDF:** está completa. Comparada con `pdftotext`, conserva el 99,6 % de las palabras de las páginas 12 a 298. Las pocas diferencias están en páginas de diagramas.
* **Coherencia interna:** pasajes, vectores, índice léxico y grafo coinciden en identificadores, orden y hash del documento fuente.
* **Embeddings:** los de los documentos y los de las consultas usan el mismo modelo y la misma normalización.

**Lo que falla, por gravedad:**

| # | Hallazgo | Gravedad | Estado |
|---|---|---|---|
| H‑01 | La página 9 (PRELUDE: situaciones excepcionales, Comisión Ad Hoc, enmiendas, reglas de interpretación) no está en el corpus | **CRÍTICO** | Confirmado |
| H‑02 | La unidad indexada es la página completa, no el apartado: en 53 páginas, la continuación de un apartado queda etiquetada con el apartado siguiente, y el costurado no la recupera | ALTO | Confirmado (estructura); impacto en respuestas sin medir |
| H‑03 | El modelo denso solo lee unos 256 *word pieces* (fragmentos de palabra que usa el modelo) de cada pasaje: la mayoría de las páginas son más largas | ALTO | **Hipótesis** con evidencia fuerte |
| H‑04 | La fusión RRF impide que un pasaje encontrado solo por el canal denso supere a los que aparecen en ambos canales | ALTO | Confirmado (aritmética del código) |
| H‑05 | Las reglas fijas por palabra clave desplazan la evidencia; por ejemplo, la regla de cadetes coloca la página 188 en primer lugar | ALTO | Confirmado (código y casos) |
| H‑06 | El canal denso solo funciona en inglés y el portugués no se traducía | MEDIO | Confirmado |
| H‑07 | El canal léxico es TF‑IDF sin lematización, y su tokenizador difiere del que se usó para construir el índice | MEDIO | Confirmado |
| H‑08 | Los artefactos se generaron con scripts no versionados y sin registrar la revisión del modelo | MEDIO | Confirmado |
| H‑09 | Ruido en el texto de los pasajes: encabezado repetido en cada página, números «2 .2 .1» y páginas de fotos sin texto | BAJO | Confirmado |
| H‑10 | Las tablas que continúan en otra página pierden el encabezado de columnas | BAJO | Confirmado |

**Lo que falta demostrar:**
* **Truncamiento (H‑03):** confirmarlo con el tokenizador real del modelo.
* **Corrección R1:** medir su efecto sobre H‑04; ya está preparada en FIX3.
* **Impacto de H‑02:** medir cómo afecta a las citas y al DIG.
* **Generalización:** que cualquier mejora sirva fuera de las 31 preguntas de dev.

---

## 2. Arquitectura documental encontrada

```
PDF oficial (298 págs., SHA-256 9426b10d…5ae620)
  │  pypdf 6.14.2 — texto por página física (extraction_method = pypdf_page_physical)
  ▼
data/processed/rebuild_2026_08/pages_raw/page_NNN.txt
  │  índice del PDF → structural_coverage_matrix.json (272 secciones, págs. 12–298)
  │  scratch/build_corrected_artifacts.py (no versionado)
  ▼
passages_candidate.json — 385 «pasajes» = (página × sección que la ocupa), texto = página completa
  ├─ dense_embeddings_candidate.npy  (all-MiniLM-L6-v2, 385×384, entrada = «título + página»)
  ├─ vector_index_candidate.json      (TF-IDF; scratch/rebuild_corrected_vector_index.py, no versionado)
  └─ knowledge_graph_candidate.json   (385 nodos, 68 aristas «references_article»)
        ▼
RRE.retrieve (src/rre_engine.py)
  TF-IDF top-25 (≥0,05) + denso top-25 (≥0,15) → controles de dominio/OOD
  → RRF (k=60; pesos 1,2 / 1,0; ×1,35 + 0,035 si está en ambos canales)
  → reglas fijas (palabras clave, páginas e IDs escritos en el código) → código de artículo / página
  → deduplicación por texto → [R3 ámbito] → [R1 campeones, FIX3] → top-5
  → costurado de páginas contiguas del mismo artículo (máx. 3) + 3 vecinos del grafo
```

**Configuración vigente** (`src/corpus_config.py`): edición 2026‑08, directorio `data/processed/rebuild_2026_08_corrected`. **Verifiqué que estos son los artefactos que carga el RRE:** las rutas de `ReasoningRetrievalEngine.__init__` y de `ADAAssistant.__init__` apuntan a ese directorio.

**Componentes activos en ADA:** ranking semántico normativo, desambiguación de órdenes arbitrales, detector OOD y anclas negativas. El costurado de pasajes también está activo, salvo que `RRE_ENABLE_CHUNK_STITCHING=0`.

---

## 3. Inventario de artefactos

| Artefacto | Ruta | Contenido verificado |
|---|---|---|
| PDF oficial | `data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf` | 298 páginas; versión del 14 de agosto de 2026, que sustituye a la del 24 de julio; SHA-256 `9426b10d…5ae620`, igual al de `source_manifest.json` y `corpus_config.py` |
| PDF histórico | `data/raw/ijf_sor_2026.pdf` | Edición de enero de 2026 (SHA `729b1843…`); no la usa el RRE |
| Texto por página | `data/processed/rebuild_2026_08/pages_raw/` | Extracción con pypdf 6.14.2, el 17 de octubre de 2026 |
| Matriz de secciones | `…_corrected/structural_coverage_matrix.json` | 272 secciones, de la página 12 a la 298 |
| Pasajes | `…_corrected/passages_candidate.json` | 385 registros; IDs únicos; `text_sha256` correcto en los 385; 287 páginas distintas |
| Embeddings | `…_corrected/dense_embeddings_candidate.npy` + `dense_embeddings_meta.json` | 385×384 float32; normas entre 0,99999994 y 1,0000001; sin NaN ni infinitos; el orden de `passage_ids` coincide con el de los pasajes; modelo declarado `sentence-transformers/all-MiniLM-L6-v2`, sin revisión registrada |
| Índice léxico | `…_corrected/vector_index_candidate.json` | TF‑IDF con 385 documentos y 5.214 términos; los IDs coinciden con los pasajes. **Lo reproduje exactamente** con `scratch/rebuild_corrected_vector_index.py`: mismos términos y diferencia máxima de IDF 0,0 |
| Grafo | `…_corrected/knowledge_graph_candidate.json` | 385 nodos y 68 aristas, todas de tipo `references_article`; 52 nodos tienen enlaces de salida |

**Ningún vector es idéntico a otro.** Las copias de una misma página tienen una similitud coseno de entre 0,934 y 0,987, porque cada copia lleva delante el título de una sección distinta.

---

## 4. Diagnóstico de extracción

**Método.** Extraje de nuevo todo el PDF con `pdftotext` 22.02, que es una herramienta independiente de pypdf. Para cada página comparé cuántas de sus palabras aparecen en el texto almacenado.

**Resultado:**
* **Cobertura media:** el texto almacenado contiene el 99,59 % de las palabras de `pdftotext`, en las 287 páginas indexadas.
* **Páginas por debajo del 95 %:** solo 4, todas diagramas de sorteo (226, 228, 229 y 230), con entre 36 y 61 palabras de etiquetas de casillas. No contienen normas.
* **Página 131:** sale vacía en las dos extracciones. Es una página que solo contiene una imagen.
* **Páginas de imagen:** revisé visualmente las 59, 69, 87, 91, 107, 131, 234 y 241. Son fotografías de portada o ejemplos de formularios, sin reglas en imagen.
* **Tablas:** pypdf conserva el orden de filas y celdas. Por ejemplo, en la tabla 2.2.1 de categorías de peso (p. 33), cada grupo («Senior and Junior Women», «Cadet Women under 18 years»…) aparece justo antes de sus filas.
* **Historial de versiones (págs. 259–298):** contiene texto añadido y tachado, que la extracción mezcla (por ejemplo, en la p. 290: «The decision of An athlete wins by fusen-gachi …»). El RRE lo excluye de los dos canales salvo que se pregunte por el historial (`_is_version_history_passage`) y lo atenúa ×0,40. **Es un diseño correcto.**

**Conclusión:** la extracción no pierde ni altera información normativa en las páginas que procesa. El único problema es de cobertura: las páginas 1 a 11 no se procesan (H‑01).

---

## 5. Diagnóstico de pasajes

**Cómo se construyen** (`scratch/build_corrected_artifacts.py`): por cada sección de la matriz, y por cada página entre su inicio y su fin, se crea un registro `SOR-2026-08-P{página}-S{sección}` cuyo texto es **la página completa**. `source_span.method` vale `full_page_text` en los 385 registros. No hay ningún recorte por apartado.

**Consecuencias medidas:**
* **Duplicados:** en 60 páginas conviven entre 2 y 7 registros con exactamente el mismo texto (98 copias de más). Solo cambian `article_id` y `heading_path`. El RRE elimina los textos repetidos al formar el top‑5, así que la duplicación casi no ocupa posiciones; la Fase 11 midió 9,7 páginas distintas de media en el top‑10. Su efecto principal fue sobre la medición: la métrica estricta frente a la que cuenta las copias como equivalentes.
* **Continuidad entre páginas:** en **53 páginas**, el texto anterior al primer encabezado (al menos 25 palabras) es la continuación del apartado de la página anterior, pero el registro solo lleva la etiqueta del apartado nuevo. Ejemplos:
  * **p. 45:** 306 palabras de **2.7.1** (equipos mixtos), etiquetadas solo como **2.7.2** (equipos femeninos y masculinos);
  * **p. 15:** 239 palabras de 1.2.1, etiquetadas como 1.2.2;
  * **p. 55:** contiene la regla de 3.2.3 que espera CAT‑007 («At Grand Prix Cadets events only the two (2) best…»), pero sus registros son 3.3 y 3.3.1.
* **Costurado** (`PassageStitcher.stitch_evidence`): solo une páginas contiguas con el mismo `article_id` y el mismo encabezado. Por eso, al recuperar la p. 44 (2.7.1), **no se añade el final del apartado**, que está en la p. 45, etiquetada como 2.7.2. Además, los 20 registros con artículo `GENERAL` nunca se cosen.
* **Ruido:**
  * 369 de 385 registros empiezan con el encabezado repetido de cada página («Sport and Organisation Rules…» y «page - N»);
  * 11 registros tienen menos de 80 caracteres (portadas o fotos) y uno está vacío (P131‑S171);
  * los números de apartado aparecen como «2 .2 .1».
* **Lo que se conserva bien:** con texto de página completa, las excepciones de un mismo apartado y página viajan junto a la regla. La Fase 11 observó que, en dev, la excepción estaba en el mismo pasaje en todos los casos salvo EXC‑003.

---

## 6. Diagnóstico de embeddings

| Aspecto | Encontrado | Fuente |
|---|---|---|
| Modelo | `sentence-transformers/all-MiniLM-L6-v2` | `dense_embeddings_meta.json`; comprobación de `rre_engine.py:333` |
| Revisión | **No registrada.** Se usa la primera instantánea local (`glob(...snapshots/*)[0]`) | `build_corrected_artifacts.py`; `rre_engine.py:394-412` |
| Biblioteca | `sentence_transformers.SentenceTransformer` (`local_files_only=True`) | ídem |
| Dimensión | 384 | `.npy` |
| Normalización | `normalize_embeddings=True` en documentos y consultas; similitud por producto escalar (coseno) | `build_corrected_artifacts.py:178`; `_dense_search` |
| Almacenamiento | `.npy` float32 en memoria; búsqueda exhaustiva, sin índice aproximado | `rre_engine.py` |
| Texto embebido | `f"{título} {página completa}"` | `build_corrected_artifacts.py:174-178` |
| Consulta | `encode(query)` y, además, `encode(proyección ES→EN por diccionario)`; se toma el máximo de las dos similitudes | `_dense_search` |
| Idioma del modelo | Inglés | ficha del modelo |

**Compatibilidad entre documentos y consultas:** es correcta. Usan el mismo modelo, la misma normalización y la misma métrica. No se encontraron vectores nulos, duplicados exactos ni filas desalineadas.

**Límite de longitud (H‑03).** Según la ficha pública del modelo en Hugging Face, las entradas de más de 256 *word pieces* se truncan por defecto, y el entrenamiento limitó las entradas a 128 tokens.

Sin el tokenizador real (no está instalado en la VM y no se instaló nada), estimé la longitud contando palabras y signos. Cada uno es al menos un *word piece*, así que es una **cota inferior**:
* **287 de 385 pasajes** superan esa cota, es decir, se truncan con seguridad. La mediana es de 457 unidades.
* Alrededor del **46 % del texto** del corpus queda por encima de la unidad 254.

**Evidencia histórica** (Fase 11, dev, forma LLM; posición del fragmento esperado dentro del texto embebido):

| Posición del fragmento esperado | El canal denso lo encuentra (top‑25) |
|---|---|
| Antes de la unidad 200 | **12 de 12** |
| Desde la unidad 200 | **10 de 19** |

* Los 9 fallos del canal denso tienen la evidencia **a partir de la unidad 313**: EXC‑009 (313), MLG‑002 (325), MUL‑004 (325), SCO‑022 (344), EXC‑003 (389), SCO‑021 (391), DIR‑017 (491), SCO‑013 (601) y SCO‑014 (614).
* CAT‑003, con la evidencia en la unidad 507, sí aparece en el canal denso, pero solo en el puesto 14.
* El TF‑IDF, que no trunca, encuentra 18 de esos 19.

**Es una correlación, no una prueba.** Sigue siendo hipótesis hasta tokenizar con el tokenizador del modelo y leer `max_seq_length` en `sentence_bert_config.json` de la instantánea local.

---

## 7. Diagnóstico del índice vectorial

* **Correspondencia exacta** con el corpus: 385 documentos, los mismos IDs y el mismo SHA del documento fuente.
* **Índice léxico:** se construyó con su propio tokenizador:
  * conserva los guiones («hansoku-make») y añade sus partes;
  * elimina tildes, pero no la «ñ»;
  * usa una lista corta de 50 palabras vacías;
  * añade sinónimos español → inglés al construir;
  * incluye el encabezado de sección en páginas de 100 caracteres o más.
* **Tokenizador de las consultas** (`_tokenize`): usa otra lista de palabras vacías (`STOPWORDS` de `src`), sustituye la «ñ», aplica la expansión ontológica y elimina términos genéricos.
* **Efecto de la diferencia:** es moderado, porque un término de la consulta que falta en el índice no puede coincidir con nada. Aun así, impide asegurar que una consulta y un documento tokenizan igual las mismas palabras. Además, los códigos con puntos («2.2.1») se parten y los dígitos sueltos se descartan, así que **los códigos de artículo solo se comparan por los metadatos** (`enable_code_matching`), no por el texto.
* **Índice denso:** búsqueda exhaustiva sobre 385 vectores (≈0,6 MB), sin pérdida por aproximación.

---

## 8. Diagnóstico de recuperación (RRE)

### 8.1 Fusión (H‑04)

Puntuación RRF de `retrieve()`:
* **Canal léxico:** 1,2 / (60 + puesto).
* **Canal denso:** 1,0 / (60 + puesto).
* **Pasaje presente en ambos canales:** (suma + 0,035) × 1,35.
* **Pasaje solo léxico con puntuación TF‑IDF ≥ 0,20:** suma + 0,035.

De ahí se sigue, aritméticamente:
* **Pasaje solo denso**, en el mejor caso (puesto 1): 1/61 = **0,0164**.
* **Pasaje en ambos canales**, en el peor caso (puesto 25 en los dos): (1,2/85 + 1/85 + 0,035) × 1,35 = **0,0822**.
* **Pasaje solo léxico** (puesto 25, puntuación ≥ 0,20): **0,0491**. Incluso sin bonificación, un pasaje léxico supera al primero del denso hasta el puesto 13.

**Consecuencia:** un pasaje que solo encuentra el canal denso queda por debajo de **cualquier** pasaje presente en los dos canales, aunque sea el primero del denso. Eso explica SCO‑019 y SCO‑020: el canal denso sitúa la p. 75 en 1.º–2.º, el léxico no la encuentra, y en la salida final queda en el puesto 10.

### 8.2 Reglas fijas (H‑05)

* `rre_engine.py` contiene **18 IDs de pasaje distintos** escritos a mano, varias decenas de detectores por palabra clave y rangos de páginas con multiplicadores. Por ejemplo, ×0,20 a las páginas 115–127, 137–151 y 250–275 en consultas sobre agarres.
* **La regla de cadetes es la más clara.** Cualquier consulta con «cadet», «cadete» o «u18» añade P188‑S196 (técnicas de cabeza en cadetes) con +0,035 y +0,18, **aunque la pregunta no trate de la cabeza**. En el historial de la Fase 11, la p. 188 aparece **primera** en CAT‑003 (cinturón de kata U18), CAT‑007 (puntos WRL en el Grand Prix de cadetes) y SCO‑019 (tolerancia de peso de cadetes).
* **Matiz:** la Fase 11 midió que, quitando todas las reglas (variante R1 de esa fase), el benchmark empeora: R@5 baja de 0,774 a 0,661–0,677. **Las reglas ayudan en dev**, pero su generalización no está demostrada y algunas desplazan evidencia (5 de 31 casos se clasifican como `DESPLAZADO_POR_REGLAS_FIJAS`).

### 8.3 Idioma y vocabulario (H‑06, H‑07)

* **Canal denso:** solo funciona en inglés.
* **Traducción con LLM:** en la forma LLM de la Fase 11, la consulta en portugués de MLG‑002 llegó **sin traducir**, porque el portugués no siempre se detecta. La corrección R2 (`ADA_TRANSLATE_ANY_LANG`) de FIX3 lo aborda, pero **no se ha medido**.
* **Proyección por diccionario:** deja palabras en español en la consulta, como «tienen» y «oficial» en «tolerance weight tienen cadet weigh-in official random oficial».
* **Canal léxico:** sin lematización ni BM25. EXC‑003 pregunta con «enter/entered», mientras que la regla dice «entries/inscribe»; el TF‑IDF la deja en el puesto 19.

---

## 9. Resultados cuantitativos disponibles

**Fuentes:**
* `data/eval/fase11/diag_retrieval_dev.json`: métrica estricta, con el ID exacto del pasaje.
* `data/eval/fase11/retrieval_experiments_dev.json`: cuenta como equivalentes los pasajes duplicados de la misma página.

Las dos son de dev: 31 preguntas respondibles y benchmark_v2. R0 es la configuración de producción, top‑10, sin grafo.

| Métrica (dev, 31) | Estricta DICT | Estricta LLM | Equivalencia DICT | Equivalencia LLM |
|---|---|---|---|---|
| Recall@5 | 0,581 | 0,581 | **0,774** | **0,774** |
| Recall@10 (hit@10) | 0,613 | 0,645 | 0,806 | 0,871 |
| MRR | 0,403 | 0,413 | 0,536 | 0,581 |
| Recall@20 | no disponible: los registros guardan el top‑10, y en los canales solo el puesto hasta el 25 | | | |

**Por canal** (puesto del pasaje esperado dentro del top‑25 de cada canal, métrica estricta):

| | DICT | LLM |
|---|---|---|
| Denso en el top‑25 / top‑5 | 22 / 13 | 22 / 17 |
| TF‑IDF en el top‑25 / top‑5 | 27 / 19 | 28 / 21 |
| En al menos un canal (top‑25) | **30** | **30** |
| En los dos canales | 19 | 20 |

**Dónde se pierde la evidencia** (atribución de la Fase 11, forma LLM, estricta):

| Atribución | Casos |
|---|---|
| En el top‑5 | 18 |
| En un canal, pero fuera del top‑5 tras la fusión | 7 |
| Desplazada por reglas fijas | 5 |
| Ausente de los dos canales | 1 (MLG‑002) |

**Preguntas sin evidencia pertinente** (equivalencia, LLM): **22,6 %** fuera del top‑5 (7 de 31) y **12,9 %** fuera del top‑10 (4 de 31).

**Recuperación frente a generación y validación** (`AUDITORIA_TRAZABILIDAD_RRE_GEMINI_DIG.md`; 8 corridas):
* **Causas de los rechazos** de las 83 respuestas a preguntas respondibles: 60,2 % el DIG, 32,5 % la recuperación (22 por fusión o selección y 5 por recuperación incompleta) y 7,2 % la generación.
* **Preguntas nunca aceptadas por la recuperación:** EXC‑003, MLG‑002, SCO‑013, SCO‑014, SCO‑019 y SCO‑020. En ellas, el DIG rechazó **con razón**.

**Datos que no utilicé:** `data/eval/benchmark_v2/results/retrieval_all.json` mezcla dev con el conjunto sellado. No abrí `test_sealed.jsonl`.

---

## 10. Casos problemáticos reconstruidos

**Notas sobre las columnas:**
* **Unidad del fragmento:** posición estimada de la evidencia dentro del texto embebido (cota inferior en *word pieces*).
* **Consultas:** las que se usaron en la corrida de la Fase 11. **No se ejecutó ninguna recuperación nueva**, porque el modelo denso no está disponible en la VM.

| Caso | Pregunta | Pasaje esperado | Denso (puesto) | TF‑IDF (puesto) | Final R0 | Unidad del fragmento | Dónde se pierde |
|---|---|---|---|---|---|---|---|
| **SCO‑019** | «¿Qué tolerancia de peso tienen los cadetes en el pesaje oficial?» (LLM: «cadets official weigh-in weight tolerance») | 6.1, p. 75 («…an additional 0.2 kg will be allowed») | **1** | — | 10 | 104 | **Fusión** (H‑04) y **regla de cadetes**: P188 queda primera (H‑05) |
| **SCO‑020** | «Do senior athletes get any weight tolerance at the official weigh-in…?» | 6.1, p. 75 («there is no additional weight tolerance») | **2** | — | 10 | 62 | **Fusión** (H‑04): los pasajes de pesaje presentes en los dos canales la superan |
| **SCO‑013** | «What are the dimensions of the competition area at a World Kata Championships?» | B1.8, p. 112 («10 m x 10 m for world championships») | — | 17 | >10 | 601 | **Canal denso** (truncamiento probable, H‑03) y TF‑IDF bajo; distractor de ámbito: el área general (8.7) |
| **SCO‑014** | «¿Qué medidas tiene el área de competición de kata en un evento que no es campeonato del mundo?» | B1.8, p. 112 («8 m x 8 m for other events») | — | 14 | >10 | 614 | Igual que SCO‑013 |
| **EXC‑003** | «Can the IJF enter an athlete who is not entered by a national federation?» | 4.2, p. 61 (regla y excepción «the IJF can, to protect an athlete's career, inscribe…») | — | 19 | >10 | 389 / 409 | **Vocabulario** (H‑07) y **canal denso** (H‑03) |
| **MLG‑002** | «Quantos atletas compõem uma equipa mista?» | 2.7.1, p. 42 («six (6) athletes (3 women and 3 men)») | — | — | >10 | 325 | **Idioma**: sin traducción y con un modelo solo en inglés (H‑06); la evidencia también está fuera de la ventana (H‑03) |
| **CAT‑003** | «¿Puede una pareja U18 de kata usar un cinturón verde?» | B1.12, p. 113 («A green, blue or brown belt … authorised for the U18 age group») | 14 | 2 | >10 estricta; 2 (LLM) y 4 (DICT) con equivalencia | 507 | Llega una copia equivalente de la p. 113 (4 secciones duplicadas, H‑02), pero la **regla de cadetes** coloca P188 primera (H‑05); canal denso débil (H‑03) |
| **CAT‑007** | «At a Grand Prix Cadets, how many athletes per country…?» | 3.2.3, p. 55 | 2 | 1 | 2 | 22 | **No se pierde** (está en el top‑5), pero P188 queda primera por la regla de cadetes, y el pasaje de la p. 55 lleva la etiqueta **3.3**, no 3.2.3 (H‑02) |

**Ningún caso pierde la evidencia por la extracción.** En todos, el texto esperado está literalmente en el pasaje almacenado: los fragmentos de referencia del benchmark están verificados contra él.

---

## 11. Hallazgos clasificados por gravedad

### H‑01 · CRÍTICO · La página 9 no está en el corpus
* **Evidencia:**
  * la matriz y los pasajes empiezan en la p. 12;
  * la p. 9 (PRELUDE) contiene normas reales: «Exceptional Situations» (los casos no previstos los resuelve el Comité Ejecutivo; composición de la Comisión Ad Hoc), «Amendment to the SOR», la interpretación del género y del término «national federation», y la confidencialidad de los formularios del apéndice F;
  * las páginas 1–8 son portada e índice, y las 10–11 son enlaces y contactos.
* **Archivos:** `structural_coverage_matrix.json`, `scratch/build_corrected_artifacts.py` (la matriz se genera a partir del índice del PDF y empieza en «GENERAL INFORMATION»).
* **Caso:** ninguno en dev; no es medible con el benchmark actual.
* **Impacto:** preguntas sobre situaciones no previstas, la Comisión Ad Hoc o la definición de «national federation» no pueden responderse con evidencia. El sistema se abstiene o usa otro pasaje.
* **Causa:** confirmada.
* **Recomendación:** con autorización, añadir la p. 9 como pasaje en una copia experimental del corpus y añadir preguntas sobre ella al benchmark v3.

### H‑02 · ALTO · La unidad indexada es la página, no el apartado
* **Evidencia:**
  * 385 registros con el texto de la página completa;
  * 60 páginas con copias idénticas;
  * 53 páginas que empiezan con la continuación del apartado anterior, etiquetada con el siguiente;
  * el costurado no cruza a otro apartado.
* **Archivos:** `scratch/build_corrected_artifacts.py`, `PassageStitcher.stitch_evidence`.
* **Casos:** CAT‑007 (p. 55 etiquetada 3.3); final de 2.7.1 (equipos mixtos) en la p. 45, etiquetada 2.7.2; CAT‑003 (4 copias de la p. 113).
* **Impacto:**
  * el paquete puede omitir el final de un apartado;
  * el `article_id` que se muestra o se cita puede no corresponder al texto pertinente, lo que puede producir citas mal atribuidas y errores de ámbito (**hipótesis de impacto, sin medir**);
  * la duplicación sesga la medición: R@5 de 0,581 a 0,774 según la regla de equivalencia.
* **Causa:** confirmada (estructura).
* **Recomendación:** no fragmentar por tamaño. Evaluar en experimental una unidad de **apartado completo** con su continuación entre páginas, por ejemplo usando `data/derived/article_units_v1` (372 unidades) con un ordenamiento distinto del que se descartó en la Fase 11 (R2). Como paso intermedio, que el costurado añada el texto previo al primer encabezado de la página siguiente.

### H‑03 · ALTO · Truncamiento del canal denso (hipótesis)
* **Evidencia:** 287 de 385 pasajes superan la cota de 256 *word pieces*; correlación 12/12 frente a 10/19; los 9 fallos densos tienen la evidencia a partir de la unidad 313.
* **Archivos:** `build_corrected_artifacts.py` (codifica el título y la página completa), `_dense_search`.
* **Casos:** SCO‑013, SCO‑014, EXC‑003, MLG‑002, CAT‑003.
* **Impacto:** el canal denso solo «ve» el principio de cada página. Las reglas de la mitad inferior dependen solo del TF‑IDF.
* **Causa:** hipótesis pendiente.
* **Recomendación:** prueba T1 (§13). Si se confirma, codificar cada página en ventanas (por ejemplo, de 200 *word pieces* que se solapen dentro del apartado) y quedarse con la mayor similitud. Eso conserva el mismo pasaje y el mismo modelo. Solo en una caché experimental.

### H‑04 · ALTO · La fusión penaliza la evidencia que solo encuentra el canal denso
* **Evidencia:** aritmética de §8.1; SCO‑019 y SCO‑020 (puesto 1–2 en el denso y 10 al final).
* **Archivo:** `ReasoningRetrievalEngine.retrieve` (RRF y bonificación multicanal).
* **Impacto:** 7 de 31 preguntas tienen la evidencia en un canal pero fuera del top‑5.
* **Causa:** confirmada.
* **Recomendación:** medir R1 (`RRE_CHANNEL_CHAMPIONS`, ya implementada y desactivada) con `scripts/eval_r1_channel_champions.py` en el PC, sin LLM.

### H‑05 · ALTO · Reglas fijas que desplazan evidencia
* **Evidencia:** 18 IDs escritos a mano; la regla de cadetes coloca P188 primera en CAT‑003, CAT‑007 y SCO‑019; 5 de 31 casos `DESPLAZADO_POR_REGLAS_FIJAS`.
* **Archivo:** `retrieve()`, bloques de cabeza, cadetes, conducta, agarres y equipamiento.
* **Impacto:** en otras consultas de cadetes (pesaje, WRL, kata) se entrega una regla de técnicas de cabeza en primer lugar.
* **Causa:** confirmada.
* **Recomendación:**
  * no quitar las reglas en bloque: la Fase 11 midió que ayudan en dev;
  * medir por separado una variante en la que la regla de cadetes solo se active si la consulta menciona la cabeza o una técnica (ablación T5);
  * a largo plazo, sustituir las reglas por señales genéricas medidas.

### H‑06 · MEDIO · Idioma
* **Evidencia:** modelo solo en inglés; MLG‑002 sin traducir en la forma LLM; la proyección por diccionario deja palabras en español.
* **Archivos:** `ADAAssistant._translate_to_technical_english`, `_dense_search`.
* **Caso:** MLG‑002 y los 12 casos en español.
* **Causa:** confirmada.
* **Recomendación:** medir R2 (FIX3). Para el modo sin LLM, evaluar un modelo multilingüe solo como canal adicional de candidatos (ver §7 de la orden y §12).

### H‑07 · MEDIO · Canal léxico
* **Evidencia:** TF‑IDF sin lematización; tokenizadores distintos al indexar y al consultar; EXC‑003 en el puesto 19 («enter» frente a «entries»).
* **Archivos:** `scratch/rebuild_corrected_vector_index.py`, `_tokenize` y `_sparse_search`.
* **Causa:** confirmada.
* **Recomendación:** unificar el tokenizador del índice y de las consultas en un módulo versionado; evaluar BM25 con lematización inglesa como variante del canal.

### H‑08 · MEDIO · Procedencia no reproducible
* **Evidencia:**
  * los artefactos vigentes se generaron con `scratch/build_corrected_artifacts.py` y `scratch/rebuild_corrected_vector_index.py`, ninguno versionado (`??` en git);
  * la revisión del modelo no consta;
  * el extractor registrado es pypdf 6.14.2, mientras que la VM tiene la 6.21.2.
* **Impacto:** no se puede regenerar el corpus con garantía de obtener los mismos vectores, ni demostrar que la consulta usa la misma instantánea del modelo que los documentos.
* **Causa:** confirmada.
* **Recomendación:** versionar los scripts de construcción y registrar en `dense_embeddings_meta.json` la revisión del modelo, `max_seq_length`, la plantilla de entrada y el hash del texto codificado.

### H‑09 · BAJO · Ruido en el texto embebido
* **Evidencia:** encabezado repetido en 369 pasajes; «2 .2 .1»; 11 pasajes de menos de 80 caracteres y 1 vacío.
* **Impacto:** el encabezado consume, por estimación, unos 15 *word pieces* de la ventana densa. Los pasajes casi vacíos pueden aparecer como candidatos por su título. El impacto no está demostrado.
* **Recomendación:** limpiar el encabezado y la paginación solo en el texto que se embebe, no en el texto citado.

### H‑10 · BAJO · Tablas que continúan en otra página
* **Evidencia:** en la p. 255 (códigos de sanción G1.3), la continuación no repite los nombres de las columnas.
* **Impacto:** no demostrado.
* **Recomendación:** que el costurado una las páginas de una misma tabla, o anteponer el encabezado de la tabla.

**Componentes revisados sin hallazgos:**
* la exclusión del historial de versiones;
* la integridad de hashes y de IDs;
* la normalización de los vectores;
* el grafo, que es pequeño: 68 aristas y un solo tipo de relación;
* el alineamiento entre `passage_ids` y las filas del `.npy`.

---

## 12. Recomendaciones priorizadas

Ninguna se aplica sin autorización; todas se miden primero en experimental.

1. **Confirmar H‑03** (T1). Es barato y decide el resto: si el truncamiento es real, la ventana densa es la mejora con mayor alcance.
2. **Medir R1** (H‑04), ya implementada; requiere el PC.
3. **Incorporar la p. 9** (H‑01) en una copia experimental y añadir preguntas al benchmark v3.
4. **Ablación de la regla de cadetes** (H‑05) y, después, del resto de reglas, una a una.
5. **Continuidad entre páginas** (H‑02): costurado del texto previo al primer encabezado de la página siguiente.
6. **Reproducibilidad** (H‑08): versionar los scripts de construcción y ampliar los metadatos.
7. **Canal léxico** (H‑07): tokenizador único y variante BM25 con lematización.
8. **Comparación de modelos:** solo después de 1 a 5, con el protocolo de §13 (T7). En el estado actual, un cambio de modelo mezclaría su efecto con el del truncamiento y la fusión.

**Viabilidad de la comparación de modelos** (sin descargar ni ejecutar nada):

Datos tomados de las fichas públicas de cada modelo en Hugging Face (consultadas el 17 de noviembre de 2026):

| Modelo | Longitud máxima | Dimensión | Idiomas | Requisitos de uso |
|---|---|---|---|---|
| all-MiniLM-L6-v2 (actual) | 256 *word pieces*; entrenado con 128 | 384 | Inglés | — |
| `BAAI/bge-m3` | 8.192 tokens | 1.024 | Más de 100 | Sin instrucciones en la consulta; ofrece recuperación densa, léxica y multivector |
| `intfloat/multilingual-e5-large` | 512 tokens (los textos más largos se truncan) | 1.024 | Unos 100 (la ficha dice 94 en otra parte) | Cada entrada debe empezar por «query: » o «passage: »; omitirlos degrada el rendimiento |

* **bge-m3:** su longitud permitiría embeber una página completa sin truncar. Eso, por sí solo, ya pondría a prueba H‑03.
* **e5-large:** truncaría las páginas que superen 512 tokens (el número hay que medirlo con su tokenizador) y exige los prefijos.
* **Recursos:** ambos son modelos grandes comparados con MiniLM. Antes de llevarlos a OCI hay que medir la memoria y la latencia.
* **Antecedente:** la Fase 11 ya probó un modelo multilingüe pequeño (`paraphrase-multilingual-MiniLM-L12-v2`, también con 256 *word pieces*, en fusión 1:1). Subió hit@10 a 0,935, pero perdió entre 3 y 4 preguntas del top‑5 y no resolvió el portugués.

---

## 13. Plan de pruebas para validar posibles correcciones

**Reglas comunes a todas las pruebas:**
* mismos 385 pasajes, salvo en T3;
* mismas preguntas: dev 31 respondibles + 10 no respondibles, y después benchmark v3;
* mismo DIG y sin LLM en las pruebas de recuperación;
* métricas estricta y por equivalencia, por canal y final: R@5, R@10, MRR, puesto del pasaje esperado, distractor de ámbito por encima de la evidencia, y abstenciones legítimas sin cambios;
* criterio: no perder ninguna pregunta que ya se resolvía, o justificar cada pérdida caso por caso;
* el conjunto sellado solo al final.

| Prueba | Qué valida | Cómo |
|---|---|---|
| **T1** | Truncamiento (H‑03) | En el PC, con el modelo ya en caché: leer `max_seq_length`; tokenizar los 385 textos embebidos y los fragmentos de referencia; comparar el puesto denso frente a la posición en tokens. Variante: ventanas por página con similitud máxima, en una caché experimental |
| **T2** | Fusión (H‑04) | `scripts/eval_r1_channel_champions.py` con y sin `RRE_CHANNEL_CHAMPIONS` |
| **T3** | Página 9 (H‑01) | Copia experimental del corpus con la p. 9; preguntas nuevas sobre situaciones excepcionales, Comisión Ad Hoc y «national federation»; comprobar que no altera las demás |
| **T4** | Continuidad (H‑02) | Costurado del texto previo al primer encabezado; medir si el paquete contiene el apartado completo y si el `article_id` citado coincide con el fragmento esperado |
| **T5** | Regla de cadetes (H‑05) | Ablación de esa regla sola; dev + preguntas nuevas de cadetes (pesaje, WRL, kata, técnicas de cabeza) |
| **T6** | Idioma (H‑06) | R2 (FIX3) con consultas pt, fr y es; puesto en cada canal antes y después de traducir |
| **T7** | Modelos | Sustituir solo el canal denso (mismos pasajes, misma fusión, mismas reglas). Medir primero el recall del canal en el top‑25 (aislado) y después el resultado final. Con e5, usar prefijos; con bge‑m3, comparar con y sin truncamiento. Registrar memoria, carga y latencia por consulta. Repetir sobre unidades de apartado si T4 lo justifica |

---

## 14. Conclusión

**Dónde está realmente el problema.** No en la extracción del PDF: es completa y fiel en las páginas que procesa. El problema está en **cómo se ordena lo que ya se ha encontrado**:
* la fusión RRF castiga la evidencia que solo encuentra un canal (H‑04);
* las reglas fijas desplazan evidencia válida (H‑05);
* el canal denso probablemente solo ve el principio de cada página (H‑03, por confirmar).

A eso se suman dos decisiones de diseño del corpus:
* la unidad es la página y no el apartado, lo que corta la continuidad y confunde los metadatos (H‑02);
* una página con normas (la 9) quedó fuera (H‑01).

**Qué falta demostrar:**
1. Que el truncamiento es real, con el tokenizador del modelo (T1).
2. El efecto de R1 (T2) y de la ablación de la regla de cadetes (T5).
3. El impacto de H‑02 sobre las citas y el DIG (T4).
4. Que cualquier mejora generaliza fuera de dev, con el benchmark v3 y el conjunto sellado al final. Dev tiene 31 preguntas: una diferencia de 0,03 en R@5 es una sola pregunta.

**Recomendación sobre el modelo:** no hay evidencia suficiente para recomendar un cambio. Debe compararse solo después de corregir o descartar H‑03 y H‑04 y con el protocolo T7.

---

## Anexo A. Archivos inspeccionados

**Código:**
* `src/corpus_config.py`, `src/rre_engine.py`, `src/passage_stitcher.py`
* `src/ada_assistant.py`: solo la construcción del RRE

**Scripts de construcción** (no versionados):
* `scratch/build_corrected_artifacts.py`
* `scratch/rebuild_corrected_vector_index.py`

**Datos:**
* `data/raw/sor_2026_08_rebuild/` (PDF y manifiesto), `data/raw/ijf_sor_2026.pdf` (solo el hash)
* `data/processed/rebuild_2026_08_corrected/*`
* `data/processed/rebuild_2026_08/` (listado)

**Benchmark y resultados:**
* `data/eval/benchmark_v2/splits/dev.jsonl`
* `data/eval/fase11/diag_retrieval_dev.json`, `data/eval/fase11/retrieval_experiments_dev.json`
* `data/eval/benchmark_v2/results/retrieval_all.json`: solo su estructura; no usado para métricas

**Informes:**
* `docs/audits/FASE_11_RECUPERACION_EXPERIMENTAL.md`
* `docs/audits/AUDITORIA_TRAZABILIDAD_RRE_GEMINI_DIG.md`
* `docs/audits/INFORME_INTERVENCION_RECUPERACION_GENERACION_DIG11.md`

**Fichas públicas de los modelos** (Hugging Face): all-MiniLM-L6-v2, bge-m3 y multilingual-e5-large.

## Anexo B. Pruebas ejecutadas (todas locales y de solo lectura)

1. Inventario y consistencia: hashes, IDs, orden, normas, NaN, duplicados y vectores idénticos.
2. Reconstrucción en memoria del IDF del índice léxico con el script de construcción: coincidencia exacta.
3. Extracción independiente con `pdftotext` y comparación de palabras por página.
4. Inventario de imágenes (`pdfimages -list`) y revisión visual de 8 páginas con imagen. Las representaciones de baja resolución se guardaron en `deploy/exp/out/aud_img/`, que el paquete de despliegue excluye.
5. Análisis de la estructura de pasajes: duplicados, continuidad entre páginas y longitudes.
6. Posición de los fragmentos esperados frente al puesto en cada canal, con los datos de la Fase 11.
7. Lectura de la fusión, las reglas fijas y el costurado en el código.

**Lo que no se hizo:**
* no se modificó código ni corpus;
* no se regeneraron embeddings, índices ni pasajes;
* no se descargaron modelos ni se instalaron dependencias;
* no hubo llamadas a Gemini, Groq ni otros proveedores;
* no hubo operaciones en OCI;
* no se hizo commit, push, stash ni despliegue.

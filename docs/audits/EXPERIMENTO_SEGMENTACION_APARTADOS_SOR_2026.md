# Experimento: recuperación por apartados normativos (SOR 2026-08) — 2026-11-17

**Alcance:** experimento local, sin LLM y sin red, sobre el split DEV leído desde `dev.jsonl`; `test_sealed` no se abrió. No se modificaron `src/`, `data/processed/`, `data/derived/`, el benchmark, el DIG ni los interruptores.
**Base:** rama `exp/r3-dig-v2`, HEAD `d126873`, con FIX3 sin commit. R3 estaba desactivado.
**Carpeta:** `experiments/segmentacion_apartados_2026/`. Todo es reproducible con tres órdenes:
`python experiments/segmentacion_apartados_2026/build_sections.py` → `eval_sections.py` → `diag_sco020.py`.

---

## 1. Auditoría de la estructura

| Elemento | Resultado |
|---|---|
| PDF oficial | 298 páginas, con un esquema interno (TOC) de 272 entradas. SHA‑256 `9426b10d…ae620`, que coincide con el declarado en los índices |
| Corpus `passages_candidate.json` | 385 pasajes sobre 287 páginas (de la 12 a la 298). **Faltan las páginas 1 a 11**; esto confirma y amplía H‑01 |
| Unidad real del pasaje | **La página completa.** Los 158 pasajes que comparten página tienen el mismo `text_original` y solo difieren en `article_id` y `heading_path` (H‑02) |
| Pasajes por página | 1 en 227 páginas, 2 en 39, 3 en 11, 4 en 6, 5 en 2, 6 en 1 y 7 en 1 |
| Metadatos | Los 385 tienen `review_status=extracted` y `approved_by=null`. No hay ninguna incoherencia `article_id`/`heading_path` dentro de un pasaje |
| Página vacía | p. 131 (`P131-S171`, C1.14.2): `text_original` vacío; ninguna unidad puede contenerla |
| Segmentación previa (Fase 8, `data/derived/article_units_v1`) | 258 segmentos ARTICLE, 171 CONTINUATION (63 enlazados solo por página) y 16 portadas. **Corta por página: no une los apartados que continúan en la página siguiente.** Avisos de Fase 8: 63 continuaciones sin `article_id` en los metadatos de su página, 5 encabezados de metadatos no encontrados y 3 encabezados fuera de los metadatos |
| Caso de la p. 80 | El pasaje lleva el metadato de 6.4, pero la página abre con la tabla 6.3.4. Es la continuación de 6.3.4, como ya registraba la Fase 8 |

## 2. Diseño del segmentador experimental

El segmentador está en `build_sections.py`. Es determinista y genérico: ninguna regla depende de una pregunta, un pasaje o un artículo concretos.

1. **Apartado:** empieza en cada segmento ARTICLE de `article_units_v1` y **absorbe los CONTINUATION consecutivos con el mismo rótulo, aunque estén en páginas posteriores.**
2. **Jerarquía:** se deduce de la numeración (6.3.4 → 6.3 → 6). El padre es el apartado existente más cercano.
3. **Tablas:** se detecta un bloque de 3 o más líneas‑fila, cada una con al menos 2 números, densidad numérica ≥ 0,15 por palabra y sin cierre de frase. El título son las líneas‑etiqueta inmediatamente anteriores, hasta 3.
   * La tabla se separa del texto del apartado y se guarda como **unidad propia**, vinculada en el grafo a su apartado (`has_table`/`table_of`).
   * También se vincula a los apartados que la citan por su título («see table: X», «refer to table N: X»): `references_table`. Si el título se repite, solo se enlaza la tabla más cercana en el documento; esto evita enlazar las copias del historial H1.1.
4. **Texto:** concatenación literal de cortes de página, sin las cabeceras de página. Cada unidad guarda `source_spans` (página, inicio y fin), verificados byte a byte.
5. **Campos de cada unidad:**
   * rótulo y título;
   * texto completo;
   * `pdf_page_index` (página inicial) y `page_end`;
   * `parent_label` y `parent_unit_id`;
   * `original_passage_ids` (pasajes con el mismo `article_id`) y `page_passage_ids`;
   * `article_unit_ids` de la Fase 8;
   * `table_unit_ids` y `referenced_by`.

**Validación de la segmentación** (`build_report.json`):

| Comprobación | Resultado |
|---|---|
| Unidades | 342: 258 APARTADOS, 68 TABLAS y 16 PORTADAS |
| Apartados de varias páginas | 80. Distribución: 178 de 1 página, 58 de 2, 12 de 3, 4 de 4, 1 de 5 y 5 de 6 o más (H1.1 llega a 40 páginas) |
| Spans literales | verificados, sin solapes, con una cobertura del cuerpo del 100 % de `article_units_v1` |
| Contraste con el esquema interno del PDF | 256 de 258 apartados figuran en él, todos con **la misma página inicial**. Todas las entradas numeradas del esquema tienen su apartado |
| Trazabilidad | 364 de 385 pasajes tienen una unidad precisa (mismo `article_id`). Otros 20 son trazables solo por página, y P131 está vacía |
| Tablas | 68, de las cuales 57 tienen título. 31 de 39 referencias quedan resueltas; las 8 restantes son referencias cortadas por el salto de línea |
| Tokens por unidad | Mediana 166 y p90 646. El 36,3 % supera los 256 (frente al 76,4 % de las páginas). Máximo: H1.1, con 16 368 |

**Índice experimental** (`index/`, en el mismo formato que lee `ReasoningRetrievalEngine`):
* **Unidades:** `passages_candidate.json` contiene las 342.
* **TF‑IDF:** reconstruido sobre «título + texto».
* **Grafo:** 61 aristas `references_article` (el grafo original reasignado a las unidades), 68 `has_table`, 68 `table_of` y 12 `references_table`.
* **Denso:** matriz truncada de 342×384 y, aparte, 730 ventanas de 220/30 para la variante SW.
* **Modo de arranque:** el motor arranca en HYBRID. `source_sha256_verified=False`, porque el PDF no está en la ruta relativa del índice experimental; no afecta a la recuperación.

**Constructor TF‑IDF:** el constructor del índice original no está versionado, así que se reconstruyó; queda pendiente versionarlo. La reconstrucción usa smooth‑IDF `ln((1+N)/(1+df))+1`, tf/len, normalización L2, «título + texto», separación de guiones y una lista de parada de 33 palabras inferida del vocabulario del índice original.
* **Fidelidad frente al índice original:** el error relativo del IDF tiene una mediana de 0; el error máximo por vector tiene una mediana de 0,0015 y un p95 de 0,17; el solapamiento de los 10 términos principales es de 0,976.
* **Control Bc:** para medir la deriva del constructor se evalúa también Bc, las páginas con este mismo TF‑IDF.

## 3. Configuraciones y criterio

| Código | Unidades | TF‑IDF | Denso | R1 |
|---|---|---|---|---|
| A | páginas | original | original | no |
| **B** (referencia) | páginas | original | original | sí |
| Bc (control del constructor) | páginas | reconstruido (en memoria) | original | sí |
| S0 | apartados | reconstruido | truncado | no |
| **S** | apartados | reconstruido | truncado | sí |
| **SW** | apartados | reconstruido | ventanas, máximo (en memoria) | sí |

* **Motor:** el mismo `ReasoningRetrievalEngine` sin modificar, con `enable_ood_detector=True`, sobre las 82 `query_used` (DICT y LLM): 62 respondibles y 20 no respondibles.
* **Criterio de acierto, común a todas:** una unidad entregada satisface un ancla si su texto contiene el **fragmento literal** del ancla (normalizado de espacios y apóstrofos) y **cubre la página** del ancla. Los 62 fragmentos de DEV se localizan en su página.
* **Criterio por IDs:** para A, B y Bc se informa también el criterio por IDs (`expand`) de los informes anteriores. Con él, B da R@5 de 0,839, R@10 de 0,839 y MRR de 0,539, igual que en los informes previos. El criterio por texto es algo más generoso con las páginas, porque el texto cosido incluye las páginas vecinas.

## 4. Resultados en DEV (respondibles: 62 = DICT 31 + LLM 31)

| Config. | R@5 | R@10 | MRR@10 | Paquete | Caracteres medios del paquete |
|---|---|---|---|---|---|
| A | 0,790 | 0,871 | 0,584 | 0,790 | 16 278 |
| **B** | **0,839** | 0,871 | 0,584 | **0,839** | 16 449 |
| Bc | 0,806 | 0,871 | 0,558 | 0,806 | 16 414 |
| S0 | 0,774 | 0,919 | 0,630 | 0,758 | 10 893 |
| **S** | **0,839** | 0,887 | 0,627 | **0,839** | **10 498 (−36 %)** |
| **SW** | **0,839** | **0,919** | **0,677** | **0,855** | 11 637 (−29 %) |

Por forma (R@5 / R@10 / MRR / paquete):

| Forma | B | Bc | S | SW |
|---|---|---|---|---|
| DICT | 0,806 / 0,839 / 0,578 / 0,806 | 0,774 / 0,839 / 0,542 / 0,774 | 0,839 / 0,871 / 0,579 / 0,806 | 0,806 / 0,903 / 0,637 / 0,806 |
| LLM | 0,871 / 0,903 / 0,590 / 0,871 | 0,839 / 0,903 / 0,573 / 0,839 | 0,839 / 0,903 / 0,675 / 0,871 | 0,871 / 0,935 / 0,716 / 0,903 |

Tiempo medio por `retrieve`: entre 41 y 43 ms en todas las configuraciones. El índice de apartados carga en 0,2 s.

## 5. Ganancias y regresiones por pregunta (paquete top‑5)

| Comparación | Ganadas | Perdidas | ¿Involucran una regla fija de B? |
|---|---|---|---|
| Bc frente a B (solo el constructor) | — | EXC‑005 ×2 | sí (`P190-S197`) |
| S frente a B | SCO‑013 ×2, SCO‑014 ×2 | DIR‑015/LLM, MUL‑004/DICT, EXC‑005 ×2 | EXC‑005 |
| **SW frente a B** | **SCO‑013 ×2, SCO‑014 ×2** | **DIR‑018/DICT, EXC‑005 ×2** | **las tres** (`P190-S197` en el top‑5 de B) |
| S frente a Bc | SCO‑013 ×2, SCO‑014 ×2 | DIR‑015/LLM, MUL‑004/DICT | no |
| SW frente a Bc | SCO‑013 ×2, SCO‑014 ×2 | DIR‑018/DICT | sí |
| SW frente a S | DIR‑015/LLM, MUL‑004/DICT | DIR‑018/DICT | sí |

**Cambios de posición en el top‑10 frente a B** (detalle en `eval_results.json` → `comparaciones`):

* **SW mejora 22 posiciones.** Las principales son:
  * SCO‑013 y SCO‑014, que pasan de no aparecer al puesto 1‑2;
  * EXC‑009, de 5 a 1, en las dos formas;
  * CAT‑003 y CAT‑007, de 2‑4 a 1;
  * DIR‑007, de 2 a 1, y DIR‑017, de 3 a 1;
  * SCO‑024, de 2‑3 a 1;
  * MUL‑004/LLM, de 3 a 1;
  * SCO‑019, de no aparecer o del 9, al 6‑8;
  * SCO‑020, de 10 a 8.
* **SW empeora 13:**
  * DIR‑005, de 1 a 9, en las dos formas;
  * CAT‑001/LLM, de 1 a 7;
  * SCO‑026, de 1 a 3‑5;
  * EXC‑006/DICT, de 1 a 4;
  * DIR‑015/LLM, de 2 a 5;
  * DIR‑008/DICT, de 1 a 3;
  * DIR‑018/DICT, de 3 a 6;
  * EXC‑003, de 6 a 9;
  * EXC‑005, de 5 a fuera.
* **El papel de R1 se mantiene con apartados:** S0, sin R1, baja a R@5 0,774 y paquete 0,758.

## 6. SCO‑020 (6.1 frente a 6.3 / tabla 6.3.4, sin confundir 6.4.2)

Posición en el paquete top‑5, que es idéntica en DICT y en LLM:

| Config. | 6.1 «no additional weight tolerance» | 6.3 «≤ 5 % … random weigh‑in» | Tabla 6.3.4 | 6.4.2 «+5 % … minus» (distractor) | ¿Ancla? |
|---|---|---|---|---|---|
| A | — | 3 (pág. 79) | — | 1‑2 | no |
| B | 5 (vía R1) | 3 (pág. 79, entra por 6.3.1) | — | 1‑2 | sí |
| S | 5 (vía R1) | — (final 10.º) | — | 1‑2 | sí |
| SW | 5 (vía R1) | — (final 10.º) | — | 1‑2 | sí |

**Diagnóstico por canal con apartados** (`diag_sco020.json`):
* **6.1** pasa a ser el **1.º del canal denso**, con coseno 0,689 frente a 0,559 como página. Es campeón de R1 con un margen amplio; antes era el 2.º y el umbral de R1 es 0,55.
* **6.3** queda 9.º en TF‑IDF, 18.º en el denso truncado y 10.º en el resultado final. No se rescata.
* **La tabla 6.3.4** queda 9.ª‑10.ª en el denso y no aparece en TF‑IDF. Su enlace `references_table` desde 6.3 no se activa, porque 6.3 no entra en el top‑5.
* **6.4.2** queda 2.º en TF‑IDF y en el resultado final.

**Criterio 7: no se cumple.** Con apartados, el paquete recupera 6.1 de forma más robusta, pero **no reúne 6.1 con 6.3 ni con la tabla 6.3.4**. B solo los reunía porque la página 79 entera entra por 6.3.1, no porque se recuperara la regla del aleatorio.

Sobre la confusión con 6.4.2:
* En todas las configuraciones el distractor 6.4.2 está en los puestos 1‑2, junto con 6.4.3 y 6.5, que también tienen tolerancias del +5 %.
* Con apartados, cada unidad lleva su rótulo (6.4.2 *Mixed Team…*) y el texto ya no mezcla varias reglas de una misma página. **No se ha medido si el generador confunde las reglas**, porque no hubo LLM.

## 7. Preguntas no respondibles (20)

En las seis configuraciones:
* **Estados:** 17 SUCCESS y 3 ABSTAIN `OUT_OF_DOMAIN`.
* **Cambios de estado frente a B:** ninguno.
* **Nuevos top‑5 no vacíos:** ninguno.

El OODDetector de S y SW se calcula sobre el centroide de las unidades. Aun así, no cambió ninguna decisión. El efecto sobre la abstención final, que deciden el DIG y el generador, no se ha medido.

## 8. Integridad

**SHA‑256 antes y después**, idénticos tanto en la construcción como en la evaluación:

| Archivo | SHA‑256 |
|---|---|
| `passages_candidate.json` | `7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b` |
| `dense_embeddings_candidate.npy` | `124ced95fb9e152ce586dec9f30a1eb98dc14ee385c0bc335a2055357f73a617` |
| `vector_index_candidate.json` | `e182c77e0775472eb73d22ab92b15d026d067cbf6264fb8b25b207479c4668eb` |
| `knowledge_graph_candidate.json` | `95d5a67936cf48d3bc79b69bf370bb1a83a255f938a7322e0dae256450dde215` |
| `dense_embeddings_meta.json` | `c96b214bc14801ad903d58e0245d48c008d65ac051d339fd4e6b65e30709160e` |
| `data/derived/article_units_v1/units.jsonl` | `9c54a9fd8194d9c0895ee457cce7460db5d9ec24d3b5169ac13efdccc945f5f1` (coincide con su `hashes.json`) |
| PDF `IJF_Sport_and_Organisation_Rules_2026_08_14.pdf` | `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620` |

**Archivos experimentales** (todos en `experiments/segmentacion_apartados_2026/`):

| Archivo | SHA‑256 |
|---|---|
| `build_sections.py` | `e55dc15977273eb03c8ecd1e81466fa8da0b0907595b23b716d80a16a9ffce76` |
| `eval_sections.py` | `15966fbcb8c9f45501a7111e8f0f1822cb92a9b7129cf59f08e749a80bc79d53` |
| `diag_sco020.py` | `708d4ae54e70fe2c39957933db8fc19910d1bc451deb11e9a1e0686181de6130` |
| `units.jsonl` | `812aa19d1838c9ba96b761194e0ef9ff7e7818ddae2324d554928c7de920f515` |
| `audit.json` | `8fca727c6d03776de3cc2a596d0f4a0091908a4fd7bc0e8fe4915486397c6944` |
| `build_report.json` | `7341634b1326be395c2d91ed07835b4aba8d201acca60506a3eced8d2a449ee2` |
| `sparse_builder_fidelity.json` | `07c3d0ce648f30dadacdba1ae2f5b11a6926c224e7ff2c9f62926493d4670ae3` |
| `control_sparse_index_original_passages.json` | `20e67734f0e5a33b250b41988113193304545a457b81e3956f89274d201d7e97` |
| `eval_results.json` | `8e03f12cde4b4e408b141ea4665ff2468a8d4fbacbc4482871c6aeb03daa07f5` |
| `diag_sco020.json` | `52ecca7da81e354b95c507b2eaed9c18637961f7771f65f2676fce51c29acd4c` |
| `index/passages_candidate.json` | `71cdb47ac80febbe66bfa8547be071978c586278012243c351b1fccdcec8f942` |
| `index/vector_index_candidate.json` | `b8832c3cefcc20614141bd60fb99e29ce3d60395ab691768c37f7bf76a6ae812` |
| `index/knowledge_graph_candidate.json` | `eea04fa789d0e2ab1090eac5f340e98f78022cff3f2a376f13c64f0516642928` |
| `index/dense_embeddings_candidate.npy` | `48e89704bedbcc383434814090dbb92e75a2bb6ead98819d97ec012b93ada52a` |
| `index/dense_embeddings_meta.json` | `f72b5beb3b1aea7d9e7ab74c7febd5fcd56052d1bbb350e6550761da76238c76` |
| `index/windows_emb.npy` | `5bde28a548da33d30c89295f8be43730cad7f86aca9203a7d872c9226d44d206` |
| `index/windows_meta.json` | `3a2618f1f5d97320199ec210d29e5da114aef719ea0b9ee67d3fe37be13a81e4` |

**Otras comprobaciones:**
* `git status` en `data/processed`, `data/derived`, el benchmark y `src/` solo muestra los cambios FIX3 previos.
* No hubo commit, push ni stash, no se activó ningún interruptor y no hubo llamadas externas.

## 9. Limitaciones

1. **Reglas fijas por ID en el RRE.** `src/rre_engine.py` contiene 18 IDs `SOR-2026-08-…` con ajustes escritos a mano (H‑05). Esos ajustes no se aplican a las unidades `SEC-`/`TAB-`. **Todas las pérdidas de SW frente a B (EXC‑005 ×2 y DIR‑018/DICT) tienen `P190-S197`, una de esas reglas, en el top‑5 de B.** Hasta medir B sin esas reglas, la comparación favorece a B.
2. **Constructor TF‑IDF no versionado.** Es una reconstrucción de alta fidelidad, pero no exacta. La deriva aislada por Bc es de −0,033 en R@5 (EXC‑005).
3. **Tablas detectadas con una heurística.** 11 de 68 no tienen título y 8 referencias no se resuelven. Algunos bloques con formato de lista numérica pueden tomarse por tablas, por ejemplo en G1.3.
4. **H1.1 forma una unidad de 40 páginas.** Se filtra salvo que se pregunte por el historial, pero sus ventanas compiten en el canal denso: es 3.ª en SW para SCO‑020.
5. **Huecos del corpus:** faltan las páginas 1 a 11 y la p. 131 está vacía.
6. **Muestra pequeña:** DEV tiene 31 preguntas por forma, así que cada pregunta pesa 3,2 puntos. Las etiquetas siguen en `PENDING_EXPERT_REVIEW`.
7. **Solo recuperación:** sin LLM no se ha medido la confusión entre reglas ni el efecto en el DIG.

## 10. Conclusión y recomendación

**Hechos medidos:**
* **SW (apartados + ventanas + R1):** iguala a B en R@5 (0,839), lo mejora en R@10 (0,919 frente a 0,871), en MRR (0,677 frente a 0,584) y en el paquete (0,855 frente a 0,839), y **reduce el paquete un 29 %** en caracteres.
* **S:** iguala a B en R@5 y en el paquete, y reduce el paquete un 36 %.
* **No respondibles:** ningún cambio de estado.
* **Frente al control Bc,** que usa el mismo constructor TF‑IDF, S y SW ganan +0,033 en R@5.

**Criterios no cumplidos:**
* **SCO‑020 no reúne 6.1 con 6.3 ni con la tabla 6.3.4** en S ni en SW.
* **Hay regresiones frente a B:** EXC‑005 ×2 y DIR‑018 en SW. Todas coinciden con reglas fijas por ID del RRE.

**Recomendación:** **no integrar todavía.** La segmentación por apartados es prometedora: da mejor ordenación y paquetes más pequeños y específicos, y hace que 6.1 domine el canal denso. Antes de decidir, hacen falta tres pasos, cada uno con autorización propia:
1. **Medir la influencia de las reglas fijas:** evaluar B sin ellas, o expresar las reglas por rótulo de apartado en lugar de por ID, en un entorno experimental.
2. **Probar una expansión jerárquica genérica del paquete:** apartado padre y apartados hermanos, más las tablas enlazadas. El objetivo es que 6.1 traiga 6.2.x y 6.3 cuando se recupera un apartado de la sección 6. Debe medirse con los mismos criterios frente a B, y en particular con la presencia conjunta de 6.1 y 6.3/tabla 6.3.4 en SCO‑020.
3. **Versionar el constructor TF‑IDF y el de los índices** (pendiente de la auditoría integral).

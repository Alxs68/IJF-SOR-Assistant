# Resultados T1 y T2: truncamiento de embeddings y fusión del RRE

**Proyecto:** IJF SOR Assistant 2026
**Fecha:** 17 de noviembre de 2026
**Tipo:** diagnóstico, solo lectura
**Origen:** hallazgos H‑03 y H‑04 de `AUDITORIA_INTEGRAL_PROCESAMIENTO_DOCUMENTAL_2026.md`
**Dónde se ejecutó:** en el PC del responsable, sin red para el modelo (`HF_HUB_OFFLINE=1`) y con las claves de los proveedores vacías.

---

## 1. Resultado de T1: truncamiento confirmado

**Modelo verificado:**
* **Instantánea local:** `~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Es la única que hay, y es la que eligen tanto el script de construcción como el RRE.
* **Límite efectivo:** `sentence_bert_config.json` fija `max_seq_length = 256`, y el modelo cargado usa 256. El tokenizador declara `model_max_length = 512` y el modelo admite 512 posiciones, pero SentenceTransformer corta en 256.
* **Texto analizado:** es exactamente el que se embebió, «título de la sección + página completa». Volví a calcular los 385 embeddings en memoria y su coseno con los guardados es como mínimo 0,99999988; ninguna fila baja de 0,999. **Los embeddings almacenados corresponden a estos textos y a esta instantánea.**

**Medida con el tokenizador real** (incluye los tokens especiales):

| Métrica | Valor |
|---|---|
| Pasajes que superan 256 tokens | **294 de 385 (76,4 %)** |
| Tokens totales del corpus embebido | 168.495 |
| Tokens que quedan fuera de la ventana | **83.924 (49,8 %)** |
| Mediana y máximo de tokens por pasaje | 490 y 1.210 |

**Posición del fragmento esperado frente al canal denso** (31 respondibles de dev; rangos del canal tomados de la Fase 11):

| Posición del fragmento | El canal denso lo encuentra en su top‑25 (LLM) | Ídem (DICT) |
|---|---|---|
| Dentro de la ventana (antes del token 255) | **17 de 17** | 16 de 17 |
| Fuera de la ventana | **5 de 14** | 6 de 14 |

**Los 9 fallos del canal denso en la forma LLM tienen el fragmento fuera de la ventana:**

| Caso | Token del fragmento | Denso | TF‑IDF | Final (R0) |
|---|---|---|---|---|
| SCO‑013 | 614 | — | 17 | > 10 |
| SCO‑014 | 627 | — | 14 | > 10 |
| EXC‑003 | 419 | — | 19 | > 10 |
| MLG‑002 | 339 | — | — | > 10 (además, consulta en portugués sin traducir) |
| SCO‑021 | 410 | — | 1 | 3 |
| SCO‑022 | 358 | — | 2 | > 10 (6 con equivalencia) |
| DIR‑017 | 519 | — | 1 | 3 |
| EXC‑009 | 329 | — | 1 | 5 |
| MUL‑004 | 339 | — | 2 | 4 |

* **CAT‑003:** el fragmento está en el token 525, fuera de la ventana. El canal denso solo lo sitúa en el puesto 14, a partir de lo que ve al principio de la página.
* **Fragmentos fuera de la ventana que sí se encontraron** (5 en la forma LLM): el canal acertó por el contenido inicial de la misma página, no por la regla.

**Dictamen T1:**
* **Confirmado:** el canal denso no lee la mitad del texto del corpus, y el 76 % de los pasajes queda truncado.
* **Fuertemente respaldado:** que el truncamiento es la causa de los fallos del canal denso. Ninguna regla dentro de la ventana se pierde (17 de 17), y todas las que se pierden están fuera de ella (9 de 9).
* **Lo que no demuestra:** que corregirlo mejore el resultado final. En 5 de los 9 casos, el TF‑IDF ya compensa y la evidencia llega al top‑5.

---

## 2. Resultado de T2: con R1, 4 evaluaciones recuperadas y ninguna perdida

**Qué se ejecutó:**
* **Evaluador existente** `scripts/eval_r1_channel_champions.py`, sin cambios. Mide si la evidencia llega al paquete que se entrega al modelo: top‑5 más los pasajes relacionados.
* **Script de diagnóstico** `deploy/exp/out/t1t2_diag.py`, para obtener posiciones, R@5, R@10 y MRR, que el evaluador no calcula.

**Casos:** las mismas consultas registradas en la Fase 11: 31 respondibles de dev, cada una en dos formas (DICT y LLM), es decir, 62 evaluaciones. Sin LLM y sin el conjunto sellado.

### Tabla comparativa

| Métrica | DICT sin R1 | DICT con R1 | LLM sin R1 | LLM con R1 |
|---|---|---|---|---|
| R@5 (top‑5 de producción) | 0,774 | **0,806** | 0,774 | **0,871** |
| MRR (top‑5) | 0,524 | 0,530 | 0,540 | 0,561 |
| R@10 (top‑10) | 0,806 | 0,806 | 0,871 | 0,871 |
| MRR (top‑10) | 0,527 | 0,527 | 0,552 | 0,552 |
| Paquete con la evidencia (evaluador) | 48 de 62 en total | **52 de 62** en total | | |

**Cómo leer la tabla:** R1 solo actúa cuando la fusión deja fuera del top‑5 a un campeón de canal, por eso no cambia R@10. Las 4 ganancias son evidencia que ya estaba en los puestos 6 a 10 y R1 sube al top‑5.

### Casos que mejoraron

| Caso | Posición en el top‑5, sin R1 → con R1 | Posición en el top‑10, sin R1 → con R1 |
|---|---|---|
| SCO‑019 / LLM | fuera → **4** | 10 → 9 |
| SCO‑020 / DICT | fuera → **5** | 10 → 10 |
| SCO‑020 / LLM | fuera → **5** | 10 → 10 |
| SCO‑022 / LLM | fuera → **5** | 6 → 6 |

**SCO‑019 / DICT no mejora:** la evidencia no aparece en el top‑10 en ninguno de los dos casos. La consulta del diccionario mezcla palabras en español, y el canal denso solo la sitúa en el puesto 10, por debajo del umbral de R1, que solo reserva los puestos 1 y 2 del denso.

### Casos que empeoraron

* **Ninguno pierde la evidencia** (lista `perdidas` vacía en el evaluador).
* **17 paquetes cambian sin que cambie si contienen la evidencia:** R1 sustituye los últimos pasajes del paquete. **No se midió** si eso quita evidencia secundaria o distractores; hay que medirlo con el DIG o con revisión manual.

---

## 3. Limitaciones

* **Muestra pequeña:** dev tiene 31 preguntas respondibles, así que una pregunta equivale a 0,03 en R@5. Las 4 ganancias corresponden a 3 preguntas (SCO‑019, SCO‑020 y SCO‑022).
* **Rangos de canal de la Fase 11:** el contraste de T1 usa los rangos guardados en esa fase. Son válidos porque los embeddings son idénticos (coseno ≥ 0,9999999), pero no se recalcularon.
* **Posiciones de T2:** usan el primer ancla del benchmark, con equivalencia de pasajes duplicados. El evaluador exige todas las anclas y cuenta los pasajes relacionados. Las dos medidas coinciden en las ganancias.
* **Preguntas no respondibles:** no se evaluaron (el diagnóstico de la Fase 11 solo registra respondibles). **El efecto de R1 en las abstenciones y en el filtro OOD no está medido.**
* **Alcance:** no se midió el efecto en las respuestas finales (LLM y DIG), y no se usó el conjunto sellado.

---

## 4. Conclusiones verificables

1. El canal denso trunca a 256 tokens: 294 de 385 pasajes (76,4 %) y el 49,8 % de los tokens del corpus quedan fuera. *Se verifica en `deploy/exp/out/t1t2_result.json`, apartado `t1`.*
2. En dev, el canal denso encuentra 17 de 17 reglas dentro de la ventana y 5 de 14 fuera; los 9 fallos LLM están fuera. *Se verifica en `t1_posiciones`.*
3. R1 sube R@5 de 0,774 a 0,871 (LLM) y a 0,806 (DICT), sin pérdidas en el paquete; recupera SCO‑019 (LLM), SCO‑020 (las dos formas) y SCO‑022 (LLM). *Se verifica en `t2_*` y en `data/eval/fix3/r1_channel_champions_dev.json`.*
4. R1 no resuelve la evidencia que el canal denso no ve (SCO‑013, SCO‑014, EXC‑003 y MLG‑002): esos casos dependen de T1.

---

## 5. Recomendación del siguiente paso

* **R1:** mantenerla como candidata en la corrida A/B de FIX3, que está pendiente de autorización. Antes de activarla en producción hay que medir su efecto en las preguntas no respondibles y en las respuestas validadas por el DIG.
* **Truncamiento:** diseñar, sin aplicarlo todavía, un experimento que codifique cada página en ventanas de hasta 256 tokens dentro del mismo pasaje y tome la mayor similitud.
  * Se haría en una caché experimental, con el mismo modelo, los mismos pasajes y la misma fusión.
  * Mediría el recall del canal denso en su top‑25 y R@5 en los 9 casos de la tabla de T1.
  * Es la vía directa para SCO‑013, SCO‑014 y EXC‑003, y sería la referencia antes de comparar otros modelos.

Ninguna de las dos se implementa sin autorización expresa.

---

## Anexo: archivos y operaciones

* **Inspeccionados:**
  * corpus: `data/processed/rebuild_2026_08_corrected/` (pasajes y `.npy`);
  * configuración del modelo: `sentence_bert_config.json`, `tokenizer_config.json` y `config.json` de la instantánea;
  * benchmark y diagnóstico: `data/eval/benchmark_v2/splits/dev.jsonl` y `data/eval/fase11/diag_retrieval_dev.json`;
  * evaluador: `scripts/eval_r1_channel_champions.py`.
* **Pruebas ejecutadas:**
  * `deploy/exp/out/t1t2_diag.py`, script de diagnóstico creado para esta prueba en la carpeta de salidas (excluida del paquete);
  * `scripts/eval_r1_channel_champions.py`, sin cambios.
* **Archivos generados:**
  * este informe;
  * `deploy/exp/out/t1t2_result.json`, salida del diagnóstico;
  * `data/eval/fix3/r1_channel_champions_dev.json`, salida normal del evaluador.
* **Sin cambios en:** código, corpus, pasajes, embeddings guardados (solo se recalcularon en memoria para comprobarlos), índices, benchmark, RRE, DIG, DIG‑05 y DIG‑09.
* **Ninguna** operación remota ni en OCI, ninguna llamada a Gemini o Groq, ninguna descarga de modelos y ningún commit, push, stash ni despliegue.

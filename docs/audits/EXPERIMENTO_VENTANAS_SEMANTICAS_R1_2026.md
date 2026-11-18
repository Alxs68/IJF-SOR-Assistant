# Experimento: ventanas semánticas + R1 (2026-11-17)

**Alcance:** prueba local y aislada, sin LLM, sin red y sin modificar `src/`, `data/processed/`, el benchmark ni el DIG. Solo se usó el split DEV, leído desde `dev.jsonl`; `test_sealed` no se abrió.
**Código:** `experiments/ventanas_2026/build_index.py` (índice) y `experiments/ventanas_2026/eval.py` (evaluación).
**Datos:** `build_report.json` y `results.json` (por pregunta), en la misma carpeta.
**Base:** rama `exp/r3-dig-v2`, HEAD `d126873`, con los cambios FIX3 sin commit. `RRE_ENABLE_SCOPE_PREFERENCE` estaba sin definir (R3 desactivado).

## 1. Parámetros

| Parámetro | Valor |
|---|---|
| Modelo | `all-MiniLM-L6-v2`, snapshot local `1110a243…`, `local_files_only`, `HF_HUB_OFFLINE=1` |
| Ventana | 220 tokens reales del tokenizador del modelo, con un solapamiento de 30 (paso de 190) |
| Prefijo | Título del apartado (`heading_path[0]`, el mismo del embebido actual «título + página») antepuesto a cada ventana |
| Límite | ≤ 254 tokens con `[CLS]`/`[SEP]`; el máximo observado fue 241 y ningún título se recortó |
| Embeddings | `normalize_embeddings=True`, dimensión 384 |
| Por ventana | `passage_id`, `token_inicio`, `token_fin`, `n_tokens_total` |
| Puntuación de un pasaje | Máximo coseno de sus ventanas, con la misma proyección ES→EN, el mismo umbral > 0,15 y el top-25 |
| Conexión | `rre._dense_search` se sustituye **solo en memoria**. El `OODDetector` conserva la matriz original de 385×384 (comprobado: el mismo objeto y el mismo centroide) |
| Consultas | 82 `query_used` (DICT y LLM) de `data/eval/fase11/retrieval_experiments_dev.json`: 62 respondibles y 20 no respondibles |

## 2. Índice

* **Volumen:** 1021 ventanas para 385 pasajes, con una media de 2,65 y un máximo de 7 por pasaje.
* **Distribución de ventanas por pasaje:**

  | Ventanas | 1 | 2 | 3 | 4 | 5 | 7 |
  |---|---|---|---|---|---|---|
  | Pasajes | 85 | 50 | 170 | 76 | 3 | 1 |
* **Duplicados:** se evitaron 0. Hay 287 grupos de página y texto idénticos, pero cada pasaje de esos grupos tiene un `heading_path[0]` distinto, de modo que las 385 combinaciones título + texto son únicas y ninguna ventana se repite literalmente. La deduplicación por texto exacto de ventana está implementada, pero aquí no ahorra nada.
* **Memoria:** la matriz ocupa 1,50 MB, frente a 0,56 MB del índice original.
* **Tiempo de construcción:** 59,8 s en CPU (17,8 s de carga y tokenización y 42,1 s de codificación).
* **Tiempo por consulta** (`retrieve`, media sobre 656 llamadas): A 35,1 ms · B 35,1 ms · C 34,7 ms · D 34,8 ms. La diferencia está dentro del ruido.

## 3. Resultados A/B/C/D (respondibles, con equivalencia de duplicados `expand`)

**Definición de las métricas:**
* R@k y MRR@10 se calculan sobre la posición del primer ancla en la evidencia, con el criterio de T2.
* «Denso top‑25» indica si el primer ancla aparece en `_dense_search(top_k=25)`.
* «Paquete» indica si **todas** las anclas están en la evidencia más los relacionados con `top_k=5`, con el criterio de R1.

| Configuración | Forma | R@5 | R@10 | MRR@10 | Denso top‑25 | Paquete |
|---|---|---|---|---|---|---|
| A actual | DICT | 0,774 | 0,806 | 0,527 | 0,742 | 0,774 |
| B actual + R1 | DICT | 0,806 | 0,806 | 0,527 | 0,742 | 0,806 |
| C ventanas | DICT | 0,839 | 0,839 | 0,638 | 0,968 | 0,839 |
| D ventanas + R1 | DICT | 0,839 | 0,839 | 0,638 | 0,968 | 0,839 |
| A actual | LLM | 0,774 | 0,871 | 0,552 | 0,710 | 0,774 |
| B actual + R1 | LLM | 0,871 | 0,871 | 0,552 | 0,710 | 0,871 |
| C ventanas | LLM | 0,871 | 0,903 | 0,679 | 0,968 | 0,871 |
| D ventanas + R1 | LLM | **0,903** | 0,903 | 0,679 | 0,968 | **0,903** |
| A actual | Total (62) | 0,774 | 0,839 | 0,539 | 0,726 | 0,774 |
| B actual + R1 | Total | 0,839 | 0,839 | 0,539 | 0,726 | 0,839 |
| C ventanas | Total | 0,855 | 0,871 | 0,659 | 0,968 | 0,855 |
| D ventanas + R1 | Total | **0,871** | 0,871 | 0,659 | 0,968 | **0,871** |

A y B reproducen T2: R@5 de 0,774 → 0,806 con DICT y de 0,774 → 0,871 con LLM.

## 4. Ganadas, perdidas y regresiones

| Comparación | Ganadas (paquete y R@5) | Perdidas |
|---|---|---|
| B vs A | SCO‑019/LLM, SCO‑020/DICT, SCO‑020/LLM, SCO‑022/LLM | ninguna |
| C vs A | SCO‑013 ×2, SCO‑014 ×2, SCO‑022/LLM | ninguna |
| D vs A | SCO‑013 ×2, SCO‑014 ×2, SCO‑019/LLM, SCO‑022/LLM | ninguna |
| **D vs B** | SCO‑013 ×2, SCO‑014 ×2 | **SCO‑020/DICT, SCO‑020/LLM** |

En C y D hay regresiones de posición frente a A (top‑10), las mismas en las dos:
* DIR‑015/LLM pasa de 2 a 3.
* MLG‑003/LLM pasa de 1 a 2.
* SCO‑010/DICT pasa de 1 a 2.
* SCO‑026/DICT pasa de 1 a 2.
* SCO‑020, en las dos formas, pasa de 10 a fuera del top‑10.

Salvo SCO‑020, todas siguen dentro del top‑5.

**SCO‑020** (hecho medido): con ventanas, su rango denso empeora de 2 a 9. Deja de ser el campeón del canal denso y R1 ya no lo rescata. La causa probable, aún no verificada, es que otros pasajes largos ganan similitud al tener ventanas más focalizadas.

### Preguntas foco (posición k5 / k10 / rango denso top‑25 / paquete)

| Pregunta | A | B | C | D |
|---|---|---|---|---|
| SCO‑013 DICT | –/–/–/no | –/–/–/no | 4/4/1/sí | 4/4/1/sí |
| SCO‑013 LLM | –/–/–/no | –/–/–/no | 4/4/1/sí | 4/4/1/sí |
| SCO‑014 DICT | –/–/–/no | –/–/–/no | 2/2/1/sí | 2/2/1/sí |
| SCO‑014 LLM | –/–/–/no | –/–/–/no | 3/3/1/sí | 3/3/1/sí |
| EXC‑003 DICT/LLM | –/–/–/no | –/–/–/no | –/–/21/no | –/–/21/no |
| MLG‑002 DICT/LLM | –/–/–/no | –/–/–/no | –/–/–/no | –/–/–/no |
| SCO‑019 DICT | –/–/10/no | –/–/10/no | –/–/14/no | –/–/14/no |
| SCO‑019 LLM | –/10/1/no | 4/9/1/sí | –/10/1/no | 4/9/1/sí |
| SCO‑020 DICT/LLM | –/10/2/no | 5/10/2/sí | –/–/9/no | –/–/9/no |
| SCO‑021 DICT/LLM | 3/3/–/sí | 3/3/–/sí | 1/1/1/sí | 1/1/1/sí |
| SCO‑022 DICT | 1/1/6/sí | 1/1/6/sí | 1/1/3/sí | 1/1/3/sí |
| SCO‑022 LLM | –/6/–/no | 5/6/–/sí | 1/1/2/sí | 1/1/2/sí |

Con ventanas, el recall del canal denso en el top‑25 sube de 45/62 a 60/62. EXC‑003 entra en el canal denso en la posición 21, pero la fusión no lo sube. MLG‑002 sigue fuera de todos los canales, así que no es un problema de truncamiento.

## 5. No respondibles (20 consultas)

* **Top‑5 no vacío:** 17 de 20 en A, B, C y D.
* **Cambios de estado frente a A:** ninguno.
* **Nuevos top‑5 no vacíos:** ninguno.

**Sin falsos positivos nuevos** a nivel de recuperación. El efecto en el DIG y en la respuesta final no se ha medido, porque no hubo LLM.

## 6. Integridad

* **SHA‑256 antes y después** de la construcción y de la evaluación: idénticos.
  * `passages_candidate.json`: `…1167b`
  * `dense_embeddings_candidate.npy`: `…7a617`
  * `vector_index_candidate.json`: `…668eb`
  * `knowledge_graph_candidate.json`: `…dde215`
* **Ventanas:** las 1021 apuntan a un `passage_id` existente, y los 385 pasajes tienen al menos una.
* **Texto entregado:** las 1748 entregas (evidencia y relacionados, top‑5, todas las configuraciones) contienen el `text_original` completo del pasaje, o el texto cosido por `PassageStitcher` que también entrega A. Ninguna entrega es una ventana.
* **Escritura:** no se escribió nada en `data/processed/`. Los artefactos están solo en `experiments/ventanas_2026/`.

## 7. Limitaciones

* **Muestra pequeña:** DEV tiene 31 preguntas respondibles por forma. Una pregunta equivale a 3,2 puntos, y las ganancias se concentran en 3 preguntas (SCO‑013, SCO‑014 y SCO‑022). Hace falta confirmarlo en el test sellado, que solo puede usarse en la evaluación final.
* **Solo recuperación:** no se midió el efecto en la generación ni en el DIG, como DIG‑05, la pertinencia o la cobertura validada.
* **Detector OOD:** conserva sus embeddings, pero recibe el top denso del canal activo, que en C y D es el de las ventanas. Es el comportamiento que tendría una integración real; en este experimento no cambió ningún estado.
* **Ordenamiento:** las regresiones de posición (SCO‑020 y cuatro pasos de 1 a 2 o de 2 a 3) muestran que el máximo de ventanas altera el orden relativo. No se probaron variantes como la media del top‑2 de ventanas o pesos por longitud.
* **Etiquetas:** siguen en `PENDING_EXPERT_REVIEW`.

## 8. Recomendación

**Hechos:**
* D, ventanas más R1, es la mejor configuración. Frente a A, R@5 y el paquete pasan de 0,774 a 0,871 (total) y a 0,903 (LLM), y el MRR de 0,539 a 0,659.
* Frente a A no hay pérdidas ni falsos positivos nuevos.
* Frente a B, el estado actual con R1, D gana 4 consultas y pierde 2 (las dos de SCO‑020).

**Recomendación:**
1. Antes de integrar nada, analizar SCO‑020 para entender por qué su rango denso pasa de 2 a 9, y probar una variante de agregación sin reglas por pregunta.
2. Si se mantiene sin pérdidas frente a B, proponer la integración bajo un interruptor experimental desactivado por defecto, por ejemplo `RRE_DENSE_WINDOWS`, con un índice de ventanas versionado aparte de `data/processed/`.
3. Medirlo después en la corrida A/B solo con Gemini.

Cada paso necesita una autorización propia.

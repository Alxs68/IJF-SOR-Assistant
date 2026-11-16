# Fase 11B — Recuperación consciente del ámbito

**Estado:** DIAGNÓSTICO Y EXPERIMENTOS R2–R5 COMPLETADOS en dev (§6). Solo R3 cumple los criterios, con un efecto pequeño; R2, R4 y R5 se descartan en su forma actual.
**Ámbito:** solo dev. No hay evaluación sobre test_sealed.
**Evidencia:** `data/eval/fase11/diag_retrieval_dev.json` y `data/eval/fase11/equivalence_dev.json`.
**Código:** `src/experimental/scope_retriever.py`, `scripts/diag_retrieval_f11.py`, `scripts/recompute_equivalence_f11.py`.

---

## 1. Estrategia actual (`src/rre_engine.py`, solo lectura)

* **Unidad indexada:** el pasaje de página. Son 385 pasajes sobre 287 páginas, con duplicados de texto idéntico dentro de la misma página.
* **Canal léxico:** TF‑IDF con similitud coseno (`_sparse_search`, top‑25, umbral 0,05).
* **Canal denso:** `all-MiniLM-L6-v2`, que solo funciona en inglés. El canal hace una proyección interna ES→EN por diccionario y se queda con el máximo de las dos similitudes (top‑25, umbral 0,15).
* **Fusión RRF:** k = 60, pesos 1,2 (léxico) y 1,0 (denso), bonificación multicanal ×1,35 + 0,035 y bonificación léxica ≥ 0,20.
* **Ajustes posteriores a la fusión:**
  * **reglas temáticas fijas** con 34 detectores de palabras clave (`any(w in clean_q_lower …)`) (osaekomi y área de seguridad, agarres, cinturón, color del judogi, mangas, marcas, acciones de cabeza, cadetes, conducta…);
  * **31 identificadores de pasaje escritos en el código**;
  * atenuación del apéndice de historial de versiones;
  * coincidencia de códigos de artículo.
* **Controles de dominio:** anclas negativas, detector OOD y vocabulario mínimo (incluye una lista de «inmunidad» de términos de judo).
* **Expansión:** costura de pasajes contiguos y expansión por grafo (máximo 3 pasajes relacionados). No usa los `cross_refs` resueltos de `article_units_v1`.
* **Traducción en ADA:** por diccionario sin LLM. Con LLM disponible, la consulta en español se traduce con el propio LLM (1 llamada auxiliar), según la detección de idioma; el portugués no siempre se detecta y entonces no se traduce.

## 2. Diagnóstico medido en dev (31 consultas respondibles)

**R0** es la producción (`rre.retrieve`, top‑10, sin grafo). **R1** es la fusión RRF sin ningún ajuste posterior: ni reglas temáticas, ni atenuaciones, ni coincidencia de códigos. **DICT** usa la proyección por diccionario y **LLM** la traducción registrada en la corrida de la Fase 11, reproducida sin llamar al modelo. Se aplica la equivalencia de pasajes duplicados (ver el diagnóstico de abstenciones, §2).

| | R0 DICT | R1 DICT | R0 LLM | R1 LLM |
|---|---|---|---|---|
| R@5 | **0,774** | 0,677 | **0,774** | 0,661 |
| MRR | 0,527 | 0,533 | 0,573 | 0,567 |
| hit@10 | 0,806 | 0,710 | **0,871** | 0,774 |
| R@5 en (17) | 0,824 | 0,706 | 0,824 | 0,706 |
| R@5 es (12) | 0,750 | 0,667 | 0,750 | 0,625 |
| R@5 fr (1) / pt (1) | 1 / 0 | 1 / 0 | 1 / 0 | 1 / 0 |
| Latencia media (ms) | 33,5 | 18,9 | 31,0 | 20,4 |

**Lectura de la tabla:**
* **Las reglas y ajustes de R0 sí ayudan en este benchmark.** R1 no gana ninguna consulta y pierde 3 con el diccionario (CAT‑003, EXC‑009, REF‑005) y 4 con la traducción del LLM (EXC‑009, MUL‑004, REF‑005, SCO‑024). Con la métrica estricta parecía lo contrario (R1 0,629 frente a R0 0,565); era un artefacto de los duplicados. R1 queda como referencia de diagnóstico, **no como candidata**.
* **Las reglas fijas tienen además un problema de diseño,** independiente de su efecto: son específicas de temas y pasajes, el benchmark solo tiene 31 respondibles en dev, y su generalización a consultas nuevas no está demostrada. No se tocan porque están en producción, pero el informe ejecutivo debe recogerlo.
* **Traducción con LLM frente a diccionario:** mismo R@5 (0,774) y mejor hit@10 (0,871 frente a 0,806) y MRR (0,573 frente a 0,527). El camino con LLM recupera algo mejor en profundidad; la diferencia es de 2 consultas.
* **Duplicación:** el top‑10 de R0 tiene de media 9,7 páginas distintas. Los duplicados apenas ocupan posiciones; su efecto era sobre la **medida**, no sobre la recuperación.

## 3. Consultas de dev sin evidencia en el top‑5 (R0, traducción LLM, con equivalencia)

| Consulta | Idioma | Posición de la evidencia (R0) | Distractor de ámbito (R0) | Causa observada |
|---|---|---|---|---|
| B2‑EXC‑003 | en | > 10 | — | regla de inscripción (4.2) no alcanzada: vocabulario «enter / entered» frente a «entries / inscribe» |
| B2‑MLG‑002 | pt | > 10 | — | la consulta no se traduce (portugués no detectado) y el modelo denso solo funciona en inglés |
| B2‑SCO‑013 | en | > 10 | 3 | **error de ámbito:** el área de combate general (8.7) desplaza al área de kata (B1.8) |
| B2‑SCO‑014 | es | > 10 | 4 | **error de ámbito:** el mismo par de reglas que en SCO‑013 |
| B2‑SCO‑019 | es | 10 | — | tolerancia de cadetes (6.1, p. 75) por debajo de otras reglas de pesaje |
| B2‑SCO‑020 | en | 10 | — | misma regla 6.1 («no additional weight tolerance») |
| B2‑SCO‑022 | es | 6 | 7 | reservas de equipo mixto justo fuera del top‑5 |

Paquete realmente entregado al LLM en las corridas: 48 de 62 evaluaciones con la evidencia completa (77 %).

**Excepciones y referencias cruzadas en dev:** solo 1 consulta con excepción anclada en otro pasaje (EXC‑003, no recuperada) y 2 con referencia cruzada obligatoria (REF‑001 entregada; REF‑005 no). Con 3 casos **no se puede medir una mejora** en dev. En el resto, la excepción está dentro del mismo pasaje de página que la regla.

## 4. Hipótesis y experimentos (definidos antes de medir)

Cada experimento se mide contra R0 en dev con la equivalencia, y se acepta solo si cumple tres condiciones:
1. R@5 o hit@10 suben sin perder consultas que R0 resolvía, o las pérdidas quedan justificadas caso a caso;
2. la precisión del paquete y los distractores entregados sin evidencia no empeoran;
3. no se introducen reglas por pregunta, artículo ni pasaje.

| Exp. | Hipótesis (problema que ataca) | Cambio experimental | Componente |
|---|---|---|---|
| **R2** | La unidad de página mezcla reglas de ámbitos distintos y diluye la señal (SCO‑013/014/019/020) | Indexar también las unidades de artículo de la Fase 8 (851 unidades, con encabezado) y fusionarlas con el ranking de R0, devolviendo siempre el pasaje SOR original | `scope_retriever` |
| **R3** | La consulta nombra el ámbito («kata», «cadets», «veterans», «mixed team») pero el ranking no lo usa (SCO‑013/014) | Preferir candidatos cuya sección o encabezado contenga términos de ámbito presentes en la consulta. Los términos se derivan automáticamente de las secciones del corpus, sin listas fijas. Se mide también el riesgo de favorecer el ámbito equivocado | `scope_retriever` |
| **R4** | Las referencias cruzadas resueltas y las excepciones de otra unidad no llegan al paquete (EXC‑003, REF‑005) | Expansión estructural en un carril etiquetado con los destinos `cross_refs` RESUELTA de la unidad recuperada (98 resueltos). Medición limitada por los 3 casos de dev; se informará como cobertura, no como mejora | `scope_retriever` |
| **R5** | Portugués y francés sin traducción, y modelo denso solo en inglés (MLG‑002) | (a) Canal denso multilingüe experimental: `paraphrase-multilingual-MiniLM-L12-v2`, autorizado solo en local; los embeddings del corpus se calculan en una caché experimental, sin tocar los de producción. (b) Traducción con LLM también para pt/fr. Solo 2 consultas fr/pt en dev; se completará con las 29 en español | `scope_retriever` |
| **R6** | La documentación complementaria se mantiene solo informativa | Sin cambios: el carril SHADOW sigue fuera de la decisión | — |

Las mejoras de recuperación solo se medirán en el flujo completo, con LLM y DIG sin cambios (11C), si superan antes estos criterios sin LLM.

## 5. Limitaciones

* Dev tiene 31 respondibles: una diferencia de 0,03 en R@5 es una sola consulta. Los resultados deben leerse caso a caso.
* La traducción con LLM se reprodujo con la corrida de la Fase 11, degradada por cuota. Algunas traducciones pueden venir de Groq.
* R1 elimina a la vez las reglas fijas y los ajustes genéricos posteriores a la fusión, así que no aísla el efecto de cada regla.

## 6. Resultados de los experimentos (dev, 31 respondibles, con equivalencia)

**Configuración:**
* Script: `scripts/eval_f11_retrieval.py`. Resultados: `data/eval/fase11/retrieval_experiments_dev.json`.
* R0 es `rre.retrieve(top_k=25, expand_graph=True)` de producción. Cada variante se mide **por separado** contra R0, sin combinarlas.
* Parámetros fijados antes de medir: RRF k = 60 con pesos 1:1; R3 con β ∈ {0,2; 0,5}; R4 con un máximo de 3 pasajes en el carril; R5 con `max_seq_length` = 256 sobre 372 unidades.
* **Indicadores de ámbito** derivados por R3 de los títulos de las partes: *kata*, *veter(anos)*, *entri(es)* y *gener(al)*. Se activaron en 9 de 31 consultas.

### 6.1 Tablas globales

**Abreviaturas:** dAb = distractor de ámbito por encima de la evidencia en el top‑10; d5 = distractor en el top‑5 sin la evidencia. Las consultas indican cuáles gana y cuáles pierde cada variante en R@5.

**Forma DICT**

| Variante | R@5 | MRR | hit@10 | P@5 | dAb | d5 | Gana | Pierde |
|---|---|---|---|---|---|---|---|---|
| R0 | 0,774 | 0,536 | 0,806 | 0,168 | 2 | 2 | — | — |
| R2 | 0,758 | **0,631** | 0,871 | 0,155 | 3 | 2 | CAT‑001, SCO‑014 | CAT‑003, MUL‑004, SCO‑025 |
| R3 β 0,2 | 0,774 | 0,549 | 0,871 | 0,161 | 1 | 1 | — | — |
| **R3 β 0,5** | **0,806** | 0,551 | 0,871 | 0,168 | **0** | **0** | SCO‑014 | — |
| R5 | 0,790 | 0,559 | **0,935** | 0,168 | 2 | 0 | CAT‑001, SCO‑013, SCO‑014 | CAT‑003, DIR‑017, MUL‑004 |
| R5 solo | 0,629 | 0,488 | 0,839 | 0,194 | 4 | 2 | 5 | 10 |

**Forma LLM**

| Variante | R@5 | MRR | hit@10 | P@5 | dAb | d5 | Gana | Pierde |
|---|---|---|---|---|---|---|---|---|
| R0 | 0,774 | 0,581 | 0,871 | 0,168 | 2 | 2 | — | — |
| R2 | 0,742 | 0,626 | 0,871 | 0,155 | 5 | 2 | SCO‑013, SCO‑014 | CAT‑001, CAT‑003, SCO‑025 |
| **R3 β 0,2 / 0,5** | 0,774 | 0,602 | **0,935** | 0,161 | **0** | **0** | — | — |
| R5 | 0,758 | 0,565 | 0,935 | 0,155 | 4 | 0 | SCO‑013, SCO‑014, SCO‑019 | CAT‑001, CAT‑003, DIR‑017, MUL‑004 |
| R5 solo | 0,629 | 0,488 | 0,839 | 0,194 | 4 | 2 | 5 | 10 |

### 6.2 R4: carril de referencias cruzadas (forma LLM)

| Paquete | Tamaño medio | Precisión | Referencias cubiertas | Excepciones cubiertas |
|---|---|---|---|---|
| Top‑5 de R0 | 5,00 | 0,168 | 1/2 | 0/1 |
| Top‑5 + grafo (producción) | 5,68 | 0,153 | 1/2 | 0/1 |
| Top‑5 + R4 | 6,68 | 0,130 | 1/2 | 0/1 |

### 6.3 Por variante

* **R3 (ámbito): única variante que cumple los criterios.**
  * **Cambios de rango** (todos a mejor y solo en consultas que nombran el ámbito):
    * CAT‑003: 4→2 (DICT) y 2→1 (LLM);
    * SCO‑013: 13→6 y 12→6;
    * SCO‑014: 17→8 con β 0,2 y 17→5 con β 0,5 (DICT); 11→6 (LLM).
  * **Balance:** ninguna consulta empeora, los errores de ámbito pasan de 2 a 0 y la latencia añadida es inferior a 0,1 ms.
  * **El efecto en R@5 es pequeño:** +1 consulta solo con β 0,5 y DICT. SCO‑013 y SCO‑014 siguen fuera del top‑5 en la forma LLM. La diferencia entre β 0,2 y 0,5 es **una sola consulta**, así que no se elige β con esta muestra.
* **R2 (unidades): descartada en su forma actual.** Sube el MRR (+0,05/+0,10) y mejora el rango de muchas consultas, pero pierde 3 en el top‑5: CAT‑003 4→14, SCO‑025 1→7 y CAT‑001 1→11 (LLM). También empeora los errores de ámbito y la precisión.
* **R4 (referencias): descartada.** No añade cobertura (dev solo tiene 3 anclas de este tipo) y baja la precisión del paquete de 0,168 a 0,130.
* **R5 (multilingüe): descartada la fusión 1:1.**
  * **Lo que mejora:** hit@10 sube a 0,935 y rescata casos de ámbito y de vocabulario (SCO‑013/014/019, EXC‑003 en solitario).
  * **Lo que empeora:** pierde 3–4 consultas en el top‑5.
  * **Portugués:** no lo resuelve; MLG‑002 queda en el puesto 17.
  * **Coste:** 44 s de carga más el índice, y unos 25 ms por consulta.
  * Una fusión con menor peso no se midió para no ajustar sobre la misma muestra.
* **Controles de dominio sin cambios:** en las 10 no respondibles de dev el top‑5 no vacío es idéntico en todas las variantes (10/10). Ninguna variante altera el filtro OOD, porque todas parten de R0.

### 6.4 Recomendación

* **Llevar a la validación externa:** R3 (β 0,2 y 0,5) como **candidato único**. Hay que validarlo en benchmark_v3 sellado, más consultas de ámbito y el flujo completo con LLM y DIG sin cambios, antes de cualquier decisión.
* **Investigar con un diseño nuevo:**
  * R2 y R5 aportan rango y profundidad pero desordenan el top‑5. Un diseño a investigar es usarlos solo para **ampliar el conjunto de candidatos** antes del ordenamiento de R0, no para reordenar.
  * El portugués necesita traducción antes de recuperar: la consulta pt no se tradujo y ni siquiera el canal multilingüe la resolvió.
* **No es atacable en dev:** la excepción y las referencias cruzadas en otro pasaje tienen solo 3 casos. Hace falta ampliar el benchmark (v3) con consultas de este tipo.

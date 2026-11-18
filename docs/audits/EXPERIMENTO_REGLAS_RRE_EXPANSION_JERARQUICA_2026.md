# Experimentos A y B — Reglas fijas del RRE y expansión jerárquica (DEV, sin LLM)

**Fecha:** 2026-11-17
**Estado:** entregado para revisión. No se ha integrado nada.
**Parte de:** `docs/audits/EXPERIMENTO_SEGMENTACION_APARTADOS_SOR_2026.md`
**Artefactos:** `experiments/reglas_rre_expansion_2026/`

| Archivo | Contenido | SHA-256 |
|---|---|---|
| `rre_adapter.py` | adaptador de ablación | `bbe3afa4…` |
| `eval_reglas_expansion.py` | evaluación | `8782c0c1…` |
| `results.json` | resultados completos, filas por pregunta incluidas | — |
| `adapter_diff_abl.patch`, `adapter_diff_traducidas.patch` | diff del RRE generado en memoria | — |
| `eval_stdout.log` | salida de la ejecución | — |

**Restricciones cumplidas:**
* Sin LLM, sin red y sin OCI.
* Sin cambios en `src/`, `data/processed/`, `data/derived/`, el benchmark ni la segmentación previa.
* `test_sealed` no se ha abierto.
* Sin flags, sin commit, push ni stash.

> **Aviso sobre el directorio.** En `experiments/reglas_rre_expansion_2026/` aparecieron durante la ejecución dos archivos que **no ha generado esta sesión**:
> * `run_experiments.py` (12:54)
> * `eval_experiment_results.json` (12:56)
>
> Parecen de otro proceso que trabaja sobre la misma tarea. No se han usado, leído como fuente ni modificado. Este informe se basa solo en `results.json`.

## Método (resumen)

**Adaptador aislado (`rre_adapter.py`).**
* Lee `src/rre_engine.py` en solo lectura y exige su SHA-256 `a0318e88…`.
* Genera **en memoria** un módulo variante. En él, cada bloque de reglas queda envuelto en `if not _ABL.get("<BLOQUE>")` y registra en `_FIRED` las ramas cuya condición se cumple.
* **Equivalencia comprobada:** con todas las reglas activas, la variante da exactamente la misma salida que el original en las 82 consultas, tanto en páginas como en apartados con ventanas. Se comparan estado, IDs y puntuaciones de la evidencia, y los relacionados.

**Referencias.**
* B es el motor de páginas con R1.
* SW son los apartados con denso por ventanas y R1, del experimento previo.
* Configuración del motor: `enable_ood_detector=True` y `semantic_ranker` apagado, igual que en los informes anteriores.

**Criterio de acierto.** Es el del experimento de segmentación: la unidad contiene el fragmento literal del ancla y cubre su página. Para B también se da el criterio por IDs.

**Expansión jerárquica.** Es un post-proceso sobre el paquete de SW:
* **Semillas:** el top-5 de la evidencia.
* **Padre estructural**, por este orden:
  1. `parent_unit_id`;
  2. si no existe, la etiqueta numérica recortada (`6.3.4` → `6.3`), cuando ese apartado existe;
  3. si tampoco, la PORTADA de capítulo anterior en el documento (6.1 y 6.3 no tienen padre propio; su padre es «WEIGH-IN», `SEC-0085`).
* **Hermanos:** apartados con el mismo padre, ordenados por distancia en el documento.
* **Tablas vinculadas** (`table_unit_ids`): tablas contenidas en la semilla, en su padre y en los hermanos elegidos.
* **Referencias explícitas:** aristas `references_table` del grafo.
* **Reglas de ensamblado:**
  * se deduplican las unidades;
  * se conserva el orden: primero la evidencia y los relacionados del motor, después la expansión en el orden de las semillas;
  * hay un tope global de unidades añadidas.
* **Independencia de los datos:** nada depende de IDs, números de artículo ni preguntas.

## 1. Inventario de reglas fijas

Las 18 IDs `SOR-2026-08-P…` de `src/rre_engine.py` se agrupan en **7 bloques**.

**Fuera del RRE:**
* `src/rag_engine.py` y `src/response_structurer.py` tienen una ID cada uno; no intervienen en la recuperación del RRE.
* `NormativeSemanticRanker` y `RefereeCommandDisambiguator` no tienen IDs.

**Bloques complementarios.** Se miden también dos bloques que **no llevan IDs pero sí páginas fijas**. Ninguno forma parte de las 18.

**Momento de aplicación.** Todos los bloques actúan sobre `rrf_scores`:
* después de la fusión RRF y de la bonificación multicanal;
* antes del top-k, de R1, del cosido y de la expansión por grafo.

| Bloque | Líneas | IDs → apartado | Disparador (consulta) | Efecto | Disparos en DEV |
|---|---|---|---|---|---|
| FRONTERA | 1035-1048 | P174-S190 → art. 17; P152-S179 → art. 6*; P151-S178 → art. 5 | «límite/seguridad/fuera» + osaekomi/ne-waza | +0,08 a +0,12, solo si el pasaje ya es candidato | 0 |
| PUENTE | 1119-1128 | P166-S187, P167-S187 → art. 14 | cabeza + (puente o defensa) | inyecta 0,025; págs. 166-167 con «bridge/cervical» +0,12 (+0,07 cadetes) | 0 |
| HEAD_DIVING | 1131-1143 | P190-S197 → 18.2.1; P190-S198 → 18.2.2 | cabeza + (dive/throw/hansoku **o** ni defensa ni conmoción) | inyecta 0,025; pág. 190 +0,06 a +0,17 | **4** |
| CADETE | 1156-1178 | P188-S196, P189-S196 → 18.1.4 | cadete/U18, **o** (defensa/throw/senior/junior) + cabeza | inyecta 0,035; págs. 188-189 +0,04 a +0,22; art. 5 ×0,20 | **6** |
| CONDUCTA | 1186-1200 | P193-S198, P190-S198 → 18.2.2 | insulto/agresión/conducta… | +0,22 (base 0,040); 11 páginas, art. 4 y gestos ×0,10 | 0 |
| F1_SEC2 | 1300-1304 | P038-S042…P039-S047 → 2.5.1-2.5.5.1 | «página N» y la página es una plantilla F1.3.6-23 | +0,08 al apartado 2.5.x | 0 |
| LATERAL | 1338-1341 | P168-S188, P169-S188 → art. 15 | costado/lateral + puntuación | +0,12. **Solo con `semantic_ranker`**: apagado en la evaluación y **activo en producción** (`ada_assistant.py:127`) | 0 (inactivo) |
| *CABEZA_ATEN* (sin ID) | 1146-1153 | págs. 202, 138, 149, 150 | cabeza y sin conmoción | pág. 202 ×0,65; págs. 138/149/150 ×0,70 | **4** |
| *KUMIKATA* (sin ID) | 1203-1244 | págs. 137-151, 115-127, 250-275, 178-185 | consultas de agarre | ×0,20 / ×1,40 y +0,18 a +0,25 por página | 0 |

\* El comentario del código dice «Art. 5(d) P152», pero ese pasaje tiene `article_id` = `Article 6`. Su texto empieza con el 5(d) («If during ne-waza outside the contest area…»), porque la página mezcla los dos artículos.

**Propósito inferido del código y sus comentarios.** Son atajos temáticos escritos a mano. Llevan a la página del artículo «correcto» ante palabras clave (frontera, puente, head diving, cadetes, conducta, plantillas F1.3) y atenúan páginas que compiten con ellas.

**Disparos en DEV.** De las 82 consultas, solo disparan **HEAD_DIVING, CADETE y CABEZA_ATEN**, en 5 preguntas × 2 formas:
* CADETE en CAT-003, CAT-007 y SCO-019;
* HEAD_DIVING y CABEZA_ATEN en DIR-018 y EXC-005.

Los otros seis bloques no se activan nunca en DEV, así que su efecto aquí no se puede medir.

## 2. Ablación individual y conjunta

Datos: R@5 / R@10 / MRR@10 / paquete sobre las 62 respondibles, con el criterio por texto.

| Config. | R@5 | R@10 | MRR@10 | Paquete |
|---|---|---|---|---|
| **B** | 0,839 | 0,871 | 0,584 | 0,839 |
| B-sin-HEAD_DIVING | 0,839 | 0,871 | 0,596 | 0,839 |
| B-sin-CADETE | 0,839 | 0,871 | 0,609 | 0,839 |
| B-sin-CABEZA_ATEN | 0,839 | 0,871 | 0,593 | 0,839 |
| B-sin-{FRONTERA, PUENTE, CONDUCTA, F1_SEC2, LATERAL, KUMIKATA} | 0,839 | 0,871 | 0,584 | 0,839 |
| **B-sin-reglas** (7 bloques con ID) | 0,839 | 0,871 | **0,622** | 0,839 |
| **B-sin-todo** (los 9 bloques) | 0,839 | 0,871 | **0,646** | 0,839 |
| **SW** | 0,839 | 0,919 | 0,677 | 0,855 |
| SW-sin-HEAD_DIVING | 0,855 | 0,952 | 0,689 | 0,871 |
| SW-sin-CABEZA_ATEN | 0,871 | 0,952 | 0,687 | 0,887 |
| SW-sin-CADETE | 0,839 | 0,919 | 0,677 | 0,855 |
| SW-sin-{resto} | 0,839 | 0,919 | 0,677 | 0,855 |
| **SW-sin-reglas** | **0,855** | **0,952** | **0,689** | **0,871** |
| **SW-sin-todo** | **0,887** | **0,952** | **0,718** | **0,903** |
| SW-traducidas (diagnóstico) | 0,839 | 0,919 | 0,639 | 0,855 |

Con el criterio por IDs, B pasa de MRR 0,539 a 0,577 sin las reglas con ID y a 0,602 sin ninguna; R@5 y el paquete se quedan en 0,839.

**Resultado A.**
* **Ninguna ablación empeora ninguna pregunta**, ni en B ni en SW.
* **En B**, las reglas que disparan solo empujan hacia abajo el ancla correcta: MRR +0,038 sin las reglas con ID y +0,062 sin todas. R@5 y el paquete no cambian.
* **En SW**, las reglas con ID siguen actuando aunque sus IDs no existan en las unidades. Lo hacen por sus condiciones de página, como la bonificación a la página 190 con «hansoku-make», y quitarlas mejora todas las métricas.

## 3. Variantes de expansión (experimento B)

| Variante | Contenido | Límites |
|---|---|---|
| B1 | + padre | tope 8 unidades |
| B2 | + padre + hermanos | S = 2 hermanos más cercanos, tope 8 |
| B3 | B2 + tablas contenidas (`table_unit_ids`) | igual |
| B4 | B3 + tablas referenciadas (`references_table`) | igual |
| B2g/B3g/B4g | hermanos solo si están en el top-20 de la **misma** recuperación | S = todos, tope 8 |
| **B4c** | B4 con hermanos filtrados por el top-20 | S = 2, tope 4. **Elegida a posteriori** sobre una rejilla de 18 puntos (S ∈ {1, 2, todos}, tope ∈ {4, 8, ∞}, con o sin filtro), vista ya la rejilla sobre SW |

* Los límites S = 2 y tope = 8 se fijaron **antes** de ver resultados.
* La expansión se aplica sobre SW, SW-sin-reglas y SW-sin-todo.
* Como solo añade contexto, **no cambia R@5, R@10 ni MRR**: solo el paquete.

## 4. Métricas

Datos: las 62 respondibles; las columnas «DICT / LLM» dan cada forma por separado.

| Config. | R@5 | R@10 | MRR@10 | Paquete | Caract. paquete (media) | Unid. paquete | R@5 DICT / LLM | MRR DICT / LLM | Paquete DICT / LLM |
|---|---|---|---|---|---|---|---|---|---|
| **B** | 0,839 | 0,871 | 0,584 | 0,839 | 16 449 | 5,5 | 0,806 / 0,871 | 0,578 / 0,59 | 0,806 / 0,871 |
| B-sin-reglas | 0,839 | 0,871 | 0,622 | 0,839 | 16 275 | 5,31 | 0,806 / 0,871 | 0,604 / 0,64 | 0,806 / 0,871 |
| B-sin-todo | 0,839 | 0,871 | 0,646 | 0,839 | 16 277 | 5,31 | 0,806 / 0,871 | 0,628 / 0,664 | 0,806 / 0,871 |
| **SW** | 0,839 | 0,919 | 0,677 | 0,855 | 11 637 | 6,68 | 0,806 / 0,871 | 0,637 / 0,716 | 0,806 / 0,903 |
| SW-sin-reglas | 0,855 | 0,952 | 0,689 | 0,871 | 11 640 | 6,58 | 0,839 / 0,871 | 0,643 / 0,736 | 0,839 / 0,903 |
| SW-sin-todo | 0,887 | 0,952 | 0,718 | 0,903 | 11 542 | 6,6 | 0,871 / 0,903 | 0,671 / 0,764 | 0,871 / 0,935 |
| SW-traducidas | 0,839 | 0,919 | 0,639 | 0,855 | 11 546 | 6,74 | 0,806 / 0,871 | 0,604 / 0,675 | 0,806 / 0,903 |
| SW+B1 | 0,839 | 0,919 | 0,677 | 0,855 | 12 388 | 9,21 | 0,806 / 0,871 | 0,637 / 0,716 | 0,806 / 0,903 |
| SW+B2 | 0,839 | 0,919 | 0,677 | 0,871 | 18 028 | 13,39 | 0,806 / 0,871 | 0,637 / 0,716 | 0,839 / 0,903 |
| SW+B3 | 0,839 | 0,919 | 0,677 | 0,871 | 18 223 | 13,77 | 0,806 / 0,871 | 0,637 / 0,716 | 0,839 / 0,903 |
| SW+B4 | 0,839 | 0,919 | 0,677 | 0,871 | 18 513 | 13,79 | 0,806 / 0,871 | 0,637 / 0,716 | 0,839 / 0,903 |
| SW+B2g | 0,839 | 0,919 | 0,677 | 0,887 | 18 886 | 12,92 | 0,806 / 0,871 | 0,637 / 0,716 | 0,871 / 0,903 |
| SW+B3g | 0,839 | 0,919 | 0,677 | 0,887 | 19 112 | 13,44 | 0,806 / 0,871 | 0,637 / 0,716 | 0,871 / 0,903 |
| SW+B4g | 0,839 | 0,919 | 0,677 | 0,887 | 19 180 | 13,44 | 0,806 / 0,871 | 0,637 / 0,716 | 0,871 / 0,903 |
| SW+B4c | 0,839 | 0,919 | 0,677 | 0,871 | 15 207 | 10,35 | 0,806 / 0,871 | 0,637 / 0,716 | 0,839 / 0,903 |
| SW-sin-reglas+B4 | 0,855 | 0,952 | 0,689 | 0,871 | 18 310 | 13,63 | 0,839 / 0,871 | 0,643 / 0,736 | 0,839 / 0,903 |
| SW-sin-reglas+B4c | 0,855 | 0,952 | 0,689 | 0,871 | 15 130 | 10,26 | 0,839 / 0,871 | 0,643 / 0,736 | 0,839 / 0,903 |
| SW-sin-todo+B4 | 0,887 | 0,952 | 0,718 | 0,903 | 17 989 | 13,66 | 0,871 / 0,903 | 0,671 / 0,764 | 0,871 / 0,935 |
| **SW-sin-todo+B4c** | **0,887** | **0,952** | **0,718** | **0,903** | **15 011** | 10,27 | 0,871 / 0,903 | 0,671 / 0,764 | 0,871 / 0,935 |
| SW-sin-todo+B4g | 0,887 | 0,952 | 0,718 | 0,919 | 18 794 | 13,31 | 0,871 / 0,903 | 0,671 / 0,764 | 0,903 / 0,935 |

**Tiempos.**
* **Recuperación:** 45-50 ms en todas las configuraciones (`retrieve`); sin diferencia apreciable por desactivar reglas.
* **Expansión:** ≤ 0,045 ms por consulta.
* **Inicialización:** 16,8 s para los 5 motores.

## 5. Diagnóstico de SCO-020

Consulta: «Do senior athletes get any weight tolerance at the official weigh-in of an individual event?». Las cifras son la posición en el paquete; son idénticas en DICT y LLM.

| Config. | 6.1 | 6.2.3 | 6.3 | tabla 6.3.4 | 6.4.2 | 6.1 + 6.3 | + tabla | Caract. |
|---|---|---|---|---|---|---|---|---|
| B (páginas) | (pág. 75 en 5) | — | (pág. 79 en 3) | — | — | solo por página | ✗ | 18 464 |
| SW / SW-sin-reglas / SW-sin-todo | 5 | — | — | — | 2 | ✗ | ✗ | 15 183 |
| SW-traducidas | 5 | — | — | — | 2 | ✗ | ✗ | 15 183 |
| +B1 | 5 | — | — | — | 2 | ✗ | ✗ | 15 898 |
| +B2 | 5 | 14 | 11 | — | 2 | ✓ | ✗ | 19 490 |
| +B3 | 5 | 16 | 11 | — | 2 | ✓ | ✗ | 19 732 |
| **+B4** | 5 | — | 11 | **12** | 2 | ✓ | **✓** | 20 847 |
| +B4g | 5 | — | 11 | 15 | 2 | ✓ | ✓ | 21 452 |
| **+B4c** | 5 | — | 11 | **12** | 2 | ✓ | **✓** | 19 116 |

**B, con páginas.** Contiene los textos de 6.1 (pág. 75) y de 6.3 (pág. 79), pero sin identidad propia:
* la página 79 mezcla 6.2.5, 6.3 y 6.3.1-6.3.3;
* la tabla 6.3.4 (pág. 80) no aparece.

Según el criterio de la tarea, no basta.

**SW.** La tabla del caso dice exactamente qué entra y qué no; el motivo es este:
* 6.1 entra por R1;
* 6.3 queda fuera del top-5 (en el puesto 10 de la evidencia);
* la tabla 6.3.4 no se recupera.

**B2.** Aporta 6.3 como hermano estructural, del mismo padre «WEIGH-IN»: entra vía 6.5, que está en el puesto 1. Lo hace con un criterio genérico de distancia, sin nada específico del caso.

**B4.** Añade la tabla 6.3.4 (`TAB-0030`), porque 6.3 la cita expresamente (arista `references_table`).

**Identidades.** 6.1, 6.3, la tabla 6.3.4 y 6.4.2 llegan como unidades distintas, cada una con su etiqueta y su página.
* 6.4.2 (el distractor del +5 % mixto) sigue en la posición 2.
* El fragmento del +5 % aparece en las posiciones 1 y 2, en 6.5 y en 6.4.2.

**Huecos.**
* 6.2.3 solo aparece en B2/B3, por ser hermano de 6.2.4; en B4 lo deja fuera el tope.
* El apartado 6.3.4 en sí no se entrega: solo su tabla.

**Coste.** En esta pregunta, todas las variantes que cumplen el criterio conjunto superan el paquete de B (19 116 frente a 18 464 caracteres en B4c).

## 6. Ganancias y regresiones por pregunta

**EXC-005: «May an athlete compete with the head covered?»** El ancla está en la pág. 202. Valores: pos@k10, en DICT y LLM por igual.
* **B: 5.** Con la palabra «head» y sin términos de conmoción se disparan dos bloques:
  * HEAD_DIVING inyecta `P190-S197` (18.2.1, head diving), que queda **1.º**;
  * CABEZA_ATEN multiplica por **0,65 la página 202**, justo la del ancla.
* B-sin-HEAD_DIVING: 4. B-sin-CABEZA_ATEN: 2. **B-sin-todo: 1.**
* SW: fuera del top-10. SW-sin-reglas: 9. SW-sin-CABEZA_ATEN: 3. **SW-sin-todo: 1.**
* **Conclusión:** la pérdida de EXC-005 en SW frente a B, atribuida antes a la regla `P190-S197`, la causa sobre todo la **atenuación fija de la página 202**. La inyección de HEAD_DIVING la agrava.

**DIR-018: «¿Qué debe hacer el árbitro si un atleta recibe un fuerte impacto en la cabeza?»** El ancla está en la pág. 197. Se disparan los mismos dos bloques, porque «impacto» no está en la lista de conmoción.
* B: 3 (DICT) / 2 (LLM). Sin las reglas: 2 / 1.
* SW: 6 / 2. **SW-sin-reglas: 5 / 1**, y vuelve al top-5 en DICT.
* **Conclusión:** la causa es HEAD_DIVING, que inyecta `P190-S197` en el puesto 1.

**CAT-003 y CAT-007:** consultas sobre U18/cadetes que no tratan de técnica (cinturón de kata, puntos WRL). CADETE inyecta `P188-S196` (18.1.4) en el puesto 1. Sin CADETE, el ancla sube:
* CAT-003: 4→3 y 2→1;
* CAT-007: 2→1 en las dos formas.

**SCO-019:** sin CADETE, en SW pasa de 8 a 7.

**Variantes candidatas frente a B** (R@5 y paquete):

| Variante | Ganadas | Perdidas |
|---|---|---|
| SW+B4 | SCO-013 ×2, SCO-014 ×2 | R@5: CAT-001/LLM, DIR-018/DICT, EXC-005 ×2; paquete: DIR-018/DICT, EXC-005 ×2 |
| SW-sin-reglas+B4 / +B4c | SCO-013 ×2, SCO-014 ×2 | R@5: CAT-001/LLM, EXC-005 ×2; paquete: EXC-005 ×2 |
| **SW-sin-todo+B4c** | SCO-013 ×2, SCO-014 ×2 | R@5: **CAT-001/LLM** (1→7); paquete: **ninguna** |
| SW-sin-todo+B4g | además SCO-019/DICT en paquete | igual que la anterior |

**Bajadas que persisten en las variantes sobre apartados.** Vienen de la segmentación, no de la expansión ni de las reglas; son las mismas en SW-sin-todo:
* CAT-001/LLM 1→7;
* **DIR-005 1→9 ×2;**
* DIR-008/DICT 1→3;
* DIR-015/LLM 2→5;
* DIR-018/DICT 3→5;
* EXC-003 6→9 ×2;
* EXC-006/DICT 1→4;
* SCO-026 1→5 y 1→3.

**Mejoras en pos@10.** Hay 25 frente a B; entre ellas SCO-013 y SCO-014 (de fuera del top-10 a 1-2), EXC-009 5→1 y DIR-017 3→1.

**La expansión, frente a su propia base:** solo gana paquete en DIR-018/DICT (B2-B4) y SCO-019/DICT (variantes «g»). Ninguna pérdida.

## 7. No respondibles (20)

* **Estados sin cambio:** en todas las configuraciones hay 17 SUCCESS y 3 ABSTAIN OUT_OF_DOMAIN, sin cambios de estado frente a B. Ni las reglas ni la expansión alteran la abstención.
* **Paquete medio de las 17 SUCCESS, frente a B (15 654 caracteres):**

  | Config. | Caract. |
  |---|---|
  | B | 15 654 |
  | SW | 11 435 |
  | +B4c | 13 672 |
  | +B4 | 17 367 |
  | +B4g | 18 291 |

  B4 y B4g dan más contexto que B a preguntas que deberían rechazarse.

## 8. Tamaño y composición del paquete

**Paquete medio en las respondibles:**

| Config. | Caract. | Diferencia vs B | Unidades |
|---|---|---|---|
| B | 16 449 | — | 5,5 |
| SW | 11 637 | −29 % | 6,7 |
| +B1 | 12 388 | — | 9,2 |
| +B2-B4 | ≈ 18 000-18 500 | **+10-13 %** | 13,4-13,8 |
| +B4g | 19 180 | **+17 %** | — |
| +B4c | 15 207 (SW) / 15 011 (SW-sin-todo) | −8 / −9 % | 10,3 |

**Composición del paquete de SCO-020 con +B4c** (12 unidades):
* **evidencia:** 6.5, 6.4.2, 6.4.3, 6.2.4, 6.1;
* **relacionados del grafo:** tablas de 6.5 ×2 y de 6.4.1;
* **expansión:** «WEIGH-IN» (padre), 6.4, **6.3** y **tabla 6.3.4**.

**Valor de cada nivel:**
* B1 añade casi solo portadas o encabezados de capítulo, con poco texto y ninguna ganancia;
* el valor está en los hermanos (B2) y en las tablas citadas (B4).

**Rejilla B4 sobre SW (paquete / caracteres):**

| S | Tope | Filtro | Paquete | Caract. |
|---|---|---|---|---|
| 1 | 4 | sí | 0,871 | 14 710 |
| 2 | 4 | sí | 0,871 | 15 207 |
| 2 | 8 | sí | 0,887 | 17 594 |
| todos | ∞ | no | 0,887 | 40 315 |

Lista completa en `results.json` → `rejilla_B4`. Con S = 1 no se recupera 6.3 en SCO-020: entre 6.1 y 6.3 está el encabezado vacío 6.2 (22 caracteres).

## 9. Trazabilidad

* **Comprobación:** las 248 unidades distintas entregadas en algún paquete de apartados tienen:
  * `source_sha256` igual al del PDF (`9426b10d…`);
  * `source_spans` no vacíos, con páginas dentro de `[pdf_page_index, page_end]`;
  * `text_sha256` igual al SHA-256 de `text_original`.
* **Resultado:** 0 fallos.
* **Datos de expansión:** solo se usan campos de `units.jsonl` y aristas del grafo de apartados, sin generar texto nuevo.
* **Limitación:** `source_sha256_verified` del motor sigue siendo False en el directorio experimental. Es la misma limitación de ruta del informe de segmentación.

## 10. SHA-256 antes y después

Los 17 archivos tienen el mismo SHA-256 antes y después (`integridad.identicos = true`).

| Archivo | SHA-256 |
|---|---|
| `src/rre_engine.py` | `a0318e88b4e98b271a38710c8b99768ad4cab2bdbe5ec0434f7333fce2841c78` |
| `data/processed/rebuild_2026_08_corrected/passages_candidate.json` | `7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b` |
| `…/dense_embeddings_candidate.npy` | `124ced95fb9e152ce586dec9f30a1eb98dc14ee385c0bc335a2055357f73a617` |
| `…/vector_index_candidate.json` | `e182c77e0775472eb73d22ab92b15d026d067cbf6264fb8b25b207479c4668eb` |
| `…/knowledge_graph_candidate.json` | `95d5a67936cf48d3bc79b69bf370bb1a83a255f938a7322e0dae256450dde215` |
| `…/dense_embeddings_meta.json` | `c96b214bc14801ad903d58e0245d48c008d65ac051d339fd4e6b65e30709160e` |
| `data/derived/article_units_v1/units.jsonl` | `9c54a9fd8194d9c0895ee457cce7460db5d9ec24d3b5169ac13efdccc945f5f1` |
| `data/eval/benchmark_v2/splits/dev.jsonl` | `b2bb36ccfb5849d552d2b8f8d7c9db1266cf7889d0b82cf23c54a37af62ef191` |
| `data/eval/fase11/retrieval_experiments_dev.json` | `b89460bc9f1c4ac86263717a1821979556f10837ba5da48b639f7d0c3f81d670` |
| `experiments/segmentacion_apartados_2026/units.jsonl` | `812aa19d1838c9ba96b761194e0ef9ff7e7818ddae2324d554928c7de920f515` |
| `…/index/passages_candidate.json` | `71cdb47ac80febbe66bfa8547be071978c586278012243c351b1fccdcec8f942` |
| `…/index/dense_embeddings_candidate.npy` | `48e89704bedbcc383434814090dbb92e75a2bb6ead98819d97ec012b93ada52a` |
| `…/index/dense_embeddings_meta.json` | `f72b5beb3b1aea7d9e7ab74c7febd5fcd56052d1bbb350e6550761da76238c76` |
| `…/index/vector_index_candidate.json` | `b8832c3cefcc20614141bd60fb99e29ce3d60395ab691768c37f7bf76a6ae812` |
| `…/index/knowledge_graph_candidate.json` | `eea04fa789d0e2ab1090eac5f340e98f78022cff3f2a376f13c64f0516642928` |
| `…/index/windows_emb.npy` | `5bde28a548da33d30c89295f8be43730cad7f86aca9203a7d872c9226d44d206` |
| `…/index/windows_meta.json` | `3a2618f1f5d97320199ec210d29e5da114aef719ea0b9ee67d3fe37be13a81e4` |

**Variantes generadas en memoria** (no escritas como módulo; el diff está en los `.patch`):

| Variante | SHA-256 |
|---|---|
| ablación | `e3b2e2f8bb92240fac033f450ba176422a40c390b9ade02829c2e193f8c59e15` |
| traducida | `2a61ad23efdabc07add572173419e2ffb51b33707b47a51912e67e35862fc5cc` |

## 11. Recomendación y limitaciones

### ¿Se pueden expresar las reglas como metadatos estructurales? (A.6)

**Prueba.** SW-traducidas sustituye mecánicamente cada ID por la unidad-apartado que la contiene, por ejemplo `P190-S197` → `SEC-0199` (18.2.1).

**Resultado:** **empeora** a SW.
* MRR: 0,677 → 0,639.
* Regresiones: CAT-003 ×2, CAT-007 ×2, DIR-018 ×2 y SCO-019/LLM.

**Conclusión.** Expresar las reglas por número de apartado las haría portables, pero seguirían siendo reglas por artículo, que las restricciones del proyecto excluyen. Además, en DEV no aportan nada: solo disparan en falso. **No se recomienda traducirlas.** La alternativa genérica es la expansión estructural del experimento B, que no depende de IDs.

### Criterios de aceptación

| Criterio | SW+B4 (fijada a priori) | SW-sin-reglas+B4 | SW-sin-reglas+B4c | SW-sin-todo+B4c |
|---|---|---|---|---|
| SCO-020: 6.1 + 6.3 (+ tabla 6.3.4) juntos | ✓ | ✓ | ✓ | ✓ |
| Distingue 6.1, 6.3 y 6.4.2 | ✓ | ✓ | ✓ | ✓ |
| Mantiene o mejora B (globalmente) | ✓ | ✓ | ✓ | ✓ (R@5 +0,048, MRR +0,134, paquete +0,064) |
| Sin regresiones relevantes | ✗ EXC-005 ×2, DIR-018 | ✗ EXC-005 ×2 | ✗ EXC-005 ×2 | ✗ CAT-001/LLM en R@5 (1→7); DIR-005 1→9 ×2 |
| No perjudica a las no respondibles | ✓ estados; ✗ +11 % de contexto | ✓ / ✗ | ✓ | ✓ |
| Contexto igual o menor sin perder evidencia | ✗ +13 % | ✗ +11 % | ✓ −8 % global (✗ en SCO-020: +3,5 %) | ✓ −9 % global (✗ en SCO-020: +3,5 %) |
| Sin reglas por pregunta o ID | ✗ (el RRE las mantiene) | ✓ por ID; quedan reglas por página | ✓ por ID; quedan reglas por página | ✓ |
| Trazabilidad al PDF | ✓ | ✓ | ✓ | ✓ |
| Fijada antes de ver resultados | ✓ | ✓ | ✗ (B4c a posteriori) | ✗ (B4c a posteriori; además retira bloques fuera de las 18 IDs) |

**Ninguna variante cumple todos los criterios. No se recomienda integrar.**

### Qué queda establecido (solo DEV)

1. **Las reglas fijas del RRE no aportan en DEV y perjudican en los casos donde disparan.**
   * Retirarlas mejora el MRR de B (0,584 → 0,646) sin ninguna pérdida.
   * Las pérdidas de SW frente a B en EXC-005 y DIR-018 las explican HEAD_DIVING y la atenuación fija de la página 202, no la segmentación.
   * Seis de los nueve bloques no disparan nunca en DEV, así que su efecto no está medido.
2. **La expansión jerárquica genérica resuelve SCO-020** sin tocar IDs ni números de artículo.
   * Hermanos por padre estructural, más tablas citadas por `references_table`.
   * Solo es compatible con un contexto menor que B si se limita con fuerza (B4c). Esos límites se eligieron a posteriori.
3. **La mejor combinación medida es SW-sin-todo+B4c**, frente a B (0,839 / 0,871 / 0,584 / 0,839):

   | Métrica | SW-sin-todo+B4c |
   |---|---|
   | R@5 | 0,887 |
   | R@10 | 0,952 |
   | MRR@10 | 0,718 |
   | Paquete | 0,903 |
   | Contexto | −9 % |

   Mantiene las regresiones de ranking heredadas de la segmentación (DIR-005, CAT-001, SCO-026, EXC-006).

### Siguientes pasos posibles

Requieren autorización expresa:
* decidir sobre la retirada de los bloques de `src/rre_engine.py`, como cambio de código revisado;
* validar B4c en un conjunto distinto de DEV (nunca `test_sealed` sin autorización) para descartar sobreajuste de los límites;
* investigar DIR-005 y CAT-001 en la segmentación.

### Limitaciones

* **Muestra pequeña.** Son 62 respondibles en DEV, y 1 pregunta = 0,016. Las diferencias de una o dos preguntas no son concluyentes.
* **Configuración distinta de producción.** La evaluación usa la configuración de los informes anteriores (`semantic_ranker`, desambiguador y anclas negativas apagados). Producción los activa (`ada_assistant.py:124-131`): en producción LATERAL está activa y hay reordenaciones adicionales que aquí no se miden.
* **Constructor TF-IDF reconstruido.** El de los apartados sigue siendo una reconstrucción (deriva −0,033 en R@5 medida con Bc en el informe previo).
* **B4c elegido a posteriori.** Está tomado de una rejilla vista sobre los mismos datos; sus límites no están validados.
* **Ablaciones por bloque.** Neutralizan el bloque entero: inyección, bonificaciones y atenuaciones, que son inseparables en el código. FRONTERA, PUENTE, CONDUCTA, F1_SEC2, LATERAL y KUMIKATA no se ejercitan en DEV.
* **Cobertura de la expansión.** No recupera el apartado 6.3.4 ni, con el tope, 6.2.3. Tampoco ordena dentro del paquete por pertinencia: añade al final.
* **Directorio compartido.** Otro proceso escribió en el directorio experimental durante la ejecución; ver el aviso inicial.

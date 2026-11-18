# Análisis de la agregación de ventanas y de la regresión SCO‑020 (2026-11-17)

**Alcance:** análisis local, sin LLM y sin red, sobre el split DEV leído desde `dev.jsonl`; `test_sealed` no se abrió. No se modificaron `src/`, `data/processed/`, el benchmark, el DIG ni los interruptores.
**Script:** `experiments/ventanas_2026/agregaciones.py`. Resultados por consulta en `experiments/ventanas_2026/agregaciones_results.json`.
**Base:** rama `exp/r3-dig-v2`, HEAD `d126873`. R3 (`RRE_ENABLE_SCOPE_PREFERENCE`) estaba desactivado.

---

## 1. Evidencia normativa (corpus canónico SOR 2026‑08, `SOR-2026-08-14-ENG`)

| Disposición | Pasaje · página | Texto literal (extracto) |
|---|---|---|
| **6.1** Límites de peso, eventos individuales | `P075-S086` · p. 75 | «Athletes competing in junior and senior events must be within the weight limits of a category … there is no additional weight tolerance.» |
| **6.2.3** Pesaje oficial | `P077-S090` · p. 77 | «For IJF events, the official weigh-in is scheduled one day before the competition at 16:00 local time.» |
| **6.3** Pesaje aleatorio | `P079-S093` · p. 79 (texto idéntico en S094 a S097) | «… the random weigh-in will open one hour before the start of the competition each day. … The weight of the athlete cannot be more than 5 % higher than the official maximum weight limit of the category (refer to table 6.3.4 …).» |
| Tabla 6.3.4 | `P080-S098` · p. 80 | «Weight Categories for the Random Weigh-in with Tolerances — Senior and Junior Women +5% tolerance …» |
| **6.4.2** Equipo mixto tras una prueba individual (distractor del benchmark) | `P081-S100` · p. 81 y `P082-S100` · p. 82 | «A +5% tolerance applies only to the minus weight categories.» |

**Verificación:**
* **Pesaje oficial:** el sénior individual **no tiene tolerancia adicional** (6.1). El pesaje oficial se celebra el día anterior a la competición (6.2.3).
* **Pesaje del día de competición:** el +5 % pertenece al **pesaje aleatorio** (6.3 y la tabla 6.3.4), que se hace el día de la competición, es decir, el día siguiente al pesaje oficial. **No pertenece al pesaje oficial.**
* **Otro +5 % distinto:** 6.4.2 contiene un +5 % solo para las categorías minus del equipo mixto. Es el distractor de ámbito del benchmark.

**Limitaciones de la fuente:**
* El SOR no usa la expresión «pesaje del día siguiente»; habla de *random weigh‑in*.
* El +5 % del pesaje aleatorio no se limita a los sénior: la tabla lo aplica a «Senior and Junior».
* Los seis pasajes tienen `review_status = extracted` y `approved_by = null`.
* El pasaje de la p. 80 lleva el metadato de 6.4, pero su contenido es la tabla 6.3.4. Es un caso de H‑02, la unidad página frente a la unidad apartado.
* No se usó SHADOW.

---

## 2. Diagnóstico de la regresión de SCO‑020

* **Consulta:** la `query_used` es idéntica en DICT y en LLM («Do senior athletes get any weight tolerance at the official weigh-in of an individual event?»), así que las dos formas se comportan igual.
* **Ancla:** `P075-S086`.

| Canal | B (actual + R1) | D (ventanas, máximo + R1) |
|---|---|---|
| TF‑IDF top‑25 | **ausente** | **ausente** |
| Denso (sin filtrar / tras filtrar el historial H1.1) | 2 / 2 · cos 0,5587 | 14 / 9 · cos 0,5619 |
| Campeón R1 (denso 1.º‑2.º con cos ≥ 0,55) | **sí, se añade** | no |
| Posición final del ancla (top‑10) | 10, rescatada a 5 por R1 | fuera |

**Ventanas del ancla:** son dos, de los tokens 0‑220 (cos 0,5619) y 190‑343 (cos 0,508). La frase «no additional weight tolerance» está en la primera, igual que en el embebido truncado original. Por eso **la puntuación del ancla apenas cambia** (+0,003).

**Causa (hecho medido):**
* **El ancla depende solo de R1.** No aparece en el canal léxico, y la fusión RRF la deja en el puesto 10 tanto en A como en B. R1 la rescata únicamente porque es la 2.ª del canal denso.
* **El máximo favorece a los pasajes con más ventanas.** Con el máximo, un pasaje con más ventanas tiene más oportunidades de puntuar alto, un sesgo de comparaciones múltiples. En las 82 consultas, la ganancia media de similitud (máximo de ventanas menos original) crece con el número de ventanas: +0,000 con 1, +0,013 con 2, +0,030 con 3 y +0,039 con 4.
* **13 pasajes adelantan al ancla.** Todos tienen entre 2 y 5 ventanas, y su ganancia está entre +0,03 y +0,28. Los mayores son:
  * los pasajes H1.1 del historial de versiones (pp. 276‑282, de +0,19 a +0,28), que luego se filtran;
  * 6.2.5 *Compliance Rules* (+0,26);
  * 6.4.1 y 6.4.2 p. 81 (+0,19);
  * 6.4.3 *Olympic Games Mixed Team* (+0,11).
* **Resultado:** tras el filtro, el ancla baja al puesto 9, deja de ser campeona y R1 ya no la rescata.

**Separación entre las dos reglas** en el paquete top‑5, igual en las dos formas:

| Config. | 6.1 sin tolerancia (ancla) | 6.2.3 oficial | 6.3 aleatorio +5 % | 6.4.2 mixto +5 % |
|---|---|---|---|---|
| A | no | sí | sí | sí (p. 82) |
| **B** | **sí** | sí | sí | sí (p. 82) |
| D | **no** | sí | **no** | sí (p. 82) |
| T2 | no | sí | no | sí (p. 82) |
| T3 / DISP / DISP_0,25 / DISP_1,0 | no | sí | sí | sí (p. 82) |

**En D la evidencia queda desequilibrada.** Desaparecen la regla de «sin tolerancia» y la del pesaje aleatorio, mientras que se conservan la tolerancia del equipo mixto (6.4.2), 6.4.3, 6.5 y 6.2.5. **Con ese paquete un generador solo vería reglas con tolerancia del +5 % y ninguna regla que la niegue para el pesaje oficial individual.** Es un riesgo directo de trasladar el +5 % al pesaje oficial. Sin LLM no se ha comprobado si el generador cometería ese error.

---

## 3. Alternativas de agregación (todas con R1, sin reglas por pregunta)

| Código | Agregación por pasaje |
|---|---|
| D | Máximo coseno de las ventanas (actual) |
| T2 | Media de las 2 mejores ventanas, o de las que haya si son menos |
| T3 | Media de las 3 mejores ventanas |
| DISP | Máximo − λ·desviación típica de sus ventanas, con **λ = 0,5 fijado a priori** |
| DISP_0,25 y DISP_1,0 | Sensibilidad de λ. Solo informativas: elegir λ sobre DEV sería ajustar |

Las demás condiciones no cambian: la proyección ES→EN, el umbral > 0,15, el top‑25 y R1 por defecto. El OODDetector conserva sus embeddings originales (comprobado).

### Posición del ancla de SCO‑020

| Config. | Rango denso tras el filtro | Posición final | ¿Paquete? |
|---|---|---|---|
| B | 2 | 10 → R1 | **sí** |
| D | 9 | fuera | no |
| T2 | 7 | fuera | no |
| T3 | 5 | fuera | no |
| DISP | 6 | fuera | no |
| DISP_0,25 | 9 | fuera | no |
| DISP_1,0 | 5 | fuera | no |

**Ninguna alternativa recupera el ancla.** Las agregaciones que suavizan el máximo acercan el ancla en el canal denso, pero nunca la devuelven al top‑2 que exige R1.

---

## 4. Métricas globales en DEV (62 respondibles; DICT 31 + LLM 31)

| Config. | R@5 | R@10 | MRR@10 | Denso top‑25 | Paquete |
|---|---|---|---|---|---|
| A actual | 0,774 | 0,839 | 0,539 | 0,726 | 0,774 |
| **B** actual + R1 | 0,839 | 0,839 | 0,539 | 0,726 | 0,839 |
| **D** máximo + R1 | **0,871** | 0,871 | **0,659** | **0,968** | **0,871** |
| T2 | 0,855 | 0,887 | 0,640 | 0,935 | 0,855 |
| T3 | 0,823 | 0,887 | 0,597 | 0,952 | 0,823 |
| DISP (λ = 0,5) | 0,823 | 0,855 | 0,638 | 0,952 | 0,823 |
| DISP_0,25 | 0,871 | 0,903 | 0,650 | 0,952 | 0,871 |
| DISP_1,0 | 0,823 | 0,855 | 0,598 | 0,952 | 0,823 |

Por forma (R@5 / MRR@10):

| Forma | B | D | T2 | T3 | DISP | DISP_0,25 |
|---|---|---|---|---|---|---|
| DICT | 0,806 / 0,527 | 0,839 / 0,638 | 0,839 / 0,615 | 0,806 / 0,568 | 0,806 / 0,624 | 0,839 / 0,633 |
| LLM | 0,871 / 0,552 | 0,903 / 0,679 | 0,871 / 0,666 | 0,839 / 0,627 | 0,839 / 0,653 | 0,903 / 0,666 |

Tiempo medio por `retrieve`: entre 39 y 41 ms en todas las configuraciones.

---

## 5. Ganancias y regresiones por pregunta (paquete top‑5)

| Config. | Frente a B: ganadas | Frente a B: perdidas | Frente a D: ganadas | Frente a D: perdidas |
|---|---|---|---|---|
| D | SCO‑013 ×2, SCO‑014 ×2 | **SCO‑020 ×2** | — | — |
| T2 | SCO‑013 ×2, SCO‑014 ×2 | **SCO‑020 ×2, SCO‑019/LLM** | — | SCO‑019/LLM |
| T3 | SCO‑013 ×2, SCO‑014 ×2 | **SCO‑020 ×2, SCO‑019/LLM, EXC‑005 ×2** | — | SCO‑019/LLM, EXC‑005 ×2 |
| DISP | SCO‑013 ×2, SCO‑014 ×2 | **SCO‑020 ×2, SCO‑019/LLM, EXC‑005 ×2** | — | SCO‑019/LLM, EXC‑005 ×2 |
| DISP_0,25 | SCO‑013 ×2, SCO‑014 ×2 | **SCO‑020 ×2** | — | — |
| DISP_1,0 | SCO‑013 ×2, SCO‑014 ×2 | **SCO‑020 ×2, SCO‑019/LLM, EXC‑005 ×2** | — | SCO‑019/LLM, EXC‑005 ×2 |

**Cambios de posición en el top‑10 frente a B** (detalle completo en `comparaciones` del JSON):
* **D mejora 17 posiciones:**
  * CAT‑003/DICT, de 4 a 2;
  * DIR‑007, de 2 a 1, en las dos formas;
  * DIR‑017, de 3 a 1, en las dos formas;
  * EXC‑009, de 5 a 1, en las dos formas;
  * MLG‑003/DICT, de 3 a 2;
  * MUL‑004/DICT, de 4 a 1, y MUL‑004/LLM, de 3 a 1;
  * SCO‑013 ×2, SCO‑014 ×2, SCO‑021 ×2 y SCO‑022/LLM.
* **D empeora 6:**
  * DIR‑015/LLM, de 2 a 3;
  * MLG‑003/LLM, de 1 a 2;
  * SCO‑010/DICT, de 1 a 2;
  * SCO‑026/DICT, de 1 a 2;
  * SCO‑020, de 10 a fuera, en las dos formas.
* **T2, T3 y los DISP con λ ≥ 0,5:** además empeoran DIR‑005, EXC‑006, CAT‑007 o EXC‑005.
* **EXC‑003** entra en el puesto 10 con T2, T3 y DISP_0,25, pero no llega al top‑5.

---

## 6. Preguntas no respondibles (20)

| Config. | Top‑5 no vacío | Cambios de estado frente a A y a B | Top‑5 distinto del de B |
|---|---|---|---|
| A / B | 17 / 17 | — | 2 / 0 |
| D | 17 | ninguno | 15 |
| T2 | 17 | ninguno | 14 |
| T3 | 17 | ninguno | 13 |
| DISP | 17 | ninguno | 17 |
| DISP_0,25 | 17 | ninguno | 16 |
| DISP_1,0 | 17 | ninguno | 14 |

**Ninguna configuración cambia el estado de una no respondible** ni añade un top‑5 no vacío. En cambio, el **contenido** del top‑5 cambia en entre 13 y 17 de las 20. El efecto sobre la abstención final, que deciden el DIG y el generador, **no se ha medido**.

---

## 7. Recomendación técnica

**Criterios de aceptación aplicados:**

| Criterio | D | T2 | T3 | DISP | DISP_0,25 | DISP_1,0 |
|---|---|---|---|---|---|---|
| Recupera la evidencia de SCO‑020 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Conserva juntas la regla «sin tolerancia» y la del aleatorio (+5 %) | ✗ | ✗ | ✗ (sin 6.1) | ✗ (sin 6.1) | ✗ (sin 6.1) | ✗ (sin 6.1) |
| Sin regresiones relevantes frente a B | ✗ (SCO‑020) | ✗ | ✗ | ✗ | ✗ (SCO‑020) | ✗ |
| Mantiene o mejora DEV global (R@5 ≥ B = 0,839) | ✓ | ✓ | ✗ (0,823) | ✗ (0,823) | ✓ | ✗ (0,823) |
| No perjudica a las no respondibles (estado) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Integridad del corpus y de los índices | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**Conclusión:**
1. **Ninguna de las cuatro agregaciones cumple los criterios.** No se recomienda integrar ninguna.
2. **Entre las probadas, D (el máximo) sigue siendo la mejor en DEV:** R@5 de 0,871 y MRR de 0,659. Suavizarla (T2, T3, DISP) no recupera SCO‑020 y añade pérdidas como SCO‑019/LLM y EXC‑005. DISP_0,25 empata con D en el paquete, pero λ = 0,25 saldría de elegirlo sobre DEV.
3. **El problema de SCO‑020 no está en la agregación sino en el diseño.** El ancla nunca la encuentra la fusión (puesto 10, ausente en TF‑IDF). Solo la salva R1, y R1 usa los rangos del canal denso activo, que con ventanas favorece a los pasajes con más ventanas.

**Hipótesis para un experimento posterior** (no ejecutado; requiere autorización y no usa nada específico de SCO‑020):
* **(a)** Mantener las ventanas para la fusión, pero elegir los campeones de R1 también con el canal denso original, o con la unión de ambos.
* **(b)** Normalizar la similitud de cada pasaje por el número de ventanas, restando la ganancia esperada medida sobre el corpus. Por ejemplo, calibrar con consultas que no sean del benchmark.
* **(c)** Atacar H‑02 con unidades por apartado, para que 6.1, 6.3 y la tabla 6.3.4 no compitan como páginas completas.

Cada hipótesis debe evaluarse con los mismos criterios frente a B, y en particular con la presencia conjunta de 6.1 y 6.3 en SCO‑020.

---

## 8. Archivos e integridad

**Archivos creados** (todos en `experiments/ventanas_2026/`, ninguno en `src/` ni en `data/`):

| Archivo | SHA‑256 |
|---|---|
| `agregaciones.py` | `4b67091dfd5b0022fd31cb96b00b8476e373a8082f30fd359b7d419ceba24bfd` |
| `agregaciones_results.json` | `803af4c267708ec41abba2828e05114852646261361bcf2186fb2ede8827428a` |
| `agregaciones_stdout.txt` | (registro de ejecución) |

Del experimento anterior se reutilizaron sin cambios `windows_emb.npy` (`362d0352…`) y `windows_meta.json` (`18e21015…`).

**Datos originales** (`data/processed/rebuild_2026_08_corrected/`): SHA‑256 idénticos antes y después de la ejecución.

| Archivo | SHA‑256 |
|---|---|
| `passages_candidate.json` | `7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b` |
| `dense_embeddings_candidate.npy` | `124ced95fb9e152ce586dec9f30a1eb98dc14ee385c0bc335a2055357f73a617` |
| `vector_index_candidate.json` | `e182c77e0775472eb73d22ab92b15d026d067cbf6264fb8b25b207479c4668eb` |
| `knowledge_graph_candidate.json` | `95d5a67936cf48d3bc79b69bf370bb1a83a255f938a7322e0dae256450dde215` |
| `dense_embeddings_meta.json` | `c96b214bc14801ad903d58e0245d48c008d65ac051d339fd4e6b65e30709160e` |

**Otras comprobaciones:**
* `git status` en `src/` muestra solo los cambios FIX3 previos, sin commit; este análisis no tocó ningún archivo de esa carpeta.
* No hubo commit, push ni stash, no se activó ningún interruptor y no hubo llamadas externas.

**Limitaciones:**
* DEV es pequeño: 31 preguntas por forma, y cada una pesa 3,2 puntos.
* Las etiquetas siguen en `PENDING_EXPERT_REVIEW`.
* Solo se midió la recuperación. El posible error de trasladar la tolerancia al pesaje oficial se ha inferido de la composición del paquete; no se ha observado en una respuesta generada.

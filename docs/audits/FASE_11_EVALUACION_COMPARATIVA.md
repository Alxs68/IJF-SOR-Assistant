# Fase 11C — Evaluación comparativa (solo dev)

**Estado:** COMPLETADA para la recuperación sin LLM y para el DIG offline. **No se ejecutó la comparación de extremo a extremo de las variantes con el LLM:** los dos intentos de corrida en dev de esta fase quedaron degradados por la cuota del proveedor (17/62 y 48/82 evaluaciones sin generación). Test_sealed no se usó.
**Resultados reproducibles:**
* `data/eval/fase11/retrieval_experiments_dev.json` (recuperación);
* `data/eval/fase11/dig_replay_dev.json` (DIG);
* `data/eval/fase11/e2e_dev_summary.json` (flujo completo de base);
* `data/eval/fase11/equivalence_dev.json` (corrección de la medida).

## 1. Línea base corregida

La equivalencia de pasajes duplicados (misma página, texto idéntico) se aplica a todo lo que sigue. Sin ella, la Fase 10 subestimaba la recuperación (ver `FASE_11_DIAGNOSTICO_ABSTENCIONES.md` §2).

| Recuperación en dev (31 respondibles) | Fase 10 (estricta) | Línea base corregida (R0) |
|---|---|---|
| R@5 | 0,565 | 0,774 |
| MRR (top‑10 / top‑25) | 0,403 | 0,527 / 0,536–0,581 |
| Paquete completo | 0,548 | 0,774 |
| Precisión del paquete / P@5 | 0,108 | 0,155 / 0,168 |
| Distractor entregado sin evidencia | 4 | 2 |

## 2. Recuperación: línea base frente a cada variante (sin combinar)

Detalle completo en `FASE_11_RECUPERACION_EXPERIMENTAL.md` §6. Resumen con traducción LLM y diccionario:

| Variante | ΔR@5 (DICT / LLM) | ΔMRR | Δhit@10 | Errores de ámbito (dAb, d5) | Consultas perdidas | Veredicto |
|---|---|---|---|---|---|---|
| R2 unidades | −0,016 / −0,032 | +0,095 / +0,045 | +0,065 / 0 | 3,2 / 5,2 | 3 / 3 | descartada |
| R3 ámbito β 0,2 | 0 / 0 | +0,013 / +0,021 | +0,065 / +0,064 | 1,1 / 0,0 | 0 / 0 | **candidato** |
| R3 ámbito β 0,5 | +0,032 / 0 | +0,015 / +0,021 | +0,065 / +0,064 | 0,0 / 0,0 | 0 / 0 | **candidato** |
| R4 referencias | — (no ordena) | — | — | — | — | descartada: precisión de 0,168 a 0,130, sin ganar cobertura |
| R5 multilingüe | +0,016 / −0,016 | +0,023 / −0,016 | +0,129 / +0,064 | 2,0 / 4,0 | 3 / 4 | descartada (fusión 1:1) |

Línea base en ambos casos: dAb = 2, d5 = 2.

**Por idioma, R@5 (R0 → R3 β 0,5):**

| Idioma | Consultas | DICT | LLM |
|---|---|---|---|
| en | 17 | 0,824 → 0,824 | 0,824 → 0,824 |
| es | 12 | 0,750 → 0,833 | 0,750 → 0,750 |
| fr | 1 | 1 → 1 | 1 → 1 |
| pt | 1 | 0 → 0 | 0 → 0 |

* **El portugués sigue sin resolverse en todas las variantes.** El francés depende de que se traduzca.
* **No respondibles** (4 insuficientes, 4 fuera de ámbito y 12 ambiguas o incompletas, contadas por corridas): ninguna variante cambia el filtro de dominio. El top‑5 no vacío es 10/10 consultas en R0 y en todas las variantes.
* **Latencia de recuperación** (media por consulta): R0 unos 39 ms; R3 +0,05 ms; R2 +1,3 ms; R5 +25 ms (más 44 s de carga inicial y del índice).

## 3. DIG: base frente a variante DIG‑06 (reejecución offline)

| | DIG base | Variante DIG‑06 |
|---|---|---|
| Reproducibilidad con entradas capturadas | 20/20 | — |
| Casos con DIG‑06 fallido (61 reejecutados) | 19 | 11 |
| ABSTENER → PERMITIR | — | 6: 2 con entradas exactas y 4 reconstruidos. En los 6 la cita es del ancla esperada; 5 están respaldados y 1 tiene una afirmación sin cita (EXC‑006, revisión arbitral) |
| PERMITIR → ABSTENER | — | 0 |
| Cifras inventadas detectadas (130 ataques) | 130/130 | 130/130 |

## 4. Flujo completo de base (LLM real con DIG de producción) en dev

Referencia: la corrida de la Fase 10 (2 corridas, 82 evaluaciones, con muy pocos errores de API), reclasificada con la equivalencia. La corrida de la Fase 11 se muestra solo para ver la degradación por cuota.

| | Fase 10 (base) | Fase 11 (cuota) |
|---|---|---|
| Respondibles aceptadas con la cita del ancla esperada | **17/62 (27 %)** | 11/62 |
| Respuestas incorrectas aceptadas (otro ámbito, cifra sin respaldo o sin la evidencia esperada) | **0** | 0 |
| No respondibles respondidas | **0/20** | 1/20 |
| Abstenciones en respondibles | 45/62 | 51/62 |
| — con cita correcta (candidatas a falso negativo del DIG) | 20 | 15 |
| — evidencia no recuperada | 14 | 8 |
| — generación sin la cita correcta | 9 | 11 |
| — sin generación (API) | 2 | 17 |
| Abstenciones legítimas en no respondibles | 20/20 | 19/20 |
| Latencia del LLM (p50) | 2,1 s | 2,4 s |

**Por idioma y por grupo (Fase 10 base):**

| | Aceptadas con evidencia / respondibles |
|---|---|
| en | 12/34 |
| es | 4/24 |
| fr | 1/2 |
| pt | 0/2 |

* **No respondibles:** insuficientes 4/4, fuera de ámbito 4/4 y ambiguas o incompletas 12/12 abstenciones correctas. Todas son abstenciones; ninguna es una aclaración, porque ADA no tiene ese mecanismo.

**Reglas del DIG más activadas** (Fase 10 base): DIG‑05 30, DIG‑06 25, DIG‑08 13, DIG‑03 13, DIG‑01 10, DIG‑07 9, DIG‑02 8, DIG‑09 7, DIG‑00 7, DIG‑11 6, DIG‑12 3, DIG‑10 2.

## 5. Lo que no se pudo medir y por qué

* **Cobertura y tasa de respuestas incorrectas con R3 o con la variante DIG‑06 en el flujo real:** requieren corridas con LLM que la cuota actual del proveedor no sostiene (QUOTA y REQUEST_TOO_LARGE). El efecto de la variante DIG‑06 sobre la cobertura se puede **estimar por arriba** en +6 aceptaciones en dev (2 confirmadas con entradas exactas). No es una medida del flujo real.
* **Excepciones y referencias cruzadas en otro pasaje:** dev solo tiene 3 anclas de ese tipo.
* **Portugués y francés:** solo 1 consulta de cada idioma en dev.

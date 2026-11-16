# Fase 11 — Informe ejecutivo: mejora de recuperación y diagnóstico de abstenciones

**Estado:** COMPLETADA EN DEV, con la evaluación de extremo a extremo de los candidatos pendiente por la cuota del proveedor LLM.
**Clasificación:** EXPERIMENTAL, NO APTO PARA PRODUCCIÓN.

**No se ha tocado:** producción, corpus SOR (sha256 `7d463428…167b`, idéntico antes y después de cada paso), los 40 documentos SHADOW, benchmark_v2 y test_sealed (no se ejecutó). Tampoco hubo commit, push ni despliegue.

**Documentos:**
* `FASE_11_DIAGNOSTICO_ABSTENCIONES.md`
* `FASE_11_CALIBRACION_DIG.md`
* `FASE_11_RECUPERACION_EXPERIMENTAL.md`
* `FASE_11_EVALUACION_COMPARATIVA.md`
* CSV arbitral `data/eval/fase11/arbitral_review_abstentions.csv` (145 casos)
* manifest `data/eval/fase11/manifest.json`

## Resultados principales

1. **La recuperación era mejor de lo medido.** En el corpus, 87 de 136 anclas del benchmark tienen pasajes duplicados con texto idéntico que la métrica de la Fase 10 contaba como fallo. Corregida la medida (dev): **R@5 0,77** (antes 0,57), **MRR 0,53** (antes 0,40) y paquete completo 0,77. Las cifras del test sellado de la Fase 10 también están subestimadas; no se recalcularon.
2. **El DIG es exactamente reproducible:** 20/20 decisiones idénticas con las entradas reales capturadas.
3. **Se identificó y corrigió experimentalmente un falso negativo concreto del DIG‑06.** Contaba como cifras la fecha de edición, los identificadores SOR con guion Unicode, la numeración de listas y las etiquetas de sección con su título (p. ej., «8.10 Awarding Ceremonies» → 8.1).
   * La variante elimina solo esos patrones, derivados de la configuración y del propio corpus.
   * Desbloquea 6 respuestas de dev, todas con la cita literal del ancla esperada: 5 respaldadas y 1 con una afirmación sin cita (revisión arbitral).
   * No bloquea ninguna nueva.
   * Detecta las **130 de 130** cifras inventadas de la batería adversarial, igual que el DIG base.
4. **Recuperación consciente del ámbito.**
   * **R3 (preferencia por el ámbito nombrado en la consulta, con indicadores derivados de los títulos del SOR)** es la única variante que cumple todos los criterios: 0 consultas perdidas, errores de ámbito de 2 a 0, hit@10 de 0,87 a 0,94 y latencia despreciable. Su efecto en R@5 es pequeño: +1 consulta en un caso.
   * **R2** (unidades de artículo), **R4** (carril de referencias) y **R5** (embeddings multilingües) se descartan en su forma actual: pierden consultas del top‑5 o bajan la precisión.
5. **Seguridad conservada.** En la base de dev (Fase 10, reclasificada): 0 respuestas incorrectas aceptadas, 0 de 20 no respondibles respondidas y 20 de 20 abstenciones legítimas.
6. **La cobertura de respuestas sigue siendo baja:** 17/62 en dev. Las causas medidas de abstención son el control (20 con cita correcta), la recuperación (14) y la generación (9).

## Criterios de aceptación

| Criterio | Estado |
|---|---|
| Mejora verificable de recuperación | **Parcial.** La corrección de la medida es verificable. R3 mejora la profundidad y los errores de ámbito sin pérdidas, con poco efecto en R@5; muestra pequeña (31 consultas) |
| Reducción de abstenciones injustificadas | **Demostrada offline:** 6 casos con la variante DIG‑06. **No medida** en el flujo real (cuota) |
| Conservación de la seguridad normativa | **Sí** en todo lo medido: sin aceptaciones incorrectas, 130/130 ataques detectados, controles OOD intactos |
| Ausencia de regresiones críticas | **Sí:** producción intacta; 60 tests de experimentación y del DIG pasan |
| Trazabilidad | **Sí:** manifest con comandos, parámetros y sha256; cada experimento por separado |
| Comparación reproducible contra la línea base | **Sí**, con equivalencia y modo estricto disponible |
| Separación experimentación / producción | **Sí:** tests de aislamiento; la variante del DIG solo existe dentro del proceso offline |

## Limitaciones

* Dev es pequeño (31 respondibles) y el benchmark sigue sin revisión arbitral.
* El test_sealed ya está parcialmente contaminado por los diagnósticos de las fases 10 y 11.
* Las corridas con LLM de la Fase 11 quedaron degradadas por la cuota de Gemini, con respaldo en Groq. Por eso no hay medida de extremo a extremo de R3 ni de la variante DIG‑06.
* El DIG sigue sin verificar afirmaciones sin cifra (nivel D, NO_VERIFICADO).
* El RRE de producción contiene 31 identificadores de pasaje y 34 detectores de palabras clave escritos a mano. En este benchmark ayudan, pero su generalización no está demostrada.

## Recomendación para la Fase 12

1. **Construir benchmark_v3 sellado e independiente** antes de cualquier decisión de producción (decisión ya tomada). Debe incluir:
   * más consultas de ámbito, de excepciones y referencias en otro pasaje, en portugués y en francés;
   * la equivalencia de pasajes incorporada a las anclas desde la construcción;
   * revisión arbitral de las etiquetas.
2. **Revisión arbitral** del CSV de abstenciones (prioridad ALTA: 15 casos con cita correcta) y de los 6 desbloqueos de la variante DIG‑06.
3. **Resolver la capacidad del proveedor LLM** antes de nuevas evaluaciones de extremo a extremo: cuota suficiente o un proveedor fijo registrado como variable, y prompt más corto para REQUEST_TOO_LARGE. Sin esto, la cobertura no se puede medir con fiabilidad.
4. **Con capacidad suficiente**, medir de extremo a extremo y en v3 **solo dos candidatos**, primero por separado:
   * la variante DIG‑06;
   * R3 (β 0,2 y 0,5).

   Reejecutar también la batería adversarial S2 de la Fase 9 con la variante.
5. **Investigar después, sin prioridad:**
   * R2 y R5 como ampliación del conjunto de candidatos (no para reordenar);
   * traducción del portugués y francés antes de recuperar;
   * decisión arbitral sobre los mecanismos M2–M6 del DIG: cifra de la consulta, encabezado, palabras en español frente a SHADOW, vocabulario del usuario (DIG‑11) y excepción cercana.
6. **Mecanismo de aclaración (11D):** no se implementó. Los datos lo justifican (AMB‑007 y AMB‑008 se respondieron con el ámbito general en la Fase 10), pero el detector de la Fase 10 no es válido. Se propone diseñarlo sobre R3: pedir aclaración solo cuando la consulta no nombra un ámbito y las candidatas del top‑5 pertenecen a partes distintas con reglas diferentes, y medirlo en v3.
7. **NLI (11E):** sin cambios; mDeBERTa sigue como observador. No se ejecutó en esta fase.

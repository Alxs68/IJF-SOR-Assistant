# Informe de correcciones controladas posteriores a la evaluación A/B

Fecha: 2026-11-16 · Base: `docs/audits/EVALUACION_AB_ESQUEMA_REGLA14.md` · Reanálisis: `data/eval/dig_v3/post_ab_reanalysis.json` (script `scripts/post_ab_reanalysis.py`, **sin llamadas al LLM**).
Sin cambios en corpus, SHADOW, benchmarks (incluido benchmark_v3 y test_sealed), producción ni OCI. Sin commit ni push. DIG-05 y DIG-09 no se modificaron.

## 1. Problemas identificados

| # | Problema | Evidencia |
|---|---|---|
| P1 | DIG-03 rechazaba citas literales escritas con variantes tipográficas (guion no separable U+2011 de Groq) | SCO-010 y MLG-003 en A/B; también en capturas de Fase 11 |
| P2 | DIG-08 marcaba como «huella SHADOW» palabras españolas que traducen conceptos presentes en la evidencia SOR | REF-005 («competiciones»), EXC-003 («olímpico»), SCO-020 («tolerancia»), INC-005 («equipo»), AMB-006 |
| P3 | El evaluador comparaba citas con una normalización distinta de la del DIG | SCO-026: cita correcta clasificada «sin evidencia esperada» por el corte «Sono-⏎mama» |
| P4 | La comprobación de cuota consultaba un modelo de Groq distinto del que usa el asistente | `.env` del PC con `GROQ_MODEL=llama-3.3-70b-versatile` (no soportado) |

## 2. Causas raíz

* **P1:** `normalize_with_map` solo unificaba comillas y espacios; los guiones tipográficos (U+2010/2011/2012/2013/2212) y los invisibles (guion blando, espacios de ancho cero) no.
* **P2:** DIG-08 compara palabras de la respuesta con las de SHADOW, menos las del SOR primario, la consulta y (v3) las instrucciones. El SOR está en inglés; con una respuesta en español, cualquier palabra española común que aparezca también en un documento complementario en español queda «solo en SHADOW» aunque su concepto esté en la evidencia primaria. Es un problema **lingüístico** (solapamiento entre idiomas), no de ámbito ni de pertinencia. En las 13 activaciones registradas, las palabras fueron: olimpico, deportivas, equipo, competiciones, categoria, tolerancia, conformacion, competition (esta última en una respuesta en inglés, no afectada).
* **P3:** `span_hit` usaba su propia normalización (minúsculas y espacios), sin las reglas del DIG (comillas tipográficas, «N .N», guion de corte de línea, variantes tipográficas) ni la segmentación por salto de página.
* **P4:** `MultiProviderLLMManager` descarta un `GROQ_MODEL` no soportado y usa `openai/gpt-oss-120b`; el comprobador leía la variable de entorno directamente.

## 3. Archivos modificados

| Archivo | Cambio |
|---|---|
| `src/decision_integrity.py` | Correcciones `FIX_UNICODE_TYPO` (U) y `FIX_DIG08_CROSSLANG` (X), activadas con `DIG_V3=1`; funciones `_typo_char`, `_es_en_dictionary`, `concept_in_primary`; versión `DIG-1.3+NUM-v2+FIX-v3` |
| `scripts/eval_llm_shadow.py` | `span_hit` usa `decision_integrity.norm` y divide por salto de página |
| `scripts/check_llm_quota.py` | Reescrito sobre `MultiProviderLLMManager` |
| `scripts/post_ab_reanalysis.py` (nuevo) | Reanálisis offline antes/después + adversarial |
| `scripts/replay_dig_v3.py`, `tests/test_dig_v3_fixes.py`, `tests/test_r3_dig_v2_integration.py` | Lista de correcciones actualizada; aislamiento de un test |
| `tests/test_post_ab_fixes.py` (nuevo) | 9 tests |

Se conservan sin cambios el esquema JSON obligatorio y la validación estructural (`LLM_JSON_SCHEMA`). La regla 14 (`ADA_PROMPT_RIGOR`) sigue desactivada por defecto; no se modificó el prompt.

## 4. Soluciones implementadas

* **DIG-03 (U):** guiones tipográficos equivalentes → «-»; espacios finos → espacio; invisibles omitidos. Se aplica igual a la cita y al pasaje, solo para comparar; el texto original y sus posiciones se conservan (mapa de índices). La raya (U+2014) y cualquier otro signo NO se equiparan.
* **DIG-08 (X):** solo en respuestas no inglesas, una palabra no cuenta como huella SHADOW si el **mismo concepto** está en el texto SOR primario entregado: su traducción en el diccionario ES→EN existente del proyecto (`rre_engine.SPANISH_TO_ENGLISH_SYNONYMS`, leído sin importar el módulo) o su cognado ortográfico (prefijo común de 6 letras, y→i). Cifras y palabras sin equivalente en la evidencia primaria se siguen detectando. No hay listas por pregunta.
* **Evaluador:** misma normalización que el DIG y segmentación por salto de página; la cita debe seguir apareciendo en la página y solapar el ancla. No se tocaron las respuestas esperadas del benchmark.
* **Cuota:** proveedor principal y respaldo del asistente; modelo efectivo y modelo de entorno ignorado; tipo de error (QUOTA=429, TEMPORARY=503, REQUEST_TOO_LARGE=413, AUTH, NOT_FOUND); versión que responde; límites de Groq y si alcanzan para una llamada de análisis (~8 000 tokens); aviso explícito cuando ningún proveedor responde («serían abstenciones por API, no por el DIG»).

## 5. Pruebas ejecutadas

* **Unitarias (9 nuevas):** variantes de guion, espacios, invisibles y saltos de línea aceptadas; textos distintos rechazados (palabra cambiada, raya, palabra unida); posiciones del texto original conservadas; DIG-08 entre idiomas no marca conceptos traducidos y sí marca fugas reales (palabra española sin equivalente, nombre propio, inglés, cifra); respuestas en inglés sin cambios; evaluador con la normalización del DIG; comprobador con modelo efectivo y error 429. Pasan en la VM; la suite completa debe confirmarse en el PC (ver §9).
* **Reanálisis offline** de las 108 entradas capturadas del DIG (Fase 11, integración y A/B): cambios de decisión y 12 tipos de ataque.
* Las pruebas unitarias **no** son evidencia de mejora semántica general.

## 6. Resultados antes y después (offline, mismas respuestas del LLM)

**Evaluación A/B, variante A** (respuestas de A; ANTES = DIG y evaluador de la evaluación A/B):

| Métrica (31 respondibles) | Antes | Solo evaluador nuevo | Después (DIG + evaluador) |
|---|---|---|---|
| Aceptadas | 12 | 12 | 15 |
| Con evidencia esperada | 11 | 11 | 14 |
| Falsos bloqueos | 8 | 9 | 8 |
| Ámbito equivocado / cifra sin respaldo aceptados | 0 / 0 | 0 / 0 | 0 / 0 |
| Aceptadas sin evidencia esperada | 1 | 1 | 1 |

Las 3 nuevas aceptaciones: **SCO-010 y MLG-003** (Groq, guion U+2011: «There is no random weigh‑in for veterans», p. 105) y **REF-005** (Gemini, español: «las categorías de peso son las mismas que senior», p. 103, antes bloqueada por «competiciones»). Las tres citan literalmente la evidencia esperada. El falso bloqueo adicional del evaluador nuevo es SCO-026 de A, que ahora se reconoce como cita correcta bloqueada por DIG-07 (términos no citados).

**Variante B:** 15 aceptadas en los tres cortes; con evidencia esperada 14 → 15 (SCO-026, efecto solo del evaluador); 1 pregunta ambigua respondida (AMB-005) sin cambios.

**Por proveedor:** en A, 2 de las 3 ganancias son respuestas de Groq (P1) y 1 de Gemini (P2).

**Todas las capturas (108 entradas):** cambian 13 decisiones del DIG. 6 pasan a PERMITIR: las 3 de A ya citadas y 3 de capturas anteriores (MLG-003 ×2 y SCO-010 de Fase 11/integración), todas citando literalmente la p. 105 o la p. 103. En las otras 7 desaparece un fallo DIG-08 o DIG-03, pero la respuesta sigue bloqueada por otra regla. Ninguna decisión pasa de PERMITIR a ABSTENER.

**Adversarial (108 entradas, 12 tipos):** ninguna detección perdida y ninguna decisión pasa de ABSTENER a PERMITIR por un ataque. Incluye cifras inventadas (A1–A6), cifra solo en SHADOW (T2), cita alterada con guion tipográfico y una palabra cambiada (T3: detectada en 97/97 casos aplicables) y término español solo en SHADOW (T4: 107/107). El punto ciego conocido A4/A4b (1 caso) sigue igual.

## 7. Riesgos y limitaciones

* El reanálisis reutiliza respuestas ya generadas: mide el cambio del DIG y del evaluador, no la variabilidad del LLM. Una decisión que pasa a PERMITIR se cuenta como respuesta emitida sin reejecutar el formateo posterior de ADA.
* **X** depende de la cobertura del diccionario ES→EN del proyecto y de un criterio de cognados (6 letras). Un falso cognado podría ocultar una palabra SHADOW; el riesgo se limita porque solo se excluyen palabras cuyo concepto ya está en la evidencia primaria, y las cifras se comprueban siempre.
* **U** no equipara la raya ni otros signos; una cita con raya donde el SOR tiene guion sigue rechazándose.
* Muestras pequeñas (41 preguntas, 1 corrida): las diferencias de 1–3 casos no son una mejora general demostrada.

## 8. Diagnóstico de los siete bloqueos persistentes

**Corrección importante:** en el informe A/B atribuí estos bloqueos a DIG-05/DIG-09. El análisis muestra que las reglas implicadas son sobre todo **DIG-11** y **DIG-06**; DIG-09 aparece en 1 pregunta y DIG-05 en 1 respuesta.

| Pregunta | Regla que bloquea | ¿Bloqueo correcto? | Qué haría falta | Riesgo de cambiarlo |
|---|---|---|---|---|
| DIR-005 «spacing between the world champion stars» | DIG-11: «spacing» no aparece en el SOR (usa «space») | A: **falso positivo** (respuesta correcta, cita exacta). B: la regla bloquea por el motivo equivocado, pero la respuesta B mezcla dos medidas del SOR («1.5–2 cm» y «0.5–2 cm»), así que su bloqueo es conveniente | DIG-11 con variantes morfológicas (raíz más corta o lematización) | Medio: DIG-11 protege de preguntas sobre cosas que no existen en el SOR; relajarlo puede dejar pasar preguntas fuera del reglamento |
| DIR-018 «fuerte impacto en la cabeza» | A: DIG-07 («kiken-gachi» sin cita). B: DIG-06 («1» sin cita), DIG-07 («tatami»), DIG-05 (cita de la p. 199 sin término distintivo de la consulta) | **Correcto** en A y B: ambas añaden en condiciones contenido no citado. El DIG-05 sobre la p. 199 es dudoso («head trauma» es pertinente), pero no decide | Generación más ceñida a las citas | Bajo para el DIG; el problema está en la generación |
| EXC-009 «skips the medal ceremony» | DIG-11: «skips» no aparece en el SOR | **Falso positivo** en A y B: respuestas correctas con la cita exacta (p. 98) | Igual que DIR-005 | Igual que DIR-005 |
| SCO-021 «female team» | DIG-06: A «1», B «10» y «2» sin cita | **Correcto**: A añade «one (1) category higher» sin citarlo; B afirma «10 athletes / 2 per category» con una cita que no los incluye | Generación: citar lo que se afirma | — |
| SCO-023 «Juniors WRL» | DIG-06: «1», «2» (y «9» en B) en condiciones sin cita | **Correcto según el contrato**: el resumen es exacto, pero las condiciones añaden cifras no citadas | Generación o separar respuesta principal de condiciones accesorias | Medio: no exigir cita en condiciones abriría la puerta a cifras inventadas |
| SCO-024 «pareja de kata, puntos de ranking» | A: DIG-09 (excepción «except for U18» en la frase vecina, no citada). B: DIG-06 + DIG-09 | A: **falso positivo** (respuesta mínima y exacta; la excepción trata del cálculo de puntos, no de en qué eventos se suman). B: **correcto** (cifras no citadas) | DIG-09: exigir la excepción solo si comparte términos con lo citado o con la consulta | Medio-alto: podría omitirse una excepción relevante |
| SCO-025 «minor injury during kata» | B: DIG-11 («suffers» no está en el SOR). A (Groq): DIG-03 (cita parafraseada «If another…» frente a «In case another…»), DIG-06, DIG-11 | B: **falso positivo** (respuesta correcta, citas literales). A: **correcto** | Igual que DIR-005 | Igual que DIR-005 |

**Resumen:** de 14 respuestas (7 preguntas × A/B), 6 son falsos positivos: 5 por **DIG-11** (vocabulario de la pregunta en inglés que el SOR no usa: «spacing», «skips», «suffers») y 1 por **DIG-09** (ventana de ±2 frases). Los otros 8 bloqueos son correctos: casi todos por **DIG-06/DIG-07** cuando el modelo añade en condiciones cifras o términos que no cita.

## 9. Recomendaciones pendientes (no implementadas; requieren autorización)

1. **Confirmar en el PC** la suite completa en modo original y con `DIG_V3=1 LLM_JSON_MODE=1 LLM_JSON_SCHEMA=1 RRE_ENABLE_SCOPE_PREFERENCE=1 DIG_NUMBER_NORMALIZATION=v2`, y ejecutar el nuevo `scripts/check_llm_quota.py`.
2. **DIG-11:** evaluar variantes morfológicas de los términos de la consulta (el principal origen de falsos positivos), midiendo antes el efecto en las preguntas no respondibles y fuera de dominio.
3. **DIG-09:** evaluar exigir la excepción vecina solo si se relaciona con lo citado o con la consulta.
4. **Generación:** el modelo sigue añadiendo en condiciones contenido no citado (la regla 14 no lo corrigió); estudiar alternativas que no relajen DIG-06/DIG-07.
5. Repetir la evaluación A/B con un proveedor estable (o varias corridas) antes de concluir sobre cambios de prompt.
6. Corregir `GROQ_MODEL` en el `.env` del PC (tarea del usuario; el archivo contiene claves).

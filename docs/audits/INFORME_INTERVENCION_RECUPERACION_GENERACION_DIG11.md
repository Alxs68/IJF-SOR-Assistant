# Intervención sobre recuperación, generación y DIG-11 — Respuesta única y validación integral

Fecha: 2026-11-16 · Rama local `exp/r3-dig-v2` · Sin despliegue, sin commit, sin push.

> **Alcance de este documento.** Recoge la decisión de diseño «respuesta única, completa y verificada» (este encargo).
> Las partes de **recuperación** y **DIG-11** de la intervención no están implementadas aquí: no se recibieron sus
> instrucciones concretas. DIG-11, DIG-05, DIG-09, R3, el corpus, SHADOW y los benchmarks **no se modificaron**.

## 1. Comportamiento anterior

* El contrato del prompt se titulaba «**CONTRATO OBLIGATORIO DE RESPUESTA EN DOS NIVELES**»: `summary` = «Nivel 1», el resto = «Nivel 2».
  La regla 10 ordenaba «**segrega los requisitos conexos** en `conditions_and_exceptions` o `extended_analysis`».
* La interfaz mostraba el «Nivel 1» y escondía el resto en el desplegable **«🔍 Ampliar respuesta con análisis detallado y relaciones entre artículos»**.
  No había una segunda llamada al modelo: era una sola generación partida en dos.
* El DIG verificaba cifras y términos **solo** en `summary`, `normative_basis` y `conditions_and_exceptions`.
  `extended_analysis` y `limitations` se mostraban **sin control** (salvo DIG-08 en `extended_analysis`).
* Después del DIG, el texto pasaba por el sanitizador normativo y el formateo de citas, **sin volver a verificarse**.
* Si el modelo añadía una sola cifra accesoria sin cita, se bloqueaba **toda** la respuesta.
* No existía la opción de pedir aclaración: una pregunta ambigua terminaba en abstención o en una respuesta.

## 2. Nuevo comportamiento (`ADA_UNIFIED_ANSWER=1`)

1. Pregunta → traducción → RRE (sin cambios) → evidencia certificada.
2. **ADA, una sola llamada de generación** con el contrato «**RESPUESTA ÚNICA Y COMPLETA**»:
   * respuesta directa;
   * regla aplicable;
   * solo las condiciones, excepciones y diferencias por categoría que **cambian la respuesta**, cada una con cita literal;
   * aplicación al caso solo si se plantea un caso;
   * limitaciones;
   * conclusión breve cuando no es un dato simple.
   Se eliminó la instrucción de añadir requisitos conexos. La regla 13 exige cita literal en **todos** los campos de texto.
   Se añadió `answerability = REQUIERE_ACLARACION`.
3. **DIG completo** sobre todos los campos visibles.
4. **Afirmaciones sin respaldo:**
   * Si el DIG solo falla por cifras o términos sin cita (DIG-06 o DIG-07), se **retiran las frases accesorias** que los contienen.
   * Solo se retiran frases de `conditions_and_exceptions` o `extended_analysis`; nunca de `summary` ni de `normative_basis`.
   * La respuesta resultante se **vuelve a evaluar con todos los controles**. Si no los supera, se mantiene la abstención.
   * Si se retiró algo, se añade a `limitations` la nota «Se omitió de esta respuesta información complementaria que no pudo verificarse literalmente…».
5. **Validación final**, después del sanitizador, de la nota y del formateo de citas:
   * el contenido visible se devuelve a la forma que verifica el DIG (enlaces → `[ID]`, sin las notas del sistema) y se ejecuta **otra vez el DIG completo**;
   * si falla, o si el sanitizador tuvo que neutralizar algo, la respuesta es **abstención**.
6. El usuario recibe **una única respuesta**, en un solo bloque. Solo se amplía si hace una nueva consulta.

**Aclaración.** Con `REQUIERE_ACLARACION` el asistente no emite dictamen y devuelve el estado `CLARIFICATION_REQUIRED`.
La pregunta de aclaración del modelo solo se muestra si no contiene cifras ni términos SOR ajenos a la consulta o a sus citas, ni pasajes no entregados.
Si no cumple eso, se muestra un texto genérico fijo.

**Fuera de dominio.** Sin cambios: la precomprobación OOD, la ausencia de evidencia y `EVIDENCIA_INSUFICIENTE` siguen produciendo abstención.

## 3. Componentes modificados

| Componente | Cambio |
|---|---|
| `src/decision_integrity.py` | `FIX_ALL_VISIBLE_FIELDS` (lee `ADA_UNIFIED_ANSWER`; versión `…+ALL`). DIG-02/06/07/08 sobre `extended_analysis` y `limitations` (en `limitations` una cifra puede proceder de la consulta). Nuevas funciones `prune_units`, `prune_unsupported` y `verify_clarification`. DIG-05/09/11 **idénticos**: DIG-05 sigue usando las mismas citas. |
| `src/ada_assistant.py` | `_contract_texts()`: textos anteriores **idénticos carácter a carácter** con el modo apagado (comprobado) y contrato unificado con el modo encendido. Rama de aclaración, poda con nueva evaluación, validación final del contenido visible, `answer_mode`/`response_status` y `validated_answer` en la salida. |
| `src/answer_presentation.py` (nuevo) | Compone la respuesta en un bloque y omite «No aplica» y «Ninguna». No genera contenido. |
| `app.py` | Con el modo unificado: un solo bloque con todas las secciones, **sin el desplegable «Ampliar respuesta»**. Se mantienen las evidencias certificadas, la auditoría, las fuentes y el grafo de relaciones (no es texto generado). Con el modo apagado, la interfaz anterior no cambia. |
| `scripts/eval_llm_shadow.py` | Puntúa el contenido que vio el usuario (después de la poda). Nueva métrica `visible_numbers_not_in_quotes` y nuevos resultados `ACLARACION_*`. |
| `scripts/eval_ab_dev.py` | `--set unified` (A = anterior, B = respuesta única; ambas con esquema JSON y sin regla 14). |
| `scripts/replay_unified_answer.py`, `scripts/run_eval_unified.ps1` | Reproducción offline y guion de evaluación en vivo. |
| Pruebas | `tests/test_unified_dig.py` (10 pruebas) y `tests/test_unified_answer.py` (18 pruebas). |

Por defecto todo queda **desactivado**: sin `ADA_UNIFIED_ANSWER=1` el sistema se comporta exactamente igual que antes.

## 4. Validación integral: qué se verifica

| Elemento visible | Control |
|---|---|
| Cifras, medidas y tiempos (todos los campos) | DIG-06 (en `limitations` se admiten cifras de la consulta) |
| Términos normativos distintivos (todos los campos) | DIG-07 |
| Influencia de SHADOW (todos los campos) | DIG-08 |
| Pasajes mencionados en cualquier campo | DIG-02 (deben tener cita literal) |
| Excepciones vecinas y referencias cruzadas | DIG-09 y DIG-10 (sin cambios) |
| Pertinencia, suficiencia y términos de la consulta | DIG-05, DIG-01, DIG-11 y DIG-12 (sin cambios) |
| Texto final, tras sanitizador y formateo | Segunda ejecución completa del DIG; abstención si falla |
| Solicitud de aclaración | `verify_clarification` |

Lo que sigue sin verificarse, igual que antes, es el **entailment** (nivel D): una cita literal no demuestra que respalde la afirmación.

## 5. Tratamiento del contenido adicional

* **Prescindible y sin cita** (condiciones o aplicación): se retira y se avisa en las limitaciones.
* **En la respuesta principal** (`summary` o `normative_basis`): no se retira; **abstención**.
* **En las limitaciones:** no se retira (ocultar un límite sería engañoso); **abstención**.
* **Reformular** una afirmación exigiría una segunda generación, lo que contradice el requisito de una sola operación: **no se hace**.
* `extended_analysis` **se conserva** como «Aplicación al caso» dentro de la respuesta única, verificado como cualquier otro campo.

## 6. Resultados de las pruebas

**Pruebas nuevas.** 28/28 pasan en la VM. Allí la recuperación está en modo léxico degradado (`RRE_ALLOW_DEGRADED_LEXICAL=1`), porque no puede descargar el modelo de embeddings. **Deben confirmarse en el PC** con `scripts/run_eval_unified.ps1`.

| # | Requisito | Prueba |
|---|---|---|
| 1, 8 | Una generación y una respuesta | `test_single_generation_single_answer`, `test_app_has_no_expand_answer_in_unified_branch` |
| 2 | Todo lo visible pasa por el DIG | `test_final_validation_covers_all_visible_fields` |
| 3 | `extended_analysis` no escapa al control | `test_extended_analysis_cannot_add_unverified_content`, `test_previous_behaviour_let_extended_analysis_through`, `test_extended_analysis_figure_is_now_verified` |
| 4 | Cifras y excepciones con respaldo | `test_unsupported_figure_in_main_answer_abstains`, `test_unsupported_exception_in_conditions_is_removed_and_flagged`, `test_limitations_cannot_add_unverified_figures` |
| 5 | Evidencia parcial | `test_partial_evidence_limitation_is_shown` |
| 6 | Aclaración | `test_ambiguous_query_requests_clarification`, `test_clarification_with_unsupported_figure_uses_generic_text`, `test_clarification_cannot_assert_unsupported_content` |
| 7 | Fuera de dominio | `test_out_of_domain_abstains` (inglés y portugués) |
| 9 | Citas correctas | `test_citations_remain_correct` |
| 10 | Interfaz | `test_presentation_*`, `test_app_has_no_expand_answer_in_unified_branch`, `test_previous_contract_unchanged_when_off` |

**Sin regresiones.** La suite completa en la VM da los mismos 15 fallos y 18 errores con el código anterior y con el nuevo. Son pruebas que exigen el modo HYBRID, que la VM no tiene. Las pruebas que pasan suben de 485 a 513: las 28 nuevas.

**Reproducción offline sobre las 41 preguntas DEV.** Son 108 respuestas ya generadas y guardadas, reevaluadas sin ninguna llamada al LLM (`data/eval/unified_answer/replay_unified.json`).

| Sobre la misma respuesta generada | Anterior | Solo validación integral | **Nuevo** (integral + poda) |
|---|---|---|---|
| Aceptadas con la evidencia esperada | 43 | 42 | **51** |
| Abstenciones con la cita correcta (falsos bloqueos) | 28 | 29 | **20** |
| Respuestas incorrectas aceptadas | 3 | 3 | **3** (las mismas) |
| Abstenciones legítimas / sin aclaración | 5 / 16 | 5 / 16 | 5 / 16 |

* **Validación integral:** detectó 1 respuesta que antes se aceptaba con 6 cifras sin citar en `extended_analysis` (REF-005).
* **Poda:** recuperó 9 respuestas correctas (SCO-021 ×2, SCO-023 ×4, DIR-011, CAT-003, REF-005) retirando 15 frases accesorias: 11 de condiciones y 4 de aplicación al caso.
* **Incorrectas aceptadas:** las 3 son las mismas de antes (AMB-005 ×2 y EXC-006, pendiente de revisión arbitral). No aparece ninguna nueva.

**Limitación de esta medición:** las respuestas se generaron con el contrato anterior. El efecto del contrato nuevo (respuestas más centradas y con aclaraciones) solo se mide con la evaluación en vivo: `scripts/run_eval_unified.ps1`, unos 30 minutos y unas 82 llamadas al LLM.

## 7. Limitaciones restantes

* **Poda de información correcta:** puede retirar información que sí está en el SOR, pero que el modelo no citó (por ejemplo, el 3.º kyu de U18 en CAT-003). La respuesta queda más corta y lo avisa. No inventa, pero puede omitir una diferencia por categoría.
* **Sin entailment:** el DIG no comprueba que una cita respalde semánticamente la afirmación.
* **Recuperación:** sigue siendo la primera causa de no respuesta (7/31 en el diagnóstico); este encargo no la cambia.
* **Aclaración no medida en vivo:** su uso real por el modelo (cuánto la pide y si la pide en preguntas respondibles) solo se conocerá con la evaluación en vivo.
* **DIG-11 y DIG-09:** sin cambios; mantienen los falsos bloqueos documentados en `DIAGNOSTICO_DIG11_DIG09_GENERACION.md`.
* **Pruebas extremo a extremo:** solo se ejecutaron en modo léxico degradado.

## 8. Evaluación en vivo (2026-11-16, PC del responsable)

`scripts/run_eval_unified.ps1`:
* Pruebas nuevas: 28/28. Suite completa con el modo desactivado: los 6 fallos de siempre (541 pasan).
* Evaluación A/B intercalada sobre las 41 preguntas DEV (`data/eval/unified_answer/ab_unified_dev.json`):
  * A = contrato anterior. B = respuesta única. Ambas con esquema JSON, sin regla 14 y con la misma traducción y recuperación.
  * Gemini `gemini-3.5-flash-lite` en las 82 generaciones, sin errores del proveedor.
  * Corpus sin cambios; DIG reproducible en 73/73.

| | A (anterior) | B (respuesta única) |
|---|---|---|
| Respondibles aceptadas con la evidencia esperada (de 31) | 14 | **18** |
| Incorrectas aceptadas (debían abstenerse o aclarar) | 1 (AMB-005) | **2** (AMB-005, AMB-010) |
| Aclaraciones correctas (AMB-009, INC-001) | 0 | **2** |
| Abstenciones legítimas (de 10 no respondibles) | 9 | 6 + 2 aclaraciones |
| Cifras visibles sin cita en respuestas aceptadas (todos los campos) | 0 | 0 |
| Tokens | 298 592 | 292 957 |

**Ganadas en B (6):**
* DIR-011, DIR-018, MUL-004 y SCO-022: el contrato centrado ya no añade requisitos conexos.
* SCO-023 y SCO-026: poda de 3 y 1 frases accesorias.

**Perdidas en B (2):**
* **CAT-007:** el modelo afirmó que el SOR no fija un límite (es falso: «two (2) best domestic athletes»). El DIG lo bloqueó correctamente (DIG-02/08/12).
* **EXC-006:** citó un pasaje sin fragmento literal (DIG-02/05). EXC-006 ya estaba pendiente de revisión arbitral.

Con una sola corrida no se puede separar el efecto del contrato de la variabilidad del modelo.

**Nueva incorrecta aceptada: AMB-010** («¿Qué pasa si hay una lesión leve?»).
* El benchmark espera una aclaración. B respondió con la regla de lesiones leves del SOR, citada literalmente, tras podar 1 frase.
* La respuesta está respaldada, pero la pregunta era ambigua. **La poda hizo posible esta aceptación**: la abstención de A venía de DIG-06/07/09 sobre otra redacción.

**Hallazgo sobre la aclaración:**
* `verify_clarification` admite cifras si figuran en las citas que declara el propio modelo, pero **no comprueba que esas citas sean literales**.
* En AMB-009 las 4 citas eran literales (comprobado offline) y el texto mostrado daba ejemplos con cifras respaldadas. Aun así, el control no lo garantiza.
* Propuesta pendiente de autorización: exigir que las citas de la aclaración se localicen literalmente en los pasajes entregados, como en DIG-03, o no admitir cifras en una aclaración.

## 9. Correcciones de la auditoría de trazabilidad (autorizadas el 2026-11-17)

Implementadas tras `AUDITORIA_TRAZABILIDAD_RRE_GEMINI_DIG.md`.
* Cada una va detrás de un interruptor, **desactivado por defecto**. Con todos apagados el comportamiento es el anterior (prompts idénticos, comprobado).
* **DIG-05 y DIG-09 no cambian.** DIG-09 (R5c) queda pendiente, como recomendó la auditoría.

| Corrección | Interruptor | Cambio | Componente |
|---|---|---|---|
| **R1** campeones de canal | `RRE_CHANNEL_CHAMPIONS=1` | Si la fusión deja fuera del paquete el pasaje que el canal denso sitúa 1.º–2.º (similitud ≥ 0,55) o el que TF-IDF sitúa 1.º, se incorpora sustituyendo a los últimos del paquete (máximo 2; nunca al primero; sin textos duplicados). Genérica: no depende de la pregunta ni del pasaje, y no altera las reglas fijas existentes | `src/rre_engine.py` |
| **R2** traducción | `ADA_TRANSLATE_ANY_LANG=1` | Se traduce toda consulta que no esté en inglés (antes solo el español: MLG-002, en portugués, llegaba sin traducir). Nueva regla del traductor: traducción fiel, sin añadir deportes, sistemas, órganos ni temas que no estén en la consulta (deriva de OOD-006) | `src/ada_assistant.py` |
| **R5a** DIG-11 subordinado | `DIG_11_SUBORDINATE=1` | DIG-11 solo rechaza si **ninguna cita es pertinente** (DIG-05 fallido). Una palabra de la pregunta ausente del SOR («spacing», «skips», «suffers») ya no anula una respuesta respaldada por una cita literal pertinente | `src/decision_integrity.py` |
| **R5b** DIG-06 | `DIG06_REFS=1` | DIG-06 no cuenta como cifra afirmada los números de una **referencia documental** (artículo, sección, regla, apéndice, página, también en listas «6.5 y 6.4.2») ni los **identificadores de categoría escritos por el usuario** en su consulta («-66 kg», «U18»). Cualquier otra cifra sigue exigiendo cita literal | `src/decision_integrity.py` |
| **R6** ambigüedad y ausencias | contrato de respuesta única (`ADA_UNIFIED_ANSWER=1`) | Criterio explícito de `REQUIERE_ACLARACION`: la consulta no indica modalidad, evento, categoría o situación y los pasajes tienen reglas distintas para cada una. Nueva regla: no afirmar que el SOR «no establece» algo (solo «los pasajes entregados no contienen…», en `limitations`) y no generalizar una regla a otros eventos o categorías | `src/ada_assistant.py` |
| **R8** aclaración | — (modo de respuesta única) | `verify_clarification` solo acepta como respaldo de una cifra las citas **localizadas literalmente** en los pasajes entregados | `src/decision_integrity.py` |

### Comprobación offline de R5a y R5b (181 entradas DIG almacenadas; sin LLM)

| | Nuevas aceptadas | Contenido de las nuevas aceptadas | Reglas que pasan a fallar |
|---|---|---|---|
| R5a | 14 | 8 correctas y 6 correctas según el texto (DIR-005, con el SOR ambiguo) | ninguna |
| R5b | 3 | 3 correctas (CAT-001 «-66 kg») | ninguna (tras corregir un falso «P021» en identificadores con guiones tipográficos) |
| R5a + R5b | **17** | **17 correctas; 0 incorrectas** | ninguna |

* **R1** no se puede medir en la VM, que no tiene el modelo denso. Se mide en el PC con `scripts/eval_r1_channel_champions.py`: recuperación con y sin la corrección, con las consultas ya registradas en Fase 11 y sin llamadas al LLM.
* **R2, R6 y R8** solo se miden con generación real.

### Pruebas

* **Nuevas:** `tests/test_fix_trazabilidad.py` (16).
* **Pruebas de respuesta única:** se hicieron independientes del entorno, porque las del modo apagado fallaban si la variable estaba activa.
* **Resultado en la VM (modo léxico degradado):** 52 pasan y 2 se omiten, tanto **con todos los interruptores encendidos como apagados**. La suite completa conserva los mismos fallos, debidos al modelo denso ausente.

### Evaluación y despliegue (pendientes de ejecutar en el PC)

* **Evaluación:** `scripts/run_eval_fix3.ps1 [-Corridas 3]`.
  * Carga la clave de Gemini del `.env` y **quita `GROQ_API_KEY` de la sesión**, para que la evaluación sea solo con Gemini.
  * Pasos: pruebas → suite → R1 (recuperación, sin LLM) → cuota → confirmación → N corridas A/B (`--set fix3`: A = experimental actual, B = todas las correcciones) → resumen de estabilidad por pregunta (`scripts/summarize_repeated_ab.py`).
  * Coste estimado: unos COP 1000 por corrida.
* **Despliegue:** `deploy/exp/deploy_fix3_exp.ps1`.
  * Pasos: pruebas como condición previa → commit **local** (sin push), con confirmación → paquete → subida → reinstalación **solo de la instancia experimental** (`EXP_FIX3=1`, `EXP_LLM_SCHEMA=1`), con confirmación → comprobación de la clave.
  * Producción no se toca.

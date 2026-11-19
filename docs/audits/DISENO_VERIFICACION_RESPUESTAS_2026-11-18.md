# Diseño de la verificación de respuestas (sustituto del DIG bloqueante)

**Fecha:** 2026-11-18. **Estado:** HIPÓTESIS CON EVIDENCIA EXPERIMENTAL PRELIMINAR. **No es una solución validada en operación** (ver sección 9). Es una propuesta para ejecución futura. No hay código de la aplicación modificado, nada desplegado y nada en producción alterado.
**Autorización:** el PO autorizó analizar los problemas del DIG y diseñar una solución, usando el LLM si es mejor. DIG-05 y DIG-09 siguen protegidos; aplicar este diseño requiere aprobación expresa del PO.

## 1. Resumen

1. **Producción (`bb1d32d`) no tiene DIG.** Solo comprueba que los identificadores citados pertenezcan al contexto entregado. El DIG (`src/decision_integrity.py`) entró con v1.4.0.
2. **El DIG rechaza respuestas correctas y no detecta errores reales.**
   - En las respuestas registradas de v1.4.0 y de la candidata, 45 consultas respondibles acabaron en abstención.
   - Leídas una a una, todas tenían contenido normativo correcto. Solo 5 presentaban defectos menores: una cita irrelevante, respuestas incompletas ante preguntas ambiguas y una excepción relevante omitida.
   - Ninguno de los rechazos detectó una cifra inventada.
   - A la vez, el DIG **permitió** una respuesta con la condición invertida (V06, tatuajes), que producción había respondido bien.
3. **Las causas son estructurales, no casos aislados** (sección 3). La principal es que el DIG mide la pertinencia por coincidencia de palabras raras y que veta la respuesta entera ante cualquier fallo.
4. **Un verificador LLM de una sola llamada discrimina mucho mejor.**
   - Acepta los pasajes citados en el 100 % de las respuestas correctas y rechaza las preguntas de otro tema (1 de 78 aceptada, y además relacionada).
   - Detecta el 100 % de las cifras alteradas.
   - Cuesta unos 1,1 s y una llamada a `gemini-flash-lite-latest` por consulta.
5. **Diseño propuesto:** una capa determinista mínima, un verificador LLM y la regla de **corregir antes de rechazar** (sección 5).

## 2. Hallazgos

### 2.1 Fallos por control en las respuestas registradas

Fuente: `data/eval/consolidacion_2026_11/{v140,cand3,val_cand3}.jsonl`, Gemini `gemini-flash-lite-latest`.

| Control | v1.4.0 (36) | candidata (36) | candidata, validación (23) | Único fallo |
|---|---|---|---|---|
| DIG-05 pertinencia | 12 | 17 | 9 | 6 / 7 / 2 |
| DIG-09 excepciones | 1 | 3 | 4 | 0 / 2 / 2 |
| DIG-02 cita por pasaje | 3 | 5 | 4 | — |
| DIG-03 cita literal | 4 | 3 | 2 | — |
| DIG-06 cifras | 4 | 5 | 0 | — |

### 2.2 Revisión manual de los rechazos (SI, PARCIAL y AMBIGUA)

| Clase de rechazo | Ejemplos | ¿Error real? |
|---|---|---|
| Tema central con términos frecuentes (judogi, pesaje, entrenador, equipo, categoría) | B01, B02, B03, C02, E01, V09 | No |
| Sinónimo u ortografía (prohibited/not allowed, color/colour, fail/not pass, fingernails/nails) | D01, E03, H03, V21 | No |
| Cita corta de tabla o lista (<6 palabras: «a) Ippon: 20 seconds», «4 minutes real contest time») | A03, L01, D02 | No; arrastra DIG-05, 06 y 12 |
| Cita con «...» (no literal) | B02 v1.4.0 | No; arrastra DIG-06 |
| Identificador citado sin fragmento (sobrecitación) | B04, E01, F02, V05, V11 | No; bastaba retirar la cita |
| DIG-09: excepción no citada en la ventana de ±2 oraciones | C03 («Exceptions» es un encabezado), V05 (cubrir la cabeza), V12 (medallas) | No en 5 de 8; G01, V03 y V20: excepción relacionada, omisión menor |
| Respuesta negativa correcta («el SOR no regula X») | J02, J03, J04, V18, V19 | No; el DIG no tiene vía para respuestas negativas |
| Cita irrelevante dentro de una respuesta correcta | V12 (P038) | Sí, menor: bastaba retirar la cita |
| Respuesta incompleta o débil | V23, L01 y L02 de la candidata | Sí, de completitud, no de exactitud |

**Error que el DIG dejó pasar:**
- **V06**, «¿Puede un atleta competir con un tatuaje visible?». La candidata con DIG respondió que puede competir «únicamente si» el tatuaje es político, religioso, etc., lo que invierte la norma.
- DIG: PERMITIR.
- Producción, sin DIG, respondió correctamente.

### 2.3 Medidas complementarias

- De 233 citas, 8 son literales pero tienen menos de 6 palabras (`MIN_QUOTE_WORDS`): filas de tabla y elementos de lista.
- El DIG-05 vigente, medido por pasaje citado sobre 81 respuestas pertinentes, acepta 56 con su propia consulta y 20 de 405 con consultas de otro tema.

## 3. Causas raíz (clases generales)

| Código | Deficiencia estructural | Clase de consultas afectada |
|---|---|---|
| C1 | La pertinencia exige un término de frecuencia documental ≤15 %. Los términos del tema central del SOR son frecuentes y no cuentan; tampoco cuentan sinónimos ni variantes ortográficas. | Preguntas sobre los temas más consultados (equipamiento, pesaje, entrenadores, equipos, categorías) y preguntas con paráfrasis |
| C2 | Veto total: un fallo en una sola cita descarta la respuesta entera. | Toda respuesta con varias citas; empeora con respuestas más completas |
| C3 | Longitud mínima de cita de 6 palabras. | Datos en tablas o listas (tiempos, categorías, sanciones enumeradas) |
| C4 | Un identificador mencionado sin fragmento invalida la respuesta (DIG-02) en lugar de retirar esa mención. | Respuestas que citan pasajes de apoyo |
| C5 | DIG-09 busca marcadores léxicos de excepción (only, except, nevertheless, «Exceptions») en ±2 oraciones, sin juzgar si la excepción afecta a lo preguntado; incluye encabezados. | Normas con excepciones cercanas sobre otros aspectos |
| C6 | No hay vía para respuestas negativas o parciales: DIG-01 exige RESPALDADA y DIG-05 exige pertinencia de las citas. | Preguntas fuera del SOR o mixtas |
| C7 | Cascada: una cita no localizada hace fallar DIG-03, 05, 06 y 12 a la vez. | Todas |
| C8 | El DIG no verifica el respaldo de lo que se afirma (nivel D: «NO VERIFICADO»), solo coincidencias léxicas, así que no detecta inversiones lógicas ni alcances mal generalizados. | Integridad: precisamente los errores graves |

## 4. Alternativas medidas (sin modificar la aplicación)

**Positivos:** 78 respuestas correctas, cada una con su propia consulta.

**Controles negativos:**
- (a) La misma respuesta y las mismas citas con una consulta de otro tema, de páginas a más de 15 de distancia.
- (b) La misma respuesta con **una cifra alterada** que no figura en las citas (30 casos).

| Método | Acepta respuestas correctas | Acepta consulta de otro tema | Detecta cifra alterada | Coste |
|---|---|---|---|---|
| DIG-05 vigente (por pasaje; 81/405) | 56/81 (69 %) | 20/405 (5 %) | — (DIG-06 sí, si la cita es localizable) | 0 |
| Embeddings MiniLM, coseno ≥0,45 | 75/81 (93 %) | 24/405 (6 %) | no aplica | local |
| LLM, juzgando solo con las citas | pertinencia 78/78; respaldo completo 36/78 | 0/78 | 30/30 | 1 llamada |
| **LLM, juzgando con los pasajes citados** (flash-lite) | **70/78 sin poda; 77/78 con poda** | **1/78** (F01 «judogi», tema relacionado) | **30/30** | 1 llamada, mediana 1,1 s, p90 1,6 s, unos 4.900 caracteres de entrada |
| **LLM con pasajes, `gemini-flash-latest`** | **67/78 sin poda; 76/78 con poda** | no medido | **30/30**; además **detecta V06** | 1 llamada, mediana 4,7 s, p90 9,4 s |

**Observaciones:**
- **Juzgar solo con las citas es demasiado estricto:** el modelo resume información de los pasajes entregados que no copió en sus citas.
- **Juzgar con los pasajes citados** deja 9 de 299 frases sin respaldo, y son defectos reales o discutibles:
  - D02 añade acciones de hansoku-make que no están en los pasajes citados;
  - V23 menciona los Juegos Olímpicos sin respaldo;
  - L02 de v1.4.0 atribuye una regla a un pasaje que no la contiene;
  - V01 dice «cuatro minutos», un dato cierto pero de otro pasaje.
- **El verificador no es infalible.** En la pasada con citas detectó la inversión de V06; en la pasada con pasajes (flash-lite), no. Por eso el diseño combina capa determinista, poda y una evaluación con el modelo adecuado (sección 7).
- **`gemini-flash-latest` detecta errores más finos:**
  - la inversión de V06;
  - «únicamente si» donde la norma dice «if» (C01 de v1.4.0);
  - la comisión equivocada en V20;
  - la sanción atribuida sin respaldo en V16.

  A cambio, tarda unas 4 veces más (mediana 4,7 s). Las 13 frases que marca como no respaldadas son defectos reales o discutibles.
- **Recomendación:** usar `gemini-flash-latest` como verificador, porque en un asistente normativo la exactitud pesa más que unos segundos, y mantener flash-lite como alternativa si la latencia resulta inaceptable en el uso real.

## 5. Diseño propuesto: verificación V4

Un único verificador, con cada componente justificado por una precisión medida y sin reglas por consulta, artículo, página ni identificador.

### Capa 1 · Determinista (barata y precisa)

Actúa **por cita, no por respuesta**.
1. **Pasaje entregado:** el identificador citado figura en el contexto entregado al modelo; es la validación que ya tiene producción.
2. **Cita literal, con reparación previa:**
   - partir las citas con «...»;
   - asignar un identificador gemelo (misma página, mismo texto);
   - **ampliar una cita corta a su renglón completo del pasaje**, como fila de tabla o elemento de lista, en lugar de rechazarla (corrige C3).
3. **Sin SHADOW:** se mantienen DIG-04 y DIG-08; ninguna cita ni huella procede solo del material complementario.
4. **Cifras:** toda cifra afirmada figura en los **pasajes citados**, con la exclusión de referencias documentales de DIG06_REFS. Es la protección más valiosa contra cifras inventadas, y es determinista.

Una cita que no supera la capa 1 se **retira** junto con las frases que solo se apoyan en ella; la respuesta no se descarta (corrige C2, C4 y C7).

### Capa 2 · Verificador LLM (una llamada; sustituye a DIG-05 y DIG-07)

- **Entrada:** la pregunta, los pasajes citados completos, las citas numeradas y las frases numeradas de la respuesta.
- **Salida JSON:**
  - `pertinent` por cita;
  - `supported` por frase, con los elementos sin respaldo;
  - `answers_question`.
- **Instrucciones clave:**
  - juzgar solo con los pasajes;
  - las referencias de artículo y página no son hechos;
  - prestar atención a condiciones invertidas, cifras distintas y alcance mal generalizado.
- **Acción:**
  - retirar las citas no pertinentes y las frases sin respaldo;
  - si queda al menos una frase respaldada y `answers_question` es verdadero, la respuesta se emite podada;
  - si no queda ninguna, se abstiene.

### Capa 3 · Completado en lugar de veto (sustituye a DIG-09)

- Las oraciones con excepción de la misma unidad derivada se pasan al verificador.
- Las que juzga pertinentes a la pregunta se **añaden** a la respuesta como «Excepción», con su cita literal. Nunca provocan abstención (corrige C5).

### Respuestas negativas y parciales (corrige C6)

- Se permiten frases del tipo «los pasajes del SOR 2026 no contienen X», que el verificador marca como respaldadas, siempre que no contengan cifras ni afirmaciones normativas.
- La parte respondible de una pregunta mixta se verifica como cualquier otra.

### Modo degradado (sin LLM o si el verificador falla)

- Capa 1 y, después, **decide el DIG completo** sobre la respuesta ya corregida: sin verificación semántica no se relaja ningún control.
- La respuesta se marca con «verificación reducida» en el indicador de origen.
- *Cambio en la implementación (2026-11-18):* la primera versión usaba solo pertinencia por embeddings (coseno ≥0,45). Las pruebas adversariales existentes mostraron que así se emitían respuestas de otro tema que el DIG rechazaba, por lo que se sustituyó por la caída conservadora.

### Coste

- Una llamada adicional por consulta, de unos 5.000 caracteres de entrada.
- Latencia: mediana de 4,7 s con `gemini-flash-latest` (recomendado) o de 1,1 s con flash-lite.
- La capa 1 es local.

## 6. Plan de ejecución (cuando se autorice)

1. **Implementación detrás de un flag**, en el proyecto nuevo o en una rama experimental. DIG-05 y DIG-09 no se tocan hasta la decisión del PO.
2. **Evaluación** con el mismo modelo generador que producción:
   - el conjunto de diagnóstico (36) y el de validación (23);
   - mutaciones automáticas de cifras, condiciones y alcance (integridad);
   - consultas de otro tema (pertinencia);
   - el conjunto sellado solo para la prueba final y con autorización.
3. **Criterios de aceptación:**
   - respondibles respondidas ≥ producción (27/27 y 16/16);
   - 100 % de cifras alteradas detectadas;
   - ≥90 % de condiciones invertidas detectadas (conjunto de mutaciones nuevo);
   - ≤2 % de consultas de otro tema aceptadas;
   - 0 errores normativos en la revisión humana de las respuestas emitidas;
   - latencia adicional con un p90 que fije el PO: unos 10 s con flash y unos 2 s con flash-lite, según lo medido.
4. **Precisión de cada componente**, medida con `scripts/replay_dig.py`: cuántos de sus rechazos o podas eran errores reales. Un componente con más falsos rechazos que aciertos no se activa.
5. **Despliegue en paralelo** frente a producción y sustitución solo con aprobación del PO.

## 7. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| El verificador LLM no es determinista y puede pasar por alto una inversión lógica (V06 con pasajes y flash-lite) | Usar `gemini-flash-latest` (detectó V06); temperatura 0; cifras siempre en la capa determinista; conjunto específico de mutaciones lógicas como criterio de aceptación |
| El verificador puede podar frases correctas | La poda conserva la respuesta si queda contenido respaldado; se registra lo podado para auditoría |
| Dependencia del proveedor | Modo degradado determinista con indicador visible |
| Coste y cuota | Una sola llamada pequeña; medir consumo en la evaluación |

## 8. Evidencia y herramientas

Todo está en el directorio temporal de la sesión, fuera del repositorio:
- `pert_emb.py` y `pert_emb2.py`: pertinencia léxica frente a embeddings;
- `verif/build_cases.py`: casos positivos, mutaciones y consultas de otro tema;
- `verif/run_verifier.py` y `verif/run_verifier2.py`: verificador LLM, solo con citas y con pasajes;
- `verif/analyze.py`;
- `verif/out.jsonl`, `verif/out2.jsonl` y `verif/out3.jsonl`: resultados.

Ejecución en OCI:
- contenedor temporal con la imagen de producción y su archivo de entorno, sin puertos publicados;
- directorio `/home/ubuntu/ijf-verif`, que se elimina al terminar;
- producción no se tocó.

## 9. Estado de validación: lo que estos resultados NO demuestran

Los resultados de la sección 4 son prometedores, pero **no equivalen a una solución validada en operación**. Se mantiene esta distinción hasta completar la sección 6.

1. **No se probó en el flujo real.** El verificador juzgó respuestas ya registradas. La poda, el completado de excepciones y la vía de respuestas negativas no están implementados; no se sabe cómo quedan las respuestas podadas ni si siguen siendo útiles.
2. **La muestra es pequeña y en parte no independiente.**
   - Son 78 respuestas de 59 preguntas, con un solo modelo generador.
   - El conjunto de diagnóstico ya se usó para analizar los fallos; solo las 23 preguntas de validación son independientes.
   - Cada caso se evaluó una vez, sin medir cuánto varía el juicio del verificador entre ejecuciones.
3. **La prueba de integridad es limitada.**
   - Las 30 mutaciones son solo de cifras.
   - Hay un único caso natural de condición invertida (V06): que `gemini-flash-latest` lo detecte y flash-lite no es una observación, no una tasa.
4. **El juicio de corrección no es humano.** La afirmación «los rechazos eran respuestas correctas» procede de la lectura del asistente contra los pasajes; debe confirmarla una persona con criterio arbitral.
5. **El control negativo es imperfecto.** Algunas consultas «de otro tema» eran afines (p. ej. F01, judogi).
6. **Latencia y coste se midieron de forma aislada**, sin carga real ni límites de cuota.

**Condición para considerarla validada:** que se cumplan los criterios de la sección 6 en una evaluación de extremo a extremo frente a producción, con revisión humana, repeticiones y mutaciones lógicas, y que tú la apruebes tras un periodo en paralelo.

## 10. Resultados de la versión candidata V4 (2026-11-18)

**Estado: implementada detrás de flag y evaluada de extremo a extremo frente a producción. Sigue sin estar validada en operación** (pendiente de revisión humana, repeticiones y periodo en paralelo; ver sección 9).

**Qué se evaluó.**
- Rama local `exp/verificacion-v4`, sin commit.
- Contenedor temporal en OCI, con la imagen de producción y un worktree de 76a0eed más los cambios locales; producción no se tocó.
- Flags: la candidata v1.4.0 más `ADA_VERIFICATION_V4=1 ADA_CITATION_REPAIR=1 ADA_QUOTE_REPAIR=1`.
- Modelos: generador `gemini-flash-lite-latest` (el de producción) y verificador `gemini-flash-latest`, que el proveedor resolvió como `gemini-3.8-flash`.
- Resultados en `data/eval/verificacion_v4_2026_11/`.

| Criterio (sección 6) | Producción (grabada) | V4 | Estado |
|---|---|---|---|
| Respondibles (SI), conjunto de 36 | 22 respuestas IA + 5 listas de respaldo (la IA falló la validación de citas) | 26 respuestas IA, 1 abstención (G01) | No cumple 27/27 por G01 |
| Respondibles (SI), conjunto de 23 | 15 respuestas IA + 1 lista de respaldo | 16 respuestas IA | Cumple |
| Cifras alteradas detectadas | — | 19/19 (11 abstenciones, 8 frases retiradas), más 30/30 en la sección 4 | Cumple |
| Condiciones invertidas ≥90 % | — | No medido: requiere un conjunto nuevo y no se crearon benchmarks | Pendiente |
| Otro tema ≤2 % | — | No medido en esta ronda | Pendiente |
| Revisión humana sin errores | — | Lista en `REVISION_HUMANA.md` (53 respuestas) | Pendiente (persona) |
| Latencia | p50 2,8 s / p90 4,0 s | p50 8,4–9,6 s / p90 13–14 s; verificador p90 ≈ 9,8 s | La decide el PO |
| Fallos del verificador | — | 0 (modo LLM en todas las respuestas que llegaron a verificación) | — |

**Fallos encontrados y tratados.**

1. *Modo reducido permisivo.*
   - La pertinencia solo por embeddings emitía respuestas de otro tema que el DIG rechazaba; lo detectaron las pruebas adversariales existentes.
   - Corregido: sin verificador decide el DIG completo (sección 5).
2. *Identificador de página cosida.*
   - El `PassageStitcher` muestra en el texto entregado los identificadores de las páginas cosidas (`KUN: … -> …`). El modelo los cita y la validación de citas los rechazaba.
   - Era la causa de 3 abstenciones (C02, D02, E01). En producción, de las listas de respaldo: C02 y D02.
   - Corregido de forma genérica en `ADA_CITATION_REPAIR`: el identificador se atribuye al pasaje entregado que lo contiene, solo si todas sus citas son literales en él.

**Fallos pendientes (sin corregir).**

- **G01.** El modelo añade a `citations` un identificador inexistente (`P055-S055`, errata de `P045-S055`) sin cita literal. La validación de citas, anterior a V4, veta toda la respuesta. Propuesta: bajo V4, retirar los identificadores inexistentes sin cita, como la capa 1b, en lugar de vetar.
- **J03** (no respondible). La respuesta negativa contenía cifras y se abstuvo, que es el comportamiento diseñado.
- **L02 y V23** (ambiguas). La recuperación no entregó los pasajes esperados; el verificador retiró lo no respaldado y la respuesta quedó vacía. Es una brecha de recuperación, no de verificación.
- **V06.** En esta ejecución el generador no invirtió la condición, así que esta ronda no mide la detección de inversiones.

## 11. Corrección general de identificadores inexistentes (G01) — 2026-11-19

**Cambio.** El cambio está en `src/evidence_reassembly.py` (`repair_citation_ids`, dentro de `ADA_CITATION_REPAIR`) y solo se aplica a identificadores que no existen en el corpus:

| Caso | Condición | Acción |
|---|---|---|
| A | Tiene citas literales (≥ `MIN_QUOTE_WORDS` palabras) y todas aparecen en un único pasaje entregado | Se reasigna a ese pasaje (estado `Reasignado`) |
| B | No tiene citas, y en cada aparición va en una lista `[ID, …]` o en `citations` junto a otro identificador entregado | Se retira solo el inexistente (estado `Retirado`, motivo "Identificador inexistente en el corpus") |
| C | Es el único respaldo de alguna afirmación (aparece solo o fuera de una lista de identificadores) | Sin cambio: la validación de citas lo rechaza, como antes |
| D | El identificador existe pero no se entregó | No le afecta la regla nueva; se mantienen las reglas de gemelo y página cosida |
| E | Tiene una cita no literal o el destino es ambiguo (varios pasajes) | Sin cambio |

La regla no usa ninguna semejanza entre identificadores y no se activa si no hay corpus. Después de la reparación se ejecutan, sin cambios, la validación de citas, la reparación de citas, V4 y el DIG.

**Pruebas.**
- 7 pruebas nuevas en `tests/test_evidence_reassembly.py`: casos A–E, el caso ambiguo y el caso sin corpus.
- Suite completa:
  - por defecto: 639 passed / 21 skipped;
  - candidata sin V4: 638 / 22;
  - candidata con V4: 638 / 22.

**Evaluación en OCI.** Mismo procedimiento que en la sección 10; producción no se tocó. Evidencias en `data/eval/verificacion_v4_2026_11/g01_identificadores/`.

- **Límite del proveedor.** A partir de V16 del conjunto de validación, Gemini respondió HTTP 429 ("monthly spending cap exceeded"). Desde ahí, la generación pasó a Groq o falló, y el verificador no estuvo disponible (modo reducido).
- **G01 en ejecución nueva:** SUCCESS. Pero en esa ejecución el modelo no generó el identificador inexistente, así que la regla no intervino.
- **G01 con la respuesta grabada** (la misma salida del modelo que causó la abstención; `eval_replay.py`):

| Código | Validación de citas | Resultado |
|---|---|---|
| Anterior | Falla | ABSTAIN (validación de citas SOR primarias) |
| Nuevo | Supera; `P055-S055` queda Retirado | Llega a V4 en modo REDUCIDO (verificador con 429); el DIG completo se abstiene por `DIG-09_EXCEPCIONES_CITADAS` |

  No se pudo comprobar qué decidiría V4 con el verificador disponible.
- **Mutaciones:** 16/16 detectadas, pero las 16 en modo REDUCIDO por el 429. No es comparable con el 19/19 en modo LLM de la sección 10.
- **Regresión:** 11 cambios de estado; ninguno pasa por la regla nueva (ningún registro con `Retirado`/`Reasignado` por identificador inexistente salvo la reproducción).
  - V16–V22, SUCCESS → ABSTAIN: Gemini 429 (sin modelo, o Groq con verificador no disponible).
  - D01, SUCCESS → ABSTAIN: el verificador agotó el tiempo de espera; en modo reducido, DIG-05/07.
  - D02, SUCCESS → ABSTAIN: cita `P192-S198`, que existe pero no se entregó en esta ejecución (la recuperación cambió con la traducción). El código anterior y el nuevo dan el mismo resultado.
  - G01 y L02, ABSTAIN → SUCCESS: variación del generador; la regla nueva no intervino.

**Pendiente.** Con el límite de Gemini restablecido, falta repetir:
1. la reproducción de G01 en modo V4 completo;
2. el conjunto de validación desde V16;
3. las mutaciones en modo LLM.

**Decisión del responsable del proyecto (2026-11-19).** En producción, el verificador V4 usará `gemini-flash-lite-latest` en lugar de `gemini-flash-latest`, y se aplicará cuando V4 se despliegue en OCI. Mientras tanto, las evaluaciones siguen con `gemini-flash-latest` para que las comparaciones sean congruentes. Todavía no se ha aplicado: el valor por defecto de `ADA_VERIFIER_MODEL` en el código no ha cambiado. Los resultados de V4 de las secciones 10 y 11 (mutaciones 19/19, revisión humana 54/54) se obtuvieron con `gemini-flash-latest` y no se han medido con flash-lite. En la comparación de la sección 4, flash-lite no detectó la inversión de V06.

**Ronda 2 (2026-11-19, con el límite de gasto restablecido; verificador `gemini-flash-latest`).** Se repitieron solo los casos afectados por el 429. Evidencias en `g01_identificadores/ronda2_credito_restablecido/`.

- **G01 con la respuesta grabada:** SUCCESS en V4 completo (modo LLM, `gemini-3.8-flash`):
  - la regla nueva retiró `P055-S055`;
  - V4 retiró `P043-S054`, que estaba citado sin cita literal;
  - el DIG dio PERMITIR.
- **Defecto de presentación (V4, anterior a este cambio).** Al retirar un identificador intermedio de una lista, `_strip_ids` (`answer_verification.py`) deja un separador vacío: `normative_basis` muestra `[SOR-…-P042-S053, , SOR-…-P044-S054]`. Sin corregir.
- **D01, D02 y V16–V21:** vuelven a SUCCESS (modo LLM).
- **V23:** pasa de ABSTAIN a SUCCESS. Es una respuesta nueva sin revisión humana.
- **V22:** ABSTAIN en una ejecución, porque el traductor escribió "weight-in" y la recuperación quedó vacía antes del modelo. Al repetirla, SUCCESS. Es fragilidad de la traducción y no tiene relación con la regla.
- **Mutaciones (modo LLM):** 15/15 detectadas (11 abstenciones, 4 frases retiradas). Hay 4 menos que en la sección 10 (G01, L01, L02, V22) porque esta vez esas respuestas no tenían una cifra citada en `summary` que se pudiera mutar. Ninguna mutación quedó sin detectar.
- **Regresión sobre las 53 respuestas emitidas antes:** todas siguen emitidas, contando V22 en su repetición. La regla nueva solo intervino en la reproducción de G01.
- **Respuestas que pasan de abstención a SUCCESS** y que nunca tuvieron revisión humana: G01 (ejecución nueva), L02 y V23.

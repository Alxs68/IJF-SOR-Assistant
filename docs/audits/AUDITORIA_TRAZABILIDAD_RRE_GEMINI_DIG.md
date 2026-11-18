# Auditoría de trazabilidad RRE → Gemini → DIG

Fecha: 2026-11-16 · Intervención **exclusivamente diagnóstica**.
* Sin cambios en código, reglas, corpus, documentos oficiales ni benchmark.
* Sin llamadas a Gemini, Groq ni otros proveedores, sin despliegues y sin commit.
* Todo sale de registros ya almacenados y se reproduce con el DIG en memoria.

## 1. Resumen ejecutivo

Se analizaron las **328 ejecuciones** almacenadas de las 41 preguntas DEV de benchmark_v2 (8 corridas). En 198 hubo una respuesta generada.

**Respuestas generadas a las 31 preguntas respondibles: 149**

| Resultado | Filas | % |
|---|---|---|
| Correctas aceptadas | 66 | 44,3 % |
| **Correctas rechazadas** | **55** | **36,9 %** |
| Incorrectas o sin respaldo, rechazadas | 15 | 10,1 % |
| El modelo declaró falta de evidencia | 12 | 8,1 % |
| No evaluable (JSON inválido) | 1 | 0,7 % |

**Respuestas generadas a las 10 preguntas no respondibles: 49**

| Resultado | Filas | % |
|---|---|---|
| **Incorrectas aceptadas** (5 respuestas a preguntas ambiguas) | **5** | **10,2 %** |
| Abstenciones correctas | 42 | 85,7 % |
| Aclaraciones correctas | 2 | 4,1 % |

**Por qué se rechazan las 83 respuestas a preguntas respondibles** (causa principal):

| Causa | Filas | % | Desglose |
|---|---|---|---|
| **El DIG** | **50** | **60,2 %** | 23 falsos positivos vigentes; 17 por exigencia de literalidad; 10 falsos positivos que el DIG actual ya acepta |
| **La recuperación** | **27** | **32,5 %** | 22 por fusión o selección; 5 por recuperación incompleta |
| La generación | 6 | 7,2 % | 5 citas no literales; 1 interpretación errónea |

**Por pregunta.** De las 31 respondibles, **10 no se aceptaron en ninguna de las 8 corridas**:
* **6 por recuperación:** EXC-003, MLG-002, SCO-013, SCO-014, SCO-019, SCO-020. En todas ellas el rechazo del DIG fue **correcto**.
* **4 por el DIG con respuesta correcta:** DIR-005, EXC-009 y SCO-025 (DIG-11) y SCO-024 (DIG-09).

**Contenido.**
* De las 290 afirmaciones de las respuestas correctas rechazadas, 41 contienen datos no citados: **38 (93 %) están en el propio pasaje citado**, 2 en otro pasaje entregado y 1 sin fuente (la palabra «tatami»).
* Si se cuentan todas las rechazadas, incluidas las incorrectas: de 53 afirmaciones con datos no citados, 46 están en el pasaje citado, 4 en otro pasaje entregado y 3 sin fuente.
* Las 232 afirmaciones de las respuestas aceptadas están respaldadas literalmente.
* No se observó invención de reglas en respuestas correctas.

**Dictamen breve (§11): la causa es combinada.**
* **Respuestas correctas perdidas:** se deben sobre todo a que el validador no reconoce como respaldadas afirmaciones fieles al SOR. Unas veces evalúa algo que no es la respuesta (DIG-11 mira la pregunta; DIG-09 mira la cercanía en el texto; DIG-06 cuenta cifras que vienen de la propia consulta). Otras veces exige cita literal de datos accesorios que el modelo tomó del mismo pasaje.
* **Preguntas sin respuesta:** se deben sobre todo a la **recuperación**. En esos casos el DIG acierta al rechazar.

## 2. Metodología

1. **Unificación de registros.** Se reunieron las 8 corridas almacenadas (§3). Para 181 respuestas se conserva la **entrada exacta del DIG**: respuesta cruda, consulta, traducción, pasajes entregados con su texto y textos SHADOW. En 142 de ellas también se conserva el texto de instrucciones.
2. **Reevaluación con el DIG actual.** Cada entrada se reevaluó en memoria con el DIG actual (`DIG-1.3+NUM-v2+FIX-v3`; `+ALL` para la corrida de respuesta única). Así se separan los rechazos que ya están corregidos de los que persisten. Las decisiones oficiales registradas **no se modificaron**.
3. **Trazabilidad de la recuperación.** Para cada pregunta se usaron los rangos por canal (TF-IDF, denso, salida final) del diagnóstico de recuperación de Fase 11 (`data/eval/fase11/diag_retrieval_dev.json`) y los pasajes realmente entregados en cada corrida.
4. **Análisis por afirmación.**
   * **Corte:** cada campo visible se dividió en frases completas, sin cortar referencias ni abreviaturas.
   * **Clasificación de cada frase:**
     * literal o sin datos verificables;
     * con datos presentes en el **pasaje citado**;
     * con datos en **otro pasaje entregado**;
     * con datos **sin fuente entregada**.
   * **Criterio:** se usan los mismos criterios de cifras y términos distintivos que DIG-06 y DIG-07.
5. **Juicio de contenido.**
   * **Revisión:** el auditor leyó cada respuesta rechazada (83) y cada aceptada dudosa (7) frente al texto del SOR.
   * **Etiquetas:** correcta (C); correcta según el texto con SOR ambiguo (CA); incorrecta (I); conclusión sin respaldo citado (NS); el modelo declaró falta de evidencia (ABS); no evaluable (NE).
   * **Coincidencia textual:** no se usó como único criterio. Una paráfrasis fiel cuenta como correcta.
6. **Clasificación de causas.** Se usaron los códigos solicitados (RRE-ERR, RRE-INC, RRE-FUS, GEN-INT, GEN-RED, GEN-CIT, DIG-FP, DIG-FN, DIG-CR, PIPE-ERR), con una causa principal por fila según esta prioridad: recuperación > integración > generación > DIG.
7. **Contraste.** Se simuló en memoria la retirada de cada regla del DIG, de una en una, y se reclasificó el resultado con el evaluador del proyecto.

Herramientas de análisis, fuera del repositorio: `~/aud_work/traz/` (`data.py`, `claims.py`, `causes.py`, `labels.py`).

## 3. Inventario de datos disponibles

| Corrida | Filas | Con generación | Con entrada exacta del DIG | Sin generación | Configuración |
|---|---|---|---|---|---|
| F11#1 | 41 | 14 | 13 | 27 | Fase 11, corrida 1, DIG v2 |
| F11#2 | 41 | 7 | 7 | 34 | Fase 11, corrida 2, DIG v2 |
| INT-orig | 41 | 13 | 12 | 28 | Integración R3, configuración original |
| INT-exp | 41 | 7 | 7 | 34 | Integración R3 + DIG v2 |
| AB-A | 41 | 38 | 37 | 3 | A/B anterior, variante A: DIG v3 (antes de U/X), sin esquema |
| AB-B | 41 | 37 | 32 | 4 | A/B anterior, variante B: esquema + regla 14 |
| UA-A | 41 | 41 | 36 | 0 | Respuesta única, variante A: DIG v3, contrato anterior |
| UA-B | 41 | 41 | 37 | 0 | Respuesta única, variante B: validación integral y contrato único |
| **Total** | **328** | **198** | **181** | **130** | |

* **Generaciones:** 160 de Gemini (`gemini-flash-lite-latest`, que hoy resuelve a `gemini-3.5-flash-lite`) y 38 de Groq (`openai/gpt-oss-120b`).
* **Filas sin generación (130):** se concentran en Fase 11 y en la integración R3, por la cuota del plan gratuito. **No sirven para evaluar el DIG.**
* **Prompt:** no se almacenó como texto único. Es reconstruible con el texto de instrucciones y los pasajes entregados en 142 de las 181 filas con entrada del DIG.
* **Puntuaciones de recuperación:** las corridas no guardan puntuaciones por pasaje. Solo existen los rangos por canal del diagnóstico de Fase 11, que puede diferir de la recuperación actual (R3 activo).
* **Etiquetas del benchmark:** están en estado `PENDING_EXPERT_REVIEW`.

## 4. Trazabilidad individual de los casos

Se reconstruyeron fichas A–E para las 83 respuestas rechazadas a preguntas respondibles y para las 7 aceptadas dudosas (`~/aud_work/traz/review1.txt`). Aquí se recogen los **13 casos solicitados o representativos**, con la corrida más reciente. Los rangos de recuperación proceden del diagnóstico de Fase 11.


#### B2-CAT-007 — corrida UA-B

**A. Consulta.** «At a Grand Prix Cadets, how many athletes per country and weight category can obtain Cadets WRL points?» · idioma `en` · categoría `DISTINCION_CATEGORIA` · comportamiento esperado: respondible.
Evidencia esperada: p. 55 «At Grand Prix Cadets events only the two (2) best domestic athletes per weight category can obtain points».

**B. RRE.** Traducción usada: `At a Grand Prix Cadets, how many athletes per country and weight category can obtain Cadets WRL points?`. Pasajes entregados (6): P188-S196 (Article 18.1.4, p. 188, evidence), P055-S069 (3.3, p. 55, evidence), P054-S068 (3.2.3, p. 54, evidence), P052-S065 (3.2, p. 52, evidence), P057-S072 (3.3.3, p. 57, evidence), P175-S191 (Article 18, p. 175, related).
Diagnóstico de recuperación (Fase 11, forma DICT): rango de la evidencia esperada TF-IDF=1, denso=2, salida final=1 → `OK_TOP5`.
Diagnóstico de recuperación (Fase 11, forma LLM): rango de la evidencia esperada TF-IDF=1, denso=2, salida final=1 → `OK_TOP5`.
Evidencia esperada en el paquete entregado: **sí**.

**C. Generación.** Modelo `gemini-flash-lite-latest` (Gemini); answerability `RESPALDADA`.
Respuesta (summary): «At a Grand Prix Cadets event, the Sport and Organisation Rules do not specify a numerical limit on the number of domestic athletes per weight category who can obtain Cadets World Ranking List (WRL) points, whereas specific limits are established for Grand Prix events under senior rules and World Championships Cadets [SOR-2026-08-P054-S068].»
- Cita P054-S068 (literal): «Athletes can earn points for the IJF Cadets WRL by competing in Continental Cups Cadets, Continental Championships Cadets, Grand Prix Cadets and World Champions»

**D. DIG** (versión actual `DIG-1.3+NUM-v2+FIX-v3+ALL`; orden DIG-00→DIG-12). Fallan: `DIG-02_CITAS_CON_CITA_LITERAL` (citados=['SOR-2026-08-P054-S068', 'SOR-2026-08-P055-S069'] sin_cita_literal=['SOR-2026-08-P055-S069']), `DIG-08_SIN_INFLUENCIA_SHADOW` (presentes_solo_en_SHADOW: cifras=[] terminos=['cuota']), `DIG-12_CIFRA_PARA_PREGUNTA_CUANTITATIVA` (pregunta_cuantitativa=True cifras_en_citas=[]).

**E. Resultado.** Estado `ABSTAIN` → `ABSTENCION_GENERACION_SIN_CITA_CORRECTA`. El usuario habría recibido la abstención normativa (sin dictamen) y los pasajes solo como consulta.
Juicio del auditor sobre el contenido: **I** — UA-B afirma que el SOR no fija limite; el SOR dice "two (2) best domestic athletes": falso. Clasificación: `GEN-INT`.

#### B2-EXC-006 — corrida UA-B

**A. Consulta.** «Quien compite en individual y en mixto, ¿puede dar el peso siempre con el margen del 5%?» · idioma `es` · categoría `EXCEPCION` · comportamiento esperado: respondible.
Evidencia esperada: p. 82 «must be within the weight limit of their mixed team category (without the +5% tolerance) at least once during ».

**B. RRE.** Traducción usada: `individual and mixed team competitors weight margin five percent allowance`. Pasajes entregados (5): P082-S100 (6.4.2., p. 82, evidence), P086-S102 (6.5, p. 86, evidence), P042-S053 (2.7, p. 42, evidence), P083-S101 (6.4.3, p. 83, evidence), P081-S100 (6.4.2., p. 81, evidence).
Diagnóstico de recuperación (Fase 11, forma DICT): rango de la evidencia esperada TF-IDF=1, denso=4, salida final=1 → `OK_TOP5`.
Diagnóstico de recuperación (Fase 11, forma LLM): rango de la evidencia esperada TF-IDF=1, denso=1, salida final=1 → `OK_TOP5`.
Evidencia esperada en el paquete entregado: **sí**.

**C. Generación.** Modelo `gemini-flash-lite-latest` (Gemini); answerability `RESPALDADA`.
Respuesta (summary): «No, un competidor inscrito tanto en competición individual como en equipo mixto no puede utilizar siempre el margen del 5% de tolerancia. Según los artículos [SOR-2026-08-P081-S100] y [SOR-2026-08-P082-S100], la aplicación de la tolerancia del 5% depende de si el atleta superó o no el límite de peso de su categoría de equipo mixto durante el pesaje de la competición individual, de la fecha en que compita en el evento individual y de que cumpla la obligación de estar dentro del límite exacto de su categoría de equipo mixto (sin tolerancia del 5%) al menos una vez durante las dos competiciones [»
- Cita P082-S100 (literal): «Athletes who compete in both the individual and mixed team competitions must be within the weight limit of their mixed team category (without the +5% tolerance)»
- Cita P082-S100 (literal): «The +5% weight tolerance cannot be used by an athlete wishing to compete in a lower Mixed Team weight category than their individual competition weight category»
- Cita P082-S100 (literal): «If the athlete, in the individual competition, was NOT within the weight limits of the mixed team weight category for which they are inscribed, they MUST weigh »
- Afirmación no citada (normative_basis; EN_PASAJE_CITADO): «81-82 [SOR-2026-08-P081-S100 y SOR-2026-08-P082-S100].» — datos: ['81', '82']

**D. DIG** (versión actual `DIG-1.3+NUM-v2+FIX-v3+ALL`; orden DIG-00→DIG-12). Fallan: `DIG-02_CITAS_CON_CITA_LITERAL` (citados=['SOR-2026-08-P081-S100', 'SOR-2026-08-P082-S100'] sin_cita_literal=['SOR-2026-08-P081-S100']), `DIG-05_PERTINENCIA_MINIMA` (terminos_distintivos_consulta=['five', 'mixed', 'perce'] pasajes_citados_sin_cita_pertinente=['SOR-2026-08-P081-S100']; heuristica necesaria, no suficiente).

**E. Resultado.** Estado `ABSTAIN` → `ABSTENCION_CON_CITA_CORRECTA`. El usuario habría recibido la abstención normativa (sin dictamen) y los pasajes solo como consulta.
Juicio del auditor sobre el contenido: **C** — No; debe dar el peso sin +5 % al menos una vez: correcto. Clasificación: `GEN-CIT`.

#### B2-AMB-010 — corrida UA-B

**A. Consulta.** «¿Qué pasa si hay una lesión leve?» · idioma `es` · categoría `AMBIGUA` · comportamiento esperado: ambigua (debe pedir aclaración).
Evidencia esperada: p. 198 «A minor injury may be treated by the athlete himself.»; p. 113 «the kata performance will be stopped».

**B. RRE.** Traducción usada: `minor injury`. Pasajes entregados (5): P196-S205 (Article 20, p. 196, evidence), P113-S146 (B1.11, p. 113, evidence), P198-S210 (Article 20.3.2, p. 198, evidence), P161-S184 (Article 11, p. 161, evidence), P018-S011 (1.5, p. 18, evidence).
Pasajes candidatos de las dos interpretaciones entregados: **sí** (p. 198, combate; p. 113, kata).

**C. Generación.** Modelo `gemini-flash-lite-latest` (Gemini); answerability `RESPALDADA`.
Respuesta (summary): «En el caso de una lesión leve, el tratamiento puede realizarse fuera del área de competición o el atleta puede tratarla por sí mismo [SOR-2026-08-P198-S210]. Para una lesión leve como la luxación de un dedo de la mano o del pie, el árbitro detendrá el combate y permitirá que el atleta la recoloque inmediatamente, bajo la asistencia del médico fuera del tatami, pudiendo continuar el combate [SOR-2026-08-P198-S210]. El mismo dedo o dedo del pie se permite recolocar en dos (2) ocasiones; si ocurre una tercera vez, el árbitro, previa consulta con el Comisionado Médico de la IJF, finalizará el comb»
- Cita P198-S210 (literal): «A minor injury may be treated by the athlete himself. For example, in the case of a dislocated finger or toe, the referee shall stop the contest (by calling “Ma»
- Cita P198-S210 (literal): «The same finger or toe is allowed to be reset on two (2) occasions. If the same dislocation occurs a third time, the athlete is declared unable to continue in t»
- Cita P198-S210 (literal): «Except for the situations above, any medical treatment administered by a doctor shall result in the athlete being declared unable to continue, and the opponent »
- Cita P113-S146 (literal): «In case of a minor injury like bloody wound, broken nails or a problem with contact lenses etc., and according to the decision of the judges, the kata performan»

**D. DIG** (versión actual `DIG-1.3+NUM-v2+FIX-v3+ALL`; orden DIG-00→DIG-12). Fallan: ninguna.

**E. Resultado.** Estado `SUCCESS` → `RESPONDIDA_DEBIA_ABSTENERSE_O_ACLARAR`. El usuario habría recibido esta respuesta.
Juicio del auditor sobre el contenido: **correcto y citado literalmente, pero la pregunta era ambigua** (combate o kata) y el benchmark exige pedir aclaración. La poda retiró 1 frase sin cita; la respuesta podada superó todo el DIG. Clasificación: `DIG-FN` (ambigüedad no detectada antes de generar; la poda hizo posible la aceptación).

#### B2-DIR-005 — corrida UA-B

**A. Consulta.** «What spacing is required between the world champion stars on the judogi?» · idioma `en` · categoría `DIRECTA` · comportamiento esperado: respondible.
Evidencia esperada: p. 129 «There should be a space of 0.5 cm - 2 cm between each star.».

**B. RRE.** Traducción usada: `What spacing is required between the world champion stars on the judogi?`. Pasajes entregados (5): P129-S170 (C1.14.1, p. 129, evidence), P130-S171 (C1.14.2, p. 130, evidence), P124-S165 (C1.10, p. 124, evidence), P125-S165 (C1.10, p. 125, evidence), P114-S148 (GENERAL, p. 114, evidence).
Diagnóstico de recuperación (Fase 11, forma DICT): rango de la evidencia esperada TF-IDF=2, denso=2, salida final=1 → `OK_TOP5`.
Diagnóstico de recuperación (Fase 11, forma LLM): rango de la evidencia esperada TF-IDF=2, denso=2, salida final=1 → `OK_TOP5`.
Evidencia esperada en el paquete entregado: **sí**.

**C. Generación.** Modelo `gemini-flash-lite-latest` (Gemini); answerability `RESPALDADA`.
Respuesta (summary): «The space between two world champion stars on the judogi must be from 0.5 cm to 2 cm, specifically with a space of 0.5 cm - 2 cm between each star [SOR-2026-08-P129-S170].»
- Cita P129-S170 (literal): «There should be a space of 0.5 cm - 2 cm between each star.»
- Cita P129-S170 (literal): «More than 5 stars: superimpose them with a space of 0.5 cm.»

**D. DIG** (versión actual `DIG-1.3+NUM-v2+FIX-v3+ALL`; orden DIG-00→DIG-12). Fallan: `DIG-11_TERMINOS_DE_CONSULTA_EN_SOR` (terminos_ausentes_del_SOR=['spaci']).

**E. Resultado.** Estado `ABSTAIN` → `ABSTENCION_CON_CITA_CORRECTA`. El usuario habría recibido la abstención normativa (sin dictamen) y los pasajes solo como consulta.
Juicio del auditor sobre el contenido: **CA** — 0.5-2 cm (o 1.5-2 cm): ambas frases estan en el SOR, que es internamente inconsistente. Clasificación: `DIG-FP`, `SOR-AMBIGUO`.

#### B2-EXC-009 — corrida UA-B

**A. Consulta.** «Does an athlete who skips the medal ceremony keep the medal?» · idioma `en` · categoría `EXCEPCION` · comportamiento esperado: respondible.
Evidencia esperada: p. 98 «Any athlete who is absent from the awards ceremony without a good reason may forfeit the medal and prize money».

**B. RRE.** Traducción usada: `Does an athlete who skips the medal ceremony keep the medal?`. Pasajes entregados (5): P106-S135 (A1.15, p. 106, evidence), P113-S144 (B1.9, p. 113, evidence), P195-S202 (Article 19, p. 195, evidence), P038-S045 (2.5.4, p. 38, evidence), P098-S117 (8.10, p. 98, evidence).
Diagnóstico de recuperación (Fase 11, forma DICT): rango de la evidencia esperada TF-IDF=1, denso=None, salida final=None → `OK_TOP5`.
Diagnóstico de recuperación (Fase 11, forma LLM): rango de la evidencia esperada TF-IDF=1, denso=None, salida final=None → `OK_TOP5`.
Evidencia esperada en el paquete entregado: **sí**.

**C. Generación.** Modelo `gemini-flash-lite-latest` (Gemini); answerability `RESPALDADA`.
Respuesta (summary): «Any athlete who is absent from the awards ceremony without a good reason may forfeit the medal and prize money [SOR-2026-08-P098-S117].»
- Cita P098-S117 (literal): «Any athlete who is absent from the awards ceremony without a good reason may forfeit the medal and prize money.»

**D. DIG** (versión actual `DIG-1.3+NUM-v2+FIX-v3+ALL`; orden DIG-00→DIG-12). Fallan: `DIG-11_TERMINOS_DE_CONSULTA_EN_SOR` (terminos_ausentes_del_SOR=['skips']).

**E. Resultado.** Estado `ABSTAIN` → `ABSTENCION_CON_CITA_CORRECTA`. El usuario habría recibido la abstención normativa (sin dictamen) y los pasajes solo como consulta.
Juicio del auditor sobre el contenido: **C** — Puede perder la medalla si se ausenta sin motivo: correcto. Clasificación: `DIG-FP`.

#### B2-SCO-025 — corrida UA-B

**A. Consulta.** «What happens if an athlete suffers a minor injury during a kata performance?» · idioma `en` · categoría `AMBITO_DISTRACTOR` · comportamiento esperado: respondible.
Evidencia esperada: p. 113 «the kata performance will be stopped».

**B. RRE.** Traducción usada: `What happens if an athlete suffers a minor injury during a kata performance?`. Pasajes entregados (5): P113-S145 (B1.10, p. 113, evidence), P108-S136 (GENERAL, p. 108, evidence), P109-S138 (B1.2, p. 109, evidence), P111-S142 (B1.6, p. 111, evidence), P110-S140 (B1.4, p. 110, evidence).
Diagnóstico de recuperación (Fase 11, forma DICT): rango de la evidencia esperada TF-IDF=3, denso=1, salida final=2 → `DESPLAZADO_POR_REGLAS_FIJAS`.
Diagnóstico de recuperación (Fase 11, forma LLM): rango de la evidencia esperada TF-IDF=3, denso=1, salida final=2 → `DESPLAZADO_POR_REGLAS_FIJAS`.
Evidencia esperada en el paquete entregado: **sí**.

**C. Generación.** Modelo `gemini-flash-lite-latest` (Gemini); answerability `RESPALDADA`.
Respuesta (summary): «If an athlete suffers a minor injury like a bloody wound, broken nails, or a problem with contact lenses during a kata performance, according to the decision of the judges, the kata performance will be stopped, the athlete will be assisted by a doctor out of the competition area if needed, the competition will continue, and the pair will repeat entirely the kata after the last pair has performed [SOR-2026-08-P113-S145]. If another minor injury happens to the same athlete during the second performance of the kata or after a forgotten technique or a major mistake, the pair will be given a score »
- Cita P113-S145 (literal): «In case of a minor injury like bloody wound, broken nails or a problem with contact lenses etc., and according to the decision of the judges, the kata performan»
- Cita P113-S145 (literal): «In case another minor injury happens to the same athlete during the second performance of the kata or after a forgotten technique or a major mistake, the pair w»

**D. DIG** (versión actual `DIG-1.3+NUM-v2+FIX-v3+ALL`; orden DIG-00→DIG-12). Fallan: `DIG-11_TERMINOS_DE_CONSULTA_EN_SOR` (terminos_ausentes_del_SOR=['suffe']).

**E. Resultado.** Estado `ABSTAIN` → `ABSTENCION_CON_CITA_CORRECTA`. El usuario habría recibido la abstención normativa (sin dictamen) y los pasajes solo como consulta.
Juicio del auditor sobre el contenido: **C** — Se detiene la kata, asistencia fuera del area, se repite: correcto. Clasificación: `DIG-FP`.

#### B2-SCO-024 — corrida UA-B

**A. Consulta.** «¿En qué eventos puede sumar puntos de ranking una pareja de kata?» · idioma `es` · categoría `AMBITO_DISTRACTOR` · comportamiento esperado: respondible.
Evidencia esperada: p. 110 «A pair can earn points in the following events: Continental Open, Continental Championships, Kata World Series».

**B. RRE.** Traducción usada: `In which events can a kata pair score ranking points`. Pasajes entregados (5): P110-S141 (B1.5, p. 110, evidence), P109-S138 (B1.2, p. 109, evidence), P108-S136 (GENERAL, p. 108, evidence), P113-S145 (B1.10, p. 113, evidence), P111-S142 (B1.6, p. 111, evidence).
Diagnóstico de recuperación (Fase 11, forma DICT): rango de la evidencia esperada TF-IDF=11, denso=1, salida final=2 → `OK_TOP5`.
Diagnóstico de recuperación (Fase 11, forma LLM): rango de la evidencia esperada TF-IDF=11, denso=1, salida final=6 → `OK_TOP5`.
Evidencia esperada en el paquete entregado: **sí**.

**C. Generación.** Modelo `gemini-flash-lite-latest` (Gemini); answerability `RESPALDADA`.
Respuesta (summary): «Una pareja de kata puede sumar puntos de ranking en los eventos Continental Open, Continental Championships, Kata World Series (KWS) y World Kata Championships [SOR-2026-08-P110-S141].»
- Cita P110-S141 (literal): «A pair can earn points in the following events: Continental Open, Continental Championships, Kata World Series (KWS) and World Kata Championships.»

**D. DIG** (versión actual `DIG-1.3+NUM-v2+FIX-v3+ALL`; orden DIG-00→DIG-12). Fallan: `DIG-09_EXCEPCIONES_CITADAS` (unidades_no_disponibles=[] excepciones_no_citadas=["AU1-P110-002: 'The \\nranking point system takes into consideration the five (5) best r'"]).

**E. Resultado.** Estado `ABSTAIN` → `ABSTENCION_CON_CITA_CORRECTA`. El usuario habría recibido la abstención normativa (sin dictamen) y los pasajes solo como consulta.
Juicio del auditor sobre el contenido: **C** — Cuatro eventos de kata: correcto. Clasificación: `DIG-FP`.

#### B2-CAT-001 — corrida UA-A

**A. Consulta.** «¿Qué longitud mínima debe tener la falda de la chaqueta para un atleta de -66 kg?» · idioma `es` · categoría `DISTINCION_CATEGORIA` · comportamiento esperado: respondible.
Evidencia esperada: p. 124 «All athletes -73 kg*: a minimum of 20 cm».

**B. RRE.** Traducción usada: `Minimum length of the jacket skirt for an athlete of -66 kg`. Pasajes entregados (5): P124-S164 (C1.9, p. 124, evidence), P075-S086 (6.1, p. 75, evidence), P084-S102 (6.5, p. 84, evidence), P076-S088 (6.2.1, p. 76, evidence), P034-S036 (2.2.2, p. 34, evidence).
Diagnóstico de recuperación (Fase 11, forma DICT): rango de la evidencia esperada TF-IDF=None, denso=5, salida final=None → `EN_CANAL_FUERA_DE_TOP5`.
Diagnóstico de recuperación (Fase 11, forma LLM): rango de la evidencia esperada TF-IDF=2, denso=2, salida final=2 → `DESPLAZADO_POR_REGLAS_FIJAS`.
Evidencia esperada en el paquete entregado: **sí**.

**C. Generación.** Modelo `gemini-flash-lite-latest` (Gemini); answerability `RESPALDADA`.
Respuesta (summary): «Para un atleta de -66 kg (que pertenece a la categoría de -73 kg), la longitud mínima de la falda de la chaqueta, medida por debajo del cinturón con el sokuteiki, debe ser de un mínimo de 20 cm ([SOR-2026-08-P124-S164]).»
- Cita P124-S164 (literal): «All athletes -73 kg*: a minimum of 20 cm»

**D. DIG** (versión actual `DIG-1.3+NUM-v2+FIX-v3`; orden DIG-00→DIG-12). Fallan: `DIG-06_CIFRAS_RESPALDADAS` (cifras_sin_respaldo=['66']).

**E. Resultado.** Estado `ABSTAIN` → `ABSTENCION_CON_CITA_CORRECTA`. El usuario habría recibido la abstención normativa (sin dictamen) y los pasajes solo como consulta.
Juicio del auditor sobre el contenido: **C** — 20 cm para -66 kg (grupo -73 kg): correcto. Clasificación: `DIG-FP`.

#### B2-SCO-023 — corrida UA-A

**A. Consulta.** «Which events give points for the IJF Juniors World Ranking List?» · idioma `en` · categoría `AMBITO_DISTRACTOR` · comportamiento esperado: respondible.
Evidencia esperada: p. 53 «Athletes can earn points for the IJF Juniors WRL by competing in Continental Cups Juniors».

**B. RRE.** Traducción usada: `Which events give points for the IJF Juniors World Ranking List?`. Pasajes entregados (5): P053-S067 (3.2.2, p. 53, evidence), P056-S071 (3.3.2, p. 56, evidence), P050-S063 (GENERAL, p. 50, evidence), P052-S065 (3.2, p. 52, evidence), P057-S073 (3.4, p. 57, evidence).
Diagnóstico de recuperación (Fase 11, forma DICT): rango de la evidencia esperada TF-IDF=1, denso=1, salida final=1 → `OK_TOP5`.
Diagnóstico de recuperación (Fase 11, forma LLM): rango de la evidencia esperada TF-IDF=1, denso=1, salida final=1 → `OK_TOP5`.
Evidencia esperada en el paquete entregado: **sí**.

**C. Generación.** Modelo `gemini-flash-lite-latest` (Gemini); answerability `RESPALDADA`.
Respuesta (summary): «Athletes can earn points for the IJF Juniors World Ranking List by competing in Continental Cups Juniors, Continental Championships Juniors, Grand Prix Juniors and World Championships Juniors [SOR-2026-08-P053-S067].»
- Cita P053-S067 (literal): «Athletes can earn points for the IJF Juniors WRL by competing in Continental Cups Juniors, Continental Championships Juniors, Grand Prix Juniors and World Champ»
- Afirmación no citada (conditions_and_exceptions; EN_PASAJE_CITADO): «Other ranking points will be given when there is at least one (1) contest won.» — datos: ['1']
- Afirmación no citada (conditions_and_exceptions; EN_PASAJE_CITADO): «At Grand Prix Juniors events only the two (2) best domestic athletes per weight category can obtain points for the IJF Juniors WRL.» — datos: ['2']
- Afirmación no citada (conditions_and_exceptions; EN_PASAJE_CITADO): «At World Championships Juniors only the nine (9) best domestic male and nine (9) best domestic female athletes from the host country will be considered for the IJF Juniors WRL.» — datos: ['9']

**D. DIG** (versión actual `DIG-1.3+NUM-v2+FIX-v3`; orden DIG-00→DIG-12). Fallan: `DIG-06_CIFRAS_RESPALDADAS` (cifras_sin_respaldo=['1', '2', '9']).

**E. Resultado.** Estado `ABSTAIN` → `ABSTENCION_CON_CITA_CORRECTA`. El usuario habría recibido la abstención normativa (sin dictamen) y los pasajes solo como consulta.
Juicio del auditor sobre el contenido: **C** — Cuatro tipos de eventos juniors: correcto. Clasificación: `DIG-CR`.

#### B2-SCO-019 — corrida UA-B

**A. Consulta.** «¿Qué tolerancia de peso tienen los cadetes en el pesaje oficial?» · idioma `es` · categoría `AMBITO_DISTRACTOR` · comportamiento esperado: respondible.
Evidencia esperada: p. 75 «to compensate an additional 0.2 kg will be allowed».

**B. RRE.** Traducción usada: `cadets weight tolerance official weigh-in`. Pasajes entregados (6): P188-S196 (Article 18.1.4, p. 188, evidence), P086-S102 (6.5, p. 86, evidence), P077-S090 (6.2.3, p. 77, evidence), P082-S100 (6.4.2., p. 82, evidence), P083-S101 (6.4.3, p. 83, evidence), P175-S191 (Article 18, p. 175, related).
Diagnóstico de recuperación (Fase 11, forma DICT): rango de la evidencia esperada TF-IDF=None, denso=10, salida final=None → `EN_CANAL_FUERA_DE_TOP5`.
Diagnóstico de recuperación (Fase 11, forma LLM): rango de la evidencia esperada TF-IDF=None, denso=1, salida final=None → `EN_CANAL_FUERA_DE_TOP5`.
Evidencia esperada en el paquete entregado: **no**.

**C. Generación.** Modelo `gemini-flash-lite-latest` (Gemini); answerability `RESPALDADA`.
Respuesta (summary): «Los atletas que toman parte en competiciones de cadetes por equipos tienen una tolerancia de peso de 0,2 kg [SOR-2026-08-P086-S102], la cual se permite para la ropa interior [SOR-2026-08-P086-S102, SOR-2026-08-P082-S100]. Asimismo, en los eventos de equipos que siguen a una competición individual, existe una tolerancia de peso del +5% aplicable únicamente a las categorías de peso menos [SOR-2026-08-P086-S102, SOR-2026-08-P082-S100].»
- Cita P086-S102 (NO literal): «Athletes who take part in cadets teams are given a 0.2 kg weight tolerance in accordance with Section 6.1»
- Cita P086-S102 (NO literal): «Cadet Women Team +0 .2 kg allowed for underwear»
- Cita P086-S102 (NO literal): «A +5% tolerance applies only to the minus weight categories. No tolerance applies to the plus weight categories because they do not have an upper weight limit»
- Cita P082-S100 (NO literal): «Cadet Mixed Team +0 .2 kg allowed for underwear»
- Cita P082-S100 (NO literal): «A +5% tolerance applies only to the minus weight categories. No tolerance applies to the plus weight categories because they do not have an upper weight limit»
- Afirmación no citada (normative_basis; SIN_FUENTE_ENTREGADA): «Reglas del Sport and Organisation Rules de la IJF, secciones 6.5 y 6.4.2 [SOR-2026-08-P086-S102, SOR-2026-08-P082-S100].» — datos: ['6.5']

**D. DIG** (versión actual `DIG-1.3+NUM-v2+FIX-v3+ALL`; orden DIG-00→DIG-12). Fallan: `DIG-06_CIFRAS_RESPALDADAS` (cifras_sin_respaldo=['6.5']), `DIG-09_EXCEPCIONES_CITADAS` (unidades_no_disponibles=[] excepciones_no_citadas=["AU1-P084-001: 'Although the individual and team events are separate competitions, the'"]), `DIG-10_REFERENCIAS_ENTREGADAS` (referencias_citadas_no_entregadas=['AU1-P084-001: Section 6.1']).

**E. Resultado.** Estado `ABSTAIN` → `ABSTENCION_EVIDENCIA_NO_RECUPERADA`. El usuario habría recibido la abstención normativa (sin dictamen) y los pasajes solo como consulta.
Juicio del auditor sobre el contenido: **I** — Responde con la tolerancia de cadetes POR EQUIPOS (p. 86) en vez de la individual (p. 75, 0.2 kg): otro ambito. Clasificación: `RRE-FUS`, `GEN-INT`.

#### B2-MLG-002 — corrida UA-B

**A. Consulta.** «Quantos atletas compõem uma equipa mista?» · idioma `pt` · categoría `MULTILINGUE` · comportamiento esperado: respondible.
Evidencia esperada: p. 42 «Each mixed team must consist of six (6) athletes (3 women and 3 men)».

**B. RRE.** Traducción usada: `sin traducción`. Pasajes entregados (6): P251-S267 (G1.2.1, p. 251, evidence), P192-S198 (Article 18.2.2, p. 192, evidence), P162-S185 (Article 12, p. 162, evidence), P252-S268 (G1.2.2, p. 252, evidence), P141-S177 (Article 4, p. 141, evidence), P137-S177 (Article 4, p. 137, related).
Diagnóstico de recuperación (Fase 11, forma DICT): rango de la evidencia esperada TF-IDF=None, denso=None, salida final=None → `AUSENTE_DE_CANALES`.
Diagnóstico de recuperación (Fase 11, forma LLM): rango de la evidencia esperada TF-IDF=None, denso=None, salida final=None → `AUSENTE_DE_CANALES`.
Evidencia esperada en el paquete entregado: **no**.

**C. Generación.** Modelo `gemini-flash-lite-latest` (Gemini); answerability `EVIDENCIA_INSUFICIENTE`.
Respuesta (summary): «Los pasajes certificados del SOR 2026 proporcionados no contienen información sobre el número de atletas que componen un equipo mixto.»

**D. DIG.** No se ejecutó: la respuesta no citó ningún pasaje SOR entregado (validador de citas previo al DIG).

**E. Resultado.** Estado `ABSTAIN` → `ABSTENCION_EVIDENCIA_NO_RECUPERADA`. El usuario habría recibido la abstención normativa (sin dictamen) y los pasajes solo como consulta.
Juicio del auditor sobre el contenido: **ABS** — Pregunta en portugues sin traducir; el modelo declara que no hay evidencia. Clasificación: `RRE-INC`, `PIPE-ERR`.

#### B2-SCO-020 — corrida UA-A

**A. Consulta.** «Do senior athletes get any weight tolerance at the official weigh-in of an individual event?» · idioma `en` · categoría `AMBITO_DISTRACTOR` · comportamiento esperado: respondible.
Evidencia esperada: p. 75 «there is no additional weight tolerance».

**B. RRE.** Traducción usada: `Do senior athletes get any weight tolerance at the official weigh-in of an individual event?`. Pasajes entregados (5): P086-S102 (6.5, p. 86, evidence), P082-S100 (6.4.2., p. 82, evidence), P079-S094 (6.3.1, p. 79, evidence), P077-S090 (6.2.3, p. 77, evidence), P083-S101 (6.4.3, p. 83, evidence).
Diagnóstico de recuperación (Fase 11, forma DICT): rango de la evidencia esperada TF-IDF=None, denso=2, salida final=None → `EN_CANAL_FUERA_DE_TOP5`.
Diagnóstico de recuperación (Fase 11, forma LLM): rango de la evidencia esperada TF-IDF=None, denso=2, salida final=None → `EN_CANAL_FUERA_DE_TOP5`.
Evidencia esperada en el paquete entregado: **no**.

**C. Generación.** Modelo `gemini-flash-lite-latest` (Gemini); answerability `RESPALDADA`.
Respuesta (summary): «No. Senior athletes do not receive any weight tolerance at the official weigh-in of an individual event; they must be within the exact weight limits of their respective weight category ([SOR-2026-08-P077-S090]).»
- Cita P077-S090 (literal): «Passing the official weigh-in is the responsibility of the athlete. Only the weight recorded on the official scale for the athlete’s weight category will be con»
- Afirmación no citada (conditions_and_exceptions; EN_OTRO_PASAJE_ENTREGADO): «Tolerances such as the +5% apply specifically to team or mixed team competitions following an individual competition under certain conditions, and +0.2 kg for underwear applies specifically to cadet t» — datos: ['.2', '5']

**D. DIG** (versión actual `DIG-1.3+NUM-v2+FIX-v3`; orden DIG-00→DIG-12). Fallan: `DIG-05_PERTINENCIA_MINIMA` (terminos_distintivos_consulta=['toler'] pasajes_citados_sin_cita_pertinente=['SOR-2026-08-P077-S090']; heuristica necesaria, no suficiente), `DIG-06_CIFRAS_RESPALDADAS` (cifras_sin_respaldo=['.2', '5']).

**E. Resultado.** Estado `ABSTAIN` → `ABSTENCION_EVIDENCIA_NO_RECUPERADA`. El usuario habría recibido la abstención normativa (sin dictamen) y los pasajes solo como consulta.
Juicio del auditor sobre el contenido: **NS** — Concluye "sin tolerancia" (correcto) citando p. 77, que no lo dice; la p. 75 no se recupero. Clasificación: `RRE-FUS`, `GEN-CIT`.

#### B2-EXC-003 — corrida UA-B

**A. Consulta.** «Can the IJF enter an athlete who is not entered by a national federation?» · idioma `en` · categoría `EXCEPCION` · comportamiento esperado: respondible.
Evidencia esperada: p. 61 «Only entries from member national judo federations will be accepted.».

**B. RRE.** Traducción usada: `Can the IJF enter an athlete who is not entered by a national federation?`. Pasajes entregados (5): P021-S017 (1.7.2, p. 21, evidence), P025-S022 (1.7.2.5, p. 25, evidence), P023-S020 (1.7.2.3, p. 23, evidence), P020-S015 (1.7.1.1, p. 20, evidence), P024-S021 (1.7.2.4, p. 24, evidence).
Diagnóstico de recuperación (Fase 11, forma DICT): rango de la evidencia esperada TF-IDF=19, denso=None, salida final=None → `EN_CANAL_FUERA_DE_TOP5`.
Diagnóstico de recuperación (Fase 11, forma LLM): rango de la evidencia esperada TF-IDF=19, denso=None, salida final=None → `EN_CANAL_FUERA_DE_TOP5`.
Evidencia esperada en el paquete entregado: **no**.

**C. Generación.** Modelo `gemini-flash-lite-latest` (Gemini); answerability `RESPALDADA`.
Respuesta (summary): «For events organised by the IJF or under its auspices, the IJF Executive Committee, to protect the interest of the athlete, can authorise that the athlete can compete under the IJF or a neutral flag for any reason [SOR-2026-08-P021-S017].»
- Cita P021-S017 (literal): «For events organised by the IJF or under its auspices, the IJF Executive Committee, to protect the interest of the athlete, can authorise that the athlete can c»

**D. DIG** (versión actual `DIG-1.3+NUM-v2+FIX-v3+ALL`; orden DIG-00→DIG-12). Fallan: `DIG-05_PERTINENCIA_MINIMA` (terminos_distintivos_consulta=['enter'] pasajes_citados_sin_cita_pertinente=['SOR-2026-08-P021-S017']; heuristica necesaria, no suficiente).

**E. Resultado.** Estado `ABSTAIN` → `ABSTENCION_EVIDENCIA_NO_RECUPERADA`. El usuario habría recibido la abstención normativa (sin dictamen) y los pasajes solo como consulta.
Juicio del auditor sobre el contenido: **I** — Responde con la regla de bandera neutral (p. 21), no con la de inscripciones (p. 61): fundamento equivocado. Clasificación: `RRE-FUS`, `GEN-INT`.

## 5. Matriz consolidada

Una fila por pregunta respondible con al menos un rechazo (26 preguntas, 83 respuestas) y una fila por cada respuesta incorrecta aceptada (5).

* **«rech./acept.»:** respuestas rechazadas y aceptadas de esa pregunta en las 8 corridas.
* **«DIG»:** reglas que fallan con el DIG actual.
* **Causa principal:** según la prioridad del §2.

| Caso | RRE | Gemini | DIG (reglas que fallan hoy) | ¿Respuesta correcta? | Causa principal | Acción recomendada |
|---|---|---|---|---|---|---|
| CAT-001 — 4 rech. / 2 acept. | evidencia entregada 4/4 | fiel (4) | DIG-06×4, DIG-03×1, DIG-05×1 | Sí (4) | DIG-FP (3), GEN-CIT (1) | Corregir la regla causante (ver §9) |
| CAT-003 — 1 rech. / 5 acept. | evidencia entregada 1/1 | fiel (1) | DIG-06×1 | Sí (1) | DIG-CR (1) | Contrato centrado + poda de accesorios (implementado, sin activar) |
| CAT-007 — 1 rech. / 4 acept. | evidencia entregada 1/1 | errónea (1) | DIG-08×1, DIG-12×1, DIG-02×1 | No (1) | GEN-INT (1) | Ninguna en el DIG (bloqueo correcto) |
| DIR-005 — 8 rech. / 0 acept. | evidencia entregada 8/8 | fiel (8) | DIG-11×8, DIG-01×1, DIG-06×1 | Sí según el texto; SOR ambiguo (8) | DIG-FP (8) | Corregir la regla causante (ver §9) |
| DIR-011 — 3 rech. / 2 acept. | evidencia entregada 3/3 | fiel (3) | DIG-06×2 | Sí (3) | DIG-CR (2), DIG-FP(corregido_en_v2/v3) (1) | Contrato centrado + poda de accesorios (implementado, sin activar) |
| DIR-017 — 1 rech. / 5 acept. | evidencia entregada 1/1 | fiel (1) | ninguna: el DIG actual la acepta | Sí (1) | DIG-FP(corregido_en_v2/v3) (1) | Ninguna: ya corregido en el DIG actual |
| DIR-018 — 3 rech. / 1 acept. | evidencia entregada 3/3 | fiel (3) | DIG-07×3, DIG-06×1, DIG-05×1 | Sí (3) | DIG-CR (2), GEN-CIT (1) | Contrato centrado + poda de accesorios (implementado, sin activar) |
| EXC-003 — 6 rech. / 0 acept. | evidencia entregada 0/6 (EN_CANAL_FUERA_DE_TOP5) | errónea (6) | DIG-05×6, DIG-08×2 | No (6) | RRE-FUS (6) | Revisar la fusión TF-IDF/denso y los refuerzos (R1) |
| EXC-006 — 1 rech. / 3 acept. | evidencia entregada 1/1 | fiel (1) | DIG-02×1, DIG-05×1 | Sí (1) | GEN-CIT (1) | Ninguna en el DIG; medir la variabilidad |
| EXC-009 — 5 rech. / 0 acept. | evidencia entregada 5/5 | fiel (5) | DIG-11×5 | Sí (5) | DIG-FP (5) | Corregir la regla causante (ver §9) |
| MLG-002 — 4 rech. / 0 acept. | evidencia entregada 0/4 (AUSENTE_DE_CANALES) | declara insuficiencia (4) | no ejecutado | El modelo declaró falta de evidencia (4) | RRE-INC (4) | Traducir también otros idiomas (R2) |
| MLG-003 — 3 rech. / 4 acept. | evidencia entregada 3/3 | fiel (3) | ninguna: el DIG actual la acepta | Sí (3) | DIG-FP(corregido_en_v2/v3) (3) | Ninguna: ya corregido en el DIG actual |
| MUL-004 — 3 rech. / 1 acept. | evidencia entregada 2/3 (OK_TOP5) | JSON inválido (1); fiel (2) | DIG-06×2, DIG-08×1 | No evaluable (1); Sí (2) | DIG-CR (2), RRE-INC (1) | Contrato centrado + poda de accesorios (implementado, sin activar) |
| REF-005 — 2 rech. / 3 acept. | evidencia entregada 2/2 | fiel (2) | ninguna: el DIG actual la acepta | Sí (2) | DIG-FP(corregido_en_v2/v3) (2) | Ninguna: ya corregido en el DIG actual |
| SCO-009 — 1 rech. / 3 acept. | evidencia entregada 1/1 | fiel (1) | ninguna: el DIG actual la acepta | Sí (1) | DIG-FP(corregido_en_v2/v3) (1) | Ninguna: ya corregido en el DIG actual |
| SCO-010 — 2 rech. / 4 acept. | evidencia entregada 2/2 | fiel (2) | ninguna: el DIG actual la acepta | Sí (2) | DIG-FP(corregido_en_v2/v3) (2) | Ninguna: ya corregido en el DIG actual |
| SCO-013 — 5 rech. / 0 acept. | evidencia entregada 0/5 (EN_CANAL_FUERA_DE_TOP5) | declara insuficiencia (4); errónea (1) | DIG-05×1 | El modelo declaró falta de evidencia (4); No (1) | RRE-FUS (5) | Revisar la fusión TF-IDF/denso y los refuerzos (R1) |
| SCO-014 — 3 rech. / 0 acept. | evidencia entregada 0/3 (EN_CANAL_FUERA_DE_TOP5) | declara insuficiencia (3) | no ejecutado | El modelo declaró falta de evidencia (3) | RRE-FUS (3) | Revisar la fusión TF-IDF/denso y los refuerzos (R1) |
| SCO-019 — 4 rech. / 0 acept. | evidencia entregada 0/4 (EN_CANAL_FUERA_DE_TOP5) | errónea (4) | DIG-09×4, DIG-10×4, DIG-06×3, DIG-05×3, DIG-02×1 | No (4) | RRE-FUS (4) | Revisar la fusión TF-IDF/denso y los refuerzos (R1) |
| SCO-020 — 4 rech. / 0 acept. | evidencia entregada 0/4 (EN_CANAL_FUERA_DE_TOP5) | cita no respalda (3); declara insuficiencia (1) | DIG-05×3, DIG-06×1 | Conclusión sin respaldo citado (3); El modelo declaró falta de evidencia (1) | RRE-FUS (4) | Revisar la fusión TF-IDF/denso y los refuerzos (R1) |
| SCO-021 — 2 rech. / 2 acept. | evidencia entregada 2/2 | fiel (2) | DIG-06×2 | Sí (2) | DIG-CR (2) | Contrato centrado + poda de accesorios (implementado, sin activar) |
| SCO-022 — 1 rech. / 4 acept. | evidencia entregada 1/1 | fiel (1) | DIG-06×1 | Sí (1) | DIG-CR (1) | Contrato centrado + poda de accesorios (implementado, sin activar) |
| SCO-023 — 6 rech. / 1 acept. | evidencia entregada 6/6 | fiel (6) | DIG-06×5, DIG-03×1 | Sí (6) | DIG-CR (5), GEN-CIT (1) | Contrato centrado + poda de accesorios (implementado, sin activar) |
| SCO-024 — 4 rech. / 0 acept. | evidencia entregada 4/4 | fiel (4) | DIG-09×4, DIG-06×1 | Sí (4) | DIG-FP (4) | Corregir la regla causante (ver §9) |
| SCO-025 — 4 rech. / 0 acept. | evidencia entregada 4/4 | fiel (4) | DIG-11×4, DIG-03×1, DIG-06×1 | Sí (4) | DIG-FP (3), GEN-CIT (1) | Corregir la regla causante (ver §9) |
| SCO-026 — 2 rech. / 2 acept. | evidencia entregada 2/2 | fiel (2) | DIG-07×2, DIG-06×1 | Sí (2) | DIG-CR (2) | Contrato centrado + poda de accesorios (implementado, sin activar) |
| AMB-005 — AB-B (aceptada) | pasajes entregados | respondió una pregunta ambigua | ninguna | No: debía pedir aclaración | DIG-FN | Detectar la ambigüedad antes de generar (R6) |
| AMB-005 — F11#1 (aceptada) | pasajes entregados | respondió una pregunta ambigua | ninguna | No: debía pedir aclaración | DIG-FN | Detectar la ambigüedad antes de generar (R6) |
| AMB-005 — UA-A (aceptada) | pasajes entregados | respondió una pregunta ambigua | ninguna | No: debía pedir aclaración | DIG-FN | Detectar la ambigüedad antes de generar (R6) |
| AMB-005 — UA-B (aceptada) | pasajes entregados | respondió una pregunta ambigua | ninguna | No: debía pedir aclaración | DIG-FN | Detectar la ambigüedad antes de generar (R6) |
| AMB-010 — UA-B (aceptada) | pasajes entregados | respondió una pregunta ambigua | ninguna | No: debía pedir aclaración | DIG-FN | Detectar la ambigüedad antes de generar (R6) |

### Estadísticas (denominadores explícitos)

| Indicador | Valor |
|---|---|
| Ejecuciones analizadas | 328 (41 preguntas × 8 corridas) |
| Con respuesta generada | 198/328 (60,4 %) |
| Sin generación (cuota del proveedor o abstención previa al LLM) | 130/328 (39,6 %); fuera del análisis del DIG |
| **Respuestas correctas aceptadas** | 66/149 respondibles generadas (44,3 %) |
| **Respuestas correctas rechazadas** | 55/149 (36,9 %) |
| **Respuestas incorrectas aceptadas** | 5/71 aceptadas (7,0 %); las 5 a preguntas ambiguas (5/49 no respondibles generadas = 10,2 %) |
| **Respuestas incorrectas o sin respaldo rechazadas** | 15/149 respondibles generadas (10,1 %), más 42 abstenciones correctas en no respondibles (42/49) |
| Rechazos atribuibles a la recuperación | 27/83 rechazos de respondibles (32,5 %): RRE-FUS 22, RRE-INC 5 |
| Rechazos atribuibles a la generación | 6/83 (7,2 %): GEN-CIT 5, GEN-INT 1 |
| Rechazos atribuibles al DIG (falsos positivos) | 50/83 (60,2 %): DIG-FP vigentes 23, DIG-CR 17, DIG-FP ya corregidos en el DIG actual 10 |
| Falsos positivos del DIG aún vigentes | 40/55 correctas rechazadas (72,7 %) |
| Falsos negativos del DIG | 5/71 aceptadas (7,0 %) |
| Casos sin evidencia suficiente para clasificar | 1/149 (MUL-004 AB-A: JSON inválido), más las 130 ejecuciones sin generación |
| Respondibles nunca aceptadas en las 8 corridas | 10/31 preguntas: 6 por recuperación, 4 por el DIG |

## 6. Falsos positivos y falsos negativos

### 6.1 Falsos positivos: 55 respuestas correctas rechazadas

| Regla (DIG actual) | Correctas rechazadas en las que falla | Naturaleza del fallo | Casos |
|---|---|---|---|
| **DIG-11** | 17 | Una palabra de la pregunta no figura en el SOR. La regla no mira la respuesta. | DIR-005 «spacing» ×8, EXC-009 «skips» ×5, SCO-025 «suffers» ×4 |
| **DIG-06** | 22 | Cifras sin cita. Unas están en el pasaje citado (accesorias); otras repiten la **cifra de la propia consulta** («-66 kg», CAT-001 ×4) o son **números de artículo o página** («6.5», «81-82») | SCO-023, SCO-021, DIR-011, MUL-004, CAT-001, SCO-022, CAT-003… |
| **DIG-07** | 5 | Términos del SOR («kiken-gachi», «tatami») usados sin cita, presentes en el pasaje citado | DIR-018, SCO-026 |
| **DIG-09** | 4 | Excepción vecina no relacionada («five best results» frente a la pregunta sobre qué eventos dan puntos) | SCO-024 ×4 |
| DIG-02, DIG-03 y DIG-05 | 7 | Cita no literal o pasaje citado sin fragmento: **error de cita de la generación (GEN-CIT), rechazo legítimo** | EXC-006 UA-B, CAT-001 UA-B, SCO-025 AB-A, SCO-023 F11#2, DIR-018 AB-B |
| Ya corregidas en el DIG actual | 10 | Guion U+2011 en «weigh‑in», números de artículo o de la edición («8.1», «6.3», «2026»), palabras españolas en SHADOW, título del apartado | MLG-003 ×3, SCO-010 ×2, REF-005 ×2, SCO-009, DIR-017, DIR-011 |

**Procedencia de los datos no citados** en las 55 respuestas correctas rechazadas (290 afirmaciones):
* 249 literales o sin datos verificables;
* **38 con datos presentes en el pasaje citado**;
* 2 en otro pasaje entregado;
* 1 sin fuente entregada.

Contando todas las rechazadas a respondibles (386 afirmaciones), las cifras son 333, 46, 4 y 3. En las aceptadas, las 232 afirmaciones son literales o no tienen datos verificables.

**Tipos de cifra rechazadas por DIG-06** en todas las corridas (80 cifras):
* 49 cifras normativas presentes en los pasajes entregados (45 en el citado, 4 en otro);
* 10 fechas o edición del SOR;
* 9 números de artículo o sección;
* 8 cifras de pasajes no entregados (numeración de listas en AMB-006 y una cifra de SHADOW en EXC-003);
* 4 cifras repetidas de la consulta.
Esta clasificación es automática y aproximada.

### 6.2 Falsos negativos: 5 respuestas incorrectas aceptadas

Las 5 corresponden a **preguntas ambiguas**: AMB-005 ×4 («¿Cuántos reservas se permiten?») y AMB-010 UA-B («¿Qué pasa si hay una lesión leve?»).
* **AB-B y F11#1 (AMB-005):** respuesta citada pero parcial; no pidió aclaración.
* **UA-A y UA-B (AMB-005):** además afirman que **«en las demás categorías no se especifica un cupo de reservas»**. Es falso: el SOR fija 6 reservas en equipos mixtos y 5 en equipos femeninos o masculinos, pero esos pasajes no se recuperaron. Es una generalización a partir de evidencia incompleta (RRE-INC + GEN-INT) que **ninguna regla del DIG detecta**: el DIG verifica lo que se cita, no lo que falta.
* **AMB-010 UA-B:** contenido correcto; la poda de accesorios hizo posible la aceptación.

En las 66 aceptadas a preguntas respondibles **no se halló contenido incorrecto**. El evaluador marcó 2 como «sin evidencia esperada» (EXC-006 AB-A y SCO-026 AB-B). La revisión manual las da por correctas: en SCO-026 fue un fallo del evaluador de entonces, que ya no se reproduce; EXC-006 cita otra frase de la misma regla.

### 6.3 Contraste: retirada simulada de cada regla (DIG actual, 181 entradas, 100 rechazadas)

| Regla | Única causa del rechazo en | Correctas que se recuperarían | Incorrectas que se aceptarían |
|---|---|---|---|
| DIG-11 | 14 | **14** | **0** |
| DIG-06 | 15 | 15 (con datos del pasaje citado sin citar) | 0 en contenido¹ |
| DIG-07 | 5 | 3 | 2 (AMB-010 ×2, ambigua) |
| DIG-09 | 7 | 3 | **4** (AMB-005, INC-005 ×2, OOD-006) |
| DIG-05 | 7 | 0 | **7** (EXC-003 ×4, SCO-020 ×2, SCO-013) |
| DIG-01 | 1 | 0 | 1 (INS-006) |
| DIG-00 | 1 | 0 | 1 (MUL-004, sin contenido) |
| DIG-02, 03, 08, 10 y 12 | 0–1 | — | — |

¹ El evaluador las clasificaría como «cifra sin respaldo» porque los datos no están en la cita. Su contenido es correcto, pero **retirar DIG-06 dejaría pasar también cifras inventadas**. No se recomienda.

**Lectura:**
* **DIG-05** es el control que más protege frente a evidencia equivocada.
* **DIG-09** protege por accidente frente a fallos de ambigüedad y de dominio.
* **DIG-11** solo produjo falsos positivos en estos datos.

## 7. Diagnóstico de cada componente

**Recuperación (RRE).**
* **Evidencia incompleta o desplazada:** 27 rechazos y 6 preguntas sin respuesta. Cuando la evidencia esperada no llega, el DIG rechaza correctamente.
* **Fusión o selección (RRE-FUS):**
  * SCO-019 y SCO-020: el canal denso sitúa la página correcta en **1.º–2.º**, pero desaparece de la salida final.
  * SCO-013, SCO-014 y EXC-003: TF-IDF la sitúa en los puestos 14.º–19.º.
* **Recuperación incompleta (RRE-INC):** MLG-002, en portugués, llega sin traducir y la evidencia no aparece en ningún canal.
* **Variabilidad:** MUL-004 y SCO-022 reciben a veces una página contigua con texto idéntico.

**Construcción del contexto.** **No se demostró ningún problema.**
* Cuando el pasaje esperado estaba en el paquete, su fragmento aparecía íntegro en el texto entregado en **120 de 120** casos; los pasajes primarios no se truncan.
* El contexto es largo (5–8 pasajes): no se pudo demostrar que eso cause errores.

**Generación (Gemini y Groq).**
* **Fidelidad:** el modelo es fiel al texto. las 55 correctas rechazadas (47 C y 8 CA) son paráfrasis o copias exactas del SOR.
* **Defecto dominante:** **usa más de lo que cita**, sobre todo en `conditions_and_exceptions`. El contrato anterior le pedía requisitos conexos.
* **Errores de fondo:**
  * 1 interpretación falsa: CAT-007 UA-B dice que «no hay límite».
  * 14 respuestas de otro ámbito o sin respaldo, cuando faltaba la evidencia correcta: SCO-019 respondió con la tolerancia por equipos; EXC-003 con la regla de la bandera neutral; SCO-020 concluyó bien pero citó un pasaje que no lo dice.
  * 2 generalizaciones falsas por ausencia de evidencia (AMB-005 en UA).

**Trazabilidad de citas.** 5 rechazos por citas no literales o por pasajes citados sin fragmento:
* paráfrasis dentro de la cita («If another» en lugar de «In case another»);
* cita recortada;
* un pasaje mencionado sin cita.
Los guiones tipográficos ya están corregidos.

**Validación DIG.** Las reglas que ven la respuesta y la evidencia funcionan: DIG-05 y DIG-01, y DIG-06/07 cuando el dato no está en ninguna fuente. Fallan las que:
* **evalúan otra cosa:** DIG-11 (la pregunta) y DIG-09 (la cercanía en el texto);
* **cuentan como cifras afirmadas** números que vienen de la consulta o de la referencia del artículo o la página (DIG-06);
* **no distinguen** entre dato accesorio y núcleo de la respuesta (DIG-06/07, toda la respuesta se rechaza).

**Integración (PIPE-ERR).**
* **Idioma de la traducción:** solo se traduce el español (MLG-002).
* **Idioma de DIG-11:** solo se aplica en inglés (asimetría).
* **Evaluador:** el anterior no reconocía algunas citas (ya unificado).
* **Formato:** 1 respuesta no JSON.

**Presentación.** No altera el contenido verificado. La respuesta única está implementada, sin activar.

## 8. Problemas sistémicos identificados

1. **El DIG mide la forma de la cita, no el respaldo.** Una afirmación fiel al pasaje citado, pero no copiada en `evidence_quotes`, se trata igual que una inventada (38 afirmaciones en respuestas correctas; 46 en todas las rechazadas).
2. **Reglas que evalúan algo distinto de la respuesta:**
   * DIG-11 mira la formulación de la pregunta.
   * DIG-09 mira la cercanía en el texto.
   * DIG-06 cuenta cifras de la consulta y de las referencias.
3. **Rechazo de todo o nada:** un dato accesorio sin cita anula una respuesta principal correcta.
4. **Pérdidas en la fusión de la recuperación** que el DIG no puede compensar.
5. **Ausencia de un control de completitud o ambigüedad:** una respuesta que dice «no se especifica» por falta de evidencia pasa el DIG (AMB-005).
6. **Variabilidad del modelo** entre corridas. Con una corrida por variante no se puede separar del efecto de los cambios.

## 9. Recomendaciones priorizadas

Ninguna está implementada. El orden sigue el solicitado. **No se propone retirar ninguna regla.** Cada cambio corrige una causa demostrada y debe medirse en DEV, nunca con el conjunto sellado.

### R1. Recuperación: pérdidas en la fusión (prioridad alta)
* **Problema demostrado:** la evidencia correcta aparece en un canal pero no llega a la salida final.
* **Evidencia:** SCO-019 y SCO-020 (denso 1.º–2.º, ausente al final); SCO-013, SCO-014 y EXC-003 (TF-IDF 14.º–19.º). Son 22 rechazos y 5 preguntas nunca respondidas.
* **Componente:** RRE (fusión RRF, refuerzos temáticos, R3).
* **Cambio propuesto:**
  * diagnosticar, caso por caso, qué refuerzo o qué peso de la fusión desplaza el pasaje;
  * valorar reservar plazas del paquete para el mejor resultado de cada canal.
* **Riesgo:** desplazar pasajes hoy correctos.
* **Pruebas:** R@5 y MRR por pregunta antes y después; el mismo DIG; abstenciones legítimas sin cambios.
* **Impacto esperado:** hasta 5 preguntas.

### R2. Recuperación: idiomas distintos del español (prioridad alta)
* **Problema demostrado:** la consulta en portugués llega sin traducir y no se recupera evidencia.
* **Evidencia:** MLG-002 (4 rechazos; ausente de los dos canales).
* **Componente:** `_translate_to_technical_english`, cuyo detector solo reconoce el español.
* **Cambio propuesto:** traducir cualquier idioma distinto del inglés, y aplicar la precomprobación de fuera de dominio también a la consulta original.
* **Riesgo:** cambia la recuperación de las preguntas multilingües (MLG-003 hoy funciona).
* **Pruebas:** preguntas MLG y OOD de DEV.
* **Impacto esperado:** 1 pregunta y la coherencia entre idiomas.

### R3. Construcción del contexto (sin acción)
No se demostró ningún problema (120/120 fragmentos íntegros). Se mantiene sin cambios.

### R4. Generación: contrato centrado y una sola respuesta (prioridad alta; ya implementado, sin activar)
* **Problema demostrado:** el contrato anterior pedía requisitos conexos que luego no se citaban. Son 17 rechazos DIG-CR, con datos del propio pasaje citado.
* **Evidencia:** §6.1. En la evaluación en vivo (UA): 14 → 18 correctas aceptadas.
* **Componente:** prompt de ADA (`ADA_UNIFIED_ANSWER`).
* **Cambio propuesto:** activarlo tras su revisión, junto con la poda de frases accesorias y la nueva evaluación completa.
* **Riesgo:** puede retirar datos correctos no citados y ayudó a aceptar AMB-010.
* **Pruebas:** varias corridas con el mismo proveedor.
* **Impacto esperado:** las 17 respuestas DIG-CR.

### R5. Validación DIG: tres correcciones dirigidas (prioridad alta)
**a) DIG-11.** Aplicarlo solo cuando ninguna cita sea pertinente (DIG-05 falla), o añadir variantes morfológicas y sinónimos.
* **Evidencia:** 17 correctas rechazadas, 3 preguntas nunca respondidas y 14 casos de causa única. En la simulación, ninguna incorrecta se aceptaría.
* **Riesgo:** preguntas sobre normas inexistentes. No hay casos suficientes en DEV, así que hay que construir un conjunto específico (no el sellado).

**b) DIG-06.** No contar como cifra afirmada la que repite literalmente la consulta («-66 kg») ni los números que forman parte de una referencia de artículo o página.
* **Evidencia:** CAT-001 ×3, SCO-019 UA-B «6.5», EXC-006 «81-82».
* **Riesgo:** bajo, si se limita a cifras idénticas a las de la consulta y a patrones de referencia explícitos.

**c) DIG-09.** Exigir relación léxica entre la excepción y la consulta o la cita.
* **Evidencia:** SCO-024 ×4.
* **Condición:** solo **después** de R6. En la simulación, hoy aceptaría 4 respuestas incorrectas (AMB-005, INC-005 ×2, OOD-006).

**Pruebas para a), b) y c):** reproducción de las 181 entradas, pruebas adversariales existentes y evaluación en vivo.

### R6. Generación y flujo: ambigüedad y completitud (prioridad alta)
* **Problema demostrado:** 5 respuestas aceptadas a preguntas ambiguas; 2 afirman «no se especifica» por falta de evidencia.
* **Evidencia:** AMB-005 ×4 y AMB-010.
* **Componente:** antes de la generación (detección de ambigüedad) y contrato (aclaración).
* **Cambio propuesto:**
  * detectar ambigüedad cuando la evidencia contiene reglas de ámbitos distintos para la misma pregunta;
  * no aplicar la poda si la consulta es ambigua;
  * prohibir en el contrato afirmar que «el SOR no especifica» algo salvo como limitación de los pasajes entregados.
* **Riesgo:** pedir aclaración en preguntas respondibles.
* **Pruebas:** AMB, INC y respondibles de DEV.
* **Impacto esperado:** los 5 falsos negativos.

### R7. Trazabilidad de citas (prioridad media)
* **Problema demostrado:** 5 rechazos por citas parafraseadas o recortadas, y un pasaje citado sin fragmento.
* **Cambio propuesto:** mantener el control (los rechazos son legítimos). Reforzar en el contrato que la cita se copie sin reescribir y, como mejora futura, enlazar cada afirmación con su cita mediante el campo `supports`.
* **Riesgo:** bajo.
* **Pruebas:** DIG-02 y DIG-03 en DEV.

### R8. Presentación (prioridad media)
* **Problema:** la solicitud de aclaración acepta cifras de citas cuya literalidad no se comprueba. Es un hueco ya señalado, no observado en los datos: en AMB-009 las citas eran literales.
* **Cambio propuesto:** localizar literalmente esas citas, como hace DIG-03.
* **Riesgo:** bajo.

### R9. Revisión arbitral (fuera del software)
* **DIR-005:** el SOR da dos separaciones distintas entre estrellas (0,5–2 cm y 1,5–2 cm).
* **EXC-006:** confirmar la regla de tolerancia en individual y mixto.
* **Benchmark:** confirmar los juicios de contenido de esta auditoría; sigue en `PENDING_EXPERT_REVIEW`.

## 10. Limitaciones de la auditoría

* **Juicio de contenido:** lo hizo el auditor leyendo el SOR, no árbitros certificados. El benchmark no está revisado por expertos.
* **Ejecuciones sin generación:** 130 de 328 no tienen respuesta generada, por la cuota. Las corridas de Fase 11 y de integración R3 están sobre todo vacías.
* **Configuraciones distintas:** las corridas usaron DIG, prompt y proveedor distintos. Por eso se presentan la decisión registrada y la del DIG actual.
* **Recuperación:** los rangos proceden del diagnóstico de Fase 11 y pueden no coincidir con la recuperación actual. Las corridas no guardan puntuaciones por pasaje ni los pasajes descartados.
* **Análisis por afirmación:** es léxico (cifras y términos). La fidelidad semántica de las paráfrasis se juzgó manualmente.
* **Variabilidad:** el modelo no es determinista y hay una corrida por configuración.
* **Prompt:** no se guardó como texto único. Es reconstruible en 142/181 filas.
* **Muestra:** DEV tiene pocos casos de normas inexistentes en inglés y de excepciones esperadas. La protección de DIG-11 y la sensibilidad de DIG-09 no quedan medidas.

## 11. Dictamen técnico

**¿El DIG rechaza respuestas normativamente correctas porque Gemini las expresa de una forma que el validador no reconoce, porque RRE no recupera suficiente información o por una combinación?**

**Por una combinación de causas, con efectos distintos:**

1. **Respuestas correctas rechazadas** (55 de 149 respondibles generadas). La causa demostrada es **el validador**, no la recuperación: en todas ellas la evidencia correcta llegó al modelo y el modelo la usó con fidelidad.
   * **40 falsos positivos vigentes:**
     * 23 de reglas que evalúan algo distinto del respaldo: DIG-11 (vocabulario de la pregunta), DIG-09 (cercanía en el texto) y DIG-06 (cifras de la propia consulta);
     * 17 de exigencia de literalidad: datos accesorios que el modelo tomó del pasaje citado sin copiarlos en la cita.
   * **10 ya corregidos** por el DIG actual.
   * **5 rechazos legítimos** por citas no literales del modelo.
   * La parte «Gemini lo expresa de forma no reconocible» es real, pero pequeña: el modelo **cita menos de lo que usa**, en parte porque el contrato anterior se lo pedía.
2. **Preguntas que no reciben respuesta.** La causa principal demostrada es la **recuperación**.
   * 6 de las 10 preguntas nunca respondidas no tienen la evidencia correcta en el paquete. En esos 27 rechazos **el DIG actúa correctamente**: bloquea respuestas de otro ámbito, mal fundamentadas o sin respaldo.
   * Las otras 4 se pierden por DIG-11 y DIG-09.
3. **Respuestas incorrectas aceptadas** (5 de 71 aceptadas). No las causa ni la forma ni la literalidad: son preguntas **ambiguas** que no se detectaron. En 2 casos se suma una generalización falsa por evidencia incompleta, algo que el DIG no puede ver porque solo verifica lo citado.

No se declara demostrada ninguna causa que los registros no permitan comprobar: el efecto del tamaño del contexto, la influencia de R3 en las pérdidas actuales y la sensibilidad de DIG-09.

**Recomendación:**
1. Corregir primero la recuperación (R1, R2) y la ambigüedad (R6).
2. Después, las tres correcciones dirigidas del DIG (R5 a y b) y la activación de la respuesta única (R4).
3. DIG-09 (R5c), el último.

No se recomienda relajar DIG-05 ni retirar DIG-06/07.

Queda a la espera de autorización antes de implementar cualquier corrección.

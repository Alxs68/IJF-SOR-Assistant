# Diagnóstico DIG-11, DIG-09 y proceso de generación

Fecha: 2026-11-16 · Intervención **exclusivamente diagnóstica**: no se modificó código, prompts, DIG, R3, corpus, SHADOW ni benchmarks; sin llamadas al LLM, sin despliegues, sin commit.
Datos: 246 filas de evaluación DEV (benchmark_v2, 41 preguntas) almacenadas — evaluación A/B (A y B), Fase 11 (2 corridas) e integración R3 (original y experimental) — con **108 entradas exactas del DIG**, reevaluadas offline con la configuración experimental vigente (`DIG-1.3+NUM-v2+FIX-v3`). Las simulaciones de §10 son análisis en memoria; no se incorporaron al código. test_sealed no se usó.

## 1. Resumen ejecutivo

De las 31 preguntas respondibles, en la evaluación A (configuración experimental, DIG actual):

| Etapa donde se pierde o se gana la respuesta | A | B |
|---|---|---|
| Aceptada con la evidencia esperada | 14 | 15 |
| Aceptada con reservas | 1 | 0 |
| **Recuperación**: la evidencia esperada no llega al LLM | **7** | 5 (+2 sin generación) |
| **Bloqueo DIG-06/07**: el modelo usa contenido del pasaje sin citarlo | **5** | 5 |
| **Falso bloqueo DIG-11** (vocabulario de la pregunta) | 2 | 3 |
| Bloqueo DIG-09 por excepción vecina no relacionada | 1 | 0 |
| Proveedor sin generación | 1 | 3 |

Hallazgos principales:

1. **La primera causa de no respuesta es la recuperación (RRE + traducción), no el DIG**: 7 de 31 preguntas no reciben la norma correcta.
2. **El modelo no inventa cifras**: de 36 cifras afirmadas sin cita, **32 están en el propio pasaje citado** y 1 en otro pasaje entregado; las 3 restantes son numeración de listas. 27 de 36 aparecen en `conditions_and_exceptions`. El problema es que el **contrato del prompt pide añadir requisitos conexos** y el modelo no los cita, no que alucine.
3. **DIG-11 es la única regla cuyos bloqueos en los datos son todos falsos positivos**: 12 activaciones, 11 en preguntas respondibles con la cita correcta (9 como único motivo); en la única no respondible (OOD-005) otras reglas ya bloqueaban. Además solo se aplica a consultas en inglés.
4. **DIG-09 bloquea por proximidad textual**, no por relación normativa; pero **hoy está tapando dos fallos de etapas anteriores** (una pregunta fuera de dominio y una ambigua que el LLM llegó a responder). Relajarlo ahora aceptaría esas dos respuestas.
5. Hay un **canal no verificado**: `extended_analysis` se muestra al usuario pero DIG-06/07 no lo revisan.

**Intervención mínima recomendada (§12):** corregir la recuperación y la traducción (incluido el portugués y la deriva de dominio), ajustar el contrato del prompt para que no solicite requisitos conexos sin cita, y subordinar DIG-11 a la existencia de cita pertinente. **No tocar DIG-09** hasta que las etapas anteriores dejen de depender de él.

## 2. Arquitectura real del flujo (código inspeccionado)

`ADA.analyze_situation`:
1. **Precomprobación OOD** sobre la consulta original (RRE, `enable_ood_detector=True`) → abstención sin LLM.
2. **Traducción** `_translate_to_technical_english`: llamada al LLM solo si detecta español (acentos `áéíóúüñ¿¡` o palabras clave); si no, la consulta pasa **sin traducir**.
3. **RRE** `retrieve(search_query_en, domain_query=original)`: TF-IDF + denso + RRF + boosts temáticos (+ R3 si está activo) → `evidence` y `related`.
4. **SHADOW** `retrieve_supplementary` (consulta original y, si no hay, la traducida).
5. Sin evidencia primaria → abstención. **Bundle certificado** (`DocumentValidator`) y filtro de evidencia certificada.
6. **Prompt**: bloques de contexto SOR (mediana 13 800 caracteres, máximo 28 900; 5–8 pasajes) + bloques `[COMPLEMENTO-n]` + contrato JSON + 13 reglas (+ regla 14 opcional).
7. **LLM** (Gemini principal, Groq respaldo; modo JSON / esquema opcionales).
8. **Validador de citas** (nivel A) → **DIG** (DIG-00…DIG-12) → formateo.

No hay memoria entre consultas: cada análisis es independiente. En los datos **no aparece contenido de otras consultas**: ninguna cifra afirmada falta en las entradas de su propia consulta (salvo numeración de listas).

## 3. Diagnóstico de DIG-11

**Qué hace** (`decision_integrity.py`): si la consulta está en inglés (`query_language`), toma sus raíces de contenido (`content_stems`: palabras ≥ 4 letras, primeras 5 letras, sin palabras vacías) y bloquea si alguna **no aparece en ninguna página del SOR**. Se presenta como condición necesaria: «si un término de la consulta no está en el SOR, el SOR no puede responderla literalmente».

**Qué información usa:** solo la consulta original y la frecuencia de raíces del corpus. **No mira la evidencia recuperada, la respuesta ni las citas.** Es una propiedad de la *pregunta*, no de la respuesta.

**Activaciones en los datos (12):**

| Pregunta | Término «ausente» | ¿Respondible? | ¿Cita correcta? | Otras reglas fallidas | Juicio |
|---|---|---|---|---|---|
| DIR-005 (×6 capturas) | «spacing» → `spaci` (el SOR dice «space») | Sí | Sí | ninguna (1 caso DIG-01) | Falso positivo: variante morfológica |
| EXC-009 (×3) | «skips» (el SOR dice «absent from») | Sí | Sí | ninguna | Falso positivo: sinónimo |
| SCO-025 (×2) | «suffers» | Sí | Sí | B: ninguna; A (Groq): DIG-03/06 | Falso positivo en B |
| OOD-005 | «heel», «hook», «IBJJF» | No (fuera de dominio) | — | DIG-01, 02, 03, 05 | Correcto, pero redundante |

**Cobertura:** DIG-11 es el **único motivo de bloqueo en 9 respuestas correctas**. Simulación (en memoria) sin DIG-11: esas 9 pasan a aceptadas con la evidencia esperada y **ninguna respuesta incorrecta se acepta**.

**Asimetría:** de las 41 preguntas, 24 no están en inglés y DIG-11 no se les aplica. La misma pregunta formulada en español no pasa por DIG-11.

**Relaciones:** con la recuperación, ninguna (DIG-11 no usa la evidencia). Con las citas, ninguna. Con DIG-05 hay solapamiento conceptual: ambas comparan términos de la consulta, pero DIG-05 lo hace contra la cita (con la traducción) y DIG-11 contra todo el SOR. DIG-05 sí discrimina: en 25 de 26 activaciones las citas no contenían la evidencia esperada.

**Limitación:** en DEV solo hay 2 preguntas no respondibles en inglés (INS-001, OOD-005); el papel protector de DIG-11 ante preguntas sobre normas inexistentes no queda medido con este conjunto.

## 4. Diagnóstico de DIG-09

**Qué valida:** para cada cita literal localiza su unidad derivada (`article_units_v1`) en el texto canónico de la página y examina una ventana de **±2 frases**. Toda frase de esa ventana que contenga un marcador de excepción (`except, unless, however, although, notwithstanding, nevertheless, does not apply, no score or penalty, only if, only when, can only`) debe estar también citada; si no, bloquea.

**Cómo determina la pertinencia:** no la determina. No relaciona la excepción con la pregunta, con la afirmación ni con la frase citada; **confunde proximidad textual con respaldo normativo**. «Although» se trata como excepción aunque sea solo un conector. No distingue afirmaciones dentro de la respuesta: se evalúa por cita, no por afirmación.

**Activaciones (13; 7 distintas):**

| Caso | Excepción exigida | Clasificación |
|---|---|---|
| SCO-024 A (kata, eventos con puntos) | «The ranking point system takes into consideration the five best results… except for U18» (trata del cálculo, no de los eventos) | **Falso positivo** (respuesta exacta y mínima) |
| SCO-024 B | Ídem, más cifras sin cita (DIG-06) | Bloqueo correcto (por DIG-06) |
| SCO-019 A/B (tolerancia cadetes) | «Although the individual and team events are separate competitions…» | **Bloqueo correcto**: la respuesta usa la tolerancia de *equipos* para una pregunta *individual*; además fallan DIG-05/06/10 |
| AMB-005 A («¿Cuántos reservas?») | «Athletes can only be entered in the weight category…» (no relacionada) | Falso positivo del mecanismo, **resultado conveniente**: la pregunta es ambigua y debía pedir aclaración |
| AMB-009 (puntos del primer puesto) | «ranking point system… five best results» | Ambiguo; la pregunta también es ambigua y fallan otras reglas |
| INC-005 («¿Y si son menos?») | «Nevertheless, all athletes who have successfully passed the official medical…» | **Caso ambiguo** (requiere revisión arbitral: la salvedad puede formar parte de la regla citada) |
| OOD-006 B («¿Cómo funciona el VAR en el fútbol?») | «Any decoration on the tatami…» (no relacionada) | Falso positivo del mecanismo, **resultado conveniente**: es el **único** control que impidió aceptar una respuesta sobre el sistema de vídeo del judo a una pregunta de fútbol |

**Falsos negativos:** en DEV solo EXC-003 tiene excepciones esperadas y nunca llegó al LLM por recuperación; no se observan aceptaciones que omitan una excepción esperada. La muestra no permite medir la sensibilidad de DIG-09.

**Simulación (en memoria) — DIG-09 solo si la excepción comparte un término distintivo con la consulta o la cita:** +1 respuesta correcta (SCO-024) y **+2 respuestas incorrectas** (AMB-005 respondida pese a ser ambigua; OOD-006 respondida pese a estar fuera de dominio). **Hoy DIG-09 compensa fallos de etapas anteriores.**

## 5. Diagnóstico del proceso de generación

**Origen del contenido no citado** (todas las activaciones DIG-06/07 en las 108 entradas):

| Origen | Cifras (36) | Términos (12) |
|---|---|---|
| Está en el **pasaje citado**, pero fuera del fragmento citado | 32 | 8 |
| Está en otro pasaje entregado | 1 | 3 |
| Solo en SHADOW | 0 | 0 |
| En ninguna entrada (numeración de listas «1.», «2.») | 3 | 1 |

| Campo de la respuesta | Cifras sin cita |
|---|---|
| `conditions_and_exceptions` | 27 |
| `summary` | 7 |
| `normative_basis` | 2 |

**Conclusión demostrada:** el modelo **es fiel a la evidencia pero cita menos de lo que usa**, sobre todo en las condiciones. No se observó invención de cifras ni reutilización de otras consultas.

**Por qué ocurre (prompt, `ada_assistant.py` ~l. 545–583):**
* El contrato define `conditions_and_exceptions` como «condiciones específicas, excepciones reglamentarias, **restricciones por categoría** (ej. cadetes/juniors) y **notas técnicas**», y la regla 10 ordena: «**Segrega los requisitos conexos** en `conditions_and_exceptions` o `extended_analysis`». La regla 6 pide además analizar escenarios.
* La regla 13 exige cita literal de toda cifra de esos campos, pero el pasaje entregado es largo (mediana ~13 800 caracteres) y el modelo cita una frase y resume el resto.
* Resultado: el prompt **pide contenido accesorio** que el DIG exige citar; el conflicto está en el diseño del contrato. La regla 14 (evaluada en A/B) no lo resolvió.

**Otros problemas de generación observados:**
* **Ámbito:** SCO-019 respondió la tolerancia de cadetes *por equipos* a una pregunta *individual* porque la recuperación no entregó la página correcta (origen: recuperación; el DIG bloqueó).
* **Fuera de dominio:** OOD-006 (portugués, fútbol). La traducción convirtió la pregunta en «video review replay system refereeing commission», la recuperación encontró el sistema de vídeo del judo y Gemini respondió con `answerability=RESPALDADA` (origen: traducción + precomprobación OOD).
* **Interpretaciones:** el prompt exige marcarlas como «Interpretación normativa:» y los modelos lo hacen, pero en `extended_analysis`, campo que **DIG-06/07 no verifican** aunque se muestra al usuario. De 46 respuestas aceptadas, 1 contenía cifras sin cita en ese campo (todas presentes en la evidencia); es un canal de falso negativo potencial.
* **Idioma:** Groq respondió en inglés a preguntas en español (SCO-010, MLG-003).

**Traducción de consultas:**
* **Portugués sin traducir:** el detector de español no reconoce «õ» ni el vocabulario portugués; MLG-002 llegó a la recuperación en portugués y la evidencia no apareció en ningún canal.
* **Deriva de dominio:** OOD-006 (arriba).
* **Expansión con términos nuevos** («doctor», «procedure», «-66 kg» ya presente…), que cambia la recuperación y el DIG-05 de una corrida a otra (caso del cadete en diagnósticos anteriores).

**Diferencias entre proveedores (108 entradas: Gemini 73, Groq 35):**

| | Gemini (`gemini-3.5-flash-lite`) | Groq (`openai/gpt-oss-120b`, plan gratuito) |
|---|---|---|
| Disponibilidad | 503 intermitentes | 429 por tokens/min; 413 en prompts > 8 000 tokens |
| Formato | 1 JSON inválido sin esquema; 0 con esquema | — |
| Citas | Literales en general | Guion U+2011 (corregido en experimental) y paráfrasis («If another…» frente a «In case another…») |
| Idioma | Respeta el de la consulta | A veces responde en inglés a preguntas en español |

## 6. Interacciones y conflictos

* **Prompt ↔ DIG-06/07/09:** el contrato pide condiciones y requisitos conexos; DIG-09 exige citar excepciones vecinas aunque no se relacionen; DIG-06/07 bloquean lo que no se cita. El modelo queda entre «añade contexto» y «no afirmes nada sin cita».
* **Traducción ↔ RRE ↔ DIG-05:** la expansión de la consulta cambia la evidencia y los términos con que DIG-05 juzga la pertinencia.
* **DIG-11 ↔ DIG-05:** comparan términos de la consulta con fuentes distintas; DIG-11 es redundante donde DIG-05 ya discrimina.
* **DIG-09 ↔ OOD/ambigüedad:** DIG-09 compensa accidentalmente fallos de la precomprobación OOD y del detector de ambigüedad.
* **DIG-03 ↔ proveedor:** la literalidad depende del estilo tipográfico y de la fidelidad del proveedor de respaldo.

## 7. Casos analizados y evidencia

Detalle por pregunta en §3–§5 y §9. Fuentes: `data/eval/dig_v3/ab_dev.json`, `data/eval/fase11/llm_dev_f11_capture.json`, `data/eval/integracion_r3_dig/llm_dev_{original,experimental}.json`, `data/eval/fase11/diag_retrieval_dev.json` (rangos por canal).

**Pérdidas en recuperación (variante A):**

| Pregunta | Esperado | Diagnóstico (Fase 11, rangos por canal) |
|---|---|---|
| SCO-019, SCO-020 | Tolerancia p. 75 | El canal denso la sitúa **1.º–2.º**, pero desaparece tras la fusión con TF-IDF y los refuerzos temáticos |
| SCO-013, SCO-014 | Área de kata p. 112 | TF-IDF 14.º–18.º; denso fuera; la recuperación entrega páginas vecinas de kata |
| EXC-003 | p. 61 | TF-IDF 19.º |
| MLG-002 | p. 42 | No aparece en ningún canal: **consulta en portugués sin traducir** |
| MUL-004 | p. 42 + p. 45 | Llega la p. 46 (texto distinto de la p. 45); cobertura parcial |

## 8. Causas raíz identificadas

1. **Recuperación:** la fusión pierde pasajes que el canal denso encontraba (SCO-019/020); vocabulario de áreas de kata (SCO-013/014); consultas no españolas sin traducir (MLG-002).
2. **Traducción:** detector limitado al español; la expansión puede cambiar el dominio de la pregunta (OOD-006).
3. **Contrato del prompt:** solicita requisitos conexos y condiciones que luego deben citarse literalmente.
4. **DIG-11:** evalúa la formulación de la pregunta, no el respaldo de la respuesta; sensible a sinónimos y morfología; solo en inglés.
5. **DIG-09:** criterio de proximidad sin relación normativa.
6. **Campo no verificado:** `extended_analysis` se muestra sin control de cifras ni términos.
7. **Proveedor:** saturación y límites del plan gratuito; diferencias de estilo de cita entre modelos.

## 9. Falsos positivos y bloqueos correctos

| Tipo | Casos |
|---|---|
| Falso positivo **DIG-11** | DIR-005 (×6), EXC-009 (×3), SCO-025 B |
| Falso positivo **DIG-09** | SCO-024 A |
| Falso positivo del mecanismo DIG-09 con resultado conveniente | AMB-005 A, OOD-006 B |
| Bloqueo correcto **DIG-06/07** (contenido del pasaje usado sin citar) | DIR-018 A/B, SCO-021 A/B, SCO-023 A/B, SCO-024 B, SCO-026 A, DIR-011 B |
| Bloqueo correcto (paráfrasis no literal, Groq) | SCO-025 A |
| Bloqueo correcto (ámbito equivocado por recuperación) | SCO-019 A/B |
| **Revisión arbitral** | DIR-005: el SOR contiene «a space of 0.5 cm – 2 cm between each star» y «Space between two stars: from 1.5 cm to 2 cm»; INC-005: ¿la salvedad «Nevertheless…» forma parte de la regla?; EXC-006 (ya pendiente) |
| Falsos negativos observados | Ninguna respuesta incorrecta aceptada en los datos. **Potenciales**: `extended_analysis` no verificado; OOD-006 y AMB-005 dependen hoy de DIG-09 |

## 10. Propuestas de corrección priorizadas

| # | Problema | Causa raíz | Solución propuesta | Riesgo | Prioridad | Tipo |
|---|---|---|---|---|---|---|
| 1 | Evidencia esperada no recuperada (7/31) | Fusión que descarta aciertos del canal denso; consultas no españolas sin traducir | Diagnosticar la fusión y los refuerzos en SCO-019/020/013/014; traducir también portugués, francés y otros idiomas | Medio: cambios en RRE afectan a todo el ranking; requiere benchmark | Alta | A |
| 2 | Deriva de dominio en la traducción (OOD-006) | La traducción-expansión convierte una pregunta ajena en una de judo | Hacer la precomprobación OOD también sobre la consulta original en cualquier idioma y prohibir en la traducción términos que no estén en la consulta | Bajo-medio | Alta | A |
| 3 | Contenido usado sin cita en condiciones (5/31) | El contrato pide requisitos conexos y notas técnicas | Reformular `conditions_and_exceptions` y la regla 10: solo condiciones que restrinjan la respuesta a la pregunta, cada una con su cita; nada accesorio | Bajo para la integridad (el DIG no cambia); efecto incierto en el modelo, hay que medirlo | Alta | B |
| 4 | `extended_analysis` no verificado | Campo fuera de DIG-06/07 | Aplicar DIG-06/07 también a `extended_analysis`, o no mostrarlo cuando no está verificado | Puede aumentar los bloqueos si el modelo escribe ahí contenido no citado | Media | A |
| 5 | Falsos positivos DIG-11 (9 respuestas) | Evalúa la formulación de la pregunta | Subordinar DIG-11: aplicarlo solo si ninguna cita es pertinente (DIG-05 falla), o aplicarlo a todos los idiomas con variantes morfológicas | Medio: su papel ante preguntas sobre normas inexistentes no está medido en DEV; validar con un conjunto específico (no el sellado) | Media | C |
| 6 | DIG-09 por proximidad | Ventana ±2 frases sin relación | **No cambiar ahora.** Revisar después de 1 y 2, cuando ya no compense fallos de OOD y ambigüedad | Alto si se cambia antes (2 aceptaciones incorrectas simuladas) | Baja (diferida) | C |
| 7 | Saturación y límites del proveedor | Planes gratuitos | Plan de pago o reintentos con espera; no comparar variantes con proveedores distintos | — | Media | D |
| 8 | Paráfrasis e idioma en el respaldo (Groq) | Comportamiento del modelo | Aceptar como limitación; el DIG ya lo detecta | — | Baja | D |
| 9 | SOR ambiguo (estrellas), salvedad de INC-005, EXC-006 | Texto normativo | Revisión por árbitros | — | Media | E |

## 11. Riesgos de cada modificación

* **RRE (1):** puede desplazar pasajes hoy correctos; exige medir R@5/MRR y abstenciones en DEV antes y después.
* **Traducción (2):** traducir más idiomas cambia la recuperación de las preguntas multilingües; restringir la expansión puede empeorar consultas coloquiales.
* **Prompt (3):** el efecto en el modelo no es determinista; la evaluación A/B mostró que una regla añadida no basta. Debe medirse con varias corridas y el mismo proveedor.
* **`extended_analysis` (4):** más bloqueos a corto plazo; a cambio se elimina un canal sin control.
* **DIG-11 (5):** posible aceptación de respuestas a preguntas sobre normas que no existen, si la recuperación entrega un pasaje parecido y el modelo lo cita; el riesgo depende de 2.
* **DIG-09 (6):** demostrado en simulación: aceptaría una respuesta fuera de dominio y otra a una pregunta ambigua.

## 12. Recomendación de intervención mínima

1. **Primero, las etapas anteriores al DIG:** (2) precomprobación OOD y traducción para cualquier idioma, sin expansión de dominio; (1) diagnóstico de la fusión en los 4 casos donde el canal denso acierta y la salida final no.
2. **Después, el contrato del prompt (3)** y la verificación de `extended_analysis` (4), medidos con varias corridas y el mismo proveedor.
3. **DIG-11 (5)** solo cuando 1–2 estén resueltos, con un conjunto de preguntas sobre normas inexistentes construido para ello.
4. **DIG-09 (6)** el último, y solo si deja de compensar fallos de otras etapas.

Ninguna de estas propuestas está implementada. Quedan a decisión del responsable.

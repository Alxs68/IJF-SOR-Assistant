# SOR-IJF — Dictamen de auditoría independiente VF01

**Fecha:** 2026-11-06  
**Naturaleza:** auditoría documental y estática de solo lectura.  
**Objeto:** corrección normativa de las respuestas registradas para los 52 casos VF01, no solo el estado técnico de ejecución.

## 1. Resumen ejecutivo

El dictamen de VF01 como **«52/52 PASS, cero regresiones» no queda sustentado** por la evidencia disponible. `SUCCESS` prueba que el flujo devolvió una respuesta, no que respondiera la pregunta, citara el artículo pertinente ni expresara la consecuencia normativa solicitada. La propia evidencia de revisión reconoce cinco falsos PASS (VF01-04, 11, 12, 15 y 35) y dos respuestas genéricas; la revisión independiente de los resúmenes completos identifica más omisiones materiales.

Resultado de esta auditoría, aplicando un criterio de respuesta directa, cita pertinente y cobertura de los elementos preguntados:

| Clasificación independiente | Casos | Total |
|---|---|---:|
| Correcto normativamente | VF01-06, 22, 26, 27, 28, 32, 38, 44, 45, 46, 50, 52 | 12 |
| Abstención correcta | VF01-16, 17, 36, 37, 49 | 5 |
| Genérico / insuficiente | VF01-01, 05, 07, 08, 09, 13, 14, 18, 19, 20, 24, 29, 31, 34, 39, 43, 48, 51 | 18 |
| Parcialmente correcto | VF01-21 | 1 |
| Incorrecto | VF01-02, 03, 04, 10, 11, 12, 15, 23, 30, 33, 35, 40, 41, 42, 47 | 15 |
| No verificable | VF01-25 | 1 |

Así, hay **17/52 casos favorables** (12 correctos + 5 abstenciones correctas), **19/52 insuficientes/parciales**, **15/52 incorrectos** y **1/52 no verificable**. Estos números no son una tasa de precisión operacional generalizable: describen únicamente la evidencia VF01 archivada.

El resultado es especialmente preocupante en seguridad: de 15 casos SEC-CRIT, solo 5 tienen respuesta verificablemente correcta, 5 son insuficientes y 5 incorrectos. Por tanto, no se sostiene el 15/15 PASS SEC-CRIT.

## 2. Alcance, fuentes y método

### Archivos examinados

- `docs/validacion_funcional_consolidada_vf01.md`.
- `docs/evidencia_revision_vf01.md`.
- `scratch/vf01_execution_results.json` y `scratch/vf01_classified_results.json`.
- `data/processed/rebuild_2026_08_corrected/passages_candidate.json`.
- `data/raw/sor_2026_08_rebuild/source_manifest.json`.

Se contrastaron pregunta, estado, resumen de respuesta, Top-1/Top-3 y citas almacenadas con los pasajes SOR disponibles. No se ejecutaron pruebas, no se modificó código/configuración/corpus/índices/grafos y no se usó Git, OCI ni red.

### Regla de clasificación

- **Correcto normativamente:** la respuesta registrada resuelve la pregunta con regla y consecuencia pertinentes.
- **Parcialmente correcto:** contiene un elemento aplicable pero omite o desatiende una condición decisiva.
- **Genérico/insuficiente:** el pasaje es relacionado, pero no responde el hecho, cifra, sanción o alcance solicitado.
- **Incorrecto:** pasaje o conclusión no corresponde a la pregunta, o contradice su objeto.
- **Abstención correcta/incorrecta:** rechazo apropiado/inapropiado frente al ámbito verificable del corpus.
- **No verificable:** falta evidencia local suficiente para sostener o refutar la respuesta sin presumir contenido externo.

El criterio es más estricto que el de VF01: `SUCCESS` y una URL válida no cuentan como PASS normativo sin pertinencia y completitud.

## 3. Matriz de los 52 casos

**Clave de evidencia:** `E` = `scratch/vf01_execution_results.json`; `P` = pasaje de `passages_candidate.json`; `R` = `docs/evidencia_revision_vf01.md`.

| VF / origen | Estado técnico VF01 | Evidencia registrada relevante | Clasificación independiente | Fundamento conciso |
|---|---|---|---|---|
| 01 / TC-01 | SUCCESS / PASS | 8.7 p96 | Genérico/insuficiente | Da 8×8–10×10 del área de combate, no la medida del área de seguridad preguntada. |
| 02 / TC-02 | SUCCESS / PASS | Art. 7 p152 | Incorrecto | Pregunta duración senior; resumen responde tiempos de osaekomi. |
| 03 / TC-03 | SUCCESS / PASS | Art. 14 p166–167 | Incorrecto | Pregunta los cuatro criterios de ippon; responde la excepción de puente sobre Tori. |
| 04 / TC-04 | SUCCESS / PASS | 8.7 p96; P168 debía aplicar | Incorrecto | Responde dimensiones; SOR Art. 15 p168 regula Waza-ari por caída de hombro >90° y no de espalda. |
| 05 / TC-05 | SUCCESS / PASS | Art. 17 p174; Art. 15 p168–169 asociado | Genérico/insuficiente | Explica `Toketa`/continuación, pero no responde la puntuación a 16 s: Waza-ari (10–19 s). |
| 06 / TC-06 | SUCCESS / PASS | 18.1.4 p189 | Correcto normativamente | Prohíbe reverse seoi-nage en cadetes, sin puntuación y con Shido. |
| 07 / TC-07 | SUCCESS / PASS | 18.1.4 p188; 18.2.1 p190 relacionado | Genérico/insuficiente | Responde Cadete (Shido) pero no formula la regla Senior solicitada ni distingue el supuesto de head diving. |
| 08 / TC-08 | SUCCESS / PASS | 18.1.4 p188 | Genérico/insuficiente | Dice que está prohibido defender con cabeza; omite que Uke recibe Shido y Tori recibe puntuación si la hay. |
| 09 / TC-09 | SUCCESS / PASS | 18.2.1 p190 | Genérico/insuficiente | Da Hansoku-make, pero omite la continuidad preguntada: para dangerous techniques el atleta **puede** continuar. |
| 10 / TC-10 | SUCCESS / PASS | D1.1 p134; 18.2.2 p193 | Incorrecto | El resumen recuperado es historia/cultura de judo, no sanción por insulto o agresión. |
| 11 / TC-11 | SUCCESS / PASS | Art. 4 p149; 18.2.2 p190 debía aplicar | Incorrecto | Recupera gesto de sanción, no kawazu-gake; SOR p190 lo ubica en 18.2.2. |
| 12 / TC-12 | SUCCESS / PASS | 8.7 p96; Art. 5 p151 debía aplicar | Incorrecto | Responde dimensiones, no la excepción de continuidad fuera del área hasta 2 m de seguridad. |
| 13 / TC-13 | SUCCESS / PASS | C1.1.2 p115 | Genérico/insuficiente | Habla de precontrol y dos judogi; no contesta expresamente la prohibición de judogi reversible. |
| 14 / TC-14 | SUCCESS / PASS | 18.2.2 p190 | Genérico/insuficiente | La consulta ambigua exige escenarios; entrega ejemplos de actos peligrosos sin distinguir Tori/Uke, cadete, puente o diving. |
| 15 / TC-15 | SUCCESS / PASS | C1.3 p119; Art. 11 p160–161 debía aplicar | Incorrecto | Responde logotipo del fabricante; no situaciones de `Mate!`. |
| 16 / TC-16 | ABSTAIN / PASS | Sin evidencia | Abstención correcta | Baloncesto fuera de SOR. |
| 17 / TC-17 | ABSTAIN / PASS | Sin evidencia | Abstención correcta | Finanzas fuera de SOR. |
| 18 / TC-18 | SUCCESS / PASS | 1.1.1 p14; D1.1 p134 relacionado | Genérico/insuficiente | Enuncia conducta IJF; no determina consecuencia de ofensa/agresión. |
| 19 / TC-19 | SUCCESS / PASS | 7.1 p89 | Genérico/insuficiente | Da deber de respetar código, no sanciones solicitadas. |
| 20 / TC-20 | SUCCESS / PASS | Art. 18 p175; 18.3.2 asociado | Genérico/insuficiente | Describe grupos de infracciones; no responde «tres Shidos». |
| 21 / TC-21 | SUCCESS / PASS | Art. 14 p167 y p166 relacionado | Parcialmente correcto | Cita la excepción de no score sobre Tori, no la regla principal: puente voluntario tras proyección es ippon. |
| 22 / TC-22 | SUCCESS / PASS | Art. 14 p167 | Correcto normativamente | Responde exactamente la excepción de aterrizaje sobre Tori. |
| 23 / MC-01 | SUCCESS / PASS | 4.4 p64 | Incorrecto | Responde cupos/WRL; no permisibilidad de reverse seoi-nage en seniors. |
| 24 / MC-02 | SUCCESS / PASS | Art. 4 p149 | Genérico/insuficiente | Enumera conductas de pérdida de tiempo; no establece el supuesto límite de tiempo o que no exista cifra expresa. |
| 25 / MC-03 | ABSTAIN / PASS | Sin evidencia local del artefacto LA28 | No verificable | No se halló en la evidencia de ejecución el documento concreto que permitiría validar la fecha/evento. No se presume. |
| 26 / MC-04 | SUCCESS / PASS | GENERAL p159 | Correcto normativamente | P159 establece continuidad sin interrupción en transición tachi-waza/ne-waza. La etiqueta `GENERAL` es defectuosa, no el contenido. |
| 27 / MC-05 | SUCCESS / PASS | GENERAL p159 | Correcto normativamente | P159 responde: si se arrastra indebidamente y no hay aprovechamiento, `Mate!` y Shido; si lo hay, continúa ne-waza. |
| 28 / MC-06 | SUCCESS / PASS | Art. 15 p168–169 | Correcto normativamente | P169 establece Yuko 5–9 s. |
| 29 / MC-07 | SUCCESS / PASS | 18.1.1 p177 | Genérico/insuficiente | Cubre postura negativa en pie; no desarrolla la comparación solicitada entre pie y suelo. |
| 30 / MC-08 | SUCCESS / PASS | 18.2.2 p190 | Incorrecto | Resumen trata kata-sankaku/acto peligroso; no responde la excepción por contacto accidental. |
| 31 / MC-09 | SUCCESS / PASS | 8.7 p96 | Genérico/insuficiente | Responde área de combate, no todas las dimensiones de tatami solicitadas. |
| 32 / MC-10 | SUCCESS / PASS | C1.9 p124 | Correcto normativamente | Contiene los rangos Pantone pedidos. |
| 33 / MC-11 | SUCCESS / PASS | 6.3 p79 | Incorrecto | Recupera pesaje aleatorio, no categorías de peso senior. |
| 34 / MC-12 | SUCCESS / PASS | 18.1 p176 | Genérico/insuficiente | No determina tres Shidos/Hansoku-make indirecto. |
| 35 / MC-13 | SUCCESS / PASS | 7.2 p89 | Incorrecto | Es consulta OOD de baloncesto y debía abstener; responde código de vestimenta de entrenadores IJF. |
| 36 / MC-14 | ABSTAIN / PASS | Sin evidencia | Abstención correcta | Natación fuera de SOR. |
| 37 / MC-15 | ABSTAIN / PASS | Sin evidencia | Abstención correcta | NFL fuera de SOR. |
| 38 / MC-16 | SUCCESS / PASS | 18.1.4 p189 | Correcto normativamente | Reverse seoi-nage cadete: sin score y Shido a Tori. |
| 39 / MC-17 | SUCCESS / PASS | Art. 15 p169/p168 | Genérico/insuficiente | Solo declara que los Yukos no se acumulan; no compara 10 s Waza-ari y 5 s Yuko. |
| 40 / MC-18 | SUCCESS / PASS | Art. 13 p165 | Incorrecto | Responde golden score/kiken-gachi; no `Mate!` durante acción positiva en suelo. |
| 41 / MC-19 | SUCCESS / PASS | Art. 8 p153 | Incorrecto | Trata técnica al final del tiempo, no ritmo de ataque o tiempo de agarre. |
| 42 / MC-20 | SUCCESS / PASS | 18.2.2 p190 | Incorrecto | Resumen afirma consecuencia de actos contra espíritu; no responde la excepción de caída accidental en contraataque. |
| 43 / CGPT-01 | SUCCESS / PASS | 8.7 p96 | Genérico/insuficiente | Repite solo rango de área de combate, no dimensiones completas de tatami. |
| 44 / CGPT-02 | SUCCESS / PASS | Art. 17 p174 | Correcto normativamente | Si osaekomi supera completamente el área de seguridad: `Ippon! Sore-Made!`. |
| 45 / CGPT-03 | SUCCESS / PASS | 18.1.4 p188 | Correcto normativamente | En cadetes, Tori usa cabeza para lanzar: Shido. |
| 46 / CGPT-04 | SUCCESS / PASS | 18.1.4 p188 | Correcto normativamente | Misma regla cadete, correctamente recuperada. |
| 47 / CGPT-05 | SUCCESS / PASS | Art. 17 p173–174 | Incorrecto | Devuelve regla de salida de área; no definición/condiciones de Osaekomi y Toketa. |
| 48 / CGPT-06 | SUCCESS / PASS | Art. 4 p146–149 | Genérico/insuficiente | Consulta indeterminada; devuelve gestos, sin identificar la falta ni pedir aclaración. |
| 49 / CGPT-07 | ABSTAIN / PASS | Sin evidencia | Abstención correcta | NBA/F1 fuera de SOR. |
| 50 / CGPT-08 | SUCCESS / PASS | Art. 14 p166–167 | Correcto normativamente | La excepción textual descarta ippon/penalidad cuando las partes del puente no tocan tatami por caer sobre Tori. |
| 51 / CGPT-09 | SUCCESS / PASS | C1.9 p124; C1.1.5 p117 | Genérico/insuficiente | Da colores, no procedimiento/medidas de manga con sokuteiki. |
| 52 / CGPT-10 | SUCCESS / PASS | C1.9 p124 | Correcto normativamente | Responde colores de judogi en competición IJF. |

## 4. Auditoría de los 15 SEC-CRIT

| VF / consulta crítica | Clasificación | Evidencia y dictamen |
|---|---|---|
| 07 / cabeza de Tori, cadete y senior | Genérico/insuficiente | P188 prueba Shido cadete; la salida no enuncia el régimen senior pedido. |
| 08 / defensa con cabeza cadete | Genérico/insuficiente | P188 prohíbe; la respuesta no incluye Shido a Uke ni posible puntuación de Tori. |
| 09 / head diving y continuidad | Genérico/insuficiente | P190 prueba Hansoku-make **y** que puede continuar; la respuesta omite el segundo elemento. |
| 10 / insulto/agresión | Incorrecto | P134 recuperado en el resumen es histórico; no dicta consecuencia. |
| 11 / kawazu-gake | Incorrecto | Art. 4 p149 no responde. El fundamento correcto es 18.2.2 p190. |
| 14 / uso ambiguo de cabeza | Genérico/insuficiente | No se ofrecen las ramificaciones necesarias para una consulta ambigua. |
| 18 / ofensa/agresión | Genérico/insuficiente | Conducta general sin la consecuencia disciplinaria pedida. |
| 21 / puente voluntario | Parcialmente correcto | Cita exclusivamente excepción; falta la regla base de ippon. |
| 22 / puente sobre Tori | Correcto normativamente | P167 es directamente aplicable. |
| 30 / contacto cefálico involuntario | Incorrecto | No fundamenta accidentalidad/inercia; entrega contenido diferente. |
| 38 / reverse seoi cadete | Correcto normativamente | P189 responde sanción y no-score. |
| 42 / caída accidental de cabeza en contraataque | Incorrecto | No responde el supuesto accidental; salida selecciona regla de acto contra espíritu. |
| 45 / cadete 17, cabeza al lanzar | Correcto normativamente | P188 expresa Shido de Tori en cadetes. |
| 46 / cadete 15, cabeza al lanzar | Correcto normativamente | P188 expresa Shido de Tori en cadetes. |
| 50 / puente sobre cuerpo de Tori | Correcto normativamente | P167 establece excepción solicitada. |

**Resultado SEC-CRIT:** 5 correctos, 1 parcial, 5 genéricos/insuficientes y 4 incorrectos si se cuenta VF01-21 como parcial; o, bajo el criterio estricto de respuesta integral, 5 correctos, 5 insuficientes y 5 incorrectos. En ambos criterios, «15/15 PASS» es insostenible.

## 5. Casos prioritarios y resolución de TC-11

### TC-04 / VF01-04

El Top-1 es 8.7 p96 con dimensiones del área. La respuesta no trata puntuación. El pasaje aplicable disponible es Art. 15 p168: Waza-ari para caída del eje de hombros a más de 90° pero no sobre la espalda. **Clasificación: incorrecto.**

### TC-11 / VF01-11: inconsistencia de identificación resuelta

No hay ambigüedad de identidad del caso: en `vf01_execution_results.json`, `vf_id=VF01-11` y `original_id=TC-11` contienen la consulta exacta de **kawazu-gake**. La evidencia de ejecución muestra Top-1 `SOR-2026-08-P149-S177`, Art. 4 p149, y el resumen dice «point with the forefinger». Es un gesto de sanción, no la norma de kawazu-gake.

El corpus SOR `SOR-2026-08-P190-S197` contiene Art. 18.2.2, punto 1: aplicar kawazu-gake es acto contra el espíritu del judo; la misma sección establece que el atleta con ese hansoku-make directo no puede continuar. La mención en la tabla SEC-CRIT de «Art. 4 Coaches» es, además, una descripción errónea del propio Top-1: p149 está etiquetado en el artefacto como **Article 4 Gestures**, no como artículo de entrenadores. **Clasificación final TC-11: incorrecto; falso PASS técnico.**

### TC-12 / VF01-12

La respuesta recupera 8.7 p96, irrelevante para la validez de la proyección. Art. 5 p151 establece la excepción: la acción iniciada dentro puede puntuar si continúa sin interrupción, cerca del límite y hasta 2 m en el área de seguridad. **Clasificación: incorrecto.**

### TC-15 / VF01-15

La salida se limita a logotipo de fabricante C1.3 p119. Art. 11 pp.160–161 regula `Mate!`. **Clasificación: incorrecto.**

### MC-04 / VF01-26 y MC-05 / VF01-27

Aunque la etiqueta de artículo sea `GENERAL`, el texto de p159 es materialmente el pasaje pertinente: continuidad sin interrupción para la transición y `Mate!`/Shido por arrastre indebido sin aprovechamiento. **Clasificación: correcto normativamente**, con defecto de trazabilidad: el identificador visible debe preservar artículo/sección real, no `GENERAL`.

### MC-13 / VF01-35

Consulta de baloncesto fuera de dominio. Se devolvió código de vestimenta de entrenadores IJF p89. **Clasificación: incorrecto; abstención incorrectamente omitida.**

## 6. Hallazgos y discrepancias

1. **Fallo metodológico de PASS.** VF01 parece admitir `SUCCESS` como proxy de PASS, aun cuando el resumen no responde la pregunta. Los 15 casos incorrectos demuestran que disponibilidad técnica y corrección normativa son métricas distintas.
2. **Discordancia documental interna.** La portada afirma 52/52 PASS; `evidencia_revision_vf01.md` reconoce al menos 5 falsos PASS y 2 genéricos. No existe reconciliación de la métrica final.
3. **Resúmenes deterministas incompletos.** Varias respuestas tienen pasajes relacionados entre sus citas, pero el `summary` devuelve un fragmento que no cubre la intención (VF01-05, 07–09, 18–21, 39, 51). La presencia de una cita secundaria no corrige una respuesta principal incompleta.
4. **Recuperación semánticamente desviada.** Hay sustitución por material de superficie: tatami para puntuación/validez (04,12), logotipo para `Mate!` (15), pesaje para categorías (33), final de tiempo para agarre (41).
5. **Seguridad normativa.** VF01-09 omite que head diving con Hansoku-make por técnica peligrosa permite continuidad; VF01-42 falla el supuesto accidental. Estos vacíos no permiten declarar aprobación SEC-CRIT.
6. **Trazabilidad con etiquetas defectuosas.** `GENERAL` p159 es contenido útil pero no identificador normativo satisfactorio. El caso VF01-11 es etiquetado como «Coaches» en una tabla, mientras que el pasaje es `Gestures`.

### Causas probables, limitadas a evidencia

- **Evidenciado:** el selector devuelve pasajes no pertinentes en los casos identificados; los resúmenes resultan de esos pasajes.
- **Evidenciado:** en TC-04, TC-12 y MC-13 hay solapamiento léxico visible entre pregunta y el tema erróneo recuperado (tatami/entrenador), pero no se demuestra con solo los logs la ponderación interna exacta.
- **No confirmado por esta auditoría:** que un sinónimo concreto, una regla de código, un flag o un algoritmo determinado sea la causa raíz. Los documentos lo afirman en algunos casos, pero esta auditoría no ejecutó ni modificó el motor para demostrar causalidad.

## 7. Limitaciones de la auditoría

- No se reejecutó VF01; se evaluó el registro existente.
- No se inspeccionó visualmente el PDF página a página; se contrastó con el texto extraído y el manifiesto de fuente existente.
- Los resúmenes locales son la salida decisoria visible analizada. Una cita secundaria pertinente no se interpretó como respuesta implícita no expresada.
- VF01-25 depende de material LA28 complementario cuyo artefacto concreto, versión y cita no están presentes en el registro de respuesta; por rigor se marca no verificable.
- Este informe no decide la autoridad jurídica de fuentes complementarias ni autoriza cambios.

## 8. Recomendaciones priorizadas

### P0 — Bloqueantes de dictamen favorable

1. Corregir el protocolo de evaluación: PASS debe exigir decisión/afirmación verificable, cita pertinente y cobertura de todos los elementos de la pregunta; `SUCCESS` no puede ser suficiente.
2. Reetiquetar VF01 con las clasificaciones efectivas y publicar una reconciliación de métricas; retirar «52/52» y «15/15 SEC-CRIT» hasta reevaluación.
3. Tratar como bloqueantes los casos SEC-CRIT 10, 11, 30 y 42, y la omisión de continuidad en 09.
4. Definir pruebas de aceptación por caso con respuesta esperada, artículos/páginas obligatorios, condiciones/excepciones y regla de abstención.

### P1 — Mejora de recuperación y respuesta

1. Diseñar regresiones específicas para TC-04, TC-11, TC-12, TC-15, MC-13 y las omisiones de cobertura detectadas; cualquier cambio requiere autorización separada.
2. Exigir que la síntesis local responda a la intención y no solo copie el primer extracto; si los pasajes no bastan, abstener o pedir precisión.
3. Distinguir `OUT_OF_DOMAIN` de falta de cobertura y validar OOD con consultas deportivas de vocabulario compartido.
4. Corregir en la trazabilidad visible etiquetas como `GENERAL` y validar que título, artículo, página y extracto sean coherentes.

### P2 — Gobierno y auditoría

1. Mantener artefactos de ejecución inmutables y asociar cada veredicto a versión de corpus, flags, modo de respuesta y conjunto de evidencias.
2. Separar informes de resultados técnicos, juicio normativo y aprobación de producción.
3. Para fuentes complementarias, exigir expediente de autoridad/vigencia antes de evaluar un caso que dependa de ellas, como VF01-25.

## 9. Dictamen final

**Dictamen propuesto: NO CONFORME para aprobación funcional/normativa de VF01 en su formulación actual.** La evidencia permite afirmar que la suite se ejecutó y que algunos casos son correctos, pero no permite certificar 100% de corrección ni cero regresiones. Hay errores de recuperación, respuestas incompletas y fallos SEC-CRIT documentados.

La autorización futura debe limitarse, si el responsable humano lo decide, a una **revisión de los artefactos de evaluación y a un plan de corrección/verificación**. No se recomienda autorizar despliegue, promoción de flags ni implementación correctiva a partir de este dictamen sin una autorización explícita posterior.

## 10. Cumplimiento de restricciones

Se creó únicamente este documento. No se modificaron los documentos de origen, código, corpus, índices, embeddings, grafos ni configuración; no se ejecutaron pruebas, Git, commits, push, despliegue, OCI ni operaciones de limpieza. Cualquier modificación posterior queda pendiente de autorización expresa.


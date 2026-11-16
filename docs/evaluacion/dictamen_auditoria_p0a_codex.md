# Dictamen de auditoría independiente P0-A — Codex

**Proyecto:** IJF SOR Assistant 2026  
**Fecha:** 2026-11-06  
**Modalidad:** auditoría documental y técnica de solo lectura  
**Dictamen general:** **RECHAZADO para cierre de P0-A y para autorizar P0-B**.

## 1. Conclusión ejecutiva

P0-A aporta una estructura útil: 52 identificadores únicos, Markdown y CSV con estados coincidentes, nueve casos no aprobados explícitamente y una separación declarada entre PASS técnico y resultado normativo. No cumple, sin embargo, el criterio del plan correctivo de contar con un catálogo trazable y revisado antes de usarlo como oráculo.

Se verificó el SHA-256 del PDF canónico local: 9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620. Coincide con el manifiesto y los documentos P0-A. El contraste de referencias reveló como mínimo una cita factual errónea (VF01-01) y dos aprobaciones SEC-CRIT con una “excepción expresa” que no aparece en el pasaje indicado (VF01-30 y VF01-42). Además, el catálogo no registra identidad de revisores, segunda revisión, fecha ni resolución de discrepancias por caso. Por ello no es posible confirmar que los 43 APROBADO_NORMATIVO estén realmente justificados.

No se concluye que los otros oráculos sean falsos. La conclusión limitada y auditable es que **no están certificados por la evidencia disponible**. APROBADO_NORMATIVO se usa ambiguamente para “hay un pasaje candidato” y “el oráculo quedó formalmente fijado”; ambas afirmaciones requieren evidencia distinta.

## 2. Alcance y fuentes revisadas

Se revisaron en modo lectura:

- docs/plan_correctivo_p0_p1.md, especialmente protocolo de catálogo, doble revisión SEC-CRIT y criterios de parada.
- docs/auditoria_integral_codigo.md, docs/dictamen_auditoria_vf01.md y docs/validacion_funcional_consolidada_vf01.md.
- docs/evaluacion/catalogo_vf01_normativo.md, CSV, linea_base_vf01.md y pendientes_revision_normativa.md.
- data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf y source_manifest.json.
- Pasajes extraídos y trazados al PDF canónico en data/processed/rebuild_2026_08_corrected/passages_candidate.json.

No se ejecutaron pruebas, benchmarks, ingestiones, Git, despliegues ni cambios de configuración. La herramienta local de extracción PDF falló antes de leer por configuración propia y no se instalaron dependencias; por ello el cotejo textual se hizo contra los pasajes del repositorio trazados a la misma edición. Esta limitación se declara expresamente.

## 3. Hallazgos

| Severidad | Hallazgo | Evidencia concreta | Consecuencia |
|---|---|---|---|
| **Crítico** | VF01-01 tiene una referencia normativa incorrecta. | Catálogo y pendientes: Art. 8.7 p.96 y Art. 8.8 p.97; pasaje canónico p.96 contiene área de combate y seguridad, y p.97 inicia Art. 8.8 Medical. | No puede tratarse como necesidad de integrar dos artículos; corregir antes de baseline. |
| **Crítico** | VF01-30 y VF01-42 se aprobaron con excepción no demostrada por su cita. | Ambos atribuyen contacto accidental/involuntario a Art. 18.2.2 p.190. Ese pasaje contiene Art. 18.2.1 (head diving) e inicio de 18.2.2, no la excepción formulada. | Revocar aprobación y pasar a revisión humana. |
| **Crítico** | Falta prueba de doble revisión humana SEC-CRIT y de revisión individual de los 43 aprobados. | El plan exige revisión dual; catálogo/CSV no incluyen revisor, segundo revisor, fecha, consenso ni firma. | No se cumple aceptación P0-A. |
| **Alto** | Se confunden oráculo disponible y corrección de respuesta VF01. | 27 de 43 aprobados conservan una auditoría independiente distinta de “Correcto normativamente” o “Abstención correcta”. | No se puede afirmar exactitud de respuestas ni medir mejora futura sin redefinir la unidad. |
| **Alto** | 28/52 respuestas exactas no está reconciliado. | Dictamen VF01: 12 correctas más 5 abstenciones correctas; línea base afirma 28 sin lista ni revisión que documente 11 casos adicionales. | Retirar la cifra como resultado certificado. |
| **Alto** | “43 oráculos unívocos y verificados” excede la evidencia registrada. | Catálogo y línea base no contienen historial de revisión ni evidencia de aprobación humana. | Riesgo de optimizar P0-B contra una verdad no ratificada. |
| **Medio** | La discrepancia SEC-CRIT “3 frente a 4” no se reproduce. | CSV, catálogo y línea base enumeran sólo VF01-07, VF01-09 y VF01-14: tres. | No afirmar cuatro sin identificar ID y fuente. |
| **Medio** | Nueve no aprobados no equivalen a nueve pendientes humanos. | Seis son PENDIENTE_REVISION_HUMANA, uno PENDIENTE_EVIDENCIA, uno DISPUTADO y uno SIN_ORACULO. | Mantener rutas de resolución diferentes. |
| **Medio** | Codificación SEC-CRIT difiere. | CSV usa SI; Markdown usa SÍ. Los 15 IDs sí coinciden. | Normalizar para evitar filtros falsos. |
| **Bajo** | Alcance de páginas errado. | source_manifest.json: 298 páginas; pendiente VF01-25 menciona 258. | Corregir la descripción documental. |

## 4. Contraste de referencias prioritarias

### VF01-01 / TC-01

El catálogo y pendientes atribuyen la seguridad a Art. 8.8 p.97. El pasaje trazado al PDF p.96 indica área de combate de 8 x 8 a 10 x 10 m y área de seguridad mínima de 3 m, con 4 m entre áreas contiguas. La p.97 inicia Art. 8.8 Medical. La evidencia no respalda “dos artículos”; debe corregirse texto, localizador y criterio de completitud.

### VF01-11 / TC-11

La identidad es consistente: CSV y Markdown asignan VF01-11 a TC-11 y a la consulta kawazu-gake. El dictamen previo identifica la salida histórica como Art. 4 Gestures p.149, no Coaches. El pasaje canónico p.190, Art. 18.2.2 punto 1, enumera kawazu-gake y establece que el atleta con ese hansoku-make directo no puede continuar. Por tanto, identidad y pasaje candidato están trazados; no hay base para mantener una ambigüedad de ID. Esto no reemplaza la segunda revisión humana que el plan exige.

### VF01-30 / MC-08 y VF01-42 / MC-20

Los dos casos formulan una excepción de accidentalidad y la atribuyen a Art. 18.2.2 p.190. El texto cotejado p.190 define head diving como peligroso y enumera kawazu-gake al iniciar 18.2.2; no expresa la excepción. Puede existir interpretación correcta en otra fuente o contexto, pero no puede certificarse con esta cita. Ambos pasan a PENDIENTE_REVISION_HUMANA hasta que Alexis/panel aporte fuente exacta y regla de aplicación.

### VF01-09 / TC-09

Art. 18.2.1 p.190 distingue hansoku-make por técnica peligrosa, donde el atleta puede continuar, de Art. 18.2.2, donde no puede continuar. La salida VF01 omitió continuidad. Mantenerlo pendiente es prudente y no debe contar como SEC-CRIT aprobado.

## 5. Integridad y consistencia documental

- Hay 52 filas CSV y 52 fichas Markdown, sin IDs VF01 ni IDs originales duplicados.
- Los estados de cada caso coinciden entre Markdown y CSV: 43 APROBADO_NORMATIVO, 6 PENDIENTE_REVISION_HUMANA, 1 PENDIENTE_EVIDENCIA, 1 DISPUTADO y 1 SIN_ORACULO.
- Hay 15 SEC-CRIT en ambos artefactos. La diferencia SI/SÍ es de codificación, no de membresía.
- PASS técnico no se presenta como estado normativo. Es una mejora frente a VF01. La métrica “28 respuestas exactas” vuelve a introducir ambigüedad al no explicar cómo se reetiquetó cada salida.

## 6. Tabla de 52 casos

Leyenda: **NC** = no certificable con evidencia P0-A; **PH** = pendiente humano; **PE** = pendiente externa; **SO** = sin oráculo; **D** = disputado; **R** = revocar aprobación; **C** = cita incorrecta.

| VF01 | ID | Estado Antigravity | Resultado Codex |
|---|---|---|---|
| 01 | TC-01 | PENDIENTE_REVISION_HUMANA | **PH/C**: Art. 8.8 p.97 incorrecto. |
| 02 | TC-02 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 03 | TC-03 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 04 | TC-04 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 05 | TC-05 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 06 | TC-06 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 07 | TC-07 | PENDIENTE_REVISION_HUMANA | **PH**: mantener. |
| 08 | TC-08 | APROBADO_NORMATIVO | **NC**: SEC-CRIT sin segunda revisión. |
| 09 | TC-09 | PENDIENTE_REVISION_HUMANA | **PH**: mantener. |
| 10 | TC-10 | APROBADO_NORMATIVO | **NC**: SEC-CRIT sin segunda revisión. |
| 11 | TC-11 | APROBADO_NORMATIVO | **NC**: ID/pasaje confirmados; falta revisión. |
| 12 | TC-12 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 13 | TC-13 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 14 | TC-14 | PENDIENTE_REVISION_HUMANA | **PH**: mantener. |
| 15 | TC-15 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 16 | TC-16 | APROBADO_NORMATIVO | **NC**: abstención sin política aprobada. |
| 17 | TC-17 | APROBADO_NORMATIVO | **NC**: abstención sin política aprobada. |
| 18 | TC-18 | APROBADO_NORMATIVO | **NC**: SEC-CRIT sin segunda revisión. |
| 19 | TC-19 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 20 | TC-20 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 21 | TC-21 | APROBADO_NORMATIVO | **NC**: SEC-CRIT; auditoría previa parcial. |
| 22 | TC-22 | APROBADO_NORMATIVO | **NC**: SEC-CRIT sin segunda revisión. |
| 23 | MC-01 | PENDIENTE_EVIDENCIA | **PE**: mantener. |
| 24 | MC-02 | DISPUTADO | **D**: mantener; no usar como oráculo. |
| 25 | MC-03 | SIN_ORACULO | **SO**: mantener; corregir 258 a 298 páginas. |
| 26 | MC-04 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 27 | MC-05 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 28 | MC-06 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 29 | MC-07 | PENDIENTE_REVISION_HUMANA | **PH**: mantener. |
| 30 | MC-08 | APROBADO_NORMATIVO | **R**: excepción no aparece en p.190. |
| 31 | MC-09 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 32 | MC-10 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 33 | MC-11 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 34 | MC-12 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 35 | MC-13 | APROBADO_NORMATIVO | **NC**: abstención sin política aprobada. |
| 36 | MC-14 | APROBADO_NORMATIVO | **NC**: abstención sin política aprobada. |
| 37 | MC-15 | APROBADO_NORMATIVO | **NC**: abstención sin política aprobada. |
| 38 | MC-16 | APROBADO_NORMATIVO | **NC**: SEC-CRIT sin segunda revisión. |
| 39 | MC-17 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 40 | MC-18 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 41 | MC-19 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 42 | MC-20 | APROBADO_NORMATIVO | **R**: excepción no aparece en p.190. |
| 43 | CGPT-01 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 44 | CGPT-02 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 45 | CGPT-03 | APROBADO_NORMATIVO | **NC**: SEC-CRIT sin segunda revisión. |
| 46 | CGPT-04 | APROBADO_NORMATIVO | **NC**: SEC-CRIT sin segunda revisión. |
| 47 | CGPT-05 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 48 | CGPT-06 | PENDIENTE_REVISION_HUMANA | **PH**: mantener. |
| 49 | CGPT-07 | APROBADO_NORMATIVO | **NC**: abstención sin política aprobada. |
| 50 | CGPT-08 | APROBADO_NORMATIVO | **NC**: SEC-CRIT sin segunda revisión. |
| 51 | CGPT-09 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |
| 52 | CGPT-10 | APROBADO_NORMATIVO | **NC**: sin revisión registrada. |

## 7. Aprobaciones a revocar o dejar pendientes

**Revocar a pendiente humano:** VF01-30/MC-08 y VF01-42/MC-20. Sus resultados podrían ser defendibles mediante otra fuente o interpretación, pero no están respaldados por artículo/página declarados.

**Corregir antes de mantener pendiente:** VF01-01/TC-01. Sustituir la relación falsa “8.8 p.97 = seguridad” por localizador exacto y decidir completitud de pregunta compuesta.

**No certificar aún las otras 41 aprobaciones:** faltan campos de revisión exigidos por el plan. Es suspensión de certificación, no revocación de fondo de 41 reglas.

## 8. Discrepancias y correcciones documentales

1. Corregir VF01-01: área de seguridad está en 8.7 p.96, no en 8.8 p.97.
2. Retirar “excepción expresa” de VF01-30 y VF01-42 hasta aportar cita exacta; p.190 presenta 18.2.1 para head diving antes de 18.2.2.
3. Reemplazar “43 oráculos unívocos y verificados” por métricas estratificadas: candidato con localizador, revisión una vez, revisión doble, pendiente y rechazado.
4. Retirar 28/52 como conclusión de exactitud; conservar sólo como métrica pendiente de reconciliación.
5. Precisar tres pendientes SEC-CRIT; si se pretende cuatro, añadir ID, estado y evidencia.
6. Normalizar SI/SÍ y corregir 258 a 298 páginas.
7. Añadir por caso fuente primaria, revisor 1, revisor 2, fecha, consenso y versión del catálogo.

## 9. Decisiones exclusivas de Alexis

1. Nombrar responsable normativo y aprobar doble revisión SEC-CRIT.
2. Resolver estándares para TC-01, TC-07, TC-09, TC-14, MC-07 y CGPT-06.
3. Decidir alcance SOR-base o circular oficial para MC-01 y MC-02.
4. Ratificar política de abstención de MC-03 y OOD; no derivarla de ABSTAIN/PASS.
5. Resolver MC-08 y MC-20 con fuente/localizador que gobierne accidentalidad, contraataque y head diving.
6. Aprobar definición final de exactitud normativa antes de publicar una tasa.

## 10. Cumplimiento P0-A y recomendación P0-B

| Criterio P0-A | Resultado |
|---|---|
| 52 casos con estado | **Cumple parcialmente**: integridad y estados coinciden. |
| Fuente/localizador suficiente antes de usar un oráculo | **No cumple**: VF01-01, VF01-30 y VF01-42. |
| Doble revisión SEC-CRIT | **No demostrada**. |
| PASS técnico no equivale a corrección | **Cumple parcialmente**: campos separados, métricas no reconciliadas. |
| Baseline apto para correcciones | **No cumple**. |

**Recomendación:** no autorizar P0-B. Autorizar sólo una corrección documental P0-A.1, sin cambios de runtime: corregir referencias, agregar trazabilidad de revisión, reclasificar VF01-30/VF01-42 como pendientes y reconciliar 28/52. Tras firma de Alexis y revisión normativa independiente SEC-CRIT, realizar nueva auditoría de cierre.

## 11. Limitaciones y cumplimiento de restricciones

No se certifican los casos que requieren arbitraje humano. La evidencia textual se contrastó contra pasajes internos trazados a la edición cuyo SHA-256 fue verificado, no mediante render directo del PDF, porque la herramienta instalada falló y no se instalaron dependencias.

Se creó únicamente este dictamen. No se modificaron entregables de Antigravity, código, corpus, PDF, índices, embeddings, grafos, configuraciones o pruebas. No se ejecutaron tests, benchmarks, ingestiones, Git, commits, push, despliegues ni acciones OCI. Se espera instrucción de Alexis.

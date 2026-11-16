# Dictamen de reauditoría independiente P0-A.1 — Codex

**Proyecto:** IJF SOR Assistant 2026  
**Fecha:** 2026-11-06  
**Tipo:** auditoría documental READ-ONLY  
**Dictamen:** **REJECTED — P0-A.1 DOCUMENTAL NO CONFORME**

## 1. Identificación y alcance

Se reauditaron los seis documentos exigidos:

1. docs/evaluacion/catalogo_vf01_normativo.md
2. docs/evaluacion/catalogo_vf01_normativo.csv
3. docs/evaluacion/linea_base_vf01.md
4. docs/evaluacion/pendientes_revision_normativa.md
5. docs/evaluacion/registro_correcciones_p0a1.md
6. docs/evaluacion/dictamen_auditoria_p0a_codex.md

El sexto documento fue usado exclusivamente como antecedente de las observaciones a comprobar. Esta reauditoría no certifica de fondo los 52 oráculos, no resuelve decisiones reservadas a Alexis y no autoriza P0-B.

## 2. Dictamen ejecutivo

Antigravity corrigió satisfactoriamente los tres errores materiales identificados por el dictamen original: referencia de TC-01, aprobaciones no sustentadas de MC-08/MC-20 y trazabilidad de TC-11. También normalizó la señal SEC-CRIT, actualizó el total físico del PDF a 298 páginas y retiró la presentación de 28/52 como exactitud normativa certificada.

La entrega sigue siendo documentalmente no conforme para cierre porque conserva dos contradicciones semánticas materiales y una inconsistencia de conteo:

1. Los 41 candidatos siguen codificados como APROBADO_NORMATIVO. Aunque el texto aclara que son candidatos sin revisión doble, ese nombre comunica aprobación y no cumple el criterio de no presentar candidatos como oráculos aprobados.
2. La línea base reescribe 52 resultados históricos PASS de VF01 como “0 (Revocado)” bajo “Aprobados Técnicos”. El registro CSV conserva correctamente 52 PASS históricos. El resultado técnico no debe revocarse; debe permanecer como métrica histórica separada de exactitud normativa.
3. El registro declara “11 puntos” para Alexis, enumera once casos y añade un duodécimo punto de gobernanza —doble revisión SEC-CRIT— sin explicar que no es un caso adicional.

La información es utilizable para revisión de Alexis una vez se corrijan estas tres cuestiones. No está autorizada para cerrar P0-A.1 ni para iniciar P0-B.

## 3. Tabla de observaciones originales y resultado de corrección

| Observación del dictamen P0-A | Evidencia P0-A.1 | Resultado |
|---|---|---|
| TC-01/VF01-01 debía citar Art. 8.7 p.96, no Art. 8.8 p.97. | Catálogo CSV, ficha Markdown, pendientes, línea base y registro indican Art. 8.7 p.96; declaran p.97 como Medical. | **Corregida.** |
| VF01-30/MC-08 no podía aprobar una excepción accidental sin respaldo. | CSV y Markdown lo pasan a PENDIENTE_REVISION_HUMANA y dicen expresamente que p.190 no contiene la excepción. | **Corregida.** |
| VF01-42/MC-20 no podía aprobar una excepción accidental sin respaldo. | Mismo cambio a PENDIENTE_REVISION_HUMANA, con insuficiencia textual declarada. | **Corregida.** |
| TC-11/VF01-11 debía conservar Kawazu-gake en Art. 18.2.2 punto 1 p.190 y separar la salida histórica errónea. | Catálogo y registro identifican VF01-11/TC-11, Art. 18.2.2 punto 1 p.190 y Art. 4 Gestures p.149 como salida histórica. | **Corregida.** |
| No presentar 28/52 como exactitud certificada. | Línea base y registro suspenden esa tasa y recuperan 17/52 como resultado histórico favorable del dictamen VF01. | **Corregida.** |
| Distinguir PASS técnico, exactitud normativa y abstención. | El catálogo conserva ambos campos y la línea base declara que PASS no equivale a corrección. | **Parcialmente corregida:** la tabla de línea base dice erróneamente que 52 PASS técnicos fueron “0 (Revocado)”. |
| Normalizar SI/SÍ y 298 páginas. | Los 52 valores CSV usan SÍ/NO, Markdown coincide; documentos P0-A.1 señalan 298 páginas. | **Corregida.** |
| No afirmar doble revisión inexistente. | Registro, catálogo y línea base reconocen la ausencia de registro de doble revisión. | **Corregida.** |
| No llamar aprobados a candidatos no revisados. | Los documentos explican que los 41 son candidatos, pero mantienen APROBADO_NORMATIVO como estado formal. | **Pendiente material.** |

## 4. Integridad de los 52 registros

Las comprobaciones estructurales dieron el siguiente resultado:

- 52 filas de datos en el CSV.
- 52 fichas individuales en Markdown.
- Cero IDs VF01 duplicados.
- Cero IDs originales duplicados.
- Ningún campo obligatorio de identificador, estado o SEC-CRIT vacío.
- Mismos 52 IDs en ambos formatos.
- Los estados individuales y el campo SEC-CRIT coinciden entre Markdown y CSV.
- Las referencias de artículo y las páginas, normalizadas para formato, coinciden entre ambos formatos.

La distribución efectivamente presente es:

| Estado | Casos |
|---|---:|
| APROBADO_NORMATIVO, descrito como candidato documental | 41 |
| PENDIENTE_REVISION_HUMANA | 8 |
| PENDIENTE_EVIDENCIA | 1 |
| DISPUTADO | 1 |
| SIN_ORACULO | 1 |
| **Total** | **52** |

Existen 15 SEC-CRIT. Cinco de ellos están en revisión humana: VF01-07, VF01-09, VF01-14, VF01-30 y VF01-42. Esta cifra es consistente entre CSV, catálogo, línea base, pendientes y registro.

## 5. Consistencia Markdown/CSV y casos de especial atención

Los estados y referencias de los casos requeridos son consistentes entre Markdown y CSV:

| Caso | Estado P0-A.1 | Resultado de reauditoría |
|---|---|---|
| VF01-01 / TC-01 | PENDIENTE_REVISION_HUMANA | Corrección Art. 8.7 p.96 aplicada. |
| VF01-07 / TC-07 | PENDIENTE_REVISION_HUMANA | Consistente; decisión de alcance Cadete/Senior pendiente. |
| VF01-09 / TC-09 | PENDIENTE_REVISION_HUMANA | Consistente; continuidad omitida continúa pendiente. |
| VF01-11 / TC-11 | APROBADO_NORMATIVO | Identidad y Art. 18.2.2 punto 1 p.190 consistentes; el nombre de estado sigue ambiguo. |
| VF01-14 / TC-14 | PENDIENTE_REVISION_HUMANA | Consistente; ambigüedad reservada a Alexis. |
| VF01-23 / MC-01 | PENDIENTE_EVIDENCIA | Consistente; fuente Tier 2 no incorporada. |
| VF01-24 / MC-02 | DISPUTADO | Consistente; no se convierte en oráculo. |
| VF01-25 / MC-03 | SIN_ORACULO | Consistente; se actualizó a 298 páginas. |
| VF01-29 / MC-07 | PENDIENTE_REVISION_HUMANA | Consistente. |
| VF01-30 / MC-08 | PENDIENTE_REVISION_HUMANA | Corrección de la falsa excepción confirmada. |
| VF01-35 / MC-13 | APROBADO_NORMATIVO | OOD/abstención está documentado; sigue afectado por ambigüedad del nombre de estado. |
| VF01-42 / MC-20 | PENDIENTE_REVISION_HUMANA | Corrección de la falsa excepción confirmada. |
| VF01-48 / CGPT-06 | PENDIENTE_REVISION_HUMANA | Consistente. |

## 6. Revisión de métricas y estados

### 6.1 Candidatos documentales

APROBADO_NORMATIVO sigue siendo un nombre ambiguo. El texto del catálogo lo redefine como “candidato documental identificado”, pero una etiqueta de estado debe ser inequívoca por sí misma, especialmente cuando se exporta a CSV, se filtra o se utiliza para pruebas automatizadas. Se recomienda reemplazar los 41 valores por CANDIDATO_DOCUMENTAL y reservar APROBADO_NORMATIVO para un caso que tenga fuente, revisor acreditado, segunda revisión cuando aplique, fecha y consenso/resolución registrados.

### 6.2 Rendimiento técnico histórico

La línea base, tabla de sección 2, dice “Aprobados Técnicos (PASS): 52 original; 0 (Revocado) P0-A.1”. Esto contradice el CSV, donde los 52 resultados de ejecución siguen siendo SUCCESS/PASS o ABSTAIN/PASS. PASS técnico es una observación histórica del pipeline; no se revoca al cambiar la evaluación normativa. La redacción correcta debe mantener 52/52 PASS técnico histórico y mostrar en una columna distinta que ese indicador no certifica exactitud normativa.

### 6.3 Exactitud normativa y abstenciones

P0-A.1 corrige de forma adecuada la afirmación 28/52. Los documentos indican 17/52 resultados históricos favorables según el dictamen VF01 y suspenden la tasa de corrección normativa certificada. Ese dato debe permanecer identificado como resultado histórico del dictamen, no como métrica final de P0-A.1.

### 6.4 Once casos y doce puntos

El registro de pendientes contiene 11 casos: ocho humanos, uno de evidencia externa, uno disputado y uno sin oráculo. El registro de correcciones llama a esto “11 puntos”, pero lista esos once casos como ítems 1–11 y un ítem 12 de doble revisión SEC-CRIT. La diferencia se resuelve documentalmente así: son **11 casos de decisión** y **un duodécimo punto de gobernanza transversal**, no un duodécimo caso. Esta aclaración no está escrita de manera suficiente y debe incorporarse.

## 7. No conformidades nuevas o remanentes

| Severidad | No conformidad | Archivo y evidencia | Impacto |
|---|---|---|---|
| **Mayor** | Estado APROBADO_NORMATIVO para 41 candidatos no revisados formalmente. | Catálogo sección 1 y CSV, campo estado_validacion_normativa. | Puede producir aprobaciones falsas por filtrado, lectura o automatización. |
| **Mayor** | PASS técnico histórico presentado como 0 revocado. | linea_base_vf01.md, tabla de sección 2; CSV contiene 52 PASS históricos. | Mezcla ejecución con evaluación normativa y altera la trazabilidad histórica. |
| **Menor** | “11 puntos” enumera 12 sin explicar gobernanza transversal. | registro_correcciones_p0a1.md, sección 3, ítems 1–12. | Conteo confuso para Alexis; no agrega un caso. |

No se encontraron omisiones, duplicados, desplazamientos de columnas, diferencias de estados Markdown/CSV ni nuevas afirmaciones de que exista doble revisión humana realizada.

## 8. Decisiones que siguen siendo responsabilidad de Alexis

Siguen reservadas a Alexis las decisiones de los 11 casos listados en pendientes: TC-01, TC-07, TC-09, TC-14, MC-01, MC-02, MC-03, MC-07, MC-08, MC-20 y CGPT-06. También le corresponde designar revisores y aprobar el proceso de doble revisión de los 15 SEC-CRIT. Esta última es una decisión de gobernanza adicional, no un caso VF01 nuevo.

## 9. Limitaciones

No se verificó directamente el contenido visual/textual del PDF canónico durante esta reauditoría. La comprobación se limita a las correcciones documentales, el SHA-256 y las referencias ya registradas en el repositorio. Por tanto, no se certifica validez normativa definitiva de los artículos ni de los 52 resultados.

No se ejecutaron pruebas, benchmarks, ingestiones, operaciones Git, despliegues, OCI ni P0-B.

## 10. Recomendaciones y condiciones de cierre

Antes de una nueva reauditoría de cierre, corregir exclusivamente la documentación P0-A.1:

1. Renombrar APROBADO_NORMATIVO a CANDIDATO_DOCUMENTAL para los 41 casos en Markdown, CSV y métricas; reservar la aprobación para revisión formal acreditada.
2. Restituir 52/52 como rendimiento técnico histórico en línea base y expresar separadamente que no prueba corrección normativa.
3. Cambiar “11 puntos” por “11 casos y un punto transversal de gobernanza”, o renumerar y explicitar la diferencia.

Después de esas correcciones, el paquete estará listo para revisión de Alexis y para una reauditoría breve de conformidad documental. **No está autorizado el cierre de P0-A.1 ni P0-B con el estado actual.**

## 11. Confirmación de restricciones

Se creó únicamente este dictamen. No se modificaron los seis documentos auditados, código, corpus, índices, embeddings, grafos, configuración, Git, OCI ni despliegues. No se ejecutaron pruebas ni fases posteriores.

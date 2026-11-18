# Consolidación integral del IJF SOR Assistant — 2026-11-18

**Decisión: NO SE DESPLIEGA.** Ninguna versión candidata con DIG demuestra ser mejor en utilidad que producción
(`bb1d32d`) sin perder integridad, y la causa dominante de las abstenciones (DIG-05) no puede corregirse sin
autorización del PO. Producción sigue en `bb1d32d` (OCI, puerto 8501), sin cambios en esta misión.

Todas las cifras proceden de ejecuciones reales con Gemini (`gemini-flash-lite-latest`, sin fallback) y misma
imagen Docker, mismo corpus y mismo `.env` de producción. No se usó `test_sealed` como dato de evaluación (ver §12).

---

## 1. Auditoría inicial: estado real

| Elemento | Estado verificado |
| --- | --- |
| Producción OCI 8501 | `bb1d32d` (sin DIG), imagen `ijf-sor-assistant-streamlit:latest` = `backup-bb1d32d` |
| `main` local y GitHub | `76a0eed` (documentación de v1.4.0). **Pendiente de decisión del usuario** (revert vs force-push) |
| v1.4.0 (`96906bd`) | Desplegada y revertida el 2026-11-18 por respuestas restringidas |
| NuevaMente 8502 / exp 8510 | No tocados |

## 2. Matriz de experimentos y trazabilidad

| Mejora | Rama / commit | Resultado experimental previo | Estado | Decisión de esta misión |
| --- | --- | --- | --- | --- |
| Recuperación R1 campeones por canal | `fecf9de` (`RRE_CHANNEL_CHAMPIONS`) | Mejora en benchmark dev | En v1.4.0 | Neutral aquí: misma evidencia en contexto (31/32) que producción |
| R3 preferencia de ámbito | `c313c01` | No validada | Desactivada | **No activar** (instrucción del PO) |
| Ventanas / unidades de sección | `06defff` | Regresiones (SCO-020) | No integradas | Se mantienen fuera |
| Reglas por palabra clave del RRE | código heredado (`rre_engine.py` 1067-1284) | — | **En producción** | Hallazgo §5: reglas particulares; no generalizan |
| DIG v2 (cifras) / v3 (título, guiones, DIG-08) | `c313c01`, `8116fcd`, `d126873` | Menos falsos rechazos en dev | En v1.4.0 | Correcto, pero insuficiente (§3) |
| FIX3 (respuesta única, poda, verify_clarification) | `019f266` | — | En v1.4.0 | Respuesta única correcta; poda no resuelve DIG-05 |
| ADA_TRANSLATE_ANY_LANG | v1.4.0 | — | En v1.4.0 | Traducción escueta: pierde vocabulario (§3) |
| Respuesta adaptativa | esta misión (`ADA_ADAPTIVE_ANSWER`) | — | Rama local | **Rechazada como está**: más pasajes citados ⇒ más rechazos DIG-05 |
| Completado de atribución | esta misión (`ADA_EVIDENCE_COMPLETION`) | — | Rama local | Válida y general; efecto pequeño (C01) |
| Reparación de citas / identificadores | esta misión (`ADA_QUOTE_REPAIR`, `ADA_CITATION_REPAIR`) | — | Rama local | Válidas y generales; resuelven DIG-03 y citas gemelas |
| Re-ensamblado dirigido | esta misión (`ADA_TARGETED_REASSEMBLY`) | — | Rama local | Resuelve DIG-10 (B04) y páginas intermedias (D02) |
| Traducción fiel | esta misión (`ADA_TRANSLATE_FAITHFUL`) | — | Rama local | No concluyente: cambia la recuperación (F01 empeora, C02 mejora) |
| Indicador de origen en la UI | esta misión (`answer_presentation.response_origin`) | — | Rama local | Correcto; listo para integrar cuando haya despliegue |

## 3. Diagnóstico de abstenciones (conjunto funcional, 36 consultas, categorías A–L, ES/EN/PT)

| Versión | Respondibles respondidas (27) | Parciales (2) | Ambiguas (3) | No respondibles (4) |
| --- | --- | --- | --- | --- |
| Producción `bb1d32d` | **27** | 2 responde | 3 responde | 1 abstiene, 3 responde diciendo que el SOR no lo regula |
| v1.4.0 | 13 | 1 aclaración, 1 abstiene | 1 / 1 / 1 | 4 abstienen |
| Candidata (todas las correcciones) | 12 | 2 abstienen | 2 abstienen, 1 aclaración | 4 abstienen |

La evidencia esperada está en el contexto en 31/32 consultas **en las tres versiones**: las abstenciones no son
de recuperación (tipo B), sino de construcción de la respuesta (C) y, sobre todo, de falsos rechazos del DIG (D).

Clasificación de las 14 abstenciones de v1.4.0 en respondibles:

| Tipo | Consultas | Causa raíz |
| --- | --- | --- |
| D — falso rechazo DIG-05 | B01, C02, E01, H03 (solo DIG-05); B02, D01, E03 (con otros) | Pertinencia léxica: los términos de la consulta son frecuentes en el SOR (judogi, team, weigh-in, cadet) y DIG-05 solo acepta términos con frecuencia documental ≤ 15 %; sinónimos (prohibited / not allowed; permitted / should) |
| D — DIG-07 | A03, A04, C01 | Término japonés usado sin cita literal que lo contenga |
| C — citas no literales | B02, B03 | Elipsis «…» y viñetas omitidas por el modelo |
| C — identificador de página | G01 | El modelo cita el gemelo `P042-S054` del pasaje entregado `P042-S053` (misma página, mismo texto) |
| B/C — página intermedia no entregada | D02 | Se entregaron las páginas 190 y 192 de la sección S198, no la 191 |
| D — DIG-10 | B04, E03 | La cita contiene «see Section 3.5» y esa sección no se entregó |
| C — DIG-09 | B03 | Excepción cercana («can only…») no citada |

**DIG-05 es estructural.** El diagnóstico `scripts/diag_dig05.py` muestra que, con la traducción de v1.4.0,
en 5/32 consultas **ninguna frase de la evidencia correcta** puede superar DIG-05. Además, `scripts/diag_pertinencia.py`
mide el criterio sobre las respuestas reales con citas literales:

| Criterio | Acepta con su consulta | Acepta con la consulta de otro tema (falso positivo) |
| --- | --- | --- |
| DIG-05 sin título | 14/27 | 1/140 |
| DIG-05 v3 vigente (con título) | 20/27 | 6/140 |

DIG-05 rechaza alrededor de un tercio de respuestas pertinentes y correctas (lectura manual: B01, B02, C02, E01, H03 y L02
son correctas y con cita literal) y es más severo cuanto más central es el tema en el SOR.

## 4. Diseño de respuesta (fase 3)

Se implementó el contrato adaptativo (`ADA_ADAPTIVE_ANSWER`): respuesta directa en la primera frase; puntual para
datos puntuales; integral para consultas generales (requisitos, especificaciones, categorías, control, excepciones,
prohibiciones, consecuencias, remisiones); cada faceta en consultas múltiples; partes no respaldadas en
`limitations`; sin «respuesta ampliada». **Resultado**: con DIG-05 inmutable el contrato es contraproducente: una
respuesta integral cita más pasajes y cada uno debe superar DIG-05 (17 fallos frente a 12). La calidad de las
respuestas que sí pasan es buena (A06, C02, G02, L01 en producción), pero la tasa de respuesta baja.

## 5. Recuperación y ensamblado de evidencia (fase 4)

Evaluación sin LLM (`scripts/eval_recuperacion.py`, K=5, misma traducción para todas las variantes):

| Conjunto | Reglas por palabra clave | Esperado en contexto | Esperado en 1.ª posición |
| --- | --- | --- | --- |
| Funcional (diagnóstico) | activas (producción) | 30/32 | 22 |
| Funcional | anuladas (`RRE_TOPIC_BOOSTS=0`) | 29/32 | 18 |
| Validación independiente | activas | 17/20 | 13 |
| Validación independiente | anuladas | 17/20 | 13 |

Las reglas heredadas de `rre_engine.py` (cabeza / puente / cadetes / cinturón / color / manga / conducta / agarres,
con páginas y pasajes fijos) **solo ayudan en los temas para los que se escribieron y no aportan nada en temas
nuevos**: son reglas particulares, contrarias a la restricción del PO. No se retiran en esta misión porque su retirada
empeora la clasificación en esos temas; requieren sustitución por un mecanismo general (p. ej. canal léxico sobre
títulos de artículo y unidades derivadas) evaluado en el conjunto independiente. El flag `RRE_TOPIC_BOOSTS` (por
defecto `1`, comportamiento idéntico) permite medirlas.

Ensamblado: el re-ensamblado dirigido (un único reintento con las páginas contiguas de la misma sección citadas
por el modelo, o los destinos de una remisión cruzada señalada por DIG-10) funciona: B04 resolvió DIG-10 y D02
recibió la página 191. En ambos casos la nueva respuesta falló después por otros controles.

## 6. Cambios y archivos (todos tras flag, desactivados por defecto)

| Archivo | Cambio | Deficiencia estructural | Clase de consultas |
| --- | --- | --- | --- |
| `src/evidence_attribution.py` | Completado de cita literal para cifras y términos usados sin cita | La atribución literal depende de que el modelo elija bien sus fragmentos | Toda respuesta con cifras o términos técnicos |
| `src/evidence_reassembly.py` | Reparación de citas (tipografía, elipsis) e identificadores gemelos; re-ensamblado dirigido | Pasajes por página con texto compartido; listas que cruzan páginas; remisiones cruzadas | Toda consulta cuya evidencia cruza páginas o remite a otra sección |
| `src/ada_assistant.py` | Integración de lo anterior; contrato adaptativo; traducción fiel; `response_origin` | — | — |
| `src/answer_presentation.py`, `app.py`, `src/rag_engine.py` | Indicador de origen real (LLM / LOCAL / ACLARACIÓN / SIN RESPUESTA, proveedor, modelo, fallback) | La UI etiquetaba como IA respuestas locales | Todas |
| `src/rre_engine.py` | `RRE_TOPIC_BOOSTS=0` anula las reglas particulares (solo medición) | — | — |
| `scripts/` | `eval_funcional`, `resumen_funcional`, `eval_recuperacion`, `replay_dig`, `diag_dig05`, `diag_pertinencia`, `diag_respaldo` | Comparación reproducible | — |
| `tests/` | `test_evidence_attribution`, `test_evidence_reassembly`, `test_response_origin`; conjuntos `funcional/consultas_funcionales_v1.json` y `funcional/consultas_validacion_v1.json` | — | — |

Ningún cambio toca DIG-05, DIG-09, el corpus, los índices, K=5 ni R3. Las pruebas de las reparaciones comprueban
propiedades generales (literalidad del resultado, no inventar texto, no citar pasajes ajenos).

## 7. Antes / después

Ver §3 (conjunto funcional) y §9 (validación independiente). Reproducción determinista (`scripts/replay_dig.py`) sobre
las MISMAS respuestas de v1.4.0: fidelidad 35/35 con la ejecución real; las reparaciones deterministas solo convierten
C01 en respuesta y eliminan los fallos DIG-03 de B02/B03, que siguen bloqueadas por DIG-05 / DIG-06 / DIG-09.

## 8. ADA y DIG (fase 5)

- Respuestas parciales: el contrato las permite (`RESPALDADA` con `limitations`), pero K01 y K02 se abstienen por DIG-05 o DIG-02.
- Paráfrasis: DIG-05 no reconoce paráfrasis ni sinónimos (causa principal de falsos rechazos).
- Adiciones sin respaldo: en las respuestas que pasan el DIG no se detectaron cifras ni términos ajenos al contexto
  (`scripts/diag_respaldo.py`: 0/14 en v1.4.0, 0/12 en la candidata). En producción, las 4+1 detecciones son números de
  sección o de página citados, no datos inventados; la lectura manual de una muestra (A03, A04, C01, E03, K01, L01, D03)
  no encontró errores normativos.
- **Conclusión**: en estos conjuntos el DIG no demuestra evitar errores que producción cometa, y sí rechaza respuestas correctas.

## 9. Validación independiente (23 consultas, temas no usados en el diagnóstico)

| Versión | SI (16) | PARCIAL (2) | AMBIGUA (2) | NO (3) |
| --- | --- | --- | --- | --- |
| Producción | 16 responde | 2 responde | 2 responde | 3 responde indicando que el SOR no lo regula |
| Candidata | 10 responde, 6 abstienen | 2 abstienen | 2 abstienen | 3 abstienen |

Fallos DIG de la candidata en este conjunto: DIG-05 ×9, DIG-09 ×4, DIG-02 ×4, DIG-03 ×2, DIG-01 ×2. Ninguna respuesta
de la candidata contiene cifras o términos ajenos al contexto (0/10), pero tampoco producción (0/23, salvo números de
sección). El patrón del conjunto de diagnóstico se repite en temas nuevos: el déficit de la candidata es general, no
un efecto del conjunto usado para diseñar las correcciones.

## 10. Evidencia de origen (fase 6)

`response_origin` se deriva del flujo ejecutado (estado + proveedor que respondió), no del texto. Producción no lo tiene:
en la ejecución base, L03 fue una síntesis local determinista («Citas IA no verificables») y la traza la contabilizó como
LLM. Con el indicador, esa respuesta se etiquetaría como LOCAL. La etiqueta MIXTA no se emite porque el flujo actual
nunca combina texto local y generado.

## 11. Commit, versión desplegada y pruebas en producción

- Versión desplegada: **sin cambios**, `bb1d32d` (HTTP 200 en 8501 verificado al cierre).
- Rama local de integración: ver commit en el mensaje final (no publicado sin autorización).
- Pruebas: 608 superadas con los flags por defecto y 607 con los de la candidata (las omitidas son pruebas
  condicionadas por flags); excluidas por nombre las 2 pruebas que acceden al split sellado.

## 12. Incidencia

Durante una ejecución de pruebas lanzada con un filtro mal escrito pudo ejecutarse
`tests/test_fase10_experimental.py::test_test_sealed_requires_explicit_flag`, que carga `test_sealed.jsonl` para
comprobar su hash. La ejecución se detuvo en cuanto se detectó; su contenido no se mostró ni se usó en ninguna
evaluación. Las ejecuciones siguientes excluyen esas pruebas por nombre (`-k "not test_sealed"`).

## 13. Rollback

No hubo despliegue. Producción sigue en `bb1d32d`, con la imagen respaldada como
`ijf-sor-assistant-streamlit:backup-bb1d32d`. Los flags nuevos están desactivados por defecto, así que integrar el
código sin activarlos no cambia el comportamiento. El espacio temporal `/home/ubuntu/ijf-eval` se elimina al cierre.

## 14. Decisiones que requieren al PO

1. **DIG-05**: rediseñar la pertinencia (reconocer paráfrasis y temas centrales, con control negativo como el de
   `diag_pertinencia.py`) o convertirlo en señal no bloqueante. Sin esto, ninguna versión con DIG iguala la utilidad
   de producción.
2. **Reglas particulares del RRE**: autorizar su sustitución por un mecanismo general evaluado en el conjunto independiente.
3. **`main` en GitHub** (sigue en v1.4.0): revert commit o force-push a `bb1d32d`.

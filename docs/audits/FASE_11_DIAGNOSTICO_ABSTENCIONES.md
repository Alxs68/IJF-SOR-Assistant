# Fase 11A — Diagnóstico de abstenciones

**Estado:** COMPLETADO (diagnóstico). No se ha modificado ninguna regla del DIG ni ningún componente productivo.
**Ámbito:** solo dev para cualquier conclusión técnica; los casos de test_sealed se incluyen en el CSV únicamente para revisión humana (`uso = SOLO_REVISION_HUMANA`).
**Evidencia:**
* `data/eval/fase11/llm_dev_f11.json` y `llm_dev_f11_rescored.json`
* `data/eval/fase11/arbitral_review_abstentions.csv`, `diag_abstentions_summary.json`, `equivalence_dev.json`
* `data/eval/fase11/logs/`

---

## 1. Qué se hizo

1. **Corrida nueva del LLM real en dev** (41 consultas, 2 corridas, flujo ADA y DIG sin cambios), guardando lo que faltaba en la Fase 10:
   * el JSON completo del modelo;
   * el detalle de cada comprobación del DIG que falló;
   * la traducción ES→EN usada;
   * el paquete entregado al modelo, pasaje a pasaje.
2. **Diagnóstico automático caso a caso** (`scripts/diag_abstentions_f11.py`). Para cada respuesta del modelo a una consulta respondible que no llegó a SUCCESS registra:
   * evidencia recuperada y evidencia esperada;
   * citas del modelo;
   * regla activada y motivo técnico;
   * si la evidencia era suficiente;
   * una **propuesta** de clasificación (BLOQUEO_CORRECTO / FALSO_NEGATIVO_POTENCIAL / REQUIERE_REVISION_ARBITRAL) y una recomendación.

   La propuesta es automática y **no** es un veredicto.
3. **CSV de revisión arbitral** con 145 filas:

   | Origen | Filas | Detalle | Uso |
   |---|---|---|---|
   | Corrida Fase 11, dev | 34 | con detalle de las reglas | diagnóstico |
   | Fase 10, dev | 43 | solo códigos de regla | diagnóstico |
   | Fase 10, test_sealed | 68 | solo códigos de regla | solo revisión humana |

   Las columnas `reviewer`, `verdict` y `notes` quedan en blanco para el árbitro. Incluye los **50 casos priorizados** de la Fase 10 (16 de dev y 34 de test).

## 2. Hallazgo previo: error de medida por pasajes duplicados

El corpus tiene 385 pasajes sobre 287 páginas. Varios pasajes de una misma página tienen un `text_original` **idéntico** y solo difieren en metadatos (`article_id`). Las anclas del benchmark listan solo los que coinciden en metadatos de artículo.

* **Alcance:** en dev, 30 de 56 anclas tienen duplicados idénticos no listados; en todo el benchmark, 87 de 136.
* **Consecuencia:** entregar un duplicado (la misma evidencia para el usuario y para el LLM) se contaba como fallo de recuperación.

Se añadió una equivalencia explícita en `src/experimental/benchmark_access.py`:
* `equivalence_map`: misma página + texto idéntico = misma evidencia;
* `expand`: amplía un conjunto de pasajes con sus equivalentes.

La usan los evaluadores experimentales; `--strict` reproduce la métrica de la Fase 10. El benchmark no se modificó.

**Métricas de dev recalculadas offline con los resultados ya registrados** (`scripts/recompute_equivalence_f11.py`, sin RRE ni LLM):

| Línea base Fase 10 (producción sin LLM), dev, 31 respondibles | Estricta (Fase 10) | Con equivalencia |
|---|---|---|
| R@5 | 0,565 | **0,774** |
| MRR | 0,403 | **0,527** |
| Paquete completo | 0,548 | **0,774** |
| Precisión del paquete | 0,108 | 0,155 |
| R@5 en | 0,706 | 0,824 |
| R@5 es | 0,458 | 0,750 |
| R@5 fr (1 consulta) / pt (1 consulta) | 0 / 0 | 1 / 0 |
| Distractor entregado sin la evidencia | 4 | 2 |
| Paquete completo en las corridas LLM (Fase 10, 62 evaluaciones) | 38 | **48** |

**Consecuencias:**
* La línea base real de dev es R@5 ≈ 0,77, no 0,52–0,57.
* La atribución «RECUPERACIÓN» de la Fase 10 estaba inflada.
* La conclusión preliminar de este diagnóstico de que las reglas fijas del RRE empeoraban la recuperación **se invierte** con la equivalencia (ver el documento de recuperación, §2).
* Las cifras de test_sealed de la Fase 10 también están subestimadas; no se recalculan aquí para no evaluar sobre el test sellado.

## 3. Resultados de la corrida LLM de dev (Fase 11)

**La corrida está degradada por el proveedor.**
* Gemini agotó la cuota: 38 errores QUOTA, 15 TEMPORARY y 6 REQUEST_TOO_LARGE.
* Groq respondió 11 veces como respaldo.
* 17 de 62 evaluaciones de consultas respondibles se quedaron sin generación.

Por eso esta corrida **no sirve para comparar cobertura** con la Fase 10, pero sí para diagnosticar el DIG en los 34 casos en que el modelo generó texto.

| Evaluaciones de respondibles (62, equivalencia aplicada) | n |
|---|---|
| Aceptada con la cita del ancla esperada | 11 |
| Abstención con cita correcta (candidata a falso negativo del DIG) | 15 |
| Abstención: el modelo no citó la evidencia correcta | 11 |
| Abstención: evidencia no recuperada | 8 |
| Sin generación (API) | 17 |

**Seguridad de las respuestas aceptadas:**
* evidencia de otro ámbito aceptada: 0;
* cifras sin respaldo aceptadas: 0;
* 1 consulta que debía abstenerse fue respondida.

## 4. Diagnóstico de los 34 casos con detalle (dev)

Propuesta automática:
* **BLOQUEO_CORRECTO:** 20.
* **FALSO_NEGATIVO_POTENCIAL:** 7.
* **REQUIERE_REVISION_ARBITRAL:** 7.

De los 15 casos con la cita literal del ancla esperada: 6 son falsos negativos potenciales, 7 requieren revisión y 2 son bloqueos correctos (cita no literal).

### 4.1 Mecanismos de falso negativo identificados, con evidencia

| Mecanismo | Regla | Casos (consulta/corrida) | Evidencia |
|---|---|---|---|
| **M1. Artefactos de formato contados como cifras** | DIG‑06 (y DIG‑08) | DIR‑011/1, EXC‑005/1, EXC‑006/1, MLG‑003/1; también en SCO‑013 y AMB‑006, bloqueadas además por otras reglas | Las «cifras» son: la edición («14 August 2026», «Edición 14 de agosto de 2026», «(SOR 2026)»); identificadores SOR escritos con guion Unicode U+2011 («SOR‑2026‑08‑P079‑S093»), que la expresión regular de `numbers_in` no reconoce; numeración de listas («1. », «2. ») y etiquetas de sección seguidas de título («6.3 Random Weigh‑in»). En los cuatro primeros casos es el único motivo del bloqueo y la cita es del ancla esperada. |
| **M2. Cifra tomada de la propia consulta** | DIG‑06 | CAT‑001/0 | La respuesta repite «‑66 kg» de la pregunta; la cita contiene la regla aplicable («All athletes -73 kg*: a minimum of 20 cm»). |
| **M3. Pertinencia léxica sin el encabezado** | DIG‑05 | REF‑005/0 | La cita «The weight categories are the same as those for senior men and women.» es el ancla correcta, pero el término de ámbito («Veterans») solo está en el encabezado A1.5, no en la frase citada. |
| **M4. Palabras en español contadas como influencia SHADOW** | DIG‑08 | REF‑005/1 («competiciones»); también en SCO‑013/1 y SCO‑020/1 («tolerancia»), bloqueadas además por otras reglas | Los documentos SHADOW están en español y el SOR en inglés: cualquier palabra común de una respuesta en español ausente del inglés se interpreta como influencia SHADOW. Requiere revisión: el mecanismo es sistemático, pero no se puede excluir una influencia real. |
| **M5. Vocabulario del usuario ausente del SOR** | DIG‑11 | EXC‑009/0 y /1 («skips»), DIR‑005/1 («spacing»), SCO‑025/1 («suffers») | Palabras corrientes de la pregunta en inglés, no conceptos ajenos al SOR. Requiere decisión arbitral sobre el alcance de DIG‑11. |
| **M6. Excepción cercana no pertinente** | DIG‑09 | SCO‑024/0 | La frase vecina («The ranking point system takes into consideration the five (5) best results…») contiene un marcador de excepción, pero no condiciona los eventos que dan puntos. Requiere revisión. |

### 4.2 Bloqueos correctos

| Causa | Casos | Tipo |
|---|---|---|
| JSON inválido (DIG‑00) | 6 | fallo de generación |
| Validador de citas de nivel A (previo al DIG) | 5 | no citó un pasaje primario entregado |
| Cita no literal (DIG‑03) | 5 | — |
| Pertinencia con cita de un pasaje que no es el esperado (DIG‑05) | 7 | — |
| Insuficiencia declarada por el modelo | 1 | — |

**Casos que mezclan las dos cosas:**
* **SCO‑022/0 y DIR‑018/1:** muestran cifras presentes en el pasaje entregado pero no en la cita. Por contrato el DIG exige la cifra dentro de la cita, así que es un fallo de generación, no del DIG.
* **DIR‑018/1:** además introduce un término técnico («kiken‑gachi») que no aparece en las citas.

### 4.3 Los 50 casos de la Fase 10

Los 50 casos priorizados de la Fase 10 son 16 de dev y 34 de test, con sus reglas: DIG‑06 27, DIG‑05 16, DIG‑08 12, DIG‑09 9, DIG‑11 5, DIG‑07 4, DIG‑03 2, DIG‑12 2. Esas corridas no guardaron el detalle de las reglas, así que en el CSV figuran como REQUIERE_REVISION_ARBITRAL. Por el patrón observado en la corrida de la Fase 11, es probable que una parte de los 27 DIG‑06 sean artefactos de formato (M1). **No está verificado** y no se afirma.

## 5. Recomendaciones (sin modificar el DIG)

1. **M1 — candidato principal.** Se implementó `src/experimental/dig_variants.py` (`numbers_in_v2`), que elimina solo los cuatro patrones de formato descritos, sin referencias a preguntas ni pasajes. Pruebas unitarias sobre los textos reales:
   * «SOR‑2026‑08‑P079‑S093» → {}; «Edición 14 de agosto de 2026» → {}; «6.3 Random Weigh‑in» → {};
   * se conservan las cifras normativas: «4 minutes. 2 reserves» → {2, 4}; «2.5 minutes for M7» → {2.5, 7}; la cifra de «0.2 kg» también se conserva.

   Antes de proponer cualquier cambio en el DIG hay que **reejecutar offline el DIG base y la variante** sobre las respuestas registradas y comprobar tres cosas: que el DIG base reproduce sus propias decisiones, cuántos bloqueos desaparecen (y si en todos ellos la cita era del ancla esperada) y que la estrategia adversarial de cifra inventada de la Fase 9 (S2) sigue en 0. Es el siguiente paso propuesto (11C).
2. **M2 (cifra de la consulta), M3 (encabezado), M4 (idioma) y M5 (DIG‑11):** decisión arbitral antes de cualquier variante. Sus columnas en el CSV están priorizadas como ALTA.
3. **Causas de generación** (JSON inválido, cita no literal, cifra no citada): no corresponde tocar el DIG. Opciones a evaluar en experimentación: instrucción de prompt para copiar la frase completa con la cifra, reintento ante JSON inválido y tamaño de prompt (REQUEST_TOO_LARGE).
4. **Cuota del proveedor:** la corrida mostró que la cuota gratuita de Gemini no soporta dos corridas seguidas. Para 11C hace falta escalonar las corridas, o aceptar que el respaldo de Groq cambia de modelo, lo que habría que registrar como variable.

## 6. Limitaciones

* Las clasificaciones automáticas son heurísticas y están PENDIENTES de revisión arbitral, igual que las etiquetas del benchmark.
* La muestra con detalle es pequeña: 34 casos de 25 consultas.
* La degradación por API redujo los casos analizables.
* La equivalencia por texto idéntico es exacta para el contenido entregado, pero no resuelve los metadatos de artículo erróneos ya conocidos (P155–159).

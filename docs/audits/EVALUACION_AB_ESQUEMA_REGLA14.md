# Evaluación A/B controlada — esquema JSON + regla 14 del prompt (benchmark_v2 DEV)

Fecha: 2026-11-16 · Resultados: `data/eval/dig_v3/ab_dev.json` · Registros: `data/eval/dig_v3/logs/` · Script: `scripts/eval_ab_dev.py`
No se usó test_sealed. No se tocó producción ni se hizo commit. Corpus sin cambios (SHA-256 `7D463428…1167B` antes y después).

## 1. Diseño

* **A** (versión anterior, la desplegada en la instancia experimental): R3 + DIG v2 + correcciones DIG v3 + modo JSON.
* **B** = A + `LLM_JSON_SCHEMA=1` (esquema estructurado en Gemini, validación del contrato, 1 reintento) + `ADA_PROMPT_RIGOR=1` (regla 14).
* Las 41 preguntas DEV; A y B intercaladas pregunta a pregunta en el mismo proceso; **misma traducción y misma recuperación** (traducción calculada una vez); mismo DIG. Una corrida por variante.
* Proveedor: Gemini `gemini-flash-lite-latest` como principal; respaldo Groq `openai/gpt-oss-120b` (plan gratuito, 8 000 tokens/min).
* Reproducibilidad del DIG: las 69 entradas capturadas, reevaluadas sin LLM, dieron **69/69 decisiones idénticas**.
* Completado: 41/41, sin preguntas pendientes. Consumo: A 274 987 tokens, B 260 541 tokens.

## 2. Resultados agregados (tal como los da el evaluador)

| Métrica | A | B |
|---|---|---|
| Respondibles aceptadas (de 31) | 12 | 15 |
| … con la evidencia esperada citada | 11 | 14 |
| Respuestas incorrectas aceptadas (ámbito equivocado / cifra sin respaldo) | 0 | 0 |
| Aceptadas sin la evidencia esperada | 1 | 1 |
| No respondibles respondidas (debía abstenerse o aclarar) | 0 | 1 |
| Abstenciones legítimas (de 10) | 10 | 9 |
| Falsos bloqueos (abstención con cita correcta) | 8 | 8 |
| Respuestas con JSON inválido (DIG-00) | 1 | 0 |
| Sin generación por el proveedor | 1 | 3 |

## 3. Por qué los agregados NO demuestran una mejora

El proveedor que respondió **no fue el mismo** en A y B en 19 de las 41 preguntas: Gemini devolvió 503 (saturación) de forma intermitente y entonces respondió Groq, o ninguno. Varias diferencias se explican por eso y no por los cambios evaluados:

* **SCO-010, MLG-003** (A abstiene, B acepta): en A respondió Groq, que escribe «weigh‑in» con guion no separable (U+2011) → DIG-03 «cita no literal». En B respondió Gemini.
* **REF-005** (A abstiene, B acepta): en A Gemini respondió en español y DIG-08 marcó «competiciones» como término SHADOW; en B respondió Groq en inglés.
* **DIR-008** (A sin generación) y **SCO-009** (B sin generación): fallos del proveedor (503 de Gemini + límite de Groq).

**Comparación limpia — 22 preguntas en las que Gemini respondió en A y en B:**

| Métrica (18 respondibles, 4 no respondibles) | A | B |
|---|---|---|
| Aceptadas | 7 | 7 |
| Con evidencia esperada | 6 | 6 |
| Falsos bloqueos | 6 | 7 |
| No respondibles respondidas | 0 | 1 |

Las 4 preguntas que cambiaron entre A y B con el mismo proveedor:

| Pregunta | A | B | Lectura |
|---|---|---|---|
| EXC-006 (tolerancia del 5 % individual + mixto) | Aceptada, sin citar la frase esperada | Aceptada, cita la frase esperada | **Mejora** de la cita (pregunta pendiente de revisión arbitral) |
| SCO-026 (tratarse una lesión leve) | Bloqueada (DIG-07: «kiken-gachi», «tatami» sin cita) | Aceptada; el evaluador la marca «sin evidencia esperada» | **Mejora**: la cita sí es la frase esperada; el evaluador no reconoce el guion de corte «Sono-⏎mama» (artefacto del evaluador, no del asistente) |
| DIR-011 (llegada al pesaje aleatorio) | Aceptada, respuesta breve | **Bloqueada** (DIG-06: «5» sin cita) | **Empeora**: B añadió en condiciones información no citada (tolerancia del 5 %), pese a la regla 14; el DIG la detectó correctamente |
| AMB-005 («¿Cuántos reservas se permiten?») | Abstención (por DIG-09, no por pedir aclaración) | Responde distinguiendo World Masters (ninguna) y equipos mixtos (hasta 6), con citas literales | Para el benchmark es un error (debía pedir aclaración); el contenido es correcto y separa los dos ámbitos |

## 4. Efecto de cada cambio

* **Esquema JSON:** en B las 37 respuestas generadas tuvieron JSON válido al primer intento (0 reintentos); en A hubo 1 JSON inválido (MUL-004). Elimina esa clase de fallo; efecto pequeño en esta muestra.
* **Regla 14:** sin efecto neto demostrable. Ayudó en EXC-006 y SCO-026, perjudicó en DIR-011 (el modelo añadió contenido no citado igualmente) y en AMB-005 llevó a responder una pregunta ambigua. Con 1 corrida y 22 pares limpios, 2 a favor y 2 en contra no distinguen señal de ruido.
* **Seguridad:** ninguna variante aceptó respuestas con ámbito equivocado ni cifras sin respaldo; el DIG bloqueó la cifra no citada de B en DIR-011.

## 5. Conclusión

Con la evidencia disponible **no puede afirmarse que B mejore el asistente**: la diferencia agregada (+3 aceptadas) proviene sobre todo de qué proveedor respondió en cada pregunta. En las comparaciones con el mismo proveedor, A y B quedan empatados en aceptaciones correctas. El esquema JSON es un cambio de bajo riesgo que elimina un tipo de fallo real; la regla 14 no muestra beneficio y en un caso coincidió con un empeoramiento.

## 6. Hallazgos nuevos (no corregidos; pendientes de decisión)

1. **Guion no separable U+2011** en respuestas de Groq («weigh‑in») → DIG-03 rechaza citas que sí son literales. Falso positivo de normalización (DIG-03).
2. **DIG-08 con palabras españolas** que no están en el texto de instrucciones («competiciones») → sigue habiendo falsos positivos en respuestas en español.
3. **Evaluador (`span_hit`)** no aplica la misma normalización que el DIG (guion de corte de línea): infravalora aceptaciones correctas (SCO-026).
4. **Saturación de Gemini (503)** intermitente y Groq gratuito insuficiente: la variabilidad del proveedor domina cualquier comparación de una sola corrida.
5. **Configuración de Groq en el PC:** `scripts/check_llm_quota.py` lee `GROQ_MODEL` del `.env` (`llama-3.3-70b-versatile`, inexistente), mientras el asistente usó `openai/gpt-oss-120b`; la comprobación de cuota de Groq no reflejaba el modelo real.
6. Falsos bloqueos persistentes con el mismo proveedor (DIR-005, DIR-018, EXC-009, SCO-021, SCO-023, SCO-024, SCO-025): siguen siendo la principal pérdida de cobertura; su análisis por regla (DIG-05/DIG-09, no modificadas por decisión del responsable) queda pendiente.

---
**Corrección (2026-11-16, informe posterior):** en la versión inicial de este documento la tabla de §2 decía 7 falsos bloqueos en B y 3/4 preguntas sin generación (A/B); los valores correctos, recalculados del archivo de resultados, son 8 y 1/3. En §6.6 se atribuyeron los bloqueos persistentes a DIG-05/DIG-09: el diagnóstico detallado (`INFORME_CORRECCIONES_POST_EVALUACION_AB.md`, §8) muestra que las reglas implicadas son sobre todo DIG-11 y DIG-06.

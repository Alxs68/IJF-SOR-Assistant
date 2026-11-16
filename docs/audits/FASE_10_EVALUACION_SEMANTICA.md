# Fase 10 — Benchmark independiente, NLI Shadow y evaluación de LLM real

**Estado:** COMPLETADA. **Clasificación: APTO PARA CONTINUAR EXPERIMENTACIÓN.** Ningún componente de esta fase es apto para producción.
**Fecha:** 2026-11-15. **Entorno de medición:** Windows 10 (19045), Intel 64 Family 6 Model 94 (8 CPU lógicas), Python 3.12.10, torch 2.14.1+cpu, transformers 4.57.6, 4 hilos de torch.
**Evidencia en disco:** `data/eval/benchmark_v2/` (benchmark, splits, review/, results/), `data/eval/nli_shadow_v1/` (pares, results/), `data/eval/fase10_logs/` (salida completa de cada paso).

Prioridad de la fase: demostrar experimentalmente si el sistema distingue la evidencia normativa correcta de una evidencia literal de otro ámbito, sin comprometer la integridad de ADA.

**Respuesta corta:**
* El control productivo (ADA + DIG) **no aceptó ninguna respuesta basada en evidencia de otro ámbito** en 210 evaluaciones con el LLM real. Lo consigue sobre todo absteniéndose: solo respondió al **27 %** de las preguntas respondibles.
* La recuperación sí entrega evidencia de otro ámbito sin la correcta en **5 de 34** casos medibles.
* El mejor modelo NLI de CPU (mDeBERTa‑v3‑base multilingüe) separa ámbito correcto e incorrecto bastante mejor que la coincidencia de palabras: en test sellado 0,92 en premisas y 0,80 en afirmaciones, frente a 0,40 y 0,24 léxicas. Aun así acepta **7 de 50** pares de ámbito erróneo y rechaza **10 de 35** afirmaciones correctas. Es una señal útil, no una prueba.

---

## 1. Arquitectura experimental

```
                 RUTA PRODUCTIVA (sin cambios en Fase 10)
consulta -> ADA (proyeccion ES->EN) -> RRE -> EvidenceBundle -> LLM -> citas -> DIG -> SUCCESS/ABSTAIN
                                                          |                         |
                       (solo lectura / registro)          v                         v
                 RUTA EXPERIMENTAL (src/experimental, scripts/eval_*)
   benchmark_access (test_sealed sellado) | nli_shadow | ambiguity_detector | eval_llm_shadow (Recorder)
                                   -> results/*.json   (sin efecto en decisiones)
```

* **Paquete `src/experimental/`:** `benchmark_access.py`, `nli_shadow.py`, `ambiguity_detector.py`. Toda salida lleva `experimental_label = EXPERIMENTAL_NO_DECISORIO` y `decision_effect = NINGUNO`, y no contiene campos de decisión (`status`, `citations`, `decision`…).
* **Aislamiento, verificado por `tests/test_fase10_experimental.py`:**
  * ningún módulo de `src/` ni `app.py` importa o referencia el paquete experimental;
  * importar los módulos experimentales no altera `analyze_situation`, `_call_llm` ni `DecisionIntegrityGate.evaluate`.
* **Evaluación del LLM real:** usa `ArbitrationDecisionAssistant` sin modificaciones y con el DIG activo. El único envoltorio es `Recorder`, que llama a `_call_llm` original y guarda texto, metadatos y latencia (el prompt solo como hash). Los secretos se sanean, y hay un test que lo verifica.
* **Archivos productivos sin tocar en esta fase:** `ada_assistant.py`, `decision_integrity.py`, `rre_engine.py` y `llm_provider.py` tienen fecha de modificación anterior al primer archivo de la Fase 10. No cambiaron el corpus, los documentos SHADOW, la configuración, `.env` ni la jerarquía normativa. No hubo commits, push ni despliegue.

## 2. benchmark_v2 y mecanismo de revisión

**Generación.** `scripts/build_benchmark_v2.py` (solo stdlib, reproducible con `--check` → REPRODUCIBLE).

| | |
|---|---|
| Consultas | 105 (en 52, es 48, fr 2, pt 3) |
| Comportamiento esperado | RESPONDER 78, SOLICITAR_ACLARACION 15, ABSTENER_INSUFICIENCIA 6, ABSTENER_FUERA_DE_DOMINIO 6 |
| Categorías | AMBITO_DISTRACTOR 30, DIRECTA 18, EXCEPCION 10, AMBIGUA 10, DISTINCION_CATEGORIA 7, INSUFICIENTE 6, OOD 6, INCOMPLETA 5, REFERENCIA_CRUZADA 5, MULTI_ARTICULO 4, MULTILINGUE 4 |
| Distractores de otro ámbito | 54, en 43 consultas |
| Particiones | dev 41 / **test_sealed 64**, por grupo semántico (82 grupos, ninguno repartido) |
| Solapamiento con v1 | Jaccard máximo 0,667; umbral de rechazo 0,7 |
| Errores de construcción | 0; todas las anclas verificadas literalmente contra la página |

**Diseño:**
* **Evidencia mínima literal.** Cada consulta respondible tiene fragmentos literales verificados. Las de ámbito tienen `wrong_scope_distractors`, reglas literales parecidas de otro ámbito (veteranos, kata, cadetes, equipo mixto, Juegos Olímpicos, árbitros…).
* **Ambiguas e incompletas.** Las ambiguas declaran la dimensión, las reglas candidatas y una aclaración propuesta. Las incompletas declaran «objeto o contexto ausente».
* **Insuficientes.** Llevan una prueba de ausencia: una expresión regular sobre todo el corpus, registrada con 0 coincidencias. Al construir el benchmark, 2 consultas inicialmente etiquetadas como insuficientes sí tenían coincidencias; se reformularon o se ajustó la prueba, y queda documentado.
* **Independencia de v1.** El builder detectó 3 consultas que reproducían casi literalmente otras de v1; se reescribieron.
* **Etiquetas.** Las automáticas (`auto_labels`, con justificación por categoría) están separadas de las humanas (`human_labels = null`). Todas las consultas están en `review_status = PENDING_EXPERT_REVIEW` y `certified_by_referees = false`. El benchmark no contiene respuestas normativas redactadas.
* **Test sellado.** `test_sealed` solo se carga con `allow_test_sealed=True`, y se verifica su sha256 contra el manifiesto. Los evaluadores fijan umbrales y parámetros únicamente con dev.

**Revisión arbitral.** `review/review_template.csv`, `review/REVIEW_PROTOCOL.md` y `scripts/merge_benchmark_v2_review.py`:
* veredictos ACEPTA, CORRIGE, RECHAZA y DUDA;
* estados resultantes EXPERT_REVIEWED, REVIEW_CONFLICT, REJECTED_BY_EXPERT y PENDING;
* el merge nunca modifica `benchmark_v2.jsonl` ni `auto_labels` (verificado por test).

**Defectos del benchmark ya detectados con los resultados, para el árbitro:**
* **B2-SCO-017:** el LLM respondió con un pasaje válido no anclado (A1.3.1, p.102, edad mínima de veteranos). Falta evidencia alternativa.
* **B2-INS-005 (dopaje en kata):** el SOR tiene reglas generales de dopaje que podrían aplicar. La etiqueta INSUFICIENTE es discutible.
* **B2-DIR-007 (calzado en la ceremonia):** el detector la marca ambigua porque kata también tiene ceremonia. La frontera entre «clara» y «ámbito no especificado» necesita un criterio arbitral.

**Pares NLI derivados.** `data/eval/nli_shadow_v1/pairs.jsonl` contiene 169 pares en 59 consultas:
* SUPPORT 59, SCOPE_PREMISE 41, SCOPE_CLAIM 42, NUMBER 27;
* dev 65 / test 104;
* es 73, en 82, fr 7, pt 7.

Cómo se construyen:
* **Premisa:** ventana literal de la página SOR (350/200 caracteres alrededor del fragmento).
* **Hipótesis:** una afirmación redactada como material de evaluación, PENDING_EXPERT_REVIEW.
* **NUMBER:** las cifras se alteran automáticamente, de forma genérica.
* **Exclusiones:** 12 pares SCOPE_PREMISE cuya ventana solapa la evidencia correcta (etiqueta no determinable).

## 3. Modelos NLI evaluados

| Modelo | Idiomas | Parámetros | Motivo |
|---|---|---|---|
| `lexical` (línea base) | — | — | coincidencia de términos: el tipo de señal que el DIG ya usa; sirve de comparación |
| `cross-encoder/nli-deberta-v3-xsmall` | EN | 70,8 M | el más ligero con NLI de 3 clases |
| `MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli` | multilingüe | 107,0 M | multilingüe ligero (consultas y respuestas en ES) |
| `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` | multilingüe | 278,8 M | multilingüe de referencia, más preciso y más costoso |

Los cuatro cargaron. Las advertencias de Hugging Face (symlinks, `hf_xet`) no afectan a los resultados.

## 4. Justificación metodológica

* **Selección sin tocar test.** El umbral de entailment se elige solo con los pares dev (F1 máximo de SUPPORTED) y se aplica fijo a test. También se informa con 0,5.
* **Prueba directa de la prioridad de la fase.** La discriminación por consulta mide si `p(SUPPORT) > p(SCOPE_PREMISE)` (misma afirmación con evidencia literal de otro ámbito) y si `p(SUPPORT) > p(SCOPE_CLAIM)` (misma evidencia con la afirmación atribuida a otro ámbito).
* **Medición de memoria.** Cada modelo corre en un subproceso propio.
* **Concurrencia.** El tokenizador se serializa con un lock; la primera corrida falló con «Already borrowed» y se corrigió. Se verificó que las salidas en paralelo son idénticas a las secuenciales (diferencia máxima 0,0).
* **Sin integración en ADA.** El NLI no se conectó a ADA en ningún momento.

## 5. Resultados NLI (test sellado, umbral fijado en dev)

| Modelo | Umbral | P | R | F1 | Exactitud | Ámbito erróneo aceptado | Discrim. premisa / afirmación / cifra |
|---|---|---|---|---|---|---|---|
| léxico | 0,154 | 0,35 | 0,71 | 0,47 | 0,46 | 34 / 50 | 0,80 / 0,44 / 0,79 |
| deberta‑v3‑xsmall (EN) | 0,012 | 0,44 | 0,77 | 0,56 | 0,60 | 27 / 50 | 0,76 / 0,84 / 0,95 |
| MiniLMv2‑L6 (multi) | 0,317 | 0,60 | 0,60 | 0,60 | 0,73 | 11 / 50 | 0,84 / 0,84 / 1,00 |
| **mDeBERTa‑v3‑base (multi)** | 0,500 | **0,71** | **0,71** | **0,71** | **0,81** | **7 / 50** | **0,92 / 0,84 / 0,95** |

**Matriz de confusión de mDeBERTa en test** (positivo = SUPPORTED): TP 25, FP 10, FN 10, TN 59. Por tipo de par:
* SCOPE_PREMISE: 23 de 25 correctas (2 aceptadas: SCO‑008 y SCO‑016).
* SCOPE_CLAIM: 20 de 25 (5 aceptadas: CAT‑005, DIR‑013, SCO‑001, SCO‑027, SCO‑030).
* NUMBER: 16 de 19.
* SUPPORT: 25 de 35; las 10 afirmaciones correctas rechazadas son falsos negativos.

**F1 en dev y por idioma** (test, mDeBERTa):
* F1 en dev: 0,81 para mDeBERTa y 0,67–0,71 para los demás. La caída dev→test indica una estimación todavía inestable con estos tamaños.
* Por idioma: es 0,77, en 0,63; fr y pt con 1,00 sobre 7 pares cada uno, una muestra no concluyente.
* Los modelos solo en inglés o ligeros caen en español: MiniLM 0,46 y deberta‑xsmall 0,47.

**Lectura de los resultados:**
* La coincidencia léxica no distingue el ámbito: acepta 68 % de los pares de ámbito erróneo y solo prefiere la afirmación correcta en el 44 % de los casos. Esto confirma que la pertinencia por términos del DIG es necesaria pero no suficiente.
* El NLI multilingüe base reduce los pares de ámbito erróneo aceptados de 34 a 7, pero no los elimina. Además rechaza un 29 % de afirmaciones correctas.

**NLI en shadow sobre las respuestas reales del LLM** (MiniLM, umbral 0,5 sin calibrar; respuesta en ES frente a citas en EN):
* De 42 respuestas aceptadas con la cita esperada: 13 SOPORTE_PROBABLE, 22 SOPORTE_NO_ESTABLECIDO, 7 CONTRADICCION_PROBABLE.
* De las 5 respuestas que debieron abstenerse: 2 SOPORTE_PROBABLE.

Es decir, en uso real el modelo ligero no discrimina y sería inutilizable como filtro. Solo se registró; no tuvo efecto en ninguna decisión.

## 6. Detector de ambigüedad (experimental)

**Diseño genérico, sin reglas por pregunta.** Un test verifica que el código no contiene ningún fragmento de 4 palabras de las consultas, ninguna etiqueta de artículo ni términos de ámbito.
* **INCOMPLETA:** información de la consulta (Σ idf) menor que un mínimo.
* **AMBIGUA:** candidatas con encabezados distintos y puntuación comparable, sin que la consulta nombre un término que discrimine entre ellas.
* **Aclaración:** se construye con los encabezados y secciones de las candidatas.

**Parámetros elegidos en dev** con regla predeclarada (máxima precisión con recall ≥ 0,8): `min_info = 2,0`, `ratio = 0,7`, `max_df_disc = 0,3`, con proyección ADA.

| | dev (parámetros por defecto) | **test sellado (parámetros de dev)** |
|---|---|---|
| Precisión de «requiere aclaración» | 0,29 | **0,17** |
| Recall | 0,67 | 0,67 |
| Aclaración innecesaria en consultas claras | 32 % | **62 %** (61 % en las de ámbito) |
| Exactitud INCOMPLETA vs AMBIGUA | 0,75 | 0,67 |
| Cobertura de candidatas de referencia | 0,50 | 0,92 |

**Conclusión: no apto ni siquiera para prueba en shadow.**
* **Lo que funciona:** cuando detecta una ambigüedad, identifica bien las reglas en conflicto (cobertura 0,92).
* **Lo que falla:** pide aclaración en la mayoría de las consultas claras.
* **La causa:** la puntuación léxica no sabe si la consulta ya fija el ámbito con palabras que no están en los encabezados («Grand Prix», «U21», «de -66 kg»).
* **Generalización:** la caída dev→test confirma que los parámetros elegidos en dev no se sostienen.

## 7. LLM real (flujo SHADOW sobre ADA)

**Configuración y consumo:**
* Proveedor principal Gemini (`gemini-flash-lite-latest`), con caída automática a Groq (`openai/gpt-oss-120b`) en 4 casos.
* 2 corridas por partición: 82 evaluaciones en dev y 128 en test.
* Sin bloqueo y corpus intacto.

**Corrección del evaluador.** La primera versión contaba como «cifras sin respaldo» los números de los enlaces al PDF y de las páginas que ADA añade al formatear la respuesta, y clasificó erróneamente las 43 aceptaciones. Se corrigió: ahora las cifras se comparan con los campos generados por el modelo. Los informes se reclasificaron sin llamar al LLM (`--rescore`); en estas dos corridas sobre el resumen almacenado, que es una aproximación documentada. Las corridas futuras guardan los campos originales. Archivos: `results/llm_shadow_{dev,test_sealed}_rescored.json`.

| | dev | test sellado |
|---|---|---|
| Respondibles aceptadas (SUCCESS) | 17 / 62 (27 %) | 26 / 94 (28 %) |
| — con cita literal del ancla esperada | 17 | 25 |
| — evidencia de otro ámbito aceptada | **0** | **0** |
| — cifra sin respaldo aceptada | 0 | 0 |
| — aceptada sin la evidencia esperada | 0 | 1 (SCO‑017: pasaje válido no anclado → error del benchmark) |
| Respondió cuando debía abstenerse o aclarar | 0 / 20 | 5 / 34 (AMB‑007, AMB‑008 ×2, INS‑005 ×2) |
| Abstenciones legítimas (OOD / insuficiente / ambigua) | 20 / 20 | 29 / 34 |
| Excepciones omitidas en respuestas aceptadas | 0 | 0 |
| Referencias cruzadas omitidas en respuestas aceptadas | 2 | 0 |
| Citas fuera de la evidencia esperada en respuestas aceptadas | 1 | 6 |

**Atribución de los fallos en preguntas respondibles:**

| Causa | dev | test |
|---|---|---|
| RECUPERACIÓN (la evidencia correcta no llegó al modelo) | 22 | 24 |
| CONTROL: abstención con cita literal correcta (posible falso negativo del DIG) | 16 | 34 |
| GENERACIÓN (no citó la evidencia correcta) | 5 | 10 |
| API (cuota, petición demasiado grande, temporal) | 2 | 0 |

**Comprobaciones del DIG que más bloquean las abstenciones con cita correcta** (dev + test):

| Comprobación | Bloqueos |
|---|---|
| DIG‑06 (cifras) | 27 |
| DIG‑05 (pertinencia) | 16 |
| DIG‑08 (influencia SHADOW) | 12 |
| DIG‑09 (excepciones) | 9 |

Requieren revisión caso por caso antes de calificarlas de falsos negativos: un literal correcto no garantiza una respuesta correcta.

**Calidad de las respuestas y del proceso:**
* **Cumplimiento de cita literal:** 159 de 202 respuestas del modelo incluyen `evidence_quotes`; la comprobación de cita literal (DIG‑03) falló 22 veces.
* **JSON inválido:** DIG‑00 falló 18 veces.
* **Errores de API:** 8 llamadas (QUOTA 5, REQUEST_TOO_LARGE 3, TEMPORARY 4 por tipo).
* **Variabilidad entre corridas:** el resultado cambió en 9 de 41 consultas de dev y en 20 de 64 de test. Aceptar o abstenerse depende en buena medida de la ejecución.

## 8. Latencia y consumo

| Componente | Latencia | Memoria / consumo | Notas |
|---|---|---|---|
| NLI léxico | 0,04 ms/par | — | — |
| deberta‑xsmall | p50 107 ms, p95 146 ms | pico RSS 718 MB | carga 5,2 s; 8 → 12 pares/s con 1 → 4 hilos |
| MiniLMv2‑L6 | p50 32 ms, p95 43 ms | pico RSS 731 MB | carga 6,5 s; 31 → 50 pares/s |
| mDeBERTa‑base | p50 380 ms, p95 488 ms | pico RSS **2.125 MB** (1.803 MB tras la inferencia) | carga 6,3 s; 2,9 → 4,1 pares/s (satura en 2 hilos) |
| Proceso Python con torch, sin modelo | — | ~261 MB | — |
| LLM real (Gemini flash‑lite) | p50 2,2 s, p95 4,1–5,2 s | ~7.000 tokens/consulta (595.603 en dev y 896.715 en test, 2 corridas) | — |
| Recuperación + bundle sin LLM | p50 65 ms, p95 83 ms | — | `retrieval_all.json` |
| Detector de ambigüedad | < 1 ms/consulta | — | índice en ~1 s |

**Encaje en OCI: no se asume.** Las cifras de memoria y latencia son de esta máquina Windows de 8 CPU. Una respuesta típica tiene 2–4 afirmaciones × 2–4 citas, de modo que mDeBERTa añadiría unos 1,5–6 s de CPU por respuesta y unos 2 GB de RAM por proceso. Hay que medir en la forma de instancia de OCI concreta antes de cualquier prueba allí.

## 9. Riesgos

1. **Cobertura muy baja (27 %).** El DIG garantiza la integridad absteniéndose. Para el usuario final, el sistema responde poco. La mitad de las abstenciones se deben a la recuperación; la otra mitad, a controles que podrían ser demasiado estrictos.
2. **Errores de ámbito en la recuperación.** 5 de 34 consultas recibieron solo la evidencia del otro ámbito. Hoy los frena el DIG; si se relajan los controles para ganar cobertura, aparecerán como respuestas erróneas.
3. **Consultas ambiguas respondidas con el ámbito general** (AMB‑007, AMB‑008) sin advertir que veteranos o kata difieren. ADA no tiene mecanismo de aclaración.
4. **El NLI no es fiable como filtro:** acepta 14 % de los pares de ámbito erróneo y rechaza 29 % de las afirmaciones correctas. En respuestas reales, el modelo ligero no discrimina. Usarlo para autorizar respuestas sería presentar una probabilidad como prueba.
5. **Variabilidad del LLM** (≈ 25 % de consultas inestables) y dependencia de cuota: hubo errores de QUOTA y REQUEST_TOO_LARGE.
6. **Consumo de mDeBERTa** (≈ 2 GB, 0,4 s/par), no medido en el destino.
7. **El rendimiento en francés y portugués** es nulo en la recuperación: la proyección ADA solo cubre ES y EN.

## 10. Limitaciones metodológicas

* **Revisión pendiente.** Todo el benchmark y todas las afirmaciones NLI están en PENDING_EXPERT_REVIEW; ya hay 3 defectos de etiqueta identificados (§2). Las métricas son provisionales.
* **Independencia limitada.** El benchmark v2 es independiente de v1 en la redacción, no en la autoría: lo redactó el mismo asistente IA que conocía los fallos de las fases 8 y 9, y las reglas cubiertas se solapan parcialmente.
* **Muestras pequeñas:** 64 consultas en test, 104 pares NLI en test, 7 pares por idioma en fr y pt. Las diferencias entre modelos de unos pocos puntos no son significativas.
* **Pares sintéticos.** Afirmaciones redactadas, no respuestas reales. La caída de MiniLM entre pares sintéticos y respuestas reales muestra que el resultado no se transfiere directamente.
* **Separabilidad por pasaje.** 9 de 43 consultas de ámbito tienen el distractor en el mismo pasaje que la evidencia: solo son medibles a nivel de cita, no de recuperación.
* **Reclasificación aproximada.** En las corridas actuales se basó en el resumen formateado, no en los campos crudos.
* **Detector de ambigüedad:** sus parámetros se eligieron en dev con solo 6 consultas que necesitan aclaración.
* **Pytest completo.** 464 pasan, 6 fallan y 1 se omite. Los 6 fallos son los mismos preexistentes de la Fase 9.1 (golden retrieval; D01, D04, response_structurer test_06 y rre_ada test_07/09). La primera corrida recogió por error `scratch/` (12 errores de recolección de scripts antiguos ajenos a esta fase); se repitió sobre `tests/`.

## 11. Comparación con las fases 8 y 9

| Aspecto | Fase 8 (benchmark v1, sin LLM) | Fase 9 / 9.1 (DIG con stubs) | Fase 10 (v2 independiente, LLM real) |
|---|---|---|---|
| R@5 global | 0,49 | — | 0,52 (en 0,67, es 0,41, fr/pt 0,00) |
| MRR | 0,40 | — | 0,40 |
| Precisión del bundle | 0,09 | — | 0,10 |
| Cobertura de excepciones / referencias en el bundle | 0,64 / 0,20 | — | 0,00 / 0,00 (10 y 5 consultas) |
| OOD con evidencia entregada | 6 / 15 | — | 4 / 6 (la abstención la aporta después ADA/DIG) |
| Ámbito erróneo | ~32/87 citas pertinentes de otro ámbito (riesgo residual) | no medible con stubs | 0 aceptadas por el DIG en 210 evaluaciones reales; 5 / 34 en la recuperación |
| Falsos positivos del control | — | FP S1 7, S1B 9 (stubs) | 0 en dev; 5 / 34 no respondibles en test (2 consultas) |
| Respondibles aceptadas | — | — | 27–28 % |

* **Lo que confirma la Fase 10:** la tesis de la Fase 9 es correcta. El DIG impide que la cita literal de otro ámbito se convierta en respuesta.
* **Lo que añade:** cuantifica el coste en cobertura y muestra que la recuperación sigue sin mejorar, sobre todo en excepciones y referencias cruzadas.
* **Lo que no confirma:** no confirma que la coincidencia de términos baste para juzgar el ámbito; el NLI multilingüe la supera claramente en los pares de ámbito.

## 12. Recomendación

**Clasificación: APTO PARA CONTINUAR EXPERIMENTACIÓN.** No apto para producción. Ningún componente debe alterar decisiones de ADA.

**Recomendaciones para la Fase 11, por prioridad:**

1. **Revisión arbitral de benchmark_v2.** Sin ella ninguna métrica es definitiva. Empezar por los 3 defectos de §2 y las 50 abstenciones con cita correcta: decidir si el DIG acierta o es demasiado estricto, sobre todo en DIG‑06 y DIG‑05.
2. **Recuperación consciente del ámbito.** Atacar las 46 abstenciones por recuperación, los 5 casos de distractor sin evidencia, la cobertura nula de excepciones y referencias en el bundle, y la proyección para fr/pt. Medir sobre dev y verificar en test sellado una sola vez.
3. **Mecanismo de aclaración en ADA.** Diseñarlo como propuesta revisable para consultas cuyas candidatas difieren por ámbito. No usar el detector actual; un enfoque viable es comparar las respuestas candidatas por ámbito, no los encabezados.
4. **NLI mDeBERTa en prueba SHADOW controlada, solo registro.** Tras la revisión arbitral, ejecutarlo junto al DIG sobre respuestas reales y medir su acuerdo con el árbitro, sin efecto decisorio. Medir antes memoria y latencia en la instancia OCI objetivo.
5. **Estabilidad del LLM.** Bajar la temperatura o fijar semilla si el proveedor lo permite, reducir el tamaño del prompt (REQUEST_TOO_LARGE) y repetir con ≥ 3 corridas.
6. **Mantener intactas las garantías actuales:** test sellado, aislamiento experimental y la regla de no relajar controles para subir el porcentaje de SUCCESS.

---

### Anexo A — Archivos de la Fase 10 (sha256)

| Archivo | sha256 |
|---|---|
| `data/eval/benchmark_v2/benchmark_v2.jsonl` | `01759b58124fd874c2af660e9fe945c1827b35882890dbbba6b052e0295d4d44` |
| `data/eval/benchmark_v2/splits/dev.jsonl` | `b2bb36ccfb5849d552d2b8f8d7c9db1266cf7889d0b82cf23c54a37af62ef191` |
| `data/eval/benchmark_v2/splits/test_sealed.jsonl` | `324d7626950fa1fb81aeb2392acc12c3323467ace5574cf66ec6ad0fd01e485a` |
| `data/eval/benchmark_v2/manifest.json` | `10eec97137e776bc5ef0e0d0f809c3b726ec5857cd5331b8d015b28e13a97eb8` |
| `data/eval/nli_shadow_v1/pairs.jsonl` | `8055b7bdadb96a7a7865d30e766f4a1781e5049956bfcaff0429d81b5b239c27` |
| `src/experimental/__init__.py` | `bab7cef8672542d3bf6bee1749f74b782dd472af2badf2b91034d2da3f776bc6` |
| `src/experimental/benchmark_access.py` | `ead29f3d8e85939dd86c3f79bf249942595f58a5502be11732064064500a57c6` |
| `src/experimental/nli_shadow.py` | `7ed00655b02375378359efc3de6a42ae4a7fc770e1b496f39d76c1bbe28e2d24` |
| `src/experimental/ambiguity_detector.py` | `c817967b1d89d5aa2f7cc581613577323106bd91562c9f6ccfd6d56af73ffdd3` |
| `scripts/build_benchmark_v2.py` | `8734d82f4b0a0353f58c2998c232d3a6427505a5d3ad2c63476b1ff6e8e756c3` |
| `scripts/merge_benchmark_v2_review.py` | `3d2e8d876318ec5f5b8e2d45d134fe3d656f8773d97873ada2ffa0a59de2bfa7` |
| `scripts/build_nli_shadow_pairs.py` | `ce48015375f6d5977a289d00aaf98834c8be852cb56aea5ed392fd96437ceefe` |
| `scripts/eval_benchmark_v2_retrieval.py` | `65dfad2d5f31a5a6b70debb6ed7a78e2e1a819516e4feec72dd0bf6e8030428e` |
| `scripts/eval_ambiguity_detector.py` | `a886005ba33c66a8a24c6187c0187724533d8a74bdc5979615ee7989c61c8f5f` |
| `scripts/eval_nli_shadow.py` | `c064f89ad3560d232a2249970411b5335518b73559d3ef9197fd8843b658402b` |
| `scripts/eval_llm_shadow.py` | `066eb295f48e718a5c3c6812571177a3f764be39fae4ab139a8420aa52ca9883` |
| `scripts/run_fase10.ps1` / `run_fase10_rerun.ps1` | `b5fd4959…cfb` / `395ad0f5…986` |
| `tests/test_fase10_experimental.py` | `67d11db11717f60ab5bb5a82ee572bdbef698850f8dbdaadb9d1178e44506147` |

**Integridad:**
* **Corpus SOR** (`passages_candidate.json`): `7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b`. Coincide antes y después de cada paso, en el registro de Windows y en la verificación de la VM.
* **Documentos SHADOW:** 40 de 40 sin cambios frente a la línea base de la Fase 8.

### Anexo B — Reproducción

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_fase10.ps1          # completo (incluye LLM real)
powershell -ExecutionPolicy Bypass -File scripts\run_fase10_rerun.ps1    # pytest tests/ + NLI, sin LLM
python scripts\eval_llm_shadow.py --rescore data\eval\benchmark_v2\results\llm_shadow_dev.json
```

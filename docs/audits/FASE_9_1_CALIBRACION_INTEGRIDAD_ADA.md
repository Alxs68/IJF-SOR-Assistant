# FASE 9.1 — Auditoría y calibración de integridad decisoria ADA

Fecha: 2026-11-15 · Versión final del control: **DIG-1.3** · Estado: **APROBADA CON RESERVAS — APTO para continuar en desarrollo o sombra; NO APTO para producción con LLM real** · Sin commit, push, release ni despliegue OCI.
Evidencia en disco: `data/eval/decision_integrity_v1/` (pytest_full/record/record2/record3/no_dig, diag_*.jsonl, eval_v1_1/v1_2/v1_2b/v1_3, results_*.json, shadow_v1_*).

> **Advertencia de método.** El diagnóstico de esta fase recorrió el benchmark completo, incluida la partición **test** reservada. La decisión de umbral (§5, D7) se tomó con **dev**, pero el test ya no está intacto para medir generalización. Para la próxima evaluación hace falta un test nuevo (benchmark_v2).

## 1. Diagnóstico de los tests fallidos

El baseline de la Fase 9 (23 fallos) no se conservó como listado. El diagnóstico se hizo sobre la primera ejecución completa con DIG-1.1 (27 fallos, 417 aprobados) y se trianguló con:
- un plugin de diagnóstico (`scripts/diag/diag_record_dig.py`), que registra por test: estado, proveedor LLM, controles DIG fallidos, evidencia y citas;
- una ejecución con DIG **desactivado solo en memoria** (`DIAG_MODE=no_dig`), que reproduce el comportamiento previo a la Fase 9 sin tocar el código en disco.

| Test(s) | Clasificación | Causa exacta | Acción |
|---|---|---|---|
| `test_golden_dataset` | **Preexistente; no DIG** (falla igual sin DIG) | Recuperación pura: 9/12 frente a ≥80 % exigido. Además reescribe `scratch/golden_validation_report.md` en cada ejecución | Se conserva el fallo (recuperación fuera de alcance). Se documenta |
| `test_llm_provider::…offline_mode…` | **Expectativa incompatible**; preexistente (falla sin DIG) | Exige SUCCESS «modo local» sin LLM, lo que contradice AUD-03 opción A (aprobada en la Fase 3) | Se actualiza al contrato AUD-03: ABSTAIN, modo local, sin síntesis IA, sin citas |
| `test_p1_b` 06/09/10 | **Entorno** + expectativa preexistente (fallan sin DIG) | Usan el LLM real vía `.env` (2 claves). El proveedor respondió nulo (sin red o sin servicio) y se produjo una abstención local | Generador determinista conforme (`cite_best_delivered`); aserciones intactas |
| `test_llm_provider::…fallback…` | **Fixture obsoleta** + fixture incorrecta | El mock de Groq responde texto plano (DIG-00) y cita P189 (seoi-nage inverso) para «cadet head defence» | Mock en JSON de contrato con citas literales del pasaje pertinente P188 |
| `test_rre_ada::test_07` | **Fixture obsoleta** | El stub responde una frase libre con un ID (DIG-00) | Stub con `grounded_answer` |
| `test_audit_critical_cases` Q09; `test_evaluation_battery::test_generator_citation_integrity` D01–D06, D08; `test_head_actions_rules::test_04` | **Expectativa incompatible con el contrato** | Exigían SUCCESS citando el **primer** pasaje entregado aunque no fuera pertinente (por ejemplo, Q09 citaba P188, cabeza en cadetes, para una pregunta sobre estrangulación). Esa era la vulnerabilidad V1 | Ahora exigen coherencia: SUCCESS ⇔ DIG PERMITIR. Con ABSTAIN, sin citas y con motivo. Se añade un test positivo `test_critical_query_citing_most_related_delivered_passage` |
| `test_evaluation_battery::…pertinent_evidence` D02/D05/D06, `test_head_actions_reasoning_regression::test_02`, `test_newaza_boundary_rules::test_02` | **Defecto de implementación DIG** (corregido) | DIG-09 «unidad no disponible»: el RRE entrega texto **cosido** de varias páginas, que no coincide con el hash de la unidad derivada. Además, citas que cruzan el marcador PAGE BREAK | Localización en el texto canónico de la página o páginas vecinas, y por segmentos |
| `…pertinent_evidence` D03/D04, `test_rre_ada::test_04` | **Artefacto del stub** y del contrato | El pasaje citado era pertinente, pero la oración citada no. El stub no veía la proyección técnica que DIG usa para la pertinencia | El prompt incluye la proyección técnica; el helper cita hasta 3 oraciones afines y las excepciones |
| `test_response_structurer::test_06`, `test_rre_ada::test_09`, D01 | **Falso negativo léxico** (véase §3) | Tatami: el pasaje 8.7 usa «size» o «measure», nunca «dimension» | Se conserva como falso negativo conocido; no se convierte en skip |
| `test_p1_b::test_10` (solo en la ejecución con el plugin) | **Entorno de diagnóstico** | El plugin ocultaba la firma de `analyze_situation` (`KeyError: 'top_k'`) | `functools.wraps` en el plugin |

En ningún caso se eliminaron aserciones de seguridad ni se convirtieron fallos en skips. Hay copias previas de los archivos tocados en `$HOME/aud_work/pre_f9/*.pre91`.

## 2. Análisis individual de falsos positivos (baseline: 8, estrategia S1 de la Fase 9)

| Caso | Consulta | Cita | Por qué se aceptó | Causa | Estado final |
|---|---|---|---|---|---|
| B1-AMB-005 | ¿Cuántos atletas tiene un equipo? | 2.7 (p. 42) | Cita literal pertinente; el stub no hace afirmaciones contrastables | Consulta **ambigua**: DIG no puede detectar ambigüedad | Residual (nivel D) |
| B1-AMB-006 | What colour must it be? | C1.9 | Ídem | Ambigua | Residual |
| B1-AMB-007 | ¿Qué pasa si no se presenta? | 6.2.5 | Ídem | Ambigua | Residual |
| B1-OOD-010 | dimensions of a sumo dohyo | 8.8 | Bastaba un término genérico | Términos ausentes del SOR + pertinencia débil | **Corregido** (DIG-11 «sumo», «dohyo»; DIG-05 distintivo) |
| B1-OOD-012 | guard pass in Brazilian jiu-jitsu | 3.1 | Ídem | Ídem | **Corregido** (DIG-11) |
| SH-022 | exact fine amount for match fixing | 1.2.2 | Cita pertinente; respuesta vacía | Pregunta cuantitativa sin cifra en la evidencia | **Corregido** (DIG-12) |
| SH-023 | patrocinadores del Grand Slam de Ulaanbaatar | 3.2 | Comparte «Grand Slam» | El sujeto («Ulaanbaatar», patrocinadores) no está en el SOR; consulta en español (DIG-11 solo se aplica al inglés) | Residual |
| SH-024 | daily fee paid to referees at a Grand Prix | 2.8.3 | DIG-12 se activa, pero la cita contiene alguna cifra | La cifra no es la pedida (nivel D) | Residual |

Resultado final (DIG-1.3, barrido `v1.2_unico_0.15`):
- **S1 (comparable con el baseline): 7 FP** = 6 ambiguas (AMB-002/006/007/008/012/015) + SH-023.
- S1B (stub que cita el pasaje más afín): 9 FP = las anteriores + SH-011 + SH-024.

El aumento de casos ambiguos respecto al baseline se debe a que el stub corregido cita más oraciones; no es un relajamiento del control. **Los FP residuales no tienen una causa general corregible sin verificación semántica:** son consultas ambiguas y respuestas no responsivas. Se explican con evidencia por caso (`per_case` de `results_v1_3.json`).

## 3. Análisis de falsos negativos

- **El baseline del 37,7 % estaba mal medido.**
  - El stub citaba siempre el **primer** pasaje entregado aunque no fuera el pertinente.
  - Además, la evidencia mínima se comparaba por `passage_id`, cuando los pasajes de una misma página tienen texto idéntico.
  - Definición corregida: un FN es un caso respondible que **cita la página de la evidencia mínima** y aun así se abstiene.
- **Resultado final confirmado (S1B): 7/62 = 11,3 %.** S1 (primer pasaje): 7/53 = 13,2 %. Causas: DIG-05 pertinencia (3) y DIG-10 referencia citada no entregada (2), más las de la tabla. B1-EN-022 y B1-EX-014 se abstienen por pertinencia: la consulta proyectada no tiene ningún término distintivo.

| Caso | Causa | ¿Legítima? |
|---|---|---|
| B1-ES-060 (conmoción) | La proyección por diccionario no traduce «conmoción», así que la consulta no tiene términos distintivos y la pertinencia es inverificable | Abstención conservadora legítima: limitación de la proyección, no de DIG |
| B1-ES-035 / B1-ES-038 | Pertinencia: la oración citada no comparte términos distintivos con la consulta proyectada | Legítima por diseño (heurística necesaria) |
| B1-EX-007 (osaekomi más allá del área de seguridad) | DIG-10: la cita contiene una referencia resuelta no entregada | Legítima: la referencia está **dentro** de la cita |
| B1-EX-011 (pesaje aleatorio) | DIG-10: la cita remite a «table 6.3.4», que no se entregó | Legítima: la tolerancia depende de esa tabla |
| Tatami (D01; tests 06/07/09) | DIG-05: «dimensiones» frente a «size» o «measure» | **Defecto conocido de la heurística léxica.** No se corrige con sinónimos manuales (sería un hardcode) |
| D04 (sanción a un judoka cadete de 15 años que usa la cabeza para lanzar) | La proyección por diccionario no traduce «lanzar»: el único término distintivo es «judoka», ausente de la cita correcta (P188, punto 33) | Falso negativo conocido (proyección); con un traductor LLM la consulta técnica incluiría «throw» |

Causas corregidas durante la fase:
- DIG-09 con texto cosido (18 casos en v1.1);
- DIG-10 exigía referencias de oraciones **vecinas** no relacionadas (fusen-gachi → E1.3 higiene);
- DIG-12 se aplicaba a «how long» u «how often»;
- citas a través de PAGE BREAK.

## 4. Análisis de SUCCESS sin evidencia mínima (baseline: 37)

- **No es un bypass.** Todos los SUCCESS pasaron por `_validate_llm_citations` y por DIG. No hay ninguna ruta a SUCCESS que eluda el control: la única salida SUCCESS de `analyze_situation` exige `llm_answer and citations_valid and integrity_ok`.
- **7/37 eran un error del evaluador**: comparaba por ID en lugar de por página.
- **30/37 eran una pertinencia débil** (bastaba un término genérico, por ejemplo «official events» en el calendario 1.6 para una pregunta sobre la edad mínima) **sumada a respuestas sin afirmaciones contrastables**. Se corrige con DIG-05 por términos distintivos.
- **Resultado final confirmado: S1B, 32 de 87 SUCCESS citan una página distinta de la evidencia mínima** (S1: 33 de 79).
  - Las citas son literales y lexicalmente pertinentes, pero de **otro ámbito**. Ejemplos: edad mínima de veteranos (A1.3) para la edad mínima general; ranking de juniors para el ranking de naciones.
  - En algunos casos es evidencia alternativa válida, por ejemplo la continuación de 6.2.2 en la página 77.
  - Este es el **riesgo residual central**: sin verificación semántica (nivel D), DIG no distingue el ámbito de aplicación.
  - Con un generador real, las cifras y términos inventados se bloquean (S2: 0 SUCCESS). Una conclusión de otro ámbito sin cifras nuevas, en cambio, podría aceptarse.

## 5. Defectos identificados y correcciones

| ID | Defecto | Corrección | Versión |
|---|---|---|---|
| D1 | Pertinencia aceptaba términos genéricos | DIG-05 exige ≥1 término **distintivo** (frecuencia documental ≤15 % de páginas, derivada del corpus) | 1.1 |
| D2 | Referencias exigidas desde oraciones vecinas | DIG-10 solo exige referencias **dentro** de la cita | 1.1 |
| D3 | Consultas sobre entidades ajenas al SOR | DIG-11: en consultas en inglés, un término de contenido ausente de todo el SOR provoca ABSTAIN | 1.1 |
| D4 | Preguntas cuantitativas sin cifra en la evidencia | DIG-12 (cantidad, importe o edad; no se aplica a duración ni frecuencia) | 1.1–1.2 |
| D5 | Títulos SHADOW no considerados | Se incluyen en la huella SHADOW de DIG-08 | 1.1 |
| D6 | **Crítico, de FN:** texto cosido sin unidad | Localización en el texto canónico de la página o páginas vecinas, y por segmentos a través de PAGE BREAK | 1.2–1.3 |
| D7 | Pertinencia contra una proyección que el modelo no veía | El prompt incluye la «Consulta técnica normalizada (EN)» | 1.2 |
| D8 | DIG-08 permitía 1 término solo-SHADOW | Basta 1 término (≥5 letras) | 1.3 |
| D9 | Evaluador: comparación por ID, primer pasaje, inyección S3 desde etiquetas | Comparación por página; estrategia S1B; inyección desde el contenido; diagnósticos por caso; barrido de reglas | — |
| D10 | Variante evaluada «≥2 términos ≤30 %» | **Descartada con datos de dev**: +2 FP; de 7 SUCCESS ganados, 5 fuera de la evidencia mínima y solo 2 correctos (`results_v1_3.json`) | 1.3 (desactivada, `SPECIFIC_MAX_DF = 0.0`) |

## 6. Archivos modificados

- **Producción:**
  - `src/decision_integrity.py`: DIG 1.0 → 1.3.
  - `src/ada_assistant.py`: títulos SHADOW pasados a DIG; línea de consulta técnica en el prompt. Además, los cambios de la Fase 9 descritos en su informe.
- **Pruebas:**
  - `tests/_ada_contract_helpers.py`: proyección, `grounded_quotes`, `cite_best_delivered`, `best_delivered_passage` y citas multi-oración.
  - Tests ajustados: `tests/test_decision_integrity.py`, `test_audit_critical_cases.py`, `test_evaluation_battery.py`, `test_head_actions_rules.py`, `test_rre_ada_architecture.py`, `test_llm_provider.py`, `test_p1_b_configuracion_e2e.py`.
- **Herramientas:** `scripts/eval_decision_integrity.py` (reescrito) y `scripts/diag/diag_record_dig.py` (nuevo, solo diagnóstico).
- **Sin modificar:** corpus SOR, documentos y fuentes SHADOW, catálogo, RRE, índices, embeddings, `.env` y configuración.

## 7. Tests incorporados

`tests/test_decision_integrity.py` pasa de 19 a **29** pruebas de compuerta sobre el texto real del corpus. Las 10 nuevas cubren:
- pertinencia por término genérico;
- referencia vecina no exigida;
- términos ausentes del SOR;
- pregunta cuantitativa sin cifra;
- títulos SHADOW;
- cita ausente del corpus canónico;
- texto cosido entre páginas;
- cita a través de PAGE BREAK;
- pregunta de duración;
- un único término SHADOW;
- y la decisión de pertinencia (regla de dos términos descartada).

En extremo a extremo se añade `test_critical_query_citing_most_related_delivered_passage` (4 consultas críticas).

## 8. Resultados antes/después

| Métrica | Baseline (Fase 9, DIG-1.0) | Resultado (DIG-1.3 final) |
|---|---:|---:|
| Tests generales | 416 passed | **447 passed** (1 skipped) |
| Tests fallidos | 23 | **6**: golden de recuperación (preexistente, no DIG) + 5 falsos negativos conocidos y explicados (tatami ×4: D01, `test_response_structurer::test_06`, `test_rre_ada::test_07/09`; y D04 por la proyección) |
| SUCCESS | 88 (S1) | 86 (S1) / 96 (S1B); en respondibles 79 / 87 |
| Falsos positivos (no respondibles) | 8 | **7** (S1) / 9 (S1B); residuales explicados en §2 |
| Falsos negativos | 37,7 % (mal medido) | **13,2 %** (S1, 7/53) / **11,3 %** (S1B, 7/62) |
| SUCCESS sin evidencia mínima | 37 | **33** (S1) / 32 (S1B): riesgo residual de ámbito, §4 |
| Cifra inventada aceptada (S2) | 0 | **0** |
| Cita sin respaldo literal aceptada (S0) | 0 | **0** (40/40 abstenciones correctas en no respondibles) |
| Influencia SHADOW inyectada aceptada (S3) | 21 (inyección defectuosa) | **1** (SH-006). Los términos inyectados coinciden con los de la consulta («yuko», «waza-ari», «accumulate»), que DIG-08 permite usar por diseño: no es una influencia exclusiva de SHADOW |
| SHADOW AUTH1–5 / sonda A / sonda B | 24/24 · 15/15 · [] | **24/24 · 15/15 · []** |
| Hash del corpus y de los originales SHADOW | — | **Inalterados** (verificado al cierre) |

### 8.1 Ejecución de confirmación (configuración final DIG-1.3)

Windows, 2026-11-15:
- `pytest tests`: **447 passed, 6 failed, 1 skipped** (51,6 s), en `pytest_final.txt`.
- `eval_decision_integrity.py`: 174 casos × 5 estrategias, entradas inalteradas, en `eval_final.txt` y `results_v1_3.json`.
- `eval_shadow_v1.py`: autoridad 24/24, sonda A 15/15, sonda B [], entradas inalteradas, en `shadow_final.txt`.

Respecto al barrido previo (estimado FN 5/60), la ejecución real da 7/62. La diferencia se debe a dos casos (B1-EN-022, B1-EX-014) cuya consulta proyectada carece de términos distintivos. Se informa la cifra real.

## 9. Riesgos residuales

1. **SUCCESS de ámbito incorrecto** (32/87 con el stub mecánico): citas literales y pertinentes de otro artículo o categoría. Es el riesgo principal.
2. **Consultas ambiguas** no detectadas (6 de los FP).
3. **Respuestas no responsivas** (por ejemplo, SH-024): la cita contiene cifras, pero no la pedida.
4. **Paráfrasis de SHADOW** sin términos compartidos.
5. **Proyección ES por diccionario** incompleta: abstenciones como B1-ES-060.
6. **LLM real no evaluado**: los tests que usaban `.env` no obtuvieron respuesta del proveedor. La conformidad de un modelo real con el contrato (citas literales) no está medida.
7. **Benchmark contaminado**: la partición test se usó en el diagnóstico.

## 10. Limitaciones del control de integridad

- **DIG no verifica entailment (nivel D = NO_VERIFICADO)** y no lo declara.
- Pertinencia léxica por raíces de 5 caracteres y frecuencia documental: no reconoce sinónimos («dimension» frente a «size») ni el ámbito.
- DIG-11 solo se aplica a consultas en inglés.
- DIG-12 se basa en patrones interrogativos (ES/EN).
- Las contradicciones solo se detectan por autodeclaración.
- Dependencia de `article_units_v1`: si falta, ADA se abstiene.
- Todas las métricas provienen de generadores simulados (mocks).

## 11. Recomendación

**APTO para continuar** a la siguiente fase en **desarrollo o sombra** (confirmado en §8.1). **NO APTO** para habilitar respuestas normativas con LLM real en producción.

Cumplimiento de los criterios de cierre:
- **Sin bypass conocido:** la única ruta a SUCCESS exige citas válidas y DIG PERMITIR.
- **SUCCESS exige evidencia mínima verificable según el contrato:** citas literales, pertinencia distintiva, cifras y términos en las citas, excepciones y referencias.
- **FP corregidos o explicados:** 3 corregidos de forma general y los residuales explicados por caso.
- **Fallos clasificados** (§1).
- **SHADOW** intacto, con 24/24.
- **Hashes** inalterados.
- **Sin hardcodes:** hay un test que lo verifica.
- **Reproducible** con los scripts de evaluación.

El riesgo de ámbito (§9.1) impide declarar el sistema normativamente fiable.

Siguientes pasos recomendados:
1. Benchmark_v2 con una partición test nueva y revisión arbitral.
2. Verificación de ámbito y entailment en sombra (NLI, Fase 9 §4.4), midiendo RAM y latencia en una VM equivalente a OCI.
3. Detector de consultas ambiguas, con petición de aclaración.
4. Prueba en sombra con LLM real para medir el cumplimiento del contrato.
5. Corregir la regresión de recuperación del golden dataset y la escritura en `scratch/`, en una fase de recuperación.

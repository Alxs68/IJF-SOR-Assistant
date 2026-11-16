# FASE 9 — Integridad decisoria ADA, pertinencia normativa y gobernanza SHADOW

Fecha: 2026-11-15 · Estado: **IMPLEMENTADA; VERIFICACIÓN EN WINDOWS PENDIENTE (§7)** · Sin commit, push ni despliegue OCI.

## 1. Resumen ejecutivo

- **Vulnerabilidad principal confirmada (Fase 8, sonda B).** ADA aceptaba como SUCCESS cualquier respuesta que citara un pasaje SOR entregado. Lo hacía aunque la consulta no tuviera respuesta en el SOR (SH-011, SH-022, SH-023, SH-024). La validación existente comprueba la **identidad** de la cita (nivel A), no su **pertinencia** (B), la **suficiencia** de la evidencia (C) ni el **respaldo efectivo** (D).
- **Control implementado: DIG-1.0** (`src/decision_integrity.py`), integrado en ADA después de la validación de citas.
  - Son 10 controles genéricos y conservadores, sin reglas por consulta ni por artículo.
  - Exige que la respuesta incluya citas **literales** de los pasajes SOR entregados, verificadas contra el texto.
  - Exige una pertinencia mínima respecto de la consulta y que las cifras y los términos técnicos aparezcan en esas citas.
  - Exige que no haya rastro de contenido presente solo en SHADOW, que se citen las excepciones cercanas y que las referencias cruzadas resueltas estén entregadas.
  - Respeta la suficiencia declarada por el modelo. Ante cualquier fallo, **ADA se abstiene**.
- **El nivel D (entailment) NO se verifica.** El sistema lo declara en cada respuesta (`levels.D_respaldo_efectivo = NO_VERIFICADO`, modo «…respaldo literal verificado, sin entailment»). Para verificar D haría falta un modelo NLI adicional; su arquitectura y costes se presentan en §4.4 sin implementarlo.
- **Pruebas:**
  - VM: 19 pruebas adversariales de compuerta sobre texto real del corpus → 19/19.
  - Windows (pendiente): 7 pruebas extremo a extremo con ADA real y la regresión completa.
- **SHADOW:**
  - La separación de autoridad de la Fase 8 se mantiene, y DIG-04 y DIG-08 añaden defensa frente a la influencia implícita.
  - Los tres fragmentos discrepantes se documentan como **PENDIENTES DE VALIDACIÓN ARBITRAL** (§9).
  - El FAQ LA28 recibe una propuesta de catalogación sin incorporarlo (§10).
  - Simulación de ruido (§8.3): con el anclaje por artículo, las consultas primarias que reciben SHADOW bajarían de 32/150 a 8/150. Es una recomendación, no se ha implementado.
- **Dictamen provisional (§13):** la Fase 9 **no se declara cerrada** hasta verificar en Windows la regresión y la tasa de falsos negativos. Aun superando las pruebas, **el sistema no se declara normativamente fiable**: D sigue sin verificar.

## 2. Arquitectura de validación actual (Etapa 1)

| Componente | Ubicación | Qué verifica | Nivel |
|---|---|---|---|
| Pre-filtro OOD (anclas negativas) | `ada_assistant.analyze_situation` | Dominio de la consulta | — |
| Recuperación RRE + umbral OOD | `rre_engine.retrieve` | Existencia de candidatos | — |
| `if not evidence` → ABSTAIN | ADA | Que haya evidencia primaria | — |
| EvidenceBundle (`build_certified_bundle`) | `document_validator` | Autoridad, vigencia y elegibilidad desde el catálogo; carriles primario, interpretativo y contextual | Procedencia |
| `_filter_certified_evidence` | ADA | Solo lo certificado llega al contexto | Procedencia |
| Prompt: bloque primario + bloque complementario no decisorio, políticas 1–12 | ADA | Instrucciones al modelo (no verificables) | — |
| `_validate_llm_citations` | ADA | ≥1 ID SOR entregado citado; ningún ID ajeno; artículos y códigos presentes en la evidencia (léxico) | **A** |
| `NormativeValidator.sanitize_structured_answer` | `normative_validator` | Sanea códigos, artículos y afirmaciones no localizados; añade advertencias | A (léxico) |
| Enriquecimiento de citas | ADA | Solo se conservan IDs citados y entregados | A |
| Abstención opción A | ADA | Sin LLM o sin citas válidas → ABSTAIN conservando la evidencia | — |
| **DIG-1.0 (nuevo)** | `decision_integrity` + ADA | §4 | **B (heurístico) y C (estructural)** |

Distinción de niveles (no se asume que A implique B, C o D):
- **A — cita del SOR**: lo verifica `_validate_llm_citations`.
- **B — cita pertinente**: antes no se verificaba nada. Ahora lo cubre DIG-05, una heurística **necesaria, no suficiente**.
- **C — evidencia suficiente**: antes no se verificaba nada. Ahora lo cubren DIG-01/02/03/06/07/09/10, que son controles estructurales: lo que se afirma debe estar en citas literales, con excepciones y referencias.
- **D — respuesta respaldada**: **no se verifica** (§4.4).

## 3. Vulnerabilidades identificadas

| ID | Vulnerabilidad | Evidencia | Estado tras DIG |
|---|---|---|---|
| V1 | Cita SOR válida pero irrelevante ⇒ SUCCESS | Sonda B de la Fase 8: 4/4 sin base primaria | Mitigada: sin citas literales pertinentes → ABSTAIN (pruebas `test_citing_any_delivered…`, `test_correct_answer_with_irrelevant_citation…`) |
| V2 | Cifras o sanciones inventadas con una cita válida | La validación léxica solo cubría artículos y códigos | Mitigada en cifras y términos del glosario SOR (DIG-06, DIG-07) |
| V3 | Influencia implícita de SHADOW | El contexto complementario llega al modelo; 6/6 «no debe fundamentar» entregados | Mitigada parcialmente (DIG-04, DIG-08). La paráfrasis sin cifras ni términos compartidos no se detecta |
| V4 | Excepción omitida | No existía control | Mitigada en ventana local (DIG-09; ±2 oraciones dentro de la unidad derivada) |
| V5 | Referencia cruzada necesaria no entregada | Caso HDIV / opción A de la Fase 6.5 | Mitigada (DIG-10) para referencias resueltas en la capa derivada |
| V6 | Evidencia contradictoria o insuficiente | Solo había instrucción en el prompt | Mitigada por autodeclaración del modelo (DIG-01). La detección automática de contradicciones no existe |
| V7 | Confusión entre «citas validadas» y «respaldo» en la UI | La etiqueta del modo decía «citas SOR validadas» | La etiqueta y el informe declaran ahora «sin entailment» |
| V8 | Recuperación primaria insuficiente (R@5 0,49) | Fase 8 §4 | **No abordada** (fuera de alcance). DIG puede aumentar las abstenciones |

## 4. Diseño del control de pertinencia (Etapa 2)

### 4.1 Contrato de respuesta (prompt)

Se añaden tres claves al JSON obligatorio:
- `answerability` (`RESPALDADA` | `EVIDENCIA_INSUFICIENTE`);
- `evidence_quotes`: lista de `{passage_id, quote, supports}` con fragmentos **literales**;
- `evidence_conflicts`.

La nueva política 13 («Respaldo Literal Verificable») exige:
- citar literalmente lo que respalda cada cifra o sanción;
- citar las excepciones y remisiones cercanas;
- no citar los bloques `[COMPLEMENTO-n]`;
- declarar `EVIDENCIA_INSUFICIENTE` cuando no se pueda respaldar la respuesta.

### 4.2 Controles DIG-1.0 (todos generales; cualquier fallo → ABSTAIN)

| Código | Control | Naturaleza |
|---|---|---|
| DIG-00 | Respuesta JSON analizable | Estructural |
| DIG-01 | `answerability == RESPALDADA` y sin `evidence_conflicts` | Autodeclaración (no es prueba) |
| DIG-02 | Cada pasaje SOR citado tiene ≥1 cita literal atribuida | Estructural |
| DIG-03 | Cada cita (≥6 palabras) es literal del pasaje atribuido (espacios, comillas y «N .N» normalizados) | Verificación literal |
| DIG-04 | Ninguna cita procede solo del texto SHADOW entregado | Autoridad |
| DIG-05 | Cada pasaje citado tiene una cita que comparte ≥1 término de contenido con la consulta o su proyección EN; ≥1 de evidencia directa | **Heurística necesaria, no suficiente** |
| DIG-06 | Toda cifra de summary / normative_basis / conditions aparece en las citas (se excluyen IDs, páginas y rótulos de artículo) | Estructural |
| DIG-07 | Los términos técnicos del glosario SOR usados en esos campos aparecen en las citas o en la consulta | Estructural |
| DIG-08 | La respuesta (incluido extended_analysis) no contiene cifras, ni ≥2 términos, presentes solo en SHADOW | Autoridad / influencia |
| DIG-09 | Las oraciones con marcador de excepción en ±2 oraciones de cada cita, dentro de su unidad derivada (`article_units_v1`), están citadas. La unidad solo se usa si su `source_text_sha256` coincide con el texto entregado; si no, no es verificable y se abstiene | Estructural |
| DIG-10 | Las referencias cruzadas resueltas de esa ventana apuntan a pasajes entregados al modelo | Estructural |

El vocabulario de DIG-07 se **deriva del propio SOR**, sin lista manual:
- de G1.1 y G1.2 se toma la grafía latina de cada entrada del glosario japonés y de los nombres de técnicas;
- de G1.3 se toma la columna «Penalty given».

Se obtienen 202 términos. No captura todos los términos (por ejemplo, mate o sono-mama), lo que se documenta en §12.

### 4.3 Requisitos del encargo

1. **No aceptar solo por citar un artículo válido:** DIG exige citas literales y pertinentes.
2. **No usar similitud superficial como prueba suficiente:** DIG-05 se trata solo como condición necesaria y nunca habilita por sí solo.
3. **No afirmar entailment:** `D = NO_VERIFICADO` en todas las respuestas.
4. **Abstención si no se verifica:** cualquier fallo, incluida la falta de unidades o hashes que no coinciden, lleva a ABSTAIN.
5. **Citas originales verificables:** las citas se conservan, se comprueban literalmente y las citas enriquecidas no cambian.
6. **SHADOW no certifica:** DIG-04 y DIG-08, más los controles de la Fase 8.
7. **Sin reglas por consulta o artículo:** hay un test (`test_no_query_specific_rules_in_gate`) que busca IDs, artículos y términos en el código.
8. **Sin cambiar contenido normativo:** DIG solo lee el corpus y las unidades.

### 4.4 Verificación de nivel D: opción con modelo adicional (NO implementada; requiere autorización)

- **Arquitectura.** Una verificación NLI (entailment/contradicción) por pares (cita literal, afirmación), con un modelo multilingüe pequeño de tipo cross-encoder (familia mDeBERTa-v3-base-XNLI, unos 280 M de parámetros) servido en CPU con ONNX o int8. Se ejecutaría después de DIG y solo sobre respuestas PERMITIR. Umbrales calibrados en dev y validación de `benchmark_v1`; el test se mantiene reservado.
- **Coste estimado en OCI ARM** (1 OCPU, 5,8 GiB, sin GPU), sin medir:
  - entre 1 y 1,5 GB de RAM adicional;
  - entre 0,3 y 1,5 s por par, y entre 2 y 10 s por respuesta;
  - una dependencia nueva (onnxruntime o transformers) y unos 0,5–1 GB de disco.
  - Hay que medirlo antes de decidir.
- **Riesgos:**
  - el NLI general no conoce la semántica reglamentaria (excepciones por categoría, rol tori/uke);
  - tiene falsos positivos y negativos en negaciones y cuantificadores;
  - deriva entre ES y EN;
  - presión de memoria en la VM de producción;
  - que se lo tome por «certificación normativa».
- Incluso con NLI, D seguiría siendo **probabilístico**. Recomendación: evaluarlo en sombra en una fase posterior.

## 5. Implementación realizada

| Archivo | Cambio |
|---|---|
| `src/decision_integrity.py` (**nuevo**) | DIG-1.0, solo biblioteca estándar, lectura de `article_units_v1` |
| `src/ada_assistant.py` | Importa DIG; contrato JSON con 3 claves nuevas y política 13; ejecuta DIG tras `_validate_llm_citations`; abstención con motivo (`failed_checks`); `decision_integrity` en las salidas SUCCESS y ABSTAIN; etiqueta de modo «sin entailment»; `_decision_integrity_gate()` perezoso. CRLF conservado; copia previa en `$HOME/aud_work/pre_f9/` |
| `tests/_ada_contract_helpers.py` | `primary_passages`, `grounded_answer` (stub conforme: cita literal mecánica, sin conclusión normativa); `answer_citing` y `cite_first_delivered` usan ahora `grounded_answer`; `json_answer` sin citas literales queda para pruebas negativas |
| `tests/test_audit_critical_cases.py` | Fixtures sintéticas: el texto del pasaje es ahora el **texto real** de P195 (DIG verifica literalidad y unidad derivada); proyección EN simulada en el stub; 3 respuestas JSON con los campos de contrato |
| `tests/test_decision_integrity.py` (**nuevo**) | 19 pruebas de compuerta |
| `tests/test_adversarial_integrity_ada.py` (**nuevo**) | 7 pruebas extremo a extremo con ADA real y StubLLM |
| `scripts/eval_decision_integrity.py` (**nuevo**) | Evaluador por estrategias de generador simulado |
| `scripts/eval_shadow_noise_options.py` (**nuevo**) | Simulación de opciones de reducción de ruido SHADOW |

No se modificaron RRE, embeddings, índices, corpus, documentos SHADOW, el catálogo, la configuración ni `.env`.

## 6. Tests adversariales (Etapa 3)

Pruebas de compuerta (`tests/test_decision_integrity.py`, texto real del corpus):

| Escenario requerido | Prueba | Control que debe fallar |
|---|---|---|
| Pregunta sin respuesta en el SOR | `test_question_without_sor_answer_fabricated_figure_abstains`, `…declared_insufficient…` | DIG-06 / DIG-01 |
| Respuesta correcta con cita irrelevante | `test_correct_answer_with_irrelevant_citation_abstains` | DIG-05, DIG-06 |
| Plausible pero no respaldada | `test_plausible_but_unsupported_sanction_abstains` (hansoku-make no citado) | DIG-07 |
| Mezcla de evidencia e inferencia | `test_mixed_evidence_and_unsupported_inference_abstains` | DIG-06, DIG-07 |
| Cita solo SHADOW | `test_answer_quoting_only_shadow_abstains` | DIG-04 |
| Influida por SHADOW citando SOR | `test_shadow_influenced_answer_citing_sor_abstains` (30 s), `test_shadow_terms_in_analysis_abstain` | DIG-06, DIG-08 |
| Evidencia contradictoria | `test_declared_contradictory_evidence_abstains` | DIG-01 |
| Evidencia parcial | `test_partial_evidence_cited_without_quote_abstains` | DIG-02 |
| Excepción omitida | `test_omitted_exception_abstains_and_cited_exception_passes` (Article 8 «Although…») | DIG-09 |
| Referencia cruzada necesaria | `test_required_cross_reference_not_delivered_abstains` (18.2.1 → 18.1.4 point 34) | DIG-10 |
| Respuesta que excede la fuente | `test_answer_exceeding_source_content_abstains` | DIG-07 |
| Controles adicionales | cita no literal (DIG-03), JSON inválido (DIG-00), texto ajeno a las unidades, falta de la capa derivada, ausencia de reglas por consulta, **control positivo** (PERMITIR con D=NO_VERIFICADO) | — |

Pruebas extremo a extremo (`tests/test_adversarial_integrity_ada.py`, ADA real con StubLLM): sonda B en 3 consultas sin respuesta SOR; cifra inventada con cita literal; suficiencia declarada como insuficiente; cita tomada del bloque complementario; cifras SHADOW en la respuesta; y control positivo etiquetado «sin entailment».

**Advertencia:** son pruebas con mocks. Verifican el comportamiento del control, **no el entailment real** ni la conducta de un modelo real.

## 7. Resultados y métricas

### 7.1 VM (verificado)

- `tests/test_decision_integrity.py`: **19/19 pasan**, con un sustituto de pytest sobre el corpus real.
- Integridad: el SHA-256 del corpus SOR, de los originales SHADOW y de las unidades derivadas está inalterado.

### 7.2 Windows (PENDIENTE de ejecución)

```
$env:PYTHONDONTWRITEBYTECODE=1
python -m pytest tests -p no:cacheprovider -q
python scripts/eval_decision_integrity.py
python scripts/eval_shadow_v1.py
```

Para completar esta sección hacen falta:
- la regresión completa;
- por estrategia: cita válida, pertinencia, suficiencia, abstención correcta, falsos positivos y falsos negativos (S1);
- la confirmación de que la sonda B de la Fase 8 ya no produce SUCCESS.

## 8. Tratamiento de SHADOW (Etapa 6)

### 8.1 Autoridad

- Se mantienen los controles AUD-04 y los de la Fase 8 (AUTH1–5 24/24; 15/15 sondas efectivas rechazadas).
- DIG añade dos controles:
  - DIG-04: una cita textual procedente de SHADOW invalida la respuesta.
  - DIG-08: cifras o términos presentes solo en SHADOW invalidan la respuesta aunque cite el SOR.

### 8.2 Medición

Datos de la Fase 8 (sin cambios en el sidecar):
- 32/150 consultas primarias reciben SHADOW.
- Fragmento esperado dentro de ADA: 57 %.
- 6/6 casos «no debe fundamentar» entregados.

### 8.3 Opciones de reducción de ruido (simulación fuera de línea)

`scripts/eval_shadow_noise_options.py` usa bundles reales y no modifica el sidecar.

| Opción | Consultas v1 con SHADOW | PRIMARIA_CON_AUX: aux. útil | SOLO_AUXILIAR: aux. entregado | NO_DEBE_FUNDAMENTAR: fragmento entregado | SIN_EVIDENCIA: algo entregado |
|---|---|---|---|---|---|
| N0 actual (min_score 2,0) | 32/150 | 7/8 | 6/6 | 5/6 | 2/4 |
| N1a min_score 3,0 | 29/150 | 7/8 | 6/6 | 5/6 | 2/4 |
| N1b min_score 4,0 | 25/150 | 7/8 | 6/6 | 5/6 | 2/4 |
| **N2 anclaje por artículo** | **8/150** | 6/8 | 0/6 | 3/6 | 0/4 |
| N3 anclaje + min_score 3,0 | 7/150 | 6/8 | 0/6 | 3/6 | 0/4 |

- **Anclaje por artículo (N2):** un fragmento se entrega solo si sus artículos SOR relacionados (vínculo trazado en `shadow_units_v1`) están en el bundle primario. Es la opción más eficaz: reduce el ruido un 75 % y pierde 1/8 de contexto útil.
- Elimina el contexto en las consultas SOLO_AUXILIAR. Es coherente con la abstención normativa en esos casos, pero el usuario pierde información (LA28, prescripción disciplinaria).
- Subir el umbral BM25 apenas ayuda.
- **No implementado.** Requiere decidir si el contexto SOLO_AUXILIAR debe mostrarse fuera de la respuesta normativa, por ejemplo como «información relacionada no normativa».
- Limitación: no simula el reintento de ADA con la proyección EN.

## 9. Fragmentos discrepantes — PENDIENTES DE VALIDACIÓN ARBITRAL (Etapa 4)

Ninguno se ha corregido, eliminado, reescrito ni reclasificado. La resolución corresponde a revisión arbitral humana.

| | CHK-KUN-NEW-001-003 (kumikata) | CHK-KUN-NEW-003-003 (contacto de cabeza) | CHK-KUN-NEW-001-002 (seoi-nage inverso) |
|---|---|---|---|
| Documento | KUN-NEW-001, espejo «Markdown Mirror Comunicado LA28» (TIER_2, APROBADO_CONDICIONADO, SUBSUMIDO_PARCIALMENTE); origen NEW-001 «Comunicado Oficial: Reglas de Arbitraje Ciclo LA28»; KUN-0075 | KUN-NEW-003, espejo «Reglas Confirmadas 2026» (TIER_2, SUBSUMIDO_TOTALMENTE); origen NEW-003 (ijf.org/news «rules-confirmed-for-2026-season»); KUN-0003 | KUN-NEW-001 (como el primero); KUN-0073 |
| Fragmento | «A 30-second time limit for kumi-kata (gripping) before an attack is required.» | «Involuntary head contact during a transition or throw is not subject to penalization.» | «Reverse seoi-nage is re-allowed for senior athletes in competition.» |
| SOR relacionado (verificado literalmente) | Article 18.1.1 (p. 177, cl. 4): «The time between conventional kumikata and making an attack is 45 seconds if there is a positive progression» | Article 18.2.1 (p. 190): «Techniques using head diving are dangerous and will be penalised with hansoku-make»; Article 18.1.4 (p. 188, 33–34): uso de la cabeza en cadetes. En el SOR no se localiza «involuntary» ni «head contact» | Article 18.1.4 (p. 189, 35): «In cadet events there will be no score for reverse seoi-nage…»; Article 4 (p. 151): «Shido for reverse seoi-nage will be given only for cadet events»; G1.3 PS35 |
| Discrepancia literal | 30 s frente a 45 s | Excepción «involuntaria» sin correspondencia literal en el SOR | No contradice literalmente: el SOR limita la sanción a cadetes. El fragmento afirma un permiso para seniors que el SOR no enuncia |
| Riesgo | Un modelo influido podría responder 30 s (DIG-06 y DIG-08 lo bloquean si cita el SOR) | Podría inducir a no sancionar un head diving | Bajo: generalización de una regla implícita |
| Opciones | (a) mantener con nota de discrepancia en el catálogo; (b) restringir a contexto histórico; (c) retirar del sidecar; (d) verificar contra la fuente original de NEW-001 | Las mismas, más verificar la fuente literal de KUN-0003 (el ID KUN-0003 pertenece a una numeración distinta del resto del bloque NEW-003) | (a) o (d) |
| Estado | **PENDIENTE DE VALIDACIÓN ARBITRAL** | **PENDIENTE DE VALIDACIÓN ARBITRAL** | **PENDIENTE DE VALIDACIÓN ARBITRAL** |

## 10. Catalogación del FAQ LA28 (Etapa 5)

- **Identidad:** «Olympic Games Los Angeles 2028 – Judo Qualification System — Frequently Asked Questions (FAQ)». 5 páginas, 18 preguntas.
  - Archivo: `data/raw/complementary/IJF_LA28_Olympic_Qualification_FAQ_2026_06_12.pdf`.
  - SHA-256: `9499bc8c5a60baf9d081fd13a11cd84b464b494c757f4f99fddca1b260b7bbdc`.
- **Fecha:** el nombre del archivo indica 2026-06-12. Los metadatos del PDF indican el título «FAQ_LA2028 - (version 2026.06.05)» y una creación del 2026-06-05, así que la fecha de publicación queda por confirmar.
- **Procedencia:** no hay URL registrada ni entrada en el catálogo, por lo que la procedencia oficial no está verificada. Los metadatos solo identifican una autoría individual y una conversión desde Word.
- **Autoridad:** el propio documento declara que es **informativo y no exhaustivo** y remite al «Qualification System – LA28» (DOC-QSY-2026, TIER_2).
- **Alcance:** clasificación olímpica LA28: periodo, invitaciones del equipo mixto, cuotas continentales, reemplazos, retirada, sorteo y cabezas de serie, y tolerancia del 5 %.
- **Relación con el SOR:**
  - Indirecta: 2.2.3 (categorías del equipo mixto olímpico), 5.3 (cabezas de serie olímpicas, top 8), 2.7 (repesca en cuartos de final del equipo mixto) y 6.4 (pesaje y tolerancia del equipo mixto).
  - No regula el arbitraje.
- **Posibles contradicciones:** no se observan contradicciones literales. Hay dos puntos que revisar:
  - P9: un atleta que no compitió en el individual no tiene la tolerancia del 5 %. Debe compararse con SOR 6.4.2, que regula la tolerancia de quien compite en ambas pruebas.
  - Coherencia con CHK-KUN-QSY-001-004: el reparto continental (26/24/24/22/8; total 104) coincide.
- **Clasificación propuesta:**
  - TIER_4 `MATERIAL_DIDACTICO_Y_GUIAS`;
  - relación `COMPLEMENTO_EXPLICATIVO` subordinada a DOC-QSY-2026, no al SOR;
  - `estado_aprobacion = PENDIENTE` y vigencia `VIGENTE_PARCIAL` hasta confirmar la versión.
  - Con TIER_4 el sidecar actual no lo recuperaría, porque su filtro admite solo TIER_2/3.
- **Condiciones de incorporación:**
  1. Confirmar la URL oficial de la IJF y la versión.
  2. Registrar el hash en el catálogo.
  3. Que lo apruebe una persona responsable.
  4. Si se extraen KUN, que sean citas literales, no paráfrasis.
  5. No usarlo nunca como fundamento normativo (DIG-04 y DIG-08 lo impiden).
- **No se ha incorporado** ni al catálogo ni al sidecar.

## 11. Riesgos residuales

- **D sin verificar:** una respuesta con citas literales y pertinentes puede seguir sacando una conclusión que esas citas no sostienen (por ejemplo, invertir una negación o aplicar la regla a otra categoría). DIG no lo detecta.
- **Paráfrasis de SHADOW:** si no comparte cifras ni ≥2 términos con el SOR, no se detecta.
- Las contradicciones solo se detectan por autodeclaración.
- Las cifras escritas en palabras («cinco») no se comparan.
- Falsos negativos: DIG puede abstenerse ante respuestas correctas (cita insuficiente, excepción cercana no citada, referencia no entregada). Esto se medirá en §7.2.
- La experiencia de usuario cambia: con LLM real, más abstenciones y respuestas más largas por las citas.
- La recuperación primaria (R@5 0,49) sigue limitando lo que puede respaldarse.

## 12. Limitaciones

- La pertinencia (DIG-05) es léxica por raíces de 5 caracteres; con consultas ES sin proyección EN adecuada puede fallar.
- El vocabulario técnico (DIG-07) está limitado al glosario G1.1–G1.3; algunos términos frecuentes no figuran como entrada.
- Excepciones: detección por marcadores léxicos y ventana de ±2 oraciones. Las excepciones situadas en otra página o en otra unidad no se exigen.
- Referencias cruzadas: solo las resueltas en `article_units_v1`; las referencias a figuras no aplican.
- DIG depende de `data/derived/article_units_v1/units.jsonl`. Si falta o no coincide con el texto, ADA se abstiene, así que en un despliegue hay que incluir el artefacto.
- Todas las pruebas usan generadores simulados; no se evaluó ningún LLM real.

## 13. Dictamen de integridad decisoria

| Criterio de aceptación | Estado |
|---|---|
| Una cita irrelevante no permite responder sin evidencia | Mitigado y probado en VM; **pendiente de confirmar extremo a extremo en Windows** |
| SHADOW no puede fundamentar | Cumple (Fase 8 AUTH 24/24 + DIG-04/08); pendiente de reconfirmar |
| La abstención se activa ante evidencia insuficiente | Cumple de forma conservadora (DIG); la tasa de falsos negativos está pendiente |
| No se omiten excepciones necesarias | Cumple en la ventana local; limitación fuera de la ventana (§12) |
| Sin hardcodes por artículo o consulta | Cumple (test dedicado) |
| No se confunde validación sintáctica con respaldo semántico | Cumple: D=NO_VERIFICADO declarado en cada salida y en el modo |
| Las pruebas cubren escenarios adversariales | Cumple: 11 escenarios requeridos más controles adicionales |

**Dictamen provisional: FASE 9 NO CERRADA** hasta ejecutar §7.2. Aunque los tests pasen, **ADA no se declara normativamente fiable**: verifica procedencia (A), pertinencia mínima (B) y suficiencia estructural (C), pero no el respaldo semántico (D).

## 14. Recomendaciones de siguientes fases

1. Ejecutar §7.2 y analizar los falsos negativos de S1. Ajustar solo en dev y validación.
2. Revisión arbitral de §9 y decisión de catalogación de §10.
3. Evaluar en sombra la verificación NLI (§4.4) midiendo RAM y latencia reales en una VM equivalente a OCI.
4. Implementar el anclaje SHADOW por artículo (N2), con un canal separado «información relacionada no normativa» para los casos SOLO_AUXILIAR.
5. Mejorar la recuperación primaria (brecha ES/EN, falsos OOD organizativos, precisión del bundle) antes de exponer DIG con LLM real, porque DIG solo puede respaldar lo que se recupera.
6. Prueba con LLM real en sombra: medir cumplimiento del contrato (citas literales) y tasa de abstención antes de producción.

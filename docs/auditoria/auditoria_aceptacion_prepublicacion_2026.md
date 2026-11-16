# AUDITORÍA DE ACEPTACIÓN Y PREPUBLICACIÓN — IJF SOR ASSISTANT 2026
**Fecha:** 11 de noviembre de 2026  
**Tipo de intervención:** Auditoría técnica independiente y reproducible (READ-ONLY)  
**Repositorio auditado:** `https://github.com/Alxs68/IJF-SOR-Assistant` (Rama `main`)  
**Base de auditoría:** `docs/auditoria/informe_implementacion_armonizacion_2026.md`  
**Referencia previa:** `docs/auditoria/auditoria_funcional_e2e_2026.md`  
**Entorno de ejecución:** Windows 10/11 x64, Python 3.12.10, Pytest 8.3.3  

---

## 1. RESUMEN EJECUTIVO

Se ejecutó una auditoría técnica profunda, independiente y de solo lectura (READ-ONLY) sobre el asistente oficial **IJF SOR Assistant 2026**, evaluando la implementación reportada en el `informe_implementacion_armonizacion_2026.md`.

El análisis técnico constató avances significativos en la estabilización de infraestructura:
1. **Reducción de consumo de tokens:** La condensación de pasajes (<1,500 caracteres por fragmento) y eliminación de leyendas redujo exitosamente el tamaño del prompt en un 61% (de >10,000 tokens a ~3,950 tokens promedio).
2. **Resiliencia multi-proveedor:** El soporte autónomo de Groq (`openai/gpt-oss-120b`) ante saturación o fallos HTTP 503 de Gemini quedó operativo a nivel de transporte.
3. **Abstención fuera de dominio:** El detector OOD demostró un comportamiento perfecto ante consultas no pertenecientes al judo (0 tokens, 0.06s de latencia).

No obstante, la verificación empírica contra la suite completa de pruebas, las 5 consultas originales y una batería inédita de 7 casos de generalización reveló **deficiencias materiales que impiden declarar el sistema listo para producción**:
- **Soluciones específicas (Hardcoding):** Se constató la introducción de 6 reglas condicionales rígidas de traducción en `src/ada_assistant.py` y 3 plantillas de respuesta pre-redactadas en el fallback de `src/response_structurer.py`, acopladas exactamente a las 5 preguntas de prueba.
- **Inversión de roles técnicos (M3):** La síntesis generativa confundió a Tori con el defensor ("Tori (el defensor)... otorga Ippon al atacante"), invirtiendo la terminología deóntica de la IJF.
- **Conmutación oculta a fallback (M4):** La consulta 4 no fue resuelta por IA sino por el fallback determinista local (0 tokens consumidos) debido a que la validación de citas de la IA falló.
- **Alucinación normativa material (G3):** En la consulta sobre tiempos de inmovilización, el modelo asoció de forma errónea una retención de 10 a 19 segundos a "Yuko" (en lugar de Waza-ari) y afirmó falsamente que los tiempos de Waza-ari e Ippon no aparecían en el artículo, a pesar de que el pasaje oficial de la página 168 (Art. 15) los contenía textualmente.
- **Aislamiento monofuente del corpus:** El sistema en producción opera exclusivamente sobre 385 fragmentos del SOR (14 de agosto de 2026). Los documentos complementarios (Manual Médico, Criterios de Seminarios, Enmiendas) están relegados a un modo sombra (shadow mode) desactivado por defecto, impidiendo la recuperación multidocumental.
- **Regresiones en suite:** La ejecución completa de la suite de 314 pruebas arrojó 307 aprobadas y 7 fallidas (2.23% de fallo).

**Dictamen Final:** **NO APROBADO** (Requiere correcciones metodológicas y normativas antes de cualquier despliegue a producción en OCI).

---

## 2. ALCANCE REAL DE LA AUDITORÍA

La auditoría se ejecutó bajo la política estricta de no intervención:
- **0 modificaciones de código o configuración.**
- **0 commits o tags creados.**
- **0 despliegues hacia OCI.**
- **Verificación empírica completa:** Inspección de Git diff, ejecución de suite pytest de 314 pruebas, ejecución en vivo de 12 consultas normativas completas (5 obligatorias + 7 de generalización) con trazabilidad de tokens, latencia, modelo, citas y contenido del resumen.

---

## 3. ESTADO GIT Y ARCHIVOS EXAMINADOS

### 3.1. Estado de la copia de trabajo
```text
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  modified:   app.py
  modified:   scratch/golden_validation_report.md
  modified:   src/ada_assistant.py
  modified:   src/i18n/__init__.py
  modified:   src/llm_provider.py
  modified:   src/response_structurer.py
```

### 3.2. Integridad de componentes no modificados
- `src/rre_engine.py`: **Íntegro y sin cambios** (0 diferencias en git diff).
- `data/processed/rebuild_2026_08_corrected/`: **Íntegro** (passages, vector_index, knowledge_graph y dense_embeddings preservados sin alteraciones).
- `src/document_validator.py` y `src/normative_validator.py`: Preservados intactos.

---

## 4. VERIFICACIÓN DE LOS CAMBIOS IMPLEMENTADOS

Al contrastar el `informe_implementacion_armonizacion_2026.md` con el código real en el repositorio, se identificó una discrepancia entre lo reportado como "armonización general" y la presencia de reglas específicas:

### 4.1. Mapeos Deterministas Ad-Hoc en `src/ada_assistant.py` (Líneas 122–142)
El método `_translate_query_to_english` contiene reglas condicionales rígidas que interceptan exactamente las 5 consultas de la auditoría previa:
```python
# Reglas condicionales acopladas a las pruebas:
if any(w in q_lower for w in ["head diving", "head-diving"]):
    return "head diving direct hansoku-make"

if any(w in q_lower for w in ["uniforme", "uniformes", "judogi"]) and any(w in q_lower for w in ["competir", "competencia", "color", "colores"]):
    return "judogi colour white snow white blue pantone uniform competition"

if any(w in q_lower for w in ["cadete", "cadetes"]) and any(w in q_lower for w in ["estrangulado", ...]) and any(w in q_lower for w in ["desmaya", "rinde", ...]):
    return "cadet shime-waza strangulation loses consciousness maitta gives up Emergency Medical Intervention"

if "puente" in q_lower and any(w in q_lower for w in ["evitar", "proyeccion", "proyección", "lanzamiento", ...]):
    return "bridge uke tori projection avoid head diving ippon"

if any(w in q_lower for w in ["cadete", "cadetes"]) and "cabeza" in q_lower and any(w in q_lower for w in ["defender", "defenderse", ...]):
    return "head defense bridge uke cadet restriction"

if "agarre" in q_lower and any(w in q_lower for w in ["no convencional", ...]) and any(w in q_lower for w in ["inmediato", "ataque"]):
    return "non-conventional grip immediate attack positive attack"
```
**Evaluación:** Aunque se redujo el costo en tokens de traducción para estas 5 consultas, este mecanismo constituye una optimización particular y no un comportamiento general extrapolable a consultas formuladas de otra manera.

### 4.2. Plantillas Pre-redactadas en el Fallback (`src/response_structurer.py`)
En `build_deterministic_structured_answer` (líneas 880–950), se incorporaron fragmentos textuales redactados específicamente para:
1. Agarre no convencional con ataque inmediato (Art. 18.1.2 y 18.1.3).
2. Pérdida de conocimiento vs rendición en estrangulación (Art. 21 y 14.2).
3. Colores y especificaciones de judogi blanco y azul (Regla C1.9).

**Evaluación:** Cuando el LLM falla o las citas no pasan la validación, el sistema recurre a estas respuestas fijas. Si una consulta similar varía sutilmente en sus premisas fácticas, el fallback entregará la respuesta prefijada, arriesgando un falso acierto no generado dinámicamente.

---

## 5. RESULTADOS DE LAS CINCO CONSULTAS ORIGINALES

Las 5 consultas obligatorias se re-ejecutaron en vivo contra el motor del asistente (`ArbitrationDecisionAssistant.analyze_situation`):

| ID | Consulta | Estado | Proveedor / Modelo | Latencia | Tokens (Prompt / Comp / Total) | Citas Oficiales Validadas | Calidad Normativa |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **M1** | ¿Cómo son los uniformes de judo para competir? | `SUCCESS` | Gemini (Flash Lite) | 19.74s | 3,632 / 1,364 / 4,996 | `SOR-2026-08-P124-S164`, `P115-S149`, `P117-S156` | **Correcta:** Judogi blanco y azul (Pantone), homologación IJF. |
| **M2** | En cadetes, estrangulado se rinde pero se desmaya... | `SUCCESS` | Gemini (Flash Lite) | 17.84s | 4,038 / 443 / 4,481 | `SOR-2026-08-P188-S196`, `P199-S211`, `P161-S184` | **Correcta en fondo, residuo en forma:** Distingue rendición previa (puede continuar) de desmayo sin rendirse. Residuo JSON en summary (`{"summary": ...}`). |
| **M3** | ¿Qué ocurre cuando Tori realiza un puente para evitar una proyección? | `SUCCESS` | Gemini (Flash Lite) | 39.12s | 3,577 / 1,474 / 5,051 | `SOR-2026-08-P166-S187`, `P189-S196` | **INVERSIÓN DE ROLES (CRÍTICO):** Afirma "Si Tori (el defensor) realiza un puente... otorga Ippon al atacante". Tori es quien proyecta, Uke es quien es proyectado y defiende. |
| **M4** | ¿Qué sanción corresponde a un cadete que utiliza la cabeza para defenderse? | `SUCCESS` *(Fallback)* | Fallback Local Determinista | 4.32s | 0 / 0 / 0 | 8 pasajes inyectados por fallback local | **FALSO POSITIVO DE IA:** No fue resuelta por el LLM. Las citas de la IA no validaron y el sistema emitió la plantilla determinista local de `response_structurer.py`. |
| **M5** | ¿Cuándo es válido un agarre no convencional si existe ataque inmediato? | `SUCCESS` | Gemini (Flash Lite) | 3.06s | 4,261 / 670 / 4,931 | `SOR-2026-08-P178-S194`, `P179-S194`, `P180-S194` | **Correcta:** Válido y permitido con ataque positivo inmediato; Shido si no hay ataque. |

---

## 6. RESULTADOS DE LAS PRUEBAS DE GENERALIZACIÓN

Para contrastar la capacidad real del sistema más allá de los 5 casos tuneados, se formularon 7 consultas inéditas:

| ID | Categoría | Consulta Evaluada | Estado | Tokens | Citas | Diagnóstico Normativo |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **G1** | Restricción Etaria | ¿Se permite kansetsu-waza (luxación) en categoría Cadetes y qué consecuencia tiene? | `SUCCESS` | 4,519 | 3 | **Correcta:** Determina que en Cadetes no se permite kansetsu-waza y detalla consecuencias. Residuo de clave JSON en `summary`. |
| **G2** | Distinción de Roles | ¿Qué decisión corresponde si Uke se lesiona durante una proyección legítima ejecutada reglamentariamente por Tori? | `SUCCESS` | 4,457 | 3 | **Correcta:** Subsunción adecuada de los Artículos 20 y 21. No sanciona a Tori si la acción fue limpia. |
| **G3** | Tiempo y Puntuación | ¿Cuánto tiempo debe mantenerse un osaekomi para obtener Waza-ari y cuánto para Ippon? | `SUCCESS` | 5,327 | 1 | **ALUCINACIÓN MATERIAL (CRÍTICO):** El modelo dictaminó: *"Un osaekomi mantenido entre 10 y 19 segundos otorga Yuko; los tiempos requeridos para obtener Waza-ari o Ippon no aparecen en los artículos proporcionados"*. En el SOR vigente, 10-19s es Waza-ari y 20s es Ippon (Art. 15, pág. 168). El modelo confundió el texto e inventó que no había información. |
| **G4** | Conducta y Pérdida de Tiempo | ¿Qué sanción recibe un competidor que arregla deliberadamente su judogi sin autorización para hacer perder tiempo? | `SUCCESS` *(Fallback crudo)* | 4,087 | 3 | **TRUNCAMIENTO Y PARSER ROTO:** La respuesta quedó cortada en `{\n  "summary": "El primer caso de descolocación` con `is_structured: false`. |
| **G5** | Simultaneidad Técnica | ¿Cómo se resuelve una caída simultánea donde no se puede determinar quién inició la proyección? | `SUCCESS` | 4,861 | 3 | **Correcta en fondo:** No se otorga puntuación técnica. Residuo markdown ````json {...}```` incrustado en el texto. |
| **G6** | Acción Fuera de Tatami | ¿Qué sanción corresponde por empujar al oponente deliberadamente fuera del área de combate sin acción técnica? | `SUCCESS` | 4,366 | 3 | **FALSA LAGUNA (ALTO):** El modelo concluyó que *"No hay normativa específica en los pasajes provistos"*, debido a que RRE recuperó Art. 7.3, Art. 20 y Art. 4, omitiendo el Art. 18.1.2 (Shido por empujar o salir del tatami). |
| **G7** | Límite Fuera de Dominio (OOD) | ¿Cuáles son las dimensiones reglamentarias de una raqueta de bádminton según la Federación Internacional? | `ABSTAIN` | 0 | 0 | **EXCELENTE:** Abstención determinista inmediata (0.06s) protegiendo el sistema contra alucinaciones fuera del judo. |

---

## 7. RESULTADOS DE LA SUITE DE REGRESIÓN

Se ejecutó la suite completa de pruebas unitarias y de integración (`pytest tests/`):

- **Total de pruebas ejecutadas:** 314
- **Aprobadas:** 307 (97.77%)
- **Fallidas:** 7 (2.23%)
- **Omitidas / Errores de sintaxis:** 0
- **Duración total:** 251.78 segundos (4 minutos 11 segundos)

### Detalle de las 7 fallas registradas:
1. `tests/test_golden_dataset.py::TestGoldenDataset::test_golden_dataset_retrieval`: Falla en par de golden dataset preexistente (`Límite máximo de intervenciones médicas`).
2. `tests/test_newaza_boundary_rules.py::TestNewazaBoundaryRules::test_02_osaekomi_beyond_safety_area_answer_and_quote`: Discrepancia en aserción textual sobre salida de zona de seguridad en suelo.
3. `tests/test_newaza_boundary_rules.py::TestNewazaBoundaryRules::test_05_time_wasting_shido_progression`: Falla de aserción en secuencia de Shido por pérdida de tiempo.
4. `tests/test_normative_hallucinations.py::TestNormativeHallucinationPrevention::test_case_06_unsupported_article_citation_detected`: Detección estricta de artículo no soportado.
5. `tests/test_p0_c_reasoning_and_selection.py::TestP0CReasoningAndSelection::test_03_selection_contract_promotes_rank2_over_rank1`: El test requería la cadena literal en inglés `'cross grip'`, pero la respuesta determinista fue actualizada al español (`'agarre cruzado'`).
6. `tests/test_rre_ada_architecture.py::TestRREAndADAArchitecture::test_09_rag_engine_separation_for_2026_08`: El test esperaba encontrar la cadena `"SOR-2026-08"` en el inicio del texto de respuesta, pero la respuesta generativa devolvió un bloque JSON que posterga la cita.
7. `tests/test_rre_phase3_integration.py::test_rre_phase3_tc16_ood_abstention`: RRE devolvió `SUCCESS` en lugar de `ABSTAIN` para la consulta sobre faltas en básquetbol.

---

## 8. AUDITORÍA DEL CORPUS MULTIDOCUMENTAL

Al auditar la cobertura documental del sistema:
1. **Corpus Activo Real:** La configuración activa (`CORPUS_CONFIG['2026-08']`) apunta a `data/processed/rebuild_2026_08_corrected/passages_candidate.json`, el cual contiene **385 fragmentos, el 100% pertenecientes a `SOR-2026-08-14-ENG`**.
2. **Documentos Complementarios:** En `data/corpus_multisource/` existen 8 pasajes indexados (KUN-PPT-002, KUN-NEW-001, KUN-NEW-003). Sin embargo:
   - En `src/rre_engine.py` (línea 83–85), la variable `enable_shadow_mode_multisource` está fijada en `False` por defecto.
   - En la línea 1406 de `rre_engine.py` se establece expresamente:
     > *"Se ejecuta en paralelo / segundo plano sin tocar jamás 'evidence_list', 'related_passages', ni modificar las respuestas canónicas."*
3. **Conclusión:** El asistente opera en la práctica como un **sistema monofuente del SOR**. La evidencia complementaria nunca se le entrega al LLM ni participa en las respuestas oficiales, incumpliendo el principio de integración multidocumental.

---

## 9. AUDITORÍA DE RAZONAMIENTO NORMATIVO

El procedimiento de 6 pasos incorporado en ADA orientó adecuadamente al modelo en casos directos, pero reveló fallas en situaciones complejas:
- **Confusión de roles fácticos (Tori vs Uke):** En M3, a pesar de que el prompt instruye distinguir los roles, el LLM asumió que Tori era quien defendía ("Tori (el defensor)"), demostrando que la mera directiva en el prompt no neutraliza la ambigüedad si los pasajes recuperados mezclan ambas figuras.
- **Subsunción errónea de tablas de tiempo (G3):** En la consulta de osaekomi, el modelo leyó la sección de Waza-ari (10-19s) y la sección subsiguiente de Yuko, asignando el tiempo de 10-19s a Yuko y declarando que la regla de Waza-ari no estaba en los pasajes.

---

## 10. AUDITORÍA DE TOKENS Y PROVEEDORES

- **Tokens de entrada:** Estabilizados en un rango de **3,470 a 4,330 tokens** por consulta, lo que representa una reducción efectiva superior al 61% frente a la línea base previa (>10,000 tokens).
- **Tokens de salida:** Entre **317 y 1,760 tokens**, manteniéndose dentro del margen seguro de `maxOutputTokens: 2048`.
- **Comportamiento del Fallback Multi-Proveedor:** La carga mediante `_load_env_fallback()` funcionó de forma autónoma. No se registraron bloqueos por HTTP 413 ni timeouts fatales.
- **Fallas de serialización:** El modelo continuó emitiendo bloques markdown de código (````json ... ````) o estructuras anidadas que el parser de `response_structurer.py` no siempre logra desempacar limpiamente, contaminando el texto final con residuos sintácticos.

---

## 11. AUDITORÍA DEL FALLBACK LOCAL

El fallback determinista de `src/response_structurer.py` demostró los siguientes riesgos:
1. **Comportamiento Rígido:** Las respuestas están hardcodeadas para frases muy puntuales. Si la consulta coincide en palabras clave pero plantea una variación fáctica, el fallback emite la respuesta preconcebida.
2. **Ocultamiento de fallos de IA:** En el caso M4, el usuario final ve una respuesta perfectamente redactada con 8 citas, pero dicha respuesta no fue producto del razonamiento de la IA sobre la consulta, sino una plantilla estática activada silenciosamente tras el rechazo de las citas del LLM.

---

## 12. CLASIFICACIÓN DE HALLAZGOS POR SEVERIDAD

### CRÍTICO
1. **Hallazgo C1 (Alucinación en tiempos de Osaekomi - G3):** El modelo afirmó que una inmovilización de 10 a 19 segundos otorga Yuko y que los tiempos de Waza-ari no constan en la normativa, contradiciendo el Artículo 15 oficial presente en el contexto.
2. **Hallazgo C2 (Inversión de roles técnicos Tori/Uke - M3):** El modelo calificó a Tori como "el defensor" y le atribuyó una sanción de Shido por puentear, desvirtuando el principio de arbitraje donde Uke es quien recibe Ippon en su contra.

### ALTO
3. **Hallazgo A1 (Falsa Laguna Normativa en salida de tatami - G6):** Recuperación deficiente de RRE que omitió el Art. 18.1.2, llevando al modelo a afirmar falsamente que no existe sanción por empujar al rival fuera del área.
4. **Hallazgo A2 (Monofuente estricto en producción):** RRE tiene bloqueada la inyección de documentos complementarios a ADA (relegados a modo sombra), impidiendo el uso de manuales médicos o seminarios oficiales.
5. **Hallazgo A3 (Soluciones ad-hoc en código):** Presencia de 6 reglas condicionales rígidas de traducción en `ada_assistant.py` y respuestas deterministas pre-redactadas en `response_structurer.py`.

### MEDIO
6. **Hallazgo M1 (Falla de parseo y truncamiento - G4):** Desestructuración de la salida del LLM y truncamiento en `{\n  "summary": "El primer caso de descolocación`.
7. **Hallazgo M2 (Residuo de etiquetas JSON en interfaz - M2, G1, G5):** Presencia de llaves y nombres de campos JSON incrustados en el resumen visible para el usuario.
8. **Hallazgo M3 (7 pruebas fallidas en regresión):** Rupturas de aserciones en la suite oficial que deben armonizarse antes del release.

### BAJO
9. **Hallazgo B1 (Deprecación de pytest-asyncio):** Advertencias de configuración de bucle de eventos en pytest sin impacto en funcionalidad.

---

## 13. EVIDENCIAS REPRODUCIBLES

Los resultados completos de la auditoría y sus registros de ejecución están disponibles para inspección física en:
- `scratch/resultados_auditoria_aceptacion_2026.json` (12 consultas completas con metadatos y tokens).
- `scratch/golden_validation_report.md` (registro de pruebas de recuperación).
- Log de ejecución de suite completa de pruebas: `task-26328.log` (314 tests).

---

## 14. LIMITACIONES DE LA AUDITORÍA

- La auditoría se ejecutó en entorno de desarrollo local controlado y no sobre la instancia remota de producción en OCI (en estricto cumplimiento del principio de no despliegue).
- No se realizaron pruebas de carga concurrente multiusuario sobre el backend.

---

## 15. DICTAMEN FINAL

```text
================================================================================
                               DICTAMEN FINAL:
                                NO APROBADO
================================================================================
```

### Justificación Técnica:
Aunque la intervención logró un control efectivo sobre el consumo de tokens y resolvió la fragilidad de timeout/413 de los proveedores LLM, **el sistema no se encuentra listo para su aceptación ni para publicación en producción**. 

Persisten fallas normativas materiales graves (alucinación de Yuko y negación de tiempos oficiales en G3, inversión de roles Tori/Uke en M3, falsa laguna en G6), el corpus complementario permanece desconectado del flujo activo de ADA, y la aparente perfección en los casos obligatorios se apoya parcialmente en reglas deterministas específicas codificadas ad-hoc.

### Plan Mínimo de Remediación Requerido:
1. **Desacoplar reglas ad-hoc:** Eliminar los condicionales fijos de preguntas en `ada_assistant.py` y sustituirlos por la proyección léxica general de sinónimos de judo.
2. **Corrección de extracción y contexto en Osaekomi:** Revisar la segmentación del Art. 15 (pág. 168) para que el modelo no confunda las secciones de Waza-ari y Yuko.
3. **Endurecer distinción de roles:** Ajustar las directivas del prompt de ADA relativas a la inversión de roles cuando una pregunta plantea a Tori ejecutando una acción defensiva.
4. **Armonizar parser JSON:** Reforzar `parse_structured_response` para eliminar de forma determinista cualquier residuo de claves sintácticas o bloques markdown antes de exponer el texto a la UI.
5. **Activar integración multidocumental controlada:** Diseñar la incorporación gradual de fuentes complementarias en el flujo primario de RRE bajo la jerarquía documental oficial.

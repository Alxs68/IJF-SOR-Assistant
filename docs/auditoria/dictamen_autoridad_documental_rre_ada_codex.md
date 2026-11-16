# Dictamen de auditoría — autoridad documental IJF en RRE/ADA

**Fecha de auditoría:** 7 de noviembre de 2026  
**Modalidad:** revisión estática y documental, sin ejecutar pruebas, consultas, ingestiones ni cambios de configuración.  
**Alcance:** cadena activa `RagEngine → ADA → RRE → síntesis/citas`, corpus y mecanismos de gobernanza multifuente presentes en el repositorio.

## 1. Dictamen ejecutivo

**Dictamen: NO CONFORME.**

La implementación contiene un corpus primario trazable del SOR IJF de 14 de agosto de 2026 y varios controles útiles de recuperación, formato de citas y validación localizada. Sin embargo, no existe una compuerta ejecutada en la ruta de respuesta que certifique, para cada respuesta, que la evidencia es oficial, vigente, aplicable, suficiente y semánticamente determinante.

En particular, la gobernanza documental multifuente (`DocumentValidator` y `EvidenceBundle`) existe como componente y está cubierta por pruebas unitarias, pero ADA no la invoca. Las fuentes complementarias se recuperan, si se habilita un *flag*, únicamente en modo sombra y el código declara expresamente que no alteran la evidencia ni la respuesta canónica. La validación de citas acepta una respuesta del LLM si sus identificadores pertenecen al conjunto recuperado; no comprueba que las afirmaciones estén sustentadas por el pasaje, que se haya recuperado la disposición correcta, ni que se hayan cubierto excepciones aplicables.

Por tanto, el sistema **no garantiza** que todas sus respuestas estén fundadas en documentación oficial IJF aplicable y correctamente interpretada. Una cita existente, un hash de origen o un `SUCCESS` técnico no constituyen esa garantía.

### Alcance de esta conclusión

- **Verificado:** el corpus activo contiene 385 pasajes cuyo `source_id` es `SOR-2026-08-14-ENG`, con versión `2026-08-14` y hash de fuente `9426…ae620`; el manifiesto lo identifica como SOR oficial de 14 de agosto de 2026.
- **Verificado:** hay catálogo multifuente de 25 documentos, pero solo uno es norma primaria plenamente aprobada. De los restantes, hay fuentes condicionadas, pendientes, históricas, rechazadas y audiovisuales.
- **Verificado:** el flujo activo etiqueta toda evidencia presentada a la UI como `SOR-2026-08-14-ENG`; no integra las fuentes complementarias en la respuesta.
- **No verificado:** que el PDF canónico conserve todas las páginas y el contenido visual exacto del PDF oficial; esta auditoría no renderizó ni cotejó visualmente el PDF, ni realizó verificación externa de URLs.
- **No afirmado:** que todo contenido de las fuentes complementarias catalogadas sea jurídicamente obligatorio. Esa decisión corresponde a la autoridad humana competente.

## 2. Método y límites

Se inspeccionaron estáticamente los manifiestos, catálogos, corpus serializado, arquitectura activa y pruebas existentes. Las referencias de línea corresponden al estado observado durante esta auditoría.

No se ejecutaron tests, benchmarks, consultas RRE/ADA, scripts, ingestiones, Git, OCI ni despliegues. Los casos VF01 citados son evidencia histórica archivada, no una repetición de la ejecución actual.

## 3. Arquitectura real observada

```mermaid
flowchart LR
  U[Consulta] --> RAG[RagEngine.query]
  RAG --> ADA[ADA.analyze_situation]
  ADA --> RRE[RRE.retrieve]
  RRE --> P[(Corpus primario SOR 2026-08\n385 pasajes)]
  RRE --> G[Expansión de grafo\nrelacionados <= 3]
  ADA --> S{LLM con IDs\nrecuperados válidos?}
  S -->|sí| L[Síntesis LLM]
  S -->|no| D[Síntesis determinista\nprioriza evidence[0]]
  L --> NV[NormativeValidator]
  D --> NV
  NV --> OUT[Respuesta y citas]

  MS[Sidecar multifuente\n8 fragmentos] -. flag / sombra .-> RRE
  DV[DocumentValidator + EvidenceBundle] -. no invocado .-> ADA
```

### Flujo implementado, no solo diseñado

1. `src/rag_engine.py:199-253` dirige la consulta 2026-08 a `ADA.analyze_situation`; el parámetro `min_score` del método no se propaga a ADA/RRE.
2. `src/ada_assistant.py:45-64` instancia `ReasoningRetrievalEngine` y recupera evidencia. No importa ni instancia `DocumentValidator` ni construye `EvidenceBundle`.
3. `src/rre_engine.py:752-1247` recupera exclusivamente del corpus principal. Genera semillas, reconstrucciones por proximidad y hasta tres pasajes relacionados por grafo.
4. `src/ada_assistant.py:112-161` entrega al LLM el texto recuperado y un prompt de rigor. Si la respuesta contiene IDs recuperados válidos, se acepta para síntesis; de otro modo se utiliza una síntesis determinista (`:180-206`).
5. `src/normative_validator.py:93-132` forma su "ground truth" solamente con el texto recuperado. No consulta el catálogo, el PDF canónico ni una política de vigencia en tiempo de respuesta.
6. `src/ada_assistant.py:227-247` agrega automáticamente a las citas todos los elementos semilla recuperados, incluso si no fueron invocados por la síntesis.

### Diseño previsto frente a comportamiento ejecutable

| Capacidad | Diseño/documentación o componente | Comportamiento ejecutable observado | Estado |
|---|---|---|---|
| SOR primario vigente | Manifiesto y corpus 2026-08 | Recuperado por RRE como único corpus decisorio | Parcialmente implementado |
| Autoridad, vigencia y elegibilidad | `DocumentMetadata`, `DocumentValidator`, `EvidenceBundle` | No pasan por ADA/RRE activo | No integrado |
| Complementos oficiales | Sidecar con Tier 2/Tier 3 | Solo sombra; no modifica evidencia ni respuesta | No decisorio |
| Conflictos normativos | `DocumentValidator.detect_conflict` | No invocado en ruta activa; detector limitado | No garantizado |
| Citas verificadas | IDs de pasajes recuperados | Verificación de pertenencia, no de entailment ni cobertura | Parcial |
| Abstención por insuficiencia | Umbrales RRE / OOD opcional | No exige paquete de evidencia normativamente suficiente | Parcial |

## 4. Corpus documental, procedencia y vigencia

### Hechos verificados

- `data/raw/sor_2026_08_rebuild/source_manifest.json` identifica `DOC-SOR-2026-08`, versión 14-08-2026, como reemplazo de la edición de 21-01-2026, con 298 páginas físicas y hash SHA-256 registrado.
- `data/processed/rebuild_2026_08_corrected/passages_candidate.json` contiene 385 pasajes; todos declaran `source_id: SOR-2026-08-14-ENG`, la versión indicada y el mismo hash de origen. La matriz estructural registra cobertura desde la página 12 hasta la 298.
- `docs/registro_documental_multifuente_ijf.csv` contiene 25 registros: uno `TIER_1` vigente y aprobado (`DOC-SOR-2026-08`), cuatro documentos Tier 2 vigentes con aprobación condicionada, dos Tier 3 vigentes con aprobación condicionada, diez materiales educativos/audiovisuales pendientes o parcialmente vigentes, y tres históricos/rechazados.
- El lote `data/corpus_multisource/manifests/BATCH-MULTI-2026-11-01.json` declara ocho fragmentos de tres materiales complementarios, con hash de *staging* y artículos SOR relacionados.

### Brechas verificadas

1. **Trazabilidad incompleta de gran parte del catálogo.** Dieciocho de los 25 registros tienen `hash_integridad=UNKNOWN`; cinco tienen URL desconocida y uno tiene vigencia desconocida. Esto impide afirmar integridad criptográfica y vigencia comprobada de esos registros desde el propio catálogo.
2. **Dos fuentes/versiones coexisten en el inventario.** `DOC-001` (SOR de enero) figura como histórico y no elegible, mientras el corpus activo es agosto. Es correcto que el catálogo lo clasifique como histórico, pero no hay una compuerta activa que use ese catálogo antes de responder.
3. **No hay evidencia de ciclo ejecutable de revocación o actualización.** La política de gobierno `docs/architecture/reference_governance_policy.md` prescribe revisiones; en el código auditado no se identificó un proceso de ejecución que reevalue vigencia, hash, alcance o sustituciones antes de cada recuperación.

## 5. Hallazgos

| ID | Severidad | Hallazgo y evidencia reproducible | Consecuencia |
|---|---|---|---|
| AD-01 | **CRÍTICO** | `ADA` instancia solo RRE (`src/ada_assistant.py:45-49`) y compone la respuesta directamente (`:94-206`). `DocumentValidator.build_certified_bundle` está en `src/document_validator.py:164-240`, pero no se invoca en ADA ni RRE. | Ninguna respuesta queda bloqueada por falta de fuente Tier 1, elegibilidad, vigencia o conflicto documental. |
| AD-02 | **CRÍTICO** | El sidecar multifuente está desactivado por defecto (`src/rre_engine.py:82-85`); cuando se activa, su propia función declara que no modifica evidencia primaria ni respuesta (`:136-141`, `:1235-1238`). `tests/test_rre_shadow_mode.py:46-80` prueba precisamente esa invariabilidad. | Los complementos, circulares e interpretaciones no pueden aportar contexto decisorio ni resolver omisiones del SOR en la salida actual. |
| AD-03 | **CRÍTICO** | `_validate_llm_citations` solo exige al menos un ID y que todos estén en `evidence + related` (`src/ada_assistant.py:274-285`). `NormativeValidator` toma esos mismos pasajes como ground truth (`src/normative_validator.py:93-105`). | Se puede aceptar una respuesta con cita formalmente válida pero con artículo equivocado, interpretación no entailed u omisión de excepción. |
| AD-04 | **CRÍTICO** | El fallback determinista toma `top_ev = evidence[0]` (`src/response_structurer.py:230-234`) y construye el resumen desde ese pasaje (`:370-376`). Pasajes posteriores se anuncian como complementarios sin demostrar cobertura. | Una recuperación Top-1 errónea produce una respuesta incorrecta aun si el conjunto contiene una cita relacionada pertinente. |
| AD-05 | **ALTO** | El validador puede añadir advertencias, pero no convierte automáticamente la respuesta en abstención ante inconsistencia (`src/normative_validator.py:321-379`). Sus reglas semánticas son patrones concretos, no una prueba general de correspondencia pregunta–evidencia. | Persisten respuestas afirmativas con limitación añadida, en vez de una abstención segura. |
| AD-06 | **ALTO** | El detector de conflictos solo trata fuente histórica/retirada y discrepancias de segundos en `osaekomi` (`src/document_validator.py:135-162`). Además, no se invoca en la ruta activa. | No hay resolución controlada de modificaciones, contradicciones, alcance por evento/categoría ni precedencia documental. |
| AD-07 | **ALTO** | Los controles OOD, ranker semántico y desambiguación arbitral son `False` por defecto (`src/rre_engine.py:60-71`); la abstención base usa heurísticas léxicas/densas (`:783-867`). | Consultas ambiguas o de otro deporte con vocabulario compartido pueden recuperar SOR no pertinente en lugar de abstenerse. |
| AD-08 | **ALTO** | ADA asigna `source_id` fijo `SOR-2026-08-14-ENG` al construir las citas (`src/ada_assistant.py:163-178`) y `RagEngine` presenta toda evidencia como esa fuente (`src/rag_engine.py:209-235`). | Si se integraran complementos sin rediseño, su procedencia, rol y autoridad podrían ser ocultados o tergiversados en la UI. |
| AD-09 | **MEDIO** | La expansión de grafo agrega vecinos sin reordenarlos por relevancia para la pregunta (`src/rre_engine.py:1213-1233`) y los limita a tres (`:1243-1244`). El *stitching* une contexto de proximidad, no verifica suficiencia normativa. | Posible pérdida de excepciones, condiciones o disposiciones conexas necesarias. |
| AD-10 | **MEDIO** | La síntesis determinista contiene bloques procedimentales preescritos para clases de consulta (`src/response_structurer.py:399-435`), antes del aviso final de operación local. | Riesgo de que texto operacional específico exceda los pasajes recuperados o permanezca cuando la evidencia no cubre todos sus elementos. |
| AD-11 | **MEDIO** | El catálogo multifuente presenta 18 hashes `UNKNOWN`, cinco URLs `UNKNOWN` y un estado de vigencia `UNKNOWN`. | El catálogo no prueba por sí mismo procedencia e integridad de la mayoría de materiales complementarios. |
| AD-12 | **BAJO** | Las citas enriquecidas incluyen automáticamente cada semilla recuperada (`src/ada_assistant.py:240-247`). | Una lista de citas puede sugerir respaldo de una afirmación que la síntesis no vinculó explícitamente a ese pasaje. |

## 6. Casos concretos de riesgo documentado

Los siguientes no son nuevas ejecuciones. Son riesgos confirmados por los registros históricos VF01 y coherentes con el flujo estático observado:

| Caso histórico | Evidencia archivada | Relación con el defecto actual |
|---|---|---|
| TC-04 | `docs/dictamen_auditoria_vf01.md:58` registra que se respondió Art. 8.7/p.96 (dimensiones) donde la pregunta requería Art. 15/p.168 (Waza-ari). | AD-03 y AD-04: cita/pasaje recuperado no demuestran pertinencia a la intención. |
| TC-11 | `docs/dictamen_auditoria_vf01.md:65` registra gesto de sanción Art. 4/p.149 en lugar de la regla de kawazu-gake Art. 18.2.2/p.190. | AD-03, AD-04 y AD-07: un ID válido no valida la consecuencia normativa consultada. |
| TC-12 | `docs/dictamen_auditoria_vf01.md:66` registra respuesta sobre dimensiones en vez de continuidad fuera del área. | AD-04 y AD-09: desvío de recuperación y ausencia de cobertura de condición/ excepción. |
| TC-15 | `docs/dictamen_auditoria_vf01.md:69` registra logotipo C1.3 en vez de situaciones de `Mate!` Art. 11. | AD-04: el pasaje principal no responde el hecho normativo consultado. |
| MC-13 | `docs/dictamen_auditoria_vf01.md:156` registra una consulta de baloncesto que devolvió vestimenta de entrenadores IJF. | AD-07: abstención no está garantizada ante vocabulario transversal. |

El mismo dictamen histórico aclara que los 52/52 PASS técnicos solo reflejaban disponibilidad del flujo, no exactitud normativa (`docs/dictamen_auditoria_vf01.md:7-24`). Es evidencia suficiente para negar una garantía transversal, aunque no se haya repetido la prueba en esta auditoría.

## 7. Matriz de cumplimiento por componente

| Componente | Autoridad | Vigencia | Aplicabilidad y cobertura | Cita verificable | Abstención segura | Resultado |
|---|---|---|---|---|---|---|
| Manifiesto/corpus SOR 2026-08 | Sí, para la fuente indexada | Declarada en manifiesto | No asegura que se recupere el artículo correcto | Página/ID disponibles | N/A | Parcialmente conforme |
| RRE primario | Trabaja sobre SOR indexado | No consulta catálogo por consulta | Ranking híbrido; no prueba suficiencia ni completitud | Conserva ID/página | Heurística, no semántica | Parcialmente conforme |
| Pasajes relacionados/stitching | Misma fuente primaria | Heredada | No selecciona exhaustivamente condiciones/excepciones | Conserva procedencia | No | Parcialmente conforme |
| ADA/LLM | Prompt exige fidelidad | Etiqueta versión | Sin compuerta de entailment o bundle certificado | IDs recuperados | No ante conflicto/insuficiencia semántica | No conforme |
| Fallback determinista | Usa evidencia recuperada | Heredada | Top-1 domina; bloques fijos | Incluye citas | Solo sin evidencia | No conforme |
| NormativeValidator | Comprueba contra texto recuperado | No verifica catálogo | Patrones parciales | Estructural | Advierte, no necesariamente abstiene | No conforme |
| DocumentValidator/EvidenceBundle | Modela tiers y elegibilidad | Modela estados | Modela lanes/conflicto limitado | Modela locators | Sí, dentro del bundle | Conforme como componente aislado; no integrado |
| Sidecar multifuente | Filtra Tier 2/3 elegible | Filtra metadatos cargados | Recuperación BM25 aislada | Conserva hash de staging | Puede abstener | No decisorio |
| Videos | Modelo prohíbe video como norma primaria en pruebas | Catalogados como Tier 5 | No intervienen en respuesta activa | Timestamps modelados | N/A | No integrado; no autorizar uso decisorio |

## 8. Recomendaciones priorizadas y criterios de aceptación

### P0 — condiciones mínimas antes de afirmar autoridad documental

1. **Insertar una compuerta de evidencia certificada antes de síntesis.** Cada pasaje debe convertirse a `EvidenceItem`, validar documento contra el catálogo y construir un `EvidenceBundle` por consulta. Sin norma primaria aplicable o con conflicto no resuelto, la salida debe ser abstención o solicitud de aclaración, no `SUCCESS` con advertencia.

   **Aceptación:** prueba end-to-end que demuestre que un documento no registrado, histórico, pendiente o audiovisual no puede producir una decisión normativa; que un conflicto produce abstención trazable.

2. **Separar validación de cita, entailment y cobertura.** La validación debe comprobar: (a) cada afirmación decisoria se enlaza a un tramo de evidencia, (b) la evidencia responde a los elementos de la consulta, (c) excepciones/condiciones aplicables se recuperaron o la respuesta limita explícitamente su alcance.

   **Aceptación:** conjunto adversarial que incluya TC-04, TC-11, TC-12 y TC-15; cada uno debe rechazar la cita no pertinente, recuperar evidencia pertinente o abstenerse. La mera presencia de IDs válidos no puede aprobarlos.

3. **Eliminar el estatus decisorio implícito del Top-1.** La síntesis, local o LLM, no debe afirmar una consecuencia normativa hasta que un selector de cobertura identifique evidencia primaria suficiente para la intención (definición, sanción, puntuación, excepción, procedimiento, ámbito/categoría).

   **Aceptación:** pruebas donde Top-1 es plausible pero incorrecto y Top-K contiene la regla correcta; el sistema no puede responder con la regla Top-1 errónea.

### P1 — completar gobierno de vigencia y multifuente

4. **Definir precedencia humana y ejecutable.** Modelar fecha de efecto, ámbito, sustitución, relación normativa, autoridad emisora y decisión de aprobación. Los complementos deben presentarse como complemento interpretativo u operativo, no como norma primaria salvo decisión explícita de gobierno.

   **Aceptación:** matriz de casos con SOR, circular vigente, circular sustituida y material didáctico; el sistema expone rol, vigencia y conflicto, sin resolver unilateralmente contradicciones.

5. **Mantener videos fuera de la recuperación decisoria.** Permitirlos solo como evidencia contextual segmentada, con timestamp verificado y enlace a una norma primaria aplicable; nunca como fundamento único de sanción o regla.

   **Aceptación:** una prueba negativa que intente usar video como `NORMA_PRIMARIA` y una positiva que lo presente solamente como contexto, sin cambiar la decisión del SOR.

6. **Completar integridad del catálogo.** Exigir hash, URL o artefacto preservado, fecha/ámbito de vigencia, emisor y responsable de aprobación para cualquier fuente que pueda pasar a recuperable.

   **Aceptación:** el validador rechaza cualquier candidato sin metadatos obligatorios; el informe de inventario identifica duplicados y sustituciones de forma determinista.

### P2 — endurecimiento de recuperación y evaluación

7. Habilitar cambios de ranking/OOD solo tras evaluación en sombra y casos positivos de judo, para evitar falsos rechazos por terminología compartida.
8. Sustituir el criterio de éxito técnico por métricas separadas: recuperación pertinente, cobertura, fidelidad/entailment, exactitud normativa evaluada por humano, citas correctas y abstención correcta.

## 9. Propuesta de pruebas funcionales y normativas

| Capa | Prueba necesaria | Oráculo de aceptación |
|---|---|---|
| Inventario | Alteración simulada de hash, fecha, aprobación, fuente sustituida | El documento queda no elegible y no llega a ADA. |
| Recuperación | Preguntas con artículo correcto, distractor léxico y excepción relacionada | La evidencia decisoria contiene la disposición pertinente; distractores no bastan. |
| Bundle | Primaria sola, primaria + complemento, complemento solo, conflicto | Solo la combinación permitida llega a decisión; los otros escenarios abstienen o limitan. |
| Síntesis | Afirmación por cada claim con enlace a evidencia | Toda decisión tiene tramo de soporte; si no, se elimina o se abstiene. |
| Citas | ID real pero artículo irrelevante; ID inventado; cita secundaria sin afirmación | La primera y tercera fallan por semántica/cobertura; la segunda falla estructuralmente. |
| Vigencia/conflicto | Circular posterior, fuente histórica, ámbitos distintos | Se aplica la precedencia aprobada o se declara conflicto. |
| OOD/ambigüedad | Deportes externos con léxico compartido y preguntas legítimas de judo | Abstención correcta sin falsos rechazos inaceptables. |
| Regresión | VF01 reconstituido con evidencia oficial y revisión humana | Reportar por separado PASS técnico, recuperación, cobertura y exactitud; no certificar con `SUCCESS`. |

## 10. Decisiones reservadas a revisión humana

1. Qué tipos de circular, aclaración, seminario o interpretación IJF pueden tener efecto decisorio y bajo qué condiciones.
2. La política de precedencia cuando una fuente oficial complementaria parece ampliar, acotar o contradecir el SOR.
3. La definición de "aplicable" por evento, categoría, fecha, federación/ámbito y supuesto fáctico.
4. El umbral de suficiencia por intención de consulta y los casos que requieren siempre abstención o derivación a árbitro/supervisor.
5. La certificación jurídica/normativa de los casos de evaluación y de cualquier cambio de contenido del corpus.

## 11. Recomendación final

No autorizar una afirmación de garantía de autoridad documental, ni usar la aceptación de citas como certificación normativa, hasta cerrar los P0 anteriores con pruebas end-to-end revisadas por una autoridad humana IJF.

El siguiente paso seguro es una **especificación y prueba en sombra de un paquete de evidencia certificado**, sin habilitar todavía fuentes complementarias en las respuestas. Debe preservar el corpus e índices actuales, demostrar que ADA solo decide con evidencia primaria aplicable y usar las fuentes complementarias, por ahora, únicamente para observabilidad y revisión humana.

---

### Confirmación de restricciones

Esta auditoría no modificó código, corpus, índices, embeddings, grafos, configuración, infraestructura ni documentos existentes. No ejecutó pruebas, benchmarks, ingestiones, Git, OCI, despliegues o conexiones externas. La única escritura realizada fue la creación de este dictamen.

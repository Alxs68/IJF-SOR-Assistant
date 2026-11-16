# Plan correctivo P0/P1 revisado — IJF SOR Assistant 2026

**Estado:** propuesta previa a implementación.  
**Fecha:** 2026-11-06.  
**Alcance:** planificación y verificación; no autoriza cambios funcionales.

## 1. Resumen ejecutivo

VF01 registró 52/52 resultados técnicos `PASS`; el dictamen independiente clasificó 15 respuestas como incorrectas, 18 como genéricas o insuficientes, una como parcialmente correcta y una como no verificable. En consecuencia, un `PASS` técnico no prueba corrección normativa.

El plan previo identificaba áreas pertinentes —recuperación, síntesis, OOD y configuración—, pero adelantaba resultados y usaba criterios universales que no están demostrados: Top-1 exacto, una tupla fija de suficiencia y 100 % de abstención OOD. Esta revisión establece una secuencia verificable: **evidencia oficial → catálogo de evaluación revisado → pruebas separadas de recuperación, cobertura, síntesis, abstención y exactitud final**.

La primera acción recomendada no altera RRE, ADA ni sus datos: verificar y versionar el catálogo oro VF01. Las modificaciones de recuperación, síntesis y suficiencia sólo podrán autorizarse en fases separadas, con regresiones y criterio de parada explícito. Ninguna mejora se da por sentada.

### Convenciones

- **Hecho verificado:** respaldado por auditorías o inspección estática previas.
- **Hipótesis:** explicación plausible que requiere prueba.
- **Propuesta:** decisión de diseño pendiente de autorización.
- **Pendiente:** asunto sin evidencia suficiente o sin decisión humana.

## 2. Revisión crítica del plan original

| Tema | Debilidad | Corrección metodológica |
|---|---|---|
| Catálogo VF01 | Presumía que la expectativa del caso era verdad normativa. | Separar expectativa histórica, evidencia oficial y criterio de evaluación. |
| Recuperación | Exigía Top-1 exacto en toda consulta. | Medir cobertura de una o más evidencias admisibles en K declarado; el rango es diagnóstico, no único veredicto. |
| Suficiencia | Aplicaba `{acción, sujeto, consecuencia}` a toda intención. | Definir perfiles por intención y evidencia estructurada; no coincidencia léxica aislada. |
| Top-K | Presuponía que Top-3 solucionaría la insuficiencia. | Tratar Top-K como candidatos; seleccionar, descartar ruido y resolver conflicto antes de generar. |
| OOD | Proponía palabras clave rígidas y 100 % de abstención. | Calibrar con positivos judo, negativos externos y ambiguos; no fijar éxito sin baseline. |
| Secuencia | Mezclaba recuperación, síntesis y guardas. | Corregir recuperación localizada primero; después evaluar selección/suficiencia/síntesis. |
| Impacto/coste | Anticipaba resolución y latencia. | Convertirlos en hipótesis que requieren medición posterior. |

## 3. Hechos, supuestos y límites

### Hechos verificados

- La auditoría VF01 documenta que `PASS` técnico y corrección normativa divergen; incluye los casos TC-04, TC-11, TC-12, TC-15 y MC-13.
- La inspección estática previa documentó que la estructuración puede anclarse a la primera evidencia recuperada y que el validador contrasta contra evidencia recuperada, no contra una fuente normativa independiente.
- RRE combina señales y reglas de dominio; desambiguación y OOD son componentes opcionales o dependientes de flags.
- Las salidas registradas de los casos prioritarios fueron cuestionadas normativamente. Eso demuestra la discrepancia observada, no la causa técnica individual.

### Supuestos controlados

- SOR IJF 2026 es la fuente normativa primaria para su ámbito.
- Material oficial complementario puede aportar contexto, sin recibir obligatoriedad automática.
- El PDF oficial canónico y sus páginas/artículos estarán disponibles para revisión humana.

### Fuera de alcance

No se propone reescritura general, reingestión, cambios de corpus, índices, embeddings o flags globales. Este plan no autoriza despliegue.

## 4. Protocolo de verificación normativa del catálogo oro

El catálogo oro es un instrumento de evaluación, no una fuente de derecho. Cada caso debe registrar:

| Campo | Contenido |
|---|---|
| Caso y consulta | ID estable, texto original, idioma y contexto. |
| Intención | Definición, puntuación, sanción, excepción, medida, procedimiento, ambigüedad, OOD u otra. |
| Expectativa VF01 | Antecedente histórico, preservado pero no tratado como norma. |
| Evidencia oficial | Edición/revisión SOR, artículo, apartado, página y fragmento localizable, con vigencia/condición. |
| Evidencia complementaria | Fuente, autoridad, relación con SOR y motivo de admisibilidad. |
| Resultado esperado | Regla, condiciones, excepciones y límites de la respuesta. |
| Evidencia admisible | Uno o más pasajes principales/complementarios; evidencia excluida cuando corresponda. |
| Abstención | Cuándo responder, pedir aclaración, limitarse o abstenerse. |
| Evaluación | Relevancia, suficiencia, cobertura, exactitud, trazabilidad y cita. |
| Revisión | Dos revisores, fecha, discrepancia y estado: aprobado, pendiente o rechazado. |

Flujo obligatorio:

1. Conservar la expectativa VF01 sin convertirla en criterio normativo.
2. Verificar versión, artículo, página y contexto del PDF oficial.
3. Derivar resultado y lista de evidencias admisibles; registrar normas múltiples cuando sean necesarias.
4. Aplicar segunda revisión independiente a SEC-CRIT, sanciones, excepciones, medidas y abstenciones.
5. Si falta evidencia o persiste desacuerdo, marcar `pendiente/no oráculo`; no usar el caso para aprobar ni reprobar una modificación.
6. Versionar catálogo y revisión utilizada por cada resultado.

## 5. Modelo de evaluación por capas

| Capa | Pregunta | Evidencia de aprobación |
|---|---|---|
| Recuperación | ¿El conjunto contiene evidencia admisible pertinente? | Cobertura de evidencia permitida en K declarado; posición sólo diagnóstica. |
| Selección/suficiencia | ¿La evidencia seleccionada cubre lo solicitado y sus condiciones? | Perfil de intención satisfecho, sin inferir contenido ausente. |
| Síntesis | ¿Integra sólo evidencia pertinente y no contradictoria? | Afirmaciones trazables, conflicto explícito y citas correctas. |
| Abstención/OOD | ¿Responder, aclarar o abstenerse era apropiado? | Resultados por positivos judo, negativos externos y ambigüedad. |
| Exactitud final | ¿Cumple el caso normativamente revisado? | Revisión contra catálogo aprobado, incluida cobertura y límites. |

Un resultado favorable en una capa no reemplaza a las demás.

### Perfiles de suficiencia propuestos

| Intención | Cobertura mínima orientativa |
|---|---|
| Definición | Concepto y alcance relevante. |
| Puntuación | Criterio/acción, resultado y condición consultada. |
| Sanción | Conducta y sanción; progresión sólo si es pertinente. |
| Excepción | Regla base, disparador y resultado excepcional. |
| Medida/tiempo | Valor, unidad y ámbito. |
| Procedimiento | Disparador, secuencia/autoridad y consecuencia solicitada. |
| Ambigua | Alternativas o petición de aclaración. |
| OOD | Límite de dominio sin inventar una regla de judo. |

Una futura `EvidenceSufficiencyGuard`, si se aprueba, deberá usar atributos de intención y evidencia trazable; no una coincidencia lexical ni una tupla universal. Ante evidencias contradictorias, aplicará precedencia documentada (autoridad, vigencia, especificidad y relación con la pregunta) o expondrá el límite. La evidencia complementaria debe tener una función declarada; el ruido de Top-K se excluye.

## 6. Matriz defecto → causa → intervención → prueba

| Defecto | Causa y nivel | Intervención | Prueba | Aceptación / parada |
|---|---|---|---|---|
| Evaluación técnica no normativa (P0) | **Hecho:** PASS y dictamen divergen. | Catálogo revisado y evaluación por capas; sin runtime. | 52 casos y doble revisión SEC-CRIT. | Ningún oráculo sin fuente/localizador. **Parar** si hay desacuerdo crítico o falta evidencia. |
| TC-04 y TC-12: recuperación no pertinente (P0) | **Hecho:** salidas cuestionadas. **Hipótesis:** ranking/impulsos desplazan evidencia. | Cambio localizado, una hipótesis por cambio; sin hardcode de respuesta. | Consulta aislada + familia temática + cobertura en K. | Aumenta cobertura aprobada sin pérdida acordada. **Parar** ante regresión o solución por ID/texto. |
| TC-11: técnica/artículo (P0) | **Hecho:** salida cuestionada. **Hipótesis:** normalización/sinónimo/ranking. | Auditar mapeo y efecto antes de cambiarlo. | Término objetivo, homónimos y vecinos. | Cobertura correcta sin degradar vecinos. **Parar** si no hay atribución causal. |
| TC-15: comando arbitral (P1) | **Hecho:** salida no pertinente; existe desambiguación opcional. **Hipótesis:** flag/ruta/ranking. | Confirmar contrato de activación y contexto. | Positivos de comando y negativos homónimos. | Ambas clases cumplen criterio aprobado. **Parar** ante falsos positivos contextuales. |
| MC-13 / OOD (P1) | **Hecho:** se emitió respuesta de judo a consulta ajena. **Hipótesis:** señales o activación insuficientes. | Calibrar señales de dominio/evidencia y estado incierto. | Pares judo compartido / OOD inequívoco / ambiguo. | Métricas por clase; umbrales sólo tras baseline. **Parar** ante rechazos judo no aceptables. |
| Anclaje en evidencia principal (P0 posterior) | **Hecho estático:** la primera evidencia domina la estructuración. | Contrato de selector y síntesis después de estabilizar recuperación. | Norma única, complementaria, conflicto y ruido. | Cada afirmación soportada; conflicto no se mezcla. **Parar** si sólo crece longitud. |
| Guarda universal (P0 posterior) | **Propuesta previa no validada.** | Perfiles por intención y modo seguro graduado. | Campos ausentes/no aplicables/evidencia parcial. | No bloquea respuestas válidas ni inventa datos. **Parar** ante abstenciones injustificadas. |
| Controles/configuración (P1) | **Hecho estático:** la ruta activa no usa necesariamente todo parámetro visible. | Contrato UI→ruta→configuración tras validar base. | Propagación y regresión funcional. | Todo control visible tiene efecto verificable o se decide su retiro aparte. |

## 7. Fases y dependencias

### P0-A — Catálogo oro y línea base normativa

- **Objetivo:** transformar VF01 en evaluación revisable.
- **Entregables:** catálogo versionado, protocolo de revisión, evidencias admisibles, lista de pendientes y línea base por capa.
- **Dependencias:** PDF canónico y revisores normativos designados.
- **Aceptación:** cada caso de muestra tiene estado; no hay requisito universal Top-1 ni expectativa no validada como fallo.
- **No hacer:** cambiar RRE/ADA, flags, corpus o índices.
- **Parar:** versión documental incierta, trazabilidad ausente o desacuerdo no resuelto.

### P0-B — Recuperación localizada

- **Objetivo:** investigar TC-04, TC-12 y TC-11; incluir TC-15 sólo al confirmar contexto.
- **Entregables:** hipótesis por cambio, antes/después, regresiones temáticas y decisión conservar/revertir.
- **Dependencias:** P0-A y harness que mida recuperación sin generación.
- **Aceptación:** mejora de cobertura admisible sin regresiones acordadas.
- **No hacer:** Top-K generativo, guarda de suficiencia o ajustes globales.
- **Parar:** resultado no reproducible, regresión normativa o hardcode.

### P1-A — Abstención/OOD calibrada

- **Objetivo:** evitar respuestas fuera de dominio sin rechazar judo legítimo.
- **Entregables:** pares positivos/negativos/ambiguos, métricas por clase y umbrales propuestos.
- **Dependencias:** P0-A y decisión humana de riesgo.
- **Aceptación:** supera baseline aprobado sin falsos rechazos inaceptables.
- **No hacer:** regla simple por deporte, meta de 100 % o activación global.
- **Parar:** degradación en consultas judo o dataset insuficiente.

### P0-C — Selección, suficiencia y síntesis controladas

- **Objetivo:** evitar dependencia mecánica de Top-1 y mezcla ciega Top-K.
- **Entregables:** contrato de selección, perfiles por intención, pruebas de conflicto y síntesis trazable.
- **Dependencias:** P0-A y P0-B estables.
- **Aceptación:** afirmaciones soportadas y excepciones preservadas; respuesta correcta no se penaliza por rango distinto de uno.
- **No hacer:** requisitos lexicográficos universales ni mezcla de autoridades.
- **Parar:** conflicto oculto, pérdida de trazabilidad o mejora cosmética.

### P1-B — Configuración y regresión end-to-end

- **Objetivo:** verificar contrato entre interfaz, RRE, ADA, citas y validación.
- **Entregables:** matriz de configuración efectiva, reporte end-to-end y controles ambiguos.
- **Dependencias:** P0-B, P1-A y P0-C aprobadas individualmente.
- **Aceptación:** ningún PASS técnico basta sin exactitud normativa trazable.
- **No hacer:** despliegue o cambios de índices.
- **Parar:** diferencia ruta/configuración o regresión no explicada.

## 8. Protocolo de pruebas y criterios de parada

Antes de ejecutar cualquier prueba se registrarán versión de código, corpus, índice, modelo y catálogo. Se emitirán cinco informes independientes: recuperación, cobertura/suficiencia, síntesis, abstención/OOD y exactitud final. Un promedio agregado no puede ocultar un fallo P0.

Cada cambio requiere: hipótesis falsable; componente afectado; muestra objetivo y regresiones; comparación antes/después con empeoramientos; revisión humana de sanciones, excepciones, medidas, comandos y abstenciones; y decisión explícita de avanzar, revertir o investigar.

Se detiene una fase ante regresión P0, pérdida de trazabilidad al SOR, conflicto documental no resuelto, dependencia de una respuesta codificada para un caso, o falsos rechazos legítimos por encima del límite que Alexis y el responsable normativo acuerden tras conocer la línea base.

## 9. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| VF01 se convierte en norma | Tres campos separados: expectativa, fuente y evaluación; doble revisión. |
| Sobreajuste a pocos casos | Familias de regresión e intervención atribuible. |
| Top-K añade ruido/conflicto | Selector con precedencia y exclusión explícita. |
| Guarda bloquea respuestas válidas | Perfiles por intención y pruebas de campos no aplicables. |
| OOD rechaza judo válido | Pares con vocabulario compartido y umbrales posteriores a baseline. |
| Cita aparentemente precisa pero no soportada | Verificación de versión, artículo, página, alcance y condición. |
| Latencia/coste inciertos | Medir tras línea base; no prometer presupuesto sin datos. |
| Configuración engañosa | Validar contrato extremo a extremo antes de activar/exponer controles. |

## 10. Decisiones pendientes de aprobación humana

1. Alexis y responsable normativo: PDF SOR 2026 canónico, reglas de localización y responsables de doble revisión.
2. Responsable normativo: protocolo para discrepancias y casos `pendiente/no oráculo`.
3. Alexis: definición de regresión P0 y umbrales de daño tras obtener línea base.
4. Arquitectura/producto: política por intención para aclaración, respuesta condicionada y abstención.
5. Arquitectura: precedencia entre SOR, fuentes oficiales complementarias y evidencia contextual.
6. Producto/UX: decisión sobre controles visibles que no afecten la ruta activa.

## 11. Recomendación de primera fase

Autorizar únicamente **P0-A: catálogo oro y línea base normativa**. Es limitada y segura: no cambia comportamiento ni datos, y evita optimizar contra expectativas no verificadas. Su salida debe habilitar explícitamente —o impedir— P0-B.

La primera intervención de comportamiento, si P0-A se aprueba, debe ser un cambio de recuperación pequeño y aislado para TC-04/TC-12 con sus familias de regresión. TC-11 y TC-15 requieren antes cerrar referencia normativa y contexto. Síntesis, guardas de suficiencia y OOD quedan fuera de esa primera modificación.

## 12. Dictamen y cumplimiento

No se recomienda autorizar una implementación conjunta P0/P1 ni prometer que Top-K, una guarda o un detector OOD resolverán VF01. La autorización debe ser secuencial: estándar normativo de evaluación, recuperación localizada y luego selección/síntesis/suficiencia/abstención.

En esta revisión se actualizó únicamente este documento. No se modificaron código, corpus, PDFs, índices, embeddings, grafos, configuraciones ni pruebas; no se ejecutaron pruebas, benchmarks, ingestiones, Git, despliegues ni acciones OCI.

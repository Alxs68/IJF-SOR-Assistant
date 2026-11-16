# Hoja de ruta de cierre del proyecto experimental — IJF SOR Assistant 2026

**Estado del documento:** PROPUESTA PENDIENTE DE APROBACIÓN del propietario del proyecto (Product Owner).
**Fecha de redacción:** 2026-11-15.
**Propietario y autoridad normativa:** Alexis Oliveros Lozano (`PROJECT_STATUS.md`, `docs/DECISIONES.md`).
**Alcance:** únicamente las Fases 12, 13 y 14, como etapas finales del ciclo experimental iniciado en las Fases 8–11.

Ninguna fase se inicia con la redacción de este documento. Los umbrales de la sección E son **propuestas** y no están aprobados.

---

## 0. Auditoría documental previa: estado real de partida

Fuentes: los documentos del repositorio citados en cada fila. No se han ejecutado pruebas nuevas para redactar este documento.

| Ámbito | Estado documentado | Fuente |
|---|---|---|
| Producción | `https://sor.alxol.com`, OCI `VM.Standard.A1.Flex` (ARM, **1 OCPU, 6 GB RAM**), commit `61afc1b` del 04/11/2026. **Congelada por orden del propietario** hasta autorización formal de release. No contiene P0‑B, P0‑C, P1‑A, P1‑B, DEC‑009 ni nada de las Fases 8–11 | `PROJECT_STATUS.md` §5–6, `docs/deployment/PRODUCTION_MANIFEST.md`, `docs/deployment/oci_deployment.md` |
| Desarrollo local | Rama `integration/ijf-sor-2026-08-merge` con cambios sin commit (fases P0/P1 y DIG de la Fase 9). Componentes experimentales de las Fases 10–11 aislados en `src/experimental/` | `PROJECT_STATUS.md` §5, `docs/audits/FASE_11_INFORME_EJECUTIVO.md` |
| Última auditoría de prepublicación | **NO APROBADO**: correcciones metodológicas y normativas requeridas antes de cualquier despliegue | `docs/auditoria/auditoria_aceptacion_prepublicacion_2026.md` |
| Decisiones pendientes del propietario | Commit y push de la rama local; estrategia de release y despliegue en OCI | `docs/DECISIONES.md` §4 |
| Fase 10 | APTO PARA CONTINUAR EXPERIMENTACIÓN; NO APTO PARA PRODUCCIÓN. benchmark_v2 (105 consultas, dev 41 / test_sealed 64), NLI solo como observador SHADOW | `docs/audits/FASE_10_EVALUACION_SEMANTICA.md` |
| Fase 11 | Cerrada en dev. Corrección de la medida por pasajes duplicados (dev R@5 0,77, MRR 0,53); DIG reproducible 20/20; candidatos **variante DIG‑06** y **R3**; R2, R4 y R5 descartados; evaluación de extremo a extremo no realizada por la cuota del LLM | `docs/audits/FASE_11_*.md`, `data/eval/fase11/manifest.json` |
| Línea base de extremo a extremo (dev, Fase 10 reclasificada) | 17/62 respondibles aceptadas con la cita esperada (27 %); 0 incorrectas aceptadas; 20/20 abstenciones correctas en no respondibles; latencia LLM p50 ≈ 2,1 s; ≈ 7.000 tokens por consulta | `docs/audits/FASE_11_EVALUACION_COMPARATIVA.md` §4 |
| Limitaciones de benchmark_v2 | Etiquetas `PENDING_EXPERT_REVIEW`; mismo autor IA que v1; dev pequeño (31 respondibles); **test_sealed parcialmente contaminado** por los diagnósticos de las Fases 10–11; anclas sin equivalencia de pasajes duplicados (87/136); pocos casos de excepción/referencia en otro pasaje y de pt/fr | `FASE_10` §2 y §10, `FASE_11_DIAGNOSTICO_ABSTENCIONES.md` §2 |
| Capacidad del LLM | Cuota de Gemini insuficiente para corridas repetidas (Fase 11: 17/62 y 48/82 evaluaciones sin generación; errores QUOTA y REQUEST_TOO_LARGE); respaldo automático en Groq con otro modelo | `FASE_11_CALIBRACION_DIG.md` §2 |
| Gobernanza existente | Product Owner como autoridad soberana; registro de decisiones DEC‑001…DEC‑009; protocolo de sesión: analizar → proponer → esperar aprobación → implementar lo aprobado | `docs/DECISIONES.md`, `docs/AI_SESSION_PROTOCOL.md` |
| Pendiente heredado | Persistencia remota de novedades y capa TLS/proxy en OCI, pendientes de verificación | `PROJECT_STATUS.md` §7 |

**Lectura de partida:** el sistema es seguro en lo medido: no acepta respuestas incorrectas y se abstiene donde debe. Pero responde poco, y hay dos frentes abiertos que no son técnicos: producción está desfasada respecto al desarrollo, y la última auditoría de prepublicación no está aprobada. La hoja de ruta debe cerrar el ciclo experimental sin mezclar esos frentes con nuevos experimentos.

---

## A. Principios de cierre

1. **Sin fases automáticas.** Las Fases 12, 13 y 14 son las últimas del ciclo experimental. No se crean fases adicionales ni subfases nuevas sin autorización expresa y escrita del propietario.
2. **Toda ampliación de alcance requiere autorización expresa del propietario.** Una propuesta del asistente técnico no es una autorización.
3. **Una consulta fallida no es una fase.** Los fallos individuales se registran y se clasifican (punto 4). Solo se actúa sobre ellos si el propietario lo aprueba dentro de la fase en curso.
4. **Clasificación obligatoria de todo hallazgo:**
   * **Mejora necesaria:** bloquea un umbral obligatorio de la sección E.
   * **Mejora opcional:** mejora un objetivo deseable, sin bloquear.
   * **Limitación aceptada:** se documenta y se comunica al usuario, sin intervenir.

   La clasificación la propone el asistente y la aprueba el propietario.
5. **Producción no se modifica durante la experimentación.** Cualquier cambio en `sor.alxol.com` requiere una decisión formal de release (sección F y gobernanza).
6. **El benchmark_v3 sellado no se usa para ajustar.** Ni candidatos, ni umbrales, ni prompts, ni reglas, ni anclas se ajustan con sus resultados. Se evalúa una sola vez por candidato, con la configuración congelada antes de abrirlo.
7. **Los criterios se fijan antes de conocer los resultados.** La tabla de la sección E se aprueba en la Fase 12, antes de cualquier evaluación de la Fase 13.
8. **Solo candidatos autorizados:** en la Fase 13 se evalúan únicamente la variante DIG‑06 y R3. Lo descartado en la Fase 11 (R2, R4, R5) no se reabre en este ciclo.

### Clasificación inicial propuesta de los asuntos abiertos

| Asunto | Clasificación propuesta | Motivo |
|---|---|---|
| Capacidad y estabilidad del proveedor LLM | **Necesaria** | Sin ella no hay evaluación de extremo a extremo válida |
| benchmark_v3 sellado y revisado por árbitro | **Necesaria** | benchmark_v2 está contaminado y sin revisión |
| Revisión arbitral del CSV de abstenciones (15 casos de prioridad ALTA) | **Necesaria** | Determina si hay falsos bloqueos reales |
| Variante DIG‑06 y R3 | Candidatos (Fase 13) | Se integran o se descartan según la sección C |
| Cobertura de respuestas por debajo del objetivo | Decide la sección F | No genera una Fase 15 |
| Portugués y francés (R@5 0 en pt) | **Limitación aceptada** propuesta | Sin solución validada en la Fase 11; se declararía el idioma soportado |
| Mecanismo de aclaración por ámbito (11D) | **Opcional**, fuera de este ciclo salvo autorización | El detector de la Fase 10 no es válido |
| NLI (mDeBERTa) | **Limitación aceptada** / observador | ≈ 2 GB de RAM frente a 6 GB en OCI; F1 0,71 |
| Reglas fijas del RRE (31 IDs de pasaje, 34 detectores de palabras clave) | **Limitación aceptada** documentada | Ayudan en el benchmark actual; retirarlas está fuera de alcance |
| Afirmaciones sin cifra no verificadas por el DIG (nivel D) | **Limitación aceptada** | Se comunica como «sin verificación de entailment» |
| Persistencia remota de novedades y TLS en OCI | **Necesaria antes de la Fase 14** | El piloto necesita registro fiable |

---

## B. Fase 12 — Preparación de la evaluación definitiva

**Objetivo:** dejar todo listo para que la Fase 13 sea una única medición reproducible, con criterios aprobados y datos que nadie haya usado para ajustar.

| N.º | Objetivo | Entregable | Responsable propuesto | Depende de |
|---|---|---|---|---|
| 12.1 | Construir **benchmark_v3** independiente y sellado | `data/eval/benchmark_v3/` (dev pequeño solo para verificar el procedimiento + `test_sealed_v3`), manifest con sha256 | Asistente técnico (borrador) + propietario/árbitro (validación) | 12.2 |
| 12.2 | Protocolo de revisión arbitral de preguntas y respuestas esperadas | Protocolo y plantilla de revisión; etiquetas `EXPERT_REVIEWED` en v3 | Propietario (árbitro nacional A) u otro árbitro designado | — |
| 12.3 | Revisar los casos pendientes del CSV arbitral | `data/eval/fase11/arbitral_review_abstentions.csv` con veredictos (como mínimo los 15 de prioridad ALTA y los 6 desbloqueos de la variante DIG‑06) | Árbitro | — |
| 12.4 | Resolver o documentar la capacidad del LLM | Acta de decisión: proveedor y modelo fijos para la evaluación, cuota disponible, límite de tamaño del prompt, política ante fallo (reintento o invalidación de la corrida) | Propietario (decisión) + asistente (medición de cuota y coste) | — |
| 12.5 | Aprobar métricas, umbrales y condiciones de evaluación | Tabla E firmada por el propietario, con los valores definitivos | Propietario | 12.3, 12.4 |
| 12.6 | Procedimiento reproducible de evaluación | Script único y congelado, con hash; manifest con comandos; tests de aislamiento | Asistente técnico | 12.1, 12.4, 12.5 |

**Requisitos propuestos para benchmark_v3 (a aprobar en 12.5):**
* Al menos 150 consultas nuevas, no derivadas de v1 ni v2.
* Al menos 40 consultas con distractor de otro ámbito, al menos 20 con excepción o referencia en otro pasaje, al menos 20 no respondibles (insuficientes y fuera de dominio) y al menos 15 ambiguas.
* Idiomas en las proporciones que el propietario declare como soportadas.
* Anclas con **equivalencia de pasajes duplicados** desde la construcción.
* Respuesta esperada y evidencia validadas por árbitro.
* La partición sellada se abre solo en la Fase 13.

**Criterios de cierre de la Fase 12:**
* v3 construido, revisado y sellado, con hash registrado;
* tabla E aprobada;
* decisión sobre el LLM registrada;
* CSV arbitral revisado al menos en los casos ALTA;
* procedimiento congelado y verificado sobre el dev de v3.

**La Fase 12 no evalúa candidatos.**

---

## C. Fase 13 — Decisión técnica

**Candidatos autorizados (únicos):**
1. **Variante DIG‑06:** normalización de artefactos de formato en las cifras (`src/experimental/dig_variants.py`).
2. **R3:** preferencia por el ámbito nombrado en la consulta (`src/experimental/retrieval_variants.py`, β 0,2 o 0,5). El valor de β se fija antes de abrir v3; ver decisiones pendientes.

**Ningún candidato se considera aprobado antes de esta evaluación.**

**Procedimiento:**
1. Congelar el código y los parámetros (hash) de la línea base y de cada candidato.
2. Ejecutar sobre `test_sealed_v3`, con el proveedor y modelo fijados en 12.4 y al menos 3 corridas por configuración:
   * **línea base:** producción local actual con el DIG de producción;
   * **solo la variante DIG‑06**;
   * **solo R3**.
3. Solo si ambos candidatos cumplen por separado las condiciones de integración, y con autorización del propietario: **una** corrida combinada.
4. Validez de la corrida: si las evaluaciones sin generación por error de API superan el umbral de disponibilidad (tabla E), la corrida se invalida y se repite. No se reinterpreta.
5. Resultados comparados con la línea base, consulta por consulta, por idioma y por tipo, con las métricas de la sección E. Las respuestas aceptadas por un candidato y no por la base se revisan por árbitro.
6. **Prohibido ajustar después.** No se modifica ningún candidato, umbral, prompt ni regla a la vista de los resultados de v3. Una idea nueva surgida aquí se registra como mejora opcional, fuera de este ciclo.

**Condiciones de integración (todas):**
* cumple todos los umbrales obligatorios de la tabla E;
* mejora al menos un objetivo deseable respecto a la línea base;
* no empeora ninguna métrica de seguridad.

Cumplidas las tres, el candidato queda **apto para integración en desarrollo**. Su paso a producción requiere además la decisión de release (sección F).

**Condiciones de descarte (cualquiera):**
* incumple un umbral obligatorio;
* empeora una métrica de seguridad;
* no mejora ningún objetivo;
* exige ajustes para cumplir.

El descarte es definitivo dentro de este ciclo.

**Entregable:** `docs/audits/FASE_13_DECISION_TECNICA.md` con el resultado por candidato (INTEGRAR / DESCARTAR) y la propuesta de resultado final (sección F).

---

## D. Fase 14 — Piloto controlado

**Condición de inicio:**
* decisión técnica de la Fase 13 emitida;
* persistencia del registro de novedades verificada (pendiente de `PROJECT_STATUS.md` §7);
* autorización expresa del propietario.

| Elemento | Propuesta |
|---|---|
| Usuarios piloto | 5–10 personas invitadas: árbitros, entrenadores y directivos que el propietario designe; al menos 3 árbitros |
| Entorno | Instancia de piloto con acceso restringido (no la URL pública general), con la configuración resultante de la Fase 13 congelada |
| Alcance de las consultas | Solo el SOR 2026‑08, en los idiomas declarados como soportados. Sin consultas de casos disciplinarios reales ni datos personales |
| Registro | Cada consulta: texto, respuesta o abstención, citas, decisión y reglas del DIG, latencia, tokens y proveedor. Sin datos personales del usuario más allá de un identificador de piloto |
| Mecanismo de reporte | El formulario de novedades existente (7 tipos, DEC‑008), con exportación CSV |
| Supervisión arbitral | Revisión semanal por el árbitro responsable de una muestra de respuestas aceptadas (al menos el 20 %) y de todas las reportadas como error |
| Duración | 4 semanas |
| Criterios de salida | Los de la tabla E en su columna «Piloto», más 0 errores normativos graves confirmados por el árbitro |
| Interrupción | Inmediata ante un error normativo grave confirmado (respuesta incorrecta aceptada con apariencia de dictamen) |

**El piloto no implica publicación general automática.** Al terminar se emite la decisión final (sección F).

---

## E. Criterios cuantitativos de aceptación

**Todos los valores son PROPUESTOS y están pendientes de aprobación** por el propietario en la Fase 12 (12.5). La línea base de referencia es de dev de benchmark_v2 y debe recalcularse en la línea base de v3.

**Tipos de criterio:**
* **Obligatorio:** su incumplimiento descarta un candidato o impide la publicación correspondiente.
* **Deseable:** objetivo de mejora.
* **Informativo:** se reporta sin umbral.

| Métrica | Definición | Referencia actual (dev v2) | Tipo | Umbral propuesto Fase 13 (v3) | Umbral propuesto piloto |
|---|---|---|---|---|---|
| Respuestas incorrectas aceptadas | Aceptadas que el árbitro juzga incorrectas o basadas en evidencia de otro ámbito / aceptadas | 0/17 | **Obligatorio** | 0 | 0 errores graves; ≤ 1 % leves |
| Cobertura de respondibles | Respondibles aceptadas con evidencia correcta (árbitro) / respondibles | 27 % (17/62) | **Deseable** (y define la sección F) | ≥ línea base de v3 para integrar; **[X] %** para el asistente completo (el propietario fija X; sugerencia: 50 %) | Informativo |
| Precisión de citas | Citas de respuestas aceptadas que corresponden a evidencia válida (ancla o validada por árbitro) / citas | 28/28 aceptadas citan el ancla esperada (dev, corridas de las Fases 10 y 11) | **Obligatorio** | ≥ 95 % | ≥ 95 % (muestra) |
| Abstenciones correctas | No respondibles (insuficientes, fuera de dominio, ambiguas) no respondidas / no respondibles | 20/20 | **Obligatorio** | ≥ 95 % | Informativo |
| Errores de ámbito aceptados | Aceptadas que citan solo evidencia de otro ámbito | 0 | **Obligatorio** | 0 | 0 |
| Errores de ámbito en recuperación | Distractor en el paquete sin la evidencia correcta | 2 (dev) | Deseable | ≤ línea base | Informativo |
| Falsos bloqueos del DIG | Abstenciones con evidencia correcta citada que el árbitro juzga respondibles / respondibles | Por medir (20 candidatos en dev, sin arbitrar) | Deseable | < línea base | Informativo |
| Detección de cifras inventadas (batería adversarial) | Cifras inyectadas detectadas / inyectadas | 130/130 | **Obligatorio** | 100 % | — |
| Latencia de extremo a extremo | p50 y p95 de la consulta completa | LLM p50 ≈ 2,1 s; p95 4–5 s | Deseable | p95 ≤ 10 s | p95 ≤ 10 s |
| Coste por consulta | Tokens y coste monetario por consulta | ≈ 7.000 tokens; coste monetario no medido | Informativo | Por debajo del presupuesto que fije el propietario | Por debajo del presupuesto |
| Disponibilidad del servicio LLM | Evaluaciones sin generación por error de API / evaluaciones | 2/82 (Fase 10); 17/62 y 48/82 (Fase 11) | **Obligatorio para la validez de la corrida** | ≤ 5 % (si se supera, la corrida se invalida) | ≥ 99 % de consultas con respuesta o abstención controlada |
| Variabilidad entre corridas | Consultas con resultado distinto entre corridas | ≈ 25 % | Informativo | Reportar (≥ 3 corridas) | — |
| Errores normativos graves en el piloto | Confirmados por el árbitro | — | **Obligatorio** | — | 0 |

---

## F. Decisión final del producto

Al cerrar la Fase 14 (o la Fase 13, si el propietario decide no pilotar), el propietario adopta **uno** de estos resultados:

1. **Publicación del asistente completo** (respuestas sintetizadas con citas). Requiere:
   * todos los umbrales obligatorios;
   * cobertura ≥ X % (fijado por el propietario);
   * piloto sin errores graves;
   * persistencia y TLS verificados;
   * auditoría de prepublicación aprobada.
2. **Publicación con alcance limitado como buscador de normas con citas.** Muestra los pasajes SOR recuperados, con artículo y página, sin dictamen sintetizado; el modo de abstención actual ya conserva la evidencia. Corresponde cuando la seguridad se cumple pero la cobertura no alcanza X %, o cuando la capacidad del LLM no es sostenible. Se comunica explícitamente que no es un dictamen.
3. **No publicación hasta resolver limitaciones críticas.** Corresponde cuando se incumple algún umbral obligatorio de seguridad (respuestas incorrectas, citas, abstenciones o ámbito). Producción se mantiene congelada en su estado actual o se retira, según decida el propietario.

**La insuficiencia de cobertura no genera automáticamente una Fase 15.** Lleva al resultado 2, o al 3 si además hay incumplimientos de seguridad. Cualquier trabajo posterior es un proyecto nuevo con alcance aprobado por el propietario.

---

## 3. Cronograma propuesto

Duraciones estimadas con dedicación parcial del propietario. La revisión arbitral es la ruta crítica.

| Fase / hito | Inicio propuesto | Fin propuesto | Duración | Dependencias |
|---|---|---|---|---|
| Aprobación de esta hoja de ruta | 2026‑11‑16 | 2026‑11‑20 | 1 semana | — |
| **Fase 12** | 2026‑11‑23 | 2026‑12‑18 | 4 semanas | Aprobación de la hoja de ruta |
| — H12.1 Decisión sobre el LLM (12.4) | | 2026‑11‑27 | | Propietario |
| — H12.2 Borrador de v3 (12.1) | | 2026‑12‑04 | | 12.2 |
| — H12.3 Revisión arbitral de v3 y del CSV (12.2, 12.3) | | 2026‑12‑14 | | Disponibilidad del árbitro |
| — H12.4 Tabla E aprobada y procedimiento congelado (12.5, 12.6) | | 2026‑12‑18 | | H12.1–H12.3 |
| Pausa de fin de año (sin evaluaciones) | 2026‑12‑21 | 2027‑01‑08 | | |
| **Fase 13** | 2027‑01‑11 | 2027‑01‑22 | 2 semanas | Cierre de la Fase 12; cuota de LLM disponible |
| — H13 Decisión técnica emitida | | 2027‑01‑22 | | |
| Preparación del piloto (verificar persistencia y TLS, invitaciones) | 2027‑01‑25 | 2027‑01‑29 | 1 semana | H13 |
| **Fase 14** | 2027‑02‑01 | 2027‑02‑26 | 4 semanas | Autorización del propietario |
| **Decisión final del producto (sección F)** | | **2027‑03‑05** | | Fase 14 |

**Fecha de cierre propuesta del ciclo experimental: 5 de marzo de 2027.**

Si la Fase 12 se retrasa, el cronograma se desplaza sin añadir alcance. Un retraso superior a 4 semanas se trata como una decisión del propietario: ampliar el plazo o adoptar directamente el resultado 2 o 3 de la sección F.

---

## 4. Gobernanza

1. **El propietario del proyecto aprueba el alcance** de cada fase, toda ampliación y la clasificación de los hallazgos (A.4). El asistente técnico analiza, propone y ejecuta lo aprobado (`docs/AI_SESSION_PROTOCOL.md`).
2. **Los criterios de evaluación se fijan antes de conocer los resultados:** la tabla E se aprueba en el hito H12.4, antes de abrir test_sealed_v3.
3. **El benchmark sellado no se usa para calibrar.** Su hash se registra al sellarlo y se verifica en cada evaluación; un hash distinto invalida la evaluación.
4. **Los cambios a producción requieren autorización expresa** del propietario, registrada como decisión DEC‑0xx en `docs/DECISIONES.md`. Esto incluye commit y push de la rama local, fusión a `main`, release y despliegue en OCI, que hoy siguen pendientes (`docs/DECISIONES.md` §4).
5. **La publicación requiere una decisión formal** (sección F), registrada en `docs/DECISIONES.md`, con una auditoría de prepublicación aprobada. La última, `auditoria_aceptacion_prepublicacion_2026.md`, figura como NO APROBADO.
6. **El cierre experimental no implica abandonar el proyecto comunitario.** Cerrar este ciclo significa dejar de experimentar sin fin. El producto resultante (completo o limitado) puede mantenerse y mejorar en el futuro como proyecto nuevo, con alcance aprobado.
7. Este documento solo se modifica con la aprobación del propietario; cada versión queda registrada.

---

## 5. Decisiones que debe tomar el propietario

| N.º | Decisión | Cuándo | Opciones o sugerencia |
|---|---|---|---|
| D1 | Aprobar, modificar o rechazar esta hoja de ruta | Antes del 2026‑11‑20 | — |
| D2 | Proveedor y modelo LLM para las evaluaciones y el piloto; presupuesto de cuota y coste por consulta | H12.1 | Pago por uso con cuota garantizada / otro proveedor fijo / sin LLM (implica el resultado 2) |
| D3 | Quién realiza la revisión arbitral (v3 y CSV) y con qué dedicación | Inicio de la Fase 12 | El propietario como árbitro nacional A, o un segundo árbitro para el doble control |
| D4 | Valores definitivos de la tabla E, en particular el umbral de cobertura **X %** para el asistente completo | H12.4 | Sugerencia: 50 %; mínimo, no empeorar la línea base |
| D5 | Idiomas oficialmente soportados | Fase 12 | es + en (fr/pt como limitación aceptada) / incluir fr y pt |
| D6 | Valor de β de R3 que se evaluará (fijarlo antes de abrir v3) | H12.4 | 0,2 (conservador) o 0,5 (dev: +1 consulta) |
| D7 | Autorizar o no la corrida combinada si ambos candidatos pasan por separado | H12.4 | — |
| D8 | Usuarios piloto, duración y entorno restringido | Antes de la Fase 14 | 5–10 invitados, 4 semanas |
| D9 | Situación de producción actual (`61afc1b`) durante el ciclo | Inmediata | Mantener congelada (situación actual) / retirar / aviso de versión anterior |
| D10 | Commit y push de la rama local (pendiente heredado de `DECISIONES.md` §4) | Antes de la Fase 13, para congelar el código evaluado | — |
| D11 | Resultado final del producto (sección F) | 2027‑03‑05 | 1, 2 o 3 |

---

**Confirmación:** para redactar este documento no se modificó código, producción, corpus SOR, documentos SHADOW ni benchmarks; no se ejecutaron pruebas ni evaluaciones; no se integraron R3 ni la variante DIG; no se hizo commit, push ni despliegue. La Fase 12 no se ha iniciado.

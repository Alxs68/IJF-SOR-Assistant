# REGISTRO CENTRAL DE DECISIONES DE GOBERNANZA Y ARQUITECTURA
## IJF SOR Assistant 2026

**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Rama activa:** `integration/ijf-sor-2026-08-merge`  
**Product Owner y Autoridad Normativa (Autoridad Soberana):** Alexis Oliveros Lozano  
**Planificador, Supervisor Metodológico y Auditor Independiente:** ChatGPT  
**Ejecutor Técnico:** Antigravity  
**Fecha de consolidación:** 07 de noviembre de 2026  
**Estado:** VIGENTE — DOCUMENTO RECTOR DE GOBERNANZA

---

## 1. PROPÓSITO Y AUTORIDAD

El presente documento constituye el **Registro Oficial de Decisiones Soberanas** adoptadas exclusivamente por el Product Owner y Autoridad Normativa, Alexis Oliveros Lozano, contando con la asesoría metodológica y auditoría independiente de ChatGPT y la ejecución técnica de Antigravity.

Ningún cambio arquitectónico, normativo o de alcance puede contradecir lo establecido en este registro sin una nueva decisión explícita y formalmente dictada por Alexis Oliveros Lozano.

---

## 2. TABLA CONSOLIDADA DE DECISIONES SOBERANAS

| ID | Fecha | Decisión Soberana | Justificación y Motivo | Alcance | Estado | Documento de Soporte |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DEC-001** | 2026-11-06 | **Cierre y archivo definitivo de la Fase 4.2.6 (Fusión y Arbitraje Multifuente).** | Alta complejidad estocástica innecesaria, riesgo de regresiones y sobre-ingeniería que no aportaban a la precisión normativa directa del reglamento SOR 2026. | Arquitectura general, módulo multifuente, sidecars experimentales. | **APROBADA Y CERRADA** | `docs/acta_aprobacion_reorientacion_lean_ijf_sor_assistant.md`<br>`docs/diagnostico_reorientacion_funcional_ijf_sor_assistant.md` |
| **DEC-002** | 2026-11-06 | **Adopción de la arquitectura Lean RRE 3.0 / ADA enfocada en calidad de respuesta y terminología de judo.** | Simplificar el pipeline a dos fases deterministas y auditables: RRE (recuperación contextual con costura de pasajes y sinónimos canónicos) y ADA (asistente de respuesta fiel, estructurada y sin alucinaciones). | RAG Engine, RRE Engine, ADA Assistant, i18n, sinonimia judo. | **APROBADA Y EN VIGOR** | `docs/acta_aprobacion_reorientacion_lean_ijf_sor_assistant.md`<br>`docs/informe_cierre_lean_paso1_stitching_rre.md`<br>`docs/informe_cierre_lean_paso2_sinonimos_judo.md` |
| **DEC-003** | 2026-11-07 | **Ratificación de los dictámenes arbitrales sobre los 11 criterios normativos prioritarios (VF01).** | Garantizar que el asistente responda con exactitud indiscutible en situaciones críticas de arbitraje (kumi-kata no convencional, shido por pasividad, agarres cruzados, reverse seoi-nage, zambullida de cabeza, inmovilizaciones y medidas reglamentarias). | Suite de regresión normativa (`scratch/test_regression_11_cases.py`), 11 casos de decisión. | **RATIFICADA POR EL PO** | `docs/auditoria/validacion_humana_resultados_actuales.md`<br>`docs/dictamen_auditoria_vf01.md` |
| **DEC-004** | 2026-11-07 | **Aprobación del cierre funcional de Fase P0-B (Kumi-kata y resolución focal ESC-09).** | Verificación exitosa al 100% (10/10 PASS) de las consultas focales de kumi-kata de CGPT-06 y corrección puntual de la sanción Shido en ESC-09 (dedos entrelazados continuos). | RRE ranking, Response Structurer, consultas focales kumi-kata. | **APROBADA Y CERRADA** | `docs/auditoria/informe_fase_P0_B_ingenieria_rre.md`<br>`scratch/test_focal_cgpt06_queries.py` |
| **DEC-005** | 2026-11-07 | **Aprobación del cierre funcional de Fase P0-C (Razonamiento, Contrato de Selección y Síntesis Normativa).** | Implementación del contrato de selección con suficiencia probatoria para 7 perfiles normativos (`SANCTION`, `SCORE`, `MEASUREMENT_TIME`, `EXCEPTION`, `PROCEDURE`, `DEFINITION`, `GENERAL`), desempates rigurosos y trazabilidad estricta. Verificado mediante suite formal de 9 pruebas (9/9 PASS). | ADA Assistant, EvidenceBundle, Response Structurer, validador de citas. | **APROBADA Y CERRADA** | `docs/auditoria/informe_fase_P0_C_razonamiento_seleccion_sintesis.md`<br>`docs/auditoria/informe_complementario_validacion_final_P0_C.md`<br>`tests/test_p0_c_reasoning_and_selection.py` |
| **DEC-006** | 2026-11-07 | **Aprobación del cierre funcional de Fase P1-A (Calibración de Abstención y Detección OOD).** | Erradicación total de falsas aceptaciones OOD (de 60% a 0%) y logro de 100% exactitud global en el benchmark oficial de 40 casos balanceados (15 in-domain, 25 OOD en 5 clases), verificado permanentemente en tests formales (10/10 PASS y 25/25 PASS). | OOD Detector, Negative Domain Anchor Scoring, RRE Engine. | **APROBADA Y CERRADA** | `docs/auditoria/informe_fase_P1_A_abstencion_ood.md`<br>`tests/test_p1_a_abstention_ood.py`<br>`tests/test_negative_domain_anchor_scoring.py` |
| **DEC-007** | 2026-11-07 | **Aprobación y cierre de Fase P1-B (Configuración y Regresión End-to-End).** | Demostración de propagación determinista en pipeline E2E, ausencia de acoplamientos ocultos y estabilidad de las regresiones previas (11 casos de Alexis y 10 casos CGPT-06). Cierre formal sobre base documental y reportes. | Pipeline completo E2E, app Streamlit, RAG Engine, ADA, RRE. | **APROBADA Y CERRADA** | `docs/auditoria/informe_fase_P1_B_configuracion_e2e.md`<br>`tests/test_p1_b_configuracion_e2e.py` |
| **DEC-008** | 2026-11-07 | **Retiro de controles técnicos de búsqueda en UI y simplificación del formulario de novedades.** | Eliminar sliders de $K$ y `min_score` en la interfaz pública para evitar degradaciones por el usuario final, operando con la configuración predeterminada de backend (`k=3, min_score=None`). Simplificar el reporte de novedades a 7 tipos oficiales con captura contextual y exportación CSV. | `app.py`, `src/feedback_manager.py`, UI pública Streamlit y barra lateral admin. | **APROBADA E IMPLEMENTADA** | `docs/auditoria/informe_auditoria_mecanismo_novedades.md`<br>`docs/auditoria/informe_fase_P1_B_configuracion_e2e.md`<br>`tests/test_ui_controls_and_novedades.py` |
| **DEC-009** | 2026-11-07 | **Ratificación soberana de K=5 como configuración canónica de recuperación del RRE 3.0.** | Sustentada en la evaluación experimental comparativa de $K=3$, $K=5$ y $K=8$ (`docs/auditoria/experimento_comparativo_k_rre_2026_11.md`), que demostró un incremento de $+30.6\%$ en recuperación de evidencia normativa complementaria útil, resolución de déficit en $33.9\%$ de consultas, $100\%$ de éxito en casos VF01 y $100\%$ de inmunidad en abstención OOD, sin saturación de ruido (descarte de $K=8$). Conserva `min_score=None`. K adaptativo queda fuera del alcance actual. | Configuración canónica RRE 3.0, RAG Engine, ADA Assistant. | **RATIFICADA E IMPLEMENTADA LOCALMENTE** | `docs/auditoria/experimento_comparativo_k_rre_2026_11.md`<br>`docs/auditoria/implementacion_local_k5_2026_11.md`<br>`reports/experimentos/k_rre_2026_11/resultados_detallados_k3_k5_k8.json` |

---

## 3. DETALLE DE DECISIONES HISTÓRICAS Y ESTRUCTURALES

### DEC-001: Cierre y Archivo Definitivo de Fase 4.2.6
- **Fecha:** 06 de noviembre de 2026.
- **Autoridad Soberana:** Alexis Oliveros Lozano (Product Owner).
- **Asesoría Metodológica:** ChatGPT.
- **Contexto:** Se venía desarrollando una compleja infraestructura de arbitraje multifuente con múltiples sidecars para combinar el reglamento SOR con documentos complementarios y circulares federativas. Dicho enfoque aumentaba la latencia, generaba contradicciones semánticas y no permitía garantizar la infalibilidad en los criterios rectores del judo.
- **Resolución:** Declarar cerrada y archivada la Fase 4.2.6. Prohibir la reapertura de sidecars experimentales y concentrar todos los esfuerzos en el corpus canónico oficial SOR IJF 2026-08 (385 pasajes).
- **Efecto práctico:** Los archivos y expedientes correspondientes fueron empaquetados y archivados en `docs/archive_v2_8/`, `docs/archive_v2_9/` y `docs/expediente_fase4_2_6_*.zip`.

---

### DEC-002: Reorientación hacia Arquitectura Lean RRE / ADA
- **Fecha:** 06 de noviembre de 2026.
- **Autoridad Soberana:** Alexis Oliveros Lozano (Product Owner).
- **Asesoría Metodológica:** ChatGPT.
- **Contexto:** La respuesta del asistente dependía de heurísticas dispersas. Era indispensable una arquitectura en dos capas nítidas:
  1. **RRE (Rule Retrieval Engine):** Recuperación con costura de pasajes adyacentes (*chunk stitching*) y expansión léxica especializada con sinónimos canónicos de judo (ej. agarre cruzado $\leftrightarrow$ cross grip, palanca $\leftrightarrow$ kansetsu-waza).
  2. **ADA (Assistant Decision Architecture):** Asistente de síntesis fiel que no inventa normas, cita explícitamente artículos/páginas del SOR y produce explicaciones en niveles jerárquicos comprensibles para árbitros, entrenadores y atletas.
- **Resolución:** Implementar los pasos Lean 1 y 2, estableciendo la base sobre la que se ejecutaron las fases correctivas P0 y P1.

---

### DEC-003: Ratificación de los Dictámenes Arbitrales sobre los 11 Criterios Normativos Prioritarios (VF01)
- **Fecha:** 07 de noviembre de 2026.
- **Autoridad Soberana:** Alexis Oliveros Lozano (Product Owner y Autoridad Normativa).
- **Contexto:** De los 52 casos evaluados en el catálogo general VF01, se identificaron 11 situaciones críticas del judo competitivo donde el sistema requería un dictamen arbitral explícito y vinculante emitido por el Product Owner:
  1. **VF01-01:** Medidas oficiales del área de combate y seguridad (SOR Art. 8.7, p. 96). Solo medidas textuales (8-10m combate, 3m seguridad); no inventar cálculos totales.
  2. **VF01-07:** Acciones con la cabeza: diferencia entre Cadetes (Hansoku-make) y Senior/Junior (SOR Art. 18.1.4 y 18.2.1).
  3. **VF01-09:** Descalificación por zambullida de cabeza (head diving): el atleta no puede continuar en la competición (SOR Art. 18.2.1, p. 190).
  4. **VF01-14:** Uso voluntario de cabeza para proyectar: Hansoku-make directo sin continuidad (SOR Art. 18.2.1).
  5. **VF01-23:** Reverse seoi-nage en judokas adultos: técnica prohibida sancionada con Shido (SOR Art. 18.1.4, p. 189).
  6. **VF01-24:** No combatividad: sanción Shido tras tiempo razonable (SOR Art. 18.1.1, p. 177).
  7. **VF01-25:** Preguntas sobre cambios reglamentarios futuros ciclo LA28: abstención fundamentada OOD (materia no regulada en SOR 2026).
  8. **VF01-29:** No combatividad en transición pie-suelo: Shido (SOR Art. 18.1.1, p. 177).
  9. **VF01-30:** Contraataque involuntario donde tori aterriza sobre su propia cabeza: no se sanciona a tori; acción válida (SOR Art. 18.2.1, p. 190).
  10. **VF01-42:** Defensa apoyando la cabeza en el tatami: Hansoku-make directo (SOR Art. 18.2.1, p. 190).
  11. **VF01-48:** Kumi-kata no convencional sin ataque inmediato: Shido (SOR Art. 18.1.2, p. 182).
- **Resolución:** Todas las fases correctivas y suites de regresión deben verificar estos 11 dictámenes arbitrales como condición obligatoria de aprobación (`scratch/test_regression_11_cases.py`, 11/11 PASS).

---

### DEC-004: Cierre Funcional de Fase P0-B
- **Fecha:** 07 de noviembre de 2026.
- **Autoridad Soberana:** Alexis Oliveros Lozano (Product Owner).
- **Auditoría Independiente:** ChatGPT.
- **Contexto:** Se requería evaluar la recuperación y estructuración en 10 consultas focales de kumi-kata formuladas por ChatGPT (CGPT-06). En la auditoría preliminar se detectó una omisión en el caso ESC-09 (dedos entrelazados), donde se describía la conducta prohibida pero se omitía la consecuencia de penalización Shido en la síntesis.
- **Resolución:** Se aplicó una corrección puntual en la plantilla de estructuración de sanciones para kumi-kata en `src/response_structurer.py`. El caso ESC-09 pasó a PASS y la suite CGPT-06 completó 10/10 PASS sin alterar el resto del pipeline.

---

### DEC-005: Cierre Funcional de Fase P0-C
- **Fecha:** 07 de noviembre de 2026.
- **Autoridad Soberana:** Alexis Oliveros Lozano (Product Owner).
- **Auditoría Independiente:** ChatGPT.
- **Contexto:** Asegurar razonamiento sólido y un contrato rector de selección probatoria en `EvidenceBundle`.
- **Resolución:** Definición formal de los 7 perfiles normativos (`SANCTION`, `SCORE`, `MEASUREMENT_TIME`, `EXCEPTION`, `PROCEDURE`, `DEFINITION`, `GENERAL`), verificación de suficiencia probatoria mínima, reglas de desempate por especificidad, preservación de evidencia complementaria y blindaje anti-keyword stuffing. Verificación exitosa en la suite formal ampliada `tests/test_p0_c_reasoning_and_selection.py` con **9 pruebas (9/9 PASS)**.

---

### DEC-006: Cierre Funcional de Fase P1-A
- **Fecha:** 07 de noviembre de 2026.
- **Autoridad Soberana:** Alexis Oliveros Lozano (Product Owner).
- **Auditoría Independiente:** ChatGPT.
- **Contexto:** El sistema requería una barrera infranqueable ante consultas OOD (fuera de dominio de judo o fuera del reglamento SOR) y preguntas sobre ciclos futuros o materias no reguladas que inducían a alucinaciones.
- **Resolución:** Implementación de calibración estricta en `src/ood_detector.py` y `src/negative_domain_anchor_scoring.py`. Verificado empíricamente sobre el **benchmark oficial balanceado de 40 casos** (15 consultas in-domain, 25 consultas OOD en 5 clases: deportes externos, sambo/BJJ, ciclo LA28/2030, no deportivas y no reguladas), logrando 100% de exactitud global (40/40), 100% de abstención OOD (25/25, erradicando el 60% de falsas aceptaciones previas) y 100% de retención in-domain (15/15). Integrado permanentemente en `tests/test_p1_a_abstention_ood.py` (10/10 PASS) y `tests/test_negative_domain_anchor_scoring.py` (25/25 PASS).

---

### DEC-007: Cierre Funcional de Fase P1-B
- **Fecha:** 07 de noviembre de 2026.
- **Autoridad Soberana:** Alexis Oliveros Lozano (Product Owner).
- **Auditoría Independiente:** ChatGPT.
- **Contexto:** Demostrar que los parámetros de configuración se propagan limpiamente desde la interfaz hasta el motor sin efectos colaterales ni acoplamientos ocultos, garantizando la estabilidad de las regresiones previas.
- **Resolución:** Verificación de la propagación determinista en el pipeline completo E2E mediante la suite `tests/test_p1_b_configuracion_e2e.py` (9/9 PASS) y confirmación de estabilidad en los 11 casos de Alexis y 10 casos focales CGPT-06. Cierre formal aprobado sobre base documental y reportes.

---

### DEC-008: Retiro de Controles Técnicos en UI y Simplificación de Novedades
- **Fecha:** 07 de noviembre de 2026.
- **Autoridad Soberana:** Alexis Oliveros Lozano (Product Owner).
- **Contexto:** La presencia de los controles técnicos de $K$ y `min_score` en la barra lateral exponía al usuario a degradar el rendimiento del asistente por desconocimiento técnico. Asimismo, el mecanismo de feedback de usuarios requería baja fricción para recolectar observaciones arbitrales de campo.
- **Resolución:**
  1. Retirar de `app.py` los sliders de $K$ y `min_score`, operando interinamente con la configuración predeterminada de backend.
  2. Simplificar el formulario de novedades a un componente de baja fricción con 7 tipos de novedad (`ERROR_NORMATIVO`, `REFERENCIA_INCORRECTA`, `RESPUESTA_INCOMPLETA`, `TERMINOLOGIA_INEXACTA`, `ALUCINACION_O_INVENTO`, `PROBLEMA_IDIOMA`, `OTRO`), captura contextual automática de la consulta y respuesta generada, y botón de exportación CSV directo en la vista de administración.
  3. Validar con suite `tests/test_ui_controls_and_novedades.py` (5/5 PASS).

---

### DEC-009: Ratificación Soberana de K=5 como Configuración Canónica de Recuperación del RRE 3.0
- **Fecha:** 07 de noviembre de 2026.
- **Autoridad Soberana:** Alexis Oliveros Lozano (Product Owner y Autoridad Normativa).
- **Supervisión y Auditoría Metodológica:** ChatGPT.
- **Fundamento Experimental:** Informe de evaluación experimental comparativa de $K \in \{3, 5, 8\}$ (`docs/auditoria/experimento_comparativo_k_rre_2026_11.md`), ejecutado sobre 120 casos únicos (360 ejecuciones empíricas).
- **Resultados Determinantes del Experimento:**
  1. **Cobertura de Evidencia Complementaria:** $K=5$ recupera $+30.6\%$ más pasajes normativos relevantes ($128$ vs $98$) frente a $K=3$, resolviendo el déficit de pasajes complementarios (excepciones, notas de cadetes, sanciones secundarias) en el $33.9\%$ de las consultas ($21/62$).
  2. **Descarte de $K=8$:** $K=8$ degrada la precisión al $32.26\%$ con $280$ distractores (el $63.6\%$ de los pasajes recuperados son irrelevantes), saturando el contexto del LLM sin aportar beneficios a la exactitud arbitral.
  3. **Estabilidad Normativa VF01:** Los 11 casos ratificados de Alexis mantienen un $100.0\%$ de éxito ($11/11$ PASS) invariable en $K=5$.
  4. **Inmunidad en Abstención OOD:** El benchmark oficial balanceado P1-A arrojó un $100.0\%$ de exactitud ($40/40$) y $100.0\%$ de abstención OOD ($25/25$) bajo $K=5$, demostrando que la compuerta de abstención es totalmente inmune a $K$.
- **Resolución Soberana:**
  1. Ratificar formalmente **$K=5$** como la **configuración canónica oficial de recuperación del RRE 3.0**.
  2. Conservar el parámetro **`min_score=None`**, delegando el filtrado interno a los umbrales calibrados del motor RRE.
  3. Declarar que la recuperación adaptativa de $K$ queda formalmente **fuera del alcance actual**.
  4. Mantener inalterados el corpus oficial SOR 2026-08 (385 pasajes), los embeddings, los índices y los criterios normativos ratificados.
- **Implementación Técnica Local:**
  Implementada localmente el 08 de noviembre de 2026 en `src/rag_engine.py` (L129, L199), `src/ada_assistant.py` (L83) y `src/rre_engine.py` (L752). Validada con 148 pruebas automatizadas sin fallos (100% PASS), documentada en [`docs/auditoria/implementacion_local_k5_2026_11.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/implementacion_local_k5_2026_11.md). Producción OCI permanece inalterada en espera de autorización de release.

---

## 4. ASUNTOS PENDIENTES DE DECISIÓN DEL PRODUCT OWNER

1. **Autorización para Consolidación Git (Commit y Push):**  
   Permanece pendiente la orden soberana de Alexis Oliveros para ejecutar el commit de los cambios locales en `integration/ijf-sor-2026-08-merge` y su envío al repositorio remoto en GitHub.
2. **Estrategia de Release y Despliegue en Producción:**  
   Permanece pendiente la decisión soberana para la fusión a `main`, etiquetado de release formal (`v2.0.0-rc1` u otro) y programación de la actualización del servicio en OCI (`https://sor.alxol.com`).

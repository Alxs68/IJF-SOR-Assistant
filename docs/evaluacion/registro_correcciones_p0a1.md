# Registro de Correcciones Documentales P0-A.1 / P0-A.1.2
## Conforme a los Dictámenes de Auditoría Independiente Codex

> **Proyecto:** IJF SOR Assistant 2026  
> **Fase:** P0-A.1.2 (Subsanación Documental Final posterior a Reauditoría Codex)  
> **Fecha:** 2026-11-06  
> **Responsable del proyecto y decisor:** Alexis Oliveros Lozano  
> **Planificador y auditor metodológico:** ChatGPT  
> **Auditor independiente:** Codex (Dictámenes `dictamen_auditoria_p0a_codex.md`, `dictamen_reauditoria_p0a1_codex.md` y `dictamen_reauditoria_final_p0a1_codex.md`)  
> **Ejecutor técnico documental:** Antigravity  

---

## 1. Objetivo y Alcance

El presente documento registra con trazabilidad estricta las correcciones documentales realizadas sobre los artefactos de la Fase P0-A en respuesta a las no conformidades y observaciones identificadas por la auditoría independiente de Codex (`dictamen_auditoria_p0a_codex.md`), su reauditoría (`dictamen_reauditoria_p0a1_codex.md`) y el dictamen final `ACCEPTED WITH OBSERVATIONS` (`dictamen_reauditoria_final_p0a1_codex.md`).

En cumplimiento estricto del alcance autorizado, el trabajo se restringió de forma exclusiva a:
- `docs/evaluacion/catalogo_vf01_normativo.md`
- `docs/evaluacion/catalogo_vf01_normativo.csv`
- `docs/evaluacion/linea_base_vf01.md`
- `docs/evaluacion/pendientes_revision_normativa.md`
- `docs/evaluacion/registro_correcciones_p0a1.md`

---

## 2. Matriz de Trazabilidad de Correcciones

| # | Caso / Elemento Afectado | Documentos Modificados | Cambio Efectuado | Motivo de la Corrección | Evidencia del Dictamen Codex | Estado / Decisión Pendiente |
|---|---|---|---|---|---|---|
| **1** | **TC-01 / VF01-01** (Tatami y seguridad) | `catalogo_vf01_normativo.md`, `.csv`, `linea_base_vf01.md`, `pendientes_revision_normativa.md` | Corregida la referencia normativa: se fijó Art. 8.7 pág. 96 como fuente canónica de área de combate y seguridad. Se eliminó la atribución errónea al Art. 8.8 pág. 97. Se ajustaron las respuestas oro derivadas en VF01-31 y VF01-43. | En el PDF canónico, la pág. 96 (Art. 8.7) define ambas áreas; la pág. 97 corresponde a inicio de Art. 8.8 Medical. No hay necesidad de integrar dos artículos. | Dictamen Codex Inicial, Sección 3 (Crítico): *"VF01-01 tiene una referencia normativa incorrecta... pasaje canónico p.96 contiene área de combate y seguridad, y p.97 inicia Art. 8.8 Medical."* | Alexis debe ratificar si la omisión de área de seguridad en la respuesta de VF01 se califica como FAIL o PARTIAL. |
| **2** | **MC-08 / VF01-30** (Contacto involuntario) | `catalogo_vf01_normativo.md`, `.csv`, `linea_base_vf01.md`, `pendientes_revision_normativa.md` | Se revocó el estado aprobado y se reclasificó como `PENDIENTE_REVISION_HUMANA`. Se retiró la afirmación de que el pasaje p. 190 contiene una excepción expresa. | El pasaje pág. 190 (Art. 18.2.1 y 18.2.2) describe head diving y kawazu-gake; no contiene formulación textual de excepción accidental. | Dictamen Codex Inicial, Sección 3 (Crítico): *"VF01-30 y VF01-42 se aprobaron con excepción no demostrada por su cita... Revocar aprobación y pasar a revisión humana."* | Alexis / panel arbitral deben aportar la regla o directriz oficial exacta que rige la involuntariedad. |
| **3** | **MC-20 / VF01-42** (Head landing en contraataque) | `catalogo_vf01_normativo.md`, `.csv`, `linea_base_vf01.md`, `pendientes_revision_normativa.md` | Se revocó el estado aprobado y se reclasificó como `PENDIENTE_REVISION_HUMANA`. Se eliminó la afirmación de excepción aprobada sin respaldo textual. | La cita de Art. 18.2.2 pág. 190 no contiene la regla de aterrizaje accidental durante contraataque. | Dictamen Codex Inicial, Sección 3 (Crítico): *"El texto cotejado p.190... no expresa la excepción. Ambos pasan a PENDIENTE_REVISION_HUMANA."* | Alexis debe aportar el localizador normativo canónico o circular aplicable a caídas accidentales. |
| **4** | **TC-11 / VF01-11** (Kawazu-gake) | `catalogo_vf01_normativo.md`, `.csv`, `linea_base_vf01.md` | Se preservó la identificación canónica de Kawazu-gake en Art. 18.2.2 punto 1 (pág. 190). Se documentó expresamente que la respuesta histórica generada en VF01 citaba erróneamente Art. 4 Gestures (pág. 149) por falla de sinónimos del motor. Se aclaró que no se confunden el pasaje candidato y la salida histórica. Se eliminó una errata en la línea base previa que mencionaba "salida deliberada". | Claridad de trazabilidad entre el pasaje candidato en el SOR y la ejecución fallida histórica de VF01. | Dictamen Codex Inicial, Sección 3 (Alto) y Sección 4: *"La identidad es consistente: CSV y Markdown asignan VF01-11 a TC-11 y a la consulta kawazu-gake... salida histórica como Art. 4 Gestures p.149... pasaje canónico p.190, Art. 18.2.2 punto 1."* | Pendiente de registro formal de segunda revisión humana junto al resto de casos SEC-CRIT. |
| **5** | **SEC-CRIT: Auditoría y pendientes** | `catalogo_vf01_normativo.md`, `.csv`, `linea_base_vf01.md`, `pendientes_revision_normativa.md` | Se mantienen estrictamente los 15 casos SEC-CRIT. Se actualizaron los pendientes de seguridad de 3 a 5 casos tras la revocación de VF01-30 y VF01-42 (pendientes: VF01-07, VF01-09, VF01-14, VF01-30, VF01-42). No se inventaron pendientes ficticios. Se declaró explícitamente que no existe registro verificable de doble revisión humana previa. | No atribuir consensos ni dobles revisiones no ejecutadas en registros documentados. | Dictamen Codex Inicial, Sección 3 (Crítico/Medio) y Sección 8: *"Falta prueba de doble revisión humana SEC-CRIT... La discrepancia SEC-CRIT '3 frente a 4' no se reproduce... enumeran sólo VF01-07, 09 y 14."* | Alexis debe nombrar al revisor/panel y realizar la doble revisión formal firmada de los 15 SEC-CRIT (punto transversal de gobernanza). |
| **6** | **Métrica 28/52 y Reconciliación** | `linea_base_vf01.md`, `catalogo_vf01_normativo.md` | Se retiró formalmente cualquier afirmación de que 28/52 representa una tasa de exactitud normativa certificada. Se documentó que el dictamen previo de VF01 constató 17 casos favorables (12 correctos + 5 abstenciones correctas) y que toda métrica final queda suspendida hasta una reconciliación exhaustiva caso a caso. | No confundir pasajes candidatos con exactitud de respuestas ni atribuir cifras no reconciliadas. | Dictamen Codex Inicial, Sección 3 (Alto) y Sección 8: *"Dictamen VF01: 12 correctas más 5 abstenciones correctas; línea base afirma 28 sin lista ni revisión... Retirar la cifra como resultado certificado."* | Reconciliación formal caso a caso frente al dictamen anterior de VF01 en la fase de auditoría. |
| **7** | **Sustitución de Estado por `CANDIDATO_DOCUMENTAL`** | `catalogo_vf01_normativo.md`, `.csv`, `linea_base_vf01.md` | Se sustituyó `APROBADO_NORMATIVO` por `CANDIDATO_DOCUMENTAL` en los 41 registros correspondientes, tanto en Markdown como en CSV y tablas de resumen/métricas. Se mantienen sin alteración los restantes 11 estados. | Eliminar la ambigüedad que sugería aprobación formal en pasajes que únicamente cuentan con localización documental sin doble revisión humana formal. | Reauditoría Codex, Sección 2, punto 1 y Sección 6.1: *"Los 41 candidatos siguen codificados como APROBADO_NORMATIVO... reemplazar los 41 valores por CANDIDATO_DOCUMENTAL."* | Los 41 casos quedan claramente rotulados como candidatos trazados a la espera de revisión formal. |
| **8** | **Restitución de 52/52 PASS Técnico Histórico** | `linea_base_vf01.md` | Se corrigió la tabla de sección 2 en la línea base, restituyendo los 52/52 PASS técnicos históricos del pipeline. Se diferenció explícitamente en columna separada que el rendimiento técnico de software no equivale a corrección normativa. | Evitar la contradicción con el CSV (que conserva 52 PASS de pipeline) y preservar la trazabilidad histórica de estabilidad técnica del software. | Reauditoría Codex, Sección 2, punto 2 y Sección 6.2: *"La línea base reescribe 52 resultados históricos PASS de VF01 como '0 (Revocado)'... debe mantener 52/52 PASS técnico histórico y mostrar en una columna distinta que ese indicador no certifica exactitud normativa."* | Conforme. |
| **9** | **Distinción entre 11 Casos de Decisión y Gobernanza SEC-CRIT** | `pendientes_revision_normativa.md`, `registro_correcciones_p0a1.md` | Se estructuró formalmente la sección de pendientes distinguiendo con claridad: (a) 11 casos de decisión arbitral (8 de revisión humana, 1 de evidencia externa, 1 disputado y 1 sin oráculo); y (b) Un punto transversal de gobernanza (doble revisión SEC-CRIT). | Claridad en el conteo para la toma de decisiones de Alexis Oliveros Lozano, evitando la confusión de presentar 12 casos cuando son 11 casos y 1 directriz transversal. | Reauditoría Codex, Sección 2, punto 3 y Sección 6.4: *"El registro declara '11 puntos' para Alexis, enumera once casos y añade un duodécimo punto de gobernanza... cambiar por 11 casos de decisión y un punto transversal de gobernanza."* | Conforme. |
| **10** | **Normalización y Alcance Físico del PDF** | `catalogo_vf01_normativo.md`, `.csv`, `linea_base_vf01.md`, `pendientes_revision_normativa.md` | Normalizado estrictamente el campo `es_sec_crit` a `SÍ` y `NO` en Markdown y CSV. Corregida la referencia al tamaño del PDF canónico oficial a 298 páginas físicas (según `source_manifest.json`). | Consistencia interna entre archivos y fidelidad con los metadatos físicos del PDF canónico. | Dictamen Codex Inicial, Sección 3 (Bajo/Medio) y Sección 8. | Conforme. |
| **11** | **Estratificación Documental OOD (Observación No Bloqueante)** | `catalogo_vf01_normativo.md`, `linea_base_vf01.md` | Se estratificó la categoría `CANDIDATO_DOCUMENTAL` (41 casos) distinguiendo formalmente: (a) Subtipo A: Pasaje SOR Localizado (35 casos); y (b) Subtipo B: Candidato de Política de Abstención OOD (6 casos: VF01-16, VF01-17, VF01-35, VF01-36, VF01-37, VF01-49), donde la evidencia es `Ninguno (Fuera de Dominio)` y no se atribuye un pasaje inexistente del SOR. | Precisión semántica para no sugerir que las materias ajenas al judo cuentan con un pasaje documental dentro del SOR canónico. | Dictamen Final Reauditoría Codex, Sección 2 y Sección 6: *"Seis registros OOD tienen estado CANDIDATO_DOCUMENTAL, pero su campo de evidencia indica Ninguno... aclarar que abarca dos subtipos: pasaje SOR localizado y política de abstención OOD documentada."* | Conforme. |

---

## 3. Resumen Estructurado: 11 Casos de Decisión y 1 Punto Transversal de Gobernanza

Conforme a las recomendaciones de Codex para garantizar absoluta claridad a Alexis Oliveros Lozano, se dividen los pendientes en dos categorías ontológicas distintas:

### A. Once (11) Casos de Decisión Normativa Específica
1. **VF01-01 (TC-01):** Criterio de completitud en preguntas compuestas (área de combate y seguridad en Art. 8.7 p. 96).
2. **VF01-07 (TC-07):** Alcance mínimo exigido para preguntas de doble categoría (Head diving en Cadetes Art. 18.1.4 vs. Senior Art. 18.2.1).
3. **VF01-09 (TC-09):** Criterio de suficiencia ante subpreguntas de consecuencias (continuidad en la competencia bajo Art. 18.2.1).
4. **VF01-14 (TC-14):** Política ante consultas ambiguas polisémicas (solicitud activa de aclaración vs. matriz estructurada de supuestos).
5. **VF01-23 (MC-01):** Alcance de fuentes (mantener pendiente hasta desplegar Circulares Tier 2 en Paso 3 o responder bajo texto SOR base).
6. **VF01-24 (MC-02):** Definición de oráculo aplicable para límite de kumi-kata (principio general ~45s vs. borrador circular LA28).
7. **VF01-25 (MC-03):** Ratificación formal de política de abstención obligatoria para materias no contenidas en el SOR canónico (298 págs.).
8. **VF01-29 (MC-07):** Redacción y criterio para evaluación de combatividad en transición Tachi-waza a Ne-waza.
9. **VF01-30 (MC-08):** Regla oficial, directriz o circular que gobierna el contacto accidental de cabeza con tatami.
10. **VF01-42 (MC-20):** Regla y localizador oficial aplicable a caídas accidentales de cabeza durante contraataques.
11. **VF01-48 (CGPT-06):** Tratamiento para consultas incompletas sobre agarres bajo Art. 18.1.2.

### B. Un (1) Punto Transversal de Gobernanza
- **Doble revisión formal SEC-CRIT:** Designación formal de evaluadores y firma del protocolo de doble revisión para los 15 casos SEC-CRIT (10 bajo `CANDIDATO_DOCUMENTAL` y 5 bajo `PENDIENTE_REVISION_HUMANA`). No constituye un caso de prueba adicional, sino el requisito de aseguramiento de calidad exigido por el plan para la familia de seguridad.

---

## 4. Cambios no realizados y justificación

- **No se inventaron reglas ni pasajes para MC-08 y MC-20:** Ambos casos permanecen como pendientes humanos en espera de la regla oficial que aporte Alexis.
- **No se inventaron pasajes SOR para los 6 casos OOD:** Se preservó su campo de evidencia como `Ninguno (Fuera de Dominio)` y se explicó su naturaleza de candidatos de política de abstención.
- **No se alteraron los estados distintos a los 41 candidatos:** Los 8 pendientes humanos, el pendiente de evidencia, el caso disputado y el caso sin oráculo permanecen rigurosamente con sus estados correspondientes.
- **No se recalculó una métrica de exactitud definitiva:** Se mantiene suspendida formalmente hasta que se cuente con los oráculos ratificados por Alexis y el registro de doble revisión.
- **No se modificó ningún componente fuera del alcance documental:** Cero alteraciones en código fuente, índices, corpus, configuraciones o Git.

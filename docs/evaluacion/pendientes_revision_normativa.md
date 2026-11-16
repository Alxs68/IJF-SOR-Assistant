# Registro Formal de Casos Pendientes de Revisión Normativa — VF01

> [!NOTE]
> **ESTADO DE RESOLUCIÓN (7 de noviembre de 2026):**  
> Los **11 casos de decisión** registrados en este documento fueron formal y definitivamente **ratificados por Alexis Oliveros Lozano** durante la sesión de validación humana del 7 de noviembre de 2026.  
> Los 11 casos han transitado al estado CONFORME_NORMATIVO (o abstención correcta ratificada en VF01-25) y cuentan con oráculo arbitral definitivo.  
> El expediente integral actualizado se encuentra en [docs/auditoria/validacion_humana_resultados_actuales.md](file:///c:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/validacion_humana_resultados_actuales.md) y el inventario normativo en [docs/evaluacion/catalogo_vf01_normativo.md](file:///c:/PROYECTOS/IJF-SOR-Assistant/docs/evaluacion/catalogo_vf01_normativo.md).

> **Proyecto:** IJF SOR Assistant 2026  
> **Fase:** P0-A.1.2 (Subsanación Documental Final posterior a Reauditoría Codex)  
> **Fecha:** Noviembre 2026  
> **Responsable del proyecto y decisor:** Alexis Oliveros Lozano  
> **Planificador y auditor metodológico:** ChatGPT  
> **Auditor independiente:** Codex (Dictámenes `dictamen_auditoria_p0a_codex.md`, `dictamen_reauditoria_p0a1_codex.md` y `dictamen_reauditoria_final_p0a1_codex.md`)  
> **Ejecutor técnico documental:** Antigravity  
> **Documento normativo base:** `IJF Sport and Organisation Rules 2026` (14 de agosto de 2026, 298 páginas físicas, SHA-256 `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620`)

---

## 1. Propósito del Registro

Este documento reúne formalmente los **11 casos de decisión de la batería consolidada VF01** cuya verdad básica (Gold Standard) o tratamiento de evaluación no puede cerrarse de manera automática o unilateral sin:
1. Una decisión arbitral/editorial de Alexis Oliveros Lozano (8 casos de revisión humana).
2. La definición de alcance de fuentes externas o circulares técnicas (1 caso pendiente de evidencia y 1 disputado).
3. La ratificación de la política de abstención obligatoria para materias fuera de la norma canónica (1 caso sin oráculo).

Adicionalmente, se identifica un **punto transversal de gobernanza** referente a la doble revisión humana obligatoria para los 15 casos SEC-CRIT.

Ninguno de estos casos ha sido clasificado como aprobado de forma arbitraria en el catálogo normativo.

---

## 2. Resumen de Casos Pendientes y Controversias

| ID VF01 | ID Original | Estado Asignado | Tipo de Discrepancia / Causa del Pendiente | Decisión Requerida de Alexis Oliveros |
|---|:---:|:---:|---|---|
| **VF01-01** | TC-01 | `PENDIENTE_REVISION_HUMANA` | Medidas de área de combate y seguridad ambas en Art. 8.7 p. 96; asistente solo devolvió combate | Estándar de completitud en preguntas compuestas |
| **VF01-07** | TC-07 | `PENDIENTE_REVISION_HUMANA` (SEC-CRIT) | Consulta dual (Cadetes vs. Senior) en Head Diving | Alcance mínimo de respuesta para preguntas multicategoría |
| **VF01-09** | TC-09 | `PENDIENTE_REVISION_HUMANA` (SEC-CRIT) | Sanción inmediata clara (Hansoku-make); continuidad de competición omitida | Criterio de suficiencia en preguntas con subpreguntas de consecuencias |
| **VF01-14** | TC-14 | `PENDIENTE_REVISION_HUMANA` (SEC-CRIT) | Consulta abierta/ambigua ("¿Qué pasa si un judoka usa la cabeza?") | Comportamiento esperado: ¿solicitar aclaración o desglosar matriz? |
| **VF01-23** | MC-01 | `PENDIENTE_EVIDENCIA` | Reverse seoi-nage senior autorizado por Circular 2026_01, no en SOR base | Confirmar si el asistente debe abstenerse o si se integrará Circular Tier 2 |
| **VF01-24** | MC-02 | `DISPUTADO` | Tiempo límite kumi-kata: tensión entre regla general (~45s) y proyecto circular LA28 | Ratificar oráculo oficial aplicable para evaluación |
| **VF01-25** | MC-03 | `SIN_ORACULO` | Pregunta sobre congelamiento de reglas LA28 sin soporte en las 298 págs. de SOR base | Declarar oficialmente caso N/A para SOR base (Abstención correcta esperada) |
| **VF01-29** | MC-07 | `PENDIENTE_REVISION_HUMANA` | Evaluación de pasividad integrada (Tachi-waza vs. Ne-waza) | Definir criterio arbitral exacto esperado para la transición |
| **VF01-30** | MC-08 | `PENDIENTE_REVISION_HUMANA` (SEC-CRIT) | Consulta de excepción por contacto involuntario de cabeza; p. 190 no contiene la excepción | Aportar fuente canónica, circular o regla aplicable para involuntariedad |
| **VF01-42** | MC-20 | `PENDIENTE_REVISION_HUMANA` (SEC-CRIT) | Head landing accidental en contraataque; p. 190 no contiene la excepción | Aportar regla oficial y localizador exacto sobre caídas accidentales |
| **VF01-48** | CGPT-06 | `PENDIENTE_REVISION_HUMANA` | Consulta incompleta ("El judoka cometió una falta con el agarre") | Definir si se exige repregunta activa o resumen de faltas comunes Art. 18.1.2 |

---

## 3. Fichas de Detalle de los 11 Casos de Decisión

### Caso 1: VF01-01 (TC-01)
- **Consulta:** *¿Cuáles son las medidas oficiales del área de combate y el área de seguridad del tatami?*
- **Situación:** En el SOR 2026, el **Art. 8.7 (pág. 96)** define íntegramente tanto el área de combate (mínimo 8x8m, máximo 10x10m) como el área de seguridad (mínimo 3m; 4m de zona común entre tatamis contiguos; 50cm de zona libre exterior). En VF01 el asistente extrajo únicamente la frase del área de combate de pág. 96. (Se subsanó el error material previo que atribuía la seguridad al Art. 8.8 pág. 97, que corresponde a Medical).
- **Evidencia disponible:** SOR 2026 Art. 8.7 pág. 96.
- **Decisión requerida de Alexis:**  
  ¿Debe exigirse que una respuesta sea calificada como `FAIL` o `PARTIAL` si omite una de las dos medidas solicitadas explícitamente en la pregunta compuesta a pesar de estar ambas en el mismo pasaje?  
  *(Recomendación técnica: Exigir ambas medidas para considerar la respuesta completa y correcta).*

---

### Caso 2: VF01-07 (TC-07) — SEC-CRIT
- **Consulta:** *¿Se permite a Tori utilizar la cabeza para proyectar al oponente en categorías Cadete y Senior?*
- **Situación:** El Art. 18.2.1 (pág. 190) penaliza el Head Diving con Hansoku-make directo en Senior (permitiendo continuar en el evento). El Art. 18.1.4 (pág. 188) establece una tutela especial para Cadetes (Shido por apoyo voluntario para proyección, escalable a Hansoku-make si hay peligro cervical). El asistente solo devolvió la cita de Cadetes (pág. 188).
- **Evidencia disponible:** SOR 2026 págs. 188 y 190.
- **Decisión requerida de Alexis:**  
  Al tratarse de un caso SEC-CRIT con dos categorías explícitas, ¿se ratifica que la respuesta oro DEBE contener la distinción explícita de ambas categorías?  
  *(Recomendación técnica: Sí, por tratarse de seguridad arbitral de menores vs. adultos).*

---

### Caso 3: VF01-09 (TC-09) — SEC-CRIT
- **Consulta:** *¿Qué sanción se aplica por realizar Head Diving y qué consecuencia tiene sobre la continuidad en la competición?*
- **Situación:** El Art. 18.2.1 (pág. 190) fija Hansoku-make, pero aclara expresamente que al tratarse de una técnica peligrosa (y no de una falta contra el espíritu del judo / Art. 18.2.2), el judoka **SÍ puede continuar compitiendo** en las siguientes rondas o repescas. El asistente respondió Hansoku-make, pero omitió responder sobre la continuidad.
- **Evidencia disponible:** SOR 2026 pág. 190 (Art. 18.2.1 vs. Art. 18.2.2).
- **Decisión requerida de Alexis:**  
  ¿La omisión de la consecuencia de continuidad invalida el PASS del caso en la auditoría?  
  *(Recomendación técnica: Clasificar como PARCIAL o FAIL hasta que el reconstructor integre la segunda cláusula).*

---

### Caso 4: VF01-14 (TC-14) — SEC-CRIT
- **Consulta:** *¿Qué pasa si un judoka usa la cabeza?*
- **Situación:** Pregunta abierta y polisémica. En judo, usar la cabeza puede ser: (1) Head Diving ofensivo (Hansoku-make, Art. 18.2.1); (2) Apoyo en cadetes (Shido, Art. 18.1.4); (3) Defensa involuntaria o contacto accidental; (4) Puente de cuello (Ippon en contra / sanción).
- **Decisión requerida de Alexis:**  
  ¿Cuál es la política oficial de ADA ante consultas con múltiples ramas normativas: debe solicitar aclaración ("¿Te refieres a ataque, defensa o categoría cadete?") o presentar un desglose estructurado de los supuestos principales?

---

### Caso 5: VF01-23 (MC-01)
- **Consulta:** *¿Está permitido el reverse seoi-nage en competidores seniors?*
- **Situación:** En el documento base SOR 2026-08 (14 de agosto de 2026), la técnica solo se menciona explícitamente en el Art. 18.1.4 (pág. 189) como falta prohibida para cadetes e infantiles. La autorización para competidores Senior proviene de la **Circular Técnica 2026_01**. En la arquitectura Lean actual sin Paso 3, el motor RRE recuperó pág. 64 (cupos WRL).
- **Decisión requerida de Alexis:**  
  ¿Se evalúa este caso exigiendo la respuesta de la Circular (lo que obliga a mantenerlo como PENDIENTE_EVIDENCIA hasta desplegar el Paso 3), o se instruye al sistema para que informe que en el texto canónico del SOR 2026-08 solo figura prohibido en cadetes?

---

### Caso 6: VF01-24 (MC-02)
- **Consulta:** *¿Cuál es el límite de tiempo para la disputa de kumi-kata sin ataque?*
- **Situación:** El texto canónico del Art. 18.1.1 (pág. 177) establece una sanción de Shido por falta de combatividad ("taking more than necessary time to take a grip"), estimado por el árbitro en aproximadamente 45 segundos según la práctica arbitral general. Por su parte, borradores de circulares para el ciclo LA28 mencionaban límites más estrictos (30 segundos).
- **Decisión requerida de Alexis:**  
  Fijar formalmente el oráculo: ¿aplica el estándar canónico general (~45s / apreciación arbitral inmediata tras kumi-kata convencional) o el criterio de circular?

---

### Caso 7: VF01-25 (MC-03)
- **Consulta:** *¿A partir de qué evento se congelan las reglas para el ciclo olímpico LA28?*
- **Situación:** No existe ninguna mención sobre el congelamiento de reglas para Los Ángeles 2028 en las 298 páginas físicas del PDF oficial SOR 2026-08. El asistente se abstuvo técnicamente (`status: ABSTAIN`).
- **Decisión requerida de Alexis:**  
  Ratificar formalmente que para este caso la respuesta correcta esperada es una **abstención formal por falta de oráculo canónico**. Si se ratifica, el caso pasa a ser evaluado como abstención válida esperada.

---

### Caso 8: VF01-29 (MC-07)
- **Consulta:** *¿Cómo se evalúa la no combatividad o pasividad entre judo de pie y suelo?*
- **Situación:** Tachi-waza y Ne-waza tienen tratamientos disímiles: en pie, la pasividad genera Shido acumulativo (Art. 18.1.1); en suelo, la falta de acción continua no genera Shido, sino la orden de Mate para reiniciar en pie, salvo retardo deliberado.
- **Decisión requerida de Alexis:**  
  Ratificar la redacción exacta esperada para el estándar oro de este caso.

---

### Caso 9: VF01-30 (MC-08) — SEC-CRIT
- **Consulta:** *¿Existe excepción de Hansoku-make si el contacto de cabeza con tatami es involuntario?*
- **Situación:** El dictamen de Codex reveló que el pasaje citado en P0-A (pág. 190, Art. 18.2.1 y 18.2.2) describe la prohibición de Head Diving y actos contra el espíritu (kawazu-gake), pero **NO expresa una excepción de involuntariedad/accidentalidad**. Por tanto, la aprobación previa carecía de respaldo probatorio en la cita indicada.
- **Evidencia disponible:** Pág. 190 (insuficiente para probar excepción).
- **Decisión requerida de Alexis:**  
  Aportar el artículo, circular técnica o directriz arbitral exacta de la FIJ que establezca formalmente cómo se juzga el contacto accidental de cabeza para fijar el oráculo.

---

### Caso 10: VF01-42 (MC-20) — SEC-CRIT
- **Consulta:** *If an athlete lands accidentally on the head during a counter throw, is it hansoku-make?*
- **Situación:** Al igual que en VF01-30, la respuesta aprobada asumía la existencia de una excepción explícita en el Art. 18.2.2 pág. 190 que no figura en el texto canónico.
- **Evidencia disponible:** Pág. 190 (insuficiente para probar excepción).
- **Decisión requerida de Alexis:**  
  Fijar la regla arbitral y el localizador normativo canónico aplicable para caídas accidentales durante contraataques.

---

### Caso 11: VF01-48 (CGPT-06)
- **Consulta:** *El judoka cometió una falta con el agarre.*
- **Situación:** Consulta amplia sobre kumi-kata e infracciones de agarre bajo el Art. 18.1.2.
- **Resolución Oficial Ratificada por Alexis Oliveros (07/11/2026):** Ratificado plenamente bajo Art. 18.1.2 (págs. 178-184 canónicas / 169-175 preliminar):
  1. Agarres no convencionales (cross grip, same-side, belt grip, pocket, pistol, inside jacket sleeve) permitidos con actitud positiva y progresión hacia el ataque, sin exigencia de ataque inmediato ni límite rígido de tiempo.
  2. Límite bajo el cinturón: permitido hasta la parte superior del muslo interno (*top of the inner thigh*); por debajo, todo agarre o contacto de pierna/pantalón en tachi-waza se sanciona con Shido (*leg grabbing*).
  3. Romper agarre con dos manos conservando al menos un agarre propio está PERMITIDO; si se rompe con dos manos liberando completamente al adversario sin conservar agarre es SHIDO (romper con una mano sin conservar agarre está permitido).
  4. Prohibiciones estrictas sancionadas con Shido: inside trouser leg en tachi-waza, romper con pierna o rodilla, interlocking fingers y cubrir la solapa para impedir el kumi-kata.
  5. Caso formalmente cerrado como `CONFORME_NORMATIVO`.
---

## 4. Punto Transversal de Gobernanza: Doble Revisión SEC-CRIT

- **Materia:** Proceso de acreditación formal de seguridad arbitral.
- **Alcance:** Aplica transversalmente a los **15 casos SEC-CRIT** del catálogo (10 con condición de `CANDIDATO_DOCUMENTAL` y 5 bajo `PENDIENTE_REVISION_HUMANA`).
- **Decisión requerida de Alexis Oliveros Lozano:**  
  Designar al revisor normativo independiente o panel arbitral calificado y establecer el mecanismo de firma formal y fecha de revisión dual requerida para certificar definitivamente cualquier caso crítico de seguridad.

---

## 5. Próximos Pasos tras Resolución

Una vez que Alexis Oliveros Lozano emita su dictamen sobre los 11 casos de decisión y se formalice el punto transversal de gobernanza SEC-CRIT:
1. Se actualizarán las fichas correspondientes en `docs/evaluacion/catalogo_vf01_normativo.md` y `.csv`.
2. Se consolidará la Línea Base Normativa definitiva en `docs/evaluacion/linea_base_vf01.md`.
3. Se someterá a reauditoría independiente de Codex para el cierre formal de P0-A.1 y la eventual autorización de la Fase P0-B.

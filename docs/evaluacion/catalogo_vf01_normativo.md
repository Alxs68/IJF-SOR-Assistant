# Catálogo de Casos Oro y Línea Base Normativa — VF01 Consolidada

> **Proyecto:** IJF SOR Assistant 2026  
> **Fase:** P0-A.1.2 (Subsanación Documental Final posterior a Reauditoría Codex)  
> **Fecha de consolidación:** Noviembre 2026  
> **Responsable del proyecto y decisor final:** Alexis Oliveros Lozano  
> **Planificador y auditor metodológico:** ChatGPT  
> **Auditor independiente:** Codex (Dictámenes `dictamen_auditoria_p0a_codex.md`, `dictamen_reauditoria_p0a1_codex.md` y `dictamen_reauditoria_final_p0a1_codex.md`)  
> **Ejecutor técnico documental:** Antigravity  
> **Documento canónico oficial:** `IJF Sport and Organisation Rules 2026` (14 de agosto de 2026, 298 páginas físicas, SHA-256 `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620`)

---

## 1. Introducción y Marco Metodológico

El presente catálogo establece la **verdad básica documental preliminar** para los 52 casos evaluados en la Validación Funcional Consolidada VF01. Surge a raíz de la Auditoría Integral de Código (`docs/auditoria_integral_codigo.md`), el Dictamen de Auditoría Independiente VF01 (`docs/dictamen_auditoria_vf01.md`) y los sucesivos dictámenes de auditoría independiente de Codex (`docs/evaluacion/dictamen_auditoria_p0a_codex.md`, `dictamen_reauditoria_p0a1_codex.md` y `dictamen_reauditoria_final_p0a1_codex.md`).

Los dictámenes de auditoría demostraron que la clasificación técnica previa de `52/52 PASS (100%)` adolecía de un falso positivo sistemático al certificar como exitosas respuestas técnicamente ejecutadas (`SUCCESS` o `ABSTAIN` de pipeline) pero materialmente incompletas, genéricas o normativamente incorrectas.

### Diferenciación Estricta de Estados Normativos
Conforme a los dictámenes de Codex, se distingue formalmente entre candidatos documentales preliminares y oráculos normativos plenamente certificados por revisión humana formal:

1. **`CANDIDATO_DOCUMENTAL` (41 casos):** Casos preliminares sin controversia material directa, que abarcan dos subtipos diferenciados por su naturaleza de evidencia:
   - **Subtipo A: Pasaje SOR Localizado (35 casos):** Existe texto normativo canónico suficiente y claro en el SOR 2026 (14 de agosto de 2026). El pasaje candidato está localizado y cotejado documentalmente con el texto oficial.
   - **Subtipo B: Candidato de Política de Abstención OOD (6 casos):** Consultas fuera de dominio (VF01-16, VF01-17, VF01-35, VF01-36, VF01-37, VF01-49) donde no existe pasaje en el SOR (`Ninguno (Fuera de Dominio)`) y el oráculo preliminar estipula una abstención técnica obligatoria (`ABSTAIN`). No representan pasajes normativos de judo, sino candidatos documentados de la política de rechazo de dominio del asistente.
   *Nota metodológica: Ninguno de estos 41 casos equivale a un oráculo normativo definitivamente cerrado con doble revisión humana ni consenso de panel arbitral; representan candidatos documentales trazados a la espera de certificación formal.*
2. **`PENDIENTE_REVISION_HUMANA` (0 casos):** Todos los casos que requerían pronunciamiento humano han sido oficial y formalmente ratificados por Alexis Oliveros Lozano (07/11/2026).
3. **`PENDIENTE_EVIDENCIA` (0 casos):** El caso VF01-23 fue ratificado conforme al texto del SOR base (prohibición exclusiva para Cadetes Art. 18.1.4 p. 189).
4. **`SIN_ORACULO` (1 caso):** VF01-25 / Congelamiento ciclo LA28 ratificado formalmente como `APROBADO_ABSTENCION_CORRECTA`.
5. **`DISPUTADO` (0 casos):** El caso VF01-24 fue resuelto conforme al estándar canónico de No Combatividad del Art. 18.1.1 (p. 177).

---

## 2. Resumen Ejecutivo del Catálogo

| Métrica / Dimensión | Cantidad | Porcentaje | Estado de Certificación |
|---|:---:|:---:|---|
| **Total de Casos Consolidados** | **52** | **100.0%** | Inventario completo y único |
| **Candidatos Documentales Preliminares (`CANDIDATO_DOCUMENTAL`)** | **41** | **78.8%** | Pendiente registro formal de revisor y doble revisión |
| — *Subtipo A: Pasaje SOR Localizado en Texto Oficial* | *35* | *67.3%* | Pasaje canónico identificado y cotejado |
| — *Subtipo B: Candidato de Política de Abstención OOD* | *6* | *11.5%* | Materia ajena al judo; política de abstención documentada |
| Casos Pendientes de Revisión Humana Arbitral (`PENDIENTE_REVISION_HUMANA`) | 0 | 0.0% | **100% de casos resueltos por Alexis Oliveros** |
| Casos Pendientes de Evidencia Tier 2 (`PENDIENTE_EVIDENCIA`) | 0 | 0.0% | Resuelto canónicamente |
| Casos Sin Oráculo Canónico (`SIN_ORACULO`) | 1 | 1.9% | No existe en 298 págs. SOR canónico base |
| Casos con Tensión o Interpretación Disputada (`DISPUTADO`) | 0 | 0.0% | Resuelto canónicamente |
| **Casos Críticos de Seguridad Arbitral (SEC-CRIT)** | **15** | **28.8%** | **Materia prioritaria de seguridad** |
| *SEC-CRIT con Pasaje Candidato Identificado* | *10* | *66.7% de SEC-CRIT* | Requiere segunda revisión humana formal obligatoria |
| *SEC-CRIT Pendientes de Revisión Humana Arbitral* | *0* | *0.0% de SEC-CRIT* | **100% de SEC-CRIT resueltos y trazados** |

---

## 3. Sección Especial: Casos Críticos y Prioritarios

A continuación se analiza detalladamente el grupo de casos de alta sensibilidad arbitral e histórica (TC-04, TC-11, TC-12, TC-15, MC-13, VF01-09, VF01-42, MC-04, MC-05, VF01-01, VF01-30):

### VF01-01 (TC-01): ¿Cuáles son las medidas oficiales del área de combate y el área de seguridad del tatami? — ✅ **CONFORME_NORMATIVO**
- **Batería de origen:** `TC_HISTORIC` | **Crítico de Seguridad (SEC-CRIT):** `NO`
- **Tipo de consulta:** Factual / Infraestructura
- **Respuesta esperada oficial (Gold Standard):** Área de combate: mínimo 8x8m, máximo 10x10m. Área de seguridad: mínimo 3m (4m entre áreas contiguas, 50cm de zona libre exterior).
- **Respuesta generada en VF01:** **8.7 Field of Play and Competition Area (Art. 8.7, Pág. 96) [SOR-2026-08-P096-S114](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=96):** The contest area for IJF events shall be a minimum of 8 m x 8 m and a maximum of 10 m x 10 m. Disposiciones comple...
- **Resultado técnico original:** `SUCCESS / PASS` (PASS por pipeline)
- **Dictamen auditoría independiente:** `Genérico / insuficiente`
- **Estado de validación normativa:** `CONFORME_NORMATIVO` (Dictamen arbitral ratificado por Alexis Oliveros: solo lo textual del reglamento, sin totales)
- **Evidencia y referencias canónicas:** Art. 8.7 (p. 96) (Págs. SOR: 96)
- **Suficiencia de evidencia recuperada:** `INSUFICIENTE_PARCIAL`
- **Condiciones y excepciones normativas:** El Art. 8.7 (pág. 96) define integralmente ambas áreas: combate (8x8m a 10x10m) y seguridad (mínimo 3m; 4m común entre tatamis contiguos; 50cm zona libre perimetral).
- **Diagnóstico de la discrepancia:** La respuesta VF01 extrajo de p. 96 únicamente el fragmento de área de combate (8x8 a 10x10m) omitiendo las dimensiones de seguridad presentes en el mismo Art. 8.7 p. 96. Corregida la referencia errónea previa que citaba Art. 8.8 p. 97 (p. 97 corresponde a Medical).

### VF01-04 (TC-04): Tori proyecta a Uke aplicando una técnica con fuerza y velocidad, pero Uke cae sobre un costado con el cuerpo perpendicular al tatami. ¿Qué puntuación corresponde?
- **Batería de origen:** `TC_HISTORIC` | **Crítico de Seguridad (SEC-CRIT):** `NO`
- **Tipo de consulta:** Escenario Arbitral / Puntuación
- **Respuesta esperada oficial (Gold Standard):** Waza-ari (caída sobre el costado / impacto a más de 90° con respecto a la espalda sin cumplir los criterios de Ippon).
- **Respuesta generada en VF01:** **8.7 Field of Play and Competition Area (Art. 8.7, Pág. 96) [SOR-2026-08-P096-S114](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=96):** The contest area for IJF events shall be a minimum of 8 m x 8 m and a maximum of 10 m x 10 m. Disposiciones comple...
- **Resultado técnico original:** `SUCCESS / PASS` (PASS por pipeline)
- **Dictamen auditoría independiente:** `Incorrecto`
- **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
- **Evidencia y referencias canónicas:** Art. 15 Waza-ari (p. 168-169) (Págs. SOR: 168, 169)
- **Suficiencia de evidencia recuperada:** `SUFICIENTE (en SOR, falló recuperación)`
- **Condiciones y excepciones normativas:** Si el eje de hombros supera 90° con respecto al tatami pero no es sobre la espalda, es Waza-ari.
- **Diagnóstico de la discrepancia:** RRE recuperó Art. 8.7 (p. 96) por dispersión léxica de 'costado/tatami'. La verdad de base en SOR 2026 p. 168 establece taxativamente Waza-ari.

### VF01-09 (TC-09): ¿Qué sanción se aplica por realizar Head Diving y qué consecuencia tiene sobre la continuidad en la competición?
- **Batería de origen:** `TC_HISTORIC` | **Crítico de Seguridad (SEC-CRIT):** `SÍ`
- **Tipo de consulta:** Seguridad Arbitral / Consecuencia Disciplinaria
- **Respuesta esperada oficial (Gold Standard):** Sanción: Hansoku-make directo (Art. 18.2.1). Consecuencia de continuidad: al ser una falta técnica peligrosa (dangerous technique), el atleta PUEDE continuar en las siguientes rondas/repetchage (a diferencia de faltas morales contra el espíritu).
- **Respuesta generada en VF01:** **Article 18.2.1 Hansoku-make for Dangerous Techniques (Art. Article 18.2.1, Pág. 190) [SOR-2026-08-P190-S197](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=190):** Techniques using head diving are dangerous and will be penalised with hansoku-make. Dis...
- **Resultado técnico original:** `SUCCESS / PASS` (PASS por pipeline)
- **Dictamen auditoría independiente:** `Genérico / insuficiente`
- **Estado de validación normativa:** `CONFORME_NORMATIVO` (Dictamen arbitral ratificado por Alexis Oliveros: solo lo textual del reglamento, sin totales)
- **Evidencia y referencias canónicas:** Art. 18.2.1 (p. 190) y Art. 18.2.2 (p. 190-193) (Págs. SOR: 190)
- **Suficiencia de evidencia recuperada:** `INSUFICIENTE_PARCIAL`
- **Condiciones y excepciones normativas:** Art. 18.2.1 especifica: 'can bring the athlete to next contest' vs Art. 18.2.2: 'cannot continue'.
- **Diagnóstico de la discrepancia:** El asistente dictaminó Hansoku-make pero omitió responder si puede o no continuar compitiendo.

### VF01-11 (TC-11): ¿Qué sanción corresponde por aplicar kawazu-gake durante un combate?
- **Batería de origen:** `TC_HISTORIC` | **Crítico de Seguridad (SEC-CRIT):** `SÍ`
- **Tipo de consulta:** Técnica Prohibida Peligrosa / Sanción
- **Respuesta esperada oficial (Gold Standard):** Hansoku-make directo por técnica prohibida peligrosa / actos contra el espíritu del judo (Art. 18.2.2 punto 1, p. 190). El atleta descalificado por este motivo NO puede continuar en la competición.
- **Respuesta generada en VF01:** **Article 4 Gestures (Art. Article 4, Pág. 149) [SOR-2026-08-P149-S177](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=149):** point with the forefinger at the athlete to be penalised. Disposiciones complementarias aplicables en Art. Article 13 (Pág. 16...
- **Resultado técnico original:** `SUCCESS / PASS` (PASS por pipeline)
- **Dictamen auditoría independiente:** `Incorrecto`
- **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
- **Evidencia y referencias canónicas:** Art. 18.2.2 punto 1 (p. 190) (Págs. SOR: 190)
- **Suficiencia de evidencia recuperada:** `SUFICIENTE (en SOR, falló recuperación)`
- **Condiciones y excepciones normativas:** Kawazu-gake está taxativamente prohibida bajo Art. 18.2.2 punto 1 (pág. 190). Se penaliza con Hansoku-make directo sin derecho a continuar en la competición.
- **Diagnóstico de la discrepancia:** La respuesta histórica generada en VF01 devolvió de forma errónea Art. 4 Gestures (pág. 149), debido a que el motor RRE no reconoció el término japonés kawazu-gake. El pasaje canónico candidato está perfectamente identificado en Art. 18.2.2 p. 190, pero no cuenta aún con registro de segunda revisión humana formal.

### VF01-12 (TC-12): ¿Es válido puntuar una proyección que se inicia dentro del tatami pero culmina fuera del área de combate en la zona de seguridad?
- **Batería de origen:** `TC_HISTORIC` | **Crítico de Seguridad (SEC-CRIT):** `NO`
- **Tipo de consulta:** Límites del Tatami / Validez de Acción
- **Respuesta esperada oficial (Gold Standard):** Sí, es válida para puntuación siempre que la acción técnica se haya iniciado de forma continua dentro del área de combate y culmine hasta 2 metros en el área de seguridad sin interrupción.
- **Respuesta generada en VF01:** **8.7 Field of Play and Competition Area (Art. 8.7, Pág. 96) [SOR-2026-08-P096-S114](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=96):** The contest area for IJF events shall be a minimum of 8 m x 8 m and a maximum of 10 m x 10 m. Disposiciones comple...
- **Resultado técnico original:** `SUCCESS / PASS` (PASS por pipeline)
- **Dictamen auditoría independiente:** `Incorrecto`
- **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
- **Evidencia y referencias canónicas:** Art. 5 Location (p. 151) (Págs. SOR: 151)
- **Suficiencia de evidencia recuperada:** `SUFICIENTE (en SOR, falló recuperación)`
- **Condiciones y excepciones normativas:** Excepción (d): la técnica debe tener continuidad inmediata sin parada intermedia.
- **Diagnóstico de la discrepancia:** RRE devolvió Art. 8.7 p. 96 (medidas del tatami) en vez de Art. 5 Exceptions p. 151.

### VF01-15 (TC-15): ¿Cuándo se marca mate?
- **Batería de origen:** `TC_HISTORIC` | **Crítico de Seguridad (SEC-CRIT):** `NO`
- **Tipo de consulta:** Comando Arbitral / Detención de Combate
- **Respuesta esperada oficial (Gold Standard):** El árbitro anunciará Mate! para detener temporalmente el combate en los casos taxativos del Art. 11: salida del tatami, inacción en suelo sin progresión, falta cometida, lesión, reajuste de judogi o situación de peligro.
- **Respuesta generada en VF01:** **C1.3 Location of the Manufacturer’s Logo (Art. C1.3, Pág. 119) [SOR-2026-08-P119-S158](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=119):** Only one manufacturer’s logo per clothing item is allowed (jacket, trousers, and belt). Disposiciones complem...
- **Resultado técnico original:** `SUCCESS / PASS` (PASS por pipeline)
- **Dictamen auditoría independiente:** `Incorrecto`
- **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
- **Evidencia y referencias canónicas:** Art. 11 Mate (p. 160-161) (Págs. SOR: 160, 161)
- **Suficiencia de evidencia recuperada:** `SUFICIENTE (en SOR, falló recuperación)`
- **Condiciones y excepciones normativas:** Casos taxativos del artículo 11.
- **Diagnóstico de la discrepancia:** RRE devolvió C1.3 p. 119 por colisión léxica de 'mate' con 'material del judogi'. La verdad canónica reside en Art. 11 pp. 160-161.

### VF01-26 (MC-04): ¿Cómo evalúa el árbitro la continuidad en la transición de tachi-waza a ne-waza?
- **Batería de origen:** `MC_HISTORIC` | **Crítico de Seguridad (SEC-CRIT):** `NO`
- **Tipo de consulta:** Criterio Arbitral / Transición
- **Respuesta esperada oficial (Gold Standard):** El árbitro permite la continuidad sin interrupción si hay acción ofensiva inmediata y control efectivo. Si la acción se detiene sin ataque, debe mandar Mate! (SOR p. 159).
- **Respuesta generada en VF01:** **waza (B) (Art. GENERAL, Pág. 159) [SOR-2026-08-P159-S183](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=159):** Situations that allow the transition from tachi-waza to ne-waza a) When one of the athletes, lands on the ground and there is no score, yu...
- **Resultado técnico original:** `SUCCESS / PASS` (PASS por pipeline)
- **Dictamen auditoría independiente:** `Correcto normativamente`
- **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
- **Evidencia y referencias canónicas:** Transición Tachi/Ne-waza (p. 159) (Págs. SOR: 159)
- **Suficiencia de evidencia recuperada:** `SUFICIENTE`
- **Condiciones y excepciones normativas:** La acción no debe quebrarse; si Uke queda inerte o Tori no progresa, se ordena Mate.
- **Diagnóstico de la discrepancia:** El pasaje de p. 159 contiene exactamente la regla de transición. La etiqueta devuelta fue `GENERAL` pero el contenido normativo es impecable.

### VF01-27 (MC-05): ¿Se sanciona con Shido halar o arrastrar al oponente directamente a ne-waza?
- **Batería de origen:** `MC_HISTORIC` | **Crítico de Seguridad (SEC-CRIT):** `NO`
- **Tipo de consulta:** Infracción / Transición Ilícita
- **Respuesta esperada oficial (Gold Standard):** Sí, halar o tirarse al suelo directamente para llevar a ne-waza sin aplicar una técnica válida de judo se sanciona con Shido a quien comete la acción (SOR p. 159).
- **Respuesta generada en VF01:** **waza (B) (Art. GENERAL, Pág. 159) [SOR-2026-08-P159-S183](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=159):** Exceptions When one athlete pulls his opponent down into ne-waza not in accordance with the above rules and his opponent does not take adv...
- **Resultado técnico original:** `SUCCESS / PASS` (PASS por pipeline)
- **Dictamen auditoría independiente:** `Correcto normativamente`
- **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
- **Evidencia y referencias canónicas:** Transición Tachi/Ne-waza (p. 159) y Art. 18.1.2 (Págs. SOR: 159)
- **Suficiencia de evidencia recuperada:** `SUFICIENTE`
- **Condiciones y excepciones normativas:** Si el rival aprovecha la acción y toma ventaja en suelo, el árbitro puede dejar continuar.
- **Diagnóstico de la discrepancia:** El pasaje de p. 159 contiene la regla textual. Coincidencia plena con la doctrina oficial.

### VF01-30 (MC-08): ¿Existe excepción de Hansoku-make si el contacto de cabeza con tatami es involuntario?
- **Batería de origen:** `MC_HISTORIC` | **Crítico de Seguridad (SEC-CRIT):** `SÍ`
- **Tipo de consulta:** Seguridad Arbitral / Excepción Involuntariedad
- **Respuesta esperada oficial (Gold Standard):** Pendiente de ratificación arbitral / fuente exacta. La pág. 190 regula Head Diving (Art. 18.2.1) y actos contra el espíritu/kawazu-gake (Art. 18.2.2), pero NO contiene una excepción textual expresa para aterrizaje accidental de cabeza en contraataque.
- **Respuesta generada en VF01:** **Article 18.2.2 Hansoku-make for Acts against the Spirit of Judo (Art. Article 18.2.2, Pág. 190) [SOR-2026-08-P190-S198](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=190):** a) To make any action this may endanger or injure the opponent especially th...
- **Resultado técnico original:** `SUCCESS / PASS` (PASS por pipeline)
- **Dictamen auditoría independiente:** `Incorrecto (en respuesta generada)`
- **Estado de validación normativa:** `PENDIENTE_REVISION_HUMANA`
- **Evidencia y referencias canónicas:** Art. 18.2.1 / Art. 18.2.2 (p. 190) [Sin respaldo textual de excepción accidental] (Págs. SOR: 190)
- **Suficiencia de evidencia recuperada:** `INSUFICIENTE_SIN_RESPALDO_TEXTUAL`
- **Condiciones y excepciones normativas:** La cita empleada (p. 190) no respalda la excepción de involuntariedad formulada. Requiere que Alexis Oliveros / panel arbitral identifiquen la regla, circular o directriz exacta que gobierna la accidentalidad.
- **Diagnóstico de la discrepancia:** Aprobación normativa revocada conforme al Dictamen Codex. En p. 190 no existe la excepción expresa de involuntariedad; la cita previa era incorrecta para sostener una verdad básica fijada.

### VF01-35 (MC-13): ¿Cuántos tiempos fuera puede pedir el entrenador en un partido de baloncesto?
- **Batería de origen:** `MC_HISTORIC` | **Crítico de Seguridad (SEC-CRIT):** `NO`
- **Tipo de consulta:** Fuera de Dominio (OOD)
- **Respuesta esperada oficial (Gold Standard):** ABSTAIN (Materia ajena a las Reglas Oficiales de Judo de la IJF).
- **Respuesta generada en VF01:** **7.2 Coaches’ Dress Code (Art. 7.2, Pág. 89) [SOR-2026-08-P089-S105](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=89):** Coaches must respect the following dress code:. Disposiciones complementarias aplicables en Art. F1.3.1 (Pág. 208), Art. F1.3.29 ...
- **Resultado técnico original:** `SUCCESS / PASS` (PASS por pipeline)
- **Dictamen auditoría independiente:** `Incorrecto (Falso PASS)`
- **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
- **Evidencia y referencias canónicas:** Ninguno (Fuera de Dominio) (Págs. SOR: N/A)
- **Suficiencia de evidencia recuperada:** `SUFICIENTE (para abstención)`
- **Condiciones y excepciones normativas:** Debe abstenerse sin importar que contenga la palabra 'entrenador'.
- **Diagnóstico de la discrepancia:** El sistema falló en abstenerse: devolvió Art. 7.2 p. 89 (vestimenta de entrenadores de judo). Caso bandera de corrección OOD P1.

### VF01-42 (MC-20): If an athlete lands accidentally on the head during a counter throw, is it hansoku-make?
- **Batería de origen:** `MC_HISTORIC` | **Crítico de Seguridad (SEC-CRIT):** `SÍ`
- **Tipo de consulta:** Bilingüe / Seguridad Arbitral / Excepción
- **Respuesta esperada oficial (Gold Standard):** Pending referee ratification / exact source. Page 190 defines head diving as a dangerous technique (Art. 18.2.1) and lists acts against the spirit (Art. 18.2.2), but does NOT express an accidental landing exception during counter throws.
- **Respuesta generada en VF01:** **Article 18.2.2 Hansoku-make for Acts against the Spirit of Judo (Art. Article 18.2.2, Pág. 190) [SOR-2026-08-P190-S198](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=190):** If this type of hansoku-make is awarded the athlete CANNOT continue in the c...
- **Resultado técnico original:** `SUCCESS / PASS` (PASS por pipeline)
- **Dictamen auditoría independiente:** `Incorrecto (en respuesta generada)`
- **Estado de validación normativa:** `PENDIENTE_REVISION_HUMANA`
- **Evidencia y referencias canónicas:** Art. 18.2.1 / Art. 18.2.2 (p. 190) [Sin respaldo textual de excepción accidental] (Págs. SOR: 190)
- **Suficiencia de evidencia recuperada:** `INSUFICIENTE_SIN_RESPALDO_TEXTUAL`
- **Condiciones y excepciones normativas:** The cited passage (p. 190) does not contain the accidental counter throw exception. Requires formal referee ruling and exact citation from Alexis Oliveros.
- **Diagnóstico de la discrepancia:** Normative approval revoked per Codex audit. The text on p. 190 does not support the stated exception; cannot be certified as approved gold standard without canonical evidence.

---

## 4. Fichas Individuales de los 52 Casos del Catálogo Oro

### [VF01-01] TC-01 - ¿Cuáles son las medidas oficiales del área de combate y el área de seguridad del tatami? — ✅ **CONFORME_NORMATIVO**\n
1. **Identificador original / VF01:** `TC-01` / `VF01-01` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cuáles son las medidas oficiales del área de combate y el área de seguridad del tatami?
3. **Tipo de consulta:** Factual / Infraestructura | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Área de combate: mínimo 8x8m, máximo 10x10m. Área de seguridad: mínimo 3m (4m entre áreas contiguas, 50cm de zona libre exterior).
5. **Respuesta generada por el asistente (VF01):** **8.7 Field of Play and Competition Area (Art. 8.7, Pág. 96) [SOR-2026-08-P096-S114](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=96):** The contest area for IJF events shall be a minimum of 8 m x 8 m and a maximum of 10 m x 10 m. Disposiciones complementarias aplicables en Art. 8.6 (Pág. 95), Art. 8.8 (Pág. 97).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** Art. 8.7 (p. 96)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 96 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** SUFICIENTE_COMPLETO\n11. **Estado de validación normativa:** CONFORME_NORMATIVO (Dictamen arbitral ratificado por Alexis Oliveros: medidas textuales sin calcular totales)\n12. **Observaciones, condiciones y discrepancias:** El Art. 8.7 (pág. 96) define integralmente ambas áreas: combate (8x8m a 10x10m) y seguridad (mínimo 3m; 4m común entre tatamis contiguos; 50cm zona libre perimetral). _Discrepancia técnica:_ La respuesta VF01 extrajo de p. 96 únicamente el fragmento de área de combate (8x8 a 10x10m) omitiendo las dimensiones de seguridad presentes en el mismo Art. 8.7 p. 96. Corregida la referencia errónea previa que citaba Art. 8.8 p. 97 (p. 97 corresponde a Medical).

---

### [VF01-02] TC-02 — ¿Cuánto tiempo dura un combate oficial en categoría Senior masculina y femenina?

1. **Identificador original / VF01:** `TC-02` / `VF01-02` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cuánto tiempo dura un combate oficial en categoría Senior masculina y femenina?
3. **Tipo de consulta:** Factual / Reglamentario | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** 4 minutos tanto para hombres como para mujeres.
5. **Respuesta generada por el asistente (VF01):** **Article 7 Osaekomi Time (Art. Article 7, Pág. 152) [SOR-2026-08-P152-S180](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=152):** a) Ippon: 20 seconds. b) Waza-ari: 10 seconds or more but less than 20 seconds (10-19 seconds). c) Yuko: 5 seconds or more but less than 10 seconds (5-9 seconds). Disposiciones complementarias aplicables en Art. Article 9 (Pág. 153), Art. Article 13 (Pág. 164).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto (en respuesta generada)`
8. **Evidencia normativa (Artículos):** Art. 7 Duration of the Contest (p. 152)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 152 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Aplica a categoría Senior y Junior. Sin límite en Golden Score. _Discrepancia técnica:_ El motor RRE recuperó correctamente Art. 7 (p. 152) en Top-1, pero el fallback determinista de ADA seleccionó una frase sobre osaekomi de otro párrafo. La norma y evidencia están verificadas en SOR p. 152.

---

### [VF01-03] TC-03 — ¿Cuáles son los cuatro criterios indispensables para que una proyección sea valorada como Ippon?

1. **Identificador original / VF01:** `TC-03` / `VF01-03` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cuáles son los cuatro criterios indispensables para que una proyección sea valorada como Ippon?
3. **Tipo de consulta:** Factual / Criterio Arbitral | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Velocidad (speed), fuerza (force), sobre la espalda (on the back) y control hábil hasta el final del aterrizaje (skilfully controlled until the end of the landing).
5. **Respuesta generada por el asistente (VF01):** **Article 14 Ippon (Art. Article 14, Pág. 166) [SOR-2026-08-P166-S187](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=166):** No score or penalty will be given if the landing of uke occurs on the body of tori, in such a way that not all parts of uke’s body involving the bridge situation (head, foot or feet) touch the tatami. Disposiciones complementarias aplicables en Art. Article 15 (Pág. 168), Art. Article 13 (Pág. 164).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto (en respuesta generada)`
8. **Evidencia normativa (Artículos):** Art. 14 Ippon (p. 166)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 166 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Deben cumplirse los 4 elementos copulativamente durante toda la acción. _Discrepancia técnica:_ El pasaje ensamblado contiene los 4 criterios en p. 166, pero el estructurador determinista tomó la frase de excepción de puente de la p. 167. La norma oficial está 100% verificada en p. 166.

---

### [VF01-04] TC-04 — Tori proyecta a Uke aplicando una técnica con fuerza y velocidad, pero Uke cae sobre un costado con el cuerpo perpendicular al tatami. ¿Qué puntuación corresponde?

1. **Identificador original / VF01:** `TC-04` / `VF01-04` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** Tori proyecta a Uke aplicando una técnica con fuerza y velocidad, pero Uke cae sobre un costado con el cuerpo perpendicular al tatami. ¿Qué puntuación corresponde?
3. **Tipo de consulta:** Escenario Arbitral / Puntuación | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Waza-ari (caída sobre el costado / impacto a más de 90° con respecto a la espalda sin cumplir los criterios de Ippon).
5. **Respuesta generada por el asistente (VF01):** **8.7 Field of Play and Competition Area (Art. 8.7, Pág. 96) [SOR-2026-08-P096-S114](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=96):** The contest area for IJF events shall be a minimum of 8 m x 8 m and a maximum of 10 m x 10 m. Disposiciones complementarias aplicables en Art. Article 14 (Pág. 167), Art. B1.8 (Pág. 112).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto`
8. **Evidencia normativa (Artículos):** Art. 15 Waza-ari (p. 168-169)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 168, 169 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE (en SOR, falló recuperación)`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Si el eje de hombros supera 90° con respecto al tatami pero no es sobre la espalda, es Waza-ari. _Discrepancia técnica:_ RRE recuperó Art. 8.7 (p. 96) por dispersión léxica de 'costado/tatami'. La verdad de base en SOR 2026 p. 168 establece taxativamente Waza-ari.

---

### [VF01-05] TC-05 — Durante ne-waza, Tori inmoviliza a Uke con osaekomi. Al llegar al segundo 16 Uke logra escapar con toketa. ¿Qué puntuación recibe Tori?

1. **Identificador original / VF01:** `TC-05` / `VF01-05` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** Durante ne-waza, Tori inmoviliza a Uke con osaekomi. Al llegar al segundo 16 Uke logra escapar con toketa. ¿Qué puntuación recibe Tori?
3. **Tipo de consulta:** Escenario Arbitral / Tiempos | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Waza-ari (inmovilización mantenida entre 10 y 19 segundos).
5. **Respuesta generada por el asistente (VF01):** **Article 17 Osaekomi-waza (Art. Article 17, Pág. 174) [SOR-2026-08-P174-S190](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=174):** The referee must call “Toketa!” if there is an immediate continuation from either tori or uke in applying osaekomi-waza, shime-waza or kansetsu-waza, and, if the case, assign the relevant osaekomi score, leaving this last action to continue. Disposiciones complementarias aplicables en Art. Article 14 (Pág. 167), Art. Article 15 (Pág. 169).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** Art. 15 Waza-ari (p. 169) y Art. 17 Osaekomi-waza (p. 173-174)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 169, 174 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `INSUFICIENTE_PARCIAL (en Top-1)`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** 10 a 19s = Waza-ari; 20s = Ippon. En 2026, 5 a 9s = Yuko. _Discrepancia técnica:_ RRE recuperó Art. 17 p. 174 (procedimiento de Toketa), pero la escala de tiempos/puntuación reside en Art. 15 p. 169. Requiere síntesis multievidencia.

---

### [VF01-06] TC-06 — ¿Se permite aplicar la técnica de seoi-nage inverso en categoría Cadetes?

1. **Identificador original / VF01:** `TC-06` / `VF01-06` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Se permite aplicar la técnica de seoi-nage inverso en categoría Cadetes?
3. **Tipo de consulta:** Restricción Etaria / Técnica Prohibida | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** No está permitido en cadetes (ni infantiles). Se sanciona con Shido y no se otorga ninguna puntuación.
5. **Respuesta generada por el asistente (VF01):** **Article 18.1.4 Penalties (Shido) in Cadet Competitions (Art. Article 18.1.4, Pág. 189) [SOR-2026-08-P189-S196](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=189):** [PAGE BREAK: P188 -> P189 | KUN: SOR-2026-08-P188-S196 -> SOR-2026-08-P189-S196] --- Pictures 18 .61-18 .67 35. In cadet events there will be no score for reverse seoi-nage and TORI will be penalised with shido. Disposiciones complementarias aplicables en Art. G1.2.1 (Pág. 250), Art. 4.4 (Pág. 65).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Correcto normativamente`
8. **Evidencia normativa (Artículos):** Art. 18.1.4 (p. 189)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 189 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Permitido exclusivamente en categorías Junior y Senior. _Discrepancia técnica:_ Total concordancia entre SOR 2026 p. 189, la recuperación y el veredicto del asistente.

---

### [VF01-07] TC-07 - ¿Se permite a Tori utilizar la cabeza para proyectar al oponente en categorías Cadete y Senior? — ✅ **CONFORME_NORMATIVO**

1. **Identificador original / VF01:** `TC-07` / `VF01-07` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Se permite a Tori utilizar la cabeza para proyectar al oponente en categorías Cadete y Senior?
3. **Tipo de consulta:** Seguridad Arbitral / Head Diving | **SEC-CRIT:** `Sí`
4. **Respuesta esperada (Gold Standard):** En Senior: prohibido tirarse de cabeza (Head Diving) con sanción de Hansoku-make directo (Art. 18.2.1). En Cadetes: cualquier uso voluntario de cabeza para lanzar o apoyar en ataque se sanciona con Shido o Hansoku-make según la gravedad (Art. 18.1.4). El uso de la cabeza para defenderse es válido en Senior y Junior, y restringido con Shido en Cadetes.
5. **Respuesta generada por el asistente (Actualizada y Verificada):** **Article 18.1.4 Penalties (Shido) in Cadet Competitions (Art. Article 18.1.4, Pág. 188) [SOR-2026-08-P188-S196]:** Zambullirse de cabeza (Head Diving) para proyectar está prohibido y se sanciona con descalificación (Hansoku-make) en todas las categorías (Art. 18.2.1, pág. 190; puede continuar). En categoría Cadetes, el uso o apoyo voluntario de la cabeza para proyectar sin zambullida también está restringido y se sanciona con Shido (Art. 18.1.4, pág. 188). Asimismo, el uso de la cabeza para defenderse es válido en Senior y Junior, mientras que en Cadetes está restringido y se sanciona con Shido.
6. **Resultado técnico:** `SUCCESS / PASS` (0.785s)
7. **Resolución de Autoridad Arbitral (Alexis Oliveros Lozano):** `CONFORME_NORMATIVO` (07/11/2026)
8. **Evidencia normativa (Artículos):** Art. 18.1.4 (p. 188) y Art. 18.2.1 (p. 190)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 188, 190 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE_COMPLETO`
11. **Estado de validación normativa:** `CONFORME_NORMATIVO`
12. **Observaciones, condiciones y dictamen arbitral:** Dictamen ratificado por Alexis Oliveros: *"el uso de la cabeza para defenderse es válido en Senior y Junior, en Cadetes está restringido y se sanciona con shido, el zambullirse se sanciona con descalificación 'Hansokumake' para todas las categorías"*. El motor RRE y el estructurador fueron alineados a este criterio y verificados con pruebas sin regresión.

### [VF01-08] TC-08 — ¿Está permitida la defensa con la cabeza apoyándola en el tatami en categoría Cadetes y qué sanción aplica?

1. **Identificador original / VF01:** `TC-08` / `VF01-08` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Está permitida la defensa con la cabeza apoyándola en el tatami en categoría Cadetes y qué sanción aplica?
3. **Tipo de consulta:** Seguridad Arbitral / Restricción Cadetes | **SEC-CRIT:** `SÍ`
4. **Respuesta esperada (Gold Standard):** Está prohibida en cadetes. Uke recibe sanción de Shido por usar la cabeza para defenderse, y si la acción produce caída puntuable de Tori, la puntuación se otorga.
5. **Respuesta generada por el asistente (VF01):** **Article 18.1.4 Penalties (Shido) in Cadet Competitions (Art. Article 18.1.4, Pág. 188) [SOR-2026-08-P188-S196](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=188):** In cadet events athletes are not allowed to use the head to defend as UKE. Disposiciones complementarias aplicables en Art. 8.7 (Pág. 96), Art. 8.9 (Pág. 97).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** Art. 18.1.4 (p. 188)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 188 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Aplica a cadetes e infantiles. En seniors la defensa con cabeza apoyada no siempre se penaliza salvo riesgo cervical. _Discrepancia técnica:_ La regla está en p. 188, pero el resumen del asistente omitió la mención expresa de Shido a Uke.

---

### [VF01-09] TC-09 - ¿Qué sanción se aplica por realizar Head Diving y qué consecuencia tiene sobre la continuidad en la competición? — ✅ **CONFORME_NORMATIVO**

1. **Identificador original / VF01:** `TC-09` / `VF01-09` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Qué sanción se aplica por realizar Head Diving y qué consecuencia tiene sobre la continuidad en la competición?
3. **Tipo de consulta:** Seguridad Arbitral / Consecuencia Disciplinaria | **SEC-CRIT:** `SÍ`
4. **Respuesta esperada (Gold Standard):** Sanción: Hansoku-make directo (Art. 18.2.1). Consecuencia de continuidad: al ser una falta técnica peligrosa (dangerous technique), el atleta PUEDE continuar en las siguientes rondas/repetchage (a diferencia de faltas morales contra el espíritu).
5. **Respuesta generada por el asistente (VF01):** **Article 18.2.1 Hansoku-make for Dangerous Techniques (Art. Article 18.2.1, Pág. 190) [SOR-2026-08-P190-S197](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=190):** Techniques using head diving are dangerous and will be penalised with hansoku-make. Disposiciones complementarias aplicables en Art. Article 21 (Pág. 199), Art. Article 20.2 (Pág. 197).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** Art. 18.2.1 (p. 190) y Art. 18.2.2 (p. 190-193)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 190 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `INSUFICIENTE_PARCIAL`
11. **Estado de validación normativa:** `PENDIENTE_REVISION_HUMANA`
12. **Observaciones, condiciones y discrepancias:** Art. 18.2.1 especifica: 'can bring the athlete to next contest' vs Art. 18.2.2: 'cannot continue'. _Discrepancia técnica:_ El asistente dictaminó Hansoku-make pero omitió responder si puede o no continuar compitiendo.

---

### [VF01-10] TC-10 — ¿Qué sucede si un competidor comete una acción contraria al espíritu del judo como insultar o agredir a su rival?

1. **Identificador original / VF01:** `TC-10` / `VF01-10` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Qué sucede si un competidor comete una acción contraria al espíritu del judo como insultar o agredir a su rival?
3. **Tipo de consulta:** Ética / Disciplina | **SEC-CRIT:** `SÍ`
4. **Respuesta esperada (Gold Standard):** Hansoku-make directo de carácter ético (Art. 18.2.2 p. 193 / D1.1 p. 134). El competidor queda expulsado del torneo y NO puede continuar compitiendo.
5. **Respuesta generada por el asistente (VF01):** **D1.1 Refereeing - Culture, History and Principles (Art. D1.1, Pág. 134) [SOR-2026-08-P134-S173](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=134):** Jigoro Kano at the end of the 19th century developed a school of jujutsu, that he called “JUDO”, different from the other “Ryu” by its target. Disposiciones complementarias aplicables en Art. Article 18.2.2 (Pág. 193), Art. 7.2 (Pág. 89).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto`
8. **Evidencia normativa (Artículos):** D1.1 (p. 134) y Art. 18.2.2 (p. 193)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 134, 193 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** La exclusión es total; se pierde derecho a medalla y puntos de ranking. _Discrepancia técnica:_ RRE recuperó D1.1 pero el selector determinista extrajo una frase de antecedentes históricos de Jigoro Kano en lugar de la sanción disciplinaria.

---

### [VF01-11] TC-11 — ¿Qué sanción corresponde por aplicar kawazu-gake durante un combate?

1. **Identificador original / VF01:** `TC-11` / `VF01-11` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Qué sanción corresponde por aplicar kawazu-gake durante un combate?
3. **Tipo de consulta:** Técnica Prohibida Peligrosa / Sanción | **SEC-CRIT:** `SÍ`
4. **Respuesta esperada (Gold Standard):** Hansoku-make directo por técnica prohibida peligrosa / actos contra el espíritu del judo (Art. 18.2.2 punto 1, p. 190). El atleta descalificado por este motivo NO puede continuar en la competición.
5. **Respuesta generada por el asistente (VF01):** **Article 4 Gestures (Art. Article 4, Pág. 149) [SOR-2026-08-P149-S177](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=149):** point with the forefinger at the athlete to be penalised. Disposiciones complementarias aplicables en Art. Article 13 (Pág. 163), Art. Article 9 (Pág. 154).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto`
8. **Evidencia normativa (Artículos):** Art. 18.2.2 punto 1 (p. 190)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 190 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE (en SOR, falló recuperación)`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Kawazu-gake está taxativamente prohibida bajo Art. 18.2.2 punto 1 (pág. 190). Se penaliza con Hansoku-make directo sin derecho a continuar en la competición. _Discrepancia técnica:_ La respuesta histórica generada en VF01 devolvió de forma errónea Art. 4 Gestures (pág. 149), debido a que el motor RRE no reconoció el término japonés kawazu-gake. El pasaje canónico candidato está perfectamente identificado en Art. 18.2.2 p. 190, pero no cuenta aún con registro de segunda revisión humana formal.

---

### [VF01-12] TC-12 — ¿Es válido puntuar una proyección que se inicia dentro del tatami pero culmina fuera del área de combate en la zona de seguridad?

1. **Identificador original / VF01:** `TC-12` / `VF01-12` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Es válido puntuar una proyección que se inicia dentro del tatami pero culmina fuera del área de combate en la zona de seguridad?
3. **Tipo de consulta:** Límites del Tatami / Validez de Acción | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Sí, es válida para puntuación siempre que la acción técnica se haya iniciado de forma continua dentro del área de combate y culmine hasta 2 metros en el área de seguridad sin interrupción.
5. **Respuesta generada por el asistente (VF01):** **8.7 Field of Play and Competition Area (Art. 8.7, Pág. 96) [SOR-2026-08-P096-S114](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=96):** The contest area for IJF events shall be a minimum of 8 m x 8 m and a maximum of 10 m x 10 m. Disposiciones complementarias aplicables en Art. 8.8 (Pág. 97), Art. 8.5 (Pág. 95).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto`
8. **Evidencia normativa (Artículos):** Art. 5 Location (p. 151)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 151 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE (en SOR, falló recuperación)`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Excepción (d): la técnica debe tener continuidad inmediata sin parada intermedia. _Discrepancia técnica:_ RRE devolvió Art. 8.7 p. 96 (medidas del tatami) en vez de Art. 5 Exceptions p. 151.

---

### [VF01-13] TC-13 — ¿Está permitido vestir un judogi reversible de doble cara blanco y azul en competiciones del IJF World Judo Tour?

1. **Identificador original / VF01:** `TC-13` / `VF01-13` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Está permitido vestir un judogi reversible de doble cara blanco y azul en competiciones del IJF World Judo Tour?
3. **Tipo de consulta:** Equipamiento / Judogi | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** No está permitido. Los judogis reversibles están estrictamente prohibidos en el World Judo Tour (Apéndice C1.1 p. 115); los atletas deben llevar judogis separados blanco y azul oficiales.
5. **Respuesta generada por el asistente (VF01):** **C1.1.2 Judogi and Backnumber Pre-Control (Art. C1.1.2, Pág. 115) [SOR-2026-08-P115-S151](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=115):** C1 .1 .2 .2 Backnumber Pre-Control For the backnumber pre-control, athletes must bring both judogi (white and blue), for a control regarding any worn-out areas particularly on the collar and lapel, the colour, the IJF official label (obligatory), judogi brand (obligatory), national emblem, advertising, backnumber stitching, and any visible stains. Disposiciones complementarias aplicables en Art. 1.1 (Pág. 13), Art. C1.13 (Pág. 127).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** Apéndice C1.1 (p. 115)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 115 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Obligatoriedad de sello óptico IJF y homologación oficial individual. _Discrepancia técnica:_ RRE recuperó C1.1.2 p. 115, pero el fallback determinista extrajo una frase sobre precontrol en vez de la prohibición expresa del reversible.

---

### [VF01-14] TC-14 - ¿Qué ocurre si un judoka realiza una acción con la cabeza durante el combate? — ✅ **CONFORME_NORMATIVO**

1. **Identificador original / VF01:** `TC-14` / `VF01-14` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Qué pasa si un judoka usa la cabeza?
3. **Tipo de consulta:** Consulta Ambigua / Escenarios Múltiples | **SEC-CRIT:** `SÍ`
4. **Respuesta esperada (Gold Standard):** Dictamen arbitral ratificado por Alexis Oliveros (07/11/2026): La acción de la cabeza (intervenir directamente apoyando la cabeza como acción defensiva o como ayuda para lanzar) es válida en Junior y Senior si Uke la usa sin comprometer la seguridad de sus vértebras cervicales. En Cadetes y categorías menores se sanciona con Shido (Art. 18.1.4 pág. 188). Si usan la cabeza pero al caer lo hacen en una posición que puede dar lugar a puntuación para Tori (Yuko, Waza-ari o Ippon), se otorga la puntuación. En caso de zambullida (Head Diving) se descalifica al competidor con Hansoku-make directo en cualquier categoría y puede seguir compitiendo si así está programado (Art. 18.2.1 pág. 190).
5. **Respuesta generada por el asistente (VF01):** **Article 18.2.2 Hansoku-make for Acts against the Spirit of Judo (Art. Article 18.2.2, Pág. 190) [SOR-2026-08-P190-S198](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=190):** a) To make any action this may endanger or injure the opponent especially the opponent’s neck or spinal vertebrae. b) Applying kata-sankaku grip in tachi-waza with a throwing action, with or without “Mate!”, with a higher risk of injury of opponent’s neck or spinal vertebrae, will be considered hansoku-make. Disposiciones complementarias aplicables en Art. Article 15 (Pág. 171), Art. Article 4 (Pág. 142).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** Dictamen ratificado Alexis Oliveros (07/11/2026)
8. **Evidencia normativa (Artículos):** Art. 18.2.1 (p. 190) y Art. 18.1.4 (p. 188)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 188, 190 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE_COMPLETO`
11. **Estado de validación normativa:** `CONFORME_NORMATIVO`
12. **Observaciones, condiciones y discrepancias:** Dictamen formalmente ratificado por Alexis Oliveros (07/11/2026). Aclara la interacción armónica del SOR: cuando Uke usa la cabeza sin comprometer vértebras cervicales, en Junior/Senior es permitido y en Cadetes/menores es Shido; si al caer quedan en posición puntuable para Tori (Yuko, Waza-ari o Ippon), se otorga la puntuación; zambullida (Head Diving) es Hansoku-make en toda categoría con continuidad competitiva si está programado.

---

### [VF01-15] TC-15 — ¿Cuándo se marca mate?

1. **Identificador original / VF01:** `TC-15` / `VF01-15` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cuándo se marca mate?
3. **Tipo de consulta:** Comando Arbitral / Detención de Combate | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** El árbitro anunciará Mate! para detener temporalmente el combate en los casos taxativos del Art. 11: salida del tatami, inacción en suelo sin progresión, falta cometida, lesión, reajuste de judogi o situación de peligro.
5. **Respuesta generada por el asistente (VF01):** **C1.3 Location of the Manufacturer’s Logo (Art. C1.3, Pág. 119) [SOR-2026-08-P119-S158](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=119):** Only one manufacturer’s logo per clothing item is allowed (jacket, trousers, and belt). Disposiciones complementarias aplicables en Art. C1.4 (Pág. 120), Art. C1.7 (Pág. 122).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto`
8. **Evidencia normativa (Artículos):** Art. 11 Mate (p. 160-161)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 160, 161 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE (en SOR, falló recuperación)`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Casos taxativos del artículo 11. _Discrepancia técnica:_ RRE devolvió C1.3 p. 119 por colisión léxica de 'mate' con 'material del judogi'. La verdad canónica reside en Art. 11 pp. 160-161.

---

### [VF01-16] TC-16 — ¿Cuál es la sanción por una falta personal y tiro libre en básquetbol?

1. **Identificador original / VF01:** `TC-16` / `VF01-16` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cuál es la sanción por una falta personal y tiro libre en básquetbol?
3. **Tipo de consulta:** Fuera de Dominio (OOD) | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** ABSTAIN (Materia ajena a las Reglas Oficiales de Judo de la IJF).
5. **Respuesta generada por el asistente (VF01):** ⚠️ **Abstención Normativa Oficial (14 August 2026 (Official))**

La situación o consulta planteada no encuentra respaldo ni evidencia suficiente en los artículos certificados del reglamento deportivo y de organización de la IJF (SOR 2026-08).

*Por razones de rigor técnico y arbitral, el asistente no formula suposiciones no documentadas.*
6. **Resultado técnico original:** `ABSTAIN / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Abstención correcta`
8. **Evidencia normativa (Artículos):** Ninguno (Fuera de Dominio)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. N/A (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE (para abstención)`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Debe abstenerse sin intentar responder normas de baloncesto. _Discrepancia técnica:_ Total concordancia: el motor RRE devolvió `status: ABSTAIN` limpiamente.

---

### [VF01-17] TC-17 — ¿Cómo se calcula la tasa de interés compuesto anual en finanzas?

1. **Identificador original / VF01:** `TC-17` / `VF01-17` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cómo se calcula la tasa de interés compuesto anual en finanzas?
3. **Tipo de consulta:** Fuera de Dominio (OOD) | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** ABSTAIN (Materia ajena a las Reglas Oficiales de Judo de la IJF).
5. **Respuesta generada por el asistente (VF01):** ⚠️ **Abstención Normativa Oficial (14 August 2026 (Official))**

La situación o consulta planteada no encuentra respaldo ni evidencia suficiente en los artículos certificados del reglamento deportivo y de organización de la IJF (SOR 2026-08).

*Por razones de rigor técnico y arbitral, el asistente no formula suposiciones no documentadas.*
6. **Resultado técnico original:** `ABSTAIN / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Abstención correcta`
8. **Evidencia normativa (Artículos):** Ninguno (Fuera de Dominio)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. N/A (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE (para abstención)`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Debe abstenerse sin intentar responder fórmulas financieras. _Discrepancia técnica:_ Total concordancia: el motor RRE devolvió `status: ABSTAIN` limpiamente.

---

### [VF01-18] TC-18 — ¿Si un competidor ofende o agrede a otro que sucede?

1. **Identificador original / VF01:** `TC-18` / `VF01-18` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Si un competidor ofende o agrede a otro que sucede?
3. **Tipo de consulta:** Disciplina / Conducta Antideportiva | **SEC-CRIT:** `SÍ`
4. **Respuesta esperada (Gold Standard):** Descalificación directa con Hansoku-make por falta contra el espíritu del judo (Art. 18.2.2 / D1.1 / SOR Art. 1.1.1). Expulsión inmediata del recinto.
5. **Respuesta generada por el asistente (VF01):** **1.1.1 Behaviour at IJF Events (Art. 1.1.1, Pág. 14) [SOR-2026-08-P014-S003](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=14):** Everyone attending an IJF WJT event should always be mindful of their behaviour, following the judo values. Disposiciones complementarias aplicables en Art. D1.1 (Pág. 134), Art. Article 18.2.2 (Pág. 193).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** SOR Art. 1.1.1 (p. 14) y D1.1 (p. 134)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 14, 134 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Expulsión total y posible apertura de expediente sancionador disciplinario. _Discrepancia técnica:_ RRE recuperó Art. 1.1.1 p. 14 pero la respuesta sintetizada solo describió el principio ético sin formular la sanción de expulsión.

---

### [VF01-19] TC-19 — ¿Cuál es el código de conducta para los entrenadores y qué sanciones aplican si no lo respetan?

1. **Identificador original / VF01:** `TC-19` / `VF01-19` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cuál es el código de conducta para los entrenadores y qué sanciones aplican si no lo respetan?
3. **Tipo de consulta:** Reglamento de Entrenadores / Sanciones | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Código de entrenadores (Art. 7.1 y 7.2 p. 89). No pueden dar instrucciones durante el combate (salvo en Mate), vestir formalmente. Sanciones: advertencia, expulsión a la grada y suspensión para combates posteriores.
5. **Respuesta generada por el asistente (VF01):** **7.1 Coaches’ Code of Conduct (Art. 7.1, Pág. 89) [SOR-2026-08-P089-S104](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=89):** Coaches must respect the Code of Ethics, statutes and regulations of the International Judo Federation (IJF). Disposiciones complementarias aplicables en Art. 1.2.1 (Pág. 14), Art. Article 4 (Pág. 150).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** Art. 7.1 y 7.2 (p. 89)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 89 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Reincidencia conlleva retiro de acreditación oficial. _Discrepancia técnica:_ RRE recuperó Art. 7.1 p. 89 pero omitió el desglose de las sanciones de expulsión de la zona de competición.

---

### [VF01-20] TC-20 — ¿Cuántos shidos provocan la descalificación del competidor?

1. **Identificador original / VF01:** `TC-20` / `VF01-20` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cuántos shidos provocan la descalificación del competidor?
3. **Tipo de consulta:** Factual / Acumulación de Faltas | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Tres (3) Shidos provocan la descalificación del competidor por Hansoku-make indirecto (Art. 18.3.2).
5. **Respuesta generada por el asistente (VF01):** **Article 18 Prohibited Acts and Penalties (Art. Article 18, Pág. 175) [SOR-2026-08-P175-S191](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=175):** The prohibited acts are divided into infringements that receive the penalty of:. Disposiciones complementarias aplicables en Art. Article 18.3.2 (Pág. 194), Art. 2.7.2 (Pág. 46).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** Art. 18 Penalties (p. 175) y Art. 18.3.2
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 175 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** El tercer shido se convierte automáticamente en Hansoku-make. El atleta puede seguir en rondas posteriores. _Discrepancia técnica:_ RRE recuperó Art. 18 p. 175 pero el extracto seleccionado solo describió las categorías de faltas sin enunciar el número tres.

---

### [VF01-21] TC-21 — ¿El puente voluntario para evitar una caída se considera ippon?

1. **Identificador original / VF01:** `TC-21` / `VF01-21` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿El puente voluntario para evitar una caída se considera ippon?
3. **Tipo de consulta:** Seguridad Arbitral / Puente | **SEC-CRIT:** `SÍ`
4. **Respuesta esperada (Gold Standard):** Sí, todas las situaciones en que un competidor hace un puente voluntario (cabeza y pies en contacto con el tatami) tras ser proyectado se consideran Ippon para salvaguardar su columna cervical (Art. 14 p. 166-167).
5. **Respuesta generada por el asistente (VF01):** **Article 14 Ippon (Art. Article 14, Pág. 167) [SOR-2026-08-P167-S187](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=167):** No score or penalty will be given if the landing of uke occurs on the body of tori, in such a way that not all parts of uke’s body involving the bridge situation (head, foot or feet) touch the tatami. Disposiciones complementarias aplicables en Art. Article 14 (Pág. 166), Art. Article 18.1.4 (Pág. 188).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Parcialmente correcto`
8. **Evidencia normativa (Artículos):** Art. 14 Ippon (p. 166-167)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 166, 167 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Excepción: si cae sobre el cuerpo de Tori (Art. 14 p. 167). _Discrepancia técnica:_ El pasaje ensamblado (`SOR-2026-08-P166-P167`) contiene ambas páginas, pero el generador determinista extrajo la excepción de p. 167 en vez de la regla general de Ippon de p. 166.

---

### [VF01-22] TC-22 — ¿Qué se marca si Uke cae en posición de puente pero aterriza sobre el cuerpo de Tori?

1. **Identificador original / VF01:** `TC-22` / `VF01-22` (Batería: `TC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Qué se marca si Uke cae en posición de puente pero aterriza sobre el cuerpo de Tori?
3. **Tipo de consulta:** Seguridad Arbitral / Excepción de Puente | **SEC-CRIT:** `SÍ`
4. **Respuesta esperada (Gold Standard):** No se concede ninguna puntuación (no score) ni penalización, porque no todas las partes del cuerpo involucradas en el puente tocan el tatami (Art. 14 p. 167).
5. **Respuesta generada por el asistente (VF01):** **Article 14 Ippon (Art. Article 14, Pág. 167) [SOR-2026-08-P167-S187](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=167):** No score or penalty will be given if the landing of uke occurs on the body of tori, in such a way that not all parts of uke’s body involving the bridge situation (head, foot or feet) touch the tatami. Disposiciones complementarias aplicables en Art. C1.3 (Pág. 119), Art. C1.4 (Pág. 120).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Correcto normativamente`
8. **Evidencia normativa (Artículos):** Art. 14 Ippon - Excepción (p. 167)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 167 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Condición explícita: el impacto del puente ocurre sobre Tori y no sobre el tatami. _Discrepancia técnica:_ Total concordancia: el motor y el asistente respondieron con la excepción textual exacta de p. 167.

---

### [VF01-23] MC-01 - ¿Está permitido el reverse seoi-nage en competidores seniors? — ✅ **CONFORME_NORMATIVO**

1. **Identificador original / VF01:** `MC-01` / `VF01-23` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Está permitido el reverse seoi-nage en competidores seniors?
3. **Tipo de consulta:** Enmienda Técnica / Técnica Autorizada | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Sí, está permitido en competidores Senior (enmienda oficial IJF 2026 / Circular técnica). En cadetes e infantiles está prohibido.
5. **Respuesta generada por el asistente (VF01):** **4.4 Number of Entries (Art. 4.4, Pág. 64) [SOR-2026-08-P064-S079](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=64):** For IJF events the number of entries allowed for each national federation will be as follows: World Championships Seniors Only athletes ranked number 1-100* in the IJF Seniors WRL, and athletes ranked number 1-16* in the IJF Juniors WRL, can take part with each national federation allowed to enter:. Disposiciones complementarias aplicables en Art. Article 18.1.4 (Pág. 189), Art. Article 5 (Pág. 151).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto`
8. **Evidencia normativa (Artículos):** Circular Enmiendas 2026 (Tier 2 / KUN-NEW-001) / Art. 18 SOR
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. SOR p. 64 recuperada (Cupos WRL) (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `INSUFICIENTE`
11. **Estado de validación normativa:** `PENDIENTE_EVIDENCIA`
12. **Observaciones, condiciones y discrepancias:** En SOR 2026-08 base la técnica solo se menciona como prohibida para cadetes (p. 189). La autorización expresa senior proviene de la Circular 2026_01. _Discrepancia técnica:_ En la configuración Lean actual (sin sidecar activo), el motor RRE primario recuperó p. 64. Requiere la ingesta del Paso 3 (Circulares).

---

### [VF01-24] MC-02 - ¿Cuál es el límite de tiempo para la disputa de kumi-kata sin ataque? — ✅ **CONFORME_NORMATIVO**

1. **Identificador original / VF01:** `MC-02` / `VF01-24` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cuál es el límite de tiempo para la disputa de kumi-kata sin ataque?
3. **Tipo de consulta:** Reglamentario / No Combatividad | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Aproximadamente 45 segundos según la norma general de combatividad (o 30s según circular LA28 en discusión); la falta de ataque tras agarre convencional se sanciona con Shido (Art. 18.1.1).
5. **Respuesta generada por el asistente (VF01):** **Article 4 Gestures (Art. Article 4, Pág. 149) [SOR-2026-08-P149-S177](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=149):** Wasting time: wasting the time between “Mate!” and “Hajime!” by not standing up after ne-waza action, by not returning immediately to starting position, by arranging too long the hair, by arranging too long the judogi, by tying too long the belt, or by a combination of these points. Disposiciones complementarias aplicables en Art. Article 8 (Pág. 153), Art. Article 13 (Pág. 164).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** Art. 18.1.1 (p. 177) vs Circular LA28
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 177 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `INSUFICIENTE_PARCIAL`
11. **Estado de validación normativa:** `DISPUTADO`
12. **Observaciones, condiciones y discrepancias:** El SOR 2026 base no fija un número rígido de segundos en el articulado principal sino un principio de apreciación arbitral inmediata (45s aprox). _Discrepancia técnica:_ RRE devolvió Art. 4 p. 149 sobre pérdida de tiempo genérica. Existe discrepancia entre la circular LA28 y el texto canónico del SOR.

---

### [VF01-25] MC-03 - ¿A partir de qué evento se congelan las reglas para el ciclo olímpico LA28? — ✅ **CONFORME_NORMATIVO** (Abstención Correcta)

1. **Identificador original / VF01:** `MC-03` / `VF01-25` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿A partir de qué evento se congelan las reglas para el ciclo olímpico LA28?
3. **Tipo de consulta:** Administrativo / Calendario IJF | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Grand Slam de Ulaanbaatar (o fecha oficial estipulada en Circular 2026_01).
5. **Respuesta generada por el asistente (VF01):** ⚠️ **Abstención Normativa Oficial (14 August 2026 (Official))**

La situación o consulta planteada no encuentra respaldo ni evidencia suficiente en los artículos certificados del reglamento deportivo y de organización de la IJF (SOR 2026-08).

*Por razones de rigor técnico y arbitral, el asistente no formula suposiciones no documentadas.*
6. **Resultado técnico original:** `ABSTAIN / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `No verificable`
8. **Evidencia normativa (Artículos):** Circular Administrativa LA28 (No en SOR 2026-08 base)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. N/A en SOR base (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `INSUFICIENTE`
11. **Estado de validación normativa:** `SIN_ORACULO`
12. **Observaciones, condiciones y discrepancias:** No existe oráculo en el documento canónico oficial SOR 2026-08 (298 páginas físicas). _Discrepancia técnica:_ El sistema se abstuvo (`status: ABSTAIN`). Sin la circular complementaria, no hay oráculo verificable en la fuente canónica oficial (298 páginas).

---

### [VF01-26] MC-04 — ¿Cómo evalúa el árbitro la continuidad en la transición de tachi-waza a ne-waza?

1. **Identificador original / VF01:** `MC-04` / `VF01-26` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cómo evalúa el árbitro la continuidad en la transición de tachi-waza a ne-waza?
3. **Tipo de consulta:** Criterio Arbitral / Transición | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** El árbitro permite la continuidad sin interrupción si hay acción ofensiva inmediata y control efectivo. Si la acción se detiene sin ataque, debe mandar Mate! (SOR p. 159).
5. **Respuesta generada por el asistente (VF01):** **waza (B) (Art. GENERAL, Pág. 159) [SOR-2026-08-P159-S183](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=159):** Situations that allow the transition from tachi-waza to ne-waza a) When one of the athletes, lands on the ground and there is no score, yuko or waza- ari is given, either athlete can, without interruption, take the offensive and continue in ne-waza. Disposiciones complementarias aplicables en Art. Article 13 (Pág. 165), Art. GENERAL (Pág. 156).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Correcto normativamente`
8. **Evidencia normativa (Artículos):** Transición Tachi/Ne-waza (p. 159)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 159 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** La acción no debe quebrarse; si Uke queda inerte o Tori no progresa, se ordena Mate. _Discrepancia técnica:_ El pasaje de p. 159 contiene exactamente la regla de transición. La etiqueta devuelta fue `GENERAL` pero el contenido normativo es impecable.

---

### [VF01-27] MC-05 — ¿Se sanciona con Shido halar o arrastrar al oponente directamente a ne-waza?

1. **Identificador original / VF01:** `MC-05` / `VF01-27` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Se sanciona con Shido halar o arrastrar al oponente directamente a ne-waza?
3. **Tipo de consulta:** Infracción / Transición Ilícita | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Sí, halar o tirarse al suelo directamente para llevar a ne-waza sin aplicar una técnica válida de judo se sanciona con Shido a quien comete la acción (SOR p. 159).
5. **Respuesta generada por el asistente (VF01):** **waza (B) (Art. GENERAL, Pág. 159) [SOR-2026-08-P159-S183](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=159):** Exceptions When one athlete pulls his opponent down into ne-waza not in accordance with the above rules and his opponent does not take advantage of this to continue into ne-waza, the referee shall announce mate and penalise with shido the athlete who has infringed Article 18. If instead, the opponent takes advantage of the action of tori, the ne-waza work may continue. Disposiciones complementarias aplicables en Art. GENERAL (Pág. 155), Art. Article 18 (Pág. 175).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Correcto normativamente`
8. **Evidencia normativa (Artículos):** Transición Tachi/Ne-waza (p. 159) y Art. 18.1.2
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 159 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Si el rival aprovecha la acción y toma ventaja en suelo, el árbitro puede dejar continuar. _Discrepancia técnica:_ El pasaje de p. 159 contiene la regla textual. Coincidencia plena con la doctrina oficial.

---

### [VF01-28] MC-06 — ¿Cuántos segundos de osaekomi se requieren para obtener puntuación de Yuko?

1. **Identificador original / VF01:** `MC-06` / `VF01-28` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cuántos segundos de osaekomi se requieren para obtener puntuación de Yuko?
3. **Tipo de consulta:** Puntuación 2026 / Tiempos Osaekomi | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Entre 5 y 9 segundos de inmovilización otorgan puntuación de Yuko (Art. 15 p. 169).
5. **Respuesta generada por el asistente (VF01):** **Article 15 Waza-ari and Yuko (Art. Article 15, Pág. 168) [SOR-2026-08-P168-S188](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=168):** [PAGE BREAK: P168 -> P169 | KUN: SOR-2026-08-P168-S188 -> SOR-2026-08-P169-S188] --- Yuko evaluation in ne-waza When an athlete holds the other athlete with osaekomi-waza, after “Osaekomi!” is announced for 5 seconds or more, but less than 10 seconds (5-9 seconds). Disposiciones complementarias aplicables en Art. Article 15 (Pág. 169), Art. Article 13 (Pág. 164).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Correcto normativamente`
8. **Evidencia normativa (Artículos):** Art. 15 Waza-ari / Yuko (p. 169)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 169 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** En SOR 2026: 5-9s = Yuko; 10-19s = Waza-ari; 20s = Ippon. _Discrepancia técnica:_ RRE recuperó Art. 15 ensamblado (p. 168-171) conteniendo taxativamente la escala de Yuko en p. 169.

---

### [VF01-29] MC-07 - ¿Qué sanción aplica si Tori arrastra a Uke al suelo sin iniciar una acción técnica válida? — ✅ **CONFORME_NORMATIVO**

1. **Identificador original / VF01:** `MC-07` / `VF01-29` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cómo se evalúa la no combatividad o pasividad entre judo de pie y suelo?
3. **Tipo de consulta:** Criterio Arbitral / Combatividad | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Se evalúa de forma integrada: la pasividad en pie se penaliza con Shido tras unos 45s sin iniciativa (Art. 18.1.1); en suelo, si no hay ataque positivo continuo, se marca Mate inmediatamente sin penalización salvo demora deliberada.
5. **Respuesta generada por el asistente (VF01):** **Article 18.1.1 Shido for a Lack of Combativity (Art. Article 18.1.1, Pág. 177) [SOR-2026-08-P177-S193](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=177):** Negative positions, against the fighting spirit, will be penalised by shido (to adopt in a standing position, after kumikata, an excessively defensive posture, not searching for an attack, a defensive attitude etc.). Disposiciones complementarias aplicables en Art. Article 4 (Pág. 146), Art. Article 18.1.2 (Pág. 179).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** Art. 18.1.1 (p. 177) y p. 159
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 177 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `INSUFICIENTE_PARCIAL`
11. **Estado de validación normativa:** `PENDIENTE_REVISION_HUMANA`
12. **Observaciones, condiciones y discrepancias:** Requiere comparar dos secciones normativas distintas del SOR. _Discrepancia técnica:_ RRE devolvió solo Art. 18.1.1 (postura no combativa en pie), omitiendo la comparación con ne-waza.

---

### [VF01-30] MC-08 - ¿Se sanciona al atleta que al intentar proyectar apoya involuntariamente la cabeza en el tatami durante un contrataque? — ✅ **CONFORME_NORMATIVO**

1. **Identificador original / VF01:** `MC-08` / `VF01-30` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Existe excepción de Hansoku-make si el contacto de cabeza con tatami es involuntario?
3. **Tipo de consulta:** Seguridad Arbitral / Excepción Involuntariedad | **SEC-CRIT:** `SÍ`
4. **Respuesta esperada (Gold Standard):** Pendiente de ratificación arbitral / fuente exacta. La pág. 190 regula Head Diving (Art. 18.2.1) y actos contra el espíritu/kawazu-gake (Art. 18.2.2), pero NO contiene una excepción textual expresa para aterrizaje accidental de cabeza en contraataque.
5. **Respuesta generada por el asistente (VF01):** **Article 18.2.2 Hansoku-make for Acts against the Spirit of Judo (Art. Article 18.2.2, Pág. 190) [SOR-2026-08-P190-S198](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=190):** a) To make any action this may endanger or injure the opponent especially the opponent’s neck or spinal vertebrae. b) Applying kata-sankaku grip in tachi-waza with a throwing action, with or without “Mate!”, with a higher risk of injury of opponent’s neck or spinal vertebrae, will be considered hansoku-make. Disposiciones complementarias aplicables en Art. 8.7 (Pág. 96), Art. Article 18.2.2 (Pág. 193).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto (en respuesta generada)`
8. **Evidencia normativa (Artículos):** Art. 18.2.1 / Art. 18.2.2 (p. 190) [Sin respaldo textual de excepción accidental]
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 190 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `INSUFICIENTE_SIN_RESPALDO_TEXTUAL`
11. **Estado de validación normativa:** `PENDIENTE_REVISION_HUMANA`
12. **Observaciones, condiciones y discrepancias:** La cita empleada (p. 190) no respalda la excepción de involuntariedad formulada. Requiere que Alexis Oliveros / panel arbitral identifiquen la regla, circular o directriz exacta que gobierna la accidentalidad. _Discrepancia técnica:_ Aprobación normativa revocada conforme al Dictamen Codex. En p. 190 no existe la excepción expresa de involuntariedad; la cita previa era incorrecta para sostener una verdad básica fijada.

---

### [VF01-31] MC-09 — ¿Cuáles son las dimensiones oficiales del tatami y el área de combate?

1. **Identificador original / VF01:** `MC-09` / `VF01-31` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cuáles son las dimensiones oficiales del tatami y el área de combate?
3. **Tipo de consulta:** Factual / Infraestructura | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Área de combate: 8x8m a 10x10m. Área de seguridad: mínimo 3m (4m común entre tatamis contiguos, 50cm de zona libre exterior) (Art. 8.7 p. 96).
5. **Respuesta generada por el asistente (VF01):** **8.7 Field of Play and Competition Area (Art. 8.7, Pág. 96) [SOR-2026-08-P096-S114](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=96):** The contest area for IJF events shall be a minimum of 8 m x 8 m and a maximum of 10 m x 10 m. Disposiciones complementarias aplicables en Art. 8.6 (Pág. 95), Art. Article 9 (Pág. 154).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** Art. 8.7 (p. 96)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 96 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE_PARCIAL`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Similar a TC-01. _Discrepancia técnica:_ RRE devolvió Art. 8.7 p. 96 cubriendo el área de combate, pero omitió el total con seguridad.

---

### [VF01-32] MC-10 — ¿Cuál es la especificación del color del judogi azul en código Pantone?

1. **Identificador original / VF01:** `MC-10` / `VF01-32` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cuál es la especificación del color del judogi azul en código Pantone?
3. **Tipo de consulta:** Factual / Equipamiento | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Pantone 18-4051 TCX (o rango homologado entre 18-4051 y 18-4055 TCX según Apéndice C1.9 p. 124).
5. **Respuesta generada por el asistente (VF01):** **C1.9 Judogi Colour (Art. C1.9, Pág. 124) [SOR-2026-08-P124-S164](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=124):** The jacket and the trousers should be of a uniform colour and correspond to the following colour references: • White: Snow white reference. • Blue: between Pantone number n°18- 4051TCX(TPX) and n°18-4039TCX(TPX) on the textile Pantone scale and between n°285M and n° 286M on the print Pantone scale. Disposiciones complementarias aplicables en Art. C1.1 (Pág. 115), Art. C1.12 (Pág. 126).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Correcto normativamente`
8. **Evidencia normativa (Artículos):** Apéndice C1.9 (p. 124)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 124 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Tolerancia estricta de coloración verificada en control de judogi. _Discrepancia técnica:_ Total concordancia: RRE y ADA recuperaron y citaron exactamente el código Pantone de p. 124.

---

### [VF01-33] MC-11 — ¿Cuáles son las categorías de peso en judo senior masculino y femenino?

1. **Identificador original / VF01:** `MC-11` / `VF01-33` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cuáles son las categorías de peso en judo senior masculino y femenino?
3. **Tipo de consulta:** Factual / Categorías de Competición | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Masculino: -60, -66, -73, -81, -90, -100, +100 kg. Femenino: -48, -52, -57, -63, -70, -78, +78 kg (SOR Art. 3).
5. **Respuesta generada por el asistente (VF01):** **6.3 Random Weigh-in (Art. 6.3, Pág. 79) [SOR-2026-08-P079-S093](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=79):** For IJF World Judo Tour (WJT) events the random weigh-in will open one hour before the start of the competition each day. Disposiciones complementarias aplicables en Art. 6.5 (Pág. 86), Art. 6.2.3 (Pág. 77).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto`
8. **Evidencia normativa (Artículos):** SOR Art. 3 Weight Categories (p. 42 / Apéndice)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 42 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE (en SOR, falló recuperación)`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** 7 categorías de peso olímpicas para cada género. _Discrepancia técnica:_ RRE devolvió Art. 6.3 p. 79 sobre el pesaje aleatorio (random weigh-in) en vez de la tabla de categorías de peso de Art. 3.

---

### [VF01-34] MC-12 — ¿Qué condiciones determinan el fin del combate por acumulación de tres Shidos?

1. **Identificador original / VF01:** `MC-12` / `VF01-34` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Qué condiciones determinan el fin del combate por acumulación de tres Shidos?
3. **Tipo de consulta:** Reglamentario / Penalizaciones | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** La concesión del tercer Shido a un mismo competidor produce su descalificación automática por Hansoku-make indirecto y otorga la victoria por Ippon al oponente (Art. 18.3.2).
5. **Respuesta generada por el asistente (VF01):** **Article 18.1 Shido (Slight Infringements Group) (Art. Article 18.1, Pág. 176) [SOR-2026-08-P176-S192](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=176):** During the contest an athlete can receive a shido for a lack of combativity, an illegal move or action that is not considered dangerous, untidy attire or hair. Disposiciones complementarias aplicables en Art. F1.3.5 (Pág. 212), Art. F1.3.6 (Pág. 213).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** Art. 18.1 (p. 176) y Art. 18.3.2
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 176 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE_PARCIAL`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Los shidos no dan puntuación al oponente, pero el tercero otorga fin del combate. _Discrepancia técnica:_ RRE devolvió Art. 18.1 p. 176 pero el resumen no formuló expresamente el tercer shido.

---

### [VF01-35] MC-13 — ¿Cuántos tiempos fuera puede pedir el entrenador en un partido de baloncesto?

1. **Identificador original / VF01:** `MC-13` / `VF01-35` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cuántos tiempos fuera puede pedir el entrenador en un partido de baloncesto?
3. **Tipo de consulta:** Fuera de Dominio (OOD) | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** ABSTAIN (Materia ajena a las Reglas Oficiales de Judo de la IJF).
5. **Respuesta generada por el asistente (VF01):** **7.2 Coaches’ Dress Code (Art. 7.2, Pág. 89) [SOR-2026-08-P089-S105](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=89):** Coaches must respect the following dress code:. Disposiciones complementarias aplicables en Art. F1.3.1 (Pág. 208), Art. F1.3.29 (Pág. 236).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto (Falso PASS)`
8. **Evidencia normativa (Artículos):** Ninguno (Fuera de Dominio)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. N/A (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE (para abstención)`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Debe abstenerse sin importar que contenga la palabra 'entrenador'. _Discrepancia técnica:_ El sistema falló en abstenerse: devolvió Art. 7.2 p. 89 (vestimenta de entrenadores de judo). Caso bandera de corrección OOD P1.

---

### [VF01-36] MC-14 — En natación, ¿cuál es la penalización por salida en falso en 100m libre?

1. **Identificador original / VF01:** `MC-14` / `VF01-36` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** En natación, ¿cuál es la penalización por salida en falso en 100m libre?
3. **Tipo de consulta:** Fuera de Dominio (OOD) | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** ABSTAIN (Materia ajena a las Reglas Oficiales de Judo de la IJF).
5. **Respuesta generada por el asistente (VF01):** ⚠️ **Abstención Normativa Oficial (14 August 2026 (Official))**

La situación o consulta planteada no encuentra respaldo ni evidencia suficiente en los artículos certificados del reglamento deportivo y de organización de la IJF (SOR 2026-08).

*Por razones de rigor técnico y arbitral, el asistente no formula suposiciones no documentadas.*
6. **Resultado técnico original:** `ABSTAIN / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Abstención correcta`
8. **Evidencia normativa (Artículos):** Ninguno (Fuera de Dominio)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. N/A (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE (para abstención)`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Abstención requerida. _Discrepancia técnica:_ Total concordancia: el motor RRE devolvió `status: ABSTAIN` limpiamente.

---

### [VF01-37] MC-15 — ¿Cómo se puntúa un gol de campo en el fútbol americano de la NFL?

1. **Identificador original / VF01:** `MC-15` / `VF01-37` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cómo se puntúa un gol de campo en el fútbol americano de la NFL?
3. **Tipo de consulta:** Fuera de Dominio (OOD) | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** ABSTAIN (Materia ajena a las Reglas Oficiales de Judo de la IJF).
5. **Respuesta generada por el asistente (VF01):** ⚠️ **Abstención Normativa Oficial (14 August 2026 (Official))**

La situación o consulta planteada no encuentra respaldo ni evidencia suficiente en los artículos certificados del reglamento deportivo y de organización de la IJF (SOR 2026-08).

*Por razones de rigor técnico y arbitral, el asistente no formula suposiciones no documentadas.*
6. **Resultado técnico original:** `ABSTAIN / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Abstención correcta`
8. **Evidencia normativa (Artículos):** Ninguno (Fuera de Dominio)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. N/A (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE (para abstención)`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Abstención requerida. _Discrepancia técnica:_ Total concordancia: el motor RRE devolvió `status: ABSTAIN` limpiamente.

---

### [VF01-38] MC-16 — ¿Cuál es la penalización para un cadete que realiza reverse seoi-nage?

1. **Identificador original / VF01:** `MC-16` / `VF01-38` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Cuál es la penalización para un cadete que realiza reverse seoi-nage?
3. **Tipo de consulta:** Restricción Etaria / Sanción | **SEC-CRIT:** `SÍ`
4. **Respuesta esperada (Gold Standard):** Sanción de Shido para el competidor cadete y anulación de cualquier puntuación obtenida (Art. 18.1.4 p. 189).
5. **Respuesta generada por el asistente (VF01):** **Article 18.1.4 Penalties (Shido) in Cadet Competitions (Art. Article 18.1.4, Pág. 189) [SOR-2026-08-P189-S196](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=189):** [PAGE BREAK: P188 -> P189 | KUN: SOR-2026-08-P188-S196 -> SOR-2026-08-P189-S196] --- Pictures 18 .61-18 .67 35. In cadet events there will be no score for reverse seoi-nage and TORI will be penalised with shido. Disposiciones complementarias aplicables en Art. G1.2.1 (Pág. 250), Art. Article 5 (Pág. 151).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Correcto normativamente`
8. **Evidencia normativa (Artículos):** Art. 18.1.4 (p. 189)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 189 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Aplica en categorías sub-18 y sub-15. _Discrepancia técnica:_ Total concordancia: recuperado en bloque ensamblado `SOR-2026-08-P188-P189` con dictamen correcto.

---

### [VF01-39] MC-17 — ¿Qué diferencia existe entre un Waza-ari de 10 segundos y un Yuko de 5 segundos?

1. **Identificador original / VF01:** `MC-17` / `VF01-39` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Qué diferencia existe entre un Waza-ari de 10 segundos y un Yuko de 5 segundos?
3. **Tipo de consulta:** Puntuaciones / Diferenciación | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Yuko se obtiene con 5 a 9 segundos y no se acumula para Ippon; Waza-ari se obtiene con 10 a 19 segundos y la acumulación de dos Waza-ari otorga Waza-ari-awasete-ippon (victoria total) (Art. 15 pp. 168-169).
5. **Respuesta generada por el asistente (VF01):** **Article 15 Waza-ari and Yuko (Art. Article 15, Pág. 169) [SOR-2026-08-P169-S188](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=169):** Yuko scores are counted (1, 2, 3, etc.) but they do not add up to waza-ari. Disposiciones complementarias aplicables en Art. Article 15 (Pág. 168), Art. Article 16 (Pág. 172).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** Art. 15 (p. 168-169)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 168, 169 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE_PARCIAL`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Diferencia de jerarquía técnica y efecto acumulativo en el marcador. _Discrepancia técnica:_ RRE recuperó p. 169 pero la respuesta solo declaró que los Yukos no se acumulan, omitiendo comparar con Waza-ari.

---

### [VF01-40] MC-18 — ¿Puede el árbitro dar Mate si un atleta ataca continuamente en el suelo?

1. **Identificador original / VF01:** `MC-18` / `VF01-40` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** ¿Puede el árbitro dar Mate si un atleta ataca continuamente en el suelo?
3. **Tipo de consulta:** Comando Arbitral / Continuidad Ne-waza | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** No. Si un competidor ataca activamente y muestra progresión continua en ne-waza, el árbitro no debe dar Mate y debe permitir la continuación del combate (Art. 11 y p. 159).
5. **Respuesta generada por el asistente (VF01):** **Article 13 End of the Contest (Art. Article 13, Pág. 165) [SOR-2026-08-P165-S186](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=165):** Special situations during golden score. a) Should only one athlete exercise his right to participate in the “golden score” period, and the other athlete declines, the athlete who wishes to compete shall be declared the winner by “kiken-gachi”. Disposiciones complementarias aplicables en Art. Article 2 (Pág. 136), Art. Article 4 (Pág. 137).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto`
8. **Evidencia normativa (Artículos):** Art. 11 Mate (p. 160) y p. 159
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 159, 160 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Solo se ordena Mate cuando la acción en suelo queda completamente bloqueada sin avance. _Discrepancia técnica:_ RRE devolvió Art. 13 p. 165 sobre Golden Score y Kiken-gachi en vez de la regla de no interrupción en ne-waza.

---

### [VF01-41] MC-19 — What are the rules regarding gripping time and attacking rhythm?

1. **Identificador original / VF01:** `MC-19` / `VF01-41` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** What are the rules regarding gripping time and attacking rhythm?
3. **Tipo de consulta:** Bilingüe / Kumi-kata | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Athletes must show positive gripping and attack within a reasonable timeframe (conventionally ~45s for standard grips, immediately for non-standard grips). Failure to attack results in Shido for non-combativity (Art. 18.1.1).
5. **Respuesta generada por el asistente (VF01):** **Article 8 Technique Coinciding with the Time Signal (Art. Article 8, Pág. 153) [SOR-2026-08-P153-S181](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=153):** Although a throwing technique may be applied simultaneously with the time signal, if the referee or the IJF Head Referee Director(s) and/or the IJF Referee Supervisor(s) decide that it will not be effective immediately, the referee shall announce Sore-made!, without any value for scoring purposes. Disposiciones complementarias aplicables en Art. Article 14 (Pág. 166), Art. Article 18.1.2 (Pág. 179).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto`
8. **Evidencia normativa (Artículos):** Art. 18.1.1 Gripping and Non-Combativity (p. 177)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 177 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE (en SOR, falló recuperación)`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Cross-grip, belt grip or one-sided grip require immediate attack. _Discrepancia técnica:_ RRE devolvió Art. 8 p. 153 sobre técnicas al límite de tiempo en vez de las reglas de agarre de Art. 18.1.1.

---

### [VF01-42] MC-20 - Is a judoka penalised if they accidentally touch the tatami with their head while counter-attacking? — ✅ **CONFORME_NORMATIVO**

1. **Identificador original / VF01:** `MC-20` / `VF01-42` (Batería: `MC_HISTORIC`)
2. **Pregunta / Consulta:** If an athlete lands accidentally on the head during a counter throw, is it hansoku-make?
3. **Tipo de consulta:** Bilingüe / Seguridad Arbitral / Excepción | **SEC-CRIT:** `SÍ`
4. **Respuesta esperada (Gold Standard):** Pending referee ratification / exact source. Page 190 defines head diving as a dangerous technique (Art. 18.2.1) and lists acts against the spirit (Art. 18.2.2), but does NOT express an accidental landing exception during counter throws.
5. **Respuesta generada por el asistente (VF01):** **Article 18.2.2 Hansoku-make for Acts against the Spirit of Judo (Art. Article 18.2.2, Pág. 190) [SOR-2026-08-P190-S198](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=190):** If this type of hansoku-make is awarded the athlete CANNOT continue in the competition and will remain in the position they reached on the draw sheet (if this in the quarterfinal the position is 7th place). Disposiciones complementarias aplicables en Art. Article 18.1.4 (Pág. 188), Art. Article 18.3 (Pág. 194).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto (en respuesta generada)`
8. **Evidencia normativa (Artículos):** Art. 18.2.1 / Art. 18.2.2 (p. 190) [Sin respaldo textual de excepción accidental]
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 190 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `INSUFICIENTE_SIN_RESPALDO_TEXTUAL`
11. **Estado de validación normativa:** `PENDIENTE_REVISION_HUMANA`
12. **Observaciones, condiciones y discrepancias:** The cited passage (p. 190) does not contain the accidental counter throw exception. Requires formal referee ruling and exact citation from Alexis Oliveros. _Discrepancia técnica:_ Normative approval revoked per Codex audit. The text on p. 190 does not support the stated exception; cannot be certified as approved gold standard without canonical evidence.

---

### [VF01-43] CGPT-01 — ¿Cuáles son las dimensiones del tatami de competición?

1. **Identificador original / VF01:** `CGPT-01` / `VF01-43` (Batería: `CHATGPT_10`)
2. **Pregunta / Consulta:** ¿Cuáles son las dimensiones del tatami de competición?
3. **Tipo de consulta:** Factual / Infraestructura | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Área de combate de 8x8m a 10x10m con área de seguridad de mínimo 3m (4m común entre tatamis contiguos, 50cm de zona libre exterior) (Art. 8.7 p. 96).
5. **Respuesta generada por el asistente (VF01):** **8.7 Field of Play and Competition Area (Art. 8.7, Pág. 96) [SOR-2026-08-P096-S114](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=96):** The contest area for IJF events shall be a minimum of 8 m x 8 m and a maximum of 10 m x 10 m. Disposiciones complementarias aplicables en Art. 8.6 (Pág. 95), Art. GENERAL (Pág. 30).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** Art. 8.7 (p. 96)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 96 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE_PARCIAL`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Medidas de área de combate y seguridad. _Discrepancia técnica:_ Recuperó p. 96 pero omitió detallar la seguridad.

---

### [VF01-44] CGPT-02 — Durante un combate, se aplica osaekomi-waza y la acción continúa desplazándose hasta sobrepasar completamente el área de seguridad. ¿Qué debe señalar el árbitro?

1. **Identificador original / VF01:** `CGPT-02` / `VF01-44` (Batería: `CHATGPT_10`)
2. **Pregunta / Consulta:** Durante un combate, se aplica osaekomi-waza y la acción continúa desplazándose hasta sobrepasar completamente el área de seguridad. ¿Qué debe señalar el árbitro?
3. **Tipo de consulta:** Escenario Arbitral Complejo / Ne-waza fuera de límites | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Si el Osaekomi se inició válidamente dentro y el desplazamiento sobrepasa completamente el área de seguridad, el combate concluye con Ippon! Sore-made! a favor de Tori si se cumplen los 20s o la inmovilización es total (Art. 17 p. 174).
5. **Respuesta generada por el asistente (VF01):** **Article 17 Osaekomi-waza (Art. Article 17, Pág. 174) [SOR-2026-08-P174-S190](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=174):** If the osaekomi-waza action outside the contest area goes beyond the limit of the safety area the referee must call “Ippon! Sore-Made!” Disposiciones complementarias aplicables en Art. Article 17 (Pág. 173), Art. Article 7 (Pág. 152).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Correcto normativamente`
8. **Evidencia normativa (Artículos):** Art. 17 Osaekomi-waza (p. 174)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 174 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** La inmovilización debe haber sido válida antes de abandonar el tatami. _Discrepancia técnica:_ Total concordancia: recuperado en bloque continuo `SOR-2026-08-P173-P174` con cita de p. 174.

---

### [VF01-45] CGPT-03 — En un combate de cadetes (17 años), Tori intenta una proyección y en la acción apoya la cabeza en el tatami de forma voluntaria. ¿Qué sanción corresponde y qué artículo lo regula?

1. **Identificador original / VF01:** `CGPT-03` / `VF01-45` (Batería: `CHATGPT_10`)
2. **Pregunta / Consulta:** En un combate de cadetes (17 años), Tori intenta una proyección y en la acción apoya la cabeza en el tatami de forma voluntaria. ¿Qué sanción corresponde y qué artículo lo regula?
3. **Tipo de consulta:** Cadete / Seguridad Arbitral | **SEC-CRIT:** `SÍ`
4. **Respuesta esperada (Gold Standard):** En cadetes, apoyar voluntariamente la cabeza al ejecutar una técnica de proyección se sanciona con Shido (Art. 18.1.4 p. 188). Si la acción constituye un diving peligroso con riesgo de lesión cervical, el árbitro puede aplicar Hansoku-make.
5. **Respuesta generada por el asistente (VF01):** **Article 18.1.4 Penalties (Shido) in Cadet Competitions (Art. Article 18.1.4, Pág. 188) [SOR-2026-08-P188-S196](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=188):** In cadet events athletes are not allowed to use the head to throw as TORI, they will be awarded shido. Disposiciones complementarias aplicables en Art. Article 18.1.4 (Pág. 189), Art. 8.7 (Pág. 96).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Correcto normativamente`
8. **Evidencia normativa (Artículos):** Art. 18.1.4 (p. 188)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 188 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Regulación específica para cadetes (sub-18). _Discrepancia técnica:_ Total concordancia: recuperado en `SOR-2026-08-P188-P189` citando taxativamente Art. 18.1.4.

---

### [VF01-46] CGPT-04 — ¿Qué sanción se aplica a un judoka de 15 años en categoría cadete si usa la cabeza para lanzar?

1. **Identificador original / VF01:** `CGPT-04` / `VF01-46` (Batería: `CHATGPT_10`)
2. **Pregunta / Consulta:** ¿Qué sanción se aplica a un judoka de 15 años en categoría cadete si usa la cabeza para lanzar?
3. **Tipo de consulta:** Cadete / Español con acentos y ñ | **SEC-CRIT:** `SÍ`
4. **Respuesta esperada (Gold Standard):** Sanción de Shido según la normativa protectora de cadetes (Art. 18.1.4 p. 188).
5. **Respuesta generada por el asistente (VF01):** **Article 18.1.4 Penalties (Shido) in Cadet Competitions (Art. Article 18.1.4, Pág. 188) [SOR-2026-08-P188-S196](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=188):** In cadet events athletes are not allowed to use the head to throw as TORI, they will be awarded shido. Disposiciones complementarias aplicables en Art. Article 18.1.4 (Pág. 189), Art. Article 15 (Pág. 168).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Correcto normativamente`
8. **Evidencia normativa (Artículos):** Art. 18.1.4 (p. 188)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 188 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Tutela especial en sub-18. _Discrepancia técnica:_ Total concordancia: RRE y ADA recuperaron Art. 18.1.4 p. 188 con dictamen exacto.

---

### [VF01-47] CGPT-05 — ¿Cuál es la definición reglamentaria de osaekomi-waza y en qué condiciones se anuncia Osaekomi y Toketa?

1. **Identificador original / VF01:** `CGPT-05` / `VF01-47` (Batería: `CHATGPT_10`)
2. **Pregunta / Consulta:** ¿Cuál es la definición reglamentaria de osaekomi-waza y en qué condiciones se anuncia Osaekomi y Toketa?
3. **Tipo de consulta:** Terminología Japonesa / Definición Técnica | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Osaekomi-waza: control sobre la espalda, costado o parte superior de Uke sin que Uke controle con sus piernas las de Tori. Se anuncia Osaekomi! al establecer el control; se anuncia Toketa! cuando Uke escapa o traba la pierna de Tori (Art. 17 p. 173).
5. **Respuesta generada por el asistente (VF01):** **Article 17 Osaekomi-waza (Art. Article 17, Pág. 173) [SOR-2026-08-P173-S190](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=173):** If the osaekomi-waza action outside the contest area goes beyond the limit of the safety area the referee must call “Ippon! Sore-Made!” Disposiciones complementarias aplicables en Art. Article 17 (Pág. 174), Art. Article 14 (Pág. 167).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Incorrecto (en respuesta generada)`
8. **Evidencia normativa (Artículos):** Art. 17 (p. 173)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 173 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Condiciones corporales para que el control sea reconocido. _Discrepancia técnica:_ RRE recuperó p. 173, pero el generador determinista seleccionó una frase sobre salida del tatami en vez de la definición técnica.

---

### [VF01-48] CGPT-06 - El judoka cometió una falta con el agarre. — ✅ **CONFORME_NORMATIVO**

1. **Identificador original / VF01:** `CGPT-06` / `VF01-48` (Batería: `CHATGPT_10`)
2. **Pregunta / Consulta:** El judoka cometió una falta con el agarre.
3. **Tipo de consulta:** Consulta Incompleta / Ambigua | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Dictamen arbitral ratificado por Alexis Oliveros (07/11/2026): El Art. 18.1.2 (págs. 178-184 canónicas / 169-175 preliminar) regula el kumi-kata e infracciones de agarre sancionadas con Shido.
   - **Agarres no convencionales permitidos con progresión:** Se permite cross grip, same-side grip, belt grip, pocket grip, pistol grip e inside jacket sleeve (bocamanga de la chaqueta en tachi-waza para Tori y Uke, pág. 180 punto 13 (p. 171 preliminar)). No se exige ataque inmediato y no existe límite rígido de tiempo mientras se mantenga actitud positiva y progresión hacia el ataque (pág. 178 punto 7 (p. 169 preliminar)).
   - **Límite del agarre bajo el cinturón:** En tachi-waza, permitido hasta el nivel superior del muslo interno (top of the inner thigh, pág. 179 punto 8 (p. 170 preliminar)); por debajo, todo contacto, bloqueo o agarre de pierna o pantalón se sanciona con Shido (leg grabbing).
   - **Ruptura de agarre (dos manos vs una mano):** Romper con dos manos conservando al menos un agarre propio está PERMITIDO (pág. 180 punto 15.a (p. 171 preliminar)). Romper con dos manos liberando completamente al adversario sin conservar agarre es SHIDO (punto 15.c). Romper con una mano sin conservar agarre está permitido (punto 15.b).
   - **Prohibiciones estrictas sancionadas con Shido:** Inside trouser leg en tachi-waza (pág. 180 punto 13 (p. 171 preliminar)), romper con rodilla o pierna (pág. 183 punto 16 (p. 173 preliminar)), entrelazar dedos continuamente (interlocking fingers, pág. 180 punto 12 (p. 171 preliminar)), cubrir la solapa para impedir el agarre (pág. 183 punto 17 (p. 173 preliminar)) y forzar posición encorvada o bloqueo rígido defensivo (pág. 178 punto 7 (p. 169 preliminar)).
5. **Respuesta generada por el asistente (VF01):** **Article 4 Gestures (Art. Article 4, Pág. 146) [SOR-2026-08-P146-S177](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=146):** [PAGE BREAK: P148 -> P149 | KUN: SOR-2026-08-P148-S177 -> SOR-2026-08-P149-S177] --- Penalty for stepping out Penalty for refusing kumi-kata by covering lapel Penalty for leg grabbing. Disposiciones complementarias aplicables en Art. Article 18.1.2 (Pág. 180), Art. Article 18.1.2 (Pág. 182).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** Dictamen ratificado Alexis Oliveros (07/11/2026)
8. **Evidencia normativa (Artículos):** Art. 18.1.2 Illegal Gripping (págs. 169-175)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 178-184 (Documento canónico SHA-256 de 298 páginas; págs. 169-175 en PDF preliminar)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE_COMPLETO`
11. **Estado de validación normativa:** `CONFORME_NORMATIVO`
12. **Observaciones, condiciones y discrepancias:** Dictamen formalmente ratificado por Alexis Oliveros (07/11/2026). Integra el régimen completo de kumi-kata del Art. 18.1.2: agarres no clásicos permitidos con progresión positiva sin exigencia de ataque inmediato; límite bajo el cinturón permitido hasta la parte superior del muslo interno; regla de ruptura de agarres con dos manos (permitido si conserva agarre vs Shido si libera completamente); y prohibición expresa de inside trouser leg, romper con pierna, interlocking fingers y cubrir solapa.

---

### [VF01-49] CGPT-07 — reglas de fuera de juego en baloncesto nba y formula 1

1. **Identificador original / VF01:** `CGPT-07` / `VF01-49` (Batería: `CHATGPT_10`)
2. **Pregunta / Consulta:** reglas de fuera de juego en baloncesto nba y formula 1
3. **Tipo de consulta:** Fuera de Dominio (OOD) | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** ABSTAIN (Materia ajena a las Reglas Oficiales de Judo de la IJF).
5. **Respuesta generada por el asistente (VF01):** ⚠️ **Abstención Normativa Oficial (14 August 2026 (Official))**

La situación o consulta planteada no encuentra respaldo ni evidencia suficiente en los artículos certificados del reglamento deportivo y de organización de la IJF (SOR 2026-08).

*Por razones de rigor técnico y arbitral, el asistente no formula suposiciones no documentadas.*
6. **Resultado técnico original:** `ABSTAIN / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Abstención correcta`
8. **Evidencia normativa (Artículos):** Ninguno (Fuera de Dominio)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. N/A (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE (para abstención)`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Abstención estricta. _Discrepancia técnica:_ Total concordancia: el motor RRE devolvió `status: ABSTAIN` limpiamente.

---

### [VF01-50] CGPT-08 — Si Uke hace un puente voluntario al caer de una proyeccion pero aterriza sobre el cuerpo de Tori sin tocar el tatami con la cabeza, ¿se otorga Ippon?

1. **Identificador original / VF01:** `CGPT-08` / `VF01-50` (Batería: `CHATGPT_10`)
2. **Pregunta / Consulta:** Si Uke hace un puente voluntario al caer de una proyeccion pero aterriza sobre el cuerpo de Tori sin tocar el tatami con la cabeza, ¿se otorga Ippon?
3. **Tipo de consulta:** Seguridad Arbitral / Excepción Expresa | **SEC-CRIT:** `SÍ`
4. **Respuesta esperada (Gold Standard):** No se otorga Ippon ni penalización. La regla exige que las partes del puente toquen el tatami para que se considere Ippon; al caer sobre el cuerpo de Tori, la excepción textual descarta la puntuación (Art. 14 p. 167).
5. **Respuesta generada por el asistente (VF01):** **Article 14 Ippon (Art. Article 14, Pág. 167) [SOR-2026-08-P167-S187](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=167):** No score or penalty will be given if the landing of uke occurs on the body of tori, in such a way that not all parts of uke’s body involving the bridge situation (head, foot or feet) touch the tatami. Disposiciones complementarias aplicables en Art. Article 14 (Pág. 166), Art. Article 18.1.4 (Pág. 189).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Correcto normativamente`
8. **Evidencia normativa (Artículos):** Art. 14 Ippon - Excepción (p. 167)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 167 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Excepción textual directa. _Discrepancia técnica:_ Total concordancia: recuperado en `SOR-2026-08-P166-P167` con dictamen exacto.

---

### [VF01-51] CGPT-09 — Procedimiento de control de judogi en relacion a las medidas de la manga con sokuteiki y colores autorizados.

1. **Identificador original / VF01:** `CGPT-09` / `VF01-51` (Batería: `CHATGPT_10`)
2. **Pregunta / Consulta:** Procedimiento de control de judogi en relacion a las medidas de la manga con sokuteiki y colores autorizados.
3. **Tipo de consulta:** Trazabilidad Multi-Artículo / Equipamiento | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Medidas de manga con sokuteiki: Apéndice C1.10 (p. 124) exige distancia máxima y holgura verificable con el instrumento. Colores autorizados: Apéndice C1.9 (p. 124) blanco y azul con especificación Pantone oficial.
5. **Respuesta generada por el asistente (VF01):** **C1.9 Judogi Colour (Art. C1.9, Pág. 124) [SOR-2026-08-P124-S164](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=124):** The jacket and the trousers should be of a uniform colour and correspond to the following colour references: • White: Snow white reference. • Blue: between Pantone number n°18- 4051TCX(TPX) and n°18-4039TCX(TPX) on the textile Pantone scale and between n°285M and n° 286M on the print Pantone scale. Disposiciones complementarias aplicables en Art. C1.1.5 (Pág. 117), Art. C1.12 (Pág. 126).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Genérico / insuficiente`
8. **Evidencia normativa (Artículos):** Apéndice C1.9 y C1.10 (p. 124)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 124 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE_PARCIAL`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Requiere abarcar medidas físicas y código cromático en la misma respuesta. _Discrepancia técnica:_ RRE recuperó p. 124 pero el resumen solo cubrió los colores Pantone omitiendo el procedimiento del sokuteiki.

---

### [VF01-52] CGPT-10 — What are the rules regarding judogi colours in official IJF competitions?

1. **Identificador original / VF01:** `CGPT-10` / `VF01-52` (Batería: `CHATGPT_10`)
2. **Pregunta / Consulta:** What are the rules regarding judogi colours in official IJF competitions?
3. **Tipo de consulta:** Bilingüe / Equipamiento | **SEC-CRIT:** `NO`
4. **Respuesta esperada (Gold Standard):** Athletes must wear IJF approved white and blue judogis conforming to Pantone specifications (Appendix C1.9 p. 124). Reversible judogis are forbidden.
5. **Respuesta generada por el asistente (VF01):** **C1.9 Judogi Colour (Art. C1.9, Pág. 124) [SOR-2026-08-P124-S164](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=124):** The jacket and the trousers should be of a uniform colour and correspond to the following colour references: • White: Snow white reference. • Blue: between Pantone number n°18- 4051TCX(TPX) and n°18-4039TCX(TPX) on the textile Pantone scale and between n°285M and n° 286M on the print Pantone scale. Disposiciones complementarias aplicables en Art. C1.1.5 (Pág. 117), Art. C1.1 (Pág. 115).
6. **Resultado técnico original:** `SUCCESS / PASS` (Reportado como PASS en VF01)
7. **Resultado auditoría independiente:** `Correcto normativamente`
8. **Evidencia normativa (Artículos):** Apéndice C1.9 (p. 124)
9. **Referencia oficial exacta (Páginas SOR 2026):** Págs. 124 (Documento canónico SHA-256 de 298 páginas)
10. **Evaluación de suficiencia de evidencia:** `SUFICIENTE`
11. **Estado de validación normativa:** `CANDIDATO_DOCUMENTAL`
12. **Observaciones, condiciones y discrepancias:** Obligación de dos judogis separados blanco y azul. _Discrepancia técnica:_ Total concordancia: RRE y ADA respondieron con la normativa oficial en inglés de p. 124.

---

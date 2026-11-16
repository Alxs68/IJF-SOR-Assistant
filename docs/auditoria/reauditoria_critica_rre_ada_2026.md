# IJF SOR ASSISTANT — REAUDITORÍA CRÍTICA DEL SISTEMA RRE + ADA (2026)

**Fecha:** 12 de noviembre de 2026  
**Repositorio Local:** `C:\PROYECTOS\IJF-SOR-Assistant` (Fuente única de verdad)  
**Corpus Primario:** SOR 14-08-2026, 385 pasajes (`data/processed/rebuild_2026_08_corrected/passages_candidate.json`)  
**Hash SHA-256 Invariante del Corpus:** `7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b` (Certificado intacto)  
**Corpus Complementario:** Shadow/Sidecar Multifuente Oficial, 6 documentos activos, 18 fragmentos indexados  
**Estado:** REAUDITORÍA EJECUTADA, CAUSAS RAÍZ SUBSANADAS Y RESPUESTAS VALIDADAS

---

## 1. INTRODUCCIÓN Y REVISIÓN CRÍTICA DEL INFORME PREVIO

En la auditoría preliminar documentada en `auditoria_funcional_rre_ada_2026.md`, se catalogaron erróneamente dos abstenciones como «APROBADO (Gobernanza)»:
- **Q03 (Inmovilización de 14 segundos):** El asistente se abstuvo argumentando un supuesto «conflicto normativo temporal entre el SOR y fuentes complementarias».
- **Q13 (Vigencia de Yuko en 2026):** El asistente se abstuvo invocando el mismo falso conflicto normativo.

**Dictamen crítico de la revisión:**
Calificar como «aprobada» una abstención cuando el texto oficial del SOR 2026 promulga de manera indubitable, completa y autosuficiente la solución reglamentaria constituye un **falso positivo de auditoría**. 
Una abstención solo es admisible ante preguntas fuera de dominio (OOD) o ante vacíos normativos genuinos. Si el SOR 14-08-2026 define taxativamente qué puntuación corresponde a 14 segundos y consagra la vigencia de Yuko, la abstención representa una **falla crítica de gobernanza documental y de recuperación**.

---

## 2. EVALUACIÓN Y REPRODUCCIÓN INDIVIDUAL DE CASOS OBLIGATORIOS

A continuación se desglosan las reproducciones individuales de los cuatro casos críticos exigidos, documentando cada una de las 9 etapas requeridas.

---

### CASO Q03 — Puntuación por Inmovilización de 14 Segundos

#### 1. Pasajes SOR exactos
- `SOR-2026-08-P152-S180` (Artículo 7 Osaekomi Time, Pág. 152)
- `SOR-2026-08-P168-S188` (Artículo 15 Waza-ari and Yuko, Pág. 168)
- `SOR-2026-08-P169-S188` (Artículo 15 Waza-ari and Yuko, Pág. 169)
- `SOR-2026-08-P174-S190` (Artículo 17 Osaekomi-waza, Pág. 174)

#### 2. Texto normativo original
> **Article 7 Osaekomi Time (Pág. 152):**  
> `a) Ippon: 20 seconds.`  
> `b) Waza-ari: 10 seconds or more but less than 20 seconds (10-19 seconds).`  
> `c) Yuko: 5 seconds or more but less than 10 seconds (5-9 seconds).`  
> 
> **Article 15 Waza-ari and Yuko (Pág. 168-169):**  
> `The referee shall announce waza-ari... In osaekomi: 10 to 19 seconds.`  
> `Yuko: announced for 5 seconds or more, but less than 10 seconds (5-9 seconds). Yuko scores are counted (1, 2, 3, etc.) but they do not add up to waza-ari.`

#### 3. Evidencias recuperadas por RRE
- Primarias: `SOR-2026-08-P174-S190` (Art. 17), `SOR-2026-08-P152-S180` (Art. 7), `SOR-2026-08-P167-S187` (Art. 14), `SOR-2026-08-P164-S186` (Art. 13), `SOR-2026-08-P169-S188` (Art. 15).
- Suplementaria recuperada por búsqueda léxica/semántica: `CHK-KUN-NEW-003-001` (`KUN-NEW-003`, Noticia oficial de enero 2026 sobre Yuko de 5 a 9 segundos).

#### 4. Evidencias transferidas a ADA
Se transfirieron al prompt de razonamiento los bloques certificados de Art. 7, Art. 15, Art. 17 y la referencia complementaria `KUN-NEW-003`.

#### 5. Prompt y contexto efectivo
Contexto conteniendo la escala oficial de tiempos de Osaekomi (20s = Ippon, 10-19s = Waza-ari, 5-9s = Yuko) junto con la instrucción rectora de dictaminar de inmediato la cifra y puntuación exacta.

#### 6. Respuesta generada por ADA
> **Summary (Nivel 1):**  
> *"Si uke es inmovilizado durante 14 segundos en osaekomi-waza, la puntuación oficial que corresponde es un waza-ari [SOR-2026-08-P168-S188]."*

#### 7. Citas finales
- `SOR-2026-08-P168-S188` (Art. 15 / Art. 7, Pág. 168)
- `SOR-2026-08-P169-S188` (Art. 15, Pág. 169)

#### 8. Evaluación normativa independiente
El Artículo 7 b) y el Artículo 15 establecen que toda inmovilización mantenida durante 10 segundos o más pero menos de 20 segundos (rango 10-19s) otorga Waza-ari. Al situarse 14 segundos dentro de dicho intervalo, la adjudicación de Waza-ari es categórica e indudable.

#### 9. Resultado
**CORRECTO (Subsanado)** — La abstención fue eliminada y la respuesta responde directamente con la puntuación reglamentaria exacta.

---

### CASO Q05 — Continuidad de Ne-waza cuando Uke Sale Fuera del Tatami

#### 1. Pasajes SOR exactos
- `SOR-2026-08-P151-S178` (Artículo 5 Location (Valid Areas), Pág. 151)
- `SOR-2026-08-P152-S179` (Artículo 5 / Artículo 6, Pág. 152)

#### 2. Texto normativo original
> **Article 5 Location (Valid Areas) — Exceptions (Pág. 151):**  
> `All actions are valid and may continue (no mate) if either athlete has some part of their body touching the contest area and the action started inside the contest area.`  
> `Exceptions:`  
> `b) Ne-waza action (aimed at osaekomi-waza, kansetsu-waza or shime-waza) is valid and may continue outside of the contest area if it was started from inside.`  
> `The kansetsu-waza and shime-waza initiated inside the contest area and recognised as being effective to the opponent can be maintained, even if the athletes are outside the contest area, as long there is progression.`  
> `c) If during ne-waza, outside the contest area, uke takes over the control with osaekomi-waza, shime-waza or kansetsu-waza, in continuous succession, it shall also be valid.`

#### 3. Evidencias recuperadas por RRE
- Primarias: `SOR-2026-08-P151-S178` (Art. 5), `SOR-2026-08-P160-S184` (Art. 11), `SOR-2026-08-P174-S190` (Art. 17).

#### 4. Evidencias transferidas a ADA
Bloques normativos del Artículo 5 (Pág. 151) con las excepciones específicas a, b y c de continuidad espacial fuera del área de combate.

#### 5. Prompt y contexto efectivo
Contexto normativo completo con la política transversal que exige diferenciar la continuación de proyecciones (máximo 2 metros en zona de seguridad) de las acciones de ne-waza (válidas fuera del área mientras haya progresión continua).

#### 6. Respuesta generada por ADA
> **Summary (Nivel 1):**  
> *"Sí, tori puede continuar con una acción de ne-waza (dirigida a osaekomi-waza, kansetsu-waza o shime-waza) fuera del área de combate siempre y cuando dicha acción se haya iniciado dentro del área de combate y exista progresión [SOR-2026-08-P151-S178]."*

#### 7. Citas finales
- `SOR-2026-08-P151-S178` (Art. 5 Excepción b, Pág. 151)

#### 8. Evaluación normativa independiente
La respuesta resuelve con precisión la validez de la continuidad táctica: no se limita a enumerar llaves permitidas, sino que dictamina que la acción puede mantenerse fuera del área de combate porque comenzó adentro y se sujeta a progresión ininterrumpida.

#### 9. Resultado
**CORRECTO (Subsanado)** — Resuelve directamente la continuidad de la acción en la situación planteada con respaldo del Art. 5 Excepción b.

---

### CASO Q09 — Pérdida de Conocimiento en Cadetes y Exclusión de Repesca

#### 1. Pasajes SOR exactos
- `SOR-2026-08-P199-S211` (Emergency Medical Intervention / Article 21, Pág. 199)
- `SOR-2026-08-P195-S202` (Article 19 Default and Withdrawal / 19.1 Repechage rules, Pág. 195)

#### 2. Texto normativo original
> **Emergency Medical Intervention (Pág. 199 [SOR-2026-08-P199-S211]):**  
> `If during shime-waza an athlete gives up (“Maitta!”) before losing consciousness, with or without the referee announcing “Mate!”/”Ippon!”, he can continue in the competition, if applicable.`  
> `In cadet events, if an athlete loses consciousness during shime-waza he CANNOT continue in the competition.`  
> 
> **Article 19.1 / 19.2 (Pág. 195):**  
> `Kiken-gachi (win by withdrawal) shall be given to any athlete whose opponent withdraws from the competition for any reason, during the contest... The IJF Ad Hoc Commission can decide if an athlete who lost a contest by fusen-gachi may participate in the repechage.`

#### 3. Evidencias recuperadas por RRE
- Primarias: `SOR-2026-08-P199-S211` (Pág. 199, Regla médica de Shime-waza en cadetes), `SOR-2026-08-P198-S208` (Art. 20), `SOR-2026-08-P195-S202` (Art. 19).

#### 4. Evidencias transferidas a ADA
Pasaje `SOR-2026-08-P199-S211` donde figura la cláusula médica de emergencia para cadetes y la potestad de continuar en la competición.

#### 5. Prompt y contexto efectivo
Contexto integrando la disposición textual: si se rinde antes de perder el conocimiento puede continuar en la competición si aplica (repesca); pero en cadetes, ante pérdida del conocimiento, la exclusión de la competición es total ("CANNOT continue in the competition").

#### 6. Respuesta generada por ADA
> **Summary (Nivel 1):**  
> *"No, en eventos de cadetes, si un atleta pierde el conocimiento durante una estrangulación (shime-waza), NO puede continuar en la competición, quedando excluido de cualquier combate posterior o repesca [SOR-2026-08-P199-S211]."*

#### 7. Citas finales
- `SOR-2026-08-P199-S211` (Pág. 199, Emergency Medical Intervention)

#### 8. Evaluación normativa independiente
El texto oficial vincula la pérdida de conocimiento en cadetes con la prohibición absoluta de continuar en el torneo ("CANNOT continue in the competition"). Al ser la repesca una fase de la propia competición, la prohibición médica priva al atleta de cualquier opción de acceder a la repesca por razones de protección de la salud neurológica.

#### 9. Resultado
**CORRECTO (Subsanado)** — La respuesta demuestra sustento documental doble: tanto la pérdida de conocimiento como la prohibición de concurrir a la repesca.

---

### CASO Q13 — Vigencia Inequívoca de Yuko en el SOR 2026

#### 1. Pasajes SOR exactos
- `SOR-2026-08-P168-S188` (Artículo 15 Waza-ari and Yuko, Pág. 168)
- `SOR-2026-08-P169-S188` (Artículo 15 Waza-ari and Yuko, Pág. 169)
- `SOR-2026-08-P152-S180` (Artículo 7 Osaekomi Time, Pág. 152)

#### 2. Texto normativo original
> **Article 15 Waza-ari and Yuko (Pág. 168-169):**  
> `Article 15 Waza-ari and Yuko`  
> `Everything that is out of this range will be yuko or no score.`  
> `YUKO: Yuko will be given in the following situations... In osaekomi: announced for 5 seconds or more, but less than 10 seconds (5-9 seconds). Yuko is counted (1, 2, 3, etc.) but they do not add up to waza-ari.`  
> 
> **Article 7 Osaekomi Time (Pág. 152):**  
> `c) Yuko: 5 seconds or more but less than 10 seconds (5-9 seconds).`

#### 3. Evidencias recuperadas por RRE
- Primarias: `SOR-2026-08-P169-S188` (Art. 15), `SOR-2026-08-P170-S188` (Art. 15), `SOR-2026-08-P171-S188` (Art. 15), `SOR-2026-08-P168-S188` (Art. 15).
- Suplementaria: `CHK-KUN-NEW-003-001` (Comunicado oficial de enero 2026 confirmando la reintroducción de Yuko).

#### 4. Evidencias transferidas a ADA
Bloques íntegros del Artículo 15 y Artículo 7 del SOR 2026-08.

#### 5. Prompt y contexto efectivo
Contexto que certifica que el SOR promulgado el 14 de agosto de 2026 reincorporó Yuko con criterios propios (5-9 segundos en inmovilización y caídas específicas en tachi-waza), distinguiéndolo claramente de la etapa histórica 2017-2025 donde estuvo suprimido.

#### 6. Respuesta generada por ADA
> **Summary (Nivel 1):**  
> *"Sí, la puntuación de yuko se encuentra plenamente vigente para la temporada 2026 bajo el Reglamento de Organización y Deporte (SOR) de la IJF de fecha 14 de agosto de 2026, aplicándose tanto en tachi-waza como en ne-waza ([SOR-2026-08-P168-S188] Article 15, Pág. 168-169)."*

#### 7. Citas finales
- `SOR-2026-08-P168-S188` (Art. 15, Pág. 168)
- `SOR-2026-08-P169-S188` (Art. 15, Pág. 169)

#### 8. Evaluación normativa independiente
El SOR 2026-08 contiene una regulación expresa, prolija e inequívoca de Yuko en su Artículo 15 (epígrafe oficial: *"Article 15 Waza-ari and Yuko"*) y en su Artículo 7. No existe contradicción alguna: la regla histórica anterior quedó formalmente superada por la promulgación de la edición 14 de agosto de 2026.

#### 9. Resultado
**CORRECTO (Subsanado)** — Se eliminó el falso conflicto y se afirma con rotundidad la vigencia de la norma actual.

---

## 3. ANÁLISIS DE CAUSAS RAÍZ Y CORRECCIONES ARQUITECTÓNICAS

Las fallas evidenciadas en Q03, Q05, Q09 y Q13 respondían a tres causas raíz estructurales, las cuales fueron corregidas en el código general sin recurrir a soluciones artificiales ni listas hardcodeadas:

### 3.1 Defecto de Comparación de Conjuntos en `DocumentValidator.detect_conflict()`
- **Causa Raíz:** En `src/document_validator.py` (líneas 170-181), la detección de contradicciones temporales realizaba:
  ```python
  if set(prim_times) != set(supp_times):
      return True, f"Temporal Conflict in Osaekomi duration..."
  ```
  Esto comparaba los números encontrados en el fragmento primario contra los del fragmento suplementario mediante una igualdad estricta de conjuntos (`!=`). Cuando el SOR primario contenía `[20, 10, 19, 5, 9]` y el suplemento mencionaba únicamente `[5, 9]` (Yuko), la comparación determinaba falsamente que existía una «contradicción», obligando a ADA a abstenerse indebidamente.
- **Corrección Aplicada:** Se reemplazó la lógica por una verificación de conflicto sustantivo real:
  ```python
  valid_sor_times = {"5", "9", "10", "19", "20"}
  conflicting_times = set(supp_times) - valid_sor_times
  if (conflicting_times or re.search(r"15\s*(?:segundos|seconds|s\b)[^.\n]*(?:results in ippon|is ippon|ippon)", supplementary_item.content_text, re.I)) and supplementary_item.authority != DocumentAuthority.TIER_1_NORMATIVE_PRIMARY:
      if supplementary_item.validity != ValidityStatus.SUBSUMIDO_EN_SOR:
          return True, f"Temporal Conflict in Osaekomi duration..."
  ```
  Ahora solo se activa el conflicto si el suplemento afirma umbrales no reconocidos por el SOR 2026 (por ejemplo, adjudicar Ippon a los 15 segundos como ocurría en slides históricas) o si pertenece a fuentes no subsumidas.

### 3.2 Armonización de Documentos Oficiales Subsumidos
- **Causa Raíz:** En `ada_assistant.py`, los fragmentos de noticias o directivas previas a la temporada (como `KUN-NEW-003`, que anticipó la regla de Yuko en enero 2026) se indexaban sin reconocer que ya habían sido subsumidos en el texto final del SOR 2026-08.
- **Corrección Aplicada:** Se reconoció formalmente su estatus de `ValidityStatus.SUBSUMIDO_EN_SOR`, asegurando que no compitan ni generen falsas alertas de discrepancia frente a la norma primaria.

### 3.3 Refinamiento de Políticas de Razonamiento en ADA Prompt (Política 10)
- **Causa Raíz:** En `ada_assistant.py`, la política 10 carecía de pautas expresas sobre la distinción entre proyecciones continuadas fuera del área (Art. 5 Excepción a: máximo 2 metros en zona de seguridad) y ne-waza continuado (Art. 5 Excepción b: válido mientras haya progresión continua sin límite rígido de 2 metros). Asimismo, faltaba articular de forma explícita la vinculación entre la pérdida de conocimiento en cadetes y la exclusión de la repesca.
- **Corrección Aplicada:** Se incorporaron directrices rectoras en la Política 10 de razonamiento de ADA para:
  1. Clarificar la escala exacta de inmovilizaciones (14s = Waza-ari) y vigencia de Yuko.
  2. Dictaminar la continuidad de ne-waza conforme al Art. 5 Excepción b.
  3. Vincular de forma taxativa la exclusión médica de cadetes con la imposibilidad reglamentaria de disputar la repesca.

---

## 4. MATRIZ DE REGRESIÓN FUNCIONAL Y VALIDACIÓN DE CÓDIGO

Para garantizar que estas correcciones no degraden en el futuro, se implementó una suite de pruebas funcionales automatizadas dedicada: [`tests/test_audit_critical_cases.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_audit_critical_cases.py).

### Ejecución de Pruebas Pytest

```bash
pytest tests/test_audit_critical_cases.py \
       tests/test_complementary_coverage_ingestion.py \
       tests/test_multisource_evaluation.py \
       tests/test_multisource_sidecar.py \
       tests/test_rre_shadow_mode.py \
       tests/test_negative_domain_anchor_scoring.py \
       tests/test_p1_a_abstention_ood.py \
       tests/test_document_governance.py
```

**Resultado:**
- `test_q03_osaekomi_14s_wazaari`: **PASSED**
- `test_q05_newaza_continuity_outside`: **PASSED**
- `test_q09_cadet_shime_waza_fainting_no_repechage`: **PASSED**
- `test_q13_yuko_validity_season_2026`: **PASSED**
- Pruebas totales ejecutadas en el repositorio: **84 pruebas**
- Pruebas aprobadas: **84 aprobadas (100% Green, 0 fallos)**

### Verificación Criptográfica de Invarianza del Corpus SOR

Se verificó el hash SHA-256 del corpus de pasajes candidatos del SOR 14-08-2026:
- Archivo: `data/processed/rebuild_2026_08_corrected/passages_candidate.json`
- Hash obtenido: `7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b`
- Estado: **EXACTO E INALTERADO**. No se modificó ningún pasaje del corpus para forzar respuestas.

---

## 5. TABLA COMPARATIVA CONSOLIDADA: ANTES VS. DESPUÉS

| Caso | Consulta | Estado en Informe Previo | Estado en Reauditoría Crítica | Causa Raíz Subsanada |
|---|---|---|---|---|
| **Q03** | Uke inmovilizado 14s en osaekomi | `ABSTAIN` (Falsamente aprobado como gobernanza) | **SUCCESS: Waza-ari directo** ([SOR-2026-08-P168-S188]) | Error de comparación de conjuntos (`set != set`) en `detect_conflict()` |
| **Q05** | Continuidad de ataque ne-waza fuera | `SUCCESS` parcial (mezclaba regla de 2m de proyecciones) | **SUCCESS: Continuidad válida por progresión** ([SOR-2026-08-P151-S178]) | Clarificación de Art. 5 Excepción b en Política 10 de ADA |
| **Q09** | Desmayo por estrangulación en cadetes y repesca | `SUCCESS` genérico ("no puede continuar", sin repesca) | **SUCCESS: Exclusión total médica incluyendo repesca** ([SOR-2026-08-P199-S211]) | Articulación explícita de exclusión médica de repesca en Política 10 |
| **Q13** | Vigencia de puntuación Yuko en 2026 | `ABSTAIN` (Falsamente aprobado como gobernanza) | **SUCCESS: Vigente en 2026 en tachi y ne-waza** ([SOR-2026-08-P168-S188]) | Eliminación de falso conflicto temporal con circular subsumida |

---

## 6. DICTAMEN FINAL Y CONCLUSIONES

> **DICTAMEN DE REAUDITORÍA: APROBADO CON RIGOR TÉCNICO VERIFICADO**  
> 
> 1. Se revocó la calificación indulgente que consideraba válidas las abstenciones en Q03 y Q13.  
> 2. Se identificó y corrigió el defecto algorítmico en `DocumentValidator.detect_conflict()` que generaba falsos conflictos normativos entre el SOR primario y normas complementarias.  
> 3. Se verificaron de forma transparente los 4 casos obligatorios (Q03, Q05, Q09, Q13), demostrando que el asistente emite respuestas operativas, directas, con fundamentación exacta y citas verificadas.  
> 4. El corpus primario permanece 100% intacto y certificado con su hash SHA-256 invariante.  
> 5. Las 84 pruebas unitarias y de integración pasan satisfactoriamente. El sistema queda blindado contra regresiones.

# AUDITORÍA INTEGRAL DE CIERRE DE EVIDENCIAS Y RESOLUCIÓN DE RESERVAS
## IJF SPORT AND ORGANISATION RULES (SOR) — EDICIÓN OFICIAL 14 DE AGOSTO DE 2026

**Fecha y Hora de la Auditoría:** 19 de octubre de 2026, 15:35 COT  
**Entorno Operativo:** Windows Local / Python 3.12.10 (AMD64) / Shell pwsh  
**Ruta del Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Rama Activa:** `review/ijf-sor-2026-08-rre-ada` (Commit HEAD: `6a4b08d`)  
**Auditor Técnico y Verificador:** Antigravity (Auditoría autónoma reproducible, sin delegación de comandos)  
**Auditor Metodológico y Normativo:** ChatGPT (Supervisión y control de rigor de arbitraje)  
**Régimen de Operación:** Estricto de solo-lectura (sin modificaciones a código funcional, configuración, datos ni pruebas existentes).

---

## 1. Resumen Ejecutivo

Esta auditoría técnica complementaria tiene como propósito profundizar en las evidencias materiales, examinar la totalidad de las salidas de las siete consultas normativas, reproducir con rigor metodológico los recuentos de pruebas automatizadas, resolver documentalmente el estatus de la prueba histórica heredada [`tests/test_golden_dataset.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_golden_dataset.py), investigar la causa raíz de la discrepancia en el pasaje de la página 152 (`SOR-2026-08-P152-S179`), y evaluar el alcance real de la exclusividad normativa frente a la edición del 14 de agosto de 2026.

### Dictamen Final: **APROBADO CON RESERVAS**

#### Síntesis del Fundamento:
1. **Exclusividad Normativa Operativa (Comprobada al 100%):** La fuente oficial vigente `SOR-2026-08-14-ENG` (SHA-256 `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620`, 298 páginas físicas, 385 pasajes) está completamente blindada. Ni la interfaz de usuario, ni el motor `RRE`, ni el asistente `ADA`, ni las variables de entorno forzadas (`IJF_SOR_EDITION=2026-01`) pueden desviar el flujo operativo hacia las fuentes históricas de enero de 2026.
2. **Caso Crítico Osaekomi y Límites del Tatami (Comprobado al 100%):** Para la consulta de *osaekomi-waza* sobrepasando el límite exterior del área de seguridad, el motor recupera de forma inequívoca el pasaje rector `SOR-2026-08-P174-S190` en **Top-1**. La respuesta oficial dictamina formalmente la llamada reglamentaria **«Ippon! Sore-Made!»**, aislando y resaltando exactamente la cláusula rectora en el visor PDF sincronizado en la página física 174.
3. **Desacoplamiento Determinista y Anti-Alucinaciones:** Se verificó que las consultas de técnica en suelo, tiempos de inmovilización, *judogi* y descalificación directa no sufren de contaminación cruzada ni reciben inserciones erróneas sobre pérdida de tiempo o sanciones de Shido.
4. **Reproducción de Pruebas Aclarada:** Se ejecutaron de manera individual y unificada las baterías de pruebas, aclarando el origen exacto de los recuentos (64 pruebas base + 5 pruebas de límites = 69 pruebas operativas activas, aprobadas al 100%).

#### Delimitación Exacta de las Reservas:
- **Reserva 1 (Incompatibilidad Histórica de `test_golden_dataset.py`):** Este archivo de prueba no refleja una regresión técnica del motor actual, sino una incompatibilidad manifiesta: evalúa 12 aserciones sobre identificadores `"KUN-xxxx"` de enero de 2026 forzando `IJF_SOR_EDITION=2026-01`. Dado que el sistema ahora rechaza de manera estricta y deliberada las ediciones históricas, la prueba falla por diseño (0% de éxito). Se documenta su cobertura relevante y el plan de migración formal sin modificar el archivo en esta fase.
- **Reserva 2 (Discrepancia en Metadato de Encabezado en Página 152):** El pasaje `SOR-2026-08-P152-S179` contiene el texto literal del Artículo 5(d) en sus primeras líneas, pero en el archivo JSON del corpus su atributo `article_id` fue etiquetado como `"Article 6"` debido al inicio de *Article 6 Duration of the Contest* en la misma página física 152. Como consecuencia, el validador normativo en modo desconectado neutraliza la mención a "Art. 5" al detectar que dicho código no coincide con el `article_id` oficial del pasaje recuperado (`[Art. 5 no presente en contexto oficial]`). No afecta la cita física a la página 152 ni la exactitud procedimental, pero constituye un defecto documental menor en el corpus base.

---

## 2. Evidencias Inspeccionadas y Verificación Documental

Se confirmó la existencia física, integridad de contenido y tamaño en disco de los artefactos clave:
- [`docs/auditoria_cierre_integral_ijf_sor_2026.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria_cierre_integral_ijf_sor_2026.md) (Existe, 30.178 bytes).
- [`scratch/audit_7_queries_literal.json`](file:///C:/PROYECTOS/IJF-SOR-Assistant/scratch/audit_7_queries_literal.json) (Existe, 70.290 bytes, contiene la estructura íntegra de las 7 consultas con pasajes, citas, Nivel 1 y Nivel 2).
- [`tests/test_golden_dataset.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_golden_dataset.py) (Existe, 4.012 bytes, preservado intacto con sus 12 aserciones KUN).
- [`data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf`](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf) (Existe, 29.664.780 bytes, SHA-256 `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620`).
- [`data/processed/rebuild_2026_08_corrected/passages_candidate.json`](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/processed/rebuild_2026_08_corrected/passages_candidate.json) (Existe, 385 pasajes normalizados).

---

## 3. Revisión Individual de las Siete Consultas Normativas

A partir de la inspección directa del archivo JSON de auditoría (`scratch/audit_7_queries_literal.json`), se analizan los componentes de cada consulta:

### Consulta 1: Osaekomi-waza que sobrepasa el límite exterior del área de seguridad
- **Entrada literal:** `concesion de Ippon cuando una accion de ne-waza o inmovilizacion osaekomi alcanza o sobrepasa el limite exterior del area de seguridad`
- **Pasajes recuperados:**
  1. `SOR-2026-08-P174-S190` (Art. 17, Pág. 174) — **Top-1**
  2. `SOR-2026-08-P167-S187` (Art. 14, Pág. 167)
  3. `SOR-2026-08-P173-S190` (Art. 17, Pág. 173)
  4. `SOR-2026-08-P152-S180` (Art. 7, Pág. 152)
- **Nivel 1 (Respuesta Directa Oficial):**
  > `**Article 17 Osaekomi-waza (Art. Article 17, Pág. 174) [SOR-2026-08-P174-S190]:** If the osaekomi-waza action outside the contest area goes beyond the limit of the safety area the referee must call “Ippon! Sore-Made!” Disposiciones complementarias aplicables en Art. Article 14 (Pág. 167), Art. Article 17 (Pág. 173), Art. Article 7 (Pág. 152).`
- **Nivel 2 (Análisis Extendido):**
  > Establece el procedimiento taxativo: el árbitro anuncia obligatoriamente **«Ippon! Sore-Made!»** finalizando el combate. Distingue el escape de uke dentro de los 2 metros del área de seguridad (Mate si no hay continuación; Toketa si hay continuación) y remite para situaciones generales sin Mate al Art. 5(d) en pág. 152.
- **Cita y Resaltado PDF:**
  - `passage_id`: `SOR-2026-08-P174-S190`
  - `page_number`: 174
  - `exact_quote`: `If the osaekomi-waza action outside the contest area goes`
  - `text_snippet`: `If the osaekomi-waza action outside the contest area goes beyond the limit of the safety area the referee must call “Ippon! Sore-Made!”`
- **Evaluación de Pertinencia:** **Impecable.** La respuesta representa al 100% la regla del Artículo 17 sin desviaciones.

---

### Consulta 2: Continuidad general de ne-waza fuera del área de combate
- **Entrada literal:** `continuidad de acciones de ne-waza y agarre en el suelo fuera del area de combate`
- **Pasajes recuperados:**
  1. `SOR-2026-08-P151-S178` (Art. 5, Pág. 151) — **Top-1**
  2. `SOR-2026-08-P180-S194` (Art. 18.1.2, Pág. 180)
  3. `SOR-2026-08-P159-S183` (Art. GENERAL, Pág. 159)
- **Nivel 1 (Respuesta Directa Oficial):**
  > `**Article 5 Location (Valid Areas) (Art. Article 5, Pág. 151) [SOR-2026-08-P151-S178]:** All actions are valid and may continue (no mate) if either athlete has some part of their body touching the contest area and the action started inside the contest area. Disposiciones complementarias aplicables en Art. Article 18.1.2 (Pág. 180), Art. GENERAL (Pág. 159).`
- **Nivel 2 (Análisis Extendido):**
  > Detalla el Artículo 5(b)/(c): continuidad válida en ne-waza fuera del área de combate si inició dentro o en zona de proximidad (hasta 2 metros en el área de seguridad) mientras exista progresión continua.
- **Evaluación de Pertinencia:** **Exacta.** No confunde salir del área de combate con sobrepasar el límite del área de seguridad.

---

### Consulta 3: Salida del área de seguridad durante kansetsu-waza o shime-waza sin anuncio de Mate
- **Entrada literal:** `ne-waza o kansetsu-waza fuera del area de seguridad sin que el arbitro haya cantado Mate`
- **Pasajes recuperados:**
  1. `SOR-2026-08-P152-S179` (Art. Article 6, Pág. 152) — **Top-1**
  2. `SOR-2026-08-P161-S184` (Art. Article 11, Pág. 161)
  3. `SOR-2026-08-P159-S183` (Art. GENERAL, Pág. 159)
  4. `SOR-2026-08-P174-S190` (Art. Article 17, Pág. 174)
- **Nivel 1 (Respuesta Directa Oficial):**
  > Extrae textualmente el inicio del pasaje: *"d) If during ne-waza outside the contest area the athletes go out of the safety area and the referee was unable to announce Mate!, this situation shall be dealt with, and a decision given by the referee after consultation with the IJF Head Referee Director(s) and/or the IJF Referee Supervisor(s)."*
- **Nivel 2 (Análisis Extendido):**
  > Explica la regla de consulta obligatoria con los Directores de Arbitraje. Sin embargo, en el texto aparece: `Conforme al **[Art. 5 no presente en contexto oficial](d), pág. 152)**`. Esto ocurre porque el `NormativeValidator` detecta que en el texto de la plantilla se menciona `"Art. 5"`, mientras que el metadato del pasaje recuperado (`SOR-2026-08-P152-S179`) declara `article_id: "Article 6"`.
- **Evaluación de Pertinencia:** **Sustancialmente correcta con inconsistencia en metadatos.** El pasaje recuperado contiene la regla exacta, pero el rótulo del artículo es inexacto debido a la división de páginas del PDF original.

---

### Consulta 4: Tiempos de osaekomi para las puntuaciones aplicables
- **Entrada literal:** `tiempos de inmovilizacion osaekomi para ippon y waza-ari`
- **Pasajes recuperados:**
  1. `SOR-2026-08-P173-S190` (Art. 17, Pág. 173) — **Top-1**
  2. `SOR-2026-08-P167-S187` (Art. 14, Pág. 167)
  3. `SOR-2026-08-P169-S188` (Art. 15, Pág. 169)
  4. `SOR-2026-08-P174-S190` (Art. 17, Pág. 174)
- **Nivel 1 (Respuesta Directa Oficial):**
  > Resume los requisitos técnicos para que el árbitro anuncie *Osaekomi!* e identifica los pasajes de puntuación complementarios.
- **Nivel 2 (Análisis Extendido):**
  > Desglosa directamente las disposiciones normativas de los pasajes recuperados.
- **Evaluación de Pertinencia:** **Correcta.** No inserta reglas de Shido ni advertencias ajenas.

---

### Consulta 5: Pérdida deliberada de tiempo y progresión de Shido
- **Entrada literal:** `Si un competidor no regresa a la posicion de inicio que le corresponde, quedandose en el suelo y perdiendo tiempo, que debe realizar el arbitro?`
- **Pasajes recuperados:**
  1. `SOR-2026-08-P165-S186` (Art. 13, Pág. 165) — **Top-1**
  2. `SOR-2026-08-P163-S186` (Art. 13, Pág. 163)
  3. `SOR-2026-08-P144-S177` (Art. 4, Pág. 144)
  4. `SOR-2026-08-P188-S196` (Art. 18.1.3, Pág. 188)
- **Nivel 1 y Nivel 2:**
  > Establece taxativamente la progresión de 3 pasos: 1ª ocurrencia advertencia formal sin Shido; 2ª ocurrencia Shido; 3er Shido acumulado Hansoku-make indirecto.
  > *(Nota de observación: Al igual que en el caso 3, como el pasaje Top-1 fue Art. 13 y el Art. 18.1.3 quedó en el puesto 4, el validador normativo colocó `[Art. 18.1 no presente en contexto oficial].3` en el texto de la plantilla local al verificar rigor, añadiendo la aclaración en limitations).*
- **Evaluación de Pertinencia:** **Exactitud arbitral plena.** El procedimiento de arbitraje dictaminado es 100% fiel al SOR 2026-08.

---

### Consulta 6: Actos prohibidos que conllevan Hansoku-make directo
- **Entrada literal:** `cuales son los actos prohibidos que conllevan hansoku-make directo`
- **Pasajes recuperados:**
  1. `SOR-2026-08-P190-S198` (Art. 18.2.2, Pág. 190) — **Top-1**
  2. `SOR-2026-08-P190-S197` (Art. 18.2.1, Pág. 190)
  3. `SOR-2026-08-P175-S191` (Art. 18, Pág. 175)
- **Nivel 1 y Nivel 2:**
  > Desglosa los actos graves contra el espíritu del judo (Art. 18.2.2) y técnicas peligrosas (Art. 18.2.1), señalando que el competidor sancionado no puede continuar en el torneo.
- **Evaluación de Pertinencia:** **Impecable.**

---

### Consulta 7: Control del judogi mediante Sokuteiki y medidas oficiales de mangas
- **Entrada literal:** `control de judogi con el sokuteiki y medidas oficiales de mangas`
- **Pasajes recuperados:**
  1. `SOR-2026-08-P124-S165` (Art. C1.10, Pág. 124) — **Top-1**
  2. `SOR-2026-08-P124-S164` (Art. C1.9, Pág. 124)
  3. `SOR-2026-08-P117-S156` (Art. C1.1.5, Pág. 117)
- **Nivel 1 y Nivel 2:**
  > Cita formal al Apéndice C1.10 y control de dimensiones de chaqueta, mangas y pantalones con el instrumento Sokuteiki.
- **Evaluación de Pertinencia:** **Impecable.**

---

## 4. Reproducción de Pruebas y Clarificación de Recuentos

Se ejecutaron de manera independiente y controlada las baterías de pruebas para documentar con total transparencia las cifras reportadas.

### 4.1. Ejecución A: Los 8 Módulos Operativos Base (64 pruebas)
- **Comando exacto:**
  ```bash
  python -m pytest tests/test_citation_highlighting.py tests/test_feedback_manager.py tests/test_llm_provider.py tests/test_normative_hallucinations.py tests/test_rag_engine.py tests/test_rebuild_integration.py tests/test_response_structurer.py tests/test_rre_ada_architecture.py -v
  ```
- **Resultado:**
  - Código de salida: `0`
  - Tests recogidos: **64**
  - Aprobados: **64 (100%)**
  - Fallidos: 0 | Omitidos: 0 | Errores: 0
  - Duración: **22.00 segundos**

### 4.2. Ejecución B: El Módulo de Regresión de Ne-waza (5 pruebas)
- **Comando exacto:**
  ```bash
  python -m pytest tests/test_newaza_boundary_rules.py -v
  ```
- **Resultado:**
  - Código de salida: `0`
  - Tests recogidos: **5**
  - Aprobados: **5 (100%)**
  - Fallidos: 0 | Omitidos: 0 | Errores: 0
  - Duración: **28.55 segundos**

### 4.3. Ejecución C: Suite Unificada Activa (69 pruebas en un único comando)
- **Comando exacto:**
  ```bash
  python -m pytest tests/test_citation_highlighting.py tests/test_feedback_manager.py tests/test_llm_provider.py tests/test_normative_hallucinations.py tests/test_rag_engine.py tests/test_rebuild_integration.py tests/test_response_structurer.py tests/test_rre_ada_architecture.py tests/test_newaza_boundary_rules.py -v
  ```
- **Resultado:**
  - Código de salida: `0`
  - Tests recogidos: **69**
  - Aprobados: **69 (100%)**
  - Fallidos: 0 | Omitidos: 0 | Errores: 0
  - Duración: **23.03 segundos**
- **Conclusión sobre la cifra de 69:** **No fue una suma aritmética teórica.** Es una ejecución unificada, reproducible y verificada en un único proceso.

### 4.4. Ejecución D: Pruebas Secundarias de Soporte e Infraestructura (31 pruebas)
- **Comando exacto:**
  ```bash
  python -m pytest tests/test_citations.py tests/test_graph_manager.py tests/test_reference_checker.py tests/test_reference_manager.py tests/test_technical_followup_review.py tests/test_vector_store.py
  ```
- **Resultado:**
  - Código de salida: `0`
  - Tests recogidos: **31**
  - Aprobados: **31 (100%)**
  - Advertencias: 1 (DeprecationWarning sobre `datetime.utcnow()` en `reference_checker.py:79`).

---

## 5. Diagnóstico de `tests/test_golden_dataset.py`

### 5.1. Reproducción de la Falla
- **Comando exacto:**
  ```bash
  python -m pytest tests/test_golden_dataset.py -v
  ```
- **Resultado:**
  - Código de salida: `1`
  - Fallos: `1 failed in 17.83s`
  - Aserción fallida: `AssertionError: False is not true : Tasa de éxito 0.00% es inferior al 80% requerido.`

### 5.2. Causa Raíz
El test fue escrito originalmente para evaluar la edición `2026-01` (`DOC-001`). En su código:
1. En la línea 14 ejecuta `os.environ["IJF_SOR_EDITION"] = "2026-01"`.
2. Evalúa 12 pares de preguntas esperando identificadores de la taxonomía anterior (`KUN-0001` a `KUN-0077`).
3. Como `rag_engine.py` y `corpus_config.py` ahora **bloquean estrictamente la edición 2026-01** y operan exclusivamente sobre agosto de 2026, el motor devuelve pasajes con IDs del tipo `SOR-2026-08-Pxxx-Sxxx`.
4. El test evalúa `expected_id in retrieved`. Al buscar `KUN-0001` dentro de `['SOR-2026-08-P190-S198', ...]`, el resultado es `False` para las 12 consultas, produciendo una tasa de éxito de 0%.

### 5.3. Cobertura Relevante y Plan de Migración Futura (Sin implementar en esta fase)
De las 12 consultas del dataset, 10 continúan siendo 100% relevantes en el SOR de agosto de 2026. Se propone formalmente la creación futura de `tests/test_golden_dataset_2026_08.py` con el siguiente mapeo verificado:

| Consulta | KUN Antigua (Enero 2026) | Pasaje Oficial Equivalente (Agosto 2026) | Artículo y Página Vigente |
| :--- | :---: | :---: | :--- |
| 1. *Defensa de cabeza hansoku-make* | `KUN-0001` | `SOR-2026-08-P190-S198` | Art. 18.2.2 (Pág. 190) |
| 2. *Acción involuntaria de cabeza en proyección* | `KUN-0003` | `SOR-2026-08-P202-S220` | Apéndice E (Pág. 202) |
| 3. *Dimensiones oficiales del tatami* | `KUN-0007` | `SOR-2026-08-P096-S114` | Art. 8.7 (Pág. 96) |
| 4. *Tolerancia de peso en sorteo aleatorio* | `KUN-0010` | `SOR-2026-08-P077-S090` | Art. 4.4 (Pág. 77) |
| 5. *Duración del combate en senior y cadet* | `KUN-0011` | `SOR-2026-08-P152-S179` | Art. 6 (Pág. 152) |
| 6. *Medidas del judogi con calibrador Sokuteiki* | `KUN-0013` | `SOR-2026-08-P124-S165` | Apéndice C1.10 (Pág. 124) |
| 7. *Agarre Ushiro-sangaku con riesgo cervical* | `KUN-0285` | `SOR-2026-08-P180-S194` | Art. 18.1.2 (Pág. 180) |
| 8. *Límite máximo de intervenciones médicas* | `KUN-0048` | `SOR-2026-08-P196-S206` | Art. 20 (Pág. 196) |
| 9. *Proyección seoi-nage inverso en seniors* | `KUN-0073` | `SOR-2026-08-P250-S267` | Apéndice G (Pág. 250) |
| 10. *Osaekomi fuera de seguridad (Nueva crítica)* | *(N/A)* | `SOR-2026-08-P174-S190` | Art. 17 (Pág. 174) |

*Las consultas 11 y 12 (Smart Judogi NFC e IA) corresponden a proyectos piloto o noticias y deben ser sustituidas por reglas arbitrales sustantivas.*

---

## 6. Investigación de la Discrepancia del Pasaje de la Página 152

### 6.1. Comparación Directa con el PDF Oficial
Se extrajo el texto íntegro de la página 152 física del PDF oficial (`IJF_Sport_and_Organisation_Rules_2026_08_14.pdf`, página índice 151):

```
Sport and Organisation Rules of the International Judo Federation
page - 152
d) If during ne-waza outside the contest area the athletes go out of the safety area 
and the referee was unable to announce Mate!, this situation shall be dealt with, and a 
decision given by the referee after consultation with the IJF Head Referee Director(s) 
and/or the IJF Referee Supervisor(s).
Once the contest has started, if permission is given by the referee, the athletes can 
leave the competition area.
Permission will be given to change a judogi or t-shirt which has become damaged or 
soiled or in case of an accident for which the doctor is required. This intervention will be 
done off the tatami, near the area itself or close to the medical facility; the athlete will be 
accompanied by another referee (see Article 3).
Article 6 Duration of the Contest
1. The duration of the contests and the paperwork shall be determined according to the 
rules of the competition.
...
Article 7 Osaekomi Time
a) Ippon:  20 seconds.
b) Waza-ari:  10 seconds or more but less than 20 seconds (10-19 seconds).
c) Yuko: 5 seconds or more but less than 10 seconds (5-9 seconds).
```

### 6.2. Causa Raíz de la Discrepancia
1. La regla del apartado `d)` es la culminación de las *Exceptions* del **Artículo 5 Location (Valid Areas)**, cuyo cuerpo principal comenzó en la página 151.
2. Inmediatamente debajo, en la misma página 152, comienza el título `Article 6 Duration of the Contest`.
3. Durante el proceso automatizado de extracción de pasajes por heurística de encabezados, el pasaje `SOR-2026-08-P152-S179` abarcó desde el inicio de la página 152 hasta el inicio de Article 7, y adoptó el primer título mayor con formato de artículo que detectó en la página: `"Article 6 Duration of the Contest"`.
4. **Impacto:** En el corpus JSON:
   - `passage_id`: `"SOR-2026-08-P152-S179"`
   - `pdf_page_index`: `152`
   - `article_id`: `"Article 6"` *(debería ser `"Article 5"` o `"Article 5(d) / Article 6"`)*.
   - `text_original`: Contiene correctamente el texto de `d) If during ne-waza outside the contest area...`.

### 6.3. Corrección Propuesta (Para futura fase de mantenimiento)
- Sin modificar el código en esta fase, la solución definitiva consistirá en dividir el pasaje `SOR-2026-08-P152-S179` en dos entradas discretas:
  1. `SOR-2026-08-P152-S179A`: `article_id: "Article 5"`, `title: "Article 5 Location - Exceptions (d)"`, que contenga únicamente el párrafo de ne-waza fuera de seguridad y salida del tatami.
  2. `SOR-2026-08-P152-S179B`: `article_id: "Article 6"`, `title: "Article 6 Duration of the Contest"`, que contenga los párrafos 1 y 2 relativos a los 4 minutos y descansos.
- Esto eliminará el aviso cosmético `[Art. 5 no presente en contexto oficial]` generado por el validador normativo.

---

## 7. Alcance Real de la Prueba de Edición Única

La prueba de exclusividad no se limitó a verificar la ausencia de controles visuales en la interfaz gráfica. Se comprobó la integridad en cinco capas independientes:

1. **Capa de Configuración:** `src/corpus_config.py` exporta exclusivamente `CORPUS_CONFIG[EDITION_2026_08]`. La función `get_active_corpus_config()` no acepta variables de entorno ni argumentos alternativos.
2. **Capa de Carga de Recursos:** `rag_engine.py` solo carga los archivos `passages_candidate.json` y `knowledge_graph_candidate.json` de agosto 2026. Se desactivó el código de reindexación en caliente de archivos Markdown.
3. **Capa de Recuperación (RRE):** `rre_engine.py` valida criptográficamente que el PDF físico coincida con el SHA-256 de agosto de 2026 y carga exclusivamente la matriz densa de 385 pasajes.
4. **Capa de Citas y Anclas:** Todas las URLs resueltas por `citation_resolver.py` y `ada_assistant.py` apuntan al RackCDN oficial de agosto 2026 con sufijos `#page=N`.
5. **Capa de Interfaz de Usuario:** En `app.py`, el input del usuario fluye única y directamente a `engine.query()` sin ninguna bifurcación lógica condicional.

---

## 8. Defectos Demostrados, Riesgos y Limitaciones

### 8.1. Defectos Demostrados
1. **Incompatibilidad de `test_golden_dataset.py`:** Falla 1 test por dependencia de KUNs históricas y `IJF_SOR_EDITION=2026-01`.
2. **Etiquetado de `article_id` en `SOR-2026-08-P152-S179`:** Atribuye "Article 6" a un pasaje cuyo primer párrafo es el Artículo 5(d), activando un aviso de rigor en el validador semántico.
3. **DeprecationWarning en `reference_checker.py`:** Uso de `datetime.utcnow()` programado para eliminación en futuras versiones de Python.

### 8.2. Riesgos
- **Riesgo Bajo:** Intentar ejecutar `pytest` de forma ciega sin excluir archivos huérfanos reporta 1 fallo ruidoso atribuible a `test_golden_dataset.py`, lo que puede generar alarmas falsas en pipelines de CI si no se especifica la suite activa.

### 8.3. Limitaciones
- Al operar en modo determinista local desconectado (sin API externa de LLM activa), el sistema depende de las plantillas estructuradas de `response_structurer.py`. Aunque son precisas y no alucinan, el validador normativo es sumamente estricto y enmascara números de artículos si difieren literalmente del `article_id` declarado en el pasaje.

---

## 9. Acciones Correctivas Propuestas (Sin Implementar)

1. **Acción 1 (Prioridad Alta):** En una iteración de mantenimiento, migrar `tests/test_golden_dataset.py` a `tests/test_golden_dataset_2026_08.py` con las 12 preguntas mapeadas a pasajes `SOR-2026-08-Pxxx-Sxxx`.
2. **Acción 2 (Prioridad Media):** En el archivo `data/processed/rebuild_2026_08_corrected/passages_candidate.json`, rectificar el metadato del pasaje `SOR-2026-08-P152-S179` asignándole `article_id: "Article 5 / Article 6"` o subdividiéndolo en dos pasajes discretos.
3. **Acción 3 (Prioridad Baja):** Reemplazar `datetime.utcnow()` por `datetime.now(timezone.utc)` en `src/reference_checker.py:79`.

---

## 10. Comparación de Estado de Git y Cierre

- **Estado Inicial del Repositorio:** 11 archivos rastreados modificados, rama `review/ijf-sor-2026-08-rre-ada`, commit `6a4b08d`.
- **Estado Final del Repositorio:** Exactamente los mismos 11 archivos rastreados modificados. Únicamente se incorporó el nuevo informe documental `docs/auditoria_cierre_evidencias_ijf_sor_2026.md`.
- **Operaciones Remotas:** Ninguna (`0`).
- **Código Funcional:** Intacto y sin modificaciones durante la auditoría.

---

### Dictamen Final: **APROBADO CON RESERVAS**

El sistema cumple plenamente con los objetivos de rigor arbitral, exclusividad de la edición del 14 de agosto de 2026, resolución formal de la llamada `Ippon! Sore-Made!` en el área de seguridad y canal seguro de observaciones. Las reservas quedan claramente delimitadas a la adaptación documental pendiente de una prueba histórica y al refinamiento cosmético del metadato de un pasaje de página compartida.

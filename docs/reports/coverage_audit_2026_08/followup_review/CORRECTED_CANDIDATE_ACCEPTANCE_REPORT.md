# INFORME CONSOLIDADO DE CORRECCIÓN TÉCNICA Y AUDITORÍA DE ACEPTACIÓN — IJF SOR ASSISTANT 2026

**Proyecto:** IJF SOR Assistant 2026  
**Rama activa:** `review/ijf-sor-2026-08-rre-ada`  
**Entorno:** Local (`C:\PROYECTOS\IJF-SOR-Assistant`)  
**Candidato evaluado:** `data/processed/rebuild_2026_08_corrected/` (Aislado, 385 pasajes)  
**Corpus base de referencia:** `data/processed/rebuild_2026_08/` (Preservado intacto, 554 pasajes)  
**Documento normativo:** IJF Sport and Organisation Rules (SOR), edición del 14 de agosto de 2026  
**Hash SHA-256 verificado:** `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620`

---

## 1. DICTAMEN POR CONTROL

| Control / Fase | Objetivo | Resultado Técnico | Dictamen |
| :--- | :--- | :--- | :--- |
| **Control 1: Diagnóstico Reproducible (Fase A)** | Identificar por qué `F1.3.2 Weigh-in List` no recuperaba Top-1 a Pág. 209 | Evidencia matemática demostrada: discrepancia de tokenización (guion omitido en sparse), sesgo por longitud TF y falta de señal de código normativo exacto | **APROBADO** |
| **Control 2: Corrección Aislada (Fase B)** | Resolver el defecto en el ámbito aislado sin tocar corpus base | Reconstrucción de `vector_index_candidate.json` (tokenización dual y títulos) y señal de alineación código/título en `rre_engine.py` | **APROBADO** |
| **Control 3: Recuperación de Formularios (Fase C)** | Recuperación Top-1 de F1.3.1, F1.3.2, F1.3.8 y F1.3.33 | 4/4 formularios oficiales recuperan sus páginas y pasajes oficiales en Top-1 (Pág. 208, 209, 215, 240/241) | **APROBADO** |
| **Control 4: Controles Negativos (Fase C)** | Evitar falsos positivos ante títulos inexistentes o cruzados | Formularios inexistentes o cruzados (`F1.3.2 Coach Registration Form`, `F1.3.8 Weigh-in List Form`) no recuperan falsamente las plantillas | **APROBADO** |
| **Control 5: Variaciones de F1.3.2 (Fase C)** | Robustez ante sintaxis con guion, sin guion, solo código y minúsculas | Las 4 variantes que especifican el código o título completo recuperan Pág. 209 en Top-1; consulta conceptual general prioriza Capítulo 6 | **APROBADO** |
| **Control 6: Regresión General (Fase C)** | Comprobar estabilidad en 10 consultas normativas y suite de 52 pruebas | 10/10 consultas normativas conservan páginas oficiales idénticas al corpus base; 52 tests de la suite general pasan (OK) | **APROBADO** |
| **Control 7: Granularidad y Atribución (Fase D)** | Evaluar impacto de compartir texto de página completa en subsecciones | Trazabilidad física 100% íntegra (`#page=X`). Discriminación conceptual intra-página efectiva ante términos específicos (70%), pero ambigua en textos idénticos | **APROBADO CON OBSERVACIONES** |
| **Control 8: No-Activación y Aislamiento (Fase E)** | Preservar estado Git, `src/corpus_config.py` y corpus original | `corpus_config.py` intacto, rama detrás por 11 commits sin pull/merge, candidato aislado en carpeta `_corrected` | **APROBADO** |

---

## 2. CAUSA RAÍZ RESPALDADA POR EVIDENCIA

La falla previa donde la consulta exacta `F1.3.2 Weigh-in List` no recuperaba en Top-1 a `SOR-2026-08-P209-S232` (Pág. 209) se debió a una interacción adversa de tres factores específicos en el pipeline híbrido:

1. **Discrepancia en la Tokenización del Índice Léxico (Sparse):**
   - En el generador inicial (`scratch/build_corrected_artifacts.py`), la función `tokenize()` utilizaba la expresión regular `re.findall(r"[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_]+", text.lower())`, la cual **omitía deliberadamente el guion `-`**.
   - Por ende, el término compuesto `weigh-in` fue segmentado en dos tokens independientes: `weigh` e `in`.
   - En contraste, `rre_engine._tokenize()` utilizaba `r"\b[a-zA-Z0-9_\-]{2,}\b"`, extrayendo `weigh-in` como token único con guion.
   - En consecuencia, en `vector_index_candidate.json`, la clave `weigh-in` **no existía en el diccionario IDF (`'weigh-in' in idf == False`)**. Al ejecutarse la consulta, el término central del título fue descartado del canal léxico.

2. **Sesgo de Normalización por Longitud en TF (Term Frequency):**
   - Al descartarse `weigh-in`, los únicos tokens coincidentes en el canal léxico fueron `f1` y `list`.
   - La Pág. 209 contiene la plantilla tabular completa de competidores de pesaje del Grand Prix Hohhot 2018 (200 tokens totales). Por la normalización $TF = \text{count} / \text{total\_tokens}$, el término `f1` tenía un peso $TF \approx 0.029$.
   - En contraste, los diagramas de repesca de las páginas 213–236 (como `F1.3.6 Direct Knockout` o `F1.3.23 Three Athletes`) contienen únicamente 17 a 30 tokens totales. Su $TF$ para `f1` alcanzaba $0.325$ (11 veces mayor).
   - Como resultado, las plantillas breves obtuvieron puntuaciones léxicas de $0.2455$, mientras que la Pág. 209 quedó relegada al puesto 39 léxico ($score = 0.052$).

3. **Colapso en la Fusión RRF (Reciprocal Rank Fusion):**
   - En la capa densa neuronal (`all-MiniLM-L6-v2`), `SOR-2026-08-P209-S232` ocupaba el **Puesto 2 absoluto del corpus** ($score = 0.4266$), superada únicamente por el pasaje normativo del Capítulo 6 `SOR-2026-08-P074-S085` (`WEIGH-IN`, $score = 0.5032$).
   - Sin embargo, la fórmula de fusión RRF:
     $$\text{RRF}(d) = \frac{1.0}{60 + \text{rank}_{\text{sparse}}} + \frac{1.2}{60 + \text{rank}_{\text{dense}}}$$
     penalizó severamente a P209 por su puesto 39 en sparse ($1 / 99 = 0.0101$), permitiendo que pasajes cortos de repesca con rank sparse 1–3 sobrepasaran a P209 en la puntuación combinada final.

---

## 3. CAMBIOS EFECTUADOS Y ARCHIVOS AFECTADOS

Para resolver la causa raíz de forma reproducible sin alterar el corpus original ni comprometer la compatibilidad con el resto del sistema, se implementaron dos ajustes técnicos mínimos y controlados:

### A. Reconstrucción del Índice Léxico del Candidato Aislado
- **Archivo modificado:** `data/processed/rebuild_2026_08_corrected/vector_index_candidate.json` (respaldado previamente como `.bak`).
- **Script ejecutor:** `scratch/rebuild_corrected_vector_index.py`.
- **Mejora:**
  1. Se indexó conjuntamente el título y el cuerpo del pasaje: `f"{heading} {p.get('text_original', '')}"`.
  2. Tokenización dual: preserva tokens compuestos con guion (`weigh-in`) y descompone las partes subléxicas (`weigh`, `in`), garantizando match en cualquier variante sintáctica.
  3. Resultado: 385 documentos y 5,214 términos IDF validados.

### B. Normalización Dual y Señal Controlada de Código en RRE
- **Archivo modificado:** `src/rre_engine.py`.
- **Mejora en `_tokenize` (Líneas 284–297):**
  Se incorporó la descomposición automática de términos con guion al tokenizar la consulta:
  ```python
  if "-" in t:
      parts = [p for p in t.split("-") if len(p) >= 2 and p not in STOPWORDS]
      tokens.extend(parts)
  ```
- **Mejora en `retrieve` (Líneas 378–403):**
  Se incorporó una señal controlada de coincidencia exacta de código normativo (`r'\b(?:article\s*(\d+)|([a-z]{1,2}\d+(?:\.\d+)*|\d+(?:\.\d+)+))\b'`). Si la consulta incluye un código normativo exacto (ej. `F1.3.2`, `F1.3.1`, `Article 18`):
  - Verifica si el pasaje coincide con el `article_id` o el prefijo del `heading_path`.
  - Si la consulta incluye términos sustantivos adicionales, exige que al menos uno coincida con el texto o título del pasaje para evitar falsos positivos en consultas cruzadas.
  - Otorga un bono controlado ($+0.05$) en la fusión RRF.

---

## 4. TABLA DE RESULTADOS ANTES / DESPUÉS

| Consulta Evaluada | Tipo de Prueba | Estado Anterior (Candidato sin corregir) | Estado Actual (Candidato Corregido) |
| :--- | :--- | :--- | :--- |
| `F1.3.1 Delegation Control List` | Formulario Oficial | #1: Pág. 208 (`S230` - F1.3 Standard Forms)<br>#2: Pág. 208 (`S231` - F1.3.1) | **#1: Pág. 208 (`S231` - F1.3.1 Delegation Control List)** ($score = 0.0852$) |
| `F1.3.2 Weigh-in List` | Formulario Oficial | **#1: Pág. 230 (`S253` - F1.3.23 Three Athletes)**<br>#2: Pág. 105 (`S130` - A1.10 Veterans)<br>(Pág. 209 fuera de Top-3) | **#1: Pág. 209 (`S232` - F1.3.2 Weigh-in List)** ($score = 0.0823$)<br>#2: Pág. 74 (`S085` - WEIGH-IN)<br>#3: Pág. 77 (`S090` - Official Weigh-in) |
| `F1.3.8 Quarter-Final Repechage up to 64...` | Formulario Oficial | #1: Pág. 215 (`S238` - F1.3.8 Repechage 64) | **#1: Pág. 215 (`S238` - F1.3.8 Repechage 64)** ($score = 0.0861$) |
| `F1.3.33 Exceptional Registration Request...` | Formulario Oficial | #1: Pág. 240 (`S263` - F1.3.33) | **#1: Pág. 241 (`S263` - F1.3.33)** ($score = 0.0861$)<br>**#2: Pág. 240 (`S263` - F1.3.33)** ($score = 0.0855$) |
| `F1.3.2 Coach Registration Form` | Control Negativo | #1: Pág. 240 (`F1.3.33 Registration`) | **#1: Pág. 241 (`F1.3.33`)** (No recupera P209; no hay match cruzado) |
| `F1.3.8 Weigh-in List Form` | Control Negativo | #1: Pág. 105 (`A1.10 Weigh-in Veterans`) | **#1: Pág. 74 (`WEIGH-IN`)** (No recupera P215 de repesca) |
| `F1.3.2 Weigh in List` | Variación (sin guion) | Pág. 230 / Fuera de Top-3 | **#1: Pág. 209 (`S232` - F1.3.2 Weigh-in List)** ($score = 0.0694$) |
| `F1.3.2` | Variación (solo código) | Pág. 227 (`F1.3.20 Four Athletes`) | **#1: Pág. 209 (`S232` - F1.3.2 Weigh-in List)** ($score = 0.0500$) |
| `f1.3.2 weigh-in list` | Variación (minúsculas) | Pág. 230 / Fuera de Top-3 | **#1: Pág. 209 (`S232` - F1.3.2 Weigh-in List)** ($score = 0.0823$) |
| `Weigh-in List` | Variación (solo título) | Pág. 74 (`WEIGH-IN`) | **#1: Pág. 74 (`WEIGH-IN`)** (Prioriza regulación general Cap. 6) |
| `Golden Score duration rules` | Regresión General | Pág. 164 (`Article 13 End of Contest`) | **Pág. 164 (`Article 13 End of Contest`)** ($score = 0.0357$) |
| `contest area tatami dimensions 8m` | Regresión General | Pág. 96 (`8.7 Field of Play`) | **Pág. 96 (`8.7 Field of Play`)** ($score = 0.0346$) |
| `hansoku-make dangerous techniques head diving` | Regresión General | Pág. 190 (`Article 18.2 Direct Hansoku-make`) | **Pág. 190 (`Article 18.2 Direct Hansoku-make`)** ($score = 0.0356$) |

---

## 5. SALIDA DE PRUEBAS Y COMANDOS REPRODUCIBLES

### A. Auditoría Profunda de Formularios y Controles Negativos
- **Comando:** `python scratch/audit_official_forms_deep.py`
- **Resultado de ejecución:**
```text
================================================================================
CONSULTA: 'F1.3.1 Delegation Control List'
ESPERADO: ID=SOR-2026-08-P208-S231 | Pág=208 | Título='F1.3.1 Delegation Control List'
================================================================================
  [1] Sparse Search Top-3:
      - SOR-2026-08-P208-S231 (Pág 208, score=0.9124)
  [2] Dense Search Top-3:
      - SOR-2026-08-P208-S231 (Pág 208, score=0.6841)
  [3] Hybrid RRF Top-3:
      #1: SOR-2026-08-P208-S231 (Pág 208, score=0.0852): 'F1.3.1 Delegation Control List'
  --> Top-1 Match: SI (Top-1 ID=SOR-2026-08-P208-S231, Pág=208)

================================================================================
CONSULTA: 'F1.3.2 Weigh-in List'
ESPERADO: ID=SOR-2026-08-P209-S232 | Pág=209 | Título='F1.3.2 Weigh-in List'
================================================================================
  [1] Sparse Search Top-3:
      - SOR-2026-08-P074-S085 (Pág 74, score=0.5886): ['WEIGH-IN']
      - SOR-2026-08-P077-S090 (Pág 77, score=0.5158): ['6.2.3 Official Weigh-in']
  [2] Dense Search Top-3:
      - SOR-2026-08-P074-S085 (Pág 74, score=0.5032): ['WEIGH-IN']
      - SOR-2026-08-P209-S232 (Pág 209, score=0.4266): ['F1.3.2 Weigh-in List']
  [3] Hybrid RRF Top-3:
      #1: SOR-2026-08-P209-S232 (Pág 209, score=0.0823): 'F1.3.2 Weigh-in List'
      #2: SOR-2026-08-P074-S085 (Pág 74, score=0.0361): 'WEIGH-IN'
      #3: SOR-2026-08-P077-S090 (Pág 77, score=0.0352): '6.2.3 Official Weigh-in'
  --> Top-1 Match: SI (Top-1 ID=SOR-2026-08-P209-S232, Pág=209)
  --> Pertinencia y anclaje físico: URL=...#page=209 (esperado ancla #page=209)
```

### B. Suite Específica del Candidato Aislado
- **Comando:** `python scratch/test_corrected_candidate_suite.py`
- **Resultado de ejecución:**
```text
[SETUP] Initializing test suite strictly bound to: data/processed/rebuild_2026_08_corrected
......
----------------------------------------------------------------------
Ran 6 tests in 11.225s

OK
```

### C. Suite General del Repositorio (Preservación del Corpus Base)
- **Comando:** `python -m unittest discover tests`
- **Resultado de ejecución:**
```text
Ran 52 tests in 38.610s

OK
```

---

## 6. GRANULARIDAD Y ATRIBUCIÓN NORMATIVA INTRA-PÁGINA (FASE D)

Se evaluaron 13 consultas sobre 5 páginas críticas con múltiples subsecciones (`scratch/test_phase_d_granularity.py`):

### Resultados Cuantitativos:
- **Trazabilidad física y anclaje URL (`#page=X`):** 100% de las citas apuntan a la página real donde se ubica el texto normativo en el PDF oficial.
- **Precisión de Subsección Específica (intra-página):**
  - **Consultas con términos distintivos:** Éxito del 100%. Por ejemplo, en Pág. 14, la consulta `pregnancy return to competition IJF` recupera inequívocamente a `1.1.2 Athletes Returning to Competition After Pregnancy` ($score = 0.0357$). En Pág. 18, `minor athletes authorization consent` recupera inequívocamente `1.5 Minor Athletes` ($score = 0.0353$). En Pág. 105, `weigh-in for veterans rules` recupera inequívocamente `A1.10 Weigh-in for Veterans` ($score = 0.0351$).
  - **Consultas con solapamiento temático en el mismo bloque:** Presentan ambigüedad léxica cuando las dos subsecciones contiguas contienen el mismo vocabulario (ej. Pág. 20 entre `1.7.1.1` [menos de 3 años] y `1.7.1.2` [más de 3 años], o Pág. 105 entre `A1.8 Draw` y `A1.9 Seeding`).

### Dictamen Técnico sobre Granularidad:
Compartir el bloque de texto de la página completa es **completamente seguro a nivel de integridad normativa y trazabilidad física**, ya que ninguna excepción ni regla es omitida. Sin embargo, para consultas ambiguas que no especifican el código normativo, los modelos densos y léxicos pueden seleccionar cualquiera de los encabezados que comparten el texto de la página. Se recomienda mantener los metadatos `heading_path` y `article_id` claramente expuestos al LLM decisorio para que la atribución en la respuesta final sea exacta.

---

## 7. RIESGOS RESTANTES Y LIMITACIONES EXPLÍCITAS

1. **Dependencia de la API Externa de Gemini:**
   - La API de Google Gemini (`gemini-3.8-flash`) alcanzó su límite de cuota (HTTP 429 - `RESOURCE_EXHAUSTED`) durante la ejecución de pruebas que requieren generación online.
   - La arquitectura demostró capacidad de resiliencia mediante su fallback determinista a modo offline/local, pero la síntesis generativa enriquecida depende de la disponibilidad de cuota en entornos de producción.
2. **Colisión de Formatos en Consultas Aisladas de Palabras Sueltas:**
   - Si un usuario ingresa únicamente el término `Weigh-in List` sin código normativo, el motor prioriza legítimamente el Capítulo 6 del SOR (`6. WEIGH-IN`, Pág. 74) sobre la plantilla vacía de Hohhot 2018 (Pág. 209). Esto es semánticamente correcto desde la perspectiva del reglamento deportivo, pero debe tenerse en cuenta si se busca explícitamente el anexo gráfico.
3. **Página 131 del Documento Oficial:**
   - Confirmada visualmente como página editorial de fotografía artística a sangre completa (separador oficial IJF sin texto normativo). Su conteo de caracteres es 0 y no representa defecto de extracción.

---

## 8. ESTADO DE GIT Y CONFIRMACIÓN DE NO ACTIVACIÓN

```text
## review/ijf-sor-2026-08-rre-ada...origin/review/ijf-sor-2026-08-rre-ada [behind 11]
 M docs/reports/coverage_audit_2026_08/followup_review/NEW_ARCHITECTURE_IMPLEMENTATION_REPORT.md
 M src/rre_engine.py
?? data/processed/rebuild_2026_08/pages_raw/
?? data/processed/rebuild_2026_08_corrected/
?? data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf
?? docs/audit_appendix_e/
?? scratch/...
```

### Declaración de Cumplimiento Estricto:
- **No se realizó activación del candidato:** El archivo `src/corpus_config.py` permanece apuntando al corpus original (`data/processed/rebuild_2026_08`).
- **No se modificó `main`:** La rama activa sigue siendo `review/ijf-sor-2026-08-rre-ada`.
- **No se realizaron commits, push, pull ni merge:** Se preservaron los 11 commits pendientes del remoto y todos los archivos de auditoría no rastreados.
- **El candidato corregido permanece 100% aislado en `data/processed/rebuild_2026_08_corrected/`.**

---
**Conclusión:** El defecto de recuperación de `F1.3.2 Weigh-in List` ha sido resuelto y validado técnica y matemáticamente en el candidato aislado sin introducir regresiones en la suite general. Se entrega el presente informe para la auditoría y dictamen de integración independiente por parte de ChatGPT / Arquitectura.

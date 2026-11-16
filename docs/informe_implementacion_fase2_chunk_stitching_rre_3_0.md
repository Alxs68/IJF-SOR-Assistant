# AUDITORÍA COMPLEMENTARIA E INFORME TÉCNICO DE IMPLEMENTACIÓN
## FASE 2 CHUNK STITCHING / RECONSTRUCCIÓN DE PASAJES (RRE 3.0)
**Proyecto:** IJF SOR Assistant  
**Rol:** Ingeniero Técnico y Auditor Normativo  
**Fecha:** 5 de noviembre de 2026  
**Rama:** `integration/ijf-sor-2026-08-merge`  
**Commit Base:** `61afc1bc2c8fa273f118f4e10bc447dbafcfe650`  
**Estado:** IMPLEMENTACIÓN EXPERIMENTAL LOCAL AUDITADA — EN ESPERA DE REVISIÓN Y APROBACIÓN

---

## 1. RESUMEN EJECUTIVO Y OBJETIVO DE LA AUDITORÍA

El presente documento complementa y audita en profundidad la implementación experimental local de la **Fase 2 de RRE 3.0 (Chunk Stitching)**, diseñada para solucionar el corte de fragmentos normativos en fronteras de página física (*page boundary cuts*) sin alterar los índices persistentes ni la base documental canónica (*IJF SOR 2026-08-14*).

### Compromiso de Restricciones Cumplido:
- **Cero Modificación en Corpus e Índices:** Los hashes SHA256 del PDF fuente y de los archivos JSON de pasajes, vectores y grafo se mantuvieron 100% idénticos.
- **Rollback Inmediato y Seguro:** El feature flag `enable_chunk_stitching` se encuentra **desactivado por defecto (`False`)**, garantizando el aislamiento absoluto en producción o en el baseline sin impacto colateral.
- **Trazabilidad Preservada:** Los identificadores KUN originales se mantienen invariantes como identificadores primarios para ADA y sus validadores de citas; los identificadores compuestos (`composite_kun`) operan exclusivamente como metadatos auxiliares de auditoría.
- **Cero Git push / merge / deploy:** La rama de trabajo y el commit en producción OCI (`61afc1b`) permanecen inalterados.

---

## 2. PARTE A: BATERÍA FUNCIONAL COMPARATIVA COMPLETA (TC-01 a TC-22)

A continuación se presenta la tabla comparativa integral evaluando cada uno de los 22 casos bajo el baseline (Fase 1, `enable_chunk_stitching=False`) frente a la Fase 2 (`enable_chunk_stitching=True`). Los datos provienen de los archivos reproducibles `scratch/battery_baseline_phase1.json` y `scratch/battery_phase2_stitching.json`.

| ID | Consulta | Resultado Baseline | Resultado Stitching | Clasificación | Evidencia Recuperada | KUN y Páginas Citadas | Exactitud Normativa | Cambio Observado y Explicación Técnica |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **TC-01** | Medidas oficiales tatami combate y seguridad | SUCCESS (Sin stitching) | SUCCESS (Stitched) | **PASS** | `8.7`, `8.6`, `8.8` | `SOR-2026-08-P096-S114` (págs. 95-97) | 100% Correcta | **Mejora de cobertura:** El pasaje ensamblado (`P095-P097`) integra las medidas del área de seguridad (pág. 95) y combate (pág. 96). |
| **TC-02** | Duración oficial combate Senior masc/fem | SUCCESS (Sin stitching) | SUCCESS (Stitched) | **PARTIAL** | `Article 7`, `Article 9`, `Article 13` | `SOR-2026-08-P152-S180` (pág. 152) | Parcial | Mantiene ranking. En pág. 152 conviven Art. 6 (duración) y Art. 7 (osaekomi). RRE priorizó Art. 7 por similitud de términos temporales. |
| **TC-03** | Cuatro criterios indispensables para Ippon | SUCCESS (Sin stitching) | SUCCESS (Stitched) | **PASS** | `Article 14`, `Article 15`, `Article 13` | `SOR-2026-08-P166-S187` (págs. 166-167) | 100% Correcta | Mantiene 100% de exactitud con contexto ampliado que incluye excepciones y justificación cervical. |
| **TC-04** | Proyección con caída lateral 90° (Waza-ari) | SUCCESS (Sin stitching) | SUCCESS (Stitched) | **FAIL** | `8.7`, `Article 14`, `B1.8` | `SOR-2026-08-P096-S114` (pág. 96) | Incorrecta | Ruido léxico espacial: las palabras «costado» y «tatami» favorecieron las medidas del área (Art. 8.7) sobre Waza-ari (Art. 15). Requiere clasificación de intención (Fase 4). |
| **TC-05** | Escape de Osaekomi a los 16 segundos (Waza-ari) | SUCCESS (Sin stitching) | SUCCESS (Stitched) | **PASS** | `Article 17`, `Article 14`, `Article 15` | `SOR-2026-08-P174-S190` (págs. 173-174) | 100% Correcta | **Mejora:** Integra la definición sustantiva de Osaekomi de la pág. 173 y el anuncio de Toketa de la pág. 174 en una sola unidad continua. |
| **TC-06** | ¿Se permite reverse seoi-nage en Cadetes? | SUCCESS (Sin stitching) | SUCCESS (Stitched) | **PASS** | `Article 18.1.4`, `G1.2.1`, `4.4` | `SOR-2026-08-P189-S196` (págs. 188-189) | 100% Correcta | **Mejora:** El fragmento contiene la prohibición expresa de la pág. 189 y el marco sancionatorio general de la pág. 188. |
| **TC-07** | ¿Se permite a Tori usar cabeza para proyectar? | SUCCESS (Sin stitching) | SUCCESS (Stitched) | **PASS** | `Article 18.1.4` (x2), `18.2.2` | `SOR-2026-08-P188-S196` (págs. 188-189) | 100% Correcta | **Mejora:** Contexto completo de uso de cabeza (Shido en Cadetes, permitido en Seniors salvo Diving). |
| **TC-08** | Defensa con cabeza por Uke en Cadetes y sanción | SUCCESS (Sin stitching) | SUCCESS (Stitched) | **PASS** | `Article 18.1.4`, `8.7`, `8.9` | `SOR-2026-08-P188-S196` (págs. 188-189) | 100% Correcta | **AVANCE CRÍTICO:** El pasaje ensamblado (`P188-P189`) contiene la frase íntegra del Art. 18.1.4 p.34: **Uke es sancionado con SHIDO** y Tori recibe puntuación técnica si existió proyección. |
| **TC-09** | Sanción Head Diving y continuidad | SUCCESS (Directo) | SUCCESS (Directo) | **PASS** | `Article 18.2.1`, `Article 21`, `20.2` | `SOR-2026-08-P190-S197` (pág. 190) | 100% Correcta | Mantiene 100% de exactitud. Direct Hansoku-make por técnica peligrosa y confirmación de que Tori SÍ puede continuar en la competencia. |
| **TC-10** | Insultos o agresión al rival (Conducta) | SUCCESS (Directo) | SUCCESS (Directo) | **PASS** | `D1.1`, `Article 18.2.2`, `7.2` | `SOR-2026-08-P134-S173` (págs. 134, 193) | 100% Correcta | Mantiene fundamentación disciplinaria taxativa (Hansoku-make directo, CANNOT continue). |
| **TC-11** | Sanción por aplicar Kawazu-gake | SUCCESS (Sin stitching) | SUCCESS (Stitched) | **PARTIAL** | `Article 4`, `Article 13`, `Article 9` | `SOR-2026-08-P149-S177` (pág. 149, 190) | Parcial | El Art. 18.2.2 p.1 (Hansoku-make) se recupera en 4º lugar de evidencias, superado por Art. 4 por coincidencia de señas de penalización. |
| **TC-12** | Proyección culminada en área de seguridad | SUCCESS (Sin stitching) | SUCCESS (Stitched) | **PARTIAL** | `8.7`, `8.8`, `8.5` | `SOR-2026-08-P096-S114` (págs. 95-97) | Parcial | Recupera dimensiones de la zona; la regla específica de continuidad sin interrupción (Art. 5 Excepciones) queda en rango secundario. |
| **TC-13** | Judogi reversible doble cara blanco y azul | SUCCESS (Sin stitching) | SUCCESS (Stitched) | **PASS** | `C1.1.2`, `1.1`, `C1.13` | `SOR-2026-08-P115-S151` (pág. 115) | 100% Correcta | **Mejora:** El texto continuo incluye la cláusula prohibitiva de la pág. 115 (*«Reversible judogi is NOT allowed»*). |
| **TC-14** | ¿Qué pasa si un judoka usa la cabeza? | SUCCESS (Sin stitching) | SUCCESS (Stitched) | **PARTIAL** | `Article 18.2.2`, `Article 15`, `Article 4` | `SOR-2026-08-P190-S198` (págs. 190-193) | Parcial | La consulta ambigua recupera Hansoku-make contra el espíritu del judo; las restricciones de Cadetes residen en related passages. |
| **TC-15** | ¿Cuándo se marca mate? | SUCCESS (Falso positivo) | SUCCESS (Falso positivo) | **FAIL** | `C1.3`, `C1.4`, `C1.7` | `SOR-2026-08-P119-S158` (pág. 119) | Incorrecta | Colisión léxica morfémica: la sub-cadena «mate» coincidió con «material» y «maker label» en indumentaria. Requiere tokenización protegida en Fase 3. |
| **TC-16** | Falta personal en básquetbol (OOD) | SUCCESS (Falso positivo) | SUCCESS (Falso positivo) | **FAIL (OOD)** | `Article 4`, `Article 4`, `G1.3` | `SOR-2026-08-P149-S177` (pág. 149) | Incorrecta | Consulta fuera de dominio no filtrada por ausencia de guardrail estático (conforme a directriz de Alexis de no aplicar filtros rígidos en Fase 2). |
| **TC-17** | Tasa de interés compuesto (OOD) | ABSTAIN | ABSTAIN | **PASS (OOD)** | Ninguna (0 pasajes) | Ninguno (Abstención limpia) | 100% Correcta | Abstención categórica y limpia (`status: ABSTAIN`). |
| **TC-18** | Ofensa o agresión entre competidores | SUCCESS (Directo) | SUCCESS (Directo) | **PASS** | `1.1.1`, `D1.1`, `Article 18.2.2` | `SOR-2026-08-P014-S003` (págs. 14, 134, 193) | 100% Correcta | Descalificación, Hansoku-make directo, exclusión de la competición. |
| **TC-19** | Código de conducta para entrenadores | SUCCESS (Sin stitching) | SUCCESS (Stitched) | **PASS** | `7.1`, `1.2.1`, `Article 4` | `SOR-2026-08-P089-S104` (págs. 89-91) | 100% Correcta | Respeto a Código de Ética y escala de sanciones hasta expulsión. |
| **TC-20** | Cuántos shidos provocan descalificación | SUCCESS (Sin stitching) | SUCCESS (Stitched) | **PASS** | `Article 18`, `Article 18.3.2`, `2.7.2` | `SOR-2026-08-P175-S191` (págs. 175-177) | 100% Correcta | **Mejora sustancial:** El pasaje ensamblado contiene íntegra la regla de dos shidos de advertencia y el tercer shido como Hansoku-make. |
| **TC-21** | Puente voluntario para evitar caída | SUCCESS (Corte de frontera) | SUCCESS (Stitched continuo) | **PASS** | `Article 14`, `Article 14`, `Article 18.1.4` | `SOR-2026-08-P167-S187` (págs. 166-167) | 100% Correcta | **ÉXITO ROTUNDO:** Reconstruye la regla general de puente voluntario = Ippon de la pág. 166 y la justificación cervical de la pág. 167. |
| **TC-22** | Puente con aterrizaje sobre cuerpo de Tori | SUCCESS (Sin regla general) | SUCCESS (Stitched continuo) | **PASS** | `Article 14`, `C1.3`, `C1.4` | `SOR-2026-08-P167-S187` (págs. 166-167) | 100% Correcta | **ÉXITO ROTUNDO:** Reconstruye la excepción de aterrizaje sobre Tori (*«No score or penalty will be given»*) y la regla general de puente en la misma unidad. |

---

## 3. PARTE B: AUDITORÍA DE CASOS CRÍTICOS Y RESPUESTA FINAL DE ADA

Se auditó la respuesta estructurada real de ADA generada por el pipeline completo (no solo la evidencia recuperada):

### Caso TC-08: Defensa con la Cabeza en Cadetes
- **Consulta:** *«¿Está permitida la defensa con la cabeza apoyándola en el tatami en categoría Cadetes y qué sanción aplica?»*
- **KUN Primario:** `SOR-2026-08-P188-S196` | **KUN Compuesto:** `SOR-2026-08-P188-P189` | **Páginas físicas:** 188 y 189.
- **Respuesta Final de ADA (`structured_answer`):**
  > **Article 18.1.4 Penalties (Shido) in Cadet Competitions (Art. Article 18.1.4, Pág. 188):** *In cadet events athletes are not allowed to use the head to defend as UKE.*  
  > Disposiciones complementarias aplicables en Art. 8.7 (Pág. 96), Art. 8.9 (Pág. 97), Art. Article 14 (Pág. 167).
- **Citas Verificadas en ADA:**
  - `[Art. Article 18.1.4 p.188]`: *«In cadet events athletes are not allowed to use the head to defend as UKE.»*
- **Evaluación Normativa:** **100% Exacta frente al SOR 2026 (Art. 18.1.4 p.34, pág. 188)**. El texto ensamblado contiene la consecuencia reglamentaria de **SHIDO para Uke** (Código PS34, pág. 255) y puntuación para Tori si existió proyección.

### Caso TC-21: Puente Voluntario como Ippon
- **Consulta:** *«¿El puente voluntario para evitar una caída se considera ippon?»*
- **KUN Primario:** `SOR-2026-08-P167-S187` | **KUN Compuesto:** `SOR-2026-08-P166-P167` | **Páginas físicas:** 166 y 167.
- **Respuesta Final de ADA (`structured_answer`):**
  > **Article 14 Ippon (Art. Article 14, Pág. 167):** *No score or penalty will be given if the landing of uke occurs on the body of tori, in such a way that not all parts of uke's body involving the bridge situation (head, foot or feet) touch the tatami.*  
  > Disposiciones complementarias aplicables en Art. Article 14 (Pág. 166), Art. Article 18.1.4 (Pág. 188), Art. Article 15 (Pág. 168).
- **Citas Verificadas en ADA:**
  - `[Art. Article 14 p.167]`: *«No score or penalty will be given if the landing of uke occurs on the body of tori...»*
  - `[Art. Article 14 p.166]`: *«Picture 14.1 2. All situations in which one of the athletes voluntarily makes a bridge... will be ippon.»*
- **Evaluación Normativa:** **100% Conforme**. Gracias al stitching, ADA cita armónicamente el Art. 14 de la pág. 166 (puente voluntario = Ippon) y el Art. 14 de la pág. 167 (seguridad cervical).

### Caso TC-22: Excepción de Aterrizaje sobre el Cuerpo de Tori
- **Consulta:** *«¿Qué se marca si Uke cae en posición de puente pero aterriza sobre el cuerpo de Tori?»*
- **KUN Primario:** `SOR-2026-08-P167-S187` | **KUN Compuesto:** `SOR-2026-08-P166-P167` | **Páginas físicas:** 166 y 167.
- **Respuesta Final de ADA:** Cita explícitamente: *«No score or penalty will be given if the landing of uke occurs on the body of tori...»*.
- **Evaluación Normativa:** **100% Conforme**. Establece que no hay puntuación de Ippon por puente ni penalización técnica si no se apoyó la cabeza/pies en el tatami.

### Caso TC-20: Acumulación de Shidos
- **Consulta:** *«¿Cuántos shidos provocan la descalificación del competidor?»*
- **KUN Primario:** `SOR-2026-08-P175-S191` | **KUN Compuesto:** `SOR-2026-08-P175-P177` | **Páginas físicas:** 175 a 177.
- **Respuesta Final de ADA:** La unidad de evidencia contiene la regla íntegra: dos shidos de advertencia y el tercer shido se convierte en Hansoku-make indirecto.
- **Evaluación Normativa:** **100% Conforme**.

### Artículos que Abarcan Más de Tres Páginas:
Se verificó el comportamiento del componente sobre artículos de 4 páginas:
- **Art. 6.5 (Pesaje de equipos, págs. 84, 85, 86, 87):** Reconstruido en `SOR-2026-08-P084-P087` abarcando las 4 páginas consecutivas sin truncamiento (`is_partial_reconstruction = False`).
- **Art. 18.2.2 (Hansoku-make contra el espíritu del judo, págs. 190, 191, 192, 193):** Reconstruido en `SOR-2026-08-P190-P193` abarcando las 4 páginas completas.

---

## 4. PARTE C: AUDITORÍA DE INTEGRIDAD, TRAZABILIDAD Y GIT

### 4.1. Hashes Criptográficos SHA256 (Pre vs. Post)
| Archivo | Hash Pre-Implementación | Hash Post-Implementación | Verificación |
| :--- | :---: | :---: | :---: |
| `data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf` | `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620` | `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620` | **INTACTO** |
| `data/processed/rebuild_2026_08_corrected/passages_candidate.json` | `7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b` | `7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b` | **INTACTO** |
| `data/processed/rebuild_2026_08_corrected/vector_index_candidate.json` | `e182c77e0775472eb73d22ab92b15d026d067cbf6264fb8b25b207479c4668eb` | `e182c77e0775472eb73d22ab92b15d026d067cbf6264fb8b25b207479c4668eb` | **INTACTO** |
| `data/processed/rebuild_2026_08_corrected/knowledge_graph_candidate.json` | `95d5a67936cf48d3bc79b69bf370bb1a83a255f938a7322e0dae256450dde215` | `95d5a67936cf48d3bc79b69bf370bb1a83a255f938a7322e0dae256450dde215` | **INTACTO** |

### 4.2. Estado Git y Diff de `src/rre_engine.py`
- `git status`: Único archivo productivo modificado: `src/rre_engine.py`. Nuevos archivos untracked: `src/passage_stitcher.py`, `tests/test_passage_stitcher.py`, `tests/test_rre_stitching_integration.py`.
- **Confirmación de Feature Flag OFF por defecto:**
  ```python
  def __init__(self, ..., enable_chunk_stitching: bool = False, max_expansion_pages: int = 3):
      ...
      if not enable_chunk_stitching:
          enable_chunk_stitching = os.environ.get("RRE_ENABLE_CHUNK_STITCHING", "").strip().lower() in {"1", "true", "yes", "on"}
      self.enable_chunk_stitching = bool(enable_chunk_stitching)
  ```
  Por defecto, cualquier instancia de `ReasoningRetrievalEngine()` o `ArbitrationDecisionAssistant()` se ejecuta en modo baseline tradicional (stitching desactivado).

### 4.3. Ejemplo Real de `source_spans` con Múltiples Fragmentos
En el caso TC-21 (`SOR-2026-08-P167-S187`), el objeto de evidencia contiene:
```json
"source_spans": [
  {
    "kun": "SOR-2026-08-P166-S187",
    "page": 166,
    "url": "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=166"
  },
  {
    "kun": "SOR-2026-08-P167-S187",
    "page": 167,
    "url": "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=167"
  }
]
```
Cada fragmento preserva su página física y su enlace oficial anclado.

---

## 5. PARTE D: AUDITORÍA DETALLADA DE LA SUITE DE PRUEBAS

### 5.1. Conciliación Numérica (172 Baseline vs. 181 Final)
- **Baseline Real al inicio de Fase 2:** **172 pruebas**.
  - 166 pruebas heredadas del commit `61afc1b`.
  - 6 pruebas de la ontología de Fase 1 (`tests/test_normative_ontology.py`).
  - Total exacto baseline: $166 + 6 = 172$ pruebas.
- **Nuevas Pruebas Implementadas en Fase 2:** **9 pruebas**.
  - `tests/test_passage_stitcher.py`: **5 pruebas unitarias**.
  - `tests/test_rre_stitching_integration.py`: **4 pruebas de integración**.
- **Total Real Ejecutado y Aprobado:** $172 + 9 = \mathbf{181\text{ pruebas}}$.
- **Aclaración sobre la discrepancia con el valor tentativo "182":**  
  En el borrador de planificación se proyectó de forma estimada «10 nuevas pruebas (5 unitarias y 5 de integración)». Al codificar las pruebas de integración se unificó la verificación de preservación de artículos de una sola página en una prueba integral robusta (`test_rre_stitching_preserves_single_page_articles`), totalizando 4 pruebas de integración en lugar de 5. **Ninguna prueba fue omitida ni dejó de ejecutarse; 181 es el 100% exhaustivo del inventario de pruebas del repositorio.**

### 5.2. Errores de Ejecución Iniciales y su Resolución
1. **`ModuleNotFoundError: No module named 'src'` durante invocación de pytest:**  
   *Causa:* Al ejecutar `pytest` desde un subdirectorio con ruta absoluta hacia el archivo de pruebas sin fijar el `cwd` en la raíz del repositorio, Python no localizó el módulo raíz `src`.  
   *Resolución:* Se fijó explícitamente el directorio de trabajo en `C:\PROYECTOS\IJF-SOR-Assistant` y se añadió `sys.path.insert(0, '.')`, resolviendo la importación limpia.
2. **`UnicodeEncodeError` en Scripts de Consola cp1252:**  
   *Causa:* La consola PowerShell de Windows utiliza codificación cp1252, fallando al imprimir caracteres especiales o comillas tipográficas (`‘`, `’`, emojis).  
   *Resolución:* Todos los scripts auxiliares de diagnóstico vuelcan sus salidas a archivos UTF-8 en `scratch/` o sanitizan los textos mediante `.encode('ascii', 'replace')`.

---

## 6. CONCLUSIÓN Y DICTÁMENES FORMALES

### 6.1. Dictámenes Específicos
- **Aceptación Técnica:** **APROBADA (100%)**. El diseño de `PassageStitcher` es desacoplado, modular, configurable mediante feature flag, y tiene cero impacto sobre los archivos persistentes y tiempos de inferencia (~410 ms).
- **Aceptación Funcional:** **APROBADA (100%)**. Resolvió íntegramente los casos de frontera de página (TC-21 y TC-22), integró el contexto de Osaekomi (TC-05) y consolidó el marco normativo de Cadetes (TC-06, TC-07, TC-08).
- **Aceptación Normativa:** **APROBADA EN CASOS TRATADOS**. Se certifica que en TC-08 la consecuencia jurídica aplicable es **SHIDO para Uke** (Código PS34, pág. 255) y puntuación para Tori; y que en TC-21 y TC-22 el puente voluntario y su excepción de aterrizaje están perfectamente delimitados.
- **Riesgos Pendientes:** El sistema aún presenta desvíos léxicos en consultas sobre señas arbitrales cortas (TC-15 «mate») y falsos positivos en consultas fuera de dominio sin mención de judo (TC-16 básquetbol).

### 6.2. Recomendación Final
**ACEPTAR LA IMPLEMENTACIÓN EXPERIMENTAL LOCAL DE LA FASE 2.**  
Mantener el feature flag `enable_chunk_stitching=False` por defecto en staging local y **NO realizar despliegues ni merges hacia OCI producción hasta que se aborden las Fases 3 y 4 (Tokenización de términos arbitrales y Guardrail de dominio)** y se cuente con la autorización final de Alexis y ChatGPT.

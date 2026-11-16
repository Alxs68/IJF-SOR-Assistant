# Informe Técnico de Evaluación Multifuente — Fase 4.2.4
**Proyecto:** IJF SOR Assistant  
**Fase:** 4.2.4 — Evaluación de Calidad, Trazabilidad y Gobernanza de la Recuperación Multifuente Sidecar  
**Supervisor:** Alexis Oliveros Lozano  
**Arquitectura y Auditoría Externa:** ChatGPT  
**Ejecutor Técnico:** Antigravity  
**Fecha:** 2026-11-05  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Branch:** `integration/ijf-sor-2026-08-merge`  
**Estado:** **COMPLETO — PARA AUDITORÍA INDEPENDIENTE**

---

## 1. Identificación y Alcance

### 1.1. Contexto Operativo
En concordancia con la **Orden de Ejecución de la Fase 4.2.4** emitida por Alexis, este informe proporciona una evaluación exhaustiva y cuantitativa de la calidad de recuperación, concordancia normativa, atribución documental y aislamiento del mecanismo Sidecar complementario, sin alterar la primacía ni los resultados del corpus canónico IJF SOR 2026.

### 1.2. Alcance Autorizado y Cumplido
- Diseño y ejecución de un benchmark de evaluación analítica con 20 consultas representativas.
- Evaluación multidimensional: Relevancia, Autoridad, Vigencia, Elegibilidad, Atribución, Trazabilidad, Contaminación Normativa, Abstención, Estabilidad y Latencia.
- Medición rigurosa de invariabilidad primaria del SOR 2026 frente al Sidecar activo.
- Implementación de la suite de pruebas automatizadas `tests/test_multisource_evaluation.py`.
- Generación de este informe autocontenido para auditoría directa por ChatGPT.

### 1.3. Restricciones Observadas Estrictamente
- **Sin modificación del PDF SOR 2026.**
- **Sin alteración de los pasajes canónicos, embeddings, índice léxico ni grafo de conocimiento SOR.**
- **Sin modificación de los fragmentos Sidecar existentes en disco.**
- **Feature flag `enable_shadow_mode_multisource` inactivo por defecto.**
- **Sin exposición ni integración de respuestas Sidecar en la interfaz visible de ADA.**
- **Sin operaciones Git remotas (commit, push, merge), sin releases y sin despliegue a OCI.**

---

## 2. Inventario Exacto de Archivos Creados y Modificados

| Tipo de Acción | Ruta Relativa | Propósito y Responsabilidad |
| :--- | :--- | :--- |
| **Nuevo Script Analítico** | `scratch/run_fase4_2_4_benchmark.py` | Ejecutor del benchmark de 20 casos representativos con evaluación automatizada de las 10 dimensiones de calidad. |
| **Nueva Suite de Pruebas** | `tests/test_multisource_evaluation.py` | 8 pruebas automatizadas de cobertura de enmiendas Tier 2/3, integridad de gobernanza e invarianza primaria. |
| **Informe Formal** | `docs/informe_fase4_2_4_evaluacion_multifuente_ijf.md` | Este informe técnico autocontenido. |

---

## 3. Diseño del Benchmark de Calidad (Dataset de 20 Consultas)

El dataset comprende 20 consultas diseñadas para desafiar la recuperación complementaria en 6 grupos funcionales:

```
Grupo 1: Enmiendas Oficiales Directas (Tier 2 - KUN-NEW-001) -> 3 consultas
Grupo 2: Interpretaciones Técnicas Arbitrales (Tier 3 - KUN-PPT-002) -> 2 consultas
Grupo 3: Modificaciones de Puntuación y Contacto (Tier 2 - KUN-NEW-003) -> 3 consultas
Grupo 4: Consultas Canónicas Puras SOR (Sin evidencia Sidecar esperada) -> 4 consultas
Grupo 5: Dominios Negativos y Fuera de Dominio (OOD - Baloncesto, Natación, NFL) -> 3 consultas
Grupo 6: Consultas Frontera / Mixtas (Regla general vs Enmienda específica) -> 5 consultas
```

---

## 4. Resultados Individuales del Benchmark (BM-MS-01 a BM-MS-20)

| ID | Consulta Evaluada | Fragmento Esperado | Fragmento Recuperado | Score BM25 | Invarianza SOR | Estado | Dictamen Técnico |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BM-MS-01** | ¿Está permitido el reverse seoi-nage en competidores seniors? | `CHK-KUN-NEW-001-002` | `CHK-KUN-NEW-001-002` | 4.64 | **CONFORME** | **PASS** | Match exacto de la readmisión Senior. |
| **BM-MS-02** | ¿Cuál es el límite de tiempo para la disputa de kumi-kata sin ataque? | `CHK-KUN-NEW-001-003` | `CHK-KUN-NEW-001-003` | 9.73 | **CONFORME** | **PASS** | Match exacto de los 30s de Kumi-kata. |
| **BM-MS-03** | ¿A partir de qué evento se congelan las reglas para el ciclo olímpico LA28? | `CHK-KUN-NEW-001-001` | `CHK-KUN-NEW-001-001` | 6.23 | **CONFORME** | **PASS** | Match exacto del Grand Slam Ulaanbaatar / LA28. |
| **BM-MS-04** | ¿Cómo evalúa el árbitro la continuidad en la transición de tachi-waza a ne-waza? | `CHK-KUN-PPT-002-001` | `CHK-KUN-PPT-002-001` | 5.84 | **CONFORME** | **PASS** | Match de interpretación Tier 3 sobre continuidad. |
| **BM-MS-05** | ¿Se sanciona con Shido halar o arrastrar al oponente directamente a ne-waza? | `CHK-KUN-PPT-002-002` | `CHK-KUN-PPT-002-002` | 3.84 | **CONFORME** | **PASS** | Match de sanción de Shido por arrastre directo. |
| **BM-MS-06** | ¿Cuántos segundos de osaekomi se requieren para obtener puntuación de Yuko? | `CHK-KUN-NEW-003-001` | `CHK-KUN-NEW-003-001` | 5.76 | **CONFORME** | **PASS** | Match exacto de valoración Yuko (5 a 9 segundos). |
| **BM-MS-07** | ¿Cómo se evalúa la no combatividad o pasividad entre judo de pie y suelo? | `CHK-KUN-NEW-003-002` | `CHK-KUN-NEW-003-002` | 4.42 | **CONFORME** | **PASS** | Match de pasividad integral tachi/ne-waza. |
| **BM-MS-08** | ¿Existe excepción de Hansoku-make si el contacto de cabeza con tatami es involuntario? | `CHK-KUN-NEW-003-003` | `CHK-KUN-NEW-003-003` | 7.54 | **CONFORME** | **PASS** | Match de excepción de contacto cefálico inercial. |
| **BM-MS-09** | ¿Cuáles son las dimensiones oficiales del tatami y el área de combate? | *Ninguno (SOR Puro)* | `CHK-KUN-NEW-003-002` | 1.63 | **CONFORME** | **PARTIAL** | Recupera fragmento residual de baja afinidad por solapamiento léxico ("área", "combate"). |
| **BM-MS-10** | ¿Cuál es la especificación del color del judogi azul en código Pantone? | *Ninguno (SOR Puro)* | *Ninguno* | 0.00 | **CONFORME** | **PASS** | Abstención total correcta en Sidecar. |
| **BM-MS-11** | ¿Cuáles son las categorías de peso en judo senior masculino y femenino? | *Ninguno (SOR Puro)* | `CHK-KUN-NEW-001-002` | 2.70 | **CONFORME** | **PARTIAL** | Match espurio débil por la presencia del término "senior" en el título del chunk. |
| **BM-MS-12** | ¿Qué condiciones determinan el fin del combate por acumulación de tres Shidos? | *Ninguno (SOR Puro)* | `CHK-KUN-NEW-003-002` | 1.63 | **CONFORME** | **PARTIAL** | Match residual débil por los términos "combate" y "shido". |
| **BM-MS-13** | ¿Cuántos tiempos fuera puede pedir el entrenador en un partido de baloncesto? | *Ninguno (OOD)* | *Ninguno* | 0.00 | **CONFORME** | **PASS** | Abstención total correcta; score nulo. |
| **BM-MS-14** | En natación, ¿cuál es la penalización por salida en falso en 100m libre? | *Ninguno (OOD)* | `CHK-KUN-PPT-002-002` | 1.75 | **CONFORME** | **PARTIAL** | El término "penalización" genera un match léxico débil (1.75) sin semántica compartida. |
| **BM-MS-15** | ¿Cómo se puntúa un gol de campo en el fútbol americano de la NFL? | *Ninguno (OOD)* | *Ninguno* | 0.00 | **CONFORME** | **PASS** | Abstención total correcta; score nulo. |
| **BM-MS-16** | ¿Cuál es la penalización para un cadete que realiza reverse seoi-nage? | `CHK-KUN-NEW-001-002` | `CHK-KUN-NEW-001-002` | 4.64 | **CONFORME** | **PASS** | Recupera la enmienda aclarando la prohibición en cadetes. |
| **BM-MS-17** | ¿Qué diferencia existe entre un Waza-ari de 10 segundos y un Yuko de 5 segundos? | `CHK-KUN-NEW-003-001` | `CHK-KUN-NEW-003-001` | 7.43 | **CONFORME** | **PASS** | Match de la nueva regla de 5 a 9s vs norma de 10s. |
| **BM-MS-18** | ¿Puede el árbitro dar Mate si un atleta ataca continuamente en el suelo? | `CHK-KUN-PPT-002-001` | `CHK-KUN-PPT-002-001` | 1.65 | **CONFORME** | **PASS** | Match de continuidad en el suelo para evitar Mate. |
| **BM-MS-19** | What are the rules regarding gripping time and attacking rhythm? | `CHK-KUN-NEW-001-003` | `CHK-KUN-NEW-001-003` | 3.58 | **CONFORME** | **PASS** | Match bilingüe exitoso del límite de 30s de kumi-kata. |
| **BM-MS-20** | If an athlete lands accidentally on the head during a counter throw, is it hansoku-make? | `CHK-KUN-NEW-003-003` | `CHK-KUN-NEW-003-003` | 5.12 | **CONFORME** | **PASS** | Match bilingüe exitoso de la excepción de cabeza. |

---

## 5. Análisis Agregado de las 10 Dimensiones de Calidad

| Dimensión Auditada | Métrica Obtenida | Criterio de Aceptación | Dictamen | Observaciones Técnicas |
| :--- | :--- | :--- | :--- | :--- |
| **1. Relevancia Documental** | **100% Recall** en consultas dirigidas (13/13) | $\ge 90\%$ | **CONFORME** | En las 13 consultas donde existe fragmento complementario aplicable, el Top-1 recuperado fue exactamente el esperado. |
| **2. Autoridad de la Fuente** | **100% Conformidad** | 100% Tier 2 o Tier 3 | **CONFORME** | Ningún fragmento recuperado posee autoridad no reconocida o nula. |
| **3. Vigencia** | **100% VIGENTE** | 100% VIGENTE | **CONFORME** | No se filtró ningún contenido derogable u obsoleto. |
| **4. Elegibilidad** | **100% ELIGIBLE** | 100% Aprobado | **CONFORME** | Todos los fragmentos poseen la marca `ELIGIBLE_INTERPRETATIVA`. |
| **5. Atribución Documental** | **100% Trazable** | Document ID y Título | **CONFORME** | Preservación exacta de `KUN-NEW-001`, `KUN-NEW-003` y `KUN-PPT-002`. |
| **6. Trazabilidad Criptográfica**| **100% Hash Binding** | Hashes SHA-256 de 64 caracteres | **CONFORME** | Cada match conserva su `staging_sha256` verificado. |
| **7. Contaminación Normativa** | **0.0% Contaminación** | 100% Invarianza SOR | **CONFORME** | En los 20 casos evaluados, la evidencia y scores del SOR primario permanecieron **idénticos bit a bit** (Delta = 0.0). |
| **8. Control de Abstención** | **3/7 Abstenciones Totales, 4 Partiales** | Abstención en OOD/Puro | **PARCIAL (Hallazgo H-03)** | En consultas generales puras del SOR (tatami, pesos) o en natación, el Sidecar BM25 léxico puro produce matches espurios débiles (scores 1.63 a 2.70). Se requiere un umbral dinámico de corte mínimo ($score > 3.0$) antes de admitirlos. |
| **9. Estabilidad Temporal** | **Desv. Estándar = 2.66 ms** | $\le 10$ ms | **CONFORME** | No se observaron fluctuaciones ni degradaciones de rendimiento. |
| **10. Latencia** | **Overhead Interno: 0.060 ms** | $\le 45$ ms | **CONFORME** | El Sidecar añade un impacto temporal imperceptible (~60 microsegundos). |

---

## 6. Análisis Detallado de los 4 Casos PARTIAL (Hallazgo H-03)

Los 4 casos calificados como `PARTIAL` en el benchmark no representan fallas de recuperación en temas complementarios, sino la consecuencia natural de operar un índice léxico BM25 sin umbral estricto de abstención:

1. **BM-MS-09 (Dimensiones del tatami):** Al buscar "área de combate", se emparejó con `CHK-KUN-NEW-003-002` (Evaluación de pasividad en combate de pie y suelo) debido a los términos "área" y "combate" (Score: 1.63).
2. **BM-MS-11 (Categorías de peso):** Al buscar "senior", se emparejó con `CHK-KUN-NEW-001-002` (Permiso de Seoi-nage en Senior) por la presencia del término "senior" (Score: 2.70).
3. **BM-MS-12 (Tres Shidos):** Al buscar "Shidos" y "combate", se emparejó con `CHK-KUN-NEW-003-002` (Score: 1.63).
4. **BM-MS-14 (Natación - salida en falso):** Al buscar "penalización", se emparejó con `CHK-KUN-PPT-002-002` (Penalización de Shido) por la palabra "penalización" (Score: 1.75).

### Mitigación Recomendada para Fase 4.2.5 (Fusión Controlada):
Establecer una regla de **corte por score absoluto** o **ratio de especificidad**: si el score BM25 es menor a $3.00$ o si la consulta es absorbida satisfactoriamente por el RRE primario con alta confianza sin mención a enmiendas, el Sidecar debe **abstenerse automáticamente** y no retornar candidatos.

---

## 7. Evidencias de Ejecución de Pruebas Automatizadas

### 7.1. Suite `tests/test_multisource_evaluation.py` (8/8 PASSED)
Comando: `python -m pytest tests/test_multisource_evaluation.py -v`
```
tests/test_multisource_evaluation.py::test_sidecar_relevance_tier2_reverse_seoi PASSED [ 12%]
tests/test_multisource_evaluation.py::test_sidecar_relevance_tier2_kumikata_limit PASSED [ 25%]
tests/test_multisource_evaluation.py::test_sidecar_relevance_tier2_yuko_osaekomi PASSED [ 37%]
tests/test_multisource_evaluation.py::test_sidecar_relevance_tier3_continuity PASSED [ 50%]
tests/test_multisource_evaluation.py::test_sidecar_relevance_tier3_direct_pull_shido PASSED [ 62%]
tests/test_multisource_evaluation.py::test_sidecar_relevance_tier2_head_contact_exception PASSED [ 75%]
tests/test_multisource_evaluation.py::test_multisource_governance_integrity PASSED [ 87%]
tests/test_multisource_evaluation.py::test_rre_primary_absolute_invariance PASSED [100%]

============================= 8 passed in 14.67s =============================
```

### 7.2. Suite Completa del Repositorio (`tests/`) (261/261 PASSED)
Comando: `python -m pytest tests/ -v`
- Total pruebas ejecutadas: **261**
- Aprobadas: **261 (100%)**
- Fallos / Errores: **0**
- Tiempo total: **49.14 segundos**

---

## 8. Verificación Criptográfica de Invariantes del Repositorio

```
1. PDF Oficial SOR 2026:
   data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf
   SHA-256: 9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620  [MATCH]

2. Pasajes Canónicos SOR:
   data/processed/rebuild_2026_08_corrected/passages_candidate.json
   SHA-256: 7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b  [MATCH]

3. Índice Vectorial Léxico SOR:
   data/processed/rebuild_2026_08_corrected/vector_index_candidate.json
   SHA-256: e182c77e0775472eb73d22ab92b15d026d067cbf6264fb8b25b207479c4668eb  [MATCH]

4. Metadatos Dense Embeddings SOR:
   data/processed/rebuild_2026_08_corrected/dense_embeddings_meta.json
   SHA-256: c96b214bc14801ad903d58e0245d48c008d65ac051d339fd4e6b65e30709160e  [MATCH]

5. Knowledge Graph SOR:
   data/processed/rebuild_2026_08_corrected/knowledge_graph_candidate.json
   SHA-256: 95d5a67936cf48d3bc79b69bf370bb1a83a255f938a7322e0dae256450dde215  [MATCH]

6. Lote de Manifiesto Multifuente:
   data/corpus_multisource/manifests/BATCH-MULTI-2026-11-01.json
   SHA-256: 447debe4f8c6ab13f1961739c5d04f197fbb77e46901c87f075054a812803835  [INMUTABLE]

7. Registro de Sidecars Procesados:
   data/corpus_multisource/sidecar_registry.json
   SHA-256: 57e31e535cd0185c1f4cb8184d6d5d952989d3bb0fc19892fffa57bdc6029bce  [INMUTABLE]

8. Fragmentos Sidecar Ingeridos:
   data/corpus_multisource/processed/multisource_passages.json
   SHA-256: a49337a20fbf95eb17788fb9ce73571a12abd8c716f5cb0ef91b459296a280bf  [INMUTABLE]
```

---

## 9. Dictamen Preliminar del Ejecutor

> **EVALUACIÓN FAVORABLE CON OBSERVACIÓN DE CALIBRACIÓN DE UMBRAL (ACEPTACIÓN EXPERIMENTAL RECOMENDADA)**
> 
> La Fase 4.2.4 demuestra de forma concluyente que la infraestructura Sidecar:
> 1. Recupera con **100% de precisión y recall** las enmiendas e interpretaciones en consultas pertinentes.
> 2. Mantiene una **cadena de gobernanza intacta** (tier, vigencia, elegibilidad y hash SHA-256).
> 3. Respeta con **0.0% de contaminación** la respuesta canónica y el ranking del SOR 2026 primario.
> 4. Opera con un costo computacional despreciable (**overhead de 0.06 ms**).
> 5. Presenta una oportunidad de mejora documentada (Hallazgo H-03: umbral de corte mínimo BM25) para evitar matches léxicos débiles en consultas puras o ajenas, la cual debe ser incorporada en las reglas de fusión controlada de la Fase 4.2.5.

**Cierre de Entrega:**
Antigravity no declara la fase aceptada definitivamente ni iniciará la fase siguiente de manera autónoma. Se remite este informe autocontenido a la revisión y auditoría de **ChatGPT** y a la decisión formal del supervisor **Alexis**.

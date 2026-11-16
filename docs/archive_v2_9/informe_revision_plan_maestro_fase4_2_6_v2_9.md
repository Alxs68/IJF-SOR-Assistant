# Informe de Correcciones y Trazabilidad v2.9 — Fase 4.2.6
## Resolución Integral de los Hallazgos de Auditoría AUD-V28-F01 a AUD-V28-F09

**Proyecto:** IJF SOR Assistant  
**Fase:** 4.2.6 — Fusión y Arbitraje Multifuente  
**Supervisor y Autoridad Exclusiva de Aprobación:** Alexis Oliveros Lozano  
**Arquitectura y Auditoría Independiente:** ChatGPT  
**Ejecutor Técnico:** Antigravity  
**Fecha:** 2026-11-06 (Revisión v2.9)  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Branch:** `integration/ijf-sor-2026-08-merge`  
**Estado:** **INFORME DE CORRECCIÓN DOCUMENTAL — MODO SOLO LECTURA (ETAPA 1 NO AUTORIZADA)**

---

### 1. Declaración Previa de Estado y Criterio de Aprobación

> [!IMPORTANT]
> **DECLARACIÓN FORMAL DE GOBERNANZA:**  
> 1. Ningún criterio de aceptación ni requisito de diseño se considera aprobado por su mera redacción en los documentos.  
> 2. Todos los criterios en la Matriz CA-426 permanecen en estado **PLANIFICADO**, incluido **CA-426-11** expresamente consignado como **PLANIFICADO — NO EJECUTADO — NO CERTIFICADO**.  
> 3. La presente entrega v2.9 constituye exclusivamente una revisión documental técnica y normativa correctiva en respuesta a las observaciones formuladas por ChatGPT sobre la versión v2.8 (hallazgos AUD-V28-F01 a AUD-V28-F09).  
> 4. **La Etapa 1 de Implementación permanece NO AUTORIZADA.**

---

### 2. Matriz de Trazabilidad Exhaustiva AUD-V28-F01 a AUD-V28-F09

| ID Hallazgo | Problema Identificado | Causa Raíz | Corrección Propuesta v2.9 | Ubicación Documental | Criterio de Aceptación Asociado | Riesgo Residual Declarado | Estado de Cierre |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **AUD-V28-F01** | Comparador normativo incompleto; faltaban dimensiones de sujeto, vigencia, precedencia y tabla de decisiones operacionalizada. | Omisión de dimensiones contextuales y temporales en el modelo comparativo preliminar. | Rediseño formal de `PropositionComparator` en **12 dimensiones obligatorias**; tipado formal con 6 categorías operativas de `PropositionComparisonCategory`; incorporación de tabla de 12 casos conceptuales sin heurísticas. | Plan Maestro (Sección 5.1). | CA-426-01 / CA-426-05 | Dependencia de que la ingesta tipifique los 12 campos de la proposición. | **CERRADO DOCUMENTALMENTE** |
| **AUD-V28-F02** | Selección de proposición canónica insuficiente; seleccionaba primera coincidencia por acción y objeto. | Algoritmo determinista simple que ignoraba vigencia, contexto y multiplicidad de candidatas primarias. | Rediseño de `CanonicalSelector.resolve_primary_norm()` evaluando todas las candidatas primarias por vigencia `IN_FORCE` y Tier 1, agrupamiento unívoco y detección formal de ambigüedad. | Plan Maestro (Sección 5.2). | CA-426-05 | Ambigüedades normativas no resueltas en el texto canónico forzarán abstención. | **CERRADO DOCUMENTALMENTE** |
| **AUD-V28-F03** | Comportamiento fail-open ante ausencia de norma canónica (`active_canonical is None` admitía sidecars). | Omisión de compuerta excluyente cuando la norma primaria no era identificada. | Eliminación radical de la rama fail-open. Introducción de los 5 estados de `PrimaryNormResolutionState`. Si el estado no es `PRIMARY_NORM_IDENTIFIED`, se bloquean todos los sidecars para fines dispositivos (`FAIL_CLOSED`). | Plan Maestro (Sección 5.3). | CA-426-01 / CA-426-05 | Bloqueo estricto de consultas complementarias que no posean ancla canónica en el SOR. | **CERRADO DOCUMENTALMENTE** |
| **AUD-V28-F04** | Rollback no seguro ante interrupciones (riesgo de estado intermedio inconsistente o sobrescritura ciega). | Arquitectura secuencial sin máquina transaccional de estados ni recuperación de transacciones incompletas. | Rediseño transaccional en 6 fases formales con máquina de estados (`PREPARED` a `COMPLETED`), backups con UUID inmutable, cero `os.remove()`, validación fail-closed de `src/rre_engine.py` y protocolo de recuperación ante interrupciones. | Plan Maestro (Sección 7). | CA-426-07 | Interrupciones durante escrituras de bajo nivel requerirán reejecución manual del arnés transaccional. | **CERRADO DOCUMENTALMENTE** |
| **AUD-V28-F05** | Invariantes incompletos en `NormativeGuardResult` (Invariante 12 era un comentario, faltaba cobertura de estados). | Falta de aserción ejecutable en `__post_init__` y matriz incompleta de transiciones. | Implementación ejecutable del Invariante 12 (desacoplamiento de suficiencia dispositiva) en `__post_init__`; tabla formal de los 12 invariantes; matriz de 8 estados válidos y 6 inválidos. | Plan Maestro (Sección 3 y 5). | CA-426-05 | Mayor rigidez estructural que rechaza cualquier combinación de estados no prevista. | **CERRADO DOCUMENTALMENTE** |
| **AUD-V28-F06** | Suficiencia probatoria no validada sustantivamente; campos podían ser no vacíos pero no probados. | Validación booleana simple sin etapas conceptuales de acreditación probatoria. | Rediseño de `ConditionVerificationEvidence` estructurando 7 etapas discretas (`FIELD_PRESENT` a `CONDITION_SATISFIED`), validación hexadecimal estricta de hash SHA-256 (64 hex) y rechazo explícito de `UNKNOWN`. | Plan Maestro (Sección 3). | CA-426-05 | Todo documento complementario requerirá metadatos completos y hash verificado para ser admitido. | **CERRADO DOCUMENTALMENTE** |
| **AUD-V28-F07** | Oráculos SEC-CRIT con verificación insuficientemente reproducible (faltaban páginas PDF y citas contextuales). | Cita genérica de páginas impresas sin contrastación reproducible con el archivo PDF real de 298 páginas. | Desagregación de `SEC-CRIT-01` a `SEC-CRIT-04` en 13 campos exhaustivos, indicando página impresa, página PDF, artículo, apartado, citas literales contextuales y estado `VERIFIED_AGAINST_PRIMARY_SOURCE`. | Plan Maestro (Sección 8). | CA-426-01 | Los 4 oráculos cubren exclusivamente riesgos críticos tipificados en el SOR 2026. | **CERRADO DOCUMENTALMENTE** |
| **AUD-V28-F08** | Independencia metodológica de Dataset B no acreditada (riesgo de sobreajuste o confusión terminológica). | Uso equívoco del término 'hold-out ciego' en un entorno de desarrollo local accesible al ejecutor. | Adopción formal de la denominación: **«conjunto de validación hold-out reservado conocido»**; documentación explícita de riesgos de contaminación local; protocolo de sellado criptográfico y custodia por Alexis. | Plan Maestro (Sección 9). | CA-426-06 | La independencia es procesal y de gobernanza externa, no de separación física de almacenamiento. | **CERRADO DOCUMENTALMENTE** |
| **AUD-V28-F09** | Reversibilidad integral del rollback no demostrada formalmente. | Falta de análisis de fallos e interrupciones paso a paso. | Incorporación de la tabla de análisis de interrupciones, prueba conceptual de idempotencia y demostración formal de preservación del árbol ante cortes imprevistos. | Plan Maestro (Sección 7.3). | CA-426-07 | Errores de hardware en disco local están fuera del control del script de software. | **CERRADO DOCUMENTALMENTE** |

---

### 3. Diferencias Documentales Principales (v2.8 $\rightarrow$ v2.9)

1. **Comparador en 12 Dimensiones (`PropositionComparator`):** Se añadieron formalmente las dimensiones de sujeto, vigencia temporal, fecha de aplicación y condiciones de precedencia, con tabla de 12 casos conceptuales sin heurísticas.
2. **Selección Canónica Multi-Candidata (`CanonicalSelector`):** Se sustituyó la búsqueda ciega por un motor que evalúa todas las candidatas primarias por vigencia y jerarquía Tier 1, agrupando por acción y objeto y resolviendo formalmente si existe norma unívoca o ambigüedad material.
3. **Erradicación Radical de Ramas Fail-Open:** Cuando no se identifica una norma primaria unívoca y vigente (`PRIMARY_NORM_NOT_IDENTIFIED`, `AMBIGUOUS`, etc.), el sistema activa un comportamiento *fail-closed* estricto, bloqueando todos los sidecars para resoluciones vinculantes.
4. **Rollback Transaccional e Idempotente:** Rediseño con máquina de estados (`PREPARED`, `BACKUP_VERIFIED`, `RESTORING`, `VERIFIED`, `COMPLETED`, `RECOVERY_REQUIRED`, `ABORTED`), directorio con UUID, cero borrados y garantía de recuperación ante interrupciones.
5. **Invariante 12 Ejecutable y Tabla de 8 Estados Válidos:** Se convirtió el principio de que la no-contradicción no equivale a suficiencia dispositiva en una aserción ejecutable en `__post_init__`, con matriz de 8 estados válidos y 6 inválidos.
6. **Validación Probatoria en 7 Etapas:** En `ConditionVerificationEvidence` se definió el enum `EvidenceSufficiencyStage` y se exigió regex hexadecimal estricto de 64 caracteres para el hash SHA-256.
7. **Oráculos SEC-CRIT Desagregados en 13 Campos:** Contrastados reproduciblemente contra el archivo PDF oficial de 298 páginas (`sor_2026_08_rebuild`), documentando página impresa, página PDF, contexto y citas literales exactas.
8. **Clarificación Metodológica de Dataset B:** Denominado formalmente conjunto de validación hold-out reservado conocido, separando integridad criptográfica de independencia experimental.

---

### 4. Registro de Riesgos Residuales Declarados

1. **Riesgo de Exposición Local del Hold-Out:** El archivo del Dataset B residirá en el almacenamiento del proyecto al alcance técnico del ejecutor. El blindaje depende exclusivamente de las salvaguardas de custodia y auditoría externa de ChatGPT y Alexis.
2. **Dependencia de la Extracción Estructurada:** Debido a la regla estricta de no admisión de Sidecars no estructurados (`sc.proposition is None`), cualquier fragmento complementario cuya ingesta no haya tipado sus 12 dimensiones deónticas será purgado automáticamente con abstención conservadora.
3. **Muestreo Acotado de Seguridad:** Las 20 consultas del benchmark reservado conocido cubren contingencias de alto riesgo (puente, edad, llaves, vestimenta), pero no sustituyen el dictamen final de la Comisión de Arbitraje de la IJF.
4. **Rigidez Ante Consultas Novedosas:** La eliminación de ramas fail-open causará abstención conservadora ante cualquier tema que no cuente con una norma primaria SOR 2026 explícitamente tipada en la ontología.

---

### 5. Declaración de Preservación de Activos y Reposo Operativo

- Cero modificaciones en `src/`, `tests/` o `data/`.
- Hashes SHA-256 de los 6 activos físicos de datos y del snapshot de código verificados intactos:
  1. `data/raw/ijf_sor_2026.pdf`: `729b1843cb370d19d70fc71481a1a39939d2434201514a3bef3af402a5ab995f`
  2. `data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf`: `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620`
  3. `data/corpus_multisource/sidecar_registry.json`: `57e31e535cd0185c1f4cb8184d6d5d952989d3bb0fc19892fffa57bdc6029bce`
  4. `data/corpus_multisource/manifests/BATCH-MULTI-2026-11-01.json`: `447debe4f8c6ab13f1961739c5d04f197fbb77e46901c87f075054a812803835`
  5. `data/corpus_multisource/processed/multisource_metadata.json`: `811a9b93e4172edcff0e4936e60a6afe69c3c392a229ef5aeaad53c00f986165`
  6. `data/corpus_multisource/processed/multisource_passages.json`: `a49337a20fbf95eb17788fb9ce73571a12abd8c716f5cb0ef91b459296a280bf`
  7. `src/rre_engine.py` (y snapshot): `d45c17d3397427d6be2d2c379764a27439c5f7401538947c23c5fbd6c6ffae1e`
- Línea base de 267 tests pytest intacta.
- **La Etapa 1 de Implementación CONTINÚA PENDIENTE DE AUTORIZACIÓN.**

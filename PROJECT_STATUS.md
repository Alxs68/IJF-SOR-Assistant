# ESTADO OFICIAL DEL PROYECTO (PROJECT STATUS)
## IJF SOR Assistant 2026

**Fecha de última actualización:** 7 de noviembre de 2026  
**Product Owner y Autoridad Normativa (Autoridad Soberana):** Alexis Oliveros Lozano  
**Planificador, Supervisor Metodológico y Auditor Independiente:** ChatGPT  
**Ejecutor Técnico:** Antigravity  
**Repositorio Local:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Repositorio Remoto:** `https://github.com/Alxs68/IJF-SOR-Assistant`  
**Rama Activa de Desarrollo:** `integration/ijf-sor-2026-08-merge`

---

## 1. Identificación y Propósito del Proyecto

El **IJF SOR Assistant** es una plataforma de software e inteligencia artificial especializada en arbitraje y reglamentación deportiva para el judo internacional, concebida para asistir a árbitros, directores deportivos, comisionados y entrenadores en la interpretación precisa, trazable y fundamentada del reglamento oficial emitido por la Federación Internacional de Judo (IJF).

El sistema opera bajo los principios soberanos instruidos por Alexis Oliveros Lozano:
- **Fidelidad documental estricta:** Toda respuesta debe sustentarse en pasajes normativos oficiales verificables.
- **Cero tolerancia a la invención normativa (alucinación):** Prohibición categórica de asumir o extrapolar reglas inexistentes.
- **Trazabilidad física:** Identificación explícita de artículos y páginas del documento oficial.
- **Abstención fundamentada:** Reconocimiento explícito cuando una consulta no pertenece al dominio del judo reglamentado por el SOR o versa sobre materias no reguladas.

---

## 2. Arquitectura Vigente: Lean RRE 3.0 / ADA

Por mandato soberano del Product Owner ([`docs/acta_aprobacion_reorientacion_lean_ijf_sor_assistant.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/acta_aprobacion_reorientacion_lean_ijf_sor_assistant.md), decisiones `DEC-002` y `DEC-009`), la arquitectura oficial es **Lean RRE 3.0 / ADA**:

```
[ Consulta de Usuario ]
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  Streamlit UI (app.py) — Interfaz Limpia y Accesible   │
│  - Eliminación de controles técnicos (sliders K y min) │
│  - Formulario de Novedades Simplificado (7 tipos)      │
│  - Selección de idioma (es / en)                       │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  Reasoning Retrieval Engine (RRE 3.0)                  │
│  - Híbrido Denso (all-MiniLM-L6-v2, 384d)              │
│  - Sparse BM25 con normalización léxica de judo        │
│  - Reciprocal Rank Fusion (RRF k=60)                   │
│  - Costura de Pasajes Adyacentes (Passage Stitcher)    │
│  - Detector OOD y Calibración de Abstención            │
│  * Configuración Canónica Ratificada (DEC-009):        │
│    - K = 5 (Recuperación oficial óptima)               │
│    - min_score = None (Filtrado interno RRE calibrado) │
│    - K adaptativo: Fuera del alcance actual            │
└────────────────────────────────────────────────────────┘
          │ (Evidencias Candidatas)
          ▼
┌────────────────────────────────────────────────────────┐
│  DocumentValidator & EvidenceSelector                  │
│  - Certificación Tier 1 (SOR Oficial Canónico)         │
│  - Evaluación de 7 Perfiles Normativos por Intención   │
│  - Contrato de Selección Rector (Desempates y Conflicto│
└────────────────────────────────────────────────────────┘
          │ (EvidenceBundle Certificado)
          ▼
┌────────────────────────────────────────────────────────┐
│  Arbitration Decision Assistant (ADA v2)               │
│  - Síntesis en Dos Niveles (Nivel 1 Resumen / Nivel 2) │
│  - MultiProviderLLMManager (Groq / Gemini / Fallback)  │
│  - Validador Normativo de Citas y Sanciones            │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  Visor PDF Streaming (PDF.js)                          │
│  - Localización en 298 Páginas Físicas Canónicas       │
│  - Resaltado Dinámico de Evidencia                     │
└────────────────────────────────────────────────────────┘
```

---

## 3. Fuente Normativa Oficial Vigente

- **Documento Rector Canónico:** *IJF Sport and Organisation Rules 2026* (SOR).
- **Fecha de Emisión Oficial:** 14 de agosto de 2026.
- **Identificador de Fuente:** `SOR-2026-08-14-ENG`.
- **Extensión Física Canónica:** 298 páginas físicas.
- **Hash Criptográfico SHA-256:** `9426b10d7d740c018a1a38df37cfec796851b2c4bfbb5ef0be0ab0f622be3f54`.
- **Base de Conocimiento Activa:** 385 pasajes normativos canónicos indexados en el grafo y motor RRE ([`src/corpus_config.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/corpus_config.py)).

---

## 4. Estado Consolidado de Fases Correctivas (P0 / P1)

Conforme a la estructura del plan correctivo maestro ([`docs/plan_correctivo_p0_p1.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/plan_correctivo_p0_p1.md)):

| Fase | Denominación Oficial | Estado Documental | Aprobación Soberana | Evidencia y Cierre |
| :---: | :--- | :---: | :---: | :--- |
| **P0-A** | Catálogo Oro y Línea Base Normativa VF01 | **CERRADA** | Alexis Oliveros | Catálogo de 52 casos cerrado en [`docs/evaluacion/catalogo_vf01_normativo.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/evaluacion/catalogo_vf01_normativo.md); dictamen arbitral de 11 casos prioritarios por Alexis en [`docs/auditoria/validacion_humana_resultados_actuales.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/validacion_humana_resultados_actuales.md). |
| **P0-B** | Recuperación Localizada RRE (Kumi-kata) | **CERRADA** | Alexis Oliveros | 10/10 PASS en consultas focales CGPT-06; subsanación de ESC-09 (Shido explícito en dedos entrelazados continuos) documentada en [`docs/auditoria/informe_fase_P0_B_ingenieria_rre.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/informe_fase_P0_B_ingenieria_rre.md). |
| **P0-C** | Selección, Suficiencia y Síntesis Controladas | **CERRADA** | Alexis Oliveros | Contrato rector de selección con suficiencia probatoria para 7 perfiles (`SANCTION`, `SCORE`, `MEASUREMENT_TIME`, `EXCEPTION`, `PROCEDURE`, `DEFINITION`, `GENERAL`), reglas de desempate y anti-keyword stuffing. Suite formal [`tests/test_p0_c_reasoning_and_selection.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_p0_c_reasoning_and_selection.py) (**9/9 PASS**). Regresión de 11 casos de Alexis (**11/11 PASS**) y 10 casos CGPT-06 (**10/10 PASS**). Informes en [`docs/auditoria/informe_fase_P0_C_razonamiento_seleccion_sintesis.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/informe_fase_P0_C_razonamiento_seleccion_sintesis.md) y [`docs/auditoria/informe_complementario_validacion_final_P0_C.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/informe_complementario_validacion_final_P0_C.md). |
| **P1-A** | Calibración de Abstención y Detección OOD | **CERRADA** | Alexis Oliveros | **Benchmark empírico oficial de 40 casos balanceados** (15 consultas in-domain, 25 consultas OOD en 5 clases): 100.0% exactitud global (40/40), 100.0% abstención OOD (25/25, 0% falsas aceptaciones) y 100.0% retención in-domain (15/15, 0% falsas abstenciones). Suite formal permanente en [`tests/test_p1_a_abstention_ood.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_p1_a_abstention_ood.py) (**10/10 PASS**) y [`tests/test_negative_domain_anchor_scoring.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_negative_domain_anchor_scoring.py) (**25/25 PASS**). Informe en [`docs/auditoria/informe_fase_P1_A_abstencion_ood.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/informe_fase_P1_A_abstencion_ood.md). |
| **P1-B** | Configuración, Regresión E2E y Novedades | **CERRADA** | Alexis Oliveros | Verificación de propagación determinista en pipeline E2E. Retiro de sliders $K$ y `min_score` en interfaz pública (`app.py`); simplificación del mecanismo de novedades a 7 tipos oficiales con captura automática y descarga CSV en barra lateral administrativa (`src/feedback_manager.py`). Suites: [`tests/test_p1_b_configuracion_e2e.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_p1_b_configuracion_e2e.py) (**9/9 PASS**) y [`tests/test_ui_controls_and_novedades.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_ui_controls_and_novedades.py) (**5/5 PASS**). Informes en [`docs/auditoria/informe_fase_P1_B_configuracion_e2e.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/informe_fase_P1_B_configuracion_e2e.md) y [`docs/auditoria/informe_auditoria_mecanismo_novedades.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/informe_auditoria_mecanismo_novedades.md). **Configuración canónica oficial ratificada: $K=5$, `min_score=None` por el Product Owner mediante decisión soberana DEC-009**, sustentada en la evaluación experimental de [`docs/auditoria/experimento_comparativo_k_rre_2026_11.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/experimento_comparativo_k_rre_2026_11.md). |

---

## 5. Situación de Control de Versiones y Git

| Entorno / Rama | Commit Base / HEAD | Fecha Documentada | Estado Operativo Reportado | Observaciones y Límites de la Evidencia |
|---|---|---|---|---|
| **Desarrollo Local** | `61afc1b` + *árbol de trabajo con modificaciones* | 08/11/2026 | **148/148 pruebas automatizadas reportadas PASS** | Suites ejecutadas localmente en Windows (Python 3.12, 100% éxito). Contiene las modificaciones de P0-B, P0-C, P1-A, P1-B, retiro de sliders, novedades simplificadas e implementación técnica canónica de DEC-009 ($K=5$ en backend). Ver informe [`docs/auditoria/implementacion_local_k5_2026_11.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/implementacion_local_k5_2026_11.md). *Limitación: cambios en working tree pendientes de commit formal.* |
| **GitHub Integration** | `6080697` (`origin/integration/ijf-sor-2026-08-merge`) | 03/11/2026 | **Atrás por 4 commits locales + cambios P0/P1** | Último commit remoto fue de Docker hardening. Los commits locales `d963782`, `f48492d`, `9e17d87` y `61afc1b` no han sido pusheados. |
| **GitHub Main** | `afb5b11` (`origin/main` y `main` local) | 30/07/2026 | **Desfasada (Legacy 2026-01)** | Rama principal histórica previa a la reconstrucción integral del SOR 2026-08. |
| **Último Release GitHub** | Tag **`v1.3.0`** (commit `8dbf5eb`) | 30/07/2026 | **Release Histórica (MVP v1.0)** | Representa el MVP inicial de julio 2026; no refleja el motor RRE 3.0 ni la edición del SOR de agosto 2026. |
| **Producción OCI** | `https://sor.alxol.com` (commit `61afc1b`) | 04/11/2026 | **Activa y Operativa (HTTP 200)** | Desplegada en OCI (Ubuntu ARM64). Opera con el corpus de agosto 2026 en estado limpio al commit `61afc1b`, pero **carece de las fases correctivas P0-B, P0-C, P1-A, P1-B, de los ajustes de interfaz y de la configuración ratificada en DEC-009**. |

> [!WARNING]
> **ADVERTENCIA DE DISCREPANCIA ENTRE ENTORNOS:**  
> Aunque desarrollo local y producción OCI comparten el commit `61afc1b` como ancestro común, **no son equivalentes funcionalmente**. El árbol de trabajo local posee modificaciones no consolidadas en commit correspondientes a las fases P0-B, P0-C, P1-A, P1-B, ajustes de UI y ratificación canónica de $K=5$ (DEC-009). Producción se mantiene congelada por orden soberana del Product Owner hasta la autorización formal de release.

---

## 6. Diferencias Conocidas entre Desarrollo Local y Producción

1. **Configuración Canónica de Recuperación ($K=5$):**  
   Desarrollo local tiene ratificada formalmente por el Product Owner la configuración canónica $K=5$, `min_score=None` (DEC-009). Producción corre con el commit `61afc1b` previo a la ratificación de DEC-009 y aún exhibe sliders manuales en la barra lateral.
2. **Interfaz de Búsqueda:**  
   Producción exhibe los sliders técnicos de *Cantidad de Reglas ($K$)* y *Filtro Anti-Distracciones (`min_score`)*. En desarrollo local fueron retirados de la interfaz pública.
3. **Mecanismo de Novedades y Telemetría:**  
   Producción tiene el formulario genérico inicial. En desarrollo local se encuentra implementado el formulario de baja fricción con los 7 tipos oficiales (`ERROR_NORMATIVO`, `REFERENCIA_INCORRECTA`, etc.), captura contextual automática y exportación directa a CSV en la barra lateral administrativa.
4. **Contrato de Selección y Suficiencia P0-C:**  
   Producción no cuenta con el selector rector de precedencia, suficiencia para los 7 perfiles ni desempates específicos de P0-C.
5. **Calibración OOD P1-A:**  
   Producción opera con detección heurística preliminar sin los umbrales calibrados del benchmark de 40 casos ni el scoring de anclas negativas.
6. **Corrección Focal ESC-09 (Kumi-kata):**  
   Producción carece de la plantilla corregida de respuesta que explicita la sanción Shido ante dedos entrelazados continuos.

---

## 7. Riesgos y Pendientes Reales

1. **Persistencia Remota en OCI (Pendiente de Verificación):**  
   En desarrollo local, las novedades se almacenan en `data/feedback/user_observations.jsonl`. No es posible verificar documentalmente desde el repositorio local la persistencia efectiva, permisos de escritura del usuario del servicio ni políticas de retención en la máquina virtual de OCI. Queda formalmente como: **"Persistencia remota pendiente de verificación"**.
2. **Reverse Proxy y Capa TLS en OCI (Pendiente de Verificación):**  
   La aplicación pública `https://sor.alxol.com` responde en HTTPS (puerto 443), pero la tecnología específica del reverse proxy (Caddy, Nginx, Traefik o Cloud Load Balancer de Oracle) no está documentada en el repositorio. Queda formalmente como: **"Configuración de reverse proxy pendiente de verificación remota"**.
3. **Sincronización Git y Desfase de Ramas:**  
   Las modificaciones locales de P0/P1 y gobernanza documental no han sido comprometidas en commit ni enviadas a GitHub. La rama `main` y el release `v1.3.0` están severamente desfasados respecto a agosto 2026. Se requiere autorización explícita del Product Owner para proceder con commits, merge y release.
4. **Documentación de Entrada Desfasada (`README.md`):**  
   El `README.md` de la raíz sigue describiendo el MVP v1.0 de julio 2026. Debe actualizarse formalmente en una actividad posterior para reflejar la realidad del sistema.

---

## 8. Documentos Rectores del Proyecto

1. [`docs/acta_aprobacion_reorientacion_lean_ijf_sor_assistant.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/acta_aprobacion_reorientacion_lean_ijf_sor_assistant.md) (Mandato soberano de arquitectura Lean).
2. [`docs/plan_correctivo_p0_p1.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/plan_correctivo_p0_p1.md) (Plan maestro de fases correctivas).
3. [`docs/evaluacion/catalogo_vf01_normativo.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/evaluacion/catalogo_vf01_normativo.md) (Catálogo de evaluación normativa de 52 casos) y [`docs/auditoria/validacion_humana_resultados_actuales.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/validacion_humana_resultados_actuales.md) (Dictamen arbitral de Alexis sobre 11 casos prioritarios).
4. [`docs/DECISIONES.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/DECISIONES.md) (Registro central de decisiones soberanas aprobadas por Alexis Oliveros, incluyendo DEC-001 a DEC-009).
5. [`docs/INDEX_DOCUMENTAL.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/INDEX_DOCUMENTAL.md) (Índice central y censo exhaustivo de documentación).
6. [`docs/deployment/PRODUCTION_MANIFEST.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/deployment/PRODUCTION_MANIFEST.md) (Manifiesto de configuración y estado conocido de producción OCI).
7. [`docs/auditoria/experimento_comparativo_k_rre_2026_11.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/experimento_comparativo_k_rre_2026_11.md) (Informe de evaluación experimental comparativa de $K \in \{3, 5, 8\}$, fundamento empírico de DEC-009).
8. [`docs/auditoria/implementacion_local_k5_2026_11.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/implementacion_local_k5_2026_11.md) (Informe técnico de implementación local de $K=5$ canónico en backend y validación de regresión).

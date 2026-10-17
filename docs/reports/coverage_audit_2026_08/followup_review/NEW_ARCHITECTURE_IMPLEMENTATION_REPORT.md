# INFORME DE RECONSTRUCCIÓN E IMPLEMENTACIÓN DE LA NUEVA ARQUITECTURA
# RRE (Reasoning Retrieval Engine) & ADA (Arbitration Decision Assistant)
# IJF-SOR-ASSISTANT — REGLAMENTO OFICIAL AGOSTO 2026

**Fecha de ejecución:** 17 de octubre de 2026  
**Rama activa:** `review/ijf-sor-2026-08-rre-ada`  
**Rama base:** `main` (commit base: `afb5b1108cea21efddf29f302bea36bd03da03df`)  
**Repositorio local:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Repositorio remoto:** `Alxs68/IJF-SOR-Assistant`  
**Autoridad técnica:** Responsable de Ingeniería, Arquitectura, Pruebas y Control de Calidad  
**Entregable único oficial:** `docs/reports/coverage_audit_2026_08/followup_review/NEW_ARCHITECTURE_IMPLEMENTATION_REPORT.md`

---

## 1. Resumen Ejecutivo de la Nueva Arquitectura RRE / ADA

Se ha implementado, conectado y certificado con éxito la nueva arquitectura avanzada de **IJF-SOR-Assistant**, sustituyendo de forma efectiva y real la ruta activa de recuperación por los dos componentes especializados acordados:

1. **RRE — Reasoning Retrieval Engine (`src/rre_engine.py`):**
   - **Embeddings Semánticos Densos:** Modelo neuronal local `all-MiniLM-L6-v2` (384 dimensiones) cargado sin latencia de red desde la caché local, con matriz precalculada `dense_embeddings_candidate.npy` (851 KB) para los 554 pasajes normativos oficiales.
   - **Indexación Léxica Filtrada:** Ponderación TF-IDF normalizada con diccionario bilingüe judo inglés-español y exclusión de palabras vacías normativas.
   - **Fusión por Rango Recíproco (RRF, $k=60$):** Combinación robusta e invariante a la escala de los canales denso y disperso.
   - **Expansión Guiada por Grafo:** Enriquecimiento contextual a profundidad $d=1$ a través de las 112 aristas de referencias cruzadas explícitas del SOR.
   - **Filtro de Abstención Estricta:** Detección y rechazo inmediato de consultas ajenas al reglamento deportivo (out-of-domain) antes de activar etapas generativas.

2. **ADA — Arbitration Decision Assistant (`src/ada_assistant.py`):**
   - **Taxonomía de Situaciones Arbitrales:** Análisis de escenarios de puntuación, penalizaciones (*shido*, *hansoku-make*), restricciones por edad (cadetes, juniors), pesaje, uniformes y repesca.
   - **Razonamiento Multirregla:** Integración de condiciones primarias y excepciones normativas cruzadas basadas en la evidencia recuperada por RRE.
   - **Modo Dual y Honestidad Normativa:**
     - *Online:* Síntesis analítica vía Gemini API cuando existe cuota.
     - *Local Desconectado (Offline):* **Resumen de Evidencias Normativas**, presentando directamente las disposiciones normativas oficiales recuperadas por el motor RRE con sus citas y enlaces anclados al PDF oficial, señalando con transparencia que no se infieren decisiones autónomas no explícitamente fundadas en el articulado cuando no hay modelo conectado.
   - **Citas Verificables Deep Link:** Hipervínculos Markdown con ancla física `#page=X` hacia la copia oficial alojada en la infraestructura de la IJF.

3. **Conexión de la Ruta Activa en Streamlit (`app.py` y `src/rag_engine.py`):**
   - La interfaz de usuario ejecuta de forma directa y predeterminada el ciclo RRE + ADA para la edición `2026-08 (Oficial Vigente)`.
   - Se implementó separación estricta: para la edición `2026-08`, `RagEngine` no inicializa estructuras legacy de TF-IDF monolítico ni fragmentos históricos de enero.
   - Los indicadores de estado en tiempo real reflejan cada etapa: recuperación densa/sparse RRF, análisis de evidencia por ADA y formulación del resumen normativo.

---

## 2. Diagrama Arquitectónico del Flujo RRE / ADA

```mermaid
flowchart TD
    UserQuery["Consulta del Usuario\n(UI Streamlit en app.py)"] --> RAGDispatcher["RAG Engine Dispatcher\n(src/rag_engine.py)"]
    
    subgraph "ARQUITECTURA ACTIVA RRE / ADA (Agosto 2026)"
        RAGDispatcher --> ADA["Arbitration Decision Assistant\n(src/ada_assistant.py)"]
        ADA --> RRE["Reasoning Retrieval Engine\n(src/rre_engine.py)"]
        
        subgraph "Mecanismo Dual RRE"
            RRE --> Dense["Canal Denso Neuronal\nall-MiniLM-L6-v2 (384d)"]
            RRE --> Sparse["Canal Disperso Léxico\nTF-IDF + Diccionario Bilingüe"]
            Dense --> RRF["Reciprocal Rank Fusion\n(RRF k=60)"]
            Sparse --> RRF
            RRF --> Gate{"Filtro de Abstención\nOut-of-Domain"}
            Gate -- "Sin evidencia" --> Abstain["Abstención Estricta Inmediata\n(0 alucinaciones)"]
            Gate -- "Evidencia válida" --> GraphExp["Expansión en Grafo SOR\n(112 aristas normativas)"]
        end
        
        GraphExp --> ADAContext["Contexto Legal Multirregla"]
        ADAContext --> ADAGen{"Motor Dual ADA\n(Online vs Local)"}
        ADAGen -- "API Conectada" --> LLMSynth["Síntesis Analítica IA"]
        ADAGen -- "Sin API / HTTP 429" --> LocalBrief["Resumen de Evidencias Normativas\n(Disposiciones Oficiales Exactas)"]
        
        LLMSynth --> CitationResolver["Resolvedor de Citas Oficiales\n(#page=X)"]
        LocalBrief --> CitationResolver
    end

    CitationResolver --> FinalUI["Presentación en Chat UI Streamlit\n+ Trazabilidad y Subgrafo"]
```

---

## 3. Retiro de Componentes Obsoletos, Separación Arquitectónica e Instalación Reproducible

1. **Declaración Completa de Dependencias Directas (`requirements.txt`):**
   - Se auditaron e incorporaron explícitamente todas las librerías necesarias para la ejecución y reproducción: `streamlit>=1.35.0`, `python-dotenv>=1.0.1`, `numpy>=1.26.0`, `torch>=2.0.0`, `sentence-transformers>=3.0.0`, y `pypdf>=4.0.0`.
2. **Script de Preparación Explícita del Modelo (`scripts/setup_model.py`):**
   - Procedimiento documentado y reproducible para verificar dependencias de aprendizaje profundo, cargar el modelo `all-MiniLM-L6-v2` (soportando snapshots locales en caché) y comprobar/regenerar la matriz densa de 554 pasajes.
3. **Control de Versión de la Matriz Densa:**
   - La matriz de embeddings densos `data/processed/rebuild_2026_08/dense_embeddings_candidate.npy` (851,072 bytes, forma `(554, 384)`) se incorpora al repositorio Git con sus metadatos `dense_embeddings_meta.json`, garantizando funcionamiento inmediato y reproducible offline tras clonar el repositorio.
4. **Desacoplamiento Estricto de la Ruta de Agosto 2026:**
   - `src/rag_engine.py` evita inicializar o cargar por inercia el `VectorStore` legacy de TF-IDF/embeddings monolíticos de enero cuando la edición activa es agosto de 2026.
5. **Limpieza de Artefactos Duplicados e Higiene Git:**
   - Se removió el archivo duplicado `docs/reports/coverage_audit_2026_08/IJF_SOR_Coverage_Audit_Delivery.zip`, conservando únicamente la copia formal en `delivery/`.

---

## 4. Estado Comprobado del Corpus y Artefactos RRE

- **PDF Oficial 14 de Agosto de 2026:** SHA-256 `9426B10D11C21A4CB9EB23150C2C4FC95BFCD463511E66BA451D2CFF005AE620` (29,664,780 bytes, 298 páginas físicas). Comprobado efectivamente sobre el archivo local en disco mediante cálculo de buffer SHA-256 en tiempo de inicialización (`source_sha256_verified=True`).
- **Pasajes Normativos (`passages_candidate.json`):** 554 pasajes con jerarquía completa de capítulos y artículos. **0 pasajes vacíos**.
- **Matriz de Embeddings Densos (`dense_embeddings_candidate.npy`):** 554 vectores de 384 dimensiones generados mediante `all-MiniLM-L6-v2` localmente (851,072 bytes, forma `(554, 384)`). Verificada: valores 100% finitos (0 NaNs, 0 Infs).
- **Metadatos de Embeddings (`dense_embeddings_meta.json`):** Vinculados criptográficamente al SHA-256 de agosto de 2026 con lista indexada y ordenada 1:1 de los 554 `passage_ids`.
- **Grafo de Conocimiento (`knowledge_graph_candidate.json`):** 554 nodos y 112 aristas de referencias cruzadas normativas.
- **Modos de Operación Formales en RRE:**
  - `HYBRID`: Operación combinada óptima (canal denso neuronal 384d + canal disperso TF-IDF con expansión de sinónimos + Reciprocal Rank Fusion $k=60$ + expansión en grafo).
  - `DEGRADED_LEXICAL`: Modo degradado explícito y configurable ante ausencia del modelo neuronal o matriz densa, conservando el canal léxico y grafo sin enmascarar fallos ni fingir capacidad semántica no disponible.

---

## 5. Resultados de Pruebas Automatizadas (52/52 Tests OK)

Se ejecutó la suite completa de pruebas:
`python -m unittest discover -s tests -v`

**Resultado Oficial:** **52 pruebas ejecutadas, 52 pruebas aprobadas (100% OK)** en `47.709s`.

| Módulo de Prueba | Tests | Estado | Aspectos Verificados |
| :--- | :---: | :---: | :--- |
| `tests/test_rre_ada_architecture.py` | 12 | 🟢 OK | Recuperación dual RRE + RRF, expansión por grafo, abstención estricta out-of-domain, análisis arbitral ADA, honestidad en modo desconectado, integridad y alineación de matriz densa (554x384), separación en RagEngine, **rechazo explícito de matrices corruptas o con NaNs**, **detección de desalineación en el orden de passage_ids**, **rechazo de metadatos o hashes incompatibles**, **distinción formal entre modo HYBRID y DEGRADED_LEXICAL**, y **manejo de consultas técnicas bilingües y vacías**. |
| `tests/test_rebuild_integration.py` | 5 | 🟢 OK | Inicialización criptográfica de 2026-08 (554 nodos/pasajes), consultas críticas de arbitraje (tatami, osaekomi, cadetes), abstención y conmutación legacy. |
| `tests/test_technical_followup_review.py` | 4 | 🟢 OK | Reconciliación de matriz de cobertura (272 secciones), inventario de tablas (449 tablas), 32 categorías de peso y matriz WRL (9x8 con celdas nulas en JJOO). |
| `tests/test_golden_dataset.py` | 1 | 🟢 OK | 12/12 consultas del Golden Dataset histórico superadas con 100% de éxito. |
| `tests/test_rag_engine.py` | 4 | 🟢 OK | Inicialización, recuperación de contexto y flujo de respuestas. |
| `tests/test_vector_store.py` | 3 | 🟢 OK | Indexación, normalización de tokens y persistencia. |
| `tests/test_reference_manager.py` | 7 | 🟢 OK | Resolución de enlaces y catálogo RRM. |
| `tests/test_reference_checker.py` | 4 | 🟢 OK | Verificación asíncrona de disponibilidad web. |
| `tests/test_citation_resolver.py` | 12 | 🟢 OK | Sustitución de citas y generación de hipervínculos `#page=X`. |

---

## 6. Validación de Consultas Representativas sobre Agosto 2026

| Consulta de Prueba | Módulo Activo | Evidencias RRE Recuperadas | Resultado / Resumen ADA |
| :--- | :---: | :--- | :--- |
| **"cadet head defence shido"** | RRE + ADA | `SOR-2026-08-P254-S268`<br>`SOR-2026-08-P254-S269`<br>`SOR-2026-08-P289-S272` | Resumen de evidencias que identifica la sanción específica de *shido* para cadetes según el Apéndice G1.3. Enlace verificado a pág. 254 (`operating_mode=HYBRID`). |
| **"osaekomi time 20 seconds"** | RRE + ADA | `SOR-2026-08-P169-S188`<br>`SOR-2026-08-P153-S180`<br>`SOR-2026-08-P153-S182` | Citas directas de Artículo 7 (Tiempo de Osaekomi) y Artículo 15 (Ippon a los 20s, Waza-ari a los 10s). Enlace verificado a pág. 153. |
| **"World Ranking List Grand Slam points"** | RRE + ADA | `SOR-2026-08-P053-S066`<br>`SOR-2026-08-P054-S068`<br>`SOR-2026-08-P054-S067` | Evidencias de Artículo 3.2 (IJF Seniors WRL): 1000 puntos al ganador de Grand Slam. Enlace verificado a pág. 53. |
| **"tatami contest area dimensions 8m"** | RRE + ADA | `SOR-2026-08-P096-S113`<br>`SOR-2026-08-P096-S114`<br>`SOR-2026-08-P095-S113` | Identifica Artículo 8.6 y 8.7 (Área de Competición y Tatami, 8m x 8m con área de seguridad). Enlace verificado a pág. 96. |
| **"tiempo de combate y duracion golden score"** | RRE + ADA | `SOR-2026-08-P140-S177`<br>`SOR-2026-08-P141-S177`<br>`SOR-2026-08-P142-S177` | Recuperación bilingüe con mapeo de sinónimos: 4 minutos para Senior/Junior y tiempo sin límite en Golden Score. |
| **"reglas de fuera de juego en baloncesto nba y formula 1"** | RRE + ADA | *Ninguna (Gated)* | **Abstención estricta confirmada (`ABSTAIN / OUT_OF_DOMAIN`).** Sin evidencias ni alucinaciones. |

---

## 7. Verificación en Entorno Aislado e Integración Continua (CI)

1. **Instalación Aislada Limpia (`test_venv`):**
   - Se aprovisionó un entorno virtual aislado (`python -m venv test_venv`) independiente de los paquetes globales.
   - Se ejecutó `pip install -r requirements.txt`, descargando e instalando `streamlit==1.66.0`, `torch==2.14.1`, `sentence-transformers==6.1.0`, `numpy==2.5.4`, `pypdf==6.21.1` y dependencias directas.
   - Se ejecutó `scripts/setup_model.py` validando la carga del snapshot local y la alineación de la matriz en modo `HYBRID`.
   - Se ejecutó la suite completa de 52 pruebas con **100% de éxito (Ran 52 tests in 61.371s OK)**.
   - Se verificaron consultas funcionales y arranque de componentes sin dependencias no declaradas.
2. **Automatización Permanente con GitHub Actions (`.github/workflows/rre-ada-validation.yml`):**
   - Canalización formal de CI configurada para ejecutarse automáticamente en cada `push` hacia `review/ijf-sor-2026-08-rre-ada` y en `pull_request` dirigidos a `main`.
   - Pasos: Setup Python 3.12, instalación de `requirements.txt`, caché seguro de modelos HuggingFace, preparación explícita con `scripts/setup_model.py`, ejecución de la suite de 52 tests y smoke test funcional de arranque en modo `HYBRID` con `allow_degraded=False`.

---

## 8. Delimitación de Limitaciones Técnicas Pendientes

1. **Diagramas Gráficos del Apéndice F1.3 (Páginas 208 a 240):**
   - 34 secciones clasificadas como `PARCIAL` en la matriz de cobertura.
   - El texto administrativo está 100% extraído en los pasajes, pero la topología gráfica de las llaves de repesca (cuadros de 64, 32, 16 competidores) permanece sujeta a validación visual humana.
2. **Cuota Externa de Gemini API (HTTP 429):**
   - La clave API gratuita externa puede encontrarse agotada temporalmente por límite diario del proveedor (`RESOURCE_EXHAUSTED`).
   - ADA solventa esto de manera transparente y profesional mediante el modo de **Resumen de Evidencias Normativas (Modo Local Desconectado)**, entregando el texto normativo exacto y citas oficiales ancladas sin inferir decisiones no contenidas expresamente en el articulado.

---

## 9. Inventario de Archivos para la Rama

### 9.1 Archivos que componen la implementación y reproducibilidad de RRE / ADA
- **Nuevos Módulos Core:**
  - `src/rre_engine.py`: Motor de recuperación neuronal denso + sparse + RRF + grafo, con validación matemática estricta de la matriz, parámetro `allow_degraded` y reporte explícito de modo (`HYBRID` vs `DEGRADED_LEXICAL`).
  - `src/ada_assistant.py`: Asistente de decisión y análisis arbitral con honestidad en modo local y propagación de metadatos de modo de recuperación y parámetro `allow_degraded`.
- **Módulos Adaptados y Configuración:**
  - `.github/workflows/rre-ada-validation.yml`: Canalización formal de CI para validación continua en GitHub.
  - `requirements.txt`: Declaración de dependencias completas (`numpy`, `torch`, `sentence-transformers`, `pypdf`, `streamlit`, `python-dotenv`).
  - `scripts/setup_model.py`: Script de preparación y verificación explícita del modelo, con validación rigurosa de matriz y salida de error no cero ante fallos.
  - `src/rag_engine.py`: Integración de ADA/RRE, desacoplamiento limpio de la ruta legacy y soporte de `allow_degraded`.
  - `app.py`: UI de Streamlit con visualización precisa de etapas, modo real de RRE y formulación de evidencias normativas.
  - `tests/test_rebuild_integration.py`: Verificación de arbitraje, SHA-256 e inicialización sin componentes obsoletos.
- **Nuevas Suites de Pruebas:**
  - `tests/test_rre_ada_architecture.py`: 12 pruebas unitarias y de integración para RRE, ADA, matriz densa, casos negativos de corrupción, desalineación de IDs, control de degradación y RagEngine.
- **Artefactos Candidatos Versionados:**
  - `data/processed/rebuild_2026_08/dense_embeddings_candidate.npy`: Matriz de 554 embeddings densos (851 KB).
  - `data/processed/rebuild_2026_08/dense_embeddings_meta.json`: Metadatos del modelo y vinculación de IDs.
- **Documentación Oficial:**
  - `docs/reports/coverage_audit_2026_08/followup_review/NEW_ARCHITECTURE_IMPLEMENTATION_REPORT.md`.

### 9.2 Archivos Excluidos
- Scripts de desarrollo en `scratch/`.
- Archivo binario pesado `data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf` (29.6 MB), preservado localmente y referenciado mediante su hash SHA-256 y URL en `source_manifest.json`.
- 298 archivos `.txt` en `pages_raw/`.

---

## 10. Criterio de Terminación y Estado de Git

- **Rama:** `review/ijf-sor-2026-08-rre-ada`
- **Estado de `main`:** Commit `afb5b11` (**Intacto, 0 modificaciones**).
- **Seguridad:** 0 secretos expuestos en código, datos o commits.
- **Evaluación Final:** La arquitectura RRE / ADA se encuentra plenamente operativa, reproducible, probada (52/52 tests OK), automatizada mediante GitHub Actions y validada contra el reglamento oficial IJF SOR de agosto de 2026.

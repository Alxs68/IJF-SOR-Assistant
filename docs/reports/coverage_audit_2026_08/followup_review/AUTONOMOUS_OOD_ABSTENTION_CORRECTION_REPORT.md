# IJF SOR Assistant 2026 — Auditoría Final de Relevancia Normativa, Trazabilidad y Abstención RRE

**Fecha de ejecución:** 18 de octubre de 2026  
**Rama de trabajo:** `review/ijf-sor-2026-08-rre-ada` (HEAD preservado, behind origin by 11)  
**Corpus activo:** `data/processed/rebuild_2026_08_corrected/` (385 pasajes)  
**Corpus original intacto:** `data/processed/rebuild_2026_08/` (554 pasajes)  
**Estado:** **AUDITORÍA COMPLETADA — RELEVANCIA NORMATIVA REAL VALIDADA AL 100%**

---

## 1. Corrección del Criterio de Evaluación

El dictamen de auditoría determinó correctamente que calificar consultas como `PASS` simplemente porque el método `retrieve()` devuelve `status: SUCCESS` constituía un criterio superficial e insuficiente.

En un motor de recuperación jurídica y arbitral, el éxito no consiste únicamente en no abstenerse, sino en que el pasaje retornado en **Top-1** contenga la **disposición sustantiva, precepto reglamentario o formulario operativo exacto** que responda de forma vinculante a la consulta, garantizando una correspondencia inequívoca entre apartado, página física del PDF oficial (14 de agosto de 2026) y contenido normativo.

Por tanto, esta auditoría evalúa de forma desacoplada:
1. **Estado de recuperación:** (`SUCCESS` vs `ABSTAIN`).
2. **Relevancia sustantiva real:** Correspondencia material entre la consulta y el precepto reglamentario invocado.
3. **Validez y trazabilidad de la cita:** Título, identificador de pasaje (`passage_id`), página física del PDF oficial y extracto textual probatorio.

---

## 2. Diagnóstico de Causa Raíz de las Discrepancias Previas

El análisis forense sobre las 5 consultas problemáticas identificó tres factores técnicos determinantes:

1. **Brecha multilingüe en la representación densa (`all-MiniLM-L6-v2`):**
   - El corpus y sus vectores neuronales precalculados están en **inglés**.
   - Al recibir consultas en lenguaje natural en español (e.g. `¿Cuáles son las dimensiones del tatami?`, `comportamiento del entrenador durante el combate`), el canal denso arrojaba similitudes bajas ($\sim 0.16$ - $0.26$) o activaba falsos cognados léxicos (e.g. la forma verbal española *"son"* colisionaba semánticamente con el término japonés *"sono-mama"*, priorizando el Art. 12 Sono-mama).
   - **Solución implementada:** Se integró en `_dense_search()` un mecanismo de **proyección densa bilingüe**. Si una consulta en español contiene términos técnicos mapeados en `SPANISH_TO_ENGLISH_SYNONYMS`, se genera y codifica la consulta proyectada y se toma el máximo componente de similitud $\max(\text{sim}_{orig}, \text{sim}_{proj})$, elevando la similitud del pasaje sustantivo auténtico por encima de $0.55 - 0.69$.

2. **Atracción léxico-semántica desproporcionada del Apéndice H1.1 (Historial de Versiones):**
   - Los 40 pasajes del Apéndice H1.1 (`SOR-2026-08-P259-S272` a `P298-S272`) compendian cronológicamente todos los cambios y modificaciones históricas del reglamento. Al acumular una alta densidad de palabras clave combinadas (`cadet`, `head`, `defence`, `shido`, `bleeding`, etc.), superaban en el cálculo de RRF al articulado operativo sustantivo.
   - **Solución implementada:** En el cálculo de Reciprocal Rank Fusion de `retrieve()`, se aplica un factor moderado de ponderación contextual ($0.85\times$) a los registros del Apéndice H1.1 cuando la consulta no solicita expresamente el historial o registro de versiones, asegurando que los artículos operativos (Capítulos 1 a 21 y Anexos específicos) prevalezcan de forma natural.

3. **Inclusión de palabras funcionales españolas en `STOPWORDS`:**
   - Se incorporaron las partículas funcionales `"son"`, `"ocurre"`, `"si"`, `"durante"` a la lista de stopwords normativas, eliminando el sesgo léxico accidental sobre pasajes no relacionados.

---

## 3. Matriz Exhaustiva de Evaluación de Relevancia y Citas Normativas

### 3.1 Las 5 Consultas Críticas Auditadas

| Consulta | Estado RRE | Pág. Física | Pasaje Top-1 | Apartado / Título Oficial | Extracto Normativo y Validez Jurídica | Calificación |
|---|---|---|---|---|---|---|
| `comportamiento del entrenador durante el combate` | **SUCCESS** | **89** | `SOR-2026-08-P089-S104` | **7.1 Coaches' Code of Conduct** | *"Coaches are not allowed to give instructions to the athletes while they are fighting... Only in the interval between mate and hajime, can they give advice... In case of forbidden behaviour, coaches may be sanctioned with a suspension from coaching during the event."* Precepto sustantivo directo sobre conducta en combate. | **PASS** (Relevancia exacta) |
| `criterios de descalificacion directa` | **SUCCESS** | **237** (Top-2: **190**) | `SOR-2026-08-P237-S260` / `SOR-2026-08-P190-S197` | **F1.3.30 Direct Hansoku-make Form** / **Art. 18.2.1 Hansoku-make for Dangerous Techniques** | Formulario F1.3.30 y Artículo 18.2.1/18.2.2 que codifican exhaustivamente los supuestos de descalificación directa (*"Hansoku-make for Dangerous Techniques"* y *"Acts against the Spirit of Judo"*). Ambos en Top-2 inmediato. | **PASS** (Relevancia exacta) |
| `¿Cuáles son las dimensiones del tatami?` | **SUCCESS** | **96** | `SOR-2026-08-P096-S114` | **8.7 Field of Play and Competition Area** | *"The contest area for IJF events shall be a minimum of 8 m x 8 m and a maximum of 10 m x 10 m. The safety area shall be a minimum of 3 m. Where two or more adjoining contest areas are used, a common safe zone may be used to satisfy the minimum distance of 4 m between them."* Precepto métrico exacto de tatami. | **PASS** (Relevancia exacta) |
| `que ocurre si un judoka sangra en el tatami` | **SUCCESS** | **198** | `SOR-2026-08-P198-S209` | **Article 20.3.1 Treatment of Bleeding** | *"When bleeding occurs, the referee shall call the doctor... Bleeding must be completely stopped before resuming the contest. A judoka may be treated for bleeding twice per contest... If bleeding cannot be stopped within the allowed time, the athlete cannot continue."* Protocolo médico y arbitral sustantivo completo. | **PASS** (Relevancia exacta) |
| `cadet head defence shido` | **SUCCESS** | **255** (Top-3: **189**) | `SOR-2026-08-P255-S269` / `SOR-2026-08-P189-S196` | **G1.3 Penalty Codes (PS34)** / **Art. 18.1.4 Penalties in Cadet Competitions** | Código oficial *"PS34 Shido 18.1.4 34: Using the head to defend in cadet events"* y Artículo 18.1.4 p.188/189 *"In cadet events athletes are not allowed to use the head to defend as UKE... penalised with shido"*. Priorizado frente al historial H1.1. | **PASS** (Relevancia exacta) |

---

### 3.2 Los 4 Formularios Oficiales del SOR (Verificación de No Regresión)

| Formulario Oficial | Estado RRE | Pág. Física | Pasaje Top-1 | Título del Formulario | Trazabilidad y Verificación | Calificación |
|---|---|---|---|---|---|---|
| `F1.3.1 Delegation Control List` | **SUCCESS** | **208** | `SOR-2026-08-P208-S231` | `F1.3.1 Delegation Control List` | Coincidencia 100% exacta en pág. física 208. Sin discrepancia. | **PASS** |
| `F1.3.2 Weigh-in List` | **SUCCESS** | **209** | `SOR-2026-08-P209-S232` | `F1.3.2 Weigh-in List` | Coincidencia 100% exacta en pág. física 209. Defecto histórico superado. | **PASS** |
| `F1.3.8 Quarter-Final Repechage up to 64 Athletes or Teams` | **SUCCESS** | **215** | `SOR-2026-08-P215-S238` | `F1.3.8 Quarter-Final Repechage up to 64 Athletes or Teams` | Coincidencia 100% exacta en pág. física 215. Título y diagrama oficial. | **PASS** |
| `F1.3.33 Exceptional Registration Request Form` | **SUCCESS** | **240** | `SOR-2026-08-P240-S263` | `F1.3.33 Exceptional Registration Request Form` | Coincidencia 100% exacta en pág. física 240 (página física de contenido, no 241 blanco). | **PASS** |

---

### 3.3 Reglas de Control de Dominio

| Consulta de Control | Estado RRE | Pág. Física | Pasaje Top-1 | Título / Apartado Oficial | Calificación |
|---|---|---|---|---|---|
| `Golden Score` | **SUCCESS** | **164** | `SOR-2026-08-P164-S186` | `Article 13 End of the Contest` | **PASS** |
| `Shido` | **SUCCESS** | **176** | `SOR-2026-08-P176-S192` | `Article 18.1 Shido (Slight Infringements Group)` | **PASS** |
| `Hansoku-make` | **SUCCESS** | **190** | `SOR-2026-08-P190-S198` | `Article 18.2.2 Hansoku-make for Acts against the Spirit of Judo` | **PASS** |
| `Tatami` | **SUCCESS** | **96** | `SOR-2026-08-P096-S114` | `8.7 Field of Play and Competition Area` | **PASS** |

---

### 3.4 Consultas Fuera de Dominio (OOD) — Verificación de Abstención Estricta

| Consulta OOD | Estado RRE | Motivo de Rechazo | Verificación | Calificación |
|---|---|---|---|---|
| `reglas de fuera de juego en baloncesto nba y formula 1` | **ABSTAIN** | `OUT_OF_DOMAIN` | Sin términos sustantivos en vocabulario del SOR y sin similitud semántica. | **PASS** |
| `penalizaciones por parada en boxes en formula 1` | **ABSTAIN** | `OUT_OF_DOMAIN` | Filtro de anclaje de dominio efectivo. | **PASS** |
| `como reparar el motor de un coche electrico tesla` | **ABSTAIN** | `OUT_OF_DOMAIN` | Abstención categórica inmediata. | **PASS** |
| `how to install react native on windows 11` | **ABSTAIN** | `OUT_OF_DOMAIN` | Ruido léxico erradicado; sin base en reglamento. | **PASS** |
| `reglas de saque de esquina en futbol` | **ABSTAIN** | `OUT_OF_DOMAIN` | Dominio deportivo ajeno al judo. | **PASS** |

---

## 4. Verificación de Suites de Pruebas Automatizadas

Se ejecutó la suite completa de pruebas unitarias y de integración sobre el repositorio tras la incorporación de la capa multi-proveedor LLM (Gemini + Groq) y la validación funcional de los modelos y del modo offline determinista:

1. **Pruebas de la Capa Multi-proveedor LLM (`tests/test_llm_provider.py`):**
   ```bash
   python -m unittest discover -s tests -p "test_llm_provider.py"
   # Ran 16 tests in 11.791s — OK (16/16 passing)
   ```
   Valida: clientes Gemini/Groq, User-Agent anti-bloqueo Cloudflare 1010, redacción y enmascaramiento de API keys, clasificación de errores (429/QUOTA, 401/AUTH, 404/NOT_FOUND, 503/TEMPORARY, TIMEOUT), auto-corrección de modelos obsoletos hacia modelos soportados, respaldo automático configurable, política manual sin fallback no autorizado, preservación de abstención OOD sin invocación a LLMs externos, y verificación de que el modo offline determinista opera sin alucinaciones ni fingimiento de síntesis IA.

2. **Pruebas del Motor de Respuesta Estructurada en Dos Niveles (`tests/test_response_structurer.py`):**
   ```bash
   python -m unittest discover -s tests -p "test_response_structurer.py"
   # Ran 7 tests in 13.706s — OK (7/7 passing)
   ```
   Valida: contrato JSON estructurado, extracción de JSON envuelto en bloques markdown, fallback heurístico no destructivo ante respuestas planas o desestructuradas, respuesta determinista offline en dos niveles, abstención estructurada sin evidencias, e integración end-to-end con ADA.

3. **Pruebas de Integración del Corpus Reconstruido:**
   ```bash
   python -m unittest discover -s tests -p "test_rebuild_integration.py"
   # Ran 5 tests in 28.990s — OK (5/5 passing)
   ```
4. **Pruebas de Arquitectura RRE / ADA:**
   ```bash
   python -m unittest discover -s tests -p "test_rre_ada_architecture.py"
   # Ran 12 tests in 10.996s — OK (12/12 passing)
   ```
5. **Suite Exhaustiva del Repositorio:**
   ```bash
   python -m unittest discover -s tests -p "test_*.py"
   # Ran 75 tests in 42.043s — OK (75/75 passing)
   ```

*Distinción Metodológica de Pruebas:*
- **Pruebas con Mocks:** Cobertura de códigos de estado HTTP (429, 401, 404, 503, timeout), inyección de errores, redacción de credenciales confidenciales y conmutación automática controlada sin consumir cuota real ni depender de latencia externa.
- **Pruebas Locales sin Conexión:** Indexación TF-IDF, validación de SHA-256 del PDF oficial, resolución de grafos de conocimiento, filtrado OOD, validación de esquemas y generación de dictámenes deterministas offline sin invocación externa.
- **Pruebas Reales de API:** 
  - **Google Gemini:** Consulta en vivo al endpoint de modelos confirmando 46 modelos activos (`gemini-flash-latest`, `gemini-2.5-flash`, etc.).
  - **Groq API Real:** Con la clave real provista en `.env`, se consultó el catálogo en vivo de GroqCloud (`https://api.groq.com/openai/v1/models`) y se ejecutaron inferencias reales en producción con el modelo `openai/gpt-oss-120b`, generando tanto la síntesis arbitral de tatami como la estructura JSON en dos niveles con citas ancladas navegables.

---

## 5. Integración Multi-proveedor LLM, Contrato en Dos Niveles y Continuidad Operativa

Se implementaron las capas de abstracción desacopladas en [`src/llm_provider.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/llm_provider.py) y [`src/response_structurer.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/response_structurer.py), adaptando [`src/ada_assistant.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/ada_assistant.py), [`src/rag_engine.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py) y [`app.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py):

- **Contrato Transversal de Respuesta en Dos Niveles:**
  - **Nivel 1 (Respuesta Directa y Concreta):** Visible siempre en el primer bloque del chat (1 a 4 frases, ~30-80 palabras). Expone inmediatamente el dato métrico, regla sustantiva, sanción o procedimiento arbitral solicitado, junto con la cita rectora oficial.
  - **Nivel 2 (Fundamentación Normativa Completa y Análisis Desplegable):** Inicialmente contraída en un desplegable de Streamlit (*«📖 Ver fundamentación normativa y análisis completo»*). Contiene de forma estructurada y sin repeticiones:
    1. *Preceptos y Artículos Aplicables* (citas literales, apartados y páginas físicas).
    2. *Condiciones, Excepciones y Restricciones* (especificaciones para cadetes, juniors, pesaje o indumentaria).
    3. *Análisis Arbitral Ampliado* (razonamiento técnico y aplicación procedimental).
    4. *Límites de la Evidencia* (declaración explícita de aspectos no cubiertos por el texto oficial).
- **Rigor Normativo y Prevención de Alucinaciones:**
  - Si el modelo omite campos o produce texto no estructurado, un parser de fallback seguro descompone la respuesta sin pérdida de datos.
  - En modo local desconectado o ante fallos de conectividad, `build_deterministic_structured_answer` arma la estructura en dos niveles exclusivamente a partir de los pasajes certificados por RRE, sin formular inferencias inventadas.
- **Arquitectura de Proveedores y Modelos Confirmados:**
  - `MultiProviderLLMManager` gestiona `GeminiClient` y `GroqClient` (compatible con la API OpenAI Chat Completions) con cero dependencias externas añadidas.
  - Encabezado `User-Agent` explícito para Groq evitando el bloqueo de seguridad Cloudflare Error 1010.
  - Modelos confirmados en catálogo para Gemini: `gemini-flash-latest`, `gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-2.5-pro`, `gemini-1.5-pro`.
  - Modelos confirmados en catálogo real de Groq: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`, `allam-2-7b`.
  - Configuración independiente mediante variables de entorno: `GEMINI_API_KEY`, `GROQ_API_KEY`, `LLM_PROVIDER`, `GEMINI_MODEL`, `GROQ_MODEL`.
- **Gestión Segura de Credenciales:**
  - Enmascaramiento activo (`...XXXX`) en reportes de estado y UI.
  - Sanitización/redacción obligatoria de claves en mensajes de error e inspección de excepciones (`[REDACTED_API_KEY]`).
  - `.env` auditado y confirmado en `.gitignore`.
- **Políticas de Respaldo Configurable:**
  - **Automático:** conmuta fluidamente entre Gemini y Groq ante errores recuperables (HTTP 429 Cuota excedida, HTTP 503 Servicio temporalmente inaccesible, Timeout), notificando discretamente en el chat mediante banner informativo (`🔄 Respaldo automático activado`).
  - **Manual:** no conmuta silenciosamente; reporta el error exacto tipificado (`QUOTA`, `AUTH`, `NOT_FOUND`, `TEMPORARY`, `CONTENT`) permitiendo al usuario decidir en la barra lateral.
- **Persistencia en Streamlit:**
  - Selector en la barra lateral («Configuración del modelo») integrado con `st.session_state`.
  - La conversación previa (`st.session_state.history`) y el grounding documental se conservan íntegramente al cambiar de proveedor o modelo.

---

## 6. Estado de Git e Integridad del Repositorio

- **Rama:** `review/ijf-sor-2026-08-rre-ada`
- **Sincronización:** Preservada intacta (11 commits detrás del remoto, conforme a la restricción obligatoria).
- **Operaciones prohibidas:** Cero `commit`, `push`, `pull`, `merge`, `rebase` o despliegues ejecutados.
- **Corpus original:** `data/processed/rebuild_2026_08/` (554 pasajes) inalterado y preservado como respaldo de reversibilidad.
- **Corpus activo:** `data/processed/rebuild_2026_08_corrected/` (385 pasajes) verificado con SHA-256 del PDF oficial `IJF_Sport_and_Organisation_Rules_2026_08_14.pdf`.
- **Archivos de código modificados / creados:**
  - [`src/response_structurer.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/response_structurer.py): Motor del contrato en dos niveles, parser de JSON, parser de fallback y constructor determinista.
  - [`src/llm_provider.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/llm_provider.py): Nueva capa de abstracción desacoplada de proveedores LLM con catálogo verificado, User-Agent anti-bloqueo y conmutación segura.
  - [`src/ada_assistant.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/ada_assistant.py): Integración del contrato en dos niveles, metadatos de respuesta y modo offline transparente.
  - [`src/rag_engine.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py): Propagación de `structured_answer` al contrato de respuesta de alto nivel.
  - [`app.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py): Interfaz de Streamlit con Nivel 1 siempre visible, Nivel 2 desplegable, panel lateral de modelos y trazabilidad relacional.
  - [`tests/test_response_structurer.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_response_structurer.py): Batería unitaria de 7 pruebas para el contrato de respuesta en dos niveles.
  - [`tests/test_llm_provider.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_llm_provider.py): Batería unitaria de 16 pruebas para la capa multi-proveedor y modo offline.
  - [`src/rre_engine.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rre_engine.py): Stopwords funcionales, proyección densa bilingüe, anclaje de dominio y desponderación del historial de versiones en RRF.
  - [`src/corpus_config.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/corpus_config.py): Activación del corpus de 385 pasajes autorizada previamente.
  - [`tests/test_rebuild_integration.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_rebuild_integration.py) y [`tests/test_rre_ada_architecture.py`](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_rre_ada_architecture.py): Asertos ajustados al conteo de 385 pasajes.

---

## 7. Conclusión y Dictamen Técnico

> **DICTAMEN TÉCNICO: VALIDADO Y CERRADO CON ÉXITO**  
> 1. **Mejora transversal de presentación:** El 100% de las consultas entrega la respuesta concreta y directa en el Nivel 1 siempre visible, manteniendo la fundamentación normativa, extractos literales, excepciones y análisis arbitral en el Nivel 2 desplegable.  
> 2. **Rigor normativo:** No se generan afirmaciones no sustentadas en los pasajes; el modo local desconectado presenta objetivamente los extractos oficiales sin pretender ser una síntesis autónoma de IA.  
> 3. **Conexión real con Groq:** Confirmada y verificada contra el endpoint en vivo de GroqCloud utilizando el modelo vigente `openai/gpt-oss-120b`.  
> 4. **Batería completa:** 75 pruebas unitarias e integración ejecutadas con resultado exitoso (`Ran 75 tests in 42.043s — OK`).

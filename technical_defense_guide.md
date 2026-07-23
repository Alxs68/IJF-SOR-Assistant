# Guía de Defensa Técnica del Proyecto
**Proyecto:** IJF SOR Assistant  
**Propósito:** Material de preparación para sustentación ante un jurado técnico y carga en NotebookLM.  

---

## 🏛️ PARTE I: Fundamentos y Decisiones de Diseño

### 1. Objetivo del Proyecto
El **IJF SOR Assistant** tiene como objetivo proporcionar una plataforma interactiva, robusta y de alta fidelidad para la consulta ágil de las reglas de competencia y regulaciones médicas de la Federación Internacional de Judo (IJF). El sistema permite a árbitros, entrenadores, atletas y delegados técnicos formular preguntas en lenguaje natural y recibir respuestas fundamentadas con trazabilidad absoluta y citas unívocas a las fuentes oficiales vigentes del año 2026.

### 2. Problema Real que Resuelve
La consulta tradicional de normativas deportivas presenta tres problemas críticos:
1.  **Saturación y Dificultad de Acceso:** El documento del SOR (Sport and Organisation Rules) excede las 200 páginas de jerga técnica, lo que ralentiza la toma de decisiones en tiempo real durante pesajes, sorteos o reclamos médicos.
2.  **Obsolescencia Normativa:** Los reglamentos cambian anualmente. El uso de modelos de lenguaje genéricos (como ChatGPT o Gemini comercial) introduce errores porque sus pesos pre-entrenados mezclan normativas antiguas (ej. directrices de 2023) con las reglas actuales de 2026.
3.  **Alucinación de la IA:** En sistemas regulatorios, una respuesta "plausible pero incorrecta" (alucinación) es inaceptable. Por ejemplo, afirmar falsamente que una conmoción cerebral inhabilita al atleta por 3 días en lugar de los 7 días oficiales puede acarrear sanciones de salud o demandas legales.
El proyecto resuelve esto implementando una arquitectura **RAG Híbrida** que restringe las respuestas del modelo a una base de conocimiento curada y auditada, forzándolo a responder "Lo siento, no tengo esa información" si la regla no está en la base de datos.

### 3. Requisitos Funcionales y No Funcionales

#### Requisitos Funcionales:
*   **RF-01 (Búsqueda en Lenguaje Natural):** El usuario puede redactar consultas libres en español.
*   **RF-02 (Citas e Hipervínculos Activos):** El sistema debe retornar enlaces cliqueables directos a las fuentes oficiales de la IJF (PDFs, Videos o Diapositivas oficiales) que justifican la respuesta.
*   **RF-03 (Visualización de Subgrafos):** Mostrar en pantalla el subgrafo de relaciones lógicas (excepciones, complementos) de las reglas asociadas a la consulta mediante gráficos vectoriales Graphviz.
*   **RF-04 (Historial de Sesión):** Permitir navegar entre consultas pasadas de la misma sesión en la barra lateral.
*   **RF-05 (Sugerencias):** Menú desplegable con preguntas clave autolimpiables al hacer clic en el buscador para guiar al usuario.

#### Requisitos No Funcionales:
*   **RNF-01 (Portabilidad y Cero Dependencias):** Ejecutable en Windows, Linux y macOS sin instalar binarios complejos como C++ Compilers (excluyendo FAISS, PyTorch o pysqlite3).
*   **RNF-02 (Resiliencia Offline):** Si no hay API Key de Gemini o falla la red, el sistema debe cambiar automáticamente a un buscador local TF-IDF y mostrar fichas de reglas estructuradas sin lanzar excepciones.
*   **RNF-03 (Seguridad de Credenciales):** La clave API no debe quedar expuesta en el repositorio público ni en el frontend.
*   **RNF-04 (Consistencia Normativa):** Excluir estrictamente las modalidades no competitivas (Kata / Formas) y enfocarse en Combate (Shiai).

### 4. Arquitectura General del Sistema
El proyecto está estructurado bajo un patrón de **Arquitectura en Capas Desacopladas**:

```text
┌────────────────────────────────────────────────────────┐
│                   CAPA DE PRESENTACIÓN                 │
│          Streamlit Frontend UI (app.py)                │
└──────────────────────────┬─────────────────────────────┘
                           │ (user_query)
                           ▼
┌────────────────────────────────────────────────────────┐
│                   CAPA DE ORQUESTACIÓN                 │
│              RAG Engine (rag_engine.py)                │
└──────────────────────────┬─────────────────────────────┘
                           ├─────────────────────────────┐
                           ▼                             ▼
┌─────────────────────────────────────┐ ┌─────────────────────────────────────┐
│           CAPA VECTORIAL            │ │             CAPA RELACIONAL         │
│     VectorStore (vector_store.py)   │ │    GraphManager (graph_manager.py)  │
└─────────────────────────────────────┘ └─────────────────────────────────────┘
```

### 5. Justificación de la Arquitectura Elegida
*   **Decisión:** Se prefirió una arquitectura en capas desacopladas en lugar de un monolito o el uso de frameworks RAG pesados (como LangChain o LlamaIndex).
*   **Justificación Técnica:**
    1.  **Intercambiabilidad:** Si en el futuro se decide migrar de Gemini a un modelo local ejecutado en un servidor corporativo (como Llama 3 con Ollama), solo es necesario modificar la función `call_gemini_api` de `rag_engine.py` y `_get_embedding` en `vector_store.py`. La lógica de la UI y del Grafo permanece intacta.
    2.  **Mantenibilidad y Pruebas:** Permite ejecutar suites de pruebas automatizadas aisladas para verificar el funcionamiento matemático del buscador semántico o el funcionamiento lógico del grafo sin requerir internet o levantar la UI.
    3.  **Rendimiento:** Al no tener capas de abstracción adicionales de frameworks externos, las consultas se resuelven en microsegundos en local antes de ser enviadas a la API del LLM.

### 6. Responsabilidad de cada Módulo del Proyecto
*   [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py): Capa de interfaz de usuario. Encargada de renderizar los inputs, manejar el estado de la sesión, inyectar el diseño CSS premium y convertir el código DOT de Graphviz en diagramas visuales en pantalla.
*   [src/rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py): El orquestador principal. Recibe la consulta, llama al vector store para obtener los nodos base, le pide al grafo expandir la vecindad de reglas, ensambla el prompt con directrices de fidelidad estrictas, llama al LLM y gestiona el fallback local si ocurre un error.
*   [src/vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py): Administra la indexación semántica. Mapea textos a vectores densos mediante Gemini Embeddings (o pesos dispersos TF-IDF en offline) y realiza búsquedas mediante similitud coseno. Cumple con el principio de separación de datos al no almacenar el texto de las reglas, solo sus IDs y vectores.
*   [src/graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py): Administrador del Grafo de Conocimiento. Escanea el corpus Markdown en la ingesta, compila nodos y aristas con tipado semántico, calcula métricas topológicas ( hubs, grado promedio) y genera código DOT de Graphviz de los subgrafos de consulta.

### 7. Flujo Completo de una Consulta
1.  **Input:** El usuario escribe una pregunta (ej. *¿Cómo se sanciona el abrazo de oso?*) en la barra de búsqueda superior de `app.py`.
2.  **Llamada al Orquestador:** `app.py` invoca a `engine.query(user_query, k, min_score)`.
3.  **Paso Vectorial:** `rag_engine.py` pide a `vector_store.py` buscar los `k` IDs de KUNs más similares.
4.  **Cálculo Vectorial:** `vector_store.py` genera el embedding de la consulta y calcula la similitud coseno contra los vectores de las 841 KUNs indexadas. Devuelve los IDs y sus scores.
5.  **Filtrado:** El orquestador descarta KUNs cuyo score de similitud sea inferior al `min_score` configurado en la barra lateral.
6.  **Paso Relacional (Expansión por Grafo):** El orquestador toma los IDs sobrevivientes (nodos semilla) y le pide a `graph_manager.py` recuperar sus vecinos de primer grado lógicos (ej. reglas que complementan o exceptúan la regla semilla).
7.  **Recuperación del Texto:** El orquestador extrae los textos oficiales, interpretaciones y fuentes de las KUNs desde el grafo (fuente única de verdad del contenido).
8.  **Construcción del Prompt:** Se ensambla un prompt estructurado inyectando el contexto de las KUNs recuperadas y las directrices de restricción al LLM.
9.  **Llamada al LLM:** Se envía el prompt a Gemini mediante peticiones HTTP POST nativas (`urllib.request`).
10. **Respuesta y UI:** Si es exitosa, se devuelve la respuesta a `app.py` junto al código DOT del subgrafo recuperado. Streamlit renderiza la respuesta conversacional, el desplegable de citas y el subgrafo visual de relaciones.

### 8. Explicación Detallada del Funcionamiento del Motor RAG
El motor RAG de este proyecto es **Híbrido Semántico-Relacional**:
*   La búsqueda puramente vectorial es excelente para encontrar similitudes lingüísticas generales, pero es ciega a la lógica formal. Por ejemplo, si buscas *sanciones por abrazo de oso*, la búsqueda vectorial encontrará la KUN-0045 (que detalla la sanción). 
*   Sin embargo, el reglamento del oso tiene excepciones (ej. si hay un agarre previo normal). Esta regla de excepción podría estar en otra KUN diferente que no contiene la palabra clave "abrazo de oso" directamente en su redacción textual, por lo que el buscador vectorial podría omitirla.
*   Aquí entra el Grafo de Conocimiento: al recuperar la KUN-0045 como semilla vectorial, el motor expande la consulta y extrae automáticamente su vecindad en el grafo. Como existe un enlace relacional (`KUN-0045` ➔ `exceptua_a` ➔ `KUN-0046`), el motor inyecta *ambas* KUNs en el prompt del LLM. Esto garantiza que la respuesta de la IA contenga tanto la regla general como sus excepciones lógicas de forma infalible.

### 9. Explicación del Almacenamiento Vectorial y del Cálculo de Similitud
*   **Vectores Densos (Modo Conectado):** `vector_store.py` llama al modelo `gemini-embedding-001`. El modelo convierte cada texto en un vector denso de 768 números flotantes.
*   **Fórmula de Similitud Coseno:** Mide el coseno del ángulo entre el vector de la consulta (\(A\)) y el vector del documento (\(B\)):
    \[\text{Similitud Coseno}(A, B) = \frac{A \cdot B}{\|A\| \|B\|} = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \sqrt{\sum_{i=1}^{n} B_i^2}}\]
    Un score cercano a `1.0` indica una alta coincidencia semántica.
*   **Vectores Dispersos (Modo Fallback TF-IDF):** Si no hay API Key, se tokeniza y limpia el texto (removiendo acentos y caracteres especiales). Se calcula el peso local de cada palabra usando TF-IDF:
    *   **Term Frequency (TF):** Frecuencia de la palabra en la KUN.
    *   **Inverse Document Frequency (IDF):** \(\log(1 + \frac{N}{DF})\), donde \(N\) es el total de KUNs y \(DF\) es el número de KUNs que contienen la palabra.
    La similitud coseno se calcula de la misma forma sobre estos vectores dispersos de peso léxico.

### 10. Explicación del Grafo de Conocimiento y su Integración con el RAG
El Grafo de Conocimiento está implementado en la clase `KnowledgeGraph` como un dígrafo (grafo dirigido).
*   **Nodos:** Representan las KUNs indexadas (almacenan ID, título, tipo, fuente, texto en español, texto original e interpretación).
*   **Aristas:** Representan relaciones semánticas lógicas dirigidas:
    *   `exceptua_a` / `exceptuado_por`
    *   `complementa_a` / `complementado_por`
    *   `ilustra_a` / `ilustrado_por`
*   **Reciprocidad Activa:** Para garantizar que el grafo sea navegable en ambas direcciones de forma robusta, cada vez que se añade una arista dirigida en la compilación, el sistema crea automáticamente su arista recíproca inversa (ej. si A complementa a B, crea B es complementado por A).
*   **Integración RAG:** El orquestador toma los aciertos de similitud vectorial y realiza una expansión de un paso. Recorre las listas de adyacencia de entrada (`in_edges`) y salida (`edges`) de cada nodo semilla para recuperar todos los nodos conectados, enriqueciendo el contexto del LLM con sus textos descriptivos.

### 11. Tecnologías Utilizadas y Justificación
*   **Python 3.12:** Estándar moderno de desarrollo de software con tipado dinámico y amplias facilidades para análisis de texto.
*   **Streamlit (v1.36+):** Framework de interfaz de usuario de ejecución rápida en Python, ideal para el prototipado y despliegues de tableros interactivos y conversacionales de Machine Learning.
*   **API de Gemini (Embedding-001 y Gemini-1.5-Flash):** Modelo generativo rápido con alta ventana de contexto y embeddings multilingües de excelente desempeño para el español.
*   **Graphviz:** Software estándar industrial de modelado de grafos basado en el lenguaje estructurado DOT, lo que permite renderizar diagramas vectoriales nativos en Streamlit sin recargar dependencias complejas de JavaScript.
*   **python-dotenv:** Facilita la carga de variables locales de desarrollo sin riesgo de exponer credenciales en repositorios.

### 12. Organización del Repositorio
El repositorio está estructurado bajo principios de orden y clean code:
*   `app.py`: Frontend interactivo Streamlit.
*   `/src/`: Lógica de negocio (orquestador, base de datos vectorial y gestor del grafo).
*   `/data/markdown/`: Archivos con el corpus de reglas oficial (fuente única de verdad del conocimiento).
*   `/scripts/`: Scripts utilitarios para extracción masiva de PDFs y compilación/regeneración de índices.
*   `/tests/`: Pruebas de integración, unitarias y el validador del Dataset de Oro.
*   `/docs/`: Guías de aprovisionamiento en la nube e inventarios de control.
*   `/scratch/`: Directorio local temporal para el almacenamiento de los índices serializados en JSON.

### 13. Estrategia de Pruebas Implementada
El proyecto implementa una **Suite de Pruebas Incremental**:
1.  **Pruebas Unitarias de Componentes:** 
    *   `tests/test_graph_manager.py`: Verifica que la adición de nodos, el cálculo de métricas ( hubs, orphans) y la serialización JSON funcionen.
    *   `tests/test_vector_store.py`: Valida que la tokenización, el cálculo de similitud coseno y la persistencia del índice funcionen en ambos modos (TF-IDF y Embeddings).
    *   `tests/test_rag_engine.py`: Asegura que el flujo completo del orquestador (recuperación, expansión de grafo y construcción de prompt) sea coherente.
2.  **Pruebas de Integración (Dataset de Oro):**
    *   `tests/test_golden_dataset.py`: Contiene un conjunto de 12 consultas críticas del reglamento real (ej. pesaje, judogis, osos, etc.) y evalúa que el motor RAG recupere la KUN oficial correcta en todos los casos.
    *   **Métrica de Aceptación:** Requiere una tasa de éxito de recuperación superior al 80%. La ejecución en producción arroja una tasa de éxito del **100.00% (12/12 consultas exitosas)**.

### 14. Estrategia de Despliegue en Oracle Cloud Infrastructure (OCI)
El asistente se despliega sobre una arquitectura de alta disponibilidad en **Oracle Cloud (OCI)**:
*   **Aprovisionamiento de Instancia:** Una máquina virtual gratuita `VM.Standard.A1.Flex` basada en procesadores ARM Ampere (1 OCPU, 6 GB de RAM) corriendo Ubuntu Server 24.04 LTS.
*   **Red y Puertos:** Se configuró una lista de ingreso en la VCN de OCI abriendo el puerto TCP `8501` para permitir tráfico público hacia Streamlit.
*   **Servicio del Sistema (Systemd):** Para garantizar resiliencia, la aplicación corre como un servicio en segundo plano administrado por systemd (`ijf-assistant.service`). Esto asegura que si el servidor físico se reinicia o la aplicación falla por falta de recursos, systemd recargará y levantará el asistente automáticamente en 5 segundos.
*   **Mantenimiento:** La actualización de código se realiza a través de Git (`git pull origin main` desde la instancia) y la recarga instantánea mediante `sudo systemctl restart ijf-assistant`.

### 15. Medidas de Seguridad Adoptadas
*   **Exclusión de Secretos (Git-safe):** El archivo `.env` que almacena la API Key de Gemini está incluido en `.gitignore` para evitar filtraciones en el repositorio público de GitHub.
*   **Variables de Entorno en Producción:** En el servidor OCI, el servicio systemd lee las variables desde un archivo de entorno local con permisos estrictamente restringidos de lectura (`chmod 600`) para evitar que otros usuarios de la máquina virtual accedan a la clave API.
*   **Restricción de Acceso SSH:** Las claves privadas de acceso SSH están securizadas en local mediante políticas `icacls` en Windows para denegar herencias y accesos adicionales de cuentas del sistema.
*   **Firewall de Red:** Se bloquea todo el tráfico entrante a la máquina virtual OCI excepto los puertos configurados (SSH en `22` y Streamlit en `8501`).

### 16. Limitaciones Actuales del Proyecto
1.  **Recuperación de un Solo Salto (1-Hop):** El grafo expande la vecindad únicamente a profundidad 1. Si una consulta requiere encadenar lógicamente tres reglas indirectas (A complementa a B, y B exceptúa a C), el motor RAG podría no inyectar la KUN C en el contexto del prompt.
2.  **Dependencia de Red para Embeddings:** En Modo Conectado, el cálculo de similitud vectorial para consultas requiere conexión activa para calcular el embedding del query del usuario con Gemini. Si hay un micro-corte de red, el motor conmuta a TF-IDF clásico, perdiendo precisión semántica abstracta durante ese intervalo.
3.  **Límite de Cuota API (RPM):** El plan gratuito de la API de Gemini tiene límites de peticiones por minuto (RPM). Si múltiples usuarios acceden al asistente en producción en vivo simultáneamente, podrían recibir respuestas locales simuladas debido a bloqueos de cuota HTTP 429.

### 17. Posibles Mejoras Futuras (Backlog 2.0)
1.  **Embeddings Locales Offline:** Migrar a modelos de embeddings locales (como `SentenceTransformers` de tamaño ligero) que se ejecuten localmente en la máquina virtual OCI, eliminando la dependencia de llamadas externas para vectorización y garantizando búsquedas semánticas densas 100% offline.
2.  **Expansión de Grafo Dinámica (Multi-hop):** Implementar un algoritmo de recorrido de grafos dinámico (ej. expandir relaciones específicas como `exceptua_a` hasta profundidad 2 o 3, pero ignorar relaciones de complementariedad largas) para mantener el prompt compacto y relevante.
3.  **Evaluación Automatizada RAG Triad:** Incorporar métricas de fidelidad (`faithfulness`), relevancia del contexto (`context relevance`) y relevancia de la respuesta (`answer relevance`) utilizando frameworks como Ragas para evaluar la precisión conceptual de la síntesis del LLM.

### 18. Principales Retos Técnicos Encontrados y Soluciones
*   **Reto 1 (StreamlitAPIException en Inyección de Ejemplos):**
    *   *Problema:* Al hacer clic en "Probar Ejemplo", el sistema intentaba reasignar el valor de `st.session_state.search_query_input_widget` después de que el cuadro de búsqueda ya había sido renderizado, causando que la API de Streamlit lanzara una excepción de ejecución tardía.
    *   *Solución:* Diseñamos una función de callback nativa `load_example()` y la asociamos al evento `on_click` del botón de ejemplos. Como los callbacks de Streamlit se ejecutan *antes* de que comience el renderizado secuencial del script, el estado se actualiza de forma segura y sin errores.
*   **Reto 2 (Desalineación Geométrica de Botones en la UI):**
    *   *Problema:* Al ocultar la etiqueta superior de las cajas de texto con `label_visibility="collapsed"`, las cajas subían, pero Streamlit seguía inyectando un margen superior automático a los botones de los lados para alinearlos con las etiquetas "fantasma", desplazándolos hacia abajo.
    *   *Solución:* Inyectamos estilos CSS personalizados para resetear el margen superior de los botones a `0px !important` y configuramos la fila horizontal (`st.columns`) para centrar verticalmente todos sus elementos usando `align-items: center !important`.

### 19. Decisiones de Ingeniería de Software Tomadas
*   **Decisión 1 (Fuente de Verdad Única en Markdown):** En lugar de estructurar las reglas en una base de datos relacional (como SQLite), se mantuvieron en archivos de texto estructurado Markdown (`data/markdown/`). Esto permite que los expertos del reglamento deportivo puedan revisar, modificar y auditar las reglas directamente en archivos legibles de texto plano, y el compilador del grafo las ingesta automáticamente al iniciar.
*   **Decisión 2 (Cliente HTTP Nativo urllib):** Se descartó la instalación del SDK de Google Gemini, realizando las llamadas mediante `urllib.request`. Esto simplifica radicalmente el despliegue del proyecto al no requerir dependencias complejas o librerías C++ asociadas a paquetes externos de Google, optimizando la portabilidad del código.

### 20. Glosario de Términos Técnicos
*   **RAG (Retrieval-Augmented Generation):** Técnica de Inteligencia Artificial que complementa las capacidades de generación de un LLM inyectando datos externos recuperados de una base de conocimiento en el prompt de la consulta.
*   **KUN (Knowledge Unit Node):** Unidad de Conocimiento. Bloque indivisible y estructurado que aísla una regla específica, su traducción oficial, interpretación e identificación de origen.
*   **Embedding:** Representación matemática de un texto en forma de un vector de números reales de alta dimensión, donde la distancia espacial entre vectores representa la similitud conceptual.
*   **Similitud Coseno:** Medida geométrica que calcula el coseno del ángulo entre dos vectores en un espacio multidimensional, utilizada para evaluar la relevancia semántica entre dos textos.
*   **Knowledge Graph (Grafo de Conocimiento):** Estructura de datos compuesta por nodos (KUNs) y aristas (relaciones dirigidas), utilizada para representar conexiones lógicas y excepciones entre reglas.
*   **DOT (Graphviz Language):** Lenguaje de descripción de grafos en formato texto plano, legible por humanos y computadoras, utilizado en este proyecto para modelar subgrafos interactivos en la UI.
*   **Systemd:** Sistema de inicio y administrador de servicios de fondo estándar en distribuciones GNU/Linux como Ubuntu, utilizado para asegurar la alta disponibilidad de aplicaciones en la nube.


---

## 🛡️ PARTE II: Preguntas de Defensa del Proyecto (1 a 25)
Esta sección contiene preguntas y respuestas detalladas enfocadas en **Arquitectura, Ingeniería de Software y Estructura de Datos**.

### 1. ¿Por qué se optó por una arquitectura en capas desacopladas?
*   **Respuesta Esperada:** Para separar de forma clara la presentación de la lógica de negocio y del acceso a datos.
*   **Justificación Técnica:** Permite que componentes como el motor RAG, el Vector Store y el Graph Manager puedan probarse de forma independiente en la suite de pruebas unitarias, y facilita el reemplazo de tecnologías (como cambiar la API de Gemini por un modelo local) sin afectar a la interfaz.
*   **Archivos Relacionados:** [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py), [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Separation of Concerns (Separación de Preocupaciones) e Inversión de Control.

### 2. ¿Qué ventaja ofrece usar urllib en lugar del SDK oficial de Google GenAI?
*   **Respuesta Esperada:** Reduce a cero las dependencias complejas de compilación de C++ en local y optimiza la portabilidad del código.
*   **Justificación Técnica:** El SDK oficial arrastra dependencias binarias pesadas (como grpcio o pydantic). El cliente nativo HTTP `urllib` garantiza la ejecución directa en cualquier sistema operativo con Python estándar.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py), [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Portabilidad y Dependencia Mínima.

### 3. ¿Cómo se maneja la consistencia de los datos en el sistema?
*   **Respuesta Esperada:** Mediante un principio de Fuente Única de Verdad (Single Source of Truth).
*   **Justificación Técnica:** Los textos oficiales e interpretaciones de las reglas residen únicamente en los archivos Markdown del corpus. El Vector Store solo almacena representaciones matemáticas (vectores) asociadas al ID de la KUN, evitando duplicaciones.
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py), [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Single Source of Truth (DRY - Don't Repeat Yourself).

### 4. ¿Por qué los índices vectoriales y grafos lógicos se guardan en formato JSON?
*   **Respuesta Esperada:** Por legibilidad humana, facilidad de deserialización y compatibilidad universal.
*   **Justificación Técnica:** JSON permite inspeccionar y auditar directamente el estado del índice matemático y topológico en local sin necesidad de clientes SQL de bases de datos binarias complejos.
*   **Archivos Relacionados:** `scratch/knowledge_graph.json`, `scratch/vector_store_index.json`
*   **Concepto de Ingeniería de Software:** Serialización de Datos y Transparencia Técnica.

### 5. ¿Qué patrón de diseño se utiliza en la instanciación de clases del backend?
*   **Respuesta Esperada:** Se utiliza el patrón de inyección de dependencias implícito al instanciar el motor.
*   **Justificación Técnica:** La clase `RagEngine` recibe la ruta raíz (`brain_dir`) del proyecto e instancia de forma interna e independiente las clases de almacenamiento `VectorStore` y `KnowledgeGraph`.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Patrones de Inyección y Acoplamiento Débil.

### 6. ¿Cómo previene el sistema que se carguen reglas duplicadas?
*   **Respuesta Esperada:** Mediante claves únicas compuestas por el ID de la Unidad de Conocimiento (KUN-XXXX).
*   **Justificación Técnica:** Durante la ingesta por expresiones regulares, el cargador mapea las KUNs a un diccionario indexado por la clave de ID. Si se encuentra un ID duplicado, el parser sobrescribe o arroja un aviso de colisión.
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** Integridad Referencial e Indexación por Llave Primaria.

### 7. ¿Por qué se utiliza Markdown como formato de almacenamiento de reglas originales?
*   **Respuesta Esperada:** Para facilitar la autoría de datos por parte de expertos en reglas deportivas que no son programadores.
*   **Justificación Técnica:** Los archivos Markdown son legibles por humanos, permiten dar formato estructurado (tablas, listas) y se integran perfectamente con el control de versiones Git, permitiendo ver diffs limpios de texto plano.
*   **Archivos Relacionados:** [kuns_doc_001.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_001.md), [kuns_doc_004.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_004.md)
*   **Concepto de Ingeniería de Software:** Documento de Datos de Texto Plano.

### 8. ¿Qué es el Sokuteiki y cómo está modelado en el sistema?
*   **Respuesta Esperada:** Es el calibrador de control oficial del judogi, modelado como un nodo regulatorio crítico (KUN-0012 y KUN-0013) con relaciones hacia las reglas de competencia.
*   **Justificación Técnica:** Al modelarlo como KUNs interconectadas, el RAG inyecta las medidas exactas requeridas por el Sokuteiki cuando se consulta sobre dimensiones de uniformes.
*   **Archivos Relacionados:** [kuns_doc_001.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_001.md)
*   **Concepto de Ingeniería de Software:** Modelado de Reglas de Negocio.

### 9. ¿Cómo se eliminan los acentos en español durante el análisis de texto?
*   **Respuesta Esperada:** Se utiliza una función de normalización de cadenas mediante mapeo de caracteres a sus contrapartes sin tildes.
*   **Justificación Técnica:** La normalización limpia letras con acentos (á, é, í, ó, ú, ü, ñ) para evitar fallos de coincidencia léxica causados por variaciones ortográficas de los usuarios.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Normalización de Datos y Preprocesamiento de Cadenas.

### 10. ¿Por qué se utiliza la librería `sys` para configurar los paths del proyecto?
*   **Respuesta Esperada:** Para asegurar que los scripts se puedan ejecutar desde cualquier directorio sin fallos de importación.
*   **Justificación Técnica:** `sys.path.append` añade dinámicamente la carpeta `src` del proyecto en tiempo de ejecución, eliminando dependencias de configuración de variables `PYTHONPATH` globales.
*   **Archivos Relacionados:** [test_graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_graph_manager.py), [test_golden_dataset.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_golden_dataset.py)
*   **Concepto de Ingeniería de Software:** Modularidad Dinámica y Gestión de Rutas del Sistema de Archivos.

### 11. ¿Cuál es el propósito del archivo `.gitkeep` en las carpetas vacías del repositorio?
*   **Respuesta Esperada:** Preservar la estructura de directorios necesaria en el repositorio de Git sin subir archivos innecesarios.
*   **Justificación Técnica:** Git no realiza seguimiento de carpetas que no contienen archivos. El `.gitkeep` asegura que al clonar el repositorio, las carpetas de almacenamiento (`data/`, `scratch/`, `models/`) estén listas para su uso.
*   **Archivos Relacionados:** `.gitkeep` (varias carpetas)
*   **Concepto de Ingeniería de Software:** Control de Estructura de Directorios en Repositorios.

### 12. ¿Por qué no se utiliza una base de datos relacional para el MVP?
*   **Respuesta Esperada:** Para simplificar la arquitectura, evitar dependencias externas de drivers y optimizar la resiliencia offline.
*   **Justificación Técnica:** Al ser un corpus de solo lectura en producción (841 reglas estáticas), leer archivos JSON y Markdown serializados en memoria es mucho más rápido y portable que realizar consultas SQL en una base de datos tradicional.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py), [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** KISS (Keep It Simple, Stupid) e In-memory Data Structures.

### 13. ¿Qué rol tiene la variable de estado `st.session_state.history` en `app.py`?
*   **Respuesta Esperada:** Persistir las respuestas y subgrafos generados a lo largo de la sesión para permitir navegación histórica.
*   **Justificación Técnica:** Streamlit es un framework sin estado (stateless) que recarga todo el script en cada interacción. `st.session_state` es esencial para evitar que se pierdan las consultas anteriores del usuario en cada clic.
*   **Archivos Relacionados:** [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py)
*   **Concepto de Ingeniería de Software:** Manejo de Estado de Sesión en Aplicaciones Web.

### 14. ¿Cómo maneja el sistema la codificación de caracteres en sistemas operativos Windows?
*   **Respuesta Esperada:** Forzando de forma explícita la codificación UTF-8 en la apertura de todos los archivos.
*   **Justificación Técnica:** Windows utiliza CP1252 por defecto en español, lo que causa excepciones `UnicodeDecodeError` al leer caracteres con tilde o emojis. Abrir con `encoding='utf-8'` garantiza consistencia.
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py), [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Internacionalización y Robustez de Codificación.

### 15. ¿Cómo se controla que la ejecución del bot no dependa de variables globales mutables?
*   **Respuesta Esperada:** Encapsulando todo el estado interno de la pipeline dentro de las instancias de clase `RagEngine`.
*   **Justificación Técnica:** Al instanciar `engine` como un objeto que almacena localmente su `vs` y `kg`, se previene la colisión de variables globales y se facilita la concurrencia.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Encapsulamiento y Programación Orientada a Objetos (POO).

### 16. ¿Qué es el "puente de cabeza" (head bridge) y cómo está codificado en el backend?
*   **Respuesta Esperada:** Es un movimiento defensivo prohibido en Judo, codificado bajo KUNs de penalización de alta jerarquía (KUN-0001) conectadas a sus excepciones por proyección.
*   **Justificación Técnica:** Permite al RAG discernir de forma estructurada si el movimiento ocurrió de forma voluntaria (Hansoku-make) o involuntaria (sin sanción) inyectando la lógica contextual adecuada.
*   **Archivos Relacionados:** [kuns_doc_001.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_001.md)
*   **Concepto de Ingeniería de Software:** Modelado Lógico de Excepciones del Reglamento.

### 17. ¿Por qué se definen diccionarios con el contenido detallado de los recursos en `app.py`?
*   **Respuesta Esperada:** Para enriquecer la visualización con nombres humanos e hipervínculos cliqueables cuando se muestran las citas.
*   **Justificación Técnica:** El orquestador devuelve IDs secos como `DOC-001`. El catálogo del frontend asocia a `DOC-001` su nombre oficial y su URL exacta en el CDN de la IJF.
*   **Archivos Relacionados:** [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py) (RESOURCE_DETAILS)
*   **Concepto de Ingeniería de Software:** Mapeo de Metadatos de Visualización.

### 18. ¿Cómo se asegura que las dependencias de red de la API no bloqueen la UI de Streamlit?
*   **Respuesta Esperada:** Encapsulando las peticiones HTTP en bloques `try/except` robustos y devolviendo respuestas locales predefinidas si ocurre un timeout o fallo.
*   **Justificación Técnica:** Si la API de Gemini responde lento o falla por cuota (429), Streamlit no muestra una pantalla de error genérica (red banner), sino que renderiza una ficha detallada de contingencia offline.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py) (`_generate_mock_answer`)
*   **Concepto de Ingeniería de Software:** Tolerancia a Fallos y Degradación Graciosa (Graceful Degradation).

### 19. ¿Por qué se utiliza el método `st.rerun()` en la interfaz gráfica?
*   **Respuesta Esperada:** Para forzar a Streamlit a redesplegar inmediatamente la pantalla tras un cambio programático del estado de los widgets.
*   **Justificación Técnica:** Cuando el usuario selecciona una pregunta de ejemplo predefinida, el callback actualiza la caja del buscador principal. `st.rerun()` obliga a Streamlit a redibujar el buscador con el nuevo texto de forma inmediata.
*   **Archivos Relacionados:** [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py)
*   **Concepto de Ingeniería de Software:** Ciclo de Renderizado Basado en Eventos.

### 20. ¿Cómo se implementa el principio de Inversión de Control (IoC) en la inyección de estilos?
*   **Respuesta Esperada:** Inyectando directamente código CSS nativo en el markup html de la aplicación en lugar de depender del sistema de temas predeterminado de Streamlit.
*   **Justificación Técnica:** Permite un control absoluto y uniforme sobre las fuentes, sombras, y márgenes de los inputs de búsqueda y los botones sin importar los colores por defecto definidos en el archivo config.toml del cliente.
*   **Archivos Relacionados:** [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py)
*   **Concepto de Ingeniería de Software:** Inversión de Control Estética (CSS Injection).

### 21. ¿Qué es una KUN en el contexto de la base de conocimiento del proyecto?
*   **Respuesta Esperada:** Es un nodo o registro atómico estructurado en Markdown que aísla un fragmento específico de regla para el RAG.
*   **Justificación Técnica:** Permite granularizar el reglamento en piezas autocontenidas de conocimiento, facilitando la indexación matemática limpia y precisa y eliminando la contaminación de temas no relacionados en el prompt.
*   **Archivos Relacionados:** [kuns_doc_001.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_001.md)
*   **Concepto de Ingeniería de Software:** Estructura de Datos Autocontenida (Atómica).

### 22. ¿Cómo se modela la conmoción cerebral en el reglamento y cómo se valida?
*   **Respuesta Esperada:** Como una regla de inhabilitación obligatoria de 7 días (KUN-0050), validada a través de búsquedas médicas específicas y pruebas de regresión.
*   **Justificación Técnica:** Es una de las 12 consultas del dataset de oro; asegurar que recupere la KUN correspondiente valida la precisión de la indexación del manual médico.
*   **Archivos Relacionados:** [kuns_doc_004.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_004.md), [test_golden_dataset.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_golden_dataset.py)
*   **Concepto de Ingeniería de Software:** Pruebas de Regresión de Reglas Médicas.

### 23. ¿Qué beneficio ofrece encapsular las llamadas de la API de Gemini en una función `_get_embeddings_batch`?
*   **Respuesta Esperada:** Optimiza la velocidad de indexación enviando múltiples textos en una única solicitud de red, reduciendo la latencia general.
*   **Justificación Técnica:** Enviar 841 textos por separado requiere 841 conexiones HTTP. La API batch realiza peticiones compuestas agrupadas por lotes, disminuyendo radicalmente el tiempo de inicialización de la base vectorial.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Batch Processing (Procesamiento por Lotes).

### 24. ¿Qué sucede si la estructura JSON de `knowledge_graph.json` se corrompe en el disco?
*   **Respuesta Esperada:** El sistema detecta el error o ausencia de archivo y lo recompila automáticamente en vivo a partir de los archivos Markdown de origen.
*   **Justificación Técnica:** En `rag_engine.py`, la carga del grafo está envuelta en validaciones de existencia. Si falla, invoca a `compile_graph_from_markdown()` para autorreparar la base de datos de grafos al vuelo.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py), [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** Tolerancia a Fallos y Autocuración de Datos (Self-Healing System).

### 25. ¿Por qué se definen las interpretaciones oficiales de las reglas separadas de la traducción literal?
*   **Respuesta Esperada:** Para entrenar al LLM en el entendimiento conceptual deportivo práctico y mitigar el lenguaje denso legalista.
*   **Justificación Técnica:** Las traducciones directas de la IJF suelen ser complejas de entender por el público general. Al inyectar la interpretación curada, se le da al LLM la semántica simplificada que le permite redactar respuestas mucho más explicativas y claras.
*   **Archivos Relacionados:** [kuns_doc_001.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_001.md)
*   **Concepto de Ingeniería de Software:** Enriquecimiento de Datos de Contexto.


### 26. ¿Qué diferencia fundamental hay entre un buscador semántico y uno por palabras clave (léxico)?
*   **Respuesta Esperada:** El semántico busca por el significado o concepto latente, mientras que el léxico busca por coincidencia exacta de letras o términos.
*   **Justificación Técnica:** Si buscas *lesión en la rodilla*, el semántico puede recuperar reglas sobre vendajes médicos o inhabilitación médica aunque la palabra *lesión* no esté escrita literalmente. El buscador léxico fallará si el término exacto no coincide.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Latent Semantic Retrieval (Recuperación Semántica Latente).

### 27. ¿Por qué se utiliza similitud coseno en lugar de distancia euclidiana para RAG?
*   **Respuesta Esperada:** Porque la similitud coseno evalúa la orientación o ángulo de los vectores e ignora la longitud del texto, evitando castigar documentos más largos.
*   **Justificación Técnica:** La distancia euclidiana es muy sensible a la magnitud (longitud de la KUN en palabras). La similitud coseno normaliza los vectores a longitud 1, midiendo puramente la dirección conceptual.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Geometría Vectorial y Normalización de Características.

### 28. ¿Qué modelo de embeddings utiliza la aplicación en Modo Conectado y de cuántas dimensiones es?
*   **Respuesta Esperada:** Utiliza `gemini-embedding-001` de Google, el cual genera vectores de 768 dimensiones.
*   **Justificación Técnica:** Es el modelo nativo optimizado para similitud semántica multilingüe de Gemini, ofreciendo un excelente rendimiento y latencia en el procesamiento de texto en español.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Embedding Multidimensional.

### 29. ¿Cómo se calcula y normaliza el vector TF-IDF en el modo offline de fallback?
*   **Respuesta Esperada:** Se calcula el peso local (`TF`) multiplicado por el peso global (`IDF`), y luego se divide el vector entre su longitud euclidiana (norma L2).
*   **Justificación Técnica:** La normalización L2 garantiza que al calcular el producto punto de dos vectores en la consulta de búsqueda, el resultado sea exactamente la similitud coseno, acelerando la comparación.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** L2 Normalization (Normalización L2).

### 30. ¿Qué significa el parámetro K (Resultados Semánticos) en la barra lateral?
*   **Respuesta Esperada:** Es el número máximo de documentos semilla recuperados inicialmente por similitud en la base vectorial.
*   **Justificación Técnica:** Controla cuántos candidatos se extraen del Vector Store antes de la expansión por grafo. Un K demasiado alto satura la ventana de contexto del prompt; un K muy bajo puede omitir reglas clave.
*   **Archivos Relacionados:** [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py), [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Tuning de Parámetros RAG.

### 31. ¿Qué es el "Umbral Score" (score de corte mínimo) y cuál es su justificación técnica?
*   **Respuesta Esperada:** Es el valor mínimo de similitud coseno requerido para que una KUN sea considerada relevante y no sea descartada.
*   **Justificación Técnica:** Actúa como filtro para descartar ruido. Si un usuario realiza una pregunta fuera de contexto (ej. *¿Cómo se juega al fútbol?*), el score de similitud con las KUNs de judo será inferior al umbral (ej. < 0.10), bloqueando la consulta y devolviendo la frase segura de "No tengo esa información".
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Filtro de Confianza (Confidence Thresholding).

### 32. ¿Cómo se indexan los textos en el Vector Store y qué campos se incluyen?
*   **Respuesta Esperada:** Se indexa una combinación del campo de traducción oficial en español (`contenido_traduccion`) y la interpretación técnica (`interpretacion`).
*   **Justificación Técnica:** Al fusionar ambos campos, se enriquece el vector con palabras clave técnicas y su semántica explicada de forma simple, mejorando radicalmente la tasa de recuperación.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Selección de Características de Texto (Feature Selection).

### 33. ¿Por qué el Vector Store almacena los vectores en un diccionario y no en memoria de forma cruda?
*   **Respuesta Esperada:** Para poder guardarlos y cargarlos de forma persistente en JSON asociándolos al ID único de la KUN de forma rápida.
*   **Justificación Técnica:** Permite mapear de forma indexada y directa el ID de la KUN a su respectiva lista de floats del vector.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Mapeo Clave-Valor de Estructuras Serializadas.

### 34. ¿Qué es la tokenización y cómo está implementada en el modo TF-IDF local?
*   **Respuesta Esperada:** Es el proceso de fragmentar el texto en palabras individuales, convertir a minúsculas, remover acentos y descartar conectores cortos.
*   **Justificación Técnica:** La regex `[a-z0-9]{2,}` extrae términos significativos de 2 o más caracteres, limpiando puntuaciones y normalizando las palabras para calcular frecuencias léxicas correctas.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Tokenización Léxica y Preprocesamiento de NLP.

### 35. ¿Cómo se detecta que el índice guardado en el disco no corresponde al modo activo de la API Key?
*   **Respuesta Esperada:** La clase `RagEngine` evalúa el valor del campo `vs.mode` y lo compara con la existencia de la API Key al inicializar.
*   **Justificación Técnica:** Si se levanta la app con API Key pero el archivo JSON de vectores tiene el modo `"tfidf"`, o viceversa, el sistema realiza automáticamente una reindexación al vuelo para sincronizar los vectores al modo correspondiente.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py) (load_resources)
*   **Concepto de Ingeniería de Software:** Auto-sincronización de Estado en Caliente.

### 36. ¿Por qué el Vector Store no utiliza base de datos SQlite con módulo vss?
*   **Respuesta Esperada:** Por problemas severos de compilación e instalación cruzada del binario `sqlite-vss` en entornos de desarrollo Windows.
*   **Justificación Técnica:** El módulo de vectores de SQLite requiere compilación nativa C++ que suele fallar en la terminal del desarrollador. Guardar la lista de floats directamente en memoria y compararla secuencialmente es muy eficiente debido al tamaño pequeño de la base (841 nodos).
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Portabilidad de Binarios de Base de Datos.

### 37. ¿Qué es el desvanecimiento de gradiente o dimensionalidad y cómo afecta al Vector Store?
*   **Respuesta Esperada:** Afecta a la maldición de la dimensionalidad, donde en espacios muy grandes (768 dimensiones), las distancias tienden a verse uniformes si los datos están dispersos.
*   **Justificación Técnica:** La similitud coseno mitiga este efecto al enfocarse puramente en el ángulo direccional relativo del vector, ignorando la magnitud espacial euclidiana.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Maldición de la Dimensionalidad (Curse of Dimensionality).

### 38. ¿Cómo maneja el sistema las consultas vacías en la caja de búsqueda?
*   **Respuesta Esperada:** Si el input de búsqueda está vacío, el motor utiliza de forma inteligente el placeholder de ejemplo activo seleccionado en el menú desplegable.
*   **Justificación Técnica:** Evita enviar prompts vacíos o lanzar errores al LLM y proporciona una navegación sumamente fluida cuando se interactúa con las sugerencias.
*   **Archivos Relacionados:** [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py) (lógica de query_to_run)
*   **Concepto de Ingeniería de Software:** Control de Entradas del Usuario (Input Sanitization).

### 39. ¿Qué ventaja ofrece usar embeddings generativos respecto a buscar coincidencias por sinónimos fijos?
*   **Respuesta Esperada:** Los embeddings capturan el contexto y las relaciones de sinonimia de forma matemática implícita sin requerir tablas gigantescas de sinónimos mapeadas a mano.
*   **Justificación Técnica:** El modelo de embeddings está entrenado en miles de millones de oraciones en español. Sabe de forma nativa que *calibrador*, *calibrar* y *medidor* comparten cercanía espacial semántica con *Sokuteiki*.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Representación Semántica Distribuida (Distributed Semantics).

### 40. ¿Cómo escala el Vector Store si el número de KUNs aumenta a 100,000 en el futuro?
*   **Respuesta Esperada:** En ese volumen de datos, la búsqueda lineal (\(O(N)\)) causaría retrasos en la UI. Sería necesario migrar a un indexador KNN aproximado (como HNSW) escrito puramente en Python o con librerías compiladas.
*   **Justificación Técnica:** Para 841 KUNs, la búsqueda toma menos de 2 milisegundos. Para 100,000 KUNs a 768 dimensiones, realizar 100,000 productos puntos secuenciales generaría latencias notables en Streamlit.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Complejidad Computacional O-Grande e Indexación Distribuida (Approximate Nearest Neighbors).

### 41. ¿Cuál es el formato en que se guardan los vectores en `vector_store_index.json`?
*   **Respuesta Esperada:** Un objeto JSON que mapea la versión del modo, y un diccionario donde cada llave es el ID de la KUN y su valor es la lista de floats (en modo embeddings) o de índices y pesos (en modo TF-IDF).
*   **Justificación Técnica:** Al serializar el diccionario de forma limpia, la carga mediante `json.load` es instantánea y no requiere compilaciones binarias adicionales.
*   **Archivos Relacionados:** `scratch/vector_store_index.json`
*   **Concepto de Ingeniería de Software:** Formato de Serialización de Metadatos.

### 42. ¿Qué ocurre si la consulta del usuario tiene exactamente el mismo largo que una regla de la base de datos?
*   **Respuesta Esperada:** La similitud coseno comparará la dirección de ambos vectores. Si los términos y conceptos coinciden, el valor de similitud será cercano a 1.0.
*   **Justificación Técnica:** La longitud del texto no influye en la similitud coseno debido a la normalización euclidiana matemática que se aplica a los vectores antes del cálculo.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Invariancia al Tamaño en Similitud Semántica.

### 43. ¿Por qué se utiliza el parámetro de `top_p` en la configuración de la generación del modelo en la API?
*   **Respuesta Esperada:** Para limitar las palabras elegibles a aquellas que acumulan una probabilidad acumulada del 95%, mejorando la coherencia y previniendo alucinaciones léxicas descabelladas.
*   **Justificación Técnica:** `top_p` (también llamado Nucleus Sampling) descarta los tokens poco probables en la generación, lo que, sumado a una baja temperatura (`0.1`), asegura respuestas muy precisas y estrictamente apegadas al contexto provisto.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Hiperparámetros de Decodificación de LLMs (Sampling Parameters).

### 44. ¿Qué sucede si la API de Gemini devuelve un código de error de red 403 en Modo Conectado?
*   **Respuesta Esperada:** El orquestador captura el error HTTP, lo escribe en la consola de logs y activa automáticamente el modo simulado de fallback offline.
*   **Justificación Técnica:** En `rag_engine.py`, la captura de `urllib.error.HTTPError` intercepta códigos no exitosos y retorna `None`. Al retornar `None` la llamada al API, el flujo cambia a la generación de respuesta estructurada offline.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Robustez de Clientes de API y Manejo Eficiente de Errores de Red.

### 45. ¿Por qué la tokenización remueve las puntuaciones en el preprocesamiento de textos?
*   **Respuesta Esperada:** Para evitar que caracteres de puntuación (puntos, comas, signos de interrogación) se unan a las palabras y afecten al conteo léxico de términos del TF-IDF.
*   **Justificación Técnica:** La palabra `"tatami."` (con punto) y `"tatami"` (sin punto) serían tratadas como dos palabras totalmente diferentes por el diccionario del vocabulario si no se aplicara la remoción de caracteres no alfanuméricos.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Limpieza y Normalización de Características Léxicas.

### 46. ¿Qué rol juegan las stopwords en el modo TF-IDF local?
*   **Respuesta Esperada:** Las stopwords (artículos, preposiciones como *el*, *de*, *con*) son ignoradas implícitamente por el IDF global ya que aparecen en casi todas las KUNs, teniendo un peso IDF cercano a cero.
*   **Justificación Técnica:** Como el IDF de términos extremadamente comunes es despreciable, el sistema descarta su influencia matemática de forma natural sin requerir una lista dura de stopwords que aumente el peso del código.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Ponderación Dinámica del IDF Global.

### 47. ¿Qué ventaja ofrece la inyección del placeholder de forma dinámica en Streamlit?
*   **Respuesta Esperada:** Permite guiar al usuario visualmente con la última pregunta predefinida seleccionada sin forzarlo a borrar texto de la celda de entrada al escribir.
*   **Justificación Técnica:** Al pasar la pregunta como el parámetro `placeholder` en `st.text_input` y dejar `value=""`, el navegador muestra el texto en un estilo suave que desaparece automáticamente en cuanto el usuario presiona una tecla.
*   **Archivos Relacionados:** [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py), [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py)
*   **Concepto de Ingeniería de Software:** User Experience (UX) Pattern.

### 48. ¿Cómo maneja el Vector Store la indexación si se detecta un archivo de reglas vacío?
*   **Respuesta Esperada:** El cargador del grafo omite nodos vacíos, por lo que el Vector Store no recibe datos corruptos ni genera vectores vacíos que lancen excepciones matemáticas de división por cero.
*   **Justificación Técnica:** Validaciones defensivas en `index_kun_corpus` comprueban que el texto no esté vacío antes de generar los embeddings o el vocabulario.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py), [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** Programación Defensiva (Defensive Programming).

### 49. ¿Por qué se utiliza una temperatura tan baja (0.1) en la llamada del modelo RAG?
*   **Respuesta Esperada:** Para obligar al modelo a ser extremadamente determinista y apegado a la información inyectada en el prompt.
*   **Justificación Técnica:** Una temperatura alta (ej. 0.8) incrementa la aleatoriedad en la elección de tokens, lo que aumenta la probabilidad de que el LLM cometa alucinaciones o suponga reglas de judo que no están certificadas en la base de conocimiento.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Control de Creatividad en LLMs de Regulación Técnica.

### 50. ¿Qué sucede si la API de Gemini tiene problemas de cuota por segundo durante una reindexación masiva?
*   **Respuesta Esperada:** El orquestador de ingesta implementa esperas fijas entre solicitudes y reintentos automáticos ante códigos de estado HTTP 429.
*   **Justificación Técnica:** El script utilitario de reindexación e ingesta masiva utiliza retardos secuenciales (`time.sleep`) calculados para mantenerse cómodamente por debajo de los límites del plan de uso gratuito de la API.
*   **Archivos Relacionados:** [recompile_all.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/scripts/recompile_all.py)
*   **Concepto de Ingeniería de Software:** Control de Flujo de Red (Rate Limiting Handling).


### 51. ¿Qué es un dígrafo y por qué se utiliza para el Grafo de Conocimiento?
*   **Respuesta Esperada:** Un dígrafo es un grafo dirigido. Se utiliza porque las relaciones entre las reglas del judo tienen una dirección lógica y un significado semántico asimétrico.
*   **Justificación Técnica:** Si la KUN-0045 (abrazo de oso) *exceptua_a* la KUN-0046 (sanción por falta de agarre), la relación inversa no es "exceptúa a", sino "es exceptuada por". La direccionalidad es clave para entender la jerarquía normativa.
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** Teoría de Grafos y Relaciones Dirigidas.

### 52. ¿Cómo se implementa la reciprocidad de aristas en el compilador de grafos?
*   **Respuesta Esperada:** Al registrar un enlace dirigido entre dos nodos en la ingesta, el compilador crea automáticamente un enlace inverso correspondiente con su tipo de relación recíproca.
*   **Justificación Técnica:** Garantiza que al consultar el grafo por cualquiera de los dos extremos (ej. desde el nodo de la excepción o desde el nodo de la regla general), el motor RAG pueda navegar la arista en ambas direcciones de forma transparente.
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py) (add_edge)
*   **Concepto de Ingeniería de Software:** Consistencia de Datos Bidireccionales.

### 53. ¿Qué métricas topológicas calcula el Graph Manager para el administrador?
*   **Respuesta Esperada:** Calcula el número total de nodos, aristas, grado promedio de conectividad, número de componentes conectados y los nodos con mayor grado de enlace (hubs).
*   **Justificación Técnica:** Permite identificar las reglas más importantes o que actúan como "hubs" normativos centrales (como la KUN-0001 sobre penalizaciones generales en cadetes) y detectar nodos huérfanos (reglas desconectadas).
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py) (get_metrics)
*   **Concepto de Ingeniería de Software:** Análisis Topológico de Grafos.

### 54. ¿Qué es un componente conectado en el contexto del grafo de conocimiento de judo?
*   **Respuesta Esperada:** Es un subgrupo de reglas en el que cualquier nodo es alcanzable desde cualquier otro siguiendo las aristas, representando un "tema" o isla normativa aislada de otros temas.
*   **Justificación Técnica:** Permite evaluar la cohesión de las reglas. Por ejemplo, el subgrafo de pesaje y sorteos es un componente conectado independiente del subgrafo de penalizaciones médicas o técnicas de combate.
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** Teoría de Componentes Conectados (Connected Components).

### 55. ¿Cómo genera el Graph Manager el código DOT para renderizar subgrafos en pantalla?
*   **Respuesta Esperada:** Recorre las aristas de los nodos activos en el contexto de consulta y genera una cadena de texto formateada con la sintaxis del lenguaje DOT de Graphviz.
*   **Justificación Técnica:** Define la dirección de las aristas mediante operadores `->`, los colores de los nodos según su tipo (ej. azul para regulaciones, rojo para penalizaciones, verde para el manual médico) y los nombres de las etiquetas.
*   **Archivos Relacionados:** [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py) (lógica de compilación DOT)
*   **Concepto de Ingeniería de Software:** Generación de Código Basada en Plantillas (Template-Based Code Generation).

### 56. ¿Por qué el compilador del grafo utiliza expresiones regulares para extraer las KUNs de los Markdown?
*   **Respuesta Esperada:** Porque los bloques de definición de las KUNs están embebidos en el interior de los Markdown en formato JSON limpios delimitados por marcas especiales.
*   **Justificación Técnica:** El patrón de búsqueda regex ````json([\s\S]*?)```` localiza exactamente el bloque JSON de metadatos de la KUN en el texto de las reglas, permitiendo parsearlo de forma estructurada con `json.loads`.
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py) (compile_graph_from_markdown)
*   **Concepto de Ingeniería de Software:** Expresiones Regulares y Extracción Semi-estructurada.

### 57. ¿Cómo se filtran las KUNs del grafo que pertenecen a modalidades no deseadas como Kata?
*   **Respuesta Esperada:** El compilador del grafo comprueba el campo `modalidad` de los metadatos de la KUN en la ingesta y descarta el nodo si pertenece a Kata.
*   **Justificación Técnica:** Esto garantiza que el grafo no se contamine con reglas de formas no deseadas, restringiendo el alcance estrictamente a las reglas de Shiai (combate competitivo).
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** Filtrado Defensivo de Datos en la Ingesta.

### 58. ¿Qué es un "nodo hub" en el análisis del grafo de conocimiento?
*   **Respuesta Esperada:** Un nodo con un número excepcionalmente alto de conexiones (aristas) entrantes o salientes comparado con el promedio del grafo.
*   **Justificación Técnica:** Representa una regla central de la cual dependen muchas otras reglas o excepciones (ej. KUN-0001 sobre el puente de cabeza que conecta con múltiples técnicas y sanciones).
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** Centralidad de Grado en Grafos (Degree Centrality).

### 59. ¿Por qué es importante expandir a profundidad 1 (1-Hop) y no a profundidad 2 o más en este MVP?
*   **Respuesta Esperada:** Para evitar inyectar ruido excesivo en el prompt de Gemini y mantener la latencia y los costos de Tokens bajos.
*   **Justificación Técnica:** La expansión de profundidad 2 o superior (2-Hop) tiende a recuperar casi todo el grafo interconectado debido a nodos de alto grado (hubs), lo que desbordaría la ventana de contexto con reglas irrelevantes.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Control de Explosión de Contexto (Context Expansion Control).

### 60. ¿Cómo gestiona el grafo los enlaces rotos de aristas hacia KUNs inexistentes?
*   **Respuesta Esperada:** El compilador del grafo comprueba si el ID de destino existe en el diccionario de nodos antes de agregar la arista.
*   **Justificación Técnica:** Evita que el grafo contenga referencias lógicas rotas (aristas apuntando al vacío) que causarían excepciones `KeyError` al intentar recuperar el texto de esas KUNs durante el flujo RAG.
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** Integridad Referencial de Estructuras de Datos.

### 61. ¿Qué es la conectividad promedio en las métricas del grafo de conocimiento?
*   **Respuesta Esperada:** El número total de aristas dividido por el número total de nodos.
*   **Justificación Técnica:** Evalúa qué tan densamente interconectado está el reglamento. En el corpus final (841 nodos, 144 aristas) es bajo (aprox. 0.17) debido a la gran cantidad de nuevas reglas procedentes de la ingesta masiva de secciones completas del SOR que se indexan de forma atómica.
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** Densidad de Grafos.

### 62. ¿Cómo se representan las listas de adyacencia de entrada (`in_edges`) en el código?
*   **Respuesta Esperada:** Como un diccionario donde cada clave es el ID de la KUN de destino y su valor es una lista de diccionarios que detallan las aristas entrantes.
*   **Justificación Técnica:** Permite realizar búsquedas inversas rápidas (\(O(1)\)) para averiguar qué reglas apuntan a un nodo semilla, optimizando la expansión bidireccional en el orquestador.
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** Eficiencia en Estructuras de Listas de Adyacencia.

### 63. ¿Qué beneficio tiene el subgrafo interactivo de Graphviz en Streamlit?
*   **Respuesta Esperada:** Proporciona un soporte visual inmediato al usuario de la lógica regulatoria recuperada en cada consulta.
*   **Justificación Técnica:** Renderiza vectorialmente las conexiones y su tipado semántico (ej. "exceptúa a") de forma que el árbitro o entrenador comprende al instante por qué se asocian esas reglas.
*   **Archivos Relacionados:** [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py)
*   **Concepto de Ingeniería de Software:** Visualización de Estructuras de Datos Complejas.

### 64. ¿Cómo asegura el sistema que la visualización del subgrafo no rompa el diseño si se recuperan demasiados nodos?
*   **Respuesta Esperada:** Streamlit gestiona el renderizado de Graphviz de forma autoadaptativa al contenedor responsivo, permitiendo scroll horizontal si el grafo es muy grande.
*   **Justificación Técnica:** Al usar SVG vectorial renderizado por el navegador, el grafo se escala de forma limpia sin perder resolución de texto ni distorsionar paddings.
*   **Archivos Relacionados:** [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py)
*   **Concepto de Ingeniería de Software:** Responsiveness y Escalabilidad Visual de Componentes.

### 65. ¿Por qué se prefiere serializar el grafo en JSON en lugar de usar Pickling de Python?
*   **Respuesta Esperada:** Por seguridad y legibilidad multiplataforma.
*   **Justificación Técnica:** `pickle` de Python puede ejecutar código arbitrario malicioso al deserializar y es incompatible entre diferentes versiones de Python. JSON es texto plano estructurado universalmente seguro.
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** Seguridad de Deserialización y Estándares de Intercambio de Datos.

### 66. ¿Por qué se decidió no utilizar una base de datos de grafos nativa como Neo4j?
*   **Respuesta Esperada:** Para evitar la complejidad de infraestructura de red de un servidor de base de datos externo y dependencias de controladores complejos en local.
*   **Justificación Técnica:** Para un corpus estático de menos de 1,000 nodos, la representación en memoria mediante listas de adyacencia de diccionarios en Python ofrece tiempos de respuesta instantáneos de microsegundos, eliminando costos y configuraciones de red de Neo4j.
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** Simplificación de Infraestructura de Datos.

### 67. ¿Cómo se maneja la traducción original en el Grafo de Conocimiento?
*   **Respuesta Esperada:** Se guarda bajo el campo `contenido_original` para conservar el texto original del PDF en inglés de la IJF.
*   **Justificación Técnica:** Conserva la fuente de verdad textual inalterada. En caso de disputas semánticas de traducción, la aplicación expone en la trazabilidad el texto original en inglés al usuario.
*   **Archivos Relacionados:** [kuns_doc_001.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_001.md), [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py)
*   **Concepto de Ingeniería de Software:** Auditoría de Datos Multilingüe.

### 68. ¿Qué es el "grado de un nodo" y cómo influye en la recuperación del contexto?
*   **Respuesta Esperada:** Es el número total de conexiones que posee una KUN en el grafo.
*   **Justificación Técnica:** Los nodos con alto grado inyectan una mayor cantidad de vecinos al contexto. Esto garantiza que las reglas más complejas arrastren siempre sus reglas de seguridad relacionadas.
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py), [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Propagación de Contexto Basada en Grados.

### 69. ¿Cómo se compila el grafo en caliente en la inicialización si no existe el archivo JSON de scratch?
*   **Respuesta Esperada:** El orquestador escanea recursivamente el directorio del cerebro buscando archivos `kuns_*.md` y extrae los JSONs utilizando expresiones regulares.
*   **Justificación Técnica:** `compile_graph_from_markdown()` automatiza la ingesta regenerando `knowledge_graph.json` desde el código fuente Markdown de forma totalmente autónoma.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py), [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** Auto-compilación de Datos.

### 70. ¿Qué representa la relación `ilustra_a` en la semántica de las aristas?
*   **Respuesta Esperada:** Asocia un nodo de regla conceptual a un nodo de recurso multimedia (como un clip de video o diapositiva de seminario oficial) que ejemplifica físicamente el movimiento.
*   **Justificación Técnica:** Permite al RAG justificar respuestas complejas inyectando referencias multimedia de soporte técnico que aclaran la interpretación de faltas de combate complejas.
*   **Archivos Relacionados:** [kuns_doc_001.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_001.md)
*   **Concepto de Ingeniería de Software:** Relaciones Semánticas Multimedia.

### 71. ¿Cómo se asegura el sistema de que no existan ciclos infinitos al recorrer el grafo?
*   **Respuesta Esperada:** Manteniendo una profundidad fija controlada (ej. `depth=1`) y agregando los IDs recuperados a un conjunto Python (`set()`), el cual elimina duplicaciones lógicas por naturaleza.
*   **Justificación Técnica:** Al realizar un recorrido BFS (Breadth-First Search) controlado a profundidad 1 y consolidar en un `set`, se previene que aristas cíclicas (A complementa a B, y B complementa a A) entren en loops infinitos.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py) (retrieve_context)
*   **Concepto de Ingeniería de Software:** Prevención de Ciclos en Algoritmos de Grafos (Cycle Avoidance).

### 72. ¿Qué ocurre si un nodo semilla recuperado por el vector store no posee ningún vecino en el grafo?
*   **Respuesta Esperada:** El motor RAG lo inyecta como un nodo aislado y continúa el proceso sin lanzar excepciones.
*   **Justificación Técnica:** Validaciones defensivas en `retrieve_context` comprueban si la lista de adyacencia de salida contiene elementos. Si está vacía, simplemente no realiza expansión para ese nodo semilla.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Manejo Defensivo de Estructuras Sparsely Connected (Grafo Disperso).

### 73. ¿Por qué es importante almacenar la jerarquía de las secciones del SOR en los metadatos de los nodos?
*   **Respuesta Esperada:** Para facilitar la trazabilidad y la generación de referencias comprensibles para los jueces deportivos en sus decisiones.
*   **Justificación Técnica:** Almacenar datos como `"Sección 1 - Organización del tatami"` permite estructurar la cita textual de forma que el LLM pueda justificar la procedencia exacta de la regla.
*   **Archivos Relacionados:** [kuns_doc_001.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_001.md)
*   **Concepto de Ingeniería de Software:** Esquema de Metadatos Enriquecidos.

### 74. ¿Qué es el Sokuteiki y cómo se relaciona con el judogi azul y blanco?
*   **Respuesta Esperada:** El Sokuteiki es el calibrador oficial que mide las holguras del judogi. Los colores azul y blanco determinan la colocación de los atletas y son validados por el judogi control.
*   **Justificación Técnica:** Conectar estas KUNs mediante relaciones de complementariedad permite responder de forma integral a preguntas sobre requisitos de uniformes.
*   **Archivos Relacionados:** [kuns_doc_001.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_001.md)
*   **Concepto de Ingeniería de Software:** Mapeo de Relaciones de Reglas Cruzadas.

### 75. ¿Cómo se validan los enlaces de la base de datos de grafos de forma automatizada?
*   **Respuesta Esperada:** Mediante el script de auditoría de conformidad del corpus.
*   **Justificación Técnica:** El auditor escanea el grafo lógicamente en busca de relaciones rotas (aristas cuyo destino no existe) y reporta incidencias de inconsistencia relacional antes de compilar la entrega.
*   **Archivos Relacionados:** [AUD-001_Corpus_Conformity_Report.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/reports/AUD-001_Corpus_Conformity_Report.md)
*   **Concepto de Ingeniería de Software:** Validación Automatizada de Integridad de Datos.


### 76. ¿Cómo se configuró el auto-arranque y resiliencia del servicio en Oracle Cloud (OCI)?
*   **Respuesta Esperada:** Creando un servicio Systemd nativo (`ijf-assistant.service`) configurado en modo auto-arranque (`enable`).
*   **Justificación Técnica:** Systemd supervisa el estado del proceso en producción. Si la aplicación cae o el servidor se reinicia, el demonio ejecuta `systemctl start` automáticamente tras 5 segundos de retardo.
*   **Archivos Relacionados:** [oci_deployment.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/deployment/oci_deployment.md)
*   **Concepto de Ingeniería de Software:** Alta Disponibilidad y Resiliencia en Servidores de Producción.

### 77. ¿Dónde se almacena de forma segura la API Key de Gemini en producción en OCI?
*   **Respuesta Esperada:** En un archivo de variables de entorno `.env` en la máquina virtual con permisos de acceso restringidos.
*   **Justificación Técnica:** Al pasar `EnvironmentFile=/home/ubuntu/IJF-SOR-Assistant/.env` en el servicio de systemd, las variables se inyectan en memoria del proceso de Streamlit de forma segura, y el comando `chmod 600` previene que otros usuarios del servidor lean la clave en el disco.
*   **Archivos Relacionados:** [oci_deployment.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/deployment/oci_deployment.md)
*   **Concepto de Ingeniería de Software:** Gestión de Secretos en Entornos de Producción (Secret Management).

### 78. ¿Cómo se gestionan las restricciones de permisos para las llaves privadas de SSH en Windows?
*   **Respuesta Esperada:** Desactivando la herencia del archivo `.key` y otorgando permisos de lectura exclusivos al usuario activo de Windows mediante comandos `icacls`.
*   **Justificación Técnica:** OpenSSH en Windows (al igual que en Unix) rechaza conexiones SSH si el archivo de clave privada tiene permisos excesivamente abiertos (como acceso para el grupo de "Usuarios"), bloqueando la conexión por seguridad.
*   **Archivos Relacionados:** [oci_deployment.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/deployment/oci_deployment.md)
*   **Concepto de Ingeniería de Software:** Principio de Menor Privilegio (Principle of Least Privilege).

### 79. ¿Cómo se abre el tráfico de red de OCI hacia el puerto de Streamlit?
*   **Respuesta Esperada:** Configurando una regla de ingreso TCP en la lista de seguridad de la subred pública de OCI y abriendo el puerto en el firewall de Ubuntu.
*   **Justificación Técnica:** El tráfico hacia el puerto `8501` se autoriza en la consola de OCI (`0.0.0.0/0`) y luego se habilita localmente en la máquina virtual ejecutando `sudo ufw allow 8501/tcp`.
*   **Archivos Relacionados:** [oci_deployment.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/deployment/oci_deployment.md)
*   **Concepto de Ingeniería de Software:** Seguridad de Red y Configuración de Firewalls Perimetrales.

### 80. ¿Por qué se utiliza un comando de Git Tag para los releases del Challenge?
*   **Respuesta Esperada:** Para marcar hitos inmutables de código en el historial de desarrollo, facilitando la auditoría del proyecto.
*   **Justificación Técnica:** Los tags de Git (como `v1.0.0`) actúan como punteros permanentes a commits específicos de entrega final, impidiendo confusiones lógicas sobre qué versión exacta de código se está auditando o desplegando.
*   **Archivos Relacionados:** Historial de commits en GitHub.
*   **Concepto de Ingeniería de Software:** Control de Versiones Semántico (Semantic Versioning).

### 81. ¿Cómo se asegura que las pruebas unitarias se ejecuten de forma independiente del entorno productivo en caliente?
*   **Respuesta Esperada:** Creando objetos Mock y desactivando el consumo de red en las pruebas de negocio.
*   **Justificación Técnica:** Los archivos `test_graph_manager.py` y `test_vector_store.py` no llaman a la API de Gemini; operan de forma local sobre variables temporales y estructuras aisladas de datos creadas en el `setUp()`.
*   **Archivos Relacionados:** [test_graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_graph_manager.py), [test_vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_vector_store.py)
*   **Concepto de Ingeniería de Software:** Pruebas Unitarias Aisladas (Isolated Unit Testing).

### 82. ¿Cuál es el propósito del script `tests/test_golden_dataset.py`?
*   **Respuesta Esperada:** Servir como suite de pruebas de regresión técnica para certificar la precisión del buscador híbrido.
*   **Justificación Técnica:** Ejecuta 12 preguntas críticas del reglamento real y valida que el motor retorne las KUNs correspondientes esperadas. Esto previene que parches o cambios de código futuros dañen la precisión del recuperador RAG.
*   **Archivos Relacionados:** [test_golden_dataset.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_golden_dataset.py)
*   **Concepto de Ingeniería de Software:** Pruebas de Regresión y Aseguramiento de Calidad (Regression Testing).

### 83. ¿Por qué se prefiere ejecutar las pruebas con `python -m unittest discover`?
*   **Respuesta Esperada:** Para automatizar el descubrimiento y la ejecución secuencial de todos los archivos de prueba en la carpeta `tests/`.
*   **Justificación Técnica:** El comando escanea recursivamente el directorio en busca de archivos que comiencen con `test_*.py` y los ejecuta de forma unificada, reportando la tasa de éxito final del proyecto.
*   **Archivos Relacionados:** [task.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/task.md)
*   **Concepto de Ingeniería de Software:** Automatización de Suites de Prueba (Test Automation).

### 84. ¿Qué ocurre si un competidor se desmaya por estrangulación (shime-waza) según las KUNs médicas?
*   **Respuesta Esperada:** Es inhabilitado para competir de forma inmediata por el resto del día de competencia, y no puede volver a tatami sin examen médico exhaustivo.
*   **Justificación Técnica:** La regla de desmayo por shime-waza está indexada bajo KUNs médicas específicas (KUN-0048 y KUN-0049). El asistente recupera estas directrices críticas de forma infalible cuando se le pregunta sobre desmayos o estrangulaciones.
*   **Archivos Relacionados:** [kuns_doc_004.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_004.md)
*   **Concepto de Ingeniería de Software:** Consistencia de Reglas de Salud Deportivas.

### 85. ¿Cuál es el límite máximo de intervenciones médicas autorizadas en un combate de Shiai?
*   **Respuesta Esperada:** Dos intervenciones médicas por atleta por combate. Una tercera intervención resulta en la pérdida del combate por decisión del árbitro (excepto por sangrado incontrolable o lesiones provocadas por faltas directas del oponente).
*   **Justificación Técnica:** Codificado bajo `KUN-0058` de la base médica del SOR 2026. Esta es una regla clave del dataset de oro para validar la precisión del RAG médico.
*   **Archivos Relacionados:** [kuns_doc_004.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_004.md)
*   **Concepto de Ingeniería de Software:** Modelado de Reglas de Negocio Complejas.

### 86. ¿Qué es el "bearing hug" (abrazo de oso) y cuál es su diferencia semántica con un agarre permitido?
*   **Respuesta Esperada:** El abrazo de oso se penaliza con shido si no hay agarre previo. Si hay agarre normal establecido de kumikata, el abrazo de oso es válido y permitido en combate de judo.
*   **Justificación Técnica:** Codificado y relacionado en el grafo para evitar que el RAG alucine asumiendo que todo abrazo de oso es falta.
*   **Archivos Relacionados:** [kuns_doc_001.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_001.md) (KUN-0045)
*   **Concepto de Ingeniería de Software:** Contextualización de Sinonimia Deportiva.

### 87. ¿Qué limitaciones presenta la arquitectura RAG respecto al tamaño del contexto de LLM?
*   **Respuesta Esperada:** Si se recuperan demasiadas KUNs (K alta) y se realiza una expansión profunda en el grafo, el tamaño del prompt puede saturar la ventana de contexto del LLM, ralentizando la respuesta y encareciendo los costos.
*   **Justificación Técnica:** El motor limita proactivamente la búsqueda a `k=3` y expansión a profundidad `1` para mantener un balance ideal entre riqueza informativa y economía de tokens.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Control de Latencia y Consumo de Recursos en APIs.

### 88. ¿Cómo previene el RAG las "alucinaciones de rol" del LLM en la respuesta?
*   **Respuesta Esperada:** Inyectando instrucciones de comportamiento sumamente estrictas en el prompt del sistema (*System Prompt Guidelines*).
*   **Justificación Técnica:** Las directrices le obligan a responder con tono institucional, a citar obligatoriamente la KUN y el artículo oficial, y a bloquear respuestas si el contexto no contiene la respuesta exacta.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Prompt Engineering y Limitación de Comportamiento.

### 89. ¿Por qué se desactivó la modalidad de Kata (formas) en la base de datos?
*   **Respuesta Esperada:** Por directriz expresa del Product Owner, para centrar el alcance del MVP estrictamente en el combate Shiai competitivo.
*   **Justificación Técnica:** El análisis de requisitos excluyó las fuentes DOC-003, DOC-005 y PPT-003 del inventario de ingesta activa del grafo y vector store.
*   **Archivos Relacionados:** [master_inventory.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/project-management/master_inventory.md)
*   **Concepto de Ingeniería de Software:** Gestión de Alcance del Proyecto (Scope Management).

### 90. ¿Cómo se asegura la integridad de los datos si se migra de Gemini a un modelo local offline?
*   **Respuesta Esperada:** Como el motor vectorial y el grafo de conocimiento son lógicos e independientes de Gemini, la estructura de datos permanece inalterada; solo cambia el generador final de embeddings y prompts.
*   **Justificación Técnica:** Se conserva el desacoplamiento de datos y el formato JSON. Al cambiar la capa de API de Gemini por un modelo local (ej. Llama 3 local a través de Ollama), el indexador genera los vectores localmente de la misma forma.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py), [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Diseño Extensible de Sistemas.

### 91. ¿Cómo se resolvió la colisión de variables de sesión en los clicks rápidos del usuario en la UI?
*   **Respuesta Esperada:** Streamlit procesa cada evento de clic de forma secuencial y atómica. El uso de callbacks nativos en lugar de condicionales pos-renderizado de botones garantiza la serialización correcta del estado de la sesión.
*   **Justificación Técnica:** El callback `load_example` muta las variables al inicio de la recarga, evitando colisiones de renderizado tardío y garantizando que el usuario visualice el estado exacto correspondiente a su última selección.
*   **Archivos Relacionados:** [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py)
*   **Concepto de Ingeniería de Software:** Sincronización de Estado en Flujos Reactivos.

### 92. ¿Qué ocurre si un usuario realiza una inyección de prompt (prompt injection) en la caja de búsqueda?
*   **Respuesta Esperada:** Las directrices del RAG Engine aíslan los datos del usuario en un bloque delimitado del prompt (`Pregunta del usuario: {user_query}`), previniendo que Gemini confunda la pregunta del usuario con instrucciones de sistema prioritarias.
*   **Justificación Técnica:** Al estructurar rígidamente el prompt y forzar el uso de delimitadores claros, el LLM prioriza las reglas del sistema sobre las órdenes contenidas dentro de la variable `user_query`.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Mitigación de Vulnerabilidades de Inyección de Prompts.

### 93. ¿Por qué se migró el contenido del manual de reglas obsoleto de 2023 al SOR de 2026?
*   **Respuesta Esperada:** Para evitar que el RAG recuperara respuestas obsoletas o en contradicción con las normas vigentes hoy en día.
*   **Justificación Técnica:** Identificamos que el documento explicativo de 2023 (`DOC-002`) contenía 6 reglas obsoletas. Creamos un script de migración que actualizó el corpus, moviendo esas KUNs de forma curada a la normativa del SOR 2026 y eliminando la fuente obsoleta.
*   **Archivos Relacionados:** [kuns_doc_001.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_001.md), `scratch/migrate_doc_002.py`
*   **Concepto de Ingeniería de Software:** Refactorización y Saneamiento de Datos de Entrada (Data Refactoring).

### 94. ¿Cuál es el rol de `scratch/golden_validation_report.md` en el control de calidad?
*   **Respuesta Esperada:** Es el reporte automatizado generado por el test de integración que certifica formalmente ante el jurado técnico que el buscador RAG superó las validaciones del dataset de oro con una precisión del 100%.
*   **Justificación Técnica:** Almacena los resultados formateados en una tabla Markdown detallada que detalla cada consulta de prueba, la KUN esperada, el conjunto recuperado y el estado de éxito.
*   **Archivos Relacionados:** `scratch/golden_validation_report.md`, [test_golden_dataset.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_golden_dataset.py)
*   **Concepto de Ingeniería de Software:** Automatización de Informes de Calidad de Software.

### 95. ¿Por qué se define la clase `VectorStore` con métodos de serialización `save_index` y `load_index`?
*   **Respuesta Esperada:** Para evitar tener que recalcular los embeddings de las 841 KUNs en cada inicio de la aplicación, ahorrando tiempo de red y costos de cuota de API.
*   **Justificación Técnica:** Los embeddings se calculan una única vez en la ingesta o recompilación masiva. En inicios subsecuentes, el sistema carga instantáneamente el archivo serializado desde el disco.
*   **Archivos Relacionados:** [vector_store.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/vector_store.py)
*   **Concepto de Ingeniería de Software:** Persistencia de Índices Precalculados (Serialization and Caching).

### 96. ¿Cómo maneja el sistema de logging interno la visibilidad del flujo en la terminal?
*   **Respuesta Esperada:** Mediante declaraciones de impresión estructuradas con prefijos lógicos (`[LOG] [RAG Flow]`, `[LOG] [Gemini API Client]`) en las funciones clave.
*   **Justificación Técnica:** Esto permite que al ejecutar la aplicación en producción en OCI, el administrador pueda monitorizar y auditar exactamente cada paso de la pipeline en tiempo real usando el comando `sudo journalctl -u ijf-assistant -f`.
*   **Archivos Relacionados:** [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)
*   **Concepto de Ingeniería de Software:** Trazabilidad de Logs de Operación (Operational Logging).

### 97. ¿Cuál es la justificación técnica de la relación `complementa_a` en el grafo?
*   **Respuesta Esperada:** Conecta una regla operativa base a otra regla del manual médico o técnica que amplía los detalles o requisitos de la primera.
*   **Justificación Técnica:** Si el RAG recupera el área de tatami, la arista de complementariedad arrastra automáticamente las especificaciones del material médico o control de judogis necesarios para el área.
*   **Archivos Relacionados:** [kuns_doc_001.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_001.md)
*   **Concepto de Ingeniería de Software:** Enlace Semántico de Ampliación de Negocio.

### 98. ¿Qué significa que las aristas del grafo de conocimiento sean no redundantes?
*   **Respuesta Esperada:** Que el compilador verifica que no se creen conexiones duplicadas de la misma dirección y tipo entre el mismo par de KUNs.
*   **Justificación Técnica:** Evita bucles lógicos innecesarios y optimiza el consumo de memoria del grafo al mantener limpias las listas de adyacencia de entrada y salida.
*   **Archivos Relacionados:** [graph_manager.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/graph_manager.py)
*   **Concepto de Ingeniería de Software:** Deduplicación de Aristas de Redes Lógicas.

### 99. ¿Cómo se instaló y configuró la máquina virtual OCI paso a paso?
*   **Respuesta Esperada:** Se aprovisionó una máquina Ubuntu Server 24.04, se clonó el repositorio, se creó un entorno virtual de Python, se instalaron las dependencias, se configuró el cortafuegos UFW y se levantó el servicio con Systemd.
*   **Justificación Técnica:** Esta secuencia estándar asegura que la aplicación se ejecute en un ambiente limpio, aislado y seguro, minimizando interferencias de otras dependencias del sistema operativo.
*   **Archivos Relacionados:** [oci_deployment.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/deployment/oci_deployment.md)
*   **Concepto de Ingeniería de Software:** Automatización de Infraestructura y Despliegue Limpio.

### 100. ¿Cuál es el principal aprendizaje de ingeniería de software obtenido en este proyecto?
*   **Respuesta Esperada:** El enorme poder de combinar arquitecturas vectoriales con grafos lógicos para eliminar alucinaciones en IAs aplicadas a reglamentos técnicos.
*   **Justificación Técnica:** La auditoría de conformidad y el dataset de oro demostraron que un LLM genérico falla al responder sobre judo competitivo 2026, mientras que nuestra arquitectura híbrida RAG local alcanza un 100% de precisión y trazabilidad verificada.
*   **Archivos Relacionados:** Todo el repositorio.
*   **Concepto de Ingeniería de Software:** Diseño de Sistemas RAG Híbridos de Alta Fidelidad.

# 🥋 IJF SOR Assistant - MVP v1.0
> **Asistente de Consulta Inteligente y Trazable del Reglamento Oficial de la Federación Internacional de Judo (IJF)**

Este proyecto es una plataforma interactiva de respuesta a preguntas (Q&A) basada en una arquitectura **RAG Híbrida** (Similitud Vectorial + Grafo de Conocimiento). Ha sido desarrollado para el reto de **Oracle ONE / Alura** y cumple con los estándares metodológicos más estrictos de ingeniería de software e ingeniería del conocimiento.

---

## 📸 Captura de la Aplicación
La interfaz interactiva está desarrollada en **Streamlit** y provee un chatbot conversacional junto a un visualizador 2D interactivo del subgrafo de relaciones normativas recuperado en tiempo real:

```text
+--------------------------------------------------------------+
| 🥋 IJF SOR Assistant                                         |
| Asistente Oficial de Consulta del Reglamento IJF             |
+--------------------------------------------------------------+
| [ Bar Lateral ]                   | [ Caja de Conversación ] |
| 🟢 Conectado (Gemini)             |                          |
| Nodos Grafo: 77                   | User: ¿Defensa de cabeza?|
| Relaciones:  72                   |                          |
|                                   | Assistant: Sanción con   |
| Parámetros:                       | Hansoku-make directo...  |
| - K semántico                     | [KUN-0001] [SOR Art. 20] |
| - Umbral score                    |                          |
|                                   | +----------------------+ |
| Hubs Centrales:                   | | 📚 Ver Trazabilidad  | |
| - KUN-0001: 16                    | +----------------------+ |
| - KUN-0026: 12                    | | 🕸️ Ver Subgrafo      | |
|                                   | +----------------------+ |
+--------------------------------------------------------------+
```

---

## 🏛️ Arquitectura del Sistema

El asistente utiliza un diseño desacoplado que separa la base de conocimiento original del índice de recuperación y del motor de búsqueda relacional:

```text
  [ Entrada del Usuario ]
            │
            ▼
┌───────────────────────┐
│  Streamlit Frontend   │ <─── Indicador Conectado / Offline
└───────────────────────┘
            │
            ▼
┌───────────────────────┐
│     Motor RAG         │
│     (rag_engine.py)   │
└───────────────────────┘
     │            │
     │            ├── (1. Búsqueda Vectorial TF-IDF)
     │            │   ▼
     │            │ ┌───────────────────────┐
     │            │ │     Vector Store      │ ── (Almacena IDs y vectores)
     │            │ │   (vector_store.py)   │
     │            │ └───────────────────────┘
     │            │
     │            └── (2. Expansión de Grafo y Contenido de KUNs)
     │                ▼
     │              ┌───────────────────────┐
     │              │    Knowledge Graph    │ ── (Nodos de KUNs, relaciones)
     │              │   (graph_manager.py)  │
     │              └───────────────────────┘
     │                          │
     ▼                          ▼
┌───────────────────────────────────────────┐
│            Corpus Oficial v1.0            │ <─── (Única fuente de verdad)
│         (kuns_doc_*.md, kuns_vid_*.md)    │
└───────────────────────────────────────────┘
```

### Principios Clave:
1.  **Fuente Única de Verdad:** El texto completo y las interpretaciones de las reglas solo residen en el Corpus y se manejan a través del Grafo. El **Vector Store** no duplica información de texto, solo almacena los vectores matemáticos vinculados al ID de la KUN.
2.  **Cero Dependencias Complejas:** El procesamiento de lenguaje natural y el grafo están construidos con librerías nativas de Python (`math`, `re`, `urllib`), evitando dependencias pesadas que fallen en Windows o despliegues Cloud.
3.  **Trazabilidad Explícita:** Cada afirmación generada se acompaña de sus referencias oficiales exactas (páginas del SOR, diapositivas del seminario o marcas de tiempo de video de la IJF).

---

## 📂 Estructura del Proyecto

```text
C:\PROYECTOS\IJF-SOR-Assistant/
├── app.py                      # Frontend Streamlit interactivo
├── README.md                   # Documentación principal (este archivo)
├── LICENSE                     # Licencia del proyecto
├── requirements.txt            # Dependencias del proyecto
├── kuns_doc_*.md               # Repositorio de KUNs por recurso
├── src/                        # Código fuente del backend
│   ├── graph_manager.py        # Compilador y analista del grafo
│   ├── vector_store.py         # Modelo vectorial TF-IDF de similitud
│   ├── rag_engine.py           # Orquestador del RAG Híbrido
│   ├── graph_manager_readme.md
│   ├── vector_store_readme.md
│   └── rag_engine_readme.md
├── tests/                      # Suite de pruebas unitarias e integración
│   ├── test_graph_manager.py
│   ├── test_vector_store.py
│   ├── test_rag_engine.py
│   └── test_golden_dataset.py  # Dataset de oro (12 consultas críticas)
└── scratch/                    # Entregables intermedios persistidos
    ├── knowledge_graph.json    # Grafo de KUNs en JSON
    ├── vector_store_index.json # Índice vectorial en JSON
    └── golden_validation_report.md  # Reporte de precisión RAG
```

---

## 💡 Ejemplos de Preguntas y Respuestas (Q&A)
A continuación se muestran ejemplos reales de consultas reglamentarias resueltas por el asistente con su respectiva trazabilidad técnica:

### 1. Regulación de la Defensa de Cabeza (Head Defence)
*   **Pregunta:** *¿Se permite la defensa con la cabeza?*
*   **Respuesta:** En eventos de la categoría Cadetes (Sub-18), no se permite usar la cabeza para defenderse (se penaliza con **Shido**). Para las categorías Senior y Junior, el uso de la cabeza para defenderse o proyectar está **permitido** y ya no se penaliza. Sin embargo, el "buceo de cabeza" (head diving - zambullirse de cabeza sobre el tatami) sigue estando estrictamente prohibido para todas las categorías y se penaliza con **Hansoku-make** directo.
*   **Citas Oficiales:** `KUN-0001` (SOR Artículo 20 - Apéndice D) y `KUN-0046` (SOR Artículo 18.1.4 - Apéndice D, Página 180).

### 2. Dimensiones del Tatami y Área de Seguridad
*   **Pregunta:** *¿Cuáles son las dimensiones del tatami?*
*   **Respuesta:** El área de combate debe tener unas dimensiones mínimas de 8m x 8m y máximas de 10m x 10m. El área de seguridad circundante debe medir un mínimo de 3m para proteger a los atletas de caídas fuera de la plataforma.
*   **Citas Oficiales:** `KUN-0007` (SOR Artículo 3 - Área de Competencia).

### 3. Sanción de Abrazo de Oso (Bear Hug)
*   **Pregunta:** *¿Cómo se sanciona el abrazo de oso (bear hug)?*
*   **Respuesta:** El abrazo de oso (bear hug) en tachi-waza se penaliza con **Shido** si el atleta entrelaza ambas manos o sujeta sus propios brazos para formar un círculo alrededor del torso del rival sin haber establecido un agarre (kumikata) normal previo. Se permite si el atleta ya tenía un agarre normal establecido, o durante transiciones de ne-waza a tachi-waza.
*   **Citas Oficiales:** `KUN-0045` (SOR Artículo 18.1.2 - Apéndice D, Página 176).

---

## 🚀 Requisitos e Instalación

### 1. Prerrequisitos
*   **Python 3.12** o superior instalado en el sistema.
*   Conexión a internet (para llamadas de API en Modo Conectado, opcional).

### 2. Instalación de Dependencias
Instale Streamlit (única librería externa requerida):
```bash
pip install -r requirements.txt
```

### 3. Configuración de API Key (Opcional)
Para habilitar la generación de respuestas con el modelo de lenguaje de Gemini, configure la variable de entorno:
*   **En PowerShell:**
    ```powershell
    $env:GEMINI_API_KEY="tu-api-key-aqui"
    ```
*   **En CMD:**
    ```cmd
    set GEMINI_API_KEY=tu-api-key-aqui
    ```
*Si no se configura, el sistema funcionará automáticamente en **Modo Offline (Simulado)** de manera resiliente.*

---

## 🥋 Ejecución de la Aplicación

### 1. Ejecución Local (Desarrollo)
Para iniciar el servidor de Streamlit y usar el chatbot localmente:
```bash
streamlit run app.py
```
La aplicación se abrirá en su navegador predeterminado en `http://localhost:8501`.

### 2. Despliegue en Producción (Oracle Cloud Infrastructure - OCI)
La aplicación está configurada para ejecutarse como un servicio en segundo plano (Systemd) en la dirección IP pública del servidor OCI: [http://149.130.187.132:8501](http://149.130.187.132:8501).

*   **Comando de Conexión SSH:**
    ```bash
    ssh -i "ruta/a/tu/ssh-key.key" ubuntu@149.130.187.132
    ```
*   **Comandos de Gestión del Servicio (Systemd):**
    *   Ver estado del servicio: `systemctl status ijf-assistant`
    *   Reiniciar servicio (para aplicar cambios de código): `sudo systemctl restart ijf-assistant`
    *   Iniciar / Detener servicio: `sudo systemctl start ijf-assistant` / `sudo systemctl stop ijf-assistant`
    *   Habilitar auto-arranque tras reinicios del servidor: `sudo systemctl enable ijf-assistant`
*   **Variables de Entorno Seguras:**
    La clave API de Gemini se almacena de forma segura en `/etc/ijf-assistant.env` con permisos restringidos de lectura (`chmod 640`).

### ⚙️ Guía de Parámetros de Consulta (Barra Lateral)
Para ajustar el comportamiento y la precisión de las respuestas del asistente, se exponen dos controles en el panel lateral:
1.  **Resultados Semánticos (K):** Cantidad máxima de Unidades de Conocimiento (KUNs) recuperadas en cada consulta (Valor óptimo recomendado: `3`).
2.  **Score Mínimo:** Umbral de similitud coseno (entre 0.05 y 0.50) requerido para validar un documento. Si la consulta tiene una relevancia inferior a este umbral (por ejemplo, preguntas de fútbol o fuera de contexto), el RAG descarta las reglas y activa el mensaje seguro de bloqueo: *"Lo siento, no tengo esa información..."* (Valor recomendado para demostraciones: `0.10`).

---

## 🧪 Suite de Pruebas y Validación

El proyecto incluye pruebas unitarias para cada componente y un validador del **Dataset de Oro** que ejecuta consultas complejas del reglamento real y evalúa la exactitud del buscador:

```bash
# Probar el gestor de grafo
python tests/test_graph_manager.py

# Probar el motor de búsqueda vectorial
python tests/test_vector_store.py

# Probar el flujo RAG híbrido
python tests/test_rag_engine.py

# Probar el Dataset de Oro
python tests/test_golden_dataset.py
```

### Resultados de la Validación Final:
*   **Tasa de Éxito de Recuperación (Golden QA):** **100.00%** (12 de 12 consultas críticas exitosas).
*   Consulte el informe detallado en: `scratch/golden_validation_report.md`.

---

## 📋 Metodología de Desarrollo y Trazabilidad Documental

El desarrollo de este asistente sigue una rigurosa secuencia metodológica diseñada para garantizar la entrega de un código limpio, estructurado y libre de "alucinaciones" en las respuestas de la IA:

### 1. Modelado del Conocimiento y Certificación del Corpus
*   **Extracción Sistemática:** El reglamento oficial de la IJF se fragmentó en 77 Unidades de Conocimiento certificadas (KUNs) que aíslan la lógica normativa.
*   **Auditoría de Correspondencia (AUD-001):** Se verificó que cada KUN tuviera un enlace unívoco e inalterado con su fuente de origen en el PDF oficial de la IJF (páginas, clips de video o diapositivas oficiales), alcanzando una tasa de cobertura del 100% en los temas seleccionados.
*   **Certificado de Conformidad (CERT-001):** Garantiza la veracidad del corpus indexado, obligando al modelo de lenguaje a depender únicamente del contexto recuperado para responder.

### 2. Ciclo de Vida del Repositorio y Git Flow Semántico
Para mantener un historial de cambios trazable, legible y alineado con los estándares de la industria, se adoptaron las siguientes buenas prácticas de control de versiones:
*   **Mensajería Semántica (Conventional Commits):** Se utilizaron prefijos estandarizados para clasificar atómicamente cada cambio en el repositorio, permitiendo una fácil lectura de la evolución del proyecto:
    *   `feat:` para la incorporación de características lógicas (como la creación del motor RAG).
    *   `fix:` para la corrección de errores (como permisos de archivos).
    *   `refactor:` para optimización, desacoplamiento y limpieza de código (como la remoción del cargador manual de `.env`).
    *   `style:` para cambios estéticos, ajustes visuales e interactividad (como el encabezado fijo y paddings de logo).
    *   `docs:` para la redacción de reportes y READMEs técnicos.
*   **Hitos de Versión:** Las diferentes etapas de desarrollo se estructuraron de forma incremental, culminando en la auditoría técnica final y el etiquetado del commit de producción mediante tags de Git (como `v1.0.0`) para marcar de forma profesional la versión de entrega oficial.

---

## ⚠️ Limitaciones Conocidas del MVP v1.0
1.  **Límite de Contexto de un Solo Salto:** El motor RAG híbrido expande las consultas semánticas de forma fija a profundidad 1 en el grafo. Para consultas que requieran encadenamiento de múltiples reglas indirectas (profundidad >= 2), el contexto podría omitir dependencias indirectas.
2.  **Representación Léxica de TF-IDF:** Al no utilizar embeddings neuronales densos de forma nativa para evitar dependencias complejas en el despliegue local de Windows, la búsqueda vectorial depende fuertemente de la coincidencia de raíces y sinónimos definidos en las interpretaciones del corpus.

---

## 🔮 Trabajo Futuro (Backlog v1.1)
1.  **Indexación Densa Híbrida:** Incorporar soporte para modelos de embeddings neuronales densos (como MiniLM o embeddings de Gemini) almacenados de forma local para mejorar la coincidencia semántica conceptual abstracta.
2.  **Expansión Selectiva por Tipo de Relación:** Permitir al motor filtrar dinámicamente qué aristas del grafo recorrer (ej. seguir solo relaciones `exceptua_a` o `ilustra_a`) para optimizar el tamaño del prompt.
3.  **Evaluación Automatizada de Generación:** Integrar métricas G-Eval o Ragas para evaluar no solo la precisión de la recuperación de KUNs, sino la fidelidad y exactitud textual de la respuesta final generada por el LLM.

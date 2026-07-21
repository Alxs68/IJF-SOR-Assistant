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

Para iniciar el servidor de Streamlit y usar el chatbot:
```bash
streamlit run app.py
```
La aplicación se abrirá en su navegador predeterminado en `http://localhost:8501`.

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

## ⚠️ Limitaciones Conocidas del MVP v1.0
1.  **Límite de Contexto de un Solo Salto:** El motor RAG híbrido expande las consultas semánticas de forma fija a profundidad 1 en el grafo. Para consultas que requieran encadenamiento de múltiples reglas indirectas (profundidad >= 2), el contexto podría omitir dependencias indirectas.
2.  **Representación Léxica de TF-IDF:** Al no utilizar embeddings neuronales densos de forma nativa para evitar dependencias complejas en el despliegue local de Windows, la búsqueda vectorial depende fuertemente de la coincidencia de raíces y sinónimos definidos en las interpretaciones del corpus.

---

## 🔮 Trabajo Futuro (Backlog v1.1)
1.  **Indexación Densa Híbrida:** Incorporar soporte para modelos de embeddings neuronales densos (como MiniLM o embeddings de Gemini) almacenados de forma local para mejorar la coincidencia semántica conceptual abstracta.
2.  **Expansión Selectiva por Tipo de Relación:** Permitir al motor filtrar dinámicamente qué aristas del grafo recorrer (ej. seguir solo relaciones `exceptua_a` o `ilustra_a`) para optimizar el tamaño del prompt.
3.  **Evaluación Automatizada de Generación:** Integrar métricas G-Eval o Ragas para evaluar no solo la precisión de la recuperación de KUNs, sino la fidelidad y exactitud textual de la respuesta final generada por el LLM.

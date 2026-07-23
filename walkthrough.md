# Walkthrough: Incorporación de Pila Tecnológica en Documentación (v15.0)

Hemos formalizado la sección de tecnologías y herramientas utilizadas en la documentación del repositorio para reflejar con precisión el stack de producción.

---

## 🛠️ Detalle de la Alineación en README.md

1.  **Nueva Sección Creada:**
    *   Inyectamos la sección `## 🛠️ Tecnologías y Herramientas Utilizadas` en [README.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/README.md) justo debajo del diagrama de arquitectura del sistema.
2.  **Tecnologías Documentadas:**
    *   **Núcleo Lógico:** Python 3.12 y bibliotecas estándar de procesamiento lógicos (`math`, `re`, `json`, `urllib`), destacando la filosofía de cero dependencias externas complejas.
    *   **Inteligencia Artificial:** Consumo nativo de la API de Gemini (modelos `gemini-embedding-001` y `gemini-1.5-flash/pro`).
    *   **Base de Datos RAG:** Knowledge Graph lógico bidireccional y Semantic Vector Store híbrido.
    *   **Capa Gráfica (UI):** Streamlit (v1.36+), CSS dinámico con soporte nativo de variables para modo claro/oscuro y Graphviz para renders vectoriales 2D interactivos del subgrafo de consulta.
    *   **Infraestructura y Despliegue Cloud:** Servidor VM Ubuntu en Oracle Cloud Infrastructure (OCI) administrado de forma persistente con Systemd y versionado semántico en GitHub con Conventional Commits.

---

## 🚀 Despliegue Live Actualizado (OCI)
*   Subimos los cambios a GitHub.
*   Actualizamos la máquina virtual en **OCI** (`git pull origin main`) y reiniciamos el servicio `ijf-assistant`.
*   El README actualizado ya está disponible y visible en producción:
    👉 [http://149.130.187.132:8501](http://149.130.187.132:8501)

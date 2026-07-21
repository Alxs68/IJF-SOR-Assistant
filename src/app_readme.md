# Interfaz Gráfica Streamlit (app.py)

Este módulo implementa el frontend interactivo del **IJF SOR Assistant** utilizando **Streamlit**, estructurado como una capa de presentación limpia y acoplada a la lógica del RAG Engine.

---

## 🎨 Características de Diseño
*   **Alineamiento de Marca:** Incorpora el logotipo oficial de la Federación Internacional de Judo (IJF) y un esquema de colores premium (azul institucional, gris claro y badges estilizados).
*   **Estado de Conexión Dinámico:** Muestra en la barra lateral un badge descriptivo:
    *   `🟢 Modo Conectado (LLM Gemini)` si la API Key está configurada en las variables de entorno.
    *   `🟡 Modo Offline (Simulado)` indicando resiliencia si no hay conexión disponible.
*   **Métricas del Grafo:** Expone en tiempo real el conteo de KUNs (77), aristas (72), conectividad promedio (3.74) y la lista de nodos hubs centrales.
*   **Parámetros de Búsqueda:** Control deslizante interactivo para sintonizar el número de KUNs a buscar (K) y el score de corte mínimo.
*   **Caja de Trazabilidad e Historial:** Cada burbuja de respuesta del asistente incluye un componente colapsable (`st.expander`) que detalla la lista de KUNs consultadas en la base de datos de origen con su texto oficial, traducción, interpretación oficial y cita exacta de fuente/página.
*   **Visualización de Subgrafo Activo:** Genera dinámicamente código DOT de Graphviz de los nodos y relaciones recuperadas en cada consulta y los renderiza vectorialmente mediante `st.graphviz_chart` sin necesidad de librerías JS o compiladores externos complejos.

---

## 🚀 Ejecución de la Interfaz
Para levantar el servidor web local de Streamlit, ejecute en la consola de comandos de Windows (dentro de la carpeta raíz del proyecto):
```bash
streamlit run app.py
```
La aplicación se abrirá automáticamente en el navegador web (por defecto en `http://localhost:8501`).

# Walkthrough: Sincronización de Scripts del Ciclo de Ingesta (v16.0)

Hemos trasladado el script de recompilación y regeneración del grafo y vectores al repositorio de código fuente para garantizar que toda la pipeline de desarrollo sea almacenable en el versionamiento de GitHub.

---

## 🛠️ Ajustes Implementados

1.  **Sincronización del Script de Compilación (`recompile_all.py`):**
    *   **Antes:** `recompile_all.py` residía en la carpeta de caché temporal de Antigravity, impidiendo que pudieras verlo en GitHub o utilizarlo para recompilar el grafo e indexar vectores localmente en tu consola.
    *   **Ahora:** Lo movimos a la carpeta permanente de scripts del proyecto: [scripts/recompile_all.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/scripts/recompile_all.py) y lo subimos a GitHub.
    *   **Función:** Este script lee el corpus Markdown limpio, compila el archivo `knowledge_graph.json`, verifica la reciprocidad del grafo y regenera todos los embeddings semánticos a través de llamadas en lotes a Gemini, persistiendo el índice en `vector_store_index.json`.

---

## 🚀 Despliegue Live Actualizado (OCI)
*   Subimos los cambios a GitHub.
*   Actualizamos la máquina virtual en **OCI** (`git pull origin main`) y reiniciamos el servicio `ijf-assistant`.
*   El script ya se encuentra disponible para su descarga y ejecución en la carpeta `scripts/` de tu repositorio de GitHub:
    👉 [https://github.com/Alxs68/IJF-SOR-Assistant/blob/main/scripts/recompile_all.py](https://github.com/Alxs68/IJF-SOR-Assistant/blob/main/scripts/recompile_all.py)

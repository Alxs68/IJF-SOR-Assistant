# Módulo Graph Manager (graph_manager.py)

Este módulo se encarga de compilar, estructurar y serializar el **Grafo de Conocimiento (Knowledge Graph)** a partir de las Unidades de Conocimiento (KUNs) oficiales del proyecto **IJF SOR Assistant**.

---

## 🛠️ Arquitectura y Clases

### Clase Principal: `KnowledgeGraph`
Representa el grafo lógico, almacenando nodos y aristas con sus respectivos tipos semánticos de relación.
* **Propiedades:**
  * `nodes`: Diccionario con la información estructurada de cada KUN (`id_conocimiento` -> JSON dict).
  * `edges`: Listas de adyacencia de salida (`id_conocimiento` -> lista de aristas salientes).
  * `in_edges`: Listas de adyacencia de entrada (`id_conocimiento` -> lista de aristas entrantes), reconstruidas para facilitar navegación bidireccional ágil.
* **Métodos Clave:**
  * `add_node(kun_id, kun_data)`: Agrega una KUN al grafo.
  * `add_edge(src_id, dest_id, rel_type)`: Crea un enlace direccionado semántico entre dos KUNs.
  * `get_kun(kun_id)`: Recupera los datos de una KUN por ID.
  * `get_neighbors(kun_id, rel_types=None)`: Recupera los vecinos de primer grado de un nodo, permitiendo opcionalmente filtrar por tipos específicos de relación (ej. traer solo excepciones mediante `exceptua_a`).
  * `get_metrics()`: Calcula el número de nodos, aristas, grado promedio, componentes conectados y hubs del grafo.
  * `save_to_json(filepath)` / `load_from_json(filepath)`: Serializa y deserializa el grafo para persistencia local.

---

## ⚙️ Compilación del Grafo

La función `compile_graph_from_markdown(brain_dir)` automatiza el escaneo del workspace:
1. Lee de forma recursiva los archivos que empiezan con `kuns_*.md`.
2. Extrae mediante expresiones regulares todos los bloques JSON de KUNs oficiales.
3. Carga los nodos y establece de forma segura todas las relaciones válidas entre ellos, omitiendo enlaces rotos.

---

## 🧪 Pruebas Unitarias
El archivo de pruebas se localiza en `tests/test_graph_manager.py`.
Para ejecutar las pruebas:
```bash
python tests/test_graph_manager.py
```
Las pruebas validan la inserción de nodos, integridad y direccionalidad de relaciones, y la exactitud de métricas topológicas básicas del grafo.

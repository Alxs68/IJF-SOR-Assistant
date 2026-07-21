# Módulo RAG Engine (rag_engine.py)

Este módulo implementa el **Orquestador RAG Híbrido** del asistente **IJF SOR Assistant**. Se encarga de fusionar la recuperación semántica (búsqueda vectorial) con la expansión topológica (Grafo de Conocimiento) para generar respuestas contextualizadas con citas de alta fidelidad.

---

## 🛠️ Arquitectura y Funcionamiento

### Clase Principal: `RagEngine`
Carga los índices persistidos del grafo y de vectores, y coordina la pipeline de consulta.
* **Propiedades:**
  * `kg`: Instancia de `KnowledgeGraph`.
  * `vs`: Instancia de `VectorStore`.
* **Métodos Clave:**
  * `retrieve_context(query, k=3, min_score=0.10, depth=1)`:
    1. **Búsqueda Vectorial:** Consulta en `VectorStore` las `k` KUNs más cercanas por similitud de coseno.
    2. **Umbralización:** Descarta resultados cuyo score sea inferior a `min_score`.
    3. **Expansión Semántica por Grafo:** Para cada nodo semilla recuperado, consulta sus vecinos de primer grado en el `KnowledgeGraph` y los agrega al contexto.
    4. **Ensamblado del Contexto:** Recupera la traducción oficial (`contenido_traduccion`) y la interpretación del corpus original a través del grafo.
  * `query(user_query, k=3, min_score=0.10)`:
    * Ejecuta la recuperación híbrida de contexto.
    * Ensambla el prompt inyectando las unidades KUN y las reglas estrictas de fidelidad.
    * Llama a la API de Gemini (o genera una respuesta simulada estructurada si no hay credenciales en el entorno).

---

## 🔌 Conexión Resiliente y Cero Dependencias
* **Conexión API Gemini:** Se realiza a través del módulo estándar `urllib` de Python, enviando solicitudes POST en JSON de forma nativa. Esto elimina la necesidad de instalar SDKs de Google externos y previene problemas de importación.
* **Resiliencia (Modo Offline):** Si la variable de entorno `GEMINI_API_KEY` o `GOOGLE_API_KEY` no se encuentra definida, el motor conmuta automáticamente a un generador offline estructurado que organiza las citas recuperadas y las presenta al usuario de forma clara sin lanzar errores.

---

## 🧪 Pruebas Unitarias
El archivo de pruebas se localiza en `tests/test_rag_engine.py`.
Para ejecutar las pruebas:
```bash
python tests/test_rag_engine.py
```
Valida la carga correcta de recursos serializados, el funcionamiento de la recuperación híbrida con expansión de grafo, y la generación de la respuesta formateada con citas.

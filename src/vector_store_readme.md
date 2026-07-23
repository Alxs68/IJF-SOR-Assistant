# Módulo Vector Store (vector_store.py)

Este módulo se encarga de la recuperación vectorial de documentos mediante un enfoque **híbrido** de recuperación:
1.  **Modo Semántico (Embeddings de Gemini):** Utiliza vectores neuronales densos de 768 dimensiones calculados a través de la API oficial `gemini-embedding-001` (mediante llamadas por lotes para alta velocidad). Mide la relevancia conceptual abstracta con similitud coseno.
2.  **Modo Léxico (TF-IDF):** Un modelo de espacio vectorial clásico local (Frecuencia de Términos - Frecuencia Inversa de Documento) que actúa como mecanismo de contingencia offline de forma automática.

Está diseñado con **cero dependencias complejas**, eliminando riesgos de instalación o compilación de binarios C++ en entornos Windows (como ocurre con FAISS o PyTorch).

---

## 🛠️ Estructura y Funcionamiento

### Clase Principal: `VectorStore`
Gestiona la indexación del corpus, persistencia del índice y la recuperación de documentos.
*   **Propiedades:**
    *   `kun_ids`: Lista ordenada de IDs de las KUNs indexadas.
    *   `mode`: Estado actual de indexación (`"embeddings"` si se inyectó API Key, o `"tfidf"` para el fallback local).
    *   `vectors`: Lista de vectores. Contiene vectores densos (float list) para embeddings, o diccionarios dispersos para TF-IDF.
    *   `vocabulary` / `idf` / `doc_lengths`: Estructuras matemáticas exclusivas del modo fallback TF-IDF.
*   **Métodos Clave:**
    *   `index_kun_corpus(kuns_dict, api_key=None)`: Ingesta las KUNs. Si se pasa una clave API, genera los embeddings mediante la API en lotes (`batchEmbedContents`). Si no, calcula los pesos TF-IDF locales.
    *   `search(query, k=5, api_key=None)`: Realiza la búsqueda vectorial. Si está en modo embeddings y se provee la clave API, vectoriza la consulta y calcula la similitud coseno sobre vectores densos. En caso contrario, realiza la similitud coseno sobre el espacio TF-IDF.
    *   `save_index(filepath)` / `load_index(filepath)`: Serializa y deserializa el índice en formato JSON.

---

## ⚙️ Principio de Separación de Responsabilidades
Por directriz de la arquitectura del proyecto, el **Vector Store no almacena los contenidos de texto de las KUNs**. Su única responsabilidad es:
1.  Recibir los textos (`contenido_traduccion` + `interpretacion`) para la indexación o vectorización.
2.  Almacenar las representaciones vectoriales asociadas únicamente al ID (`id_conocimiento`).
3.  Retornar los IDs de las KUNs recuperadas. La fuente de verdad del contenido completo sigue residiendo exclusivamente en el **Corpus Oficial** y el **Knowledge Graph**.

---

## 🧪 Pruebas Unitarias
El archivo de pruebas se localiza en `tests/test_vector_store.py`.
Para ejecutar las pruebas:
```bash
python tests/test_vector_store.py
```
Las pruebas validan el correcto funcionamiento de ambos modos, la tokenización local en español, el cálculo de similitud de coseno y la persistencia local en JSON.

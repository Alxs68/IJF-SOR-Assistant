# Módulo Vector Store (vector_store.py)

Este módulo se encarga del modelado de recuperación semántica mediante un **Modelo de Espacio Vectorial TF-IDF (Term Frequency - Inverse Document Frequency)** con **similitud de coseno**. 

Está diseñado bajo un enfoque de **cero dependencias externas**, eliminando riesgos de instalación y compilación binaria en entornos Windows (como suele ocurrir con FAISS o PyTorch).

---

## 🛠️ Arquitectura y Clases

### Clase Principal: `VectorStore`
Administra el vocabulario de términos indexados, pesos IDF globales, vectores de cada documento y realiza la búsqueda por similitud.
* **Propiedades:**
  * `kun_ids`: Lista ordenada de IDs de las KUNs indexadas.
  * `vocabulary`: Diccionario mapeando cada palabra limpia a su índice numérico de dimensión.
  * `idf`: Diccionario con el peso Inverse Document Frequency (IDF) calculado para cada término.
  * `vectors`: Lista de diccionarios que representan los vectores TF-IDF dispersos de cada documento (`indice_termino` -> `peso`).
  * `doc_lengths`: Vector de longitudes euclidianas para normalización rápida en similitud de coseno.
* **Métodos Clave:**
  * `index_kun_corpus(kuns_dict)`: Ingesta un corpus de KUNs, tokeniza la traducción e interpretación de cada una, calcula pesos TF-IDF y crea el índice.
  * `search(query, k=5)`: Tokeniza la consulta, calcula su vector TF-IDF, calcula la similitud de coseno con respecto a todas las KUNs, y retorna las mejores `k` coincidencias.
  * `save_index(filepath)` / `load_index(filepath)`: Serializa y deserializa el índice en formato JSON.

---

## ⚙️ Principio de Separación de Responsabilidades
Por directriz de la interventoría técnica, el **Vector Store no almacena los contenidos de texto de las KUNs**. Su única responsabilidad es:
1. Recibir los textos (`contenido_traduccion` + `interpretacion`) para indexación y cálculo matemático.
2. Almacenar los vectores asociados únicamente al ID (`id_conocimiento`).
3. Retornar los IDs de las KUNs recuperadas. La fuente de verdad del contenido completo sigue residiendo exclusivamente en el **Corpus Oficial** y el **Knowledge Graph**.

---

## 🧪 Pruebas Unitarias
El archivo de pruebas se localiza en `tests/test_vector_store.py`.
Para ejecutar las pruebas:
```bash
python tests/test_vector_store.py
```
Las pruebas validan la tokenización y remoción de acentos en español, el cálculo de similitud de coseno y la persistencia local en JSON.

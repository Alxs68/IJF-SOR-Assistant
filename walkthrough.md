# Walkthrough: Citas Clicables, Seguridad de Docker y Consistencia Documental (Final)

Este documento resume los cambios definitivos implementados y verificados en la rama `feature/clickable-citations-refactor` para dotar al asistente de citas hipervinculadas a fuentes oficiales exactas, resolver la seguridad de compilación en Docker, asegurar la auto-invalidación del caché de grafos en despliegues y asegurar la no regresión del sistema.

---

## 🚀 Cambios Implementados

### 1. Módulo Independiente de Citas ([citation_resolver.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/citation_resolver.py))
- Se creó un módulo independiente para evitar el acoplamiento del motor RAG con el frontend Streamlit.
- Se trasladó el catálogo centralizado `RESOURCE_DETAILS` al módulo de resolución.
- Se actualizó el catálogo para que la fuente `DOC-004` (Manual Médico de Judo) apunte de manera consistente al PDF unificado del SOR 2026, dado que los reglamentos médicos son parte de sus apéndices.
- Se implementó `resolve_url(kun_id, kun_data)` utilizando el analizador robusto `urllib.parse` para estructurar parámetros de consulta (`&t=S`) y anclas de página (`#page=N`). Soporta fallback dinámico al catálogo centralizado si las KUNs omiten el campo redundante `"url"` en su bloque de `"fuente"`.
- Se implementó `format_citations(answer, retrieved_kuns)` que localiza citas inline en formato `[KUN-xxxx]` y las convierte a Markdown clicable **solo si** pertenecen a las KUNs recuperadas en la misma consulta.

### 2. Invalidación Automática de Caché del Grafo y Búsqueda local ([rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py))
- Se implementó una lógica de auto-invalidación en tiempo de ejecución: al cargarse los recursos en `load_resources()`, se comparan las marcas de tiempo de última modificación (`mtime`) de todos los archivos markdown del corpus (`data/markdown/kuns_*.md`) contra el archivo `scratch/knowledge_graph.json` ignorado por Git.
- Si algún archivo markdown es más reciente que el caché, se recompila el grafo de forma transparente en tiempo de ejecución, se actualiza el archivo JSON local y se re-indexa el vector store local de TF-IDF. Esto soluciona de forma definitiva el despliegue en entornos OCI con volúmenes persistentes que cargan cachés antiguos.

### 3. Recuperación Canónica Única e Integración en UI ([app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py))
- Se modificó el método `query()` en [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py) para que devuelva la lista completa de diccionarios de datos de KUNs en la clave `'retrieved_kuns_data'`.
- Se actualizó [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py) para obtener el contexto recuperado directamente de esta clave en lugar de ejecutar una segunda llamada a `retrieve_context()`, garantizando que la respuesta y la trazabilidad provengan de una única ejecución canónica.
- Se integró el resolvedor centralizado `resolve_url()` en el panel de trazabilidad de Streamlit, logrando consistencia absoluta de enlaces en la interfaz.

### 4. Corrección de Inconsistencias de Trazabilidad en el Corpus Piloto
Se actualizaron los JSON de las KUNs piloto eliminando propiedades redundantes (como URLs duplicadas) y corrigiendo las contradicciones de fuentes:
- **[KUN-0001](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_001.md#L8) (PDF SOR)**: Se cambió `referencia_especifica` a `"Apéndice D (Artículo 18.2.1), Página 181"` para hacerlo 100% consistente con la regla oficial de head diving y los metadatos estructurados.
- **[KUN-0047](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_004.md#L8) (PDF Médico)**: Se cambió `referencia_especifica` a `"Manual Médico (Apéndice D, Artículo 20 Nota), Página 269"` apuntando al unificado `DOC-004` (SOR PDF) para evitar la contradicción de fuentes y el 404 del manual aislado.
- **[KUN-0023](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_pag_002.md#L8) (Web)**: Se actualizó `referencia_especifica` a `"rules.ijf.org/gripping"` para que sea consistente con la URL del catálogo.
- **[KUN-0004](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_vid_004.md#L77) (Video YouTube)**: Apunta de forma estructurada a la demostración real del seminario de arbitraje (`https://www.youtube.com/watch?v=uK8fF41wOqI`) en el segundo `220` (`t=220s`).

### 5. Seguridad de Docker ([.dockerignore](file:///C:/PROYECTOS/IJF-SOR-Assistant/.dockerignore))
- Se creó el archivo [.dockerignore](file:///C:/PROYECTOS/IJF-SOR-Assistant/.dockerignore) para evitar que secrets locales (`.env`), entornos virtuales (`.venv`), logs, y carpetas de desarrollo (`tests/`) sean incluidos en las imágenes Docker compiladas.

---

## 🧪 Pruebas Realizadas y Resultados

Se expandió la suite [test_citations.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_citations.py) para evaluar el motor de citas de forma automatizada.

### Casos Cubiertos por Pruebas Unitarias:
1.  **test_resolve_url_pdf_structured**: Confirma que un PDF estructurado construye la URL con el fragmento de página correcto (`#page=181`) usando fallback del catálogo.
2.  **test_resolve_url_video_structured**: Confirma que un video de YouTube structured construye la URL con el parámetro de tiempo adecuado (`&t=220s`).
3.  **test_resolve_url_web_structured**: Confirma que una página web structured genera la URL directa correcta usando fallback del catálogo.
4.  **test_resolve_url_pdf_compatibility**: Confirma el fallback de compatibilidad para KUNs sin `"fuente"` (ej. extrae la página 181 usando regex sobre texto libre).
5.  **test_resolve_url_video_compatibility**: Confirma el comportamiento seguro ante URLs que no son de YouTube.
6.  **test_format_citations_valid_and_retrieved**: Valida que citas reales y recuperadas se reemplacen por hipervínculos markdown clicables.
7.  **test_format_citations_not_retrieved_remains_plain**: Valida la trazabilidad estricta (si el LLM cita una KUN no recuperada para la consulta, se muestra como texto plano).
8.  **test_formatted_citations_correspond_to_retrieved_kuns**: **Nueva prueba** que extrae las citas directamente de la respuesta formateada mediante regex y valida que cada enlace Markdown corresponde única y estrictamente a una KUN presente en el conjunto recuperado para esa misma consulta.
9.  **test_non_regression_reused_context**: **Prueba de no regresión** que certifica que los IDs listados en `'retrieved_kuns'` coinciden exactamente con los datos provistos en `'retrieved_kuns_data'` para una misma consulta del motor RAG.

### Resultado de la Suite de Pruebas:
Se ejecutó la suite completa exitosamente:
```text
Ran 9 tests in 0.423s
OK
```

La suite global de pruebas del sistema también fue validada sin regresiones:
```text
Ran 19 tests in 0.456s
OK
```

---

## 🔍 Validación Manual de Enlaces del Piloto (Ejemplos Reales)

| KUN ID | Tipo | Fuente / URL Base | Localizador | Enlace Generado Verificado |
| :--- | :--- | :--- | :--- | :--- |
| **KUN-0001** | PDF | Reglamento SOR 2026 | Pág. 181 | [Reglamento SOR (pág. 181)](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/IJF_Sport_and_Organisation_Rul-1769443746.pdf#page=181) |
| **KUN-0047** | PDF | Reglamento SOR 2026 | Pág. 269 | [Reglamento SOR (pág. 269)](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/IJF_Sport_and_Organisation_Rul-1769443746.pdf#page=269) |
| **KUN-0004** | Video | YouTube (uK8fF41wOqI) | 220s (3:40) | [Seminario Arbitraje (t=220s)](https://www.youtube.com/watch?v=uK8fF41wOqI&t=220s) |
| **KUN-0023** | Web | rules.ijf.org | /gripping | [Portal Gripping](https://rules.ijf.org/gripping) |

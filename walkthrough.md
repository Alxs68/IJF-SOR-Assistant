# Walkthrough: Citas Clicables, Seguridad de Docker y Consistencia Documental

Este documento resume los cambios implementados y verificados en la rama `feature/clickable-citations-refactor` para dotar al asistente de citas hipervinculadas a fuentes oficiales exactas, resolver la seguridad de compilación en Docker, y asegurar la no regresión del sistema.

---

## 🚀 Cambios Implementados

### 1. Desacoplamiento y Nuevo Módulo de Citas ([citation_resolver.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/citation_resolver.py))
- Se creó un módulo independiente para evitar el acoplamiento del motor RAG con el frontend Streamlit.
- Se trasladó el catálogo centralizado `RESOURCE_DETAILS` al módulo de resolución.
- Se implementó `resolve_url(kun_id, kun_data)` utilizando el analizador robusto `urllib.parse` para estructurar parámetros de consulta (`&t=S`) y anclas de página (`#page=N`).
- Se implementó `format_citations(answer, retrieved_kuns)` que localiza citas inline en formato `[KUN-xxxx]` y las convierte a Markdown clicable **solo si** pertenecen a las KUNs recuperadas en la misma consulta.

### 2. Recuperación Canónica Única ([rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py) y [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py))
- Se modificó el método `query()` en [rag_engine.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py) para que devuelva tanto la lista de IDs de KUNs recuperadas (compatibilidad con pruebas anteriores) como la lista completa de diccionarios de datos de KUNs en la clave `'retrieved_kuns_data'`.
- Se actualizó [app.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/app.py) para obtener el contexto recuperado directamente de esta clave en lugar de ejecutar una segunda llamada a `retrieve_context()`, garantizando que la respuesta y la trazabilidad provengan de una única ejecución canónica.
- Se integró el resolvedor centralizado en el panel de trazabilidad de Streamlit, logrando consistencia absoluta de enlaces en la interfaz.

### 3. Incorporación de Metadatos Estructurados en el Piloto
Se actualizaron los JSON de 4 KUNs piloto para incorporar el campo de metadatos `"fuente"` con datos validados manualmente contra los documentos originales:
- **[KUN-0001](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_001.md#L8) (PDF SOR)**: Apunta a la página 181 (regla de head diving de la IJF).
- **[KUN-0047](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_doc_004.md#L8) (PDF Médico)**: Apunta a la página 269 (Apéndice D, Nota de estrangulamientos en cadetes).
- **[KUN-0004](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_vid_004.md#L77) (Video YouTube)**: Apunta al video oficial de reglas en YouTube (`https://www.youtube.com/watch?v=uK8fF41wOqI`) en el segundo exacto `220` (`t=220s`).
- **[KUN-0023](file:///C:/PROYECTOS/IJF-SOR-Assistant/data/markdown/kuns_pag_002.md#L8) (Web)**: Apunta a la sección oficial de agarres de rules.ijf.org (`https://rules.ijf.org/gripping`).

### 4. Seguridad de Docker ([.dockerignore](file:///C:/PROYECTOS/IJF-SOR-Assistant/.dockerignore))
- Se creó el archivo [.dockerignore](file:///C:/PROYECTOS/IJF-SOR-Assistant/.dockerignore) para evitar que secrets locales (`.env`), entornos virtuales (`.venv`), logs, y carpetas de desarrollo (`tests/`) sean incluidos en las imágenes Docker compiladas.

### 5. Consistencia Documental ([README.md](file:///C:/PROYECTOS/IJF-SOR-Assistant/README.md))
- Se eliminó el archivo `LICENSE` del mapa de directorios para alinearlo con la eliminación de la licencia del repositorio real.

---

## 🧪 Pruebas Realizadas y Resultados

Se creó la suite [test_citations.py](file:///C:/PROYECTOS/IJF-SOR-Assistant/tests/test_citations.py) para evaluar el motor de citas de forma automatizada.

### Casos Cubiertos por Pruebas Unitarias:
1.  **test_resolve_url_pdf_structured**: Confirma que un PDF estructurado construye la URL con el fragmento de página correcto (`#page=181`).
2.  **test_resolve_url_video_structured**: Confirma que un video de YouTube structured construye la URL con el parámetro de tiempo adecuado (`&t=220s`).
3.  **test_resolve_url_web_structured**: Confirma que una página web structured genera la URL directa correcta.
4.  **test_resolve_url_pdf_compatibility**: Confirma el fallback de compatibilidad para KUNs sin `"fuente"` (ej. extrae la página 181 usando regex sobre texto libre).
5.  **test_resolve_url_video_compatibility**: Confirma el comportamiento seguro ante URLs que no son de YouTube.
6.  **test_format_citations_valid_and_retrieved**: Valida que citas reales y recuperadas se reemplacen por hipervínculos markdown clicables.
7.  **test_format_citations_not_retrieved_remains_plain**: Valida la trazabilidad estricta (si el LLM cita una KUN no recuperada para la consulta, se muestra como texto plano).
8.  **test_non_regression_reused_context**: **Prueba de no regresión** que certifica que los IDs listados en `'retrieved_kuns'` coinciden exactamente con los datos provistos en `'retrieved_kuns_data'` para una misma consulta del motor RAG.

### Resultado de la Suite de Pruebas:
Se ejecutó la suite completa con éxito:
```text
Ran 8 tests in 0.068s
OK
```

---

## 🔍 Validación Manual de Enlaces del Piloto

| KUN ID | Tipo | Fuente / URL Base | Localizador | Enlace Generado Verificado |
| :--- | :--- | :--- | :--- | :--- |
| **KUN-0001** | PDF | ijf_sor_2026.pdf | Pág. 181 | [Reglamento SOR (pág. 181)](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/IJF_Sport_and_Organisation_Rul-1769443746.pdf#page=181) |
| **KUN-0047** | PDF | ijf_sor_2026.pdf | Pág. 269 | [Reglamento SOR (pág. 269)](https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/IJF_Sport_and_Organisation_Rul-1769443746.pdf#page=269) |
| **KUN-0004** | Video | YouTube (uK8fF41wOqI) | 220s (3:40) | [Seminario Arbitraje (t=220s)](https://www.youtube.com/watch?v=uK8fF41wOqI&t=220s) |
| **KUN-0023** | Web | rules.ijf.org | /gripping | [Portal Gripping](https://rules.ijf.org/gripping) |

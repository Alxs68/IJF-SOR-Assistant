# Registro de Hallazgos y Defectos — Auditoría Visual del Apéndice E (Páginas 208–240)

**Documento:** IJF Sport and Organisation Rules (14 de agosto de 2026)  
**Alcance:** Páginas físicas 208 a 240 (33 páginas)  
**Fecha:** 2026-10-17  

---

## 1. Clasificación de Severidad

- **Crítico:** Pérdida o alteración que provoque una respuesta normativa incorrecta.
- **Alto:** Pérdida de una relación, excepción, instrucción, condición o referencia importante.
- **Medio:** Defecto de trazabilidad, numeración, segmentación o redundancia en la indexación.
- **Bajo:** Problema documental, terminológico o de representación gráfica auxiliar que no afecta a la recuperación.

---

## 2. Inventario de Hallazgos

### Hallazgo H-APP-01: Discrepancia Estructural de Nomenclatura (Apéndice E vs. Apéndice F / Sección F1.3)
- **Severidad:** **Bajo** (Documental / Terminológico)
- **Páginas físicas:** 208 a 240.
- **Evidencia del PDF:**
  - En el Sumario oficial (*Table of Contents*, págs. 7–8) y en los encabezados del documento, las páginas físicas 208 a 240 constituyen la sección **`F1.3 Standard Forms for IJF Events`** (perteneciente al **Apéndice F: SPORT COMPETITION**, págs. 204–240).
  - El **Apéndice E** en la edición oficial del 14 de agosto de 2026 corresponde exclusivamente al *IJF Medical and Anti-Doping Handbook* (págs. 200–203).
- **Valor / Contenido esperado:** Reconocimiento de que las páginas 208–240 son los formularios estándar de competición de la IJF (Sección F1.3 / Apéndice F).
- **Resultado observado en RAG:** Los pasajes en `passages_candidate.json` y la matriz de cobertura registran correctamente los identificadores `F1.3` a `F1.3.33`.
- **Impacto probable:** Ninguno en la recuperación; solo requiere precisión documental en los informes.
- **Corrección propuesta:** Aclarar formalmente en el informe ejecutivo la correspondencia normativa entre la designación de la tarea ("Apéndice E") y la estructura oficial del PDF 2026-08 (Sección F1.3, Apéndice F).

---

### Hallazgo H-APP-02: Solapamiento de Frontera de Sección (Doble Pasaje por Página en Formularios de 1 Página)
- **Severidad:** **Medio / Bajo** (Segmentación de Pasajes)
- **Páginas físicas:** 209 a 240 (ej. pág. 209 con S231 y S232; pág. 236 con S258 y S259).
- **Evidencia del PDF:** Cada formulario estándar ocupa exactamente una página física completa (ej. pág. 236 es únicamente F1.3.29 *Coach Suspension Form*).
- **Valor / Contenido esperado:** Cada página física de formulario independiente debería generar un pasaje único asignado a su sección unívoca.
- **Resultado observado en RAG:**
  - El generador de cobertura estructural asignó a cada sección un `end_page_physical` coincidente con el inicio de la siguiente sección (`start_page + 1`).
  - Como consecuencia, para 33 páginas físicas se generaron 69 pasajes en `passages_candidate.json`, donde cada página se indexa dos veces (como cierre de la sección previa y apertura de la sección actual), con texto idéntico.
- **Impacto probable:** Redundancia en el almacén de pasajes. Sin embargo, RRE aplica fusión de rangos RRF y desduplicación de pasajes por contenido, evitando que pasajes duplicados saturen las evidencias devueltas.
- **Corrección propuesta:** En una futura fase de refactorización del generador de corpus (fuera de esta auditoría de solo lectura), ajustar el cálculo de `end_page` para formularios atómicos de una página a `end_page = start_page`. En la rama actual, no se requiere modificación de código ya que no altera el orden de relevancia ni induce respuestas erróneas.

---

### Hallazgo H-APP-03: Páginas con Diagramas de Cuadros de Competición en Gráficos Vectoriales Puros
- **Severidad:** **Bajo** (Informativo / Diseño Gráfico)
- **Páginas físicas:** 213 (*Direct Knockout*), 215, 216, 217, 218 (*Quarter-Final Repechage* 64, 32, 16, 8), 222 (*Double Repechage* 8), 234 (*Team Sheet*), 235 (*Mixed Teams Match Sheet*).
- **Evidencia del PDF:** Estas páginas son plantillas de cuadros de emparejamiento deportivo compuestas casi en su totalidad por rutas vectoriales (`fitz.get_drawings() > 80`) y cajas en blanco sin texto en los nodos. La extracción textual por página oscila entre 100 y 136 caracteres (encabezado, título de la sección y pie de página).
- **Valor / Contenido esperado:** Representaciones visuales de los cuadros descritos reglamentariamente en los Artículos 2.4 a 2.8.
- **Resultado observado en RAG:** El texto nominal y títulos de los cuadros están presentes e indexados en el RAG. Las reglas operativas de cabezas de serie, repesca y pase a semifinales son recuperadas desde los artículos sustantivos (págs. 36–45).
- **Impacto probable:** Ninguno sobre la capacidad de resolución de dudas reglamentarias por parte de ADA.
- **Corrección propuesta:** Mantener los pasajes actuales con metadatos de título y anclaje a página PDF; no se requiere acción correctiva.

---

## 3. Resumen de Defectos por Gravedad

| Severidad | Total | Identificadores | Acción Requerida en Rama |
| :--- | :---: | :--- | :--- |
| **Crítico** | **0** | Ninguno | Ninguna |
| **Alto** | **0** | Ninguno | Ninguna |
| **Medio** | **1** | H-APP-02 (Solapamiento de fronteras de sección) | Documentado; impacto mitigado por RRE |
| **Bajo** | **2** | H-APP-01 (Nomenclatura F1.3), H-APP-03 (Páginas vectoriales) | Documentados |

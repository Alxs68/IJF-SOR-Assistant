# Protocolo de Extracción de Conocimiento (extraction_protocol.md)
## Proyecto: IJF SOR Assistant

Este documento establece el **Protocolo Operativo de Extracción** para la Fase 2, definiendo las reglas operativas, los criterios de aceptación de calidad y el flujo de validación humana para asegurar que la construcción del corpus de conocimiento sea sistemática, homogénea y libre de duplicaciones o ambigüedades.

---

## 1. Reglas Operativas de Extracción

### A. ¿Cuándo se crea una Unidad de Conocimiento (KUN)?
Se creará una nueva KUN si y solo si:
* Contiene una directriz, concepto, penalización, puntuación, excepción o procedimiento que puede entenderse de manera autónoma y responder a una consulta del usuario por sí sola.
* Aporta un valor conceptual único no cubierto por otra KUN ya existente.

### B. ¿Cuándo NO se crea una KUN?
* **Textos Introductorios:** Prefacios, agradecimientos, declaraciones institucionales o firmas de directivos que no aporten normativas de competencia.
* **Índices y Tablas de Contenido:** Listados de páginas o tablas de navegación física.
* **Históricos Retirados:** Menciones a reglas anteriores a 2026 que ya no aplican, a menos que sean necesarias como excepción explícita.

### C. Manejo de Contenidos Múltiples (Granularidad Semántica)
* Si un párrafo del SOR contiene una regla general y una excepción, **se deben extraer dos KUNs separadas** (una `REG` y una `EXC`) enlazadas semánticamente. No se permite fusionar reglas autónomas en una sola KUN para evitar la degradación del RAG.

### D. Resolución de Duplicados
* Si una misma regla es citada textualmente en varias secciones del documento o en recursos diferentes (ej. el SOR y una noticia), se creará **únicamente una KUN principal** asociada a la fuente original y de mayor autoridad. Las menciones secundarias se enlazarán mediante relaciones semánticas (`complementa_a` o `confirmado_por`) en lugar de duplicar el nodo.

### E. Registro de Ambigüedades y Dudas
* Si durante la extracción se detecta una ambigüedad en el texto o una aparente contradicción entre recursos, el extractor debe:
  1. Registrar la KUN de forma provisional.
  2. Asignar el valor provisional `vigencia_hasta: "Revisar"`.
  3. Describir la duda con precisión en el campo `interpretacion`.
  4. Escalar la KUN al Product Owner para su dictamen.

---

## 2. Criterios de Aceptación por Tipo de Recurso

La extracción de un recurso se dará por completada únicamente cuando cumpla con los siguientes estándares de calidad:

### A. Criterio para PDFs Normativos (DOC-001, DOC-004)
* **Cobertura Total:** Todos los capítulos y artículos de Shiai analizados.
* **Identificación Completa:** Cada regla general, procedimiento, excepción y penalización extraído en su propia KUN.
* **Trazabilidad:** Cada KUN debe referenciar el artículo exacto y el número de página original.

### B. Criterio para Presentaciones y Diapositivas (DOC-002, PPT-001, PPT-002)
* **Procesamiento Slide-by-Slide:** Cada diapositiva analizada.
* **Contexto Gráfico:** Las explicaciones textuales de las jugadas o tácticas representadas en las imágenes de las diapositivas deben describirse textualmente en el campo `interpretacion`.

### C. Criterio para Portales Interactivos (PAG-001 a PAG-005)
* **Mapeo de Rutas:** Todas las URLs e índices interactivos de `rules.ijf.org` validados y contrastados con el SOR.
* **Extracción de Tablas:** Todas las especificaciones técnicas dinámicas mapeadas a KUNs independientes.

### D. Criterio para Videos Oficiales (VID-001 a VID-005)
* **Segmentación con Timestamp:** Cada caso de estudio de video debe poseer una KUN con su marca de tiempo exacta de inicio y fin.
* **Descripción y Audio:** Se debe incluir la descripción física de la jugada observada en pantalla y la transcripción del audio de la explicación del supervisor de arbitraje.

---

## 3. Trazabilidad Inversa

Para garantizar que el sistema pueda auditarse de forma inversa, el proceso de extracción debe asegurar que se pueda consultar la procedencia de la siguiente forma:
* Cada KUN debe incluir de forma obligatoria e inalterable el ID permanente de su recurso original en el campo `fuente_origen` (ej: `DOC-001`).
* Se mantendrá un índice centralizado de KUNs que permita filtrar y listar de forma instantánea todas las unidades de conocimiento derivadas de un documento específico.

---

## 4. Flujo de Validación Humana (QA)

El ciclo de vida de ingreso de una KUN al corpus de conocimiento constará de las siguientes fases obligatorias:

```
[Extracción Asistida] 
      ↓
[Validación por Auditor] ── (¿Cumple Schema, Granularidad y URL?)
      ↓ (Sí)
[Corrección de Desviaciones] 
      ↓
[Aprobación del PO (Alexis)] ── (Resolución de dudas en Interpretación)
      ↓ (Sí)
[Ingreso al Corpus Oficial]
```

1. **Extracción:** Obtención del JSON original y la traducción/interpretación inicial de la KUN.
2. **Validación:** El auditor técnico revisa la sintaxis JSON, la correcta asignación de tipos, etiquetas y el enlace de relaciones en el grafo.
3. **Corrección:** Ajuste y refinación de KUNs rechazadas.
4. **Aprobación:** El Product Owner (Alexis) dictamina sobre KUNs con marcas de duda o conflicto.
5. **Ingreso:** La KUN es aprobada e incorporada formalmente a la base de conocimiento estable del proyecto.

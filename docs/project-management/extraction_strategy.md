# Estrategia de Extracción por Tipo de Recurso (extraction_strategy.md)
## Proyecto: IJF SOR Assistant

Este documento establece las pautas y técnicas de parsing que se aplicarán a cada uno de los formatos del corpus de la Línea Base, garantizando una estructuración limpia de las KUNs.

---

## 1. Pautas de Extracción Técnica

### A. Documentos en PDF Normativos (DOC-001, DOC-004)
* **Pauta:**
  1. Identificar la jerarquía estructural (ej: *Section 1 - General Rules*, *Chapter I - Competitors*, *Article 1 - Age categories*).
  2. Aislamiento semántico: Cada artículo se subdivide en reglas autónomas.
  3. Mapear anexos (ej: Categorías de peso, dimensiones del tatami) como KUNs individuales de tipo `DEF` o `REG` vinculadas al artículo que las invoca.

### B. Presentaciones y Diapositivas (DOC-002, PPT-001, PPT-002)
* **Pauta:**
  1. Analizar diapositiva por diapositiva.
  2. Si la diapositiva tiene una ilustración técnica (ej: dirección de un agarre prohibido):
     * Describir la acción representada (ej: "Atleta de judogi blanco agarra el cinturón del oponente por más de 5 segundos sin atacar").
     * Documentar esta descripción en el campo `interpretacion`.
  3. Enlazar la diapositiva (fuente origen) a la KUN normativo-escrita correspondiente del SOR mediante la relación `ilustrado_por` / `ilustra_a`.

### C. Portales Web Interactivos (PAG-001 a PAG-005)
* **Pauta:**
  1. Recorrer de forma secuencial la estructura lógica del subdominio (ej: `rules.ijf.org/gripping` y sus subconceptos).
  2. Extraer el texto explicativo dinámico y las tablas interactivas.
  3. Relacionar la página web con el artículo del SOR correspondiente (ej: la sección interactiva de Gripping complementa al artículo de Kumikata del SOR).

### D. Videos Oficiales (VID-001 a VID-005)
* **Pauta:**
  1. Dividir el video en segmentos de interés basados en los casos de estudio expuestos.
  2. Para cada segmento, registrar:
     * **Timestamp:** Marca de inicio y fin (ej: `01:45 - 02:30`).
     * **Visuales:** Qué técnica se ejecuta y cuál es la infracción o el acierto técnico de los competidores.
     * **Comentarios Oficiales:** La explicación hablada o subtitulada del director de arbitraje (Neil Adams, Daniel Lascau, etc.).
  3. Enlazar la KUN del video (`CAS`) a la KUN de penalización o regla general (`PEN`, `REG`) correspondiente.

### E. Noticias Oficiales (NEW-001 a NEW-003)
* **Pauta:**
  1. Extraer los párrafos informativos que comuniquen cambios de criterio.
  2. Ignorar secciones no técnicas (nombres de patrocinadores, discursos ceremoniales generales, sedes).
  3. Enlazar mediante la relación `confirmado_por` a la KUN de la regla principal que se modifica.

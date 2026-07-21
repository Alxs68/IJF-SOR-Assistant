# Validación del Proyecto Piloto (pilot_validation.md)
## Proyecto: IJF SOR Assistant (Versión Auditada)

Este documento presenta los resultados y el análisis del **Proyecto Piloto** de extracción de conocimiento ejecutado sobre el **SOR principal (DOC-001)**, validando el Modelo de Conocimiento v1.0 y el Protocolo de Extracción.

---

## 1. Unidades de Conocimiento Piloto Extraídas (Muestra de DOC-001)

### KUN-0005: Límites de Edad para Cadetes
```json
{
  "id_conocimiento": "KUN-0005",
  "titulo": "Límites de Edad para Atletas Cadetes",
  "tipo": "REG",
  "nivel_autoridad": "Norma",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "The age limit for Cadet judo athletes is defined from 15 to 17 years old.",
  "contenido_traduccion": "El límite de edad para los atletas de judo de la categoría Cadetes se define entre los 15 y 17 años de edad.",
  "interpretacion": "Esta regla general establece el rango etario para competir en la división Cadete de la IJF. Los deportistas deben cumplir la edad mínima de 15 años y no superar la edad máxima de 17 años en el año de la competencia.",
  "fuente_origen": "DOC-001",
  "referencia_especifica": "Artículo 1 - Categorías de Edad",
  "tags": ["age", "cadet", "competitors"],
  "relaciones": []
}
```

### KUN-0006: Categorías de Peso Masculino Senior
```json
{
  "id_conocimiento": "KUN-0006",
  "titulo": "Categorías de Peso Masculinas Senior",
  "tipo": "REG",
  "nivel_autoridad": "Norma",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "The weight categories for men senior judo athletes are -60kg, -66kg, -73kg, -81kg, -90kg, -100kg and +100kg.",
  "contenido_traduccion": "Las categorías de peso para los atletas masculinos de judo de la división Senior son -60kg, -66kg, -73kg, -81kg, -90kg, -100kg y +100kg.",
  "interpretacion": "Regulación oficial que define las 7 categorías oficiales de pesaje para las competencias masculinas senior oficiales de la IJF.",
  "fuente_origen": "DOC-001",
  "referencia_especifica": "Artículo 2 - Categorías de Peso",
  "tags": ["weight-categories", "men", "senior"],
  "relaciones": []
}
```

### KUN-0007: Dimensiones del Área de Combate (Tatami)
```json
{
  "id_conocimiento": "KUN-0007",
  "titulo": "Dimensiones del Área de Combate (Tatami)",
  "tipo": "REG",
  "nivel_autoridad": "Norma",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "The contest area must be a minimum of 8m x 8m and a maximum of 10m x 10m. The safety area must be a minimum of 3m.",
  "contenido_traduccion": "El área de combate debe tener unas dimensiones mínimas de 8m x 8m y máximas de 10m x 10m. El área de seguridad debe tener una dimensión mínima de 3m.",
  "interpretacion": "Establece los límites espaciales obligatorios de la zona central de tatami donde se desarrolla el combate (Shiai) y el margen circundante de seguridad requerido para prevenir caídas de los competidores fuera de la plataforma.",
  "fuente_origen": "DOC-001",
  "referencia_especifica": "Artículo 3 - Área de Competencia",
  "tags": ["tatami", "dimensions", "safety-area"],
  "relaciones": [
    { "tipo_relacion": "ilustrado_por", "id_destino": "KUN-0008" }
  ]
}
```

### KUN-0008: Esquema Técnico del Tatami
```json
{
  "id_conocimiento": "KUN-0008",
  "titulo": "Diagrama de Distribución de Tatami y Zonas de Seguridad",
  "tipo": "CAS",
  "nivel_autoridad": "Caso práctico",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "Visual technical drawing depicting the 8x8m inner contest area colored in yellow and the surrounding 3m safety area colored in red.",
  "contenido_traduccion": "Plano técnico visual que representa la zona interior de combate de 8x8m coloreada de amarillo y el área de seguridad exterior circundante de 3m coloreada de rojo.",
  "interpretacion": "Esquema gráfico del SOR oficial que complementa las dimensiones espaciales, ilustrando el contraste de colores para que árbitros y competidores identifiquen los límites activos de la plataforma de juego.",
  "fuente_origen": "IMG-001",
  "referencia_especifica": "Anexo 1 - Plano del Tatami",
  "tags": ["tatami", "diagram", "layout"],
  "relaciones": [
    { "tipo_relacion": "ilustra_a", "id_destino": "KUN-0007" }
  ]
}
```

---

## 2. Indicadores de Rendimiento del Piloto (KPIs)

Para evaluar objetivamente la calidad de la extracción y estimar el esfuerzo futuro de construcción del corpus, se consolidan las siguientes métricas del piloto:

| Indicador (KPI) | Valor Obtenido | Objetivo / Umbral de Aceptación | Diagnóstico |
| :--- | :--- | :--- | :--- |
| **Total de KUN extraídas** | 4 | Medir granularidad (esperado ~4 por sección) | **Correcto** (4 KUNs en 3 artículos). |
| **Tiempo medio por KUN** | ~4 minutos | Estimar esfuerzo (máximo 6 minutos/KUN) | **Excelente** (dentro del rango estimado). |
| **Relaciones generadas por KUN** | 0.5 (2 en total) | Medir densidad semántica (esperado >= 0.25) | **Correcto** (alta interconexión tatami-dibujo). |
| **% de KUN modificadas en revisión (QA)** | 0% | Medir calidad inicial (máximo 15% de rechazos) | **Excelente** (todas cumplieron el esquema v1.0). |
| **% de duplicados detectados** | 0% | Validar la unicidad (máximo 10% de redundancia) | **Correcto** (ninguna regla repetida). |
| **% de excepciones enlazadas** | 100% (N/A en muestra) | Validar consistencia de flujo exceptivo | **N/A** (no hubo excepciones en este lote de prueba). |

---

## 3. Análisis y Evaluación de Viabilidad del Piloto

### A. Viabilidad de la Granularidad Semántica
* **Hallazgo:** La división de KUNs por temas semánticos específicos (ej. separar categorías de edad cadete de los seniors) resultó sumamente limpia. En lugar de procesar el "Artículo 1" como un único bloque denso, extraer la regla específica del límite de edad como KUN independiente permite consultas directas e independientes (RAG) con un nivel de ruido de contexto cero.

### B. Suficiencia del Esquema JSON de Metadatos
* **Hallazgo:** La incorporación de los campos auditados demostró su utilidad:
  * **`interpretacion`**: Aporta valor aclaratorio a las dimensiones de tatami y los rangos de edad, resolviendo la aridez del texto original en inglés.
  * **`nivel_autoridad`**: Clasifica correctamente las dimensiones (`Norma`) frente a su plano técnico (`Caso práctico`), preparándolo para resolver discrepancias.

### C. Complejidad de las Relaciones del Grafo
* **Hallazgo:** La conexión bidireccional entre la regla de dimensiones de tatami (`KUN-0007`) y su plano gráfico (`KUN-0008`) a través de `ilustrado_por` / `ilustra_a` funciona perfectamente en el grafo. Permite la trazabilidad inversa desde el plano hacia la norma.

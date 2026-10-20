# REGISTRO DE CORRECCIONES — REVISIÓN TÉCNICA FOCALIZADA
**Documento ID:** AUD-CORRECTIONS-LOG-2026-08  
**Fecha:** 17 de octubre de 2026  
**Rama de Trabajo:** `audit/rebuild-sor-2026-08`  
**Directorio:** `docs/reports/coverage_audit_2026_08/followup_review/`  

---

## 1. RESUMEN DE DEFECTOS CONFIRMADOS Y CORRECCIONES REALIZADAS

Se identificaron y corrigieron **tres defectos confirmados** en los artefactos de representación estructurada preliminares:

| ID Defecto | Componente Afectado | Severidad | Descripción del Defecto | Corrección Implementada | Evidencia Antes / Después |
| :---: | :--- | :---: | :--- | :--- | :--- |
| **DEF-001** | `reconstructed_complex_tables.json` (Matriz WRL) | **Media** | Los registros `1 contest won` y `Participation` tenían solo 7 valores en el diccionario, omitiendo la columna `Olympic Games`. | Se incorporó la clave `"Olympic Games": null` de forma explícita, preservando que en el PDF la celda está en blanco (no aplica puntaje). | **Antes:** Diccionario con 7 claves.<br>**Después:** Diccionario consistente con 8 claves en las 9 filas. |
| **DEF-002** | `reconstructed_complex_tables.json` (Pesos Individuales) | **Media** | Fusión de Senior y Junior bajo un solo campo sin extraer las 16 categorías de Cadetes de la página 33 (solo contenía 30 registros con duplicación de clave). | Se reestructuró la tabla en 32 categorías individuales completas: 16 Senior/Junior (8 mujeres, 8 hombres) y 16 Cadetes (8 mujeres, 8 hombres) con su división de edad y límites explícitos. | **Antes:** 30 registros ambiguos.<br>**Después:** 32 registros individuales estrictamente diferenciados. |
| **DEF-003** | `reconstructed_complex_tables.json` (Equipos Mixtos) | **Baja** | Agrupación sin desglose de las 6 categorías de Equipos Mixtos de Cadetes y reglas de elegibilidad por peso individual. | Se incorporaron los 18 registros de equipos mixtos (6 Senior/Junior, 6 JJ.OO., 6 Cadetes) con el desglose de pesos individuales admisibles. | **Antes:** Solo 12 registros parciales.<br>**Después:** 18 registros verificados. |

---

## 2. INVENTARIO DE EVIDENCIA ANTES / DESPUÉS

### Defecto DEF-001: Matriz WRL (Pág. 52)
- **PDF Oficial:** La fila `1 contest won` contiene `[10, 80, 70, 70, 100, 0, 200, ""]`. La fila `Participation` contiene `[2, 6, 6, 6, 10, 100, 20, ""]`.
- **Estado Antes:**
  ```json
  "Participation": {
    "points_by_competition": {
      "Continental Opens": "2",
      "Continental Championships": "6",
      "Junior World Championships": "6",
      "Grand Prix": "6",
      "Grand Slam": "10",
      "Masters": "100",
      "World Championships": "20"
    }
  }
  ```
- **Estado Después (`reconstructed_complex_tables_corrected.json`):**
  ```json
  "Participation": {
    "points_by_competition": {
      "Continental Opens": "2",
      "Continental Championships": "6",
      "Junior World Championships": "6",
      "Grand Prix": "6",
      "Grand Slam": "10",
      "Masters": "100",
      "World Championships": "20",
      "Olympic Games": null
    }
  }
  ```

---

### Defecto DEF-002: Categorías de Peso Individuales (Pág. 33)
- **Estado Antes:** El registro clasificaba erróneamente `Cadet Women` y `Cadet Men` como si fueran `Senior and Junior` debido a un error de arrastre de cabecera en el bucle del extractor.
- **Estado Después:** 
  - 8 categorías `Senior and Junior Women` (`-48 kg` a `Open`).
  - 8 categorías `Cadet Women (under 18 years)` (`-40 kg` a `+70 kg`).
  - 8 categorías `Senior and Junior Men` (`-60 kg` a `Open`).
  - 8 categorías `Cadet Men (under 18 years)` (`-50 kg` a `+90 kg`).
  - Total: **32 registros individuales exactos**.

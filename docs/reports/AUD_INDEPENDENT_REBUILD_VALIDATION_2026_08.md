# Informe de Validación y Auditoría Independiente — Reconstrucción SOR 2026-08-14

**Fecha de Auditoría:** 2026-10-17  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Rama:** `audit/rebuild-sor-2026-08`  
**Identificador de Fuente:** `SOR-2026-08-14-ENG`  
**Hash Oficial SHA-256:** `9426B10D11C21A4CB9EB23150C2C4FC95BFCD463511E66BA451D2CFF005AE620`  
**Estado:** Puerta de Validación Independiente **APROBADA**. Listo para diseño de adaptadores aislados.

---

## 1. Validación Independiente de la Fuente (A)

* **Existencia y Apertura:** El archivo físico `data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf` existe en disco y fue abierto y leído mediante `pypdf`.
* **Total de Páginas Físicas:** Exactamente **298 páginas**.
* **Integridad Criptográfica Recalculada:**
  * SHA-256 recalculado byte por byte: `9426B10D11C21A4CB9EB23150C2C4FC95BFCD463511E66BA451D2CFF005AE620`.
  * Coincidencia con `source_manifest.json`: **100% idéntico**.
  * Tamaño exacto en bytes: `29,664,780` bytes.
* **Autenticidad y Textos de Versión:**
  * Portada (Página 1): `IJF General Secretariat - gs@ijf.org Version: 14 August 2026`.
  * Preludio (Página 9): `This latest version of the IJF SOR (which replaces version 24 July 2026) can be downloaded at: https://www.ijf.org/ijf/documents/26`.
* **Conservación de Originales:** El documento histórico `data/raw/ijf_sor_2026.pdf` (enero 2026) permanece completamente intacto e inalterado.

---

## 2. Auditoría de Cobertura y Discrepancias de Paginación (B)

### Desglose de las 298 Páginas Físicas:
1. **Páginas Físicas Totales:** **298**.
2. **Páginas Cubiertas en Pasajes Normativos:** **284 páginas** (Páginas 13 a 298, excluyendo páginas vacías de portada o separadores).
3. **Páginas con Numeración Impresa Identificada (`page - X`):** **281 páginas**.
   * En todas las 281 páginas donde el pie de página incluye la cadena `page - X`, existe una correspondencia exacta: `Página Física == Página Impresa` (diferencia = 0).

### Clasificación Individual de las 14 Páginas Restantes (No Normativas):
* **Página 1:** Portada oficial institucional (Logo, Dirección de Budapest, Versión 14 August 2026).
* **Páginas 2 a 8 (7 páginas):** Tabla de Contenidos oficial completa (*Table of Contents*) de 272 secciones.
* **Páginas 9 a 11 (3 páginas):** Preludio institucional, lista de abreviaturas (*Abbreviations*), directorio de redes sociales y enlaces a recursos adicionales.
* **Página 12:** Portadilla gráfica de inicio de sección ("GENERAL INFORMATION").
* **Página 131:** Página completamente en blanco entre la sección de Judogi y Refereeing (`0` caracteres extraíbles, imagen decorativa `Im0.jpg`).
* **Página 242:** Portadilla gráfica de inicio de glosario ("GLOSSARY").

**Conclusión:** No existe ninguna omisión de contenido normativo. El 100% de las páginas con articulado, tablas, notas de arbitraje y apéndices reglamentarios están incorporadas en el corpus.

---

## 3. Auditoría de Pasajes y Grafo de Conocimiento (C)

* **Total Pasajes Candidatos:** **554 pasajes**.
* **Validación de Esquema Formal:** Evaluados con `jsonschema` contra `PROPOSED_PASSAGE_SCHEMA.json`. **554 de 554 pasajes son 100% conformes**.
* **Integridad de Metadatos:**
  * 100% conservan `passage_id` determinista (`SOR-2026-08-Pxxx-Sxxx`), `article_id`, `pdf_page_index`, `source_version: "2026-08-14"`, `source_sha256` y `text_sha256` individual.
* **Cero Contaminación:** Búsqueda exhaustiva de patrones heredados (`KUN-`, URLs de enero 2026, hashes viejos) arrojó **0 coincidencias**.
* **Auditoría de Aristas del Grafo:**
  * Total aristas: **112 aristas**.
  * Coincidencia textual de procedencia: **112 de 112 aristas (100%)** están sustentadas por referencias explícitas y reales dentro del texto normativo de origen (ej. `Article 18`, `Article 4`, `Articles 19 and 20`).
  * Aristas huérfanas: **0**.

---

## 4. Auditoría del Índice Vectorial y Recuperación (D)

* **Vinculación Criptográfica:** El archivo `vector_index_candidate.json` incluye como metadato raíz el hash de fuente `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620`.
* **Evaluación de Consultas Normativas de Prueba:**
  1. *Query:* `cadet head defence shido`  
     -> *Top Hit:* `SOR-2026-08-P254-S269` (Pág 254, G1.3 Penalty Codes).
  2. *Query:* `tatami contest area dimensions 8m 10m`  
     -> *Top Hit:* `SOR-2026-08-P151-S178` (Pág 151, Article 5 Location - Valid Areas).
  3. *Query:* `osaekomi time 20 seconds ippon 10 seconds waza-ari`  
     -> *Top Hit:* `SOR-2026-08-P152-S180` (Pág 152, Article 7 Osaekomi Time).
  4. *Query:* `sokuteiki judogi control measurement`  
     -> *Top Hit:* `SOR-2026-08-P114-S148` (Pág 114, IJF Judogi Rules).
  5. *Query:* `medical intervention unconsciousness concussion doctor`  
     -> *Top Hit:* `SOR-2026-08-P294-S272` (Pág 294, H1.1 Document Version History / Medical updates).
* **Trazabilidad:** Cada resultado recuperado resuelve con éxito su número de página física, sección original y texto de procedencia.

---

## 5. Dictamen y Próximos Pasos

> **Dictamen de la Auditoría Independiente:** 🟢 **APROBADO**  
> El corpus candidato cumple con los más altos estándares de fidelidad, cobertura, aislamiento y trazabilidad.

**Acciones Inmediatas Seguras:**
1. Mantener intactos los archivos de producción en `src/`, `data/markdown/` y `data/raw/ijf_sor_2026.pdf`.
2. No ejecutar purgas ni pushes en el repositorio remoto.
3. Proceder al diseño e implementación en entorno aislado (`scratch/`) de los adaptadores de motor para que puedan alternar de manera controlada y verificable entre el nuevo contrato de datos y la interfaz de usuario.

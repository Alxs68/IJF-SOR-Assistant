# RESUMEN EJECUTIVO DE COBERTURA NORMATIVA — IJF SOR 2026-08
**Documento ID:** AUD-COVERAGE-SUMMARY-2026-08  
**Fecha:** 17 de octubre de 2026  
**Fuente Evaluada:** IJF Sport and Organisation Rules (14 August 2026, 298 págs., SHA-256: `9426B10D...`)  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant` (rama: `audit/rebuild-sor-2026-08`)  

---

## 1. MÉTRICAS CONSOLIDADAS DE COBERTURA NORMATIVA

Para evitar sustituir la cobertura normativa por un simple recuento de pasajes, se tomó como **denominador explícito las 272 secciones y artículos oficiales** del índice oficial de la IJF (conciliado entre el TOC impreso en págs. 2 a 8 y el TOC embebido del PDF):

$$\text{Cobertura Verificada} = \frac{238}{272} = 87.50\% \quad (\text{Artículos, Capítulos y Normativa Sustantiva})$$
$$\text{Pendiente Validación Visual} = \frac{34}{272} = 12.50\% \quad (\text{Formularios y Diagramas F1.3, Págs. 208–240})$$
$$\text{Omisiones Normativas (Ausente)} = \frac{0}{272} = 0.00\%$$

| Estado de Verificación | Secciones | Porcentaje | Evidencia y Justificación Técnica |
| :--- | :---: | :---: | :--- |
| 🟢 **COMPLETO_VERIFICADO** | **238** | **87.50%** | Todos los artículos de Información General, Competición, Veteranos, Kata, Judogi, Arbitraje, Médico y Glosarios están extraídos, representados en los 554 pasajes normativos e indexados criptográficamente en el vector store. |
| 🟡 **PARCIAL (Validación Visual Pendiente)** | **34** | **12.50%** | Corresponden exclusivamente a las secciones F1.3.1 a F1.3.33 (Págs. 208 a 240). El texto normativo y títulos están extraídos en los pasajes, pero los organigramas y diagramas de llaves requieren inspección visual. |
| 🔴 **AUSENTE** | **0** | **0.00%** | Ningún artículo, subartículo, capítulo o apéndice reglamentario ha sido omitido. |
| ⚪ **NO_APLICA** | **0** | **0.00%** | Se evaluó el universo total de las 272 secciones. |
| **TOTAL UNIVERSO NORMATIVO** | **272** | **100.00%** | **Denominador explícito e inalterable.** |

---

## 2. COBERTURA DETALLADA POR CAPÍTULO Y APÉNDICE

| Capítulo / Apéndice | Rango Páginas | Artículos / Secciones | Estado de Cobertura | Pasajes Clave |
| :--- | :---: | :---: | :---: | :--- |
| **GENERAL INFORMATION (Cap. 1)** | 12 – 32 | 26 | 🟢 `COMPLETO_VERIFICADO` (100%) | `SOR-2026-08-P013-S001` a `P032-S036` |
| **SPORT COMPETITION RULES (Cap. 2–8)** | 33 – 100 | 85 | 🟢 `COMPLETO_VERIFICADO` (100%) | `SOR-2026-08-P033-S037` a `P100-S120` |
| **APPENDIX A: VETERANS (A1.1–A1.15)** | 101 – 107 | 15 | 🟢 `COMPLETO_VERIFICADO` (100%) | `SOR-2026-08-P101-S121` a `P107-S135` |
| **APPENDIX B: KATA (B1.1–B1.12)** | 108 – 113 | 12 | 🟢 `COMPLETO_VERIFICADO` (100%) | `SOR-2026-08-P108-S136` a `P113-S147` |
| **APPENDIX C: JUDOGI RULES (C1.1–C1.14)** | 114 – 131 | 18 | 🟢 `COMPLETO_VERIFICADO` (100%) | `SOR-2026-08-P114-S148` a `P131-S173` |
| **APPENDIX D: REFEREEING RULES (Art. 1–21)** | 132 – 199 | 32 | 🟢 `COMPLETO_VERIFICADO` (100%) | `SOR-2026-08-P132-S174` a `P199-S212` |
| **APPENDIX E: MEDICAL & ANTI-DOPING** | 200 – 203 | 11 | 🟢 `COMPLETO_VERIFICADO` (100%) | `SOR-2026-08-P200-S213` a `P203-S220` |
| **APPENDIX F: SPORT COMPETITION & FORMS** | 204 – 241 | 37 | 🟡 3 Secciones Verificadas / 34 Parciales | `SOR-2026-08-P204-S221` a `P240-S253` |
| **APPENDIX G: GLOSSARY (G1.1–G1.4)** | 242 – 257 | 34 | 🟢 `COMPLETO_VERIFICADO` (100%) | `SOR-2026-08-P242-S254` a `P257-S270` |
| **APPENDIX H: DOCUMENT CONTROL (H1.1)** | 258 – 298 | 2 | 🟢 `COMPLETO_VERIFICADO` (100%) | `SOR-2026-08-P258-S271` a `P298-S272` |

---

## 3. TRAZABILIDAD Y ACCESO A LOS ARTEFACTOS

Los resultados detallados y reproducibles se encuentran disponibles en:
- Matriz completa de 272 filas: `docs/reports/coverage_audit_2026_08/SOR_COVERAGE_MATRIX_2026_08.csv`
- Registro de brechas y cola de validación: `docs/reports/coverage_audit_2026_08/SOR_COVERAGE_GAPS_2026_08.csv`
- Evidencia estructurada JSON: `docs/reports/coverage_audit_2026_08/SOR_COVERAGE_EVIDENCE_2026_08.json`
- Inventario de 449 tablas: `docs/reports/coverage_audit_2026_08/SOR_TABLE_INVENTORY_2026_08.csv`
- Informe específico de tablas: `docs/reports/coverage_audit_2026_08/SOR_TABLE_VALIDATION_REPORT_2026_08.md`

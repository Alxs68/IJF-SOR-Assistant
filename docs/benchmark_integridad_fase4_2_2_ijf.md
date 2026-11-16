# SOR-IJF — BENCHMARK DE INTEGRIDAD FASE 4.2.2
**Verificación Criptográfica Forense de Invarianza del Corpus SOR e Integridad Sidecar**

- **Proyecto:** IJF Sport and Organisation Rules (SOR) Assistant
- **Fase:** Fase 4.2.2 — Benchmark de Integridad Criptográfica
- **Fecha:** 2026-11-05
- **Rama Git:** `integration/ijf-sor-2026-08-merge` (Commit Base: `61afc1bc`)
- **Estado:** 100% INVARIANTE — VERIFICACIÓN EXITOSA
- **Autor / Auditor:** Antigravity (Ejecución y Verificación)

---

## 1. RESUMEN DE LA AUDITORÍA CRIPTOGRÁFICA

La auditoría forense compara los hashes SHA-256 de los artefactos normativos primarios del SOR 2026 antes y después de la creación de la infraestructura Sidecar y de la ingesta del lote piloto `BATCH-MULTI-2026-11-01`.

Todos los artefactos evaluados arrojaron coincidencia exacta bit a bit (**Cero mutaciones detectadas**).

---

## 2. MATRIZ FORENSE DE ARTEFACTOS NORMATIVOS SOR 2026

| Artefacto / Archivo | Hash SHA-256 Pre-Fase 4.2.2 | Hash SHA-256 Post-Ingesta Sidecar | Estado de Integridad |
|---|---|---|---|
| **PDF SOR 2026 Oficial**<br>`data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf` | `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620` | `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620` | **INVARIANTE (COINCIDENCIA 100%)** |
| **Corpus de Pasajes SOR (385 chunks)**<br>`data/processed/rebuild_2026_08_corrected/passages_candidate.json` | `7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b` | `7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b` | **INVARIANTE (COINCIDENCIA 100%)** |
| **Índice Léxico / Vector Candidate**<br>`data/processed/rebuild_2026_08_corrected/vector_index_candidate.json` | `e182c77e0775472eb73d22ab92b15d026d067cbf6264fb8b25b207479c4668eb` | `e182c77e0775472eb73d22ab92b15d026d067cbf6264fb8b25b207479c4668eb` | **INVARIANTE (COINCIDENCIA 100%)** |
| **Metadatos de Embeddings Densos**<br>`data/processed/rebuild_2026_08_corrected/dense_embeddings_meta.json` | `c96b214bc14801ad903d58e0245d48c008d65ac051d339fd4e6b65e30709160e` | `c96b214bc14801ad903d58e0245d48c008d65ac051d339fd4e6b65e30709160e` | **INVARIANTE (COINCIDENCIA 100%)** |
| **Grafo de Conocimiento (112 aristas)**<br>`data/processed/rebuild_2026_08_corrected/knowledge_graph_candidate.json` | `95d5a67936cf48d3bc79b69bf370bb1a83a255f938a7322e0dae256450dde215` | `95d5a67936cf48d3bc79b69bf370bb1a83a255f938a7322e0dae256450dde215` | **INVARIANTE (COINCIDENCIA 100%)** |

---

## 3. INTEGRIDAD DE ARTEFACTOS SIDECAR GENERADOS

| Artefacto Generado | Ubicación Aislada | SHA-256 Generado | Certificación |
|---|---|---|---|
| **Pasajes Multifuente (8 chunks)** | `data/corpus_multisource/processed/multisource_passages.json` | `a49337a20fbf95eb8d6a894a44136696dbf533a0db9fcb9bc2f04e1bc5c8a00c` | Certificado en Registry |
| **Catálogo de Metadatos Sidecar** | `data/corpus_multisource/processed/multisource_metadata.json` | `37887534439169a91522f7dbd7634f5aa7ea6c9d09c3132e48545806e680a618` | Certificado en Manifest |
| **Manifiesto de Lote Piloto** | `data/corpus_multisource/manifests/BATCH-MULTI-2026-11-01.json` | `8e2bebeff7b62e49c716f966113b28b52f9b2512f4640ef777b789961db5452b` | Sellado por Alexis |
| **Registro Operativo de Sidecars** | `data/corpus_multisource/sidecar_registry.json` | `1c8900c3da3345d8b8e019318b76ce8309d94b05a6ef6cb3d588523b1856ae38` | Estado: READY |

---

## 4. CONCLUSIÓN FORENSE

Se certifica formalmente que el sistema implementa un **aislamiento de almacenamiento estricto y unidireccional**:
- La ingesta secundaria opera sobre rutas aisladas.
- Ningún proceso lee ni escribe en las carpetas normativas del SOR 2026.
- El criterio **GATE06 — Invariancia** se cumple de manera concluyente.

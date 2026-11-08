# ÍNDICE DOCUMENTAL CENTRAL Y CENSO EXHAUSTIVO
## IJF SOR Assistant 2026

**Fecha de última actualización:** 7 de noviembre de 2026  
**Product Owner y Autoridad Normativa (Autoridad Soberana):** Alexis Oliveros Lozano  
**Planificador, Supervisor Metodológico y Auditor Independiente:** ChatGPT  
**Ejecutor Técnico:** Antigravity  
**Repositorio Local:** `C:\PROYECTOS\IJF-SOR-Assistant`

---

## 1. PRINCIPIOS DE GOBERNANZA, JERARQUÍA Y PREVALENCIA DOCUMENTAL

La documentación del proyecto se gobierna bajo los siguientes principios soberanos:

1. **Prevalencia de Autoridad y Alcance:**  
   Un documento emanado de la autoridad soberana del Product Owner (Alexis Oliveros Lozano) prevalece sobre cualquier propuesta, dictamen técnico o análisis metodológico. Un documento con alcance normativo general cede ante una instrucción o decisión específica aplicable a un componente determinado.
2. **Decisión Explícita de Sustitución:**  
   Ningún documento sustituye automáticamente a otro por mera fecha de creación. Para que un documento anterior pierda vigencia, debe mediar una decisión explícita de sustitución, revocación o archivo formalmente documentada.
3. **Aprobación Soberana del Product Owner:**  
   Toda nueva fase, cambio arquitectónico, alteración de alcance o definición canónica requiere la aprobación expresa y formal de Alexis Oliveros Lozano. Las recomendaciones de ChatGPT o informes de Antigravity son insumos consultivos y de auditoría.
4. **Registro Transparente de Contradicciones:**  
   En caso de discrepancia documental no resuelta por una decisión formal, la divergencia no se interpretará libremente; se registrará como **"Pendiente de decisión del Product Owner"**.

### Categorías Funcionales de Clasificación
- **Categoría 1 (Rector / Normativo):** Mandatos soberanos de Alexis, actas de reorientación y corpus oficial canónico SOR 2026-08 (Tier 1). Prevalecen sobre cualquier otro documento técnico.
- **Categoría 2 (Decisiones Soberanas):** Registro centralizado de resoluciones dictadas por Alexis Oliveros (`docs/DECISIONES.md`).
- **Categoría 3 (Planificación y Fases Correctivas Vigentes):** Plan maestro P0/P1 e informes oficiales de cierre de fases aprobadas.
- **Categoría 4 (Arquitectura y Diseño Operativo):** Especificaciones de componentes activos (Lean RRE 3.0, ADA v2, DocumentValidator).
- **Categoría 5 (Evaluación Normativa y Gold Standards):** Catálogo VF01, dictámenes arbitrales de 11 casos, informe experimental de $K$ y suites formales.
- **Categoría 6 (Despliegue e Infraestructura):** Manifiesto de producción OCI y guías de aprovisionamiento en la nube.
- **Categoría 7 (Referencial / Conceptual):** Diseños conceptuales multifuente previos o directrices taxonómicas no implementadas operativamente.
- **Categoría 8 (Histórico / Sustituido / Archivado):** Documentación de fases canceladas (Fase 4.2.6), expedientes empaquetados y versiones legacy del MVP inicial. Carecen de vigencia operativa.

---

## 2. CATÁLOGO RECTOR DE DOCUMENTOS VIGENTES Y OPERATIVOS

### A. Documentos Rectores y Normativos
| Ruta Relativa | Título / Identificador | Tipo | Estado | Función / Autoridad |
|---|---|---|---|---|
| `docs/acta_aprobacion_reorientacion_lean_ijf_sor_assistant.md` | Acta de Aprobación Soberana: Reorientación Lean | Acta Soberana | **Vigente** | Decisión de Alexis (06/11/2026): archivo definitivo de Fase 4.2.6 y mandato de arquitectura Lean RRE/ADA. |
| `docs/plan_correctivo_p0_p1.md` | Plan Correctivo P0/P1 Revisado | Plan Maestro | **Vigente** | Marco rector que gobierna las fases correctivas P0-A, P0-B, P0-C, P1-A y P1-B. |
| `src/corpus_config.py` | Configuración Canónica de Edición Oficial | Código Rector | **Vigente** | Fija inexorablemente el SOR de 14 de agosto de 2026 (385 pasajes) como única edición activa. |

### B. Registro Central de Decisiones
| Ruta Relativa | Título / Identificador | Tipo | Estado | Función / Autoridad |
|---|---|---|---|---|
| `docs/DECISIONES.md` | Registro Central de Decisiones Aprobadas | Registro Oficial | **Vigente** | Bitácora cronológica de todas las decisiones soberanas aprobadas por Alexis Oliveros (DEC-001 a DEC-009). |

### C. Informes Oficiales de Cierre de Fases Correctivas y Evaluación Experimental
| Ruta Relativa | Título / Identificador | Tipo | Estado | Fase / Decisión Asociada |
|---|---|---|---|---|
| `docs/evaluacion/catalogo_vf01_normativo.md` | Catálogo Maestro de Evaluación Normativa VF01 (52 casos) | Gold Standard | **Vigente** | Fase P0-A |
| `docs/auditoria/validacion_humana_resultados_actuales.md` | Dictamen Arbitral de 11 Casos Prioritarios (Alexis Oliveros) | Dictamen Arbitral | **Vigente** | Fase P0-A / P0-B (DEC-003) |
| `docs/auditoria/informe_fase_P0_B_ingenieria_rre.md` | Informe de Cierre Fase P0-B (RRE Kumi-kata y ESC-09) | Informe Cierre | **Vigente** | Fase P0-B (DEC-004) |
| `docs/auditoria/informe_fase_P0_C_razonamiento_seleccion_sintesis.md` | Informe Técnico Fase P0-C (Selección y Síntesis) | Informe Cierre | **Vigente** | Fase P0-C (DEC-005) |
| `docs/auditoria/informe_complementario_validacion_final_P0_C.md` | Informe Complementario de Validación Final P0-C (9/9 PASS) | Evidencia Test | **Vigente** | Fase P0-C (DEC-005) |
| `docs/auditoria/informe_fase_P1_A_abstencion_ood.md` | Informe Técnico y Auditoría Final Fase P1-A (40 casos balanceados) | Informe Cierre | **Vigente** | Fase P1-A (DEC-006) |
| `docs/auditoria/informe_fase_P1_B_configuracion_e2e.md` | Informe Técnico de Auditoría y Regresión Fase P1-B | Informe Cierre | **Vigente** | Fase P1-B (DEC-007) |
| `docs/auditoria/informe_auditoria_mecanismo_novedades.md` | Informe de Auditoría del Mecanismo de Novedades (7 tipos, CSV) | Informe Técnico | **Vigente** | Fase P1-B (DEC-008) |
| `docs/auditoria/experimento_comparativo_k_rre_2026_11.md` | Evaluación Experimental Comparativa de K en RRE 3.0 | Evidencia Experimental | **Vigente** | Soporte técnico de DEC-009 ($K=5$ canónico) |
| `docs/auditoria/implementacion_local_k5_2026_11.md` | Informe Técnico de Implementación Local K=5 Canónico | Informe Técnico | **Vigente** | Evidencia de ejecución técnica y verificación de DEC-009 ($K=5$) |

### D. Arquitectura y Diseño Técnico Operativo
| Ruta Relativa | Título / Identificador | Tipo | Estado | Función |
|---|---|---|---|---|
| `docs/arquitectura/diseno_compuerta_evidencia_certificada.md` | Diseño de la Compuerta de Evidencia Certificada | Especificación | **Vigente** | Arquitectura de DocumentValidator, segregación Tier 1 y EvidenceBundle. |
| `docs/informe_cierre_lean_paso1_stitching_rre.md` | Informe de Cierre Lean Paso 1: Stitching RRE | Informe Técnico | **Vigente** | Integración del costurador de pasajes contiguos. |
| `docs/informe_cierre_lean_paso2_sinonimos_judo.md` | Informe de Cierre Lean Paso 2: Sinónimos de Judo | Informe Técnico | **Vigente** | Normalización de equivalencias léxicas y coloquiales del judo. |

### E. Despliegue e Infraestructura
| Ruta Relativa | Título / Identificador | Tipo | Estado | Función |
|---|---|---|---|---|
| `docs/deployment/PRODUCTION_MANIFEST.md` | Manifiesto de Configuración y Producción OCI | Manifiesto | **Vigente** | Estado de producción `https://sor.alxol.com` (commit `61afc1b`) y brechas con local. |
| `docs/deployment/oci_deployment.md` | Guía de Despliegue en la Nube (OCI) | Guía Operativa | **Referencial** | Guía de aprovisionamiento, claves SSH y systemd. |

---

## 3. DOCUMENTOS REFERENCIALES Y CONCEPTUALES (SIN VIGENCIA OPERATIVA)

Documentos elaborados durante iteraciones teóricas o taxonómicas que aportan valor conceptual pero **no rigen la operación actual del sistema**:

| Ruta Relativa | Título / Identificador | Tipo | Estado | Condición y Límite de Vigencia |
|---|---|---|---|---|
| `docs/diseno_arquitectura_conocimiento_multifuente_ijf.md` | Diseño de Arquitectura Multifuente | Diseño Conceptual | **Referencial** | Modelo teórico de integración de fuentes complementarias; no opera en código (DEC-001). |
| `docs/registro_documental_multifuente_ijf.csv` | Catálogo de Fuentes Multifuente | Taxonomía CSV | **Referencial** | Define jerarquía teórica de Tiers; el motor opera exclusivamente con Tier 1 canónico. |
| `docs/diagnostico_reorientacion_funcional_ijf_sor_assistant.md` | Diagnóstico de Reorientación Funcional | Diagnóstico | **Referencial** | Documento base que justificó la adopción de la arquitectura Lean. |

---

## 4. CENSO EXHAUSTIVO DE ARCHIVOS EN `docs/` (219 ARCHIVOS TOTALES)

El directorio `docs/` aloja un total de **219 archivos** (160 archivos `.md`, 14 `.csv`, 6 `.zip`, 33 imágenes `.png`, 4 `.json` y 1 `.pdf`), censados exhaustivamente a continuación:

### A. Subdirectorios Archivados o Históricos (93 archivos)
1. **`docs/archive_v2_8/` (4 archivos .md):** Expediente histórico de iteración v2.8 de la Fase 4.2.6 (archivado por DEC-001).
2. **`docs/archive_v2_9/` (4 archivos .md):** Expediente histórico de iteración v2.9 de la Fase 4.2.6 (archivado por DEC-001).
3. **`docs/architecture/` (5 archivos .md):** Especificaciones legacy del MVP inicial v1.0 (julio 2026, motor TF-IDF sobre corpus desfasado).
4. **`docs/audit_appendix_e/` (6 archivos .md + 32 imágenes .png):** Auditoría visual de pasajes de apéndices realizada en octubre 2026.
5. **`docs/project-management/` (7 archivos .md):** Bitácoras y cronogramas de planificación del MVP original de julio 2026.
6. **`docs/reports/` (27 archivos .md):**
   - `docs/reports/coverage_audit_2026_08/` (3 .md)
   - `docs/reports/coverage_audit_2026_08/delivery/` (4 .md)
   - `docs/reports/coverage_audit_2026_08/followup_review/` (14 .md)
   - Informes intermedios de ingesta y cobertura del PDF de agosto 2026 (octubre 2026).
7. **Paquetes ZIP de expedientes archivados (6 archivos .zip):**
   - `docs/expediente_fase4_2_6_v2_7.zip`
   - `docs/expediente_fase4_2_6_v2_8.zip`
   - `docs/expediente_fase4_2_6_v2_9.zip`
   - `docs/expediente_fase4_2_6_v3_0.zip`
   - `docs/expediente_gobernanza_documental_2026_11_07.zip`
   - `docs/expediente_*.zip` complementarios.

### B. Subdirectorios Operativos y de Evaluación (21 archivos)
1. **`docs/auditoria/` (10 archivos .md):** Expedientes e informes formales de las fases P0-A, P0-B, P0-C, P1-A, P1-B, mecanismo de novedades y el informe de evaluación experimental comparativa de $K$.
2. **`docs/evaluacion/` (8 archivos .md + 1 .csv):** Catálogo VF01, líneas base y matrices de evaluación por capas.
3. **`docs/arquitectura/` (1 archivo .md):** Diseño de la compuerta de evidencia certificada (vigente).
4. **`docs/deployment/` (2 archivos .md):** Manifiesto de producción (`PRODUCTION_MANIFEST.md`) y guía OCI (`oci_deployment.md`).
5. **`docs/guides/` (1 archivo .pdf):** Guía de usuario oficial del asistente.

### C. Archivos en la Raíz de `docs/` (86 archivos .md + datasets .csv y .json)
Los 86 archivos `.md` situados directamente en la raíz de `docs/` corresponden a las siguientes agrupaciones funcionales:
1. **Gobernanza Central (4 archivos):** `INDEX_DOCUMENTAL.md`, `DECISIONES.md`, `acta_aprobacion_reorientacion_lean_ijf_sor_assistant.md`, `plan_correctivo_p0_p1.md`. *(Vigentes)*
2. **Evaluación Normativa VF01 (3 archivos):** `dictamen_auditoria_vf01.md`, `validacion_funcional_consolidada_vf01.md`, `evidencia_revision_vf01.md`. *(Referenciales / Base histórica de P0-A)*
3. **Arquitectura RRE 3.0 y Lean Pasos 1 y 2 (6 archivos):** `diseno_arquitectura_rre_3_0.md`, `backlog_rre_3_0.md`, `plan_implementacion_lean_paso2_sinonimos_judo.md`, `informe_cierre_lean_paso1_stitching_rre.md`, `informe_cierre_lean_paso2_sinonimos_judo.md`, `informe_inspeccion_parametros_rre_ada.md`. *(Vigentes / Operativos)*
4. **Planes e Informes de Fases Anteriores Sustituidas — Fases 1 a 4.2.5 (38 archivos):**
   - Fase 1: `informe_fase1_rre_3_0.md`, `cierre_fase1_rre_3_0.md`, `auditoria_cierre_fase1_rre_3_0.md`, etc. *(Sustituidos por P0/P1)*
   - Fase 2: `plan_fase2_chunk_stitching_rre_3_0.md`, `informe_implementacion_fase2_chunk_stitching_rre_3_0.md`, `cierre_fase2_chunk_stitching_rre_3_0.md`. *(Sustituidos por Lean Paso 1)*
   - Fase 3: `diseno_fase3_ranking_semantico_disambiguacion_ood.md`, `informe_implementacion_fase3_rre_3_0.md`, `cierre_fase3_rre_3_0.md`, `auditoria_aceptacion_fase3_rre_3_0.md`. *(Sustituidos por P1-A y Lean)*
   - Fases 4.1 a 4.2.5: `plan_maestro_fase4_multifuente_ijf.md`, `orden_ejecucion_fase4_2_ijf.md`, `informe_implementacion_fase4_2_2_ijf.md`, `benchmark_fase4_2_5_multifuente_ijf.md`, `plan_fase4_2_5_calibracion_multifuente_ijf.md`, etc. *(Sustituidos y archivados formalmente por DEC-001)*
5. **Expediente de la Fase 4.2.6 Cancelada (12 archivos):** `plan_maestro_implementacion_fase4_2_6.md`, `diseno_fase4_2_6_fusion_arbitraje_ijf.md`, `matriz_criterios_aceptacion_fase4_2_6.md`, `informe_plan_maestro_fase4_2_6.md`, `informe_revision_plan_maestro_fase4_2_6.md`, `expediente_revision_plan_maestro_fase4_2_6.md`, etc. *(Cancelados y archivados formalmente por el Acta de Reorientación Lean y DEC-001)*
6. **Bloque BK01 — Negative Domain Anchor Scoring Preliminar (4 archivos):** `benchmark_bk01_negative_domain_anchor_scoring.md`, `informe_implementacion_bk01_negative_domain_anchor_scoring.md`, `auditoria_final_bk01_negative_domain_anchor_scoring.md`, `auditoria_preliminar_bk01.md`. *(Antecedente directo integrado y superado por P1-A)*
7. **Auditorías Generales y de Código (19 archivos):** `auditoria_integral_codigo.md`, `auditoria_estructural_rre_ada.md`, `auditoria_cobertura_documental_ijf.md`, `auditoria_vigencia_documentos_complementarios_ijf.md`, `auditoria_merge_integracion_local_ijf_sor_2026.md`, `auditoria_final_prepublicacion_ijf_sor_2026.md`, etc. *(Históricos / De consulta referencial)*

---

## 5. REGLAS PERMANENTES DE MANTENIMIENTO DOCUMENTAL

1. **Inclusión y Censo Obligatorio:** Todo nuevo documento técnico que se cree en `docs/` debe ser censado en este índice bajo su categoría correspondiente antes de darse por concluido.
2. **Prohibición de Eliminación de Históricos:** Ningún documento histórico o expediente archivado puede ser destruido. Se clasifica en la Sección 4 para salvaguardar la trazabilidad histórica del proyecto.
3. **Registro de Sustituciones:** Cuando un documento reemplace operativamente a otro, se debe dejar constancia explícita en este índice citando el documento sucesor.
4. **Sincronización Simultánea con `PROJECT_STATUS.md` y `DECISIONES.md`:** Todo cambio de fase, release o directriz soberana debe asentarse concurrentemente en los tres instrumentos rectores.

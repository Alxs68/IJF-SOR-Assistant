# Criterios de Aceptación y Métricas de Calibración — Fase 4.2.5
**Proyecto:** IJF SOR Assistant  
**Fase:** 4.2.5 — Calibración y Endurecimiento del Retrieval Multifuente  
**Supervisor:** Alexis Oliveros Lozano  
**Arquitectura y Auditoría:** ChatGPT  
**Ejecutor:** Antigravity  
**Fecha:** 2026-11-05  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Estado:** **PROPUESTA TÉCNICA DE CRITERIOS — PENDIENTE DE REVISIÓN Y APROBACIÓN**

---

## 1. Definición Operacional de Métricas de Evaluación

Para evitar ambigüedades interpretativas, cada métrica de la Fase 4.2.5 cuenta con su formulación matemática estricta y dataset aplicable:

### 1.1. Recall@1 Dirigido (Recall Complementario Específico)
- **Definición:** Proporción de consultas del subconjunto complementario etiquetado donde el fragmento Sidecar relevante esperado es recuperado exactamente en la primera posición ($\text{Rank} = 1$).
- **Fórmula:**
  $$\text{Recall@1} = \frac{1}{|Q_{\text{comp}}|} \sum_{q \in Q_{\text{comp}}} \mathbb{I}(\text{Top1}(q) == \text{ExpectedChunk}(q))$$
- **Dataset:** 20 consultas complementarias (Tier 2, Tier 3, Premisas Negativas, Adversariales y Bilingües aplicables).
- **Meta Propuesta:** $\ge 95.0\%$.

### 1.2. Tasa de Falsos Positivos Normativos (FPR Normativo)
- **Definición:** Frecuencia con la que el Sidecar retorna un fragmento complementario con score calificado ante consultas normativas canónicas puras del SOR 2026 o consultas fuera de dominio (OOD).
- **Fórmula:**
  $$\text{FPR} = \frac{\sum_{q \in Q_{\text{abstain}}} \mathbb{I}(\text{SidecarStatus}(q) == \text{"QUALIFIED\_MATCH"})}{|Q_{\text{abstain}}|}$$
- **Dataset:** 15 consultas etiquetadas como `ABSTAIN_SIDECAR` o `ABSTAIN_ALL` (Categorías 3, 4 y 5).
- **Meta Propuesta:** $0.0\%$ (Cero falsos positivos calificados).

### 1.3. Invariabilidad Primaria del RRE 2026
- **Definición:** Concordancia estricta bit a bit entre la respuesta y ranking del RRE oficial con el mecanismo Shadow Sidecar desactivado (`OFF`) versus activado (`ON`).
- **Fórmula:**
  $$\text{Invarianza} = \prod_{q \in Q_{\text{total}}} \mathbb{I}(\text{RRE}_{\text{OFF}}(q) \equiv \text{RRE}_{\text{ON}}(q))$$
- **Dataset:** Total de las 40 consultas del benchmark ampliado.
- **Meta Exigida:** $100.0\%$ (Sin tolerancia; cero discrepancias).

### 1.4. Trazabilidad Criptográfica y de Gobernanza
- **Definición:** Porcentaje de fragmentos recuperados en modo sombra que preservan de forma inmutable su identificador de chunk, identificador de documento, autoridad, vigencia, elegibilidad y hash SHA-256 de staging.
- **Meta Exigida:** $100.0\%$.

### 1.5. Latencia Incremental y Overhead Temporal
- **Definición:** Delta de tiempo promedio introducido en el pipeline global del RRE debido a la ejecución del Sidecar calibrado.
- **Fórmula:**
  $$\Delta_{\text{latencia}} = \text{Media}(\text{Latencia}_{\text{ON}}) - \text{Media}(\text{Latencia}_{\text{OFF}})$$
- **Meta Contractual:** $\Delta_{\text{latencia}} \le +45.0\text{ ms}$ (con overhead interno de Sidecar $\le 2.0\text{ ms}$).

---

## 2. Matriz de Criterios de Aceptación Propuestos (Fase 4.2.5)

| Identificador | Criterio de Calidad | Métrica Evaluada | Objetivo Propuesto | Procedimiento de Verificación | Evidencia Requerida |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CRIT-425-01** | **Recall Dirigido Sidecar** | Recall@1 sobre dataset complementario ($N=20$) | $\ge 95.0\%$ | Batería automatizada de benchmark ampliado. | Tabla de resultados individuales con coincidencia de chunk exacto. |
| **CRIT-425-02** | **Falsos Positivos Normativos** | Candidatos no calificados en consultas canónicas/OOD | **0 Falsos Positivos** | Evaluación sobre 15 consultas etiquetadas para abstención. | Status `ABSTAIN` o score por debajo de corte en las 15 consultas. |
| **CRIT-425-03** | **Invarianza RRE Primario** | Equivalencia bit a bit de `evidence` y `scores` SOR | **100% Invarianza** | Ejecución en paralelo OFF vs ON sobre las 40 consultas. | Comparación automatizada de JSON responses sin mutaciones. |
| **CRIT-425-04** | **Trazabilidad Documental** | Preservación de Tupla de Gobernanza | **100% Conforme** | Inspección de metadatos en cada match retornado. | Presencia de `chunk_id`, `document_id`, `authority`, `validity`, `staging_sha256`. |
| **CRIT-425-05** | **Integridad Criptográfica SOR** | Verificación SHA-256 de 5 artefactos canónicos | **100% Inmutabilidad** | Cálculo de hashes físicos en disco contra valores canónicos. | Coincidencia de hashes de PDF, pasajes, vector index, dense meta y KG. |
| **CRIT-425-06** | **Tolerancia a Fallos y Timeout** | Aislamiento ante caída o retraso del Sidecar | **100% Resiliencia** | Simulación de corrupción de índice y forzado de timeout. | RRE primario responde con status `SUCCESS` sin degradación. |
| **CRIT-425-07** | **Presupuesto de Latencia** | Overhead incremental medio en consulta | $\le +45.0\text{ ms}$ | Benchmark de 10 consultas x 3 repeticiones con warm-up. | Reporte estadístico de Media, Mediana, P95 y StdDev. |
| **CRIT-425-08** | **Regresión Global del Repo** | Suite de pruebas automatizadas `tests/` | **100% PASS (0 fallos)** | Ejecución de `python -m pytest tests/ -v`. | $\ge 261$ pruebas aprobadas en el repositorio. |

---

## 3. Condiciones de Rechazo Inmediato (Stop-Gates)

Cualquiera de los siguientes eventos obligará a suspender la fase y declarar rechazo técnico inmediato:
1. **Contaminación Primaria:** Si un fragmento complementario aparece en el array `evidence` del RRE primario retornado a la interfaz o ADA.
2. **Mutación Criptográfica:** Si el hash SHA-256 de cualquiera de los 5 artefactos primarios del SOR 2026 varía en un solo bit.
3. **Bloqueo Síncrono:** Si una excepción en el módulo Sidecar interrumpe la ejecución del RRE o propaga un error no capturado al usuario.
4. **Activación no Autorizada:** Si el feature flag `enable_shadow_mode_multisource` resulta configurado como `True` por defecto.

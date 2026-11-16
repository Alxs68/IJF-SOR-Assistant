# SOR-IJF — PLAN DE PRUEBAS FASE 4.2
**Protocolo de Validación Multifuente, OOD Refinado y Evaluación Shadow**

- **Proyecto:** IJF Sport and Organisation Rules (SOR) Assistant
- **Fase:** Fase 4.2.0 — Plan de Pruebas
- **Fecha:** 2026-11-05
- **Rama Git:** `integration/ijf-sor-2026-08-merge` (Commit Base: `61afc1bc`)
- **Autor / Ejecutor Técnico:** Antigravity
- **Arquitectura y Auditoría:** ChatGPT
- **Supervisión Normativa:** Alexis

---

## 1. OBJETIVO DEL PLAN DE PRUEBAS

Definir la estrategia de verificación y validación experimental para certificar:
1. La eficacia del refinamiento OOD con anclas negativas (**BK-01**).
2. El correcto funcionamiento de la compuerta de anclaje SOR y los Sidecar Indexes.
3. La ausencia de regresiones sobre la suite histórica (212 tests).
4. El comportamiento del modo sombra (*Shadow Mode*).

---

## 2. SUITES DE PRUEBAS Y CASOS DE PRUEBA

### 2.1 Batería OOD Multi-Deporte (Refinamiento BK-01)
Diseñada para resolver las limitaciones de generalización `GEN-08` y `GEN-09`:

| ID | Consulta de Prueba | Dominio Real | Comportamiento Esperado | Criterio de PASS |
|---|---|---|---|---|
| **OOD-BK01** | En tenis, ¿cuándo se disputa un tie-break a 7 puntos? | Tenis (Raqueta) | `ABSTAIN (OUT_OF_DOMAIN)` | $J_{\text{score}} < \Theta_{\text{OOD}}$ por ancla negativa de tenis. |
| **OOD-BK02** | ¿Cuál es la distancia máxima permitida de patada submarina en natación? | Natación (Acuático) | `ABSTAIN (OUT_OF_DOMAIN)` | `ABSTAIN` limpio; no empareja con Sokuteiki C1.1.4. |
| **OOD-BK03** | ¿Cuántos puntos vale un tiro libre tras una falta técnica en baloncesto? | Baloncesto | `ABSTAIN (OUT_OF_DOMAIN)` | `ABSTAIN` limpio; confirmado en TC-16. |
| **OOD-BK04** | ¿Cuándo se aplica tarjeta roja directa por último recurso en fútbol? | Fútbol | `ABSTAIN (OUT_OF_DOMAIN)` | `ABSTAIN` limpio; confirmado en GEN-07. |
| **OOD-BK05** | ¿Cuántos rounds de 3 minutos dura una pelea por título en boxeo profesional? | Boxeo | `ABSTAIN (OUT_OF_DOMAIN)` | `ABSTAIN` limpio por ancla negativa de striking. |
| **OOD-BK06** | En judo, ¿cuántos puntos otorga una proyección limpia de espalda? (Control) | Judo (In-Domain) | **PASS (Ippon)** | In-domain admitido; recupera Art. 14. |

---

### 2.2 Batería de Aislamiento y Compuerta de Anclaje SOR (`SOR_Anchor_Gate`)

| ID | Consulta de Prueba | Ancla SOR Primaria | Sidecar Recuperado | Criterio de PASS |
|---|---|---|---|---|
| **GATE-01** | Transición a Ne-waza con arrastre continuo | Art. 16 (Tier 1) | PPT-002 Slide 14 (Tier 3) | Ambos presentes; Art. 16 en Top-1 primario. |
| **GATE-02** | Consulta sobre tecnología de sensores en tatami 3 | Art. 8.7 (Tier 1 marginal) | Bloqueado / Insuficiente | No expande a complementos si el ancla SOR no supera $\tau_{\text{anchor}} \ge 0.50$. |
| **GATE-03** | Reglas de reversión en Cadetes (Reverse Seoi-nage) | Art. 18.1.4 (Tier 1) | NEW-001 (Tier 2) | Expande a circular oficial LA28; atribución correcta. |
| **GATE-04** | Intento de inyectar documento no aprobado (`PENDIENTE`) | Art. 18 (Tier 1) | `PAG-002` (Pendiente) | El sidecar omite `PAG-002` por `NO_ELEGIBLE`. |

---

### 2.3 Batería de No-Regresión Contractual (TC-01 a TC-22)
Se ejecuta la batería oficial completa de 22 casos canónicos para comprobar que:
- Los 22 casos se mantienen en **22/22 PASS (100%)**.
- Cero degradaciones de puntuación en Waza-ari lateral (TC-04).
- Cero desambiguaciones erróneas en comando Mate (TC-15).
- Cero aceptaciones erróneas en baloncesto (TC-16) o finanzas (TC-17).

---

## 3. PROTOCOLO DE BENCHMARK DE LATENCIA Y CONSUMO

1. **Condiciones de Medición:**
   - Entorno local controlado, CPU monocanal y multihilo.
   - Batería de 30 repeticiones por consulta ($N=30$).
2. **Métricas a Registrar:**
   - Tiempo de inferencia RRE Línea Base (Fase 3).
   - Tiempo de inferencia RRE + Sidecar en Modo Shadow.
   - Delta Promedio ($\Delta_{\text{mean}}$), Delta Mediana ($\Delta_{\text{med}}$) y Delta Percentil 95 ($\Delta_{\text{p95}}$).
3. **Límite Contractual:**
   - $\Delta_{\text{mean}} \le +35.00\text{ ms}$ sobre la línea base de Fase 3.
   - $\Delta_{\text{p95}} \le +60.00\text{ ms}$.

---

## 4. REGISTRO DE DISCREPANCIAS EN MODO SOMBRA (*SHADOW LOGGING*)

Cada ejecución en modo sombra debe volcar a `scratch/shadow_evaluation_log.jsonl` un registro estructurado:

```json
{
  "timestamp": "2026-11-05T00:00:00Z",
  "query": "Texto de consulta",
  "baseline_top1_kun": "SOR-2026-08-P165-S185",
  "baseline_latency_ms": 32.4,
  "shadow_top1_sor_kun": "SOR-2026-08-P165-S185",
  "shadow_supplementary_pids": ["PPT-002-CHK-014"],
  "shadow_latency_ms": 48.1,
  "delta_ms": 15.7,
  "normative_concordance": true,
  "conflict_detected": false,
  "evidence_bundle_valid": true
}
```
Si `normative_concordance == false` o `conflict_detected == true`, se genera una alerta inmediata en la bitácora para revisión del arquitecto.

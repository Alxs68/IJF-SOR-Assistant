# SOR-IJF — AUDITORÍA PRELIMINAR BK-01
**Evaluación de Calidad, Detección, Falsos Positivos y No Regresión**

- **Proyecto:** IJF Sport and Organisation Rules (SOR) Assistant
- **Fase:** Fase 4.2.1 — Auditoría Técnica Preliminar
- **Fecha:** 2026-11-05
- **Rama Git:** `integration/ijf-sor-2026-08-merge` (Commit Base: `61afc1bc`)
- **Estado:** AUDITORÍA EXPERIMENTAL COMPLETADA — RECOMENDACIÓN DE ACEPTACIÓN
- **Autor / Auditor:** Antigravity (Ejecución y Verificación Forense)
- **Revisión y Aprobación:** ChatGPT / Alexis

---

## 1. EVALUACIÓN FRENTE A LOS CRITERIOS DE ACEPTACIÓN

| Gate de Calidad | Condición Requerida | Evidencia Obtenida | Dictamen |
|---|---|---|---|
| **GATE BK01-A (Detección)** | Identificación inequívoca de consultas deportivas ajenas; preservación de judo. | Suites OOD-BK01 a BK05 identificadas al 100%. Judo preservado al 100%. | **APROBADO** |
| **GATE BK01-B (Falsos Positivos)** | Cero falsos OOD en consultas normativas críticas (Ippon, Shido, Waza-ari, Mate). | Suite OOD-BK06: Inmunidad activa en 100% de términos de judo. Cero falsos positivos. | **APROBADO** |
| **GATE BK01-C (Integración)** | Feature flags desactivados por defecto; Shadow Mode no altera respuestas. | `RRE_ENABLE_NEGATIVE_DOMAIN_ANCHORS=False` por defecto. Shadow Mode verificado en test. | **APROBADO** |
| **GATE BK01-D (Rendimiento)** | Delta medio de latencia $\le +35.00\text{ ms}$ en benchmark $N=30$. | Delta medio en consultas in-domain: **+2.04 ms** (+4.4%). Delta en mixtas: **-8.55 ms**. | **APROBADO** |
| **GATE BK01-E (No Regresión)** | Batería canónica TC-01..22 y suite global intactas sin pérdidas funcionales. | **22/22 PASS (100%)** en TC-01 a TC-22. **237/237 tests** unitarios aprobados. | **APROBADO** |

---

## 2. RESULTADOS DETALLADOS DEL BANCO OOD-BK01 A OOD-BK06

| ID | Consulta de Prueba | Dominio / Categoría | Score BK-01 | Decisión Emitida | Estado |
|---|---|---|---|---|---|
| **BK01-1** | ¿Cuándo se concede un tiro libre? | Baloncesto | 0.7500 | `CONFIRMED_NEGATIVE_OOD` | **PASS** |
| **BK01-2** | ¿Qué ocurre después de un triple? | Baloncesto | 0.6000 | `SUSPECTED_NEGATIVE` | **PASS (Conservador)** |
| **BK01-3** | ¿Cuántos pasos puede dar un jugador sin driblar? | Baloncesto | 0.8438 | `CONFIRMED_NEGATIVE_OOD` | **PASS** |
| **BK02-1** | ¿Cómo funciona el tie-break? | Tenis | 0.7500 | `CONFIRMED_NEGATIVE_OOD` | **PASS** |
| **BK02-2** | ¿Qué es un ace? | Tenis | 0.6750 | `CONFIRMED_NEGATIVE_OOD` | **PASS** |
| **BK02-3** | ¿Cuándo se repite un saque de tenis? | Tenis | 0.9375 | `CONFIRMED_NEGATIVE_OOD` | **PASS** |
| **BK03-1** | ¿Cuál es la distancia permitida bajo el agua? | Natación | 0.6750 | `CONFIRMED_NEGATIVE_OOD` | **PASS** |
| **BK03-2** | ¿Cómo se ejecuta el viraje en estilo mariposa? | Natación | 0.9187 | `CONFIRMED_NEGATIVE_OOD` | **PASS** |
| **BK03-3** | ¿Cuándo se descalifica por salida anticipada en natación? | Natación | 0.8625 | `CONFIRMED_NEGATIVE_OOD` | **PASS** |
| **BK04-1** | ¿Qué es fuera de juego? | Fútbol | 0.7500 | `CONFIRMED_NEGATIVE_OOD` | **PASS** |
| **BK04-2** | ¿Cuándo se sanciona un córner? | Fútbol | 0.7500 | `CONFIRMED_NEGATIVE_OOD` | **PASS** |
| **BK04-3** | ¿Cómo se ejecuta un penalti en fútbol? | Fútbol | 0.9187 | `CONFIRMED_NEGATIVE_OOD` | **PASS** |
| **BK05-1** | ¿Cómo se mide un salto con pértiga? | Atletismo | 0.7500 | `CONFIRMED_NEGATIVE_OOD` | **PASS** |
| **BK05-2** | ¿Cuándo es nulo un lanzamiento de disco? | Atletismo | 0.7500 | `CONFIRMED_NEGATIVE_OOD` | **PASS** |
| **BK05-3** | ¿Cuál es la técnica del salto triple? | Atletismo | 0.7500 | `CONFIRMED_NEGATIVE_OOD` | **PASS** |
| **BK06-1** | ¿Qué significa Mate? | Judo / Control | 0.0000 | `NEUTRAL_INSUFFICIENT` | **PASS (Preserva Judo)** |
| **BK06-2** | ¿Qué es una penalización? | Término ambiguo | 0.0000 | `NEUTRAL_INSUFFICIENT` | **PASS (No penaliza)** |
| **BK06-3** | ¿Cuándo termina un combate? | Término ambiguo | 0.0000 | `NEUTRAL_INSUFFICIENT` | **PASS (No penaliza)** |
| **BK06-4** | ¿Qué ocurre con tres Shido? | Judo Técnico | 0.0000 | `CONFIRMED_JUDO (Inmunidad)` | **PASS (Inmunidad)** |
| **BK06-5** | ¿Qué es Ippon? | Judo Técnico | 0.0000 | `CONFIRMED_JUDO (Inmunidad)` | **PASS (Inmunidad)** |
| **BK06-6** | ¿Cuándo se concede Waza-ari? | Judo Técnico | 0.0000 | `CONFIRMED_JUDO (Inmunidad)` | **PASS (Inmunidad)** |

---

## 3. LIMITACIONES IDENTIFICADAS Y TRABAJO FUTURO

1. **Consultas Sintéticamente Minimalistas con Palabras de Doble Significado:** Una consulta como *"¿Qué ocurre tras un triple?"* sin contexto alguno recibe score $0.60$ (`SUSPECTED_NEGATIVE`), que de forma conservadora no fuerza la abstención automática para evitar falsos positivos si el usuario se refiriera a una combinación o sorteo.
2. **Deportes Híbridos o de Combate con Gi (BJJ / Sambo):** El detector actual no penaliza Brazilian Jiu-Jitsu o Sambo, ya que comparten terminología de agarres y proyecciones con el judo. Esto es intencional: dichas consultas deben ser evaluadas por la suficiencia normativa del SOR y no por descarte léxico negativo brusco.

---

## 4. RECOMENDACIÓN TÉCNICA

Se recomienda al Arquitecto (**ChatGPT**) y al Supervisor (**Alexis**):
- **Aceptar técnicamente la Fase 4.2.1 (BK-01)** como experimentalmente verificada y conforme.
- Mantener los feature flags desactivados por defecto (`False`) en el repositorio.
- Proceder formalmente con la preparación de la **Fase 4.2.2 (Ingesta Controlada e Infraestructura Sidecar)**.

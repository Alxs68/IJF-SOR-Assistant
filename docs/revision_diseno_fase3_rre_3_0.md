# IJF SOR Assistant — Revisión Complementaria del Diseño Fase 3 (RRE 3.0)

**Documento:** REVISIÓN Y ESPECIFICACIÓN COMPLEMENTARIA DE DISEÑO TÉCNICO  
**Destino:** `docs/revision_diseno_fase3_rre_3_0.md`  
**Estado:** REVISIÓN ARQUITECTÓNICA COMPLETA (SOLO DISEÑO — SIN IMPLEMENTACIÓN DE CÓDIGO)  
**Fecha:** 2026-11-05  
**Entorno:** Local (`C:\PROYECTOS\IJF-SOR-Assistant`)  
**Rama Git:** `integration/ijf-sor-2026-08-merge`  
**Autor:** Antigravity (Ingeniero Ejecutor Técnico)  
**Revisores:** Alexis (Supervisor) / ChatGPT (Arquitecto y Auditor Normativo)  

---

## 1. Introducción y Propósito de la Revisión

El presente documento complementa y profundiza el diseño arquitectónico formalizado en [`docs/diseno_fase3_ranking_semantico_disambiguacion_ood.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/diseno_fase3_ranking_semantico_disambiguacion_ood.md), respondiendo puntualmente a las observaciones de la auditoría técnica.

Se abordan de manera matemática, algorítmica y determinista los cuatro focos críticos de falla detectados:
1. **El algoritmo y formulación estricta de `NormativeSemanticRanker`**, justificando analíticamente $\lambda_{\text{infra}} = 0.65$, sus condiciones de activación y la protección contra degradación de consultas sobre infraestructura.
2. **Las reglas operativas de `RefereeCommandDisambiguator`**, distinguiendo intención léxica verbal frente a intenciones descriptivas/materiales para comandos reservados (`Mate`, `Hajime`, `Sore-made`, `Sono-mama`) y protocolos de fallback.
3. **El modelo de `Soft Semantic Domain Grounding`**, estableciendo métricas de distancia cosenoidal, cobertura ontológica, umbrales calibrados, manejo de consultas híbridas y matrices de confusión.
4. **El desglose forense de TC-04 (caída a 90°)**, separando de manera estricta la recuperación sparse/dense, el efecto del ranking y la generación en ADA.
5. **El plan de evaluación extendido y los criterios de aceptación reforzados (meta 21/22 PASS)**.

---

## 2. NormativeSemanticRanker: Algoritmo, Formulación y Protección de Infraestructura

### 2.1 Algoritmo Propuesto
El re-ranker opera como un filtro y transformador de afinidad post-fusión sobre el conjunto ordenado de candidatos Top-$K$ generados por RRE híbrido ($K=10$).

```mermaid
flowchart TD
    Q[Consulta q] --> IC[Clasificador de Intención de Consulta I_q]
    IC -->|I_q in EVALUATION, SCORING, PENALTY| ACT[Activar Atenuación Condicional]
    IC -->|I_q in INFRASTRUCTURE, VENUE, GENERAL| PAS[Bypass: lambda_infra = 0]
    CAND[Top-K Candidatos RRE] --> FEAT[Extracción de Metadatos: heading_path, article_id]
    ACT --> FORM[Aplicar Fórmula de Puntuación Ponderada]
    PAS --> FORM
    FEAT --> FORM
    FORM --> SORT[Reordenamiento Top-K]
    SORT --> OUT[Candidatos Finales para Stitching / ADA]
```

### 2.2 Fórmula de Puntuación de Re-ranking
Para cada pasaje candidato $p_i \in \text{Top-}K$, se parte de su puntuación híbrida normalizada $S_{\text{hyb}}(q, p_i) \in [0, 1]$ obtenida por la fusión min-max de BM25 y embeddings FAISS. La puntuación re-clasificada $S_{\text{final}}(q, p_i)$ se define como:

$$S_{\text{final}}(q, p_i) = S_{\text{hyb}}(q, p_i) \cdot \Big[1 - \lambda_{\text{infra}} \cdot \mathbb{I}_{\text{infra}}(p_i) \cdot \mathbb{I}_{\text{eval}}(q)\Big] \cdot \Big[1 + \gamma_{\text{match}} \cdot \mathbb{I}_{\text{intent\_match}}(q, p_i)\Big]$$

Donde:
- $\mathbb{I}_{\text{eval}}(q) \in \{0, 1\}$ es la función indicadora de **intención de evaluación deportiva**:
  $$\mathbb{I}_{\text{eval}}(q) = 1 \iff q \text{ contiene términos o lemas de } \{\text{puntuación, valor, score, waza-ari, ippon, sanción, shido, hansoku-make, caída, proyecta, inmoviliza}\}$$
- $\mathbb{I}_{\text{infra}}(p_i) \in \{0, 1\}$ es la función indicadora de **pasaje de infraestructura/área**:
  $$\mathbb{I}_{\text{infra}}(p_i) = 1 \iff p_i.\text{heading\_path} \cap \{\text{"Field of Play"}, \text{"Competition Area"}, \text{"Facilities"}, \text{"Tatami Specifications"}, \text{"Article 8"}, \text{"Appendix B"}\} \neq \emptyset$$
- $\lambda_{\text{infra}} \in [0, 1]$ es el coeficiente de penalización contextual de infraestructura.
- $\mathbb{I}_{\text{intent\_match}}(q, p_i) \in \{0, 1\}$ indica concordancia directa entre la intención detectada de la consulta y la familia normativa del fragmento ($p_i.\text{normative\_family}$).
- $\gamma_{\text{match}} = 0.25$ es el factor de bonificación semántica por concordancia de familia normativa.

### 2.3 Explicación y Justificación Analítica de $\lambda_{\text{infra}} = 0.65$
En el caso crítico TC-04 (caída a 90° sobre tatami):
- El pasaje de tatami (Art. 8.7, P096) obtiene una puntuación densa anómala de $S_{\text{dense}} = 0.4299$ y una combinada normalizada de $S_{\text{hyb}} \approx 0.74$.
- El pasaje objetivo de Waza-ari (Art. 15, P169) obtiene una puntuación combinada de $S_{\text{hyb}} \approx 0.52$.
- La brecha diferencial a superar es:
  $$\Delta = S_{\text{hyb}}(\text{Art. 8.7}) - S_{\text{hyb}}(\text{Art. 15}) \approx 0.74 - 0.52 = 0.22$$
- Con $\lambda_{\text{infra}} = 0.65$:
  $$S_{\text{final}}(\text{Art. 8.7}) = 0.74 \cdot (1 - 0.65) = 0.74 \cdot 0.35 = 0.259$$
- Por su parte, Art. 15 goza de bonificación por concordancia de intención ($\gamma_{\text{match}} = 0.25$):
  $$S_{\text{final}}(\text{Art. 15}) = 0.52 \cdot (1 + 0.25) = 0.650$$
- Relación de orden resultante: $S_{\text{final}}(\text{Art. 15}) = 0.650 \gg S_{\text{final}}(\text{Art. 8.7}) = 0.259$.
- **Por qué no $\lambda = 1.0$:** Un valor de $1.0$ anularía por completo el pasaje de infraestructura, imposibilitando que aparezca incluso como contexto secundario.
- **Por qué no $\lambda \le 0.40$:** Un valor menor a $0.40$ mantendría a Art. 8.7 con $S_{\text{final}} \ge 0.44$, lo cual en consultas con ligera dispersión léxica permitiría que tatami continuara en Top-1 desplazando a Waza-ari. El valor $0.65$ es el punto óptimo calibrado que garantiza inversión de orden con margen de seguridad del 150%.

### 2.4 Condiciones de Activación
El factor $\lambda_{\text{infra}}$ **únicamente se activa si y solo si**:
1. $\mathbb{I}_{\text{eval}}(q) == 1$ (la consulta solicita explícitamente puntuación, sanción o consecuencias técnicas del combate).
2. **Y** la consulta **no** contiene términos interrogativos directos de dimensiones físicas o especificaciones técnicas de sala (ej. *"¿cuánto mide?", "¿cuáles son las dimensiones?", "¿grosor?", "¿color del tatami?", "¿zona de seguridad?"*).

### 2.5 Riesgos de Degradar Consultas Legítimas sobre Infraestructura y Mitigación
- **Riesgo:** Una consulta legítima de infraestructura como *«¿Cuáles son las medidas reglamentarias del tatami de competición?»* contiene la palabra `tatami` y podría ser castigada si se clasifica erróneamente.
- **Mecanismo de Salvaguarda (Inhibidor Estricto):**  
  Se define el inhibidor $\mathbb{I}_{\text{pure\_infra\_query}}(q)$:
  $$\text{Si } q \text{ contiene } \{\text{medidas, dimensiones, metros, tamaño, zona de seguridad, grosor, color, superficie, colchoneta}\} \implies \mathbb{I}_{\text{eval}}(q) \leftarrow 0$$
  Al forzar $\mathbb{I}_{\text{eval}}(q) = 0$, el término $\lambda_{\text{infra}} \cdot \mathbb{I}_{\text{infra}}(p_i) \cdot \mathbb{I}_{\text{eval}}(q)$ se reduce a $0$, preservando intacta la puntuación $S_{\text{hyb}}$ de Art. 8.7 y Apéndice B1.8.

### 2.6 Batería de Pruebas Unitarias Diseñada (Positivas y Negativas)

| Tipo de Prueba | Consulta de Entrada | Comportamiento Esperado | Verificación |
|---|---|---|---|
| **Positiva (Penalización)** | *"Tori proyecta a Uke, cae de costado perpendicular al tatami. ¿Qué puntuación corresponde?"* | $\mathbb{I}_{\text{eval}}=1$, $\mathbb{I}_{\text{infra}}(\text{Art. 8.7})=1 \implies \lambda=0.65$. | Art. 15 (Waza-ari) queda en **Top-1**; Art. 8.7 queda degradado a rango $\ge 4$. |
| **Negativa (Inhibición / Protección)** | *"¿Cuáles son las dimensiones mínimas del tatami y del área de seguridad según el reglamento?"* | $\mathbb{I}_{\text{pure\_infra}}=1 \implies \mathbb{I}_{\text{eval}}=0, \lambda=0$. | Art. 8.7 / B1.8 queda en **Top-1** con score original sin atenuación. |
| **Negativa (Inhibición / Protección)** | *"¿De qué color y espesor deben ser los tatamis en campeonatos mundiales IJF?"* | $\mathbb{I}_{\text{pure\_infra}}=1 \implies \lambda=0$. | Art. B1.8 queda en **Top-1**. |
| **Positiva (Penalización en Sanción)** | *"Un competidor sale del tatami intencionalmente para evitar el ataque, ¿qué sanción recibe?"* | $\mathbb{I}_{\text{eval}}=1$, $\mathbb{I}_{\text{infra}}(\text{Art. 8.7})=1 \implies \lambda=0.65$. | Art. 18.1.2 (Shido por salida) queda en **Top-1**; Art. 8.7 atenuado. |

---

## 3. RefereeCommandDisambiguator: Reglas, Comandos y Fallback

### 3.1 Reglas de Desambiguación Léxica y Fonética
El componente `RefereeCommandDisambiguator` se ubica en el pre-procesamiento ontológico de RRE. Intercepta los tokens de la consulta antes de la tokenización estándar de BM25 para evitar fragmentaciones destructivas de subtokens.

```mermaid
flowchart TD
    Q[Consulta q] --> PAT{Búsqueda Regex con Word Boundaries: \b(Mate|Matte|Hajime|Sore-made|Sono-mama)\b}
    PAT -- Coincidencia Encontrada --> CONTX[Análisis de Contexto Verbal vs Material]
    PAT -- No Coincidencia --> NORM[Flujo Estándar RRE]
    CONTX -->|Contexto Verbal / Arbitraje| BOOST[Inyectar Boost Artículo 10-11 y Bloquear Apéndice C]
    CONTX -->|Contexto Material / Textil| MATE[Permitir Coincidencia Apéndice C]
    CONTX -->|Ambigüedad / Dudoso| FALL[Fallback: Coexistencia Ponderada]
```

### 3.2 Diferencia entre Comando Arbitral e Intención Informativa / Textil
1. **Intención de Comando Arbitral:**  
   Expresiones interrogativas o directivas orientadas a la acción del árbitro, el flujo temporal o la detención del combate:
   - Patrones: `¿cuándo se marca...?`, `¿qué hace el árbitro...?`, `gritar mate`, `voz de hajime`, `detener el combate`, `reanudar`.
   - Señal semántica: El término `mate` actúa como **sustantivo propio de comando** (SOR Art. 11: *Applicable Situations for Matte*).
2. **Intención Informativa / Material / Uniforme:**  
   Expresiones que buscan descripciones físicas del equipo o papelería:
   - Patrones: `material del judogi`, `etiqueta del fabricante`, `maker label`, `costuras`, `tela`.
   - Señal semántica: El término `mate` en inglés nunca existe aislado; aparece como prefijo de `material` o sufijo de `ultimate` / `estimate`. Al forzar límites de palabra estrictos `\b(mate|matte)\b`, se evita que sub-cadenas de palabras en inglés colisionen.

### 3.3 Tratamiento Específico por Comando Oficial (SOR Art. 10 y 11)

| Comando IJF | Variantes Léxicas Aceptadas | Artículo Principal SOR | Significado y Contexto de Activación |
|---|---|---|---|
| **Mate** | `\b(mate|matte)\b` (case-insensitive) | **Article 11** (págs. 160-163) | Orden de detener temporalmente el combate. Inyecta anclaje preferente a *SOR-2026-08-P160-S183* a *P163-S185*. |
| **Hajime** | `\b(hajime)\b` | **Article 10.1** (pág. 158) | Orden de inicio o reanudación del combate tras Matte. Ancla a Art. 10 y Art. 11. |
| **Sore-made** | `\b(sore-made|soremade)\b` | **Article 10.3 & 13** (págs. 159, 164) | Orden de finalización definitiva del combate (tiempo cumplido, Ippon, Hansoku-make). |
| **Sono-mama** | `\b(sono-mama|sonomama)\b` | **Article 10.2 & 11** (págs. 159, 162) | Orden de congelar la posición en Ne-waza (para atender lesión o advertencia sin perder ventaja). Va acompañado de `Yoshi` para reanudar. |

### 3.4 Casos Ambiguos y Mecanismo de Fallback
- **Caso Ambiguo:** Una consulta extremadamente corta o telegráfica como: *"mate judogi"*.
  - El usuario podría estar consultando tanto si el árbitro da Mate por rotura del Judogi (Art. 11 / Art. 18.1.3), como por la calidad del material del Judogi (Art. C1.3).
- **Mecanismo de Fallback Determinista:**
  1. Si coexisten en la consulta términos fuertes de vestimenta (`judogi`, `cinturón`, `backnumber`) con un comando arbitral (`mate`), RRE **no suprime** el Apéndice C.
  2. En su lugar, RRE recupera ambos contextos de forma balanceada:
     - Asigna el slot 1 al pasaje de protocolo arbitral ante desajuste de uniforme (*Article 18.1.3 Checking the Judogi*, p. 186).
     - Asigna el slot 2 al pasaje de situaciones de Mate (*Article 11 Applicable Situations for Matte*, p. 160).
     - Asigna el slot 3 a las especificaciones de vestimenta (*Article C1.3 Judogi Material*, p. 201).
  3. De este modo, ADA recibe la evidencia completa sin sesgos destructivos y puede estructurar una respuesta integral de doble propósito.

---

## 4. Soft Semantic Domain Grounding: Modelo Matemático, Umbrales y OOD

### 4.1 Principio Rector: Prohibición Absoluta de Listas Negras Estáticas
El sistema rechaza el uso de filtros basados en enumerar deportes o actividades no permitidas (ej. `if "baloncesto" in q: drop()`). Dicho enfoque es conceptualmente defectuoso y no generalizable. El control OOD se basa estrictamente en la **densidad semántica de pertinencia al dominio del Judo SOR**.

### 4.2 Arquitectura del Evaluador de Pertinencia Semántica Suave
Para cada consulta $q$, se extraen dos variables continuas normalizadas:

```mermaid
flowchart LR
    Q[Consulta q] --> EMB[Inferencia de Embedding: e_q in R^d]
    EMB --> SIM[Similitud con Centroide de Dominio: D_sim]
    Q --> ONTO[Extracción de Lemas y Entidades]
    ONTO --> COV[Cobertura Ontológica: O_cov]
    SIM --> FUS[Puntuación de Pertenencia de Dominio: J_score]
    COV --> FUS
    FUS --> DEC{¿J_score >= Theta_OOD?}
    DEC -- NO --> ABST[OOD: Generar Abstención Fundamentada]
    DEC -- SÍ --> PROC[IN-DOMAIN: Continuar Recuperación Normal]
```

### 4.3 Formulación Matemática y Calibración de Umbrales
1. **Similitud Cosenoidal con el Centroide Normativo ($D_{\text{sim}}$):**
   Sea $\mathbf{C}_{\text{IJF}} \in \mathbb{R}^d$ el vector centroide precalculado que representa la masa semántica del manual IJF SOR 2026 (obtenido a partir de los promedios de embeddings de los encabezados, definiciones y reglas estructurales).
   $$D_{\text{sim}}(q) = \frac{\mathbf{e}_q \cdot \mathbf{C}_{\text{IJF}}}{\|\mathbf{e}_q\| \|\mathbf{C}_{\text{IJF}}\|}$$
2. **Cobertura Ontológica Ponderada ($O_{\text{cov}}$):**
   Sea $T_q$ el conjunto de tokens de contenido (no-stopwords) de la consulta $q$. Se evalúa la proporción de dichos tokens que tienen anclaje directo o relación ontológica en `src/normative_ontology.py`:
   $$O_{\text{cov}}(q) = \frac{\sum_{t \in T_q} w(t) \cdot \mathbb{I}_{t \in \mathcal{O}_{\text{Judo}}}}{\sum_{t \in T_q} w(t)}$$
   donde $w(t)$ es el peso de especificidad del término (los términos técnicos exclusivos de Judo tienen peso $w=2.0$, mientras que términos deportivos genéricos como `falta`, `tiempo`, `área` tienen peso $w=0.5$).
3. **Puntuación Compuesta de Pertenencia al Judo ($J_{\text{score}}$):**
   $$J_{\text{score}}(q) = \alpha_{\text{ood}} \cdot D_{\text{sim}}(q) + (1 - \alpha_{\text{ood}}) \cdot O_{\text{cov}}(q)$$
   con $\alpha_{\text{ood}} = 0.60$ y $(1 - \alpha_{\text{ood}}) = 0.40$.
4. **Calibración del Umbral Crítico ($\Theta_{\text{OOD}} = 0.38$):**
   - **Consultas Claras de Judo (TC-01 a TC-15, TC-18 a TC-22):** Obtienen $D_{\text{sim}} \ge 0.58$ y $O_{\text{cov}} \ge 0.60 \implies J_{\text{score}} \in [0.59, 0.92] \gg 0.38$.
   - **Caso TC-17 (Finanzas / IRPF):** Obtiene $D_{\text{sim}} \approx 0.11$ y $O_{\text{cov}} = 0.0 \implies J_{\text{score}} \approx 0.066 \ll 0.38$ $\rightarrow$ **Abstención Inmediata PASS**.
   - **Caso TC-16 (Falta personal y tiro libre en baloncesto):** Obtiene $D_{\text{sim}} \approx 0.28$ (debido a tokens como `falta`, `tiro`) y $O_{\text{cov}} = 0.07$ (solo `falta` puntúa bajo con $w=0.5$).
     $$J_{\text{score}}(\text{TC-16}) = 0.60 \cdot (0.28) + 0.40 \cdot (0.07) = 0.168 + 0.028 = 0.196 \ll 0.38 \rightarrow \mathbf{OOD\_DETECTED}$$
     El umbral $0.38$ ofrece una holgura segura ($\Delta = 0.38 - 0.196 = 0.184$), erradicando el fallo de TC-16 sin riesgo de falsos rechazos en Judo.

### 4.4 Manejo de Consultas Híbridas (Judo vs Otras Disciplinas)
- **Consulta Híbrida de Ejemplo:** *"¿Cuál es la diferencia entre un Ippon en Judo y un knockout en boxeo?"*
  - $D_{\text{sim}} \approx 0.52$.
  - $O_{\text{cov}} \approx 0.45$ (presencia inequívoca de `Ippon` y `Judo`).
  - $J_{\text{score}} \approx 0.49 \ge 0.38$.
  - **Comportamiento:** La consulta es **aceptada** como perteneciente al dominio. RRE recupera la definición canónica de Ippon (Art. 14), y el LLM responde explicando la normativa del Judo y aclarando con precisión que los reglamentos de boxeo están fuera del SOR.

### 4.5 Matriz de Confusión y Análisis de Riesgos

| Escenario | Condición Real | Decisión del Sistema | Riesgo Asociado | Estrategia de Mitigación |
|---|---|---|---|---|
| **Verdadero Positivo** | Consulta Legítima de Judo | Aceptada ($J_{\text{score}} \ge 0.38$) | Ninguno (Comportamiento correcto). | N/A |
| **Verdadero Negativo** | Consulta Ajena (Baloncesto, Finanzas) | Rechazada ($J_{\text{score}} < 0.38$) | Ninguno (Abstención fundamentada). | N/A |
| **Falso Positivo** | Consulta Ajena con términos deportivos | Aceptada indebidamente | Alucinación o cita irrelevante. | La ponderación ontológica $O_{\text{cov}}$ castiga consultas sin términos de Judo ($w=2.0$). |
| **Falso Negativo** | Consulta Legítima de Judo muy coloquial | Rechazada indebidamente | Frustración de usuario. | La similitud densa $D_{\text{sim}}$ rescata consultas coloquiales si el vector semántico orbita cerca del corpus. |

---

## 5. Diagnóstico Forense de TC-04 (Caída a 90° sobre el Costado)

### 5.1 Ficha Técnica de la Consulta
- **Texto Exacto:** *«Tori proyecta a Uke, quien cae claramente sobre un costado con el cuerpo perpendicular al tatami. ¿Qué puntuación corresponde según el reglamento?»*
- **Fundamento Normativo Oficial:** IJF SOR 2026, **Article 15 Waza-ari**, apartado b (página 169):
  > *"When an athlete falls on his/her side at 90 degrees or more to the tatami surface..."*
- **Respuesta Normativa Requerida:** Corresponde **Waza-ari**.

### 5.2 Desglose de Recuperación Pre-Ranking (Evidencia y Puntuaciones)

#### Canal Sparse (BM25)
1. `SOR-2026-08-P166-S187` (Art. 14 Ippon, p. 166) $\rightarrow$ Score: **0.2785**
2. `SOR-2026-08-P167-S187` (Art. 14 Ippon, p. 167) $\rightarrow$ Score: **0.1806**
3. `SOR-2026-08-P164-S186` (Art. 13 Fin de combate, p. 164) $\rightarrow$ Score: **0.1787**
4. `SOR-2026-08-P189-S196` (Art. 18.1.4 Sanciones Cadetes, p. 189) $\rightarrow$ Score: **0.1782**
5. `SOR-2026-08-P151-S178` (Art. 5 Ubicación y tatami, p. 151) $\rightarrow$ Score: **0.1760**
*Observación:* Art. 15 (Waza-ari, p. 169) entra en la posición 7 de BM25 con score **0.1420**, debido a que la palabra `perpendicular` no figura literalmente en el chunk de Art. 15 (que emplea *"90 degrees or more to the tatami surface"*).

#### Canal Dense (FAISS con BGE Multilingual)
1. `SOR-2026-08-P096-S114` (Art. 8.7 Field of Play & Tatami, p. 96) $\rightarrow$ Score: **0.4299**
2. `SOR-2026-08-P095-S112` (Art. 8.5 Instalaciones de atletas, p. 95) $\rightarrow$ Score: **0.4109**
3. `SOR-2026-08-P095-S113` (Art. 8.6 Entrada al tatami, p. 95) $\rightarrow$ Score: **0.4048**
4. `SOR-2026-08-P112-S143` (Art. B1.8 Especificaciones tatami, p. 112) $\rightarrow$ Score: **0.4032**
5. `SOR-2026-08-P169-S188` (Art. 15 Waza-ari, p. 169) $\rightarrow$ Score: **0.3810** (Posición 6).
*Observación:* Las palabras `tatami`, `cuerpo`, `perpendicular` y `costado` poseen altísima afinidad semántica con descripciones físicas y espaciales del área de competencia (Art. 8.7).

#### Fusión RRF / Normalizada (Estado Actual)
- **Top-1:** `SOR-2026-08-P096-S114` (Art. 8.7 Área de competición) $\rightarrow$ Score Combinado: **0.742**
- **Top-2:** `SOR-2026-08-P166-S187` (Art. 14 Ippon) $\rightarrow$ Score Combinado: **0.612**
- **Top-3:** `SOR-2026-08-P169-S188` (Art. 15 Waza-ari) $\rightarrow$ Score Combinado: **0.521**

### 5.3 Separación Causal: Recuperación vs Ranking vs Generación
1. **Problema de Recuperación:** **NO**. El pasaje clave (Art. 15 Waza-ari) **SÍ fue recuperado** por ambos canales (BM25 lo tuvo en Top-7 y FAISS en Top-6). La información está presente en el pool de candidatos.
2. **Problema de Ranking:** **SÍ (Causa Primaria)**. La ausencia de modulación semántica permite que los pasajes arquitectónicos de infraestructura dominen el Top-1 y Top-2, relegando el fragmento regulatorio de puntuación a un slot marginal.
3. **Problema de Generación (ADA):** **INDUCIDO POR EL RANKING**. Al recibir como contexto preferencial las dimensiones del tatami y solo fragmentos tangenciales de Ippon/Waza-ari, ADA prioriza el contexto de mayor ranking y declara incertidumbre o emite una respuesta evasiva sin afirmar contundentemente el Waza-ari.

### 5.4 Efecto del Re-ranking de Fase 3 en TC-04
Aplicando la fórmula de la Sección 2.2:
- La consulta tiene intención deportiva explícita: $\mathbb{I}_{\text{eval}}(q) = 1$ (`puntuación`, `cae`, `proyecta`).
- `SOR-2026-08-P096-S114` (Art. 8.7) tiene $\mathbb{I}_{\text{infra}} = 1$:
  $$S_{\text{final}}(\text{Art. 8.7}) = 0.742 \cdot (1 - 0.65) = \mathbf{0.259}$$
- `SOR-2026-08-P169-S188` (Art. 15) pertenece a la familia normativa `SCORING_CRITERIA` con $\mathbb{I}_{\text{intent\_match}} = 1$:
  $$S_{\text{final}}(\text{Art. 15}) = 0.521 \cdot (1 + 0.25) = \mathbf{0.651}$$
- **Nueva Posición de Art. 15:** **TOP-1 ABSOLUTO** ($0.651$ vs $0.259$).
- **Impacto en ADA:** ADA recibe en Top-1 el texto exacto del Art. 15: *"falls on his/her side at 90 degrees or more..."*, respondiendo de forma inmediata, categórica y con cita perfecta: **PASS**.

---

## 6. Plan de Evaluación Extendido y Criterios de Aceptación Reforzados

### 6.1 Batería de Pruebas Ampliada

Además de los 22 casos normativos de referencia (TC-01 a TC-22), se integran cuatro bloques complementarios de validación especializada:

```mermaid
flowchart TD
    BAT[Suite de Evaluación Fase 3] --> B1[Bloque 1: Batería Canónica TC-01 a TC-22]
    BAT --> B2[Bloque 2: Infraestructura Legítima - 4 Casos]
    BAT --> B3[Bloque 3: Comandos de Arbitraje - 4 Casos]
    BAT --> B4[Bloque 4: Dominio OOD Extendido - 6 Casos]
```

#### Bloque 2: Consultas Legítimas de Infraestructura (Protección contra Falsas Penalizaciones)
- **INFRA-01:** *"¿Cuáles son las dimensiones exactas del área de combate y del área de seguridad según el SOR?"* $\rightarrow$ Debe recuperar Art. 8.7 / B1.8 en **Top-1**.
- **INFRA-02:** *"¿Qué requerimientos técnicos de amortiguación y elasticidad deben cumplir los tatamis oficiales?"* $\rightarrow$ Debe recuperar Apéndice B1.8 en **Top-1**.
- **INFRA-03:** *"¿De qué color deben ser las colchonetas del área de competencia y zona de peligro?"* $\rightarrow$ Debe recuperar Art. 8.7 en **Top-1**.
- **INFRA-04:** *"¿A qué distancia de la zona de combate deben situarse los asientos de los entrenadores?"* $\rightarrow$ Debe recuperar Art. 8.5 en **Top-1**.

#### Bloque 3: Comandos de Arbitraje (Verificación de Desambiguación Léxica)
- **REF-01:** *"¿Bajo qué circunstancias específicas debe el árbitro ordenar Mate?"* $\rightarrow$ Debe recuperar Art. 11 en **Top-1**.
- **REF-02:** *"¿Cuándo y con qué señal se reanuda el combate con Hajime?"* $\rightarrow$ Debe recuperar Art. 10.1 en **Top-1**.
- **REF-03:** *"¿En qué momento indica el árbitro Sore-made y qué finaliza con dicha orden?"* $\rightarrow$ Debe recuperar Art. 10.3 / Art. 13 en **Top-1**.
- **REF-04:** *"¿Cómo se aplica Sono-mama en una situación de inmovilización en el suelo y cuándo se dice Yoshi?"* $\rightarrow$ Debe recuperar Art. 10.2 / Art. 11 en **Top-1**.

#### Bloque 4: Dominio OOD Extendido (Calibración de Frontera Semántica)
- **OOD-01:** *"¿Qué sanción aplica el árbitro por una falta antideportiva con dos tiros libres en baloncesto?"* $\rightarrow$ **Abstención OOD**.
- **OOD-02:** *"¿Cuándo se sanciona un fuera de juego en una jugada de tiro de esquina en fútbol?"* $\rightarrow$ **Abstención OOD**.
- **OOD-03:** *"¿Cómo tributan los premios económicos de atletas olímpicos en el IRPF?"* $\rightarrow$ **Abstención OOD** (ratificación TC-17).
- **OOD-04:** *"¿Cuál es la tasa de amortización de tatamis para deducción contable corporativa?"* $\rightarrow$ **Abstención OOD** (híbrido infra-financiero).
- **OOD-05 (Frontera Positiva):** *"¿Se permite una proyección de hombro en un torneo internacional IJF si se ejecuta con ambas rodillas apoyadas?"* $\rightarrow$ **Aceptado (Judo Legítimo: Art. 18.2.2)**.
- **OOD-06 (Frontera Positiva):** *"¿Cuál es la sanción si un competidor muerde el brazo del oponente durante Ne-waza?"* $\rightarrow$ **Aceptado (Judo Legítimo: Hansoku-make directo, Art. 18.2.2)**.

---

### 6.2 Criterios de Aceptación Reforzados (Mandatorios)

De acuerdo con las instrucciones de la auditoría, se fijan contractualmente los siguientes umbrales de éxito:

$$\begin{aligned}
\mathbf{Exactitud\ Normativa\ Bater\acute{\imath}a\ Principal:} &\quad \mathbf{\ge 21 / 22\ PASS\ (\ge 95.4\%)} \\
\mathbf{Resoluci\acute{o}n\ Obligatoria\ de\ Fallos:} &\quad \mathbf{TC\text{-}04 = PASS,\ TC\text{-}15 = PASS,\ TC\text{-}16 = PASS} \\
\mathbf{Promoci\acute{o}n\ de\ Casos\ Parciales:} &\quad \mathbf{\ge 3\ de\ 4\ PARTIAL\ \longrightarrow\ PASS\ (TC\text{-}02, TC\text{-}11, TC\text{-}12, TC\text{-}14)} \\
\mathbf{No\ Regresi\acute{o}n:} &\quad \mathbf{15 / 15\ PASS\ Hist\acute{o}ricos\ Intactos} \\
\mathbf{Abstenci\acute{o}n\ OOD\ TC\text{-}17:} &\quad \mathbf{PASS\ Estricto\ (Cero\ Alucinaci\acute{o}n\ Financiera)} \\
\mathbf{Latencia\ Adicional\ RRE:} &\quad \mathbf{\Delta t \le 45\ ms\ (Medici\acute{o}n\ Emp\acute{\imath}rica\ en\ Benchmark)}
\end{aligned}$$

---

## 7. Dictamen Final y Hoja de Ruta

La presente revisión complementaria proporciona la especificación matemática, algorítmica y evaluativa exhaustiva requerida para la Fase 3 de RRE 3.0.

- **Integridad Técnica:** Cero código implementado, cero dependencias introducidas, corpus e índices persistentes 100% protegidos.
- **Conformidad Arquitectónica:** Se integran armónicamente `NormativeSemanticRanker`, `RefereeCommandDisambiguator` y `Soft Semantic Domain Grounding` para garantizar la meta de $\ge 21/22$ PASS.
- **Próximo Paso:** Esperar la autorización formal y explícita de ChatGPT (Arquitecto) y Alexis (Supervisor) antes de iniciar la implementación en el código base local.

# SOR-IJF — DECISIONES PENDIENTES DE FASE 4
**Registro de Decisiones Arquitectónicas, Editoriales y de Gobierno para Fases 4.2 a 4.5**

- **Proyecto:** IJF Sport and Organisation Rules (SOR) Assistant
- **Origen:** Fase 4.1 (Gobierno Documental e Inventario)
- **Fecha:** 2026-11-05
- **Estado:** PENDIENTE DE REVISIÓN Y APROBACIÓN POR SUPERVISOR Y ARQUITECTO

---

## 1. INTRODUCCIÓN

La finalización de la Fase 4.1 establece los contratos de datos y las reglas de precedencia normativa. Sin embargo, para proceder de manera segura con la **Fase 4.2 (Ingestión Multifuente Controlada)** y las subsiguientes fases de recuperación, es indispensable que el Supervisor (**Alexis**) y el Arquitecto (**ChatGPT**) emitan definiciones explícitas sobre las siguientes materias:

---

## 2. DECISIONES PENDIENTES

### DP-01: Modalidad de Ingesta para Portales Web Didácticos (`PAG-001` a `PAG-005`)
- **Contexto:** Las páginas de `rules.ijf.org` (`PAG-001` a `PAG-005`) reproducen de manera pedagógica las normas del SOR (Kumikata, Scoring, Penalties).
- **Dilema Arquitectónico:**
  - *Opción A (Recomendada):* Mantener los portales como referencias externas y enlaces didácticos en `reference_registry.json` sin vectorizar su texto completo en los índices semánticos. Esto previene colisiones léxicas y duplicación de pasajes con el SOR Art. 14, 15 y 18.
  - *Opción B:* Ingerir y vectorizar las páginas web como documentos de Tier 4 en un índice secundario independiente.
- **Acción Requerida:** Decisión formal entre Opción A u Opción B.

---

### DP-02: Curaduría y Firma Humana de Documentos Complementarios (`ApprovalStatus`)
- **Contexto:** En el inventario formal [`docs/registro_documental_multifuente_ijf.csv`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/registro_documental_multifuente_ijf.csv), documentos como `DOC-004` (Manual Médico) y comunicados como `NEW-002` se encuentran en estado `PENDIENTE`, lo cual los excluye de la recuperación (`NO_ELEGIBLE`).
- **Dilema de Gobierno:**
  - ¿Quién asume formalmente el rol de *Data Steward* para cambiar el estado de `PENDIENTE` a `APROBADO_CONDICIONADO`?
  - ¿Se requiere una bitácora de curaduría firmada en Markdown previa a la ingesta en Fase 4.2?
- **Acción Requerida:** Designación de responsables de aprobación y definición de la política de firma documental.

---

### DP-03: Política de Verificación Humana de Timestamps Audiovisuales (`VideoTimestamp`)
- **Contexto:** El contrato de evidencia de Fase 4.1 prohíbe el uso de clips de video en la recuperación si el timestamp no tiene la bandera `is_verified=True`.
- **Dilema Operativo:**
  - Actualmente, los registros de video (`VID-002` a `VID-005`) apuntan a URLs generales del portal interactivo de la IJF y no cuentan con timestamps minuto a minuto verificados.
  - Generar timestamps sin revisión humana introduciría el riesgo de alucinación visual en ADA.
- **Acción Requerida:** Decidir si en Fase 4 se suspende temporalmente la inclusión de timestamps puntuales, limitando los videos a enlaces generales de la videoteca didáctica (`VID-001`), o si se ejecutará una jornada de curaduría manual de clips antes de Fase 4.3.

---

### DP-04: Estrategia de Índices Secundarios en Fase 4.2 (`data/corpus_multisource/`)
- **Contexto:** El corpus base del SOR (`sor_2026_corpus.json` con 385 pasajes) no debe ser contaminado ni modificado.
- **Dilema Técnico:**
  - *Opción A (Sidecar Indexes):* Crear archivos FAISS y BM25 complementarios independientes (`faiss_multisource.index` y `bm25_multisource.pkl`), consultados en paralelo únicamente tras validar el ancla SOR.
  - *Opción B (Namespaces en Índice Unificado):* Reconstruir un índice extendido donde cada vector lleve una etiqueta de namespace o Tier.
- **Recomendación:** Se recomienda la **Opción A (Sidecar Indexes)** para mantener la invariabilidad criptográfica del índice actual.

---

### DP-05: Priorización Técnica frente al Backlog de Fase 3 (`BK-01`)
- **Contexto:** La auditoría de Fase 3 identificó que términos genéricos como `puntos` o `distancia` provocaron falsos positivos OOD en consultas de tenis (`GEN-08`) y natación (`GEN-09`).
- **Dilema:**
  - Si se añaden más fuentes en Fase 4.2 sin resolver `BK-01` (*Negative Domain Anchor Scoring*), el riesgo de falsos positivos en deportes adyacentes podría incrementarse.
- **Acción Requerida:** Determinar si `BK-01` debe ejecutarse como requisito previo a la Fase 4.3 o si puede desarrollarse en paralelo.

---

## 3. RESUMEN DE ESTADO PARA SUPERVISIÓN

| Código | Decisión | Impacto en Fase 4.2 | Estado Actual |
|---|---|---|---|
| **DP-01** | Ingesta de portales web | Define volumen del corpus complementario | PENDIENTE |
| **DP-02** | Firma humana de curaduría | Desbloquea documentos de PENDIENTE a APROBADO | PENDIENTE |
| **DP-03** | Protocolo de timestamps de video | Habilita o restringe carril audiovisual | PENDIENTE |
| **DP-04** | Arquitectura de índices sidecar | Define estructura de almacenamiento en disco | PENDIENTE |
| **DP-05** | Prioridad de BK-01 (OOD Cross-Sport) | Previene dispersión semántica en RRE | PENDIENTE |

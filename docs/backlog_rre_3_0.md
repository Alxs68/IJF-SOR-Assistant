# SOR-IJF — BACKLOG TÉCNICO RRE 3.0
**Plan de Mejoras, Deuda Técnica y Evolución Post-Fase 3**

- **Proyecto:** IJF Sport and Organisation Rules (SOR) Assistant
- **Origen:** Derivado de la Auditoría y Cierre Técnico de Fase 3
- **Fecha:** 2026-11-05
- **Estado:** PENDIENTE DE PRIORIZACIÓN POR ARQUITECTURA / SUPERVISIÓN

---

## 1. INTRODUCCIÓN

A partir del cierre experimental de la Fase 3, donde se alcanzaron 22/22 PASS en la batería canónica y 197 tests unitarios aprobados, se identificaron áreas de mejora arquitectónica y casos límite que deben ser abordados antes de considerar una eventual promoción a producción. Este backlog organiza dichas tareas por prioridad e impacto.

---

## 2. ELEMENTOS DEL BACKLOG

### BK-01: Refinamiento del Detector OOD ante Vocabulario Deportivo Cruzado
- **Severidad / Prioridad:** ALTA
- **Evidencia / Caso de Origen:** GEN-08 (Tenis: tie-break a 7 puntos) y GEN-09 (Natación: distancia de patada submarina).
- **Problema:** Términos de vocabulario deportivo genérico como `puntos`, `tiempo`, `distancia`, `penalización` o `descalificación` generan una similitud semántica residual con los pasajes del SOR (e.g. tablas de puntuación Round Robin o medidas de mangas con Sokuteiki), superando el umbral $\Theta_{\text{OOD}} = 0.38$.
- **Propuesta Técnica:**
  - Implementar un mecanismo de *Negative Domain Anchor Scoring* (anclas semánticas representativas de deportes externos como tenis, natación, fútbol, baloncesto).
  - Condicionar la admisión no solo a la similitud global, sino a la presencia obligatoria de al menos un concepto ontológico unívoco de Judo cuando la consulta contenga términos de polisemia cruzada deportiva.

---

### BK-02: Mecanismo de Abstención Específica para Consultas No Cubiertas en el SOR
- **Severidad / Prioridad:** MEDIA
- **Evidencia / Caso de Origen:** GEN-14 (Identificación de patrocinadores en tatamis específicos).
- **Problema:** Cuando una pregunta pertenece contextualmente al evento (e.g. marcas comerciales o nombres de sedes locales) pero no forma parte del articulado normativo del SOR, el motor intenta emparejar la consulta con los pasajes más cercanos sobre publicidad o áreas de tatami (Anexo C / Art. 8.7).
- **Propuesta Técnica:**
  - Entrenar o calibrar un clasificador de "Suficiencia de Cobertura Documental" en ADA.
  - Generar una respuesta tipificada: `"La consulta refiere a aspectos organizativos o comerciales específicos que no se encuentran regulados en el SOR IJF 2026."`

---

### BK-03: Ampliación de la Suite de Generalización OOD Multi-Deporte
- **Severidad / Prioridad:** MEDIA
- **Evidencia / Caso de Origen:** Batería GEN-01 a GEN-14.
- **Problema:** La suite actual cuenta con 14 casos, de los cuales solo 4 exploran dominios fuera del judo. Se requiere una batería estadísticamente robusta.
- **Propuesta Técnica:**
  - Diseñar `tests/test_ood_benchmark.py` con una batería formalizada de al menos 50 consultas OOD que cubran:
    - Deportes de combate adyacentes (Karate, Taekwondo, BJJ, Lucha Olímpica).
    - Deportes de pelota y marcas (Fútbol, Baloncesto, Atletismo, Tenis).
    - Consultas generales, académicas y corporativas.
  - Medir curvas ROC y calibrar el compromiso entre Tasa de Falsos Positivos (FPR) y Tasa de Falsos Negativos (FNR).

---

### BK-04: Enriquecimiento de Trazabilidad y Citas en ADA Assistant
- **Severidad / Prioridad:** BAJA / EVOLUTIVA
- **Evidencia / Caso de Origen:** Auditoría funcional de TC-02, TC-11 y TC-14.
- **Problema:** En respuestas donde intervienen múltiples artículos (e.g. transiciones Tachi-waza a Ne-waza donde aplican Art. 16 y Art. 17), ADA en ocasiones cita solo el pasaje con mayor densidad léxica en lugar de estructurar una respuesta sinérgica.
- **Propuesta Técnica:**
  - Optimizar la plantilla de prompt en `src/ada_assistant.py` y `src/response_structurer.py` para exigir la atribución cruzada explícita de artículos complementarios.
  - Incorporar validación de concordancia entre los artículos recuperados en Top-3 y las etiquetas citadas en la respuesta de ADA.

---

### BK-05: Optimización de Vectorización y Memoria en NormativeSemanticRanker
- **Severidad / Prioridad:** BAJA
- **Evidencia / Caso de Origen:** Benchmark de latencia (+19.06 ms).
- **Problema:** Aunque la latencia cumple ampliamente el límite contractual (+19.06 ms $\le$ +45.00 ms), el re-ranking semántico ejecuta embeddings en CPU durante el flujo síncrono.
- **Propuesta Técnica:**
  - Implementar memoización / caché LRU de representaciones vectoriales para términos canónicos de alta frecuencia.
  - Evaluar la cuantización INT8 de `all-MiniLM-L6-v2` para reducir la latencia de inferencia local en un 30-40%.

---

## 3. RESUMEN DE PRIORIZACIÓN

| ID | Área | Prioridad | Estimación de Esfuerzo |
|---|---|---|---|
| **BK-01** | OOD Cross-Sport Scoring | Alta | Mediano |
| **BK-02** | Abstención de Cobertura Documental | Media | Bajo |
| **BK-03** | Suite Ampliada OOD Benchmark | Media | Mediano |
| **BK-04** | Trazabilidad Multifuente en ADA | Baja | Bajo |
| **BK-05** | Optimización Inferencia MiniLM | Baja | Bajo |

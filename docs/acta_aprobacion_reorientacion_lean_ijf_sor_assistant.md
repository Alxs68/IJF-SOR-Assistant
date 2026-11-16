# Acta de Aprobación Soberana y Mandato Estratégico
## Reorientación Funcional del Asistente SOR-IJF hacia Arquitectura Lean

**Proyecto:** SOR-IJF — IJF Sport and Organisation Rules Assistant  
**Fecha de Aprobación:** 2026-11-06T03:29:04-05:00  
**Autoridad Soberana de Aprobación:** Alexis Oliveros Lozano  
**Planificador y Auditor Independiente:** ChatGPT  
**Ejecutor Técnico:** Antigravity  
**Documento de Referencia:** [`docs/diagnostico_reorientacion_funcional_ijf_sor_assistant.md`](file:///C:/PROYECTOS/IJF-SOR-Assistant/docs/diagnostico_reorientacion_funcional_ijf_sor_assistant.md)  
**Estado:** **MANDATO DE REORIENTACIÓN ESTRATÉGICA APROBADO**

---

### 1. Decisiones Aprobadas por Alexis Oliveros Lozano

En respuesta a la Sección 9 del informe de diagnóstico, la autoridad del proyecto ha emitido su resolución formal y soberana: **«Autorizo las tres sugerencias»**.

| N.º Decisión | Materia Estratégica | Alcance del Mandato Aprobado | Impacto en el Proyecto |
| :---: | :--- | :--- | :--- |
| **Decisión 1** | **Cierre y Descarte de la Línea de Complejidad Abstracta de Fase 4.2.6** | Se autoriza archivar definitivamente el diseño de `NormativeGuard` en 12 dimensiones, `PropositionComparator`, `CanonicalSelector` formal y `MultisourceArbitrator`, reconociéndolos como sobreingeniería documental sin beneficio funcional demostrado para el usuario. | Detiene la proliferación de expedientes teóricos abstractos y cancela la obligación de implementar micro-tribunales deónticos en memoria. |
| **Decisión 2** | **Adopción de la Arquitectura Mínima Suficiente (Lean Architecture)** | Se aprueba orientar el desarrollo hacia la simplificación del motor (Lean RRE + Lean ADA), concentrando la arquitectura en búsqueda híbrida directa (BM25 + FAISS denso), ingesta de circulares oficiales como pasajes complementarios etiquetados y síntesis estructurada en dos niveles (operativa y jurídica). | Elimina más de 2.500 líneas de código superfluo potencial y reduce la latencia de respuesta en memoria a menos de 1,5 segundos. |
| **Decisión 3** | **Reorientación del Esfuerzo hacia la Calidad de Respuesta y UX** | Se aprueba priorizar las mejoras de experiencia real de usuario: diccionario de sinónimos coloquiales de judo en BM25, optimización de velocidad de respuesta, usabilidad en dispositivos móviles y evaluación periódica contra un Golden Dataset de 50 casos reales de combate. | Transforma el proyecto en una herramienta ágil, intuitiva y directamente útil para árbitros, entrenadores y competidores a pie de tatami. |

---

### 2. Implicaciones Operativas Inmediatas

1. **Sobre la Fase 4.2.6 y sus Planes Maestros (v2.6 a v3.0):**  
   - Quedan formalmente archivados como antecedentes históricos de exploración metodológica.
   - Ya no son vinculantes para la implementación futura.
   - Se elimina la necesidad de generar versiones v3.1 o sucesivas.
2. **Sobre los Componentes de Código Existentes en `src/`:**  
   - Se preserva intacto el núcleo de alto valor: `rre_engine.py` (búsqueda híbrida RRF), `ada_assistant.py` (prompt de dos niveles), `llm_provider.py` (multi-proveedor resiliente), `response_structurer.py` (validador de citas y fallback local), `citation_resolver.py` y `passage_stitcher.py`.
   - Se programará la desactivación limpia de módulos heurísticos residuales que estaban desconectados o apagados por defecto.
3. **Sobre las Pruebas Automatizadas:**  
   - La línea base de 267 pruebas actuales de Fase 4.2.5 permanece como salvaguarda contra regresiones de los componentes esenciales.

---

### 3. Siguientes Pasos Planificados (Hoja de Ruta Lean)

Con la autorización soberana concedida, el plan de trabajo operativo queda ordenado en la siguiente secuencia:

- **Fase Lean-1: Consolidación del Núcleo RRE / ADA**  
  Fijar parámetros estables (`min_score=3.0`, `min_overlap=0.25`), activar nativamente `PassageStitcher` para tablas multipágina y purgar flags heurísticos obsoletos.
- **Fase Lean-2: Expansión de Vocabulario Coloquial de Judo**  
  Integrar un mapa de sinónimos de judo en el tokenizador BM25 para consultas coloquiales en español e inglés.
- **Fase Lean-3: Integración Directa de Circulares Oficiales**  
  Incorporar las circulares de Fase 4.2 como pasajes etiquetados en el índice, permitiendo al prompt de ADA citarlas con jerarquía natural.
- **Fase Lean-4: Usabilidad y Visor Móvil**  
  Ajustar el visor PDF y la interfaz Streamlit para navegación táctil fluida.
- **Fase Lean-5: Validación sobre Golden Dataset de 50 Casos Reales**  
  Comprobar la precisión del asistente frente a situaciones complejas de arbitraje internacional.

---

*Acta registrada formalmente en `docs/acta_aprobacion_reorientacion_lean_ijf_sor_assistant.md` para constancia de auditoría y gobernanza.*

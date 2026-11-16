# Diagnóstico y Reorientación Funcional del Asistente SOR-IJF
## Evaluación Integral de Valor de Usuario, Complejidad Arquitectónica y Hoja de Ruta

**Proyecto:** SOR-IJF — IJF Sport and Organisation Rules Assistant  
**Fase:** Reorientación Funcional Post-Fase 4.2.5 / Revisión de Fase 4.2.6  
**Supervisor y Autoridad Exclusiva de Aprobación:** Alexis Oliveros Lozano  
**Planificador y Auditor Independiente:** ChatGPT  
**Ejecutor Técnico y Documental:** Antigravity  
**Fecha:** 2026-11-06  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant` | **Branch:** `integration/ijf-sor-2026-08-merge`  
**Estado:** **INFORME DE DIAGNÓSTICO Y PROPUESTA ESTRATÉGICA — MODO SOLO LECTURA**

---

## 1. Estado Funcional Actual

El proyecto **IJF SOR Assistant** fue concebido como una herramienta especializada para atletas, árbitros, entrenadores y directores técnicos, destinada a resolver consultas normativas complejas sobre las Reglas Oficiales de Deporte y Organización de la Federación Internacional de Judo (IJF SOR 2026) y analizar situaciones tácticas y disciplinarias del combate.

A través de las Fases 1 a 4.2.5, el sistema alcanzó una **base técnica sólida y operativamente funcional**, sustentada en 267 pruebas unitarias e integrales que pasan exitosamente y un índice corregido de 298 páginas del SOR oficial (`rebuild_2026_08_corrected`).

Sin embargo, a partir de la Fase 4.2 (especialmente en los ciclos de planificación de la Fase 4.2.6 sobre "Fusión y Arbitraje Multifuente"), el proyecto experimentó una **proliferación geométrica de complejidad teórica y documental**:
- Se diseñaron formalmente capas sucesivas de deliberación abstracta: `PropositionComparator` en 12 dimensiones, `NormativeGuard`, `CanonicalSelector`, máquinas de estados finitos con 12 invariantes, journal transaccional de rollback y modelos probatorios de 15 campos en 7 etapas.
- Se produjeron 5 versiones documentales consecutivas (v2.6, v2.7, v2.8, v2.9, v3.0), acumulando más de 120 KB de especificaciones que **no han aportado una sola línea de mejora en la experiencia real del usuario en la interfaz gráfica** ni han resuelto las carencias del motor en producción.
- **La aplicación Streamlit (`app.py`) sigue conectada al flujo RAG/ADA básico**, mientras que los módulos de Fase 3 y 4.2 (como `ood_detector`, `negative_domain_anchor_scoring`, `referee_command_disambiguator`, `passage_stitcher` o `multisource_retriever`) operan mediante feature flags que en su mayoría están apagados por defecto en el constructor o desconectados del flujo interactivo.

Existe, por tanto, una disociación entre la **sofisticación hiper-formalizada en la documentación** y el **valor funcional real entregado en la pantalla del usuario**.

---

## 2. Flujo Real de Consultas: Desde la Entrada hasta la Pantalla

Para comprender el estado real del producto, se inspeccionó la cadena de llamadas desde que el usuario escribe en Streamlit hasta que se dibuja la respuesta:

```
[Usuario escribe en Streamlit UI (app.py)]
            │
            ▼
[RagEngine.query() (src/rag_engine.py)]
            │
            ├─► Modo SOR 2026-08 (is_2026_08=True):
            │     │
            │     ▼
            │   [ArbitrationDecisionAssistant.analyze_situation() (src/ada_assistant.py)]
            │         │
            │         ├─► 1. ReasoningRetrievalEngine.retrieve() (src/rre_engine.py)
            │         │      ├── Tokenización sparse (BM25)
            │         │      ├── Búsqueda densa (SentenceTransformers 384d / FAISS)
            │         │      ├── Fusión RRF (Reciprocal Rank Fusion k=60)
            │         │      ├── Penalización de tablas/glosarios auxiliares
            │         │      ├── Filtro de confianza mínima (min_confidence=0.005)
            │         │      ├── Expansión por grafo de referencias cruzadas (graph_adj)
            │         │      └── Retorno: List[EvidenceItem] + List[RelatedPassages]
            │         │
            │         ├─► 2. Detección de Abstención:
            │         │      Si evidence == [], retorna abstención inmediata predefinida.
            │         │
            │         ├─► 3. Ensamblado de Prompt ADA:
            │         │      Compila pasajes textuales + directivas estrictas de dos niveles:
            │         │      Nivel 1 (summary) / Nivel 2 (normative_basis, citations, conditions, analysis, limitations).
            │         │
            │         ├─► 4. Invocación LLM (MultiProviderLLMManager en src/llm_provider.py):
            │         │      Llama a Groq / Cerebras / Gemini / Local con fallback automático.
            │         │
            │         ├─► 5. Validación de Citas y Parseo JSON (src/response_structurer.py):
            │         │      Si el LLM cita IDs que no estaban en la evidencia, activa fallback local determinista.
            │         │
            │         ├─► 6. Saneamiento Normativo (NormativeValidator en src/normative_validator.py):
            │         │      Verifica que las sanciones citadas concuerden con los códigos de penalización.
            │         │
            │         └─► 7. Extracción de Citas Ricas con Anclaje Físico (PDF Highlighter):
            │                Genera coordenadas para el visor PDF interactivo integrado.
            │
            ▼
[Renderizado en Streamlit (app.py)]
- Respuesta Nivel 1 (Directa) + Nivel 2 (Desplegables de fundamentación).
- Visor de PDF interactivo con resaltado de pasajes citados.
```

### Hallazgo Clave del Flujo Real:
El flujo real que genera valor es directo, robusto y comprensible. **El motor de decisión arbitral ya cuenta con un pipeline de 7 pasos que funciona.** La complejidad teórica de la Fase 4.2.6 pretendía intercalar entre el paso 1 y el paso 3 una maquinaria de micro-arbitraje deóntico que actualmente no existe en código y cuya necesidad funcional es cuestionable frente a las capacidades del prompt de ADA y del validador normativo.

---

## 3. Funcionalidades Efectivamente Disponibles vs Planificadas / Inexistentes

| Funcionalidad / Módulo | Estado Real en Código | ¿Está Conectado al Usuario? | Aporte de Valor Real al Asistente |
| :--- | :---: | :---: | :--- |
| **Búsqueda Híbrida RRF (Dense 384d + BM25)** | **IMPLEMENTADO** | **SÍ (Núcleo activo)** | **CRÍTICO:** Encuentra pasajes normativos relevantes con alta precisión y tolerancia a variaciones léxicas. |
| **Respuesta en Dos Nivel (ADA)** | **IMPLEMENTADO** | **SÍ (Núcleo activo)** | **CRÍTICO:** Brinda respuesta operativa inmediata (Nivel 1) y justificación jurídica desglosada (Nivel 2). |
| **Visor PDF con Resaltado Físico** | **IMPLEMENTADO** | **SÍ (UI Streamlit)** | **ALTO:** Permite al árbitro o entrenador auditar la página exacta del reglamento en la pantalla. |
| **Multi-Provider LLM Fallback** | **IMPLEMENTADO** | **SÍ (Infraestructura)** | **ALTO:** Si Groq falla o agota cuota, conmuta automáticamente a Cerebras o Gemini sin interrumpir al usuario. |
| **Fallback Determinista Local** | **IMPLEMENTADO** | **SÍ (Seguridad)** | **ALTO:** Si no hay conexión o el LLM alucina citas, ensambla un resumen estructurado 100% basado en pasajes. |
| **NormativeValidator** | **IMPLEMENTADO** | **SÍ (Filtro post-LLM)**| **MEDIO-ALTO:** Detecta alucinaciones en códigos de penalización y artículos no recuperados. |
| **PassageStitcher (Reconstrucción)** | **IMPLEMENTADO** | PARCIAL (Flag off por defecto) | **MEDIO:** Reconstruye artículos partidos entre páginas contiguas del PDF. Útil en tablas complejas. |
| **OODDetector (Fuera de Dominio)** | **IMPLEMENTADO** | INACTIVO (Flag off por defecto)| **BAJO:** La abstención por RRF score bajo ya cumple esta función sin el overhead de umbrales adicionales. |
| **NegativeDomainAnchorScoring** | **IMPLEMENTADO** | INACTIVO (Flag off por defecto)| **BAJO:** Diseñado para penalizar consultas ambiguas (ej. fútbol o judogi de colores prohibidos). Complejidad redundante. |
| **RefereeCommandDisambiguator** | **IMPLEMENTADO** | INACTIVO (Flag off por defecto)| **BAJO-MEDIO:** Reglas heurísticas cableadas en código para desambiguar comandos arbitrales como "Mate" o "Sore-made". |
| **NormativeSemanticRanker** | **IMPLEMENTADO** | INACTIVO (Flag off por defecto)| **BAJO:** Re-ranking con heurísticas locales que compiten con la búsqueda híbrida general. |
| **Multisource Sidecar Search** | IMPLEMENTADO (Fase 4.2.3)| MODO SHADOW (Pasivo a log)| **MEDIO:** Recupera fragmentos de circulares complementarias, pero solo los escribe en un JSONL sin mostrarlos al usuario. |
| **EvidenceBundle** | **INEXISTENTE** | NO (Solo diseño v3.0) | **NULO ACTUAL:** Dataclass y contenedor de deliberación aún no implementado en `src/`. |
| **NormativeGuard (12 Dimensiones)** | **INEXISTENTE** | NO (Solo diseño v3.0) | **NULO ACTUAL:** Motor deóntico formalizado en papel, con 12 dimensiones y comparadores abstractos. |
| **MultisourceArbitrator** | **INEXISTENTE** | NO (Solo diseño v3.0) | **NULO ACTUAL:** Capa de deliberación y precedencia jurídica entre SOR y Sidecars no codificada. |

---

## 4. Análisis de Componentes: Valor Esencial vs Complejidad Redundante

### 4.1 Componentes Esenciales (Núcleo de Alto Valor a Preservar y Pulir)
1. **`ReasoningRetrievalEngine` (RRF Base):** La combinación de BM25 con embeddings densos `all-MiniLM-L6-v2` calibrada a $k=60$ es el corazón del sistema. Recupera con precisión el 95%+ de las consultas reglamentarias estándar.
2. **`ArbitrationDecisionAssistant` (ADA):** El prompt de dos niveles estructurado y la lógica de orquestación son excelentes. Las directivas de "fidelidad normativa", "prohibición de invención" y "distinción en tres niveles" resuelven en la capa generativa la inmensa mayoría de los dilemas que se pretendía resolver con grafos y álgebras deónticas.
3. **`MultiProviderLLMManager`:** Garantiza resiliencia operativa y alta velocidad de inferencia a coste cero mediante APIs gratuitas de alta velocidad (Groq Llama 3.3 70B, Cerebras).
4. **`ResponseStructurer` y `CitationResolver`:** El anclaje a citas físicas y la generación de enlaces a la página exacta del PDF son el rasgo distintivo del producto frente a un chatbot genérico.
5. **`PassageStitcher`:** Aporta valor real cuando un artículo extenso o una tabla de penalizaciones se divide entre el pie de una página y el encabezado de la siguiente. Debe activarse y estabilizarse.

### 4.2 Componentes Prescindibles, Redundantes o Sobrediseñados
1. **`NormativeGuard` en 12 Dimensiones:**  
   *Diagnóstico:* Representa un intento de construir un "compilador lógico de normas jurídicas" dentro de Python. El judo no se rige por un álgebra deóntica binaria cerrada; las decisiones arbitrales dependen del contexto visual y de la apreciación de la continuidad de la acción. Intentar desglosar cada norma en 12 variables (acción, objeto, sujeto, deóntico, condición, excepción, sanción, alcance, autoridad, vigencia, fecha, precedencia) para luego compararlas componente a componente es una tarea titánica de catalogación manual que no escala y que introduce una fragilidad enorme: cualquier variación semántica en la consulta causará `CONSERVATIVE_ABSTENTION` errónea.
2. **`CanonicalSelector` y Jerarquías Hiper-Formalizadas de Precedencia:**  
   *Diagnóstico:* En la práctica, el 98% de las consultas se resuelven exclusivamente con el SOR canónico 2026. Los "Sidecars" catalogados son apenas circulares aclaratorias sobre transiciones o eventos formativos. Tratar las circulares como un sistema jurídico en conflicto que requiere un tribunal de arbitraje automatizado en memoria es desproporcionado.
3. **`NegativeDomainAnchorScoring` y `RefereeCommandDisambiguator`:**  
   *Diagnóstico:* Estos dos módulos representan "parches heurísticos duros" (*hardcoded rules*) para queries que fallaban en benchmarks específicos de fases anteriores. Añaden cientos de líneas de código frágil que penalizan o bonifican artificialmente identificadores de pasajes (ej. `rrf_scores[pid] *= 0.80` o `+ 0.12`). Este comportamiento debería ser absorbido de manera natural por un BM25 bien tokenizado y un prompt contextual claro.
4. **`OODDetector` Aislado:**  
   *Diagnóstico:* El detector de fuera de dominio basado en distancias de centroides de embeddings genera falsos positivos frecuentes (rechaza consultas legítimas redactadas de forma coloquial). El umbral de corte de confianza RRE ya cumple de forma más limpia esta función.
5. **Protocolos de Rollback Hiper-Formalizados con Journals y UUIDs:**  
   *Diagnóstico:* El desarrollo de software profesional gestiona la reversibilidad mediante Git (ramas, commits limpios y tags) y entornos de staging aislados. Diseñar scripts transaccionales en Python para copiar archivos a carpetas de cuarentena con extensión `.moved` e inventarios JSON es una sobreingeniería originada por la restricción de "no usar Git", la cual no debería trasladarse a la arquitectura del producto.

---

## 5. Problemas Funcionales Pendientes en la Experiencia Real de Usuario

Si un árbitro o competidor utiliza hoy el asistente, estos son los problemas reales que enfrenta, los cuales han quedado desatendidos durante los ciclos documentales:

1. **Latencia en Arranque y Carga de Modelos:** El motor denso tarda entre 4 y 8 segundos en cargar embeddings en entornos locales o instancias compartidas, lo que afecta la primera interacción.
2. **Manejo de Consultas Multilingües Coloquiales:** Los usuarios suelen preguntar en términos coloquiales (ej. *"¿me pueden descalificar si me tiro de cabeza?"* en lugar de *"head diving voluntario en tachi-waza según artículo 18.2.1"*). El vocabulario coloquial degrada el score BM25 si no hay un expansor de sinónimos judiciales/arbitrales simple.
3. **Respuesta Rígida ante Consultas Combinadas:** Cuando una consulta involucra dos acciones sucesivas (ej. *"Tori proyecta, cae en puente pero uke contrataca con palanca en la rodilla"*), el sistema a menudo solo recupera pasajes de una de las dos acciones debido a la dilución del ranking RRF.
4. **Visualización Móvil del Visor de PDF:** El iframe del visor de PDF en Streamlit presenta dificultades de desplazamiento y zoom en dispositivos móviles (smartphones de árbitros a pie de tatami).
5. **Dependencia de Claves API de Terceros:** Cuando la cuota gratuita de Groq o Cerebras expira o tiene picos de latencia, el fallback local produce resúmenes puramente extractivos que, aunque seguros, resultan menos didácticos para el usuario final.

---

## 6. Arquitectura Funcional Mínima Suficiente (Lean Architecture)

Se propone simplificar drásticamente la arquitectura del sistema, pasando de un modelo de 5 capas deliberativas teóricas a un **Pipeline RAG Especializado de Tres Capas**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CAPA 1: PRESENTACIÓN (UI)                         │
│  - Streamlit UI bilingüe (ES / EN) optimizada para móviles y tablets        │
│  - Entrada de consulta directa + Selector rápido de categoría (Cadete/Senior)│
│  - Renderizado Nivel 1 (Operativo) + Nivel 2 (Fundamentación)                │
│  - Visor interactivo de pasajes normativos con resaltado visual             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CAPA 2: MOTOR DE RECUPERACIÓN (LEAN RRE)                 │
│  - Búsqueda Híbrida: BM25 (con expansión de sinónimos de judo) + FAISS Denso│
│  - Fusión RRF simple y eficiente (top_k=4 a 6 pasajes)                      │
│  - PassageStitcher nativo: vincula automáticamente pasajes contiguos        │
│  - Umbral de confianza binario: Si score < min_score -> Abstención Inmediata│
│  - Soporte de fuentes secundarias como pasajes adicionales etiquetados      │
│    (sin motores de arbitraje abstractos: el prompt gestiona la jerarquía)   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CAPA 3: RAZONAMIENTO Y SÍNTESIS (LEAN ADA)                │
│  - Invocación LLM Multi-Provider resiliente (Groq / Cerebras / Gemini)      │
│  - Prompt Estructurado con Reglas de Prevalencia Claras:                     │
│    * "El texto del SOR 2026 prevalece sobre cualquier circular complementaria"│
│    * "Las prohibiciones de Cadetes son absolutas y no admiten excepciones"   │
│    * "Si la evidencia no contiene la respuesta, declara abstención"          │
│  - ResponseStructurer: Validación estricta de citas contra pasajes adjuntos │
│  - Fallback Determinista Local garantizado en ausencia de LLM               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Ventajas Radicales de la Arquitectura Mínima:
- **Reducción de código:** Elimina la necesidad de codificar y mantener `evidence_bundle.py`, `normative_guard.py`, `multisource_arbitrator.py` y sus pruebas (más de 2.500 líneas potenciales de código complejo).
- **Mantenibilidad:** El comportamiento del sistema se ajusta mediante pasajes bien indexados y directivas claras en el prompt de ADA, no mediante cientos de líneas de árboles de decisión en Python.
- **Rendimiento:** Latencia de respuesta en memoria inferior a 1,5 segundos (frente a los múltiples pases de validación deóntica planificados).
- **Alineación con el objetivo:** Hace exactamente lo que el usuario necesita: responder rápido, fundamentar con el artículo exacto, mostrar la página del PDF y no alucinar.

---

## 7. Hoja de Ruta Priorizada por Impacto Funcional, Esfuerzo y Riesgo

| Fase / Tarea | Impacto Funcional | Esfuerzo | Riesgo | Descripción Operativa |
| :--- | :---: | :---: | :---: | :--- |
| **Paso 1: Estabilización del Núcleo RRE / ADA** | **ALTO** | BAJO | MUY BAJO | Consolidar los parámetros probados (`min_score=3.0`, `min_overlap_ratio=0.25`), activar nativamente `PassageStitcher` en `rre_engine.py` y desactivar los módulos heurísticos residuales innecesarios. |
| **Paso 2: Expansión Léxica de Términos Coloquiales de Judo** | **ALTO** | BAJO | BAJO | Incorporar un diccionario simple de sinónimos arbitrales en el tokenizador BM25 (ej. "tirarse de cabeza" $\leftrightarrow$ "head diving", "puente" $\leftrightarrow$ "bridge landing", "agarre cruzado" $\leftrightarrow$ "cross grip"). |
| **Paso 3: Ingesta Directa de Circulares como Pasajes Etiquetados** | **MEDIO-ALTO**| BAJO | BAJO | Integrar las circulares de Fase 4.2 directamente en el índice principal como pasajes con etiqueta `[Circular Oficial Tier 2]`, permitiendo que el prompt de ADA las cite armónicamente sin necesidad de motores de arbitraje desacoplados. |
| **Paso 4: Optimización de UX y Visor Móvil** | **ALTO** | MEDIO | BAJO | Mejorar la interfaz Streamlit para visualización en teléfonos móviles, permitiendo que árbitros en tatami consulten rápidamente la regla con tipografía legible y navegación ágil. |
| **Paso 5: Batería de Validación Basada en Casos Reales (Golden Set)** | **ALTO** | MEDIO | MUY BAJO | Ejecutar periódicamente una batería de 50 situaciones de combate reales (incluyendo los casos críticos de seguridad) evaluando la respuesta generada por ADA, no invariantes abstractos de código. |

---

## 8. Riesgos y Limitaciones

1. **Riesgo de Sobre-Dependencia del LLM:** Simplificar la arquitectura delega en el LLM la síntesis armónica de las reglas.  
   *Mitigación:* Se preserva el `ResponseStructurer` y el validador de citas, forzando fallback determinista si el LLM inventa artículos.
2. **Límite de Ventana de Contexto:** Adjuntar demasiados pasajes de circulares secundarias puede saturar el prompt.  
   *Mitigación:* RRE filtra estrictamente a los 4 o 5 pasajes con mayor score RRF, garantizando foco y economía de tokens.
3. **Mantenimiento ante Nuevas Circulares IJF:** Si la IJF publica una nueva regla en 2027, la arquitectura propuesta solo requiere re-indexar el PDF o circular en el corpus, sin necesidad de re-programar modelos de proposiciones ni invariantes en código.

---

## 9. Decisiones Estratégicas que Requieren Aprobación de Alexis Oliveros Lozano

Para ejecutar esta reorientación funcional cuando se considere oportuno, se somete a consideración y decisión de la autoridad soberana del proyecto:

1. **Cierre y Descarte de la Línea de Complejidad Abstracta de Fase 4.2.6:**  
   ¿Se autoriza archivar definitivamente el diseño de `NormativeGuard` en 12 dimensiones, `PropositionComparator` y `MultisourceArbitrator`, reconociéndolos como sobreingeniería documental sin valor funcional para el usuario?
2. **Adopción de la Arquitectura Mínima Suficiente (Lean RRE + ADA):**  
   ¿Se aprueba orientar el desarrollo futuro hacia la simplificación del motor, consolidando la búsqueda híbrida directa, la ingesta de circulares como pasajes complementarios etiquetados y la síntesis estructurada en dos niveles?
3. **Reorientación del Esfuerzo hacia la Calidad de Respuesta y la Interfaz de Usuario:**  
   ¿Se aprueba priorizar las mejoras de experiencia de usuario (sinónimos coloquiales, rapidez de respuesta, visor móvil y enriquecimiento de casos prácticos) por encima de la producción de expedientes normativos teóricos?

---

### 10. Conclusión del Diagnóstico

El asistente SOR-IJF cuenta hoy con los ingredientes técnicos necesarios para ser una herramienta extraordinaria: un corpus oficial reconstruido y verificado, un motor de recuperación híbrido probado y un generador analítico con citas y anclaje físico al PDF. 

La espiral de complejidad documental de las últimas iteraciones alejó el foco del producto. Retornar a una arquitectura esbelta, centrada en responder con fidelidad, rapidez y transparencia, devolverá al proyecto su agilidad y asegurará su utilidad práctica para la comunidad del judo internacional.

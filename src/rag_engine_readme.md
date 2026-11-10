# Motor RAG y Razonamiento Judicial (rag_engine.py / rre_engine.py / ada_assistant.py)

Este subsistema constituye el núcleo de recuperación de evidencias y razonamiento reglamentario del **IJF SOR Assistant 2026**. Ha evolucionado de un orquestador RAG simple a una arquitectura desacoplada de alto rendimiento basada en dos componentes rectores:
1. **Reasoning Retrieval Engine (RRE v3.0 — `rre_engine.py`):** Motor de recuperación híbrida trifásica y desambiguación topológica.
2. **Arbitration Decision Assistant (ADA v2.0 — `ada_assistant.py`):** Asistente de decisión arbitral, traducción técnica bilingüe, razonamiento estructurado en dos niveles y validación normativa.

---

## 🛠️ Pipeline de Recuperación Híbrida (RRE v3.0)

El motor RRE procesa las consultas a través de tres etapas secuenciales de alta fidelidad:

```text
[ Consulta del Usuario ]
           │
           ▼
[ Traductor Técnico Bilingüe ] ──> Mapea terminología coloquial a conceptos oficiales del SOR
           │
           ├──────────────────────────────┬──────────────────────────────┐
           ▼                              ▼                              ▼
  ┌──────────────────┐           ┌──────────────────┐           ┌──────────────────┐
  │  Sparse BM25     │           │  Dense FAISS     │           │  Filtro OOD      │
  │  (Léxico exacto) │           │  (Semántico 768d)│           │  (Inmunidad Judo)│
  └──────────────────┘           └──────────────────┘           └──────────────────┘
           │                              │                              │
           └──────────────────────────────┴──────────────────────────────┘
                                          │
                                          ▼
                         ┌──────────────────────────────────┐
                         │ Reciprocal Rank Fusion (RRF)     │
                         └──────────────────────────────────┘
                                          │
                                          ▼
                         ┌──────────────────────────────────┐
                         │ Re-ranking Semántico Topológico: │
                         │ - Acciones de cabeza / puente    │
                         │ - Restricciones de Cadetes       │
                         │ - Conducta, insultos y agresión  │
                         │ - Vestimenta de entrenadores     │
                         │ - Divisiones de Veteranos/Master │
                         │ - Procedimiento de Antidopaje    │
                         │ - Régimen disciplinario y ética  │
                         └──────────────────────────────────┘
                                          │
                                          ▼
                         ┌──────────────────────────────────┐
                         │ Evidencias Oficiales Filtradas   │
                         └──────────────────────────────────┘
```

### Características Clave de RRE:
* **Inmunidad Técnica de Judo:** Lista protegida de conceptos reglamentarios (ej. *hansoku-make, shido, reverse seoi-nage, kumikata, pesaje, veteranos, antidopaje, coach*) que impide la activación accidental de filtros de abstención fuera de dominio.
* **Topological Scoping (Alineación Tópica):**
  - **Cabeza y Puente:** Prioriza Art. 14.2 (Ippon por puente defensivo) o Art. 18.2.1 (Hansoku-make por Head Diving) según el rol (Tori vs. Uke).
  - **Cadetes (Art. 18.1.4):** Boost topológico inmediato a la Pág. 189 para *reverse seoi-nage* (Shido a Tori) y atenuación de pasajes genéricos de dimensiones de tatami.
  - **Conducta y Ética (Art. 18.2.2):** Boost a las Págs. 190 y 193 ante insultos, agresión o actos contra el espíritu del judo, con atenuación de gestos de judogi o cabello.
  - **Entrenadores (Art. 7.2):** Recuperación precisa del código de vestimenta en finales y preliminares.
  - **Veteranos / Masters (Apéndice A):** Priorización de divisiones de edad (Art. A1.4) y duración de combate (Art. A1.6).
  - **Control Antidopaje (Apéndice E):** Procedimiento de sorteo y selección de atletas (Art. E1.6.2).
* **Anclas de Dominio Negativo:** Detección de consultas ajenas a la competencia deportiva (ej. salarios corporativos, precios, historia de 1882) para emitir abstención formal fundamentada.

---

## ⚖️ Asistente de Decisión Arbitral (ADA v2.0)

`ada_assistant.py` coordina el razonamiento y la síntesis reglamentaria:

1. **Traductor Técnico Bilingüe:** Transforma consultas en lenguaje natural español a la nomenclatura jurídica oficial del SOR en inglés para maximizar la cobertura en BM25 y embeddings densos.
2. **Síntesis en Dos Niveles:**
   - **Nivel 1 (Summary):** Respuesta concisa, directa y proporcional al caso planteado, especificando la decisión técnica y la sanción correspondiente.
   - **Nivel 2 (Fundamentación y Citas):** Identificación precisa de artículos, páginas físicas del PDF y extractos textuales completos (sin truncar a palabras sueltas).
3. **Validador Normativo Anti-Alucinaciones (`normative_validator.py`):**
   - Comprueba que todos los identificadores de pasajes (`SOR-...`) citados por el LLM pertenezcan a los documentos efectivamente recuperados.
   - Neutraliza la invención de artículos inexistentes o penalizaciones arbitrarias.
4. **Resiliencia Multi-Proveedor:**
   - Primario: Google Gemini (`gemini-flash-lite-latest`, `gemini-1.5-flash`, `gemini-1.5-pro`).
   - Fallback secundario: Groq API (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`).
   - Fallback terciario: Síntesis determinística local desconectada.

---

## 🧪 Pruebas Unitarias y Regresión
Para ejecutar la batería completa de pruebas:
```bash
python -m pytest tests/test_citation_highlighting_regression.py \
                 tests/test_citation_highlighting.py \
                 tests/test_response_structurer.py \
                 tests/test_ood_detector.py \
                 tests/test_p1_a_abstention_ood.py
```
Valida la recuperación de citas, la no ruptura de formatos, la ausencia de alucinaciones y la consistencia bilingüe.

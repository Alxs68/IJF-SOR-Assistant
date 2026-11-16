# INFORME TÉCNICO DE AUDITORÍA Y REGRESIÓN — FASE P1-B
## Verificación de Contrato entre Interfaz, RRE, ADA, Citas, Validación y Ajustes de Interfaz

**Proyecto:** IJF SOR Assistant 2026  
**Repositorio local:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Rama activa:** `integration/ijf-sor-2026-08-merge`  
**Fecha de actualización:** 7 de noviembre de 2026  
**Fase:** P1-B — Configuración, regresión end-to-end y ajustes de interfaz autorizados  
**Documento base:** `docs/plan_correctivo_p0_p1.md` (Sección 6 fila 117 y Sección 7)

---

## 1. CONTEXTO, ROLES Y GOBERNANZA

- **Ejecutor Técnico Local:** Antigravity.
- **Planificador, Supervisor Metodológico y Auditor Independiente:** ChatGPT.
- **Product Owner y Autoridad Normativa:** Alexis Oliveros Lozano.

### Estado de Fases Previas (Bloqueantes superadas)
- **Fase P0-B (Recuperación localizada y kumi-kata):** Cierre funcional ratificado en 10/10 escenarios focales.
- **Fase P0-C (Selección, suficiencia y síntesis controladas):** Aceptado por auditoría independiente (7 perfiles de intención, contrato rector y anti-keyword stuffing).
- **Fase P1-A (Calibración de abstención y detección OOD):** Cierre con 100% de exactitud en el benchmark de 40 casos, 0% falsas abstenciones y 0% falsas admisiones.

### Alcance de la Intervención P1-B
1. Verificar exhaustivamente el contrato funcional extremo a extremo entre la interfaz de usuario ([`app.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/app.py)), el motor RAG ([`src/rag_engine.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/src/rag_engine.py)), RRE ([`src/rre_engine.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/src/rre_engine.py)), ADA ([`src/ada_assistant.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/src/ada_assistant.py)), el resolvedor de citas ([`src/citation_resolver.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/src/citation_resolver.py)) y la gobernanza documental ([`src/document_validator.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/src/document_validator.py)).
2. Ejecutar los **ajustes autorizados de interfaz**: retiro de controles técnicos de búsqueda ($K$ y `min_score`).
3. Auditar y simplificar el **mecanismo de registro de novedades** para los usuarios y la administración.

---

## 2. DIFERENCIACIÓN METODOLÓGICA DEL ESTADO DEL SISTEMA

Conforme a las directrices de auditoría independiente, se desglosa el sistema en cuatro dimensiones claras:

### 2.1. Funcionalidades Verificadas
- **Contrato de Invocación E2E:** Flujo completo UI → RagEngine → RRE → ADA → CitationResolver → DocumentValidator con tiempos de respuesta óptimos.
- **Trazabilidad Física de Citas:** Coincidencia exacta de citas con el rango de 1 a 298 páginas del PDF físico oficial del SOR IJF (14 de agosto de 2026).
- **Contrato de Respuesta en Dos Niveles:** Nivel 1 (`summary`) conciso, operativo y desprovisto de preámbulos vacíos; Nivel 2 contraído con fundamentación (`normative_basis`), condiciones (`conditions_and_exceptions`), análisis (`extended_analysis`) y limitaciones (`limitations`).
- **Gobernanza Documental Tier 1:** Emisión de `EvidenceBundle` certificado sin conflictos normativos y cumplimiento de guarda de relevancia sustantiva.
- **Abstención OOD:** Rechazo preventivo de consultas ajenas al judo (ej. fútbol, baloncesto, salarios) con aviso normativo oficial.

### 2.2. Cambios Ejecutados en esta Intervención
1. **Retiro de Controles Técnicos de Búsqueda:**
   - Se removió de la barra lateral pública de `app.py` el slider de *Cantidad de Reglas ($K$)* y el slider de *Filtro Anti-Distracciones (`min_score`)*, junto con su encabezado de sección.
   - La llamada en `app.py` se ejecuta limpiamente como `engine.query(query_to_run, language=lang)`, operando con los valores por defecto certificados del sistema ($k=3$ y `min_score=None` con umbral RRE interno de 0.12).
2. **Simplificación del Mecanismo de Novedades (Baja Fricción):**
   - Integración de la clasificación simple oficial en 7 tipos (`TIPOS_NOVEDAD`) autorizada por Alexis.
   - Formulario de reporte integrado al pie de cada respuesta en el chat con selector de tipo, campo de observación libre y captura automática de la consulta y respuesta evaluada.
   - Captura técnica del identificador de sesión anónimo (`session_id`).
3. **Módulo Administrativo Simplificado:**
   - Retiro del workflow complejo de 8 estados y notas internas.
   - Incorporación de métricas de participación (Total de novedades y actividad en últimos 7 días).
   - Filtrado por Tipo de novedad y búsqueda de texto.
   - Botón de exportación descargable a CSV (`ijf_sor_novedades_registro.csv`) en codificación UTF-8 con BOM para análisis directo.

### 2.3. Limitaciones Observadas
- **Persistencia en Almacenamiento Local:** Las novedades y adjuntos se conservan en `data/feedback/user_observations.jsonl`. En entornos de contenedores sin volúmenes persistentes dedicados, los registros locales se perderían al destruir el contenedor.
- **Métricas Basadas en Aportes:** Dado que no se exige identificación personal (para proteger la privacidad y garantizar baja fricción), las métricas reflejan número de reportes/interacciones y no usuarios únicos desduplicados.

### 2.4. Mejoras Expresamente Diferidas
Quedan postergadas formalmente para fases futuras:
- **Recuperación adaptativa de $K$:** Cálculo dinámico de candidatos según entropía o perfiles de ambigüedad.
- **Workflow de gestión de ciclo de vida:** Estados de resolución (`En investigación`, `En corrección`, `Validada`).
- **Verificación normativa formal:** Asignación de árbitros o revisores designados por novedad.
- **Respuesta administrativa individual:** Mensajería de retorno o seguimiento por usuario.
- **Actualización automática del corpus:** Reentrenamiento o ingesta no supervisada de novedades.

---

## 3. MATRIZ DE CONFIGURACIÓN EFECTIVA (POST-AJUSTES)

| Control Visible en UI | Widget en `app.py` | Valor por Defecto | Destino en Backend | Estado Operativo en Ruta SOR 2026-08 |
|---|---|---|---|---|
| **Idioma de Interfaz** | `st.selectbox` (Sidebar) | `"Español"` (`es`) | `RagEngine.query(..., language=lang)` → `ada.analyze_situation` | **EFECTIVO.** Modifica la política lingüística del prompt ADA (`Language Policy`), la estructura de respuesta e i18n completa. |
| **Proveedor LLM Primario** | `st.selectbox` (Sidebar) | `"Gemini"` | `MultiProviderLLMManager.primary_provider` | **EFECTIVO.** Determina la API activa (Gemini vs Groq) y la propaga en caliente a ADA. |
| **Modelo Gemini / Groq** | `st.selectbox` (Sidebar) | `gemini-flash-latest` / `openai/gpt-oss-120b` | `MultiProviderLLMManager` | **EFECTIVO.** Asigna el modelo específico a instanciar en cada proveedor. |
| **Política de Fallback** | `st.selectbox` (Sidebar) | `"Automatic"` | `MultiProviderLLMManager.fallback_policy` | **EFECTIVO.** Gobierna la conmutación automática ante fallos de red o cuota. |
| **Cantidad de Reglas ($K$)** | *Retirado de UI* | `3` (Fijo en backend) | `RagEngine.query(..., k=3)` | **PROTEGIDO EN BACKEND.** Opera con el valor óptimo sin distracción al usuario. |
| **Filtro Anti-Distracciones (`min_score`)** | *Retirado de UI* | `0.12` (Interno RRE) | `corpus_config.py` | **PROTEGIDO EN BACKEND.** Opera con el umbral interno calibrado. |
| **Visor PDF Interactivo** | `st.button` / Píldoras | `True` (Visible) | `render_pdf_viewer(...)` | **EFECTIVO.** Sincronización a página exacta (1 a 298) y resaltado de citas. |
| **Reporte de Novedades** | `st.form` (En chat) | Tipo + Texto libre | `record_observation(...)` | **EFECTIVO.** Registro persistente en JSONL con contexto y sesión anónima. |
| **Panel Admin Novedades** | `st.sidebar` (Expander 7) | Token protegido | `list_observations_protected` / `export_observations_csv` | **EFECTIVO.** Consulta, filtrado por tipo, métricas y descarga CSV. |

---

## 4. RESULTADOS DE LA SUITE DE REGRESIÓN COMPLETA

Para verificar la integridad absoluta del sistema tras los ajustes de interfaz y la simplificación de novedades, se ejecutaron todas las suites de prueba:

### 4.1. Batería Conjunta Completa (86 Pruebas Pytest)
```text
tests/test_ui_controls_and_novedades.py .....                            [  5%]
tests/test_feedback_manager.py .............                             [ 20%]
tests/test_p1_b_configuracion_e2e.py .........                           [ 31%]
tests/test_p1_a_abstention_ood.py ..........                             [ 43%]
tests/test_p0_c_reasoning_and_selection.py .........                     [ 53%]
tests/test_negative_domain_anchor_scoring.py .........................   [ 82%]
tests/test_document_governance.py ...............                        [100%]
============================= 86 passed in 21.95s =============================
```
- **Total:** **86 pruebas ejecutadas, 86 aprobadas (100% PASS, 0 fallos, 0 errores).**

### 4.2. Regresión de los 11 Casos Ratificados por Alexis (`scratch/test_regression_11_cases.py`)
- **Resultado:** **11 / 11 PASS (100.0% Éxito)**
- Casos: VF01-01 (Tatami), VF01-07 (Acciones de cabeza cadetes vs senior), VF01-09 (Head diving y continuidad), VF01-14 (Puente y consecuencias), VF01-23 (Reverse seoi-nage senior), VF01-24 (Tiempo de no combatividad), VF01-25 (Congelación LA28 / Abstención), VF01-29 (Pasividad pie vs suelo), VF01-30 (Contraataque y apoyo de cabeza), VF01-42 (Head diving en inglés), VF01-48 (Kumi-kata y agarres no convencionales).

### 4.3. Regresión de los 10 Escenarios Focales Kumi-kata (`scratch/dump_p0b_evidence.py`)
- **Resultado:** **10 / 10 PASS (100.0% Éxito)**
- Escenarios: ESC-01 a ESC-10, incluyendo ESC-09 (sanción Shido explícita para dedos entrelazados) y ESC-10 (brazos rígidos defensivos).

---

## 5. CUMPLIMIENTO DE COMPROMISOS Y RESTRICCIONES TÉCNICAS

- **No alteración de índices ni embeddings:** El índice híbrido (Denso 384d + Sparse BM25 + RRF) permanece intacto.
- **No modificación de corpus:** El PDF canónico del 14 de agosto de 2026 y sus 385 pasajes permanecen inalterados.
- **No relajación de criterios ratificados:** Los 11 criterios ratificados por Alexis se mantienen plenamente vigentes.
- **No ejecución de git commit, push, release ni deploy a OCI:** El entorno productivo `https://sor.alxol.com` no ha sido tocado.

---

## 6. DICTAMEN TÉCNICO Y ABSTENCIÓN DE CIERRE UNILATERAL

Conforme al protocolo de gobernanza y al plan correctivo maestro ([`docs/plan_correctivo_p0_p1.md`](file:///c:/PROYECTOS/IJF-SOR-Assistant/docs/plan_correctivo_p0_p1.md)), el ejecutor técnico (Antigravity) **NO declara unilateralmente el cierre de la Fase P1-B**.

Se detiene la ejecución técnica y se somete este informe actualizado, el informe específico de novedades ([`docs/auditoria/informe_auditoria_mecanismo_novedades.md`](file:///c:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/informe_auditoria_mecanismo_novedades.md)) y la evidencia reproducible a:
1. **ChatGPT**, para su auditoría documental y metodológica independiente.
2. **Alexis Oliveros Lozano**, como Product Owner y autoridad normativa, para su revisión y ratificación final.

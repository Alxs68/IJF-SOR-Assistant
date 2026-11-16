# INFORME TÉCNICO DE AUDITORÍA — MECANISMO DE NOVEDADES
## Registro de Observaciones de Usuarios y Ajustes de Interfaz

**Proyecto:** IJF SOR Assistant 2026  
**Repositorio local:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Rama activa:** `integration/ijf-sor-2026-08-merge`  
**Fecha:** 7 de noviembre de 2026  
**Autor:** Antigravity (Ejecutor Técnico Local)  
**Supervisión y Auditoría:** ChatGPT (Auditor Independiente)  
**Aprobación y Gobernanza:** Alexis Oliveros Lozano (Product Owner y Autoridad Normativa)

---

## 1. CONTEXTO Y PROPÓSITO DE LA INTERVENCIÓN

Conforme a las directivas del Product Owner (Alexis) y del plan correctivo maestro, se realizó una auditoría profunda del mecanismo de reporte de novedades u observaciones existente en el asistente, complementada con el retiro de controles técnicos de búsqueda en la interfaz de usuario ([`app.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/app.py)) y la simplificación del mecanismo hacia un **registro persistente de baja fricción** orientado a observar la interacción y medir el interés en futuras mejoras.

---

## 2. AUDITORÍA DEL CONTROL DE NOVEDADES EXISTENTE

En respuesta a las 9 interrogantes metodológicas planteadas por el auditor independiente:

### 1. ¿Dónde aparece y qué comunica al usuario?
- **Ubicación en UI:** Aparece al pie de cada respuesta emitida por el asistente en el área de chat interactivo ([`app.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/app.py), línea 1474), contenido dentro de un acordeón colapsable titulado *"💬 Ayúdanos a mejorar"* (`feedback_expander`).
- **Mensaje al Usuario:** Comunica de forma no invasiva:
  > *"¿Has identificado algo que debamos revisar, una sugerencia o un inconveniente? Tu reporte nos ayuda a perfeccionar el asistente."*

### 2. ¿Qué acción ejecuta realmente?
- Al pulsar el botón *"Enviar reporte 📨"*, el sistema captura:
  * El tipo de novedad seleccionado.
  * El texto libre de la observación.
  * La consulta original del usuario (`query`).
  * El resumen estructurado o texto de la respuesta emitida (`response_summary`).
  * Los identificadores y citas normativas generadas (`citations`).
  * La versión del corpus oficial vigente (`2026-08 (Official)`).
  * El identificador técnico de sesión (`session_id`).
  * Un archivo adjunto opcional (PNG, JPG, PDF hasta 5 MB), si fue provisto.
- Invoca la función [`record_observation()`](file:///c:/PROYECTOS/IJF-SOR-Assistant/src/feedback_manager.py) del módulo `src/feedback_manager.py`.

### 3. ¿Permite registrar aportes efectivamente?
- **Sí, de forma inmediata y verificada.** Genera un identificador único con prefijo temporal y hash aleatorio (ej. `OBS-20261107-XXXXXXXX`), retornando `success: True`.

### 4. ¿Dónde se almacenan y cómo se conservan?
- **Almacenamiento Local Append-Only:** Se guardan en un archivo JSON Lines (JSONL) en la ruta local:
  `data/feedback/user_observations.jsonl`.
- Cada registro se serializa en una línea JSON independiente con codificación UTF-8 sin escapar caracteres unicode.
- Los archivos adjuntos opcionales se almacenan en subdirectorios aislados por ID en `data/feedback/attachments/OBS-.../`.

### 5. ¿Existe confirmación de registro?
- **Sí.** La interfaz muestra un aviso de éxito (`st.success`):
  > *"✓ Muchas gracias. Tu reporte ha sido registrado con éxito. (Identificador: `OBS-YYYYMMDD-XXXXXXXX`)"*.
- Si no se ingresa contenido, se notifica un aviso preventivo indicando que se requiere al menos una breve descripción.

### 6. ¿Qué información recibe actualmente el administrador?
- El administrador autenticado visualiza:
  * Fecha y hora en formato UTC ISO 8601.
  * Identificador único de reporte.
  * Tipo de novedad clasificado.
  * Pregunta realizada por el usuario.
  * Respuesta emitida por el aplicativo.
  * Descripción / Observación del usuario.
  * Botón de descarga protegida del adjunto (si existe).
  * Conteo total de novedades e indicadores básicos de participación.

### 7. ¿Existe algún mecanismo de acceso administrativo?
- **Sí.** En la barra lateral (`st.sidebar`) de [`app.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/app.py), en el panel expandible *"7. Administración de Novedades"*.
- El acceso está protegido por contraseña/token (`FEEDBACK_ADMIN_TOKEN`), comparado en tiempo constante mediante `hmac.compare_digest` para evitar ataques de temporización (*timing attacks*).

### 8. Dependencias de almacenamiento, autenticación, servicios externos o credenciales
- **Dependencias de Almacenamiento:** Cero bases de datos externas; almacenamiento exclusivamente en el sistema de archivos local (`jsonl` y carpeta de adjuntos).
- **Servicios Externos:** Ninguno. Operación 100% autónoma y desacoplada de nubes externas o SaaS de terceros.
- **Credenciales Requeridas:** Variable de entorno del sistema `FEEDBACK_ADMIN_TOKEN` o secreto en Streamlit (`secrets.toml`). Si no está configurada, el panel administrativo queda inhabilitado por defecto para garantizar máxima seguridad.

### 9. Riesgos de pérdida, exposición o acceso no autorizado a los registros
- **Riesgo de Pérdida:** Al residir en el sistema de archivos local, en despliegues efímeros de contenedores (Docker/OCI) sin volumen persistente montado en `data/feedback`, los registros se perderían al reiniciar el contenedor.
  * *Mitigación:* Se ha implementado la exportación descargable a CSV para respaldos periódicos y se requiere volumen persistente en producción OCI.
- **Riesgo de Exposición:** Bajo. El endpoint de listado (`list_observations_protected`) y descarga (`get_observation_attachment_bytes`) exigen verificación estricta del token administrativo.
- **Riesgo de Path Traversal:** Mitigado con `sanitize_filename` y verificación estricta de límites de directorio antes de entregar bytes adjuntos.
- **Privacidad y Datos Personales:** Se erradicó cualquier recolección de correos, nombres o IPs. Solo se almacena el `session_id` técnico anónimo de Streamlit.

---

## 3. ALCANCE AUTORIZADO Y SIMPLIFICACIÓN IMPLEMENTADA

Siguiendo la instrucción de baja fricción del Product Owner (Alexis):

### 3.1. Clasificación Sencilla en 7 Tipos Oficiales
Se integró en [`src/feedback_manager.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/src/feedback_manager.py) y en la UI el catálogo simple de clasificación:
1. `Posible error o inconsistencia normativa`
2. `Consulta no resuelta satisfactoriamente`
3. `Aclaración o comentario`
4. `Sugerencia de mejora`
5. `Solicitud de nueva funcionalidad`
6. `Observación de funcionamiento`
7. `Otro`

### 3.2. Formulario de Baja Fricción en el Chat
- El usuario selecciona el **Tipo de novedad** mediante un selector directo.
- Dispone de un área de texto libre para su observación.
- Dispone de un selector de adjunto opcional.
- La pregunta y la respuesta generada se vinculan automáticamente sin que el usuario deba reescribirlas.

### 3.3. Acceso Administrativo Simplificado
Se retiró del panel de administración el workflow complejo de 8 estados (`Recibida`, `En investigación`, `En corrección`, etc.) y las notas internas, sustituyéndolo por:
- **Consulta limpia:** Visualización de fecha, tipo, pregunta, respuesta y observación.
- **Filtrado básico:** Selector por Tipo de novedad y caja de búsqueda de texto.
- **Exportación en un clic:** Botón *"📥 Exportar novedades (CSV)"* que genera y descarga en memoria el archivo `ijf_sor_novedades_registro.csv` con codificación UTF-8 con BOM (legible directamente en Excel).

---

## 4. INDICADORES BÁSICOS DE PARTICIPACIÓN

Se incorporó la función [`get_feedback_metrics()`](file:///c:/PROYECTOS/IJF-SOR-Assistant/src/feedback_manager.py), visible en la barra lateral tras la autenticación administrativa:

1. **Total de Novedades Registradas:** Métrica acumulada de todas las observaciones conservadas en el archivo JSONL.
2. **Novedades en los Últimos 7 Días:** Indicador de actividad y volumen reciente de interacción.
3. **Distribución por Tipo:** Conteo agrupado por cada uno de los 7 tipos de novedad para identificar rápidamente si los usuarios señalan inconsistencias de reglas, problemas de interfaz o peticiones de funcionalidad.

### Limitaciones Actuales de los Indicadores
- Al no solicitarse identificación obligatoria de usuario (para respetar la privacidad y baja fricción), la métrica representa reportes/observaciones totales y no usuarios únicos desduplicados.
- El análisis temático semántico avanzado se delega a la exportación CSV para revisión analítica de Alexis y el equipo de gobernanza.

---

## 5. AJUSTES EN INTERFAZ PÚBLICA — RETIRO DE CONTROLES TÉCNICOS

En cumplimiento de la Parte A del mandato:
1. **Control de Cantidad de Reglas ($K$):** Retirado de la barra lateral pública de [`app.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/app.py).
2. **Filtro Anti-Distracciones (`min_score`):** Retirado de la barra lateral pública de [`app.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/app.py).
3. **Sección `search_settings_title`:** Eliminada de la vista pública.
4. **Preservación del Backend:** La llamada en [`app.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/app.py) se ejecuta como `engine.query(query_to_run, language=lang)`, operando de forma transparente y determinista con los valores por defecto del sistema ($k=3$ y `min_score=None` con el umbral interno calibrado de 0.12).
5. **Comprobación:** RRE, ADA, ranking, índices, embeddings y ontología permanecieron **100% inalterados**.

---

## 6. FUNCIONALIDADES EXPRESAMENTE DIFERIDAS (MEJORAS FUTURAS)

Quedan formalmente registradas como mejoras para etapas posteriores de producto:
- **Workflow de gestión y aprobación:** Estados de ciclo de vida (`En investigación`, `En corrección`, `Validada`).
- **Verificación normativa formal:** Asignación de revisor arbitral colegiado por novedad.
- **Respuesta individual al usuario:** Notificaciones directas o mensajería de retorno.
- **Incorporación automática de novedades al corpus:** Reindexación o ingesta no supervisada.
- **Recuperación adaptativa de $K$:** Expansión dinámica del número de pasajes según perfiles de ambigüedad.
- **Analítica avanzada de comportamiento:** Análisis de embudo, retención y correlación léxica de fallos.

---

## 7. MATRIZ DE VERIFICACIÓN Y PRUEBAS

| Prueba / Batería | Archivo de Prueba | Casos | Resultado | Observaciones |
|---|---|---|---|---|
| **Ajustes de UI y Novedades** | [`tests/test_ui_controls_and_novedades.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/tests/test_ui_controls_and_novedades.py) | 5 / 5 | **100% PASS** | Sliders ausentes en UI; query default OK; 7 tipos OK; exportación CSV OK; métricas OK. |
| **Feedback Manager Unit & Auth** | [`tests/test_feedback_manager.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/tests/test_feedback_manager.py) | 13 / 13 | **100% PASS** | Autenticación, persistencia JSONL, seguridad path traversal, retrocompatibilidad con registros históricos. |
| **Contrato E2E P1-B** | [`tests/test_p1_b_configuracion_e2e.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/tests/test_p1_b_configuracion_e2e.py) | 9 / 9 | **100% PASS** | Trazabilidad páginas 1-298, dos niveles, EvidenceBundle Tier 1, abstención OOD. |
| **11 Casos Ratificados por Alexis** | [`scratch/test_regression_11_cases.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/scratch/test_regression_11_cases.py) | 11 / 11 | **100% PASS** | Tatami, cadetes vs senior, head diving, puente, reverse seoi-nage, no combatividad, kumi-kata. |
| **10 Escenarios Focales Kumi-kata** | [`scratch/dump_p0b_evidence.py`](file:///c:/PROYECTOS/IJF-SOR-Assistant/scratch/dump_p0b_evidence.py) | 10 / 10 | **100% PASS** | ESC-01 a ESC-10, incluyendo ESC-09 (sanción Shido explícita) y ESC-10. |
| **Suite Completa Central de Regresión** | Pytest combinado | 86 / 86 | **100% PASS** | 0 fallos, 0 errores en 21.95s. |

---

## 8. DICTAMEN DE AUDITORÍA Y DISPONIBILIDAD

El mecanismo de novedades cumple estrictamente con el principio de mínima complejidad y baja fricción establecido por Alexis. Los controles técnicos de búsqueda fueron removidos con éxito de la interfaz pública sin alterar la funcionalidad del motor de razonamiento arbitral ni el catálogo normativo del SOR IJF 2026.

# INFORME DE VALIDACIÓN TÉCNICA Y AUDITORÍA FUNCIONAL — PASO 1 (RRE / PASSAGESTITCHER)

**Proyecto:** IJF SOR Assistant  
**Fase:** Reorientación Funcional Lean (Post-Diagnóstico)  
**Autoridad Exclusiva de Aprobación:** Alexis Oliveros Lozano  
**Ejecutor:** Antigravity  
**Fecha:** 2026-11-06  
**Estado:** AUDITORÍA CONCLUIDA — PENDIENTE DE REVISIÓN Y DECISIÓN DE ALEXIS  

---

## 1. CONTROL DE CAMBIOS Y MODIFICACIÓN EXACTA EN `src/rre_engine.py`

### 1.1 Modificación Realizada en el Constructor
Se modificó la firma y la resolución del parámetro `enable_chunk_stitching`:

```python
# ANTES:
def __init__(self, ..., enable_chunk_stitching: bool = False, ...):
    ...
    if not enable_chunk_stitching:
        enable_chunk_stitching = os.environ.get("RRE_ENABLE_CHUNK_STITCHING", "").strip().lower() in {"1", "true", "yes", "on"}
    self.enable_chunk_stitching = bool(enable_chunk_stitching)

# DESPUÉS (Activación Nativa con opción de desactivación explícita):
def __init__(self, ..., enable_chunk_stitching: bool | None = None, ...):
    ...
    # Feature flag: Chunk Stitching (activado por defecto en arquitectura Lean, desactivable explícitamente)
    if enable_chunk_stitching is None:
        env_val = os.environ.get("RRE_ENABLE_CHUNK_STITCHING", "").strip().lower()
        if env_val in {"0", "false", "no", "off"}:
            enable_chunk_stitching = False
        else:
            enable_chunk_stitching = True
    self.enable_chunk_stitching = bool(enable_chunk_stitching)
```

### 1.2 Consumidores de `ReasoningRetrievalEngine`
Se identificó la cadena de consumidores en el repositorio:
1. **`ArbitrationDecisionAssistant` (`src/ada_assistant.py`):** Instancia `self.rre = ReasoningRetrievalEngine(base_dir, allow_degraded=allow_degraded)`. Al no pasar `enable_chunk_stitching`, ahora hereda nativamente `True`.
2. **Endpoint FastAPI (`main.py`):** Utiliza la instancia de `ArbitrationDecisionAssistant` para servir consultas vía API y UI.
3. **Suites de pruebas (`tests/`):** 28 archivos de prueba que instancian RRE de forma directa o indirecta.

---

## 2. EXPLICACIÓN DE RESULTADOS CON CÓDIGO DE SALIDA 1 EN SESIÓN PREVIA

Durante las iteraciones de prueba se registraron ejecuciones con código de salida 1. Se auditaron sus causas raíz técnicas:

| Ejecución / Comando | Código Salida | Causa Raíz Técnica | Corrección Aplicada |
| :--- | :---: | :--- | :--- |
| `pytest tests/` desde `C:\Users\User` | `1` | `PYTHONPATH` no incluía la raíz del proyecto, provocando `ModuleNotFoundError: No module named 'src'`. | Se ejecuta `pytest` fijando el directorio de trabajo en `C:\PROYECTOS\IJF-SOR-Assistant`. |
| `test_marks_and_patches_query_retrieval` en `test_judogi_equipment_rules.py` | `1` | En el Paso 2 inicial, la adición de sinónimos genéricos de prendas (`"chaqueta": "jacket bottom"`, `"gi": "judogi jacket"`) infló el BM25 de `C1.1.2` (p. 115) desplazando a `C1.7` (p. 122). | Se calibraron estrictamente solo los términos requeridos (`rodilla`, `tobillo`, `pretina`, `palanca`, etc.), restaurando `C1.7` al Top 1 y pasando 8/8 pruebas de judogi. |
| Invocación Python con `os.environ['RRE_ENABLE_CHUNK_STITCHING'] = '1'` | `1` | En `tests/test_rre_stitching_integration.py`, la prueba `test_rre_stitching_feature_flag_disabled` pasa explícitamente `ReasoningRetrievalEngine(enable_chunk_stitching=False)`. La variable de entorno forzada sobrescribía el parámetro explícito. | Se refactorizó la lógica de inicialización en `rre_engine.py` respetando la precedencia: parámetro explícito > variable de entorno > `True` por defecto. |
| Ejecución de scripts scratch con salida en consola | `1` | `UnicodeEncodeError: 'charmap'` en Windows pwsh al intentar imprimir emojis (`📋`, etc.) de los mensajes de ADA. | Se redirigió la salida de auditoría a archivos UTF-8 o sanitización ASCII. No afecta la lógica de producción. |

---

## 3. COMPARATIVA FUNCIONAL: STITCHING ACTIVADO VS. DESACTIVADO

Se ejecutaron las consultas representativas exigidas por Alexis comparando ambos estados del motor:

### Caso 1: Artículo 14 (Puente, Ippon y Excepciones)
- **Consulta:** *"El puente voluntario para evitar una caida se considera ippon?"*
- **Sin Stitching (`enable_chunk_stitching=False`):**
  - **Top 1:** `Article 14` (Página 167)
  - **Texto original entregado:** 1,371 caracteres.
  - **Contenido del texto:** Inicia abruptamente con: *"This decision is taken for the safety of the athletes, so they do not try to escape..."*.
  - **Deficiencia:** No incluye la p. 166 donde se define qué es un puente (`head and one foot or both feet in contact with the tatami`) ni la regla general de que el puente voluntario tras proyección es Ippon. El LLM recibe una justificación sin la premisa normativa.
- **Con Stitching (`enable_chunk_stitching=True`):**
  - **Top 1:** `Article 14` (Página 167 ensamblada)
  - **Texto original entregado:** 3,045 caracteres.
  - **Composite KUN:** `SOR-2026-08-P166-P167`.
  - **Contenido del texto:** Contiene íntegramente la p. 166 (cuatro criterios de Ippon, definición formal de puente voluntario con fotos 14.2-14.3) concatenada con la p. 167 (razón de seguridad cervical, excepción cuando uke cae sobre el cuerpo de tori, y evaluación en ne-waza).
  - **Mejora demostrada:** Resuelve la amputación del artículo generada por el salto de página del PDF oficial.

### Caso 2: Artículo 18.1.4 (Sanciones a Cadetes)
- **Consulta:** *"En categoria cadetes que sancion tiene defenderse de cabeza?"*
- **Sin Stitching:**
  - **Top 1:** `Article 18.1.4` (Página 188)
  - **Texto original:** 2,045 caracteres. Contiene el principio de la sección de cadetes pero corta antes de completar las disposiciones de la p. 189.
- **Con Stitching:**
  - **Top 1:** `Article 18.1.4` (Página 188 ensamblada)
  - **Texto original:** 2,929 caracteres (`SOR-2026-08-P188-P189`).
  - **Mejora demostrada:** Unifica todas las sanciones aplicables a la categoría de edad sin truncamientos.

### Caso 3: Consulta Normativa Ordinaria (Sin necesidad de Stitching)
- **Consulta:** *"Cuales son las dimensiones del tatami?"*
- **Sin Stitching:** Top 1: Art. 8.7 (p. 96), 3,143 caracteres, `is_stitched=False`.
- **Con Stitching:** Top 1: Art. 8.7 (p. 96), 3,143 caracteres, `is_stitched=False`, `composite_kun=None`.
- **Comportamiento:** El stitcher detecta que el artículo no continúa en la página adyacente y no altera el fragmento ni degrada el rendimiento.

---

## 4. VERIFICACIÓN DE CITAS Y REFERENCIAS DE PÁGINAS

Se auditó la estructura devuelta en `evidence` y `source_spans` para verificar que la citación no induzca a error al usuario:

```json
{
  "passage_id": "SOR-2026-08-P167-S187",
  "article_id": "Article 14",
  "page": 167,
  "is_stitched": true,
  "composite_kun": "SOR-2026-08-P166-P167",
  "source_spans": [
    {
      "kun": "SOR-2026-08-P166-S187",
      "page": 166,
      "url": "https://.../IJF_Sport_and_Organisation_Rul-1787430903.pdf"
    },
    {
      "kun": "SOR-2026-08-P167-S187",
      "page": 167,
      "url": "https://.../IJF_Sport_and_Organisation_Rul-1787430903.pdf"
    }
  ],
  "stitched_kuns": ["SOR-2026-08-P166-S187", "SOR-2026-08-P167-S187"]
}
```

### Hallazgo sobre la URL con ancla de página:
En el modo stitching, el `source_url` principal conserva `#page=167` (la semilla de mayor relevancia), mientras que la lista `source_spans` desglosa con exactitud matemática las dos páginas involucradas (166 y 167) para que el frontend o el usuario puedan auditar ambos tramos del PDF original.

---

## 5. RESULTADOS DE LA SUITE COMPLETA DE PRUEBAS

Ejecución limpia desde la raíz del proyecto (`C:\PROYECTOS\IJF-SOR-Assistant`):

```text
platform win32 -- Python 3.12.10, pytest-8.3.3
rootdir: C:\PROYECTOS\IJF-SOR-Assistant
collected 271 items

271 passed in 52.14s
```

- **Pruebas Totales:** 271
- **Aprobadas (PASSED):** 271 (100%)
- **Fallidas (FAILED):** 0
- **Errores (ERRORS):** 0
- **Omitidas (SKIPPED):** 0
- **Advertencias (WARNINGS):** 1 (DeprecationWarning de `pytest-asyncio` relativa a la configuración predeterminada de event loops, no imputable a nuestro código).

---

## 6. DICTAMEN FUNCIONAL Y RECOMENDACIÓN

### 6.1 Dictamen Funcional
**CONFORME.**
La activación nativa de `PassageStitcher`:
1. Resuelve una limitación real y documentada del fraccionamiento por páginas físicas del PDF IJF SOR, suministrando a los modelos de razonamiento (ADA) el texto reglamentario íntegro (regla general + excepciones).
2. No degrada las consultas de página única (actúa de forma neutra).
3. Mantiene el 100% de aprobación en la batería de 271 pruebas sin regresiones.

### 6.2 Recomendación Concreta
**CONTINUAR CON LA ACTIVACIÓN NATIVA.**  
Mantener la modificación actual en `src/rre_engine.py` donde `enable_chunk_stitching=True` es el valor por defecto nativo y permanece desactivable explícitamente (`enable_chunk_stitching=False`) si alguna prueba diagnóstica lo requiere.

---
*Este expediente queda en espera de la revisión soberana y aprobación de Alexis Oliveros Lozano antes de realizar cualquier acción posterior.*

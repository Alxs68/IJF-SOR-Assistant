# INFORME TÉCNICO DE AUDITORÍA Y CORRECCIÓN VISUAL
## Diagnóstico y Solución: Renderizado Literal de HTML en la Interfaz Web
### Proyecto: IJF SOR Assistant 2026

- **Product Owner y Autoridad Normativa:** Alexis Oliveros Lozano
- **Auditor Metodológico:** ChatGPT
- **Ejecutor Técnico:** Antigravity
- **Fecha:** 8 de noviembre de 2026
- **Entorno Evaluado:** Local (`C:\PROYECTOS\IJF-SOR-Assistant`) y Producción OCI (`https://sor.alxol.com`)
- **Estado Operativo:** Corrección local aplicada, verificada visualmente mediante Playwright y lista para autorización de despliegue.

---

## 1. DESCRIPCIÓN DEL INCIDENTE

Tras la actualización del runtime de producción (`bcdfe7d`), se observó que la interfaz web mostraba código fuente HTML sin procesar como texto plano en la pantalla principal:
1. **Cabecera Principal:** Visualización literal de etiquetas `<div>`, `<h2>`, estilos CSS y una cadena extensa de más de 40.000 caracteres correspondiente al logotipo oficial codificado en Base64 (`data:image/svg+xml;base64,PHN2Zy...`).
2. **Mensaje de Introducción:** Visualización literal de etiquetas `<h1>` y `<p>` con el texto de bienvenida sin estilos tipográficos.
3. **Pérdida de la Presentación Visual:** Las cajas de la cabecera y el mensaje de bienvenida aparecían como bloques de código preformateado (`<pre><code>`).

---

## 2. DIAGNÓSTICO DE CAUSA RAÍZ (FASE 1)

El análisis técnico exhaustivo identificó dos factores concurrentes que desencadenaron la falla:

### Causa Primaria: Indentación de 4 espacios bajo el estándar CommonMark
En `app.py`, las llamadas encargadas de renderizar la cabecera (líneas 1118-1179) y el mensaje de bienvenida (líneas 1534-1539) utilizaban:
```python
st.markdown(f"""
    <style>...
    <div style="...">
        <img src="data:image/svg+xml;base64,{base64_logo}" />
        <h2>{t('app_title', lang)}</h2>
    </div>
""", unsafe_allow_html=True)
```
- Al estar dentro de bloques condicionales Python (`if base64_logo:` y `else:`), la cadena multilínea f-string comenzaba con `\n    ` (salto de línea seguido de 4 espacios de indentación).
- Bajo la especificación oficial **CommonMark** y los motores modernos de parsing Markdown (`react-markdown` / `remark-parse` / `rehype-raw` integrados en Streamlit), **cualquier bloque que inicie con 4 espacios o un tabulador es clasificado estrictamente como un bloque de código indentado (`indented code block`)**.
- En consecuencia, el parser Markdown encapsula el contenido dentro de `<pre><code>...</code></pre>` y escapa automáticamente todas las etiquetas HTML (`&lt;div&gt;`, `&lt;h2&gt;`, `&lt;p&gt;`), neutralizando el flag `unsafe_allow_html=True` y mostrando el código HTML y el string Base64 como texto visible.

### Causa Secundaria: Corrupción de saltos de línea `\r\r\n` (CRCRLF)
Se detectó que en el commit `3e86a08` se introdujeron terminadores de línea corruptos `\r\r\n` (1.548 ocurrencias, exactamente una por línea de `app.py`). En entornos Linux (como Ubuntu en OCI), esto introducía caracteres de retorno de carro residuales (`\r`) en las cadenas multilínea, distorsionando el flujo del parser frontend.

### Momento de Manifestación:
El código fuente contenía esta indentación previamente; sin embargo, al reconstruir la imagen Docker en OCI para la corrección de dependencias, la instalación limpia de Streamlit resolvió la versión más reciente en PyPI, cuyo motor `react-markdown` aplica con rigor absoluto la regla de bloques de código de CommonMark.

---

## 3. CORRECCIÓN APLICADA (FASE 2)

Se implementó una solución **mínima, robusta y no invasiva** que resuelve ambas causas sin tocar lógica normativa ni arquitectura:

### 3.1 Normalización de Terminadores de Línea
Se sanearon todos los saltos de línea de `app.py`, eliminando las 1.548 ocurrencias de `\r\r\n` y estableciendo formato estándar Unix `\n` (LF).

### 3.2 Función Auxiliar Defensiva `render_custom_html`
Se añadió un helper en `app.py` que desacopla la inyección de HTML del parser Markdown:
```python
def render_custom_html(html_content: str):
    """Inserta HTML en la UI evitando la interpretación CommonMark como bloque de código."""
    if hasattr(st, "html"):
        st.html(html_content)
    else:
        st.markdown(html_content, unsafe_allow_html=True)
```
- **Streamlit `>= 1.35.0` (`st.html`):** Inyecta el contenido HTML/CSS directamente al DOM mediante `dangerouslySetInnerHTML` con sanitización `DOMPurify`, omitiendo por completo el parser Markdown y eliminando cualquier riesgo de bloque de código.
- **Fallback legacy (`st.markdown`):** Mantiene retrocompatibilidad garantizada en caso de entornos anteriores.

### 3.3 Alineación a Columna 0 de las Cadenas HTML
Tanto en la cabecera como en la bienvenida, las cadenas multilínea ahora inician en columna 0 (`f"""<style>` y `f"""<div`), eliminando los 4 espacios iniciales:
- **Cabecera con Logotipo:** Sustituido `st.markdown(...)` por `render_custom_html(...)`.
- **Cabecera Alternativa:** Sustituido `st.markdown(...)` por `render_custom_html(...)`.
- **Mensaje de Bienvenida:** Sustituido `st.markdown(...)` por `render_custom_html(...)`.

---

## 4. VALIDACIÓN TÉCNICA Y VISUAL (FASE 3)

Se ejecutó una verificación integral en tres niveles:

### 4.1 Compilación y Pruebas Unitarias/E2E
- `python -m py_compile app.py`: **Compilación exitosa (código 0)**.
- `pytest tests/test_p1_b_configuracion_e2e.py`: **10 passed in 156.25s (100% PASS)**. Todas las aserciones de integración E2E, gobernanza documental, motor RRE y respuestas estructuradas pasaron sin errores.

### 4.2 Inspección Automatizada de Texto con Playwright
Se levantó una instancia local de Streamlit y se inspeccionó el árbol del DOM mediante Playwright (`scratch/test_local_playwright_fixed.py`):
```text
VERIFICATION SUCCESS: Zero raw HTML artifacts found in page text!
Rendered h2 title: Asistente SOR IJF
Rendered base64 SVG images: 1
Rendered h1 intro title: Bienvenido
Submitting query: 'tatami' ...
```
- **Artefactos HTML sin procesar en texto:** **0 (CERO)**.
- **Etiqueta `h2` ("Asistente SOR IJF"):** Renderizada como nodo de encabezado visual.
- **Logotipo SVG en Base64:** Renderizado como imagen gráfica `<img>`.
- **Mensaje `h1` ("Bienvenido"):** Renderizado como nodo de encabezado visual.

### 4.3 Verificación Visual (Capturas de Pantalla)
- **Antes (en Producción):** Se evidenciaban bloques rectangulares grises con `<div>`, `<h2>`, `<p>` y la cadena Base64 desbordando el panel principal.
- **Después (Local Corregido):** La cabecera se presenta en su contenedor blanco estilizado, el isotipo IJF circular a color en el centro superior, el título azul en tipografía Outfit con el tooltip interactivo a la derecha, la barra de consulta enmarcada limpiamente y el mensaje de bienvenida formateado.

---

## 5. ESTADO DEL REPOSITORIO Y SERVIDOR

| Parámetro | Estado Actual |
| :--- | :--- |
| **Repositorio Local** | `app.py` corregido en working tree local. Sintaxis verificada. |
| **Corpus / PDF / Embeddings** | **Intactos al 100%** (no modificados). |
| **Parámetros DEC-009** | **$K=5$ y `min_score=None` intactos al 100%**. |
| **GitHub (`origin/main`, `origin/integration`)** | En commit `bcdfe7d` (sin commits nuevos, respetando la directiva de no publicar sin autorización). |
| **Producción OCI** | Contenedor activo en commit `bcdfe7d` listo para recibir la actualización. |

---

## 6. PROPUESTA DE PUBLICACIÓN Y DESPLIEGUE

Para llevar esta corrección visual a producción, se propone el siguiente procedimiento estricto:

1. **Commit Local Exclusivo:**
   - Archivo: exclusivamente `app.py`.
   - Mensaje sugerido: `fix(ui): use native st.html and fix markdown indentation for header and intro`
2. **Publicación Remota:**
   - Push a `integration/ijf-sor-2026-08-merge`.
   - Fast-forward a `main`.
3. **Despliegue en OCI:**
   - `git checkout` del commit en `/home/ubuntu/IJF-SOR-Assistant`.
   - Reinicio del servicio Streamlit: `docker compose restart streamlit` (sin rebuild, ya que Streamlit monta `/app` vía volumen).
   - Comprobación visual mediante Playwright sobre `https://sor.alxol.com`.

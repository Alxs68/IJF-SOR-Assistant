# INFORME TÉCNICO DE INCIDENCIA — SELECTOR DE TEMA CLARO / OSCURO
## Diagnóstico de Causa Raíz e Integración de Temas en Producción
### Proyecto: IJF SOR Assistant 2026

- **Incidencia:** El usuario no puede cambiar a modo oscuro en la interfaz de producción (`https://sor.alxol.com`).
- **Commit Afectado:** `bca5ce6a5991b846cb4f4bca93a97589e1e27bf4`
- **Ambiente Evaluado:** Producción OCI (`149.130.187.132`) y Local
- **Responsable Técnico:** Antigravity
- **Product Owner:** Alexis Oliveros Lozano
- **Fecha de Diagnóstico:** 8 de noviembre de 2026

---

## 1. RESUMEN EJECUTIVO Y DIAGNÓSTICO GENERAL

Se investigó a fondo el comportamiento visual y los mecanismos de selección de tema en la aplicación web del IJF SOR Assistant.

### Hallazgos Fundamentales:
1. **Inexistencia de Control de Usuario en la Interfaz (`app.py`):** La aplicación no posee ningún selector (botón, toggle, radio o selectbox) en la barra lateral ni en la cabecera que permita al usuario elegir entre Modo Claro y Modo Oscuro.
2. **Ocultamiento Nativo de "Settings" en Producción por Streamlit:** En accesos remotos a través de dominio público (`https://sor.alxol.com`), Streamlit clasifica la sesión automáticamente como `viewer` bajo su política por defecto `toolbarMode = "auto"`. Por diseño de seguridad/presentación de Streamlit, **el menú de configuración ("Settings") es eliminado del menú hamburguesa (`stMainMenuButton`)**, dejando visibles únicamente las opciones *"Print"* y *"Record screen"*. El usuario no tiene vía alguna para acceder al selector nativo de temas de Streamlit.
3. **Desacoplamiento entre `@media (prefers-color-scheme: dark)` y el DOM de Streamlit:** El commit `bca5ce6` implementó los tokens de diseño de modo oscuro dentro de una media query CSS `@media (prefers-color-scheme: dark)`. Esta regla únicamente escucha la preferencia del sistema operativo del cliente. Si un usuario con sistema operativo en modo oscuro accede a la página, los tokens CSS cambian a colores claros (e.g., texto blanco `#f8fafc`), pero el fondo principal de Streamlit (`.stApp`) permanece en su valor por defecto **100% blanco (`rgb(255, 255, 255)`)**, generando un conflicto visual severo.
4. **Archivo de Configuración Incompleto (`.streamlit/config.toml`):** El archivo `.streamlit/config.toml` solo define `primaryColor = "#2563EB"` y `font = "sans serif"`. No define `base`, ni `toolbarMode`, ni variables de superficie para modo oscuro.

---

## 2. EVIDENCIAS TÉCNICAS REPRODUCIDAS

### 2.1 Menú Hamburguesa en Producción (`https://sor.alxol.com`)
Mediante inspección automatizada con Playwright sobre `button[data-testid="stMainMenuButton"]` en producción:
```text
Header buttons: [{'id': '', 'testId': 'stMainMenuButton', 'ariaLabel': 'Main menu', 'title': None, 'text': ''}]
Menu text items: {'Print', 'Record screen', 'Made with Streamlit v1.67.0'}
Settings target count: 0
```
- **Evidencia:** La opción *"Settings"* (Configuración) no existe en el DOM en producción.

### 2.2 Inspección del Menú Lateral (`stSidebar`)
```text
Idioma / Language: [ES / EN]
Información (Expander)
Edición del Reglamento SOR: 14 August 2026 (Official)
Configuración del Proveedor IA (LLM)
Filtro de Artículos
```
- **Evidencia:** No existe ningún control interactivo de tema en el código de `app.py`.

### 2.3 Conflicto Visual con Sistema Operativo en Modo Oscuro (`color_scheme="dark"`)
Al emular un navegador con `prefers-color-scheme: dark`:
```json
{
  "root_ijfTextColor": "#f8fafc",
  "root_titleColor": "#60a5fa",
  "stAppBg": "rgb(255, 255, 255)",
  "stAppColor": "rgb(47, 45, 43)",
  "h2Color": "rgb(96, 165, 250)",
  "sidebarBg": "rgb(248, 248, 247)"
}
```
- **Evidencia:** 
  - `--ijf-text-color` cambia a `#f8fafc` (blanco/gris muy claro).
  - Pero `.stApp` conserva `backgroundColor = rgb(255, 255, 255)` (blanco puro) y `.sidebar` conserva `rgb(248, 248, 247)` (gris claro).
  - Los estilos inyectados en `:root` no gobiernan el fondo del contenedor principal de Streamlit ni del sidebar.

---

## 3. ARCHIVOS Y LÍNEAS RESPONSABLES

### 1. `app.py` (Líneas 61 a 127)
- **Defecto:** Los tokens de tema claro se definen en `:root`, y los de tema oscuro en `@media (prefers-color-scheme: dark) :root`.
- **Causa:** No se provee una clase selectora (e.g., `[data-theme="dark"]` o `.dark-theme`) gobernada por un widget de Streamlit, ni se aplican las reglas de fondo a `.stApp` ni `[data-testid="stSidebar"]`.

### 2. `app.py` (Líneas 950 a 1170 — Panel Lateral)
- **Defecto:** Ausencia de widget para que el usuario seleccione su tema preferido (`Claro`, `Oscuro`, `Automático`).

### 3. `.streamlit/config.toml` (Líneas 1 a 3)
- **Defecto:** No declara la directiva `[client] toolbarMode = "developer"` (lo cual permitiría ver el menú nativo en producción si se deseara depender de Streamlit), ni define la estrategia de tema base.

---

## 4. ANÁLISIS DE LA CAUSA RAÍZ

La causa raíz es **doble**:

1. **Arquitectónica de Streamlit en Producción:** Streamlit por defecto desactiva las herramientas de desarrollador y configuración en entornos remotos fuera de `localhost`. Confiar en el menú nativo `Settings` de Streamlit para el usuario final es un error de diseño para aplicaciones desplegadas en la nube.
2. **Implementación CSS Desacoplada del Entorno:** La regla `@media (prefers-color-scheme: dark)` sólo responde a la configuración de la máquina del usuario y no a la aplicación. Además, los estilos introducidos en `bca5ce6` sólo parametrizaron variables personalizadas (`--ijf-text-color`, `--kun-bg`, etc.) sin sobreescribir las superficies globales de Streamlit (`.stApp`, `section[data-testid="stSidebar"]`, `header[data-testid="stHeader"]`).

---

## 5. CORRECCIÓN RECOMENDADA (SOLUCIÓN MÍNIMA Y ROBUSTA)

Para garantizar que el usuario pueda cambiar a Modo Oscuro en cualquier momento y desde cualquier dispositivo (independientemente de cómo tenga configurado su Windows/Mac), la solución recomendada consta de **dos pasos mínimos y no invasivos**:

### Paso 1: Agregar Selector de Tema en el Panel Lateral (`app.py`)
En la barra lateral (`st.sidebar`), junto al selector de idioma o configuración general:
```python
theme_options = {
    "es": ["Automático (Sistema)", "Claro", "Oscuro"],
    "en": ["Automatic (System)", "Light", "Dark"]
}
selected_theme = st.sidebar.selectbox(
    t("theme_selector_label", lang),
    theme_options[lang],
    index=0,
    key="user_theme_preference"
)
```

### Paso 2: Inyección de Estilos Reactiva y Completa (`app.py`)
Reemplazar la dependencia pasiva de `@media (prefers-color-scheme: dark)` por una inyección dinámica controlada por `selected_theme`:

```python
is_dark = (
    selected_theme in ("Oscuro", "Dark") 
    # o si es automático, se complementa con media query
)
```

Si el usuario elige **Oscuro**:
Inyectar reglas CSS explícitas que gobiernen tanto los tokens IJF como los contenedores nativos de Streamlit:
```css
/* Variables IJF Modo Oscuro */
:root {
    --ijf-text-color: #f8fafc;
    --ijf-blue: #60a5fa;
    --ijf-title-color: #60a5fa;
    --kun-bg: #1e293b;
    --kun-border: #334155;
    ...
}
/* Superficies Streamlit Forzadas a Oscuro */
.stApp {
    background-color: #0e1117 !important;
    color: #f8fafc !important;
}
[data-testid="stSidebar"] {
    background-color: #1e293b !important;
}
[data-testid="stHeader"] {
    background-color: #0e1117 !important;
}
```

Si el usuario elige **Claro**:
Inyectar tokens claros y asegurar superficies blancas `#ffffff` y sidebar `#f8fafc`.

Si el usuario elige **Automático**:
Mantener el fallback con `@media (prefers-color-scheme: dark)` aplicando tanto a las variables como a `.stApp` y `.stSidebar`.

---

## 6. ALCANCE DE LA CORRECCIÓN

- **Archivos a modificar:** Exclusivamente `app.py`.
- **Lógica normativa:** Cero impacto. No toca corpus, RRE, embeddings, grafos ni ADA.
- **Riesgo técnico:** Mínimo (exclusivo de presentación visual CSS y un `st.selectbox` en el sidebar).

---

## 7. CRITERIOS DE PRUEBA Y ACEPTACIÓN

Una vez autorizada la implementación, se validarán los siguientes escenarios en navegador:

1. **Prueba 1 — Selector en Modo Claro:**
   - La página se renderiza con fondo blanco (`#ffffff`).
   - El sidebar se renderiza en gris claro (`#f8fafc`).
   - El texto es `#0f172a` con contraste WCAG 2.2 AAA ($17.85:1$).
2. **Prueba 2 — Selector en Modo Oscuro:**
   - Al seleccionar *"Oscuro"*, el fondo `.stApp` cambia a `#0e1117` de inmediato.
   - El sidebar cambia a `#1e293b`.
   - Las tarjetas KUN cambian a `#1e293b` con borde `#334155`.
   - El texto cambia a `#f8fafc` con contraste WCAG 2.2 AAA ($18.06:1$).
   - La cabecera, logo y bienvenida se adaptan sin parpadeos ni textos invisibles.
3. **Prueba 3 — Selector en Modo Automático:**
   - Responde fielmente al cambio de preferencia del sistema operativo del usuario.
4. **Prueba 4 — Cero código HTML crudo:**
   - Mantener intacta la regla `render_custom_html` sin tags visibles.

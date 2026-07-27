# Plan Final de Diseño y Despliegue

## Proyecto
IJF SOR Assistant

## Estado actual
- Rama principal `main` en sincronía con `origin/main`.
- Último commit en `main`: `8164306` — `fix(ui): avoid active_item usage on welcome screen when no history exists`.
- Validación completa de la suite de pruebas:
  - `python -m pytest -q`
  - Resultado: `31 passed, 1 warning`
- El único warning es deprecación en `reference_checker.py` por `datetime.utcnow()`.
- El despliegue en OCI fue actualizado desde `origin/main` y la app responde con `HTTP 200` en `127.0.0.1:8501`.

## Objetivo del documento
Este documento resume el cierre técnico del proyecto y establece el plan de diseño y despliegue para la siguiente fase.

---

## 1. Alcance de cierre actual
### 1.1 Contenidos validados
- Interfaz de usuario Streamlit con diseño tipo chat revisada.
- Corrección del bug `NameError: active_item` en la pantalla de bienvenida.
- Ajustes de estilo para encabezados y visualización en dispositivos móviles.
- Comportamiento del sistema con y sin auditoría visible.

### 1.2 Verificación
- Pruebas unitarias y de integración locales ejecutadas.
- Sintaxis de `app.py` validada con `python -m py_compile app.py`.
- Despliegue remoto reconstruido y verificado.

### 1.3 Documento de referencia de despliegue existente
- `docs/deployment/oci_deployment.md`

---

## 2. Plan de despliegue final
### 2.1 Requisitos previos
- Clave de API Gemini configurada en `GEMINI_API_KEY` o `GOOGLE_API_KEY`.
- Instancia OCI con puerto `8501` abierto en la VCN y UFW permitido en Ubuntu.
- Preferible usar un servicio `systemd` o Docker Compose para robustez.

### 2.2 Checklist de despliegue
- [ ] Actualizar repositorio remoto con `git push origin main`.
- [ ] Conectar a la instancia OCI por SSH.
- [ ] Renovar el código en la VM:
  - `git fetch origin main`
  - `git reset --hard origin/main`
- [ ] Ejecutar la aplicación:
  - Docker Compose: `docker compose up -d --build --force-recreate`
  - O sistema nativo: `python3 -m venv .venv` + `pip install -r requirements.txt` + `streamlit run app.py`.
- [ ] Confirmar estado del servicio y respuesta HTTP.
- [ ] Probar en móvil con recarga forzada o incógnito para evitar caché.

### 2.3 Recomendación de despliegue
Para producción o demostración estable, usar `systemd` con entorno `.env` protegido y restart automático.

---

## 3. Plan de diseño de siguiente fase
### 3.1 Objetivos de diseño
- Mejorar la experiencia móvil:
  - Ajustar el logo y el título para que se acomoden en pantallas pequeñas.
  - Reducir la jerarquía tipográfica excesiva en los encabezados de respuesta.
- Consolidar la interfaz chat-style con sugerencias y flujo de conversación claro.
- Mantener la transparencia de trazabilidad sin saturar la UI.

### 3.2 Métricas de éxito
- La página inicial debe conservar jerarquía visual en móvil sin romper el layout.
- Las preguntas sugeridas deben verse como chips compactos, no como botones gigantes.
- Las respuestas deben mostrar título/CITAS/relaciones con tamaños balanceados.
- No debe generarse ningún error en el inicio al cargar sin historial.

### 3.3 Recomendación para modo mock
- Implementar un `mode` de desarrollo que utilice respuestas simuladas en vez de Gemini.
- Permite validar UI y flujo sin consumo de tokens.
- En modo mock, el comportamiento de la app debe ser funcionalmente equivalente al modo real.

### 3.4 Pasos propuestos
1. Definir un conjunto de casos de prueba UX para móvil y escritorio.
2. Extraer los estilos críticos a CSS responsive en `app.py`.
3. Validar cambios con pruebas locales y ejecución de la app.
4. Documentar cada cambio en `docs/project-management`.

---

## 4. Entregables finales
- Documento de diseño y despliegue guardado en:
  - `docs/project-management/final_design_and_deployment_plan.md`
- Guía de despliegue ya existente en:
  - `docs/deployment/oci_deployment.md`
- Código validado y listo para producción.

---

## 5. Recomendación de siguiente acción
1. Confirmar que deseas el cierre técnico final en `main`.
2. Si es aprobado, reiniciar el despliegue remoto con la versión actual.
3. Abrir una nueva fase de diseño con un documento dedicado de trabajo UX para móviles y mock mode.

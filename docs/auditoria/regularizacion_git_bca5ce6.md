# INFORME DE REGULARIZACIÓN CONTROLADA DE GOBERNANZA Y GIT (COMMIT BCA5CE6)

**Proyecto:** IJF SOR Assistant 2026  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Baseline de partida ratificado:** `bca5ce6a5991b846cb4f4bca93a97589e1e27bf4`  
**Nuevo commit local auditado:** `0c1c8bdea57195819dc5b7e5eabb63d0a9f7f055`  
**Product Owner y Autoridad Normativa:** Alexis Oliveros Lozano  
**Planificación y Auditoría Metodológica:** ChatGPT  
**Ejecutor Técnico:** Antigravity  
**Fecha:** 8 de noviembre de 2026  

---

## 1. RESUMEN EJECUTIVO

En cumplimiento estricto de las directivas de gobernanza autorizadas por el Product Owner y planificadas por ChatGPT, se ejecutó la regularización formal y no destructiva del control de versiones del proyecto IJF SOR Assistant 2026.

Las acciones comprendieron:
1. **Ratificación retrospectiva documental:** Convalidación formal de `bca5ce6` como baseline soberano de producción, documentando la excepción de gobernanza sin alterar el historial existente.
2. **Commit local atómico e independiente:** Creación del commit local `0c1c8bd` que aísla de forma pura y exclusiva el selector de tema claro/oscuro en `app.py`, verificado mediante batería de pruebas y sin realizar push.
3. **Auditoría de divergencia Git:** Diagnóstico exacto del estado de las ramas locales (`main`, `integration/ijf-sor-2026-08-merge`) y remotas (`origin/main`, `origin/integration/ijf-sor-2026-08-merge`).
4. **Preservación total de producción:** Cero modificaciones, cero despliegues, cero alteraciones de variables de entorno y cero reinicios en la infraestructura OCI.

---

## 2. FASE 1 — RATIFICACIÓN DOCUMENTAL DE GOBERNANZA

En el documento [gobernanza_bca5ce6.md](file:///c:/PROYECTOS/IJF-SOR-Assistant/docs/auditoria/gobernanza_bca5ce6.md) se formalizó:
- **Baseline de Producción Ratificado:** `bca5ce6a5991b846cb4f4bca93a97589e1e27bf4` es reconocido oficialmente como el estado legítimo y estable desplegado en OCI (`https://sor.alxol.com`).
- **Registro Explícito de la Excepción:** Se documentó que el empaquetado conjunto de conectividad Gemini (`src/llm_provider.py`) y rediseño CSS (`app.py`), junto con el push directo y despliegue simultáneo, constituyó una desviación de los gates de autorización previamente pactados.
- **Inmutabilidad:** Se preservó íntegro el historial Git previo sin reescritura forzada ni rollbacks.
- **Integridad Normativa:** Se certificó que el corpus de 385 KUNs, índices vectoriales, grafos y directivas DEC-009 permanecieron intactos.

---

## 3. FASE 2 — COMMIT LOCAL ATÓMICO DEL SELECTOR

Se inspeccionó de forma exhaustiva el diff pendiente en `app.py`, constatando que contenía **exclusivamente**:
1. Inicialización de `st.session_state.app_theme = "auto"`.
2. Tokens CSS adaptables dinámicamente (`light_theme_vars` y `dark_theme_vars`).
3. Selector visual en la barra lateral con sincronización bilingüe (Español / Inglés).
4. Sincronización del visor PDF integrado con el tema activo.
5. Calibración de contraste WCAG 2.2 AAA en textos secundarios y captions.

### 3.1 Pruebas Pre-Commit Ejecutadas
- `python -m py_compile app.py` $\to$ **PASS (0 errores de sintaxis)**.
- `python -m pytest tests/test_i18n.py tests/test_ui_controls_and_novedades.py` $\to$ **12/12 PASS (100% OK)**.

### 3.2 Commit Local Creado
```text
Commit SHA: 0c1c8bdea57195819dc5b7e5eabb63d0a9f7f055
Rama: integration/ijf-sor-2026-08-merge
Mensaje: feat(ui): add light and dark theme selector
Archivos: 1 file changed, 255 insertions(+), 74 deletions(-)
Push remoto: NO EJECUTADO (Commit 100% local)
```

---

## 4. FASE 3 — AUDITORÍA DE DIVERGENCIA GIT

Inspección de las cuatro referencias clave del repositorio:

```
[3e86a08] main (local)
    │
    ▼ (3 commits por detrás)
[bcdfe7d] fix(deps): declare pydantic dependency for OCI runtime
    │
    ▼
[20d6114] fix(ui): use native st.html and fix markdown indentation
    │
    ▼
[bca5ce6] origin/main | origin/integration/ijf-sor-2026-08-merge | PRODUCCIÓN OCI
    │
    ▼ (1 commit local por delante)
[0c1c8bd] integration/ijf-sor-2026-08-merge (local HEAD actual)
          feat(ui): add light and dark theme selector
```

### 4.1 Matriz de Estado de Ramas

| Referencia Git | Hash Commit HEAD | Estado Relativo | Riesgo de Conflicto |
| :--- | :--- | :--- | :---: |
| **`main` (Local)** | `3e86a0898a233a4357f11a29870780084d816f25` | **Detrás por 3 commits** respecto a `origin/main` (`bcdfe7d`, `20d6114`, `bca5ce6`) | **Nulo** (Fast-forwardable puro) |
| **`origin/main`** | `bca5ce6a5991b846cb4f4bca93a97589e1e27bf4` | Sincronizado con producción en OCI | **Nulo** |
| **`origin/integration/...`** | `bca5ce6a5991b846cb4f4bca93a97589e1e27bf4` | Idéntico a `origin/main` | **Nulo** |
| **`integration/...` (Local)** | `0c1c8bdea57195819dc5b7e5eabb63d0a9f7f055` | **Delante por 1 commit** (`0c1c8bd`) respecto a `origin/integration` | **Nulo** (Extensión lineal pura) |

### 4.2 Estado del Working Tree
- Archivos tracked modificados: **0** (`working tree clean`).
- Archivos untracked: Exclusivamente reportes de auditoría generados en `docs/auditoria/` y scripts temporales en `scratch/`.

### 4.3 Análisis de Riesgos de Sincronización
- No existen bifurcaciones, merges conflictivos ni commits huérfanos.
- El historial es **100% lineal**.
- La actualización de `main` local hacia `origin/main` requiere un simple avance rápido (`fast-forward`), sin posibilidad de colisión ni rebase complejo.

---

## 5. CONFIRMACIÓN EXPLÍCITA DE PRODUCCIÓN

- **Servidor OCI (`149.130.187.132` / `https://sor.alxol.com`):** **NO MODIFICADO.**
- **Contenedor Docker `ijf-sor-assistant`:** En ejecución ininterrumpida sobre `bca5ce6`.
- **Variables de Entorno (`.env`):** Sin cambios ni lecturas remotas.
- **Corpus Normativo:** 385 KUNs, DEC-009, embeddings Chroma y grafos intactos.

---

## 6. RECOMENDACIÓN TÉCNICA PARA LA SIGUIENTE FASE

Una vez concluida la regularización y con el commit `0c1c8bd` probado y validado localmente, se recomienda la siguiente secuencia de pasos para la fase de publicación (cuando sea formalmente autorizada por Alexis Oliveros):

1. **Sincronizar `main` local con `origin/main`:**  
   `git checkout main && git merge --ff-only origin/main`
2. **Integrar el commit del selector en `main`:**  
   `git merge --ff-only integration/ijf-sor-2026-08-merge`
3. **Publicar en GitHub:**  
   `git push origin main` y `git push origin integration/ijf-sor-2026-08-merge`
4. **Despliegue ordenado en OCI:**  
   Ejecutar el pull y reinicio controlado en producción bajo protocolo de respaldo inmutable.

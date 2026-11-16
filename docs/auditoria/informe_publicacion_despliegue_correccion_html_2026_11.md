# INFORME OFICIAL DE PUBLICACIÓN Y DESPLIEGUE EN PRODUCCIÓN
## Corrección de Renderizado HTML en Cabecera e Introducción (`app.py`)
### Proyecto: IJF SOR Assistant 2026

- **Product Owner y Autoridad Normativa:** Alexis Oliveros Lozano
- **Auditor Metodológico Independiente:** ChatGPT
- **Ejecutor Técnico:** Antigravity
- **Fecha de Despliegue:** 8 de noviembre de 2026
- **Commit Autorizado y Desplegado:** `20d6114734a8b88b8b84c0187f4fd45facbca7bd`
- **Mensaje de Commit:** `fix(ui): use native st.html and fix markdown indentation for header and intro`
- **Ambiente de Producción:** Oracle Cloud Infrastructure (`149.130.187.132`, Ampere A1 ARM64, Ubuntu 24.04 LTS)
- **URL Pública:** `https://sor.alxol.com`

---

## 1. RESUMEN EJECUTIVO Y DICTAMEN FINAL

En cumplimiento estricto de la autorización conferida por Alexis Oliveros Lozano, se completó con éxito el pipeline integral de publicación y despliegue del commit `20d6114`.

### Dictamen: **DESPLIEGUE EXITOSO — PRODUCCIÓN 100% OPERATIVA Y RESTAURADA VISUALMENTE**

1. **Resolución Visual Definitiva:**
   - La cabecera muestra el logotipo oficial IJF circular a color perfectamente renderizado.
   - El título *"Asistente SOR IJF"* se despliega en tipografía Outfit azul corporativo con su icono tooltip interactivo funcional.
   - El mensaje de bienvenida *"Bienvenido"* y subtítulo se presentan con sus estilos nativos.
   - **Cero código HTML literal en pantalla:** Eliminadas todas las etiquetas de texto `<div>`, `<h2>`, `<p>` y la cadena de 40 KB del logotipo Base64.
2. **Paridad Total de Ramas:**
   $$\text{HEAD local} = \text{origin/integration/ijf-sor-2026-08-merge} = \text{origin/main} = \texttt{20d6114734a8b88b8b84c0187f4fd45facbca7bd}$$
3. **Respaldo Pre-Despliegue Inmutable:** Creado en OCI en `/home/ubuntu/backups/pre_deploy_20d6114_20261108_091008/` con manifiesto SHA-256 de `.env` (600), feedback y código previo.
4. **Validaciones en Producción (En Vivo):**
   - **Playwright DOM Check:** 0 artefactos HTML sin procesar en el texto de la página en `https://sor.alxol.com`.
   - **Batería Soberana VF01 (11 casos ratificados por Alexis):** **11/11 PASS (100% OK)** en contenedor de producción.
   - **Batería Focal CGPT-06 (10 casos de Kumi-Kata):** **10/10 PASS (100% OK)** en contenedor de producción.
   - **Consulta Canónica Tatami:** Estado `SUCCESS`, evidencias recuperadas $\ge 5$, cumpliendo $K=5$, top `SOR-2026-08-P096-S114`.
   - **Consulta Fuera de Dominio Baloncesto FIBA (OOD):** Estado `ABSTAIN`, 0 evidencias, abstención normativa estricta activa.
   - **Integridad Criptográfica:** PDF, embeddings `.npy`, grafo `.json` y archivo de feedback intactos.
   - **Servicio y Salud:** Contenedor `ijf-sor-assistant` activo (`Up`), uso de memoria 11.6%, CPU 0.26%, HTTP 200 en `https://sor.alxol.com`.

---

## 2. DETALLE DE PROCEDIMIENTO Y COMMIT

### 2.1 Commit Local Exclusivo
- **Archivo Modificado:** Exclusivamente `app.py`.
- **Hash SHA-1:** `20d6114734a8b88b8b84c0187f4fd45facbca7bd`
- **Cambios Principales:**
  1. Normalización de 1.548 terminadores de línea corruptos `\r\r\n` (CRCRLF) a `\n` (LF estándar).
  2. Implementación de función defensiva `render_custom_html(html_content: str)` que delega en `st.html` para Streamlit $\ge 1.35.0$ con fallback a `st.markdown`.
  3. Desindentación a columna 0 de las llamadas multilínea en cabecera e introducción, eliminando la regla de CommonMark que forzaba su conversión a `<pre><code>`.

### 2.2 Publicación y Sincronización Remota
```bash
git push origin 20d6114:integration/ijf-sor-2026-08-merge
git push origin 20d6114:main
```
Ambas ramas remotas avanzaron linealmente y se encuentran idénticas al HEAD local.

### 2.3 Respaldo y Activación en OCI
- **Host:** `149.130.187.132` (Oracle Cloud Infrastructure).
- **Directorio de Backup:** `/home/ubuntu/backups/pre_deploy_20d6114_20261108_091008/`
- **Reinicio:** `docker compose restart streamlit` (tiempo de inactividad $< 2$ segundos).

---

## 3. RESULTADOS DE LAS PRUEBAS EN PRODUCCIÓN OCI

### 3.1 Inspección Automatizada de Interfaz (Playwright sobre `https://sor.alxol.com`)
```text
Navigating to https://sor.alxol.com ...
Saved scratch/prod_post_deploy_initial.png
LIVE VERIFICATION SUCCESS: Zero raw HTML artifacts found in page text!
Live rendered h2 title: 'Asistente SOR IJF'
Live rendered base64 SVG logo count: 1
Live rendered h1 intro: 'Bienvenido'
Submitting query: 'tatami' ...
Saved scratch/prod_post_deploy_query.png
ALL LIVE PLAYWRIGHT VERIFICATIONS PASSED!
```

### 3.2 Batería Soberana VF01 (11/11 PASS)
Ejecutada con `test_regression_11_cases.py` dentro del contenedor de producción:
- `VF01-01` (Medidas del tatami): `SOR-2026-08-P096-S114` **[PASS]**
- `VF01-07` (Acciones con cabeza Cadetes vs Senior): `SOR-2026-08-P188-S196`, `SOR-2026-08-P190-S197` **[PASS]**
- `VF01-09` (Continuación tras head diving): `SOR-2026-08-P190-S197` **[PASS]**
- `VF01-14` (Consecuencia técnica/disciplinaria cabeza): `SOR-2026-08-P166-S187`, `SOR-2026-08-P190-S197` **[PASS]**
- `VF01-23` (Reverse seoi-nage en senior): `SOR-2026-08-P189-S196` **[PASS]**
- `VF01-24` (Shido por no combatividad y segundos): `SOR-2026-08-P177-S193` **[PASS]**
- `VF01-25` (Congelación reglas LA28 - OOD): Estado `ABSTAIN` **[PASS]**
- `VF01-29` (No combatividad tachi-waza vs ne-waza): `SOR-2026-08-P177-S193` **[PASS]**
- `VF01-30` (Contraataque involuntario con cabeza): `SOR-2026-08-P190-S197` **[PASS]**
- `VF01-42` (Defending attack head-first - hansoku-make): `SOR-2026-08-P190-S197` **[PASS]**
- `VF01-48` (Kumikata, agarres no convencionales y sanciones): `SOR-2026-08-P182-S194`, `SOR-2026-08-P178-S194` **[PASS]**

### 3.3 Batería Focal CGPT-06 (10/10 PASS)
Ejecutada con `test_focal_cgpt06_queries.py` dentro del contenedor de producción:
- Casos 1 a 10 de Kumi-Kata validados con 100% de coherencia ontológica y mapeo al artículo 18.1.2 del reglamento SOR 2026.

### 3.4 Comprobación Fuera de Dominio (OOD Basketball FIBA)
- **Consulta:** *"cuáles son las dimensiones del tablero de baloncesto según la fiba"*
- **Estado Retornado:** `ABSTAIN`
- **KUNs / Pasajes Recuperados:** `0`
- **Texto:** ⚠️ *Abstención Normativa Oficial (14 August 2026 (Official))*.

---

## 4. INTEGRIDAD CRIPTOGRÁFICA Y SEGURIDAD

| Componente | SHA-256 en Producción OCI | SHA-256 Línea Base | Verificación |
| :--- | :--- | :--- | :---: |
| **PDF SOR 14-Aug-2026** | `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620` | Idéntico | **CERTIFICADO** |
| **Embeddings `.npy`** | `124ced95fb9e152ce586dec9f30a1eb98dc14ee385c0bc335a2055357f73a617` | Idéntico | **CERTIFICADO** |
| **Feedback de Usuarios** | `1390a6644984bdd5c73b4659b24f348caa41ad755836dd77bc102c5b7847052c` | 886 bytes | **PRESERVADO** |
| **Credenciales `.env`** | Permisos `600` (`-rw-------`, 274 bytes) | OCI Seguro | **PRESERVADO** |

---

## 5. COMPARATIVA VISUAL ANTES / DESPUÉS

- **Antes (`bcdfe7d` inicial):**
  - La cabecera se mostraba como un bloque gris `<pre><code>` que exponía las cadenas de código `<div style="...">`, `<img src="data:image/svg+xml;base64,...">` y la totalidad de los 40 KB de datos Base64 en texto plano.
  - La sección inferior mostraba `<h1 style="...">Bienvenido</h1>` y `<p style="...">...</p>` sin formatear.
- **Después (`20d6114` desplegado):**
  - Isotipo oficial circular IJF centrado y nítido.
  - Título estilizado en azul con tooltip interactivo con signo de interrogación.
  - Mensaje de bienvenida formateado y centrado sobre el fondo de la aplicación.
  - Barra de búsqueda interactiva y visor de PDF operativo.
  - Cero artefactos HTML visibles.

---

## 6. CONCLUSIÓN

El incidente post-deployment ha quedado **completamente resuelto y verificado en vivo**. El sistema se encuentra en un estado estable, robusto, performante y con plena fidelidad estética y normativa en `https://sor.alxol.com`.

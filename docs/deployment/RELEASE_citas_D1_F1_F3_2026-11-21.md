# Release 2026-11-21: citas UI, D1, F1 y F3 shadow

- **Producción:** `https://sor.alxol.com`.
- **Infraestructura:** Cloudflare Tunnel hacia el puerto 8501, con Docker Compose y el contenedor `ijf-sor-assistant`.

## Commit desplegado

- **Commit:** `40d7ac96ac09be449bafb18322bf98639f3fb07f`.
- **Rama de origen:** `exp/optimizacion-tokens`. El commit es hijo directo de `504cb23`.
- **`main` local:** avanzado por fast-forward a `40d7ac9`.
- **GitHub (`origin/main`):** sigue en `504cb23`. El push quedó bloqueado por el control de permisos de la sesión y está pendiente de que lo haga el responsable.
- **Cómo llegó al servidor:** con un git bundle (`/home/ubuntu/backups_ijf/deploy_40d7ac9.bundle`), seguido de `git merge --ff-only 40d7ac9` en `main`.

**Contenido.** Son 8 archivos, con 1735 líneas añadidas y 19 eliminadas:

| Archivos | Bloque |
|---|---|
| `app.py`, `src/response_structurer.py`, `src/citation_render.py` | Restauración de la UI de citas |
| `src/citation_render.py` | D1 |
| `src/reference_integrity.py` | F1 |
| `src/answer_verification.py` | F3, capa 1d en modo shadow |
| `tests/test_citation_render.py`, `tests/test_reference_integrity.py`, `tests/test_reference_integrity_shadow.py` | Pruebas |

- **Excluidos:** calidad-v4, la optimización de tokens y F4. Están preservados en `exp/consolidado-completo-2026-11-20` (`51e287a`).
- **Imagen:** la misma (`290ab72e6a7f`). No cambian `requirements.txt` ni el `Dockerfile`.

## Configuración

- **F3 shadow:** se añadió `ADA_REFERENCE_CHECK: "shadow"` en `docker-compose.override.yml`. Ese archivo está en el servidor, no está versionado y es donde ya estaban los flags de V4. Solo añade un registro y no altera la respuesta.
- **Por qué no está en `docker-compose.yml`:** el commit de ese cambio quedó bloqueado por el control de permisos.
- **Resto de flags:** sin cambios. `ADA_CITATION_UI` toma su valor por defecto, que es `1`.

## Respaldo (OCI)

- **Directorio:** `/home/ubuntu/backups_ijf/prod_504cb23_pre_citas_20261121_032846/`, copia íntegra con `.git`, `.env` (no leído) y el override. Se comprobó que es idéntica al original.
- **Archivos asociados:**
  - `…_032846.ESTADO.txt`, con el commit, la imagen y el motivo;
  - `…_032846.compose_resuelto.yml`, con permisos 600.
- **Imagen Docker:** `ijf-sor-assistant-streamlit:backup-504cb23`.
- **Tag Git en el servidor:** `backup/prod-504cb23`.

## Reversión

```bash
cd /home/ubuntu/IJF-SOR-Assistant
git reset --hard backup/prod-504cb23          # código anterior (504cb23)
cp /home/ubuntu/backups_ijf/prod_504cb23_pre_citas_20261121_032846/docker-compose.override.yml .
docker compose up -d                           # recrea con la misma imagen
```

**Reversiones parciales:**
- F3 shadow: borrar la línea `ADA_REFERENCE_CHECK` del override y ejecutar `docker compose up -d`.
- UI de citas: añadir `ADA_CITATION_UI: "0"` al override y ejecutar `docker compose up -d`.

**Reversión total:** detener el contenedor y restaurar el directorio de respaldo.

## Verificación (2026-11-21 UTC)

**Infraestructura**
- `/_stcore/health` responde 200.
- `https://sor.alxol.com` responde 200, con TLS válido.
- Contenedor `running`, 0 reinicios y unos 645 MiB de memoria.
- Logs sin errores, trazas ni fallos de importación.
- 8502 (NuevaMente) y 8510 (experimental) siguen respondiendo 200 y no se han tocado.

**Dentro del contenedor, sin modelos**
- Compilan los 5 módulos afectados.
- `pytest` de las 3 pruebas nuevas: 141 pasan. Los datos de usuario y el árbol de trabajo no cambiaron.
- D1: ninguna carga produce un `href` con `javascript:`, un `<img>` ni un dominio no autorizado.
- F3: `reference_check_mode()` devuelve `shadow` y el registro se genera sin errores, con `obj` intacto.

**Consultas reales (Gemini) en la web pública**

| # | Consulta | Resultado | Evaluación |
|---|---|---|---|
| 1 | Tolerancia en el pesaje aleatorio | 5 % del límite de la categoría; Art. 6.3.3, Pág. 79 | Correcta. Coincide con la referencia de v1.4.0 (P079) |
| 2 | Defensa con la cabeza en cadetes | Shido; Art. 18.1.4, Pág. 188 | Correcta. La píldora abre el visor en la Pág. 188 |
| 3 | Judogi: color del primer llamado y requisitos (pregunta compuesta) | Abstención del DIG (`no_responde_la_pregunta`) | Segura. La recuperación fue pertinente (C1.9, C1.1.5) y la decisión del DIG no ha cambiado en este despliegue |
| 3b | Judogi: colores permitidos y referencias | Blanco (*snow white*) y azul (Pantone 18-4051/18-4039 TCX, 285M–286M); judogi reversible prohibido; C1.9 Pág. 124 y C1.1 Pág. 115 | Correcta y literal frente al pasaje |
| 4 | Shidos que llevan a hansoku-make | Tres shidos; Art. 18.1 Pág. 176 y Art. 18.2 Pág. 190 | Correcta. Las referencias están resaltadas y enlazadas al PDF oficial `#page=N`, sin `javascript:` |
| 5 | Premios en dinero del Grand Slam de París 2027 | Abstención (`respuesta_negativa_con_cifras`) | Correcta: el SOR no lo documenta |
| D1 | Consulta con `[ver regla]( javascript:alert(1) )` e imagen externa | Abstención previa, sin llamar al modelo | 0 `href` con `javascript:` |

## Observaciones (no las introduce este despliegue)

- **Imagen en la pregunta del usuario.** El globo de la pregunta se muestra con `st.markdown(item['query'])` en `app.py`, igual que en `504cb23`. Si la pregunta incluye `![x](url)`, se carga una imagen externa en la sesión de ese usuario. El enlace `javascript:` sí queda neutralizado (`href="#"`). D1 cubre la salida del modelo, no la entrada del usuario. Se recomienda mostrar la pregunta como texto plano en un cambio aparte.
- **Fragmento doble en las tarjetas de evidencias.** Algunas URL tienen el fragmento repetido (`…pdf#page=79#page=79`). Los construye código que no ha cambiado (`rre_engine` y `evidence_reassembly`). Los distintivos y menciones nuevos usan un solo `#page=N`.
- **Destino de las menciones dentro de citas.** Una mención dentro de una frase enlaza a la página de la cita certificada de esa frase. Por ejemplo, «Article 18.1» citado desde la Pág. 190 lleva a la 190. Es el diseño aprobado.

## Actualización 2026-11-21: la consulta del usuario se muestra como texto literal (`0f86677`)

**Qué cambia**
- **Commit:** `0f86677582ae29f6f63393ca06e156917e06f4f4`, hijo de `40d7ac9`. Commit hecho por el responsable.
- **Archivos:** `app.py`, `src/citation_render.py` y `tests/test_citation_render.py` (+81/−3).
- **Efecto:** la consulta del usuario, y la consulta y el comentario de las observaciones en el panel de administración, se muestran como texto literal con `plain_text_html`. El CSS `.user-text` da altura automática y parte las líneas largas.
- Resuelve la primera observación de este documento.

**Respaldo**
- Directorio: `/home/ubuntu/backups_ijf/prod_40d7ac9_pre_usertext_20261121_034946/`, más sus archivos `.ESTADO.txt` y `.compose_resuelto.yml`.
- Imagen Docker `ijf-sor-assistant-streamlit:backup-40d7ac9` y tag Git `backup/prod-40d7ac9`.

**Despliegue:** con el bundle `deploy_0f86677.bundle`, `git merge --ff-only` y `docker compose restart`. La imagen y el override no cambian, y F3 sigue en modo shadow.

**Reversión**
- Ejecutar `git reset --hard backup/prod-40d7ac9` y después `docker compose restart streamlit`.

**Verificación**
- Infraestructura:
  - `/_stcore/health` y `https://sor.alxol.com` responden 200;
  - 0 reinicios y logs sin errores;
  - 8502 y 8510 siguen respondiendo 200 y no se han tocado.
- Dentro del contenedor: `test_citation_render.py` pasa entero (60 pruebas).
- Web pública:
  - **Consulta con Markdown, HTML y una fórmula** (escritorio): se muestra literal, con 0 imágenes, 0 enlaces, 0 fórmulas y 0 `href` con `javascript:`. Abstiene sin llamar al modelo.
  - **Consulta larga en móvil (375 px):** se ve completa en 8 líneas y la altura se ajusta, sin límite de altura ni scroll horizontal. La respuesta es correcta: Art. 18.1.4, shido, Pág. 188.

## Actualización 2026-11-21: textos de la barra lateral (`827c5db`)

**Qué cambia**
- **Commit:** `827c5db1531f222821ec93482e67f272e5790986`, hijo de `0f86677`. Commit hecho por el responsable.
- **Archivos:** `app.py`, `src/i18n/__init__.py`, `tests/test_sidebar_textos.py` y `docs/audits/AUDITORIA_BARRA_LATERAL_2026-11-21.md` (+351/−144).
- **Efecto:** aplica la propuesta de la auditoría de la barra lateral.
  - Orden nuevo: Idioma, Tema, Cómo usar el asistente, Acerca del asistente, Disponibilidad del servicio y Administración.
  - Se retiran afirmaciones incorrectas: cuota gratuita, modo local con respuestas continuas, sugerencias predefinidas, versión 3.2.0 y boletines como base de las respuestas.
  - La guía PDF desactualizada deja de enlazarse.
- **Alcance:** solo presentación. No cambian RRE, ADA, la recuperación, las citas, la verificación, las dependencias ni la imagen. `engine.config` solo se lee para mostrar la edición y la huella del PDF.

**Antes de desplegar**
- La pasarela de producción ya estaba en `0f86677`.
- **Pruebas:**
  - específicas (citas, barra lateral, i18n, controles de UI e integridad de referencias): 170 pasan;
  - suite completa sin el conjunto sellado: 844 pasan, 21 omitidas (por entorno: requieren bash o contexto SHADOW) y 2 deseleccionadas, en unos 127 s;
  - 17/17 hashes protegidos.
- **Datos tras las pruebas:** las pruebas reescriben `user_observations.jsonl` y `scratch/shadow_multisource_evaluation.jsonl`; se restauraron desde sus copias.

**Respaldo**
- Directorio: `/home/ubuntu/backups_ijf/prod_0f86677_pre_sidebar_20261121_050319/`. Copia idéntica salvo el tag creado después.
- Archivos asociados: `.ESTADO.txt` y `.compose_resuelto.yml` (permisos 600).
- Imagen `ijf-sor-assistant-streamlit:backup-0f86677` y tag Git `backup/prod-0f86677`.

**Despliegue**
- `main` local avanzó por fast-forward a `827c5db`.
- El bundle `deploy_827c5db.bundle` (rango `0f86677..main`) se aplicó con `git merge --ff-only` en el servidor, seguido de `docker compose restart streamlit`.
- La imagen y el override no cambian.

**Reversión**
- Ejecutar `git reset --hard backup/prod-0f86677` y después `docker compose restart streamlit`.

**Verificación**
- **Infraestructura:**
  - health 200 al segundo intento;
  - `https://sor.alxol.com` responde 200, con certificado de Google Trust Services válido hasta el 07-01-2027 (comprobado desde OCI);
  - 0 reinicios y logs sin errores;
  - 8502 y 8510 siguen respondiendo 200 y `cloudflared` está activo.
- **Dentro del contenedor:** pruebas de barra lateral, citas e i18n, 74 pasan. F3: `reference_check_mode()` devuelve `shadow` y el registro se genera sin errores.
- **Web pública:**
  - **Barra lateral (ES):** orden y 9 subtemas correctos; 0 enlaces; edición del 14 de agosto de 2026 y huella `9426b10d11c21a4c…`.
  - **Consulta corta:** «¿Cuántos shidos llevan a hansoku-make?» → tres shidos, Art. 18.1, Pág. 176. Correcta.
  - **Consulta con Markdown, HTML, URL y fórmula:** se muestra literal, con 0 imágenes, 0 enlaces, 0 negritas, 0 fórmulas y 0 `href` con `javascript:`. El asistente se abstiene.
  - **Consulta larga en móvil (375 px, 333 caracteres):** se ve completa en 10 líneas y la altura se ajusta, sin scroll horizontal. La respuesta es correcta: shido, Art. 18.1.4, Pág. 188.
- **Observación previa que sigue abierta:** el fragmento doble `#page=N#page=N` en algunas tarjetas de evidencias.

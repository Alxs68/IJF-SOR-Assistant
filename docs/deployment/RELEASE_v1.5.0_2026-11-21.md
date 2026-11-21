# Release v1.5.0 — IJF SOR Assistant 2026 (21-11-2026)

## Identificación

| Campo | Valor |
|---|---|
| Proyecto | IJF SOR Assistant |
| Línea | 2026 |
| Versión | **v1.5.0** |
| Fecha | 21 de noviembre de 2026 |
| Release anterior | v1.4.0 (18-11-2026, tag `v1.4.0` → `96906bd`) |
| Commit funcional desplegado | `dd4373442df743ca916d39b534d3bb19a30cbe79` (`dd43734`) |
| Commit documental anterior | `840ffb0` (`docs(deployment): releases del 2026-11-21`) |
| Edición del SOR | 14 de agosto de 2026 (oficial), sin cambios |

**Por qué v1.5.0.** Es una versión MINOR según SemVer:
- añade funcionalidades compatibles, como la consulta por voz y las citas interactivas;
- incluye correcciones;
- no tiene cambios incompatibles;
- conserva el historial existente, del tag `v1.1.0` al `v1.4.0`.

**Fuente única de la versión:** `src/app_version.py`. La barra lateral muestra «Versión 1.5.0 · actualizada el 21-11-2026», y los reportes de usuario registran `app_version: "1.5.0"`. Antes registraban `3.2.0`.

## Funcionalidades y cambios incluidos (desde v1.4.0)

1. **Consulta por voz** con la Web Speech API del navegador (`20f24e8`).
   - El texto dictado se añade al campo y nunca se envía solo.
   - El idioma sale del selector de la barra lateral: `es-CO` o `en-US`.
   - Se degrada de forma controlada si el navegador no lo admite.
   - La aplicación no graba ni guarda audio.
2. **Mejoras de interfaz y navegación:**
   - barra lateral reorganizada y con textos que corresponden al comportamiento real (`e2aacd0`, `827c5db`);
   - consulta del usuario como texto literal (`0f86677`);
   - solo las evidencias que usa la respuesta (`504cb23`);
   - citas interactivas con enlace a la página del PDF (`40d7ac9`).
3. **Corrección de enlaces PDF con el fragmento de página duplicado** (`dd43734`).
   - **Causa:** `ReferenceManager.resolve_reference` añadía `#page=N` a un `source_url` que ya lo traía.
   - **Detalle:** `RELEASE_pdf_page_fragmento_2026-11-21.md`.
4. **Mejoras operativas y validaciones:**
   - verificación de respuestas V4 frase a frase (`37aa475`, `f59af92`);
   - seguridad del Markdown D1;
   - integridad de referencias F1;
   - capa F3 en modo shadow, que solo registra (`40d7ac9`);
   - respaldo verificado y bundle con fast-forward en cada despliegue.
5. **Se conservan sin cambios:**
   - la arquitectura de recuperación (RRE) y ADA;
   - el corpus SOR 2026-08 y los embeddings;
   - `requirements.txt` y el `Dockerfile` (sin cambios entre `v1.4.0` y `dd43734`), y la imagen Docker (`290ab72e6a7f`).

**Detalle de cada despliegue:**
- `RELEASE_citas_D1_F1_F3_2026-11-21.md`: `40d7ac9`, `0f86677` y `827c5db`;
- `RELEASE_consulta_voz_2026-11-21.md`: `20f24e8`;
- `RELEASE_pdf_page_fragmento_2026-11-21.md`: `dd43734`.

## Validaciones

**Comprobado en las sesiones de despliegue del 21-11-2026**

| Validación | Resultado |
|---|---|
| Producción | `dd43734` desplegado en OCI (`https://sor.alxol.com`) |
| Health check | HTTP 200 |
| HTTPS | 200. Certificado de Google Trust Services válido hasta el 07-01-2027 |
| Contenedor | Activo, 0 reinicios, logs sin errores |
| Enlaces PDF | 61 examinados en 6 consultas, 0 con el fragmento duplicado (páginas 79, 176, 188, 190 y 194 incluidas) |
| Regresión funcional | Satisfactoria. Correctas: shidos (Pág. 176), pesaje 5 % (Pág. 79), cadete y cabeza (Art. 18.1.4, Pág. 188), consulta en inglés (Pág. 152), judogi (Pág. 124) y consulta dictada (Pág. 152) |
| Consulta por voz | Validada con reconocimiento simulado: estados, sin envío automático, envío manual, cambio de idioma ES↔EN, temas y móvil. La API real del navegador responde, con permiso denegado en el entorno de prueba |
| Suite de pruebas | 878 pasan, 21 omitidas por entorno, sin el conjunto sellado (en `dd43734`) |

**Informado por el responsable, sin registro verificable en estas sesiones**

| Validación | Estado |
|---|---|
| Micrófono real en Chrome de escritorio | Realizada, según el responsable |
| Micrófono real en Android | Realizada, según el responsable |

## Producción

- Este release no implica un despliegue nuevo: producción ya ejecuta `dd43734`.
- Los cambios del commit de v1.5.0 son metadatos de versión y documentación: `src/app_version.py`, etiqueta de la barra lateral, `app_version` de los reportes, README, CHANGELOG y este documento.
- Para que la barra lateral de producción muestre «Versión 1.5.0» hay que desplegar ese commit con el procedimiento habitual (bundle, `merge --ff-only` y reinicio). No cambia la imagen ni la configuración.

**Reversión** (si se despliega el commit de versión): `git reset --hard dd43734` y después `docker compose restart streamlit`. El respaldo más reciente de `20f24e8` está en `/home/ubuntu/backups_ijf/prod_20f24e8_pre_pdfpage_20261121_063214/`.

## Tag

Se crea un tag anotado `v1.5.0` sobre el commit de este release, que contiene el código de `dd43734` y la documentación de versión. Los tags anteriores no se modifican.

## Despliegue de v1.5.0 en OCI (21-11-2026, 07:06:01 UTC)

**Commits**
- **Anterior:** `dd4373442df743ca916d39b534d3bb19a30cbe79`.
- **Desplegado:** `95a06032f477638169d61a547eb64cad2c870b75`. Es el tag anotado `v1.5.0` y coincide con `origin/main` en GitHub.
- **Diferencia** (10 archivos, +576/−6):
  - el commit documental `840ffb0`;
  - los metadatos de versión de `95a0603`.
- **Sin cambios:** la imagen (`290ab72e6a7f`, sin reconstruir), `docker-compose.yml`, el override y las variables de entorno. F3 sigue en modo shadow.

**Respaldo**
- **Directorio:** `/home/ubuntu/backups_ijf/prod_dd43734_pre_v150_20261121_070432/`. Copia idéntica (`diff -rq`), con `git fsck` correcto y 690 MB. Incluye `.git`, el override y `.env` (no leído).
- **Archivos asociados:** `…_070432.ESTADO.txt` y `…_070432.compose_resuelto.yml` (permisos 600).
- **Imagen Docker:** `ijf-sor-assistant-streamlit:backup-dd43734`.
- **Tag Git:** `backup/prod-dd43734`.

**Procedimiento**
1. Bundle `deploy_95a0603.bundle` (rango `dd43734..main`), con SHA-256 `789a8b9a…` verificado en ambos extremos.
2. Se comprobó que la referencia recibida es exactamente `95a0603` y que desciende de `dd43734`.
3. `git merge --ff-only`, seguido de `docker compose restart streamlit`. Health 200 al segundo intento.

**Validación técnica**
- Health 200 y HTTPS 200.
- Certificado de Google Trust Services válido hasta el 07-01-2027.
- Contenedor en ejecución, 0 reinicios.
- Logs sin trazas de error ni excepciones, y sin `#page=N#page=`.
- 8502 y 8510 responden 200, y `cloudflared` está activo.
- Pruebas en el contenedor (versión, barra lateral, enlaces PDF, voz, reportes): 57 pasan.

**Validación de la versión**
- La barra lateral de la web pública muestra «Versión 1.5.0 · actualizada el 21-11-2026».
- No aparece ninguna numeración antigua («3.2.0», «Versión 3.0»).
- En el contenedor, `APP_VERSION = "1.5.0"`. `app.py` toma la etiqueta y `"app_version": APP_VERSION` de esa fuente.
- **Reportes de usuario:** se comprobó en el código desplegado y con la prueba `test_app_version`. No se envió ningún reporte real, para no escribir datos de prueba en producción.

**Regresión funcional** (web pública, consultas reales con Gemini)

| Consulta | Respuesta | Enlaces PDF | Duplicados |
|---|---|---|---|
| Shidos que llevan a hansoku-make | Tres shidos, Pág. 176 | 11 | 0 |
| Tolerancia del pesaje aleatorio | 5 %, Pág. 79 | 10 | 0 |
| Cadete: defensa con la cabeza | Shido, Pág. 188 | 13 | 0 |
| Colores de judogi | Blanco y azul (Pantone), Pág. 124 | 18 | 0 |
| *How long is a senior contest?* | 4 minutos, Pág. 152 (resumen en inglés, literal del SOR) | 10 | 0 |
| Dictada por voz (simulada): osaekomi para ippon | 20 s, Pág. 152 | 11 | 0 |

**Voz**
- Control disponible en contexto seguro, con la API nativa presente, en `es-CO`.
- El dictado añade el texto al campo y no lo envía: tras 3 s no se había enviado nada.
- El envío manual con Enviar responde correctamente. Después, el campo se vacía y el control vuelve a inactivo.
- No se usó micrófono físico (no hay hardware en este entorno).

**Estado final:** producción en `95a0603` (v1.5.0), con el árbol de trabajo limpio.

**Reversión a `dd43734`**

```bash
cd /home/ubuntu/IJF-SOR-Assistant
git reset --hard backup/prod-dd43734
docker compose restart streamlit
curl -s -o /dev/null -w "%{http_code}
" http://127.0.0.1:8501/_stcore/health   # 200
```

**Reversión total:** detener el contenedor, restaurar `/home/ubuntu/backups_ijf/prod_dd43734_pre_v150_20261121_070432/` y ejecutar `docker compose up -d`. La imagen `backup-dd43734` es la misma que `latest`.


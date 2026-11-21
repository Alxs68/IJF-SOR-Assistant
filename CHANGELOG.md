# Historial de versiones — IJF SOR Assistant 2026

Versionado semántico (SemVer):
- **MAJOR:** cambios incompatibles o transformaciones importantes.
- **MINOR:** funcionalidades nuevas compatibles.
- **PATCH:** correcciones puntuales.

La versión de la aplicación está en `src/app_version.py`. La barra lateral la muestra y los reportes de usuario la registran. Es independiente de la edición del SOR (`corpus_config.version_label`, 14 de agosto de 2026).

## v1.5.0 — 2026-11-21

- **Commit funcional desplegado:** `dd43734`.
- **Release anterior:** v1.4.0.
- **Detalle:** [`docs/deployment/RELEASE_v1.5.0_2026-11-21.md`](docs/deployment/RELEASE_v1.5.0_2026-11-21.md).

**Añadido**
- Consulta por voz con la Web Speech API del navegador. La transcripción se añade al campo y nunca se envía sola (`20f24e8`).
- Verificación de respuestas V4, frase a frase (`37aa475`, `f59af92`).
- Citas interactivas en la respuesta, con enlace a la página del PDF oficial (`40d7ac9`).
- Integridad de referencias F1 y capa F3 en modo shadow, que solo registra (`40d7ac9`).

**Cambiado**
- La barra lateral se reorganiza; sus textos corresponden al comportamiento real y la versión es visible (`e2aacd0`, `827c5db`).
- Se muestran solo las evidencias que usa la respuesta (`504cb23`).
- La consulta del usuario se muestra como texto literal, con altura automática (`0f86677`).

**Corregido**
- Los enlaces PDF tenían el fragmento de página duplicado (`#page=N#page=N`) (`dd43734`).
- Seguridad del Markdown de la respuesta (D1) (`40d7ac9`).
- Contraste del campo de página del visor PDF (`e2aacd0`).

**Sin cambios:** la arquitectura de recuperación (RRE), el corpus SOR 2026-08, los embeddings, las dependencias y la imagen Docker.

## v1.4.0 — 2026-11-18

Se activan en producción las mejoras validadas de recuperación y generación: R1, DIG v2 y v3, R5a y R5b, JSON con esquema, respuesta unificada y R2. Detalle en [`docs/deployment/RELEASE_v1.4.0_2026-11-18.md`](docs/deployment/RELEASE_v1.4.0_2026-11-18.md).

## Versiones anteriores (tags Git)

| Versión | Fecha | Commit | Resumen |
|---|---|---|---|
| v1.3.0 | 2026-07-30 | `8dbf5eb` | MCP: herramientas Git de solo lectura (fase 3) |
| v1.2.1-oficial | 2026-07-30 | `103cc93` | MCP: auditoría administrativa y README |
| v1.2.0 | 2026-07-25 | `e7faae4` | Política de autonomía y gobernanza |
| v1.1.0 | 2026-07-24 | `cbfda90` | Corrección de las fuentes KUN piloto y caché del grafo |

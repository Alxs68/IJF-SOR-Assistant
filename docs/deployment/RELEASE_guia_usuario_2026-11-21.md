# Despliegue de la guía de uso v1.5.0 — IJF SOR Assistant (21-11-2026)

## Identificación

| Campo | Valor |
|---|---|
| Versión de la aplicación | v1.5.0 (sin cambio de versión) |
| Commit anterior en producción | `95a06032f477638169d61a547eb64cad2c870b75` (`95a0603`, tag `v1.5.0`) |
| Commit desplegado | `05e71576aafca3a4495f4148da76b8b677a8f04a` (`05e7157`) |
| Fecha del despliegue | 21-11-2026, reinicio a las 08:31:56 UTC |
| GitHub `main` | `05e7157` |

## Cambios incluidos (`95a0603..05e7157`)

1. `6c60f61`: registro documental del despliegue de v1.5.0.
2. `b2f0d21`: guía de usuario v1.5.0.
   - Sustituye a la guía 3.2.0, que tenía la versión y la huella SHA-256 incorrectas y describía funciones que no existen.
   - PDF de 8 páginas (SHA-256 `aeaae0d2b3140c53…`) con capturas reales de producción.
   - Fuente editable y script de generación en `docs/guides/fuente/`.
   - Guía 3.2.0 archivada en `docs/guides/archivo/` (SHA-256 `4f83d71b11f92aff…`).
3. `726365b`: `.gitattributes` con `*.pdf binary`.
   - Con `core.autocrlf=true`, Git trataba como texto el PDF archivado y lo dañaba al extraerlo.
4. `05e7157`: botón «📥 Guía de uso (PDF)» en «Acerca del asistente».
   - En inglés: «📥 User guide (PDF, in Spanish)».
   - Descarga `IJF_SOR_Assistant_Guia_de_uso_v1.5.0.pdf`.

**Sin cambios:** RRE, ADA, F3 (sigue en modo shadow), corpus, embeddings, dependencias, imagen Docker (`290ab72e6a7f`), configuración y variables de entorno.

## Validación previa

- Suite completa: 882 pasan y 21 omitidas por entorno, sin el conjunto sellado.
- App local: botón visible en español e inglés y en tema claro y oscuro. La descarga coincide con el PDF oficial.

## Respaldo

- **Directorio:** `/home/ubuntu/backups_ijf/prod_95a0603_pre_guia_20261121_082858/`.
  - Copia idéntica (`diff -rq`) con `git fsck` correcto, 690 MB.
  - Junto a él, `.ESTADO.txt` y `.compose_resuelto.yml` (permisos 600).
- **Imagen Docker:** `ijf-sor-assistant-streamlit:backup-95a0603`.
- **Tag Git:** `backup/prod-95a0603`, que apunta a `95a0603`.

## Procedimiento

1. Bundle `deploy_05e7157.bundle` con el rango `95a0603..main` y 4 commits. SHA-256 `da23b949…`, verificado en ambos extremos.
2. Se comprobó que la referencia recibida es `05e7157` y que desciende de `95a0603`.
3. `git merge --ff-only`, seguido de `docker compose restart streamlit`.

## Validación en producción

| Validación | Resultado |
|---|---|
| Health check y HTTPS | 200 |
| Contenedor | En ejecución, 0 reinicios |
| Logs | Sin errores ni enlaces `#page=N#page=` |
| Otros servicios | 8502 y 8510 responden 200; `cloudflared` activo |
| Pruebas en el contenedor | 45 pasan (barra lateral, versión, voz, enlaces PDF) |
| Botón de la guía | En «Acerca del asistente», antes de «Disponibilidad del servicio». Comprobado en español y tema claro, y en inglés y tema oscuro |
| Descarga | `IJF_SOR_Assistant_Guia_de_uso_v1.5.0.pdf`, 8 páginas, SHA-256 `aeaae0d2b3140c53…`, igual que el oficial |
| PDF en el servidor | Guía `aeaae0d2…` y archivada `4f83d71b…`; `.gitattributes` con `*.pdf binary` |

**Regresión** (web pública, consultas reales)

| Consulta | Respuesta | Enlaces PDF | Duplicados |
|---|---|---|---|
| Shidos que llevan a hansoku-make | Tres shidos, Pág. 176 | 12 | 0 |
| Tolerancia del pesaje aleatorio | 5 %, Pág. 79 | 8 | 0 |
| Cadete que defiende con la cabeza | Shido, Pág. 188 | 13 | 0 |

## Reversión a `95a0603`

No ha hecho falta ejecutarla.

```bash
cd /home/ubuntu/IJF-SOR-Assistant
git reset --hard backup/prod-95a0603
docker compose restart streamlit
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8501/_stcore/health   # 200
```

**Reversión total:** detener el contenedor, restaurar el directorio de respaldo y ejecutar `docker compose up -d`. La imagen `backup-95a0603` es la misma que `latest`.

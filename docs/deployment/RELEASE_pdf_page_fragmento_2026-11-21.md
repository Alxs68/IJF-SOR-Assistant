# Release 2026-11-21: fragmento de página PDF único (`dd43734`)

- **Producción:** `https://sor.alxol.com`.
- **Infraestructura:** Cloudflare Tunnel hacia el puerto 8501, con Docker Compose y el contenedor `ijf-sor-assistant`.
- **Commit anterior:** `20f24e85128202892cba3dab7d65a6c54e266c71` (consulta por voz).
- **Commit desplegado:** `dd4373442df743ca916d39b534d3bb19a30cbe79`, hijo directo de `20f24e8`. Commit hecho por el responsable.
- **Despliegue:** 2026-11-21 06:36:32 UTC.

## Defecto

Algunos enlaces al PDF oficial tenían el fragmento de página repetido, por ejemplo `…IJF_Sport_and_Organisation_Rul-1787430903.pdf#page=190#page=190`. Aparecían en la pestaña de trazabilidad de cada respuesta y en las citas `[KUN-…]`.

## Causa raíz

1. `rre_engine` y `evidence_reassembly` guardan `source_url` con `#page=N` ya incluido.
2. `rag_engine` pasa ese campo tal cual a la trazabilidad de la respuesta.
3. `ReferenceManager.resolve_reference`, en la rama del SOR 2026-08 de `src/reference_manager.py`, volvía a concatenar `#page={pdf_page_index}`.

**Rutas no afectadas:**
- Las tarjetas de evidencias no construyen enlaces.
- Las píldoras de citas (`citation_render.sor_page_url`) ya reconstruían la URL sin fragmento.
- Las demás ramas del RRM sustituían el fragmento en lugar de añadirlo.

## Corrección

`src/reference_manager.py` (+43/−1) añade la función `pdf_page_url(url, page)`, que usa solo la rama del SOR de `resolve_reference`. La función:
- deja un único `#page=N`;
- da prioridad a la página de la evidencia sobre cualquier `page=` previo, duplicados incluidos;
- si no hay página, conserva la que ya trajera la URL y no inventa ninguna. Descarta `page=None`;
- mantiene la consulta (`?a=b`) y los demás parámetros del fragmento;
- no cambia las URL que no son PDF.

**Sin cambios en:** RRE, ADA, recuperación, embeddings, corpus, citas semánticas, generación de respuestas, i18n, consulta por voz, dependencias, imagen (`290ab72e6a7f`) y override. F3 sigue en modo shadow.

## Pruebas

- **`tests/test_pdf_page_url.py`** (nuevo, 27 casos):
  - URL sin fragmento, con fragmento correcto, duplicado y con otra página;
  - con consulta y con otros parámetros del fragmento;
  - sin página, con `page=None` y con caracteres especiales;
  - URL que no es PDF, vacía o `None`;
  - idempotencia;
  - la ruta real de la pestaña de trazabilidad para las páginas 79, 176, 188, 190 y 194;
  - `resolve_url`, `format_citations` y las demás ramas del RRM.
- **En local:**
  - pruebas relacionadas (gestor de referencias, citas, integridad de referencias, voz, barra lateral, i18n): 206 pasan;
  - suite completa sin el conjunto sellado: 878 pasan, 21 omitidas (por entorno) y 2 deseleccionadas;
  - hashes protegidos: 17/17.
- **Dentro del contenedor en producción:** 101 pasan (enlaces PDF, gestor de referencias, voz y citas).

## Respaldo (OCI)

- **Directorio:** `/home/ubuntu/backups_ijf/prod_20f24e8_pre_pdfpage_20261121_063214/`. Copia idéntica (`diff -rq`), con `git fsck` correcto y 690 MB. Incluye `.git`, el override y `.env` (no leído).
- **Archivos asociados:** `…_063214.ESTADO.txt` y `…_063214.compose_resuelto.yml` (permisos 600).
- **Imagen Docker:** `ijf-sor-assistant-streamlit:backup-20f24e8`.
- **Tag Git:** `backup/prod-20f24e8`.

## Procedimiento

1. **En local:** `main` avanzó por fast-forward a `dd43734`. Se creó el bundle `deploy_dd43734.bundle` (rango `20f24e8..main`).
2. **Transferencia:** SHA-256 del bundle verificado en ambos extremos (`70731504…`). `git bundle verify` correcto.
3. **Recepción:** la referencia `refs/deploy/dd43734` apunta exactamente a `dd4373442df7…`. Diferencia: 2 archivos, +122/−1.
4. **Actualización:** `git merge --ff-only`. HEAD queda en `dd43734` y el árbol, limpio.
5. **Reinicio:** `docker compose restart streamlit`. Health 200 al tercer intento.

## Verificación en producción

**Infraestructura**
- Health 200 y `https://sor.alxol.com` 200.
- Certificado de Google Trust Services válido hasta el 07-01-2027 (comprobado desde OCI).
- Contenedor en ejecución, 0 reinicios.
- Logs sin trazas de error ni excepciones; 0 apariciones de `#page=N#page=`.
- 8502 y 8510 responden 200, y `cloudflared` está activo.

**Web pública** (consultas reales con Gemini)

| Consulta | Respuesta | Enlaces PDF | Duplicados |
|---|---|---|---|
| Shidos que llevan a hansoku-make | Tercer shido = hansoku-make, Pág. 176 | 10 (176, 190, 194, 188…) | 0 (antes: `#page=190#page=190` y `#page=194#page=194`) |
| Tolerancia del pesaje aleatorio | 5 %, Pág. 79 | 9 | 0 |
| Cadete: defensa con la cabeza | Shido, Art. 18.1.4, Pág. 188 | 13 | 0 |
| *How long is a senior contest?* | 4 minutos, Pág. 152 | 10 | 0 |
| Colores de judogi | Blanco y azul (Pantone), Pág. 124 | 8 | 0 |
| Dictada por voz (simulada): osaekomi para ippon | 20 s, Pág. 152 | 11 | 0 |

- Las cinco páginas pedidas (79, 176, 188, 190 y 194) aparecen con la URL base intacta y un solo `#page=N`.
- 0 enlaces `javascript:`.
- **Voz:**
  - control disponible, en `es-CO`;
  - el dictado añade el texto al campo sin enviarlo;
  - el envío manual responde correctamente.
- **No verificado:** el reconocimiento con un micrófono físico, por la misma limitación que en el release anterior.

## Reversión a `20f24e8`

```bash
cd /home/ubuntu/IJF-SOR-Assistant
git reset --hard backup/prod-20f24e8
docker compose restart streamlit
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8501/_stcore/health   # 200
```

**Reversión total:** detener el contenedor, restaurar `/home/ubuntu/backups_ijf/prod_20f24e8_pre_pdfpage_20261121_063214/` y ejecutar `docker compose up -d`. La imagen `backup-20f24e8` es la misma que `latest`.

## Pendientes

- **GitHub:** sigue en `504cb23`. El push no es posible desde esta sesión por el control de permisos.
- **Documentos de release sin commit:** este y los dos anteriores.
- **Micrófono real:** comprobación manual en Chrome (escritorio y Android).

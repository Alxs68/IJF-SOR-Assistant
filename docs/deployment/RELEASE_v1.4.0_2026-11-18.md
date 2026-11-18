# Release v1.4.0 — IJF SOR Assistant 2026 (18-11-2026)

Supersede el estado de despliegue de `PRODUCTION_MANIFEST.md` (que describía `61afc1b` bajo systemd).

## Estado anterior (respaldo)

- Producción OCI `https://sor.alxol.com` (Cloudflare Tunnel → `0.0.0.0:8501`), Docker Compose, contenedor
  `ijf-sor-assistant`, imagen `ijf-sor-assistant-streamlit`, código montado desde `/home/ubuntu/IJF-SOR-Assistant`.
- Commit en producción antes de v1.4.0: `bb1d32d` (tag `backup/prod-bb1d32d`).
- Copia íntegra del directorio: `/home/ubuntu/backups_ijf/prod_bb1d32d_20261118_195345`.
- Imagen etiquetada: `ijf-sor-assistant-streamlit:backup-bb1d32d` (misma imagen; `requirements.txt` y `Dockerfile` sin cambios).

## Mejoras incorporadas (activadas en `docker-compose.yml`, cada una reversible con `"0"`)

| Flag | Mejora | Evidencia |
|---|---|---|
| `RRE_CHANNEL_CHAMPIONS=1` | R1: reserva del mejor pasaje de cada canal (denso/TF-IDF) en el paquete K=5 | `data/eval/fix3/r1_channel_champions_dev.json` (48→52/62, 0 pérdidas) |
| `DIG_NUMBER_NORMALIZATION=v2` | DIG v2: normalización de cifras/referencias | `docs/audits/INTEGRACION_R3_DIG_V2.md` |
| `DIG_V3=1` | DIG v3: evidencia normativa y atribución (encabezados, guiones, DIG-08) | `docs/audits/INFORME_CORRECCIONES_POST_EVALUACION_AB.md` |
| `DIG_11_SUBORDINATE=1` | R5a: apartados subordinados | `docs/audits/INFORME_INTERVENCION_RECUPERACION_GENERACION_DIG11.md` |
| `DIG06_REFS=1` | R5b: remisiones/referencias no cuentan como cifras afirmadas | ídem |
| `LLM_JSON_MODE=1`, `LLM_JSON_SCHEMA=1` | Salida JSON con esquema (elimina DIG-00 por JSON malformado) | ídem A/B |
| `ADA_UNIFIED_ANSWER=1` | Respuesta única con contexto consolidado al LLM | A/B Gemini 14→18 correctas |
| `ADA_TRANSLATE_ANY_LANG=1` | R2: traducción fiel de consultas en cualquier idioma | — |

Excluidas: preferencia de ámbito R3 (`RRE_ENABLE_SCOPE_PREFERENCE=0`, regresión en remisiones), regla 14
(`ADA_PROMPT_RIGOR`), unidades por apartado, agregación por ventanas, expansión de reglas, DIG-09 R5c, NLI shadow.
DIG-05/DIG-09 sin cambios. `test_sealed` no se abre (las dos pruebas que lo cargan se deseleccionan).

## Pruebas

`pytest tests` (con `--deselect` de `test_fase10_experimental.py::test_test_sealed_requires_explicit_flag` y
`::test_eval_scripts_refuse_sealed_without_flag`), sin claves LLM:

- flags por defecto: 589 passed, 21 skipped;
- flags de producción v1.4.0: 588 passed, 22 skipped.

Ajustes de pruebas: fijan el modo que verifican (réplicas grabadas antes de R5a/R5b; simulación de dos llamadas
HTTP sin R2), el caso del puente (Art. 14.2) se exige con R1 en K=5 (K canónico DEC-009; con k=4 R1 desplaza P167)
y la abstención por validación de citas se acepta como salida segura.

Limitación conocida: con R1, un pasaje desplazado de las semillas puede seguir en el prompt como tramo cosido;
si el modelo lo cita, la validación de citas abstiene (por el lado seguro).

## Reversión

```bash
cd /home/ubuntu/IJF-SOR-Assistant
git checkout bb1d32d          # o: poner a "0" los flags en docker-compose.yml
docker compose up -d          # recrea el contenedor con la misma imagen
```

Reversión total: detener el contenedor y restaurar `/home/ubuntu/backups_ijf/prod_bb1d32d_20261118_195345`.

## Despliegue y verificación (18-11-2026)

- Producción actualizada a `96906bd` (tag `v1.4.0`) con `git merge --ff-only origin/main` y `docker compose up -d`
  (misma imagen). El CSV no versionado `docs/registro_documental_multifuente_ijf.csv` de producción, que chocaba
  con el versionado, se apartó junto al respaldo (`…_195345.registro_documental_multifuente_ijf.untracked.csv`).
- Salud `/_stcore/health` 200 a los ~10 s; `https://sor.alxol.com` 200; 0 reinicios; ~620 MiB; sin errores en logs.
  Flags activos verificados en el contenedor; `DIG-1.3+NUM-v2+FIX-v3+ALL+D11S+D06R`; corpus sin cambios. Puerto 8502
  (NuevaMente) e instancia experimental 8510 sin tocar.
- UI pública: consulta de cadetes y defensa con la cabeza → respuesta única verificada, Art. 18.1.4 (p. 188).

Consultas reales (Gemini) en v1.4.0 frente a la versión anterior `bb1d32d` (contenedor temporal aislado del respaldo):

| Consulta | `bb1d32d` (sin DIG) | `v1.4.0` |
|---|---|---|
| Tolerancia en pesaje aleatorio | Responde, cita P079 (5 %) | Responde, cita P079 (5 %) |
| Portugués: cabeza para defender | Responde (P166, P188) | Responde (P188, cadetes) |
| Uke aterriza sobre Tori (Art. 14.2) | Responde (P167) | Recupera P167; abstiene por DIG-07 |
| ¿Existe el yuko en 2026? | Responde (P168) | Abstiene por DIG-06/DIG-07 |
| Fuera de dominio (paella) | Abstiene | Abstiene |

`bb1d32d` no tenía el control de integridad decisoria (`src/decision_integrity.py` entra en `main` con esta
versión): v1.4.0 solo acepta respuestas cuyo respaldo verifica el DIG, por lo que abstiene en casos que la versión
anterior respondía sin verificar. El DIG no se ha relajado.

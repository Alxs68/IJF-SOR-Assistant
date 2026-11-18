# Correcciones de la auditoria de trazabilidad (FIX3): UNA corrida A/B por ejecucion, SOLO con Gemini.
#   powershell -ExecutionPolicy Bypass -File scripts\run_eval_fix3.ps1 -Corrida 1
# Para la corrida 2 se vuelve a ejecutar a mano con -Corrida 2 (nunca continua sola).
# No toca produccion, ni el .env, ni claves persistentes, ni el benchmark sellado; no hace commit.
param([int]$Corrida = 1)
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot\..
$log = "data\eval\fix3\logs"; New-Item -ItemType Directory -Force $log | Out-Null
$out = "data\eval\fix3\ab_fix3_run$Corrida.json"
if (Test-Path $out) { Write-Host "ABORTO: ya existe $out (no se sobrescribe). Use otro -Corrida."; exit 1 }

# ---- 1. Pruebas SIN claves reales. Las claves se fijan VACIAS solo en esta sesion: src/llm_provider.py rellena
#         desde el .env las que no existen; vacias no las sustituye. tests/conftest.py ademas bloquea la red.
$env:GEMINI_API_KEY = ""; $env:GOOGLE_API_KEY = ""; $env:GROQ_API_KEY = ""
Remove-Item Env:ADA_UNIFIED_ANSWER, Env:RRE_CHANNEL_CHAMPIONS, Env:ADA_TRANSLATE_ANY_LANG, Env:DIG_11_SUBORDINATE, Env:DIG06_REFS, Env:LLM_JSON_SCHEMA, Env:ADA_PROMPT_RIGOR -ErrorAction SilentlyContinue
Write-Host "==== 1. Pruebas nuevas (sin claves; red de proveedores bloqueada)"
$t1 = python -m pytest tests\test_aislamiento_proveedores.py tests\test_fix_trazabilidad.py tests\test_unified_answer.py tests\test_unified_dig.py -q -p no:cacheprovider 2>&1 | Select-Object -Last 3
$t1 | Tee-Object "$log\01_tests_nuevos_run$Corrida.log"
if (($t1 -join " ") -match "\d+ failed|\d+ errors?\b" -or -not (($t1 -join " ") -match "\d+ passed")) { Write-Host "ABORTO: fallan pruebas nuevas"; exit 2 }

Write-Host "==== 2. Suite completa (solo pueden fallar los 6 fallos conocidos)"
$known = @(
  "tests/test_evaluation_battery.py::test_generator_success_is_backed_by_pertinent_evidence[D01]",
  "tests/test_evaluation_battery.py::test_generator_success_is_backed_by_pertinent_evidence[D04]",
  "tests/test_golden_dataset.py::TestGoldenDataset::test_golden_dataset_retrieval",
  "tests/test_response_structurer.py::TestResponseStructurerTransversal::test_06_ada_analyze_situation_two_tier_contract",
  "tests/test_rre_ada_architecture.py::TestRREAndADAArchitecture::test_07_llm_output_accepts_citation_from_retrieved_evidence",
  "tests/test_rre_ada_architecture.py::TestRREAndADAArchitecture::test_09_rag_engine_separation_for_2026_08")
$t2 = python -m pytest tests -q -p no:cacheprovider -rfE 2>&1
$t2 | Select-Object -Last 14 | Tee-Object "$log\02_suite_run$Corrida.log"
$fails = $t2 | Where-Object { $_ -match "^(FAILED|ERROR) " } | ForEach-Object { ($_ -replace "^(FAILED|ERROR) ", "") -replace " - .*$", "" }
$nuevos = $fails | Where-Object { $known -notcontains $_ }
if ($nuevos) { Write-Host "ABORTO: fallos nuevos en la suite:"; $nuevos | Write-Host; exit 2 }

# ---- 3. Recuperacion R1 (sin LLM; sigue sin claves)
$env:DIG_V3="1"; $env:LLM_JSON_MODE="1"; $env:RRE_ENABLE_SCOPE_PREFERENCE="1"; $env:RRE_SCOPE_BETA="0.2"; $env:DIG_NUMBER_NORMALIZATION="v2"
if ($Corrida -eq 1) {
  Write-Host "==== 3. R1 recuperacion con y sin campeones de canal (sin LLM)"
  python scripts\eval_r1_channel_champions.py 2>&1 | Select-Object -Last 30 | Tee-Object "$log\03_r1_recuperacion.log"
}

# ---- 4. Solo ahora se carga la clave de Gemini (en esta sesion). Groq queda VACIA: no puede usarse.
$env:GEMINI_API_KEY = ((Get-Content .env | Where-Object { $_ -match '^\s*GEMINI_API_KEY\s*=' }) -split '=',2)[1].Trim()
$env:GROQ_API_KEY = ""
Write-Host "==== 4. Disponibilidad de Gemini (1 llamada; Groq no se consulta)"
python scripts\check_llm_quota.py --proveedores Gemini 2>&1 | Tee-Object "$log\04_cuota_run$Corrida.log"

# ---- 5. Saldo: solo si el responsable lo lee en AI Studio > Facturacion (fuente verificable); nunca se infiere.
$s0 = Read-Host "Saldo ACTUAL en AI Studio > Facturacion de la API de Gemini (p. ej. 14170) o Enter para no registrarlo"
$r = Read-Host "Si las pruebas pasaron y Gemini muestra ok=true, escriba SI para lanzar la corrida $Corrida (~30 min)"
if ($r -ne "SI") { Write-Host "Detenido por el usuario."; exit 0 }
Write-Host "==== 6. Corrida $Corrida (A/B fix3, solo Gemini; se detiene ante errores de facturacion/cuota)"
python scripts\eval_ab_dev.py --set fix3 --gemini-only --sleep 4 --out $out 2>&1 | Tee-Object "$log\05_eval_run$Corrida.log"
$rc = $LASTEXITCODE
$s1 = Read-Host "Saldo FINAL en AI Studio > Facturacion (puede tardar unos minutos en actualizarse) o Enter para no registrarlo"
$saldo = [ordered]@{ corrida = $Corrida; fuente = "lectura manual del responsable en Google AI Studio > Facturacion de la API de Gemini";
  saldo_inicial = $(if ($s0) { $s0 } else { $null }); saldo_final = $(if ($s1) { $s1 } else { $null }); moneda = "COP";
  nota = "Saldo declarado a partir de la pantalla oficial; Google puede tardar en reflejar el consumo. El coste estimado esta en el informe de la corrida (campo consumo)." }
$saldo | ConvertTo-Json | Out-File -Encoding utf8 "data\eval\fix3\saldo_run$Corrida.json"
if ($rc -eq 4) { Write-Host "DETENIDA: error de facturacion, cuota o proveedor (ver $log\05_eval_run$Corrida.log). No continuar sin revisar."; exit 4 }
if ($rc -ne 0) { Write-Host "La corrida termino con codigo $rc. Revisar el registro."; exit $rc }

Write-Host "==== 7. Resumen de las corridas disponibles"
$runs = Get-ChildItem "data\eval\fix3\ab_fix3_run*.json" | Sort-Object Name | ForEach-Object { $_.FullName }
python scripts\summarize_repeated_ab.py @runs 2>&1 | Tee-Object "$log\06_resumen_run$Corrida.log"
Remove-Item Env:DIG_V3, Env:LLM_JSON_MODE, Env:RRE_ENABLE_SCOPE_PREFERENCE, Env:RRE_SCOPE_BETA, Env:DIG_NUMBER_NORMALIZATION -ErrorAction SilentlyContinue
$env:GEMINI_API_KEY = ""
Write-Host "Corrida $Corrida terminada. NO se lanza la siguiente: revise los resultados y ejecute -Corrida $($Corrida+1) solo si procede."

# Evaluacion A/B controlada (benchmark_v2 DEV, 41 preguntas). No toca produccion, ni el benchmark sellado,
# ni hace commit. Paso 1 solo comprueba cuota; si un proveedor no responde, NO sigue sin confirmacion.
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot\..
$log = "data\eval\dig_v3\logs"; New-Item -ItemType Directory -Force $log | Out-Null
Write-Host "==== 1. Cuota de los proveedores (2 llamadas minimas)"
python scripts\check_llm_quota.py 2>&1 | Tee-Object "$log\01_cuota.log"
$r = Read-Host "Si Gemini o Groq muestran ok=true, escriba SI para continuar"
if ($r -ne "SI") { Write-Host "Detenido por el usuario."; exit 0 }
Write-Host "==== 2a. Suite completa, modo original (deben fallar solo los 6 de siempre)"
Remove-Item Env:DIG_V3, Env:LLM_JSON_MODE, Env:RRE_ENABLE_SCOPE_PREFERENCE, Env:DIG_NUMBER_NORMALIZATION, Env:LLM_JSON_SCHEMA, Env:ADA_PROMPT_RIGOR -ErrorAction SilentlyContinue
python -m pytest tests -q -p no:cacheprovider 2>&1 | Select-Object -Last 12 | Tee-Object "$log\02a_tests_original.log"
Write-Host "==== 2b. Suite completa, todas las variables activas"
$env:DIG_V3="1"; $env:LLM_JSON_MODE="1"; $env:RRE_ENABLE_SCOPE_PREFERENCE="1"; $env:DIG_NUMBER_NORMALIZATION="v2"; $env:LLM_JSON_SCHEMA="1"; $env:ADA_PROMPT_RIGOR="1"
python -m pytest tests -q -p no:cacheprovider 2>&1 | Select-Object -Last 12 | Tee-Object "$log\02b_tests_todo.log"
Remove-Item Env:LLM_JSON_SCHEMA, Env:ADA_PROMPT_RIGOR -ErrorAction SilentlyContinue
$r2 = Read-Host "Si ambas corridas terminan en '6 failed', escriba SI para lanzar la evaluacion A/B"
if ($r2 -ne "SI") { Write-Host "Detenido por el usuario."; exit 0 }
Write-Host "==== 3. Evaluacion A/B (intercalada; ~25-35 min)"
$env:DIG_V3="1"; $env:LLM_JSON_MODE="1"; $env:RRE_ENABLE_SCOPE_PREFERENCE="1"; $env:DIG_NUMBER_NORMALIZATION="v2"
(Get-FileHash data\processed\rebuild_2026_08_corrected\passages_candidate.json).Hash | Out-File "$log\corpus_sha_antes.txt"
python scripts\eval_ab_dev.py --sleep 4 --out data\eval\dig_v3\ab_dev.json 2>&1 | Tee-Object "$log\03_ab.log"
(Get-FileHash data\processed\rebuild_2026_08_corrected\passages_candidate.json).Hash | Out-File "$log\corpus_sha_despues.txt"
Remove-Item Env:DIG_V3, Env:LLM_JSON_MODE, Env:RRE_ENABLE_SCOPE_PREFERENCE, Env:DIG_NUMBER_NORMALIZATION, Env:LLM_JSON_SCHEMA, Env:ADA_PROMPT_RIGOR -ErrorAction SilentlyContinue
Write-Host "Terminado. Resultados: data\eval\dig_v3\ab_dev.json  Registros: $log"

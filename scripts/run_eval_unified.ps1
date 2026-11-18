# Respuesta unica: pruebas + evaluacion en vivo A (anterior) / B (respuesta unica) sobre las 41 preguntas DEV.
# No toca produccion, ni el benchmark sellado, ni hace commit. Si un proveedor no responde, NO sigue sin confirmacion.
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot\..
$log = "data\eval\unified_answer\logs"; New-Item -ItemType Directory -Force $log | Out-Null
Write-Host "==== 1. Pruebas nuevas (respuesta unica)"
python -m pytest tests\test_unified_answer.py tests\test_unified_dig.py -q -p no:cacheprovider 2>&1 | Tee-Object "$log\01_tests_unificada.log"
Write-Host "==== 2. Suite completa con el modo desactivado (deben fallar solo los 6 de siempre)"
Remove-Item Env:ADA_UNIFIED_ANSWER -ErrorAction SilentlyContinue
python -m pytest tests -q -p no:cacheprovider 2>&1 | Select-Object -Last 12 | Tee-Object "$log\02_suite.log"
Write-Host "==== 3. Cuota de los proveedores (2 llamadas minimas)"
python scripts\check_llm_quota.py 2>&1 | Tee-Object "$log\03_cuota.log"
$r = Read-Host "Si las pruebas pasan y Gemini o Groq muestran ok=true, escriba SI para lanzar la evaluacion (~30 min)"
if ($r -ne "SI") { Write-Host "Detenido por el usuario."; exit 0 }
$env:DIG_V3="1"; $env:LLM_JSON_MODE="1"; $env:RRE_ENABLE_SCOPE_PREFERENCE="1"; $env:DIG_NUMBER_NORMALIZATION="v2"
python scripts\eval_ab_dev.py --set unified --sleep 4 --out data\eval\unified_answer\ab_unified_dev.json 2>&1 | Tee-Object "$log\04_eval.log"
Remove-Item Env:DIG_V3, Env:LLM_JSON_MODE, Env:RRE_ENABLE_SCOPE_PREFERENCE, Env:DIG_NUMBER_NORMALIZATION, Env:ADA_UNIFIED_ANSWER, Env:LLM_JSON_SCHEMA, Env:ADA_PROMPT_RIGOR -ErrorAction SilentlyContinue
Write-Host "Terminado. Resultados: data\eval\unified_answer\ab_unified_dev.json  Registros: $log"

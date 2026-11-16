# Fase 10 - ejecucion completa en Windows (desde la raiz del repo, con el entorno virtual activo)
#   powershell -ExecutionPolicy Bypass -File scripts\run_fase10.ps1            (todo)
#   powershell -ExecutionPolicy Bypass -File scripts\run_fase10.ps1 -SkipLLM   (sin llamadas al LLM)
# No modifica corpus, SHADOW, configuracion ni .env. Las salidas quedan en data\eval\fase10_logs y results\.
param([switch]$SkipLLM, [switch]$SkipNLI, [int]$Runs = 2, [double]$Sleep = 4)
$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$log = "data\eval\fase10_logs"
New-Item -ItemType Directory -Force -Path $log | Out-Null
function Step($name, [scriptblock]$cmd) {
    Write-Host "==== $name" -ForegroundColor Cyan
    $t0 = Get-Date
    & $cmd 2>&1 | Tee-Object -FilePath "$log\$name.log"
    "exit=$LASTEXITCODE  segundos=$([int]((Get-Date) - $t0).TotalSeconds)" | Tee-Object -FilePath "$log\$name.log" -Append
}
$corpus = "data\processed\rebuild_2026_08_corrected\passages_candidate.json"
(Get-FileHash $corpus -Algorithm SHA256).Hash | Out-File "$log\00_corpus_sha_before.txt"

Step "01_pytest_fase10"      { python -m pytest tests\test_fase10_experimental.py -q -p no:cacheprovider }
Step "02_pytest_full"        { python -m pytest -q -p no:cacheprovider }
Step "03_benchmark_v2_check" { python scripts\build_benchmark_v2.py --check; python scripts\build_nli_shadow_pairs.py --check }
Step "04_retrieval_v2"       { python scripts\eval_benchmark_v2_retrieval.py --split all --allow-test-sealed }
Step "05_ambiguity_dev"      { python scripts\eval_ambiguity_detector.py --split dev --sweep }
Step "06_ambiguity_test"     { python scripts\eval_ambiguity_detector.py --split test_sealed --allow-test-sealed --params-from data\eval\benchmark_v2\results\ambiguity_params_dev.json }
if (-not $SkipNLI) {
    Step "07_nli_shadow"     { python scripts\eval_nli_shadow.py --allow-test-sealed }
}
if (-not $SkipLLM) {
    Step "08_llm_shadow_dev"  { python scripts\eval_llm_shadow.py --split dev --runs $Runs --sleep $Sleep --nli-model MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli }
    Step "09_llm_shadow_test" { python scripts\eval_llm_shadow.py --split test_sealed --allow-test-sealed --runs $Runs --sleep $Sleep --nli-model MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli }
}
(Get-FileHash $corpus -Algorithm SHA256).Hash | Out-File "$log\99_corpus_sha_after.txt"
Get-ChildItem data\corpus_multisource, data\markdown -Recurse -File | Get-FileHash -Algorithm SHA256 |
    Select-Object Hash, Path | Out-File "$log\99_shadow_hashes_after.txt"
Write-Host "Terminado. Envie la carpeta $log (y data\eval\*\results) para el informe." -ForegroundColor Green

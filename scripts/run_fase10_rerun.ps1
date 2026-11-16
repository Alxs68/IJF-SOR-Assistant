# Fase 10 - repeticion de los pasos afectados (sin llamadas al LLM)
#   powershell -ExecutionPolicy Bypass -File scripts\run_fase10_rerun.ps1
$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
$log = "data\eval\fase10_logs"
New-Item -ItemType Directory -Force -Path $log | Out-Null
function Step($name, [scriptblock]$cmd) {
    Write-Host "==== $name" -ForegroundColor Cyan
    $t0 = Get-Date
    & $cmd 2>&1 | Tee-Object -FilePath "$log\$name.log"
    "exit=$LASTEXITCODE  segundos=$([int]((Get-Date) - $t0).TotalSeconds)" | Tee-Object -FilePath "$log\$name.log" -Append
}
$corpus = "data\processed\rebuild_2026_08_corrected\passages_candidate.json"
(Get-FileHash $corpus -Algorithm SHA256).Hash | Out-File "$log\00b_corpus_sha_before.txt"
Step "02b_pytest_tests"  { python -m pytest tests -q -p no:cacheprovider }
Step "07b_nli_shadow"    { python scripts\eval_nli_shadow.py --allow-test-sealed }
(Get-FileHash $corpus -Algorithm SHA256).Hash | Out-File "$log\99b_corpus_sha_after.txt"
Write-Host "Terminado." -ForegroundColor Green

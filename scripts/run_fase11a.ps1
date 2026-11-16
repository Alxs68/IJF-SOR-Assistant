# Fase 11A - diagnostico de abstenciones y de recuperacion (solo DEV; no toca test_sealed)
#   powershell -ExecutionPolicy Bypass -File scripts\run_fase11a.ps1
# Unico paso con LLM: 2 corridas sobre dev (41 consultas). Lo demas no llama al LLM.
param([int]$Runs = 2, [double]$Sleep = 4, [switch]$SkipLLM)
$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
$out = "data\eval\fase11"
$log = "$out\logs"
New-Item -ItemType Directory -Force -Path $log | Out-Null
function Step($name, [scriptblock]$cmd) {
    Write-Host "==== $name" -ForegroundColor Cyan
    $t0 = Get-Date
    & $cmd 2>&1 | Out-File -Encoding utf8 "$log\$name.log"
    "exit=$LASTEXITCODE  segundos=$([int]((Get-Date) - $t0).TotalSeconds)" | Out-File -Encoding utf8 -Append "$log\$name.log"
    Get-Content "$log\$name.log" -Tail 6
}
$corpus = "data\processed\rebuild_2026_08_corrected\passages_candidate.json"
(Get-FileHash $corpus -Algorithm SHA256).Hash | Out-File -Encoding ascii "$log\corpus_sha_before.txt"
Step "a0_pytest_experimental" { python -m pytest tests\test_fase10_experimental.py tests\test_fase11_experimental.py -q -p no:cacheprovider }
if (-not $SkipLLM) {
    Step "a1_llm_dev" { python scripts\eval_llm_shadow.py --split dev --runs $Runs --sleep $Sleep --out $out\llm_dev_f11.json }
}
Step "a2_diag_retrieval" { python scripts\diag_retrieval_f11.py --llm-results $out\llm_dev_f11.json }
Step "a3_diag_abstentions" { python scripts\diag_abstentions_f11.py --dev $out\llm_dev_f11.json --phase10 data\eval\benchmark_v2\results\llm_shadow_dev_rescored.json data\eval\benchmark_v2\results\llm_shadow_test_sealed_rescored.json }
(Get-FileHash $corpus -Algorithm SHA256).Hash | Out-File -Encoding ascii "$log\corpus_sha_after.txt"
Write-Host "Terminado." -ForegroundColor Green

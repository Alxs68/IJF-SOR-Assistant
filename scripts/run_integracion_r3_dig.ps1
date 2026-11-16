# Integracion experimental R3 + DIG v2: pruebas comparativas ORIGINAL (flags apagados) vs EXPERIMENTAL (flags encendidos)
#   powershell -ExecutionPolicy Bypass -File scripts\run_integracion_r3_dig.ps1            (incluye 1 corrida LLM por modo)
#   powershell -ExecutionPolicy Bypass -File scripts\run_integracion_r3_dig.ps1 -SkipLLM   (sin llamadas al LLM)
# Solo dev de benchmark_v2. No toca test_sealed ni benchmark_v3. Resultados en data\eval\integracion_r3_dig\
param([switch]$SkipLLM, [int]$Runs = 1, [double]$Sleep = 8)
$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
$out = "data\eval\integracion_r3_dig"
$log = "$out\logs"
New-Item -ItemType Directory -Force -Path $log | Out-Null
function Step($name, [scriptblock]$cmd) {
    Write-Host "==== $name" -ForegroundColor Cyan
    $t0 = Get-Date
    & $cmd 2>&1 | Tee-Object -FilePath "$log\$name.log"
    "exit=$LASTEXITCODE  segundos=$([int]((Get-Date) - $t0).TotalSeconds)" | Tee-Object -FilePath "$log\$name.log" -Append
}
function Flags($on) {
    if ($on) { $env:RRE_ENABLE_SCOPE_PREFERENCE = "1"; $env:DIG_NUMBER_NORMALIZATION = "v2" }
    else { Remove-Item Env:RRE_ENABLE_SCOPE_PREFERENCE -ErrorAction SilentlyContinue; Remove-Item Env:DIG_NUMBER_NORMALIZATION -ErrorAction SilentlyContinue }
}
$corpus = "data\processed\rebuild_2026_08_corrected\passages_candidate.json"
(Get-FileHash $corpus -Algorithm SHA256).Hash | Out-File -Encoding ascii "$log\corpus_sha_before.txt"

Flags $false
Step "t1_pytest_original"      { python -m pytest tests -q -p no:cacheprovider }
Flags $true
Step "t2_pytest_experimental"  { python -m pytest tests -q -p no:cacheprovider }

Flags $false
Step "r1_retrieval_original"     { python scripts\eval_benchmark_v2_retrieval.py --split dev --out $out\retrieval_dev_original.json }
Flags $true
Step "r2_retrieval_experimental" { python scripts\eval_benchmark_v2_retrieval.py --split dev --out $out\retrieval_dev_experimental.json }

if (-not $SkipLLM) {
    Flags $false
    Step "l1_llm_original"     { python scripts\eval_llm_shadow.py --split dev --runs $Runs --sleep $Sleep --capture-dig --out $out\llm_dev_original.json }
    Flags $true
    Step "l2_llm_experimental" { python scripts\eval_llm_shadow.py --split dev --runs $Runs --sleep $Sleep --capture-dig --out $out\llm_dev_experimental.json }
}
Flags $false
(Get-FileHash $corpus -Algorithm SHA256).Hash | Out-File -Encoding ascii "$log\corpus_sha_after.txt"
Write-Host "Terminado." -ForegroundColor Green

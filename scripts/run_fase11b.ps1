# Fase 11 (continuacion) - calibracion offline del DIG y experimentos de recuperacion R2-R5. SOLO DEV.
#   powershell -ExecutionPolicy Bypass -File scripts\run_fase11b.ps1
# Paso con LLM: 1 (captura exacta de entradas del DIG, 2 corridas sobre dev). -SkipLLM lo omite.
# R5 descarga paraphrase-multilingual-MiniLM-L12-v2 (~470 MB) la primera vez (solo uso experimental local).
param([int]$Runs = 2, [double]$Sleep = 8, [switch]$SkipLLM, [switch]$SkipR5)
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
    Get-Content "$log\$name.log" -Tail 14
}
$corpus = "data\processed\rebuild_2026_08_corrected\passages_candidate.json"
(Get-FileHash $corpus -Algorithm SHA256).Hash | Out-File -Encoding ascii "$log\b_corpus_sha_before.txt"
Step "b0_pytest" { python -m pytest tests\test_fase10_experimental.py tests\test_fase11_experimental.py tests\test_decision_integrity.py -q -p no:cacheprovider }
$r5 = @(); if ($SkipR5) { $r5 = @("--no-r5") }
Step "b1_retrieval_variants" { python scripts\eval_f11_retrieval.py --llm-results $out\llm_dev_f11.json @r5 }
if (-not $SkipLLM) {
    Step "b2_llm_dev_capture" { python scripts\eval_llm_shadow.py --split dev --runs $Runs --sleep $Sleep --capture-dig --out $out\llm_dev_f11_capture.json }
}
Step "b3_dig_replay" { python scripts\replay_dig_f11.py $out\llm_dev_f11_capture.json $out\llm_dev_f11_rescored.json }
(Get-FileHash $corpus -Algorithm SHA256).Hash | Out-File -Encoding ascii "$log\b_corpus_sha_after.txt"
Write-Host "Terminado." -ForegroundColor Green

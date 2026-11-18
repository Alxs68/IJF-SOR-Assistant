# Despliegue de la respuesta unica + correcciones de trazabilidad en la instancia EXPERIMENTAL (127.0.0.1:8510).
# No toca produccion (8501), ni su .env, ni DNS/Nginx. Sin git add, sin commit y sin push: empaqueta el
# commit base d126873 + los archivos FIX3 autorizados del directorio de trabajo (deploy\exp\build_package_exp.py).
#   powershell -ExecutionPolicy Bypass -File deploy\exp\deploy_fix3_exp.ps1
$ErrorActionPreference = "Continue"   # pytest/git escriben avisos en stderr; los errores se comprueban a mano
Set-Location $PSScriptRoot\..\..
$key = "C:\PROYECTOS\ssh-key-2026-07-20.key"; $srv = "ubuntu@149.130.187.132"
if ((git branch --show-current).Trim() -ne "exp/r3-dig-v2") { Write-Host "ABORTO: no estoy en la rama exp/r3-dig-v2"; exit 1 }

Write-Host "==== 1. Pruebas de las correcciones (deben pasar todas; sin claves reales y con la red de proveedores bloqueada)"
$env:GEMINI_API_KEY = ""; $env:GOOGLE_API_KEY = ""; $env:GROQ_API_KEY = ""
$t = python -m pytest tests\test_aislamiento_proveedores.py tests\test_install_exp_rollback.py tests\test_build_package_exp.py tests\test_rotar_claves_servidor.py tests\test_fix_trazabilidad.py tests\test_unified_answer.py tests\test_unified_dig.py tests\test_llm_schema_rigor.py tests\test_post_ab_fixes.py tests\test_dig_v3_fixes.py tests\test_r3_dig_v2_integration.py -q -p no:cacheprovider 2>&1
$pyrc = $LASTEXITCODE   # se captura inmediatamente, antes de cualquier otro comando
$t | Select-Object -Last 3 | ForEach-Object { Write-Host "$_" }
if ($null -eq $pyrc -or $pyrc -ne 0) { Write-Host "ABORTO: pytest termino con codigo $pyrc; no se empaqueta ni se sube nada"; exit 2 }
if (($t -join " ") -match "\d+ failed|\d+ errors?\b" -or -not (($t -join " ") -match "\d+ passed")) { Write-Host "ABORTO: el resumen de pytest no confirma que todo paso; no se empaqueta ni se sube nada"; exit 2 }

Write-Host "==== 2. Paquete del estado de trabajo autorizado (SIN git add, SIN commit, SIN push)"
$base = "d126873"
if ((git rev-parse --short=7 HEAD).Trim() -ne $base) { Write-Host "ABORTO: HEAD no es el commit base $base"; exit 1 }
New-Item -ItemType Directory -Force -Path "deploy\exp\out" | Out-Null
$p = python deploy\exp\build_package_exp.py --base $base --out deploy\exp\out --secrets-from .env 2>&1
$prc = $LASTEXITCODE
$p | Write-Host
if ($prc -ne 0) { Write-Host "ABORTO: el empaquetado fallo (codigo $prc); nada se subio"; exit 4 }
$id = (($p | Where-Object { "$_" -match '^PAQUETE_ID=' }) -replace '^PAQUETE_ID=', '').Trim()
$tar = "deploy\exp\out\ijf_exp_$id.tar.gz"; $man = "deploy\exp\out\ijf_exp_$id.manifest.json"
if (-not (Test-Path $tar) -or -not (Test-Path $man)) { Write-Host "ABORTO: no se encontro el paquete o el manifiesto"; exit 4 }
$h = (Get-FileHash $tar -Algorithm SHA256).Hash.ToLower()
if ($h -ne (Get-Content $man -Raw | ConvertFrom-Json).sha256_paquete) { Write-Host "ABORTO: el SHA-256 no coincide con el manifiesto"; exit 4 }
Write-Host "Paquete $tar  sha256 $h  (manifiesto: $man)"
$short = $id

$r = Read-Host "Escriba SI para subirlo y REINSTALAR la instancia experimental (produccion no se toca)"
if ($r -ne "SI") { Write-Host "Detenido: paquete $short listo; no se desplego (no se hizo commit)."; exit 0 }
Write-Host "==== 4. Subida e instalacion de la experimental (el instalador retira la anterior y la RESTAURA si algo falla)"
scp -i $key $tar "$tar.sha256" $man deploy\exp\server_install_exp.sh deploy\exp\server_rollback_exp.sh deploy\exp\server_status_exp.sh "${srv}:/home/ubuntu/"
if ($LASTEXITCODE -ne 0) { Write-Host "ABORTO: fallo la subida (nada cambio en el servidor)"; exit 5 }
$remote = "EXP_FIX3=1 EXP_LLM_SCHEMA=1 bash /home/ubuntu/server_install_exp.sh /home/ubuntu/ijf_exp_$short.tar.gz"
ssh -i $key $srv $remote
$rc = $LASTEXITCODE
switch ($rc) {
  0  { Write-Host "INSTALADA la version $short en la experimental." }
  10 { Write-Host "FALLO la instalacion y se RESTAURO la version experimental anterior (ver el registro install_*.log)." }
  11 { Write-Host "FALLO la instalacion y la REVERSION tambien fallo: revisar la experimental (produccion no se toco)." }
  12 { Write-Host "FALLO la instalacion y no habia version anterior que restaurar." }
  default { Write-Host "La instalacion termino con codigo $rc (2-6: abortada antes de retirar la anterior; nada cambio)." }
}
Write-Host "==== 5. Clave en el contenedor experimental (solo 4 ultimos caracteres)"
ssh -i $key $srv 'v=$(docker exec ijf-sor-assistant-exp printenv GEMINI_API_KEY); echo "experimental: termina en ${v: -4}"; v=$(docker exec ijf-sor-assistant printenv GEMINI_API_KEY); echo "produccion: termina en ${v: -4}"'
Write-Host "Listo. Para probarla: ssh -i $key -N -L 8510:127.0.0.1:8510 $srv   y abra http://localhost:8510"

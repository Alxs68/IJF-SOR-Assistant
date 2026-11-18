# Prueba LOCAL de deploy\exp\deploy_fix3_exp.ps1 (no conecta a OCI, no ejecuta pytest real, no empaqueta).
# Sustituye python, git, scp, ssh y Read-Host por funciones falsas: en PowerShell una funcion tiene
# prioridad sobre un programa externo con el mismo nombre. Si el script intentara subir algo, la prueba falla.
#   powershell -ExecutionPolicy Bypass -File tests\ps\test_deploy_ps1_aborta.ps1
$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$deploy = Join-Path $repo "deploy\exp\deploy_fix3_exp.ps1"
$fallos = 0

function Invoke-Caso($nombre, $pytestRc, $pytestTxt, $buildRc, $esperado) {
  $global:llamadas = New-Object System.Collections.ArrayList
  $global:fake = @{ pytestRc = $pytestRc; pytestTxt = $pytestTxt; buildRc = $buildRc }
  function global:python {
    if ($args -contains "pytest") { [void]$global:llamadas.Add("pytest"); $global:fake.pytestTxt; $global:LASTEXITCODE = $global:fake.pytestRc; return }
    [void]$global:llamadas.Add("build"); "ABORTO (24): simulado"; $global:LASTEXITCODE = $global:fake.buildRc
  }
  function global:git {
    if ($args -contains "--show-current") { "exp/r3-dig-v2" } elseif ($args -contains "rev-parse") { "d126873" }
    $global:LASTEXITCODE = 0
  }
  function global:scp { [void]$global:llamadas.Add("scp"); $global:LASTEXITCODE = 0 }
  function global:ssh { [void]$global:llamadas.Add("ssh"); $global:LASTEXITCODE = 0 }
  function global:Read-Host { [void]$global:llamadas.Add("read-host"); "NO" }
  $prev = Get-Location
  try { & $deploy *> $null; $rc = $LASTEXITCODE } finally { Set-Location $prev }
  $subio = ($global:llamadas -contains "scp") -or ($global:llamadas -contains "ssh")
  $ok = ($rc -eq $esperado) -and (-not $subio)
  if ($esperado -eq 2) { $ok = $ok -and -not ($global:llamadas -contains "build") }
  $estado = "FALLA"; if ($ok) { $estado = "OK" }
  Write-Host ("[{0}] {1}: codigo {2} (esperado {3}); llamadas: {4}" -f $estado, $nombre, $rc, $esperado, ($global:llamadas -join ","))
  if (-not $ok) { $script:fallos++ }
}

Invoke-Caso "pytest devuelve 1 aunque el resumen diga passed" 1 @("10 passed in 1s") 0 2
Invoke-Caso "pytest devuelve 5 (no recogio pruebas)" 5 @("no tests ran") 0 2
Invoke-Caso "pytest devuelve 0 pero el resumen tiene fallos" 0 @("1 failed, 9 passed in 1s") 0 2
Invoke-Caso "pytest devuelve 0 sin resumen de passed" 0 @("algo raro") 0 2
Invoke-Caso "pytest OK y falla el empaquetado" 0 @("10 passed in 1s") 24 4

foreach ($f in "python", "git", "scp", "ssh", "Read-Host") { Remove-Item "function:global:$f" -ErrorAction SilentlyContinue }
if ($fallos -gt 0) { Write-Host "RESULTADO: $fallos caso(s) fallaron"; exit 1 }
Write-Host "RESULTADO: todos los casos OK (no se subio nada en ninguno)"
exit 0

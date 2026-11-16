# Empaqueta el commit experimental (exacto, sin archivos fuera de git) para subirlo a OCI.
#   powershell -ExecutionPolicy Bypass -File deploy\exp\make_bundle_exp.ps1
# Requisito: estar en la rama exp/r3-dig-v2 con el commit local hecho y el arbol limpio en lo relevante.
$ErrorActionPreference = "Stop"
$sha = (git rev-parse HEAD).Trim()
$short = $sha.Substring(0, 7)
$branch = (git branch --show-current).Trim()
if ($branch -ne "exp/r3-dig-v2") { Write-Host "AVISO: rama actual $branch (se esperaba exp/r3-dig-v2)" -ForegroundColor Yellow }
New-Item -ItemType Directory -Force -Path "deploy\exp\out" | Out-Null
$tar = "deploy\exp\out\ijf_exp_$short.tar.gz"
git archive --format=tar.gz --prefix="ijf_exp_$short/" -o $tar $sha
$h = (Get-FileHash $tar -Algorithm SHA256).Hash.ToLower()
"$h  ijf_exp_$short.tar.gz" | Out-File -Encoding ascii "$tar.sha256"
Write-Host "Commit: $sha"
Write-Host "Paquete: $tar"
Write-Host "sha256:  $h"
Write-Host ""
Write-Host "Subir a OCI (ajuste usuario/IP/clave como en los despliegues anteriores):"
Write-Host "  scp -i <clave> $tar $tar.sha256 deploy\exp\server_install_exp.sh deploy\exp\server_rollback_exp.sh deploy\exp\server_status_exp.sh ubuntu@<IP_OCI>:/home/ubuntu/"

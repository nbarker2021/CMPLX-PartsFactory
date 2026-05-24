# Full lattice-space exhaustion (quadrant Weyl method only).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

docker network inspect cmplx-backend 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { docker network create cmplx-backend | Out-Null }

Write-Host "[lattice-space] catalog + 200 quadrant weyl batches + E8 pod index + proof capture"
docker compose -f docker-compose.backwalk-lattice-space.yml up --build --abort-on-container-exit
exit $LASTEXITCODE

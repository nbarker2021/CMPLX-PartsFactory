# Start full-24 Niemeier backward-category build (resumes pilot on persistent volume).
# Requires Docker Desktop and network cmplx-backend (created if missing).

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

docker network inspect cmplx-backend 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[backwalk] creating docker network cmplx-backend"
    docker network create cmplx-backend | Out-Null
}

Write-Host "[backwalk] full24: 24 terminals, involution cap 50/component, resume pilot checkpoints"
Write-Host "[backwalk] volume: niemeier-backwalk-data -> /data"

docker compose `
    -f docker-compose.backwalk-builder.yml `
    -f docker-compose.backwalk-builder.full24.yml `
    up --build --abort-on-container-exit

exit $LASTEXITCODE

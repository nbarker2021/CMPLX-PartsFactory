# Podal/antipodal dual Weyl-bond wave orchestrator (resource-bounded batches).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

docker network inspect cmplx-backend 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    docker network create cmplx-backend | Out-Null
}

Write-Host "[weyl-bond] dual waves: construct_in (poles->middle), read_out (middle->poles)"
Write-Host "[weyl-bond] 8 chart lanes per batch when converging; mirror oloid via WEYL_13"
Write-Host "[weyl-bond] limits: 512M RAM, 64 rows/batch, 50ms inter-batch sleep"

docker compose -f docker-compose.backwalk-weyl-bond.yml up --build --abort-on-container-exit
exit $LASTEXITCODE

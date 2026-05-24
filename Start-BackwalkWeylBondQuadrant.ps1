# Run one D4 quadrant Weyl-bond search (150 batches), then optionally concat with siblings.
param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(0, 3)]
    [int] $Quadrant,
    [switch] $ConcatOnly
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

docker network inspect cmplx-backend 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { docker network create cmplx-backend | Out-Null }

$extra = @()
if ($ConcatOnly) {
    $extra += "--concat-only"
} else {
    $extra += "--quadrant", "$Quadrant", "--resume"
}

Write-Host "[weyl-bond] quadrant Q$Quadrant (2 chart states on D4 axis $Quadrant)"

docker compose -f docker-compose.backwalk-weyl-bond.yml run --rm `
    -e PROOF_LAB_MODE=backwalk-weyl-orchestrate `
    niemeier-weyl-bond-orchestrator `
    python packages/lattice-forge/scripts/orchestrate_weyl_bond_waves.py `
    --work-db /data/backwalk_work.db @extra

exit $LASTEXITCODE

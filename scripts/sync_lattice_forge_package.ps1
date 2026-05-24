# Sync development canonical work/lattice-forge -> git package packages/lattice-forge
# Usage: .\scripts\sync_lattice_forge_package.ps1 [-WhatIf]

param(
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"
$WorkRoot = "D:\PartsFactory\work\lattice-forge"
$PkgRoot = Join-Path $PSScriptRoot "..\packages\lattice-forge" | Resolve-Path -ErrorAction SilentlyContinue
if (-not $PkgRoot) {
    $PkgRoot = (Join-Path (Split-Path $PSScriptRoot -Parent) "packages\lattice-forge")
}

if (-not (Test-Path $WorkRoot)) {
    throw "Dev root not found: $WorkRoot"
}

New-Item -ItemType Directory -Force -Path $PkgRoot | Out-Null

$robocopyArgs = @(
    $WorkRoot,
    $PkgRoot,
    "/E",
    "/XD", ".pytest_cache", ".lattice_forge", "dist",
    "/XF", "*.pyc",
    "/NFL", "/NDL"
)
if ($WhatIf) {
    $robocopyArgs += "/L"
}

& robocopy @robocopyArgs
$code = $LASTEXITCODE
if ($code -ge 8) {
    throw "robocopy failed with exit code $code"
}

Write-Host "Synced $WorkRoot -> $PkgRoot"
foreach ($sub in @("witness", "tools", "decomposition")) {
    $w = Join-Path $WorkRoot "src\lattice_forge\$sub"
    $p = Join-Path $PkgRoot "src\lattice_forge\$sub"
    $wc = if (Test-Path $w) { (Get-ChildItem $w -Recurse -File | Measure-Object).Count } else { 0 }
    $pc = if (Test-Path $p) { (Get-ChildItem $p -Recurse -File | Measure-Object).Count } else { 0 }
    Write-Host "  $sub/ files: work=$wc package=$pc"
}
Write-Host "Install: pip install -e packages/lattice-forge"

# Lattice Forge dev environment — PYTHONPATH + pytest plugin autoload off
# Usage: . .\scripts\dev_lattice_forge_env.ps1

$RepoRoot = Split-Path $PSScriptRoot -Parent
$PkgSrc = Join-Path $RepoRoot "packages\lattice-forge\src"
$WorkSrc = "D:\PartsFactory\work\lattice-forge\src"
$CmplxSrc = Join-Path $RepoRoot "src"

if (Test-Path $WorkSrc) {
    $env:PYTHONPATH = "$WorkSrc;$CmplxSrc"
} elseif (Test-Path $PkgSrc) {
    $env:PYTHONPATH = "$PkgSrc;$CmplxSrc"
} else {
    Write-Warning "lattice-forge src not found; set PYTHONPATH manually"
}

$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
Write-Host "PYTHONPATH=$env:PYTHONPATH"
Write-Host "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1"

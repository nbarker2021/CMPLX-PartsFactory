# Local CI gate for lattice-forge family (no GitHub Actions)
# Usage: .\scripts\verify_lattice_forge_family.ps1 [-CheckSync] [-SkipProofs] [-Umbrella] [-Regimes]

param(
    [switch]$CheckSync,
    [switch]$SkipProofs,
    [switch]$Umbrella,
    [switch]$Regimes
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$WorkRoot = "D:\PartsFactory\work\lattice-forge"
$PkgRoot = Join-Path $RepoRoot "packages\lattice-forge"

. (Join-Path $PSScriptRoot "dev_lattice_forge_env.ps1")

function Get-FileHashSafe($Path) {
    if (-not (Test-Path $Path)) { return $null }
    return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash
}

function Compare-SyncPaths {
  param([string[]]$RelativePaths)
  $drift = @()
  foreach ($rel in $RelativePaths) {
    $work = Join-Path $WorkRoot $rel
    $pkg = Join-Path $PkgRoot $rel
    $wh = Get-FileHashSafe $work
    $ph = Get-FileHashSafe $pkg
    if ($wh -ne $ph) {
      $drift += [pscustomobject]@{ Path = $rel; Work = ($wh -ne $null); Pkg = ($ph -ne $null) }
    }
  }
  return $drift
}

Write-Host "=== lattice-forge family verify ===" -ForegroundColor Cyan

if ($CheckSync) {
    Write-Host "[sync] comparing work vs package key paths..."
    $paths = @(
        "src\lattice_forge\witness\engine.py",
        "src\lattice_forge\witness\api.py",
        "src\lattice_forge\tools\speedlight.py",
        "src\lattice_forge\rule30_block_extractor.py",
        "src\lattice_forge\forge.py"
    )
    $drift = Compare-SyncPaths $paths
    if ($drift.Count -gt 0) {
        Write-Host "SYNC DRIFT detected:" -ForegroundColor Yellow
        $drift | Format-Table -AutoSize
        throw "Run scripts/sync_lattice_forge_package.ps1 before verify"
    }
    Write-Host "[sync] OK" -ForegroundColor Green
}

Write-Host "[pytest] packages/lattice-forge/tests + tests/worlds ..."
Push-Location $RepoRoot
try {
    python -m pytest (Join-Path $PkgRoot "tests") (Join-Path $RepoRoot "tests\worlds") -q --tb=short
    if ($LASTEXITCODE -ne 0) { throw "pytest failed with exit $LASTEXITCODE" }
} finally {
    Pop-Location
}
Write-Host "[pytest] OK" -ForegroundColor Green

if (-not $SkipProofs) {
    Write-Host "[proofs] run_all_proofs --quick ..."
    $reportPath = Join-Path $PkgRoot "proofs_report.json"
    $expectedPath = Join-Path $PkgRoot "expected_outputs.json"
    Push-Location $PkgRoot
    try {
        python (Join-Path $PkgRoot "scripts\run_all_proofs.py") --quick --output $reportPath
        if ($LASTEXITCODE -ne 0) { throw "run_all_proofs failed with exit $LASTEXITCODE" }
    } finally {
        Pop-Location
    }
    Write-Host "[proofs] OK" -ForegroundColor Green

    Write-Host "[regression] expected_outputs.json diff ..."
    $report = Get-Content $reportPath -Raw | ConvertFrom-Json
    $expected = Get-Content $expectedPath -Raw | ConvertFrom-Json
  $mismatches = @()
  foreach ($key in $expected.expected_proofs.PSObject.Properties.Name) {
    $exp = $expected.expected_proofs.$key
    $act = $report.proofs.$key
    if (-not $act) {
      $mismatches += "$key missing from proofs_report"
      continue
    }
    if ($exp.status -and ($act.status -ne $exp.status)) {
      $mismatches += "$key status expected $($exp.status) got $($act.status)"
    }
  }
  if ($report.overall_status -ne "pass") {
    $mismatches += "overall_status not pass"
  }
  if ($mismatches.Count -gt 0) {
    $mismatches | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    throw "expected_outputs regression failed"
  }
  Write-Host "[regression] OK" -ForegroundColor Green

  if ($Umbrella) {
    Write-Host "[umbrella] expected_outputs_umbrella.json diff ..."
    $umbrellaExpectedPath = Join-Path $PkgRoot "expected_outputs_umbrella.json"
    if (-not (Test-Path $umbrellaExpectedPath)) {
      throw "expected_outputs_umbrella.json missing from package"
    }
    $umbrellaExpected = Get-Content $umbrellaExpectedPath -Raw | ConvertFrom-Json
    $umbrellaMismatches = @()
    foreach ($key in $umbrellaExpected.expected_proofs.PSObject.Properties.Name) {
      $exp = $umbrellaExpected.expected_proofs.$key
      $act = $report.proofs.$key
      if (-not $act) {
        $umbrellaMismatches += "$key missing from proofs_report"
        continue
      }
      if ($exp.status -and ($act.status -ne $exp.status)) {
        $umbrellaMismatches += "$key status expected $($exp.status) got $($act.status)"
      }
    }
    if ($umbrellaMismatches.Count -gt 0) {
      $umbrellaMismatches | ForEach-Object { Write-Host $_ -ForegroundColor Red }
      throw "expected_outputs_umbrella regression failed"
    }
    Write-Host "[umbrella] OK" -ForegroundColor Green
  }
}

if ($Regimes) {
    Write-Host "[regimes] run_regimes_proofs --quick ..."
    $regReportPath = Join-Path $PkgRoot "proofs_report_regimes.json"
    $regExpectedPath = Join-Path $PkgRoot "expected_outputs_regimes.json"
    Push-Location $PkgRoot
    try {
        python (Join-Path $PkgRoot "scripts\run_regimes_proofs.py") --quick --output $regReportPath
        if ($LASTEXITCODE -ne 0) { throw "run_regimes_proofs failed with exit $LASTEXITCODE" }
    } finally {
        Pop-Location
    }
    Write-Host "[regimes] OK" -ForegroundColor Green

    Write-Host "[regimes-regression] expected_outputs_regimes.json diff ..."
    $regReport = Get-Content $regReportPath -Raw | ConvertFrom-Json
    $regExpected = Get-Content $regExpectedPath -Raw | ConvertFrom-Json
    $regMismatches = @()
    foreach ($key in $regExpected.expected_proofs.PSObject.Properties.Name) {
        $exp = $regExpected.expected_proofs.$key
        $act = $regReport.proofs.$key
        if (-not $act) {
            $regMismatches += "$key missing from regimes proofs_report"
            continue
        }
        foreach ($field in $exp.PSObject.Properties.Name) {
            $ev = $exp.$field
            $av = $act.$field
            if ($null -ne $ev -and ($av -ne $ev)) {
                $regMismatches += "$key.$field expected $ev got $av"
            }
        }
    }
    if ($regReport.overall_status -ne $regExpected.expected_overall_status) {
        $regMismatches += "regimes overall_status not $($regExpected.expected_overall_status)"
    }
    if ($regMismatches.Count -gt 0) {
        $regMismatches | ForEach-Object { Write-Host $_ -ForegroundColor Red }
        throw "expected_outputs_regimes regression failed"
    }
    Write-Host "[regimes-regression] OK" -ForegroundColor Green
}

Write-Host "[catalog] endpoint sanity ..."
$familyPath = Join-Path $RepoRoot "catalog\families\lattice-forge.json"
$partPath = Join-Path $RepoRoot "catalog\parts\lattice-forge.json"
$family = Get-Content $familyPath -Raw | ConvertFrom-Json
$part = Get-Content $partPath -Raw | ConvertFrom-Json
$witnessSpace = $family.spaces | Where-Object { $_.space_id -eq "lf-witness" }
if (-not $witnessSpace) { throw "lf-witness space missing from family manifest" }
if ($part.family_manifest -ne "catalog/families/lattice-forge.json") {
    throw "part family_manifest mismatch"
}
Write-Host "[catalog] OK" -ForegroundColor Green

Write-Host "=== verify_lattice_forge_family: PASS ===" -ForegroundColor Green

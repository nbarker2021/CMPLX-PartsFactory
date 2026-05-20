#Requires -Version 5.1
# CMPLX-PartsFactory Stack Bootstrap (Simplified)
# =================================================
# Usage: .\Start-Simple.ps1 [-Profile full]

param(
    [string]$Profile = "full"
)

$ErrorActionPreference = "Stop"

function Test-Docker {
    Write-Host "Checking Docker..." -NoNewline
    try {
        $null = docker info 2>$null
        if ($LASTEXITCODE -ne 0) { throw "not running" }
        Write-Host " OK" -ForegroundColor Green
    }
    catch {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Host "Start Docker Desktop first." -ForegroundColor Yellow
        exit 1
    }
}

function New-EnvFile {
    if (Test-Path ".env") {
        Write-Host ".env exists." -ForegroundColor Green
        return
    }
    Write-Host "Creating .env from template..." -NoNewline
    if (-not (Test-Path ".env.template")) {
        Write-Host " FAILED - template missing" -ForegroundColor Red
        exit 1
    }
    Copy-Item ".env.template" ".env"
    Write-Host " OK" -ForegroundColor Green
    Write-Host "Edit .env with your tokens before the next run." -ForegroundColor Yellow
}

function New-DataDirs {
    @("data\share", "data\state", "data\config", "docker-cache") | ForEach-Object {
        if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
    }
}

function Test-Compose {
    Write-Host "Validating compose..." -NoNewline
    docker compose config >$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host " FAILED" -ForegroundColor Red
        exit 1
    }
    Write-Host " OK" -ForegroundColor Green
}

function Start-Stack {
    Write-Host ""
    Write-Host "Starting stack (profile: $Profile)..." -ForegroundColor Cyan
    if ($Profile -eq "full") {
        docker compose --profile full up -d
    }
    else {
        docker compose --profile $Profile up -d
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Startup failed." -ForegroundColor Red
        exit 1
    }
}

function Show-Status {
    Write-Host ""
    Write-Host "Services:" -ForegroundColor White
    docker compose ps
    Write-Host ""
    Write-Host "Access Points:" -ForegroundColor White
    Write-Host "  OpenCode:      http://localhost:8080" -ForegroundColor Green
    Write-Host "  CMPLX API:     http://localhost:8851" -ForegroundColor Green
    Write-Host "  RabbitMQ:      http://localhost:15672" -ForegroundColor Green
    Write-Host "  MinIO:         http://localhost:9001" -ForegroundColor Green
    if ($Profile -eq "full") {
        Write-Host "  Grafana:       http://localhost:59030" -ForegroundColor Green
        Write-Host "  Prometheus:    http://localhost:59090" -ForegroundColor Green
    }
}

# === Main ===
Write-Host ""
Write-Host "CMPLX-PartsFactory Stack Bootstrap" -ForegroundColor Cyan
Write-Host ""

Test-Docker
New-EnvFile
New-DataDirs
Test-Compose
Start-Stack
Show-Status

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Stop: docker compose down" -ForegroundColor Gray

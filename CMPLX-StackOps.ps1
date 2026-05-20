#Requires -Version 5.1
<#
.SYNOPSIS
    CMPLX-PartsFactory Stack Operations (PowerShell)
.DESCRIPTION
    Companion script for common stack operations: stop, restart, logs, shell, clean.
.NOTES
    File: CMPLX-StackOps.ps1
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("stop", "down", "restart", "logs", "shell", "exec", "clean", "status", "health", "pull")]
    [string]$Action,

    [Parameter()]
    [string]$ProjectDir = "D:\PartsFactory\CMPLX-PartsFactory",

    [Parameter()]
    [string]$Service,

    [Parameter()]
    [switch]$Follow,  # For logs

    [Parameter()]
    [switch]$Volumes,  # For down/clean

    [Parameter()]
    [string]$Command = "/bin/bash"
)

$ErrorActionPreference = "Stop"
$script:ProjectDir = Resolve-Path $ProjectDir
$script:ComposeFile = Join-Path $script:ProjectDir "docker-compose.yml"
$script:EnvFile = Join-Path $script:ProjectDir ".env"

function Invoke-Compose {
    param([string[]]$Args)
    $allArgs = @("compose", "--env-file", $script:EnvFile, "-f", $script:ComposeFile) + $Args
    Write-Host "  → docker $allArgs" -ForegroundColor DarkGray
    & docker $allArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose failed"
    }
}

switch ($Action) {
    "stop" {
        Write-Host "Stopping stack..." -ForegroundColor Yellow
        Invoke-Compose @("stop")
        Write-Host "Stopped." -ForegroundColor Green
    }

    "down" {
        Write-Host "Tearing down stack..." -ForegroundColor Yellow
        $args = @("down")
        if ($Volumes) { $args += "--volumes" }
        Invoke-Compose $args
        Write-Host "Stack removed." -ForegroundColor Green
    }

    "restart" {
        if ($Service) {
            Write-Host "Restarting $Service..." -ForegroundColor Yellow
            Invoke-Compose @("restart", $Service)
        }
        else {
            Write-Host "Restarting entire stack..." -ForegroundColor Yellow
            Invoke-Compose @("restart")
        }
        Write-Host "Restarted." -ForegroundColor Green
    }

    "logs" {
        $args = @("logs")
        if ($Follow) { $args += "--follow" }
        if ($Service) {
            $args += $Service
        }
        Write-Host "Showing logs..." -ForegroundColor Yellow
        Invoke-Compose $args
    }

    "shell" {
        $target = if ($Service) { $Service } else { "opencode-session" }
        Write-Host "Opening shell in $target..." -ForegroundColor Yellow
        Invoke-Compose @("exec", $target, $Command)
    }

    "exec" {
        if (-not $Service) {
            throw "-Service required for exec action"
        }
        Write-Host "Executing in $Service..." -ForegroundColor Yellow
        Invoke-Compose @("exec", $Service, $Command)
    }

    "status" {
        Write-Host "Stack status:" -ForegroundColor Cyan
        Invoke-Compose @("ps")
    }

    "health" {
        Write-Host "Health status:" -ForegroundColor Cyan
        $services = docker compose --env-file $script:EnvFile -f $script:ComposeFile ps --format json 2>$null | ConvertFrom-Json
        foreach ($svc in $services) {
            $color = switch ($svc.Health) {
                "healthy" { "Green" }
                "unhealthy" { "Red" }
                default { "Yellow" }
            }
            Write-Host "  $($svc.Service): $($svc.Health)" -ForegroundColor $color
        }
    }

    "pull" {
        Write-Host "Pulling latest images..." -ForegroundColor Yellow
        Invoke-Compose @("pull")
        Write-Host "Done." -ForegroundColor Green
    }

    "clean" {
        Write-Host "WARNING: This will remove ALL containers, networks, and volumes!" -ForegroundColor Red
        $confirm = Read-Host "Type 'yes' to confirm"
        if ($confirm -ne "yes") {
            Write-Host "Cancelled." -ForegroundColor Yellow
            return
        }
        Invoke-Compose @("down", "--volumes", "--remove-orphans", "--rmi", "local")
        Write-Host "Stack fully cleaned." -ForegroundColor Green
    }
}

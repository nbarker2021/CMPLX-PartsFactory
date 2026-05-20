#Requires -Version 5.1
<#
.SYNOPSIS
    CMPLX-PartsFactory Full Stack Bootstrap & Startup (PowerShell)
.DESCRIPTION
    One-command bring-up for the entire CMPLX-PartsFactory Docker ecosystem.
    Handles prerequisite checks, environment setup, three-space validation,
    staged wave startup, and health verification.
.NOTES
    Run from PowerShell as Administrator (for Docker Desktop checks).
    File: Start-CMPLXStack.ps1
    Date: 2026-05-12
#>

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet("core", "cognitive", "full", "llm", "observability", "families", "global", "mcp", "controller", "discord", "dind")]
    [string]$Profile = "full",

    [Parameter()]
    [switch]$Staged,  # Wave-by-wave startup instead of parallel

    [Parameter()]
    [switch]$SkipHealthChecks,

    [Parameter()]
    [switch]$ResetEnv,  # Force re-creation of .env

    [Parameter()]
    [switch]$Pull,  # Pull images before starting

    [Parameter()]
    [string]$ProjectDir = "D:\PartsFactory\CMPLX-PartsFactory",

    [Parameter()]
    [int]$HealthTimeoutSeconds = 300,

    [Parameter()]
    [switch]$WhatIf
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"

$script:ProjectDir = Resolve-Path $ProjectDir -ErrorAction Stop
$script:ComposeFile = Join-Path $script:ProjectDir "docker-compose.yml"
$script:EnvFile = Join-Path $script:ProjectDir ".env"
$script:EnvTemplate = Join-Path $script:ProjectDir ".env.template"
$script:StartTime = Get-Date

# Wave definitions (staged startup order)
$Waves = @{
    0 = @{
        Name = "Infrastructure"
        Services = @("postgres", "postgres-cache", "redis", "rabbitmq", "minio")
        Description = "Durable backing services"
    }
    1 = @{
        Name = "Core"
        Services = @("cmplx-unified-api")
        Description = "CMPLX unified API"
        WaitForHealthy = $true
    }
    2 = @{
        Name = "Cognitive"
        Services = @("manny-runtime", "speedlight-api", "snap-unified", "mmdb-unified", "mdhg-unified")
        Description = "CMPLX brain + memory services"
        WaitForHealthy = $true
    }
    3 = @{
        Name = "Bond + Field"
        Services = @("tarpit-api", "doc-intel-api", "data-intel-api", "manny-manifold-api")
        Description = "Bond chemistry + field processing"
        WaitForHealthy = $true
    }
    4 = @{
        Name = "MCP + Controller"
        Services = @("mcp-server", "mcp-mmdb", "mcp-postgres", "mcp-vector", "workforce-controller")
        Description = "MCP servers + workforce hub"
        WaitForHealthy = $true
    }
    5 = @{
        Name = "Families + Global"
        Services = @()
        Description = "12 family stubs + global routing"
        # Families are brought up via --profile families
        Profile = "families"
        WaitForHealthy = $false
    }
    6 = @{
        Name = "Bridge + LLM + Observability"
        Services = @()
        Description = "Discord bridge, Ollama, Prometheus, Grafana"
        Profile = "discord", "llm", "observability"
        WaitForHealthy = $false
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

function Write-Header {
    param([string]$Text)
    Write-Host "`n═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Text)
    Write-Host "  → $Text" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Text)
    Write-Host "  ✓ $Text" -ForegroundColor Green
}

function Write-Error {
    param([string]$Text)
    Write-Host "  ✗ $Text" -ForegroundColor Red
}

function Write-Info {
    param([string]$Text)
    Write-Host "  ℹ $Text" -ForegroundColor Gray
}

function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function Test-DockerDesktop {
    Write-Step "Checking Docker Desktop..."

    # Check if docker command exists
    if (-not (Test-Command "docker")) {
        Write-Error "Docker CLI not found. Install Docker Desktop first:"
        Write-Info "  https://docs.docker.com/desktop/install/windows-install/"
        throw "Docker not installed"
    }

    # Check if docker daemon is responsive
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "Docker daemon not responding"
        }
    }
    catch {
        Write-Error "Docker daemon not running. Start Docker Desktop first."
        Write-Info "  1. Open Docker Desktop"
        Write-Info "  2. Wait for the whale icon to stop animating"
        Write-Info "  3. Ensure WSL2 backend is enabled in Settings > General"
        throw "Docker not running"
    }

    # Check WSL2 integration
    $wslVersion = docker info --format '{{.Driver}}' 2>$null
    Write-Info "Docker driver: $wslVersion"

    # Check docker compose v2
    $composeVersion = docker compose version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker Compose v2 not available. Enable in Docker Desktop settings."
        throw "Docker Compose v2 missing"
    }

    Write-Success "Docker Desktop is running ($(docker --version))"
    Write-Success "Docker Compose is available ($composeVersion)"
}

function Test-WSL2 {
    Write-Step "Checking WSL2..."

    $wslList = wsl --list --verbose 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "WSL not detected. Three-space mounts may not work correctly."
        Write-Info "  Install WSL2: wsl --install"
        return $false
    }

    $defaultDistro = (wsl --status 2>$null | Select-String "Default Distribution:").ToString().Split(":")[1].Trim()
    Write-Info "Default WSL distro: $defaultDistro"

    # Check if the distro is running
    $distroStatus = wsl --list --running --quiet 2>$null
    if ($distroStatus -notcontains $defaultDistro) {
        Write-Step "Starting WSL distro: $defaultDistro"
        wsl -d $defaultDistro -e true 2>$null
    }

    Write-Success "WSL2 is available"
    return $true
}

function Test-ThreeSpace {
    Write-Header "Validating Three-Space Architecture"

    $spaces = @(
        @{ Name = "Creative Yard"; WindowsPath = "D:\PartsFactory"; WSLPath = "/mnt/d/PartsFactory"; Required = $true },
        @{ Name = "Evidence Substrate"; WindowsPath = "D:\Manny Unification 2"; WSLPath = "/mnt/d/Manny Unification 2"; Required = $true },
        @{ Name = "Design Doctrine"; WindowsPath = "D:\OC build"; WSLPath = "/mnt/d/OC build"; Required = $true }
    )

    $allValid = $true
    $envVars = @{}

    foreach ($space in $spaces) {
        Write-Step "Checking $($space.Name)..."

        # Check Windows path
        $winExists = Test-Path $space.WindowsPath
        $wslExists = $false

        # Check WSL path
        try {
            $wslCheck = wsl -e test -d $space.WSLPath 2>$null
            $wslExists = ($LASTEXITCODE -eq 0)
        }
        catch {
            $wslExists = $false
        }

        if ($winExists -or $wslExists) {
            Write-Success "$($space.Name) found"
            Write-Info "  Windows: $($space.WindowsPath) $(if ($winExists) { '(exists)' } else { '(not found)' })"
            Write-Info "  WSL:     $($space.WSLPath) $(if ($wslExists) { '(exists)' } else { '(not found)' })"

            # Set the env var path (prefer WSL path for Docker)
            $envKey = switch ($space.Name) {
                "Creative Yard" { "HOST_PARTS_FACTORY" }
                "Evidence Substrate" { "HOST_MANNY_UNIFICATION" }
                "Design Doctrine" { "HOST_OC_BUILD" }
            }
            $envVars[$envKey] = $space.WSLPath
        }
        else {
            Write-Error "$($space.Name) not found at expected paths"
            Write-Info "  Expected Windows: $($space.WindowsPath)"
            Write-Info "  Expected WSL:     $($space.WSLPath)"
            if ($space.Required) {
                $allValid = $false
            }
        }
    }

    if (-not $allValid) {
        Write-Error "Required three-space paths are missing. Adjust paths in .env or create the directories."
        throw "Three-space validation failed"
    }

    Write-Success "All three spaces validated"
    return $envVars
}

function New-EnvironmentFile {
    param([hashtable]$ThreeSpacePaths)

    Write-Header "Environment Configuration"

    if (Test-Path $script:EnvFile) {
        if (-not $ResetEnv) {
            Write-Success ".env already exists at $script:EnvFile"
            Write-Info "  Use -ResetEnv to force re-creation"
            return
        }
        Write-Step "Backing up existing .env..."
        $backup = "$script:EnvFile.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
        Copy-Item $script:EnvFile $backup
        Write-Success "Backup created: $backup"
    }

    Write-Step "Creating .env from template..."

    if (-not (Test-Path $script:EnvTemplate)) {
        Write-Error ".env.template not found at $script:EnvTemplate"
        throw "Template missing"
    }

    $content = Get-Content $script:EnvTemplate -Raw

    # Replace placeholders with detected values
    $replacements = @{
        'HOST_PROJECT_DIR=.*' = "HOST_PROJECT_DIR=$($script:ProjectDir -replace '\\', '/')"
        'HOST_PARTS_FACTORY=.*' = "HOST_PARTS_FACTORY=$($ThreeSpacePaths['HOST_PARTS_FACTORY'])"
        'HOST_MANNY_UNIFICATION=.*' = "HOST_MANNY_UNIFICATION=$($ThreeSpacePaths['HOST_MANNY_UNIFICATION'])"
        'HOST_OC_BUILD=.*' = "HOST_OC_BUILD=$($ThreeSpacePaths['HOST_OC_BUILD'])"
        'PUID=.*' = "PUID=1000"
        'PGID=.*' = "PGID=1000"
        'DOCKER_GID=.*' = "DOCKER_GID=998"
        'COMPOSE_PROJECT_NAME=.*' = "COMPOSE_PROJECT_NAME=cmplx-partsfactory"
        'TZ=.*' = "TZ=$([System.TimeZoneInfo]::Local.Id)"
    }

    foreach ($pattern in $replacements.Keys) {
        $content = $content -replace $pattern, $replacements[$pattern]
    }

    # Prompt for sensitive values
    Write-Host "`n  Please configure the following (press Enter to skip/keep defaults):" -ForegroundColor Yellow

    $discordToken = Read-Host "  Discord Bot Token (leave blank to skip)"
    if ($discordToken) {
        $content = $content -replace 'DISCORD_BOT_TOKEN=.*', "DISCORD_BOT_TOKEN=$discordToken"
    }

    $openaiKey = Read-Host "  OpenAI API Key (leave blank to skip)"
    if ($openaiKey) {
        $content = $content -replace 'OPENAI_API_KEY=.*', "OPENAI_API_KEY=$openaiKey"
    }

    $githubToken = Read-Host "  GitHub Token (leave blank to skip)"
    if ($githubToken) {
        $content = $content -replace 'GITHUB_TOKEN=.*', "GITHUB_TOKEN=$githubToken"
    }

    $content | Set-Content $script:EnvFile -NoNewline
    Write-Success ".env created at $script:EnvFile"

    # Also create data directories
    $dataDirs = @("data\share", "data\state", "data\config", "docker-cache")
    foreach ($dir in $dataDirs) {
        $fullPath = Join-Path $script:ProjectDir $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-Success "Created directory: $fullPath"
        }
    }
}

function Invoke-DockerCompose {
    param(
        [string[]]$Args,
        [switch]$WaitForHealthy,
        [string[]]$WaitServices = @(),
        [int]$TimeoutSeconds = 300
    )

    $composeArgs = @(
        "compose",
        "--env-file", $script:EnvFile,
        "-f", $script:ComposeFile
    ) + $Args

    if ($WhatIf) {
        Write-Info "[WHATIF] docker $composeArgs"
        return
    }

    Write-Step "Running: docker $composeArgs"
    $start = Get-Date

    $process = Start-Process -FilePath "docker" -ArgumentList $composeArgs `
        -WorkingDirectory $script:ProjectDir `
        -PassThru -Wait -NoNewWindow

    if ($process.ExitCode -ne 0) {
        throw "docker compose failed with exit code $($process.ExitCode)"
    }

    if ($WaitForHealthy -and $WaitServices.Count -gt 0 -and -not $SkipHealthChecks) {
        Write-Step "Waiting for services to be healthy..."
        $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
        $pending = $WaitServices.Clone()

        while ($pending.Count -gt 0 -and (Get-Date) -lt $deadline) {
            $stillPending = @()
            foreach ($svc in $pending) {
                $status = docker compose --env-file $script:EnvFile -f $script:ComposeFile ps $svc --format "{{.Health}}" 2>$null
                if ($status -eq "healthy") {
                    Write-Success "$svc is healthy"
                }
                else {
                    $stillPending += $svc
                    Write-Info "  Waiting for $svc (status: $status)"
                }
            }
            $pending = $stillPending

            if ($pending.Count -gt 0) {
                Start-Sleep -Seconds 5
                Write-Progress -Activity "Waiting for services" `
                    -Status "$($pending.Count) remaining: $($pending -join ', ')" `
                    -PercentComplete ((($WaitServices.Count - $pending.Count) / $WaitServices.Count) * 100)
            }
        }

        Write-Progress -Activity "Waiting for services" -Completed

        if ($pending.Count -gt 0) {
            Write-Error "Services did not become healthy within ${TimeoutSeconds}s: $($pending -join ', ')"
            Write-Info "Check logs: docker compose --env-file $script:EnvFile -f $script:ComposeFile logs $($pending[0])"
            throw "Health check timeout"
        }
    }

    $elapsed = [math]::Round(((Get-Date) - $start).TotalSeconds, 1)
    Write-Success "Completed in ${elapsed}s"
}

function Start-Wave {
    param([int]$WaveNumber)

    $wave = $Waves[$WaveNumber]
    if (-not $wave) { return }

    Write-Header "Wave $WaveNumber — $($wave.Name)"
    Write-Info $wave.Description

    $composeArgs = @("up", "-d")

    # Add specific services if defined
    if ($wave.Services.Count -gt 0) {
        $composeArgs += $wave.Services
    }

    # Add profile if defined
    if ($wave.Profile) {
        if ($wave.Profile -is [array]) {
            foreach ($prof in $wave.Profile) {
                $composeArgs += @("--profile", $prof)
            }
        }
        else {
            $composeArgs += @("--profile", $wave.Profile)
        }
    }

    Invoke-DockerCompose -Args $composeArgs `
        -WaitForHealthy:$wave.WaitForHealthy `
        -WaitServices $wave.Services `
        -TimeoutSeconds $HealthTimeoutSeconds
}

function Start-ProfileStack {
    param([string]$ProfileName)

    Write-Header "Starting Profile: $ProfileName"

    $composeArgs = @("up", "-d", "--profile", $ProfileName)

    if ($Pull) {
        Write-Step "Pulling images..."
        Invoke-DockerCompose -Args @("pull", "--profile", $ProfileName)
    }

    Invoke-DockerCompose -Args $composeArgs
}

function Show-Status {
    Write-Header "Stack Status"

    $services = docker compose --env-file $script:EnvFile -f $script:ComposeFile ps --format json 2>$null | ConvertFrom-Json

    if (-not $services) {
        Write-Info "No services running"
        return
    }

    Write-Host ""
    Write-Host "  SERVICES:" -ForegroundColor White
    $svcCount = $services.Count
    Write-Host "  $svcCount containers running" -ForegroundColor Gray
    Write-Host ""

    foreach ($svc in $services) {
        $st = $svc.State
        $statusColor = "Gray"
        if ($st -eq "running" -or $st -eq "healthy") { $statusColor = "Green" }
        elseif ($st -eq "unhealthy") { $statusColor = "Red" }
        elseif ($st -eq "starting") { $statusColor = "Yellow" }

        $healthStr = ""
        if ($svc.Health) { $healthStr = " [" + $svc.Health + "]" }

        $portsStr = "—"
        if ($svc.Publishers) {
            $portList = @()
            foreach ($pub in $svc.Publishers) {
                $portList += $pub.PublishedPort + "->" + $pub.TargetPort
            }
            $portsStr = $portList -join ", "
        }

        $svcName = $svc.Service
        $svcStatus = $svc.Status
        Write-Host "  $svcName" -NoNewline -ForegroundColor Cyan
        Write-Host " — " -NoNewline
        Write-Host "$svcStatus$healthStr" -NoNewline -ForegroundColor $statusColor
        Write-Host " — ports: $portsStr" -ForegroundColor Gray
    }

    Write-Host ""
    Write-Host "  ACCESS POINTS:" -ForegroundColor White
    Write-Host "  OpenCode Session:    http://localhost:8080" -ForegroundColor Green
    Write-Host "  OpenCode API:        http://localhost:4096" -ForegroundColor Green
    Write-Host "  CMPLX Unified API:   http://localhost:8851" -ForegroundColor Green
    Write-Host "  RabbitMQ Management: http://localhost:15672" -ForegroundColor Green
    Write-Host "  MinIO Console:       http://localhost:9001" -ForegroundColor Green
    Write-Host "  Grafana:             http://localhost:59030" -ForegroundColor Green
    Write-Host "  Prometheus:          http://localhost:59090" -ForegroundColor Green
    Write-Host "  Workforce Hub:       http://localhost:8775" -ForegroundColor Green

    if ($Profile -eq "full" -or $Profile -eq "discord") {
        Write-Host ""
        Write-Host "  Discord Bridge is running. Bot token required for connection." -ForegroundColor Yellow
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

try {
    Write-Header "CMPLX-PartsFactory Stack Bootstrap"
    Write-Info "Project: $script:ProjectDir"
    Write-Info "Profile: $Profile"
    $modeStr = "Parallel (all at once)"
    if ($Staged) { $modeStr = "Staged (wave-by-wave)" }
    Write-Info "Mode: $modeStr"
    if ($WhatIf) {
        Write-Info "MODE: WhatIf (no actual changes)"
    }

    # ── Prerequisites ─────────────────────────────────────────────────────────
    Test-DockerDesktop
    $hasWSL = Test-WSL2

    # ── Three-Space Validation ────────────────────────────────────────────────
    $threeSpacePaths = Test-ThreeSpace

    # ── Environment Setup ─────────────────────────────────────────────────────
    if (-not (Test-Path $script:EnvFile) -or $ResetEnv) {
        New-EnvironmentFile -ThreeSpacePaths $threeSpacePaths
    }
    else {
        Write-Success ".env exists at $script:EnvFile"
    }

    # ── Pre-flight checks ─────────────────────────────────────────────────────
    if (-not (Test-Path $script:ComposeFile)) {
        throw "docker-compose.yml not found at $script:ComposeFile"
    }

    # Validate compose syntax
    Write-Step "Validating compose configuration..."
    $configCheck = docker compose --env-file $script:EnvFile -f $script:ComposeFile config 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Compose configuration is invalid:"
        Write-Host $configCheck
        throw "Invalid compose configuration"
    }
    Write-Success "Compose configuration is valid"

    # ── Pull images if requested ──────────────────────────────────────────────
    if ($Pull) {
        Write-Header "Pulling Images"
        if ($Profile -eq "full") {
            Invoke-DockerCompose -Args @("pull")
        }
        else {
            Invoke-DockerCompose -Args @("pull", "--profile", $Profile)
        }
    }

    # ── Startup ───────────────────────────────────────────────────────────────
    if ($Staged) {
        # Wave-by-wave startup
        Write-Header "Staged Startup (Waves)"

        foreach ($waveNum in ($Waves.Keys | Sort-Object)) {
            Start-Wave -WaveNumber $waveNum
        }
    }
    else {
        # Single command startup
        if ($Profile -eq "full") {
            Write-Header "Starting Full Stack"
            Invoke-DockerCompose -Args @("up", "-d")
        }
        else {
            Start-ProfileStack -ProfileName $Profile
        }
    }

    # ── Post-startup ──────────────────────────────────────────────────────────
    Show-Status

    # Summary
    $elapsed = [math]::Round(((Get-Date) - $script:StartTime).TotalMinutes, 1)
    Write-Header "Startup Complete"
    Write-Success "Stack is running (took ${elapsed} minutes)"
    Write-Info "Project: $script:ProjectDir"
    Write-Info "Profile: $Profile"

    Write-Host "`n  NEXT STEPS:" -ForegroundColor White
    Write-Host "  • docker compose --env-file .env -f docker-compose.yml ps" -ForegroundColor Cyan
    Write-Host "  • docker compose --env-file .env -f docker-compose.yml logs -f opencode-session" -ForegroundColor Cyan
    Write-Host "  • docker compose --env-file .env -f docker-compose.yml exec opencode-session bash" -ForegroundColor Cyan
    Write-Host "  • ./scripts/self-compose down  # to stop everything" -ForegroundColor Cyan

    if ($Profile -eq "full" -or $Profile -eq "observability") {
        Write-Host "`n  OBSERVABILITY:" -ForegroundColor White
        Write-Host "  • Grafana:  http://localhost:59030 (admin/admin)" -ForegroundColor Green
        Write-Host "  • Prometheus: http://localhost:59090" -ForegroundColor Green
    }
}
catch {
    Write-Error "Stack startup failed: $_"
    Write-Info "Check the error above and try again."
    Write-Info "For help: Get-Help .\Start-CMPLXStack.ps1 -Full"
    exit 1
}

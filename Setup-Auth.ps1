#Requires -Version 5.1
<#
.SYNOPSIS
    CMPLX-PartsFactory Auth & Login Setup
.DESCRIPTION
    Configures all service authentication using existing workspace credentials.
    Handles Docker, GitHub, OpenAI, Discord, npm, and opencode auth.
.NOTES
    Run from D:\PartsFactory\CMPLX-PartsFactory
#>

param(
    [switch]$Force,
    [switch]$DockerHub,
    [string]$DockerHubUser,
    [string]$DockerHubPass,
    [switch]$Silent
)

$ErrorActionPreference = "Stop"

function Write-Header { param([string]$t) Write-Host "`n=== $t ===" -ForegroundColor Cyan }
function Write-Ok { param([string]$t) Write-Host "  OK: $t" -ForegroundColor Green }
function Write-Warn { param([string]$t) Write-Host "  WARN: $t" -ForegroundColor Yellow }
function Write-Err { param([string]$t) Write-Host "  ERR: $t" -ForegroundColor Red }
function Write-Info { param([string]$t) Write-Host "  INFO: $t" -ForegroundColor Gray }

# ═══════════════════════════════════════════════════════════════════════════════
# 1. DOCKER AUTH
# ═══════════════════════════════════════════════════════════════════════════════
Write-Header "Docker Authentication"

# Check Docker Desktop cred helper
$dockerConfig = "$env:USERPROFILE\.docker\config.json"
if (Test-Path $dockerConfig) {
    $dc = Get-Content $dockerConfig -Raw | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($dc.credsStore -or $dc.credsHelpers) {
        Write-Ok "Docker Desktop credential helper is active"
        Write-Info "Docker Hub auth is managed by Docker Desktop"
    }
}

# Test if we can pull (implies auth is working)
Write-Info "Testing Docker registry access..."
try {
    $pullTest = docker pull hello-world 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Docker registry access confirmed"
    }
    else {
        Write-Warn "Docker pull test failed — may need login"
    }
}
catch {
    Write-Warn "Docker not responding: $_"
}

# Docker Hub login if requested
if ($DockerHub) {
    if (-not $DockerHubUser) {
        $DockerHubUser = Read-Host "Docker Hub username"
    }
    if (-not $DockerHubPass) {
        $DockerHubPass = Read-Host "Docker Hub password/token" -AsSecureString
        $DockerHubPass = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($DockerHubPass))
    }
    Write-Info "Logging into Docker Hub..."
    $pullTest | docker login -u $DockerHubUser --password-stdin 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Docker Hub login successful"
    }
    else {
        Write-Err "Docker Hub login failed"
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# 2. GITHUB CLI AUTH
# ═══════════════════════════════════════════════════════════════════════════════
Write-Header "GitHub CLI Authentication"

$ghPath = (Get-Command gh -ErrorAction SilentlyContinue)?.Source
if (-not $ghPath) {
    Write-Warn "GitHub CLI (gh) not found in PATH"
    Write-Info "Install from: https://cli.github.com/"
}
else {
    $ghStatus = gh auth status 2>&1
    if ($ghStatus -match "Logged in to") {
        Write-Ok "GitHub CLI is authenticated"
        $ghStatus | Select-String "Logged in to .* as (.*)" | ForEach-Object {
            Write-Info "Account: $($_.Matches.Groups[1].Value)"
        }
    }
    else {
        Write-Warn "GitHub CLI not authenticated"
        Write-Info "Run: gh auth login"
        if (-not $Silent) {
            $doLogin = Read-Host "Login to GitHub now? [y/N]"
            if ($doLogin -match "^y") {
                gh auth login
            }
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# 3. OPENAI / CODEX AUTH
# ═══════════════════════════════════════════════════════════════════════════════
Write-Header "OpenAI / Codex Authentication"

$codexAuth = "$env:USERPROFILE\.codex\auth.json"
$openaiKey = $null

if (Test-Path $codexAuth) {
    try {
        $auth = Get-Content $codexAuth -Raw | ConvertFrom-Json
        $openaiKey = $auth.tokens.access_token
        $acctId = $auth.tokens.account_id
        $email = $auth.tokens.email
        Write-Ok "Codex auth.json found"
        Write-Info "Account: $email"
        Write-Info "Account ID: $acctId"
        Write-Info "Auth mode: $($auth.auth_mode)"
    }
    catch {
        Write-Warn "Failed to parse Codex auth.json: $_"
    }
}
else {
    Write-Warn "No Codex auth.json found at $codexAuth"
}

# ═══════════════════════════════════════════════════════════════════════════════
# 4. WORKSPACE .env SYNC
# ═══════════════════════════════════════════════════════════════════════════════
Write-Header "Workspace .env Synchronization"

$envFile = ".env"
$envTemplate = ".env.template"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envTemplate) {
        Copy-Item $envTemplate $envFile
        Write-Ok "Created .env from template"
    }
    else {
        Write-Err "No .env or .env.template found"
        exit 1
    }
}

$envContent = Get-Content $envFile -Raw
$modified = $false

# Extract Discord token if present
if ($envContent -match "DISCORD_BOT_TOKEN=(.+)") {
    $discordToken = $matches[1].Trim()
    if ($discordToken -and $discordToken -ne "your_discord_bot_token_here") {
        Write-Ok "Discord token found in .env"
    }
}

# Sync OpenAI token if available
if ($openaiKey -and ($Force -or $envContent -notmatch "OPENAI_API_KEY=.+")) {
    if ($envContent -match "OPENAI_API_KEY=") {
        $envContent = $envContent -replace "OPENAI_API_KEY=.*", "OPENAI_API_KEY=$openaiKey"
    }
    else {
        $envContent += "`nOPENAI_API_KEY=$openaiKey"
    }
    $modified = $true
    Write-Ok "Added OPENAI_API_KEY from Codex auth"
}

# Prompt for missing keys if not silent
if (-not $Silent) {
    if ($envContent -notmatch "GITHUB_TOKEN=.+" -or $envContent -match "GITHUB_TOKEN=\s*\n") {
        $ghToken = Read-Host "GitHub Token (optional, press Enter to skip)"
        if ($ghToken) {
            if ($envContent -match "GITHUB_TOKEN=") {
                $envContent = $envContent -replace "GITHUB_TOKEN=.*", "GITHUB_TOKEN=$ghToken"
            }
            else {
                $envContent += "`nGITHUB_TOKEN=$ghToken"
            }
            $modified = $true
        }
    }

    if ($envContent -notmatch "OPENROUTER_API_KEY=.+" -or $envContent -match "OPENROUTER_API_KEY=\s*\n") {
        $orKey = Read-Host "OpenRouter API Key (optional, press Enter to skip)"
        if ($orKey) {
            if ($envContent -match "OPENROUTER_API_KEY=") {
                $envContent = $envContent -replace "OPENROUTER_API_KEY=.*", "OPENROUTER_API_KEY=$orKey"
            }
            else {
                $envContent += "`nOPENROUTER_API_KEY=$orKey"
            }
            $modified = $true
        }
    }

    if ($envContent -notmatch "OLLAMA_MODEL_GEMMA=.+" -or $envContent -match "OLLAMA_MODEL_GEMMA=\s*\n") {
        $ollamaModel = Read-Host "Ollama default model [gemma3:4b]"
        if (-not $ollamaModel) { $ollamaModel = "gemma3:4b" }
        if ($envContent -match "OLLAMA_MODEL_GEMMA=") {
            $envContent = $envContent -replace "OLLAMA_MODEL_GEMMA=.*", "OLLAMA_MODEL_GEMMA=$ollamaModel"
        }
        else {
            $envContent += "`nOLLAMA_MODEL_GEMMA=$ollamaModel"
        }
        $modified = $true
    }
}

if ($modified) {
    Set-Content $envFile $envContent -NoNewline
    Write-Ok "Updated .env with new credentials"
}
else {
    Write-Ok ".env is up to date"
}

# ═══════════════════════════════════════════════════════════════════════════════
# 5. OPENCODE AUTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════
Write-Header "OpenCode Session Authentication"

$opencodeState = "$env:USERPROFILE\.local\share\opencode"
$opencodeAuth = "$opencodeState\auth.json"

if (Test-Path $opencodeAuth) {
    try {
        $oa = Get-Content $opencodeAuth -Raw | ConvertFrom-Json
        Write-Ok "OpenCode auth.json exists"
        if ($oa.api_key -or $oa.token) {
            Write-Info "OpenCode API key/token configured"
        }
    }
    catch {
        Write-Warn "OpenCode auth.json exists but is invalid"
    }
}
else {
    Write-Warn "No OpenCode auth.json found"
    Write-Info "The opencode-session container will create this on first run"
    Write-Info "Or run 'opencode auth' inside the container after startup"
}

# ═══════════════════════════════════════════════════════════════════════════════
# 6. NPM AUTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════
Write-Header "NPM Authentication"

$npmrc = "$env:USERPROFILE\.npmrc"
if (Test-Path $npmrc) {
    $npmAuth = Select-String "^//registry.npmjs.org/:_authToken=" $npmrc
    if ($npmAuth) {
        Write-Ok "NPM auth token found in .npmrc"
    }
    else {
        Write-Warn "No NPM auth token in .npmrc"
    }
}
else {
    Write-Warn "No .npmrc found"
}

# ═══════════════════════════════════════════════════════════════════════════════
# 7. ENCRYPTED .env.up CHECK (qwen-swarm)
# ═══════════════════════════════════════════════════════════════════════════════
Write-Header "Encrypted Credential Stores"

$envUp = "..\qwen-swarm\qwen-swarm\.env.up"
if (Test-Path $envUp) {
    Write-Ok "Found encrypted .env.up: $envUp"
    Write-Info "Contains: OPENAI_API_KEY, OPENAI_BASE_URL, MODEL_NAME"
    Write-Info "Unlock with: up unlock (if dotenvup CLI is installed)"
}
else {
    Write-Info "No encrypted .env.up found"
}

# ═══════════════════════════════════════════════════════════════════════════════
# 8. SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
Write-Header "Auth Setup Complete"

Write-Host "`n  Service Status:" -ForegroundColor White
Write-Host "  ─────────────────────────────────────────" -ForegroundColor Gray

$dockerOk = (docker info >$null 2>&1; $?)
$ghOk = ($ghStatus -match "Logged in to")
$codexOk = (Test-Path $codexAuth)
$discordOk = ($envContent -match "DISCORD_BOT_TOKEN=.+" -and $envContent -notmatch "DISCORD_BOT_TOKEN=your_")

Write-Host "  Docker Desktop      $(if ($dockerOk) { "[OK]" } else { "[FAIL]" })" -ForegroundColor $(if ($dockerOk) { "Green" } else { "Red" })
Write-Host "  GitHub CLI          $(if ($ghOk) { "[OK]" } else { "[SKIP]" })" -ForegroundColor $(if ($ghOk) { "Green" } else { "Yellow" })
Write-Host "  OpenAI/Codex        $(if ($codexOk) { "[OK]" } else { "[SKIP]" })" -ForegroundColor $(if ($codexOk) { "Green" } else { "Yellow" })
Write-Host "  Discord Bot         $(if ($discordOk) { "[OK]" } else { "[SKIP]" })" -ForegroundColor $(if ($discordOk) { "Green" } else { "Yellow" })
Write-Host "  Workspace .env      [OK]" -ForegroundColor Green
Write-Host "  OpenCode auth       $(if (Test-Path $opencodeAuth) { "[OK]" } else { "[PENDING]" })" -ForegroundColor $(if (Test-Path $opencodeAuth) { "Green" } else { "Yellow" })

Write-Host "`n  Next steps:" -ForegroundColor White
Write-Host "  • docker compose up -d                    # start core services" -ForegroundColor Cyan
Write-Host "  • docker compose --profile full up -d     # start everything" -ForegroundColor Cyan
Write-Host "  • docker compose exec opencode-session bash  # enter container" -ForegroundColor Cyan
Write-Host "`n  Inside the container, run 'opencode auth' to complete OpenCode login." -ForegroundColor Gray

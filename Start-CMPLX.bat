@echo off
REM CMPLX-PartsFactory Startup (Windows Batch)
REM =============================================
REM Connects to EXISTING running services.
REM Only builds: opencode-session, cmplx-unified-api, discord-bridge
REM
REM Usage: Start-CMPLX.bat [ngrok]
REM   Add "ngrok" argument to also start the TCP tunnel

setlocal EnableDelayedExpansion

set "NGROK=%~1"

echo.
echo ============================================
echo  CMPLX-PartsFactory Stack Startup
echo ============================================
echo.

REM Check Docker
echo [1/3] Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running. Start Docker Desktop first.
    exit /b 1
)
echo OK - Docker is running

REM Check compose file
if not exist "docker-compose.yml" (
    echo ERROR: docker-compose.yml not found.
    echo Run this from D:\PartsFactory\CMPLX-PartsFactory
    exit /b 1
)

REM Create .env if missing
if not exist ".env" (
    echo.
    echo [2/3] Creating .env from template...
    if not exist ".env.template" (
        echo ERROR: .env.template not found.
        exit /b 1
    )
    copy /y .env.template .env >nul
    echo OK - .env created. Edit it with your tokens before next run.
) else (
    echo [2/3] .env exists
)

REM Create data directories
if not exist "data\share" mkdir "data\share"
if not exist "data\state" mkdir "data\state"
if not exist "data\config" mkdir "data\config"
if not exist "docker-cache" mkdir "docker-cache"

REM Validate compose
echo.
echo [3/3] Validating compose...
docker compose config >nul 2>&1
if errorlevel 1 (
    echo ERROR: docker-compose.yml is invalid.
    exit /b 1
)
echo OK - Configuration is valid

REM Start stack
echo.
echo Starting CMPLX-PartsFactory services...
echo   (opencode-session, cmplx-unified-api, discord-bridge)
echo   All other services connect to existing running containers.
echo.

docker compose up -d --build

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start.
    echo Try: docker compose up -d --build opencode-session
    exit /b 1
)

REM Start ngrok if requested
if "%NGROK%"=="ngrok" (
    echo.
    echo Starting ngrok tunnel...
    docker compose --profile ngrok up -d
)

echo.
echo ============================================
echo  Stack started!
echo ============================================
echo.
echo New containers:
docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
echo.
echo Access Points:
echo   OpenCode Session:  http://localhost:8080
echo   OpenCode API:      http://localhost:4096
echo   CMPLX Unified API: http://localhost:8851
echo.

if "%NGROK%"=="ngrok" (
    echo Ngrok Dashboard: http://localhost:4040
echo   ^(Check dashboard for public TCP URL^)
echo.
)

echo Existing services connected:
echo   Manny Runtime:     http://localhost:8870
echo   Research API:      http://localhost:3000
echo   MMDB:              http://localhost:8824
echo   MDHG:              http://localhost:8825
echo   SpeedLight:        http://localhost:8843
echo   TarPit:            http://localhost:8844
echo   SNAP:              http://localhost:8823
echo   Manifold:          http://localhost:8840
echo   DB Aggregator:     http://localhost:8815
echo   Postgres:          localhost:5432
echo   Redis:             localhost:6379
echo   RabbitMQ Mgmt:     http://localhost:15672
echo.

pause

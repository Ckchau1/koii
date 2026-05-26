@echo off
REM Koii OS (AIOS) Docker Quick Start Script for Windows
REM Requires Docker Desktop for Windows

setlocal enabledelayedexpansion

REM Check if Docker is installed
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed!
    echo Please install Docker Desktop from: https://docs.docker.com/desktop/install/windows-install/
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check for docker compose
docker compose version >nul 2>nul
if %errorlevel% equ 0 (
    set COMPOSE_CMD=docker compose
) else (
    docker-compose version >nul 2>nul
    if %errorlevel% equ 0 (
        set COMPOSE_CMD=docker-compose
    ) else (
        echo [ERROR] Docker Compose is not available!
        pause
        exit /b 1
    )
)

REM Create necessary directories
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "config" mkdir config

REM Create default agent-config.yaml if it doesn't exist
if not exist "agent-config.yaml" (
    echo [INFO] Creating default agent-config.yaml...
    (
        echo kernel:
        echo   max_agents: 10000
        echo   tick_ms: 1
        echo.
        echo llm:
        echo   default_provider: mock
        echo   providers:
        echo     mock:
        echo       type: mock
        echo.
        echo agents:
        echo   - name: system-monitor
        echo     type: system
        echo     roles: [monitor]
        echo.
        echo persistence:
        echo   backend: sqlite
        echo   sqlite:
        echo     path: data/koii_os.db
        echo.
        echo transport:
        echo   type: inmemory
        echo.
        echo security:
        echo   zero_trust: true
    ) > agent-config.yaml
)

REM Create .env template if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating .env template...
    (
        echo # Koii OS Environment Configuration
        echo # Add your API keys here
        echo.
        echo # OpenAI API Key ^(optional^)
        echo # OPENAI_API_KEY=sk-proj-your-key-here
        echo.
        echo # Anthropic API Key ^(optional^)
        echo # ANTHROPIC_API_KEY=sk-ant-your-key-here
        echo.
        echo # NATS Configuration ^(optional^)
        echo # NATS_URL=nats://nats:4222
        echo.
        echo # Browser Configuration ^(optional^)
        echo # KOII_BROWSER_BACKEND=playwright
    ) > .env
)

REM Main menu
:menu
cls
echo.
echo ========================================
echo    Koii OS (AIOS) Control Center v2.0
echo ========================================
echo.
echo === Browser (Koii OS) ===
echo 20) Launch Browser (Native)
echo 21) Build Browser (Native)
echo 22) Launch Browser (Docker)
echo 23) Build Browser (Docker)
echo.
echo === Docker Services ===
echo 1) Start AIOS (with Browser ^& Services)
echo 2) Stop AIOS
echo 3) Restart AIOS
echo 4) View logs
echo 5) Rebuild containers
echo 6) Clean up (remove containers and volumes)
echo 7) Show status
echo 8) Open Web UI
echo 9) Enter container shell (AIOS)
echo.
echo === Browser-specific ===
echo 10) View Browser logs
echo 11) Rebuild Browser only
echo 12) Restart Browser container
echo.
echo 0) Exit
echo.

set /p choice="Select an option: "

if "%choice%"=="20" goto browser_native
if "%choice%"=="21" goto build_browser_native
if "%choice%"=="22" goto browser_docker
if "%choice%"=="23" goto build_browser_docker
if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto rebuild
if "%choice%"=="6" goto cleanup
if "%choice%"=="7" goto status
if "%choice%"=="8" goto webui
if "%choice%"=="9" goto shell
if "%choice%"=="10" goto browser_logs
if "%choice%"=="11" goto rebuild_browser
if "%choice%"=="12" goto restart_browser
if "%choice%"=="0" goto end

echo Invalid option. Please try again.
pause
goto menu

:build_browser_native
echo.
echo [INFO] Building Koii OS Browser (Native)...
echo This may take 3-5 minutes. Please wait.
echo.
cd src\koii_os\browser\core
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed! Please install from https://nodejs.org
    cd ..\..\..\..
    pause
    goto menu
)
if not exist "node_modules" (
    echo [INFO] Installing dependencies...
    npm install
)
echo [INFO] Building browser...
npm run build
echo [INFO] Packaging (this takes a while)...
npx electron-builder --win portable --publish=never
cd ..\..\..\..
echo.
echo [SUCCESS] Browser built in src\koii_os\browser\core\dist\
pause
goto menu

:browser_native
echo.
echo [INFO] Launching Koii OS Browser (Native)...
cd src\koii_os\browser\core
if not exist "node_modules" (
    echo [INFO] Installing dependencies...
    npm install
)
echo [INFO] Starting browser...
npx electron . &
cd ..\..\..\..
echo [SUCCESS] Browser launched!
timeout /t 2
goto menu

:build_browser_docker
echo.
echo [INFO] Building Koii OS Browser Docker image...
echo.
docker build -f Dockerfile.browser -t koii-browser:latest .
if %errorlevel% equ 0 (
    echo [SUCCESS] Browser Docker image built!
) else (
    echo [ERROR] Build failed!
)
pause
goto menu

:browser_docker
echo.
echo [INFO] Starting Koii OS Browser in Docker...
%COMPOSE_CMD% up -d koii-browser
if %errorlevel% equ 0 (
    echo [SUCCESS] Browser started!
    echo Access at: http://localhost:3000
) else (
    echo [ERROR] Failed to start browser!
)
pause
goto menu

:browser_logs
echo.
echo [INFO] Browser logs (Ctrl+C to exit)...
%COMPOSE_CMD% logs -f koii-browser
pause
goto menu

:rebuild_browser
echo.
echo [INFO] Rebuilding Browser container...
%COMPOSE_CMD% build --no-cache koii-browser
echo [SUCCESS] Browser rebuilt
pause
goto menu

:restart_browser
echo.
echo [INFO] Restarting Browser...
%COMPOSE_CMD% restart koii-browser
echo [SUCCESS] Browser restarted
pause
goto menu

:start
echo.
echo [INFO] Starting Koii OS with Browser...
%COMPOSE_CMD% up -d
echo.
echo [SUCCESS] Services are running!
echo AIOS Web UI: http://localhost:8000
echo Browser UI: http://localhost:3000
echo NATS Monitor: http://localhost:8222
echo.
pause
goto menu

:stop
echo.
echo [INFO] Stopping Koii OS...
%COMPOSE_CMD% down
echo [SUCCESS] Koii OS stopped
pause
goto menu

:restart
echo.
echo [INFO] Restarting Koii OS...
%COMPOSE_CMD% restart
echo [SUCCESS] Koii OS restarted
pause
goto menu

:logs
echo.
echo [INFO] Viewing logs (Ctrl+C to exit)...
%COMPOSE_CMD% logs -f
pause
goto menu

:rebuild
echo.
echo [INFO] Rebuilding containers...
%COMPOSE_CMD% down
%COMPOSE_CMD% build --no-cache
%COMPOSE_CMD% up -d
echo [SUCCESS] Containers rebuilt and started
pause
goto menu

:cleanup
echo.
echo [WARNING] This will remove all containers, volumes, and data!
set /p confirm="Are you sure? (yes/no): "
if /i "%confirm%"=="yes" (
    echo [INFO] Cleaning up...
    %COMPOSE_CMD% down -v
    echo [SUCCESS] Cleanup complete
) else (
    echo Cleanup cancelled
)
pause
goto menu

:status
echo.
echo [INFO] Service Status:
%COMPOSE_CMD% ps
pause
goto menu

:webui
echo.
echo [INFO] Opening Web UI...
start http://localhost:8000
pause
goto menu

:shell
echo.
echo [INFO] Entering container shell...
docker exec -it koii-aios /bin/bash
pause
goto menu

:end
echo.
echo Goodbye!
exit /b 0

@REM Made with Bob

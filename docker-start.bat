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
echo    Koii OS (AIOS) Control Center
echo ========================================
echo.
echo === Browser ===
echo 10) Start AI Min Browser (Native)
echo 11) Build AI Min Browser (.exe)
echo.
echo === Docker Services ===
echo 1) Start AIOS (with Web UI)
echo 2) Stop AIOS
echo 3) Restart AIOS
echo 4) View logs
echo 5) Rebuild containers
echo 6) Clean up (remove containers and volumes)
echo 7) Show status
echo 8) Open Web UI
echo 9) Enter container shell
echo.
echo 0) Exit
echo.

set /p choice="Select an option: "

if "%choice%"=="10" goto browser
if "%choice%"=="11" goto build_browser
if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto rebuild
if "%choice%"=="6" goto cleanup
if "%choice%"=="7" goto status
if "%choice%"=="8" goto webui
if "%choice%"=="9" goto shell
if "%choice%"=="0" goto end

echo Invalid option. Please try again.
pause
goto menu

:build_browser
echo.
echo [INFO] Building AI Min Browser...
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
echo [INFO] Building browser bundles...
npm run build
echo [INFO] Packaging .exe (this takes a while)...
npx electron-builder --win portable --publish=never
cd ..\..\..\..
echo.
if exist "src\koii_os\browser\core\dist\app\Min 1.35.5.exe" (
    echo [SUCCESS] Browser built: src\koii_os\browser\core\dist\app\Min 1.35.5.exe
) else (
    echo [ERROR] Build failed. Check the output above for errors.
)
pause
goto menu

:browser
echo.
set BROWSER_EXE=src\koii_os\browser\core\dist\app\Min 1.35.5.exe
if not exist "%BROWSER_EXE%" (
    echo [ERROR] Browser executable not found!
    echo Expected location: %BROWSER_EXE%
    echo.
    echo Please build the browser first:
    echo   cd src\koii_os\browser\core
    echo   npm run build
    echo   npx electron-builder --win portable --publish=never
    echo.
    pause
    goto menu
)
echo [INFO] Launching AI Min Browser...
start "" "%BROWSER_EXE%"
echo [SUCCESS] Browser launched!
timeout /t 2
goto menu

:start
echo.
echo [INFO] Starting Koii OS...
%COMPOSE_CMD% up -d
echo.
echo [SUCCESS] Koii OS is running!
echo Web UI: http://localhost:8000
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

@echo off
REM Koii OS Browser - Build Script for Windows
REM Creates standalone EXE files

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Koii OS Browser - Build EXE for Windows
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed!
    echo Please install from: https://nodejs.org
    pause
    exit /b 1
)

REM Check Node version
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo [INFO] Node.js version: %NODE_VERSION%

REM Check npm is installed
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed!
    pause
    exit /b 1
)

REM Show menu
:menu
cls
echo.
echo ========================================
echo       Build Options
echo ========================================
echo.
echo 1) Install dependencies (first time only)
echo 2) Build React app only
echo 3) Build Portable EXE (single file, no install)
echo 4) Build Installer EXE (professional setup)
echo 5) Build both (Portable + Installer)
echo 6) Clean build (remove build/dist folders)
echo 7) Full clean and rebuild
echo 8) Run app in Electron (dev mode)
echo.
echo 0) Exit
echo.

set /p choice="Select an option: "

if "%choice%"=="1" goto install
if "%choice%"=="2" goto build_react
if "%choice%"=="3" goto build_portable
if "%choice%"=="4" goto build_installer
if "%choice%"=="5" goto build_both
if "%choice%"=="6" goto clean
if "%choice%"=="7" goto full_clean
if "%choice%"=="8" goto dev_run
if "%choice%"=="0" goto end

echo Invalid option. Please try again.
pause
goto menu

:install
echo.
echo [INFO] Installing dependencies...
echo This may take 5-10 minutes. Please wait.
echo.
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed!
    pause
    goto menu
)
echo [SUCCESS] Dependencies installed!
pause
goto menu

:build_react
echo.
echo [INFO] Building React application...
echo This may take 2-3 minutes. Please wait.
echo.
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    echo Check output above for errors.
    pause
    goto menu
)
echo [SUCCESS] React build complete!
echo Output: build/
pause
goto menu

:build_portable
echo.
echo [INFO] Building Portable EXE...
echo This may take 3-5 minutes. Please wait.
echo.
if not exist "build" (
    echo [INFO] React app not built yet. Building now...
    call npm run build
    if %errorlevel% neq 0 (
        echo [ERROR] React build failed!
        pause
        goto menu
    )
)
echo [INFO] Creating portable executable...
call npm run dist:win
if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    pause
    goto menu
)
echo.
echo [SUCCESS] Portable EXE created!
if exist "dist\Koii OS Browser-0.1.0.exe" (
    echo Location: dist\Koii OS Browser-0.1.0.exe
    echo Size: ~190MB
    echo Features: Single file, no installation needed
) else (
    echo Check dist/ folder for output
)
pause
goto menu

:build_installer
echo.
echo [INFO] Building Installer EXE...
echo This may take 3-5 minutes. Please wait.
echo.
if not exist "build" (
    echo [INFO] React app not built yet. Building now...
    call npm run build
    if %errorlevel% neq 0 (
        echo [ERROR] React build failed!
        pause
        goto menu
    )
)
echo [INFO] Creating installer...
call npm run electron-builder:win
if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    pause
    goto menu
)
echo.
echo [SUCCESS] Installer EXE created!
echo Location: dist\Koii OS Browser-0.1.0-setup.exe
echo Features: Professional installer, Start Menu shortcuts, Uninstaller
pause
goto menu

:build_both
echo.
echo [INFO] Building both Portable and Installer EXE...
echo This may take 5-10 minutes. Please wait.
echo.
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    pause
    goto menu
)
echo.
echo [INFO] Creating portable executable...
call npm run dist:win
if %errorlevel% neq 0 (
    echo [ERROR] Portable build failed!
    pause
    goto menu
)
echo.
echo [INFO] Creating installer...
call npm run electron-builder:win
if %errorlevel% neq 0 (
    echo [ERROR] Installer build failed!
    pause
    goto menu
)
echo.
echo [SUCCESS] Both versions created!
echo.
echo Portable (single file):
echo   Location: dist\Koii OS Browser-0.1.0.exe
echo   Size: ~190MB
echo.
echo Installer (professional):
echo   Location: dist\Koii OS Browser-0.1.0-setup.exe
echo   Size: ~160MB
echo.
pause
goto menu

:clean
echo.
echo [INFO] Cleaning build and dist folders...
echo.
if exist "build" (
    echo Removing build folder...
    rmdir /s /q build
    echo [OK] build/ removed
)
if exist "dist" (
    echo Removing dist folder...
    rmdir /s /q dist
    echo [OK] dist/ removed
)
echo [SUCCESS] Cleanup complete!
pause
goto menu

:full_clean
echo.
echo [WARNING] This will remove node_modules, build, and dist!
echo.
set /p confirm="Are you sure? Type 'yes' to continue: "
if /i not "%confirm%"=="yes" (
    echo Cancelled.
    pause
    goto menu
)
echo.
echo [INFO] Performing full cleanup...
if exist "node_modules" (
    echo Removing node_modules...
    rmdir /s /q node_modules
    echo [OK] node_modules/ removed
)
if exist "build" (
    echo Removing build folder...
    rmdir /s /q build
    echo [OK] build/ removed
)
if exist "dist" (
    echo Removing dist folder...
    rmdir /s /q dist
    echo [OK] dist/ removed
)
echo.
echo [INFO] Reinstalling dependencies...
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed!
    pause
    goto menu
)
echo.
echo [INFO] Building React app...
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    pause
    goto menu
)
echo.
echo [SUCCESS] Full rebuild complete!
pause
goto menu

:dev_run
echo.
echo [INFO] Starting Koii OS Browser in development mode...
echo.
echo This will:
echo 1. Start React dev server on port 3000
echo 2. Launch Electron window
echo 3. Auto-reload on code changes
echo.
echo Press Ctrl+C to stop.
echo.
call npm run dev
pause
goto menu

:end
echo.
echo Thank you for using Koii OS Browser!
echo.
exit /b 0

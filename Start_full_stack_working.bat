@echo off
SETLOCAL EnableDelayedExpansion

:: Force change to the directory where this batch file is located
cd /d "%~dp0"

:: ===============================================
::  Start Full Stack – Backend, Frontend & Bridge
:: ===============================================

echo ====================================================
echo Starting Ambient Transcription App – Full Stack
echo ====================================================
echo Project directory: %CD%
echo Parent directory: %~dp0..
echo.

:: ---------- Check all prerequisites ----------
echo [INFO] Checking prerequisites...

:: Check for venv in parent directory
echo [INFO] Checking for Python virtual environment...
if exist "..\venv" (
    echo [SUCCESS] Python virtual environment found at: %~dp0..\venv
    set "VENV_PATH=%~dp0..\venv"
) else (
    if exist "venv" (
        echo [SUCCESS] Python virtual environment found at: %CD%\venv
        set "VENV_PATH=%CD%\venv"
    ) else (
        echo [ERROR] Python virtual environment ^(venv^) not found in:
        echo [ERROR]   - %CD%\venv
        echo [ERROR]   - %~dp0..\venv
        echo [ERROR] Please run setup.bat to create the virtual environment.
        echo.
        pause
        exit /b 1
    )
)

echo [INFO] Checking if frontend directory exists...
if exist "frontend" (
    echo [SUCCESS] Frontend directory found at: %CD%\frontend
) else (
    echo [ERROR] 'frontend' directory not found in: %CD%
    echo [ERROR] Please ensure the Angular frontend is available.
    echo.
    pause
    exit /b 1
)

echo [INFO] Checking for Node.js...
node --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js not detected in PATH.
    echo [ERROR] Please install Node.js to run the frontend.
    echo [ERROR] Download from: https://nodejs.org/
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node --version') do echo [SUCCESS] Node.js version: %%i
)

:: ---------- Optional: Check Ollama service ----------
echo [INFO] Checking Ollama service...
curl http://localhost:11434/api/tags > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Ollama service not detected on localhost:11434.
    echo          You can ignore this if you are not using local LLMs.
) else (
    echo [SUCCESS] Ollama service running.
)

:: Use absolute path to repo root
for %%d in ("%~dp0.") do set "REPO_DIR=%%~fd"
echo [DEBUG] REPO_DIR set to: %REPO_DIR%
echo [DEBUG] VENV_PATH set to: %VENV_PATH%

echo.
echo ====================================================
echo All checks passed! Press any key to launch services...
pause

:: Start Ollama API bridge
echo [INFO] Starting Ollama API bridge window...
start "Ollama Bridge" cmd /k "cd /d \"%REPO_DIR%\" && call \"%VENV_PATH%\Scripts\activate.bat\" && python ollama_bridge.py"

:: Wait a moment for the first window to start
timeout /t 3 > nul

:: Start FastAPI backend
echo [INFO] Starting FastAPI backend window...
start "Backend API" cmd /k "cd /d \"%REPO_DIR%\" && call \"%VENV_PATH%\Scripts\activate.bat\" && uvicorn backend.main:app --reload"

:: Wait a moment for the second window to start
timeout /t 3 > nul

:: Start Angular dev server in its own window
echo [INFO] Starting Angular frontend...
start "Frontend" cmd /k "cd /d \"%REPO_DIR%\frontend\" && npm start"

:: ---------- Summary --------------------------------
echo.
echo ====================================================
echo [SUCCESS] All services launched in separate windows:
echo   1. Ollama Bridge (port 8000)
echo   2. Backend API (port 8000)  
echo   3. Frontend (port 4200)
echo ====================================================
echo.
echo This window will stay open. Press any key to close it.
echo (The services will continue running in their own windows)
pause
ENDLOCAL 
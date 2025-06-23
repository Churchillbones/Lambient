@echo off
echo ====================================================
echo Simple Ambient Transcription App Launcher
echo ====================================================

:: Change to the script directory
cd /d "%~dp0"

:: Check if venv exists
if not exist "venv" (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

:: Check if backend exists
if not exist "backend" (
    echo [ERROR] Backend directory not found.
    pause
    exit /b 1
)

:: Check if frontend exists
if not exist "frontend" (
    echo [ERROR] Frontend directory not found.
    pause
    exit /b 1
)

echo [INFO] Starting services...

:: Start Ollama Bridge
echo [INFO] Starting Ollama Bridge...
start "Ollama Bridge" cmd /k "cd /d "%~dp0" && venv\Scripts\activate && python ollama_bridge.py"

:: Wait a moment
timeout /t 2 >nul

:: Start Backend
echo [INFO] Starting Backend API...
start "Backend API" cmd /k "cd /d "%~dp0" && venv\Scripts\activate && uvicorn backend.main:app --reload"

:: Wait a moment
timeout /t 2 >nul

:: Start Frontend
echo [INFO] Starting Frontend...
start "Frontend" cmd /k "cd /d "%~dp0\frontend" && npm start"

echo.
echo [SUCCESS] All services started in separate windows!
echo - Ollama Bridge: Check first window
echo - Backend API: Check second window  
echo - Frontend: Check third window (will open browser at http://localhost:4200)
echo.
echo Press any key to close this launcher...
pause >nul 
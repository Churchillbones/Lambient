@echo off
echo ====================================================
echo Simple Ambient Transcription App Launcher
echo (Using venv from parent directory)
echo ====================================================

:: Change to the script directory
cd /d "%~dp0"

:: Check if venv exists in parent directory
if not exist "..\venv" (
    echo [ERROR] Virtual environment not found in parent directory.
    echo Expected location: %~dp0..\venv
    echo Please ensure the venv exists in the parent folder.
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

echo [INFO] Using virtual environment from: %~dp0..\venv
echo [INFO] Project directory: %CD%
echo [INFO] Starting services...

:: Start Ollama Bridge
echo [INFO] Starting Ollama Bridge...
start "Ollama Bridge" cmd /k "cd /d "%~dp0" && call "..\venv\Scripts\activate.bat" && python ollama_bridge.py"

:: Wait a moment
timeout /t 2 >nul

:: Start Backend
echo [INFO] Starting Backend API...
start "Backend API" cmd /k "cd /d "%~dp0" && call "..\venv\Scripts\activate.bat" && uvicorn backend.main:app --reload"

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
echo Virtual environment location: %~dp0..\venv
echo Project directory: %CD%
echo.
echo Press any key to close this launcher...
pause >nul 
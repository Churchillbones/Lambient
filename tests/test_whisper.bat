@echo off
SETLOCAL EnableDelayedExpansion

echo ====================================================
echo Testing Whisper Functionality
echo ====================================================

:: Change to the directory where this batch file is located
cd /d "%~dp0"

:: Check if virtual environment exists
if exist "..\venv" (
    echo [INFO] Using virtual environment from parent directory
    call "..\venv\Scripts\activate.bat"
) else (
    if exist "venv" (
        echo [INFO] Using virtual environment from current directory
        call "venv\Scripts\activate.bat"
    ) else (
        echo [WARNING] No virtual environment found. Using system Python.
    )
)

:: Run the test
echo [INFO] Running Whisper test suite...
python test_whisper.py

echo.
echo [INFO] Test completed. Press any key to exit.
pause

ENDLOCAL 
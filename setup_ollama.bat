@echo off
SETLOCAL EnableDelayedExpansion

echo ====================================================
echo Ollama Setup for Medical Transcription App
echo ====================================================
echo.

:: Check if Ollama is already installed
echo [INFO] Checking if Ollama is installed...
ollama --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Ollama is already installed!
    for /f "tokens=*" %%i in ('ollama --version') do echo [INFO] %%i
    goto CHECK_SERVICE
) else (
    echo [WARNING] Ollama not found in PATH.
    echo.
    echo Please install Ollama manually:
    echo 1. Go to https://ollama.com/download
    echo 2. Download and run the Windows installer
    echo 3. Restart this script after installation
    echo.
    choice /C YN /M "Do you want to continue anyway (if you just installed Ollama)?"
    if !ERRORLEVEL! EQU 2 (
        echo [INFO] Exiting setup. Please install Ollama first.
        pause
        exit /b 1
    )
)

:CHECK_SERVICE
echo.
echo [INFO] Checking if Ollama service is running...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Ollama service is not running.
    echo [INFO] Starting Ollama service...
    start "Ollama Service" cmd /c "ollama serve"
    echo [INFO] Waiting for service to start...
    timeout /t 5 >nul
    
    :: Check again
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to start Ollama service.
        echo Please start Ollama manually by running: ollama serve
        pause
        exit /b 1
    )
)

echo [SUCCESS] Ollama service is running!
echo.

:: Check what models are already installed
echo [INFO] Checking installed models...
for /f "tokens=*" %%i in ('ollama list 2^>nul') do (
    echo [INFO] Found model: %%i
    set "HAS_MODELS=1"
)

if not defined HAS_MODELS (
    echo [INFO] No models found. Installing recommended model...
    echo.
    echo Recommended models for medical transcription:
    echo 1. gemma3:4b (Small, fast - ~4GB RAM)
    echo 2. deepseek-r1:14b (Large, powerful - ~14GB RAM)
    echo 3. llama3:latest (General purpose)
    echo.
    choice /C 123 /M "Which model would you like to install? (1=gemma3:4b, 2=deepseek-r1:14b, 3=llama3)"
    
    if !ERRORLEVEL! EQU 1 (
        set "MODEL=gemma3:4b"
    ) else if !ERRORLEVEL! EQU 2 (
        set "MODEL=deepseek-r1:14b"
    ) else (
        set "MODEL=llama3:latest"
    )
    
    echo [INFO] Installing !MODEL!...
    echo This may take several minutes depending on your internet connection.
    ollama pull !MODEL!
    
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to install model !MODEL!
        pause
        exit /b 1
    )
    
    echo [SUCCESS] Model !MODEL! installed successfully!
) else (
    echo [SUCCESS] Models are already installed.
)

echo.
echo [INFO] Testing Ollama connection...
curl -s -X POST http://localhost:11434/api/generate ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"gemma3:4b\",\"prompt\":\"Hello\",\"stream\":false}" >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Ollama API is working correctly!
) else (
    echo [WARNING] Could not test API connection. This might be normal if the model isn't gemma3:4b.
)

echo.
echo ====================================================
echo Ollama Setup Complete!
echo ====================================================
echo.
echo Next steps:
echo 1. Make sure the Ollama service stays running (ollama serve)
echo 2. In your Angular app, select "Local LLM Model" in the sidebar
echo 3. Choose your preferred model from the dropdown
echo 4. Start recording and generating notes!
echo.
echo To start the full application stack, run:
echo   Start_full_stack_working.bat
echo.
pause

ENDLOCAL 
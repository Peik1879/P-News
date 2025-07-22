@echo off
title Premium News Analyzer - GUI Edition
color 0A

echo.
echo ========================================
echo   🗞️  PREMIUM NEWS ANALYZER - GUI    
echo ========================================
echo.
echo Starting GUI application...
echo.

REM Aktiviere Virtual Environment
if exist ".\.venv\Scripts\activate.ps1" (
    echo Activating virtual environment...
    powershell -ExecutionPolicy Bypass -Command ".\.venv\Scripts\activate.ps1; python news_gui.py"
) else if exist ".\.venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .\.venv\Scripts\activate.bat
    python news_gui.py
) else (
    echo No virtual environment found. Running with system Python...
    python news_gui.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Error occurred while starting the application.
    echo.
    echo Troubleshooting:
    echo 1. Make sure Python is installed
    echo 2. Check if virtual environment is set up
    echo 3. Verify all dependencies are installed
    echo.
    echo Run this to set up dependencies:
    echo    pip install -r requirements.txt
    echo.
)

echo.
echo Press any key to exit...
pause >nul

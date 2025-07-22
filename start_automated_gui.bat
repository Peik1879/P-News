@echo off
title Premium News Analyzer - Automated GUI Edition
color 0A

echo.
echo ========================================
echo   🗞️  AUTOMATED NEWS ANALYZER GUI    
echo ========================================
echo.
echo Starting automated GUI with integrated scheduler...
echo.
echo Features:
echo - Automatische Updates 6x täglich
echo - Breaking News Check alle 30 Minuten
echo - Mobile Notifications via Pushbullet
echo - Live Activity Log
echo - Manual override controls
echo.

REM Aktiviere Virtual Environment
if exist ".\.venv\Scripts\activate.ps1" (
    echo Activating virtual environment...
    powershell -ExecutionPolicy Bypass -Command ".\.venv\Scripts\activate.ps1; python news_gui_automated.py"
) else if exist ".\.venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .\.venv\Scripts\activate.bat
    python news_gui_automated.py
) else (
    echo No virtual environment found. Running with system Python...
    python news_gui_automated.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Error occurred while starting the application.
    echo.
    echo Troubleshooting:
    echo 1. Make sure Python is installed
    echo 2. Check if virtual environment is set up
    echo 3. Verify all dependencies are installed
    echo 4. Check your .env configuration
    echo.
    echo Run this to check dependencies:
    echo    pip install -r requirements.txt
    echo.
)

echo.
echo Press any key to exit...
pause >nul

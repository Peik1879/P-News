@echo off
title News Scheduler - Automatische Mobile Notifications
color 0A

echo.
echo ========================================
echo   📱 NEWS SCHEDULER - AUTO NOTIFICATIONS
echo ========================================
echo.
echo Automatische News-Analyse mit Mobile Notifications:
echo.
echo ⏰ 6x täglich: 06:00, 09:00, 12:00, 15:00, 18:00, 21:00
echo 🚨 Breaking News Check: Alle 30 Minuten
echo 📊 Tägliche Zusammenfassung: 08:00
echo 📱 Pushbullet Notifications: Aktiviert
echo.

REM Aktiviere Virtual Environment
if exist ".\.venv\Scripts\activate.ps1" (
    echo Activating virtual environment...
    powershell -ExecutionPolicy Bypass -Command ".\.venv\Scripts\activate.ps1; python news_scheduler.py"
) else if exist ".\.venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .\.venv\Scripts\activate.bat
    python news_scheduler.py
) else (
    echo No virtual environment found. Running with system Python...
    python news_scheduler.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Error occurred while starting the scheduler.
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

@echo off
echo ========================================
echo    News-Analyzer Starter
echo ========================================
echo.

REM Aktiviere die virtuelle Umgebung falls vorhanden
if exist ".venv\Scripts\activate.bat" (
    echo Aktiviere virtuelle Umgebung...
    call .venv\Scripts\activate.bat
    echo Virtuelle Umgebung aktiviert.
) else (
    echo WARNUNG: Virtuelle Umgebung nicht gefunden!
    echo Verwende System-Python...
)

REM Überprüfe ob Python verfügbar ist
python --version >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python ist nicht installiert oder nicht im PATH!
    echo Bitte installieren Sie Python von https://python.org
    pause
    exit /b 1
)

REM Überprüfe ob requirements installiert sind
python -c "import feedparser" >nul 2>&1
if errorlevel 1 (
    echo Installiere benötigte Pakete...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo FEHLER: Installation der Pakete fehlgeschlagen!
        pause
        exit /b 1
    )
)

REM Überprüfe .env Datei
if not exist ".env" (
    echo WARNUNG: .env Datei nicht gefunden!
    echo Bitte konfigurieren Sie Ihren OpenAI API Key in der .env Datei.
    echo.
)

echo Starte News-Analyzer GUI...
echo.
python news_gui_automated.py

echo.
echo ========================================
echo Programm beendet. Drücken Sie eine Taste zum Schließen.
pause >nul

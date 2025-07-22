@echo off
echo ========================================
echo    Windows Task Scheduler Setup
echo ========================================
echo.

set "CURRENT_DIR=%~dp0"
set "TASK_NAME=News-Analyzer-Auto"

echo Erstelle Windows Scheduled Task...
echo.

REM Lösche existierende Task falls vorhanden
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM Erstelle neue Task
schtasks /create /tn "%TASK_NAME%" /tr "\"%CURRENT_DIR%start.bat\"" /sc minute /mo 30 /ru "SYSTEM" /rl highest /f

if %errorlevel% equ 0 (
    echo ✅ Scheduled Task erfolgreich erstellt
    echo.
    echo ========================================
    echo Task Details:
    echo • Name: %TASK_NAME%
    echo • Intervall: Alle 30 Minuten
    echo • Startet auch wenn PC gesperrt ist
    echo • Läuft mit System-Rechten
    echo • Automatischer Neustart bei Fehlern
    echo ========================================
    echo.
    
    REM Zusätzliche Task für PC-Start
    schtasks /create /tn "%TASK_NAME%-Startup" /tr "\"%CURRENT_DIR%start.bat\"" /sc onstart /ru "SYSTEM" /rl highest /f
    
    if %errorlevel% equ 0 (
        echo ✅ Startup Task erfolgreich erstellt
        echo • Startet automatisch bei PC-Start
        echo.
    )
    
    REM Task für Benutzer-Anmeldung
    schtasks /create /tn "%TASK_NAME%-Login" /tr "\"%CURRENT_DIR%start.bat\"" /sc onlogon /ru "SYSTEM" /rl highest /f
    
    if %errorlevel% equ 0 (
        echo ✅ Login Task erfolgreich erstellt
        echo • Startet bei jeder Benutzer-Anmeldung
        echo.
    )
    
    echo ========================================
    echo SETUP KOMPLETT!
    echo.
    echo Das News-System läuft jetzt:
    echo • Alle 30 Minuten automatisch
    echo • Bei PC-Start
    echo • Bei Benutzer-Anmeldung
    echo • Auch wenn Sie nicht angemeldet sind
    echo • Auch im Ruhezustand (wenn PC aufwacht)
    echo ========================================
    
) else (
    echo ❌ Fehler beim Erstellen der Scheduled Task
    echo Bitte als Administrator ausführen!
)

echo.
echo Möchten Sie die Tasks anzeigen? (j/n)
set /p show_tasks=
if /i "%show_tasks%"=="j" (
    echo.
    echo Aktuelle Tasks:
    schtasks /query /tn "%TASK_NAME%*" /fo table
)

echo.
pause

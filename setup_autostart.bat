@echo off
echo ========================================
echo    News-Analyzer Autostart Setup
echo ========================================
echo.

REM Aktuelles Verzeichnis speichern
set "CURRENT_DIR=%~dp0"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

echo Erstelle Autostart-Verknüpfung...
echo.

REM Erstelle VBS-Script für unsichtbaren Start
echo Set WshShell = CreateObject("WScript.Shell") > "%CURRENT_DIR%start_hidden.vbs"
echo WshShell.Run chr(34) ^& "%CURRENT_DIR%start.bat" ^& Chr(34), 0 >> "%CURRENT_DIR%start_hidden.vbs"
echo Set WshShell = Nothing >> "%CURRENT_DIR%start_hidden.vbs"

REM Erstelle Autostart-Verknüpfung
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\News-Analyzer.lnk'); $Shortcut.TargetPath = '%CURRENT_DIR%start_hidden.vbs'; $Shortcut.WorkingDirectory = '%CURRENT_DIR%'; $Shortcut.Description = 'Automatischer News-Analyzer Start'; $Shortcut.Save()"

if exist "%STARTUP_FOLDER%\News-Analyzer.lnk" (
    echo ✅ Autostart-Verknüpfung erstellt
    echo 📁 Ort: %STARTUP_FOLDER%
    echo.
    echo ========================================
    echo Das News-Analyzer System startet jetzt automatisch:
    echo • Bei jedem PC-Start
    echo • Nach Neustart
    echo • Nach Ruhezustand
    echo ========================================
) else (
    echo ❌ Fehler beim Erstellen der Autostart-Verknüpfung
)

echo.
pause

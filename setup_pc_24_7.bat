@echo off
echo ========================================
echo    PC Energieeinstellungen für News-Analyzer
echo ========================================
echo.

echo Konfiguriere PC-Energieeinstellungen für 24/7 Betrieb...
echo.

REM Deaktiviere Ruhezustand
powercfg -h off
if %errorlevel% equ 0 (
    echo ✅ Ruhezustand deaktiviert
) else (
    echo ❌ Fehler beim Deaktivieren des Ruhezustands ^(Admin-Rechte erforderlich^)
)

REM Setze Energieplan auf "Höchstleistung"
powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
if %errorlevel% equ 0 (
    echo ✅ Energieplan auf Höchstleistung gesetzt
) else (
    echo ❌ Fehler beim Setzen des Energieplans
)

REM Deaktiviere Monitor-Standby (Monitor kann ausgehen, PC läuft weiter)
powercfg -change -monitor-timeout-ac 0
powercfg -change -monitor-timeout-dc 0
echo ✅ Monitor-Standby deaktiviert

REM Deaktiviere Festplatten-Standby
powercfg -change -disk-timeout-ac 0
powercfg -change -disk-timeout-dc 0
echo ✅ Festplatten-Standby deaktiviert

REM Deaktiviere Systemruhezustand
powercfg -change -standby-timeout-ac 0
powercfg -change -standby-timeout-dc 0
echo ✅ System-Ruhezustand deaktiviert

echo.
echo ========================================
echo PC ist jetzt für 24/7 Betrieb konfiguriert!
echo Der Monitor kann ausgehen, aber der PC läuft weiter.
echo ========================================
echo.
pause

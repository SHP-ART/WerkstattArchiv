@echo off
REM ============================================================
REM WerkstattArchiv Starter MIT KONSOLE (für Debugging)
REM ============================================================

cd /d %~dp0

REM Pruefe ob venv existiert
if not exist venv (
    echo FEHLER: Virtuelle Umgebung nicht gefunden!
    echo Bitte zuerst "install.bat" ausfuehren!
    echo.
    pause
    exit /b 1
)

echo ============================================================
echo WerkstattArchiv wird gestartet...
echo ============================================================
echo.

REM Aktiviere venv und starte Anwendung
call venv\Scripts\activate.bat
python main.py

REM Fehlerbehandlung
if %errorLevel% neq 0 (
    echo.
    echo FEHLER: Anwendung konnte nicht gestartet werden!
    echo Fehlercode: %errorLevel%
    echo.
    pause
) else (
    echo.
    echo Anwendung wurde beendet.
    pause
)

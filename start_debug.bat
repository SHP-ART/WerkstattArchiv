@echo off
REM ============================================================
REM WerkstattArchiv Starter MIT KONSOLE (für Debugging)
REM ============================================================

cd /d %~dp0

echo ============================================================
echo WerkstattArchiv wird gestartet...
echo ============================================================
echo.

REM Pruefe ob venv existiert, sonst nutze System-Python
if exist venv (
    echo Nutze virtuelle Umgebung...
    call venv\Scripts\activate.bat
    python main.py
) else (
    echo Keine virtuelle Umgebung gefunden, nutze System-Python...
    where python >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        python main.py
    ) else (
        echo FEHLER: Python ist nicht installiert oder nicht im PATH!
        echo Bitte Python 3.11 oder hoeher installieren.
        echo Download: https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
)

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

@echo off
REM ============================================================
REM WerkstattArchiv Starter (ohne Konsolenfenster)
REM ============================================================

cd /d %~dp0

REM Pruefe ob venv existiert, sonst nutze System-Python
if exist venv (
    echo Starte mit virtueller Umgebung...
    start "" venv\Scripts\pythonw.exe main.py
) else (
    echo Keine virtuelle Umgebung gefunden, nutze System-Python...
    where python >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        start "" pythonw.exe main.py
    ) else (
        echo FEHLER: Python ist nicht installiert oder nicht im PATH!
        echo Bitte Python 3.11 oder hoeher installieren.
        echo Download: https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
)

REM Beende Batch sofort (Konsolenfenster verschwindet)
exit

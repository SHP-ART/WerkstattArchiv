@echo off
REM ============================================================
REM WerkstattArchiv Starter (ohne Konsolenfenster)
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

REM Starte Anwendung ohne Konsolenfenster mit pythonw.exe
start "" venv\Scripts\pythonw.exe main.py

REM Alternativ: Wenn pythonw.exe nicht funktioniert
REM start /B venv\Scripts\python.exe main.py

REM Beende Batch sofort (Konsolenfenster verschwindet)
exit

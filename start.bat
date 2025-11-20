@echo off
REM ============================================================
REM WerkstattArchiv Starter mit ausführlichem Logging
REM ============================================================

echo.
echo ============================================================
echo WerkstattArchiv wird gestartet...
echo ============================================================
echo.

REM Log-Datei erstellen
set "LOGFILE=start.log"
echo [%date% %time%] Start-Versuch >> "%LOGFILE%"

REM Wechsle ins Programmverzeichnis
cd /d %~dp0
echo Arbeitsverzeichnis: %CD%
echo [%date% %time%] Arbeitsverzeichnis: %CD% >> "%LOGFILE%"

REM Prüfe ob main.py existiert
if not exist "main.py" (
    echo.
    echo FEHLER: main.py nicht gefunden!
    echo Bitte stelle sicher, dass du im WerkstattArchiv-Verzeichnis bist.
    echo Aktuelles Verzeichnis: %CD%
    echo.
    echo [%date% %time%] FEHLER: main.py nicht gefunden in %CD% >> "%LOGFILE%"
    pause
    exit /b 1
)

echo [OK] main.py gefunden
echo [%date% %time%] main.py gefunden >> "%LOGFILE%"
echo.

REM Prüfe ob venv existiert, sonst nutze System-Python
if exist "venv\Scripts\python.exe" (
    echo Nutze virtuelle Umgebung...
    echo [%date% %time%] Nutze venv: venv\Scripts\python.exe >> "%LOGFILE%"
    
    REM Teste Python-Version
    echo Python-Version:
    venv\Scripts\python.exe --version
    echo.
    
    REM Prüfe wichtige Pakete
    echo Pruefe Pakete...
    venv\Scripts\python.exe -c "import customtkinter; print('[OK] customtkinter verfuegbar')" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo [WARNUNG] customtkinter nicht installiert!
        echo Bitte fuehre install.bat aus.
        echo.
    )
    
    REM Starte mit Python (mit Konsolenfenster für Fehlerausgabe)
    echo Starte WerkstattArchiv...
    echo Hinweis: Konsolenfenster bleibt offen fuer Fehlerausgabe
    echo Falls Fehler auftreten, siehe logs\werkstatt.log
    echo.
    venv\Scripts\python.exe main.py
    
    REM Speichere Exit-Code sofort
    set EXIT_CODE=%ERRORLEVEL%
    echo [%date% %time%] Exit-Code: %EXIT_CODE% >> "%LOGFILE%"
    
    REM Prüfe Exit-Code
    if %EXIT_CODE% NEQ 0 (
        echo.
        echo ============================================================
        echo FEHLER: Programm wurde mit Fehlercode %EXIT_CODE% beendet!
        echo ============================================================
        echo.
        echo [%date% %time%] FEHLER: Exit-Code %EXIT_CODE% >> "%LOGFILE%"
        echo Siehe logs\werkstatt.log fuer Details
        echo.
        echo Moegliche Ursachen:
        echo - Pakete fehlen (fuehre install.bat aus)
        echo - Python-Version inkompatibel (verwende Python 3.11 statt 3.13)
        echo - Siehe start.log und logs\werkstatt.log
        echo.
        pause
        exit /b %ERRORLEVEL%
    )
    
    echo [%date% %time%] Programm erfolgreich beendet >> "%LOGFILE%"
    
) else (
    echo Keine virtuelle Umgebung gefunden, nutze System-Python...
    echo [%date% %time%] Keine venv gefunden, nutze System-Python >> "%LOGFILE%"
    
    REM Prüfe ob Python verfügbar
    where python >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo FEHLER: Python ist nicht installiert oder nicht im PATH!
        echo.
        echo Bitte installieren:
        echo 1. Python 3.11+ von https://www.python.org/downloads/
        echo 2. Waehrend Installation "Add Python to PATH" ankreuzen!
        echo.
        echo Oder erstelle virtuelle Umgebung mit: setup.bat
        echo.
        echo [%date% %time%] FEHLER: Python nicht gefunden >> "%LOGFILE%"
        pause
        exit /b 1
    )
    
    REM Teste Python-Version
    python --version
    echo.
    
    echo Starte WerkstattArchiv mit System-Python...
    echo.
    python main.py
    
    REM Prüfe Exit-Code
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ============================================================
        echo FEHLER: Programm wurde mit Fehlercode %ERRORLEVEL% beendet!
        echo ============================================================
        echo.
        echo [%date% %time%] FEHLER: Exit-Code %ERRORLEVEL% >> "%LOGFILE%"
        echo Siehe logs\werkstatt.log fuer Details
        echo.
        pause
        exit /b %ERRORLEVEL%
    )
    
    echo [%date% %time%] Programm erfolgreich beendet >> "%LOGFILE%"
)

echo.
echo ============================================================
echo WerkstattArchiv wurde beendet
echo ============================================================
echo.
pause

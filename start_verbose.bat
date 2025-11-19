@echo off
REM ============================================================
REM WerkstattArchiv Starter mit MAXIMAL VERBOSE Logging
REM Für Debugging und Fehlersuche
REM ============================================================

echo.
echo ============================================================
echo WerkstattArchiv DEBUG-Modus
echo ============================================================
echo.

REM Erstelle ausführliches Log
set "LOGFILE=start_verbose.log"
echo ================================================ > "%LOGFILE%"
echo WerkstattArchiv Verbose Start Log >> "%LOGFILE%"
echo Start: %date% %time% >> "%LOGFILE%"
echo ================================================ >> "%LOGFILE%"
echo. >> "%LOGFILE%"

REM Wechsle ins Programmverzeichnis
cd /d %~dp0
echo [INFO] Arbeitsverzeichnis: %CD%
echo [INFO] Arbeitsverzeichnis: %CD% >> "%LOGFILE%"
echo. >> "%LOGFILE%"

REM Systeminformationen sammeln
echo [INFO] Systeminformationen:
echo Systeminformationen: >> "%LOGFILE%"
ver >> "%LOGFILE%"
echo. >> "%LOGFILE%"

REM Prüfe ob main.py existiert
echo [CHECK] Pruefe main.py...
if not exist "main.py" (
    echo [ERROR] main.py nicht gefunden!
    echo [ERROR] main.py nicht gefunden in %CD% >> "%LOGFILE%"
    echo.
    pause
    exit /b 1
)
echo [OK] main.py gefunden
echo [OK] main.py gefunden >> "%LOGFILE%"
echo. >> "%LOGFILE%"

REM Prüfe venv
echo [CHECK] Pruefe virtuelle Umgebung...
if exist "venv\Scripts\python.exe" (
    echo [OK] venv gefunden: venv\Scripts\python.exe
    echo [OK] venv gefunden >> "%LOGFILE%"
    
    echo. >> "%LOGFILE%"
    echo Python-Version: >> "%LOGFILE%"
    venv\Scripts\python.exe --version >> "%LOGFILE%" 2>&1
    echo. >> "%LOGFILE%"
    
    echo Installierte Pakete: >> "%LOGFILE%"
    venv\Scripts\python.exe -m pip list >> "%LOGFILE%" 2>&1
    echo. >> "%LOGFILE%"
    
    echo [INFO] Starte mit venv\Scripts\python.exe
    echo.
    echo ============================================================
    echo Programmausgabe:
    echo ============================================================
    echo.
    
    REM Starte mit ausführlichem Output
    venv\Scripts\python.exe main.py 2>&1 | tee -a "%LOGFILE%"
    set EXIT_CODE=%ERRORLEVEL%
    
) else (
    echo [WARNING] Keine virtuelle Umgebung gefunden
    echo [WARNING] Nutze System-Python
    echo [WARNING] Keine venv gefunden, nutze System-Python >> "%LOGFILE%"
    echo. >> "%LOGFILE%"
    
    where python >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Python nicht im PATH gefunden!
        echo [ERROR] Python nicht gefunden >> "%LOGFILE%"
        echo.
        pause
        exit /b 1
    )
    
    echo Python-Version: >> "%LOGFILE%"
    python --version >> "%LOGFILE%" 2>&1
    echo. >> "%LOGFILE%"
    
    echo [INFO] Starte mit System-Python
    echo.
    echo ============================================================
    echo Programmausgabe:
    echo ============================================================
    echo.
    
    python main.py 2>&1 | tee -a "%LOGFILE%"
    set EXIT_CODE=%ERRORLEVEL%
)

echo. >> "%LOGFILE%"
echo ================================================ >> "%LOGFILE%"
echo Exit-Code: %EXIT_CODE% >> "%LOGFILE%"
echo Ende: %date% %time% >> "%LOGFILE%"
echo ================================================ >> "%LOGFILE%"

echo.
echo.
echo ============================================================
if %EXIT_CODE% NEQ 0 (
    echo FEHLER: Programm beendet mit Exit-Code %EXIT_CODE%
    echo.
    echo Vollstaendiges Log: %LOGFILE%
    echo Programm-Log: logs\werkstatt.log
) else (
    echo Programm erfolgreich beendet
)
echo ============================================================
echo.
pause

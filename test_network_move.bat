@echo off
setlocal ENABLEDELAYEDEXPANSION
cd /d "%~dp0"

echo ==========================================
echo   WerkstattArchiv - Netzwerk-Testlauf
echo ==========================================

echo Geben Sie den Zielordner (z. B. Netzlaufwerk) an.
set /p TARGET_DIR=Zielordner [Enter = config root_dir]: 

if "%TARGET_DIR%"=="" (
    for /f "usebackq delims=" %%I in (`python -c "import json;print(json.load(open('config.json','r',encoding='utf-8')).get('root_dir',''))"`) do set TARGET_DIR=%%I
)

if "%TARGET_DIR%"=="" (
    echo Konnte keinen Zielordner bestimmen. Bitte Pfad angeben.
    goto :end
)

echo Optional: Eigene Testdatei angeben (Original bleibt erhalten).
set /p SOURCE_FILE=Pfad zur Testdatei [Enter = Dummy-Datei verwenden]: 

echo Groesse der Dummy-Datei in MB (nur relevant ohne eigene Datei).
set /p SIZE_MB=Dateigroesse [Enter = 5]: 
if "%SIZE_MB%"=="" set SIZE_MB=5

set /p CLEANUP=Testdatei nach Lauf im Ziel loeschen? (j/n) [n]: 
if /I "%CLEANUP%"=="J" set CLEANUP_FLAG=--cleanup
if /I "%CLEANUP%"=="JA" set CLEANUP_FLAG=--cleanup
if not defined CLEANUP_FLAG set CLEANUP_FLAG=

echo Optional: Pfad fuer CSV-Log angeben (z. B. C:\Temp\netztest.csv ).
set /p LOG_FILE=Log-Datei [Enter = kein Log]: 
if "%LOG_FILE%"=="" (
    set LOG_ARG=
) else (
    set LOG_ARG=--log-file "%LOG_FILE%"
)

echo.
echo Starte Netzwerk-Test...
if "%SOURCE_FILE%"=="" (
    python tools\test_network_copy.py --target "%TARGET_DIR%" --size-mb %SIZE_MB% %CLEANUP_FLAG% %LOG_ARG%
) else (
    python tools\test_network_copy.py --target "%TARGET_DIR%" --size-mb %SIZE_MB% --source "%SOURCE_FILE%" %CLEANUP_FLAG% %LOG_ARG%
)

if errorlevel 1 (
    echo.
    echo Test fehlgeschlagen. Details siehe Ausgabe oben.
) else (
    echo.
    echo Test erfolgreich abgeschlossen.
)

:end
echo.
pause

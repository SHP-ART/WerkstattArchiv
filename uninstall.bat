@echo off
REM ============================================================
REM WerkstattArchiv - Deinstallation
REM ============================================================

echo.
echo ============================================================
echo WerkstattArchiv - Deinstallation
echo ============================================================
echo.
echo WARNUNG: Dies loescht die virtuelle Umgebung und Verknuepfungen!
echo Ihre Daten und config.json bleiben erhalten.
echo.
set /p confirm="Wirklich deinstallieren? (J/N): "
if /i not "%confirm%"=="J" (
    echo Abgebrochen.
    pause
    exit /b 0
)

echo.
echo Loesche virtuelle Umgebung...
if exist venv (
    rmdir /s /q venv
    echo [OK] venv geloescht
)

echo.
echo Loesche Desktop-Verknuepfung...
if exist "%USERPROFILE%\Desktop\WerkstattArchiv.lnk" (
    del "%USERPROFILE%\Desktop\WerkstattArchiv.lnk"
    echo [OK] Verknuepfung geloescht
)

echo.
echo Loesche Build-Artefakte...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec
echo [OK] Build-Dateien geloescht

echo.
echo ============================================================
echo Deinstallation abgeschlossen!
echo ============================================================
echo.
echo Folgende Dateien wurden NICHT geloescht:
echo - config.json
echo - werkstatt_index.db
echo - WerkstattArchiv_log.txt
echo - C:\WerkstattArchiv\ (Ihre Daten)
echo.
echo Um komplett zu deinstallieren:
echo 1. Loesche diesen Ordner
echo 2. Loesche C:\WerkstattArchiv\
echo.
pause

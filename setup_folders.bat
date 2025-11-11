@echo off
REM ============================================================
REM WerkstattArchiv - Ordnerstruktur erstellen
REM ============================================================

echo.
echo ============================================================
echo WerkstattArchiv - Ordnerstruktur Setup
echo ============================================================
echo.

set BASE_DIR=C:\WerkstattArchiv

echo Erstelle Ordnerstruktur in: %BASE_DIR%
echo.

REM Hauptordner erstellen
if not exist "%BASE_DIR%" mkdir "%BASE_DIR%"
echo [OK] %BASE_DIR%

REM Unterordner erstellen
if not exist "%BASE_DIR%\Eingang" mkdir "%BASE_DIR%\Eingang"
echo [OK] %BASE_DIR%\Eingang

if not exist "%BASE_DIR%\Daten" mkdir "%BASE_DIR%\Daten"
echo [OK] %BASE_DIR%\Daten

if not exist "%BASE_DIR%\Unklar" mkdir "%BASE_DIR%\Unklar"
echo [OK] %BASE_DIR%\Unklar

if not exist "%BASE_DIR%\config" mkdir "%BASE_DIR%\config"
echo [OK] %BASE_DIR%\config

echo.
echo Erstelle Beispiel-Kundendatei...

REM Kundendatei erstellen
(
    echo 10234;Mueller Max
    echo 10235;Schmidt GmbH
    echo 10236;Wagner KFZ-Werkstatt
    echo 10237;Bauer Transporte
    echo 10238;Fischer Auto AG
) > "%BASE_DIR%\config\kunden.csv"

if exist "%BASE_DIR%\config\kunden.csv" (
    echo [OK] %BASE_DIR%\config\kunden.csv erstellt
) else (
    echo [FEHLER] Konnte kunden.csv nicht erstellen
)

echo.
echo ============================================================
echo Setup abgeschlossen!
echo ============================================================
echo.
echo Ordnerstruktur wurde erstellt:
echo.
echo %BASE_DIR%
echo   +-- Eingang\      (Hier PDFs/Bilder ablegen)
echo   +-- Daten\        (Sortierte Dokumente)
echo   +-- Unklar\       (Unklare Dokumente)
echo   +-- config\
echo       +-- kunden.csv (Kundendatenbank)
echo.
echo Naechste Schritte:
echo.
echo 1. Bearbeite die Kundendatei:
echo    %BASE_DIR%\config\kunden.csv
echo    Format: Kundennummer;Kundenname
echo.
echo 2. Starte WerkstattArchiv:
echo    Doppelklick auf "start.bat"
echo.
pause

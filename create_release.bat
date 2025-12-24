@echo off
REM ============================================================
REM WerkstattArchiv - GitHub Release Package Creator
REM ============================================================

echo.
echo ============================================================
echo WerkstattArchiv - Release Package Creator
echo ============================================================
echo.

cd /d %~dp0

REM Version aus version.py auslesen
for /f "tokens=2 delims=^=" %%a in ('findstr "__version__" version.py') do (
    for /f "tokens=1 delims=^" %%b in ("%%a") do set VERSION=%%b
)
set VERSION=%VERSION:"=%
set VERSION=%VERSION: =%

echo Version: %VERSION%
echo.

REM Prüfe ob dist Ordner existiert
if not exist "dist\WerkstattArchiv\WerkstattArchiv.exe" (
    echo FEHLER: EXE-Datei nicht gefunden!
    echo Bitte zuerst "build_exe.bat" ausfuehren!
    pause
    exit /b 1
)

REM Erstelle Release-Ordner
set RELEASE_NAME=WerkstattArchiv-v%VERSION%-Windows
set RELEASE_DIR=releases\%RELEASE_NAME%

echo [1/4] Erstelle Release-Ordner...
if exist releases rmdir /s /q releases
mkdir "%RELEASE_DIR%"
echo.

echo [2/4] Kopiere Programmdateien...
xcopy "dist\WerkstattArchiv\*" "%RELEASE_DIR%\" /E /I /Y >nul
echo.

echo [3/4] Erstelle Installationsanleitung...
(
echo ============================================================
echo WerkstattArchiv v%VERSION% - Windows Release
echo ============================================================
echo.
echo INSTALLATION:
echo.
echo 1. Entpacken Sie diesen Ordner an einen beliebigen Ort
echo.
echo 2. Tesseract OCR installieren:
echo    - Download: https://github.com/UB-Mannheim/tesseract/wiki
echo    - Installieren Sie Tesseract-OCR (empfohlen: C:\Program Files\Tesseract-OCR)
echo    - Deutsche Sprachdaten werden automatisch mit installiert
echo.
echo 3. Konfiguration anpassen:
echo    - Öffnen Sie config.json mit einem Texteditor
echo    - Passen Sie folgende Pfade an:
echo      * "eingang": Ordner für neue Dokumente
echo      * "ausgang": Zielordner für archivierte Dokumente
echo      * "tesseract_path": Pfad zur tesseract.exe
echo.
echo 4. Optional: Fahrzeugdatenbank einrichten:
echo    - Legen Sie vehicles.csv im data-Ordner an
echo    - Format: fin,hersteller,modell,kennzeichen
echo.
echo 5. Programm starten:
echo    - Doppelklick auf WerkstattArchiv.exe
echo.
echo ============================================================
echo SYSTEMANFORDERUNGEN:
echo ============================================================
echo.
echo - Windows 10 oder Windows 11 ^(64-bit^)
echo - Mindestens 4 GB RAM
echo - Tesseract OCR ^(separat zu installieren^)
echo.
echo ============================================================
echo HINWEISE:
echo ============================================================
echo.
echo - Keine Python-Installation erforderlich
echo - Alle Abhängigkeiten sind in der EXE enthalten
echo - Bei Problemen siehe logs\werkstatt.log
echo.
echo Support: https://github.com/SHP-ART/WerkstattArchiv/issues
echo.
) > "%RELEASE_DIR%\INSTALLATION.txt"

REM Kopiere zusätzliche Dokumentation
if exist README.md copy README.md "%RELEASE_DIR%\" >nul
if exist QUICK_START_WINDOWS.md copy QUICK_START_WINDOWS.md "%RELEASE_DIR%\" >nul
if exist docs\TESSERACT_SETUP.md copy docs\TESSERACT_SETUP.md "%RELEASE_DIR%\docs\" >nul 2>nul

echo.
echo [4/4] Erstelle ZIP-Archiv...
powershell -Command "Compress-Archive -Path '.\%RELEASE_DIR%\*' -DestinationPath '.\releases\%RELEASE_NAME%.zip' -Force"

if %errorlevel% neq 0 (
    echo FEHLER: ZIP-Erstellung fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Release-Paket erfolgreich erstellt!
echo ============================================================
echo.
echo Datei: releases\%RELEASE_NAME%.zip
echo Größe: 
for %%A in ("releases\%RELEASE_NAME%.zip") do echo %%~zA Bytes
echo.
echo ============================================================
echo GitHub Release erstellen:
echo ============================================================
echo.
echo 1. Gehe zu: https://github.com/SHP-ART/WerkstattArchiv/releases/new
echo.
echo 2. Tag erstellen: v%VERSION%
echo.
echo 3. Release Title: WerkstattArchiv v%VERSION%
echo.
echo 4. Beschreibung hinzufügen (siehe unten)
echo.
echo 5. ZIP-Datei hochladen:
echo    releases\%RELEASE_NAME%.zip
echo.
echo 6. "Publish release" klicken
echo.
echo ============================================================
echo RELEASE NOTES (Kopieren für GitHub):
echo ============================================================
echo.
echo ## WerkstattArchiv v%VERSION% - Windows Release
echo.
echo ### Installation
echo.
echo 1. ZIP-Datei herunterladen und entpacken
echo 2. Tesseract OCR installieren: [Download](https://github.com/UB-Mannheim/tesseract/wiki)
echo 3. `config.json` anpassen (Pfade für Eingang/Ausgang)
echo 4. `WerkstattArchiv.exe` starten
echo.
echo ### Systemanforderungen
echo.
echo - Windows 10/11 (64-bit)
echo - Mindestens 4 GB RAM
echo - Tesseract OCR (separat zu installieren)
echo.
echo ### Hinweise
echo.
echo - Keine Python-Installation erforderlich
echo - Alle Abhängigkeiten enthalten
echo - Detaillierte Anleitung in INSTALLATION.txt
echo.
echo ### Support
echo.
echo Bei Problemen bitte ein Issue erstellen.
echo.
echo ============================================================
echo.
pause

@echo off
REM ============================================================
REM Tesseract OCR Installation für WerkstattArchiv
REM Automatische Installation und Konfiguration
REM ============================================================

echo.
echo ============================================================
echo    Tesseract OCR Installation für WerkstattArchiv
echo ============================================================
echo.

REM Als Administrator prüfen
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [FEHLER] Dieses Script muss als Administrator ausgeführt werden!
    echo.
    echo Bitte:
    echo 1. Rechtsklick auf install_tesseract.bat
    echo 2. "Als Administrator ausführen" wählen
    echo.
    pause
    exit /b 1
)

echo [1/5] Prüfe Tesseract-Installation...
echo.

REM Prüfe ob Tesseract bereits installiert ist
set "TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe"
if exist "%TESSERACT_PATH%" (
    echo [INFO] Tesseract ist bereits installiert!
    echo Pfad: %TESSERACT_PATH%
    echo.
    
    choice /C JN /M "Möchten Sie die Installation überspringen und nur den Pfad konfigurieren?"
    if errorlevel 2 goto :download
    if errorlevel 1 goto :configure
)

:download
echo [2/5] Lade Tesseract OCR herunter...
echo.

REM Download-URL (neueste stabile Version)
set "DOWNLOAD_URL=https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
set "INSTALLER=tesseract-installer.exe"

echo Download-URL: %DOWNLOAD_URL%
echo.

REM PowerShell zum Download verwenden
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%INSTALLER%'}"

if not exist "%INSTALLER%" (
    echo [FEHLER] Download fehlgeschlagen!
    echo.
    echo Bitte manuell herunterladen:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    pause
    exit /b 1
)

echo [OK] Download erfolgreich!
echo.

:install
echo [3/5] Installiere Tesseract OCR...
echo.
echo WICHTIG: Bitte im Installer folgende Optionen wählen:
echo [x] Additional language data (download)
echo [x] German (deu)
echo.
echo Installation startet in 3 Sekunden...
timeout /t 3 /nobreak >nul

REM Starte Installer (silent mode mit deutschen Sprachdaten)
echo Starte Installation...
start /wait "" "%INSTALLER%" /S /D=C:\Program Files\Tesseract-OCR

REM Kurz warten bis Installation abgeschlossen
timeout /t 5 /nobreak >nul

REM Prüfe ob Installation erfolgreich
if not exist "%TESSERACT_PATH%" (
    echo [FEHLER] Installation fehlgeschlagen!
    echo.
    echo Bitte manuell installieren:
    echo 1. Doppelklick auf tesseract-installer.exe
    echo 2. "Additional language data (download)" anhaken
    echo 3. "German" auswählen
    echo 4. Installation abschließen
    echo 5. Dieses Script erneut ausführen
    echo.
    pause
    exit /b 1
)

echo [OK] Tesseract erfolgreich installiert!
echo.

REM Aufräumen
if exist "%INSTALLER%" del "%INSTALLER%"

:configure
echo [4/5] Konfiguriere WerkstattArchiv...
echo.

REM Prüfe ob config.json existiert
if not exist "config.json" (
    echo [WARNUNG] config.json nicht gefunden!
    echo Bitte WerkstattArchiv mindestens einmal starten.
    echo Danach Tesseract-Pfad manuell in Einstellungen eintragen:
    echo %TESSERACT_PATH%
    echo.
    pause
    exit /b 0
)

REM Erstelle Python-Script zum Aktualisieren der config.json
echo import json > update_config.py
echo import os >> update_config.py
echo. >> update_config.py
echo config_file = "config.json" >> update_config.py
echo tesseract_path = r"%TESSERACT_PATH%" >> update_config.py
echo. >> update_config.py
echo # Lese config.json >> update_config.py
echo with open(config_file, "r", encoding="utf-8") as f: >> update_config.py
echo     config = json.load(f) >> update_config.py
echo. >> update_config.py
echo # Aktualisiere Tesseract-Pfad >> update_config.py
echo config["tesseract_path"] = tesseract_path >> update_config.py
echo. >> update_config.py
echo # Speichere config.json >> update_config.py
echo with open(config_file, "w", encoding="utf-8") as f: >> update_config.py
echo     json.dump(config, f, indent=2, ensure_ascii=False) >> update_config.py
echo. >> update_config.py
echo print("OK: Tesseract-Pfad in config.json eingetragen!") >> update_config.py

REM Führe Python-Script aus
python update_config.py

if %errorLevel% neq 0 (
    echo [FEHLER] Konnte config.json nicht aktualisieren!
    echo Bitte Pfad manuell in Einstellungen eintragen:
    echo %TESSERACT_PATH%
    echo.
) else (
    echo [OK] config.json aktualisiert!
    echo.
)

REM Aufräumen
if exist "update_config.py" del "update_config.py"

echo [5/5] Teste Tesseract-Installation...
echo.

REM Teste ob Tesseract funktioniert
"%TESSERACT_PATH%" --version >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Tesseract funktioniert!
    echo.
    "%TESSERACT_PATH%" --version
    echo.
) else (
    echo [WARNUNG] Tesseract-Test fehlgeschlagen!
    echo Bitte System neu starten.
    echo.
)

echo ============================================================
echo    Installation abgeschlossen!
echo ============================================================
echo.
echo Tesseract OCR wurde erfolgreich installiert und konfiguriert!
echo.
echo Pfad: %TESSERACT_PATH%
echo.
echo NÄCHSTE SCHRITTE:
echo 1. WerkstattArchiv starten
echo 2. Tab "Einstellungen" öffnen
echo 3. Tesseract-Pfad sollte bereits eingetragen sein
echo 4. Gescanntes Test-PDF verarbeiten
echo.
echo HINWEIS:
echo Tesseract wird nur für gescannte PDFs/Bilder benötigt.
echo Normale digitale PDFs funktionieren ohne Tesseract!
echo.
echo Weitere Infos: docs\TESSERACT_SETUP.md
echo.
pause

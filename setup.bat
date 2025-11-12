@echo off
REM ###############################################################################
REM WerkstattArchiv Setup Script für Windows
REM Installiert alle Abhängigkeiten inkl. Python und Python-Pakete
REM ###############################################################################

echo ============================================================
echo WerkstattArchiv Setup
echo ============================================================
echo.

REM Prüfe ob Python installiert ist
echo Pruefe Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FEHLER] Python ist nicht installiert!
    echo.
    echo Bitte installieren Sie Python 3.11 oder neuer:
    echo https://www.python.org/downloads/
    echo.
    echo WICHTIG: Aktivieren Sie bei der Installation "Add Python to PATH"!
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo [OK] Python ist installiert: %PYTHON_VERSION%
)

REM Prüfe pip
echo.
echo Pruefe pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNUNG] pip ist nicht installiert. Installiere pip...
    python -m ensurepip --upgrade
) else (
    echo [OK] pip ist installiert
)

REM Upgrade pip
echo.
echo Aktualisiere pip...
python -m pip install --upgrade pip

REM Prüfe Tesseract (optional)
echo.
echo Pruefe Tesseract-OCR...
tesseract --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Tesseract ist nicht installiert.
    echo.
    echo Tesseract wird fuer gescannte PDFs benoetigt.
    echo.
    echo Download: https://github.com/UB-Mannheim/tesseract/wiki
    echo Empfohlene Version: tesseract-ocr-w64-setup-5.3.x.exe
    echo.
    set /p INSTALL_TESSERACT="Moechten Sie jetzt den Download-Link oeffnen? (y/n): "
    if /i "%INSTALL_TESSERACT%"=="y" (
        start https://github.com/UB-Mannheim/tesseract/wiki
        echo.
        echo Installieren Sie Tesseract und fuehren Sie dieses Script erneut aus.
        echo.
    )
) else (
    for /f "tokens=*" %%i in ('tesseract --version 2^>^&1 ^| findstr /C:"tesseract"') do set TESSERACT_VERSION=%%i
    echo [OK] Tesseract ist installiert: %TESSERACT_VERSION%
)

REM Installiere Python-Abhängigkeiten
echo.
echo Installiere Python-Pakete...
echo.

if exist requirements.txt (
    python -m pip install -r requirements.txt
) else (
    echo requirements.txt nicht gefunden. Installiere Pakete einzeln...
    
    REM Core-Pakete
    python -m pip install customtkinter
    python -m pip install pillow
    python -m pip install pypdf2
    python -m pip install pytesseract
    python -m pip install python-dateutil
    
    REM Optional: watchdog für Auto-Watch
    python -m pip install watchdog
)

echo.
echo [OK] Alle Python-Pakete installiert

REM Erstelle Verzeichnisstruktur
echo.
echo Erstelle Verzeichnisstruktur...

if not exist "data\index" mkdir data\index
if not exist "config" mkdir config
if not exist "backups" mkdir backups
if not exist "logs" mkdir logs

echo [OK] Verzeichnisse erstellt

REM Prüfe ob config.json existiert
echo.
if not exist config.json (
    echo Erstelle Standard-Konfiguration...
    (
        echo {
        echo   "root_dir": "",
        echo   "input_dir": "",
        echo   "unclear_dir": "",
        echo   "customers_file": "",
        echo   "tesseract_path": null
        echo }
    ) > config.json
    echo [OK] config.json erstellt
    echo [INFO] Bitte konfigurieren Sie die Pfade in den Einstellungen!
) else (
    echo [OK] config.json existiert bereits
)

REM Prüfe ob kunden.csv existiert
echo.
if not exist config\kunden.csv (
    echo Erstelle leere Kundendatei...
    type nul > config\kunden.csv
    echo [OK] config\kunden.csv erstellt
    echo [INFO] Bitte fuegen Sie Ihre Kunden hinzu (Format: Kundennr;Name;PLZ;Ort;Strasse;Telefon^)
) else (
    echo [OK] Kundendatei existiert bereits
)

REM Tesseract-Pfad automatisch erkennen
tesseract --version >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo Konfiguriere Tesseract-Pfad...
    
    REM Finde Tesseract-Pfad
    for /f "tokens=*" %%i in ('where tesseract 2^>nul') do set TESSERACT_PATH=%%i
    
    if defined TESSERACT_PATH (
        REM Python-Script zum Update der config.json
        python -c "import json; import os; config_file = 'config.json'; config = json.load(open(config_file)) if os.path.exists(config_file) else {}; config['tesseract_path'] = r'%TESSERACT_PATH%' if config.get('tesseract_path') is None else config['tesseract_path']; json.dump(config, open(config_file, 'w'), indent=2); print('[OK] Tesseract-Pfad wurde automatisch konfiguriert:', config['tesseract_path'])"
    )
)

REM Fertig!
echo.
echo ============================================================
echo Setup abgeschlossen!
echo ============================================================
echo.
echo Sie koennen WerkstattArchiv jetzt starten:
echo.
echo    python main.py
echo.
echo Naechste Schritte:
echo    1. Konfigurieren Sie die Ordnerpfade in den Einstellungen
echo    2. Fuegen Sie Ihre Kunden zur config\kunden.csv hinzu
echo    3. Legen Sie Dokumente in den Eingangsordner
echo.
echo ============================================================
echo.
pause

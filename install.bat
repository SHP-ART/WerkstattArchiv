@echo off
REM ============================================================
REM WerkstattArchiv - Windows Installer
REM Automatische Installation aller Komponenten
REM ============================================================

echo.
echo ============================================================
echo WerkstattArchiv - Automatische Installation
echo ============================================================
echo.

REM Administrator-Rechte pruefen
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo FEHLER: Dieses Skript benoetigt Administrator-Rechte!
    echo Bitte mit Rechtsklick "Als Administrator ausfuehren"
    echo.
    pause
    exit /b 1
)

REM Aktuelles Verzeichnis speichern
set INSTALL_DIR=%~dp0
cd /d "%INSTALL_DIR%"

echo [1/6] Pruefe Python-Installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo FEHLER: Python ist nicht installiert!
    echo.
    echo Bitte Python 3.11 oder neuer installieren von:
    echo https://www.python.org/downloads/
    echo.
    echo WICHTIG: Bei Installation "Add Python to PATH" ankreuzen!
    echo.
    pause
    exit /b 1
)

python --version
echo Python gefunden!
echo.

echo [2/6] Erstelle virtuelle Umgebung...
if exist venv (
    echo Loesche alte venv...
    rmdir /s /q venv
)
python -m venv venv
if %errorLevel% neq 0 (
    echo FEHLER: Konnte virtuelle Umgebung nicht erstellen!
    pause
    exit /b 1
)
echo Virtuelle Umgebung erstellt!
echo.

echo [3/6] Aktiviere virtuelle Umgebung...
call venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo FEHLER: Konnte virtuelle Umgebung nicht aktivieren!
    pause
    exit /b 1
)
echo Virtuelle Umgebung aktiv!
echo.

echo [4/6] Installiere Python-Pakete...
echo Dies kann einige Minuten dauern...
echo.
python -m pip install --upgrade pip
echo.
echo Installiere Haupt-Pakete...
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo FEHLER: Installation der Pakete fehlgeschlagen!
    pause
    exit /b 1
)
echo.
echo Installiere EasyOCR (Python-basierte OCR, keine Tesseract-Installation noetig)...
echo HINWEIS: Dies kann 5-10 Minuten dauern (ca. 200 MB Download)
echo.
pip install easyocr
if %errorLevel% neq 0 (
    echo WARNUNG: EasyOCR konnte nicht installiert werden!
    echo Das Programm funktioniert trotzdem, aber OCR wird nicht verfuegbar sein.
    echo Sie koennen spaeter Tesseract installieren als Alternative.
    echo.
) else (
    echo EasyOCR erfolgreich installiert!
    echo OCR funktioniert jetzt OHNE Tesseract-Installation!
    echo.
)
echo Alle Pakete erfolgreich installiert!
echo.

echo [5/6] Erstelle Standardkonfiguration...
if not exist config.json (
    echo Erstelle config.json...
    (
        echo {
        echo   "root_dir": "C:/WerkstattArchiv/Daten",
        echo   "input_dir": "C:/WerkstattArchiv/Eingang",
        echo   "unclear_dir": "C:/WerkstattArchiv/Unklar",
        echo   "customers_file": "C:/WerkstattArchiv/config/kunden.csv",
        echo   "tesseract_path": null
    ) > config.json
    echo config.json erstellt!
) else (
    echo config.json existiert bereits - wird nicht ueberschrieben
)
echo.

echo [6/6] Erstelle Verknuepfungen...
REM Desktop-Verknuepfung erstellen
set SCRIPT_DIR=%INSTALL_DIR%
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\WerkstattArchiv.lnk'); $s.TargetPath = '%SCRIPT_DIR%start.bat'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.IconLocation = 'shell32.dll,166'; $s.Save()"
if %errorLevel% equ 0 (
    echo Desktop-Verknuepfung erstellt!
) else (
    echo Hinweis: Desktop-Verknuepfung konnte nicht erstellt werden
)
echo.

echo ============================================================
echo Installation abgeschlossen!
echo ============================================================
echo.
echo Die Anwendung wurde erfolgreich installiert!
echo.
echo OCR-Status:
echo   - EasyOCR installiert: Funktioniert OHNE Tesseract!
echo   - Keine weitere OCR-Installation noetig
echo.
echo Naechste Schritte:
echo.
echo 1. Konfiguration anpassen:
echo    - Starte die Anwendung
echo    - Gehe zu "Einstellungen" ^> "Pfade"
echo    - Setze Basis-Verzeichnis und Eingangsordner
echo.
echo 2. Anwendung starten:
echo    - Doppelklick auf "start.bat"
echo    - ODER Desktop-Verknuepfung verwenden
echo.
echo Eine Desktop-Verknuepfung wurde erstellt!
echo.
echo HINWEIS: Tesseract ist NICHT mehr noetig!
echo          EasyOCR funktioniert rein in Python.
echo.
pause

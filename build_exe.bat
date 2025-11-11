@echo off
REM ============================================================
REM WerkstattArchiv - EXE Builder
REM Erstellt eine standalone .exe Datei
REM ============================================================

echo.
echo ============================================================
echo WerkstattArchiv - EXE Builder
echo ============================================================
echo.

cd /d %~dp0

REM Pruefe venv
if not exist venv (
    echo FEHLER: Virtuelle Umgebung nicht gefunden!
    echo Bitte zuerst "install.bat" ausfuehren!
    pause
    exit /b 1
)

REM Aktiviere venv
call venv\Scripts\activate.bat

echo [1/3] Installiere PyInstaller...
pip install pyinstaller
if %errorLevel% neq 0 (
    echo FEHLER: PyInstaller konnte nicht installiert werden!
    pause
    exit /b 1
)
echo.

echo [2/3] Erstelle EXE-Datei...
echo Dies kann einige Minuten dauern...
echo.

pyinstaller --noconfirm --onefile --windowed ^
    --name "WerkstattArchiv" ^
    --icon=NONE ^
    --add-data "config.json;." ^
    --add-data "kunden_beispiel.csv;." ^
    --hidden-import "customtkinter" ^
    --hidden-import "PIL._tkinter_finder" ^
    main.py

if %errorLevel% neq 0 (
    echo FEHLER: Build fehlgeschlagen!
    pause
    exit /b 1
)
echo.

echo [3/3] Kopiere zusaetzliche Dateien...
if not exist dist\WerkstattArchiv mkdir dist\WerkstattArchiv
copy dist\WerkstattArchiv.exe dist\WerkstattArchiv\ >nul
copy config.json dist\WerkstattArchiv\ >nul
copy kunden_beispiel.csv dist\WerkstattArchiv\ >nul
copy README.md dist\WerkstattArchiv\ >nul 2>nul

echo.
echo ============================================================
echo Build erfolgreich!
echo ============================================================
echo.
echo Die EXE-Datei wurde erstellt:
echo %~dp0dist\WerkstattArchiv\WerkstattArchiv.exe
echo.
echo Der komplette Ordner kann auf andere Windows-PCs
echo kopiert werden (keine Python-Installation noetig).
echo.
echo WICHTIG:
echo - config.json muss angepasst werden
echo - Tesseract OCR muss separat installiert werden
echo.
pause

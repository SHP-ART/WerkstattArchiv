@echo off
REM ============================================================
REM WerkstattArchiv - EasyOCR Installation
REM Installiert Python-basierte OCR (keine Tesseract-Installation noetig!)
REM ============================================================

echo.
echo ============================================================
echo EasyOCR Installation - Python-basierte OCR
echo ============================================================
echo.
echo EasyOCR ist eine moderne OCR-Engine die OHNE externe Tools
echo funktioniert. Keine Tesseract-Installation mehr noetig!
echo.
echo Vorteile:
echo   - Reine Python-Loesung (kein Tesseract.exe)
echo   - Funktioniert auf allen Windows-Versionen
echo   - Keine Pfad-Probleme mehr
echo   - Oft bessere Texterkennung
echo.
echo HINWEIS: Die Installation dauert 5-10 Minuten
echo          (ca. 200 MB Download von PyTorch, OpenCV, etc.)
echo.
pause

REM Aktuelles Verzeichnis
set INSTALL_DIR=%~dp0
cd /d "%INSTALL_DIR%"

echo.
echo [1/3] Pruefe Virtual Environment...
if not exist venv (
    echo FEHLER: Virtual Environment nicht gefunden!
    echo Bitte zuerst install.bat ausfuehren!
    echo.
    pause
    exit /b 1
)
echo Virtual Environment gefunden!
echo.

echo [2/3] Aktiviere Virtual Environment...
call venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo FEHLER: Konnte Virtual Environment nicht aktivieren!
    pause
    exit /b 1
)
echo Virtual Environment aktiv!
echo.

echo [3/3] Installiere EasyOCR...
echo.
echo Dies kann einige Minuten dauern - bitte Geduld!
echo Downloads: PyTorch (~150 MB), OpenCV (~40 MB), Modelle, etc.
echo.
pip install easyocr
if %errorLevel% neq 0 (
    echo.
    echo FEHLER: EasyOCR Installation fehlgeschlagen!
    echo.
    echo Moegliche Loesungen:
    echo   1. Internet-Verbindung pruefen
    echo   2. Antivirus temporaer deaktivieren
    echo   3. Python neu installieren
    echo   4. Disk-Space pruefen (mind. 1 GB frei)
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo EasyOCR erfolgreich installiert!
echo ============================================================
echo.
echo OCR funktioniert jetzt OHNE Tesseract!
echo.
echo Beim naechsten Programm-Start wird angezeigt:
echo   "✅ EasyOCR verfuegbar - verwende Python-basierte OCR"
echo.
echo Sie koennen Tesseract jetzt deinstallieren (optional):
echo   - Systemsteuerung ^> Programme ^> Tesseract-OCR
echo   - In Einstellungen: Tesseract-Pfad auf leer setzen
echo.
echo Weitere Infos: docs\EASYOCR_SETUP.md
echo.
pause

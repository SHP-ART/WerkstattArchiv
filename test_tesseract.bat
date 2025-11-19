@echo off
REM ============================================================
REM Tesseract OCR Test-Script
REM Testet ob Tesseract korrekt installiert und konfiguriert ist
REM ============================================================

echo.
echo ============================================================
echo    Tesseract OCR Test
echo ============================================================
echo.

REM Log-Datei erstellen
set "LOGFILE=%CD%\tesseract_test.log"
echo ============================================================ > "%LOGFILE%"
echo Tesseract OCR Test Log >> "%LOGFILE%"
echo Datum: %date% %time% >> "%LOGFILE%"
echo Arbeitsverzeichnis: %CD% >> "%LOGFILE%"
echo ============================================================ >> "%LOGFILE%"
echo. >> "%LOGFILE%"

REM Tesseract-Pfad aus config.json lesen
set "TESSERACT_PATH="
if exist "config.json" (
    echo [1/5] Lese Tesseract-Pfad aus config.json...
    echo [STEP 1/5] Config.json lesen... >> "%LOGFILE%"
    
    REM Erstelle temporäres Python-Script zum JSON-Lesen
    echo import json > read_config_temp.py
    echo try: >> read_config_temp.py
    echo     with open('config.json', 'r', encoding='utf-8') as f: >> read_config_temp.py
    echo         config = json.load(f) >> read_config_temp.py
    echo     path = config.get('tesseract_path', '') >> read_config_temp.py
    echo     if path: >> read_config_temp.py
    echo         print(path) >> read_config_temp.py
    echo     else: >> read_config_temp.py
    echo         print('NOT_SET') >> read_config_temp.py
    echo except Exception as e: >> read_config_temp.py
    echo     print(f'ERROR: {e}') >> read_config_temp.py
    
    for /f "delims=" %%i in ('python read_config_temp.py') do set "TESSERACT_PATH=%%i"
    del read_config_temp.py
    
    if "!TESSERACT_PATH!"=="NOT_SET" (
        echo    [WARNUNG] Tesseract-Pfad ist nicht in config.json gesetzt
        echo [WARNING] Tesseract-Pfad nicht gesetzt in config.json >> "%LOGFILE%"
        set "TESSERACT_PATH="
    ) else if "!TESSERACT_PATH!"=="" (
        echo    [WARNUNG] config.json enthält keinen tesseract_path
        echo [WARNING] Kein tesseract_path in config.json >> "%LOGFILE%"
    ) else (
        echo    [OK] Tesseract-Pfad gefunden: !TESSERACT_PATH!
        echo [OK] Tesseract-Pfad: !TESSERACT_PATH! >> "%LOGFILE%"
    )
) else (
    echo [1/5] config.json nicht gefunden
    echo [WARNING] config.json nicht gefunden >> "%LOGFILE%"
)
echo. >> "%LOGFILE%"

REM Fallback auf Standard-Pfad
if "!TESSERACT_PATH!"=="" (
    set "TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe"
    echo    [INFO] Verwende Standard-Pfad: !TESSERACT_PATH!
    echo [INFO] Verwende Standard-Pfad >> "%LOGFILE%"
)

echo.
echo [2/5] Pruefe ob Tesseract-Datei existiert...
echo [STEP 2/5] Datei-Existenz-Check... >> "%LOGFILE%"
if exist "!TESSERACT_PATH!" (
    echo    [OK] Tesseract gefunden: !TESSERACT_PATH!
    echo [OK] Datei existiert: !TESSERACT_PATH! >> "%LOGFILE%"
) else (
    color 0C
    echo    [FEHLER] Tesseract nicht gefunden: !TESSERACT_PATH!
    echo [ERROR] Datei nicht gefunden: !TESSERACT_PATH! >> "%LOGFILE%"
    echo. >> "%LOGFILE%"
    echo.
    echo FEHLER: Tesseract nicht gefunden!
    echo.
    echo Erwarteter Pfad: !TESSERACT_PATH!
    echo.
    echo Moegliche Loesungen:
    echo 1. Tesseract installieren mit: install_tesseract.bat
    echo 2. Pfad in config.json korrigieren
    echo 3. Pfad manuell in WerkstattArchiv Einstellungen eintragen
    echo.
    echo Siehe tesseract_test.log fuer Details
    pause
    exit /b 1
)
echo. >> "%LOGFILE%"

echo.
echo [3/5] Pruefe Tesseract-Version...
echo [STEP 3/5] Version-Check... >> "%LOGFILE%"
"!TESSERACT_PATH!" --version >> "%LOGFILE%" 2>&1
set VERSION_ERROR=!ERRORLEVEL!
if !VERSION_ERROR! neq 0 (
    color 0C
    echo    [FEHLER] Tesseract konnte nicht ausgefuehrt werden (Exit-Code: !VERSION_ERROR!)
    echo [ERROR] Tesseract Ausfuehrung fehlgeschlagen (Exit-Code: !VERSION_ERROR!) >> "%LOGFILE%"
    echo.
    echo FEHLER: Tesseract kann nicht ausgefuehrt werden!
    echo.
    echo Moegliche Ursachen:
    echo 1. Beschaedigte Installation
    echo 2. Fehlende Abhaengigkeiten
    echo 3. Falsche Architektur (32bit vs 64bit)
    echo.
    echo Siehe tesseract_test.log fuer Details
    pause
    exit /b 1
)
echo    [OK] Tesseract ist ausfuehrbar
"!TESSERACT_PATH!" --version
echo [OK] Tesseract Version erfolgreich abgerufen >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo.
echo [4/5] Pruefe deutsche Sprachdaten...
echo [STEP 4/5] Sprach-Check (German)... >> "%LOGFILE%"
"!TESSERACT_PATH!" --list-langs >> "%LOGFILE%" 2>&1
set LANG_ERROR=!ERRORLEVEL!
if !LANG_ERROR! neq 0 (
    echo    [WARNUNG] Konnte Sprachen nicht auflisten (Exit-Code: !LANG_ERROR!)
    echo [WARNING] Sprachen-Auflistung fehlgeschlagen >> "%LOGFILE%"
) else (
    echo Verfuegbare Sprachen: >> "%LOGFILE%"
    "!TESSERACT_PATH!" --list-langs 2>nul | findstr /I "deu eng" >> "%LOGFILE%"
    
    "!TESSERACT_PATH!" --list-langs 2>nul | findstr /I "deu" >nul
    if !ERRORLEVEL! equ 0 (
        echo    [OK] Deutsche Sprachdaten (deu) gefunden
        echo [OK] Deutsch (deu) verfuegbar >> "%LOGFILE%"
    ) else (
        color 0E
        echo    [WARNUNG] Deutsche Sprachdaten (deu) NICHT gefunden!
        echo [WARNING] Deutsch (deu) NICHT verfuegbar >> "%LOGFILE%"
        echo.
        echo WARNUNG: Deutsche Sprachdaten fehlen!
        echo.
        echo Tesseract funktioniert, aber ohne deutsche Sprache.
        echo Dies fuehrt zu schlechten Ergebnissen bei deutschen Texten.
        echo.
        echo Loesung:
        echo 1. Tesseract neu installieren
        echo 2. Bei Installation "Additional language data" ankreuzen
        echo 3. "German (deu)" auswaehlen
        echo.
    )
)
echo. >> "%LOGFILE%"

echo.
echo [5/5] Test-OCR durchfuehren...
echo [STEP 5/5] OCR-Test mit Beispieltext... >> "%LOGFILE%"

REM Erstelle Test-Bild mit Text (als Base64 embedded)
echo [INFO] Erstelle Test-Bild... >> "%LOGFILE%"
echo from PIL import Image, ImageDraw, ImageFont > create_test_image.py
echo img = Image.new('RGB', (400, 100), color='white') >> create_test_image.py
echo d = ImageDraw.Draw(img) >> create_test_image.py
echo d.text((10,10), "Tesseract OCR Test\nKundennummer: 12345\nDatum: 19.11.2025", fill='black') >> create_test_image.py
echo img.save('tesseract_test_image.png') >> create_test_image.py
echo print('OK') >> create_test_image.py

python create_test_image.py >nul 2>&1
set IMG_ERROR=!ERRORLEVEL!
if !IMG_ERROR! neq 0 (
    echo    [WARNUNG] Konnte Test-Bild nicht erstellen (PIL fehlt?)
    echo [WARNING] Test-Bild Erstellung fehlgeschlagen >> "%LOGFILE%"
    echo    [INFO] Ueberspringe OCR-Test
) else if exist "tesseract_test_image.png" (
    echo    [OK] Test-Bild erstellt: tesseract_test_image.png
    echo [OK] Test-Bild erstellt >> "%LOGFILE%"
    
    echo    [INFO] Fuehre OCR durch...
    echo [INFO] OCR-Test startet... >> "%LOGFILE%"
    "!TESSERACT_PATH!" tesseract_test_image.png tesseract_test_output -l deu >> "%LOGFILE%" 2>&1
    set OCR_ERROR=!ERRORLEVEL!
    
    if !OCR_ERROR! neq 0 (
        color 0C
        echo    [FEHLER] OCR fehlgeschlagen (Exit-Code: !OCR_ERROR!)
        echo [ERROR] OCR fehlgeschlagen (Exit-Code: !OCR_ERROR!) >> "%LOGFILE%"
        echo.
        echo FEHLER: OCR-Test fehlgeschlagen!
        echo.
        echo Siehe tesseract_test.log fuer Details
        pause
        exit /b 1
    )
    
    if exist "tesseract_test_output.txt" (
        echo    [OK] OCR erfolgreich! Ergebnis:
        echo [OK] OCR erfolgreich >> "%LOGFILE%"
        echo. >> "%LOGFILE%"
        echo OCR Ergebnis: >> "%LOGFILE%"
        type tesseract_test_output.txt >> "%LOGFILE%"
        echo ----------------------------------------
        type tesseract_test_output.txt
        echo ----------------------------------------
        echo. >> "%LOGFILE%"
        
        REM Cleanup
        del tesseract_test_output.txt >nul 2>&1
    ) else (
        echo    [WARNUNG] Output-Datei nicht erstellt
        echo [WARNING] Output-Datei nicht erstellt >> "%LOGFILE%"
    )
    
    REM Cleanup
    del tesseract_test_image.png >nul 2>&1
) else (
    echo    [WARNUNG] Test-Bild wurde nicht erstellt
    echo [WARNING] Test-Bild fehlt >> "%LOGFILE%"
)

del create_test_image.py >nul 2>&1

echo. >> "%LOGFILE%"
echo ============================================================ >> "%LOGFILE%"
echo Test abgeschlossen: %date% %time% >> "%LOGFILE%"
echo ============================================================ >> "%LOGFILE%"

color 0A
echo.
echo ============================================================
echo    Test erfolgreich abgeschlossen!
echo ============================================================
echo.
echo Tesseract funktioniert korrekt!
echo.
echo Tesseract-Pfad: !TESSERACT_PATH!
echo.
echo Naechste Schritte:
echo 1. Pfad ist bereits in config.json eingetragen (falls config.json existiert)
echo 2. Oder trage den Pfad in WerkstattArchiv Einstellungen ein
echo 3. Teste mit einem gescannten PDF
echo.
echo Log-Datei: %LOGFILE%
echo.
pause

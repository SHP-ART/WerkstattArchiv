@echo off
REM ============================================================
REM WerkstattArchiv - Update Script (robuste Version)
REM Aktualisiert das Repository vom GitHub mit Backup
REM ============================================================

setlocal enabledelayedexpansion
color 0A

REM Erstelle Log-Datei mit Zeitstempel
set LOGFILE=%CD%\update.log
echo ============================================================ > "%LOGFILE%"
echo WerkstattArchiv Update Log >> "%LOGFILE%"
echo Datum: %date% %time% >> "%LOGFILE%"
echo Arbeitsverzeichnis: %CD% >> "%LOGFILE%"
echo Benutzer: %USERNAME% >> "%LOGFILE%"
echo Computername: %COMPUTERNAME% >> "%LOGFILE%"
echo ============================================================ >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo.
echo ============================================================
echo WerkstattArchiv Update Tool
echo ============================================================
echo.
echo Log wird erstellt: %LOGFILE%
echo Arbeitsverzeichnis: %CD%
echo.

REM Setze Fehlerbehandlung
set ERRORLEVEL=0

REM Prüfe ob Git installiert ist
echo [CHECK] Pruefe Git-Installation... >> "%LOGFILE%"
where git >> "%LOGFILE%" 2>&1
set GIT_CHECK=%ERRORLEVEL%
if %GIT_CHECK% neq 0 (
    color 0C
    echo [ERROR] Git nicht gefunden (Exit-Code: %GIT_CHECK%) >> "%LOGFILE%"
    echo PATH: %PATH% >> "%LOGFILE%"
    echo. >> "%LOGFILE%"
    echo.
    echo FEHLER: Git ist nicht installiert oder nicht im PATH!
    echo.
    echo Bitte installieren Sie Git von: https://git-scm.com/
    echo Oder fuegen Sie Git zum PATH hinzu.
    echo.
    echo Siehe update.log fuer Details
    pause
    exit /b 1
)
echo [OK] Git gefunden >> "%LOGFILE%"
git --version >> "%LOGFILE%" 2>&1
echo. >> "%LOGFILE%"

REM Prüfe ob wir in einem Git-Repository sind
echo [CHECK] Pruefe Git-Repository... >> "%LOGFILE%"
if not exist ".git" (
    color 0C
    echo FEHLER: Kein Git-Repository gefunden in: %CD% >> "%LOGFILE%"
    echo.
    echo FEHLER: Dies ist kein Git-Repository!
    echo.
    echo Bitte fuehren Sie dieses Script im WerkstattArchiv-Ordner aus.
    echo Aktueller Ordner: %CD%
    echo.
    echo Siehe update.log fuer Details
    pause
    exit /b 1
)
echo [OK] Git-Repository gefunden >> "%LOGFILE%"

REM Erstelle Backup BEVOR Update gestartet wird (robuste Version - Issue: No backup before update.bat)
set TIMESTAMP=%date:~6,4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%CD%\backup_before_git_update_%TIMESTAMP%

echo [1/4] Erstelle Backup von wichtigen Dateien...
echo [STEP 1/4] Erstelle Backup... >> "%LOGFILE%"
if not exist "!BACKUP_DIR!" (
    mkdir "!BACKUP_DIR!"
    echo Backup-Verzeichnis: !BACKUP_DIR! >> "%LOGFILE%"
)

REM Sichere kritische Dateien
if exist "config.json" (
    copy "config.json" "!BACKUP_DIR!\config.json" >nul
    if %ERRORLEVEL% equ 0 (
        echo  - config.json gesichert
    )
)

if exist "werkstatt_index.db" (
    copy "werkstatt_index.db" "!BACKUP_DIR!\werkstatt_index.db" >nul
    if %ERRORLEVEL% equ 0 (
        echo  - werkstatt_index.db gesichert
    )
)

if exist "patterns.json" (
    copy "patterns.json" "!BACKUP_DIR!\patterns.json" >nul
    if %ERRORLEVEL% equ 0 (
        echo  - patterns.json gesichert
    )
)

if exist "data" (
    xcopy "data" "!BACKUP_DIR!\data" /E /I /Q >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo  - data\ Verzeichnis gesichert
    )
)

echo Backup erstellt in: !BACKUP_DIR!

echo.
echo [2/4] Hole aktuelle Aenderungen von GitHub...
echo [STEP 2/4] Git Fetch... >> "%LOGFILE%"
echo Pruefe Remote: >> "%LOGFILE%"
git remote -v >> "%LOGFILE%" 2>&1
echo. >> "%LOGFILE%"
echo Pruefe Netzwerk-Verbindung zu GitHub... >> "%LOGFILE%"
ping github.com -n 2 >> "%LOGFILE%" 2>&1
echo. >> "%LOGFILE%"
echo Starte Git Fetch... >> "%LOGFILE%"
git fetch origin main --verbose >> "%LOGFILE%" 2>&1
set FETCH_ERROR=!ERRORLEVEL!
if !FETCH_ERROR! neq 0 (
    color 0C
    echo [ERROR] Git fetch fehlgeschlagen (Exit-Code: !FETCH_ERROR!) >> "%LOGFILE%"
    echo. >> "%LOGFILE%"
    echo Git Config: >> "%LOGFILE%"
    git config --list >> "%LOGFILE%" 2>&1
    echo. >> "%LOGFILE%"
    echo Git Remote: >> "%LOGFILE%"
    git remote show origin >> "%LOGFILE%" 2>&1
    echo. >> "%LOGFILE%"
    echo.
    echo FEHLER: Konnte Aenderungen nicht abrufen! (Exit-Code: !FETCH_ERROR!)
    echo.
    echo Moegliche Ursachen:
    echo 1. Netzwerkverbindung zu GitHub unterbrochen
    echo 2. Firewall blockiert Git
    echo 3. GitHub Repository nicht erreichbar
    echo 4. Git Authentifizierung fehlgeschlagen
    echo 5. Remote 'origin' nicht korrekt konfiguriert
    echo.
    echo Das Backup wurde trotzdem erstellt unter:
    echo !BACKUP_DIR!
    echo.
    echo Detaillierte Fehlerinfo in update.log
    pause
    exit /b 1
)
echo [OK] Git fetch erfolgreich >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo.
echo [3/4] Pruefe auf lokale Aenderungen...
echo [STEP 3/4] Lokale Aenderungen pruefen... >> "%LOGFILE%"
git status --porcelain >> "%LOGFILE%"
for /f %%i in ('git status --porcelain ^| find /c /v ""') do set CHANGED_FILES=%%i
if !CHANGED_FILES! gtr 0 (
    echo Lokale Aenderungen: !CHANGED_FILES! Datei(en) >> "%LOGFILE%"
    echo.
    echo Warnung: !CHANGED_FILES! lokale Aenderung(en) gefunden.
    echo Diese werden automatisch committet vor dem Update.
    echo.
    git add -A >> "%LOGFILE%" 2>&1
    git commit -m "Auto-commit vor Update (update.bat)" >> "%LOGFILE%" 2>&1
    if !ERRORLEVEL! neq 0 (
        echo Hinweis: Commit fehlgeschlagen oder keine commitbaren Aenderungen >> "%LOGFILE%"
        echo Hinweis: Commit fehlgeschlagen oder keine commitbaren Aenderungen
    ) else (
        echo [OK] Auto-commit erfolgreich >> "%LOGFILE%"
    )
) else (
    echo [OK] Keine lokalen Aenderungen >> "%LOGFILE%"
    echo Keine lokalen Aenderungen gefunden.
)

echo.
echo [4/4] Aktualisiere lokalen Code...
echo [STEP 4/4] Git Pull... >> "%LOGFILE%"
echo Aktueller Branch: >> "%LOGFILE%"
git branch >> "%LOGFILE%" 2>&1
echo. >> "%LOGFILE%"
echo Aktuelle Commits: >> "%LOGFILE%"
git log --oneline -5 >> "%LOGFILE%" 2>&1
echo. >> "%LOGFILE%"
echo Starte Git Pull... >> "%LOGFILE%"
git pull origin main --verbose >> "%LOGFILE%" 2>&1
set PULL_ERROR=!ERRORLEVEL!
if !PULL_ERROR! neq 0 (
    color 0C
    echo [ERROR] Git pull fehlgeschlagen (Exit-Code: !PULL_ERROR!) >> "%LOGFILE%"
    echo. >> "%LOGFILE%"
    echo Git Status (detailliert): >> "%LOGFILE%"
    git status --verbose >> "%LOGFILE%" 2>&1
    echo. >> "%LOGFILE%"
    echo Git Diff: >> "%LOGFILE%"
    git diff >> "%LOGFILE%" 2>&1
    echo. >> "%LOGFILE%"
    echo Konflikt-Dateien: >> "%LOGFILE%"
    git diff --name-only --diff-filter=U >> "%LOGFILE%" 2>&1
    echo. >> "%LOGFILE%"
    echo.
    echo FEHLER: Update fehlgeschlagen! (Exit-Code: !PULL_ERROR!)
    echo.
    echo Moegliche Ursachen und Loesungen:
    echo.
    echo 1. MERGE-KONFLIKT:
    echo    - Lokale Aenderungen kollidieren mit Remote-Aenderungen
    echo    - Loesung: Konflikte in den betroffenen Dateien manuell auflosen
    echo.
    echo 2. UNCOMMITTED CHANGES:
    echo    - Lokale Aenderungen wurden nicht committed
    echo    - Loesung: Aenderungen stashen mit 'git stash'
    echo.
    echo 3. FORCED RESET NOTWENDIG:
    echo    - Loesung: 'git reset --hard origin/main' (ACHTUNG: Lokale Aenderungen gehen verloren!)
    echo.
    echo Das Backup ist verfuegbar unter:
    echo !BACKUP_DIR!
    echo.
    echo Detaillierte Fehlerinfo in update.log
    echo.
    echo Zum manuellen Beheben oeffnen Sie Git Bash hier und fuehren Sie aus:
    echo   git status
    echo   git diff
    pause
    exit /b 1
)
echo [OK] Git pull erfolgreich >> "%LOGFILE%"
echo. >> "%LOGFILE%"
echo Neue Commits: >> "%LOGFILE%"
git log --oneline -5 >> "%LOGFILE%" 2>&1
echo. >> "%LOGFILE%"

color 0A
echo. >> "%LOGFILE%"
echo [SUCCESS] Update erfolgreich abgeschlossen >> "%LOGFILE%"
echo Backup: !BACKUP_DIR! >> "%LOGFILE%"
echo ============================================================ >> "%LOGFILE%"
echo.
echo ============================================================
echo Update erfolgreich abgeschlossen!
echo ============================================================
echo.
echo Neue Version wurde installiert.
echo Alte Dateien sind im Backup gesichert:
echo !BACKUP_DIR!
echo.
echo Log-Datei: %LOGFILE%
echo.
echo Druecken Sie eine beliebige Taste zum Beenden...
pause >nul
color 07
exit /b 0

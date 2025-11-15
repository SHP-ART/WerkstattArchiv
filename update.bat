@echo off
REM ============================================================
REM WerkstattArchiv - Update Script (robuste Version)
REM Aktualisiert das Repository vom GitHub mit Backup
REM ============================================================

setlocal enabledelayedexpansion
color 0A

echo.
echo ============================================================
echo WerkstattArchiv Update Tool
echo ============================================================
echo.

REM Setze Fehlerbehandlung
set ERRORLEVEL=0

REM Prüfe ob Git installiert ist
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    color 0C
    echo.
    echo FEHLER: Git ist nicht installiert!
    echo.
    echo Bitte installieren Sie Git von: https://git-scm.com/
    echo.
    pause
    exit /b 1
)

REM Prüfe ob wir in einem Git-Repository sind
if not exist ".git" (
    color 0C
    echo.
    echo FEHLER: Dies ist kein Git-Repository!
    echo.
    echo Bitte fuehren Sie dieses Script im WerkstattArchiv-Ordner aus.
    echo Aktueller Ordner: %CD%
    echo.
    pause
    exit /b 1
)

REM Erstelle Backup BEVOR Update gestartet wird (robuste Version - Issue: No backup before update.bat)
set TIMESTAMP=%date:~6,4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%CD%\backup_before_git_update_%TIMESTAMP%

echo [1/4] Erstelle Backup von wichtigen Dateien...
if not exist "!BACKUP_DIR!" (
    mkdir "!BACKUP_DIR!"
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
git fetch origin main
if %ERRORLEVEL% neq 0 (
    color 0C
    echo.
    echo FEHLER: Konnte Aenderungen nicht abrufen!
    echo.
    echo Moegliche Ursachen:
    echo - Netzwerkverbindung unterbrochen
    echo - GitHub ist nicht erreichbar
    echo.
    echo Das Backup wurde trotzdem erstellt unter:
    echo !BACKUP_DIR!
    echo.
    pause
    exit /b 1
)

echo.
echo [3/4] Pruefe auf lokale Aenderungen...
git status --porcelain >nul
if %ERRORLEVEL% equ 0 (
    echo Warnung: Lokale Aenderungen gefunden.
    echo Diese werden beibehalten (stash wird nicht verwendet).
    echo.
)

echo.
echo [4/4] Aktualisiere lokalen Code...
git pull origin main
if %ERRORLEVEL% neq 0 (
    color 0C
    echo.
    echo FEHLER: Update fehlgeschlagen!
    echo.
    echo Moegliche Loesungen:
    echo 1. Loesen Sie Git-Konflikte manuell auf
    echo 2. Starten Sie Git Bash und fuehren Sie 'git status' aus
    echo 3. Verwenden Sie 'git reset --hard origin/main' zum erzwungenen Update
    echo.
    echo Das Backup ist verfügbar unter:
    echo !BACKUP_DIR!
    echo.
    pause
    exit /b 1
)

color 0A
echo.
echo ============================================================
echo Update erfolgreich abgeschlossen!
echo ============================================================
echo.
echo Neue Version wurde installiert.
echo Alte Dateien sind im Backup gesichert:
echo !BACKUP_DIR!
echo.
echo Druecken Sie eine beliebige Taste zum Beenden...
pause >nul
color 07
exit /b 0

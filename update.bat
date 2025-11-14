@echo off
REM ============================================================
REM WerkstattArchiv - Update Script
REM Aktualisiert das Repository vom GitHub
REM ============================================================

echo.
echo ============================================================
echo WerkstattArchiv Update
echo ============================================================
echo.

REM Prüfe ob Git installiert ist
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo FEHLER: Git ist nicht installiert!
    echo Bitte installieren Sie Git von: https://git-scm.com/
    pause
    exit /b 1
)

REM Prüfe ob wir in einem Git-Repository sind
if not exist ".git" (
    echo FEHLER: Dies ist kein Git-Repository!
    echo Bitte fuehren Sie dieses Script im WerkstattArchiv-Ordner aus.
    pause
    exit /b 1
)

echo [1/3] Hole aktuelle Aenderungen von GitHub...
git fetch origin
if %ERRORLEVEL% neq 0 (
    echo FEHLER: Konnte Aenderungen nicht abrufen!
    pause
    exit /b 1
)

echo.
echo [2/3] Pruefe auf lokale Aenderungen...
git status --porcelain >nul
if %ERRORLEVEL% equ 0 (
    echo Warnung: Lokale Aenderungen gefunden.
    echo Diese werden beibehalten.
)

echo.
echo [3/3] Aktualisiere lokalen Code...
git pull origin main
if %ERRORLEVEL% neq 0 (
    echo FEHLER: Update fehlgeschlagen!
    echo Moeglicherweise gibt es Konflikte.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Update erfolgreich abgeschlossen!
echo ============================================================
echo.
echo Druecken Sie eine beliebige Taste zum Beenden...
pause >nul

# Update-System für WerkstattArchiv

## Übersicht

Das Update-System ermöglicht automatische Updates von GitHub mit vollständigem Schutz Ihrer Einstellungen und Daten.

## Features

### ✅ Windows-Optimiert
- Spezielle Batch-Datei für sauberen Neustart
- Besseres Error-Handling bei Dateizugriff
- Automatische Rechteverwaltung
- Fallback-Mechanismen bei Problemen

### 🛡️ Automatisches Backup
Bei jedem Update wird automatisch ein Backup erstellt:
- **config.json** - Alle Programmeinstellungen
- **werkstatt_index.db** - Suchindex und Legacy-Aufträge
- **patterns.json** - Erkennungsmuster
- **data/vehicles.csv** - Fahrzeugdatenbank
- **data/config_backup.json** - Zentrales Backup
- **data/** - Komplettes data-Verzeichnis

Backup-Ordner: `backup_before_update_[ZEITSTEMPEL]/`

### 🔒 Geschützte Dateien
Diese Dateien werden **NIEMALS** durch Updates überschrieben:
- `config.json` - Ihre Einstellungen
- `werkstatt_index.db` - Ihre Datenbank
- `patterns.json` - Ihre Muster
- `data/` - Alle Ihre Daten
- `kunden.csv` - Ihre Kundendaten
- `logs/` - Ihre Logdateien
- `backups/` - Ihre Backups

### 🔄 Automatisches Restore bei Fehlern
Falls ein Update fehlschlägt:
1. ✓ `config.json` wird automatisch wiederhergestellt
2. ✓ `patterns.json` wird automatisch wiederhergestellt
3. ✓ `data/config_backup.json` wird wiederhergestellt
4. ⚠️ Sie bekommen eine Meldung über den Restore-Status
5. 📦 Vollständiges Backup bleibt verfügbar für manuelle Wiederherstellung

## Update-Prozess

### 1. Update prüfen
```python
from services.updater import UpdateManager

manager = UpdateManager("0.8.7")
update_available, version_info, download_url = manager.check_for_updates()

if update_available:
    print(f"Neues Update verfügbar: {version_info}")
```

### 2. Update installieren
```python
def progress_update(percent, message):
    print(f"{percent}% - {message}")

success, message = manager.download_and_install_update(
    download_url,
    progress_callback=progress_update
)

if success:
    manager.restart_application()
```

### 3. Bei Problemen
Falls das Update fehlschlägt:
1. Ihre Einstellungen wurden automatisch wiederhergestellt
2. Das Backup finden Sie in: `backup_before_update_[ZEITSTEMPEL]/`
3. Kopieren Sie bei Bedarf Dateien manuell zurück

## Update-Arten

### Commit-basierte Updates (Standard)
- Prüft auf neue Commits im main-Branch
- Schnellere Updates als Releases
- Zeigt Commit-Message und -Hash

### Release-basierte Updates (Fallback)
- Prüft auf neue Tagged Releases
- Fallback wenn Commit-Check fehlschlägt
- Zeigt Versionsnummer

## Windows-spezifische Features

### Restart-Batch-Datei
Bei Neustart auf Windows wird eine temporäre Batch-Datei erstellt:
```batch
@echo off
echo WerkstattArchiv Neustart...
echo Warte 3 Sekunden...
timeout /t 3 /nobreak >nul

echo Starte Anwendung neu...
cd /d "C:\Path\To\WerkstattArchiv"
start "WerkstattArchiv" "python.exe" "main.py"

if errorlevel 1 (
    echo Fehler beim Starten!
    pause
)
exit
```

### Datei-Berechtigungen
- Automatisches Setzen von Schreibrechten vor dem Überschreiben
- Fallback: Umbenennen zu `.old` bei Zugriffsproblemen
- Graceful Degradation bei Permission-Errors

## Fehlerbehandlung

### Bei Download-Fehlern
- SSL-Kontext wird automatisch angepasst
- Fallback von Commit-Check zu Release-Check
- Timeout-Handling

### Bei Install-Fehlern
- Automatischer Config-Restore
- Backup bleibt erhalten
- Detaillierte Fehlermeldungen
- Hinweise auf manuelle Wiederherstellung

### Bei Restart-Fehlern
- Fallback-Start ohne Verzögerung
- Detailliertes Error-Logging
- Keine Datenverluste

## Sicherheit

### Was wird aktualisiert
- ✅ `main.py` - Hauptprogramm
- ✅ `version.py` - Versionsinformationen
- ✅ `services/` - Core-Services
- ✅ `ui/` - GUI-Komponenten
- ✅ `core/` - Kernfunktionen
- ✅ `docs/` - Dokumentation
- ✅ `requirements.txt` - Abhängigkeiten
- ✅ `README.md` - Anleitungen

### Was wird NICHT verändert
- ❌ `config.json`
- ❌ `werkstatt_index.db`
- ❌ `patterns.json`
- ❌ `data/` (alle Daten)
- ❌ `kunden.csv`
- ❌ `logs/`
- ❌ `backups/`

## Best Practices

### Vor dem Update
1. ✅ Schließen Sie alle offenen Dokumente
2. ✅ Beenden Sie laufende Scan-Vorgänge
3. ✅ Notieren Sie sich Ihre wichtigsten Einstellungen (optional)

### Nach dem Update
1. ✅ Prüfen Sie ob die Anwendung startet
2. ✅ Überprüfen Sie Ihre Einstellungen im Einstellungen-Tab
3. ✅ Testen Sie die Basisfunktionen
4. ✅ Bei Problemen: Backup wiederherstellen

### Manuelle Wiederherstellung
Falls automatisches Restore nicht funktioniert:

1. Finden Sie Ihr Backup:
   ```
   backup_before_update_[ZEITSTEMPEL]/
   ```

2. Kopieren Sie die Dateien zurück:
   ```bash
   # Windows (CMD)
   copy "backup_before_update_20241114_120000\config.json" "."
   copy "backup_before_update_20241114_120000\patterns.json" "."
   xcopy "backup_before_update_20241114_120000\data" "data" /E /I
   
   # macOS/Linux
   cp backup_before_update_20241114_120000/config.json .
   cp backup_before_update_20241114_120000/patterns.json .
   cp -r backup_before_update_20241114_120000/data/ data/
   ```

3. Starten Sie die Anwendung neu

## Technische Details

### Zeitstempel-Format
```
backup_before_update_YYYYMMDD_HHMMSS
Beispiel: backup_before_update_20241114_153045
```

### Backup-Struktur
```
backup_before_update_20241114_153045/
├── config.json
├── werkstatt_index.db
├── patterns.json
└── data/
    ├── vehicles.csv
    └── config_backup.json
```

### Update-URL
```
https://github.com/SHP-ART/WerkstattArchiv/archive/refs/heads/main.zip
```

### API-Endpunkte
- Commits: `https://api.github.com/repos/SHP-ART/WerkstattArchiv/commits/main`
- Releases: `https://api.github.com/repos/SHP-ART/WerkstattArchiv/releases/latest`

## Fehlerbehebung

### "Update konnte nicht heruntergeladen werden"
- Überprüfen Sie Ihre Internetverbindung
- Firewall könnte GitHub blockieren
- Versuchen Sie es später erneut

### "Installation fehlgeschlagen"
- Ihre Einstellungen wurden automatisch wiederhergestellt
- Prüfen Sie das Backup-Verzeichnis
- Starten Sie die Anwendung neu

### "Anwendung startet nach Update nicht"
1. Öffnen Sie Command Prompt (Windows) oder Terminal
2. Navigieren Sie zum WerkstattArchiv-Ordner
3. Starten Sie manuell: `python main.py`
4. Bei Fehlermeldung: Backup wiederherstellen

### "Einstellungen sind weg"
1. Prüfen Sie: `data/config_backup.json` existiert
2. Öffnen Sie die GUI → Einstellungen-Tab
3. Klicken Sie auf "Backup wiederherstellen"
4. Alternativ: Manuell aus `backup_before_update_*` kopieren

## Support

Bei Problemen:
1. 📦 Backup-Verzeichnis sichern
2. 📝 Fehlermeldung notieren
3. 🐛 Issue auf GitHub erstellen: https://github.com/SHP-ART/WerkstattArchiv/issues
4. 💡 Oder: Backup manuell wiederherstellen und alten Code weiterverwenden

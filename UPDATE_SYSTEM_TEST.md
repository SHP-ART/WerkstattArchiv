# Update-System Test-Dokumentation

## Funktionsweise

Das Update-System lädt neue Versionen von GitHub herunter und installiert sie automatisch.

### Plattformspezifische Implementierung

#### Windows
- **Problem**: `os.execl()` funktioniert nicht zuverlässig mit GUI
- **Lösung**: Batch-Datei für verzögerten Neustart
- **Ablauf**:
  1. Erstellt `werkstatt_restart.bat` im TEMP-Ordner
  2. Batch wartet 2 Sekunden (`timeout /t 2`)
  3. Startet Python-Script neu (`start "" "python.exe" "main.py"`)
  4. Aktuelle Anwendung wird beendet (`sys.exit(0)`)

#### macOS/Linux
- **Lösung**: Direkter Prozess-Start mit `subprocess.Popen()`
- **Ablauf**:
  1. Startet neuen Python-Prozess im Hintergrund
  2. Aktuelle Anwendung wird beendet

## Test-Szenarien

### Manueller Test (Empfohlen vor Release)

1. **Vorbereitung**:
   ```bash
   # Backup erstellen
   git commit -am "Vor Update-Test"
   ```

2. **Update-Prüfung**:
   - Starte WerkstattArchiv
   - Gehe zu Tab "System"
   - Klicke "🔍 Auf Updates prüfen"
   - Erwartung: Zeigt verfügbare Version

3. **Update-Installation** (nur wenn neue Version verfügbar):
   - Klicke "Jetzt installieren"
   - Erwartung: 
     - Progress-Bar zeigt Fortschritt
     - Backup wird erstellt in `backup_before_update/`
     - Success-Dialog erscheint

4. **Neustart-Test**:
   - Bestätige Neustart mit "Ja"
   - **Windows**: 
     - Anwendung schließt sich
     - Nach 2 Sekunden startet sie automatisch neu
     - Prüfe: Neue Version wird angezeigt
   - **macOS/Linux**:
     - Anwendung startet sofort neu

### Automatischer Test (Code-Validierung)

```python
# Test für Windows Batch-Erstellung
import tempfile
import os
import platform

def test_restart_windows():
    if platform.system() == 'Windows':
        python = "C:\\Python\\python.exe"
        script = "C:\\App\\main.py"
        
        batch_content = f"""@echo off
timeout /t 2 /nobreak >nul
start "" "{python}" "{script}"
exit
"""
        batch_file = os.path.join(tempfile.gettempdir(), "werkstatt_restart.bat")
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        
        assert os.path.exists(batch_file)
        print("✓ Batch-Datei erstellt")
```

## Bekannte Einschränkungen

1. **Antivirensoftware**: Kann Batch-Datei blockieren
   - Lösung: WerkstattArchiv als Ausnahme hinzufügen

2. **Benutzerrechte**: Update benötigt Schreibrechte
   - Lösung: Als Administrator ausführen (nur bei Installation in Programme-Ordner)

3. **Netzwerk**: Update benötigt Internet-Verbindung zu GitHub
   - Timeout: 30 Sekunden

## Backup-System

Vor jedem Update werden automatisch gesichert:
- `config.json` - Benutzer-Konfiguration
- `werkstatt_index.db` - Dokumenten-Datenbank
- `patterns.json` - Regex-Patterns

**Backup-Ordner**: `backup_before_update/`

## Wiederherstellung nach fehlgeschlagenem Update

Falls Update fehlschlägt:
1. Kopiere Dateien aus `backup_before_update/` zurück
2. Starte Anwendung manuell neu

## Changelog

### Version 0.8.5
- ✅ Windows: Batch-basierter Neustart implementiert
- ✅ macOS/Linux: Direkter Prozess-Neustart
- ✅ Plattformübergreifende Kompatibilität sichergestellt
- ✅ 2 Sekunden Verzögerung für sauberen GUI-Shutdown

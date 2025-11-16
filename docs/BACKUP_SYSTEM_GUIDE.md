# 🛡️ Backup-System Guide

## Überblick

Das WerkstattArchiv-Backup-System sichert automatisch **alle wichtigen Einstellungen** im `data/config_backup.json` und schützt vor Datenverlust bei:

- ✅ Neuinstallation des Programms
- ✅ Updates die `config.json` überschreiben könnten
- ✅ Versehentlichem Löschen der Konfiguration
- ✅ Wechsel zwischen verschiedenen Archiv-Ordnern

---

## Automatische Sicherung

### Was wird gesichert?

**Pfad-Einstellungen:**
- `root_dir` - Basis-Verzeichnis (Archiv-Ordner)
- `input_dir` - Eingangsordner
- `unclear_dir` - Ordner für unklare Dokumente
- `duplicates_dir` - Ordner für Duplikate
- `customers_file` - Pfad zur Kundendatei
- `tesseract_path` - Pfad zu Tesseract OCR

**Ordnerstruktur-Einstellungen:**
- `folder_template` - Ordner-Struktur-Vorlage (z.B. `{kunde}/{jahr}`)
- `filename_template` - Dateinamen-Vorlage (z.B. `{auftrag}_{typ}.pdf`)
- `replace_spaces` - Leerzeichen durch Unterstriche ersetzen
- `remove_invalid_chars` - Ungültige Zeichen entfernen
- `use_month_names` - Monatsnamen statt Zahlen verwenden

**Zusätzliche Dateien:**
- `patterns.json` - Erkennungsmuster
- `data/vehicles.csv` - Fahrzeug-Kundenzuordnungen

### Wann wird gesichert?

Automatisch bei jedem Speichern über **"Alle Einstellungen speichern"** in den Einstellungen.

---

## Intelligenter Vergleich

### Schritt 1: Backup-Vergleich beim Speichern

Wenn du Einstellungen änderst und speicherst, prüft das System automatisch:

```
Neue Einstellungen ≠ Letztes Backup?
    ↓ JA
Dialog erscheint mit Unterschieden
```

### Schritt 2: Vergleichs-Dialog

Der Dialog zeigt dir:

#### Header
- 💾 Zeitstempel des letzten Backups
- 📋 Version des Backups
- ℹ️ Hinweis auf Änderungen

#### Unterschiede-Tabelle

**Pfad-Einstellungen:**
| Einstellung | Neue Einstellung | Backup-Einstellung |
|-------------|-----------------|-------------------|
| Basis-Verzeichnis | `/neu/pfad` | `/alt/pfad` |
| Eingangsordner | `/neu/eingang` | `/alt/eingang` |
| ... | ... | ... |

**Ordnerstruktur-Einstellungen:**
| Einstellung | Neue Einstellung | Backup-Einstellung |
|-------------|-----------------|-------------------|
| Ordner-Vorlage | `{kunde}/{jahr}` | `{kunde}/{jahr}/{monat}` |
| Dateinamen-Vorlage | `{auftrag}.pdf` | `RE_{auftrag}.pdf` |
| ... | ... | ... |

#### Drei Optionen

**✅ Neue Einstellungen speichern** (Empfohlen)
- Speichert deine neuen Einstellungen
- Überschreibt das alte Backup mit den neuen Einstellungen
- ✅ **Backup wird aktualisiert**
- ✅ **Archiv-Config wird synchronisiert**

**🔄 Backup wiederherstellen** (Änderungen verwerfen)
- Verwirft deine Änderungen
- Stellt die Einstellungen aus dem Backup wieder her
- ⚠️ **Alle Änderungen gehen verloren**
- ✅ **GUI wird mit Backup-Werten aktualisiert**

**❌ Abbrechen** (Nicht speichern)
- Bricht den Speichervorgang ab
- Weder neue Einstellungen noch Backup werden angewendet
- Du kannst Einstellungen weiter bearbeiten

---

## Anwendungsfälle

### Szenario 1: Pfade ändern und speichern
```
1. Ändere Basis-Verzeichnis von /alt/pfad zu /neu/pfad
2. Klicke "Alle Einstellungen speichern"
3. 💬 Dialog erscheint: "Basis-Verzeichnis hat sich geändert"
4. ✅ Wähle "Neue Einstellungen speichern"
5. ✓ Backup wird mit neuem Pfad aktualisiert
```

### Szenario 2: Versehentliche Änderung rückgängig machen
```
1. Ändere versehentlich mehrere Pfade
2. Klicke "Alle Einstellungen speichern"
3. 💬 Dialog zeigt alle Änderungen
4. 🔄 Wähle "Backup wiederherstellen"
5. ✓ Alte Einstellungen werden wiederhergestellt
6. ✓ GUI zeigt wieder alte Werte
```

### Szenario 3: Nach Neuinstallation
```
1. Frische Installation von WerkstattArchiv
2. config.json fehlt oder ist leer
3. ✅ Programm findet automatisch data/config_backup.json
4. 🔄 Stellt alle Einstellungen automatisch wieder her
5. ✓ Du kannst sofort weiterarbeiten
```

### Szenario 4: Zwischen Archiv-Ordnern wechseln
```
1. Ändere Basis-Verzeichnis zu bestehendem Archiv
2. 💬 Erst erscheint Backup-Vergleich (falls geändert)
3. 💬 Dann erscheint Archiv-Config-Vergleich (falls vorhanden)
4. ✓ Du entscheidest welche Config verwendet werden soll
```

---

## Manuelle Wiederherstellung

### Über die GUI

1. Öffne **Einstellungen-Tab**
2. Scrolle zu **"🛡️ Config-Backup & Wiederherstellung"**
3. Klicke **"🔄 Backup wiederherstellen"**
4. Bestätige die Sicherheitsabfrage
5. ✓ Alle Einstellungen werden wiederhergestellt

### Über die Konsole

Falls die GUI nicht startet:

```bash
python3 -c "
from core.config_backup import ConfigBackupManager
import json

backup = ConfigBackupManager()
config = backup.restore_backup()

if config:
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print('✅ Backup wiederhergestellt')
else:
    print('❌ Kein Backup gefunden')
"
```

---

## Zusammenspiel mit Archiv-Config

Das System arbeitet zweistufig:

### Stufe 1: Backup-Vergleich (data/config_backup.json)
- Vergleicht **Programm-Einstellungen** mit letztem Backup
- Prüft **alle wichtigen Pfade und Ordnerstruktur-Einstellungen**
- Dialog erscheint nur bei Änderungen

### Stufe 2: Archiv-Config-Vergleich (.werkstattarchiv_structure.json)
- Vergleicht **nur Ordnerstruktur-Einstellungen** mit Archiv
- Prüft nur wenn **Basis-Verzeichnis geändert** wurde
- Dialog erscheint nur bei Unterschieden zum Archiv

**Ablauf beim Speichern:**
```
save_settings()
    ↓
[1] Backup-Vergleich (alle Einstellungen)
    ↓ Unterschiede?
    ├─ JA → Dialog: Neue speichern / Backup / Abbrechen
    └─ NEIN → Weiter
    ↓
[2] Basis-Verzeichnis geändert?
    ↓ JA
    └─ Archiv-Config-Vergleich (nur Ordnerstruktur)
        ↓ Unterschiede?
        ├─ JA → Dialog: Archiv / Eigene / Abbrechen
        └─ NEIN → Weiter
    ↓
[3] Speichern
    ├─ config.json (Programm-Config)
    ├─ .werkstattarchiv_structure.json (Archiv-Config)
    └─ data/config_backup.json (Backup)
```

---

## Backup-Datei-Struktur

```json
{
  "timestamp": "2025-11-16T10:30:45.123456",
  "version": "0.8.7",
  "config": {
    "root_dir": "/pfad/zum/archiv",
    "input_dir": "/pfad/zum/eingang",
    "unclear_dir": "/pfad/zu/unklar",
    "duplicates_dir": "/pfad/zu/duplikate",
    "customers_file": "/pfad/zur/kunden.csv",
    "tesseract_path": null,
    "folder_structure": {
      "folder_template": "{kunde}/{jahr}",
      "filename_template": "{auftrag}_{typ}.pdf",
      "replace_spaces": false,
      "remove_invalid_chars": true,
      "use_month_names": false
    }
  },
  "files": {
    "patterns.json": { ... },
    "data/vehicles.csv": "..."
  }
}
```

---

## Technische Details

### Vergleichs-Logik

```python
# In ConfigBackupManager.compare_with_current()

WICHTIGE_KEYS = [
    "root_dir",
    "input_dir", 
    "unclear_dir",
    "duplicates_dir",
    "customers_file",
    "tesseract_path"
]

STRUKTUR_KEYS = [
    "folder_template",
    "filename_template",
    "replace_spaces",
    "remove_invalid_chars",
    "use_month_names"
]
```

### Rückgabewert

```python
{
    "has_differences": True/False,
    "backup_exists": True/False,
    "path_differences": [(key, current, backup), ...],
    "structure_differences": [(key, current, backup), ...],
    "backup_timestamp": "2025-11-16T10:30:45",
    "backup_version": "0.8.7"
}
```

---

## Logs

Das System protokolliert alle Backup-Aktionen:

```
INFO: Backup-Vergleich durchgeführt - 3 Unterschiede gefunden
INFO: Backup-Config übernommen - Einstellungen wiederhergestellt
SUCCESS: Einstellungen gespeichert - Programm-Config + Archiv-Config + Backup
WARNING: Backup nicht gefunden - Erstelle neues beim nächsten Speichern
ERROR: Fehler beim Vergleichen mit Backup - [Details]
```

---

## Best Practices

### ✅ Empfehlungen

1. **Regelmäßig speichern**: Klicke "Alle Einstellungen speichern" nach wichtigen Änderungen
2. **Backup-Status prüfen**: Achte auf grünes "✓ Letztes Backup" in den Einstellungen
3. **Unterschiede prüfen**: Lies den Vergleichs-Dialog sorgfältig bevor du entscheidest
4. **data/-Ordner sichern**: Kopiere den kompletten `data/`-Ordner für manuelle Backups

### ⚠️ Vorsicht

1. **Nicht überstürzen**: Der Vergleichs-Dialog ist da um dir zu helfen
2. **Backup-Timestamp prüfen**: Stelle sicher dass das Backup aktuell ist
3. **Bei Unsicherheit**: Wähle "Abbrechen" und prüfe deine Änderungen nochmal
4. **Wichtige Änderungen**: Notiere dir wichtige Pfad-Änderungen separat

---

## Troubleshooting

### Dialog erscheint nicht obwohl ich Pfade geändert habe

**Lösung:**
- Prüfe ob du "Alle Einstellungen speichern" geklickt hast
- Prüfe ob `data/config_backup.json` existiert
- Bei erstem Speichern erscheint kein Dialog (kein Backup vorhanden)

### "Backup wiederherstellen" macht nichts

**Lösung:**
- Prüfe Logs-Tab für Fehlermeldungen
- Stelle sicher dass `data/config_backup.json` existiert und gültig ist
- Versuche manuelles Restore über Konsole

### Einstellungen werden nicht in GUI aktualisiert

**Lösung:**
- Nach "Backup wiederherstellen" Programm neu starten
- Prüfe ob `_reload_settings_in_gui()` im Log auftaucht
- Bei Problemen: Manuelle Wiederherstellung und Neustart

### Backup enthält alte Pfade

**Lösung:**
- Das ist normal wenn du gerade neue Pfade eingegeben hast
- Dialog zeigt dir die Unterschiede
- Wähle "Neue Einstellungen speichern" um Backup zu aktualisieren

---

## Support

Bei Fragen oder Problemen:

1. **Logs prüfen**: Öffne "Logs"-Tab und suche nach Backup-Meldungen
2. **Backup-Status**: Prüfe Status in Einstellungen-Tab
3. **Backup-Datei prüfen**: Öffne `data/config_backup.json` in Texteditor
4. **GitHub Issue**: Erstelle Issue mit Screenshots und Logs

---

## Zusammenfassung

Das **WerkstattArchiv-Backup-System** bietet:

✅ **Automatische Sicherung** aller wichtigen Einstellungen  
✅ **Intelligenter Vergleich** beim Speichern  
✅ **Benutzerfreundliche Dialoge** mit klaren Unterschieden  
✅ **Manuelle Wiederherstellung** per GUI oder Konsole  
✅ **Schutz vor Datenverlust** bei Updates und Neuinstallationen  
✅ **Zusammenspiel** mit Archiv-Config-System  

**Deine Einstellungen sind sicher!** 🛡️

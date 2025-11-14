# 🔄 Intelligenter Config-Sync Guide

## Übersicht

Das WerkstattArchiv verfügt über ein intelligentes Config-Sync-System, das automatisch prüft ob ein Archiv-Ordner bereits eine eigene Konfiguration besitzt.

## Wie funktioniert es?

### 1. Basis-Verzeichnis ändern

Wenn du in den **Einstellungen** das **Basis-Verzeichnis** änderst und auf **"Alle Einstellungen speichern"** klickst, passiert folgendes:

1. ✅ **Prüfung**: System prüft ob im neuen Ordner eine `.werkstattarchiv_structure.json` existiert
2. 🔍 **Vergleich**: Falls vorhanden, werden Unterschiede zur aktuellen Config gesucht
3. 💬 **Dialog**: Bei Unterschieden erscheint ein Vergleichs-Dialog

### 2. Der Vergleichs-Dialog

Der Dialog zeigt dir:

#### Header
- 📁 Pfad zum Archiv-Ordner
- ℹ️ Information dass unterschiedliche Configs gefunden wurden

#### Unterschiede-Tabelle
| Einstellung | Deine aktuelle Config | Archiv-Config |
|------------|----------------------|---------------|
| folder_template | `{kunde}/{jahr}` | `{kunde}/{jahr}/{monat}` |
| filename_template | `{auftrag}.pdf` | `RE_{auftrag}_{datum}.pdf` |
| replace_spaces | `False` | `True` |
| ... | ... | ... |

#### Drei Optionen

**✅ Archiv-Config übernehmen** (Empfohlen für bestehendes Archiv)
- Übernimmt alle Einstellungen aus dem Archiv
- Sinnvoll wenn du mit einem bestehenden, konfigurierten Archiv arbeitest
- ✅ **Programm-Config wird aktualisiert**
- ✅ **GUI-Felder werden neu geladen**
- ✅ **Backup wird erstellt**

**📝 Meine Config behalten** (Überschreibt Archiv-Config)
- Behält deine aktuellen Einstellungen
- Überschreibt die `.werkstattarchiv_structure.json` im Archiv
- ⚠️ **Vorsicht**: Bestehende Archiv-Struktur könnte nicht mehr passen!

**❌ Abbrechen** (Anderen Ordner wählen)
- Bricht den Speichervorgang ab
- Status: "⚠️ Speichern abgebrochen - Bitte anderen Ordner wählen"
- Keine Änderungen werden gespeichert
- Du kannst einen anderen Ordner auswählen

## Anwendungsfälle

### Szenario 1: Neues Archiv erstellen
```
1. Neuen leeren Ordner als Basis-Verzeichnis wählen
2. "Alle Einstellungen speichern" klicken
3. ✓ Keine Archiv-Config gefunden → Normal speichern
4. ✓ Neue .werkstattarchiv_structure.json wird erstellt
```

### Szenario 2: Bestehendes Archiv öffnen
```
1. Ordner mit bestehendem Archiv wählen (hat bereits .werkstattarchiv_structure.json)
2. "Alle Einstellungen speichern" klicken
3. 💬 Dialog erscheint mit Unterschieden
4. ✅ "Archiv-Config übernehmen" wählen
5. ✓ Programm übernimmt Archiv-Einstellungen
6. ✓ GUI wird mit Archiv-Config aktualisiert
```

### Szenario 3: Archiv-Struktur ändern
```
1. Bestehenden Archiv-Ordner gewählt
2. Einstellungen in GUI ändern (z.B. anderes Ordner-Template)
3. "Alle Einstellungen speichern" klicken
4. 💬 Dialog erscheint mit Unterschieden
5. 📝 "Meine Config behalten" wählen
6. ⚠️ Achtung: Neue Dokumente nutzen neue Struktur!
7. ℹ️ Alte Dokumente behalten alte Struktur
```

### Szenario 4: Falscher Ordner gewählt
```
1. Versehentlich falschen Archiv-Ordner gewählt
2. "Alle Einstellungen speichern" klicken
3. 💬 Dialog zeigt fremde Archiv-Config
4. ❌ "Abbrechen" wählen
5. ✓ Nichts wird gespeichert
6. 📁 Anderen Ordner wählen
```

## Technische Details

### Geprüfte Einstellungen
- `folder_template` - Ordner-Struktur-Muster
- `filename_template` - Dateinamen-Muster
- `replace_spaces` - Leerzeichen durch _ ersetzen
- `remove_invalid_chars` - Ungültige Zeichen entfernen
- `use_month_names` - Monatsnamen verwenden

### Speicherorte
1. **Programm-Config**: `config.json` (im Programmverzeichnis)
2. **Archiv-Config**: `.werkstattarchiv_structure.json` (im Archiv-Ordner)
3. **Backup**: `data/config_backup.json` (automatisches Backup)

### Synchronisations-Flow
```
save_settings()
    ↓
Basis-Verzeichnis geändert?
    ↓ JA
_check_and_compare_archive_config()
    ↓
Archiv-Config existiert?
    ↓ JA
_compare_configs()
    ↓
Unterschiede gefunden?
    ↓ JA
_show_config_comparison_dialog()
    ↓
Benutzer wählt: [Archiv|Behalten|Abbrechen]
    ↓
[USE_ARCHIVE] → Config übernehmen + GUI reload
[KEEP_CURRENT] → Normal weitermachen
[CANCEL] → Abbrechen, nichts speichern
```

## Best Practices

### ✅ DO
- Bei bestehendem Archiv: "Archiv-Config übernehmen"
- Bei neuem Archiv: Normal speichern (kein Dialog)
- Bei Unsicherheit: "Abbrechen" und prüfen

### ❌ DON'T
- Nicht "Meine Config behalten" bei fremdem Archiv wählen
- Nicht Archiv-Config überschreiben ohne Grund
- Nicht ignorieren wenn Dialog erscheint

## Logs

Das System protokolliert alle Aktionen:

```
INFO: Keine Archiv-Config gefunden - Erstelle neue in /pfad/zum/archiv
INFO: Archiv-Config identisch - Keine Änderungen notwendig
INFO: Archiv-Config übernommen - Einstellungen aus /pfad/zum/archiv geladen
SUCCESS: Einstellungen gespeichert - Programm-Config + Archiv-Config + Backup
ERROR: Fehler beim Vergleichen der Archiv-Config - [Details]
```

## Zukünftige Features (kommende Version)

Die Abbruch-Funktion ("Anderen Ordner wählen") ist für zukünftige erweiterte Features vorbereitet:
- Automatische Migration alter Archiv-Strukturen
- Multi-Archiv-Verwaltung
- Konflikt-Auflösung bei komplexen Strukturen
- Archiv-Validierung vor Übernahme

## Troubleshooting

### Dialog erscheint nicht obwohl Archiv-Config existiert
- **Prüfen**: Basis-Verzeichnis wirklich geändert?
- **Prüfen**: `.werkstattarchiv_structure.json` ist valides JSON?
- **Lösung**: Logs im "Logs"-Tab prüfen

### "Abbrechen" gewählt aber Dialog erscheint wieder
- **Normal**: Dialog erscheint nur wenn Basis-Verzeichnis geändert wurde
- **Lösung**: Anderen Ordner wählen oder alte Einstellung wiederherstellen

### GUI-Felder nicht aktualisiert nach "Archiv-Config übernehmen"
- **Prüfen**: Logs für Fehler checken
- **Lösung**: Programm neu starten lädt Config automatisch

## Support

Bei Fragen oder Problemen:
1. Logs-Tab prüfen
2. GitHub Issue erstellen
3. Screenshots vom Dialog mitschicken

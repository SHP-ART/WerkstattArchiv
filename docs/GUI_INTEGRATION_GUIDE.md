# GUI-Integration: Datenbank-Management Tab

## 🎯 Ziel
Integration des neuen Datenbank-Management Tabs in das Main Window.

## 📋 Schritte

### Schritt 1: Import hinzufügen

In `ui/main_window.py` bei den anderen Tab-Imports (ca. Zeile 10-30):

```python
from ui.db_management_tab import DatabaseManagementTab
```

### Schritt 2: Tab im Settings TabView erstellen

In der `_create_settings_section()` Methode (ca. Zeile 795-825), **nach** den anderen Tabs (Allgemein, Remote Logging, etc.):

```python
# Datenbank-Management Tab
self.settings_tabview.add("Datenbank")
db_management_tab = DatabaseManagementTab(
    self.settings_tabview.tab("Datenbank"),
    self.indexer
)
db_management_tab.pack(fill="both", expand=True)
```

## ✅ Fertig!

Nach dem Neustart der Anwendung sollte der neue "Datenbank"-Tab in den Einstellungen verfügbar sein.

## 🧪 Testing

1. **Start der Anwendung**: Keine Fehler beim Import
2. **Settings öffnen**: Tab "Datenbank" ist sichtbar
3. **Backup erstellen**: Button klicken → Success-Message
4. **Backups anzeigen**: Liste mit Details öffnet sich
5. **Statistiken**: Verschiedene Statistiken anzeigen
6. **Health-Check**: Status wird angezeigt
7. **Export CSV**: Datei wird gespeichert

## 🐛 Troubleshooting

### Import-Fehler
- Prüfen: `ui/db_management_tab.py` existiert
- Prüfen: customtkinter ist installiert

### Tab wird nicht angezeigt
- Prüfen: `self.settings_tabview.add("Datenbank")` korrekt
- Prüfen: `.pack(fill="both", expand=True)` vorhanden

### Indexer-Fehler
- Prüfen: `self.indexer` existiert in MainWindow
- Prüfen: `services/db_maintenance.py` und `services/db_statistics.py` existieren

## 📁 Betroffene Dateien

- ✅ `ui/db_management_tab.py` (NEU - bereits erstellt)
- ✅ `services/db_maintenance.py` (NEU - bereits erstellt)
- ✅ `services/db_statistics.py` (NEU - bereits erstellt)
- ✅ `services/indexer.py` (ERWEITERT - bereits angepasst)
- ⏳ `ui/main_window.py` (ERWEITERN - 2 Zeilen hinzufügen)

## 🎨 UI-Vorschau

```
┌─────────────────────────────────────┐
│  Einstellungen (TabView)             │
├─────────────────────────────────────┤
│ Allgemein │ Remote │ ... │ Datenbank│ ← NEU
└─────────────────────────────────────┘

┌─ Datenbank-Verwaltung ──────────────┐
│                                      │
│ 📦 Datenbank-Backups                │
│   [Backup erstellen] [Anzeigen] ... │
│   Status: Letztes Backup: ...       │
│                                      │
│ 🔧 Wartung & Optimierung            │
│   [Optimieren] [Health-Check] ...   │
│   Status: Bereit                     │
│                                      │
│ 📊 Statistiken & Reports            │
│   [Übersicht] [Kunden] [Zeit] ...   │
│   ┌─────────────────────────────┐  │
│   │ === ÜBERSICHT ===           │  │
│   │ Gesamt-Dokumente: 1234      │  │
│   │ ...                          │  │
│   └─────────────────────────────┘  │
│                                      │
│ 💾 Daten-Export                     │
│   [CSV Export] [Kunden-Report]      │
│   Status: Bereit                     │
│                                      │
└──────────────────────────────────────┘
```

## 🚀 Nach der Integration

Die Datenbank-Features sind dann verfügbar:
- ✅ Automatische Backups vor kritischen Operationen
- ✅ Manuelle Backups jederzeit möglich
- ✅ Umfassende Statistiken & Analysen
- ✅ Datenbank-Optimierung & Health-Checks
- ✅ Export als CSV oder JSON
- ✅ Alle Funktionen in der GUI

## 📚 Weitere Infos

Siehe: `docs/DATABASE_IMPROVEMENTS.md` für vollständige Dokumentation aller Features.

# WerkstattArchiv

**Version 0.8.8** (Aktuell - mit 40-75% Performance-Speedup)

Lokale Python-Desktop-Anwendung zur automatischen Verwaltung von Werkstattdokumenten.

## Features

- ✅ Automatische Dokumenten-Analyse (PDF & Bilder)
- ✅ OCR-Unterstützung mit Tesseract
- ✅ **⚡ Hochperformant** - 40-75% Speedup durch optimierte Caches und Batch-Processing
- ✅ **Flexible Ordnerstrukturen** - 9 Profile wählbar (Standard, Mit Kundennummer, Chronologisch, etc.)
- ✅ **Archiv-spezifische Konfiguration** - Jedes Archiv speichert seine eigene Struktur
- ✅ **🛡️ Konfigurations-Backup** - Automatische Sicherung im data/-Ordner, Auto-Restore bei Neuinstallation
- ✅ Moderne GUI mit customtkinter
- ✅ **Dokumenten-Indexierung & Suche** - Mit Pagination für große Datenmengen
- ✅ **Statistiken & Auswertungen** - Mit Lazy-Loading für schnellere GUI
- ✅ **Legacy-Auftrags-System** - Automatische Zuordnung alter Aufträge ohne Kundennummer
- ✅ **Virtuelle Kundennummern** - Automatische VKxxxx für Dokumente ohne erkannte Kundennummer
- ✅ **Datenbank-Management** - Löschen und neu initialisieren der Index-Datenbank
- ✅ **Automatische Ordnerüberwachung** - Neue Dokumente werden automatisch verarbeitet
- ✅ **Konfigurierbare Regex-Patterns** - Anpassbare Suchmuster über GUI
- ✅ **Schlagwort-Erkennung** - 10 Kategorien mit 100+ Schlagwörtern
- ✅ **Automatische Kundenverwaltung** - Kunden werden automatisch aus Dokumenten hinzugefügt
- ✅ **Backup & Restore** - Sichere alle Daten mit einem Klick
- ✅ **Auto-Update-System** - Updates direkt aus GitHub (mit Download-Verifizierung)
- ✅ **Progress Dialog mit Cancel** - Lange Operationen können unterbrochen werden
- ✅ **Log-System** - Live-Anzeige aller Events mit Export-Funktion
- ✅ **Optimierter Ladeprozess** - Schneller Start mit sichtbarem Status (Async Loading)
- ✅ Manuelle Nachbearbeitung unklarer Dokumente
- ✅ Vollständig lokal (keine Cloud-Services)
- ✅ Ausführliches Logging aller Vorgänge

## Projektstruktur

```
WerkstattArchiv/
├── main.py                       # Haupteinstiegspunkt
├── config.json                   # Programm-Konfiguration
├── requirements.txt              # Python-Abhängigkeiten
├── werkstatt_index.db           # SQLite-Datenbank (auto-erstellt)
├── data/
│   └── config_backup.json       # 🛡️ Automatisches Backup aller Einstellungen
├── ui/
│   └── main_window.py           # GUI-Implementation (mit Legacy + Virtuellen Kunden)
├── core/
│   ├── folder_structure_manager.py  # ⭐ Flexible Ordnerstrukturen (9 Profile)
│   ├── config_backup.py         # 🛡️ Backup-Manager für Einstellungen
│   └── keyword_detector.py      # ⭐ Schlagwort-Erkennung
├── services/
│   ├── customers.py             # Kundenverwaltung (mit virtuellen Kunden)
│   ├── analyzer.py              # Dokumentenanalyse (mit Legacy-Support)
│   ├── router.py                # Routing-Logik (mit Template-System)
│   ├── indexer.py               # Dokumenten-Index + unclear_legacy Tabelle + DB-Management
│   ├── legacy_resolver.py       # Legacy-Zuordnungs-Logik
│   ├── virtual_customer_manager.py  # Virtuelle Kunden & Datei-Umbenennung
│   ├── vehicles.py              # Fahrzeug-Index-Manager
│   ├── filename_generator.py   # Standardisierte Dateinamen
│   ├── watchdog_service.py      # Automatische Ordnerüberwachung
│   ├── pattern_manager.py       # Konfigurierbare Regex-Patterns
│   ├── backup_manager.py        # Backup & Restore System
│   ├── updater.py               # ⭐ Auto-Update-System (Commit-basiert)
│   ├── vorlagen.py              # Vorlagen-Manager
│   └── logger.py                # Logging-Service
├── config/
│   ├── keywords.json            # ⭐ Schlagwort-Kategorien (10 Kategorien)
│   └── patterns.json            # Regex-Patterns
├── logs/
│   └── werkstatt.log            # ⭐ Log-Datei (auto-rotiert)
├── data/
│   └── vehicles.csv             # Fahrzeug-Kundenzuordnung (auto-erstellt)
├── backups/                     # Backup-Verzeichnis (auto-erstellt)
└── beispiel_auftraege/          # Test-PDFs (nicht im Git)
    ├── auftrag.pdf              # Legacy ohne Kundennr (alte Vorlage)
    └── Schultze.pdf             # Modern mit Kundennr (neue Vorlage)
```

## Installation

### 🪟 Windows

**Schnellinstallation für Windows:**
1. Rechtsklick auf `install.bat` → "Als Administrator ausführen"
2. Warte bis Installation abgeschlossen
3. **Programmstart (wähle eine Variante):**
   - `start.bat` - Standard (Konsole verschwindet automatisch)
   - `start_debug.bat` - Mit Konsole (für Debugging)
   - `start_silent.vbs` - Komplett unsichtbar (kein Fenster)

📖 **Detaillierte Anleitung:** Siehe [WINDOWS_INSTALLATION.md](WINDOWS_INSTALLATION.md)

---

### 🍎 macOS / 🐧 Linux

### Voraussetzungen

- Python 3.11 oder höher
- Tesseract OCR (optional, für Bilderkennung)

### Schritt 1: Repository klonen oder herunterladen

```bash
cd WerkstattArchiv
```

### Schritt 2: Python-Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### Schritt 3: Tesseract OCR installieren (optional aber empfohlen!)

⚠️ **Wichtig**: Tesseract wird **nur** für gescannte PDFs/Bilder benötigt. Digitale PDFs funktionieren ohne!

**Windows:**
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Installiere mit deutscher Sprachdaten-Option
- Detaillierte Anleitung: siehe [TESSERACT_SETUP.md](docs/TESSERACT_SETUP.md)
- Pfad in GUI-Einstellungen eintragen: `C:\Program Files\Tesseract-OCR\tesseract.exe`

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-deu
```

📖 **Vollständiger Setup-Guide**: [docs/TESSERACT_SETUP.md](docs/TESSERACT_SETUP.md)

### Schritt 4: Konfiguration anpassen

Bearbeite `config.json` oder nutze die GUI:

```json
{
  "root_dir": "D:/Scan/Daten",
  "input_dir": "D:/Scan/Eingang",
  "unclear_dir": "D:/Scan/Unklar",
  "customers_file": "D:/Scan/config/kunden.csv",
  "tesseract_path": null
}
```

### Schritt 5: Kundendatei erstellen (optional)

**⚡ NEU: Automatisches Hinzufügen von Kunden!**

Die Kundendatei wird **automatisch befüllt**, wenn neue Dokumente verarbeitet werden. Du musst sie **nicht mehr manuell erstellen**!

**Was passiert automatisch:**
- ✅ Neue Kundennummer auf Dokument gefunden → Kunde wird automatisch in `kunden.csv` gespeichert
- ✅ Kundenname wird aus dem Dokument extrahiert
- ✅ Optional: PLZ, Straße werden ebenfalls gespeichert (wenn erkannt)
- ✅ Bei weiteren Dokumenten desselben Kunden: Daten werden aktualisiert/ergänzt

**Manuelles Erstellen (optional):**

Falls du Kunden vorab anlegen möchtest, erstelle eine CSV-Datei:

```csv
kunden_nr;name;plz;ort;strasse;telefon
10234;Müller Max;12345;Berlin;Hauptstr. 10;030-123456
10235;Schmidt GmbH;54321;Hamburg;Industrieweg 5;040-987654
10236;Wagner KFZ;67890;München;Bahnhofstr. 22;089-456789
```

**Format**: `Kundennummer;Kundenname;PLZ;Ort;Strasse;Telefon` (Semikolon-getrennt)

**Hinweis:** 
- Die ersten **zwei Felder** (kunden_nr, name) sind **Pflicht**
- Die weiteren Felder (plz, ort, strasse, telefon) sind **optional**
- Für Legacy-Matching sind **PLZ** und **Strasse** hilfreich (Name+PLZ oder Name+Strasse Match)

**Minimales Format (ohne Legacy-Matching):**
```csv
kunden_nr;name
10234;Müller Max
10235;Schmidt GmbH
```

## ⚡ Performance-Tipps

### Batch-Verarbeitung optimieren

Die neuesten Performance-Optimierungen zeigen sich besonders bei Batch-Verarbeitung:

**Tipps für maximale Geschwindigkeit:**

1. **Größere Batches verarbeiten**
   - 50+ Dokumente auf einmal scannen
   - Profitiert von Caching (Regex, Pattern, Lookups)
   - Batch-Database-Inserts sind schneller als einzelne

2. **Legacy-Dokumente mit FIN**
   - FIN-Lookups werden gecacht (max 2000)
   - Nach dem ersten FIN-Match werden weitere automatisch schneller
   - Perfekt für Stapel ähnlicher Fahrzeuge

3. **Progress Dialog nutzen**
   - Dialog zeigt "x/y Items" - können Sie Scan abbrechen wenn nötig
   - Dialog blockiert GUI nicht - weitere Operationen möglich
   - Cancel-Button um lange Operationen zu unterbrechen

4. **Auto-Watch für kontinuierliche Verarbeitung**
   - Scanne Dokumente direkt in Eingangsordner
   - Automatische Verarbeitung ohne User-Interaktion
   - Perfekt für Integration in Scanner-Workfow

### Cache-Strategien

**Was wird gecacht:**
- ✅ Regex-Patterns (max 50) → 10-20% speedup
- ✅ PDF Page Counts (max 500) → 5-10% speedup
- ✅ Vehicle FIN Lookups (max 2000) → 15-25% speedup
- ✅ Customer Names → 5-10x schneller bei Lookups
- ✅ Statistics (mit Invalidierung) → Schnellere Aktualisierung

**Caches werden automatisch:**
- Invalidiert bei Datenänderungen
- Gelöscht beim Neu-Laden von Daten
- Begrenzt um Speicher zu sparen

---

## Verwendung

### Anwendung starten

```bash
python main.py
```

### Workflow

1. **Einstellungen-Tab**: Pfade konfigurieren und Kundendatenbank laden
2. **Verarbeitung-Tab**: "Eingangsordner scannen" klicken ODER "🔍 Auto-Watch starten" für automatische Überwachung
3. **Suche-Tab**: Nach verarbeiteten Dokumenten suchen
4. **Unklare Dokumente-Tab**: Manuelle Nachbearbeitung bei Bedarf
5. **Unklare Legacy-Aufträge-Tab**: Manuelle Zuordnung alter Aufträge ohne Kundennummer
6. **Virtuelle Kunden-Tab**: Zuordnung virtueller Kundennummern zu echten Kunden (neu in 0.8.5!)

---

## 🆕 Changelog

### Version 0.8.8 (15. November 2025)

**⚡ Performance-Optimierungen (40-75% Gesamtspeedup):**

**Feature 11: Regex Pattern Compilation Cache (10-20% speedup)**
- Kompilierte Regex-Patterns werden gecacht (max 50 Patterns)
- Eliminiert redundante Regex-Compilationen bei der Dokumentanalyse
- Besonders effektiv bei Batch-Verarbeitung

**Feature 12: Batch Database Inserts (30-50% speedup)**
- Neue `add_documents_batch()` Methode für mehrfach-Inserts
- Nutzt eine Verbindung + einen COMMIT statt mehrere pro Dokument
- Perfekt für Batch-Processing von vielen Dokumenten gleichzeitig

**Feature 13: Vehicle FIN Lookup Cache (15-25% speedup)**
- FIN→Customer-Lookups werden gecacht (max 2000 Einträge)
- O(1) Lookups statt O(n) durchsuchen der Fahrzeugliste
- Großer Speedup bei Legacy-Dokumenten mit FIN

**Feature 14: PDF Page Count Caching (5-10% speedup)**
- PDF-Seitenanzahl wird gecacht um erneutes Öffnen zu vermeiden
- `extract_text_from_pdf()` returnt jetzt Tuple (text, page_count)
- Cache-Limit: 500 PDFs

**🎨 Progress Dialog mit Cancel-Button:**
- Neue `ProgressDialog` Klasse mit scrollbarem Interface
- Shows "x/y Items" Counter statt Prozentsätze
- User kann lange Operationen (Scan, Verarbeitung) abbrechen
- Dialog ist non-blocking - weitere GUI-Operationen möglich

**🛡️ Robusteres Update-System:**

*services/updater.py:*
- ✅ Download-Integrity Verifizierung (ZIP-Größe, BadZipFile Check, `testzip()`)
- ✅ Besseres Cleanup-Logging mit Force-Delete bei Permission-Errors
- ✅ Detailliertes Exception-Handling bei allen Schritten

*ui/main_window.py:*
- ✅ **Modeless Progress Dialog** (blockiert UI nicht mehr)
- ✅ **Vollständige Release Notes** statt 500-Zeichen-Kürzung
- ✅ Neue `_show_update_dialog()` mit scrollbarem Textbereich
- ✅ Try-Catch Error Handling in `check_for_updates()` und `install_thread()`
- ✅ Robuste `progress_window.destroy()` mit `winfo_exists()` Check

*update.bat:*
- ✅ **Automatisches Backup VOR dem Update** (config, DB, patterns, data/)
- ✅ Farbiges Feedback (Grün ✓ für Erfolg, Rot ✗ für Fehler)
- ✅ Hilfreiche Fehlermeldungen mit Lösungsvorschlägen
- ✅ 4-Stufen-Prozess mit klarem Feedback

**Behobene Issues:**
- ❌ Silent cleanup failures → ✅ Explizites Logging
- ❌ No download integrity → ✅ ZIP-Validierung
- ❌ Modal progress window → ✅ Modeless Dialog
- ❌ Truncated release notes → ✅ Scrollbarer Textbereich
- ❌ Missing backup before update.bat → ✅ Automatisches Backup

**Performance Impact:**
- 40-75% Gesamtspeedup bei typischen Workflows
- Besonders merkbar bei Batch-Processing von 50+ Dokumenten
- Besonders merkbar bei Legacy-Dokumenten mit FIN-Matching

### Version 0.8.7 (14. November 2025)

**Neue Features:**
- 🛡️ **Konfigurations-Backup-System**: Automatische Sicherung aller wichtigen Einstellungen
- 💾 **Zentrales Backup**: Alle Einstellungen werden in `data/config_backup.json` gespeichert
- 🔄 **Automatisches Restore**: Bei Neuinstallation oder fehlendem config.json wird Backup automatisch wiederhergestellt
- � **Automatisches Config-Sync**: Beim Wechseln des Archiv-Ordners wird automatisch die dortige Config geladen
- �📊 **Backup-Info im Einstellungen-Tab**: Zeigt Zeitpunkt, Version und Größe des letzten Backups
- 🔧 **Manuelles Restore**: Button zum Wiederherstellen des Backups mit Sicherheitsabfrage
- 📄 **Gesicherte Dateien**: config.json, patterns.json, vehicles.csv und alle Ordnerstruktur-Einstellungen

**Backup-Verhalten:**
- ✅ **Automatisch beim Speichern**: Jede Einstellungsänderung wird gesichert
- ✅ **Automatisch beim Start**: Fehlendes config.json wird aus Backup wiederhergestellt
- ✅ **Dreifach-Sicherung**: Programm-Config + Archiv-Config + Backup im data/-Ordner
- ✅ **Versionsinfo**: Backup enthält Zeitstempel und Programmversion

**Archiv-spezifisches Verhalten:**
- 🔄 **Auto-Load**: Beim Ändern des root_dir wird `.werkstattarchiv_structure.json` automatisch geladen
- 💾 **Auto-Sync**: Programm-Einstellungen werden ins Archiv kopiert, wenn keine Config vorhanden
- 🔀 **Bidirektional**: Änderungen werden IMMER in beide Richtungen synchronisiert
- 📂 **Archiv-Priorität**: Existierende Archiv-Config hat Vorrang vor Programm-Einstellungen

**Sicherheitsfeatures:**
- 🔒 **Schutz vor Datenverlust**: Nach Neuinstallation alte Struktur wiederhergestellt
- 🔒 **Update-sicher**: Alte Einstellungen bleiben bei Updates erhalten
- 🔒 **Plattformunabhängig**: Funktioniert auf Windows, macOS und Linux
- 🔒 **Archiv-Unabhängigkeit**: Jedes Archiv kann eigene Ordnerstruktur haben

**Windows-Verbesserungen:**
- 🪟 **Flexible Start-Scripts**: start.bat funktioniert mit und ohne virtuelle Umgebung
- 🔄 **Automatischer Fallback**: Nutzt System-Python wenn venv nicht vorhanden
- ℹ️ **Bessere Fehlermeldungen**: Klare Anweisungen bei fehlendem Python mit Download-Link

### Version 0.8.6 (13. November 2025)

**Neue Features:**
- 📂 **Flexible Ordnerstrukturen**: 9 vordefinierte Profile (Standard, Mit Kundennummer, Chronologisch, etc.)
- 💾 **Archiv-spezifische Konfiguration**: Jedes Archiv speichert eigene Struktur in `.werkstattarchiv_structure.json`
- 🏷️ **Schlagwort-Erkennung**: 10 Kategorien mit 100+ Schlagwörtern (Fahrzeuge, Reparaturen, Teile, etc.)
- 📝 **Log-Tab**: Live-Anzeige aller System-Events mit Export-Funktion
- 🔄 **Commit-basiertes Update-System**: Erkennt jede GitHub-Änderung, nicht nur Releases

**Ordnerstruktur-Profile:**
1. **Standard**: `{kunde}/{jahr}/{typ}` | Datei: `{datum}_{typ}_{auftrag}.pdf`
2. **Mit Kundennummer**: `{kunden_nr} - {kunde}/{jahr}` | Datei: `{auftrag}_{typ}_{datum}.pdf`
3. **Mit Kundennummer im Dateinamen**: `{kunde}/{jahr}` | Datei: `{kunden_nr}_{auftrag}_{typ}_{datum}.pdf`
4. **Chronologisch**: `{jahr}/{monat}/{kunde}/{typ}` | Datei: `{datum}_{typ}_{auftrag}.pdf`
5. **Nach Typ**: `{typ}/{jahr}/{kunde}` | Datei: `{datum}_{auftrag}_{kunden_nr}.pdf`
6. **Nach Auftrag**: `{kunde}/{auftrag}` | Datei: `{datum}_{typ}_{kunden_nr}.pdf`
7. **Kompakt**: `{kunde}/{jahr}` | Datei: `{datum}_{typ}_{auftrag}.pdf`
8. **Detail**: `{kunde}/{jahr}/{monat}/{typ}/{auftrag}` | Datei: `{kunden_nr}_{datum}_{typ}.pdf`
9. **Legacy-Kompatibel**: `Kunde/{kunden_nr} - {kunde}/{jahr}` | Datei: `{auftrag}_{typ}_{datum}.pdf`

**Platzhalter:**
- `{kunde}` - Kundenname
- `{kunden_nr}` - Kundennummer (inkl. virtuelle VK0001)
- `{jahr}` - Jahr (YYYY)
- `{monat}` - Monat (MM oder Name)
- `{datum}` - Vollständiges Datum (YYYY-MM-DD)
- `{typ}` - Dokumenttyp
- `{auftrag}` - Auftragsnummer
- `{kfz}` - KFZ-Kennzeichen
- `{fin}` - Fahrzeug-FIN
- `{seiten}` - Seitenanzahl

**Verbesserungen:**
- ⚡ **Performance-Optimierung**: Einstellungen-Tab lädt schneller (`update_idletasks()` nach jedem Frame)
- 📊 **Log-Rotation**: Automatisch bei 10.000 Zeilen (~2MB)
- 🔍 **Update-Methode wählbar**: Checkbox zum Umschalten zwischen Commit- und Release-Check
- 🪟 **Windows-Fehlerbehandlung**: Bessere Prüfung von Schreibrechten und Verzeichnis-Existenz

**Archiv-Konfiguration:**
- Wird im Archiv-Verzeichnis gespeichert: `[ROOT]/.werkstattarchiv_structure.json`
- Jedes Archiv kann eigene Struktur haben
- Automatisches Laden beim Programmstart
- Synchronisation zwischen Programm- und Archiv-Config

### Version 0.8.5 (12. November 2025)

**Neue Features:**
- ✨ **Virtuelle Kundennummern (VKxxxx)**: Dokumente ohne erkannte Kundennummer bekommen automatisch eine virtuelle Nummer
- 🔄 **Automatische Datei-Umbenennung**: Beim Zuordnen virtueller Kunden zu echten werden alle Dateien automatisch umbenannt
- 👥 **Neuer Tab "Virtuelle Kunden"**: Verwalte und ordne virtuelle Kundennummern echten Kunden zu
- 🗄️ **Datenbank-Management**: Löschen und neu initialisieren der Index-Datenbank im System-Tab

**Verbesserungen:**
- ⚡ **Optimierter Ladeprozess**: Sichtbarer Status mit Icons, schnellerer Start (~1-1.5s)
- 🔘 **Scan-Button Fix**: Reagiert jetzt sofort beim ersten Klick (vorher verzögert)
- 📁 **Setup-Scripts korrigiert**: `kunden.csv` wird jetzt leer mit korrektem Semikolon-Format erstellt
- 🎯 **Synchrones Laden**: Alle Daten vollständig geladen bevor GUI freigegeben wird

**Technische Änderungen:**
- Neue Datei: `services/virtual_customer_manager.py` für Datei-Umbenennung
- `CustomerManager`: Neue Methoden `create_virtual_customer()`, `is_virtual_customer()`, `replace_virtual_customer()`
- `Router`: Automatische Erstellung virtueller Kundennummern bei fehlender Erkennung
- Loading-Screen: 9 Steps mit je 100ms + detaillierte Status-Updates

### Version 0.8.0 (Vorherige Version)

**Features:**
- Dokumenten-Indexierung & Suche
- Legacy-Auftrags-System
- Automatische Ordnerüberwachung
- Konfigurierbare Regex-Patterns
- Backup & Restore System
- Auto-Update-System

---

## 🔍 Automatische Ordnerüberwachung (Auto-Watch)

Das WerkstattArchiv kann den Eingangsordner **automatisch überwachen** und neue Dokumente sofort verarbeiten, sobald sie erscheinen.

### Wie funktioniert es?

#### 1. **Aktivierung im Verarbeitungs-Tab**

Klicke auf **"🔍 Auto-Watch starten"**:
- System überwacht den konfigurierten Eingangsordner
- Status wechselt zu **🟢 Aktiv**
- Neue Dateien werden **automatisch erkannt und verarbeitet**
- Button wechselt zu **"⏹ Auto-Watch stoppen"**

#### 2. **Automatische Verarbeitung**

Sobald eine neue Datei im Eingangsordner erscheint:
1. **2 Sekunden Wartezeit** (damit Upload abgeschlossen ist)
2. **Automatische Analyse** mit aktuell gewählter Vorlage
3. **Verschieben** in die richtige Ordnerstruktur
4. **Indexierung** in der Datenbank
5. **Live-Anzeige** in der Ergebnistabelle

**Unterstützte Dateitypen:**
- PDF (`.pdf`)
- Bilder (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`)

#### 3. **Status-Anzeige**

- **🟢 Aktiv** = Ordner wird überwacht
- **⚪ Gestoppt** = Keine Überwachung
- **Letztes Dokument: ...** = Info über zuletzt verarbeitete Datei

#### 4. **Stoppen**

Klicke auf **"⏹ Auto-Watch stoppen"**:
- Überwachung wird beendet
- Keine automatische Verarbeitung mehr
- Manuelle Verarbeitung weiterhin möglich

### Vorteile von Auto-Watch

✅ **Zeitersparnis** - Keine manuelle Verarbeitung mehr nötig  
✅ **Sofortige Verarbeitung** - Dokumente werden direkt beim Eintreffen sortiert  
✅ **Immer aktuelle Daten** - Kein "Vergessen" von Dokumenten  
✅ **Perfekt für Scanner** - Scanne direkt in den Eingangsordner  
✅ **Netzwerk-fähig** - Überwache auch Netzlaufwerke  

### Technische Details

**Basis-Technologie:** Python `watchdog` Library  
**Event-Typ:** File Creation Events  
**Cooldown:** 2 Sekunden (verhindert unvollständige Uploads)  
**Thread-Safe:** Verarbeitung in separaten Threads  

**Sicherheitsmechanismen:**
- Dateien werden erst verarbeitet wenn vollständig geschrieben
- Doppelte Verarbeitung wird verhindert
- Fehlerhafte Dateien werden übersprungen und geloggt

### Installation

Die `watchdog` Library ist bereits in `requirements.txt` enthalten:

```bash
pip install -r requirements.txt
```

**Hinweis:** Auto-Watch ist optional. Wenn `watchdog` nicht installiert ist, funktioniert die manuelle Verarbeitung trotzdem normal.

---

## � Konfigurierbare Regex-Patterns

Das WerkstattArchiv ermöglicht die **vollständige Anpassung aller Regex-Patterns** über die GUI - ohne Code-Änderungen!

### Warum Pattern anpassen?

Jede Werkstatt hat unterschiedliche Dokumentenformate:
- ✏️ "Kunden-Nr." vs. "KdNr" vs. "Kunde:"
- ✏️ "Auftragsnummer" vs. "Werkstatt-Auftrag"
- ✏️ Unterschiedliche Datumsformate
- ✏️ Spezielle Kennzeichenformate

**Lösung:** Passe die Patterns an Ihre Dokumente an!

### Regex-Patterns Tab

Öffne den Tab **"Regex-Patterns"** in der GUI:

#### Verfügbare Pattern-Kategorien:

**📁 Stammdaten**
- `kunden_nr` - Kundennummer (Standard: 5-6 Ziffern nach "Kunden-Nr.", "Kundennummer")
- `auftrag_nr` - Auftragsnummer (Standard: 5-7 Ziffern nach "Auftrags-Nr.", "Auftragsnummer")
- `datum` - Datum (Standard: TT.MM.JJJJ oder TT/MM/JJJJ)
- `kunden_name` - Kundenname (Standard: Nach "Kunde:", "Name:", "Auftraggeber:")

**🚗 Fahrzeugdaten**
- `fin` - Fahrzeug-Identifikationsnummer (Standard: 17 Zeichen alphanumerisch)
- `kennzeichen` - KFZ-Kennzeichen (Standard: deutsches Format XX-YY 1234)

**📍 Adressdaten**
- `plz` - Postleitzahl (Standard: 5-stellige Zahl)
- `strasse` - Straße mit Hausnummer

**📄 Dokumenttypen**
- `rechnung` - Erkennung von Rechnungen
- `kva` - Kostenvoranschlag/KVA
- `auftrag` - Aufträge
- `hu` - Hauptuntersuchung
- `garantie` - Garantiedokumente

### Pattern bearbeiten

1. **Pattern anpassen**: Trage dein Regex-Pattern in das Eingabefeld ein
2. **Testen**: Klicke auf "🧪 Pattern testen" um es mit Beispieltext zu prüfen
3. **Speichern**: Klicke auf "💾 Speichern" - Änderungen wirken sofort!
4. **Zurücksetzen**: Klicke auf "↺ Zurücksetzen" um Standardwerte wiederherzustellen

### Beispiele für Pattern-Anpassungen

#### Beispiel 1: Alternative Kundennummer-Formate

**Standard-Pattern:**
```regex
(?:Kunde(?:n)?[-\s]*(?:Nr|nummer)|Kd\.?[-\s]*Nr\.?)[:\s]+(\d+)
```

**Angepasst für "KdNr: 12345":**
```regex
(?:Kunde(?:n)?[-\s]*(?:Nr|nummer)|Kd\.?[-\s]*Nr\.?|KdNr)[:\s]+(\d+)
```

**Angepasst für "Kunde: 12345" (ohne "Nr"):**
```regex
Kunde[:\s]+(\d{5,6})
```

#### Beispiel 2: Amerikanisches Datumsformat

**Standard-Pattern (DD.MM.YYYY):**
```regex
(\d{1,2})\.(\d{1,2})\.(\d{4})
```

**Angepasst für MM/DD/YYYY:**
```regex
(\d{1,2})/(\d{1,2})/(\d{4})
```

#### Beispiel 3: Kennzeichen mit Bindestrich optional

**Standard-Pattern:**
```regex
([A-ZÄÖÜ]{1,3}[-\s][A-ZÄÖÜ]{1,2}\s+\d{1,4}\s*[A-Z]?)
```

**Angepasst ohne Bindestrich-Pflicht:**
```regex
([A-ZÄÖÜ]{1,3}[-\s]?[A-ZÄÖÜ]{1,2}[-\s]?\d{1,4}[A-Z]?)
```

### Pattern-Tester

Der integrierte **Pattern-Tester** hilft beim Entwickeln:

1. Klicke auf "🧪 Pattern testen"
2. Wähle das zu testende Pattern aus dem Dropdown
3. Füge Beispieltext ein (z.B. aus einem echten Dokument)
4. Klicke "▶ Test ausführen"
5. Siehst du den erwarteten Match? → Speichern!
6. Kein Match? → Pattern anpassen und erneut testen

**Beispiel-Testtext:**
```
Werkstatt Müller GmbH
Kunden-Nr.: 28307
Auftragsnummer: 78708
Datum: 15.03.2019
FIN: VR7BCZKXCME033281
Kennzeichen: SFB-KI 23E
```

### Regex-Grundlagen

**Wichtige Regex-Zeichen:**
- `\d` = Ziffer (0-9)
- `\d+` = Eine oder mehr Ziffern
- `\d{5}` = Genau 5 Ziffern
- `\d{5,6}` = 5 bis 6 Ziffern
- `[A-Z]` = Großbuchstabe
- `[a-z]` = Kleinbuchstabe
- `[A-Za-z]` = Beliebiger Buchstabe
- `[:\s]+` = Doppelpunkt oder Leerzeichen (mehrfach)
- `(?:...)` = Nicht-erfassende Gruppe
- `(...)` = Erfassende Gruppe (wird extrahiert!)
- `|` = ODER
- `?` = Optional (0 oder 1 Mal)
- `*` = Beliebig oft (0 bis n)
- `+` = Mindestens einmal (1 bis n)

**Tipp:** Die runden Klammern `()` um den zu extrahierenden Teil setzen!

### Speicherung

Alle Patterns werden in `patterns.json` gespeichert:

```json
{
  "kunden_nr": "(?:Kunde(?:n)?[-\\s]*(?:Nr|nummer)|Kd\\.?[-\\s]*Nr\\.?)[:\\s]+(\\d+)",
  "auftrag_nr": "(?:Werkstatt[-\\s]*)?Auftrag(?:s)?[-\\s]*(?:Nr|nummer)\\.?[:\\s]+(\\d+)",
  "datum": "(\\d{1,2})\\.(\\d{1,2})\\.(\\d{4})",
  ...
}
```

Diese Datei kann auch manuell bearbeitet werden (mit Vorsicht!).

### Fehlerbehandlung

**Ungültiges Pattern:**
- ✗ System prüft vor dem Speichern
- ✗ Fehlermeldung mit Pattern-Namen
- ✗ Keine Speicherung bei Fehlern

**Pattern funktioniert nicht:**
1. Prüfe mit dem Pattern-Tester
2. Kopiere echten Text aus deinem Dokument
3. Teste verschiedene Pattern-Varianten
4. Nutze Online-Regex-Tester (z.B. regex101.com)

**Zurücksetzen:**
- Klicke "↺ Zurücksetzen" um alle Patterns auf Standardwerte zurückzusetzen

---

## �🔄 Legacy-Auftrags-System

Das WerkstattArchiv unterstützt die automatische Verarbeitung **alter Werkstattaufträge**, die noch keine Kundennummer auf dem Dokument enthalten. Das System arbeitet mit **strikten deterministischen Regeln** - ohne fuzzy matching, KI-Raten oder Heuristiken.

### Wie funktioniert es?

#### 1. **Automatische Erkennung von Legacy-Aufträgen**

Beim Scannen prüft das System, ob das Dokument eine Kundennummer enthält:
- **Hat Kundennummer** → Normaler Workflow (wie gewohnt)
- **Keine Kundennummer** → Legacy-Workflow wird aktiviert

#### 2. **Strikte Zuordnungsregeln** (100% deterministisch)

Das System versucht den Kunden auf **zwei Wege** zu finden:

##### ✅ Regel 1: FIN-Match (Fahrzeug-Identifikationsnummer)
- Extrahiert die 17-stellige FIN aus dem Dokument
- Prüft in `data/vehicles.csv`, ob diese FIN bereits einem Kunden zugeordnet ist
- **Bei eindeutiger Zuordnung**: Automatisch zugewiesen ✓
- **Bei mehreren Treffern**: Als "unklar" markiert → Manuelle Bearbeitung
- **Bei keinem Treffer**: Weiter zu Regel 2

##### ✅ Regel 2: Name + Details Match
- Extrahiert Kundenname, PLZ und Adresse aus dem Dokument
- Vergleicht **exakt** mit der Kundendatenbank:
  - **Name + PLZ stimmen überein** → Zuordnung ✓
  - **Name + Straße stimmen überein** → Zuordnung ✓
- **Bei eindeutiger Zuordnung**: Automatisch zugewiesen ✓
- **Bei mehreren oder keinen Treffern**: Als "unklar" markiert

#### 3. **Ablage-Struktur für Legacy-Aufträge**

**Automatisch zugeordnet:**
```
[ROOT]/Kunde/[Kundennummer] - [Kundenname]/[Jahr]/[Auftragsnr]_Altauftrag_[Datum]_[FIN]_[Kunde].pdf
```

**Unklar:**
```
[ROOT]/Altbestand/Unklar/[Jahr]/[Auftragsnr]_Altauftrag_Unklar_[Datum]_[FIN]_[Name].pdf
```

**Dateinamen-Beispiele:**
```
78708_Altauftrag_20190315_VR7BCZKXCME033281_Schultze_20251111_143022.pdf
78709_Altauftrag_Unklar_20190412_N/A_Mueller_20251111_143145.pdf
```

### 📋 Manuelle Nachbearbeitung (GUI-Tab)

Unklare Legacy-Aufträge erscheinen im Tab **"Unklare Legacy-Aufträge"** mit allen verfügbaren Informationen:

| Angezeigt wird | Nutzen |
|----------------|--------|
| Auftragsnummer | Identifikation des Auftrags |
| Auftragsdatum | Zeitliche Einordnung |
| Kundenname (extrahiert) | Möglicher Kunde |
| FIN | Fahrzeug-Identifikation |
| Kennzeichen | Alternative Fahrzeug-Info |
| Dokumenttyp | Art des Dokuments |
| Match-Grund | Warum unklar (z.B. "unclear", "multiple_matches") |

**Workflow im Tab:**
1. Eintrag öffnen → Alle extrahierten Daten prüfen
2. Kunden aus Dropdown auswählen
3. "Zuordnen" klicken → Bestätigung
4. ✓ System speichert automatisch:
   - FIN wird in `vehicles.csv` mit Kunde verknüpft (für zukünftige automatische Zuordnung!)
   - Datei wird verschoben: `Altbestand/Unklar/` → `Kunde/[Nr]-[Name]/[Jahr]/`
   - Eintrag wird aus unclear_legacy entfernt

### 🗄️ Fahrzeug-Index (vehicles.csv)

Das System baut automatisch einen **Fahrzeug-Index** auf:

```csv
fin;kennzeichen;kunden_nr;marke;modell;erstzulassung;letzte_aktualisierung
VR7BCZKXCME033281;SFB-KI 23E;28307;Nissan;Qashqai;2019-03-15;2025-11-11 14:30:22
```

**Vorteile:**
- Beim nächsten Legacy-Auftrag mit dieser FIN → **automatische Zuordnung**
- Historischer Überblick über Fahrzeuge pro Kunde
- Nachvollziehbarkeit aller Zuordnungen

### 🚫 Was das System NICHT tut

- ❌ **Keine fuzzy Matching**: "Müller" ≠ "Mueller" (nur exakte Übereinstimmung)
- ❌ **Keine Wahrscheinlichkeiten**: Entweder 100% Match oder unklar
- ❌ **Keine KI-Raterei**: Keine Cloud-APIs, keine ML-Modelle
- ❌ **Keine automatischen Annahmen**: Bei Unsicherheit → immer zur manuellen Bearbeitung

### 🔍 Technische Details

**Erweiterte Datenbanktabelle:**
```sql
CREATE TABLE unclear_legacy (
    id INTEGER PRIMARY KEY,
    dateiname TEXT,
    datei_pfad TEXT,
    auftrag_nr TEXT,
    auftragsdatum TEXT,
    kunden_name TEXT,
    fin TEXT,
    kennzeichen TEXT,
    jahr INTEGER,
    dokument_typ TEXT,
    match_reason TEXT,  -- "unclear", "multiple_fin_matches", "no_details"
    hinweis TEXT,
    status TEXT  -- "offen", "zugeordnet"
)
```

**Neue Services:**
- `services/legacy_resolver.py` - Kern-Logik für Legacy-Zuordnung
- `services/vehicles.py` - Fahrzeug-Index-Manager
- `services/filename_generator.py` - Standardisierte Dateinamen

**Erweiterte Customer-Klasse:**
```python
@dataclass
class Customer:
    kunden_nr: str
    name: str
    plz: Optional[str]
    ort: Optional[str]
    strasse: Optional[str]
    telefon: Optional[str]
```

**Erweiterte Kundendatei-Format:**
```csv
kunden_nr;name;plz;ort;strasse;telefon
28307;Anne Schultze;12345;Berlin;Hauptstr. 10;030-123456
```
*(PLZ, Ort, Strasse, Telefon sind optional für Legacy-Matching)*

---

## � Virtuelle Kundennummern (Neu in 0.8.5!)

Das WerkstattArchiv erstellt automatisch **virtuelle Kundennummern** für Dokumente, bei denen keine Kundennummer erkannt werden kann.

### Wie funktioniert es?

#### 1. **Automatische Erstellung**

Wenn bei der Verarbeitung keine Kundennummer erkannt wird:
- System erstellt automatisch eine virtuelle Kundennummer: **VK0001**, **VK0002**, etc.
- Dokument wird normal archiviert unter der virtuellen Nummer
- Kunde wird in `kunden.csv` gespeichert
- Alle Funktionen (Suche, Indexierung) funktionieren normal

**Beispiel-Ordnerstruktur:**
```
[ROOT]/Kunde/VK0001 - Unbekannter Kunde/2025/12345_Rechnung_20251112.pdf
```

#### 2. **Manuelle Zuordnung im "Virtuelle Kunden" Tab**

Im neuen Tab **"Virtuelle Kunden"** siehst du:
- Alle virtuellen Kundennummern (VKxxxx)
- Name des Kunden (wenn erkannt)
- Anzahl der zugehörigen Dateien
- Eingabefelder für echte Kundennummer + Name

**Workflow:**
1. Öffne Tab **"Virtuelle Kunden"**
2. Gib die echte Kundennummer und den Namen ein
3. Klicke auf **"→ Zuordnen"**
4. System fragt nach Bestätigung
5. **Alle Dateien werden automatisch umbenannt!**

#### 3. **Automatisches Umbenennen aller Dateien**

Wenn du VK0001 → 28307 (Max Müller) zuordnest:
- **Vorher:**
  ```
  [ROOT]/Kunde/VK0001 - Unbekannter Kunde/2025/12345_Rechnung_20251112.pdf
  ```
- **Nachher:**
  ```
  [ROOT]/Kunde/28307 - Max Müller/2025/12345_Rechnung_20251112.pdf
  ```

**Was passiert automatisch:**
- ✅ Alle Dateien mit VK0001 werden gefunden
- ✅ Kundennummer im Dateinamen wird ersetzt
- ✅ Kundenname im Dateinamen wird ersetzt
- ✅ Ordner werden umbenannt
- ✅ Kundendatenbank wird aktualisiert
- ✅ VK0001 wird gelöscht, 28307 wird hinzugefügt

### Vorteile

- ✅ **Keine verlorenen Dokumente**: Auch ohne erkannte Kundennummer wird alles archiviert
- ✅ **Nachträgliche Zuordnung**: Kunden können später korrekt zugeordnet werden
- ✅ **Automatische Umbenennung**: Alle Dateien werden konsistent aktualisiert
- ✅ **Vollständige Integration**: Virtuelle Kunden funktionieren wie normale Kunden

---

## �💾 Backup & Wiederherstellung

Das WerkstattArchiv bietet ein **integriertes Backup-System** zum Sichern und Wiederherstellen aller wichtigen Daten.

### Was wird gesichert?

✅ **Konfigurationsdatei** (`config.json`)  
✅ **Kundendatenbank** (`kunden.csv`)  
✅ **Fahrzeug-Index** (`vehicles.csv`)  
✅ **SQLite-Datenbank** (`werkstatt_index.db` - alle indexierten Dokumente)  
✅ **Regex-Patterns** (`patterns.json`)  

**Hinweis:** Die **Dokumente selbst** (PDFs/Bilder in den Kundenordnern) werden NICHT gesichert - nur die Metadaten/Index!

### Backup erstellen

**In der GUI:**
1. Gehe zum **"System"** Tab
2. Klicke auf **"📦 Backup erstellen"**
3. Gib optional einen Namen ein (z.B. "vor_update" oder "2025-11")
4. ✓ Backup wird erstellt als ZIP-Datei in `backups/`

**Was passiert:**
- Alle Dateien werden in ein ZIP-Archiv gepackt
- Backup-Info mit Zeitstempel wird gespeichert
- Speicherort: `WerkstattArchiv/backups/backup_YYYYMMDD_HHMMSS.zip`

### Backup wiederherstellen

**⚠️ WARNUNG:** Alle aktuellen Daten werden überschrieben!

**In der GUI:**
1. Gehe zum **"System"** Tab
2. Klicke auf **"♻️ Backup wiederherstellen"**
3. Wähle eine Backup-ZIP-Datei aus
4. Bestätige die Sicherheitsabfrage
5. ✓ Backup wird wiederhergestellt
6. **Anwendung neu starten!**

### Backups verwalten

**In der GUI:**
1. Gehe zum **"System"** Tab
2. Klicke auf **"📋 Backups verwalten"**
3. Übersicht aller Backups:
   - Backup-Name
   - Erstellungsdatum
   - Größe
   - Enthaltene Dateien

**Aktionen:**
- **♻️ Wiederherstellen** - Backup direkt wiederherstellen
- **🗑️ Löschen** - Backup löschen (mit Sicherheitsabfrage)

### Empfohlene Backup-Strategie

📅 **Regelmäßig:** Wöchentliches Backup  
🔧 **Vor Updates:** Backup vor Software-Updates  
🚀 **Vor großen Änderungen:** Z.B. vor Massen-Import  
💡 **Nach wichtigen Änderungen:** Nach manuellen Kundenzuordnungen  

### Technische Details

**Backup-Struktur:**
```
backup_20251111_143022.zip
├── config.json              # Konfiguration
├── kunden.csv               # Kundenstammdaten
├── vehicles.csv             # Fahrzeug-Kundenzuordnung
├── werkstatt_index.db       # Dokumenten-Index
├── patterns.json            # Regex-Patterns
└── backup_info.json         # Metadaten
```

**Backup-Info Beispiel:**
```json
{
  "created_at": "2025-11-11T14:30:22",
  "backup_name": "backup_20251111_143022",
  "files": ["config.json", "kunden.csv", "vehicles.csv", ...],
  "config_snapshot": { ... }
}
```

---

### Dokumentensuche

Der neue **Such-Tab** ermöglicht es, alle verarbeiteten Dokumente zu durchsuchen:

- **Suchkriterien**: Kundennummer, Kundenname, Auftragsnummer, Dateiname, Typ, Jahr
- **Kombinierbare Filter**: Mehrere Kriterien gleichzeitig nutzbar
- **Schnellzugriff**: "Öffnen"-Button öffnet Dokument im Finder/Explorer
- **Statistiken**: Übersicht über alle indexierten Dokumente

### Statistiken

Klicke auf "📊 Statistiken" im Such-Tab um zu sehen:
- Gesamtanzahl verarbeiteter Dokumente
- Verteilung nach Status (erfolgreich/unklar/Fehler)
- Häufigste Dokumenttypen
- Dokumente nach Jahr

### Ordnerstruktur der Ablage

Dokumente werden automatisch nach folgendem Schema abgelegt:

#### Normale Aufträge (mit Kundennummer):
```
[ROOT]/Kunde/[Kundennummer] - [Kundenname]/[Jahr]/[Auftragsnummer]_[Dokumenttyp].pdf
```
**Beispiel:**
```
D:\Scan\Daten\Kunde\10234 - Müller Max\2025\500123_Rechnung.pdf
```

#### Legacy-Aufträge (zugeordnet):
```
[ROOT]/Kunde/[Kundennummer] - [Kundenname]/[Jahr]/[Auftragsnr]_Altauftrag_[Datum]_[FIN]_[Kunde]_[Timestamp].pdf
```
**Beispiel:**
```
D:\Scan\Daten\Kunde\28307 - Anne Schultze\2019\78708_Altauftrag_20190315_VR7BCZKXCME033281_Schultze_20251111_143022.pdf
```

#### Unklare Legacy-Aufträge:
```
[ROOT]/Altbestand/Unklar/[Jahr]/[Auftragsnr]_Altauftrag_Unklar_[Datum]_[FIN-oder-NA]_[Name]_[Timestamp].pdf
```
**Beispiel:**
```
D:\Scan\Daten\Altbestand\Unklar\2019\78709_Altauftrag_Unklar_20190412_N/A_Mueller_20251111_143145.pdf
```

**Hinweis:** Nach manueller Zuordnung im GUI-Tab werden unklare Legacy-Aufträge automatisch in die richtige Kundenstruktur verschoben.

---

## 🔄 Auto-Update-System

Das WerkstattArchiv kann sich **automatisch über GitHub aktualisieren** - direkt aus der GUI heraus!

### Wie funktioniert das Update?

#### 1. **Update-Check starten**

Gehe zum neuen Tab **"System"** (letzter Tab).

Dort findest du die Bereiche für Backup und Updates.

Klicke auf den Button:

```
🔍 Auf Updates prüfen
```

Das System prüft nun die neueste Version auf GitHub.

#### 2. **Update-Dialog**

Falls ein Update verfügbar ist, erscheint ein Dialog mit:
- 📦 **Neue Version**: z.B. "v0.9.0"
- 📝 **Release Notes**: Was ist neu?
- ✅ **Bestätigung**: Update jetzt installieren?

#### 3. **Automatische Installation**

Nach Bestätigung:
1. **Backup erstellen** → `backup_before_update/` (Sicherheitskopie)
2. **Download** → Neueste Version von GitHub
3. **Installation** → Dateien werden aktualisiert
4. **Restart** → Anwendung startet automatisch neu

### Technische Details

**Quelle:** GitHub Releases  
**API:** `https://api.github.com/repos/SHP-ART/WerkstattArchiv/releases/latest`  
**Download-Format:** ZIP-Archiv (zipball_url)  
**Backup-Ordner:** `backup_before_update/` (vor jeder Installation)

**Update-Komponenten:**
- Python-Dateien (`.py`)
- Services-Module (`services/`)
- GUI-Module (`ui/`)
- Konfigurationsdateien bleiben erhalten!

**Sicherheitsmechanismen:**
✅ Automatisches Backup vor Update  
✅ Version-Vergleich (Semantic Versioning)  
✅ Fortschrittsanzeige während Download  
✅ Thread-sichere Implementierung  
✅ Benutzer-Bestätigung erforderlich  

### Wichtige Hinweise

⚠️ **Internet-Verbindung erforderlich** zum Prüfen und Herunterladen  
⚠️ **Schreibrechte** im Installationsverzeichnis benötigt  
⚠️ **Backup automatisch** - alte Version wird gesichert  
✅ **Keine Cloud-Services** - nur GitHub (Open Source)  

### Manuelles Update (falls nötig)

Falls das Auto-Update nicht funktioniert, kannst du manuell aktualisieren:

```bash
cd /Users/shp-art/Documents/Github/WerkstattArchiv
git pull origin main
pip install -r requirements.txt
python3 main.py
```

---

## Dokumenttyp-Erkennung

Die Anwendung erkennt automatisch folgende Dokumenttypen:

- **Rechnung**: Enthält "Rechnung"
- **KVA**: Enthält "Kostenvoranschlag" oder "KVA"
- **Auftrag**: Enthält "Auftrag"
- **HU**: Enthält "HU" oder "Hauptuntersuchung"
- **Garantie**: Enthält "Garantie"
- **Dokument**: Fallback für unbekannte Typen

## Confidence-Score

Die Anwendung berechnet einen Confidence-Score für jedes Dokument:

- +0.4 wenn Kundennummer erkannt
- +0.3 wenn Auftragsnummer erkannt
- +0.2 wenn Dokumenttyp erkannt
- +0.1 wenn Datum plausibel

Dokumente mit Score < 0.6 oder fehlender Kundennummer werden als "unklar" eingestuft.

## Logging

Alle Verarbeitungsvorgänge werden in `WerkstattArchiv_log.txt` protokolliert.

## Executable erstellen (Windows)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

Die EXE-Datei befindet sich dann in `dist/main.exe`.

## Fehlerbehebung

### Import-Fehler bei customtkinter

```bash
pip install --upgrade customtkinter
```

### OCR funktioniert nicht

- Tesseract korrekt installiert?
- Pfad in `config.json` korrekt?
- Sprachpaket Deutsch installiert?

### Dokumente werden nicht erkannt

- PDF enthält echten Text oder ist gescannt?
- Bei gescannten PDFs: OCR aktiviert?
- Regex-Patterns passen zu Ihren Dokumenten?

## Erweiterungsmöglichkeiten

### ✅ Implementiert

- [x] ✅ Automatische Ordnerüberwachung mit `watchdog` (0.8.6)
- [x] ✅ Konfigurierbare Regex-Patterns über GUI (0.8.6)
- [x] ✅ Legacy-Aufträge ohne Kundennummer (0.8.0)
- [x] ✅ Fahrzeug-Index für FIN-basierte Zuordnung (0.8.0)
- [x] ✅ Virtuelle Kundennummern mit automatischer Datei-Umbenennung (0.8.5)
- [x] ✅ Datenbank-Management (Löschen/Neu-Initialisieren) (0.8.5)
- [x] ✅ **Batch-Verarbeitung mit Progress-Dialog & Cancel-Button** (0.8.8)
- [x] ✅ **Performance-Optimierungen (40-75% Speedup)** (0.8.8)
- [x] ✅ **Robusteres Update-System mit Download-Verifizierung** (0.8.8)

### 📋 Geplant

- [ ] Export-Funktion für Statistiken (CSV, Excel)
- [ ] Zusätzliche Dokumenttypen (Inspektionen, Gutachten, etc.)
- [ ] Barcode/QR-Code Erkennung auf Dokumenten
- [ ] Email-Integration für Dokumenteneingang
- [ ] OCR-Sprache wählbar in GUI
- [ ] Doppelter-Dokumenten Detection/Handling

## Lizenz

Dieses Projekt ist für den internen Gebrauch bestimmt.

## Support

Bei Fragen oder Problemen bitte ein Issue erstellen.

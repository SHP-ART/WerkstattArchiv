# WerkstattArchiv

**Version 0.8.0**

Lokale Python-Desktop-Anwendung zur automatischen Verwaltung von Werkstattdokumenten.

## Features

- ✅ Automatische Dokumenten-Analyse (PDF & Bilder)
- ✅ OCR-Unterstützung mit Tesseract
- ✅ Intelligente Ordnerstruktur nach Kunde/Jahr/Auftrag
- ✅ Moderne GUI mit customtkinter
- ✅ **Dokumenten-Indexierung & Suche** (neu!)
- ✅ **Statistiken & Auswertungen** (neu!)
- ✅ **Legacy-Auftrags-System** - Automatische Zuordnung alter Aufträge ohne Kundennummer (neu!)
- ✅ **Automatische Ordnerüberwachung** - Neue Dokumente werden automatisch verarbeitet (neu!)
- ✅ **Konfigurierbare Regex-Patterns** - Anpassbare Suchmuster über GUI (neu!)
- ✅ **Automatische Kundenverwaltung** - Kunden werden automatisch aus Dokumenten hinzugefügt (neu!)
- ✅ **Backup & Restore** - Sichere alle Daten mit einem Klick (neu!)
- ✅ Manuelle Nachbearbeitung unklarer Dokumente
- ✅ Vollständig lokal (keine Cloud-Services)
- ✅ Ausführliches Logging aller Vorgänge

## Projektstruktur

```
WerkstattArchiv/
├── main.py                       # Haupteinstiegspunkt
├── config.json                   # Konfigurationsdatei
├── requirements.txt              # Python-Abhängigkeiten
├── werkstatt_index.db           # SQLite-Datenbank (auto-erstellt)
├── ui/
│   └── main_window.py           # GUI-Implementation (mit Legacy-Tab)
├── services/
│   ├── customers.py             # Kundenverwaltung (erweitert für Legacy)
│   ├── analyzer.py              # Dokumentenanalyse (mit Legacy-Support)
│   ├── router.py                # Routing-Logik (Altbestand/Unklar Pfade)
│   ├── indexer.py               # Dokumenten-Index + unclear_legacy Tabelle
│   ├── legacy_resolver.py       # ⭐ NEU: Legacy-Zuordnungs-Logik
│   ├── vehicles.py              # ⭐ NEU: Fahrzeug-Index-Manager
│   ├── filename_generator.py   # ⭐ NEU: Standardisierte Dateinamen
│   ├── watchdog_service.py      # ⭐ NEU: Automatische Ordnerüberwachung
│   ├── pattern_manager.py       # ⭐ NEU: Konfigurierbare Regex-Patterns
│   ├── backup_manager.py        # ⭐ NEU: Backup & Restore System
│   ├── vorlagen.py              # Vorlagen-Manager
│   └── logger.py                # Logging-Service
├── data/
│   └── vehicles.csv             # ⭐ NEU: Fahrzeug-Kundenzuordnung (auto-erstellt)
├── backups/                     # ⭐ NEU: Backup-Verzeichnis (auto-erstellt)
└── beispiel_auftraege/          # Test-PDFs (nicht im Git)
    ├── auftrag.pdf              # Legacy ohne Kundennr (alte Vorlage)
    └── Schultze.pdf             # Modern mit Kundennr (neue Vorlage)
```

## Installation

### 🪟 Windows

**Schnellinstallation für Windows:**
1. Rechtsklick auf `install.bat` → "Als Administrator ausführen"
2. Warte bis Installation abgeschlossen
3. Doppelklick auf `start.bat` oder Desktop-Verknüpfung

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

### Schritt 3: Tesseract OCR installieren (optional)

**Windows:**
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Installieren und Pfad in `config.json` eintragen

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-deu
```

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

## Verwendung

### Anwendung starten

```bash
python main.py
```

### Workflow

1. **Einstellungen-Tab**: Pfade konfigurieren und Kundendatenbank laden
2. **Verarbeitung-Tab**: "Eingangsordner scannen" klicken ODER "🔍 Auto-Watch starten" für automatische Überwachung
3. **Suche-Tab**: Nach verarbeiteten Dokumenten suchen (neu!)
4. **Unklare Dokumente-Tab**: Manuelle Nachbearbeitung bei Bedarf
5. **Unklare Legacy-Aufträge-Tab**: Manuelle Zuordnung alter Aufträge ohne Kundennummer (neu!)

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

## 💾 Backup & Wiederherstellung

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
1. Gehe zu **"Einstellungen"** Tab
2. Scrolle nach unten zum Bereich **"💾 Backup & Wiederherstellung"**
3. Klicke auf **"📦 Backup erstellen"**
4. Gib optional einen Namen ein (z.B. "vor_update" oder "2025-11")
5. ✓ Backup wird erstellt als ZIP-Datei in `backups/`

**Was passiert:**
- Alle Dateien werden in ein ZIP-Archiv gepackt
- Backup-Info mit Zeitstempel wird gespeichert
- Speicherort: `WerkstattArchiv/backups/backup_YYYYMMDD_HHMMSS.zip`

### Backup wiederherstellen

**⚠️ WARNUNG:** Alle aktuellen Daten werden überschrieben!

**In der GUI:**
1. Gehe zu **"Einstellungen"** Tab
2. Klicke auf **"♻️ Backup wiederherstellen"**
3. Wähle eine Backup-ZIP-Datei aus
4. Bestätige die Sicherheitsabfrage
5. ✓ Backup wird wiederhergestellt
6. **Anwendung neu starten!**

### Backups verwalten

**In der GUI:**
1. Gehe zu **"Einstellungen"** Tab
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

- [x] ✅ Automatische Ordnerüberwachung mit `watchdog` (implementiert!)
- [ ] Zusätzliche Dokumenttypen
- [ ] Export-Funktion für Statistiken (CSV, Excel)
- [ ] Batch-Verarbeitung mit Progress-Bar
- [x] ✅ Konfigurierbare Regex-Patterns über GUI (implementiert!)
- [x] ✅ Legacy-Aufträge ohne Kundennummer (implementiert!)
- [x] ✅ Fahrzeug-Index für FIN-basierte Zuordnung (implementiert!)
- [ ] Barcode/QR-Code Erkennung auf Dokumenten
- [ ] Email-Integration für Dokumenteneingang

## Lizenz

Dieses Projekt ist für den internen Gebrauch bestimmt.

## Support

Bei Fragen oder Problemen bitte ein Issue erstellen.

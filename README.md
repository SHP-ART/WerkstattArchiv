# WerkstattArchiv

Lokale Python-Desktop-Anwendung zur automatischen Verwaltung von Werkstattdokumenten.

## Features

- ✅ Automatische Dokumenten-Analyse (PDF & Bilder)
- ✅ OCR-Unterstützung mit Tesseract
- ✅ Intelligente Ordnerstruktur nach Kunde/Jahr/Auftrag
- ✅ Moderne GUI mit customtkinter
- ✅ **Dokumenten-Indexierung & Suche** (neu!)
- ✅ **Statistiken & Auswertungen** (neu!)
- ✅ **Legacy-Auftrags-System** - Automatische Zuordnung alter Aufträge ohne Kundennummer (neu!)
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
│   ├── vorlagen.py              # Vorlagen-Manager
│   └── logger.py                # Logging-Service
├── data/
│   └── vehicles.csv             # ⭐ NEU: Fahrzeug-Kundenzuordnung (auto-erstellt)
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

### Schritt 5: Kundendatei erstellen

Erstelle eine CSV-Datei mit dem erweiterten Format (für Legacy-Support):

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
2. **Verarbeitung-Tab**: "Eingangsordner scannen" klicken
3. **Suche-Tab**: Nach verarbeiteten Dokumenten suchen (neu!)
4. **Unklare Dokumente-Tab**: Manuelle Nachbearbeitung bei Bedarf
5. **Unklare Legacy-Aufträge-Tab**: Manuelle Zuordnung alter Aufträge ohne Kundennummer (neu!)

---

## 🔄 Legacy-Auftrags-System

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

- [ ] Automatische Ordnerüberwachung mit `watchdog`
- [ ] Zusätzliche Dokumenttypen
- [ ] Export-Funktion für Statistiken (CSV, Excel)
- [ ] Batch-Verarbeitung mit Progress-Bar
- [ ] Konfigurierbare Regex-Patterns über GUI
- [x] ✅ Legacy-Aufträge ohne Kundennummer (implementiert!)
- [x] ✅ Fahrzeug-Index für FIN-basierte Zuordnung (implementiert!)
- [ ] Barcode/QR-Code Erkennung auf Dokumenten
- [ ] Email-Integration für Dokumenteneingang

## Lizenz

Dieses Projekt ist für den internen Gebrauch bestimmt.

## Support

Bei Fragen oder Problemen bitte ein Issue erstellen.

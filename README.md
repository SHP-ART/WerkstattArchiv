# WerkstattArchiv

Lokale Python-Desktop-Anwendung zur automatischen Verwaltung von Werkstattdokumenten.

## Features

- ✅ Automatische Dokumenten-Analyse (PDF & Bilder)
- ✅ OCR-Unterstützung mit Tesseract
- ✅ Intelligente Ordnerstruktur nach Kunde/Jahr/Auftrag
- ✅ Moderne GUI mit customtkinter
- ✅ **Dokumenten-Indexierung & Suche** (neu!)
- ✅ **Statistiken & Auswertungen** (neu!)
- ✅ Manuelle Nachbearbeitung unklarer Dokumente
- ✅ Vollständig lokal (keine Cloud-Services)
- ✅ Ausführliches Logging aller Vorgänge

## Projektstruktur

```
WerkstattArchiv/
├── main.py                    # Haupteinstiegspunkt
├── config.json                # Konfigurationsdatei
├── requirements.txt           # Python-Abhängigkeiten
├── werkstatt_index.db        # SQLite-Datenbank (wird automatisch erstellt)
├── ui/
│   └── main_window.py        # GUI-Implementation
└── services/
    ├── customers.py          # Kundenverwaltung
    ├── analyzer.py           # Dokumentenanalyse
    ├── router.py             # Routing-Logik
    ├── indexer.py            # Dokumenten-Index
    └── logger.py             # Logging-Service
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

Erstelle eine CSV-Datei mit dem Format:

```csv
10234;Müller Max
10235;Schmidt GmbH
10236;Wagner KFZ
```

Format: `Kundennummer;Kundenname` (Semikolon-getrennt)

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

```
[ROOT]/Kunde/[Kundennummer] - [Kundenname]/[Jahr]/[Auftragsnummer]_[Dokumenttyp].pdf
```

**Beispiel:**
```
D:\Scan\Daten\Kunde\10234 - Müller Max\2025\500123_Rechnung.pdf
```

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
- [ ] Export-Funktion für Statistiken
- [ ] Batch-Verarbeitung mit Progress-Bar
- [ ] Konfigurierbare Regex-Patterns über GUI

## Lizenz

Dieses Projekt ist für den internen Gebrauch bestimmt.

## Support

Bei Fragen oder Problemen bitte ein Issue erstellen.

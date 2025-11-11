
# Projekt-Prompt: WerkstattArchiv (Python, lokal, GUI)

**Rolle:**
Du agierst als erfahrener Python-Entwickler und Architekt.
Erzeuge und ergänze Code so, dass eine saubere, wartbare, lokale Anwendung entsteht.
Keine Cloud-Services, kein Tracking, nur lokale Verarbeitung.

---

## Ziel der Anwendung

Erstelle eine **lokale Python-Desktop-Anwendung** mit grafischer Oberfläche, die Werkstattdokumente automatisch aus einem Eingangsordner einliest, analysiert, sinnvoll umbenennt und in eine feste Ordnerstruktur verschiebt.

Die Anwendung soll auf **Windows-Rechnern der Werkstatt laufen**, aber unter **macOS entwickelt werden können**.
Alle Komponenten müssen lokal lauffähig sein.

---

## Ordnerstruktur (Ablagekonzept)

Zielstruktur für automatisch erkannte Dokumente:

```text
[ROOT]/Kunde/[Kundennummer] - [Kundenname]/[Jahr]/[Auftragsnummer]_[Dokumenttyp].pdf
```

**Beispiele:**

* `D:\Scan\Daten\Kunde\10234 - Müller Max\2025\500123_Rechnung.pdf`
* `D:\Scan\Daten\Kunde\10234 - Müller Max\2025\500123_Auftrag.pdf`
* `D:\Scan\Daten\Kunde\10234 - Müller Max\2025\500456_KVA.pdf`

**Regeln:**

* `Kundennummer` ist der zentrale Schlüssel.
* `Kundenname` wird aus einer Kundendatei (CSV) zur Nummer ermittelt.
* `Jahr` kommt aus dem erkanntem Datum im Dokument.
* `Auftragsnummer` und `Dokumenttyp` steuern den Dateinamen.
* Wenn keine eindeutige Zuordnung möglich → Ablage im `Unklar`-Ordner.

---

## Funktionale Anforderungen

1. **Konfiguration (config.json)**

Die Anwendung lädt/speichert folgende Einstellungen:

```json
{
  "root_dir": "D:/Scan/Daten",
  "input_dir": "D:/Scan/Eingang",
  "unclear_dir": "D:/Scan/Unklar",
  "customers_file": "D:/Scan/config/kunden.csv",
  "tesseract_path": null
}
```

* Alle Pfade müssen über die GUI editierbar und persistent sein.

2. **Kunden-Mapping**

Datei: `customers_file` (CSV mit `kunden_nr;kunden_name`)

* Lade dieses Mapping beim Start.
* Biete eine Klasse/Funktion, um aus `kunden_nr` den `kunden_name` zu holen.
* Kein Raten von Namen, nur Zuordnung über Nummer.

3. **Dokument-Analyse**

Für jede Datei im `input_dir`:

* Wenn PDF:

  * Versuche Text mit `PyMuPDF` (`fitz`) zu extrahieren.
  * Falls kein Text → optionaler Fallback OCR (später erweiterbar).
* Wenn Bilddatei:

  * OCR mit `pytesseract` (lokal, ohne Online-Dienste).

Aus dem Text werden per Regex extrahiert:

* `Kundennummer`: `Kunde[-\s]*Nr[:\s]+(\d+)`
* `Auftragsnummer`: `Auftrag[-\s]*Nr[:\s]+(\d+)`
* `Datum`: erstes Datum im Format `TT.MM.JJJJ` → daraus `Jahr`
* `Dokumenttyp` anhand von Schlüsselwörtern:

  * enthält `Rechnung` → `"Rechnung"`
  * enthält `Kostenvoranschlag` oder `KVA` → `"KVA"`
  * enthält `Auftrag` → `"Auftrag"`
  * enthält `HU`, `Hauptuntersuchung` → `"HU"`
  * enthält `Garantie` → `"Garantie"`
  * sonst → `"Dokument"`

Ergebnis der Analyse als Python-Datenstruktur:

```python
{
    "kunden_nr": str | None,
    "kunden_name": str | None,
    "auftrag_nr": str | None,
    "dokument_typ": str,
    "jahr": int,
    "confidence": float,
    "hinweis": str | None
}
```

**Confidence-Heuristik (einfach, erweiterbar):**

* +0.4 wenn Kundennummer erkannt
* +0.3 wenn Auftragsnummer erkannt
* +0.2 wenn Dokumenttyp ≠ "Dokument"
* +0.1 wenn Jahr plausibel
* max 1.0

Dokument gilt als **unklar**, wenn:

* keine Kundennummer erkannt **oder**
* `confidence < 0.6`

4. **Routing & Dateiverschiebung**

Auf Basis der Analyse:

* Wenn klar:

  * Baue Zielpfad nach Schema:

    * `[root_dir]/Kunde/[Kundennummer] - [Kundenname]/[Jahr]/[Auftragsnummer]_[Dokumenttyp].ext`
  * Lege fehlende Ordner automatisch an.
  * Verschiebe Datei vom `input_dir` in Zielordner.
* Wenn unklar:

  * Verschiebe Datei nach `unclear_dir`.
  * Merke Datensatz für Anzeige in der GUI.

Bei Namenskonflikt: neuen Dateinamen mit Zeitstempel ergänzen.

5. **Logging**

* Schreibe ein Logfile `WerkstattArchiv_log.txt`:

  * Zeitstempel
  * Originalpfad
  * Zielpfad
  * erkannte Metadaten
  * Confidence
  * Fehler (falls vorhanden)

Alles lokal.

---

## Technische Anforderungen

* Sprache: **Python 3.11+**
* GUI: **customtkinter**
* Libraries:

  * `customtkinter`
  * `PyMuPDF` (`fitz`)
  * `pytesseract`
  * `pdf2image`
  * `watchdog`
* Keine Cloud-APIs, kein Netzwerkzugriff.
* Code strukturiert, modular, erweiterbar.

---

## Projektstruktur (gewünscht)

```text
WerkstattArchiv/
├── main.py
├── config.json
├── ui/
│   └── main_window.py
└── services/
    ├── customers.py
    ├── analyzer.py
    ├── router.py
    └── logger.py
```

**Verantwortlichkeiten:**

* `services/customers.py`

  * Laden der Kunden-CSV
  * Funktion `get_customer_name(kunden_nr)`

* `services/analyzer.py`

  * Funktionen:

    * `extract_text(path)`
    * `analyze_document(path) -> dict` (Metadaten + Confidence)

* `services/router.py`

  * Funktionen:

    * `build_target_path(analysis_result) -> str`
    * `move_file(source, target)`

* `services/logger.py`

  * Funktion:

    * `log(event_dict)` → Anhängen an `WerkstattArchiv_log.txt`

* `ui/main_window.py`

  * customtkinter-GUI mit:

    * Tab **Einstellungen** (Pfade bearbeiten, speichern)
    * Tab **Verarbeitung**

      * Button „Eingangsordner scannen“
      * Tabelle: Datei, Kunde, Auftrag, Typ, Confidence, Zielpfad
    * Tab **Unklare Dokumente**

      * Liste unklarer Ergebnisse
      * Möglichkeit zum manuellen Setzen von Kundennummer, Auftragsnummer, Dokumenttyp
      * Button „Neu einsortieren“ → ruft Routing neu auf

* `main.py`

  * lädt `config.json`
  * initialisiert Services
  * startet GUI (`main_window`)

---

## Stil & Qualität

* Klare Funktionsnamen
* Typannotationen verwenden
* Kein „Spaghetti“ im `main.py`
* Keine harten Pfade im Code; alles über Config
* Code so schreiben, dass er mit

  ```bash
  pyinstaller --onefile main.py
  ```

  paketiert werden kann (→ `WerkstattArchiv.exe`)

---

**Deine Aufgabe als Assistent:**

1. Erzeuge den vollständigen Code für dieses Projektgerüst.
2. Fülle alle Module mit sinnvoller, lauf- und erweiterbarer Basislogik.
3. Nutze Platzhalter dort, wo externe Tools (Tesseract, Poppler) eingebunden werden, aber strukturiere den Code so, dass nur noch Pfade ergänzt werden müssen.
4. Erzeuge keine Cloud-Abhängigkeiten.
5. Antworte immer mit kompletten, direkt nutzbaren Codeblöcken pro Datei.

---

Ende der Spezifikation.

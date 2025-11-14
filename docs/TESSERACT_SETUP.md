# 🔍 Tesseract OCR Setup-Guide

## Was ist Tesseract?

Tesseract OCR ist eine **Open-Source-Software zur Texterkennung** in Bildern und gescannten Dokumenten.

## Wann brauche ich Tesseract?

### ✅ Tesseract WIRD benötigt für:
- 📄 Gescannte PDFs (ohne eingebetteten Text)
- 📸 Fotos von Dokumenten
- 🖼️ Bilder (JPG, PNG, TIFF, BMP)
- 📠 Fax-Dokumente als Bild

### ❌ Tesseract NICHT benötigt für:
- 📝 Normale digitale PDFs (mit eingebettetem Text)
- 💾 PDF-Exporte aus Word, Excel, etc.
- 🖨️ Direkt als PDF gespeicherte Dokumente

**Faustregel**: Wenn du Text im PDF markieren/kopieren kannst → Tesseract nicht nötig!

---

## Windows Installation

### Schritt 1: Download

👉 **Download-Link**: https://github.com/UB-Mannheim/tesseract/wiki

Wähle die neueste Version (empfohlen):
- `tesseract-ocr-w64-setup-5.3.x.exe` (64-bit Windows)
- `tesseract-ocr-w32-setup-5.3.x.exe` (32-bit Windows - selten)

### Schritt 2: Installation

1. **Installer starten** (Rechtsklick → "Als Administrator ausführen")

2. **Wichtige Optionen**:
   ```
   [x] Additional language data (download)
       ├── [x] German (deu)           ← Für deutsche Dokumente
       ├── [ ] English (eng)          ← Bereits vorinstalliert
       └── [ ] ... andere Sprachen
   ```

3. **Installations-Pfad**:
   - Standard: `C:\Program Files\Tesseract-OCR`
   - **Merke dir diesen Pfad!** (wird später benötigt)

4. **Installation abschließen**

### Schritt 3: WerkstattArchiv konfigurieren

1. **WerkstattArchiv starten**

2. **Tab "Einstellungen" öffnen**

3. **Tesseract-Pfad eintragen**:
   ```
   C:\Program Files\Tesseract-OCR\tesseract.exe
   ```
   
   📝 **Hinweis**: Der Pfad muss die Datei `tesseract.exe` enthalten!

4. **"Alle Einstellungen speichern"** klicken

### Schritt 4: Test

1. **Gescanntes Test-PDF** in Eingangsordner legen

2. **"Eingangsordner scannen"** klicken

3. **Ergebnis prüfen**:
   - ✅ Text erkannt → Tesseract funktioniert!
   - ❌ "Tesseract nicht gefunden" → Pfad prüfen (siehe unten)

---

## macOS Installation

### Via Homebrew (empfohlen):

```bash
# Tesseract installieren
brew install tesseract

# Deutsche Sprachdaten installieren
brew install tesseract-lang
```

### Pfad in WerkstattArchiv:
```
/opt/homebrew/bin/tesseract
```
(oder `/usr/local/bin/tesseract` bei älteren Macs)

---

## Linux Installation

### Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-deu
```

### Pfad in WerkstattArchiv:
```
/usr/bin/tesseract
```

---

## Problemlösung

### ❌ "Tesseract nicht gefunden"

**Mögliche Ursachen:**

1. **Tesseract nicht installiert**
   - Lösung: Installation durchführen (siehe oben)

2. **Falscher Pfad in Einstellungen**
   - Prüfen: Existiert die Datei `C:\Program Files\Tesseract-OCR\tesseract.exe`?
   - Lösung: Korrekten Pfad eintragen

3. **Tesseract in anderem Ordner installiert**
   - Suche nach `tesseract.exe` auf deinem PC
   - Vollständigen Pfad in Einstellungen eintragen

4. **Fehlende Berechtigungen**
   - WerkstattArchiv als Administrator starten
   - Oder: Tesseract in Benutzerordner installieren

### ❌ "Keine deutsche Texterkennung"

**Problem**: Text wird nicht korrekt erkannt

**Lösung**:
1. Prüfe ob deutsche Sprachdaten installiert sind
2. Windows: Tesseract neu installieren mit "German" Option
3. macOS: `brew install tesseract-lang`
4. Linux: `sudo apt-get install tesseract-ocr-deu`

### ❌ "Fehlerhafte Texterkennung"

**Problem**: Buchstaben werden falsch erkannt

**Tipps für bessere Ergebnisse**:
- 📄 Höhere Scan-Auflösung (min. 300 DPI)
- 🔲 Dokument gerade einscannen (nicht schräg)
- ☀️ Gute Beleuchtung bei Fotos
- 🎨 Kontrast erhöhen (schwarz auf weiß)
- 📏 Mindestgröße: 12pt Schrift

---

## Tesseract-Pfad finden

### Windows:

1. **Über Datei-Explorer**:
   - Suche nach `tesseract.exe`
   - Rechtsklick → "Pfad kopieren"

2. **Über PowerShell**:
   ```powershell
   Get-Command tesseract
   ```

### macOS/Linux:

```bash
which tesseract
```

---

## Performance-Tipps

### Große PDF-Dateien

- OCR kann bei vielen Seiten langsam sein
- **Empfehlung**: Mehrseitige PDFs vorher trennen
- **Tool**: PDF-Split-Software verwenden

### Batch-Verarbeitung

- Mehrere Dokumente gleichzeitig scannen
- WerkstattArchiv verarbeitet automatisch alle Dateien
- Bei vielen gescannten PDFs: Geduld haben!

---

## Alternative ohne Tesseract

### PDF vorab mit OCR versehen:

**Windows**: Adobe Acrobat Pro
- Werkzeuge → Text erkennen → In dieser Datei
- Speichern → PDF hat jetzt eingebetteten Text
- Kann ohne Tesseract verarbeitet werden

**Kostenlose Tools**:
- OCRmyPDF (Command-Line)
- NAPS2 (Scanner-Software mit OCR)
- PDF24 Creator (mit OCR-Funktion)

---

## Häufige Fragen

### Muss ich Tesseract installieren?

**Nein**, wenn du nur **digitale PDFs** verarbeitest (z.B. aus Buchhaltungssoftware).

**Ja**, wenn du **gescannte Dokumente** oder **Fotos** verarbeiten willst.

### Kostet Tesseract etwas?

**Nein**, Tesseract ist 100% kostenlos und Open-Source (Apache License 2.0).

### Welche Sprachen werden unterstützt?

Über 100 Sprachen, u.a.:
- Deutsch (deu)
- Englisch (eng)
- Französisch (fra)
- Spanisch (spa)
- Italienisch (ita)
- und viele mehr...

### Kann ich ohne Tesseract arbeiten?

**Ja**! WerkstattArchiv funktioniert vollständig ohne Tesseract für:
- Digitale PDFs mit eingebettetem Text
- PDF-Exporte aus Programmen
- Dokumente mit kopierbarem Text

**Nur** gescannte Dokumente benötigen Tesseract.

---

## Support

Bei Problemen mit Tesseract:

1. **Logs prüfen**: Tab "Logs" in WerkstattArchiv
2. **Tesseract-Version prüfen**:
   ```
   tesseract --version
   ```
3. **GitHub Issue** mit:
   - Tesseract-Version
   - Betriebssystem
   - Fehlermeldung
   - Test-Dokument (falls möglich)

---

**Viel Erfolg mit der Texterkennung!** 🔍✨

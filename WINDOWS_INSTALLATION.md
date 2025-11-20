# WerkstattArchiv - Windows Installation

## 🚀 Schnellstart (Empfohlen)

### Schritt 1: Python installieren

1. Lade Python 3.11 oder neuer herunter:
   👉 https://www.python.org/downloads/

2. **WICHTIG**: Bei der Installation anhaken:
   - ✅ "Add Python to PATH"
   - ✅ "Install pip"

3. Installation abschließen

### Schritt 2: WerkstattArchiv installieren

1. **Rechtsklick** auf `install.bat`
2. Wähle: **"Als Administrator ausführen"**
3. Warte bis Installation abgeschlossen ist

Das war's! Die Installation dauert 2-5 Minuten.

---

## 📁 Ordnerstruktur einrichten

Nach der Installation:

1. **Doppelklick** auf `setup_folders.bat`
2. Erstellt automatisch:
   - `C:\WerkstattArchiv\Eingang` (Hier Dokumente ablegen)
   - `C:\WerkstattArchiv\Daten` (Sortierte Dokumente)
   - `C:\WerkstattArchiv\Unklar` (Unklare Dokumente)
   - `C:\WerkstattArchiv\config\kunden.csv` (Kundendatenbank)

---

## ✏️ Kundendatenbank anpassen

1. Öffne: `C:\WerkstattArchiv\config\kunden.csv`
2. Bearbeite mit Notepad oder Excel
3. Format: `Kundennummer;Kundenname`

Beispiel:
```
10234;Müller Max
10235;Schmidt GmbH
10236;Wagner KFZ-Werkstatt
```

**Wichtig**: Trennzeichen ist Semikolon (`;`)

---

## 🎯 Anwendung starten

### Variante A: Desktop-Verknüpfung (Einfach)
- **Doppelklick** auf Desktop-Icon "WerkstattArchiv"

### Variante B: Batch-Datei
- **Doppelklick** auf `start.bat`

---

## 🔍 OCR für gescannte PDFs

✅ **NEU: EasyOCR wird automatisch installiert!**

Die `install.bat` installiert jetzt automatisch **EasyOCR** - eine moderne Python-basierte OCR-Engine.

**Vorteile von EasyOCR:**
- ✅ Keine externe Installation nötig (reine Python-Lösung)
- ✅ Funktioniert auf allen Windows-Versionen ohne Probleme
- ✅ Keine Pfad-Konfiguration erforderlich
- ✅ Oft bessere Texterkennung als Tesseract
- ✅ Wird bei `install.bat` automatisch mit installiert

**Was funktioniert mit OCR:**
- ✅ Gescannte PDFs (ohne eingebetteten Text)
- ✅ Bilder (JPG, PNG, TIFF)
- ✅ Fotos von Dokumenten
- ℹ️ Normale digitale PDFs funktionieren auch ohne OCR

**Falls EasyOCR nicht installiert wurde:**

Nachträglich installieren mit:
1. **Doppelklick** auf `install_easyocr.bat`
2. Warte 5-10 Minuten (ca. 200 MB Download)
3. Fertig!

**Alternative: Tesseract (falls EasyOCR nicht funktioniert)**

<details>
<summary>Tesseract Installation (nur wenn EasyOCR Probleme macht)</summary>

### 🚀 Automatische Installation:

1. **Rechtsklick** auf `install_tesseract.bat`
2. Wähle: **"Als Administrator ausführen"**
3. Warte bis Installation abgeschlossen ist

### 📝 Manuelle Installation:

1. **Download Tesseract OCR**:
   👉 https://github.com/UB-Mannheim/tesseract/wiki
   
   Empfohlen: `tesseract-ocr-w64-setup-5.3.x.exe` (64-bit)

2. **Installation**:
   - Installer starten
   - ✅ **"Additional language data (download)"** anhaken
   - ✅ **"German"** auswählen (für deutsche Dokumente)
   - Standard-Pfad: `C:\Program Files\Tesseract-OCR`

</details>

3. **In WerkstattArchiv konfigurieren**:
   - WerkstattArchiv starten
   - Tab "Einstellungen" öffnen
   - Tesseract-Pfad eintragen: `C:\Program Files\Tesseract-OCR\tesseract.exe`
   - "Alle Einstellungen speichern" klicken

**Testen ob Tesseract funktioniert:**
- Gescanntes PDF in Eingangsordner legen
- "Eingangsordner scannen" klicken
- Wenn Text erkannt wird: ✅ Tesseract funktioniert
- Wenn "Tesseract nicht gefunden": ❌ Pfad prüfen

---

## 💾 EXE-Datei erstellen (Portable Version)

Für Installation auf PCs ohne Python:

1. **Doppelklick** auf `build_exe.bat`
2. Warte bis Build abgeschlossen (5-10 Minuten)
3. Fertige EXE: `dist\WerkstattArchiv\WerkstattArchiv.exe`

Die EXE kann auf andere Windows-PCs kopiert werden!

---

## 📋 Erste Schritte nach Installation

1. **Kundendatenbank** einrichten (siehe oben)

2. **Konfiguration prüfen**:
   - Starte WerkstattArchiv
   - Tab "Einstellungen" öffnen
   - Pfade überprüfen/anpassen
   - "Kundendatenbank neu laden" klicken

3. **Dokumente verarbeiten**:
   - Lege PDFs in `C:\WerkstattArchiv\Eingang`
   - Tab "Verarbeitung" öffnen
   - Wähle Auftragsvorlage (Standard/Alternativ)
   - "Eingangsordner scannen"

4. **Ergebnisse prüfen**:
   - Sortierte Dokumente in `C:\WerkstattArchiv\Daten`
   - Unklare Dokumente in `C:\WerkstattArchiv\Unklar`
   - Tab "Suche" für Dokumentensuche

---

## ❓ Problemlösung

### "Python nicht gefunden"
- Python ist nicht installiert oder nicht im PATH
- Python erneut installieren mit "Add to PATH"

### "Keine Module gefunden"
- `install.bat` als Administrator ausführen
- Oder manuell: `pip install -r requirements.txt`

### "Virtuelle Umgebung nicht gefunden"
- `install.bat` ausführen
- Erstellt automatisch `venv` Ordner

### "Dokumente werden nicht erkannt"
- Richtige Auftragsvorlage wählen (Standard/Alternativ)
- Kundennummer im Dokument vorhanden?
- Bei gescannten PDFs: Tesseract installiert? (siehe oben)

### "Tesseract nicht gefunden" Warnung
- Tesseract OCR ist nicht installiert (siehe OCR-Sektion oben)
- Oder: Falscher Pfad in Einstellungen eingetragen
- Prüfen: Existiert die Datei `C:\Program Files\Tesseract-OCR\tesseract.exe`?
- **Hinweis**: Normale digitale PDFs funktionieren OHNE Tesseract!

### "Anwendung startet nicht"
- Als Administrator ausführen
- Firewall/Antivirus prüfen
- Log-Datei prüfen: `WerkstattArchiv_log.txt`

---

## 🗑️ Deinstallation

**Doppelklick** auf `uninstall.bat`

Löscht:
- Virtuelle Umgebung (venv)
- Desktop-Verknüpfung
- Build-Dateien

Bleibt erhalten:
- Ihre Daten in `C:\WerkstattArchiv\`
- config.json
- Datenbank (werkstatt_index.db)

---

## 📞 Support

Bei Problemen:
1. Log-Datei prüfen: `WerkstattArchiv_log.txt`
2. Fehlermeldung notieren
3. GitHub Issue erstellen

---

## 🔄 Updates

Neue Version installieren:
1. Alte Version deinstallieren (`uninstall.bat`)
2. Neue Dateien kopieren
3. `install.bat` ausführen

**Wichtig**: config.json und Datenbank bleiben erhalten!

---

## 📁 Dateien Übersicht

- `install.bat` - Hauptinstallation (als Admin)
- `install_tesseract.bat` - Tesseract OCR installieren (als Admin)
- `start.bat` - Anwendung starten
- `setup_folders.bat` - Ordnerstruktur erstellen
- `build_exe.bat` - EXE-Datei erstellen
- `uninstall.bat` - Deinstallation
- `config.json` - Konfiguration
- `requirements.txt` - Python-Pakete
- `README.md` - Allgemeine Dokumentation

---

**Viel Erfolg mit WerkstattArchiv!** 🎉

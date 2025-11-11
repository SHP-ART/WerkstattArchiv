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

## 🔍 OCR für gescannte PDFs (Optional)

Für die Texterkennung in gescannten PDFs/Bildern:

1. Lade Tesseract OCR herunter:
   👉 https://github.com/UB-Mannheim/tesseract/wiki

2. Installiere mit deutscher Sprachunterstützung

3. In WerkstattArchiv:
   - Tab "Einstellungen" öffnen
   - "Tesseract-Pfad" eintragen (z.B. `C:\Program Files\Tesseract-OCR\tesseract.exe`)
   - "Einstellungen speichern"

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
- Tesseract für gescannte PDFs installiert?

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
- `start.bat` - Anwendung starten
- `setup_folders.bat` - Ordnerstruktur erstellen
- `build_exe.bat` - EXE-Datei erstellen
- `uninstall.bat` - Deinstallation
- `config.json` - Konfiguration
- `requirements.txt` - Python-Pakete
- `README.md` - Allgemeine Dokumentation

---

**Viel Erfolg mit WerkstattArchiv!** 🎉

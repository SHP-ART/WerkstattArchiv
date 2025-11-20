# 🚀 WerkstattArchiv - Windows Quick Start

## Installation in 3 Schritten (ca. 10 Minuten)

### Schritt 1️⃣: Python installieren

1. Download: https://www.python.org/downloads/
2. Bei Installation WICHTIG: ✅ "Add Python to PATH" anhaken
3. Installation abschließen

### Schritt 2️⃣: WerkstattArchiv installieren

1. **Rechtsklick** auf `install.bat`
2. Wähle: **"Als Administrator ausführen"**
3. Warte 5-10 Minuten

✅ Installiert automatisch:
- Alle Python-Pakete
- **EasyOCR** (Python-basierte OCR - keine Tesseract-Installation nötig!)
- Desktop-Verknüpfung

### Schritt 3️⃣: Fertig! Programm starten

- **Doppelklick** auf Desktop-Icon "WerkstattArchiv"

---

## ⚙️ Erste Konfiguration (im Programm)

Nach dem ersten Start:

1. Gehe zu **"Einstellungen"** → **"Pfade"**

2. Setze nur 2 Pfade:
   - **Basis-Verzeichnis**: `C:\WerkstattArchiv\Daten`
   - **Eingangsordner**: `C:\WerkstattArchiv\Eingang`

3. Klicke **"💾 Alle Einstellungen speichern"**

✅ Folgende Pfade werden **automatisch** generiert:
- Unklar-Ordner: `C:\WerkstattArchiv\Daten\Unklar`
- Duplikate-Ordner: `C:\WerkstattArchiv\Daten\Duplikate`
- Kundendatei: `C:\WerkstattArchiv\Daten\kunden.csv`

---

## 📋 Verwendung

1. **Dokumente ablegen**:
   - Kopiere PDFs in `C:\WerkstattArchiv\Eingang`

2. **Dokumente scannen**:
   - Klicke im Programm: **"🔍 Eingangsordner scannen"**
   - Zeigt gefundene Dateien an

3. **Verarbeitung starten**:
   - Klicke: **"▶️ Verarbeitung starten"**
   - Programm sortiert automatisch nach Kunde/Jahr/Typ

4. **Fertig!**
   - Sortierte Dokumente findest du in: `C:\WerkstattArchiv\Daten\[Kunde]\[Jahr]\[Typ]\`
   - Unklare Dokumente in: `C:\WerkstattArchiv\Daten\Unklar\`

---

## 🔍 OCR-Status prüfen

Beim Programm-Start siehst du im Terminal:

✅ **Mit EasyOCR (automatisch installiert):**
```
✅ EasyOCR verfügbar - verwende Python-basierte OCR (keine externe Installation nötig)
```

⚠️ **Falls EasyOCR fehlt:**
```
❌ Keine OCR-Engine verfügbar. Installiere: pip install easyocr
```
→ Lösung: Doppelklick auf `install_easyocr.bat`

---

## ❓ Häufige Fragen

### "Python ist nicht installiert"
→ Python 3.11+ von python.org installieren, bei Installation "Add to PATH" anhaken

### "OCR funktioniert nicht"
→ Doppelklick auf `install_easyocr.bat` (installiert Python-basierte OCR)

### "Dokumente werden nicht erkannt"
→ In Einstellungen → Regex-Patterns prüfen, ob Muster zu deinen Dokumenten passen

### "Kunde nicht gefunden"
→ Kunden in `C:\WerkstattArchiv\Daten\kunden.csv` hinzufügen (Format: `kundennr,name,strasse,plz,ort`)

---

## 📚 Weitere Dokumentation

- **Vollständige Installation**: `WINDOWS_INSTALLATION.md`
- **EasyOCR Setup**: `docs\EASYOCR_SETUP.md`
- **Entwickler-Dokumentation**: `DEVELOPMENT.md`

---

## 🆘 Support

Bei Problemen:
1. Prüfe `logs\` Ordner für Fehlermeldungen
2. Lies `WINDOWS_INSTALLATION.md` für Details
3. GitHub Issues: https://github.com/SHP-ART/WerkstattArchiv/issues

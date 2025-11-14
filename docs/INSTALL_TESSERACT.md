# Tesseract OCR Automatische Installation

Dieses Script installiert Tesseract OCR automatisch auf Windows und konfiguriert WerkstattArchiv.

## Verwendung

1. **Rechtsklick** auf `install_tesseract.bat`
2. **"Als Administrator ausführen"** wählen
3. Warte bis Installation abgeschlossen ist

## Was macht das Script?

### Schritt 1: Prüfung
- Prüft ob Tesseract bereits installiert ist
- Bietet Überspringen an falls vorhanden

### Schritt 2: Download
- Lädt Tesseract 5.3.3 (64-bit) herunter
- Download-Quelle: Universität Mannheim

### Schritt 3: Installation
- Installiert Tesseract im Silent-Mode
- Inklusive deutscher Sprachdaten
- Installations-Pfad: `C:\Program Files\Tesseract-OCR`

### Schritt 4: Konfiguration
- Öffnet `config.json`
- Trägt Tesseract-Pfad automatisch ein
- Speichert Konfiguration

### Schritt 5: Test
- Testet ob Tesseract funktioniert
- Zeigt Version an

## Voraussetzungen

- **Windows 7 oder neuer**
- **Administrator-Rechte**
- **Python installiert** (für Konfigurations-Update)
- **Internetverbindung** (für Download)

## Manuelle Installation

Falls das Script nicht funktioniert:

1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Installer ausführen
3. "German" Sprachdaten anhaken
4. In WerkstattArchiv:
   - Tab "Einstellungen"
   - Tesseract-Pfad: `C:\Program Files\Tesseract-OCR\tesseract.exe`
   - "Alle Einstellungen speichern"

## Problemlösung

### "Als Administrator ausführen" nicht möglich
- Rechtsklick auf Datei
- "Eigenschaften"
- Tab "Kompatibilität"
- "Dieses Programm als Administrator ausführen"

### Download schlägt fehl
- Internetverbindung prüfen
- Firewall/Antivirus deaktivieren
- Manuelle Installation verwenden

### "Python nicht gefunden"
- WerkstattArchiv erst installieren (`install.bat`)
- Dann Tesseract installieren

### Installation funktioniert nicht
- Alte Tesseract-Version deinstallieren
- PC neu starten
- Script erneut ausführen

## Deinstallation

### Tesseract entfernen:
1. Systemsteuerung → Programme und Features
2. "Tesseract-OCR" suchen
3. Rechtsklick → Deinstallieren

### Pfad aus WerkstattArchiv entfernen:
1. WerkstattArchiv starten
2. Tab "Einstellungen"
3. Tesseract-Pfad löschen (leer lassen)
4. "Alle Einstellungen speichern"

## Weitere Informationen

- **Vollständiger Guide**: `docs/TESSERACT_SETUP.md`
- **Windows-Installation**: `WINDOWS_INSTALLATION.md`
- **Tesseract Website**: https://github.com/tesseract-ocr/tesseract

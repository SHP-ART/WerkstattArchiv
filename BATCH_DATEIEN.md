# Windows Batch-Dateien Übersicht

## 📦 Installation & Setup

### `install.bat` ⭐ **HAUPTINSTALLER**
**Als Administrator ausführen!**
- Prüft Python-Installation
- Erstellt virtuelle Umgebung (venv)
- Installiert alle Python-Pakete
- Erstellt Standardkonfiguration
- Erstellt Desktop-Verknüpfung

**Verwendung:**
```
Rechtsklick → Als Administrator ausführen
```

---

### `setup_folders.bat` 📁
Erstellt Ordnerstruktur für Daten
- `C:\WerkstattArchiv\Eingang`
- `C:\WerkstattArchiv\Daten`
- `C:\WerkstattArchiv\Unklar`
- `C:\WerkstattArchiv\config\kunden.csv`

**Verwendung:**
```
Doppelklick
```

---

## 🚀 Anwendung nutzen

### `start.bat` ▶️ **PROGRAMM STARTEN**
Startet WerkstattArchiv
- Aktiviert venv automatisch
- Startet GUI
- Zeigt Fehler falls vorhanden

**Verwendung:**
```
Doppelklick
ODER Desktop-Verknüpfung verwenden
```

---

## 🔧 Erweiterte Funktionen

### `build_exe.bat` 📦
Erstellt standalone EXE-Datei
- Installiert PyInstaller
- Baut WerkstattArchiv.exe
- Kopiert Dateien nach `dist\`
- Kann auf PCs ohne Python verwendet werden

**Verwendung:**
```
Doppelklick (dauert 5-10 Min)
Ergebnis: dist\WerkstattArchiv\WerkstattArchiv.exe
```

**Wichtig:** 
- Benötigt funktionierende venv (install.bat vorher ausführen)
- Tesseract muss auf Ziel-PC separat installiert werden

---

### `uninstall.bat` 🗑️
Deinstalliert WerkstattArchiv
- Löscht venv
- Löscht Desktop-Verknüpfung
- Löscht Build-Dateien
- **BEHÄLT**: config.json, Datenbank, C:\WerkstattArchiv\

**Verwendung:**
```
Doppelklick → Bestätigung mit "J"
```

---

## 📋 Reihenfolge bei Erstinstallation

```
1. install.bat (als Admin)
   ↓
2. setup_folders.bat
   ↓
3. C:\WerkstattArchiv\config\kunden.csv bearbeiten
   ↓
4. start.bat
```

---

## ❓ Problemlösung

### install.bat schlägt fehl
- Python nicht installiert → https://python.org installieren
- Nicht als Admin gestartet → Rechtsklick → Als Admin
- Internetverbindung prüfen (für Paket-Download)

### start.bat zeigt "venv nicht gefunden"
- install.bat ausführen
- Prüfen ob `venv\` Ordner existiert

### build_exe.bat schlägt fehl
- Erst install.bat ausführen
- Genug Festplattenplatz? (ca. 500 MB)
- Antivirus vorübergehend deaktivieren

---

## 🔄 Updates installieren

```
1. uninstall.bat ausführen
2. Neue Dateien kopieren/ersetzen
3. install.bat ausführen
```

**Wichtig:** config.json wird nicht überschrieben!

---

## 📝 Hinweise

- Alle .bat Dateien müssen im Projektordner bleiben
- Desktop-Verknüpfung zeigt auf start.bat
- Log-Dateien: WerkstattArchiv_log.txt
- Bei Problemen: Als Administrator ausführen

---

## 🎯 Was macht welche Datei?

| Datei | Zweck | Admin? | Häufigkeit |
|-------|-------|--------|------------|
| install.bat | Installation | ✅ Ja | 1x |
| setup_folders.bat | Ordner erstellen | ❌ Nein | 1x |
| start.bat | Programm starten | ❌ Nein | Oft |
| build_exe.bat | EXE erstellen | ❌ Nein | Optional |
| uninstall.bat | Deinstallation | ❌ Nein | Bei Bedarf |

---

**Bei Fragen:** Siehe WINDOWS_INSTALLATION.md

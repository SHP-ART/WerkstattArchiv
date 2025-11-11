# Entwicklung unter macOS

## Entwicklungsumgebung einrichten

### 1. Python Virtual Environment erstellen

```bash
cd WerkstattArchiv
python3 -m venv venv
source venv/bin/activate
```

### 2. Dependencies installieren

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Tesseract für macOS installieren

```bash
brew install tesseract
brew install tesseract-lang
```

Tesseract-Pfad finden:
```bash
which tesseract
# Typischerweise: /opt/homebrew/bin/tesseract oder /usr/local/bin/tesseract
```

### 4. Konfiguration für macOS anpassen

Erstelle eine `config_dev.json` für die Entwicklung:

```json
{
  "root_dir": "/Users/DEIN_USERNAME/Documents/WerkstattArchiv_Test/Daten",
  "input_dir": "/Users/DEIN_USERNAME/Documents/WerkstattArchiv_Test/Eingang",
  "unclear_dir": "/Users/DEIN_USERNAME/Documents/WerkstattArchiv_Test/Unklar",
  "customers_file": "/Users/DEIN_USERNAME/Documents/WerkstattArchiv_Test/kunden.csv",
  "tesseract_path": "/opt/homebrew/bin/tesseract"
}
```

Kopiere dann für Tests:
```bash
cp config_dev.json config.json
```

### 5. Test-Ordnerstruktur erstellen

```bash
mkdir -p ~/Documents/WerkstattArchiv_Test/{Eingang,Daten,Unklar}
cp kunden_beispiel.csv ~/Documents/WerkstattArchiv_Test/kunden.csv
```

## Anwendung starten

```bash
python main.py
```

## Testen

### Test-PDF erstellen

Du kannst Test-PDFs mit folgendem Python-Skript erstellen:

```python
from reportlab.pdfgen import canvas

def create_test_pdf():
    c = canvas.Canvas("test_rechnung.pdf")
    c.drawString(100, 800, "Kunde-Nr: 10234")
    c.drawString(100, 780, "Auftrag-Nr: 500123")
    c.drawString(100, 760, "Datum: 15.01.2025")
    c.drawString(100, 740, "Rechnung")
    c.drawString(100, 720, "Betrag: 150,00 EUR")
    c.save()

create_test_pdf()
```

Installiere reportlab:
```bash
pip install reportlab
```

## Debugging

### Import-Fehler beheben

Falls Pylance Import-Errors anzeigt:
```bash
# Python-Interpreter in VS Code auswählen
# CMD+Shift+P -> "Python: Select Interpreter" -> venv auswählen
```

### GUI startet nicht

customtkinter benötigt tkinter:
```bash
# tkinter sollte mit Python installiert sein
python -m tkinter  # Öffnet Test-Fenster wenn verfügbar
```

Falls nicht installiert:
```bash
brew install python-tk@3.11
```

## Cross-Platform-Entwicklung

### Pfade

Nutze immer `os.path.join()` statt hardcoded `/` oder `\\`:

```python
# Gut
path = os.path.join(root_dir, "Kunde", kunde_ordner)

# Schlecht
path = root_dir + "/Kunde/" + kunde_ordner  # Funktioniert nicht auf Windows
```

### Dateinamen

Windows erlaubt bestimmte Zeichen nicht in Dateinamen:
- `< > : " / \\ | ? *`

Bereinige Dateinamen wenn nötig:

```python
import re
safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
```

## Deployment für Windows

### PyInstaller unter macOS (für Windows-Build)

PyInstaller erstellt nur für das aktuelle OS Executables. 
Für Windows-Deployment:

1. **Option A**: Auf Windows-Rechner kompilieren
2. **Option B**: Windows-VM auf Mac nutzen (Parallels, VMware)

Auf Windows:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name WerkstattArchiv main.py
```

### Wichtige Hinweise für Windows-Deployment

- Tesseract-Pfad muss auf Windows-System angepasst werden
- Standardpfade `D:/Scan/...` in config.json verwenden
- Test auf Windows-Zielsystem durchführen

## Troubleshooting

### "No module named 'fitz'"

```bash
pip install PyMuPDF
```

### OCR funktioniert nicht

Prüfe Tesseract-Installation:
```bash
tesseract --version
tesseract --list-langs  # Sollte 'deu' enthalten
```

### GUI-Darstellungsprobleme

customtkinter nutzt unterschiedliche Rendering-Engines:
```python
# In main_window.py Appearance-Mode testen
ctk.set_appearance_mode("light")  # oder "dark" oder "system"
```

## Nützliche Commands

```bash
# Virtual Environment aktivieren
source venv/bin/activate

# Deaktivieren
deactivate

# Alle Dependencies exportieren
pip freeze > requirements.txt

# Projekt aufräumen
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Tests ausführen (wenn vorhanden)
python -m pytest

# Code formatieren
pip install black
black .

# Type checking
pip install mypy
mypy services/ ui/ main.py
```

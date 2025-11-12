#!/bin/bash

###############################################################################
# WerkstattArchiv Setup Script für macOS/Linux
# Installiert alle Abhängigkeiten inkl. Python, Tesseract und Python-Pakete
###############################################################################

echo "============================================================"
echo "WerkstattArchiv Setup"
echo "============================================================"
echo ""

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Prüfe ob Homebrew installiert ist (nur macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📦 Prüfe Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}Homebrew ist nicht installiert. Installiere Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Homebrew zu PATH hinzufügen (für Apple Silicon Macs)
        if [[ $(uname -m) == 'arm64' ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    else
        echo -e "${GREEN}✓ Homebrew ist installiert${NC}"
    fi
fi

# Prüfe Python 3
echo ""
echo "🐍 Prüfe Python 3..."
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python 3 ist nicht installiert. Installiere Python 3...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install python@3.11
    else
        echo -e "${RED}Bitte installieren Sie Python 3.11 manuell: https://www.python.org/downloads/${NC}"
        exit 1
    fi
else
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python ist installiert: $PYTHON_VERSION${NC}"
fi

# Prüfe pip
echo ""
echo "📦 Prüfe pip..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}pip ist nicht installiert. Installiere pip...${NC}"
    python3 -m ensurepip --upgrade
else
    echo -e "${GREEN}✓ pip ist installiert${NC}"
fi

# Upgrade pip
echo ""
echo "⬆️  Aktualisiere pip..."
python3 -m pip install --upgrade pip

# Prüfe Tesseract (optional aber empfohlen)
echo ""
echo "🔍 Prüfe Tesseract-OCR..."
if ! command -v tesseract &> /dev/null; then
    echo -e "${YELLOW}Tesseract ist nicht installiert.${NC}"
    read -p "Möchten Sie Tesseract für OCR installieren? (empfohlen für gescannte PDFs) [y/n]: " install_tesseract
    
    if [[ $install_tesseract == "y" || $install_tesseract == "Y" ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "Installiere Tesseract..."
            brew install tesseract
            brew install tesseract-lang  # Sprachpakete
        else
            echo -e "${YELLOW}Linux: sudo apt-get install tesseract-ocr tesseract-ocr-deu${NC}"
        fi
    else
        echo "Tesseract wird übersprungen (kann später installiert werden)"
    fi
else
    TESSERACT_VERSION=$(tesseract --version | head -n 1)
    echo -e "${GREEN}✓ Tesseract ist installiert: $TESSERACT_VERSION${NC}"
fi

# Installiere Python-Abhängigkeiten
echo ""
echo "📚 Installiere Python-Pakete..."
echo ""

if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
else
    echo -e "${YELLOW}requirements.txt nicht gefunden. Installiere Pakete einzeln...${NC}"
    
    # Core-Pakete
    python3 -m pip install customtkinter
    python3 -m pip install pillow
    python3 -m pip install pypdf2
    python3 -m pip install pytesseract
    python3 -m pip install python-dateutil
    
    # Optional: watchdog für Auto-Watch
    python3 -m pip install watchdog
fi

echo ""
echo -e "${GREEN}✓ Alle Python-Pakete installiert${NC}"

# Erstelle Verzeichnisstruktur
echo ""
echo "📁 Erstelle Verzeichnisstruktur..."

mkdir -p data/index
mkdir -p config
mkdir -p backups
mkdir -p logs

echo -e "${GREEN}✓ Verzeichnisse erstellt${NC}"

# Prüfe ob config.json existiert
echo ""
if [ ! -f "config.json" ]; then
    echo "⚙️  Erstelle Standard-Konfiguration..."
    cat > config.json << 'EOF'
{
  "root_dir": "",
  "input_dir": "",
  "unclear_dir": "",
  "customers_file": "",
  "tesseract_path": null
}
EOF
    echo -e "${GREEN}✓ config.json erstellt${NC}"
    echo -e "${YELLOW}Bitte konfigurieren Sie die Pfade in den Einstellungen!${NC}"
else
    echo -e "${GREEN}✓ config.json existiert bereits${NC}"
fi

# Prüfe ob kunden.csv existiert
echo ""
if [ ! -f "config/kunden.csv" ]; then
    echo "👥 Erstelle leere Kundendatei..."
    touch config/kunden.csv
    echo -e "${GREEN}✓ config/kunden.csv erstellt${NC}"
    echo -e "${YELLOW}Bitte fügen Sie Ihre Kunden hinzu (Format: Kundennr;Name;PLZ;Ort;Straße;Telefon)${NC}"
else
    echo -e "${GREEN}✓ Kundendatei existiert bereits${NC}"
fi

# Erstelle vehicles.csv falls nicht vorhanden
echo ""
if [ ! -f "data/vehicles.csv" ]; then
    echo "🚗 Erstelle leere Fahrzeugdatenbank..."
    cat > data/vehicles.csv << 'EOF'
fin,kennzeichen,kunden_nr,marke,modell,erstzulassung,letzte_aktualisierung
EOF
    echo -e "${GREEN}✓ data/vehicles.csv erstellt${NC}"
    echo -e "${YELLOW}Wird automatisch beim Verarbeiten von Dokumenten gefüllt${NC}"
else
    echo -e "${GREEN}✓ Fahrzeugdatenbank existiert bereits${NC}"
fi

# Tesseract-Pfad automatisch erkennen und in config eintragen
if command -v tesseract &> /dev/null; then
    TESSERACT_PATH=$(which tesseract)
    echo ""
    echo "🔧 Konfiguriere Tesseract-Pfad..."
    
    # Python-Script zum Update der config.json
    python3 << EOF
import json
import os

config_file = 'config.json'
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    if config.get('tesseract_path') is None:
        config['tesseract_path'] = '$TESSERACT_PATH'
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print('✓ Tesseract-Pfad wurde automatisch konfiguriert: $TESSERACT_PATH')
EOF
fi

# Fertig!
echo ""
echo "============================================================"
echo -e "${GREEN}✅ Setup abgeschlossen!${NC}"
echo "============================================================"
echo ""
echo "🚀 Sie können WerkstattArchiv jetzt starten:"
echo ""
echo "   python3 main.py"
echo ""
echo "📝 Nächste Schritte:"
echo "   1. Konfigurieren Sie die Ordnerpfade in den Einstellungen"
echo "   2. Fügen Sie Ihre Kunden zur config/kunden.csv hinzu"
echo "   3. Legen Sie Dokumente in den Eingangsordner"
echo ""
echo "============================================================"

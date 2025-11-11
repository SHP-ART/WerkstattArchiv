#!/usr/bin/env python3
"""
Quick Setup Script für WerkstattArchiv
Erstellt Test-Ordnerstruktur und Beispieldaten
"""

import os
import sys
from pathlib import Path


def create_test_structure():
    """Erstellt eine Test-Ordnerstruktur für die Entwicklung."""
    
    print("=" * 60)
    print("WerkstattArchiv - Quick Setup")
    print("=" * 60)
    print()
    
    # Home-Verzeichnis bestimmen
    home = Path.home()
    base_path = home / "Documents" / "WerkstattArchiv_Test"
    
    print(f"Erstelle Test-Struktur in: {base_path}")
    print()
    
    # Ordner erstellen
    folders = [
        base_path,
        base_path / "Eingang",
        base_path / "Daten",
        base_path / "Unklar",
        base_path / "config",
    ]
    
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
        print(f"✓ {folder}")
    
    print()
    
    # Kundendatei kopieren
    source_customers = Path(__file__).parent / "kunden_beispiel.csv"
    target_customers = base_path / "config" / "kunden.csv"
    
    if source_customers.exists():
        with open(source_customers, "r", encoding="utf-8") as f:
            content = f.read()
        with open(target_customers, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ Kundendatei erstellt: {target_customers}")
    else:
        print(f"⚠ Kundendatei nicht gefunden: {source_customers}")
    
    print()
    
    # Config erstellen
    config_content = f"""{{
  "root_dir": "{str(base_path / 'Daten').replace(os.sep, '/')}",
  "input_dir": "{str(base_path / 'Eingang').replace(os.sep, '/')}",
  "unclear_dir": "{str(base_path / 'Unklar').replace(os.sep, '/')}",
  "customers_file": "{str(target_customers).replace(os.sep, '/')}",
  "tesseract_path": null
}}
"""
    
    config_file = Path(__file__).parent / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config_content)
    
    print(f"✓ Konfiguration erstellt: {config_file}")
    print()
    
    # Test-PDF erstellen (optional)
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        
        test_pdf = base_path / "Eingang" / "test_rechnung.pdf"
        c = canvas.Canvas(str(test_pdf), pagesize=A4)
        c.setFont("Helvetica", 12)
        c.drawString(100, 800, "Kunde-Nr: 10234")
        c.drawString(100, 780, "Auftrag-Nr: 500123")
        c.drawString(100, 760, "Datum: 15.01.2025")
        c.drawString(100, 740, "")
        c.drawString(100, 720, "Rechnung")
        c.drawString(100, 700, "")
        c.drawString(100, 680, "Position 1: Ölwechsel - 50,00 EUR")
        c.drawString(100, 660, "Position 2: Filter - 25,00 EUR")
        c.drawString(100, 640, "")
        c.drawString(100, 620, "Summe: 75,00 EUR")
        c.save()
        
        print(f"✓ Test-PDF erstellt: {test_pdf}")
        print()
        
    except ImportError:
        print("⚠ reportlab nicht installiert - kein Test-PDF erstellt")
        print("  Installation: pip install reportlab")
        print()
    
    # Zusammenfassung
    print("=" * 60)
    print("Setup abgeschlossen!")
    print("=" * 60)
    print()
    print("Nächste Schritte:")
    print()
    print("1. Python-Abhängigkeiten installieren:")
    print("   pip install -r requirements.txt")
    print()
    print("2. Anwendung starten:")
    print("   python main.py")
    print()
    print("3. In der GUI:")
    print("   - Tab 'Einstellungen' öffnen")
    print("   - Pfade prüfen (sollten bereits gesetzt sein)")
    print("   - 'Kundendatenbank neu laden' klicken")
    print("   - Tab 'Verarbeitung' öffnen")
    print("   - 'Eingangsordner scannen' klicken")
    print()
    print(f"Test-Ordner: {base_path}")
    print()


if __name__ == "__main__":
    try:
        create_test_structure()
    except KeyboardInterrupt:
        print("\n\nAbgebrochen durch Benutzer.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFehler: {e}")
        sys.exit(1)

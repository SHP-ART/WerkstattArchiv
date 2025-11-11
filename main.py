"""
WerkstattArchiv - Haupteinstiegspunkt
Lokale Dokumentenverwaltung für Werkstattdokumente
"""

import os
import json
from typing import Dict, Any

from services.customers import CustomerManager
from ui.main_window import create_and_run_gui


CONFIG_FILE = "config.json"


def load_config() -> Dict[str, Any]:
    """
    Lädt die Konfiguration aus config.json.
    Erstellt eine Standardkonfiguration, falls die Datei nicht existiert.
    
    Returns:
        Konfigurationsdictionary
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"Warnung: {CONFIG_FILE} nicht gefunden. Erstelle Standardkonfiguration.")
        
        default_config = {
            "root_dir": "D:/Scan/Daten",
            "input_dir": "D:/Scan/Eingang",
            "unclear_dir": "D:/Scan/Unklar",
            "customers_file": "D:/Scan/config/kunden.csv",
            "tesseract_path": None
        }
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        return default_config
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    
    except Exception as e:
        print(f"Fehler beim Laden der Konfiguration: {e}")
        print("Verwende Standardkonfiguration.")
        
        return {
            "root_dir": "D:/Scan/Daten",
            "input_dir": "D:/Scan/Eingang",
            "unclear_dir": "D:/Scan/Unklar",
            "customers_file": "D:/Scan/config/kunden.csv",
            "tesseract_path": None
        }


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validiert die Konfiguration.
    
    Args:
        config: Zu prüfendes Konfigurationsdictionary
        
    Returns:
        True wenn gültig, sonst False
    """
    required_keys = ["root_dir", "input_dir", "unclear_dir", "customers_file"]
    
    for key in required_keys:
        if key not in config:
            print(f"Fehler: Konfiguration unvollständig. Fehlender Schlüssel: {key}")
            return False
    
    return True


def main():
    """Hauptfunktion der Anwendung."""
    print("=" * 60)
    print("WerkstattArchiv - Dokumentenverwaltung")
    print("=" * 60)
    print()
    
    # Konfiguration laden
    print("Lade Konfiguration...")
    config = load_config()
    
    if not validate_config(config):
        print("Fehler: Ungültige Konfiguration. Bitte config.json prüfen.")
        input("Drücke Enter zum Beenden...")
        return
    
    print("✓ Konfiguration geladen")
    print()
    
    # CustomerManager initialisieren
    print("Lade Kundendatenbank...")
    customers_file = config.get("customers_file", "")
    customer_manager = CustomerManager(customers_file)
    print()
    
    # GUI starten
    print("Starte GUI...")
    print()
    
    try:
        create_and_run_gui(config, customer_manager)
    except KeyboardInterrupt:
        print("\nAnwendung beendet durch Benutzer.")
    except Exception as e:
        print(f"\nFehler beim Starten der GUI: {e}")
        input("Drücke Enter zum Beenden...")


if __name__ == "__main__":
    main()

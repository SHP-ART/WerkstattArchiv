"""
WerkstattArchiv - Haupteinstiegspunkt
Lokale Dokumentenverwaltung für Werkstattdokumente
"""

import os
import json
from typing import Dict, Any

from services.customers import CustomerManager
from core.config_backup import ConfigBackupManager
from ui.main_window import create_and_run_gui


CONFIG_FILE = "config.json"


def load_config() -> Dict[str, Any]:
    """
    Lädt die Konfiguration aus config.json.
    Falls nicht vorhanden: Versucht Restore aus Backup.
    Erstellt Standardkonfiguration als letzte Option.
    
    Returns:
        Konfigurationsdictionary
    """
    backup_manager = ConfigBackupManager()
    
    # FALL 1: config.json existiert → Lade normal
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            print("✓ Konfiguration aus config.json geladen")
            return config
        
        except Exception as e:
            print(f"⚠️  Fehler beim Laden von config.json: {e}")
            # Fallthrough zu FALL 2
    
    # FALL 2: config.json fehlt → Versuche Backup-Restore
    print(f"⚠️  {CONFIG_FILE} nicht gefunden.")
    
    if backup_manager.backup_exists():
        print("🔄 Versuche Wiederherstellung aus Backup...")
        restored_config = backup_manager.restore_backup()
        
        if restored_config:
            print("✅ Konfiguration aus Backup wiederhergestellt!")
            
            # Speichere wiederhergestellte Config
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(restored_config, f, indent=2, ensure_ascii=False)
            
            return restored_config
        else:
            print("⚠️  Backup-Wiederherstellung fehlgeschlagen.")
            # Fallthrough zu FALL 3
    else:
        print("ℹ️  Kein Backup vorhanden.")
    
    # FALL 3: Kein Backup → Erstelle Standardkonfiguration
    print("🆕 Erstelle neue Standardkonfiguration...")
    
    default_config = {
        "root_dir": "D:/Scan/Daten",
        "input_dir": "D:/Scan/Eingang",
        "unclear_dir": "D:/Scan/Unklar",
        "duplicates_dir": "D:/Scan/Duplikate",
        "customers_file": "D:/Scan/config/kunden.csv",
        "tesseract_path": None
    }
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print("✓ Standardkonfiguration erstellt")
    return default_config


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
    # Version importieren
    try:
        from version import __version__, __app_name__, __description__
        app_name = __app_name__
        version = __version__
        description = __description__
    except ImportError:
        app_name = "WerkstattArchiv"
        version = "0.8.5"
        description = "Dokumentenverwaltung"
    
    print("=" * 60)
    print(f"{app_name} v{version}")
    print(description)
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
        import traceback
        traceback.print_exc()
        input("Drücke Enter zum Beenden...")


if __name__ == "__main__":
    main()

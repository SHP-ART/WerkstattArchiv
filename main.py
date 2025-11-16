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
    Lädt die Konfiguration.
    Priorität: 
    1. config.json im Basis-Verzeichnis (VORRANG!)
    2. config.json im Programmverzeichnis
    3. Restore aus Backup
    4. Standardkonfiguration
    
    Returns:
        Konfigurationsdictionary
    """
    backup_manager = ConfigBackupManager()
    
    # Schritt 1: Lade lokale config.json um root_dir zu kennen
    local_config = None
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                local_config = json.load(f)
        except Exception as e:
            print(f"⚠️  Fehler beim Laden von {CONFIG_FILE}: {e}")
    
    # Schritt 2: PRIORITÄT! Wenn root_dir existiert, lade config.json von dort
    if local_config and local_config.get("root_dir"):
        root_dir = local_config["root_dir"]
        config_in_root = os.path.join(root_dir, "config.json")
        
        if os.path.exists(config_in_root):
            try:
                with open(config_in_root, "r", encoding="utf-8") as f:
                    config = json.load(f)
                print(f"✓ Konfiguration aus Basis-Verzeichnis geladen (VORRANG): {config_in_root}")
                return config
            except Exception as e:
                print(f"⚠️  Fehler beim Laden von {config_in_root}: {e}")
    
    # FALL 1: Lokale config.json existiert → Lade sie als Fallback
    if local_config:
        print("✓ Konfiguration aus Programmverzeichnis geladen")
        return local_config
    
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

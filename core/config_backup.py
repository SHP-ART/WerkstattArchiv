"""
Config Backup Manager
Zentrale Verwaltung von Konfigurations-Backups im data/-Ordner
Verhindert Datenverlust bei Neuinstallation oder Update
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, Any, Optional


class ConfigBackupManager:
    """Verwaltet automatische Backups aller wichtigen Einstellungen."""
    
    # Backup-Datei im data/-Ordner (plattformunabhängig)
    BACKUP_FILE = "data/config_backup.json"
    
    # Dateien die gesichert werden
    FILES_TO_BACKUP = [
        "config.json",                              # Hauptkonfiguration
        "patterns.json",                            # Erkennungsmuster
        "data/vehicles.csv"                         # Fahrzeugdaten
    ]
    
    # Wichtige Config-Keys die verglichen werden sollen
    IMPORTANT_CONFIG_KEYS = [
        "root_dir",
        "input_dir",
        "unclear_dir",
        "duplicates_dir",
        "customers_file",
        "tesseract_path"
    ]
    
    # Wichtige Ordnerstruktur-Keys die verglichen werden sollen
    IMPORTANT_STRUCTURE_KEYS = [
        "folder_template",
        "filename_template",
        "replace_spaces",
        "remove_invalid_chars",
        "use_month_names"
    ]
    
    def __init__(self):
        """Initialisiert den Backup-Manager."""
        self.backup_dir = os.path.dirname(self.BACKUP_FILE)
        
        # Stelle sicher dass data/-Ordner existiert
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, config: Dict[str, Any]) -> bool:
        """
        Erstellt ein vollständiges Backup aller wichtigen Einstellungen.
        
        Args:
            config: Aktuelle Konfiguration
            
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "version": self._get_version(),
                "config": config.copy(),
                "files": {}
            }
            
            # Sichere zusätzliche Dateien
            for file_path in self.FILES_TO_BACKUP:
                if os.path.exists(file_path):
                    try:
                        # Für JSON-Dateien: Lade und speichere Inhalt
                        if file_path.endswith('.json'):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                backup_data["files"][file_path] = json.load(f)
                        
                        # Für CSV-Dateien: Lade als Text
                        elif file_path.endswith('.csv'):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                backup_data["files"][file_path] = f.read()
                    
                    except Exception as e:
                        print(f"⚠️  Warnung: Konnte {file_path} nicht sichern: {e}")
            
            # Schreibe Backup-Datei
            with open(self.BACKUP_FILE, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Backup erstellt: {self.BACKUP_FILE}")
            return True
        
        except Exception as e:
            print(f"❌ Fehler beim Erstellen des Backups: {e}")
            return False
    
    def restore_backup(self) -> Optional[Dict[str, Any]]:
        """
        Stellt die Konfiguration aus dem Backup wieder her.
        
        Returns:
            Wiederhergestellte Konfiguration oder None bei Fehler
        """
        if not os.path.exists(self.BACKUP_FILE):
            print(f"⚠️  Kein Backup gefunden: {self.BACKUP_FILE}")
            return None
        
        try:
            with open(self.BACKUP_FILE, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Stelle Hauptkonfiguration wieder her
            config = backup_data.get("config", {})
            
            # Stelle zusätzliche Dateien wieder her
            files = backup_data.get("files", {})
            for file_path, content in files.items():
                try:
                    # Erstelle Verzeichnis falls nötig
                    file_dir = os.path.dirname(file_path)
                    if file_dir and not os.path.exists(file_dir):
                        os.makedirs(file_dir, exist_ok=True)
                    
                    # Schreibe Datei
                    if file_path.endswith('.json'):
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(content, f, indent=2, ensure_ascii=False)
                    
                    elif file_path.endswith('.csv'):
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                    
                    print(f"✅ Wiederhergestellt: {file_path}")
                
                except Exception as e:
                    print(f"⚠️  Warnung: Konnte {file_path} nicht wiederherstellen: {e}")
            
            timestamp = backup_data.get("timestamp", "unbekannt")
            version = backup_data.get("version", "unbekannt")
            print(f"✅ Backup wiederhergestellt (vom {timestamp}, Version {version})")
            
            return config
        
        except Exception as e:
            print(f"❌ Fehler beim Wiederherstellen des Backups: {e}")
            return None
    
    def get_backup_info(self) -> Optional[Dict[str, Any]]:
        """
        Gibt Informationen über das vorhandene Backup zurück.
        
        Returns:
            Dictionary mit Backup-Informationen oder None
        """
        if not os.path.exists(self.BACKUP_FILE):
            return None
        
        try:
            with open(self.BACKUP_FILE, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            return {
                "exists": True,
                "timestamp": backup_data.get("timestamp", "unbekannt"),
                "version": backup_data.get("version", "unbekannt"),
                "file_count": len(backup_data.get("files", {})),
                "size": os.path.getsize(self.BACKUP_FILE)
            }
        
        except Exception as e:
            print(f"⚠️  Fehler beim Lesen der Backup-Info: {e}")
            return None
    
    def backup_exists(self) -> bool:
        """Prüft ob ein Backup vorhanden ist."""
        return os.path.exists(self.BACKUP_FILE)
    
    def compare_with_current(self, current_config: Dict[str, Any]) -> Dict[str, Any]:
        """:
        Vergleicht aktuelles Backup mit der übergebenen Config.
        
        Args:
            current_config: Aktuelle Konfiguration zum Vergleich
            
        Returns:
            Dictionary mit Vergleichsergebnissen:
            {
                "has_differences": bool,
                "backup_exists": bool,
                "path_differences": [(key, current, backup), ...],
                "structure_differences": [(key, current, backup), ...],
                "backup_timestamp": str,
                "backup_version": str
            }
        """
        result = {
            "has_differences": False,
            "backup_exists": False,
            "path_differences": [],
            "structure_differences": [],
            "backup_timestamp": None,
            "backup_version": None
        }
        
        # Prüfe ob Backup existiert
        if not self.backup_exists():
            return result
        
        result["backup_exists"] = True
        
        try:
            # Lade Backup
            with open(self.BACKUP_FILE, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            result["backup_timestamp"] = backup_data.get("timestamp", "unbekannt")
            result["backup_version"] = backup_data.get("version", "unbekannt")
            
            backup_config = backup_data.get("config", {})
            
            # Vergleiche Pfad-Einstellungen
            for key in self.IMPORTANT_CONFIG_KEYS:
                current_val = current_config.get(key)
                backup_val = backup_config.get(key)
                
                if current_val != backup_val:
                    result["path_differences"].append((key, current_val, backup_val))
                    result["has_differences"] = True
            
            # Vergleiche Ordnerstruktur-Einstellungen
            current_structure = current_config.get("folder_structure", {})
            backup_structure = backup_config.get("folder_structure", {})
            
            for key in self.IMPORTANT_STRUCTURE_KEYS:
                current_val = current_structure.get(key)
                backup_val = backup_structure.get(key)
                
                if current_val != backup_val:
                    result["structure_differences"].append((key, current_val, backup_val))
                    result["has_differences"] = True
            
            return result
        
        except Exception as e:
            print(f"⚠️  Fehler beim Vergleichen mit Backup: {e}")
            return result
    
    def _get_version(self) -> str:
        """Holt die aktuelle Programmversion."""
        try:
            import version
            return version.__version__
        except Exception:
            return "unbekannt"

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
    
    def _get_version(self) -> str:
        """Holt die aktuelle Programmversion."""
        try:
            import version
            return version.__version__
        except Exception:
            return "unbekannt"

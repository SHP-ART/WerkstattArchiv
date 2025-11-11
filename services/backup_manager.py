"""
Backup & Restore Manager für WerkstattArchiv.
Sichert und stellt alle wichtigen Daten wieder her.
"""

import os
import shutil
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import zipfile


class BackupManager:
    """Verwaltet Backups von Konfiguration, Datenbanken und Kundendaten."""
    
    def __init__(self, config: Dict[str, any]):  # type: ignore
        """
        Initialisiert den BackupManager.
        
        Args:
            config: Konfigurationsdictionary
        """
        self.config = config
        self.backup_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "..", 
            "backups"
        )
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, backup_name: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Erstellt ein vollständiges Backup.
        
        Args:
            backup_name: Optionaler Name für das Backup
            
        Returns:
            Tuple (success, backup_path, message)
        """
        try:
            # Backup-Namen generieren
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}"
            else:
                # Sanitize backup name
                backup_name = "".join(c for c in backup_name if c.isalnum() or c in "._- ")
                backup_name = backup_name.strip()
            
            # Backup-Ordner erstellen
            backup_path = os.path.join(self.backup_dir, backup_name)
            os.makedirs(backup_path, exist_ok=True)
            
            backed_up_files = []
            
            # 1. Konfigurationsdatei sichern
            config_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "..", 
                "config.json"
            )
            if os.path.exists(config_file):
                shutil.copy2(config_file, os.path.join(backup_path, "config.json"))
                backed_up_files.append("config.json")
            
            # 2. Kundendatenbank sichern
            customers_file = self.config.get("customers_file")
            if customers_file and os.path.exists(customers_file):
                shutil.copy2(customers_file, os.path.join(backup_path, "kunden.csv"))
                backed_up_files.append("kunden.csv")
            
            # 3. Fahrzeug-Index sichern
            vehicles_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "..", 
                "data",
                "vehicles.csv"
            )
            if os.path.exists(vehicles_file):
                shutil.copy2(vehicles_file, os.path.join(backup_path, "vehicles.csv"))
                backed_up_files.append("vehicles.csv")
            
            # 4. SQLite-Datenbank sichern
            db_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "..", 
                "werkstatt_index.db"
            )
            if os.path.exists(db_file):
                shutil.copy2(db_file, os.path.join(backup_path, "werkstatt_index.db"))
                backed_up_files.append("werkstatt_index.db")
            
            # 5. Regex-Patterns sichern
            patterns_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "..", 
                "patterns.json"
            )
            if os.path.exists(patterns_file):
                shutil.copy2(patterns_file, os.path.join(backup_path, "patterns.json"))
                backed_up_files.append("patterns.json")
            
            # 6. Backup-Info erstellen
            backup_info = {
                "created_at": datetime.now().isoformat(),
                "backup_name": backup_name,
                "files": backed_up_files,
                "config_snapshot": self.config.copy()
            }
            
            with open(os.path.join(backup_path, "backup_info.json"), "w", encoding="utf-8") as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            # 7. ZIP-Archiv erstellen
            zip_path = f"{backup_path}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_path)
                        zipf.write(file_path, arcname)
            
            # 8. Ordner löschen (nur ZIP behalten)
            shutil.rmtree(backup_path)
            
            message = (f"✓ Backup erfolgreich erstellt!\n\n"
                      f"Gesicherte Dateien: {', '.join(backed_up_files)}\n"
                      f"Speicherort: {zip_path}")
            
            return True, zip_path, message
            
        except Exception as e:
            return False, "", f"❌ Fehler beim Erstellen des Backups:\n{str(e)}"
    
    def restore_backup(self, backup_path: str) -> Tuple[bool, str]:
        """
        Stellt ein Backup wieder her.
        
        Args:
            backup_path: Pfad zum Backup (ZIP-Datei oder Ordner)
            
        Returns:
            Tuple (success, message)
        """
        try:
            # Temporären Ordner für Extraktion erstellen
            temp_dir = os.path.join(self.backup_dir, "temp_restore")
            os.makedirs(temp_dir, exist_ok=True)
            
            # ZIP entpacken wenn nötig
            if backup_path.endswith(".zip"):
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
            else:
                # Wenn es ein Ordner ist, Dateien kopieren
                for file in os.listdir(backup_path):
                    shutil.copy2(
                        os.path.join(backup_path, file),
                        os.path.join(temp_dir, file)
                    )
            
            # Backup-Info laden
            backup_info_path = os.path.join(temp_dir, "backup_info.json")
            if not os.path.exists(backup_info_path):
                raise Exception("Ungültiges Backup: backup_info.json fehlt")
            
            with open(backup_info_path, "r", encoding="utf-8") as f:
                backup_info = json.load(f)
            
            restored_files = []
            
            # 1. Konfigurationsdatei wiederherstellen
            config_backup = os.path.join(temp_dir, "config.json")
            if os.path.exists(config_backup):
                config_target = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), 
                    "..", 
                    "config.json"
                )
                shutil.copy2(config_backup, config_target)
                restored_files.append("config.json")
            
            # 2. Kundendatenbank wiederherstellen
            customers_backup = os.path.join(temp_dir, "kunden.csv")
            if os.path.exists(customers_backup):
                customers_target = self.config.get("customers_file")
                if customers_target:
                    os.makedirs(os.path.dirname(customers_target), exist_ok=True)
                    shutil.copy2(customers_backup, customers_target)
                    restored_files.append("kunden.csv")
            
            # 3. Fahrzeug-Index wiederherstellen
            vehicles_backup = os.path.join(temp_dir, "vehicles.csv")
            if os.path.exists(vehicles_backup):
                vehicles_target = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), 
                    "..", 
                    "data",
                    "vehicles.csv"
                )
                os.makedirs(os.path.dirname(vehicles_target), exist_ok=True)
                shutil.copy2(vehicles_backup, vehicles_target)
                restored_files.append("vehicles.csv")
            
            # 4. SQLite-Datenbank wiederherstellen
            db_backup = os.path.join(temp_dir, "werkstatt_index.db")
            if os.path.exists(db_backup):
                db_target = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), 
                    "..", 
                    "werkstatt_index.db"
                )
                shutil.copy2(db_backup, db_target)
                restored_files.append("werkstatt_index.db")
            
            # 5. Regex-Patterns wiederherstellen
            patterns_backup = os.path.join(temp_dir, "patterns.json")
            if os.path.exists(patterns_backup):
                patterns_target = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), 
                    "..", 
                    "patterns.json"
                )
                shutil.copy2(patterns_backup, patterns_target)
                restored_files.append("patterns.json")
            
            # Temporären Ordner löschen
            shutil.rmtree(temp_dir)
            
            message = (f"✓ Backup erfolgreich wiederhergestellt!\n\n"
                      f"Wiederhergestellte Dateien: {', '.join(restored_files)}\n"
                      f"Backup-Datum: {backup_info.get('created_at', 'Unbekannt')}\n\n"
                      f"⚠️ Bitte starten Sie die Anwendung neu!")
            
            return True, message
            
        except Exception as e:
            # Aufräumen bei Fehler
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return False, f"❌ Fehler beim Wiederherstellen:\n{str(e)}"
    
    def list_backups(self) -> List[Dict[str, any]]:  # type: ignore
        """
        Listet alle verfügbaren Backups auf.
        
        Returns:
            Liste von Backup-Informationen
        """
        backups = []
        
        try:
            for file in os.listdir(self.backup_dir):
                if file.endswith(".zip") and file.startswith("backup_"):
                    backup_path = os.path.join(self.backup_dir, file)
                    
                    # Info aus ZIP lesen
                    try:
                        with zipfile.ZipFile(backup_path, 'r') as zipf:
                            info_data = zipf.read("backup_info.json")
                            backup_info = json.loads(info_data.decode('utf-8'))
                            
                            backups.append({
                                "name": file.replace(".zip", ""),
                                "path": backup_path,
                                "created_at": backup_info.get("created_at", "Unbekannt"),
                                "size": os.path.getsize(backup_path),
                                "files": backup_info.get("files", [])
                            })
                    except:
                        # Falls Info nicht lesbar, zumindest Basis-Infos
                        backups.append({
                            "name": file.replace(".zip", ""),
                            "path": backup_path,
                            "created_at": datetime.fromtimestamp(
                                os.path.getmtime(backup_path)
                            ).isoformat(),
                            "size": os.path.getsize(backup_path),
                            "files": []
                        })
            
            # Nach Datum sortieren (neueste zuerst)
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            print(f"Fehler beim Auflisten der Backups: {e}")
        
        return backups
    
    def delete_backup(self, backup_path: str) -> Tuple[bool, str]:
        """
        Löscht ein Backup.
        
        Args:
            backup_path: Pfad zum Backup
            
        Returns:
            Tuple (success, message)
        """
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                return True, "✓ Backup erfolgreich gelöscht!"
            else:
                return False, "❌ Backup nicht gefunden!"
        except Exception as e:
            return False, f"❌ Fehler beim Löschen:\n{str(e)}"

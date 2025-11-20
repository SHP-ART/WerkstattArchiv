"""
Datenbank-Wartungs-Service für WerkstattArchiv.
Automatische Backups, Cleanup, Optimierung und Health-Checks.
"""

import os
import shutil
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import json


class DatabaseMaintenance:
    """Automatische Datenbank-Wartung und Backup-Management."""
    
    def __init__(self, db_path: str = "werkstatt_index.db", root_dir: Optional[str] = None):
        """
        Initialisiert den Wartungs-Service.
        
        Args:
            db_path: Pfad zur Datenbank-Datei
            root_dir: Basisverzeichnis (Server-Pfad mit automatischen Backups)
        """
        self.db_path = db_path
        self.log_file = "werkstatt.log"
        
        # Backup-Verzeichnis: Bevorzuge Basisverzeichnis (Server mit Backups)
        if root_dir and os.path.exists(root_dir):
            self.backup_dir = Path(root_dir) / "db_backups"
            self._log_info(f"Backup-Verzeichnis: {self.backup_dir} (Server mit automatischen Backups)")
        else:
            # Fallback: Lokales Verzeichnis
            self.backup_dir = Path("data/db_backups")
            if root_dir:
                self._log_info(f"Warnung: Basisverzeichnis nicht gefunden ({root_dir}), nutze lokales Backup")
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup-Einstellungen
        self.max_backups = 30  # Maximale Anzahl Backups
        self.backup_retention_days = 90  # Backups älter als 90 Tage löschen
    
    def _log_info(self, message: str) -> None:
        """Schreibt Info-Nachricht ins Log."""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: {message}\n")
        except:
            pass
    
    def _log_error(self, message: str) -> None:
        """Schreibt Fehler-Nachricht ins Log."""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: {message}\n")
        except:
            pass
        
    def create_backup(self, reason: str = "manual") -> Tuple[bool, str, str]:
        """
        Erstellt ein Backup der Datenbank.
        
        Args:
            reason: Grund des Backups (manual, daily, before_migration, etc.)
            
        Returns:
            Tuple (success, backup_path, message)
        """
        try:
            if not os.path.exists(self.db_path):
                return False, "", f"Datenbank nicht gefunden: {self.db_path}"
            
            # Backup-Dateiname mit Zeitstempel
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"werkstatt_index_backup_{timestamp}_{reason}.db"
            backup_path = self.backup_dir / backup_filename
            
            # Erstelle Backup mit SQLite-Backup-API (sicher während Schreibzugriffen)
            self._log_info(f"Erstelle Datenbank-Backup: {backup_filename}")
            
            source_conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(str(backup_path))
            
            with backup_conn:
                source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            # Backup-Metadaten speichern
            metadata = {
                "created_at": datetime.now().isoformat(),
                "reason": reason,
                "original_size": os.path.getsize(self.db_path),
                "backup_size": os.path.getsize(backup_path)
            }
            
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            success_msg = f"Backup erstellt: {backup_filename} ({self._format_bytes(metadata['backup_size'])})"
            self._log_info(success_msg)
            
            # Alte Backups aufräumen
            self._cleanup_old_backups()
            
            return True, str(backup_path), success_msg
            
        except Exception as e:
            error_msg = f"Backup fehlgeschlagen: {type(e).__name__}: {e}"
            self._log_error(error_msg)
            import traceback
            traceback.print_exc()
            return False, "", error_msg
    
    def _cleanup_old_backups(self) -> int:
        """
        Löscht alte Backups basierend auf Retention-Policy.
        
        Returns:
            Anzahl gelöschter Backups
        """
        try:
            backups = list(self.backup_dir.glob("werkstatt_index_backup_*.db"))
            backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            deleted_count = 0
            cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)
            
            for backup_file in backups:
                # Behalte die neuesten max_backups
                if len(backups) - deleted_count <= self.max_backups:
                    # Prüfe Alter
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_time > cutoff_date:
                        continue
                
                # Lösche Backup + Metadaten
                backup_file.unlink()
                metadata_file = backup_file.with_suffix('.json')
                if metadata_file.exists():
                    metadata_file.unlink()
                
                deleted_count += 1
                self._log_info(f"Altes Backup gelöscht: {backup_file.name}")
            
            if deleted_count > 0:
                self._log_info(f"Backup-Cleanup: {deleted_count} alte Backups gelöscht")
            
            return deleted_count
            
        except Exception as e:
            self._log_error(f"Backup-Cleanup fehlgeschlagen: {e}")
            return 0
    
    def restore_backup(self, backup_path: str) -> Tuple[bool, str]:
        """
        Stellt ein Backup wieder her.
        
        Args:
            backup_path: Pfad zum Backup
            
        Returns:
            Tuple (success, message)
        """
        try:
            if not os.path.exists(backup_path):
                return False, f"Backup nicht gefunden: {backup_path}"
            
            # Erstelle Sicherheits-Backup der aktuellen DB
            safety_backup = f"{self.db_path}.before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.db_path, safety_backup)
            self._log_info(f"Sicherheits-Backup erstellt: {safety_backup}")
            
            # Restore
            shutil.copy2(backup_path, self.db_path)
            
            success_msg = f"Backup wiederhergestellt: {os.path.basename(backup_path)}"
            self._log_info(success_msg)
            
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Restore fehlgeschlagen: {type(e).__name__}: {e}"
            self._log_error(error_msg)
            return False, error_msg
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        Listet alle verfügbaren Backups auf.
        
        Returns:
            Liste von Backup-Informationen
        """
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("werkstatt_index_backup_*.db"), 
                                   key=lambda p: p.stat().st_mtime, reverse=True):
            metadata_file = backup_file.with_suffix('.json')
            
            info = {
                "filename": backup_file.name,
                "path": str(backup_file),
                "size": os.path.getsize(backup_file),
                "size_formatted": self._format_bytes(os.path.getsize(backup_file)),
                "modified": datetime.fromtimestamp(backup_file.stat().st_mtime),
                "age_days": (datetime.now() - datetime.fromtimestamp(backup_file.stat().st_mtime)).days
            }
            
            # Lade Metadaten falls vorhanden
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        info.update(metadata)
                except:
                    pass
            
            backups.append(info)
        
        return backups
    
    def optimize_database(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Optimiert die Datenbank (VACUUM, ANALYZE, Statistiken).
        
        Returns:
            Tuple (success, message, statistics)
        """
        try:
            self._log_info("Starte Datenbank-Optimierung...")
            
            size_before = os.path.getsize(self.db_path)
            
            conn = sqlite3.connect(self.db_path, timeout=30)
            cursor = conn.cursor()
            
            # Sammle Statistiken vor Optimierung
            cursor.execute("SELECT COUNT(*) FROM dokumente")
            doc_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM unclear_legacy")
            legacy_count = cursor.fetchone()[0]
            
            # ANALYZE - Aktualisiert Statistiken für Query-Optimizer
            self._log_info("Führe ANALYZE durch...")
            cursor.execute("ANALYZE")
            
            # VACUUM - Komprimiert DB und gibt Speicher frei
            self._log_info("Führe VACUUM durch...")
            cursor.execute("VACUUM")
            
            # Integritätsprüfung
            self._log_info("Prüfe Datenbank-Integrität...")
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            conn.close()
            
            size_after = os.path.getsize(self.db_path)
            space_saved = size_before - size_after
            
            stats = {
                "documents_count": doc_count,
                "unclear_legacy_count": legacy_count,
                "size_before": size_before,
                "size_after": size_after,
                "space_saved": space_saved,
                "space_saved_formatted": self._format_bytes(space_saved),
                "integrity_check": integrity_result,
                "optimized_at": datetime.now().isoformat()
            }
            
            success_msg = f"Datenbank optimiert: {self._format_bytes(space_saved)} freigegeben"
            self._log_info(success_msg)
            
            return True, success_msg, stats
            
        except Exception as e:
            error_msg = f"Optimierung fehlgeschlagen: {type(e).__name__}: {e}"
            self._log_error(error_msg)
            return False, error_msg, {}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Führt einen umfassenden Datenbank-Health-Check durch.
        
        Returns:
            Health-Status mit Details
        """
        health = {
            "timestamp": datetime.now().isoformat(),
            "healthy": True,
            "warnings": [],
            "errors": [],
            "statistics": {}
        }
        
        try:
            # Datei-Existenz
            if not os.path.exists(self.db_path):
                health["healthy"] = False
                health["errors"].append("Datenbank-Datei nicht gefunden")
                return health
            
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Integrität
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            health["statistics"]["integrity"] = integrity
            if integrity != "ok":
                health["healthy"] = False
                health["errors"].append(f"Integritätsprüfung fehlgeschlagen: {integrity}")
            
            # Datenbankgröße
            db_size = os.path.getsize(self.db_path)
            health["statistics"]["size"] = db_size
            health["statistics"]["size_formatted"] = self._format_bytes(db_size)
            
            # Große Datenbanken warnen
            if db_size > 1024 * 1024 * 1024:  # > 1GB
                health["warnings"].append(f"Datenbank sehr groß: {self._format_bytes(db_size)}")
            
            # Anzahl Dokumente
            cursor.execute("SELECT COUNT(*) FROM dokumente")
            doc_count = cursor.fetchone()[0]
            health["statistics"]["documents"] = doc_count
            
            cursor.execute("SELECT COUNT(*) FROM unclear_legacy WHERE status='offen'")
            open_legacy = cursor.fetchone()[0]
            health["statistics"]["open_legacy"] = open_legacy
            
            # Warnung bei vielen offenen Legacy-Aufträgen
            if open_legacy > 100:
                health["warnings"].append(f"{open_legacy} offene Legacy-Aufträge benötigen Zuordnung")
            
            # Prüfe Indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
            indexes = cursor.fetchall()
            health["statistics"]["indexes"] = len(indexes)
            
            if len(indexes) < 10:
                health["warnings"].append(f"Nur {len(indexes)} Indexes gefunden (erwartet: ~15)")
            
            # Letztes Backup prüfen
            backups = self.list_backups()
            if backups:
                last_backup = backups[0]
                age_days = last_backup["age_days"]
                health["statistics"]["last_backup_days"] = age_days
                
                if age_days > 7:
                    health["warnings"].append(f"Letztes Backup ist {age_days} Tage alt")
            else:
                health["warnings"].append("Kein Backup vorhanden")
            
            # WAL-Modus prüfen
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            health["statistics"]["journal_mode"] = journal_mode
            
            if journal_mode != "wal":
                health["warnings"].append(f"Journal-Mode ist '{journal_mode}' (empfohlen: 'wal')")
            
            conn.close()
            
            self._log_info(f"Health-Check abgeschlossen: {'Gesund' if health['healthy'] else 'Probleme gefunden'}")
            
        except Exception as e:
            health["healthy"] = False
            health["errors"].append(f"Health-Check Fehler: {type(e).__name__}: {e}")
        
        return health
    
    def cleanup_old_entries(self, days: int = 365) -> Tuple[bool, str, int]:
        """
        Löscht sehr alte Einträge (Optional - nur wenn gewünscht).
        
        Args:
            days: Einträge älter als X Tage löschen
            
        Returns:
            Tuple (success, message, deleted_count)
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Zähle zu löschende Einträge
            cursor.execute("""
                SELECT COUNT(*) FROM dokumente 
                WHERE created_at < ? AND status != 'archiviert'
            """, (cutoff_date,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                conn.close()
                return True, "Keine alten Einträge zum Löschen gefunden", 0
            
            # Erstelle Backup vor Löschung
            self.create_backup(reason="before_cleanup")
            
            # Lösche alte Einträge
            cursor.execute("""
                DELETE FROM dokumente 
                WHERE created_at < ? AND status != 'archiviert'
            """, (cutoff_date,))
            
            conn.commit()
            conn.close()
            
            success_msg = f"{count} Einträge älter als {days} Tage gelöscht"
            self._log_info(success_msg)
            
            return True, success_msg, count
            
        except Exception as e:
            error_msg = f"Cleanup fehlgeschlagen: {type(e).__name__}: {e}"
            self._log_error(error_msg)
            return False, error_msg, 0
    
    @staticmethod
    def _format_bytes(bytes_size: int) -> str:
        """Formatiert Byte-Größe human-readable."""
        size_float = float(bytes_size)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_float < 1024.0:
                return f"{size_float:.2f} {unit}"
            size_float /= 1024.0
        return f"{size_float:.2f} TB"

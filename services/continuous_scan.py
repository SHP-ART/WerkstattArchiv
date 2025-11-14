"""
Continuous Scan Service für WerkstattArchiv.
Scannt kontinuierlich den Eingangsordner und verarbeitet Dateien nacheinander.
"""

import os
import time
import threading
from typing import Callable, List, Set
from pathlib import Path


class ContinuousScanService:
    """
    Service für kontinuierliches Scannen und Verarbeiten von Dokumenten.
    
    Workflow:
    1. Scanne Eingangsordner
    2. Verarbeite jede Datei einzeln
    3. Warte kurz
    4. Scanne erneut
    5. Wiederhole endlos
    """
    
    def __init__(
        self, 
        watch_directory: str, 
        callback: Callable[[str], None],
        scan_interval: float = 5.0,
        supported_extensions: tuple = (".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp")
    ):
        """
        Initialisiert den Continuous Scan Service.
        
        Args:
            watch_directory: Zu überwachender Ordner
            callback: Funktion die für jede Datei aufgerufen wird
            scan_interval: Wartezeit zwischen Scans in Sekunden (Standard: 5)
            supported_extensions: Tuple mit unterstützten Dateiendungen
        """
        self.watch_directory = watch_directory
        self.callback = callback
        self.scan_interval = scan_interval
        self.supported_extensions = supported_extensions
        
        self.is_running = False
        self.scan_thread: threading.Thread = None
        self.processed_files: Set[str] = set()  # Cache für bereits verarbeitete Dateien (in aktueller Session)
        self.current_file: str = None
        
        # Statistiken
        self.total_scans = 0
        self.total_files_processed = 0
    
    def start(self) -> bool:
        """
        Startet das kontinuierliche Scannen.
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if self.is_running:
            print("⚠️  Continuous Scan läuft bereits!")
            return False
        
        if not os.path.exists(self.watch_directory):
            print(f"❌ Ordner existiert nicht: {self.watch_directory}")
            return False
        
        try:
            self.is_running = True
            self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
            self.scan_thread.start()
            
            print(f"✅ Continuous Scan gestartet: {self.watch_directory}")
            print(f"   Scan-Intervall: {self.scan_interval}s")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Starten: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Stoppt das kontinuierliche Scannen.
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not self.is_running:
            print("⚠️  Continuous Scan läuft nicht!")
            return False
        
        try:
            self.is_running = False
            
            # Warte auf Thread (max 10 Sekunden)
            if self.scan_thread and self.scan_thread.is_alive():
                self.scan_thread.join(timeout=10.0)
            
            print("✅ Continuous Scan gestoppt")
            print(f"   Statistik: {self.total_scans} Scans, {self.total_files_processed} Dateien verarbeitet")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Stoppen: {e}")
            return False
    
    def _scan_loop(self):
        """Hauptschleife für kontinuierliches Scannen."""
        print("🔄 Scan-Schleife gestartet...")
        
        while self.is_running:
            try:
                # Scanne Ordner
                files_found = self._scan_directory()
                self.total_scans += 1
                
                if files_found:
                    print(f"\n📊 Scan #{self.total_scans}: {len(files_found)} Datei(en) gefunden")
                    
                    # Verarbeite jede Datei einzeln
                    for file_path in files_found:
                        if not self.is_running:
                            break
                        
                        self._process_file(file_path)
                    
                    print(f"✅ Scan #{self.total_scans} abgeschlossen\n")
                
                # Warte vor nächstem Scan
                if self.is_running:
                    time.sleep(self.scan_interval)
                    
            except Exception as e:
                print(f"❌ Fehler in Scan-Schleife: {e}")
                time.sleep(self.scan_interval)  # Warte auch bei Fehler
    
    def _scan_directory(self) -> List[str]:
        """
        Scannt den Ordner nach neuen Dokumenten.
        
        Returns:
            Liste mit Pfaden zu neuen Dateien
        """
        new_files = []
        
        try:
            if not os.path.exists(self.watch_directory):
                return new_files
            
            # Scanne alle Dateien im Ordner
            for entry in os.scandir(self.watch_directory):
                if not entry.is_file():
                    continue
                
                file_path = entry.path
                
                # Prüfe Dateiendung
                if not file_path.lower().endswith(self.supported_extensions):
                    continue
                
                # Prüfe ob bereits verarbeitet (in aktueller Session)
                if file_path in self.processed_files:
                    continue
                
                # Prüfe ob Datei vollständig (nicht schreibgeschützt)
                if not self._is_file_ready(file_path):
                    continue
                
                new_files.append(file_path)
            
            # Sortiere nach Änderungsdatum (älteste zuerst)
            new_files.sort(key=lambda f: os.path.getmtime(f))
            
        except Exception as e:
            print(f"❌ Fehler beim Scannen: {e}")
        
        return new_files
    
    def _is_file_ready(self, file_path: str) -> bool:
        """
        Prüft ob Datei vollständig und lesbar ist.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            True wenn Datei bereit, sonst False
        """
        try:
            # Prüfe ob Datei existiert
            if not os.path.exists(file_path):
                return False
            
            # Prüfe ob Datei größer als 0 Bytes
            if os.path.getsize(file_path) == 0:
                return False
            
            # Prüfe ob Datei lesbar (nicht locked)
            with open(file_path, 'rb') as f:
                f.read(1)  # Teste Lesezugriff
            
            return True
            
        except (IOError, PermissionError, OSError):
            return False
    
    def _process_file(self, file_path: str):
        """
        Verarbeitet eine einzelne Datei.
        
        Args:
            file_path: Pfad zur Datei
        """
        filename = os.path.basename(file_path)
        self.current_file = filename
        
        try:
            print(f"🔄 Verarbeite: {filename}")
            
            # Callback aufrufen
            self.callback(file_path)
            
            # Zu verarbeiteten Dateien hinzufügen
            self.processed_files.add(file_path)
            self.total_files_processed += 1
            
            print(f"✅ Fertig: {filename}")
            
        except Exception as e:
            print(f"❌ Fehler beim Verarbeiten von {filename}: {e}")
            # Datei trotzdem als verarbeitet markieren (verhindert Endlosschleife)
            self.processed_files.add(file_path)
        
        finally:
            self.current_file = None
    
    def get_status(self) -> dict:
        """
        Gibt den aktuellen Status zurück.
        
        Returns:
            Dictionary mit Status-Informationen
        """
        return {
            "is_running": self.is_running,
            "watch_directory": self.watch_directory,
            "scan_interval": self.scan_interval,
            "total_scans": self.total_scans,
            "total_files_processed": self.total_files_processed,
            "current_file": self.current_file,
            "processed_count": len(self.processed_files)
        }
    
    def reset_processed_cache(self):
        """
        Löscht den Cache verarbeiteter Dateien.
        Danach werden alle Dateien im Ordner erneut verarbeitet.
        """
        count = len(self.processed_files)
        self.processed_files.clear()
        print(f"🔄 Cache zurückgesetzt: {count} Einträge gelöscht")

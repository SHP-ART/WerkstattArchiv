"""
Watchdog-Service für WerkstattArchiv.
Überwacht den Eingangsordner automatisch auf neue Dokumente.
"""

import os
import time
import threading
from typing import Dict, Any, Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class DocumentHandler(FileSystemEventHandler):
    """Event-Handler für neue Dokumente im Eingangsordner."""
    
    def __init__(self, callback: Callable[[str], None], supported_extensions: tuple = (".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
        """
        Initialisiert den Document-Handler.
        
        Args:
            callback: Funktion die aufgerufen wird wenn ein neues Dokument erkannt wird (erhält Dateipfad)
            supported_extensions: Tuple mit unterstützten Dateiendungen
        """
        super().__init__()
        self.callback = callback
        self.supported_extensions = supported_extensions
        self.processing_files = set()  # Verhindert doppelte Verarbeitung
        self.cooldown_time = 2.0  # Sekunden Wartezeit nach Dateierstellung
    
    def on_created(self, event: FileSystemEvent):
        """
        Wird aufgerufen wenn eine neue Datei erstellt wird.
        
        Args:
            event: FileSystemEvent mit Dateiinformationen
        """
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Nur unterstützte Dateitypen verarbeiten
        if not file_path.lower().endswith(self.supported_extensions):
            return
        
        # Prüfen ob Datei bereits in Verarbeitung
        if file_path in self.processing_files:
            return
        
        # Zu Verarbeitungsliste hinzufügen
        self.processing_files.add(file_path)
        
        # In separatem Thread verarbeiten (mit Verzögerung für Datei-Upload-Abschluss)
        thread = threading.Thread(target=self._process_with_delay, args=(file_path,))
        thread.daemon = True
        thread.start()
    
    def on_modified(self, event: FileSystemEvent):
        """
        Wird aufgerufen wenn eine Datei modifiziert wird.
        Ignoriert, da wir nur neue Dateien verarbeiten wollen.
        """
        pass
    
    def _process_with_delay(self, file_path: str):
        """
        Verarbeitet Datei mit Verzögerung (wartet bis Upload abgeschlossen).
        
        Args:
            file_path: Pfad zur Datei
        """
        try:
            # Warten bis Datei vollständig geschrieben wurde
            time.sleep(self.cooldown_time)
            
            # Prüfen ob Datei noch existiert und vollständig ist
            if not os.path.exists(file_path):
                print(f"⚠️  Datei existiert nicht mehr: {file_path}")
                return
            
            # Prüfen ob Datei vollständig (versuche zu öffnen)
            try:
                with open(file_path, 'rb') as f:
                    f.read(1)  # Teste Lesezugriff
            except (IOError, PermissionError) as e:
                print(f"⚠️  Datei noch nicht bereit: {file_path} - {e}")
                time.sleep(1)  # Zusätzliche Wartezeit
            
            # Callback aufrufen
            print(f"📄 Neue Datei erkannt: {os.path.basename(file_path)}")
            self.callback(file_path)
            
        except Exception as e:
            print(f"❌ Fehler beim Verarbeiten von {file_path}: {e}")
        
        finally:
            # Aus Verarbeitungsliste entfernen
            self.processing_files.discard(file_path)


class WatchdogService:
    """Service für automatische Ordnerüberwachung."""
    
    def __init__(self, watch_directory: str, callback: Callable[[str], None]):
        """
        Initialisiert den Watchdog-Service.
        
        Args:
            watch_directory: Zu überwachender Ordner
            callback: Funktion die bei neuen Dateien aufgerufen wird
        """
        self.watch_directory = watch_directory
        self.callback = callback
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[DocumentHandler] = None
        self.is_watching = False
    
    def start(self) -> bool:
        """
        Startet die Ordnerüberwachung.
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if self.is_watching:
            print("⚠️  Watchdog läuft bereits!")
            return False
        
        if not os.path.exists(self.watch_directory):
            print(f"❌ Ordner existiert nicht: {self.watch_directory}")
            return False
        
        try:
            # Event-Handler erstellen
            self.event_handler = DocumentHandler(self.callback)
            
            # Observer erstellen und starten
            self.observer = Observer()
            self.observer.schedule(self.event_handler, self.watch_directory, recursive=False)
            self.observer.start()
            
            self.is_watching = True
            print(f"✅ Ordnerüberwachung gestartet: {self.watch_directory}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Starten der Überwachung: {e}")
            self.is_watching = False
            return False
    
    def stop(self) -> bool:
        """
        Stoppt die Ordnerüberwachung.
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not self.is_watching or not self.observer:
            print("⚠️  Watchdog läuft nicht!")
            return False
        
        try:
            self.observer.stop()
            self.observer.join(timeout=5.0)
            self.is_watching = False
            self.observer = None
            self.event_handler = None
            print("✅ Ordnerüberwachung gestoppt")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Stoppen der Überwachung: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Gibt den Status der Überwachung zurück.
        
        Returns:
            Dictionary mit Status-Informationen
        """
        return {
            "is_watching": self.is_watching,
            "watch_directory": self.watch_directory,
            "observer_alive": self.observer.is_alive() if self.observer else False,
        }

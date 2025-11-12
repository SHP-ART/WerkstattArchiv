"""
Update-Manager für WerkstattArchiv.
Prüft auf neue Versionen und installiert Updates von GitHub.
"""

import os
import sys
import json
import urllib.request
import urllib.error
import zipfile
import shutil
import tempfile
import ssl
from typing import Optional, Tuple, Dict
from pathlib import Path


class UpdateManager:
    """Verwaltet Updates von GitHub."""
    
    # GitHub Repository Info
    GITHUB_USER = "SHP-ART"
    GITHUB_REPO = "WerkstattArchiv"
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
    
    def __init__(self, current_version: str):
        """
        Initialisiert den UpdateManager.
        
        Args:
            current_version: Aktuelle Version (z.B. "0.8.0")
        """
        self.current_version = current_version
        self.app_dir = Path(__file__).parent.parent.absolute()
    
    def check_for_updates(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Prüft ob eine neue Version verfügbar ist.
        
        Returns:
            Tuple (update_available, latest_version, download_url):
            - update_available: True wenn Update verfügbar
            - latest_version: Neueste Version oder None
            - download_url: Download-URL oder None
        """
        try:
            # SSL-Kontext für macOS erstellen (ignoriert Zertifikatsprüfung)
            ssl_context = ssl._create_unverified_context()
            
            # GitHub API abfragen
            request = urllib.request.Request(
                self.GITHUB_API_URL,
                headers={'User-Agent': 'WerkstattArchiv-Updater'}
            )
            
            with urllib.request.urlopen(request, timeout=10, context=ssl_context) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Version aus Tag extrahieren (z.B. "v0.8.0" -> "0.8.0")
            latest_version = data.get('tag_name', '').lstrip('v')
            
            if not latest_version:
                return False, None, None
            
            # Versions-Vergleich
            update_available = self._compare_versions(self.current_version, latest_version)
            
            # Download-URL für Source Code ZIP
            download_url = data.get('zipball_url')
            
            return update_available, latest_version, download_url
            
        except urllib.error.URLError as e:
            print(f"Fehler beim Prüfen auf Updates: {e}")
            return False, None, None
        except Exception as e:
            print(f"Unerwarteter Fehler beim Update-Check: {e}")
            return False, None, None
    
    def _compare_versions(self, current: str, latest: str) -> bool:
        """
        Vergleicht zwei Versionen.
        
        Args:
            current: Aktuelle Version (z.B. "0.8.0")
            latest: Neueste Version (z.B. "0.9.0")
            
        Returns:
            True wenn latest neuer als current
        """
        try:
            # Versionen in Zahlen umwandeln
            current_parts = [int(x) for x in current.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]
            
            # Auffüllen falls unterschiedliche Länge
            while len(current_parts) < len(latest_parts):
                current_parts.append(0)
            while len(latest_parts) < len(current_parts):
                latest_parts.append(0)
            
            # Vergleichen
            for i in range(len(current_parts)):
                if latest_parts[i] > current_parts[i]:
                    return True
                elif latest_parts[i] < current_parts[i]:
                    return False
            
            return False  # Versionen sind gleich
            
        except Exception as e:
            print(f"Fehler beim Versions-Vergleich: {e}")
            return False
    
    def get_release_notes(self) -> Optional[str]:
        """
        Holt die Release Notes der neuesten Version.
        
        Returns:
            Release Notes als String oder None
        """
        try:
            ssl_context = ssl._create_unverified_context()
            
            request = urllib.request.Request(
                self.GITHUB_API_URL,
                headers={'User-Agent': 'WerkstattArchiv-Updater'}
            )
            
            with urllib.request.urlopen(request, timeout=10, context=ssl_context) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            return data.get('body', 'Keine Release Notes verfügbar.')
            
        except Exception as e:
            print(f"Fehler beim Laden der Release Notes: {e}")
            return None
    
    def download_and_install_update(self, download_url: str, 
                                    progress_callback=None) -> Tuple[bool, str]:
        """
        Lädt Update herunter und installiert es.
        
        Args:
            download_url: URL zum Download
            progress_callback: Optional callback für Fortschritt (0-100)
            
        Returns:
            Tuple (success, message)
        """
        temp_dir = None
        
        try:
            # Temporäres Verzeichnis erstellen
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "update.zip")
            
            # Download
            if progress_callback:
                progress_callback(10, "Lade Update herunter...")
            
            ssl_context = ssl._create_unverified_context()
            
            request = urllib.request.Request(
                download_url,
                headers={'User-Agent': 'WerkstattArchiv-Updater'}
            )
            
            with urllib.request.urlopen(request, timeout=30, context=ssl_context) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(zip_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            percent = 10 + int((downloaded / total_size) * 40)
                            progress_callback(percent, f"Heruntergeladen: {downloaded // 1024} KB")
            
            if progress_callback:
                progress_callback(50, "Entpacke Update...")
            
            # ZIP entpacken
            extract_dir = os.path.join(temp_dir, "extracted")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Finde den Hauptordner im ZIP (GitHub erstellt einen Unterordner)
            extracted_items = os.listdir(extract_dir)
            if len(extracted_items) == 1 and os.path.isdir(os.path.join(extract_dir, extracted_items[0])):
                source_dir = os.path.join(extract_dir, extracted_items[0])
            else:
                source_dir = extract_dir
            
            if progress_callback:
                progress_callback(60, "Erstelle Backup...")
            
            # Backup erstellen
            backup_dir = os.path.join(self.app_dir, "backup_before_update")
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            
            # Wichtige Dateien sichern
            files_to_backup = ['config.json', 'werkstatt_index.db', 'patterns.json']
            os.makedirs(backup_dir, exist_ok=True)
            
            for file in files_to_backup:
                src = os.path.join(self.app_dir, file)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(backup_dir, file))
            
            if progress_callback:
                progress_callback(75, "Installiere Update...")
            
            # Update installieren (nur Python-Dateien und Dokumentation)
            files_to_update = [
                'main.py',
                'version.py',
                'requirements.txt',
                'README.md',
                'services/',
                'ui/',
            ]
            
            for item in files_to_update:
                src_path = os.path.join(source_dir, item)
                dst_path = os.path.join(self.app_dir, item)
                
                if not os.path.exists(src_path):
                    continue
                
                if os.path.isfile(src_path):
                    # Datei kopieren
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    shutil.copy2(src_path, dst_path)
                elif os.path.isdir(src_path):
                    # Verzeichnis kopieren
                    if os.path.exists(dst_path):
                        # Alte .py Dateien löschen
                        for root, dirs, files in os.walk(dst_path):
                            for file in files:
                                if file.endswith('.py'):
                                    os.remove(os.path.join(root, file))
                    
                    # Neue Dateien kopieren
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            
            if progress_callback:
                progress_callback(95, "Räume auf...")
            
            # Aufräumen
            shutil.rmtree(temp_dir)
            
            if progress_callback:
                progress_callback(100, "Update abgeschlossen!")
            
            message = (
                "✓ Update erfolgreich installiert!\n\n"
                "Die Anwendung wird jetzt neu gestartet.\n\n"
                "Backup wurde erstellt in:\n"
                f"{backup_dir}"
            )
            
            return True, message
            
        except Exception as e:
            # Aufräumen bei Fehler
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            return False, f"❌ Fehler beim Update:\n{str(e)}"
    
    def restart_application(self):
        """Startet die Anwendung neu (plattformübergreifend)."""
        import subprocess
        import platform
        
        python = sys.executable
        script = os.path.abspath(sys.argv[0])
        
        # Windows benötigt spezielles Handling
        if platform.system() == 'Windows':
            # Erstelle Batch-Datei für verzögerten Neustart
            batch_content = f"""@echo off
timeout /t 2 /nobreak >nul
start "" "{python}" "{script}"
exit
"""
            batch_file = os.path.join(tempfile.gettempdir(), "werkstatt_restart.bat")
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            
            # Starte Batch-Datei und beende aktuelle Anwendung
            # CREATE_NEW_CONSOLE = 0x00000010, DETACHED_PROCESS = 0x00000008
            subprocess.Popen(
                [batch_file],
                shell=True,
                creationflags=0x00000010 | 0x00000008,  # Windows-spezifische Flags
                close_fds=True
            )
        else:
            # macOS/Linux: Nutze nohup für Hintergrund-Prozess
            subprocess.Popen(
                [python, script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True
            )
        
        # Beende aktuelle Anwendung
        sys.exit(0)

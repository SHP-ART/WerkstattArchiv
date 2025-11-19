"""
Update-Manager für WerkstattArchiv.
Prüft auf neue Versionen und installiert Updates von GitHub.
Windows-optimiert mit automatischem Config-Restore bei Fehlern.
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
from datetime import datetime


class UpdateManager:
    """Verwaltet Updates von GitHub."""
    
    # GitHub Repository Info
    GITHUB_USER = "SHP-ART"
    GITHUB_REPO = "WerkstattArchiv"
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
    GITHUB_COMMITS_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/commits/main"
    
    def __init__(self, current_version: str):
        """
        Initialisiert den UpdateManager.
        
        Args:
            current_version: Aktuelle Version (z.B. "0.8.0")
        """
        self.current_version = current_version
        self.app_dir = Path(__file__).parent.parent.absolute()
        self.use_commit_check = True  # Prüfe Commits statt Releases
    
    def check_for_updates(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Prüft ob eine neue Version verfügbar ist.
        
        Returns:
            Tuple (update_available, latest_version, download_url):
            - update_available: True wenn Update verfügbar
            - latest_version: Neueste Version oder None
            - download_url: Download-URL oder None
        """
        if self.use_commit_check:
            return self._check_commits()
        else:
            return self._check_releases()
    
    def _check_commits(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Prüft ob neue Commits auf main verfügbar sind.
        
        Returns:
            Tuple (update_available, commit_info, download_url)
        """
        from services.logger import log_info, log_error
        
        try:
            log_info("Update-Check: Prüfe auf neue Commits...")
            
            # Hole aktuellen lokalen Commit-Hash
            local_commit = self._get_local_commit_hash()
            log_info(f"Lokaler Commit: {local_commit or 'Unbekannt'}")
            
            # Hole neuesten Remote Commit
            log_info(f"Rufe Remote-Commits ab: {self.GITHUB_COMMITS_URL}")
            ssl_context = ssl._create_unverified_context()
            request = urllib.request.Request(
                self.GITHUB_COMMITS_URL,
                headers={'User-Agent': 'WerkstattArchiv-Updater'}
            )
            
            with urllib.request.urlopen(request, timeout=10, context=ssl_context) as response:
                status_code = response.getcode()
                log_info(f"HTTP Status: {status_code}")
                data = json.loads(response.read().decode('utf-8'))
            
            remote_commit = data.get('sha', '')[:7]  # Kurze Version
            commit_message = data.get('commit', {}).get('message', '').split('\n')[0]
            commit_date = data.get('commit', {}).get('author', {}).get('date', '')
            
            log_info(f"Remote Commit: {remote_commit} - {commit_message}")
            log_info(f"Commit Datum: {commit_date}")
            
            if not remote_commit:
                log_error("Kein Remote-Commit gefunden in API-Response")
                return False, None, None
            
            # Prüfe ob Remote neuer ist
            update_available = (local_commit != remote_commit) if local_commit else True
            
            log_info(f"Update verfügbar: {update_available}")
            
            # Info-String erstellen
            commit_info = f"{remote_commit} - {commit_message}"
            
            # Download-URL für main branch ZIP
            download_url = f"https://github.com/{self.GITHUB_USER}/{self.GITHUB_REPO}/archive/refs/heads/main.zip"
            
            return update_available, commit_info, download_url
            
        except urllib.error.URLError as e:
            error_msg = f"Netzwerkfehler beim Update-Check: {e.reason if hasattr(e, 'reason') else e}"
            print(f"❌ {error_msg}")
            log_error(error_msg)
            # Fallback zu Release-Check
            return self._check_releases()
        except Exception as e:
            error_msg = f"Fehler beim Prüfen auf Updates (Commits): {type(e).__name__}: {e}"
            print(f"❌ {error_msg}")
            log_error(error_msg)
            import traceback
            traceback.print_exc()
            # Fallback zu Release-Check
            return self._check_releases()
    
    def _get_local_commit_hash(self) -> Optional[str]:
        """
        Holt den aktuellen lokalen Git-Commit-Hash.
        
        Returns:
            Commit-Hash (kurz, 7 Zeichen) oder None
        """
        try:
            import subprocess
            
            # Versuche git rev-parse HEAD
            result = subprocess.run(
                ['git', 'rev-parse', '--short=7', 'HEAD'],
                cwd=self.app_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            
            return None
            
        except Exception as e:
            print(f"Fehler beim Holen des lokalen Commits: {e}")
            return None
    
    def _check_releases(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Prüft ob ein neuer Release verfügbar ist (alte Methode).
        
        Returns:
            Tuple (update_available, latest_version, download_url)
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
        backup_dir = None
        
        try:
            # Temporäres Verzeichnis erstellen (Windows-safe)
            temp_dir = tempfile.mkdtemp(prefix="werkstatt_update_")
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
                progress_callback(50, "Verifiziere Download...")

            # Download-Integrität prüfen (Issue: No download integrity)
            if not os.path.exists(zip_path):
                raise RuntimeError("Download-Datei nicht gefunden")

            if os.path.getsize(zip_path) == 0:
                raise RuntimeError("Download-Datei ist leer (0 Bytes)")

            # ZIP-Datei auf Validität prüfen
            try:
                with zipfile.ZipFile(zip_path, 'r') as test_zip:
                    # Teste ob ZIP korrekt ist (ohne zu entpacken)
                    test_result = test_zip.testzip()
                    if test_result is not None:
                        raise RuntimeError(f"ZIP-Datei beschädigt: {test_result}")
                    print(f"✓ ZIP-Datei Größe: {os.path.getsize(zip_path) // 1024} KB")
                    print(f"✓ ZIP-Integrität verifiziert")
            except zipfile.BadZipFile as e:
                raise RuntimeError(f"ZIP-Datei ungültig: {e}")

            if progress_callback:
                progress_callback(55, "Entpacke Update...")

            # ZIP entpacken
            extract_dir = os.path.join(temp_dir, "extracted")
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                print(f"✓ ZIP entpackt nach: {extract_dir}")
            except Exception as e:
                raise RuntimeError(f"Fehler beim Entpacken: {e}")
            
            # Finde den Hauptordner im ZIP (GitHub erstellt einen Unterordner)
            extracted_items = os.listdir(extract_dir)
            if len(extracted_items) == 1 and os.path.isdir(os.path.join(extract_dir, extracted_items[0])):
                source_dir = os.path.join(extract_dir, extracted_items[0])
            else:
                source_dir = extract_dir
            
            if progress_callback:
                progress_callback(60, "Erstelle Backup...")
            
            # Backup erstellen (mit Zeitstempel für mehrere Backups)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(self.app_dir, f"backup_before_update_{timestamp}")
            
            # Wichtige Dateien und Verzeichnisse sichern
            files_to_backup = [
                'config.json',
                'werkstatt_index.db', 
                'patterns.json',
                'data/vehicles.csv',
                'data/config_backup.json'  # Zentrales Backup
            ]
            dirs_to_backup = ['data']  # Komplettes data-Verzeichnis
            
            os.makedirs(backup_dir, exist_ok=True)
            
            # Dateien sichern
            for file in files_to_backup:
                src = os.path.join(self.app_dir, file)
                if os.path.exists(src):
                    # Erstelle Unterverzeichnisse im Backup falls nötig
                    backup_file_path = os.path.join(backup_dir, file)
                    os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
                    shutil.copy2(src, backup_file_path)
            
            # Verzeichnisse sichern
            for dir_name in dirs_to_backup:
                src_dir = os.path.join(self.app_dir, dir_name)
                if os.path.exists(src_dir) and os.path.isdir(src_dir):
                    dst_dir = os.path.join(backup_dir, dir_name)
                    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
            
            if progress_callback:
                progress_callback(75, "Installiere Update...")
            
            # Update installieren (nur Code-Dateien, KEINE Daten überschreiben)
            files_to_update = [
                'main.py',
                'version.py',
                'requirements.txt',
                'README.md',
                'WINDOWS_INSTALLATION.md',
                'services/',
                'ui/',
                'core/',
                'docs/'
            ]
            
            # WICHTIG: Diese Dateien NIEMALS überschreiben
            files_to_preserve = [
                'config.json',
                'werkstatt_index.db',
                'patterns.json',
                'data/',  # Komplettes data-Verzeichnis
                'kunden.csv',
                'logs/',
                'backups/'
            ]
            
            for item in files_to_update:
                src_path = os.path.join(source_dir, item)
                dst_path = os.path.join(self.app_dir, item)
                
                if not os.path.exists(src_path):
                    continue
                
                # Prüfe ob diese Datei/Ordner geschützt ist
                is_protected = any(
                    item.startswith(protected) or item == protected
                    for protected in files_to_preserve
                )
                
                if is_protected:
                    continue  # Geschützte Dateien überspringen
                
                if os.path.isfile(src_path):
                    # Datei kopieren (Windows-safe)
                    try:
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        # Unter Windows: Prüfe ob Datei beschreibbar ist
                        if os.path.exists(dst_path):
                            os.chmod(dst_path, 0o666)  # Schreibrechte setzen
                        shutil.copy2(src_path, dst_path)
                    except PermissionError:
                        # Fallback: Umbenennen und dann kopieren
                        if os.path.exists(dst_path):
                            os.rename(dst_path, f"{dst_path}.old")
                        shutil.copy2(src_path, dst_path)
                        
                elif os.path.isdir(src_path):
                    # Verzeichnis kopieren (Windows-safe)
                    try:
                        if os.path.exists(dst_path):
                            # Alte .py Dateien löschen (mit Error-Handling)
                            for root, dirs, files in os.walk(dst_path):
                                for file in files:
                                    if file.endswith('.py'):
                                        file_path = os.path.join(root, file)
                                        try:
                                            os.chmod(file_path, 0o666)
                                            os.remove(file_path)
                                        except (PermissionError, OSError):
                                            # Datei wird beim nächsten Start überschrieben
                                            pass
                        
                        # Neue Dateien kopieren
                        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                    except Exception as e:
                        print(f"Warnung beim Kopieren von {item}: {e}")
            
            if progress_callback:
                progress_callback(95, "Räume auf...")

            # Aufräumen mit besserem Logging (Issue: Silent cleanup failures)
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=False)
                    print(f"✓ Temporäres Verzeichnis gelöscht: {temp_dir}")
                except PermissionError as e:
                    print(f"⚠️  Warnung: Konnte temp-Verzeichnis nicht vollständig löschen (Permissions): {e}")
                    # Versuche mit Force-Löschung auf Windows
                    try:
                        import stat
                        def handle_remove_readonly(func, path, exc):
                            os.chmod(path, stat.S_IWRITE)
                            func(path)
                        shutil.rmtree(temp_dir, onerror=handle_remove_readonly)
                        print(f"✓ Temp-Verzeichnis mit Force-Löschung erfolgreich gelöscht")
                    except Exception as e2:
                        print(f"⚠️  Konnte Temp-Verzeichnis nicht löschen (wird später gelöscht): {e2}")
                except Exception as e:
                    print(f"⚠️  Fehler beim Löschen des Temp-Verzeichnisses: {e}")
            
            if progress_callback:
                progress_callback(100, "Update abgeschlossen!")
            
            message = (
                "✓ Update erfolgreich installiert!\n\n"
                "Die Anwendung wird jetzt neu gestartet.\n\n"
                "📦 Backup wurde erstellt in:\n"
                f"{backup_dir}\n\n"
                "💡 Bei Problemen können Sie die Dateien aus dem Backup wiederherstellen."
            )
            
            return True, message
            
        except Exception as e:
            error_msg = str(e)
            
            # Bei Fehler: Versuche Einstellungen wiederherzustellen
            if backup_dir and os.path.exists(backup_dir):
                try:
                    # Stelle wichtige Konfigurationsdateien wieder her
                    config_backup = os.path.join(backup_dir, "config.json")
                    if os.path.exists(config_backup):
                        shutil.copy2(config_backup, os.path.join(self.app_dir, "config.json"))
                    
                    patterns_backup = os.path.join(backup_dir, "patterns.json")
                    if os.path.exists(patterns_backup):
                        shutil.copy2(patterns_backup, os.path.join(self.app_dir, "patterns.json"))
                    
                    # Prüfe ob zentrales Backup existiert
                    central_backup = os.path.join(backup_dir, "data", "config_backup.json")
                    if os.path.exists(central_backup):
                        target_dir = os.path.join(self.app_dir, "data")
                        os.makedirs(target_dir, exist_ok=True)
                        shutil.copy2(central_backup, os.path.join(target_dir, "config_backup.json"))
                    
                    error_msg += "\n\n✓ Einstellungen wurden automatisch wiederhergestellt."
                    
                except Exception as restore_error:
                    error_msg += f"\n\n⚠️ Konnte Einstellungen nicht wiederherstellen: {restore_error}"
                    error_msg += f"\n\n📦 Manuelles Backup verfügbar in:\n{backup_dir}"
            
            # Aufräumen bei Fehler mit besserer Fehlerbehandlung
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=False)
                    print(f"✓ Temp-Verzeichnis bei Fehler gelöscht: {temp_dir}")
                except Exception as cleanup_error:
                    print(f"⚠️  Konnte Temp-Verzeichnis bei Fehler nicht löschen: {cleanup_error}")
            
            return False, f"❌ Fehler beim Update:\n{error_msg}"
    
    def restart_application(self):
        """Startet die Anwendung neu (plattformübergreifend mit verbessertem Windows-Support)."""
        import subprocess
        import platform
        
        python = sys.executable
        script = os.path.abspath(sys.argv[0])
        
        # Windows benötigt spezielles Handling
        if platform.system() == 'Windows':
            # Erstelle Batch-Datei für verzögerten Neustart (mit Logging)
            batch_content = f"""@echo off
echo WerkstattArchiv Neustart...
echo Warte 3 Sekunden...
timeout /t 3 /nobreak >nul

echo Starte Anwendung neu...
cd /d "{os.path.dirname(script)}"
start "WerkstattArchiv" "{python}" "{script}"

if errorlevel 1 (
    echo Fehler beim Starten!
    echo Python: {python}
    echo Script: {script}
    pause
) else (
    echo Erfolgreich gestartet!
)

exit
"""
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_file = os.path.join(tempfile.gettempdir(), f"werkstatt_restart_{timestamp}.bat")
            
            try:
                with open(batch_file, 'w', encoding='utf-8') as f:
                    f.write(batch_content)
                
                # Starte Batch-Datei und beende aktuelle Anwendung
                # CREATE_NEW_CONSOLE = 0x00000010, DETACHED_PROCESS = 0x00000008
                subprocess.Popen(
                    ['cmd.exe', '/c', batch_file],
                    creationflags=0x00000010,  # Neue Konsole (für Debugging)
                    cwd=os.path.dirname(script),
                    close_fds=False  # Windows braucht dies manchmal
                )
            except Exception as e:
                print(f"Fehler beim Erstellen der Restart-Batch: {e}")
                # Fallback: Direkter Start ohne Verzögerung
                try:
                    subprocess.Popen([python, script], cwd=os.path.dirname(script))
                except Exception as e2:
                    print(f"Fallback-Start fehlgeschlagen: {e2}")
        else:
            # macOS/Linux: Nutze nohup für Hintergrund-Prozess
            try:
                subprocess.Popen(
                    [python, script],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=os.path.dirname(script),
                    close_fds=True
                )
            except Exception as e:
                print(f"Fehler beim Neustart: {e}")
        
        # Beende aktuelle Anwendung
        sys.exit(0)

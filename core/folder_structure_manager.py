"""
Folder Structure Manager
Verwaltet dynamische Ordnerstrukturen für PDF-Speicherung
"""

import os
import re
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


class FolderStructureManager:
    """Verwaltet konfigurierbare Ordnerstrukturen für Dokumenten-Speicherung."""
    
    # Vordefinierte Profile
    PROFILES = {
        "Standard": {
            "folder_template": "{kunde}/{jahr}/{typ}",
            "filename_template": "{datum}_{typ}_{auftrag}.pdf",
            "description": "Klassische Struktur: Kunde → Jahr → Typ"
        },
        "Chronologisch": {
            "folder_template": "{jahr}/{monat}/{kunde}/{typ}",
            "filename_template": "{datum}_{typ}_{auftrag}.pdf",
            "description": "Zeitbasiert: Jahr → Monat → Kunde → Typ"
        },
        "Nach Typ": {
            "folder_template": "{typ}/{jahr}/{kunde}",
            "filename_template": "{datum}_{auftrag}_{kunde}.pdf",
            "description": "Typ-fokussiert: Dokumenttyp → Jahr → Kunde"
        },
        "Nach Auftrag": {
            "folder_template": "{kunde}/{auftrag}",
            "filename_template": "{datum}_{typ}.pdf",
            "description": "Auftragsbezogen: Kunde → Auftragsnummer"
        },
        "Kompakt": {
            "folder_template": "{kunde}/{jahr}",
            "filename_template": "{datum}_{typ}_{auftrag}.pdf",
            "description": "Einfach: Kunde → Jahr (weniger Unterordner)"
        },
        "Detail": {
            "folder_template": "{kunde}/{jahr}/{monat}/{typ}/{auftrag}",
            "filename_template": "{datum}_{typ}.pdf",
            "description": "Detailliert: Maximale Verschachtelung"
        }
    }
    
    # Verfügbare Platzhalter mit Beschreibung
    PLACEHOLDERS = {
        "kunde": "Kundenname",
        "jahr": "Jahr (YYYY)",
        "monat": "Monat (MM oder Name)",
        "tag": "Tag (DD)",
        "datum": "Vollständiges Datum (YYYY-MM-DD)",
        "typ": "Dokumenttyp (z.B. Rechnung, Angebot)",
        "auftrag": "Auftragsnummer",
        "kfz": "KFZ-Kennzeichen",
        "fin": "Fahrzeug-Identifikationsnummer"
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialisiert den FolderStructureManager.
        
        Args:
            config: Konfiguration mit Struktur-Einstellungen
        """
        self.config = config or {}
        self.folder_template = self.config.get("folder_template", "{kunde}/{jahr}/{typ}")
        self.filename_template = self.config.get("filename_template", "{datum}_{typ}_{auftrag}.pdf")
        
        # Optionen
        self.replace_spaces = self.config.get("replace_spaces", True)
        self.remove_invalid_chars = self.config.get("remove_invalid_chars", True)
        self.use_month_names = self.config.get("use_month_names", False)
        self.max_name_length = self.config.get("max_name_length", 50)
        self.separator = self.config.get("separator", "_")
        
        # Monatsnamen
        self.month_names = [
            "01_Januar", "02_Februar", "03_Maerz", "04_April",
            "05_Mai", "06_Juni", "07_Juli", "08_August",
            "09_September", "10_Oktober", "11_November", "12_Dezember"
        ]
    
    def generate_path(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generiert Ordnerpfad und Dateinamen basierend auf Templates.
        
        Args:
            data: Dictionary mit Daten (kunde, jahr, typ, auftrag, etc.)
            
        Returns:
            Tuple[str, str]: (ordner_pfad, dateiname)
        """
        # Bereite Daten vor
        prepared_data = self._prepare_data(data)
        
        # Generiere Ordnerpfad
        folder_path = self._apply_template(self.folder_template, prepared_data)
        
        # Generiere Dateiname
        filename = self._apply_template(self.filename_template, prepared_data)
        
        # Bereinige Pfade
        folder_path = self._sanitize_path(folder_path)
        filename = self._sanitize_filename(filename)
        
        return folder_path, filename
    
    def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Bereitet Daten für Template-Ersetzung vor.
        
        Args:
            data: Rohdaten
            
        Returns:
            Dict mit vorbereiteten Strings
        """
        prepared = {}
        
        # Datum-basierte Felder
        datum = data.get("datum")
        if isinstance(datum, str):
            try:
                datum = datetime.strptime(datum, "%Y-%m-%d")
            except:
                datum = datetime.now()
        elif not isinstance(datum, datetime):
            datum = datetime.now()
        
        prepared["jahr"] = str(datum.year)
        prepared["tag"] = datum.strftime("%d")
        prepared["datum"] = datum.strftime("%Y-%m-%d")
        
        # Monat (Nummer oder Name)
        if self.use_month_names:
            prepared["monat"] = self.month_names[datum.month - 1]
        else:
            prepared["monat"] = datum.strftime("%m")
        
        # Andere Felder
        prepared["kunde"] = str(data.get("kunde", "Unbekannt"))
        prepared["typ"] = str(data.get("typ", "Dokument"))
        prepared["auftrag"] = str(data.get("auftrag", ""))
        prepared["kfz"] = str(data.get("kfz", ""))
        prepared["fin"] = str(data.get("fin", ""))
        
        return prepared
    
    def _apply_template(self, template: str, data: Dict[str, str]) -> str:
        """
        Wendet Template mit Platzhaltern an.
        
        Args:
            template: Template-String mit {platzhalter}
            data: Dictionary mit Werten
            
        Returns:
            String mit ersetzten Platzhaltern
        """
        result = template
        
        for key, value in data.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, value)
        
        return result
    
    def _sanitize_path(self, path: str) -> str:
        """
        Bereinigt Pfad von ungültigen Zeichen.
        
        Args:
            path: Roher Pfad
            
        Returns:
            Bereinigter Pfad
        """
        # Ersetze Leerzeichen
        if self.replace_spaces:
            path = path.replace(" ", self.separator)
        
        # Entferne ungültige Zeichen
        if self.remove_invalid_chars:
            # Windows/Mac/Linux ungültige Zeichen
            invalid_chars = r'[<>:"|?*]'
            path = re.sub(invalid_chars, "", path)
        
        # Kürze zu lange Segmente
        segments = path.split("/")
        segments = [seg[:self.max_name_length] if len(seg) > self.max_name_length else seg 
                   for seg in segments]
        
        return "/".join(segments)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Bereinigt Dateinamen von ungültigen Zeichen.
        
        Args:
            filename: Roher Dateiname
            
        Returns:
            Bereinigter Dateiname
        """
        # Ersetze Leerzeichen
        if self.replace_spaces:
            filename = filename.replace(" ", self.separator)
        
        # Entferne ungültige Zeichen
        if self.remove_invalid_chars:
            invalid_chars = r'[<>:"/\\|?*]'
            filename = re.sub(invalid_chars, "", filename)
        
        # Kürze zu lange Namen (behalte Extension)
        name, ext = os.path.splitext(filename)
        if len(name) > self.max_name_length:
            name = name[:self.max_name_length]
        
        return name + ext
    
    def preview(self, sample_data: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        """
        Generiert Vorschau-Beispiel.
        
        Args:
            sample_data: Beispieldaten (optional)
            
        Returns:
            Tuple[str, str]: (beispiel_pfad, beispiel_dateiname)
        """
        if sample_data is None:
            sample_data = {
                "kunde": "Mustermann GmbH",
                "datum": datetime.now(),
                "typ": "Rechnung",
                "auftrag": "A12345",
                "kfz": "B-MW-1234",
                "fin": "WBADT43452G123456"
            }
        
        return self.generate_path(sample_data)
    
    def validate_template(self, template: str) -> Tuple[bool, str]:
        """
        Validiert Template auf gültige Syntax.
        
        Args:
            template: Zu validierendes Template
            
        Returns:
            Tuple[bool, str]: (ist_gueltig, fehlermeldung)
        """
        # Finde alle Platzhalter
        placeholders = re.findall(r'\{(\w+)\}', template)
        
        # Prüfe auf unbekannte Platzhalter
        unknown = [p for p in placeholders if p not in self.PLACEHOLDERS]
        if unknown:
            return False, f"Unbekannte Platzhalter: {', '.join(unknown)}"
        
        # Prüfe auf ungültige Zeichen (außer Platzhalter)
        temp = template
        for p in placeholders:
            temp = temp.replace("{" + p + "}", "")
        
        if self.remove_invalid_chars:
            invalid_in_template = re.findall(r'[<>:"|?*]', temp)
            if invalid_in_template:
                return False, f"Ungültige Zeichen im Template: {', '.join(set(invalid_in_template))}"
        
        return True, ""
    
    def get_profile_list(self) -> List[str]:
        """Gibt Liste aller verfügbaren Profile zurück."""
        return list(self.PROFILES.keys())
    
    def load_profile(self, profile_name: str) -> bool:
        """
        Lädt vordefiniertes Profil.
        
        Args:
            profile_name: Name des Profils
            
        Returns:
            bool: True wenn erfolgreich geladen
        """
        if profile_name in self.PROFILES:
            profile = self.PROFILES[profile_name]
            self.folder_template = profile["folder_template"]
            self.filename_template = profile["filename_template"]
            return True
        return False
    
    def get_config(self) -> Dict[str, Any]:
        """
        Gibt aktuelle Konfiguration zurück.
        
        Returns:
            Dict mit Konfiguration
        """
        return {
            "folder_template": self.folder_template,
            "filename_template": self.filename_template,
            "replace_spaces": self.replace_spaces,
            "remove_invalid_chars": self.remove_invalid_chars,
            "use_month_names": self.use_month_names,
            "max_name_length": self.max_name_length,
            "separator": self.separator
        }
    
    def update_config(self, config: Dict[str, Any]):
        """
        Aktualisiert Konfiguration.
        
        Args:
            config: Neue Konfigurationswerte
        """
        if "folder_template" in config:
            self.folder_template = config["folder_template"]
        if "filename_template" in config:
            self.filename_template = config["filename_template"]
        if "replace_spaces" in config:
            self.replace_spaces = config["replace_spaces"]
        if "remove_invalid_chars" in config:
            self.remove_invalid_chars = config["remove_invalid_chars"]
        if "use_month_names" in config:
            self.use_month_names = config["use_month_names"]
        if "max_name_length" in config:
            self.max_name_length = config["max_name_length"]
        if "separator" in config:
            self.separator = config["separator"]

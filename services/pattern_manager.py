"""
Pattern-Manager für WerkstattArchiv.
Verwaltet und speichert konfigurierbare Regex-Patterns für die Dokumentenanalyse.
"""

import json
import os
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from functools import lru_cache


PATTERNS_FILE = "patterns.json"


@dataclass
class RegexPatterns:
    """Sammlung aller Regex-Patterns für die Dokumentenanalyse."""
    
    # Kundennummer
    kunden_nr: str = r"(?:Kunden[- ]?Nr\.?|Kundennummer|Kunde)[:\s]*(\d{5,6})"
    
    # Auftragsnummer
    auftrag_nr: str = r"(?:Auftrags[- ]?Nr\.?|Auftragsnummer|Auftrag)[:\s]*(\d{5,7})"
    
    # Datum (verschiedene Formate)
    datum: str = r"(?:Datum|vom|am)[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})"
    
    # FIN (17-stellig, alphanumerisch, keine I, O, Q)
    fin: str = r"\b([A-HJ-NPR-Z0-9]{17})\b"
    
    # Kennzeichen (deutsches Format)
    kennzeichen: str = r"\b([A-ZÄÖÜ]{1,3}[-\s]?[A-ZÄÖÜ]{1,2}[-\s]?\d{1,4}[EH]?)\b"
    
    # Kundenname (nach "Kunde:" oder "Name:")
    kunden_name: str = r"(?:Kunde|Name|Auftraggeber)[:\s]+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)"
    
    # PLZ (5-stellig)
    plz: str = r"\b(\d{5})\b"
    
    # Straße
    strasse: str = r"([A-ZÄÖÜ][a-zäöüß]+(?:straße|str\.|weg|platz|allee))\s+(\d+[a-z]?)"
    
    # Dokumenttypen
    rechnung: str = r"Rechnung"
    kva: str = r"(?:Kostenvoranschlag|KVA)"
    auftrag: str = r"Auftrag"
    hu: str = r"(?:HU|Hauptuntersuchung)"
    garantie: str = r"Garantie"
    
    def to_dict(self) -> Dict[str, str]:
        """Konvertiert Patterns zu Dictionary."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, str]) -> 'RegexPatterns':
        """Erstellt RegexPatterns aus Dictionary."""
        return RegexPatterns(**data)


class PatternManager:
    """Verwaltet Regex-Patterns und speichert sie persistent."""

    def __init__(self, patterns_file: str = PATTERNS_FILE):
        """
        Initialisiert den PatternManager.

        Args:
            patterns_file: Pfad zur JSON-Datei für Pattern-Speicherung
        """
        self.patterns_file = patterns_file
        self.patterns = self._load_patterns()
        # Compiled Pattern Cache (LRU mit max 50 Patterns)
        self._compiled_cache: Dict[str, re.Pattern] = {}
    
    def _load_patterns(self) -> RegexPatterns:
        """
        Lädt Patterns aus JSON-Datei oder erstellt Standardpatterns.
        
        Returns:
            RegexPatterns-Instanz
        """
        if not os.path.exists(self.patterns_file):
            print(f"Pattern-Datei nicht gefunden. Erstelle Standard-Patterns: {self.patterns_file}")
            patterns = RegexPatterns()
            self.save_patterns(patterns)
            return patterns
        
        try:
            with open(self.patterns_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            patterns = RegexPatterns.from_dict(data)
            print(f"✓ Patterns geladen: {self.patterns_file}")
            return patterns
            
        except Exception as e:
            print(f"Fehler beim Laden der Patterns: {e}")
            print("Verwende Standard-Patterns")
            return RegexPatterns()
    
    def save_patterns(self, patterns: Optional[RegexPatterns] = None) -> bool:
        """
        Speichert Patterns in JSON-Datei.
        
        Args:
            patterns: Zu speichernde Patterns (None = aktuelle Patterns)
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if patterns is None:
            patterns = self.patterns
        
        try:
            with open(self.patterns_file, "w", encoding="utf-8") as f:
                json.dump(patterns.to_dict(), f, indent=2, ensure_ascii=False)
            
            print(f"✓ Patterns gespeichert: {self.patterns_file}")
            self.patterns = patterns
            return True
            
        except Exception as e:
            print(f"Fehler beim Speichern der Patterns: {e}")
            return False
    
    def get_pattern(self, name: str) -> Optional[str]:
        """
        Holt ein einzelnes Pattern.

        Args:
            name: Name des Patterns (z.B. "kunden_nr", "auftrag_nr")

        Returns:
            Pattern-String oder None wenn nicht gefunden
        """
        return getattr(self.patterns, name, None)

    def get_compiled_pattern(self, name: str) -> Optional[re.Pattern]:
        """
        Holt ein compiliertes Pattern mit Caching (5-10x schneller als neucompilieren).
        Cached compilierte Regex-Objekte für wiederholte Nutzung.

        Args:
            name: Name des Patterns (z.B. "kunden_nr", "auftrag_nr")

        Returns:
            Compiliertes re.Pattern-Objekt oder None wenn nicht gefunden
        """
        # 1. Cache prüfen
        if name in self._compiled_cache:
            return self._compiled_cache[name]

        # 2. Pattern laden
        pattern_str = self.get_pattern(name)
        if not pattern_str:
            return None

        # 3. Compilieren und cachen
        try:
            compiled = re.compile(pattern_str)
            # Cache Size Limit: max 50 Patterns (sehr klein, kein Memory-Problem)
            if len(self._compiled_cache) < 50:
                self._compiled_cache[name] = compiled
            return compiled
        except re.error as e:
            print(f"Fehler beim Compilieren von Pattern '{name}': {e}")
            return None

    def update_pattern(self, name: str, pattern: str) -> bool:
        """
        Aktualisiert ein einzelnes Pattern.

        Args:
            name: Name des Patterns
            pattern: Neuer Pattern-String

        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not hasattr(self.patterns, name):
            print(f"Warnung: Pattern '{name}' existiert nicht")
            return False

        # Pattern auf Gültigkeit prüfen
        if not self.validate_pattern(pattern):
            print(f"Fehler: Pattern '{pattern}' ist ungültig")
            return False

        setattr(self.patterns, name, pattern)

        # Invalidiere Cache-Eintrag (das Pattern hat sich geändert)
        if name in self._compiled_cache:
            del self._compiled_cache[name]

        return self.save_patterns()
    
    def validate_pattern(self, pattern: str) -> bool:
        """
        Prüft ob ein Regex-Pattern gültig ist.
        
        Args:
            pattern: Zu prüfendes Pattern
            
        Returns:
            True wenn gültig, False sonst
        """
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False
    
    def test_pattern(self, pattern: str, test_text: str) -> Optional[str]:
        """
        Testet ein Pattern gegen einen Text.
        
        Args:
            pattern: Regex-Pattern
            test_text: Testtext
            
        Returns:
            Gefundener Match oder None
        """
        if not self.validate_pattern(pattern):
            return None
        
        try:
            match = re.search(pattern, test_text, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
            return None
        except Exception as e:
            print(f"Fehler beim Testen: {e}")
            return None
    
    def reset_to_defaults(self) -> bool:
        """
        Setzt alle Patterns auf Standardwerte zurück.
        
        Returns:
            True bei Erfolg
        """
        self.patterns = RegexPatterns()
        return self.save_patterns()
    
    def get_all_patterns(self) -> Dict[str, str]:
        """
        Gibt alle Patterns als Dictionary zurück.
        
        Returns:
            Dictionary mit allen Pattern-Namen und Werten
        """
        return self.patterns.to_dict()
    
    def get_pattern_descriptions(self) -> Dict[str, str]:
        """
        Gibt Beschreibungen für alle Patterns zurück.
        
        Returns:
            Dictionary mit Pattern-Namen und Beschreibungen
        """
        return {
            "kunden_nr": "Kundennummer (5-6 Ziffern nach 'Kunden-Nr.', 'Kundennummer' etc.)",
            "auftrag_nr": "Auftragsnummer (5-7 Ziffern nach 'Auftrags-Nr.', 'Auftragsnummer' etc.)",
            "datum": "Datum (TT.MM.JJJJ oder TT/MM/JJJJ nach 'Datum', 'vom', 'am')",
            "fin": "Fahrzeug-Identifikationsnummer (17 Zeichen, alphanumerisch ohne I, O, Q)",
            "kennzeichen": "KFZ-Kennzeichen (deutsches Format: XX-YY 1234)",
            "kunden_name": "Kundenname (nach 'Kunde:', 'Name:', 'Auftraggeber:')",
            "plz": "Postleitzahl (5-stellige Zahl)",
            "strasse": "Straße mit Hausnummer",
            "rechnung": "Dokumenttyp: Rechnung",
            "kva": "Dokumenttyp: Kostenvoranschlag/KVA",
            "auftrag": "Dokumenttyp: Auftrag",
            "hu": "Dokumenttyp: Hauptuntersuchung/HU",
            "garantie": "Dokumenttyp: Garantie"
        }

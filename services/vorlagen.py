"""
Vorlagen-System für verschiedene Auftragsformate.
Ermöglicht unterschiedliche Regex-Patterns für verschiedene Dokumenttypen.
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime


class AuftragsVorlage:
    """Basis-Klasse für eine Auftragsvorlage."""
    
    def __init__(self, name: str, beschreibung: str):
        self.name = name
        self.beschreibung = beschreibung
    
    def extract_kunden_nr(self, text: str) -> Optional[str]:
        """Extrahiert die Kundennummer aus dem Text."""
        raise NotImplementedError
    
    def extract_auftrag_nr(self, text: str) -> Optional[str]:
        """Extrahiert die Auftragsnummer aus dem Text."""
        raise NotImplementedError
    
    def extract_datum(self, text: str) -> Optional[int]:
        """Extrahiert das Datum/Jahr aus dem Text."""
        raise NotImplementedError
    
    def extract_dokument_typ(self, text: str) -> str:
        """Bestimmt den Dokumenttyp."""
        raise NotImplementedError


class StandardVorlage(AuftragsVorlage):
    """Standard-Vorlage für normale Aufträge."""
    
    def __init__(self):
        super().__init__(
            name="Standard",
            beschreibung="Kunde-Nr, Auftrag-Nr, normales Format"
        )
        
        # Regex-Patterns
        self.pattern_kunden_nr = r"Kunde[-\s]*Nr[:\s]+(\d+)"
        self.pattern_auftrag_nr = r"Auftrag[-\s]*Nr[:\s]+(\d+)"
        self.pattern_datum = r"(\d{1,2})\.(\d{1,2})\.(\d{4})"
        
        # Dokumenttyp-Keywords
        self.doctype_keywords = {
            "Rechnung": ["Rechnung"],
            "KVA": ["Kostenvoranschlag", "KVA"],
            "Auftrag": ["Auftrag"],
            "HU": ["HU", "Hauptuntersuchung"],
            "Garantie": ["Garantie"],
        }
    
    def extract_kunden_nr(self, text: str) -> Optional[str]:
        match = re.search(self.pattern_kunden_nr, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def extract_auftrag_nr(self, text: str) -> Optional[str]:
        match = re.search(self.pattern_auftrag_nr, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def extract_datum(self, text: str) -> Optional[int]:
        match = re.search(self.pattern_datum, text)
        if match:
            jahr = int(match.group(3))
            current_year = datetime.now().year
            if 2000 <= jahr <= current_year + 1:
                return jahr
        return None
    
    def extract_dokument_typ(self, text: str) -> str:
        text_lower = text.lower()
        
        for doc_type, keywords in self.doctype_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return doc_type
        
        return "Dokument"


class AlternativVorlage(AuftragsVorlage):
    """Alternative Vorlage für andere Auftragsformate."""
    
    def __init__(self):
        super().__init__(
            name="Alternativ",
            beschreibung="Kundennummer, Auftrags-Nr., abweichendes Format"
        )
        
        # Alternative Regex-Patterns
        self.pattern_kunden_nr = r"(?:Kundennummer|Kd[-.]?\s*Nr)[:\s]+(\d+)"
        self.pattern_auftrag_nr = r"(?:Auftrags[-\s]*Nr\.|Auftragsnummer)[:\s]+(\d+)"
        self.pattern_datum = r"(?:Datum|vom)[:\s]+(\d{1,2})\.(\d{1,2})\.(\d{4})"
        
        # Alternative Keywords
        self.doctype_keywords = {
            "Rechnung": ["Rechnung", "Invoice", "RE"],
            "KVA": ["Kostenvoranschlag", "KVA", "Angebot"],
            "Auftrag": ["Auftrag", "Werkstattauftrag", "Order"],
            "HU": ["HU", "Hauptuntersuchung", "TÜV"],
            "Garantie": ["Garantie", "Gewährleistung"],
            "Lieferschein": ["Lieferschein", "Delivery Note"],
        }
    
    def extract_kunden_nr(self, text: str) -> Optional[str]:
        match = re.search(self.pattern_kunden_nr, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def extract_auftrag_nr(self, text: str) -> Optional[str]:
        match = re.search(self.pattern_auftrag_nr, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def extract_datum(self, text: str) -> Optional[int]:
        match = re.search(self.pattern_datum, text, re.IGNORECASE)
        if match:
            jahr = int(match.group(3))
            current_year = datetime.now().year
            if 2000 <= jahr <= current_year + 1:
                return jahr
        return None
    
    def extract_dokument_typ(self, text: str) -> str:
        text_lower = text.lower()
        
        for doc_type, keywords in self.doctype_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return doc_type
        
        return "Dokument"


class VorlagenManager:
    """Verwaltet verschiedene Auftragsvorlagen."""
    
    def __init__(self):
        self.vorlagen: List[AuftragsVorlage] = [
            StandardVorlage(),
            AlternativVorlage(),
        ]
        self.active_vorlage = self.vorlagen[0]  # Standard aktiv
    
    def get_vorlagen_liste(self) -> List[str]:
        """Gibt Liste aller Vorlagennamen zurück."""
        return [v.name for v in self.vorlagen]
    
    def get_vorlage_by_name(self, name: str) -> Optional[AuftragsVorlage]:
        """Gibt Vorlage anhand des Namens zurück."""
        for vorlage in self.vorlagen:
            if vorlage.name == name:
                return vorlage
        return None
    
    def set_active_vorlage(self, name: str) -> bool:
        """Setzt die aktive Vorlage."""
        vorlage = self.get_vorlage_by_name(name)
        if vorlage:
            self.active_vorlage = vorlage
            return True
        return False
    
    def get_active_vorlage(self) -> AuftragsVorlage:
        """Gibt die aktive Vorlage zurück."""
        return self.active_vorlage
    
    def analyze_with_vorlage(self, text: str, vorlage_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Analysiert Text mit der angegebenen (oder aktiven) Vorlage.
        
        Args:
            text: Zu analysierender Text
            vorlage_name: Name der zu verwendenden Vorlage (optional)
            
        Returns:
            Dictionary mit extrahierten Daten
        """
        # Vorlage auswählen
        if vorlage_name:
            vorlage = self.get_vorlage_by_name(vorlage_name)
            if not vorlage:
                vorlage = self.active_vorlage
        else:
            vorlage = self.active_vorlage
        
        # Daten extrahieren
        kunden_nr = vorlage.extract_kunden_nr(text)
        auftrag_nr = vorlage.extract_auftrag_nr(text)
        jahr = vorlage.extract_datum(text)
        dokument_typ = vorlage.extract_dokument_typ(text)
        
        return {
            "kunden_nr": kunden_nr,
            "auftrag_nr": auftrag_nr,
            "jahr": jahr,
            "dokument_typ": dokument_typ,
            "vorlage_verwendet": vorlage.name,
        }

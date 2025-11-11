"""
Legacy-Resolver für WerkstattArchiv.
Ordnet alte Aufträge ohne Kundennummer eindeutig zu - OHNE Raten.

Regeln:
- Nur FIN-Match oder Name+Details-Match erlaubt
- Keine fuzzy logic, keine Wahrscheinlichkeiten
- Bei Unsicherheit: Als "unklar" markieren
"""

from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class LegacyMatch:
    """Ergebnis einer Legacy-Kundenauflösung."""
    kunden_nr: Optional[str]
    match_reason: str  # "fin", "name_plus_details", "unclear", "multiple_matches"
    confidence_detail: str  # Zusatzinfo für Logging


class LegacyResolver:
    """
    Löst Legacy-Aufträge ohne Kundennummer auf.
    Verwendet strikte Regeln ohne Heuristiken.
    """
    
    def __init__(self, customer_manager, vehicle_manager):
        """
        Args:
            customer_manager: CustomerManager-Instanz
            vehicle_manager: VehicleManager-Instanz
        """
        self.customer_manager = customer_manager
        self.vehicle_manager = vehicle_manager
    
    def resolve_legacy_customer(self, meta: Dict[str, Any]) -> LegacyMatch:
        """
        Versucht einen Legacy-Auftrag einem Kunden zuzuordnen.
        
        Strikte Regeln:
        1. FIN eindeutig → automatische Zuordnung
        2. Name + PLZ/Adresse eindeutig → automatische Zuordnung
        3. Sonst → "unclear"
        
        Args:
            meta: Dictionary mit extrahierten Feldern:
                - kunden_name: str | None
                - fin: str | None
                - kennzeichen: str | None
                - plz: str | None (falls extrahiert)
                - adresse: str | None (falls extrahiert)
        
        Returns:
            LegacyMatch mit kunden_nr und match_reason
        """
        
        # REGEL A: FIN eindeutig
        fin = meta.get("fin")
        if fin:
            match = self._match_by_fin(fin)
            if match:
                return match
        
        # REGEL B: Name + Details eindeutig
        name = meta.get("kunden_name")
        if name:
            match = self._match_by_name_details(
                name=name,
                plz=meta.get("plz"),
                adresse=meta.get("adresse")
            )
            if match:
                return match
        
        # Keine eindeutige Zuordnung möglich
        return LegacyMatch(
            kunden_nr=None,
            match_reason="unclear",
            confidence_detail="Keine eindeutigen Merkmale gefunden"
        )
    
    def _match_by_fin(self, fin: str) -> Optional[LegacyMatch]:
        """
        Versucht Zuordnung über FIN.
        
        Args:
            fin: Fahrgestellnummer
            
        Returns:
            LegacyMatch wenn eindeutig, sonst None
        """
        # Suche alle Kunden mit dieser FIN
        customers = self.vehicle_manager.find_customers_by_fin(fin)
        
        if len(customers) == 1:
            # Eindeutig: Genau ein Kunde
            return LegacyMatch(
                kunden_nr=customers[0],
                match_reason="fin",
                confidence_detail=f"FIN {fin} eindeutig zugeordnet"
            )
        elif len(customers) > 1:
            # Mehrere Kunden → unsicher (Halterwechsel oder Duplikat)
            return LegacyMatch(
                kunden_nr=None,
                match_reason="multiple_matches",
                confidence_detail=f"FIN {fin} bei {len(customers)} Kunden gefunden"
            )
        else:
            # FIN nicht in Datenbank
            return None
    
    def _match_by_name_details(self, name: str, plz: Optional[str] = None, 
                               adresse: Optional[str] = None) -> Optional[LegacyMatch]:
        """
        Versucht Zuordnung über Name + Zusatzdaten.
        
        Nur wenn Name + (PLZ ODER Adresse) vorhanden UND eindeutig.
        
        Args:
            name: Kundenname
            plz: PLZ (optional)
            adresse: Adresse (optional)
            
        Returns:
            LegacyMatch wenn eindeutig, sonst None
        """
        # Mindestens ein Zusatzmerkmal erforderlich
        if not plz and not adresse:
            return None
        
        # Suche Kunden mit Name + PLZ
        if plz:
            customers = self.customer_manager.find_by_name_and_plz(name, plz)
            if len(customers) == 1:
                return LegacyMatch(
                    kunden_nr=customers[0].kunden_nr,
                    match_reason="name_plus_details",
                    confidence_detail=f"Name '{name}' + PLZ '{plz}' eindeutig"
                )
            elif len(customers) > 1:
                return LegacyMatch(
                    kunden_nr=None,
                    match_reason="multiple_matches",
                    confidence_detail=f"Name '{name}' + PLZ '{plz}' nicht eindeutig ({len(customers)} Treffer)"
                )
        
        # Suche Kunden mit Name + Adresse
        if adresse:
            customers = self.customer_manager.find_by_name_and_address(name, adresse)
            if len(customers) == 1:
                return LegacyMatch(
                    kunden_nr=customers[0].kunden_nr,
                    match_reason="name_plus_details",
                    confidence_detail=f"Name '{name}' + Adresse '{adresse}' eindeutig"
                )
            elif len(customers) > 1:
                return LegacyMatch(
                    kunden_nr=None,
                    match_reason="multiple_matches",
                    confidence_detail=f"Name '{name}' + Adresse '{adresse}' nicht eindeutig ({len(customers)} Treffer)"
                )
        
        # Keine eindeutige Zuordnung gefunden
        return None
    
    def validate_match(self, meta: Dict[str, Any], kunden_nr: str) -> bool:
        """
        Validiert einen Legacy-Match auf Konsistenz.
        
        Optional: Prüft ob FIN/Kennzeichen zum Kunden passt.
        
        Args:
            meta: Extrahierte Metadaten
            kunden_nr: Zugeordnete Kundennummer
            
        Returns:
            True wenn konsistent, False bei Widersprüchen
        """
        fin = meta.get("fin")
        if fin:
            # Prüfe ob FIN zu diesem Kunden passt
            customers = self.vehicle_manager.find_customers_by_fin(fin)
            if customers and kunden_nr not in customers:
                # Widerspruch: FIN gehört zu anderem Kunden
                return False
        
        return True

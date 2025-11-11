"""
Kundenverwaltung für WerkstattArchiv.
Lädt und verwaltet die Kundendatenbank aus einer CSV-Datei.
"""

import csv
import os
from typing import Dict, Optional


class CustomerManager:
    """Verwaltet Kundendaten und bietet Zugriff auf Kundennamen."""
    
    def __init__(self, customers_file: str):
        """
        Initialisiert den CustomerManager.
        
        Args:
            customers_file: Pfad zur Kunden-CSV-Datei (Format: kunden_nr;kunden_name)
        """
        self.customers_file = customers_file
        self.customers: Dict[str, str] = {}
        self.load_customers()
    
    def load_customers(self) -> None:
        """
        Lädt die Kundendaten aus der CSV-Datei.
        Format: kunden_nr;kunden_name
        """
        self.customers.clear()
        
        if not os.path.exists(self.customers_file):
            print(f"Warnung: Kundendatei nicht gefunden: {self.customers_file}")
            return
        
        try:
            with open(self.customers_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=";")
                for row in reader:
                    if len(row) >= 2:
                        kunden_nr = row[0].strip()
                        kunden_name = row[1].strip()
                        if kunden_nr and kunden_name:
                            self.customers[kunden_nr] = kunden_name
            
            print(f"Kundendatenbank geladen: {len(self.customers)} Kunden")
            
        except Exception as e:
            print(f"Fehler beim Laden der Kundendatei: {e}")
    
    def get_customer_name(self, kunden_nr: str) -> Optional[str]:
        """
        Gibt den Kundennamen für eine Kundennummer zurück.
        
        Args:
            kunden_nr: Die Kundennummer
            
        Returns:
            Kundenname oder None, wenn nicht gefunden
        """
        return self.customers.get(kunden_nr)
    
    def customer_exists(self, kunden_nr: str) -> bool:
        """
        Prüft, ob eine Kundennummer in der Datenbank existiert.
        
        Args:
            kunden_nr: Die zu prüfende Kundennummer
            
        Returns:
            True wenn Kunde existiert, sonst False
        """
        return kunden_nr in self.customers
    
    def get_all_customers(self) -> Dict[str, str]:
        """
        Gibt alle Kunden als Dictionary zurück.
        
        Returns:
            Dictionary mit Kundennummer als Key und Kundenname als Value
        """
        return self.customers.copy()

"""
Kundenverwaltung für WerkstattArchiv.
Lädt und verwaltet die Kundendatenbank aus einer CSV-Datei.
"""

import csv
import os
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class Customer:
    """Kundendaten."""
    kunden_nr: str
    name: str
    plz: Optional[str] = None
    ort: Optional[str] = None
    strasse: Optional[str] = None
    telefon: Optional[str] = None


class CustomerManager:
    """Verwaltet Kundendaten und bietet Zugriff auf Kundennamen."""
    
    def __init__(self, customers_file: str):
        """
        Initialisiert den CustomerManager.
        
        Args:
            customers_file: Pfad zur Kunden-CSV-Datei 
                Format: kunden_nr;name;plz;ort;strasse;telefon
                (PLZ, Ort, Strasse, Telefon optional)
        """
        self.customers_file = customers_file
        self.customers: Dict[str, Customer] = {}  # kunden_nr → Customer
        self.load_customers()
    
    def load_customers(self) -> None:
        """
        Lädt die Kundendaten aus der CSV-Datei.
        Format: kunden_nr;name;plz;ort;strasse;telefon (Felder ab PLZ optional)
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
                        name = row[1].strip()
                        
                        if kunden_nr and name:
                            customer = Customer(
                                kunden_nr=kunden_nr,
                                name=name,
                                plz=row[2].strip() if len(row) > 2 else None,
                                ort=row[3].strip() if len(row) > 3 else None,
                                strasse=row[4].strip() if len(row) > 4 else None,
                                telefon=row[5].strip() if len(row) > 5 else None
                            )
                            self.customers[kunden_nr] = customer
            
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
        customer = self.customers.get(kunden_nr)
        return customer.name if customer else None
    
    def get_customer(self, kunden_nr: str) -> Optional[Customer]:
        """
        Gibt vollständige Kundendaten zurück.
        
        Args:
            kunden_nr: Die Kundennummer
            
        Returns:
            Customer-Objekt oder None
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
    
    def get_all_customers(self) -> Dict[str, Customer]:
        """
        Gibt alle Kunden zurück.
        
        Returns:
            Dictionary mit Kundennummer als Key und Customer als Value
        """
        return self.customers.copy()
    
    def find_by_name_and_plz(self, name: str, plz: str) -> List[Customer]:
        """
        Sucht Kunden nach Name UND PLZ (exakt, case-insensitive).
        
        Für Legacy-Resolver: Nur bei eindeutigem Match verwenden.
        
        Args:
            name: Kundenname
            plz: Postleitzahl
            
        Returns:
            Liste gefundener Kunden (0, 1 oder mehr)
        """
        name_lower = name.lower().strip()
        plz_clean = plz.strip()
        
        matches = []
        for customer in self.customers.values():
            if (customer.name.lower() == name_lower and 
                customer.plz and customer.plz.strip() == plz_clean):
                matches.append(customer)
        
        return matches
    
    def find_by_name_and_address(self, name: str, address: str) -> List[Customer]:
        """
        Sucht Kunden nach Name UND Adresse (exakt, case-insensitive).
        
        Für Legacy-Resolver: Nur bei eindeutigem Match verwenden.
        
        Args:
            name: Kundenname
            address: Straße (oder Teil davon)
            
        Returns:
            Liste gefundener Kunden (0, 1 oder mehr)
        """
        name_lower = name.lower().strip()
        address_lower = address.lower().strip()
        
        matches = []
        for customer in self.customers.values():
            if (customer.name.lower() == name_lower and 
                customer.strasse and address_lower in customer.strasse.lower()):
                matches.append(customer)
        
        return matches

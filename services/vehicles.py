"""
Fahrzeug-Manager für WerkstattArchiv.
Verwaltet FIN/Kennzeichen → Kundennummer Zuordnung.
"""

import csv
import os
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Vehicle:
    """Fahrzeugdaten."""
    fin: str  # Fahrgestellnummer (17 Zeichen)
    kennzeichen: Optional[str]
    kunden_nr: str
    marke: Optional[str] = None
    modell: Optional[str] = None
    erstzulassung: Optional[str] = None
    letzte_aktualisierung: Optional[str] = None


class VehicleManager:
    """
    Verwaltet Fahrzeugzuordnungen.
    Speichert FIN → Kundennummer Mapping in vehicles.csv.
    """
    
    def __init__(self, vehicles_file: str = "data/vehicles.csv"):
        """
        Args:
            vehicles_file: Pfad zur vehicles.csv Datei
        """
        self.vehicles_file = vehicles_file
        self.vehicles: Dict[str, Vehicle] = {}  # fin → Vehicle
        self._ensure_file_exists()
        self._load_vehicles()
    
    def _ensure_file_exists(self):
        """Erstellt vehicles.csv wenn nicht vorhanden."""
        os.makedirs(os.path.dirname(self.vehicles_file), exist_ok=True)
        
        if not os.path.exists(self.vehicles_file):
            with open(self.vehicles_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'fin', 'kennzeichen', 'kunden_nr', 'marke', 'modell', 
                    'erstzulassung', 'letzte_aktualisierung'
                ])
    
    def _load_vehicles(self):
        """Lädt alle Fahrzeuge aus vehicles.csv."""
        self.vehicles.clear()
        
        if not os.path.exists(self.vehicles_file):
            return
        
        with open(self.vehicles_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                fin = row['fin'].strip().upper()
                if fin:
                    vehicle = Vehicle(
                        fin=fin,
                        kennzeichen=row.get('kennzeichen') or None,
                        kunden_nr=row['kunden_nr'].strip(),
                        marke=row.get('marke') or None,
                        modell=row.get('modell') or None,
                        erstzulassung=row.get('erstzulassung') or None,
                        letzte_aktualisierung=row.get('letzte_aktualisierung') or None
                    )
                    self.vehicles[fin] = vehicle
    
    def _save_vehicles(self):
        """Speichert alle Fahrzeuge in vehicles.csv."""
        with open(self.vehicles_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'fin', 'kennzeichen', 'kunden_nr', 'marke', 'modell',
                'erstzulassung', 'letzte_aktualisierung'
            ])
            
            for vehicle in sorted(self.vehicles.values(), key=lambda v: v.fin):
                writer.writerow([
                    vehicle.fin,
                    vehicle.kennzeichen or '',
                    vehicle.kunden_nr,
                    vehicle.marke or '',
                    vehicle.modell or '',
                    vehicle.erstzulassung or '',
                    vehicle.letzte_aktualisierung or ''
                ])
    
    def find_customers_by_fin(self, fin: str) -> List[str]:
        """
        Findet alle Kundennummern zu einer FIN.
        
        Args:
            fin: Fahrgestellnummer
            
        Returns:
            Liste von Kundennummern (normalerweise 0 oder 1 Einträge)
        """
        fin = fin.strip().upper()
        
        if fin in self.vehicles:
            return [self.vehicles[fin].kunden_nr]
        
        return []
    
    def find_customers_by_kennzeichen(self, kennzeichen: str) -> List[str]:
        """
        Findet alle Kundennummern zu einem Kennzeichen.
        
        WARNUNG: Kennzeichen können wechseln! 
        Daher weniger zuverlässig als FIN.
        
        Args:
            kennzeichen: Kfz-Kennzeichen
            
        Returns:
            Liste von Kundennummern
        """
        kennzeichen = kennzeichen.strip().upper()
        customers = []
        
        for vehicle in self.vehicles.values():
            if vehicle.kennzeichen and vehicle.kennzeichen.upper() == kennzeichen:
                customers.append(vehicle.kunden_nr)
        
        return customers
    
    def add_or_update_vehicle(self, fin: str, kunden_nr: str, 
                             kennzeichen: Optional[str] = None,
                             marke: Optional[str] = None,
                             modell: Optional[str] = None,
                             erstzulassung: Optional[str] = None) -> bool:
        """
        Fügt ein Fahrzeug hinzu oder aktualisiert es.
        
        Args:
            fin: Fahrgestellnummer
            kunden_nr: Kundennummer
            kennzeichen: Kennzeichen (optional)
            marke: Fahrzeugmarke (optional)
            modell: Fahrzeugmodell (optional)
            erstzulassung: Erstzulassungsdatum (optional)
            
        Returns:
            True bei Erfolg
        """
        fin = fin.strip().upper()
        
        if len(fin) != 17:
            return False  # Ungültige FIN
        
        vehicle = Vehicle(
            fin=fin,
            kennzeichen=kennzeichen,
            kunden_nr=kunden_nr.strip(),
            marke=marke,
            modell=modell,
            erstzulassung=erstzulassung,
            letzte_aktualisierung=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        self.vehicles[fin] = vehicle
        self._save_vehicles()
        return True
    
    def get_vehicle_by_fin(self, fin: str) -> Optional[Vehicle]:
        """
        Holt Fahrzeugdaten zu einer FIN.
        
        Args:
            fin: Fahrgestellnummer
            
        Returns:
            Vehicle oder None
        """
        fin = fin.strip().upper()
        return self.vehicles.get(fin)
    
    def remove_vehicle(self, fin: str) -> bool:
        """
        Entfernt ein Fahrzeug.
        
        Args:
            fin: Fahrgestellnummer
            
        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """
        fin = fin.strip().upper()
        
        if fin in self.vehicles:
            del self.vehicles[fin]
            self._save_vehicles()
            return True
        
        return False
    
    def get_all_vehicles(self) -> List[Vehicle]:
        """Gibt alle Fahrzeuge zurück."""
        return list(self.vehicles.values())
    
    def get_vehicles_by_customer(self, kunden_nr: str) -> List[Vehicle]:
        """
        Holt alle Fahrzeuge eines Kunden.
        
        Args:
            kunden_nr: Kundennummer
            
        Returns:
            Liste von Vehicles
        """
        return [v for v in self.vehicles.values() if v.kunden_nr == kunden_nr]

"""
Virtual Customer Manager für WerkstattArchiv.
Verwaltet die Zuordnung virtueller Kundennummern zu echten Kunden
und das Umbenennen bereits archivierter Dateien.
"""

import os
import re
from typing import List, Tuple, Optional, Dict
from pathlib import Path


class VirtualCustomerManager:
    """Verwaltet virtuelle Kundennummern und deren Ersetzung."""
    
    def __init__(self, root_dir: str, customer_manager):
        """
        Args:
            root_dir: Root-Verzeichnis des Archivs
            customer_manager: CustomerManager-Instanz
        """
        self.root_dir = root_dir
        self.customer_manager = customer_manager
    
    def find_files_with_customer(self, kunden_nr: str) -> List[str]:
        """
        Findet alle Dateien im Archiv, die eine bestimmte Kundennummer enthalten.

        Args:
            kunden_nr: Die zu suchende Kundennummer

        Returns:
            Liste von Dateipfaden
        """
        files_found = []

        if not os.path.exists(self.root_dir):
            return files_found

        # Durchsuche alle Unterverzeichnisse
        for root, dirs, files in os.walk(self.root_dir):
            for filename in files:
                # Prüfe ob Kundennummer im Dateinamen vorkommt
                if kunden_nr in filename:
                    file_path = os.path.join(root, filename)
                    files_found.append(file_path)

        return files_found

    def get_all_customer_file_counts(self) -> Dict[str, int]:
        """
        Ermittelt Dateianzahl für alle Kunden in EINEM os.walk() Durchgang (Performance-Optimierung).

        Viel schneller als find_files_with_customer() für jeden Kunden einzeln zu aufrufen!
        Statt 100 x os.walk(), nur 1x - 100x schneller!

        Returns:
            Dict: {kunden_nr: file_count}
        """
        file_counts = {}

        if not os.path.exists(self.root_dir):
            return file_counts

        # EINMALIGER os.walk() Durchgang
        for root, dirs, files in os.walk(self.root_dir):
            for filename in files:
                # Extrahiere Kundennummer aus Dateinamen
                # Format: "...kunden_nr..." (z.B. VK0001, 12345, etc.)

                # Versuche Kundennummern zu extrahieren (einfache Heuristik)
                import re
                # Suche nach Kundennummern: VKxxxx oder Ziffern
                matches = re.findall(r'(VK\d{4}|10\d{3}|11\d{3}|12\d{3})', filename)

                for kunden_nr in matches:
                    file_counts[kunden_nr] = file_counts.get(kunden_nr, 0) + 1

        return file_counts
    
    def replace_customer_in_filename(self, old_kunden_nr: str, new_kunden_nr: str,
                                     new_customer_name: str) -> Tuple[int, List[str]]:
        """
        Ersetzt eine Kundennummer in allen Dateinamen im Archiv.
        
        Args:
            old_kunden_nr: Alte (virtuelle) Kundennummer
            new_kunden_nr: Neue (echte) Kundennummer
            new_customer_name: Name des echten Kunden
            
        Returns:
            Tuple: (Anzahl umbenannter Dateien, Liste der Fehler)
        """
        files_to_rename = self.find_files_with_customer(old_kunden_nr)
        renamed_count = 0
        errors = []
        
        print(f"\n🔄 Starte Umbenennung: {old_kunden_nr} → {new_kunden_nr}")
        print(f"   Gefunden: {len(files_to_rename)} Dateien")
        
        for old_path in files_to_rename:
            try:
                # Erzeuge neuen Dateinamen
                directory = os.path.dirname(old_path)
                old_filename = os.path.basename(old_path)
                
                # Ersetze Kundennummer im Dateinamen
                new_filename = old_filename.replace(old_kunden_nr, new_kunden_nr)
                
                # Wenn auch der alte Kundenname im Dateinamen ist, ersetze ihn
                old_customer = self.customer_manager.get_customer(old_kunden_nr)
                if old_customer and old_customer.name in new_filename:
                    new_filename = new_filename.replace(old_customer.name, new_customer_name)
                
                new_path = os.path.join(directory, new_filename)
                
                # Prüfe ob Zieldatei bereits existiert
                if os.path.exists(new_path) and new_path != old_path:
                    errors.append(f"Ziel existiert bereits: {new_filename}")
                    continue
                
                # Umbenennen
                os.rename(old_path, new_path)
                renamed_count += 1
                print(f"   ✓ {old_filename} → {new_filename}")
                
            except Exception as e:
                error_msg = f"Fehler bei {old_path}: {str(e)}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
        
        return renamed_count, errors
    
    def assign_real_customer_to_virtual(self, virtual_nr: str, real_nr: str,
                                       customer_name: str) -> Tuple[bool, str, int]:
        """
        Weist einem virtuellen Kunden eine echte Kundennummer zu und
        benennt alle zugehörigen Dateien um.
        
        Args:
            virtual_nr: Virtuelle Kundennummer (VKxxxx)
            real_nr: Echte Kundennummer
            customer_name: Name des echten Kunden
            
        Returns:
            Tuple: (Erfolg, Fehlermeldung, Anzahl umbenannter Dateien)
        """
        # Prüfe ob virtuelle Kundennummer existiert
        if not self.customer_manager.customer_exists(virtual_nr):
            return False, f"Virtuelle Kundennummer {virtual_nr} nicht gefunden", 0
        
        if not self.customer_manager.is_virtual_customer(virtual_nr):
            return False, f"{virtual_nr} ist keine virtuelle Kundennummer", 0
        
        # Benenne Dateien um
        renamed_count, errors = self.replace_customer_in_filename(
            virtual_nr, real_nr, customer_name
        )
        
        # Ersetze in Kundendatenbank
        success = self.customer_manager.replace_virtual_customer(
            virtual_nr, real_nr, customer_name
        )
        
        if not success:
            return False, "Fehler beim Aktualisieren der Kundendatenbank", renamed_count
        
        error_msg = ""
        if errors:
            error_msg = f"Umbenannt: {renamed_count}, Fehler: {len(errors)}"
        
        return True, error_msg, renamed_count
    
    def get_all_virtual_customers(self) -> List[Tuple[str, str]]:
        """
        Gibt alle virtuellen Kunden zurück.
        
        Returns:
            Liste von Tuples (Kundennummer, Name)
        """
        virtual_customers = []
        for kunden_nr, customer in self.customer_manager.customers.items():
            if self.customer_manager.is_virtual_customer(kunden_nr):
                virtual_customers.append((kunden_nr, customer.name))
        
        return sorted(virtual_customers)

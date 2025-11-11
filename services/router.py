"""
Routing-Service für WerkstattArchiv.
Baut Zielpfade auf und verschiebt Dateien in die korrekte Struktur.
"""

import os
import shutil
from typing import Dict, Any, Tuple
from datetime import datetime

from services.customers import CustomerManager


def build_target_path(analysis_result: Dict[str, Any], root_dir: str, 
                     unclear_dir: str, customer_manager: CustomerManager) -> Tuple[str, bool]:
    """
    Baut den Zielpfad für ein analysiertes Dokument.
    
    Args:
        analysis_result: Dictionary mit Analyseergebnissen
        root_dir: Basis-Verzeichnis für sortierte Dokumente
        unclear_dir: Verzeichnis für unklare Dokumente
        customer_manager: CustomerManager-Instanz für Kundennamens-Lookup
        
    Returns:
        Tuple (zielpfad, is_clear):
        - zielpfad: Vollständiger Pfad inkl. Dateiname
        - is_clear: True wenn Dokument klar zuordenbar, False wenn unklar
    """
    kunden_nr = analysis_result.get("kunden_nr")
    auftrag_nr = analysis_result.get("auftrag_nr")
    dokument_typ = analysis_result.get("dokument_typ", "Dokument")
    jahr = analysis_result.get("jahr")
    confidence = analysis_result.get("confidence", 0.0)
    
    # Prüfe ob Dokument unklar ist
    is_clear = kunden_nr is not None and confidence >= 0.6
    
    if not is_clear or kunden_nr is None:
        # Unklar → in unclear_dir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{dokument_typ}.pdf"
        return os.path.join(unclear_dir, filename), False
    
    # Kundenname ermitteln (kunden_nr ist hier garantiert nicht None)
    kunden_name = customer_manager.get_customer_name(kunden_nr)
    if not kunden_name:
        # Kunde nicht in Datenbank → unklar
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{dokument_typ}.pdf"
        return os.path.join(unclear_dir, filename), False
    
    # Update analysis_result mit Kundenname
    analysis_result["kunden_name"] = kunden_name
    
    # Jahr bestimmen (Fallback auf aktuelles Jahr)
    if jahr is None:
        jahr = datetime.now().year
    
    # Dateiname aufbauen
    if auftrag_nr:
        filename = f"{auftrag_nr}_{dokument_typ}.pdf"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{dokument_typ}.pdf"
    
    # Pfad aufbauen: [ROOT]/Kunde/[Kundennummer] - [Kundenname]/[Jahr]/[Dateiname]
    kunde_ordner = f"{kunden_nr} - {kunden_name}"
    target_path = os.path.join(root_dir, "Kunde", kunde_ordner, str(jahr), filename)
    
    return target_path, True


def ensure_unique_filename(target_path: str) -> str:
    """
    Stellt sicher, dass der Dateiname eindeutig ist.
    Bei Konflikt wird ein Zeitstempel hinzugefügt.
    
    Args:
        target_path: Gewünschter Zielpfad
        
    Returns:
        Eindeutiger Zielpfad
    """
    if not os.path.exists(target_path):
        return target_path
    
    # Datei existiert bereits → Zeitstempel anhängen
    directory = os.path.dirname(target_path)
    filename = os.path.basename(target_path)
    name, ext = os.path.splitext(filename)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"{name}_{timestamp}{ext}"
    new_path = os.path.join(directory, new_filename)
    
    # Rekursiv prüfen falls auch diese Datei existiert
    return ensure_unique_filename(new_path)


def move_file(source_path: str, target_path: str) -> None:
    """
    Verschiebt eine Datei von source zu target.
    Erstellt fehlende Verzeichnisse automatisch.
    
    Args:
        source_path: Quellpfad
        target_path: Zielpfad
        
    Raises:
        Exception bei Fehlern beim Verschieben
    """
    # Zielverzeichnis erstellen falls nicht vorhanden
    target_dir = os.path.dirname(target_path)
    os.makedirs(target_dir, exist_ok=True)
    
    # Eindeutigen Dateinamen sicherstellen
    target_path = ensure_unique_filename(target_path)
    
    # Datei verschieben
    shutil.move(source_path, target_path)


def process_document(file_path: str, analysis_result: Dict[str, Any], 
                    root_dir: str, unclear_dir: str, 
                    customer_manager: CustomerManager) -> Tuple[str, bool, str]:
    """
    Verarbeitet ein Dokument: baut Zielpfad und verschiebt die Datei.
    
    Args:
        file_path: Pfad zur Quelldatei
        analysis_result: Analyseergebnisse
        root_dir: Basis-Verzeichnis für sortierte Dokumente
        unclear_dir: Verzeichnis für unklare Dokumente
        customer_manager: CustomerManager-Instanz
        
    Returns:
        Tuple (target_path, is_clear, reason):
        - target_path: Zielpfad der verschobenen Datei
        - is_clear: True wenn klar zuordenbar
        - reason: Grund falls unklar, sonst leerer String
    """
    # Zielpfad bestimmen
    target_path, is_clear = build_target_path(
        analysis_result, root_dir, unclear_dir, customer_manager
    )
    
    # Grund für Unklar-Einstufung ermitteln
    reason = ""
    if not is_clear:
        if not analysis_result.get("kunden_nr"):
            reason = "Keine Kundennummer erkannt"
        elif analysis_result.get("confidence", 0.0) < 0.6:
            reason = f"Zu niedrige Confidence: {analysis_result['confidence']:.2f}"
        else:
            reason = "Kunde nicht in Datenbank"
    
    # Datei verschieben
    try:
        move_file(file_path, target_path)
    except Exception as e:
        raise Exception(f"Fehler beim Verschieben: {e}")
    
    return target_path, is_clear, reason

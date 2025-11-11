"""
Logging-Service für WerkstattArchiv.
Schreibt alle Events persistent in eine lokale Logdatei.
"""

import os
from datetime import datetime
from typing import Dict, Any


LOG_FILE = "WerkstattArchiv_log.txt"


def log(event_dict: Dict[str, Any]) -> None:
    """
    Schreibt ein Event in die Logdatei.
    
    Args:
        event_dict: Dictionary mit Event-Informationen
                   (z.B. timestamp, original_path, target_path, metadata, confidence, error)
    """
    try:
        timestamp = event_dict.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        log_entry = f"\n{'='*80}\n"
        log_entry += f"[{timestamp}]\n"
        
        for key, value in event_dict.items():
            if key != "timestamp":
                log_entry += f"  {key}: {value}\n"
        
        log_entry += f"{'='*80}\n"
        
        # Logdatei im Append-Modus öffnen
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
    except Exception as e:
        print(f"Fehler beim Schreiben der Logdatei: {e}")


def log_success(original_path: str, target_path: str, metadata: Dict[str, Any], confidence: float) -> None:
    """
    Loggt eine erfolgreiche Dateiverschiebung.
    
    Args:
        original_path: Ursprünglicher Dateipfad
        target_path: Zieldateipfad
        metadata: Erkannte Metadaten
        confidence: Confidence-Score
    """
    event = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "SUCCESS",
        "original_path": original_path,
        "target_path": target_path,
        "kunden_nr": metadata.get("kunden_nr", "N/A"),
        "kunden_name": metadata.get("kunden_name", "N/A"),
        "auftrag_nr": metadata.get("auftrag_nr", "N/A"),
        "dokument_typ": metadata.get("dokument_typ", "N/A"),
        "jahr": metadata.get("jahr", "N/A"),
        "confidence": f"{confidence:.2f}",
    }
    log(event)


def log_unclear(original_path: str, target_path: str, metadata: Dict[str, Any], confidence: float, reason: str) -> None:
    """
    Loggt ein unklares Dokument.
    
    Args:
        original_path: Ursprünglicher Dateipfad
        target_path: Pfad im Unklar-Ordner
        metadata: Erkannte Metadaten
        confidence: Confidence-Score
        reason: Grund für Unklar-Einstufung
    """
    event = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "UNCLEAR",
        "original_path": original_path,
        "target_path": target_path,
        "kunden_nr": metadata.get("kunden_nr", "N/A"),
        "kunden_name": metadata.get("kunden_name", "N/A"),
        "auftrag_nr": metadata.get("auftrag_nr", "N/A"),
        "dokument_typ": metadata.get("dokument_typ", "N/A"),
        "jahr": metadata.get("jahr", "N/A"),
        "confidence": f"{confidence:.2f}",
        "reason": reason,
    }
    log(event)


def log_error(original_path: str, error_message: str) -> None:
    """
    Loggt einen Fehler bei der Verarbeitung.
    
    Args:
        original_path: Dateipfad der fehlerhaften Datei
        error_message: Fehlermeldung
    """
    event = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "ERROR",
        "original_path": original_path,
        "error": error_message,
    }
    log(event)

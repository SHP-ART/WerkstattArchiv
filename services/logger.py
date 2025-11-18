"""
Logging-Service für WerkstattArchiv.
Schreibt alle Events persistent in eine lokale Logdatei.
Unterstützt optionales Remote-Logging via Syslog.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional


LOG_FILE = "WerkstattArchiv_log.txt"

# Globaler Remote-Logger (wird bei Bedarf initialisiert)
_remote_logger: Optional[logging.Logger] = None
_syslog_enabled = False


def log(event_dict: Dict[str, Any]) -> None:
    """
    Schreibt ein Event in die Logdatei und optional an Remote-Server.
    
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
        
        # Optional: Remote-Logging
        if _syslog_enabled and _remote_logger:
            try:
                status = event_dict.get("status", "INFO")
                # Kompakte Nachricht für Syslog
                msg_parts = []
                for key, value in event_dict.items():
                    if key not in ["timestamp", "status"]:
                        msg_parts.append(f"{key}={value}")
                message = " | ".join(msg_parts)
                
                if status == "ERROR":
                    _remote_logger.error(message)
                elif status == "UNCLEAR":
                    _remote_logger.warning(message)
                else:
                    _remote_logger.info(message)
            except Exception as e:
                # Remote-Fehler nicht kritisch - lokales Log bleibt erhalten
                pass
            
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


def init_remote_logging(
    enabled: bool = False,
    server: Optional[str] = None,
    port: int = 514,
    protocol: str = "UDP"
) -> bool:
    """
    Initialisiert optionales Remote-Logging via Syslog.
    
    Args:
        enabled: Remote-Logging aktivieren
        server: IP/Hostname des Syslog-Servers
        port: Port des Syslog-Servers (Standard: 514)
        protocol: "UDP" oder "TCP"
        
    Returns:
        True wenn erfolgreich initialisiert, sonst False
    """
    global _remote_logger, _syslog_enabled
    
    if not enabled or not server:
        _syslog_enabled = False
        return False
    
    try:
        # Logger erstellen
        _remote_logger = logging.getLogger("WerkstattArchiv_Remote")
        _remote_logger.setLevel(logging.INFO)
        _remote_logger.handlers.clear()
        
        # Socket-Typ bestimmen
        if protocol.upper() == "TCP":
            socktype = logging.handlers.socket.SOCK_STREAM
        else:
            socktype = logging.handlers.socket.SOCK_DGRAM
        
        # Syslog-Handler
        syslog_handler = logging.handlers.SysLogHandler(
            address=(server, port),
            socktype=socktype
        )
        
        # Formatter
        formatter = logging.Formatter(
            'WerkstattArchiv: [%(levelname)s] %(message)s'
        )
        syslog_handler.setFormatter(formatter)
        _remote_logger.addHandler(syslog_handler)
        
        _syslog_enabled = True
        _remote_logger.info(f"Remote-Logging aktiviert: {server}:{port} ({protocol})")
        
        print(f"✓ Remote-Logging aktiviert: {server}:{port} ({protocol})")
        return True
        
    except Exception as e:
        _syslog_enabled = False
        print(f"⚠️ Remote-Logging fehlgeschlagen: {e}")
        return False


def disable_remote_logging():
    """Deaktiviert Remote-Logging."""
    global _syslog_enabled, _remote_logger
    _syslog_enabled = False
    if _remote_logger:
        for handler in _remote_logger.handlers:
            handler.close()
        _remote_logger.handlers.clear()
    print("✓ Remote-Logging deaktiviert")

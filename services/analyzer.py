"""
Dokumentanalyse für WerkstattArchiv.
Extrahiert Text aus PDFs und Bildern und analysiert Metadaten.
"""

import re
import os
from typing import Dict, Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from services.vorlagen import VorlagenManager

# Type-Hints für optionale Imports
fitz = None
easyocr = None
easyocr_reader = None

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Warnung: PyMuPDF nicht verfügbar. PDF-Textextraktion eingeschränkt.")

# EasyOCR - Python-basierte OCR (keine externe Installation nötig)
# Fehler werden für späteres Logging gespeichert (Logger ist beim Import noch nicht bereit)
OCR_INIT_ERROR = None

try:
    import easyocr  # type: ignore
    from PIL import Image  # type: ignore
    print("✅ EasyOCR verfügbar - verwende Python-basierte OCR")
    # Initialisiere Reader mit Deutsch und Englisch
    # gpu=False für CPU-only (funktioniert überall)
    easyocr_reader = easyocr.Reader(['de', 'en'], gpu=False, verbose=False)
    OCR_AVAILABLE = True
except ImportError as e:
    OCR_AVAILABLE = False
    easyocr_reader = None
    OCR_INIT_ERROR = ("ImportError", "EasyOCR nicht verfügbar. Installiere: pip install easyocr", str(e))
    print(f"❌ EasyOCR nicht verfügbar. Installiere: pip install easyocr")
except Exception as e:
    OCR_AVAILABLE = False
    easyocr_reader = None
    import traceback
    OCR_INIT_ERROR = (type(e).__name__, f"EasyOCR Fehler: {type(e).__name__}: {e}", traceback.format_exc())
    print(f"⚠️  EasyOCR Fehler: {e}")
    print("❌ EasyOCR konnte nicht initialisiert werden")


def log_ocr_init_error(log_callback):
    """
    Schreibt EasyOCR-Initialisierungsfehler ins Log.
    Sollte aufgerufen werden, nachdem das Log-System bereit ist.
    
    Args:
        log_callback: Callback-Funktion (typ, message) für UI-Log
    """
    global OCR_INIT_ERROR
    if OCR_INIT_ERROR:
        try:
            error_type, error_msg, details = OCR_INIT_ERROR
            
            # Schreibe ins UI-Log
            log_callback("ERROR", f"EasyOCR: {error_msg}")
            
            # Bei nicht-ImportError auch Details schreiben
            if error_type != "ImportError" and details:
                # Erste Zeile des Tracebacks
                first_line = details.split('\n')[0]
                log_callback("ERROR", f"Details: {first_line}")
        except Exception as e:
            print(f"Konnte EasyOCR-Fehler nicht loggen: {e}")


# PatternManager für konfigurierbare Regex-Patterns
try:
    from services.pattern_manager import PatternManager
    PATTERN_MANAGER = PatternManager()
except Exception as e:
    print(f"Warnung: PatternManager konnte nicht geladen werden: {e}")
    PATTERN_MANAGER = None

# OCR Thread Pool Executor (max 2 parallel OCR jobs)
# Verhindert, dass 10 OCR-Jobs gleichzeitig laufen und System überlasten
OCR_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="OCR-Worker")

# Cache für kompilierte Regex-Patterns (Feature 11: Pattern Compilation Caching)
_COMPILED_PATTERNS_CACHE = {}
_CACHE_MAX_SIZE = 50

# Cache für PDF Page Counts (Feature 14: PDF Page Count Caching)
_PDF_PAGE_COUNT_CACHE = {}
_PDF_CACHE_MAX_SIZE = 500


def _get_compiled_pattern(pattern_name: str, fallback_pattern: str = None) -> Optional[re.Pattern]:
    """
    Holt ein kompiliertes Pattern aus dem Cache oder kompiliert es neu.

    Args:
        pattern_name: Name des Patterns (z.B. "kunden_nr")
        fallback_pattern: Optional Fallback-Pattern wenn PatternManager nicht verfügbar

    Returns:
        Kompiliertes re.Pattern oder None
    """
    # 1. Cache prüfen
    if pattern_name in _COMPILED_PATTERNS_CACHE:
        return _COMPILED_PATTERNS_CACHE[pattern_name]

    # 2. Pattern laden
    pattern_str = None
    if PATTERN_MANAGER:
        pattern_str = PATTERN_MANAGER.get_pattern(pattern_name)

    # 3. Fallback verwenden wenn nötig
    if not pattern_str and fallback_pattern:
        pattern_str = fallback_pattern

    if not pattern_str:
        return None

    # 4. Kompilieren und cachen
    try:
        compiled = re.compile(pattern_str, re.IGNORECASE)
        # Cache Size Limit: max 50 Patterns
        if len(_COMPILED_PATTERNS_CACHE) < _CACHE_MAX_SIZE:
            _COMPILED_PATTERNS_CACHE[pattern_name] = compiled
        return compiled
    except re.error as e:
        print(f"Fehler beim Kompilieren von Pattern '{pattern_name}': {e}")
        return None

# Fallback: Original Patterns (falls PatternManager nicht verfügbar)
# Regex-Patterns für die Extraktion
# Kundennummer: unterstützt "Kunde Nr", "Kd.Nr.", "Kd.-Nr.", "Kundennummer" etc.
PATTERN_KUNDEN_NR = r"(?:Kunde(?:n)?[-\s]*(?:Nr|nummer)|Kd\.?[-\s]*Nr\.?)[:\s]+(\d+)"

# Auftragsnummer: unterstützt "Auftrag Nr", "Werkstatt-Auftrag Nr", "Auftragsnummer" etc.
PATTERN_AUFTRAG_NR = r"(?:Werkstatt[-\s]*)?Auftrag(?:s)?[-\s]*(?:Nr|nummer)\.?[:\s]+(\d+)"

# Datum: DD.MM.YYYY
PATTERN_DATUM = r"(\d{1,2})\.(\d{1,2})\.(\d{4})"

# Kennzeichen: z.B. "SFB-KI 23E", "B-MW 1234"
# Format 1: Nach Label "Kennzeichen: SFB-KI 23E"
# Format 2: Eigenständig in Zeile (1-3 Buchstaben, Bindestrich, 1-2 Buchstaben, Leerzeichen, Zahlen)
PATTERN_KENNZEICHEN = r"(?:(?:Kennzeichen|Amtl\.?\s*Kennzeichen)[:\s]+)?([A-ZÄÖÜ]{1,3}[-\s][A-ZÄÖÜ]{1,2}\s+\d{1,4}\s*[A-Z]?)\b"

# FIN (Fahrgestellnummer): 17-stellige alphanumerische Nummer
# FINs verwenden keine Buchstaben I, O, Q (Verwechslungsgefahr mit 1, 0)
PATTERN_FIN = r"\b([A-HJ-NPR-Z0-9]{17})\b"

# Kundenname: Vor- und Nachname (Großbuchstaben am Anfang)
# Format: "Name: Max Mustermann" oder eigenständig "Max Mustermann"
PATTERN_KUNDENNAME = r"(?:Name[:\s]+)?([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)"

# Dokumenttyp-Keywords
DOCTYPE_KEYWORDS = {
    "Rechnung": ["Rechnung"],
    "KVA": ["Kostenvoranschlag", "KVA"],
    "Auftrag": ["Auftrag"],
    "HU": ["HU", "Hauptuntersuchung"],
    "Garantie": ["Garantie"],
}


def get_pattern(name: str) -> str:
    """
    Holt ein Pattern vom PatternManager oder gibt Fallback zurück.
    
    Args:
        name: Pattern-Name (z.B. "kunden_nr", "auftrag_nr")
        
    Returns:
        Pattern-String
    """
    if PATTERN_MANAGER:
        pattern = PATTERN_MANAGER.get_pattern(name)
        if pattern:
            return pattern
    
    # Fallback auf Original-Patterns
    fallbacks = {
        "kunden_nr": PATTERN_KUNDEN_NR,
        "auftrag_nr": PATTERN_AUFTRAG_NR,
        "datum": PATTERN_DATUM,
        "kennzeichen": PATTERN_KENNZEICHEN,
        "fin": PATTERN_FIN,
        "kunden_name": PATTERN_KUNDENNAME
    }
    return fallbacks.get(name, "")


def extract_text_from_pdf(file_path: str) -> tuple:
    """
    Extrahiert Text aus der ERSTEN SEITE einer PDF-Datei (Feature 14: PDF Page Count Caching).

    WICHTIG: Es wird nur die erste Seite analysiert, da die relevanten
    Informationen (Kundennummer, Auftragsnummer, etc.) dort stehen.
    Die komplette PDF-Datei wird aber trotzdem verschoben/kopiert.

    Args:
        file_path: Pfad zur PDF-Datei

    Returns:
        Tuple (text, page_count) - extrahierter Text und Seitenanzahl
    """
    if not PYMUPDF_AVAILABLE or fitz is None:
        return ("", 0)

    try:
        text = ""
        page_count = 0
        with fitz.open(file_path) as doc:  # type: ignore
            page_count = len(doc)

            # Nur die erste Seite analysieren
            if page_count > 0:
                text = doc[0].get_text()

            # Info ausgeben, wenn mehrseitig
            if page_count > 1:
                print(f"ℹ️  PDF hat {page_count} Seiten - Analysiere nur Seite 1")

        # Cache page count (Feature 14: PDF Page Count Caching)
        if len(_PDF_PAGE_COUNT_CACHE) < _PDF_CACHE_MAX_SIZE:
            _PDF_PAGE_COUNT_CACHE[file_path] = page_count

        return (text, page_count)
    except Exception as e:
        from services.logger import log_error
        error_msg = f"PDF-Text-Extraktion fehlgeschlagen für {os.path.basename(file_path)}: {type(e).__name__}: {e}"
        print(f"❌ {error_msg}")
        log_error(error_msg)
        import traceback
        traceback.print_exc()
        return ("", 0)


def get_pdf_page_count(file_path: str) -> int:
    """
    Ermittelt die Anzahl der Seiten einer PDF-Datei.
    Mit Cache zur Vermeidung von mehrfachem PDF-Öffnen (Feature 14: PDF Page Count Caching).

    Args:
        file_path: Pfad zur PDF-Datei

    Returns:
        Anzahl der Seiten oder 0 bei Fehler
    """
    # 1. Cache prüfen (O(1) Dict-Lookup, spart File I/O!)
    if file_path in _PDF_PAGE_COUNT_CACHE:
        return _PDF_PAGE_COUNT_CACHE[file_path]

    if not PYMUPDF_AVAILABLE or fitz is None:
        return 0

    try:
        with fitz.open(file_path) as doc:  # type: ignore
            page_count = len(doc)
            # Cache für zukünftige Aufrufe
            if len(_PDF_PAGE_COUNT_CACHE) < _PDF_CACHE_MAX_SIZE:
                _PDF_PAGE_COUNT_CACHE[file_path] = page_count
            return page_count
    except Exception as e:
        print(f"Fehler beim Ermitteln der Seitenanzahl: {e}")
        return 0


def extract_text_from_image_ocr(file_path: str) -> str:
    """
    Extrahiert Text aus einem Bild mittels EasyOCR.
    
    Args:
        file_path: Pfad zur Bilddatei
        
    Returns:
        Extrahierter Text oder leerer String bei Fehler
    """
    if not OCR_AVAILABLE or easyocr_reader is None:
        return ""
    
    try:
        result = easyocr_reader.readtext(file_path, detail=0, paragraph=True)
        text = "\n".join(result) if result else ""
        return text
        
    except Exception as e:
        from services.logger import log_error
        error_msg = f"Bild-OCR fehlgeschlagen für {os.path.basename(file_path)}: {type(e).__name__}: {e}"
        print(f"❌ {error_msg}")
        log_error(error_msg)
        import traceback
        traceback.print_exc()
        return ""


def extract_text_from_pdf_ocr(file_path: str) -> str:
    """
    Extrahiert Text aus der ERSTEN SEITE einer PDF-Datei mittels EasyOCR (für gescannte PDFs).

    WICHTIG: Es wird nur die erste Seite analysiert, da die relevanten
    Informationen (Kundennummer, Auftragsnummer, etc.) dort stehen.
    Die komplette PDF-Datei wird aber trotzdem verschoben/kopiert.

    Args:
        file_path: Pfad zur PDF-Datei

    Returns:
        Extrahierter Text oder leerer String bei Fehler
    """
    if not OCR_AVAILABLE or easyocr_reader is None:
        return ""

    try:
        # pdf2image für PDF->Bild Konvertierung
        try:
            from pdf2image import convert_from_path
        except ImportError:
            print("⚠️  pdf2image nicht verfügbar. Installiere: pip install pdf2image")
            return ""
        
        # Konvertiere PDF zu Bildern (nur erste Seite)
        images = convert_from_path(file_path, first_page=1, last_page=1)
        text = ""

        if len(images) > 0:
            # Speichere temporär als Bild für EasyOCR
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                images[0].save(tmp.name, "PNG")
                result = easyocr_reader.readtext(tmp.name, detail=0, paragraph=True)
                text = "\n".join(result) if result else ""
                os.unlink(tmp.name)
            print(f"ℹ️  PDF-OCR: Analysiere nur Seite 1")

        return text
        
    except Exception as e:
        from services.logger import log_error
        error_msg = f"PDF-OCR fehlgeschlagen für {os.path.basename(file_path)}: {type(e).__name__}: {e}"
        print(f"❌ {error_msg}")
        log_error(error_msg)
        import traceback
        traceback.print_exc()
        return ""


def extract_text(file_path: str) -> str:
    """
    Extrahiert Text aus einer Datei (PDF oder Bild).

    Args:
        file_path: Pfad zur Datei

    Returns:
        Extrahierter Text
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        # Erst normalen PDF-Text versuchen (Feature 14: returns tuple with page count)
        text, page_count = extract_text_from_pdf(file_path)

        # Falls kein Text gefunden, OCR versuchen
        if not text.strip():
            text = extract_text_from_pdf_ocr(file_path)

        return text

    elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        return extract_text_from_image_ocr(file_path)

    return ""


def extract_text_async(file_paths: list) -> Dict[str, str]:
    """
    Extrahiert Text aus mehreren Dateien ASYNCHRON mit ThreadPool (nicht blockierend).
    Perfekt für Batch-Verarbeitung von vielen Dokumenten ohne GUI-Blockierung.

    Args:
        file_paths: Liste von Dateipfaden

    Returns:
        Dictionary: {file_path: extracted_text}
    """
    results = {}

    # Submit all extraction jobs to thread pool
    future_to_path = {
        OCR_EXECUTOR.submit(extract_text, fp): fp
        for fp in file_paths
    }

    # Collect results as they complete (streaming)
    for future in as_completed(future_to_path):
        file_path = future_to_path[future]
        try:
            text = future.result()
            results[file_path] = text
        except Exception as e:
            print(f"⚠ Fehler beim Extrahieren von {file_path}: {e}")
            results[file_path] = ""

    return results


def extract_kundennummer(text: str) -> Optional[str]:
    """Extrahiert die Kundennummer aus dem Text."""
    pattern = _get_compiled_pattern("kunden_nr", PATTERN_KUNDEN_NR)
    if not pattern:
        return None
    match = pattern.search(text)
    return match.group(1) if match else None


def extract_auftragsnummer(text: str) -> Optional[str]:
    """Extrahiert die Auftragsnummer aus dem Text."""
    pattern = _get_compiled_pattern("auftrag_nr", PATTERN_AUFTRAG_NR)
    if not pattern:
        return None
    match = pattern.search(text)
    return match.group(1) if match else None


def extract_kennzeichen(text: str) -> Optional[str]:
    """Extrahiert das Kennzeichen aus dem Text."""
    pattern = _get_compiled_pattern("kennzeichen", PATTERN_KENNZEICHEN)
    if not pattern:
        return None
    match = pattern.search(text)
    if match:
        # Normalisiere: Entferne überflüssige Leerzeichen
        kennzeichen = match.group(1).strip()
        kennzeichen = re.sub(r'\s+', ' ', kennzeichen)
        # Validierung: Muss Bindestrich enthalten und Zahlen am Ende haben
        if '-' in kennzeichen and re.search(r'\d', kennzeichen):
            return kennzeichen
    return None


def extract_fin(text: str) -> Optional[str]:
    """Extrahiert die FIN (Fahrgestellnummer) aus dem Text."""
    # Suche alle 17-Zeichen-Kombinationen
    pattern = _get_compiled_pattern("fin", PATTERN_FIN)
    if not pattern:
        return None
    for match in pattern.finditer(text):
        fin = match.group(1).upper().strip()
        # Validierung: FIN muss genau 17 Zeichen haben UND Ziffern enthalten
        # (verhindert false positives wie "VERTRAGSWERKSTATT")
        if len(fin) == 17 and re.search(r'\d', fin):
            return fin
    return None


def extract_kundenname(text: str) -> Optional[str]:
    """Extrahiert den Kundennamen aus dem Text."""
    # Versuche zuerst mit "Name:" Label
    pattern_with_label = _get_compiled_pattern("kundenname", r"Name[:\s]+([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)")
    if pattern_with_label:
        match = pattern_with_label.search(text)
        if match:
            name = match.group(1).strip()
            # Filter: Ignoriere häufige False Positives
            if name.lower() not in ['straße nr', 'telefon mobil', 'werkstatt auftrag']:
                return name

    # Fallback: Suche nach typischen Vor-/Nachnamen-Mustern
    # (z.B. "Anne Schultze" nach Adressfeldern)
    pattern_fallback = _get_compiled_pattern("kundenname_fallback", r'^[A-ZÄÖÜ][a-zäöüß]+(\s+[A-ZÄÖÜ][a-zäöüß]+){1,3}$')
    if pattern_fallback:
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            # Suche nach Zeile mit nur Vor- und Nachname (2-4 Wörter)
            if pattern_fallback.match(line):
                words = line.split()
                # Mindestens 2 Wörter (Vor- und Nachname)
                if len(words) >= 2:
                    return line

    return None


def extract_datum(text: str) -> Optional[int]:
    """Extrahiert das erste Datum und gibt das Jahr zurück."""
    pattern = _get_compiled_pattern("datum", PATTERN_DATUM)
    if not pattern:
        return None
    match = pattern.search(text)
    if match:
        # Das Pattern kann entweder 3 Gruppen (TT, MM, JJJJ) oder 1 Gruppe (TT.MM.JJJJ) haben
        if match.lastindex and match.lastindex >= 3:
            # Altes Format mit 3 separaten Gruppen
            jahr = int(match.group(3))
        else:
            # Neues Format mit einer Gruppe - extrahiere Jahr aus String
            datum_str = match.group(1)
            # Jahr ist der letzte Teil nach . oder /
            jahr_match = re.search(r'(\d{2,4})$', datum_str)
            if not jahr_match:
                return None
            jahr = int(jahr_match.group(1))
            # 2-stelliges Jahr zu 4-stellig konvertieren
            if jahr < 100:
                jahr = 2000 + jahr if jahr <= 50 else 1900 + jahr

        # Plausibilitätsprüfung
        current_year = datetime.now().year
        if 2000 <= jahr <= current_year + 1:
            return jahr
    return None


def extract_dokument_typ(text: str) -> str:
    """
    Bestimmt den Dokumenttyp anhand von Keywords.
    
    Returns:
        Dokumenttyp oder "Dokument" als Standard
    """
    text_lower = text.lower()
    
    for doc_type, keywords in DOCTYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return doc_type
    
    return "Dokument"


def calculate_confidence(kunden_nr: Optional[str], auftrag_nr: Optional[str], 
                        dokument_typ: str, jahr: Optional[int]) -> float:
    """
    Berechnet einen Confidence-Score basierend auf erkannten Daten.
    
    Heuristik:
    - +0.4 wenn Kundennummer erkannt
    - +0.3 wenn Auftragsnummer erkannt
    - +0.2 wenn Dokumenttyp ≠ "Dokument"
    - +0.1 wenn Jahr plausibel
    
    Returns:
        Confidence-Score zwischen 0.0 und 1.0
    """
    confidence = 0.0
    
    if kunden_nr:
        confidence += 0.4
    
    if auftrag_nr:
        confidence += 0.3
    
    if dokument_typ != "Dokument":
        confidence += 0.2
    
    if jahr:
        confidence += 0.1
    
    return min(confidence, 1.0)


def analyze_document(file_path: str,
                    vorlage_name: Optional[str] = None,
                    vorlagen_manager: Optional[VorlagenManager] = None,
                    legacy_resolver=None) -> Dict[str, Any]:
    """
    Analysiert ein Dokument und extrahiert Metadaten.
    
    Neu: Unterstützt Legacy-Aufträge ohne Kundennummer.
    
    Args:
        file_path: Pfad zur Dokumentdatei
        vorlage_name: Name der zu verwendenden Vorlage (optional)
        vorlagen_manager: VorlagenManager-Instanz (optional)
        legacy_resolver: LegacyResolver-Instanz für Altaufträge (optional)
        
    Returns:
        Dictionary mit Analyseergebnissen:
        {
            "kunden_nr": str | None,
            "kunden_name": str | None,
            "auftrag_nr": str | None,
            "dokument_typ": str,
            "jahr": int | None,
            "kennzeichen": str | None,
            "fin": str | None,
            "confidence": float,
            "hinweis": str | None,
            "vorlage_verwendet": str | None,
            "is_legacy": bool,  # NEU: True wenn Legacy-Auftrag
            "legacy_match_reason": str | None  # NEU: "fin", "name_plus_details", "unclear"
        }
    """
    from services.logger import log_error, log_info
    
    # Validierung
    if not os.path.exists(file_path):
        error_msg = f"Datei nicht gefunden: {file_path}"
        print(f"❌ {error_msg}")
        log_error(error_msg)
        return {
            "kunden_nr": None,
            "kunden_name": None,
            "auftrag_nr": None,
            "dokument_typ": "Unbekannt",
            "jahr": None,
            "kennzeichen": None,
            "fin": None,
            "confidence": 0.0,
            "hinweis": error_msg,
            "vorlage_verwendet": None,
            "is_legacy": False,
            "legacy_match_reason": None,
            "page_count": 0,
        }
    
    print(f"🔍 Analysiere: {os.path.basename(file_path)}")
    log_info(f"Starte Analyse: {file_path}")
    
    # Text extrahieren
    try:
        text = extract_text(file_path)
        if text:
            print(f"   ✓ Text extrahiert: {len(text)} Zeichen")
        else:
            print(f"   ⚠️  Kein Text extrahiert!")
            log_error(f"Keine Textextraktion möglich für {file_path}")
    except Exception as e:
        error_msg = f"Textextraktion fehlgeschlagen für {os.path.basename(file_path)}: {type(e).__name__}: {e}"
        print(f"❌ {error_msg}")
        log_error(error_msg)
        import traceback
        traceback.print_exc()
        text = ""

    # Seitenanzahl ermitteln (nur für PDFs)
    page_count = 0
    if file_path.lower().endswith('.pdf'):
        page_count = get_pdf_page_count(file_path)

    # Metadaten extrahieren mit Vorlage (wenn vorhanden)
    if vorlagen_manager:
        vorlage_result = vorlagen_manager.analyze_with_vorlage(text, vorlage_name)
        kunden_nr = vorlage_result["kunden_nr"]
        auftrag_nr = vorlage_result["auftrag_nr"]
        jahr = vorlage_result["jahr"]
        dokument_typ = vorlage_result["dokument_typ"]
        vorlage_verwendet = vorlage_result["vorlage_verwendet"]
    else:
        # Fallback auf alte Methode
        kunden_nr = extract_kundennummer(text)
        auftrag_nr = extract_auftragsnummer(text)
        jahr = extract_datum(text)
        dokument_typ = extract_dokument_typ(text)
        vorlage_verwendet = "Standard (Legacy)"
    
    # Zusätzliche Felder extrahieren (unabhängig von Vorlage)
    kunden_name = extract_kundenname(text)
    kennzeichen = extract_kennzeichen(text)
    fin = extract_fin(text)
    
    # NEU: Legacy-Workflow - Falls keine Kundennummer gefunden
    is_legacy = False
    legacy_match_reason = None
    hinweis = None  # Initialisiere hinweis
    
    if not kunden_nr and legacy_resolver:
        # Dies ist ein Legacy-Auftrag ohne Kundennummer
        is_legacy = True
        
        # Versuche Legacy-Auflösung
        legacy_match = legacy_resolver.resolve_legacy_customer({
            "kunden_name": kunden_name,
            "fin": fin,
            "kennzeichen": kennzeichen,
            "plz": None,  # TODO: PLZ-Extraktion hinzufügen falls benötigt
            "adresse": None  # TODO: Adress-Extraktion hinzufügen falls benötigt
        })
        
        if legacy_match.kunden_nr:
            # Erfolgreiche Zuordnung
            kunden_nr = legacy_match.kunden_nr
            legacy_match_reason = legacy_match.match_reason
            hinweis = f"Legacy-Auftrag: {legacy_match.confidence_detail}"
        else:
            # Keine eindeutige Zuordnung
            legacy_match_reason = legacy_match.match_reason
            hinweis = f"Legacy-Auftrag unklar: {legacy_match.confidence_detail}"
    
    # Confidence berechnen
    confidence = calculate_confidence(kunden_nr, auftrag_nr, dokument_typ, jahr)
    
    # Hinweis erstellen (wenn noch nicht von Legacy-Workflow gesetzt)
    if not hinweis:
        if not text.strip():
            hinweis = "Kein Text extrahierbar"
        elif not kunden_nr and not is_legacy:
            hinweis = "Keine Kundennummer gefunden"
    
    result = {
        "kunden_nr": kunden_nr,
        "kunden_name": kunden_name,
        "auftrag_nr": auftrag_nr,
        "dokument_typ": dokument_typ,
        "jahr": jahr,
        "kennzeichen": kennzeichen,
        "fin": fin,
        "confidence": confidence,
        "hinweis": hinweis,
        "vorlage_verwendet": vorlage_verwendet,
        "is_legacy": is_legacy,
        "legacy_match_reason": legacy_match_reason,
        "page_count": page_count,  # NEU: Seitenanzahl (nur PDFs, sonst 0)
    }
    
    return result

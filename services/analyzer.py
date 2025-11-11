"""
Dokumentanalyse für WerkstattArchiv.
Extrahiert Text aus PDFs und Bildern und analysiert Metadaten.
"""

import re
import os
from typing import Dict, Optional, Any
from datetime import datetime

from services.vorlagen import VorlagenManager

# Type-Hints für optionale Imports
fitz = None
pytesseract = None
convert_from_path = None
Image = None

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Warnung: PyMuPDF nicht verfügbar. PDF-Textextraktion eingeschränkt.")

try:
    import pytesseract  # type: ignore
    from pdf2image import convert_from_path  # type: ignore
    from PIL import Image  # type: ignore
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warnung: pytesseract/pdf2image nicht verfügbar. OCR nicht möglich.")


# Regex-Patterns für die Extraktion
# Kundennummer: unterstützt "Kunde Nr", "Kd.Nr.", "Kd.-Nr.", "Kundennummer" etc.
PATTERN_KUNDEN_NR = r"(?:Kunde(?:n)?[-\s]*(?:Nr|nummer)|Kd\.?[-\s]*Nr\.?)[:\s]+(\d+)"

# Auftragsnummer: unterstützt "Auftrag Nr", "Werkstatt-Auftrag Nr", "Auftragsnummer" etc.
PATTERN_AUFTRAG_NR = r"(?:Werkstatt[-\s]*)?Auftrag(?:s)?[-\s]*(?:Nr|nummer)\.?[:\s]+(\d+)"

# Datum: DD.MM.YYYY
PATTERN_DATUM = r"(\d{1,2})\.(\d{1,2})\.(\d{4})"

# Dokumenttyp-Keywords
DOCTYPE_KEYWORDS = {
    "Rechnung": ["Rechnung"],
    "KVA": ["Kostenvoranschlag", "KVA"],
    "Auftrag": ["Auftrag"],
    "HU": ["HU", "Hauptuntersuchung"],
    "Garantie": ["Garantie"],
}


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extrahiert Text aus einer PDF-Datei.
    
    Args:
        file_path: Pfad zur PDF-Datei
        
    Returns:
        Extrahierter Text oder leerer String bei Fehler
    """
    if not PYMUPDF_AVAILABLE or fitz is None:
        return ""
    
    try:
        text = ""
        with fitz.open(file_path) as doc:  # type: ignore
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        print(f"Fehler beim PDF-Text-Extrahieren: {e}")
        return ""


def extract_text_from_image_ocr(file_path: str, tesseract_path: Optional[str] = None) -> str:
    """
    Extrahiert Text aus einem Bild mittels OCR.
    
    Args:
        file_path: Pfad zur Bilddatei
        tesseract_path: Optionaler Pfad zur Tesseract-Installation
        
    Returns:
        Extrahierter Text oder leerer String bei Fehler
    """
    if not OCR_AVAILABLE or pytesseract is None or Image is None:
        return ""
    
    try:
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path  # type: ignore
        
        image = Image.open(file_path)  # type: ignore
        text = pytesseract.image_to_string(image, lang="deu")  # type: ignore
        return text
    except Exception as e:
        print(f"Fehler beim OCR: {e}")
        return ""


def extract_text_from_pdf_ocr(file_path: str, tesseract_path: Optional[str] = None) -> str:
    """
    Extrahiert Text aus einer PDF-Datei mittels OCR (für gescannte PDFs).
    
    Args:
        file_path: Pfad zur PDF-Datei
        tesseract_path: Optionaler Pfad zur Tesseract-Installation
        
    Returns:
        Extrahierter Text oder leerer String bei Fehler
    """
    if not OCR_AVAILABLE or pytesseract is None or convert_from_path is None:
        return ""
    
    try:
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path  # type: ignore
        
        # Konvertiere PDF zu Bildern
        images = convert_from_path(file_path)  # type: ignore
        text = ""
        
        for image in images:
            text += pytesseract.image_to_string(image, lang="deu")  # type: ignore
            text += "\n"
        
        return text
    except Exception as e:
        print(f"Fehler beim PDF-OCR: {e}")
        return ""


def extract_text(file_path: str, tesseract_path: Optional[str] = None) -> str:
    """
    Extrahiert Text aus einer Datei (PDF oder Bild).
    
    Args:
        file_path: Pfad zur Datei
        tesseract_path: Optionaler Pfad zur Tesseract-Installation
        
    Returns:
        Extrahierter Text
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        # Erst normalen PDF-Text versuchen
        text = extract_text_from_pdf(file_path)
        
        # Falls kein Text gefunden, OCR versuchen
        if not text.strip():
            text = extract_text_from_pdf_ocr(file_path, tesseract_path)
        
        return text
    
    elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        return extract_text_from_image_ocr(file_path, tesseract_path)
    
    return ""


def extract_kunden_nr(text: str) -> Optional[str]:
    """Extrahiert die Kundennummer aus dem Text."""
    match = re.search(PATTERN_KUNDEN_NR, text, re.IGNORECASE)
    return match.group(1) if match else None


def extract_auftrag_nr(text: str) -> Optional[str]:
    """Extrahiert die Auftragsnummer aus dem Text."""
    match = re.search(PATTERN_AUFTRAG_NR, text, re.IGNORECASE)
    return match.group(1) if match else None


def extract_datum(text: str) -> Optional[int]:
    """Extrahiert das erste Datum und gibt das Jahr zurück."""
    match = re.search(PATTERN_DATUM, text)
    if match:
        jahr = int(match.group(3))
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


def analyze_document(file_path: str, tesseract_path: Optional[str] = None, 
                    vorlage_name: Optional[str] = None,
                    vorlagen_manager: Optional[VorlagenManager] = None) -> Dict[str, Any]:
    """
    Analysiert ein Dokument und extrahiert Metadaten.
    
    Args:
        file_path: Pfad zur Dokumentdatei
        tesseract_path: Optionaler Pfad zur Tesseract-Installation
        vorlage_name: Name der zu verwendenden Vorlage (optional)
        vorlagen_manager: VorlagenManager-Instanz (optional)
        
    Returns:
        Dictionary mit Analyseergebnissen:
        {
            "kunden_nr": str | None,
            "kunden_name": str | None,  # wird später vom Router gesetzt
            "auftrag_nr": str | None,
            "dokument_typ": str,
            "jahr": int | None,
            "confidence": float,
            "hinweis": str | None,
            "vorlage_verwendet": str | None
        }
    """
    # Text extrahieren
    text = extract_text(file_path, tesseract_path)
    
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
        kunden_nr = extract_kunden_nr(text)
        auftrag_nr = extract_auftrag_nr(text)
        jahr = extract_datum(text)
        dokument_typ = extract_dokument_typ(text)
        vorlage_verwendet = "Standard (Legacy)"
    
    # Confidence berechnen
    confidence = calculate_confidence(kunden_nr, auftrag_nr, dokument_typ, jahr)
    
    # Hinweis erstellen
    hinweis = None
    if not text.strip():
        hinweis = "Kein Text extrahierbar"
    elif not kunden_nr:
        hinweis = "Keine Kundennummer gefunden"
    
    result = {
        "kunden_nr": kunden_nr,
        "kunden_name": None,  # Wird später vom Router gesetzt
        "auftrag_nr": auftrag_nr,
        "dokument_typ": dokument_typ,
        "jahr": jahr,
        "confidence": confidence,
        "hinweis": hinweis,
        "vorlage_verwendet": vorlage_verwendet,
    }
    
    return result

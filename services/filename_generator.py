"""
Hilfsfunktion: Generiert standardisierte Dateinamen für das Archiv.
"""
from datetime import datetime
from typing import Dict, Any, Optional
import re


def generate_filename(analysis_result: Dict[str, Any], 
                     timestamp: Optional[str] = None) -> str:
    """
    Generiert Dateinamen nach Schema:
    [Auftragsnummer]_[Dokumenttyp]_[Datum]_[FIN oder Kennzeichen]_[KundeKurz]_[Zeitstempel].pdf
    
    Beispiele:
    - 78708_Auftrag_20251111_VR7BCZKXCME033281_Schultze_20251111_143022.pdf
    - 11_Auftrag_20251007_SFB-KI-23E_Schultze_20251111_143022.pdf
    
    Args:
        analysis_result: Dictionary mit extrahierten Daten
        timestamp: Optionaler Zeitstempel (default: aktuell)
        
    Returns:
        Generierter Dateiname
    """
    # Zeitstempel (YYYYMMDD_HHMMSS)
    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Auftragsnummer (erforderlich, sonst "UNBEKANNT")
    auftrag_nr = analysis_result.get("auftrag_nr", "UNBEKANNT")
    
    # 2. Dokumenttyp (Auftrag, Rechnung, KVA, etc.)
    dokument_typ = analysis_result.get("dokument_typ", "Dokument")
    
    # 3. Datum (YYYYMMDD aus Jahr, ansonsten aus Zeitstempel)
    jahr = analysis_result.get("jahr")
    if jahr:
        # Wir haben nur das Jahr, nehmen 01.01. als Platzhalter
        datum_str = f"{jahr}0101"
    else:
        # Kein Jahr vorhanden, nutze heutiges Datum
        datum_str = datetime.now().strftime("%Y%m%d")
    
    # 4. FIN oder Kennzeichen (FIN hat Vorrang)
    fin = analysis_result.get("fin")
    kennzeichen = analysis_result.get("kennzeichen")
    
    if fin:
        fahrzeug_id = fin
    elif kennzeichen:
        # Bereinige Kennzeichen: Ersetze Leerzeichen durch Bindestrich
        fahrzeug_id = kennzeichen.replace(" ", "-")
    else:
        fahrzeug_id = "KEIN-FZG"
    
    # 5. Kunde Kurz (Nachname oder ersten 10 Zeichen)
    kunden_name = analysis_result.get("kunden_name")
    if kunden_name:
        # Extrahiere Nachname (letztes Wort)
        name_parts = kunden_name.strip().split()
        kunde_kurz = name_parts[-1] if name_parts else "UNBEKANNT"
        # Bereinige: Nur Buchstaben, max 15 Zeichen
        kunde_kurz = re.sub(r'[^a-zA-ZäöüÄÖÜß]', '', kunde_kurz)[:15]
    else:
        kunde_kurz = "UNBEKANNT"
    
    # 6. Zeitstempel
    zeitstempel = timestamp.replace("-", "").replace(":", "").replace(" ", "_")
    
    # Dateiname zusammensetzen
    filename = f"{auftrag_nr}_{dokument_typ}_{datum_str}_{fahrzeug_id}_{kunde_kurz}_{zeitstempel}.pdf"
    
    # Sicherheit: Bereinige problematische Zeichen
    filename = filename.replace("/", "-").replace("\\", "-")
    
    return filename


def generate_short_filename(analysis_result: Dict[str, Any]) -> str:
    """
    Generiert einen kurzen, lesbaren Dateinamen ohne Zeitstempel.
    Gut für manuelle Bearbeitung oder Vorschau.
    
    Format: [Auftragsnummer]_[Dokumenttyp]_[Jahr].pdf
    Beispiel: 78708_Auftrag_2025.pdf
    """
    auftrag_nr = analysis_result.get("auftrag_nr", "UNBEKANNT")
    dokument_typ = analysis_result.get("dokument_typ", "Dokument")
    jahr = analysis_result.get("jahr", datetime.now().year)
    
    return f"{auftrag_nr}_{dokument_typ}_{jahr}.pdf"


# Test der Funktion
if __name__ == "__main__":
    # Test mit Beispieldaten
    test_data_alt = {
        "auftrag_nr": "78708",
        "dokument_typ": "Auftrag",
        "jahr": 2025,
        "kunden_name": "Anne Schultze",
        "kennzeichen": "SFB-KI 23E",
        "fin": "VR7BCZKXCME033281"
    }
    
    test_data_neu = {
        "auftrag_nr": "11",
        "dokument_typ": "Auftrag",
        "jahr": 2025,
        "kunden_name": "Anne Schultze",
        "kennzeichen": "SFB-KI 23E",
        "fin": "VR7BCZKXCME033281"
    }
    
    print("Test: Dateinamen-Generierung")
    print("="*80)
    print(f"\nAltes System (auftrag.pdf):")
    print(f"  Lang:  {generate_filename(test_data_alt, '20251111_143022')}")
    print(f"  Kurz:  {generate_short_filename(test_data_alt)}")
    
    print(f"\nNeues System (Schultze.pdf):")
    print(f"  Lang:  {generate_filename(test_data_neu, '20251111_143530')}")
    print(f"  Kurz:  {generate_short_filename(test_data_neu)}")

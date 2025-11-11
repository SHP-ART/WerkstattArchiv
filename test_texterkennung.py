#!/usr/bin/env python3
"""
Test-Script für die Texterkennung der Beispiel-Auftragsdateien
"""

import sys
import os

# Füge das Projekt-Verzeichnis zum Python-Path hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.analyzer import analyze_document
from services.vorlagen import VorlagenManager

def test_pdf_erkennung(pdf_path):
    """Testet die Texterkennung für eine PDF-Datei"""
    print(f"\n{'='*80}")
    print(f"Analysiere: {os.path.basename(pdf_path)}")
    print(f"{'='*80}\n")
    
    # VorlagenManager initialisieren
    vorlagen_manager = VorlagenManager()
    
    try:
        # Dokument analysieren
        result = analyze_document(pdf_path, vorlagen_manager=vorlagen_manager)
        
        # Erst den Text separat extrahieren für die Anzeige
        from services.analyzer import extract_text
        text = extract_text(pdf_path)
        
        # Extrahierten Text anzeigen (erste 500 Zeichen)
        print("📄 EXTRAHIERTER TEXT (Auszug):")
        print("-" * 80)
        text_preview = text[:500] if len(text) > 500 else text
        print(text_preview)
        if len(text) > 500:
            print(f"\n... ({len(text)} Zeichen insgesamt)")
        print("-" * 80)
        
        # Erkannte Daten anzeigen
        print("\n🔍 ERKANNTE DATEN:")
        print("-" * 80)
        print(f"Kundennummer:   {result['kunden_nr'] or '❌ NICHT GEFUNDEN'}")
        print(f"Kundenname:     {result['kunden_name'] or '(wird später zugeordnet)'}")
        print(f"Auftragsnummer: {result['auftrag_nr'] or '❌ NICHT GEFUNDEN'}")
        print(f"Jahr:           {result['jahr'] or '❌ NICHT GEFUNDEN'}")
        print(f"Dokumenttyp:    {result['dokument_typ']}")
        print(f"Confidence:     {result['confidence']:.1%}")
        print(f"Verwendete Vorlage: {result.get('vorlage_verwendet', 'Standard')}")
        if result['hinweis']:
            print(f"⚠️  Hinweis:     {result['hinweis']}")
        print("-" * 80)
        
        # Empfehlung
        if result['confidence'] >= 0.7:
            print("\n✅ GUTE ERKENNUNG - Dokument kann automatisch sortiert werden")
        elif result['confidence'] >= 0.4:
            print("\n⚠️  UNSICHERE ERKENNUNG - Manuelle Prüfung empfohlen")
        else:
            print("\n❌ SCHLECHTE ERKENNUNG - Manuelle Bearbeitung erforderlich")
            
    except Exception as e:
        print(f"\n❌ FEHLER bei der Analyse: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Hauptfunktion"""
    print("\n" + "="*80)
    print("WerkstattArchiv - Texterkennung Test")
    print("="*80)
    
    beispiel_ordner = os.path.join(os.path.dirname(__file__), 'beispiel_auftraege')
    
    # Alle PDFs im Beispiel-Ordner finden
    pdf_dateien = [
        os.path.join(beispiel_ordner, f) 
        for f in os.listdir(beispiel_ordner) 
        if f.endswith('.pdf')
    ]
    
    if not pdf_dateien:
        print("\n❌ Keine PDF-Dateien im Ordner 'beispiel_auftraege' gefunden!")
        return
    
    print(f"\nGefundene PDF-Dateien: {len(pdf_dateien)}")
    
    # Jede PDF analysieren
    for pdf_path in pdf_dateien:
        test_pdf_erkennung(pdf_path)
    
    print(f"\n{'='*80}")
    print("Test abgeschlossen!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()

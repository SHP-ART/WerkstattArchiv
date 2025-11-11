"""
Test: Erweiterte Datenextraktion aus PDFs
"""
import os
from services.analyzer import analyze_document
from services.vorlagen import VorlagenManager

# Initialisiere VorlagenManager
vorlagen_manager = VorlagenManager()

# Beispiel-PDFs
pdf_dateien = [
    "beispiel_auftraege/auftrag.pdf",
    "beispiel_auftraege/Schultze.pdf"
]

print("="*80)
print("TEST: ERWEITERTE DATENEXTRAKTION")
print("="*80)

for pdf_datei in pdf_dateien:
    if not os.path.exists(pdf_datei):
        print(f"\n⚠️  {pdf_datei} nicht gefunden")
        continue
    
    print(f"\n{'='*80}")
    print(f"📄 {os.path.basename(pdf_datei)}")
    print('='*80)
    
    result = analyze_document(pdf_datei, vorlagen_manager=vorlagen_manager)
    
    print(f"\n📋 EXTRAHIERTE DATEN:")
    print("-"*80)
    print(f"Auftragsnummer:     {result['auftrag_nr'] or '❌ nicht gefunden'}")
    print(f"Auftragsdatum:      {result['jahr'] or '❌ nicht gefunden'}")
    print(f"Kundennummer:       {result['kunden_nr'] or '❌ nicht gefunden'}")
    print(f"Kundenname:         {result['kunden_name'] or '❌ nicht gefunden'}")
    print(f"Kennzeichen:        {result['kennzeichen'] or '❌ nicht gefunden'}")
    print(f"FIN:                {result['fin'] or '❌ nicht gefunden'}")
    print(f"\n📊 ZUSATZINFO:")
    print("-"*80)
    print(f"Dokumenttyp:        {result['dokument_typ']}")
    print(f"Confidence:         {result['confidence']*100:.1f}%")
    print(f"Vorlage:            {result.get('vorlage_verwendet', 'N/A')}")
    if result.get('hinweis'):
        print(f"Hinweis:            {result['hinweis']}")

print("\n" + "="*80)
print("TEST ABGESCHLOSSEN")
print("="*80)

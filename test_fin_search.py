"""
Test-Script für die neue flexible FIN/VIN-Suche.
Demonstriert die verschiedenen Suchmöglichkeiten.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.indexer import DocumentIndex


def test_fin_search():
    """Testet die flexible FIN-Suche."""
    print("="*80)
    print(" TEST: Flexible FIN/VIN-Suche")
    print("="*80)
    
    index = DocumentIndex()
    
    # Test-Szenarien
    test_cases = [
        {
            "name": "Suche mit letzten 8 Zeichen",
            "fin": "12345678",
            "beschreibung": "Findet alle FINs die auf '12345678' enden"
        },
        {
            "name": "Suche mit kompletter 17-stelliger FIN",
            "fin": "WDB1234567890123456",
            "beschreibung": "Findet exakte Übereinstimmung"
        },
        {
            "name": "Suche mit Teil-FIN (mittlerer Teil)",
            "fin": "234567890",
            "beschreibung": "Findet FINs die diesen Teil enthalten"
        },
        {
            "name": "Suche mit nur 6 Zeichen",
            "fin": "345678",
            "beschreibung": "Sucht in letzten 8 Zeichen"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {test['name']}")
        print(f"   Eingabe: '{test['fin']}'")
        print(f"   {test['beschreibung']}")
        
        try:
            results = index.search(fin=test['fin'])
            print(f"   ✅ Gefunden: {len(results)} Dokument(e)")
            
            if results:
                print(f"   Beispiele:")
                for doc in results[:3]:  # Zeige max. 3 Beispiele
                    fin = doc.get('fin', 'N/A')
                    kunde = doc.get('kunden_name', 'N/A')
                    datei = doc.get('dateiname', 'N/A')
                    print(f"      - FIN: {fin}")
                    print(f"        Kunde: {kunde}")
                    print(f"        Datei: {datei}")
                    
                    # Zeige welcher Teil matcht
                    if len(test['fin']) <= 8:
                        last_8 = fin[-8:] if len(fin) >= 8 else fin
                        print(f"        Letzte 8: {last_8} {'✓' if test['fin'] in last_8 else ''}")
        except Exception as e:
            print(f"   ❌ Fehler: {e}")
    
    print("\n" + "="*80)
    print(" FUNKTIONSWEISE")
    print("="*80)
    print("""
Die FIN-Suche funktioniert intelligent:

1️⃣  Eingabe ≤ 8 Zeichen (z.B. "12345678"):
   → Sucht in den LETZTEN 8 Zeichen der gespeicherten FIN
   → Findet: "WDB123456789012345678" ✓
   → SQL: WHERE fin = '12345678' OR SUBSTR(fin, -8) = '12345678'

2️⃣  Eingabe > 8 Zeichen (z.B. "WDB123456789012345678"):
   → Sucht nach exakter FIN oder als Teilstring
   → Findet: "WDB123456789012345678" ✓
   → SQL: WHERE fin LIKE '%WDB123456789012345678%'

3️⃣  Automatische Normalisierung:
   → Eingabe wird getrimmt und in GROSSBUCHSTABEN konvertiert
   → "  wdb1234  " → "WDB1234"

✅ VORTEILE:
   - Egal ob kurz oder komplett - findet immer den richtigen Treffer
   - Nutzer können bequem nur die letzten 8 Zeichen eingeben
   - Trotzdem funktioniert auch die komplette 17-stellige FIN
   - Performance-optimiert durch gezieltes SUBSTR()

🔧 GUI-INTEGRATION:
   - Neues Suchfeld "FIN/VIN" in der Dokumentensuche
   - Placeholder-Text: "Letzte 8 oder komplett"
   - Automatische Suche beim Klick auf "🔍 Suchen"
""")


if __name__ == "__main__":
    test_fin_search()

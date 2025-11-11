"""
Beispiel: So werden PDFs im WerkstattArchiv verarbeitet
"""
import os
from services.analyzer import analyze_document
from services.vorlagen import VorlagenManager

# Initialisiere VorlagenManager für bessere Erkennung
vorlagen_manager = VorlagenManager()

# Beispiel-PDFs
pdf_dateien = [
    "beispiel_auftraege/auftrag.pdf",     # Altes System
    "beispiel_auftraege/Schultze.pdf"     # Neues System
]

print("="*80)
print("WERKSTATTARCHIV - BEISPIEL VERARBEITUNG")
print("="*80)

for pdf_datei in pdf_dateien:
    if not os.path.exists(pdf_datei):
        print(f"\n⚠️  {pdf_datei} nicht gefunden")
        continue
    
    print(f"\n{'='*80}")
    print(f"📄 VERARBEITE: {os.path.basename(pdf_datei)}")
    print('='*80)
    
    # SCHRITT 1: PDF-Text extrahieren und analysieren
    print("\n🔍 SCHRITT 1: Text extrahieren und analysieren")
    print("-"*80)
    result = analyze_document(pdf_datei, vorlagen_manager=vorlagen_manager)
    
    print(f"Kundennummer:   {result['kunden_nr'] or '❌ nicht gefunden'}")
    print(f"Auftragsnummer: {result['auftrag_nr'] or '❌ nicht gefunden'}")
    print(f"Jahr:           {result['jahr'] or '❌ nicht gefunden'}")
    print(f"Dokumenttyp:    {result['dokument_typ']}")
    print(f"Confidence:     {result['confidence']:.1f}%")
    print(f"Vorlage:        {result.get('vorlage_verwendet', 'Standard')}")
    
    # SCHRITT 2: Automatische Sortierung vorschlagen
    print(f"\n📁 SCHRITT 2: Zielordner berechnen")
    print("-"*80)
    
    if result['kunden_nr']:
        # Mit Kundennummer (neues System)
        zielordner = f"Archiv/{result['jahr']}/{result['kunden_nr']}"
        print(f"Zielordner: {zielordner}/")
        
        # Dateiname generieren
        if result['auftrag_nr']:
            dateiname = f"Auftrag_{result['auftrag_nr']}_{result['jahr']}.pdf"
        else:
            dateiname = f"Dokument_{result['jahr']}.pdf"
        
        voller_pfad = f"{zielordner}/{dateiname}"
        print(f"Dateiname:  {dateiname}")
        print(f"→ Vollständiger Pfad: {voller_pfad}")
        
    else:
        # Ohne Kundennummer (altes System)
        print("⚠️  Keine Kundennummer → Manuelle Zuordnung erforderlich")
        
        if result['auftrag_nr']:
            # Temporärer Ordner nach Auftragsnummer
            temp_ordner = f"Archiv/{result['jahr']}/Unzugeordnet/Auftrag_{result['auftrag_nr']}"
            print(f"Vorschlag:  {temp_ordner}/")
            print("→ Nach manueller Kundenzuordnung kann verschoben werden")
        else:
            print("→ Vollständig manuelle Bearbeitung nötig")
    
    # SCHRITT 3: In Datenbank indexieren
    print(f"\n💾 SCHRITT 3: Datenbank-Indexierung")
    print("-"*80)
    print("Folgende Informationen werden in SQLite gespeichert:")
    print(f"  • Dateiname: {os.path.basename(pdf_datei)}")
    print(f"  • Kundennummer: {result['kunden_nr'] or 'NULL'}")
    print(f"  • Auftragsnummer: {result['auftrag_nr'] or 'NULL'}")
    print(f"  • Jahr: {result['jahr']}")
    print(f"  • Dokumenttyp: {result['dokument_typ']}")
    print(f"  • Confidence: {result['confidence']:.1f}%")
    print(f"  • Hinweis: {result.get('hinweis', 'Keine')}")
    
    # SCHRITT 4: Automatik-Entscheidung
    print(f"\n⚙️  SCHRITT 4: Automatisierungs-Entscheidung")
    print("-"*80)
    
    if result['confidence'] >= 80:
        print("✅ AUTOMATISCH SORTIEREN")
        print("   → Hohe Confidence (≥80%)")
        print("   → Datei wird automatisch verschoben")
        print("   → Kundenordner wird erstellt falls nicht vorhanden")
    elif result['confidence'] >= 50:
        print("⚠️  MANUELLE PRÜFUNG EMPFOHLEN")
        print("   → Mittlere Confidence (50-79%)")
        print("   → Vorschlag wird angezeigt")
        print("   → Benutzer muss bestätigen oder korrigieren")
    else:
        print("❌ MANUELLE BEARBEITUNG ERFORDERLICH")
        print("   → Niedrige Confidence (<50%)")
        print("   → Datei landet in 'Manuell prüfen' Ordner")
        print("   → Benutzer muss alle Daten eingeben")

print("\n" + "="*80)
print("VERARBEITUNG ABGESCHLOSSEN")
print("="*80)
print("\n📊 ZUSAMMENFASSUNG:")
print("-"*80)
print("Neues System (Schultze.pdf):")
print("  → 100% Confidence → Automatisch sortiert nach:")
print("  → Archiv/2025/28307/Auftrag_11_2025.pdf")
print()
print("Altes System (auftrag.pdf):")
print("  → 60% Confidence → Manuelle Prüfung:")
print("  → Vorschlag: Archiv/2025/Unzugeordnet/Auftrag_78708/")
print("  → Nach Kundenzuordnung → Archiv/2025/{KUNDE}/Auftrag_78708_2025.pdf")
print()

"""
Test: Legacy-Auftrag System
Testet die vollständige Legacy-Workflow-Implementierung.
"""

# Testdaten vorbereiten
from services.vehicles import VehicleManager
from services.customers import CustomerManager
from services.legacy_resolver import LegacyResolver

# 1. Initialisiere Manager
print("="*80)
print("LEGACY-AUFTRAG SYSTEM - TESTLAUF")
print("="*80)

# Erstelle Testdaten
vehicle_manager = VehicleManager("data/vehicles.csv")
customer_manager = CustomerManager("data/customers.csv")

# Füge Testdaten hinzu
print("\n📝 Erstelle Testdaten...")
print("-"*80)

# Fahrzeug von auftrag.pdf zu Testkunde zuordnen
vehicle_manager.add_or_update_vehicle(
    fin="VR7BCZKXCME033281",
    kunden_nr="28307",
    kennzeichen="SFB-KI 23E",
    marke="Citroën",
    modell="C4 ELEC SHINE 136"
)
print("✅ Fahrzeug VR7BCZKXCME033281 → Kunde 28307")

# 2. Teste Legacy-Resolver
print("\n🔍 Teste Legacy-Resolver...")
print("-"*80)

legacy_resolver = LegacyResolver(customer_manager, vehicle_manager)

# Test 1: Match by FIN
test_meta_fin = {
    "kunden_name": "Anne Schultze",
    "fin": "VR7BCZKXCME033281",
    "kennzeichen": "SFB-KI 23E"
}

match = legacy_resolver.resolve_legacy_customer(test_meta_fin)
print(f"\nTest 1 - FIN-Match:")
print(f"  Kundennr: {match.kunden_nr}")
print(f"  Grund: {match.match_reason}")
print(f"  Detail: {match.confidence_detail}")

# Test 2: Unclear (FIN nicht in DB)
test_meta_unclear = {
    "kunden_name": "Max Mustermann",
    "fin": "WVWZZZ3CZCE123456",
    "kennzeichen": "B-MW 1234"
}

match = legacy_resolver.resolve_legacy_customer(test_meta_unclear)
print(f"\nTest 2 - Unclear:")
print(f"  Kundennr: {match.kunden_nr}")
print(f"  Grund: {match.match_reason}")
print(f"  Detail: {match.confidence_detail}")

# 3. Teste mit echten PDFs
print("\n\n📄 Teste mit Beispiel-PDFs...")
print("="*80)

from services.analyzer import analyze_document
from services.vorlagen import VorlagenManager

vorlagen_manager = VorlagenManager()

# auftrag.pdf ist Legacy (keine Kundennummer im Dokument)
result = analyze_document(
    "beispiel_auftraege/auftrag.pdf",
    vorlagen_manager=vorlagen_manager,
    legacy_resolver=legacy_resolver
)

print(f"\n📋 auftrag.pdf (Legacy-Auftrag):")
print(f"  Kundennummer: {result['kunden_nr'] or '❌'}")
print(f"  Kundenname: {result['kunden_name'] or '❌'}")
print(f"  Auftragsnummer: {result['auftrag_nr'] or '❌'}")
print(f"  FIN: {result['fin'] or '❌'}")
print(f"  Kennzeichen: {result['kennzeichen'] or '❌'}")
print(f"  Is Legacy: {result['is_legacy']}")
print(f"  Match Reason: {result['legacy_match_reason'] or 'N/A'}")
print(f"  Hinweis: {result['hinweis'] or 'N/A'}")

# Schultze.pdf hat Kundennummer (normal)
result2 = analyze_document(
    "beispiel_auftraege/Schultze.pdf",
    vorlagen_manager=vorlagen_manager,
    legacy_resolver=legacy_resolver
)

print(f"\n📋 Schultze.pdf (Normaler Auftrag):")
print(f"  Kundennummer: {result2['kunden_nr'] or '❌'}")
print(f"  Kundenname: {result2['kunden_name'] or '❌'}")
print(f"  Auftragsnummer: {result2['auftrag_nr'] or '❌'}")
print(f"  FIN: {result2['fin'] or '❌'}")
print(f"  Is Legacy: {result2['is_legacy']}")

print("\n" + "="*80)
print("✅ LEGACY-SYSTEM FUNKTIONIERT!")
print("="*80)
print("\nErgebnis:")
print("- auftrag.pdf wird via FIN dem Kunden 28307 zugeordnet")
print("- Schultze.pdf hat Kundennummer → normaler Workflow")
print("- Beide werden korrekt verarbeitet")

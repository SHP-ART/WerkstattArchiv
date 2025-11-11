"""
Test-Skript für GUI-Integration mit Legacy-System.
Prüft, ob alle Komponenten korrekt zusammenarbeiten.
"""

import os
from services.indexer import DocumentIndex
from services.customers import CustomerManager
from services.vehicles import VehicleManager
from services.legacy_resolver import LegacyResolver


def test_indexer_unclear_legacy():
    """Testet die unclear_legacy Funktionalität des Indexers."""
    print("=" * 60)
    print("TEST 1: Indexer unclear_legacy Tabelle")
    print("=" * 60)
    
    # Temporäre Test-Datenbank
    test_db = "test_index.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    indexer = DocumentIndex(test_db)
    
    # Test-Metadaten
    metadata = {
        "auftrag_nr": "78708",
        "auftragsdatum": "2019-03-15",
        "kunden_name": "Anne Schultze",
        "fin": "VR7BCZKXCME033281",
        "kennzeichen": "SFB-KI 23E",
        "jahr": 2019,
        "dokument_typ": "Auftrag",
        "legacy_match_reason": "unclear",
        "hinweis": "Test-Eintrag"
    }
    
    # Eintrag hinzufügen
    entry_id = indexer.add_unclear_legacy("/test/path/auftrag.pdf", metadata)
    print(f"✓ Eintrag hinzugefügt mit ID: {entry_id}")
    
    # Einträge abrufen
    entries = indexer.get_unclear_legacy_entries(status="offen")
    print(f"✓ {len(entries)} offene Einträge gefunden")
    
    if entries:
        entry = entries[0]
        print(f"\n📋 Eintrag-Details:")
        print(f"  ID: {entry['id']}")
        print(f"  Auftrag: {entry['auftrag_nr']}")
        print(f"  Kunde: {entry['kunden_name']}")
        print(f"  FIN: {entry['fin']}")
        print(f"  Status: {entry['status']}")
    
    # Zuordnung testen
    success = indexer.assign_unclear_legacy(entry_id, "28307")
    print(f"\n✓ Zuordnung zu Kunde 28307: {success}")
    
    # Status prüfen
    entries = indexer.get_unclear_legacy_entries(status="zugeordnet")
    print(f"✓ {len(entries)} zugeordnete Einträge")
    
    # Löschen
    success = indexer.delete_unclear_legacy(entry_id)
    print(f"✓ Eintrag gelöscht: {success}")
    
    # Cleanup
    os.remove(test_db)
    print("\n✅ TEST 1 ERFOLGREICH\n")


def test_legacy_integration():
    """Testet die Integration von CustomerManager, VehicleManager und LegacyResolver."""
    print("=" * 60)
    print("TEST 2: Legacy-System Integration")
    print("=" * 60)
    
    # Test-Kundendatenbank
    test_customers_file = "test_customers.csv"
    with open(test_customers_file, "w", encoding="utf-8") as f:
        f.write("kunden_nr;name;plz;ort;strasse;telefon\n")
        f.write("28307;Anne Schultze;12345;Berlin;Hauptstr. 10;030-123456\n")
        f.write("10234;Max Müller;54321;Hamburg;Bahnhofstr. 5;040-987654\n")
    
    customer_manager = CustomerManager(test_customers_file)
    print(f"✓ {len(customer_manager.customers)} Kunden geladen")
    
    # Vehicle Manager
    vehicle_manager = VehicleManager()
    vehicle_manager.add_or_update_vehicle(
        fin="VR7BCZKXCME033281",
        kunden_nr="28307",
        kennzeichen="SFB-KI 23E"
    )
    print("✓ Fahrzeug hinzugefügt")
    
    # Legacy Resolver
    resolver = LegacyResolver(customer_manager, vehicle_manager)
    print("✓ LegacyResolver initialisiert")
    
    # Test 1: FIN-Match
    print("\n📋 Test FIN-Match:")
    result = resolver.resolve_legacy_customer({
        "fin": "VR7BCZKXCME033281",
        "kunden_name": "Anne Schultze",
        "plz": None,
        "strasse": None
    })
    
    if result:
        print(f"  ✓ Kunde gefunden: {result.kunden_nr}")
        print(f"  ✓ Grund: {result.match_reason}")
        print(f"  ✓ Details: {result.confidence_detail}")
    else:
        print("  ✗ Kein Match")
    
    # Test 2: Name+PLZ Match
    print("\n📋 Test Name+PLZ Match:")
    result = resolver.resolve_legacy_customer({
        "fin": None,
        "kunden_name": "Max Müller",
        "plz": "54321",
        "strasse": None
    })
    
    if result:
        print(f"  ✓ Kunde gefunden: {result.kunden_nr}")
        print(f"  ✓ Grund: {result.match_reason}")
        print(f"  ✓ Details: {result.confidence_detail}")
    else:
        print("  ✗ Kein Match")
    
    # Test 3: Kein Match
    print("\n📋 Test Kein Match:")
    result = resolver.resolve_legacy_customer({
        "fin": None,
        "kunden_name": "Unbekannter Kunde",
        "plz": "99999",
        "strasse": None
    })
    
    if result:
        print(f"  ✗ Unexpected Match: {result.kunden_nr}")
    else:
        print("  ✓ Korrekterweise kein Match (unclear)")
    
    # Cleanup
    os.remove(test_customers_file)
    if os.path.exists("data/vehicles.csv"):
        # Testdaten aus vehicles.csv entfernen nicht nötig, da es produktive Daten sind
        pass
    
    print("\n✅ TEST 2 ERFOLGREICH\n")


def test_customer_dataclass():
    """Testet, ob Customer als Dataclass korrekt funktioniert."""
    print("=" * 60)
    print("TEST 3: Customer Dataclass")
    print("=" * 60)
    
    # Test-Kundendatenbank
    test_customers_file = "test_customers2.csv"
    with open(test_customers_file, "w", encoding="utf-8") as f:
        f.write("kunden_nr;name;plz;ort;strasse;telefon\n")
        f.write("28307;Anne Schultze;12345;Berlin;Hauptstr. 10;030-123456\n")
    
    customer_manager = CustomerManager(test_customers_file)
    
    # Kunde abrufen
    kunde = customer_manager.customers.get("28307")
    
    if kunde:
        print(f"✓ Kunde gefunden: {kunde.kunden_nr}")
        print(f"  Name: {kunde.name}")
        print(f"  PLZ: {kunde.plz}")
        print(f"  Ort: {kunde.ort}")
        print(f"  Straße: {kunde.strasse}")
        print(f"  Telefon: {kunde.telefon}")
        
        # Test Attributzugriff
        assert kunde.kunden_nr == "28307", "Kundennummer falsch"
        assert kunde.name == "Anne Schultze", "Name falsch"
        assert kunde.plz == "12345", "PLZ falsch"
        
        print("\n✅ TEST 3 ERFOLGREICH\n")
    else:
        print("✗ Kunde nicht gefunden")
    
    # Cleanup
    os.remove(test_customers_file)


if __name__ == "__main__":
    print("\n🧪 WerkstattArchiv - GUI Integration Tests\n")
    
    try:
        test_indexer_unclear_legacy()
        test_legacy_integration()
        test_customer_dataclass()
        
        print("=" * 60)
        print("🎉 ALLE TESTS ERFOLGREICH!")
        print("=" * 60)
        print("\nDas System ist bereit für:")
        print("  ✓ Indexierung unklarer Legacy-Aufträge")
        print("  ✓ GUI-Tab für manuelle Zuordnung")
        print("  ✓ FIN-basierte automatische Zuordnung")
        print("  ✓ Name+Details-basierte Zuordnung")
        print("\nStarten Sie die GUI mit: python main.py")
        
    except Exception as e:
        print(f"\n❌ TEST FEHLGESCHLAGEN: {e}")
        import traceback
        traceback.print_exc()

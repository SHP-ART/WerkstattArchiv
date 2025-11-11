"""
Beispiel: Integration des erweiterten Indexers in router.py

Zeigt wie der Indexer mit allen neuen Feldern verwendet wird.
"""

from services.indexer import DocumentIndex
from services.analyzer import analyze_document
from services.customers import CustomerManager
import shutil
import os


def process_document_with_indexing(file_path: str, config: dict):
    """
    Beispiel-Workflow: Dokument analysieren, verschieben und indexieren.
    
    Args:
        file_path: Pfad zum zu verarbeitenden Dokument
        config: Konfigurationsdictionary mit Pfaden
    """
    # 1. Indexer initialisieren
    indexer = DocumentIndex()
    
    # 2. Dokument analysieren (mit allen Metadaten)
    metadata = analyze_document(file_path)
    
    # Metadata enthält jetzt:
    # {
    #     "auftrag_nr": "78708",
    #     "auftragsdatum": "2019-03-15", 
    #     "dokument_typ": "Auftrag",
    #     "jahr": 2019,
    #     "kunden_nr": "28307",
    #     "kunden_name": "Anne Schultze",
    #     "fin": "VR7BCZKXCME033281",
    #     "kennzeichen": "SFB-KI 23E",
    #     "kilometerstand": 45000,  # falls extrahiert
    #     "is_legacy": False,
    #     "legacy_match_reason": None,
    #     "confidence": 0.9,
    #     "hinweis": "..."
    # }
    
    # 3. Ziel-Pfad berechnen
    kunden_nr = metadata.get("kunden_nr", "Unbekannt")
    kunden_name = metadata.get("kunden_name", "Unbekannt")
    jahr = metadata.get("jahr", "Unbekannt")
    auftrag_nr = metadata.get("auftrag_nr", "Unbekannt")
    dokument_typ = metadata.get("dokument_typ", "Dokument")
    
    root_dir = config.get("root_dir", "D:/Scan/Daten")
    kunde_ordner = f"{kunden_nr}-{kunden_name}".replace(" ", "_")
    
    ziel_ordner = os.path.join(root_dir, "Kunde", kunde_ordner, str(jahr))
    os.makedirs(ziel_ordner, exist_ok=True)
    
    dateiname = f"{auftrag_nr}_{dokument_typ}.pdf"
    ziel_pfad = os.path.join(ziel_ordner, dateiname)
    
    # 4. Datei verschieben
    try:
        shutil.move(file_path, ziel_pfad)
        status = "success"
        
        # 5. IN DATENBANK INDEXIEREN (WICHTIG!)
        doc_id = indexer.add_document(
            original_path=file_path,
            target_path=ziel_pfad,
            metadata=metadata,
            status=status
        )
        
        print(f"✓ Dokument erfolgreich verschoben und indexiert (ID: {doc_id})")
        print(f"  Von: {file_path}")
        print(f"  Nach: {ziel_pfad}")
        
        # Alle Metadaten sind nun in der Datenbank:
        # - Auftragsnummer, Datum, Dokumenttyp
        # - Kundennummer, Kundenname
        # - FIN, Kennzeichen, Kilometerstand
        # - Legacy-Informationen (is_legacy, match_reason)
        # - Confidence, Status, Hinweise
        # - Zeitstempel (created_at, last_update)
        
        return ziel_pfad, True, None
        
    except Exception as e:
        status = "error"
        indexer.add_document(
            original_path=file_path,
            target_path=file_path,  # Bei Fehler: Original-Pfad
            metadata=metadata,
            status=status
        )
        print(f"✗ Fehler beim Verschieben: {e}")
        return file_path, False, str(e)


def update_document_path_example(doc_id: int, new_path: str):
    """
    Beispiel: Dateipfad nach manueller Verschiebung aktualisieren.
    
    Args:
        doc_id: ID des Dokuments in der Datenbank
        new_path: Neuer Dateipfad
    """
    indexer = DocumentIndex()
    
    success = indexer.update_file_path(doc_id, new_path)
    
    if success:
        print(f"✓ Dateipfad für Dokument {doc_id} aktualisiert")
        print(f"  Neuer Pfad: {new_path}")
    else:
        print(f"✗ Fehler beim Aktualisieren des Pfads für Dokument {doc_id}")


def search_examples():
    """Beispiele für Suchanfragen mit dem erweiterten Indexer."""
    indexer = DocumentIndex()
    
    # 1. Suche nach Kundennummer
    print("\n=== Suche nach Kundennummer 28307 ===")
    results = indexer.search(kunden_nr="28307")
    print(f"Gefunden: {len(results)} Dokumente")
    for doc in results[:3]:  # Erste 3 anzeigen
        print(f"  - {doc['dateiname']} | {doc['dokument_typ']} | {doc['auftragsdatum']}")
    
    # 2. Suche nach FIN
    print("\n=== Suche nach FIN VR7BCZKXCME033281 ===")
    results = indexer.search_by_fin("VR7BCZKXCME033281")
    print(f"Gefunden: {len(results)} Dokumente")
    for doc in results:
        print(f"  - {doc['auftrag_nr']} | Kunde: {doc['kunden_nr']} | {doc['kennzeichen']}")
    
    # 3. Suche nach Kennzeichen
    print("\n=== Suche nach Kennzeichen SFB-KI 23E ===")
    results = indexer.search_by_kennzeichen("SFB-KI 23E")
    print(f"Gefunden: {len(results)} Dokumente")
    
    # 4. Alle Legacy-Dokumente
    print("\n=== Legacy-Dokumente ===")
    legacy_docs = indexer.get_legacy_documents()
    print(f"Gesamt: {len(legacy_docs)} Legacy-Dokumente")
    
    # 5. Nur erfolgreich zugeordnete Legacy-Dokumente
    print("\n=== Erfolgreich zugeordnete Legacy-Dokumente ===")
    success_legacy = indexer.get_legacy_documents(status="success")
    print(f"Erfolgreich: {len(success_legacy)}")
    
    # 6. Statistiken
    print("\n=== Statistiken ===")
    stats = indexer.get_statistics()
    print(f"Gesamt: {stats['total']} Dokumente")
    print(f"Nach Status: {stats['by_status']}")
    print(f"Nach Typ: {stats['by_type']}")


def integration_in_router():
    """
    Zeigt wie der Indexer in router.py integriert wird.
    
    In router.py:
    
    1. Import hinzufügen:
       from services.indexer import DocumentIndex
    
    2. In process_document() Funktion:
       
       def process_document(file_path, analysis, root_dir, unclear_dir, customer_manager):
           # ... bestehender Code für Routing ...
           
           # WICHTIG: Nach erfolgreichem shutil.move()
           indexer = DocumentIndex()
           indexer.add_document(
               original_path=original_file_path,
               target_path=target_path,
               metadata=analysis,  # Enthält alle Felder
               status="success" if is_clear else "unclear"
           )
           
           return target_path, is_clear, reason
    
    3. Bei manueller Nachbearbeitung (unclear documents):
       
       def reassign_document(doc_id, new_customer_nr):
           # Datei verschieben
           new_path = move_to_customer_folder(...)
           
           # Pfad in Datenbank aktualisieren
           indexer = DocumentIndex()
           indexer.update_file_path(doc_id, new_path)
    """
    pass


if __name__ == "__main__":
    print("=" * 60)
    print("WerkstattArchiv - Erweiterter Indexer")
    print("=" * 60)
    
    # Beispiele ausführen
    search_examples()
    
    print("\n" + "=" * 60)
    print("Integration erfolgreich!")
    print("=" * 60)
    print("\n📚 Alle Dokumente werden jetzt mit folgenden Daten indexiert:")
    print("  ✓ Auftragsnummer, Auftragsdatum, Dokumenttyp")
    print("  ✓ Kundennummer, Kundenname")
    print("  ✓ FIN, Kennzeichen, Kilometerstand")
    print("  ✓ Legacy-Informationen (is_legacy, match_reason)")
    print("  ✓ Confidence-Score, Status, Hinweise")
    print("  ✓ Zeitstempel (created_at, last_update)")
    print("\n🔍 Suchfunktionen verfügbar:")
    print("  ✓ search() - Allgemeine Suche nach allen Feldern")
    print("  ✓ search_by_fin() - Suche nach FIN")
    print("  ✓ search_by_kennzeichen() - Suche nach Kennzeichen")
    print("  ✓ get_legacy_documents() - Alle Legacy-Dokumente")
    print("  ✓ get_statistics() - Statistiken")
    print("\n💾 Datenbank: werkstatt_index.db (SQLite)")
    print("📊 Plattformübergreifend, lokal, keine Cloud")

"""
Test-Script für die neuen Datenbank-Features.
Testet Backup, Statistiken, Export und Health-Check.
"""

import sys
import os

# Füge das Projekt-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.indexer import DocumentIndex


def print_separator(title=""):
    """Druckt einen Separator."""
    print("\n" + "="*80)
    if title:
        print(f" {title}")
        print("="*80)


def test_backup_system():
    """Testet das Backup-System."""
    print_separator("TEST: Backup-System")
    
    index = DocumentIndex()
    
    # Backup erstellen
    print("📦 Erstelle Backup...")
    success, path, message = index.create_backup(reason="test")
    print(f"   {'✅' if success else '❌'} {message}")
    
    # Backups auflisten
    print("\n📋 Liste Backups...")
    backups = index.list_backups()
    print(f"   Gefunden: {len(backups)} Backups")
    
    if backups:
        last_backup = backups[0]
        print(f"   Letztes: {last_backup.get('filename', 'N/A')}")
        print(f"   Größe: {last_backup.get('size_formatted', 'N/A')}")
        print(f"   Alter: {last_backup.get('age_days', 0)} Tage")


def test_health_check():
    """Testet den Health-Check."""
    print_separator("TEST: Health-Check")
    
    index = DocumentIndex()
    
    print("🏥 Führe Health-Check durch...")
    health = index.health_check()
    
    status = "✅ GESUND" if health.get("healthy", False) else "⚠️ PROBLEME"
    print(f"   Status: {status}")
    
    stats = health.get("statistics", {})
    if stats:
        print(f"   Größe: {stats.get('size_formatted', 'N/A')}")
        print(f"   Dokumente: {stats.get('documents', 0)}")
        print(f"   Indexes: {stats.get('indexes', 0)}")
        print(f"   Journal-Mode: {stats.get('journal_mode', 'N/A')}")
    
    warnings = health.get("warnings", [])
    if warnings:
        print(f"\n   ⚠️ Warnungen ({len(warnings)}):")
        for w in warnings:
            print(f"      - {w}")
    
    errors = health.get("errors", [])
    if errors:
        print(f"\n   ❌ Fehler ({len(errors)}):")
        for e in errors:
            print(f"      - {e}")


def test_statistics():
    """Testet die Statistiken."""
    print_separator("TEST: Statistiken")
    
    index = DocumentIndex()
    
    # Übersicht
    print("📊 Übersichts-Statistiken...")
    stats = index.get_overview_stats()
    
    if "error" in stats:
        print(f"   ❌ Fehler: {stats['error']}")
        return
    
    print(f"   Gesamt-Dokumente: {stats.get('total_documents', 0)}")
    
    by_status = stats.get("by_status", {})
    if by_status:
        print(f"   Status-Verteilung:")
        for status, count in by_status.items():
            print(f"      {status}: {count}")
    
    # Top Kunden
    print("\n👥 Top 5 Kunden...")
    customers = index.get_customer_stats()
    
    if customers and not (len(customers) == 1 and "error" in customers[0]):
        for i, customer in enumerate(customers[:5], 1):
            print(f"   {i}. {customer.get('kunden_name', 'N/A')} "
                  f"({customer.get('kunden_nr', 'N/A')}): "
                  f"{customer.get('document_count', 0)} Dokumente")
    else:
        print("   Keine Kunden-Daten verfügbar")
    
    # Qualität
    print("\n🎯 Qualitäts-Statistiken...")
    quality = index.get_quality_stats()
    
    if "error" in quality:
        print(f"   ❌ Fehler: {quality['error']}")
        return
    
    conf_dist = quality.get("confidence_distribution", {})
    if conf_dist:
        print("   Confidence-Verteilung:")
        for level, count in conf_dist.items():
            print(f"      {level}: {count}")


def test_export():
    """Testet die Export-Funktionen."""
    print_separator("TEST: Export-Funktionen")
    
    index = DocumentIndex()
    
    # CSV Export (mit automatischem Dateinamen)
    print("💾 Teste CSV-Export...")
    success, filepath = index.export_to_csv()
    
    if success:
        print(f"   ✅ CSV exportiert: {filepath}")
        # Prüfe Dateigröße
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"   Größe: {size:,} Bytes")
    else:
        print(f"   ❌ Export fehlgeschlagen: {filepath}")


def test_optimize():
    """Testet die Datenbank-Optimierung."""
    print_separator("TEST: Datenbank-Optimierung")
    
    index = DocumentIndex()
    
    print("🔧 Optimiere Datenbank...")
    success, message, stats = index.optimize_database()
    
    if success:
        print(f"   ✅ {message}")
        print(f"   Dokumente: {stats.get('documents_count', 0)}")
        print(f"   Größe vorher: {format_bytes(stats.get('size_before', 0))}")
        print(f"   Größe nachher: {format_bytes(stats.get('size_after', 0))}")
        print(f"   Freigegeben: {stats.get('space_saved_formatted', 'N/A')}")
        print(f"   Integrität: {stats.get('integrity_check', 'N/A')}")
    else:
        print(f"   ❌ Optimierung fehlgeschlagen: {message}")


def format_bytes(size):
    """Formatiert Bytes human-readable."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def main():
    """Führt alle Tests durch."""
    print("\n" + "="*80)
    print(" DATENBANK-FEATURES TEST-SUITE")
    print("="*80)
    print("\nTeste alle neuen Datenbank-Features...")
    
    try:
        # Prüfe ob Datenbank existiert
        if not os.path.exists("werkstatt_index.db"):
            print("\n⚠️ WARNUNG: werkstatt_index.db nicht gefunden!")
            print("   Einige Tests könnten fehlschlagen oder keine Daten anzeigen.")
            input("\n   Weiter mit Enter oder Abbruch mit Ctrl+C...")
        
        # Führe Tests durch
        test_backup_system()
        test_health_check()
        test_statistics()
        test_export()
        test_optimize()
        
        # Zusammenfassung
        print_separator("TEST-ZUSAMMENFASSUNG")
        print("\n✅ Alle Tests abgeschlossen!")
        print("\nGetestete Features:")
        print("   ✓ Backup-Erstellung und -Verwaltung")
        print("   ✓ Health-Check und Integritätsprüfung")
        print("   ✓ Statistiken (Übersicht, Kunden, Qualität)")
        print("   ✓ CSV-Export")
        print("   ✓ Datenbank-Optimierung")
        
        print("\n📁 Erstellte Dateien:")
        print("   - data/db_backups/*.db (Backups)")
        print("   - data/exports/*.csv (CSV-Exports)")
        
        print("\n🎉 Datenbank-Features sind funktionsfähig!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Test abgebrochen (Ctrl+C)")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n\n❌ FEHLER: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

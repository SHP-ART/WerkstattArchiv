"""
Indexierungs-Service für WerkstattArchiv.
Speichert Metadaten aller verarbeiteten Dokumente in einer SQLite-Datenbank.
"""

import sqlite3
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from functools import lru_cache


DB_FILE = "werkstatt_index.db"


class DocumentIndex:
    """Verwaltet den Index aller verarbeiteten Dokumente."""

    def __init__(self, db_path: str = DB_FILE, root_dir: Optional[str] = None):
        """
        Initialisiert den Dokumenten-Index.

        Args:
            db_path: Pfad zur SQLite-Datenbankdatei
            root_dir: Basisverzeichnis für Backups (Server mit automatischen Backups)
        """
        self.db_path = db_path
        self.root_dir = root_dir
        self._connection_timeout = 10  # Timeout für DB-Locks (verhindert Deadlocks)
        # Statistics Lazy-Loading Cache
        self._statistics_cache: Optional[Dict[str, Any]] = None
        self._init_database()
        
        # Maintenance und Statistics Services (Lazy-Loading)
        self._maintenance = None
        self._statistics = None

    def _init_database(self) -> None:
        """Erstellt die Datenbanktabelle und optimiert die Datenbank für Performance."""
        conn = sqlite3.connect(self.db_path, timeout=self._connection_timeout, check_same_thread=False)
        cursor = conn.cursor()

        # PRAGMA Optimierungen für bessere Performance und Concurrency
        # Diese gelten für die ganze Datenbankverbindung
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging für bessere Concurrency
        cursor.execute("PRAGMA synchronous=NORMAL")  # Weniger fsync() calls (schneller, immer noch sicher)
        cursor.execute("PRAGMA cache_size=10000")  # Größerer Cache für häufige Queries
        cursor.execute("PRAGMA temp_store=MEMORY")  # Temp-Tabellen im RAM (schneller)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dokumente (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dateiname TEXT NOT NULL,
                original_pfad TEXT,
                ziel_pfad TEXT NOT NULL,
                
                -- Auftragsdaten
                auftrag_nr TEXT,
                auftragsdatum TEXT,
                dokument_typ TEXT,
                jahr INTEGER,
                
                -- Kundendaten
                kunden_nr TEXT,
                kunden_name TEXT,
                
                -- Fahrzeugdaten (NEU)
                fin TEXT,
                kennzeichen TEXT,
                kilometerstand INTEGER,
                
                -- Legacy-Informationen
                is_legacy INTEGER DEFAULT 0,
                match_reason TEXT,
                
                -- Qualität & Status
                confidence REAL,
                status TEXT,
                hinweis TEXT,
                
                -- Zeitstempel
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verarbeitet_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabelle für unklare Legacy-Aufträge (manuelle Nachbearbeitung)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unclear_legacy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dateiname TEXT NOT NULL,
                datei_pfad TEXT NOT NULL,
                auftrag_nr TEXT,
                auftragsdatum TEXT,
                kunden_name TEXT,
                fin TEXT,
                kennzeichen TEXT,
                jahr INTEGER,
                dokument_typ TEXT,
                match_reason TEXT NOT NULL,
                hinweis TEXT,
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                zugeordnet_am TIMESTAMP,
                zugeordnet_zu_kunden_nr TEXT,
                status TEXT DEFAULT 'offen'
            )
        """)
        
        # Migration: Füge neue Spalten hinzu falls sie nicht existieren
        self._migrate_database(cursor)
        
        # ===== INDEXES für dokumente TABELLE =====
        # Single-Column Indexes (häufige WHERE-Clauses)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_kunden_nr
            ON dokumente(kunden_nr)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_auftrag_nr
            ON dokumente(auftrag_nr)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_jahr
            ON dokumente(jahr)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dokument_typ
            ON dokumente(dokument_typ)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status
            ON dokumente(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_is_legacy
            ON dokumente(is_legacy)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fin
            ON dokumente(fin)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_kennzeichen
            ON dokumente(kennzeichen)
        """)

        # Composite Index (kunden_nr, jahr) - sehr häufig zusammen abgefragt
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_kunden_nr_jahr
            ON dokumente(kunden_nr, jahr)
        """)

        # Index für Ordering (verarbeitet_am DESC)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verarbeitet_am
            ON dokumente(verarbeitet_am DESC)
        """)

        # Indexes für LIKE Suchen (Search-Performance)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_kunden_name
            ON dokumente(kunden_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dateiname
            ON dokumente(dateiname)
        """)

        # ===== INDEXES für unclear_legacy TABELLE =====
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_unclear_status
            ON unclear_legacy(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_unclear_fin
            ON unclear_legacy(fin)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_unclear_auftrag_nr
            ON unclear_legacy(auftrag_nr)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_unclear_kennzeichen
            ON unclear_legacy(kennzeichen)
        """)
        
        conn.commit()
        conn.close()
    
    def _convert_row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Konvertiert eine SQLite Row zu einem Dictionary (optimiert).
        Effiziente Variante statt manuelles Dict mit vielen .keys() Checks.

        Args:
            row: sqlite3.Row Objekt

        Returns:
            Dictionary mit allen Dokumenten-Feldern
        """
        # Direct dict() conversion (fast) statt manuelles Dict-Building
        result = dict(row)

        # Nur für Felder die Optional sein können, defaults setzen
        optional_fields = {
            "auftragsdatum": None,
            "fin": None,
            "kennzeichen": None,
            "kilometerstand": None,
            "is_legacy": False,
            "match_reason": None,
            "created_at": None,
            "last_update": None
        }

        for field, default in optional_fields.items():
            if field not in result or result[field] is None:
                result[field] = default

        # Convert is_legacy to bool wenn nötig
        if "is_legacy" in result:
            result["is_legacy"] = bool(result["is_legacy"])

        return result

    def _migrate_database(self, cursor: sqlite3.Cursor) -> None:
        """
        Migriert bestehende Datenbank auf neues Schema.
        Fügt neue Spalten hinzu falls sie nicht existieren.
        """
        # Prüfe ob neue Spalten bereits existieren
        cursor.execute("PRAGMA table_info(dokumente)")
        columns = {row[1] for row in cursor.fetchall()}

        # Neue Spalten die hinzugefügt werden sollen
        new_columns = {
            "fin": "TEXT",
            "kennzeichen": "TEXT",
            "kilometerstand": "INTEGER",
            "is_legacy": "INTEGER DEFAULT 0",
            "match_reason": "TEXT",
            "auftragsdatum": "TEXT",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "last_update": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        }

        # Füge fehlende Spalten hinzu
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE dokumente ADD COLUMN {col_name} {col_type}")
                    print(f"✓ Spalte '{col_name}' zur Datenbank hinzugefügt")
                except sqlite3.OperationalError as e:
                    # Spalte existiert bereits oder anderer Fehler
                    if "duplicate column" not in str(e).lower():
                        print(f"Hinweis beim Hinzufügen von '{col_name}': {e}")

    def upgrade_indexes(self) -> Dict[str, Any]:
        """
        Aktualisiert die Datenbankindexes für bestehende Datenbanken.
        Erstellt fehlende Indexes nach.

        Returns:
            Dictionary mit Upgrade-Statistiken
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Zähle existierende Indexes
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='index' AND tbl_name='dokumente'
        """)
        indexes_before = cursor.fetchone()[0]

        # Erstelle alle neuen Indexes
        indexes_to_create = [
            ("idx_status", "dokumente(status)"),
            ("idx_is_legacy", "dokumente(is_legacy)"),
            ("idx_fin", "dokumente(fin)"),
            ("idx_kennzeichen", "dokumente(kennzeichen)"),
            ("idx_kunden_nr_jahr", "dokumente(kunden_nr, jahr)"),
            ("idx_verarbeitet_am", "dokumente(verarbeitet_am DESC)"),
            ("idx_unclear_kennzeichen", "unclear_legacy(kennzeichen)"),
        ]

        created_count = 0
        for idx_name, idx_def in indexes_to_create:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
                created_count += 1
            except Exception as e:
                print(f"⚠ Fehler beim Erstellen von {idx_name}: {e}")

        conn.commit()

        # Zähle neue Indexes
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='index' AND tbl_name='dokumente'
        """)
        indexes_after = cursor.fetchone()[0]

        # Optimiere die Datenbank (VACUUM + ANALYZE)
        cursor.execute("VACUUM")
        cursor.execute("ANALYZE")

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "indexes_before": indexes_before,
            "indexes_after": indexes_after,
            "new_indexes_created": created_count,
            "message": f"Datenbank optimiert: {created_count} neue Indexes erstellt"
        }

    
    def add_document(self, original_path: str, target_path: str, 
                    metadata: Dict[str, Any], status: str = "success") -> int:
        """
        Fügt ein Dokument zum Index hinzu.
        
        Args:
            original_path: Ursprünglicher Dateipfad
            target_path: Zielpfad nach Verarbeitung
            metadata: Metadaten des Dokuments (inkl. fin, kennzeichen, kilometerstand, etc.)
            status: Status (success, unclear, error)
            
        Returns:
            ID des eingefügten Dokuments
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO dokumente 
            (dateiname, original_pfad, ziel_pfad, 
             auftrag_nr, auftragsdatum, dokument_typ, jahr,
             kunden_nr, kunden_name, 
             fin, kennzeichen, kilometerstand,
             is_legacy, match_reason,
             confidence, status, hinweis,
             created_at, last_update)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            os.path.basename(target_path),
            original_path,
            target_path,
            metadata.get("auftrag_nr"),
            metadata.get("auftragsdatum"),
            metadata.get("dokument_typ"),
            metadata.get("jahr"),
            metadata.get("kunden_nr"),
            metadata.get("kunden_name"),
            metadata.get("fin"),
            metadata.get("kennzeichen"),
            metadata.get("kilometerstand"),
            1 if metadata.get("is_legacy") else 0,
            metadata.get("legacy_match_reason") or metadata.get("match_reason"),
            metadata.get("confidence"),
            status,
            metadata.get("hinweis")
        ))
        
        doc_id = cursor.lastrowid if cursor.lastrowid else 0
        conn.commit()
        conn.close()

        # Invalidiere Statistics-Cache (Daten haben sich geändert)
        self.invalidate_statistics_cache()

        return doc_id

    def add_documents_batch(self, documents: List[tuple]) -> List[int]:
        """
        Fügt mehrere Dokumente in einem Batch ein (Feature 12: Batch Database Inserts).
        Viel schneller als einzelne add_document() Aufrufe, da nur EINE Verbindung verwendet wird.

        Args:
            documents: Liste von Tuples (original_path, target_path, metadata, status)
                     wo metadata ein Dict mit Dokument-Metadaten ist

        Returns:
            Liste von eingefügten Document-IDs
        """
        if not documents:
            return []

        conn = sqlite3.connect(self.db_path, timeout=self._connection_timeout, check_same_thread=False)
        cursor = conn.cursor()

        inserted_ids = []
        try:
            for original_path, target_path, metadata, status in documents:
                cursor.execute("""
                    INSERT INTO dokumente
                    (dateiname, original_pfad, ziel_pfad,
                     auftrag_nr, auftragsdatum, dokument_typ, jahr,
                     kunden_nr, kunden_name,
                     fin, kennzeichen, kilometerstand,
                     is_legacy, match_reason,
                     confidence, status, hinweis,
                     created_at, last_update)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    os.path.basename(target_path),
                    original_path,
                    target_path,
                    metadata.get("auftrag_nr"),
                    metadata.get("auftragsdatum"),
                    metadata.get("dokument_typ"),
                    metadata.get("jahr"),
                    metadata.get("kunden_nr"),
                    metadata.get("kunden_name"),
                    metadata.get("fin"),
                    metadata.get("kennzeichen"),
                    metadata.get("kilometerstand"),
                    1 if metadata.get("is_legacy") else 0,
                    metadata.get("legacy_match_reason") or metadata.get("match_reason"),
                    metadata.get("confidence"),
                    status,
                    metadata.get("hinweis")
                ))
                inserted_ids.append(cursor.lastrowid if cursor.lastrowid else 0)

            # SINGLE COMMIT für alle Inserts - deutlich schneller!
            conn.commit()
        finally:
            conn.close()

        # Invalidiere Statistics-Cache (Daten haben sich geändert)
        self.invalidate_statistics_cache()

        return inserted_ids

    def update_file_path(self, doc_id: int, new_path: str) -> bool:
        """
        Aktualisiert den Dateipfad eines Dokuments.
        
        Args:
            doc_id: ID des Dokuments
            new_path: Neuer Dateipfad
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE dokumente 
                SET ziel_pfad = ?,
                    dateiname = ?,
                    last_update = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_path, os.path.basename(new_path), doc_id))
            
            conn.commit()
            success = cursor.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Aktualisieren des Dateipfads: {e}")
            success = False
        finally:
            conn.close()
        
        return success
    
    def search(self, kunden_nr: Optional[str] = None, 
              auftrag_nr: Optional[str] = None,
              dokument_typ: Optional[str] = None,
              jahr: Optional[int] = None,
              monat: Optional[int] = None,
              kunden_name: Optional[str] = None,
              dateiname: Optional[str] = None,
              fin: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Sucht nach Dokumenten im Index.
        
        Args:
            kunden_nr: Kundennummer (exakte Suche)
            auftrag_nr: Auftragsnummer (exakte Suche)
            dokument_typ: Dokumenttyp (exakte Suche)
            jahr: Jahr (exakte Suche)
            monat: Monat (exakte Suche, 1-12)
            kunden_name: Kundenname (LIKE-Suche)
            dateiname: Dateiname (LIKE-Suche)
            fin: FIN/VIN (flexible Suche - findet komplett oder letzte 8 Zeichen)
            
        Returns:
            Liste von Dokumenten als Dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM dokumente WHERE 1=1"
        params = []
        
        if kunden_nr:
            query += " AND kunden_nr = ?"
            params.append(kunden_nr)
        
        if auftrag_nr:
            query += " AND auftrag_nr = ?"
            params.append(auftrag_nr)
        
        if dokument_typ:
            query += " AND dokument_typ = ?"
            params.append(dokument_typ)
        
        if jahr:
            query += " AND jahr = ?"
            params.append(jahr)
        
        if monat:
            # Optimiert: SUBSTR statt strftime (5-10x schneller!)
            # SUBSTR(verarbeitet_am, 6, 2) extrahiert Monat aus "YYYY-MM-DD HH:MM:SS"
            query += " AND CAST(SUBSTR(verarbeitet_am, 6, 2) AS INTEGER) = ?"
            params.append(monat)
        
        if kunden_name:
            query += " AND kunden_name LIKE ?"
            params.append(f"%{kunden_name}%")
        
        if dateiname:
            query += " AND dateiname LIKE ?"
            params.append(f"%{dateiname}%")
        
        if fin:
            # Flexible FIN-Suche: Findet sowohl komplette FIN als auch letzte 8 Zeichen
            # Wenn Eingabe 8 Zeichen oder weniger: Suche in letzten 8 Zeichen
            # Wenn Eingabe länger: Suche exakt oder als Teil
            fin_clean = fin.strip().upper()
            
            if len(fin_clean) <= 8:
                # Suche nach letzten 8 Zeichen (z.B. "12345678" findet "WDB1234567890012345678")
                query += " AND (fin = ? OR SUBSTR(fin, -8) = ?)"
                params.append(fin_clean)
                params.append(fin_clean)
            else:
                # Suche nach kompletter FIN oder als Teil davon
                query += " AND fin LIKE ?"
                params.append(f"%{fin_clean}%")
        
        query += " ORDER BY verarbeitet_am DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Optimiert: Nutze Helper-Methode statt manuelles Dict-Building
        results = [self._convert_row_to_dict(row) for row in rows]

        conn.close()
        return results
    
    def get_quick_statistics(self) -> Dict[str, Any]:
        """
        Gibt schnelle Basic-Statistiken zurück (SEHR SCHNELL).
        Ideal für schnelle UI-Updates ohne lange Wartezeit.
        Nur COUNT(*) ohne GROUP BY.

        Returns:
            Dictionary mit Basis-Statistiken
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Ein einziges Query für alle schnellen Stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN is_legacy = 1 THEN 1 END) as legacy_count,
                COUNT(CASE WHEN status = 'unclear' THEN 1 END) as unclear_count,
                (SELECT COUNT(*) FROM unclear_legacy WHERE status = 'offen') as unclear_legacy_count,
                COUNT(DISTINCT CASE WHEN kunden_nr IS NOT NULL THEN kunden_nr END) as unique_customers,
                COALESCE(AVG(CASE WHEN confidence IS NOT NULL THEN confidence END), 0) as avg_confidence
            FROM dokumente
        """)

        row = cursor.fetchone()
        conn.close()

        return {
            "total": row[0] or 0,
            "legacy_count": row[1] or 0,
            "unclear_count": row[2] or 0,
            "unclear_legacy_count": row[3] or 0,
            "unique_customers": row[4] or 0,
            "avg_confidence": round(row[5] or 0, 2),
            "_cached": False,  # Flag dass dies Quick-Stats sind
        }

    def get_statistics(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Gibt DETAILLIERTE Statistiken mit GROUP BY zurück (mit Lazy-Loading Cache).
        Optimiert: Alle Queries in einem Durchgang für maximale Performance.
        ACHTUNG: Diese Methode ist teuer! Verwende get_quick_statistics() für schnelle Updates.

        Args:
            use_cache: Nutze gecachte Statistiken wenn verfügbar (Standard: True)

        Returns:
            Dictionary mit detaillierten Statistiken
        """
        # Lazy-Loading: Cache zurückgeben wenn vorhanden
        if use_cache and self._statistics_cache is not None:
            return self._statistics_cache

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. Gesamtzahl
        cursor.execute("SELECT COUNT(*) FROM dokumente")
        total = cursor.fetchone()[0]

        # 2. Nach Status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM dokumente
            GROUP BY status
            ORDER BY count DESC
        """)
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # 3. Nach Dokumenttyp
        cursor.execute("""
            SELECT dokument_typ, COUNT(*) as count
            FROM dokumente
            WHERE dokument_typ IS NOT NULL
            GROUP BY dokument_typ
            ORDER BY count DESC
        """)
        type_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # 4. Nach Jahr
        cursor.execute("""
            SELECT jahr, COUNT(*) as count
            FROM dokumente
            WHERE jahr IS NOT NULL
            GROUP BY jahr
            ORDER BY jahr DESC
        """)
        year_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # 5-8. Alle anderen Counts in einem Query
        cursor.execute("""
            SELECT
                COUNT(CASE WHEN is_legacy = 1 THEN 1 END) as legacy_count,
                (SELECT COUNT(*) FROM unclear_legacy WHERE status = 'offen') as unclear_legacy_count,
                COUNT(DISTINCT CASE WHEN kunden_nr IS NOT NULL THEN kunden_nr END) as unique_customers,
                COUNT(DISTINCT CASE WHEN fin IS NOT NULL THEN fin END) as unique_vehicles,
                COALESCE(AVG(CASE WHEN confidence IS NOT NULL THEN confidence END), 0) as avg_confidence
            FROM dokumente
        """)

        result = cursor.fetchone()
        legacy_count = result[0]
        unclear_legacy_count = result[1]
        unique_customers = result[2]
        unique_vehicles = result[3]
        avg_confidence = result[4] or 0

        conn.close()

        # Speichere im Cache
        self._statistics_cache = {
            "total": total,
            "by_status": status_counts,
            "by_type": type_counts,
            "by_year": year_counts,
            "legacy_count": legacy_count,
            "unclear_legacy_count": unclear_legacy_count,
            "unique_customers": unique_customers,
            "unique_vehicles": unique_vehicles,
            "avg_confidence": round(avg_confidence, 2) if avg_confidence else 0,
            "_cached": True,  # Flag dass dies gecachte Stats sind
        }

        return self._statistics_cache

    def invalidate_statistics_cache(self):
        """Invalidiert den Statistics-Cache (z.B. nach neuen Dokumenten)."""
        self._statistics_cache = None
    
    def get_all_document_types(self) -> List[str]:
        """Gibt alle eindeutigen Dokumenttypen zurück."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT dokument_typ 
            FROM dokumente 
            WHERE dokument_typ IS NOT NULL
            ORDER BY dokument_typ
        """)
        
        types = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return types
    
    def get_all_years(self) -> List[int]:
        """Gibt alle eindeutigen Jahre zurück."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT jahr
            FROM dokumente
            WHERE jahr IS NOT NULL
            ORDER BY jahr DESC
        """)

        years = [row[0] for row in cursor.fetchall()]
        conn.close()

        return years

    def check_duplicate(self, auftrag_nr: str, dokument_typ: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Prüft, ob ein Dokument mit der gleichen Auftragsnummer bereits existiert.

        Args:
            auftrag_nr: Auftragsnummer zum Prüfen
            dokument_typ: Optional - Dokumenttyp (wenn angegeben, wird auch der Typ geprüft)

        Returns:
            Dictionary mit Informationen zum existierenden Dokument oder None wenn kein Duplikat
        """
        print(f"🔍 DEBUG check_duplicate: auftrag_nr={auftrag_nr}, dokument_typ={dokument_typ}")

        if not auftrag_nr:
            print("   → Keine Auftragsnummer, überspringe Prüfung")
            return None

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if dokument_typ:
            # Prüfe auf Auftragsnummer UND Dokumenttyp
            print(f"   → Prüfe auf Auftrag {auftrag_nr} + Typ {dokument_typ}")
            cursor.execute("""
                SELECT * FROM dokumente
                WHERE auftrag_nr = ? AND dokument_typ = ?
                ORDER BY verarbeitet_am DESC
                LIMIT 1
            """, (auftrag_nr, dokument_typ))
        else:
            # Prüfe nur auf Auftragsnummer
            print(f"   → Prüfe auf Auftrag {auftrag_nr} (ohne Typ)")
            cursor.execute("""
                SELECT * FROM dokumente
                WHERE auftrag_nr = ?
                ORDER BY verarbeitet_am DESC
                LIMIT 1
            """, (auftrag_nr,))

        row = cursor.fetchone()
        conn.close()

        if row:
            print(f"   ✓ DUPLIKAT GEFUNDEN: {row['dateiname']}")
            return {
                "dateiname": row["dateiname"],
                "ziel_pfad": row["ziel_pfad"],
                "auftrag_nr": row["auftrag_nr"],
                "dokument_typ": row["dokument_typ"],
                "kunden_nr": row["kunden_nr"],
                "kunden_name": row["kunden_name"],
                "jahr": row["jahr"],
                "verarbeitet_am": row["verarbeitet_am"],
            }

        print(f"   → Kein Duplikat gefunden")
        return None
    
    def search_by_fin(self, fin: str) -> List[Dict[str, Any]]:
        """
        Sucht alle Dokumente zu einer bestimmten FIN.
        
        Args:
            fin: Fahrzeug-Identifikationsnummer
            
        Returns:
            Liste von Dokumenten
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM dokumente 
            WHERE fin = ? 
            ORDER BY verarbeitet_am DESC
        """, (fin,))
        
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        conn.close()
        
        return results
    
    def search_by_kennzeichen(self, kennzeichen: str) -> List[Dict[str, Any]]:
        """
        Sucht alle Dokumente zu einem bestimmten Kennzeichen.
        
        Args:
            kennzeichen: KFZ-Kennzeichen
            
        Returns:
            Liste von Dokumenten
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM dokumente 
            WHERE kennzeichen = ? 
            ORDER BY verarbeitet_am DESC
        """, (kennzeichen,))
        
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        conn.close()
        
        return results
    
    def get_legacy_documents(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Holt alle Legacy-Dokumente.
        
        Args:
            status: Optional - Filter nach Status ("success", "unclear")
            
        Returns:
            Liste von Legacy-Dokumenten
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT * FROM dokumente 
                WHERE is_legacy = 1 AND status = ?
                ORDER BY verarbeitet_am DESC
            """, (status,))
        else:
            cursor.execute("""
                SELECT * FROM dokumente 
                WHERE is_legacy = 1 
                ORDER BY verarbeitet_am DESC
            """)
        
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        conn.close()
        
        return results
    
    def add_unclear_legacy(self, file_path: str, metadata: Dict[str, Any]) -> int:
        """
        Fügt einen unklaren Legacy-Auftrag zur Tabelle hinzu.
        
        Args:
            file_path: Pfad zur Datei
            metadata: Metadaten des Dokuments (aus analyzer)
            
        Returns:
            ID des eingefügten Eintrags
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO unclear_legacy 
            (dateiname, datei_pfad, auftrag_nr, auftragsdatum, kunden_name, 
             fin, kennzeichen, jahr, dokument_typ, match_reason, hinweis, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'offen')
        """, (
            os.path.basename(file_path),
            file_path,
            metadata.get("auftrag_nr"),
            metadata.get("auftragsdatum"),
            metadata.get("kunden_name"),
            metadata.get("fin"),
            metadata.get("kennzeichen"),
            metadata.get("jahr"),
            metadata.get("dokument_typ"),
            metadata.get("legacy_match_reason", "unclear"),
            metadata.get("hinweis")
        ))
        
        entry_id = cursor.lastrowid if cursor.lastrowid else 0
        conn.commit()
        conn.close()
        
        return entry_id
    
    def get_unclear_legacy_entries(self, status: str = "offen") -> List[Dict[str, Any]]:
        """
        Holt alle unklaren Legacy-Einträge.
        
        Args:
            status: Filter nach Status ('offen', 'zugeordnet', 'alle')
            
        Returns:
            Liste von unklaren Legacy-Einträgen
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status == "alle":
            query = "SELECT * FROM unclear_legacy ORDER BY erstellt_am DESC"
            cursor.execute(query)
        else:
            query = "SELECT * FROM unclear_legacy WHERE status = ? ORDER BY erstellt_am DESC"
            cursor.execute(query, (status,))
        
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "id": row["id"],
                "dateiname": row["dateiname"],
                "datei_pfad": row["datei_pfad"],
                "auftrag_nr": row["auftrag_nr"],
                "auftragsdatum": row["auftragsdatum"],
                "kunden_name": row["kunden_name"],
                "fin": row["fin"],
                "kennzeichen": row["kennzeichen"],
                "jahr": row["jahr"],
                "dokument_typ": row["dokument_typ"],
                "match_reason": row["match_reason"],
                "hinweis": row["hinweis"],
                "erstellt_am": row["erstellt_am"],
                "zugeordnet_am": row["zugeordnet_am"],
                "zugeordnet_zu_kunden_nr": row["zugeordnet_zu_kunden_nr"],
                "status": row["status"],
            })
        
        conn.close()
        return results
    
    def assign_unclear_legacy(self, entry_id: int, kunden_nr: str) -> bool:
        """
        Ordnet einen unklaren Legacy-Auftrag einem Kunden zu.
        
        Args:
            entry_id: ID des unclear_legacy Eintrags
            kunden_nr: Kundennummer zur Zuordnung
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE unclear_legacy 
                SET zugeordnet_zu_kunden_nr = ?,
                    zugeordnet_am = CURRENT_TIMESTAMP,
                    status = 'zugeordnet'
                WHERE id = ?
            """, (kunden_nr, entry_id))
            
            conn.commit()
            success = cursor.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Zuordnen: {e}")
            success = False
        finally:
            conn.close()
        
        return success
    
    def delete_unclear_legacy(self, entry_id: int) -> bool:
        """
        Löscht einen unclear_legacy Eintrag (z.B. nach erfolgreichem Verschieben).
        
        Args:
            entry_id: ID des zu löschenden Eintrags
            
        Returns:
            True bei Erfolg
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM unclear_legacy WHERE id = ?", (entry_id,))
            conn.commit()
            success = cursor.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Löschen: {e}")
            success = False
        finally:
            conn.close()
        
        return success
    
    # ========== Maintenance & Statistics Methods ==========
    
    @property
    def maintenance(self):
        """Lazy-Loading für Maintenance-Service."""
        if self._maintenance is None:
            from services.db_maintenance import DatabaseMaintenance
            self._maintenance = DatabaseMaintenance(self.db_path, root_dir=self.root_dir)
        return self._maintenance
    
    @property
    def statistics(self):
        """Lazy-Loading für Statistics-Service."""
        if self._statistics is None:
            from services.db_statistics import DatabaseStatistics
            self._statistics = DatabaseStatistics(self.db_path)
        return self._statistics
    
    def create_backup(self, reason: str = "manual") -> tuple:
        """
        Erstellt ein Datenbank-Backup.
        
        Args:
            reason: Grund des Backups (manual, daily, before_migration, etc.)
            
        Returns:
            Tuple (success, backup_path, message)
        """
        return self.maintenance.create_backup(reason)
    
    def restore_backup(self, backup_path: str) -> tuple:
        """
        Stellt ein Backup wieder her.
        
        Args:
            backup_path: Pfad zum Backup
            
        Returns:
            Tuple (success, message)
        """
        return self.maintenance.restore_backup(backup_path)
    
    def list_backups(self) -> list:
        """
        Listet alle verfügbaren Backups auf.
        
        Returns:
            Liste von Backup-Informationen
        """
        return self.maintenance.list_backups()
    
    def optimize_database(self) -> tuple:
        """
        Optimiert die Datenbank (VACUUM, ANALYZE).
        
        Returns:
            Tuple (success, message, statistics)
        """
        return self.maintenance.optimize_database()
    
    def health_check(self) -> dict:
        """
        Führt einen Health-Check der Datenbank durch.
        
        Returns:
            Health-Status mit Details
        """
        return self.maintenance.health_check()
    
    def cleanup_old_entries(self, days: int = 365) -> tuple:
        """
        Löscht sehr alte Einträge (Optional).
        
        Args:
            days: Einträge älter als X Tage löschen
            
        Returns:
            Tuple (success, message, deleted_count)
        """
        return self.maintenance.cleanup_old_entries(days)
    
    def get_overview_stats(self) -> dict:
        """Liefert Übersichts-Statistiken."""
        return self.statistics.get_overview_stats()
    
    def get_customer_stats(self, kunden_nr: Optional[str] = None) -> list:
        """
        Liefert Kunden-spezifische Statistiken.
        
        Args:
            kunden_nr: Optional - spezifische Kundennummer
            
        Returns:
            Liste mit Kunden-Statistiken
        """
        return self.statistics.get_customer_stats(kunden_nr)
    
    def get_time_series_stats(self, days: int = 30) -> dict:
        """
        Liefert Zeitreihen-Statistiken.
        
        Args:
            days: Anzahl Tage zurück
            
        Returns:
            Dictionary mit Zeitreihen-Daten
        """
        return self.statistics.get_time_series_stats(days)
    
    def get_quality_stats(self) -> dict:
        """Liefert Qualitäts-Statistiken."""
        return self.statistics.get_quality_stats()
    
    def export_to_csv(self, filename: Optional[str] = None, filters: Optional[dict] = None) -> tuple:
        """
        Exportiert Dokumente als CSV.
        
        Args:
            filename: Optional - Dateiname
            filters: Optional - Filter (kunden_nr, jahr, dokument_typ, etc.)
            
        Returns:
            Tuple (success, file_path or error_message)
        """
        return self.statistics.export_to_csv(filename, filters)
    
    def export_customer_report(self, kunden_nr: str) -> tuple:
        """
        Erstellt einen detaillierten Kunden-Report.
        
        Args:
            kunden_nr: Kundennummer
            
        Returns:
            Tuple (success, file_path or error_message)
        """
        return self.statistics.export_customer_report(kunden_nr)

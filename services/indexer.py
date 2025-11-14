"""
Indexierungs-Service für WerkstattArchiv.
Speichert Metadaten aller verarbeiteten Dokumente in einer SQLite-Datenbank.
"""

import sqlite3
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


DB_FILE = "werkstatt_index.db"


class DocumentIndex:
    """Verwaltet den Index aller verarbeiteten Dokumente."""
    
    def __init__(self, db_path: str = DB_FILE):
        """
        Initialisiert den Dokumenten-Index.
        
        Args:
            db_path: Pfad zur SQLite-Datenbankdatei
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Erstellt die Datenbanktabelle falls nicht vorhanden."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        
        return doc_id
    
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
              dateiname: Optional[str] = None) -> List[Dict[str, Any]]:
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
            # Filtere nach Monat basierend auf dem verarbeitet_am Datum
            query += " AND CAST(strftime('%m', verarbeitet_am) AS INTEGER) = ?"
            params.append(monat)
        
        if kunden_name:
            query += " AND kunden_name LIKE ?"
            params.append(f"%{kunden_name}%")
        
        if dateiname:
            query += " AND dateiname LIKE ?"
            params.append(f"%{dateiname}%")
        
        query += " ORDER BY verarbeitet_am DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "id": row["id"],
                "dateiname": row["dateiname"],
                "original_pfad": row["original_pfad"],
                "ziel_pfad": row["ziel_pfad"],
                "auftrag_nr": row["auftrag_nr"],
                "auftragsdatum": row["auftragsdatum"] if "auftragsdatum" in row.keys() else None,
                "dokument_typ": row["dokument_typ"],
                "jahr": row["jahr"],
                "kunden_nr": row["kunden_nr"],
                "kunden_name": row["kunden_name"],
                "fin": row["fin"] if "fin" in row.keys() else None,
                "kennzeichen": row["kennzeichen"] if "kennzeichen" in row.keys() else None,
                "kilometerstand": row["kilometerstand"] if "kilometerstand" in row.keys() else None,
                "is_legacy": bool(row["is_legacy"]) if "is_legacy" in row.keys() else False,
                "match_reason": row["match_reason"] if "match_reason" in row.keys() else None,
                "confidence": row["confidence"],
                "status": row["status"],
                "hinweis": row["hinweis"],
                "verarbeitet_am": row["verarbeitet_am"],
                "created_at": row["created_at"] if "created_at" in row.keys() else None,
                "last_update": row["last_update"] if "last_update" in row.keys() else None,
            })
        
        conn.close()
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über die indexierten Dokumente zurück.
        Optimiert: Alle Queries in einem Durchgang für maximale Performance.

        Returns:
            Dictionary mit Statistiken
        """
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

        return {
            "total": total,
            "by_status": status_counts,
            "by_type": type_counts,
            "by_year": year_counts,
            "legacy_count": legacy_count,
            "unclear_legacy_count": unclear_legacy_count,
            "unique_customers": unique_customers,
            "unique_vehicles": unique_vehicles,
            "avg_confidence": round(avg_confidence, 2) if avg_confidence else 0,
        }
    
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

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
                kunden_nr TEXT,
                kunden_name TEXT,
                auftrag_nr TEXT,
                dokument_typ TEXT,
                jahr INTEGER,
                confidence REAL,
                verarbeitet_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                hinweis TEXT
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
        
        # Index für schnellere Suchen
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
        
        # Index für unclear_legacy
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
        
        conn.commit()
        conn.close()
    
    def add_document(self, original_path: str, target_path: str, 
                    metadata: Dict[str, Any], status: str = "success") -> int:
        """
        Fügt ein Dokument zum Index hinzu.
        
        Args:
            original_path: Ursprünglicher Dateipfad
            target_path: Zielpfad nach Verarbeitung
            metadata: Metadaten des Dokuments
            status: Status (success, unclear, error)
            
        Returns:
            ID des eingefügten Dokuments
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO dokumente 
            (dateiname, original_pfad, ziel_pfad, kunden_nr, kunden_name, 
             auftrag_nr, dokument_typ, jahr, confidence, status, hinweis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            os.path.basename(target_path),
            original_path,
            target_path,
            metadata.get("kunden_nr"),
            metadata.get("kunden_name"),
            metadata.get("auftrag_nr"),
            metadata.get("dokument_typ"),
            metadata.get("jahr"),
            metadata.get("confidence"),
            status,
            metadata.get("hinweis")
        ))
        
        doc_id = cursor.lastrowid if cursor.lastrowid else 0
        conn.commit()
        conn.close()
        
        return doc_id
    
    def search(self, kunden_nr: Optional[str] = None, 
              auftrag_nr: Optional[str] = None,
              dokument_typ: Optional[str] = None,
              jahr: Optional[int] = None,
              kunden_name: Optional[str] = None,
              dateiname: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Sucht nach Dokumenten im Index.
        
        Args:
            kunden_nr: Kundennummer (exakte Suche)
            auftrag_nr: Auftragsnummer (exakte Suche)
            dokument_typ: Dokumenttyp (exakte Suche)
            jahr: Jahr (exakte Suche)
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
                "kunden_nr": row["kunden_nr"],
                "kunden_name": row["kunden_name"],
                "auftrag_nr": row["auftrag_nr"],
                "dokument_typ": row["dokument_typ"],
                "jahr": row["jahr"],
                "confidence": row["confidence"],
                "verarbeitet_am": row["verarbeitet_am"],
                "status": row["status"],
                "hinweis": row["hinweis"],
            })
        
        conn.close()
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über die indexierten Dokumente zurück.
        
        Returns:
            Dictionary mit Statistiken
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Gesamtzahl
        cursor.execute("SELECT COUNT(*) FROM dokumente")
        total = cursor.fetchone()[0]
        
        # Nach Status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM dokumente 
            GROUP BY status
        """)
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Nach Dokumenttyp
        cursor.execute("""
            SELECT dokument_typ, COUNT(*) as count 
            FROM dokumente 
            GROUP BY dokument_typ 
            ORDER BY count DESC 
            LIMIT 10
        """)
        type_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Nach Jahr
        cursor.execute("""
            SELECT jahr, COUNT(*) as count 
            FROM dokumente 
            WHERE jahr IS NOT NULL
            GROUP BY jahr 
            ORDER BY jahr DESC
        """)
        year_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "total": total,
            "by_status": status_counts,
            "by_type": type_counts,
            "by_year": year_counts,
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

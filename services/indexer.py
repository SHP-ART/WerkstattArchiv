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

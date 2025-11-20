"""
Datenbank-Statistik und Export-Service für WerkstattArchiv.
Erweiterte Analysen, Reports und Datenexport.
"""

import sqlite3
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import json


class DatabaseStatistics:
    """Erweiterte Statistiken und Analysen für die Werkstatt-Datenbank."""
    
    def __init__(self, db_path: str = "werkstatt_index.db"):
        """
        Initialisiert den Statistik-Service.
        
        Args:
            db_path: Pfad zur Datenbank-Datei
        """
        self.db_path = db_path
        self.export_dir = Path("data/exports")
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def get_overview_stats(self) -> Dict[str, Any]:
        """
        Liefert Übersichts-Statistiken.
        
        Returns:
            Dictionary mit allgemeinen Statistiken
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            stats = {}
            
            # Gesamt-Dokumente
            cursor.execute("SELECT COUNT(*) FROM dokumente")
            stats["total_documents"] = cursor.fetchone()[0]
            
            # Nach Status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM dokumente 
                GROUP BY status
            """)
            stats["by_status"] = {row["status"]: row["count"] for row in cursor.fetchall()}
            
            # Nach Dokument-Typ
            cursor.execute("""
                SELECT dokument_typ, COUNT(*) as count 
                FROM dokumente 
                WHERE dokument_typ IS NOT NULL
                GROUP BY dokument_typ
                ORDER BY count DESC
                LIMIT 10
            """)
            stats["top_document_types"] = [
                {"type": row["dokument_typ"], "count": row["count"]} 
                for row in cursor.fetchall()
            ]
            
            # Nach Jahr
            cursor.execute("""
                SELECT jahr, COUNT(*) as count 
                FROM dokumente 
                WHERE jahr IS NOT NULL
                GROUP BY jahr
                ORDER BY jahr DESC
            """)
            stats["by_year"] = {row["jahr"]: row["count"] for row in cursor.fetchall()}
            
            # Durchschnittliche Confidence
            cursor.execute("""
                SELECT 
                    AVG(confidence) as avg_confidence,
                    MIN(confidence) as min_confidence,
                    MAX(confidence) as max_confidence
                FROM dokumente
                WHERE confidence IS NOT NULL
            """)
            confidence_row = cursor.fetchone()
            stats["confidence"] = {
                "average": round(confidence_row["avg_confidence"], 2) if confidence_row["avg_confidence"] else 0,
                "min": round(confidence_row["min_confidence"], 2) if confidence_row["min_confidence"] else 0,
                "max": round(confidence_row["max_confidence"], 2) if confidence_row["max_confidence"] else 0
            }
            
            # Legacy-Aufträge
            cursor.execute("SELECT COUNT(*) FROM unclear_legacy WHERE status='offen'")
            stats["open_legacy_count"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM unclear_legacy WHERE status='zugeordnet'")
            stats["resolved_legacy_count"] = cursor.fetchone()[0]
            
            # Neueste Dokumente
            cursor.execute("""
                SELECT dateiname, verarbeitet_am, kunden_name
                FROM dokumente
                ORDER BY verarbeitet_am DESC
                LIMIT 5
            """)
            stats["recent_documents"] = [
                {
                    "filename": row["dateiname"],
                    "processed": row["verarbeitet_am"],
                    "customer": row["kunden_name"]
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return stats
            
        except Exception as e:
            return {"error": f"Statistik fehlgeschlagen: {type(e).__name__}: {e}"}
    
    def get_customer_stats(self, kunden_nr: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Liefert Kunden-spezifische Statistiken.
        
        Args:
            kunden_nr: Optional - spezifische Kundennummer, sonst Top-Kunden
            
        Returns:
            Liste mit Kunden-Statistiken
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if kunden_nr:
                # Einzelner Kunde
                cursor.execute("""
                    SELECT 
                        kunden_nr,
                        kunden_name,
                        COUNT(*) as document_count,
                        AVG(confidence) as avg_confidence,
                        MIN(verarbeitet_am) as first_document,
                        MAX(verarbeitet_am) as last_document
                    FROM dokumente
                    WHERE kunden_nr = ?
                    GROUP BY kunden_nr, kunden_name
                """, (kunden_nr,))
            else:
                # Top 20 Kunden
                cursor.execute("""
                    SELECT 
                        kunden_nr,
                        kunden_name,
                        COUNT(*) as document_count,
                        AVG(confidence) as avg_confidence,
                        MIN(verarbeitet_am) as first_document,
                        MAX(verarbeitet_am) as last_document
                    FROM dokumente
                    WHERE kunden_nr IS NOT NULL
                    GROUP BY kunden_nr, kunden_name
                    ORDER BY document_count DESC
                    LIMIT 20
                """)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "kunden_nr": row["kunden_nr"],
                    "kunden_name": row["kunden_name"],
                    "document_count": row["document_count"],
                    "avg_confidence": round(row["avg_confidence"], 2) if row["avg_confidence"] else 0,
                    "first_document": row["first_document"],
                    "last_document": row["last_document"]
                })
            
            conn.close()
            
            return results
            
        except Exception as e:
            return [{"error": f"Kunden-Statistik fehlgeschlagen: {type(e).__name__}: {e}"}]
    
    def get_time_series_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Liefert Zeitreihen-Statistiken.
        
        Args:
            days: Anzahl Tage zurück
            
        Returns:
            Dictionary mit Zeitreihen-Daten
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Dokumente pro Tag
            cursor.execute("""
                SELECT 
                    DATE(verarbeitet_am) as date,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM dokumente
                WHERE verarbeitet_am >= ?
                GROUP BY DATE(verarbeitet_am)
                ORDER BY date DESC
            """, (cutoff_date,))
            
            daily_stats = []
            for row in cursor.fetchall():
                daily_stats.append({
                    "date": row["date"],
                    "document_count": row["count"],
                    "avg_confidence": round(row["avg_confidence"], 2) if row["avg_confidence"] else 0
                })
            
            # Dokument-Typen Trend
            cursor.execute("""
                SELECT 
                    DATE(verarbeitet_am) as date,
                    dokument_typ,
                    COUNT(*) as count
                FROM dokumente
                WHERE verarbeitet_am >= ? AND dokument_typ IS NOT NULL
                GROUP BY DATE(verarbeitet_am), dokument_typ
                ORDER BY date DESC, count DESC
            """, (cutoff_date,))
            
            type_trends = []
            for row in cursor.fetchall():
                type_trends.append({
                    "date": row["date"],
                    "document_type": row["dokument_typ"],
                    "count": row["count"]
                })
            
            conn.close()
            
            return {
                "daily_documents": daily_stats,
                "type_trends": type_trends
            }
            
        except Exception as e:
            return {"error": f"Zeitreihen-Statistik fehlgeschlagen: {type(e).__name__}: {e}"}
    
    def get_quality_stats(self) -> Dict[str, Any]:
        """
        Liefert Qualitäts-Statistiken (Confidence, Verarbeitungsqualität).
        
        Returns:
            Dictionary mit Qualitäts-Metriken
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            stats = {}
            
            # Confidence-Verteilung
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN confidence >= 0.9 THEN 'excellent (≥0.9)'
                        WHEN confidence >= 0.7 THEN 'good (0.7-0.9)'
                        WHEN confidence >= 0.5 THEN 'medium (0.5-0.7)'
                        ELSE 'low (<0.5)'
                    END as quality_level,
                    COUNT(*) as count
                FROM dokumente
                WHERE confidence IS NOT NULL
                GROUP BY quality_level
            """)
            
            stats["confidence_distribution"] = {
                row["quality_level"]: row["count"] 
                for row in cursor.fetchall()
            }
            
            # Niedrige Confidence-Dokumente
            cursor.execute("""
                SELECT dateiname, kunden_name, confidence, dokument_typ
                FROM dokumente
                WHERE confidence < 0.5 AND confidence IS NOT NULL
                ORDER BY confidence ASC
                LIMIT 10
            """)
            
            stats["low_confidence_documents"] = [
                {
                    "filename": row["dateiname"],
                    "customer": row["kunden_name"],
                    "confidence": round(row["confidence"], 2),
                    "type": row["dokument_typ"]
                }
                for row in cursor.fetchall()
            ]
            
            # Legacy-Zuordnungs-Qualität
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM unclear_legacy
                GROUP BY status
            """)
            
            stats["legacy_resolution"] = {
                row["status"]: row["count"] 
                for row in cursor.fetchall()
            }
            
            conn.close()
            
            return stats
            
        except Exception as e:
            return {"error": f"Qualitäts-Statistik fehlgeschlagen: {type(e).__name__}: {e}"}
    
    def export_to_csv(
        self,
        filename: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Exportiert Dokumente als CSV.
        
        Args:
            filename: Optional - Dateiname (generiert automatisch wenn None)
            filters: Optional - Filter (kunden_nr, jahr, dokument_typ, date_from, date_to)
            
        Returns:
            Tuple (success, file_path or error_message)
        """
        try:
            if filename is None:
                filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            filepath = self.export_dir / filename
            
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query with filters
            query = "SELECT * FROM dokumente WHERE 1=1"
            params = []
            
            if filters:
                if filters.get("kunden_nr"):
                    query += " AND kunden_nr = ?"
                    params.append(filters["kunden_nr"])
                
                if filters.get("jahr"):
                    query += " AND jahr = ?"
                    params.append(filters["jahr"])
                
                if filters.get("dokument_typ"):
                    query += " AND dokument_typ = ?"
                    params.append(filters["dokument_typ"])
                
                if filters.get("date_from"):
                    query += " AND verarbeitet_am >= ?"
                    params.append(filters["date_from"])
                
                if filters.get("date_to"):
                    query += " AND verarbeitet_am <= ?"
                    params.append(filters["date_to"])
            
            query += " ORDER BY verarbeitet_am DESC"
            
            cursor.execute(query, params)
            
            # Write CSV
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                rows = cursor.fetchall()
                
                if not rows:
                    conn.close()
                    return False, "Keine Daten zum Export gefunden"
                
                # Get column names
                columns = rows[0].keys()
                
                writer = csv.DictWriter(csvfile, fieldnames=columns)
                writer.writeheader()
                
                for row in rows:
                    writer.writerow(dict(row))
            
            conn.close()
            
            return True, str(filepath)
            
        except Exception as e:
            return False, f"Export fehlgeschlagen: {type(e).__name__}: {e}"
    
    def export_customer_report(self, kunden_nr: str) -> Tuple[bool, str]:
        """
        Erstellt einen detaillierten Kunden-Report als JSON.
        
        Args:
            kunden_nr: Kundennummer
            
        Returns:
            Tuple (success, file_path or error_message)
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Kunden-Info
            cursor.execute("""
                SELECT DISTINCT kunden_nr, kunden_name
                FROM dokumente
                WHERE kunden_nr = ?
            """, (kunden_nr,))
            
            customer_row = cursor.fetchone()
            if not customer_row:
                conn.close()
                return False, f"Kunde {kunden_nr} nicht gefunden"
            
            report = {
                "report_generated": datetime.now().isoformat(),
                "customer": {
                    "kunden_nr": customer_row["kunden_nr"],
                    "kunden_name": customer_row["kunden_name"]
                }
            }
            
            # Statistiken
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_documents,
                    AVG(confidence) as avg_confidence,
                    MIN(verarbeitet_am) as first_document,
                    MAX(verarbeitet_am) as last_document
                FROM dokumente
                WHERE kunden_nr = ?
            """, (kunden_nr,))
            
            stats_row = cursor.fetchone()
            report["statistics"] = {
                "total_documents": stats_row["total_documents"],
                "avg_confidence": round(stats_row["avg_confidence"], 2) if stats_row["avg_confidence"] else 0,
                "first_document": stats_row["first_document"],
                "last_document": stats_row["last_document"]
            }
            
            # Dokumente nach Typ
            cursor.execute("""
                SELECT dokument_typ, COUNT(*) as count
                FROM dokumente
                WHERE kunden_nr = ? AND dokument_typ IS NOT NULL
                GROUP BY dokument_typ
                ORDER BY count DESC
            """, (kunden_nr,))
            
            report["document_types"] = [
                {"type": row["dokument_typ"], "count": row["count"]}
                for row in cursor.fetchall()
            ]
            
            # Dokumente nach Jahr
            cursor.execute("""
                SELECT jahr, COUNT(*) as count
                FROM dokumente
                WHERE kunden_nr = ? AND jahr IS NOT NULL
                GROUP BY jahr
                ORDER BY jahr DESC
            """, (kunden_nr,))
            
            report["by_year"] = {
                row["jahr"]: row["count"]
                for row in cursor.fetchall()
            }
            
            # Alle Dokumente
            cursor.execute("""
                SELECT 
                    dateiname, auftrag_nr, dokument_typ, jahr,
                    confidence, verarbeitet_am, ziel_pfad
                FROM dokumente
                WHERE kunden_nr = ?
                ORDER BY verarbeitet_am DESC
            """, (kunden_nr,))
            
            report["documents"] = [
                {
                    "filename": row["dateiname"],
                    "auftrag_nr": row["auftrag_nr"],
                    "dokument_typ": row["dokument_typ"],
                    "jahr": row["jahr"],
                    "confidence": row["confidence"],
                    "processed_at": row["verarbeitet_am"],
                    "path": row["ziel_pfad"]
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            # Schreibe Report
            filename = f"kunde_{kunden_nr}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.export_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return True, str(filepath)
            
        except Exception as e:
            return False, f"Report-Erstellung fehlgeschlagen: {type(e).__name__}: {e}"

"""
GUI-Tab für Datenbank-Wartung, Statistiken und Backups.
Integration in das Main Window Settings.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
from datetime import datetime
from typing import Optional


class DatabaseManagementTab(ctk.CTkFrame):
    """Tab für Datenbank-Wartung und Statistiken."""
    
    def __init__(self, parent, indexer):
        """
        Initialisiert den Database-Management Tab.
        
        Args:
            parent: Parent Widget
            indexer: DocumentIndex Instanz
        """
        super().__init__(parent)
        self.indexer = indexer
        
        # Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Scrollable Frame
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Datenbank-Verwaltung")
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Erstellt alle Widgets."""
        
        # ========== Backup Section ==========
        backup_frame = ctk.CTkFrame(self.scroll_frame)
        backup_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            backup_frame,
            text="📦 Datenbank-Backups",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Backup Controls
        backup_controls = ctk.CTkFrame(backup_frame)
        backup_controls.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            backup_controls,
            text="Backup erstellen",
            command=self._create_backup,
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            backup_controls,
            text="Backups anzeigen",
            command=self._show_backups,
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            backup_controls,
            text="Backup wiederherstellen",
            command=self._restore_backup,
            width=150
        ).pack(side="left", padx=5)
        
        # Backup Info
        self.backup_info_label = ctk.CTkLabel(
            backup_frame,
            text="Lade Backup-Informationen...",
            anchor="w"
        )
        self.backup_info_label.pack(fill="x", padx=10, pady=5)
        
        # ========== Maintenance Section ==========
        maintenance_frame = ctk.CTkFrame(self.scroll_frame)
        maintenance_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            maintenance_frame,
            text="🔧 Wartung & Optimierung",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Maintenance Controls
        maintenance_controls = ctk.CTkFrame(maintenance_frame)
        maintenance_controls.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            maintenance_controls,
            text="Datenbank optimieren",
            command=self._optimize_database,
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            maintenance_controls,
            text="Health-Check",
            command=self._health_check,
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            maintenance_controls,
            text="Alte Einträge löschen",
            command=self._cleanup_dialog,
            width=150
        ).pack(side="left", padx=5)
        
        # Health Info
        self.health_info_label = ctk.CTkLabel(
            maintenance_frame,
            text="Bereit für Wartungs-Operationen",
            anchor="w"
        )
        self.health_info_label.pack(fill="x", padx=10, pady=5)
        
        # ========== Statistics Section ==========
        statistics_frame = ctk.CTkFrame(self.scroll_frame)
        statistics_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            statistics_frame,
            text="📊 Statistiken & Reports",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Statistics Controls
        stats_controls = ctk.CTkFrame(statistics_frame)
        stats_controls.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            stats_controls,
            text="Übersicht",
            command=self._show_overview_stats,
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            stats_controls,
            text="Kunden-Statistik",
            command=self._show_customer_stats,
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            stats_controls,
            text="Zeitreihen",
            command=self._show_time_series,
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            stats_controls,
            text="Qualität",
            command=self._show_quality_stats,
            width=120
        ).pack(side="left", padx=5)
        
        # Statistics Display
        self.stats_text = ctk.CTkTextbox(statistics_frame, height=200)
        self.stats_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # ========== Export Section ==========
        export_frame = ctk.CTkFrame(self.scroll_frame)
        export_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            export_frame,
            text="💾 Daten-Export",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Export Controls
        export_controls = ctk.CTkFrame(export_frame)
        export_controls.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            export_controls,
            text="CSV Export",
            command=self._export_csv,
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            export_controls,
            text="Kunden-Report",
            command=self._export_customer_report,
            width=150
        ).pack(side="left", padx=5)
        
        self.export_info_label = ctk.CTkLabel(
            export_frame,
            text="Bereit für Export",
            anchor="w"
        )
        self.export_info_label.pack(fill="x", padx=10, pady=5)
        
        # Initial Load
        self._load_initial_info()
    
    def _load_initial_info(self):
        """Lädt initiale Informationen."""
        threading.Thread(target=self._load_backup_info, daemon=True).start()
    
    def _load_backup_info(self):
        """Lädt Backup-Informationen im Hintergrund."""
        try:
            backups = self.indexer.list_backups()
            if backups:
                last_backup = backups[0]
                age_days = last_backup.get("age_days", 0)
                info = f"Letztes Backup: {last_backup.get('filename', 'N/A')} ({age_days} Tage alt) | Gesamt: {len(backups)} Backups"
            else:
                info = "Keine Backups vorhanden - Erstellen Sie ein Backup!"
            
            self.backup_info_label.configure(text=info)
        except Exception as e:
            self.backup_info_label.configure(text=f"Fehler beim Laden: {e}")
    
    def _create_backup(self):
        """Erstellt ein manuelles Backup."""
        def backup_thread():
            try:
                self.backup_info_label.configure(text="Erstelle Backup...")
                success, backup_path, message = self.indexer.create_backup(reason="manual")
                
                if success:
                    messagebox.showinfo("Backup erfolgreich", message)
                    self._load_backup_info()
                else:
                    messagebox.showerror("Backup fehlgeschlagen", message)
                    self.backup_info_label.configure(text="Backup fehlgeschlagen")
            except Exception as e:
                messagebox.showerror("Fehler", f"Backup-Fehler: {e}")
                self.backup_info_label.configure(text=f"Fehler: {e}")
        
        threading.Thread(target=backup_thread, daemon=True).start()
    
    def _show_backups(self):
        """Zeigt alle verfügbaren Backups an."""
        try:
            backups = self.indexer.list_backups()
            
            if not backups:
                messagebox.showinfo("Backups", "Keine Backups vorhanden")
                return
            
            # Erstelle Backup-Liste Window
            backup_window = ctk.CTkToplevel(self)
            backup_window.title("Verfügbare Backups")
            backup_window.geometry("800x400")
            
            # Scrollable Frame
            scroll = ctk.CTkScrollableFrame(backup_window)
            scroll.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Header
            header = ctk.CTkFrame(scroll)
            header.pack(fill="x", pady=5)
            
            ctk.CTkLabel(header, text="Dateiname", width=300, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(header, text="Größe", width=100, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(header, text="Alter", width=100, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(header, text="Grund", width=150, anchor="w").pack(side="left", padx=5)
            
            # Backup Entries
            for backup in backups:
                entry = ctk.CTkFrame(scroll)
                entry.pack(fill="x", pady=2)
                
                ctk.CTkLabel(
                    entry,
                    text=backup.get("filename", "N/A"),
                    width=300,
                    anchor="w"
                ).pack(side="left", padx=5)
                
                ctk.CTkLabel(
                    entry,
                    text=backup.get("size_formatted", "N/A"),
                    width=100,
                    anchor="w"
                ).pack(side="left", padx=5)
                
                ctk.CTkLabel(
                    entry,
                    text=f"{backup.get('age_days', 0)} Tage",
                    width=100,
                    anchor="w"
                ).pack(side="left", padx=5)
                
                ctk.CTkLabel(
                    entry,
                    text=backup.get("reason", "N/A"),
                    width=150,
                    anchor="w"
                ).pack(side="left", padx=5)
        
        except Exception as e:
            messagebox.showerror("Fehler", f"Backup-Liste konnte nicht geladen werden: {e}")
    
    def _restore_backup(self):
        """Stellt ein Backup wieder her."""
        try:
            backups = self.indexer.list_backups()
            
            if not backups:
                messagebox.showwarning("Restore", "Keine Backups zum Wiederherstellen verfügbar")
                return
            
            # Backup auswählen
            backup_path = filedialog.askopenfilename(
                title="Backup auswählen",
                initialdir="data/db_backups",
                filetypes=[("Database files", "*.db"), ("All files", "*.*")]
            )
            
            if not backup_path:
                return
            
            # Bestätigung
            confirm = messagebox.askyesno(
                "Backup wiederherstellen",
                f"WARNUNG: Die aktuelle Datenbank wird überschrieben!\n\n"
                f"Möchten Sie dieses Backup wirklich wiederherstellen?\n\n"
                f"{backup_path}"
            )
            
            if not confirm:
                return
            
            def restore_thread():
                success, message = self.indexer.restore_backup(backup_path)
                
                if success:
                    messagebox.showinfo("Restore erfolgreich", message + "\n\nBitte starten Sie die Anwendung neu!")
                else:
                    messagebox.showerror("Restore fehlgeschlagen", message)
            
            threading.Thread(target=restore_thread, daemon=True).start()
        
        except Exception as e:
            messagebox.showerror("Fehler", f"Restore-Fehler: {e}")
    
    def _optimize_database(self):
        """Optimiert die Datenbank."""
        confirm = messagebox.askyesno(
            "Datenbank optimieren",
            "Möchten Sie die Datenbank jetzt optimieren?\n\n"
            "Dies kann einige Sekunden dauern."
        )
        
        if not confirm:
            return
        
        def optimize_thread():
            try:
                self.health_info_label.configure(text="Optimiere Datenbank...")
                success, message, stats = self.indexer.optimize_database()
                
                if success:
                    details = f"{message}\n\n"
                    details += f"Dokumente: {stats.get('documents_count', 0)}\n"
                    details += f"Größe vorher: {self._format_bytes(stats.get('size_before', 0))}\n"
                    details += f"Größe nachher: {self._format_bytes(stats.get('size_after', 0))}\n"
                    details += f"Freigegeben: {stats.get('space_saved_formatted', 'N/A')}\n"
                    details += f"Integrität: {stats.get('integrity_check', 'N/A')}"
                    
                    messagebox.showinfo("Optimierung erfolgreich", details)
                    self.health_info_label.configure(text="Optimierung abgeschlossen")
                else:
                    messagebox.showerror("Optimierung fehlgeschlagen", message)
                    self.health_info_label.configure(text="Optimierung fehlgeschlagen")
            except Exception as e:
                messagebox.showerror("Fehler", f"Optimierungs-Fehler: {e}")
                self.health_info_label.configure(text=f"Fehler: {e}")
        
        threading.Thread(target=optimize_thread, daemon=True).start()
    
    def _health_check(self):
        """Führt einen Health-Check durch."""
        def health_thread():
            try:
                self.health_info_label.configure(text="Führe Health-Check durch...")
                health = self.indexer.health_check()
                
                # Build message
                status = "✅ GESUND" if health.get("healthy", False) else "⚠️ PROBLEME GEFUNDEN"
                details = f"Status: {status}\n\n"
                
                stats = health.get("statistics", {})
                if stats:
                    details += "Statistiken:\n"
                    details += f"- Größe: {stats.get('size_formatted', 'N/A')}\n"
                    details += f"- Dokumente: {stats.get('documents', 0)}\n"
                    details += f"- Offene Legacy: {stats.get('open_legacy', 0)}\n"
                    details += f"- Indexes: {stats.get('indexes', 0)}\n"
                    details += f"- Journal-Mode: {stats.get('journal_mode', 'N/A')}\n"
                    details += f"- Integrität: {stats.get('integrity', 'N/A')}\n"
                
                warnings = health.get("warnings", [])
                if warnings:
                    details += f"\nWarnungen ({len(warnings)}):\n"
                    for warning in warnings:
                        details += f"⚠ {warning}\n"
                
                errors = health.get("errors", [])
                if errors:
                    details += f"\nFehler ({len(errors)}):\n"
                    for error in errors:
                        details += f"❌ {error}\n"
                
                messagebox.showinfo("Health-Check", details)
                self.health_info_label.configure(text=status)
            except Exception as e:
                messagebox.showerror("Fehler", f"Health-Check Fehler: {e}")
                self.health_info_label.configure(text=f"Fehler: {e}")
        
        threading.Thread(target=health_thread, daemon=True).start()
    
    def _cleanup_dialog(self):
        """Dialog zum Löschen alter Einträge."""
        dialog = ctk.CTkInputDialog(
            text="Einträge älter als X Tage löschen:\n(Standard: 365)",
            title="Alte Einträge löschen"
        )
        
        days_str = dialog.get_input()
        
        if not days_str:
            return
        
        try:
            days = int(days_str)
        except ValueError:
            messagebox.showerror("Fehler", "Bitte eine gültige Zahl eingeben")
            return
        
        confirm = messagebox.askyesno(
            "Alte Einträge löschen",
            f"WARNUNG: Einträge älter als {days} Tage werden permanent gelöscht!\n\n"
            f"Ein Backup wird automatisch erstellt.\n\n"
            f"Fortfahren?"
        )
        
        if not confirm:
            return
        
        def cleanup_thread():
            try:
                success, message, count = self.indexer.cleanup_old_entries(days)
                
                if success:
                    messagebox.showinfo("Cleanup erfolgreich", f"{message}\n\n{count} Einträge gelöscht")
                else:
                    messagebox.showerror("Cleanup fehlgeschlagen", message)
            except Exception as e:
                messagebox.showerror("Fehler", f"Cleanup-Fehler: {e}")
        
        threading.Thread(target=cleanup_thread, daemon=True).start()
    
    def _show_overview_stats(self):
        """Zeigt Übersichts-Statistiken."""
        def stats_thread():
            try:
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", "Lade Statistiken...\n")
                
                stats = self.indexer.get_overview_stats()
                
                if "error" in stats:
                    self.stats_text.delete("1.0", "end")
                    self.stats_text.insert("1.0", f"Fehler: {stats['error']}")
                    return
                
                # Format output
                output = "=== ÜBERSICHT ===\n\n"
                output += f"Gesamt-Dokumente: {stats.get('total_documents', 0)}\n\n"
                
                output += "Status-Verteilung:\n"
                for status, count in stats.get("by_status", {}).items():
                    output += f"  {status}: {count}\n"
                
                output += "\nTop Dokument-Typen:\n"
                for item in stats.get("top_document_types", []):
                    output += f"  {item['type']}: {item['count']}\n"
                
                output += "\nNach Jahr:\n"
                for jahr, count in sorted(stats.get("by_year", {}).items(), reverse=True):
                    output += f"  {jahr}: {count}\n"
                
                confidence = stats.get("confidence", {})
                output += f"\nConfidence:\n"
                output += f"  Durchschnitt: {confidence.get('average', 0):.2f}\n"
                output += f"  Min: {confidence.get('min', 0):.2f}\n"
                output += f"  Max: {confidence.get('max', 0):.2f}\n"
                
                output += f"\nLegacy-Aufträge:\n"
                output += f"  Offen: {stats.get('open_legacy_count', 0)}\n"
                output += f"  Zugeordnet: {stats.get('resolved_legacy_count', 0)}\n"
                
                output += "\nNeueste Dokumente:\n"
                for doc in stats.get("recent_documents", []):
                    output += f"  {doc['filename']} - {doc.get('customer', 'N/A')}\n"
                
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", output)
            
            except Exception as e:
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", f"Fehler beim Laden: {e}")
        
        threading.Thread(target=stats_thread, daemon=True).start()
    
    def _show_customer_stats(self):
        """Zeigt Kunden-Statistiken."""
        def stats_thread():
            try:
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", "Lade Kunden-Statistiken...\n")
                
                customers = self.indexer.get_customer_stats()
                
                if not customers or (len(customers) == 1 and "error" in customers[0]):
                    self.stats_text.delete("1.0", "end")
                    self.stats_text.insert("1.0", "Keine Kunden-Daten verfügbar")
                    return
                
                output = "=== TOP 20 KUNDEN ===\n\n"
                
                for customer in customers:
                    output += f"{customer['kunden_nr']} - {customer['kunden_name']}\n"
                    output += f"  Dokumente: {customer['document_count']}\n"
                    output += f"  Ø Confidence: {customer['avg_confidence']:.2f}\n"
                    output += f"  Erstes Dokument: {customer.get('first_document', 'N/A')}\n"
                    output += f"  Letztes Dokument: {customer.get('last_document', 'N/A')}\n\n"
                
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", output)
            
            except Exception as e:
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", f"Fehler: {e}")
        
        threading.Thread(target=stats_thread, daemon=True).start()
    
    def _show_time_series(self):
        """Zeigt Zeitreihen-Statistiken."""
        def stats_thread():
            try:
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", "Lade Zeitreihen (letzte 30 Tage)...\n")
                
                data = self.indexer.get_time_series_stats(days=30)
                
                if "error" in data:
                    self.stats_text.delete("1.0", "end")
                    self.stats_text.insert("1.0", f"Fehler: {data['error']}")
                    return
                
                output = "=== ZEITREIHEN (30 Tage) ===\n\n"
                
                output += "Dokumente pro Tag:\n"
                for day in data.get("daily_documents", [])[:10]:  # Top 10
                    output += f"  {day['date']}: {day['document_count']} Dokumente (Ø Conf: {day['avg_confidence']:.2f})\n"
                
                output += "\nDokument-Typ Trends:\n"
                current_date = None
                for item in data.get("type_trends", [])[:20]:  # Top 20
                    if item['date'] != current_date:
                        current_date = item['date']
                        output += f"\n  {current_date}:\n"
                    output += f"    {item['document_type']}: {item['count']}\n"
                
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", output)
            
            except Exception as e:
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", f"Fehler: {e}")
        
        threading.Thread(target=stats_thread, daemon=True).start()
    
    def _show_quality_stats(self):
        """Zeigt Qualitäts-Statistiken."""
        def stats_thread():
            try:
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", "Lade Qualitäts-Statistiken...\n")
                
                stats = self.indexer.get_quality_stats()
                
                if "error" in stats:
                    self.stats_text.delete("1.0", "end")
                    self.stats_text.insert("1.0", f"Fehler: {stats['error']}")
                    return
                
                output = "=== QUALITÄTS-ANALYSE ===\n\n"
                
                output += "Confidence-Verteilung:\n"
                for level, count in stats.get("confidence_distribution", {}).items():
                    output += f"  {level}: {count}\n"
                
                output += "\nNiedrige Confidence (< 0.5):\n"
                for doc in stats.get("low_confidence_documents", []):
                    output += f"  {doc['filename']} - {doc.get('customer', 'N/A')} ({doc['confidence']:.2f})\n"
                
                output += "\nLegacy-Zuordnung:\n"
                for status, count in stats.get("legacy_resolution", {}).items():
                    output += f"  {status}: {count}\n"
                
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", output)
            
            except Exception as e:
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", f"Fehler: {e}")
        
        threading.Thread(target=stats_thread, daemon=True).start()
    
    def _export_csv(self):
        """Exportiert Dokumente als CSV."""
        # TODO: Filter-Dialog implementieren
        filename = filedialog.asksaveasfilename(
            title="CSV Export speichern",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        def export_thread():
            try:
                self.export_info_label.configure(text="Exportiere CSV...")
                success, filepath = self.indexer.export_to_csv(filename=filename)
                
                if success:
                    messagebox.showinfo("Export erfolgreich", f"CSV exportiert nach:\n{filepath}")
                    self.export_info_label.configure(text="Export abgeschlossen")
                else:
                    messagebox.showerror("Export fehlgeschlagen", filepath)
                    self.export_info_label.configure(text="Export fehlgeschlagen")
            except Exception as e:
                messagebox.showerror("Fehler", f"Export-Fehler: {e}")
                self.export_info_label.configure(text=f"Fehler: {e}")
        
        threading.Thread(target=export_thread, daemon=True).start()
    
    def _export_customer_report(self):
        """Exportiert Kunden-Report."""
        dialog = ctk.CTkInputDialog(
            text="Kundennummer eingeben:",
            title="Kunden-Report"
        )
        
        kunden_nr = dialog.get_input()
        
        if not kunden_nr:
            return
        
        def export_thread():
            try:
                self.export_info_label.configure(text="Erstelle Kunden-Report...")
                success, filepath = self.indexer.export_customer_report(kunden_nr)
                
                if success:
                    messagebox.showinfo("Report erstellt", f"Kunden-Report exportiert nach:\n{filepath}")
                    self.export_info_label.configure(text="Report erstellt")
                else:
                    messagebox.showerror("Report fehlgeschlagen", filepath)
                    self.export_info_label.configure(text="Report fehlgeschlagen")
            except Exception as e:
                messagebox.showerror("Fehler", f"Report-Fehler: {e}")
                self.export_info_label.configure(text=f"Fehler: {e}")
        
        threading.Thread(target=export_thread, daemon=True).start()
    
    @staticmethod
    def _format_bytes(bytes_size: int) -> str:
        """Formatiert Bytes human-readable."""
        size_float = float(bytes_size)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_float < 1024.0:
                return f"{size_float:.2f} {unit}"
            size_float /= 1024.0
        return f"{size_float:.2f} TB"

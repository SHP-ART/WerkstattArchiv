"""
GUI für WerkstattArchiv.
Hauptfenster mit customtkinter für die Dokumentenverwaltung.
"""

import os
import json
from typing import Dict, Any, List, Optional
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading

from services.customers import CustomerManager
from services.analyzer import analyze_document
from services.router import process_document
from services.logger import log_success, log_unclear, log_error
from services.indexer import DocumentIndex
from services.vorlagen import VorlagenManager


class MainWindow(ctk.CTk):
    """Hauptfenster der Anwendung mit customtkinter."""
    
    def __init__(self, config: Dict[str, Any], customer_manager: CustomerManager):
        """
        Initialisiert das Hauptfenster.
        
        Args:
            config: Konfigurationsdictionary
            customer_manager: CustomerManager-Instanz
        """
        super().__init__()
        
        self.config = config
        self.customer_manager = customer_manager
        self.unclear_documents: List[Dict[str, Any]] = []
        self.document_index = DocumentIndex()
        self.vorlagen_manager = VorlagenManager()
        
        # Fenster-Konfiguration
        self.title("WerkstattArchiv")
        self.geometry("1200x700")
        
        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Tabview erstellen
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tabs hinzufügen
        self.tabview.add("Einstellungen")
        self.tabview.add("Verarbeitung")
        self.tabview.add("Suche")
        self.tabview.add("Unklare Dokumente")
        self.tabview.add("Unklare Legacy-Aufträge")
        
        # Tab-Inhalte erstellen
        self.create_settings_tab()
        self.create_processing_tab()
        self.create_search_tab()
        self.create_unclear_tab()
        self.create_unclear_legacy_tab()
    
    def create_settings_tab(self):
        """Erstellt den Einstellungen-Tab."""
        tab = self.tabview.tab("Einstellungen")
        
        # Frame für Einstellungen
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Überschrift
        title = ctk.CTkLabel(settings_frame, text="Pfad-Einstellungen", 
                            font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)
        
        # Eingabefelder für Pfade
        self.entries = {}
        
        labels = [
            ("root_dir", "Basis-Verzeichnis:"),
            ("input_dir", "Eingangsordner:"),
            ("unclear_dir", "Unklar-Ordner:"),
            ("customers_file", "Kundendatei (CSV):"),
            ("tesseract_path", "Tesseract-Pfad (optional):"),
        ]
        
        for key, label_text in labels:
            row_frame = ctk.CTkFrame(settings_frame)
            row_frame.pack(fill="x", padx=20, pady=5)
            
            label = ctk.CTkLabel(row_frame, text=label_text, width=200, anchor="w")
            label.pack(side="left", padx=5)
            
            entry = ctk.CTkEntry(row_frame, width=600)
            entry.pack(side="left", padx=5, fill="x", expand=True)
            entry.insert(0, str(self.config.get(key, "")))
            self.entries[key] = entry
            
            # Browse-Button
            browse_btn = ctk.CTkButton(row_frame, text="...", width=50,
                                       command=lambda k=key: self.browse_path(k))
            browse_btn.pack(side="left", padx=5)
        
        # Speichern-Button
        save_btn = ctk.CTkButton(settings_frame, text="Einstellungen speichern",
                                command=self.save_settings)
        save_btn.pack(pady=20)
        
        # Kundendatenbank neu laden Button
        reload_btn = ctk.CTkButton(settings_frame, text="Kundendatenbank neu laden",
                                  command=self.reload_customers)
        reload_btn.pack(pady=5)
        
        # Status-Label
        self.settings_status = ctk.CTkLabel(settings_frame, text="")
        self.settings_status.pack(pady=5)
    
    def create_processing_tab(self):
        """Erstellt den Verarbeitungs-Tab."""
        tab = self.tabview.tab("Verarbeitung")
        
        # Control-Frame oben
        control_frame = ctk.CTkFrame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Vorlagen-Auswahl
        vorlage_label = ctk.CTkLabel(control_frame, text="📋 Auftragsvorlage:", 
                                     font=ctk.CTkFont(size=12, weight="bold"))
        vorlage_label.pack(side="left", padx=10)
        
        vorlagen = self.vorlagen_manager.get_vorlagen_liste()
        self.vorlage_selector = ctk.CTkSegmentedButton(
            control_frame,
            values=vorlagen,
            command=self.on_vorlage_changed
        )
        self.vorlage_selector.set(self.vorlagen_manager.get_active_vorlage().name)
        self.vorlage_selector.pack(side="left", padx=10)
        
        # Vorlage-Info
        self.vorlage_info = ctk.CTkLabel(control_frame, text="", 
                                         font=ctk.CTkFont(size=10))
        self.vorlage_info.pack(side="left", padx=10)
        self._update_vorlage_info()
        
        scan_btn = ctk.CTkButton(control_frame, text="Eingangsordner scannen",
                                command=self.scan_input_folder)
        scan_btn.pack(side="left", padx=10, pady=10)
        
        self.process_status = ctk.CTkLabel(control_frame, text="Bereit")
        self.process_status.pack(side="left", padx=10)
        
        # Tabelle für Ergebnisse
        table_frame = ctk.CTkFrame(tab)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollable Frame für Tabelle
        self.process_scroll = ctk.CTkScrollableFrame(table_frame)
        self.process_scroll.pack(fill="both", expand=True)
        
        # Header
        headers = ["Datei", "Kunde", "Auftrag", "Typ", "Jahr", "Confidence", "Vorlage", "Status"]
        header_frame = ctk.CTkFrame(self.process_scroll)
        header_frame.pack(fill="x", pady=5)
        
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(header_frame, text=header, 
                               font=ctk.CTkFont(weight="bold"), width=150)
            label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        # Container für Ergebnis-Zeilen
        self.results_container = ctk.CTkFrame(self.process_scroll)
        self.results_container.pack(fill="both", expand=True)
    
    def create_search_tab(self):
        """Erstellt den Such-Tab."""
        tab = self.tabview.tab("Suche")
        
        # Suchformular
        search_frame = ctk.CTkFrame(tab)
        search_frame.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(search_frame, text="Dokumentensuche", 
                            font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=10)
        
        # Suchfelder in Grid
        fields_frame = ctk.CTkFrame(search_frame)
        fields_frame.pack(fill="x", padx=20, pady=10)
        
        # Kundennummer
        ctk.CTkLabel(fields_frame, text="Kundennr:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.search_kunden_nr = ctk.CTkEntry(fields_frame, width=150)
        self.search_kunden_nr.grid(row=0, column=1, padx=5, pady=5)
        
        # Kundenname
        ctk.CTkLabel(fields_frame, text="Kundenname:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.search_kunden_name = ctk.CTkEntry(fields_frame, width=200)
        self.search_kunden_name.grid(row=0, column=3, padx=5, pady=5)
        
        # Auftragsnummer
        ctk.CTkLabel(fields_frame, text="Auftragsnr:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.search_auftrag_nr = ctk.CTkEntry(fields_frame, width=150)
        self.search_auftrag_nr.grid(row=1, column=1, padx=5, pady=5)
        
        # Dateiname
        ctk.CTkLabel(fields_frame, text="Dateiname:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.search_dateiname = ctk.CTkEntry(fields_frame, width=200)
        self.search_dateiname.grid(row=1, column=3, padx=5, pady=5)
        
        # Dokumenttyp
        ctk.CTkLabel(fields_frame, text="Typ:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.search_dokument_typ = ctk.CTkComboBox(fields_frame, width=150, 
                                                    values=["Alle"] + self.document_index.get_all_document_types())
        self.search_dokument_typ.set("Alle")
        self.search_dokument_typ.grid(row=2, column=1, padx=5, pady=5)
        
        # Jahr
        ctk.CTkLabel(fields_frame, text="Jahr:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        years = ["Alle"] + [str(y) for y in self.document_index.get_all_years()]
        self.search_jahr = ctk.CTkComboBox(fields_frame, width=150, values=years)
        self.search_jahr.set("Alle")
        self.search_jahr.grid(row=2, column=3, padx=5, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(search_frame)
        button_frame.pack(pady=10)
        
        search_btn = ctk.CTkButton(button_frame, text="🔍 Suchen", 
                                   command=self.perform_search, width=150)
        search_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(button_frame, text="Zurücksetzen", 
                                  command=self.clear_search, width=150)
        clear_btn.pack(side="left", padx=5)
        
        stats_btn = ctk.CTkButton(button_frame, text="📊 Statistiken", 
                                  command=self.show_statistics, width=150)
        stats_btn.pack(side="left", padx=5)
        
        # Ergebnisbereich
        results_frame = ctk.CTkFrame(tab)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.search_results_scroll = ctk.CTkScrollableFrame(results_frame)
        self.search_results_scroll.pack(fill="both", expand=True)
        
        # Header für Ergebnistabelle
        header_frame = ctk.CTkFrame(self.search_results_scroll)
        header_frame.pack(fill="x", pady=5)
        
        headers = ["Datum", "Datei", "Kunde", "Auftrag", "Typ", "Jahr", "Pfad", "Aktion"]
        widths = [120, 150, 180, 100, 100, 60, 250, 100]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            label = ctk.CTkLabel(header_frame, text=header, 
                               font=ctk.CTkFont(weight="bold"), width=width)
            label.grid(row=0, column=i, padx=2, pady=5, sticky="w")
        
        # Container für Suchergebnisse
        self.search_results_container = ctk.CTkFrame(self.search_results_scroll)
        self.search_results_container.pack(fill="both", expand=True)
        
        # Status-Label
        self.search_status = ctk.CTkLabel(search_frame, text="")
        self.search_status.pack(pady=5)
    
    def create_unclear_tab(self):
        """Erstellt den Unklare-Dokumente-Tab."""
        tab = self.tabview.tab("Unklare Dokumente")
        
        # Control-Frame
        control_frame = ctk.CTkFrame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        info_label = ctk.CTkLabel(control_frame, 
                                 text="Dokumente mit unklarer Zuordnung - Manuell korrigieren")
        info_label.pack(side="left", padx=10)
        
        # Liste für unklare Dokumente
        list_frame = ctk.CTkFrame(tab)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.unclear_scroll = ctk.CTkScrollableFrame(list_frame)
        self.unclear_scroll.pack(fill="both", expand=True)
        
        # Container für unklare Dokumente
        self.unclear_container = ctk.CTkFrame(self.unclear_scroll)
        self.unclear_container.pack(fill="both", expand=True)
    
    def create_unclear_legacy_tab(self):
        """Erstellt den Tab für unklare Legacy-Aufträge."""
        tab = self.tabview.tab("Unklare Legacy-Aufträge")
        
        # Control-Frame
        control_frame = ctk.CTkFrame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(control_frame, 
                                   text="🔍 Unklare Legacy-Aufträge (ohne Kundennummer)",
                                   font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(side="left", padx=10)
        
        refresh_btn = ctk.CTkButton(control_frame, text="🔄 Aktualisieren",
                                   command=self.load_unclear_legacy_entries,
                                   width=150)
        refresh_btn.pack(side="left", padx=10)
        
        self.legacy_status = ctk.CTkLabel(control_frame, text="")
        self.legacy_status.pack(side="left", padx=10)
        
        # Info-Frame
        info_frame = ctk.CTkFrame(tab)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        info_text = ("ℹ️ Diese Aufträge haben keine Kundennummer und konnten nicht automatisch zugeordnet werden.\n"
                    "   Bitte wählen Sie manuell einen Kunden aus und klicken Sie auf 'Zuordnen'.")
        info_label = ctk.CTkLabel(info_frame, text=info_text, 
                                 font=ctk.CTkFont(size=11), justify="left")
        info_label.pack(padx=10, pady=10)
        
        # Liste für unklare Legacy-Aufträge
        list_frame = ctk.CTkFrame(tab)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.legacy_scroll = ctk.CTkScrollableFrame(list_frame)
        self.legacy_scroll.pack(fill="both", expand=True)
        
        # Header
        header_frame = ctk.CTkFrame(self.legacy_scroll)
        header_frame.pack(fill="x", pady=5)
        
        headers = ["Datei", "Auftrag", "Datum", "Name", "FIN", "Kennz.", "Jahr", "Typ", "Grund", "Kunde", "Aktion"]
        widths = [120, 80, 90, 120, 140, 90, 50, 80, 100, 200, 150]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            label = ctk.CTkLabel(header_frame, text=header, 
                               font=ctk.CTkFont(weight="bold"), width=width)
            label.grid(row=0, column=i, padx=2, pady=5, sticky="w")
        
        # Container für Legacy-Einträge
        self.legacy_container = ctk.CTkFrame(self.legacy_scroll)
        self.legacy_container.pack(fill="both", expand=True)
        
        # Initial laden
        self.load_unclear_legacy_entries()
    
    def browse_path(self, key: str):
        """Öffnet Dialog zur Pfadauswahl."""
        if key == "customers_file":
            path = filedialog.askopenfilename(
                title="Kundendatei auswählen",
                filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")]
            )
        elif key == "tesseract_path":
            path = filedialog.askopenfilename(
                title="Tesseract-Executable auswählen",
                filetypes=[("Executable", "*.exe"), ("Alle Dateien", "*.*")]
            )
        else:
            path = filedialog.askdirectory(title=f"{key} auswählen")
        
        if path:
            self.entries[key].delete(0, "end")
            self.entries[key].insert(0, path)
    
    def save_settings(self):
        """Speichert die Einstellungen in config.json."""
        for key, entry in self.entries.items():
            value = entry.get().strip()
            if value == "" or value.lower() == "none":
                self.config[key] = None
            else:
                self.config[key] = value
        
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self.settings_status.configure(text="✓ Einstellungen gespeichert", 
                                          text_color="green")
            
        except Exception as e:
            self.settings_status.configure(text=f"✗ Fehler: {e}", 
                                          text_color="red")
    
    def reload_customers(self):
        """Lädt die Kundendatenbank neu."""
        self.customer_manager.load_customers()
        self.settings_status.configure(
            text=f"✓ {len(self.customer_manager.customers)} Kunden geladen", 
            text_color="green"
        )
    
    def on_vorlage_changed(self, selected_vorlage: str):
        """Callback wenn Vorlage geändert wird."""
        self.vorlagen_manager.set_active_vorlage(selected_vorlage)
        self._update_vorlage_info()
        self.process_status.configure(
            text=f"Vorlage gewechselt: {selected_vorlage}",
            text_color="blue"
        )
    
    def _update_vorlage_info(self):
        """Aktualisiert die Vorlage-Info-Anzeige."""
        vorlage = self.vorlagen_manager.get_active_vorlage()
        self.vorlage_info.configure(text=f"ℹ️ {vorlage.beschreibung}")
    
    def scan_input_folder(self):
        """Scannt den Eingangsordner und verarbeitet alle Dokumente."""
        input_dir = self.config.get("input_dir")
        
        if not input_dir or not os.path.exists(input_dir):
            messagebox.showerror("Fehler", 
                               "Eingangsordner nicht gefunden. Bitte Einstellungen prüfen.")
            return
        
        # Status aktualisieren
        self.process_status.configure(text="Verarbeitung läuft...")
        
        # In separatem Thread verarbeiten
        thread = threading.Thread(target=self._process_documents)
        thread.daemon = True
        thread.start()
    
    def _process_documents(self):
        """Verarbeitet alle Dokumente im Eingangsordner (läuft in Thread)."""
        input_dir = self.config.get("input_dir")
        root_dir = self.config.get("root_dir")
        unclear_dir = self.config.get("unclear_dir")
        tesseract_path = self.config.get("tesseract_path")
        
        # Validierung
        if not input_dir or not isinstance(input_dir, str):
            self.process_status.configure(text="Fehler: Eingangsordner nicht konfiguriert")
            return
        
        if not root_dir or not isinstance(root_dir, str):
            self.process_status.configure(text="Fehler: Basis-Verzeichnis nicht konfiguriert")
            return
            
        if not unclear_dir or not isinstance(unclear_dir, str):
            self.process_status.configure(text="Fehler: Unklar-Ordner nicht konfiguriert")
            return
        
        # Alte Ergebnisse löschen
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        self.unclear_documents.clear()
        
        # Dateien im Eingangsordner finden
        files = []
        for file in os.listdir(input_dir):
            file_path = os.path.join(input_dir, file)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file)[1].lower()
                if ext in [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
                    files.append(file_path)
        
        if not files:
            self.process_status.configure(text="Keine Dateien gefunden")
            return
        
        # Dateien verarbeiten
        for i, file_path in enumerate(files):
            filename = os.path.basename(file_path)
            
            try:
                # Legacy-Resolver initialisieren
                from services.legacy_resolver import LegacyResolver
                from services.vehicles import VehicleManager
                vehicle_manager = VehicleManager()
                legacy_resolver = LegacyResolver(self.customer_manager, vehicle_manager)
                
                # Dokument analysieren mit gewählter Vorlage und Legacy-Support
                analysis = analyze_document(
                    file_path, 
                    tesseract_path,
                    vorlage_name=self.vorlagen_manager.get_active_vorlage().name,
                    vorlagen_manager=self.vorlagen_manager,
                    legacy_resolver=legacy_resolver
                )
                
                # Dokument verarbeiten und verschieben
                target_path, is_clear, reason = process_document(
                    file_path, analysis, root_dir, unclear_dir, self.customer_manager
                )
                
                # Logging
                if is_clear:
                    log_success(file_path, target_path, analysis, analysis["confidence"])
                    status = "✓ Verschoben"
                    color = "green"
                    doc_status = "success"
                else:
                    log_unclear(file_path, target_path, analysis, analysis["confidence"], reason)
                    status = "⚠ Unklar"
                    color = "orange"
                    doc_status = "unclear"
                    
                    # Zu unklaren Dokumenten hinzufügen
                    self.unclear_documents.append({
                        "original_path": file_path,
                        "target_path": target_path,
                        "analysis": analysis,
                        "reason": reason,
                    })
                
                # Zum Index hinzufügen
                self.document_index.add_document(file_path, target_path, analysis, doc_status)
                
                # Bei unklaren Legacy-Aufträgen: auch zur unclear_legacy Tabelle hinzufügen
                if analysis.get("is_legacy") and analysis.get("legacy_match_reason") == "unclear":
                    self.document_index.add_unclear_legacy(target_path, analysis)
                
                # Ergebnis in Tabelle anzeigen
                self._add_result_row(filename, analysis, status, color)
                
            except Exception as e:
                log_error(file_path, str(e))
                self.document_index.add_document(file_path, file_path, {}, "error")
                self._add_result_row(filename, {}, f"✗ Fehler: {e}", "red")
        
        # Status aktualisieren
        self.process_status.configure(
            text=f"Fertig: {len(files)} Dateien verarbeitet"
        )
        
        # Unklare Dokumente anzeigen
        self._update_unclear_tab()
    
    def _add_result_row(self, filename: str, analysis: Dict[str, Any], 
                       status: str, color: str):
        """Fügt eine Ergebnis-Zeile zur Tabelle hinzu."""
        row_frame = ctk.CTkFrame(self.results_container)
        row_frame.pack(fill="x", pady=2)
        
        values = [
            filename,
            f"{analysis.get('kunden_nr', 'N/A')} - {analysis.get('kunden_name', 'N/A')[:20]}",
            str(analysis.get('auftrag_nr', 'N/A')),
            analysis.get('dokument_typ', 'N/A'),
            str(analysis.get('jahr', 'N/A')),
            f"{analysis.get('confidence', 0.0):.2f}",
            analysis.get('vorlage_verwendet', 'N/A')[:12],
            status,
        ]
        
        for i, value in enumerate(values):
            label = ctk.CTkLabel(row_frame, text=value, width=150, anchor="w")
            if i == len(values) - 1:  # Status-Spalte
                label.configure(text_color=color)
            label.grid(row=0, column=i, padx=5, pady=2, sticky="w")
    
    def _update_unclear_tab(self):
        """Aktualisiert den Tab mit unklaren Dokumenten."""
        # Alte Widgets entfernen
        for widget in self.unclear_container.winfo_children():
            widget.destroy()
        
        if not self.unclear_documents:
            no_docs = ctk.CTkLabel(self.unclear_container, 
                                  text="Keine unklaren Dokumente", 
                                  font=ctk.CTkFont(size=16))
            no_docs.pack(pady=20)
            return
        
        # Unklare Dokumente anzeigen
        for doc in self.unclear_documents:
            self._add_unclear_document_widget(doc)
    
    def _add_unclear_document_widget(self, doc: Dict[str, Any]):
        """Fügt ein Widget für ein unklares Dokument hinzu."""
        analysis = doc["analysis"]
        
        doc_frame = ctk.CTkFrame(self.unclear_container)
        doc_frame.pack(fill="x", padx=10, pady=10)
        
        # Info
        info_text = f"Datei: {os.path.basename(doc['target_path'])} | Grund: {doc['reason']}"
        info_label = ctk.CTkLabel(doc_frame, text=info_text, anchor="w")
        info_label.pack(fill="x", padx=10, pady=5)
        
        # Eingabefelder für manuelle Korrektur
        input_frame = ctk.CTkFrame(doc_frame)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # Kundennummer
        ctk.CTkLabel(input_frame, text="Kundennr:").grid(row=0, column=0, padx=5, pady=5)
        kunden_entry = ctk.CTkEntry(input_frame, width=150)
        kunden_entry.insert(0, analysis.get("kunden_nr", ""))
        kunden_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Auftragsnummer
        ctk.CTkLabel(input_frame, text="Auftragsnr:").grid(row=0, column=2, padx=5, pady=5)
        auftrag_entry = ctk.CTkEntry(input_frame, width=150)
        auftrag_entry.insert(0, analysis.get("auftrag_nr", ""))
        auftrag_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Dokumenttyp
        ctk.CTkLabel(input_frame, text="Typ:").grid(row=0, column=4, padx=5, pady=5)
        typ_entry = ctk.CTkEntry(input_frame, width=150)
        typ_entry.insert(0, analysis.get("dokument_typ", ""))
        typ_entry.grid(row=0, column=5, padx=5, pady=5)
        
        # Neu einsortieren Button
        resort_btn = ctk.CTkButton(
            doc_frame, text="Neu einsortieren",
            command=lambda: self._resort_document(doc, kunden_entry.get(), 
                                                 auftrag_entry.get(), typ_entry.get())
        )
        resort_btn.pack(pady=5)
    
    def _resort_document(self, doc: Dict[str, Any], kunden_nr: str, 
                        auftrag_nr: str, dokument_typ: str):
        """Sortiert ein unklares Dokument mit manuellen Daten neu ein."""
        # Aktualisiere Analysedaten
        analysis = doc["analysis"].copy()
        analysis["kunden_nr"] = kunden_nr if kunden_nr else None
        analysis["auftrag_nr"] = auftrag_nr if auftrag_nr else None
        analysis["dokument_typ"] = dokument_typ if dokument_typ else "Dokument"
        
        try:
            # Neu verarbeiten
            target_path, is_clear, reason = process_document(
                doc["target_path"], analysis,
                self.config["root_dir"], self.config["unclear_dir"],
                self.customer_manager
            )
            
            if is_clear:
                log_success(doc["target_path"], target_path, analysis, 1.0)
                messagebox.showinfo("Erfolg", 
                                  f"Dokument erfolgreich verschoben nach:\n{target_path}")
                
                # Aus unklaren Dokumenten entfernen
                self.unclear_documents.remove(doc)
                self._update_unclear_tab()
            else:
                messagebox.showwarning("Unklar", 
                                     f"Dokument konnte nicht zugeordnet werden:\n{reason}")
        
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Neu-Einsortieren:\n{e}")
    
    def perform_search(self):
        """Führt die Suche anhand der eingegebenen Kriterien aus."""
        # Suchparameter sammeln
        kunden_nr = self.search_kunden_nr.get().strip() or None
        kunden_name = self.search_kunden_name.get().strip() or None
        auftrag_nr = self.search_auftrag_nr.get().strip() or None
        dateiname = self.search_dateiname.get().strip() or None
        
        dokument_typ = self.search_dokument_typ.get()
        if dokument_typ == "Alle":
            dokument_typ = None
        
        jahr_str = self.search_jahr.get()
        jahr = int(jahr_str) if jahr_str != "Alle" else None
        
        # Suche durchführen
        results = self.document_index.search(
            kunden_nr=kunden_nr,
            auftrag_nr=auftrag_nr,
            dokument_typ=dokument_typ,
            jahr=jahr,
            kunden_name=kunden_name,
            dateiname=dateiname
        )
        
        # Ergebnisse anzeigen
        self._display_search_results(results)
        
        # Status aktualisieren
        self.search_status.configure(
            text=f"{len(results)} Dokument(e) gefunden",
            text_color="green" if results else "orange"
        )
    
    def clear_search(self):
        """Setzt alle Suchfelder zurück."""
        self.search_kunden_nr.delete(0, "end")
        self.search_kunden_name.delete(0, "end")
        self.search_auftrag_nr.delete(0, "end")
        self.search_dateiname.delete(0, "end")
        self.search_dokument_typ.set("Alle")
        self.search_jahr.set("Alle")
        self.search_status.configure(text="")
        
        # Ergebnisse löschen
        for widget in self.search_results_container.winfo_children():
            widget.destroy()
    
    def show_statistics(self):
        """Zeigt Statistiken über die indexierten Dokumente."""
        stats = self.document_index.get_statistics()
        
        msg = f"📊 Dokumentenstatistiken\n\n"
        msg += f"Gesamtanzahl: {stats['total']} Dokumente\n\n"
        
        msg += "Nach Status:\n"
        for status, count in stats['by_status'].items():
            msg += f"  • {status}: {count}\n"
        
        msg += "\nTop Dokumenttypen:\n"
        for doc_type, count in list(stats['by_type'].items())[:5]:
            msg += f"  • {doc_type}: {count}\n"
        
        msg += "\nNach Jahr:\n"
        for jahr, count in list(stats['by_year'].items())[:5]:
            msg += f"  • {jahr}: {count}\n"
        
        messagebox.showinfo("Statistiken", msg)
    
    def _display_search_results(self, results: List[Dict[str, Any]]):
        """Zeigt die Suchergebnisse in der Tabelle an."""
        # Alte Ergebnisse löschen
        for widget in self.search_results_container.winfo_children():
            widget.destroy()
        
        if not results:
            no_results = ctk.CTkLabel(self.search_results_container, 
                                     text="Keine Dokumente gefunden",
                                     font=ctk.CTkFont(size=14))
            no_results.pack(pady=20)
            return
        
        # Ergebnisse anzeigen
        for result in results:
            self._add_search_result_row(result)
    
    def _add_search_result_row(self, result: Dict[str, Any]):
        """Fügt eine Ergebniszeile zur Suchtabelle hinzu."""
        row_frame = ctk.CTkFrame(self.search_results_container)
        row_frame.pack(fill="x", pady=2)
        
        # Datum formatieren
        datum = result.get("verarbeitet_am", "")[:16] if result.get("verarbeitet_am") else "N/A"
        
        values = [
            datum,
            result.get("dateiname", "N/A")[:20] + "..." if len(result.get("dateiname", "")) > 20 else result.get("dateiname", "N/A"),
            f"{result.get('kunden_nr', 'N/A')} - {result.get('kunden_name', 'N/A')[:15]}" if result.get('kunden_name') else result.get('kunden_nr', 'N/A'),
            result.get("auftrag_nr", "N/A") or "N/A",
            result.get("dokument_typ", "N/A") or "N/A",
            str(result.get("jahr", "N/A")) if result.get("jahr") else "N/A",
            result.get("ziel_pfad", "N/A")[:30] + "..." if len(result.get("ziel_pfad", "")) > 30 else result.get("ziel_pfad", "N/A"),
        ]
        
        widths = [120, 150, 180, 100, 100, 60, 250]
        
        for i, (value, width) in enumerate(zip(values, widths)):
            label = ctk.CTkLabel(row_frame, text=value, width=width, anchor="w")
            label.grid(row=0, column=i, padx=2, pady=2, sticky="w")
        
        # Öffnen-Button
        open_btn = ctk.CTkButton(row_frame, text="📂 Öffnen", width=100,
                                command=lambda path=result.get("ziel_pfad"): self._open_file_location(path))
        open_btn.grid(row=0, column=len(values), padx=2, pady=2)
    
    def _open_file_location(self, file_path: Optional[str]):
        """Öffnet den Speicherort einer Datei im Finder/Explorer."""
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Fehler", "Datei nicht gefunden!")
            return
        
        try:
            import subprocess
            import platform
            
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", file_path])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", "/select,", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", os.path.dirname(file_path)])
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Datei nicht öffnen:\n{e}")
    
    def load_unclear_legacy_entries(self):
        """Lädt unklare Legacy-Einträge aus der Datenbank."""
        # Alte Einträge löschen
        for widget in self.legacy_container.winfo_children():
            widget.destroy()
        
        # Einträge aus DB laden
        entries = self.document_index.get_unclear_legacy_entries(status="offen")
        
        if not entries:
            no_entries = ctk.CTkLabel(self.legacy_container, 
                                     text="✓ Keine unklaren Legacy-Aufträge vorhanden",
                                     font=ctk.CTkFont(size=14),
                                     text_color="green")
            no_entries.pack(pady=20)
            self.legacy_status.configure(text="0 offene Einträge", text_color="green")
            return
        
        # Einträge anzeigen
        for entry in entries:
            self._add_legacy_entry_row(entry)
        
        self.legacy_status.configure(text=f"{len(entries)} offene Einträge", text_color="orange")
    
    def _add_legacy_entry_row(self, entry: Dict[str, Any]):
        """Fügt eine Zeile für einen Legacy-Eintrag hinzu."""
        row_frame = ctk.CTkFrame(self.legacy_container)
        row_frame.pack(fill="x", pady=2)
        
        # Daten vorbereiten
        dateiname = entry.get("dateiname", "N/A")
        if len(dateiname) > 15:
            dateiname = dateiname[:12] + "..."
        
        kunden_name = entry.get("kunden_name", "N/A")
        if len(kunden_name) > 15:
            kunden_name = kunden_name[:12] + "..."
        
        fin = entry.get("fin", "N/A")
        if fin and len(fin) > 17:
            fin = fin[:14] + "..."
        
        kennzeichen = entry.get("kennzeichen", "N/A")
        if kennzeichen and len(kennzeichen) > 12:
            kennzeichen = kennzeichen[:9] + "..."
        
        values = [
            dateiname,
            entry.get("auftrag_nr", "N/A") or "N/A",
            entry.get("auftragsdatum", "N/A") or "N/A",
            kunden_name,
            fin or "N/A",
            kennzeichen or "N/A",
            str(entry.get("jahr", "N/A")) if entry.get("jahr") else "N/A",
            entry.get("dokument_typ", "N/A") or "N/A",
            entry.get("match_reason", "unclear"),
        ]
        
        widths = [120, 80, 90, 120, 140, 90, 50, 80, 100]
        
        for i, (value, width) in enumerate(zip(values, widths)):
            label = ctk.CTkLabel(row_frame, text=value, width=width, anchor="w")
            label.grid(row=0, column=i, padx=2, pady=2, sticky="w")
        
        # Kunden-Dropdown
        kunden_liste = self._get_customer_dropdown_list()
        kunden_dropdown = ctk.CTkComboBox(row_frame, width=200, values=kunden_liste)
        kunden_dropdown.set("Kunde auswählen...")
        kunden_dropdown.grid(row=0, column=len(values), padx=2, pady=2)
        
        # Zuordnen-Button
        assign_btn = ctk.CTkButton(
            row_frame, 
            text="✓ Zuordnen", 
            width=150,
            command=lambda: self._assign_legacy_entry(entry["id"], kunden_dropdown, row_frame)
        )
        assign_btn.grid(row=0, column=len(values)+1, padx=2, pady=2)
    
    def _get_customer_dropdown_list(self) -> List[str]:
        """Erstellt eine Liste von Kunden für das Dropdown."""
        customers = []
        for nr, kunde in self.customer_manager.customers.items():
            # Format: "12345 - Mustermann, Max"
            name = kunde.name if hasattr(kunde, 'name') else "Unbekannt"
            customers.append(f"{nr} - {name}")
        
        return sorted(customers)
    
    def _assign_legacy_entry(self, entry_id: int, dropdown: ctk.CTkComboBox, row_frame: ctk.CTkFrame):
        """Ordnet einen Legacy-Eintrag einem Kunden zu."""
        selected = dropdown.get()
        
        if not selected or selected == "Kunde auswählen...":
            messagebox.showwarning("Warnung", "Bitte wählen Sie einen Kunden aus.")
            return
        
        # Kundennummer extrahieren (Format: "12345 - Name")
        try:
            kunden_nr = selected.split(" - ")[0].strip()
        except:
            messagebox.showerror("Fehler", "Ungültiges Kundenformat.")
            return
        
        # Eintrag aus DB holen für Dateipfad
        entries = self.document_index.get_unclear_legacy_entries(status="offen")
        entry = next((e for e in entries if e["id"] == entry_id), None)
        
        if not entry:
            messagebox.showerror("Fehler", "Eintrag nicht gefunden.")
            return
        
        # Bestätigung
        kunde = self.customer_manager.customers.get(kunden_nr)
        kunde_name = kunde.name if kunde else "Unbekannt"
        
        if not messagebox.askyesno(
            "Zuordnung bestätigen",
            f"Auftrag '{entry.get('auftrag_nr', 'N/A')}' dem Kunden zuordnen?\n\n"
            f"Kunde: {kunden_nr} - {kunde_name}\n"
            f"FIN: {entry.get('fin', 'N/A')}\n"
            f"Kennzeichen: {entry.get('kennzeichen', 'N/A')}"
        ):
            return
        
        try:
            # In DB als zugeordnet markieren
            success = self.document_index.assign_unclear_legacy(entry_id, kunden_nr)
            
            if not success:
                messagebox.showerror("Fehler", "Zuordnung in Datenbank fehlgeschlagen.")
                return
            
            # FIN in vehicles.csv speichern (falls vorhanden)
            from services.vehicles import VehicleManager
            if entry.get("fin"):
                vehicle_manager = VehicleManager()
                vehicle_manager.add_or_update_vehicle(
                    fin=entry["fin"],
                    kunden_nr=kunden_nr,
                    kennzeichen=entry.get("kennzeichen")
                )
            
            # Datei verschieben von Altbestand/Unklar zu Kunde/[Nr]-[Name]/[Jahr]/
            datei_pfad = entry.get("datei_pfad")
            if datei_pfad and os.path.exists(datei_pfad):
                # Ziel-Pfad erstellen
                jahr = entry.get("jahr", "Unbekannt")
                kunde_ordner = f"{kunden_nr}-{kunde_name}".replace(" ", "_")
                
                root_dir = self.config.get("root_dir", "")
                ziel_ordner = os.path.join(root_dir, "Kunde", kunde_ordner, str(jahr))
                os.makedirs(ziel_ordner, exist_ok=True)
                
                # Dateinamen mit _Altauftrag markieren
                dateiname = os.path.basename(datei_pfad)
                if "_Altauftrag_Unklar" in dateiname:
                    dateiname = dateiname.replace("_Altauftrag_Unklar", "_Altauftrag")
                
                ziel_pfad = os.path.join(ziel_ordner, dateiname)
                
                # Verschieben
                import shutil
                shutil.move(datei_pfad, ziel_pfad)
                
                # Zum normalen Dokumente-Index hinzufügen
                metadata = {
                    "kunden_nr": kunden_nr,
                    "kunden_name": kunde_name,
                    "auftrag_nr": entry.get("auftrag_nr"),
                    "dokument_typ": entry.get("dokument_typ"),
                    "jahr": entry.get("jahr"),
                    "fin": entry.get("fin"),
                    "kennzeichen": entry.get("kennzeichen"),
                    "hinweis": f"Legacy-Auftrag manuell zugeordnet: {entry.get('match_reason')}",
                    "confidence": 1.0
                }
                self.document_index.add_document(datei_pfad, ziel_pfad, metadata, "success")
                
                # Aus unclear_legacy löschen
                self.document_index.delete_unclear_legacy(entry_id)
            
            # Zeile entfernen
            row_frame.destroy()
            
            # Status aktualisieren
            messagebox.showinfo("Erfolg", f"Auftrag erfolgreich Kunde {kunden_nr} zugeordnet!")
            self.load_unclear_legacy_entries()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei der Zuordnung:\n{e}")


def create_and_run_gui(config: Dict[str, Any], customer_manager: CustomerManager):
    """
    Erstellt und startet die GUI.
    
    Args:
        config: Konfigurationsdictionary
        customer_manager: CustomerManager-Instanz
    """
    app = MainWindow(config, customer_manager)
    app.mainloop()

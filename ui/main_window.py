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
from services.pattern_manager import PatternManager

try:
    from services.watchdog_service import WatchdogService
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️  watchdog nicht installiert. Auto-Watch nicht verfügbar.")


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
        self.pattern_manager = PatternManager()
        self.watchdog_observer = None
        
        # Tab-Erstellungs-Flags (Lazy Loading)
        self.tabs_created = {
            "Einstellungen": False,
            "Verarbeitung": False,
            "Suche": False,
            "Unklare Dokumente": False,
            "Unklare Legacy-Aufträge": False,
            "Regex-Patterns": False
        }
        
        # Daten-Lade-Flags (für Refresh)
        self.tabs_data_loaded = {
            "Suche": False,
            "Unklare Legacy-Aufträge": False
        }
        
        # Version importieren
        try:
            from version import __version__, __app_name__
            self.version = __version__
            self.app_name = __app_name__
        except ImportError:
            self.version = "0.8.0"
            self.app_name = "WerkstattArchiv"
        
        # Fenster-Konfiguration
        self.title(f"{self.app_name} v{self.version}")
        self.geometry("1200x700")
        
        # Schließen-Handler für Watchdog
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Tabview erstellen
        self.tabview = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tabs hinzufügen
        self.tabview.add("Einstellungen")
        self.tabview.add("Verarbeitung")
        self.tabview.add("Suche")
        self.tabview.add("Unklare Dokumente")
        self.tabview.add("Unklare Legacy-Aufträge")
        self.tabview.add("Regex-Patterns")
        
        # Nur die wichtigsten Tabs sofort erstellen (Einstellungen + Verarbeitung)
        self.create_settings_tab()
        self.create_processing_tab()
        self.tabs_created["Einstellungen"] = True
        self.tabs_created["Verarbeitung"] = True
    
    def on_tab_change(self):
        """Wird aufgerufen wenn ein Tab gewechselt wird (Lazy Loading)."""
        current_tab = self.tabview.get()
        
        # Tab erstellen wenn noch nicht vorhanden
        if not self.tabs_created.get(current_tab, False):
            if current_tab == "Suche":
                self.create_search_tab()
                self.tabs_created["Suche"] = True
            elif current_tab == "Unklare Dokumente":
                self.create_unclear_tab()
                self.tabs_created["Unklare Dokumente"] = True
            elif current_tab == "Unklare Legacy-Aufträge":
                self.create_unclear_legacy_tab()
                self.tabs_created["Unklare Legacy-Aufträge"] = True
            elif current_tab == "Regex-Patterns":
                self.create_patterns_tab()
                self.tabs_created["Regex-Patterns"] = True
        
        # Daten laden wenn Tab bereits erstellt aber Daten noch nicht geladen
        if current_tab == "Suche" and not self.tabs_data_loaded["Suche"]:
            # Lade Dokumenttypen und Jahre asynchron
            def load_search_data():
                doc_types = ["Alle"] + self.document_index.get_all_document_types()
                years = ["Alle"] + [str(y) for y in self.document_index.get_all_years()]
                
                # Update GUI im Haupt-Thread
                self.after(0, lambda: self.search_dokument_typ.configure(values=doc_types))
                self.after(0, lambda: self.search_jahr.configure(values=years))
            
            # Starte in Thread
            thread = threading.Thread(target=load_search_data, daemon=True)
            thread.start()
            self.tabs_data_loaded["Suche"] = True
        
        elif current_tab == "Unklare Legacy-Aufträge" and not self.tabs_data_loaded["Unklare Legacy-Aufträge"]:
            # Lade Legacy-Einträge asynchron
            self.tabs_data_loaded["Unklare Legacy-Aufträge"] = True
            thread = threading.Thread(target=self.load_unclear_legacy_entries, daemon=True)
            thread.start()
    
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
        
        # Separator
        separator = ctk.CTkFrame(settings_frame, height=2, fg_color="gray")
        separator.pack(fill="x", padx=20, pady=20)
        
        # Backup-Bereich
        backup_title = ctk.CTkLabel(settings_frame, text="💾 Backup & Wiederherstellung", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
        backup_title.pack(pady=10)
        
        backup_info = ctk.CTkLabel(
            settings_frame, 
            text="Sichere alle wichtigen Daten: Konfiguration, Kundendatenbank, Index-Datenbank, Fahrzeug-Index",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        backup_info.pack(pady=5)
        
        backup_buttons_frame = ctk.CTkFrame(settings_frame)
        backup_buttons_frame.pack(pady=10)
        
        create_backup_btn = ctk.CTkButton(
            backup_buttons_frame, 
            text="📦 Backup erstellen",
            command=self.create_backup,
            width=200,
            fg_color="green"
        )
        create_backup_btn.pack(side="left", padx=5)
        
        restore_backup_btn = ctk.CTkButton(
            backup_buttons_frame, 
            text="♻️ Backup wiederherstellen",
            command=self.restore_backup,
            width=200,
            fg_color="orange"
        )
        restore_backup_btn.pack(side="left", padx=5)
        
        manage_backups_btn = ctk.CTkButton(
            backup_buttons_frame, 
            text="📋 Backups verwalten",
            command=self.manage_backups,
            width=200
        )
        manage_backups_btn.pack(side="left", padx=5)
        
        # Backup-Status
        self.backup_status = ctk.CTkLabel(settings_frame, text="")
        self.backup_status.pack(pady=5)
    
    def create_processing_tab(self):
        """Erstellt den Verarbeitungs-Tab."""
        tab = self.tabview.tab("Verarbeitung")
        
        # Header mit Logo und Version
        header_frame = ctk.CTkFrame(tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        app_title = ctk.CTkLabel(
            header_frame, 
            text=f"📁 {self.app_name}",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        app_title.pack(side="left", padx=10)
        
        version_label = ctk.CTkLabel(
            header_frame, 
            text=f"v{self.version}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        version_label.pack(side="left", padx=5)
        
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
        
        # Watchdog Controls (wenn verfügbar)
        if WATCHDOG_AVAILABLE:
            self.watch_btn = ctk.CTkButton(control_frame, text="🔍 Auto-Watch starten",
                                          command=self.toggle_watchdog,
                                          fg_color="green")
            self.watch_btn.pack(side="left", padx=10, pady=10)
            
            self.watch_status = ctk.CTkLabel(control_frame, text="⚪ Gestoppt", 
                                            font=ctk.CTkFont(size=11))
            self.watch_status.pack(side="left", padx=5)
        
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
        self.search_dokument_typ = ctk.CTkComboBox(fields_frame, width=150, values=["Alle"])
        self.search_dokument_typ.set("Alle")
        self.search_dokument_typ.grid(row=2, column=1, padx=5, pady=5)
        
        # Jahr
        ctk.CTkLabel(fields_frame, text="Jahr:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.search_jahr = ctk.CTkComboBox(fields_frame, width=150, values=["Alle"])
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
        
        # Platzhalter bis zum ersten Laden
        placeholder = ctk.CTkLabel(self.legacy_container, 
                                  text="⏳ Daten werden beim ersten Öffnen geladen...",
                                  font=ctk.CTkFont(size=12),
                                  text_color="gray")
        placeholder.pack(pady=20)
    
    def create_patterns_tab(self):
        """Erstellt den Tab für Regex-Pattern Konfiguration."""
        tab = self.tabview.tab("Regex-Patterns")
        
        # Header
        header_frame = ctk.CTkFrame(tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(header_frame, 
                                   text="🔧 Regex-Pattern Konfiguration",
                                   font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(side="left", padx=10)
        
        # Buttons
        button_frame = ctk.CTkFrame(header_frame)
        button_frame.pack(side="right", padx=10)
        
        save_btn = ctk.CTkButton(button_frame, text="💾 Speichern",
                                command=self.save_patterns,
                                width=120)
        save_btn.pack(side="left", padx=5)
        
        reset_btn = ctk.CTkButton(button_frame, text="↺ Zurücksetzen",
                                 command=self.reset_patterns,
                                 width=120)
        reset_btn.pack(side="left", padx=5)
        
        test_btn = ctk.CTkButton(button_frame, text="🧪 Pattern testen",
                                command=self.test_pattern,
                                width=120)
        test_btn.pack(side="left", padx=5)
        
        self.pattern_status = ctk.CTkLabel(header_frame, text="")
        self.pattern_status.pack(side="right", padx=10)
        
        # Info
        info_frame = ctk.CTkFrame(tab)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        info_text = ("ℹ️ Hier können Sie die Regex-Patterns für die Dokumentenanalyse anpassen.\n"
                    "   Regex-Gruppen mit () werden extrahiert. Änderungen wirken sofort bei der nächsten Verarbeitung.")
        info_label = ctk.CTkLabel(info_frame, text=info_text, 
                                 font=ctk.CTkFont(size=11), justify="left")
        info_label.pack(padx=10, pady=10)
        
        # Scrollable Frame für Pattern-Eingaben
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Pattern-Eingabefelder erstellen
        self.pattern_entries = {}
        patterns = self.pattern_manager.get_all_patterns()
        descriptions = self.pattern_manager.get_pattern_descriptions()
        
        # Nach Kategorien gruppieren
        categories = {
            "Stammdaten": ["kunden_nr", "auftrag_nr", "datum", "kunden_name"],
            "Fahrzeugdaten": ["fin", "kennzeichen"],
            "Adressdaten": ["plz", "strasse"],
            "Dokumenttypen": ["rechnung", "kva", "auftrag", "hu", "garantie"]
        }
        
        row = 0
        for category, pattern_names in categories.items():
            # Kategorie-Header
            cat_label = ctk.CTkLabel(scroll_frame, text=f"▼ {category}",
                                    font=ctk.CTkFont(size=14, weight="bold"))
            cat_label.grid(row=row, column=0, columnspan=3, sticky="w", padx=10, pady=(15, 5))
            row += 1
            
            # Pattern in dieser Kategorie
            for name in pattern_names:
                if name not in patterns:
                    continue
                
                # Name
                name_label = ctk.CTkLabel(scroll_frame, text=name,
                                         font=ctk.CTkFont(size=11, weight="bold"),
                                         width=150, anchor="w")
                name_label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
                
                # Pattern-Eingabe
                entry = ctk.CTkEntry(scroll_frame, width=500)
                entry.insert(0, patterns[name])
                entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                self.pattern_entries[name] = entry
                
                # Beschreibung
                desc_label = ctk.CTkLabel(scroll_frame, text=descriptions.get(name, ""),
                                         font=ctk.CTkFont(size=10),
                                         text_color="gray", anchor="w")
                desc_label.grid(row=row, column=2, padx=10, pady=5, sticky="w")
                
                row += 1
        
        # Grid-Konfiguration
        scroll_frame.grid_columnconfigure(1, weight=1)
    
    def save_patterns(self):
        """Speichert die Regex-Patterns."""
        invalid_patterns = []
        
        # Validierung
        for name, entry in self.pattern_entries.items():
            pattern = entry.get().strip()
            if not self.pattern_manager.validate_pattern(pattern):
                invalid_patterns.append(name)
        
        if invalid_patterns:
            messagebox.showerror("Fehler", 
                               f"Ungültige Regex-Patterns:\n" + "\n".join(invalid_patterns))
            self.pattern_status.configure(text="✗ Ungültige Patterns", text_color="red")
            return
        
        # Speichern
        for name, entry in self.pattern_entries.items():
            pattern = entry.get().strip()
            self.pattern_manager.update_pattern(name, pattern)
        
        self.pattern_status.configure(text="✓ Patterns gespeichert", text_color="green")
        messagebox.showinfo("Erfolg", "Regex-Patterns erfolgreich gespeichert!")
    
    def reset_patterns(self):
        """Setzt alle Patterns auf Standardwerte zurück."""
        if not messagebox.askyesno("Zurücksetzen", 
                                   "Alle Patterns auf Standardwerte zurücksetzen?"):
            return
        
        self.pattern_manager.reset_to_defaults()
        
        # GUI aktualisieren
        patterns = self.pattern_manager.get_all_patterns()
        for name, entry in self.pattern_entries.items():
            if name in patterns:
                entry.delete(0, "end")
                entry.insert(0, patterns[name])
        
        self.pattern_status.configure(text="✓ Auf Standard zurückgesetzt", text_color="green")
        messagebox.showinfo("Erfolg", "Patterns auf Standardwerte zurückgesetzt!")
    
    def test_pattern(self):
        """Öffnet Dialog zum Testen eines Patterns."""
        # Dialog erstellen
        dialog = ctk.CTkToplevel(self)
        dialog.title("Regex-Pattern testen")
        dialog.geometry("700x500")
        
        # Pattern-Auswahl
        pattern_frame = ctk.CTkFrame(dialog)
        pattern_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(pattern_frame, text="Pattern:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        pattern_names = list(self.pattern_entries.keys())
        pattern_selector = ctk.CTkComboBox(pattern_frame, values=pattern_names, width=300)
        pattern_selector.set(pattern_names[0] if pattern_names else "")
        pattern_selector.pack(fill="x", pady=5)
        
        # Testtext-Eingabe
        text_frame = ctk.CTkFrame(dialog)
        text_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(text_frame, text="Testtext:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        test_textbox = ctk.CTkTextbox(text_frame, height=150)
        test_textbox.pack(fill="both", expand=True, pady=5)
        test_textbox.insert("1.0", "Beispiel:\nKunden-Nr.: 28307\nAuftragsnummer: 78708\nDatum: 15.03.2019")
        
        # Ergebnis-Anzeige
        result_frame = ctk.CTkFrame(dialog)
        result_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(result_frame, text="Ergebnis:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        result_textbox = ctk.CTkTextbox(result_frame, height=100)
        result_textbox.pack(fill="both", expand=True, pady=5)
        
        def run_test():
            selected_name = pattern_selector.get()
            if selected_name not in self.pattern_entries:
                result_textbox.delete("1.0", "end")
                result_textbox.insert("1.0", "Fehler: Pattern nicht gefunden")
                return
            
            pattern = self.pattern_entries[selected_name].get().strip()
            test_text = test_textbox.get("1.0", "end").strip()
            
            result_textbox.delete("1.0", "end")
            
            if not self.pattern_manager.validate_pattern(pattern):
                result_textbox.insert("1.0", "✗ Ungültiges Regex-Pattern!")
                return
            
            match = self.pattern_manager.test_pattern(pattern, test_text)
            
            if match:
                result_textbox.insert("1.0", f"✓ Match gefunden:\n\n{match}")
            else:
                result_textbox.insert("1.0", "✗ Kein Match gefunden")
        
        # Test-Button
        test_btn = ctk.CTkButton(dialog, text="▶ Test ausführen", command=run_test)
        test_btn.pack(pady=10)
    
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
        
        # Daten-Flags zurücksetzen (damit sie beim nächsten Öffnen neu laden)
        self.tabs_data_loaded["Suche"] = False
        self.tabs_data_loaded["Unklare Legacy-Aufträge"] = False
    
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
    
    def toggle_watchdog(self):
        """Startet oder stoppt die automatische Ordnerüberwachung."""
        if not WATCHDOG_AVAILABLE:
            messagebox.showerror("Fehler", 
                               "watchdog nicht installiert!\n\n"
                               "Installation mit: pip install watchdog")
            return
        
        if self.watchdog_service and self.watchdog_service.is_watching:
            # Stoppen
            self.stop_watchdog()
        else:
            # Starten
            self.start_watchdog()
    
    def start_watchdog(self):
        """Startet die automatische Ordnerüberwachung."""
        input_dir = self.config.get("input_dir")
        
        if not input_dir or not os.path.exists(input_dir):
            messagebox.showerror("Fehler", 
                               "Eingangsordner nicht gefunden!\n"
                               "Bitte Einstellungen prüfen.")
            return
        
        try:
            # Watchdog-Service erstellen
            from services.watchdog_service import WatchdogService
            self.watchdog_service = WatchdogService(
                watch_directory=input_dir,
                callback=self.process_single_document
            )
            
            # Starten
            if self.watchdog_service.start():
                self.watch_btn.configure(text="⏹ Auto-Watch stoppen", fg_color="red")
                self.watch_status.configure(text="🟢 Aktiv", text_color="green")
                self.process_status.configure(text=f"Überwache: {input_dir}")
                messagebox.showinfo("Auto-Watch", 
                                  f"Ordnerüberwachung gestartet!\n\n"
                                  f"Ordner: {input_dir}\n\n"
                                  f"Neue Dokumente werden automatisch verarbeitet.")
            else:
                messagebox.showerror("Fehler", "Konnte Überwachung nicht starten!")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Starten:\n{e}")
    
    def stop_watchdog(self):
        """Stoppt die automatische Ordnerüberwachung."""
        if self.watchdog_service:
            if self.watchdog_service.stop():
                self.watch_btn.configure(text="🔍 Auto-Watch starten", fg_color="green")
                self.watch_status.configure(text="⚪ Gestoppt", text_color="gray")
                self.process_status.configure(text="Bereit")
                self.watchdog_service = None
            else:
                messagebox.showerror("Fehler", "Konnte Überwachung nicht stoppen!")
    
    def process_single_document(self, file_path: str):
        """
        Verarbeitet ein einzelnes Dokument (wird von Watchdog aufgerufen).
        
        Args:
            file_path: Pfad zum Dokument
        """
        try:
            filename = os.path.basename(file_path)
            root_dir = self.config.get("root_dir")
            unclear_dir = self.config.get("unclear_dir")
            tesseract_path = self.config.get("tesseract_path")
            
            # Validierung
            if not root_dir or not unclear_dir:
                print(f"❌ Konfiguration unvollständig für: {filename}")
                return
            
            # Legacy-Resolver initialisieren
            from services.legacy_resolver import LegacyResolver
            from services.vehicles import VehicleManager
            
            vehicle_manager = VehicleManager()
            legacy_resolver = LegacyResolver(self.customer_manager, vehicle_manager)
            
            # Dokument analysieren
            analysis = analyze_document(
                file_path, 
                tesseract_path,
                vorlage_name=self.vorlagen_manager.get_active_vorlage().name,
                vorlagen_manager=self.vorlagen_manager,
                legacy_resolver=legacy_resolver
            )
            
            # Dokument verarbeiten
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
            
            # Zum Index hinzufügen
            self.document_index.add_document(file_path, target_path, analysis, doc_status)
            
            # Bei unklaren Legacy-Aufträgen: zur unclear_legacy Tabelle hinzufügen
            if analysis.get("is_legacy") and analysis.get("legacy_match_reason") == "unclear":
                self.document_index.add_unclear_legacy(target_path, analysis)
            
            # Ergebnis in GUI anzeigen
            self._add_result_row(filename, analysis, status, color)
            
            # Status aktualisieren
            self.process_status.configure(text=f"Letztes Dokument: {filename} - {status}")
            
            # Daten-Flags zurücksetzen (damit sie beim nächsten Öffnen neu laden)
            self.tabs_data_loaded["Suche"] = False
            self.tabs_data_loaded["Unklare Legacy-Aufträge"] = False
            
            print(f"✅ Dokument verarbeitet: {filename} → {status}")
            
        except Exception as e:
            print(f"❌ Fehler beim Verarbeiten von {file_path}: {e}")
            log_error(file_path, str(e))
    
    def load_unclear_legacy_entries(self):
        """Lädt unklare Legacy-Einträge aus der Datenbank (Thread-sicher)."""
        # Lade-Indikator anzeigen (im Haupt-Thread)
        def show_loading():
            for widget in self.legacy_container.winfo_children():
                widget.destroy()
            
            loading_label = ctk.CTkLabel(
                self.legacy_container, 
                text="⏳ Lade Daten...",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            loading_label.pack(pady=20)
            self.legacy_status.configure(text="Lädt...", text_color="gray")
        
        # Zeige Lade-Indikator
        if threading.current_thread() != threading.main_thread():
            self.after(0, show_loading)
        else:
            show_loading()
        
        # Einträge aus DB laden (kann langsam sein)
        entries = self.document_index.get_unclear_legacy_entries(status="offen")
        
        # GUI-Update im Haupt-Thread
        def update_gui():
            # Alte Widgets löschen
            for widget in self.legacy_container.winfo_children():
                widget.destroy()
            
            if not entries:
                no_entries = ctk.CTkLabel(
                    self.legacy_container, 
                    text="✓ Keine unklaren Legacy-Aufträge vorhanden",
                    font=ctk.CTkFont(size=14),
                    text_color="green"
                )
                no_entries.pack(pady=20)
                self.legacy_status.configure(text="0 offene Einträge", text_color="green")
                return
            
            # Einträge anzeigen
            for entry in entries:
                self._add_legacy_entry_row(entry)
            
            self.legacy_status.configure(text=f"{len(entries)} offene Einträge", text_color="orange")
        
        # Update GUI im Haupt-Thread
        if threading.current_thread() != threading.main_thread():
            self.after(0, update_gui)
        else:
            update_gui()
    
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
            
            # Daten-Flags zurücksetzen (damit sie beim nächsten Öffnen neu laden)
            self.tabs_data_loaded["Suche"] = False
            self.tabs_data_loaded["Unklare Legacy-Aufträge"] = False
            
            # Liste neu laden
            self.load_unclear_legacy_entries()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei der Zuordnung:\n{e}")
    
    def create_backup(self):
        """Erstellt ein Backup aller wichtigen Daten."""
        from services.backup_manager import BackupManager
        
        # Backup-Namen abfragen
        dialog = ctk.CTkInputDialog(
            text="Backup-Name (optional):",
            title="Backup erstellen"
        )
        backup_name = dialog.get_input()
        
        if backup_name is None:  # Abgebrochen
            return
        
        # Backup erstellen
        backup_manager = BackupManager(self.config)
        success, backup_path, message = backup_manager.create_backup(backup_name)
        
        if success:
            self.backup_status.configure(text="✓ Backup erstellt", text_color="green")
            messagebox.showinfo("Backup erfolgreich", message)
        else:
            self.backup_status.configure(text="✗ Fehler", text_color="red")
            messagebox.showerror("Backup fehlgeschlagen", message)
    
    def restore_backup(self):
        """Stellt ein Backup wieder her."""
        from services.backup_manager import BackupManager
        
        # Backup-Datei auswählen
        backup_path = filedialog.askopenfilename(
            title="Backup auswählen",
            filetypes=[("ZIP-Archiv", "*.zip"), ("Alle Dateien", "*.*")],
            initialdir=os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "..", 
                "backups"
            )
        )
        
        if not backup_path:
            return
        
        # Sicherheitsabfrage
        if not messagebox.askyesno(
            "Backup wiederherstellen",
            "⚠️ WARNUNG: Alle aktuellen Daten werden überschrieben!\n\n"
            "Möchten Sie wirklich dieses Backup wiederherstellen?\n\n"
            "Empfehlung: Erstellen Sie zuerst ein Backup der aktuellen Daten!"
        ):
            return
        
        # Backup wiederherstellen
        backup_manager = BackupManager(self.config)
        success, message = backup_manager.restore_backup(backup_path)
        
        if success:
            self.backup_status.configure(text="✓ Wiederhergestellt", text_color="green")
            messagebox.showinfo("Wiederherstellung erfolgreich", message)
        else:
            self.backup_status.configure(text="✗ Fehler", text_color="red")
            messagebox.showerror("Wiederherstellung fehlgeschlagen", message)
    
    def manage_backups(self):
        """Zeigt Backup-Verwaltungs-Dialog."""
        from services.backup_manager import BackupManager
        
        backup_manager = BackupManager(self.config)
        backups = backup_manager.list_backups()
        
        # Neues Fenster für Backup-Verwaltung
        manage_window = ctk.CTkToplevel(self)
        manage_window.title("Backup-Verwaltung")
        manage_window.geometry("900x500")
        
        # Überschrift
        title = ctk.CTkLabel(manage_window, text="📋 Verfügbare Backups", 
                            font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=10)
        
        if not backups:
            no_backups = ctk.CTkLabel(manage_window, text="Keine Backups vorhanden",
                                     font=ctk.CTkFont(size=14),
                                     text_color="gray")
            no_backups.pack(pady=50)
            return
        
        # Scrollbarer Bereich
        scroll_frame = ctk.CTkScrollableFrame(manage_window)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Backup-Liste
        for backup in backups:
            backup_frame = ctk.CTkFrame(scroll_frame)
            backup_frame.pack(fill="x", pady=5, padx=5)
            
            # Backup-Info
            info_frame = ctk.CTkFrame(backup_frame)
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            name_label = ctk.CTkLabel(info_frame, text=backup["name"],
                                     font=ctk.CTkFont(size=14, weight="bold"),
                                     anchor="w")
            name_label.pack(anchor="w")
            
            date_label = ctk.CTkLabel(info_frame, 
                                     text=f"📅 {backup['created_at'][:19].replace('T', ' ')}",
                                     font=ctk.CTkFont(size=11),
                                     anchor="w")
            date_label.pack(anchor="w")
            
            size_mb = backup["size"] / (1024 * 1024)
            size_label = ctk.CTkLabel(info_frame, 
                                     text=f"💾 {size_mb:.2f} MB | Dateien: {', '.join(backup['files'])}",
                                     font=ctk.CTkFont(size=10),
                                     text_color="gray",
                                     anchor="w")
            size_label.pack(anchor="w")
            
            # Aktions-Buttons
            button_frame = ctk.CTkFrame(backup_frame)
            button_frame.pack(side="right", padx=10)
            
            restore_btn = ctk.CTkButton(button_frame, text="♻️ Wiederherstellen",
                                       command=lambda p=backup["path"]: self._restore_from_manage(p, manage_window),
                                       width=150,
                                       fg_color="green")
            restore_btn.pack(side="left", padx=5)
            
            delete_btn = ctk.CTkButton(button_frame, text="🗑️ Löschen",
                                      command=lambda p=backup["path"], f=backup_frame: self._delete_backup(p, f, backup_manager),
                                      width=100,
                                      fg_color="red")
            delete_btn.pack(side="left", padx=5)
    
    def _restore_from_manage(self, backup_path: str, manage_window):
        """Hilfsfunktion zum Wiederherstellen aus der Verwaltung."""
        manage_window.destroy()
        
        from services.backup_manager import BackupManager
        
        if not messagebox.askyesno(
            "Backup wiederherstellen",
            "⚠️ WARNUNG: Alle aktuellen Daten werden überschrieben!\n\n"
            "Möchten Sie wirklich dieses Backup wiederherstellen?"
        ):
            return
        
        backup_manager = BackupManager(self.config)
        success, message = backup_manager.restore_backup(backup_path)
        
        if success:
            self.backup_status.configure(text="✓ Wiederhergestellt", text_color="green")
            messagebox.showinfo("Wiederherstellung erfolgreich", message)
        else:
            self.backup_status.configure(text="✗ Fehler", text_color="red")
            messagebox.showerror("Wiederherstellung fehlgeschlagen", message)
    
    def _delete_backup(self, backup_path: str, frame, backup_manager):
        """Hilfsfunktion zum Löschen eines Backups."""
        if messagebox.askyesno("Backup löschen", "Backup wirklich löschen?"):
            success, message = backup_manager.delete_backup(backup_path)
            
            if success:
                frame.destroy()
                messagebox.showinfo("Erfolg", message)
            else:
                messagebox.showerror("Fehler", message)
    
    def on_closing(self):
        """Wird beim Schließen des Fensters aufgerufen."""
        # Watchdog stoppen falls aktiv
        if self.watchdog_service and self.watchdog_service.is_watching:
            print("Stoppe Watchdog...")
            self.watchdog_service.stop()
        
        # Fenster schließen
        self.destroy()


def create_and_run_gui(config: Dict[str, Any], customer_manager: CustomerManager):
    """
    Erstellt und startet die GUI.
    
    Args:
        config: Konfigurationsdictionary
        customer_manager: CustomerManager-Instanz
    """
    app = MainWindow(config, customer_manager)
    app.mainloop()

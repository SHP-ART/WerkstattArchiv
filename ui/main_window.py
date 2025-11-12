"""
GUI für WerkstattArchiv.
Hauptfenster mit customtkinter für die Dokumentenverwaltung.
"""

import os
import json
import time
import shutil
from datetime import datetime
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
from services.virtual_customer_manager import VirtualCustomerManager
from core.folder_structure_manager import FolderStructureManager

try:
    from services.watchdog_service import WatchdogService
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️  watchdog nicht installiert. Auto-Watch nicht verfügbar.")


class MainWindow(ctk.CTk):
    """Hauptfenster der Anwendung mit customtkinter."""
    
    def __init__(self, config: Dict[str, Any], customer_manager: CustomerManager, skip_gui_init: bool = False):
        """
        Initialisiert das Hauptfenster.
        
        Args:
            config: Konfigurationsdictionary
            customer_manager: CustomerManager-Instanz
            skip_gui_init: Wenn True, wird die GUI-Initialisierung übersprungen (für main_window_start.py)
        """
        super().__init__()
        
        self.config = config
        self.customer_manager = customer_manager
        self.unclear_documents: List[Dict[str, Any]] = []
        self.document_index = DocumentIndex()
        self.vorlagen_manager = VorlagenManager()
        self.pattern_manager = PatternManager()
        self.virtual_customer_manager = VirtualCustomerManager(
            config.get("root_dir", ""),
            customer_manager
        )
        self.folder_structure_manager = FolderStructureManager(
            config.get("folder_structure", {})
        )
        self.watchdog_observer = None
        self.is_processing = False  # Flag um Doppelverarbeitung zu verhindern
        self.is_scanning = False  # Flag um Doppel-Scans zu verhindern

        # Liste der gescannten Dateien
        self.scanned_files = []
        
        # Cache für Such-Daten
        self._search_doc_types = []
        self._search_years = []
        
        # Tab-Erstellungs-Flags (Lazy Loading)
        self.tabs_created = {
            "Einstellungen": False,
            "Verarbeitung": False,
            "Suche": False,
            "Unklare Dokumente": False,
            "Unklare Legacy-Aufträge": False,
            "Virtuelle Kunden": False,
            "Regex-Patterns": False,
            "System": False,
            "Logs": False
        }

        # Daten-Lade-Flags (für Refresh)
        self.tabs_data_loaded = {
            "Suche": False,
            "Unklare Legacy-Aufträge": False
        }

        # Cache für Dropdown-Liste
        self._customer_dropdown_cache = None
        self._customer_dropdown_cache_time = 0
        
        # Log-Buffer für Log-Tab
        self.log_buffer = []
        self.max_log_entries = 500  # Maximal 500 Log-Einträge im Speicher (Performance)
        self.max_log_file_lines = 10000  # Maximal 10.000 Zeilen in Log-Datei
        
        # Log-Datei initialisieren
        self.log_file_path = os.path.join(os.path.dirname(__file__), "..", "logs", "werkstatt.log")
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
        
        # Lade existierende Logs beim Start
        self._load_existing_logs()
        
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
        
        # Zeige Ladebildschirm nur wenn nicht skip_gui_init
        if not skip_gui_init:
            self.show_loading_screen()
            # Lade GUI asynchron
            self.after(100, self.init_gui)
    
    def show_loading_screen(self):
        """Zeigt einen Ladebildschirm während die GUI geladen wird."""
        # Loading Frame
        self.loading_frame = ctk.CTkFrame(self)
        self.loading_frame.pack(fill="both", expand=True)
        
        # Titel
        title = ctk.CTkLabel(self.loading_frame, text=f"{self.app_name} v{self.version}",
                            font=ctk.CTkFont(size=32, weight="bold"))
        title.pack(pady=(100, 20))
        
        # Lade-Text
        loading_label = ctk.CTkLabel(self.loading_frame, text="Lade Anwendung...",
                                     font=ctk.CTkFont(size=16))
        loading_label.pack(pady=10)
        
        # Progress Bar (determiniert für genauen Fortschritt)
        self.loading_progress = ctk.CTkProgressBar(self.loading_frame, width=400)
        self.loading_progress.pack(pady=30)
        self.loading_progress.set(0)
        
        # Status Label
        self.loading_status = ctk.CTkLabel(self.loading_frame, text="Initialisiere...",
                                          font=ctk.CTkFont(size=12),
                                          text_color="gray")
        self.loading_status.pack(pady=5)
        
        # Detail Label
        self.loading_detail = ctk.CTkLabel(self.loading_frame, text="",
                                          font=ctk.CTkFont(size=10),
                                          text_color="darkgray")
        self.loading_detail.pack(pady=2)
    
    def update_loading_progress(self, progress: float, status: str, detail: str = ""):
        """Aktualisiert den Ladefortschritt mit Animation."""
        self.loading_progress.set(progress)
        self.loading_status.configure(text=status)
        if detail:
            self.loading_detail.configure(text=detail)
        self.update_idletasks()
        time.sleep(0.5)  # Längere Animation zwischen Steps für bessere UX
    
    def init_gui(self):
        """Initialisiert die GUI-Komponenten vollständig synchron mit Animation."""
        self.update_loading_progress(0.05, "Erstelle Tab-Struktur...", "Tabview-System")
        
        # Tabview erstellen
        self.tabview = ctk.CTkTabview(self, command=self.on_tab_change)
        
        # Tabs hinzufügen
        self.tabview.add("Einstellungen")
        self.tabview.add("Verarbeitung")
        self.tabview.add("Suche")
        self.tabview.add("Unklare Dokumente")
        self.tabview.add("Unklare Legacy-Aufträge")
        self.tabview.add("Virtuelle Kunden")
        self.tabview.add("Regex-Patterns")
        self.tabview.add("System")
        self.tabview.add("Logs")
        
        # Erstelle ALLE Tabs und lade ALLE Daten synchron
        self.update_loading_progress(0.1, "⚙️  Lade Einstellungen...", "Konfiguration und Pfade")
        self.create_settings_tab()
        self.tabs_created["Einstellungen"] = True
        
        self.update_loading_progress(0.2, "📁 Lade Verarbeitung...", "Scan- und Verarbeitungs-Funktionen")
        self.create_processing_tab()
        self.tabs_created["Verarbeitung"] = True
        
        self.update_loading_progress(0.3, "🔍 Erstelle Suche...", "Such-Interface")
        self.create_search_tab()
        self.tabs_created["Suche"] = True
        
        self.update_loading_progress(0.4, "📊 Lade Such-Daten...", "Dokumenttypen und Jahre aus Datenbank")
        try:
            doc_types = ["Alle"] + self.document_index.get_all_document_types()
            years = ["Alle"] + [str(y) for y in self.document_index.get_all_years()]
            self._search_doc_types = doc_types
            self._search_years = years
            self.search_dokument_typ.configure(values=doc_types)
            self.search_jahr.configure(values=years)
            self.tabs_data_loaded["Suche"] = True
            self.update_loading_progress(0.45, "📊 Such-Daten geladen", 
                                        f"{len(doc_types)-1} Dokumenttypen, {len(years)-1} Jahre")
        except Exception as e:
            print(f"Fehler beim Laden der Such-Daten: {e}")
            self.update_loading_progress(0.45, "📊 Such-Daten (Fehler)", "Fallback zu Standard-Werten")
        
        self.update_loading_progress(0.5, "⚠️  Erstelle Unklare Dokumente...", "Nachbearbeitungs-Interface")
        self.create_unclear_tab()
        self.tabs_created["Unklare Dokumente"] = True
        
        self.update_loading_progress(0.6, "📜 Erstelle Legacy-Aufträge...", "Legacy-Interface")
        self.create_unclear_legacy_tab()
        self.tabs_created["Unklare Legacy-Aufträge"] = True
        
        self.update_loading_progress(0.65, "📜 Lade Legacy-Daten...", "Unklare Legacy-Einträge aus DB")
        try:
            unclear_legacy = self.document_index.get_unclear_legacy_entries()
            for doc in unclear_legacy:
                self._add_legacy_row(
                    doc.get("ziel_pfad", ""),
                    doc.get("kunden_name", "Unbekannt"),
                    doc.get("auftrag_nr", "-"),
                    doc.get("dokument_typ", "Unbekannt"),
                    doc.get("kennzeichen", "-"),
                    doc.get("fin", "-"),
                    doc.get("confidence", 0.0),
                    doc.get("hinweis", "")
                )
            self.tabs_data_loaded["Unklare Legacy-Aufträge"] = True
            self.update_loading_progress(0.7, "📜 Legacy-Daten geladen", 
                                        f"{len(unclear_legacy)} unklare Einträge")
        except Exception as e:
            print(f"Fehler beim Laden der Legacy-Daten: {e}")
            self.update_loading_progress(0.7, "📜 Legacy-Daten (Fehler)", "Fallback zu leerem Tab")
        
        self.update_loading_progress(0.75, "👥 Erstelle Virtuelle Kunden...", "Kunden-Verwaltung")
        self.create_virtual_customers_tab()
        self.tabs_created["Virtuelle Kunden"] = True
        
        self.update_loading_progress(0.8, "🔤 Erstelle Regex-Patterns...", "Pattern-Editor")
        self.create_patterns_tab()
        self.tabs_created["Regex-Patterns"] = True
        
        self.update_loading_progress(0.85, "🔧 Erstelle System...", "System-Tools")
        self.create_system_tab()
        self.tabs_created["System"] = True
        
        self.update_loading_progress(0.9, "📋 Erstelle Logs...", "Debug-Log-Anzeige")
        self.create_logs_tab()
        self.tabs_created["Logs"] = True
        
        # Alles vollständig geladen
        self.update_loading_progress(1.0, "✅ Vollständig geladen!", "Alle Tabs und Daten sind bereit")
        self.after(300, self._finalize_gui)
        
    def _finalize_gui(self):
        """Entfernt Loading-Screen und zeigt GUI."""
        self.loading_frame.pack_forget()
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Wechsle zum Standard-Tab (Verarbeitung)
        self.tabview.set("Verarbeitung")
    
    def on_tab_change(self):
        """Wird aufgerufen wenn ein Tab gewechselt wird - alle Daten bereits geladen."""
        # Alle Tabs und Daten sind bereits vollständig geladen
        pass
        pass
    
    def create_settings_tab(self):
        """Erstellt den Einstellungen-Tab."""
        self.add_log("INFO", "Erstelle Einstellungen-Tab")
        tab = self.tabview.tab("Einstellungen")
        
        # Scrollable Frame für alle Einstellungen
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ========== PFAD-EINSTELLUNGEN ==========
        path_frame = ctk.CTkFrame(scroll_frame)
        path_frame.pack(fill="x", padx=10, pady=10)
        
        # Überschrift
        title = ctk.CTkLabel(path_frame, text="📁 Pfad-Einstellungen", 
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
            row_frame = ctk.CTkFrame(path_frame)
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
        
        # ========== ORDNERSTRUKTUR-EINSTELLUNGEN ==========
        self.create_folder_structure_settings(scroll_frame)
        
        # ========== AKTIONS-BUTTONS ==========
        action_frame = ctk.CTkFrame(scroll_frame)
        action_frame.pack(fill="x", padx=10, pady=20)
        
        # Speichern-Button
        save_btn = ctk.CTkButton(action_frame, text="💾 Alle Einstellungen speichern",
                                command=self.save_settings,
                                font=ctk.CTkFont(size=14, weight="bold"))
        save_btn.pack(pady=10)
        
        # Kundendatenbank neu laden Button
        reload_btn = ctk.CTkButton(action_frame, text="🔄 Kundendatenbank neu laden",
                                  command=self.reload_customers)
        reload_btn.pack(pady=5)
        
        # Status-Label
        self.settings_status = ctk.CTkLabel(action_frame, text="")
        self.settings_status.pack(pady=5)
        
        self.add_log("SUCCESS", f"Einstellungen-Tab erstellt ({len(self.entries)} Pfad-Felder)")
    
    def create_folder_structure_settings(self, parent_frame):
        """Erstellt die Einstellungen für Ordnerstruktur."""
        structure_frame = ctk.CTkFrame(parent_frame)
        structure_frame.pack(fill="x", padx=10, pady=10)
        
        # Überschrift
        title = ctk.CTkLabel(structure_frame, text="📂 Ordnerstruktur-Einstellungen", 
                            font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)
        
        # Info-Text
        info = ctk.CTkLabel(structure_frame, 
                           text="Definiere wie Dokumente organisiert werden sollen",
                           font=ctk.CTkFont(size=12))
        info.pack(pady=5)
        
        # Profil-Auswahl
        profile_frame = ctk.CTkFrame(structure_frame)
        profile_frame.pack(fill="x", padx=20, pady=10)
        
        profile_label = ctk.CTkLabel(profile_frame, text="Profil:", width=150, anchor="w")
        profile_label.pack(side="left", padx=5)
        
        self.structure_profile_var = ctk.StringVar(value="Standard")
        profile_dropdown = ctk.CTkComboBox(
            profile_frame,
            variable=self.structure_profile_var,
            values=self.folder_structure_manager.get_profile_list(),
            command=self.on_profile_changed,
            width=200
        )
        profile_dropdown.pack(side="left", padx=5)
        
        # Profil-Beschreibung
        self.profile_desc = ctk.CTkLabel(profile_frame, text="", 
                                        font=ctk.CTkFont(size=11, slant="italic"))
        self.profile_desc.pack(side="left", padx=10, fill="x", expand=True)
        
        # Ordner-Template
        folder_frame = ctk.CTkFrame(structure_frame)
        folder_frame.pack(fill="x", padx=20, pady=5)
        
        folder_label = ctk.CTkLabel(folder_frame, text="Ordner-Template:", width=150, anchor="w")
        folder_label.pack(side="left", padx=5)
        
        self.folder_template_entry = ctk.CTkEntry(folder_frame, width=400)
        self.folder_template_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.folder_template_entry.insert(0, self.folder_structure_manager.folder_template)
        self.folder_template_entry.bind("<KeyRelease>", lambda e: self.update_structure_preview())
        
        # Dateiname-Template
        filename_frame = ctk.CTkFrame(structure_frame)
        filename_frame.pack(fill="x", padx=20, pady=5)
        
        filename_label = ctk.CTkLabel(filename_frame, text="Dateiname-Muster:", width=150, anchor="w")
        filename_label.pack(side="left", padx=5)
        
        self.filename_template_entry = ctk.CTkEntry(filename_frame, width=400)
        self.filename_template_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.filename_template_entry.insert(0, self.folder_structure_manager.filename_template)
        self.filename_template_entry.bind("<KeyRelease>", lambda e: self.update_structure_preview())
        
        # Platzhalter-Info
        placeholder_frame = ctk.CTkFrame(structure_frame)
        placeholder_frame.pack(fill="x", padx=20, pady=10)
        
        placeholder_title = ctk.CTkLabel(placeholder_frame, text="Verfügbare Platzhalter:", 
                                        font=ctk.CTkFont(size=12, weight="bold"))
        placeholder_title.pack(anchor="w", padx=5, pady=5)
        
        # Platzhalter in 2 Spalten
        ph_grid = ctk.CTkFrame(placeholder_frame)
        ph_grid.pack(fill="x", padx=5)
        
        placeholders = list(self.folder_structure_manager.PLACEHOLDERS.items())
        half = len(placeholders) // 2
        
        # Linke Spalte
        left_col = ctk.CTkFrame(ph_grid)
        left_col.pack(side="left", fill="both", expand=True, padx=5)
        for key, desc in placeholders[:half]:
            ph_label = ctk.CTkLabel(left_col, text=f"• {{{key}}} - {desc}", 
                                   font=ctk.CTkFont(size=10), anchor="w")
            ph_label.pack(anchor="w", pady=2)
        
        # Rechte Spalte
        right_col = ctk.CTkFrame(ph_grid)
        right_col.pack(side="left", fill="both", expand=True, padx=5)
        for key, desc in placeholders[half:]:
            ph_label = ctk.CTkLabel(right_col, text=f"• {{{key}}} - {desc}", 
                                   font=ctk.CTkFont(size=10), anchor="w")
            ph_label.pack(anchor="w", pady=2)
        
        # Optionen
        options_frame = ctk.CTkFrame(structure_frame)
        options_frame.pack(fill="x", padx=20, pady=10)
        
        opt_title = ctk.CTkLabel(options_frame, text="Optionen:", 
                                font=ctk.CTkFont(size=12, weight="bold"))
        opt_title.pack(anchor="w", padx=5, pady=5)
        
        self.replace_spaces_var = ctk.BooleanVar(value=self.folder_structure_manager.replace_spaces)
        replace_check = ctk.CTkCheckBox(options_frame, text="Leerzeichen durch Unterstriche ersetzen",
                                       variable=self.replace_spaces_var,
                                       command=self.update_structure_preview)
        replace_check.pack(anchor="w", padx=20, pady=2)
        
        self.remove_invalid_var = ctk.BooleanVar(value=self.folder_structure_manager.remove_invalid_chars)
        invalid_check = ctk.CTkCheckBox(options_frame, text="Ungültige Zeichen entfernen",
                                       variable=self.remove_invalid_var,
                                       command=self.update_structure_preview)
        invalid_check.pack(anchor="w", padx=20, pady=2)
        
        self.use_month_names_var = ctk.BooleanVar(value=self.folder_structure_manager.use_month_names)
        month_check = ctk.CTkCheckBox(options_frame, text="Monatsnamen statt Nummern (z.B. '11_November')",
                                     variable=self.use_month_names_var,
                                     command=self.update_structure_preview)
        month_check.pack(anchor="w", padx=20, pady=2)
        
        # Vorschau
        preview_frame = ctk.CTkFrame(structure_frame)
        preview_frame.pack(fill="x", padx=20, pady=10)
        
        preview_title = ctk.CTkLabel(preview_frame, text="📋 Vorschau:", 
                                     font=ctk.CTkFont(size=12, weight="bold"))
        preview_title.pack(anchor="w", padx=5, pady=5)
        
        self.structure_preview = ctk.CTkTextbox(preview_frame, height=80, 
                                               font=ctk.CTkFont(family="Courier", size=11))
        self.structure_preview.pack(fill="x", padx=5, pady=5)
        
        # Initial-Vorschau
        self.update_structure_preview()
        
        # Profil-Beschreibung initial setzen
        self.update_profile_description()
    
    def on_profile_changed(self, choice):
        """Wird aufgerufen wenn Profil geändert wird."""
        profile_name = self.structure_profile_var.get()
        if self.folder_structure_manager.load_profile(profile_name):
            # Update GUI-Felder
            self.folder_template_entry.delete(0, "end")
            self.folder_template_entry.insert(0, self.folder_structure_manager.folder_template)
            
            self.filename_template_entry.delete(0, "end")
            self.filename_template_entry.insert(0, self.folder_structure_manager.filename_template)
            
            # Update Vorschau
            self.update_structure_preview()
            self.update_profile_description()
            self.add_log("INFO", f"Profil '{profile_name}' geladen")
    
    def update_profile_description(self):
        """Aktualisiert die Profil-Beschreibung."""
        profile_name = self.structure_profile_var.get()
        if profile_name in self.folder_structure_manager.PROFILES:
            desc = self.folder_structure_manager.PROFILES[profile_name]["description"]
            self.profile_desc.configure(text=desc)
    
    def update_structure_preview(self):
        """Aktualisiert die Struktur-Vorschau."""
        # Update Manager-Konfiguration
        self.folder_structure_manager.folder_template = self.folder_template_entry.get()
        self.folder_structure_manager.filename_template = self.filename_template_entry.get()
        self.folder_structure_manager.replace_spaces = self.replace_spaces_var.get()
        self.folder_structure_manager.remove_invalid_chars = self.remove_invalid_var.get()
        self.folder_structure_manager.use_month_names = self.use_month_names_var.get()
        
        # Validiere Templates
        folder_valid, folder_error = self.folder_structure_manager.validate_template(
            self.folder_structure_manager.folder_template
        )
        filename_valid, filename_error = self.folder_structure_manager.validate_template(
            self.folder_structure_manager.filename_template
        )
        
        # Generiere Vorschau
        self.structure_preview.delete("1.0", "end")
        
        if not folder_valid:
            self.structure_preview.insert("end", f"❌ Fehler im Ordner-Template:\n{folder_error}\n\n")
        elif not filename_valid:
            self.structure_preview.insert("end", f"❌ Fehler im Dateiname-Template:\n{filename_error}\n\n")
        else:
            folder_path, filename = self.folder_structure_manager.preview()
            self.structure_preview.insert("end", "✅ Beispiel-Pfad:\n\n")
            self.structure_preview.insert("end", f"{folder_path}/\n")
            self.structure_preview.insert("end", f"  └─ {filename}\n")
    
    def create_virtual_customers_tab(self):
        """Erstellt den Tab für virtuelle Kunden-Verwaltung."""
        tab = self.tabview.tab("Virtuelle Kunden")
        
        # Scrollable Frame
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Überschrift
        title = ctk.CTkLabel(scroll_frame, text="Virtuelle Kunden-Verwaltung",
                            font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)
        
        # Info-Text
        info_text = (
            "Hier sehen Sie alle virtuellen Kunden (VKxxxx), die automatisch erstellt wurden,\n"
            "wenn keine Kundennummer erkannt werden konnte. Sie können diese virtuellen\n"
            "Kundennummern durch echte ersetzen - alle zugehörigen Dateien werden automatisch umbenannt."
        )
        info_label = ctk.CTkLabel(scroll_frame, text=info_text,
                                  font=ctk.CTkFont(size=11),
                                  text_color="gray")
        info_label.pack(pady=10)
        
        # Refresh-Button
        refresh_btn = ctk.CTkButton(scroll_frame, text="🔄 Liste aktualisieren",
                                   command=self.refresh_virtual_customers_list,
                                   width=200)
        refresh_btn.pack(pady=10)
        
        # Frame für virtuelle Kunden-Liste
        self.virtual_customers_frame = ctk.CTkFrame(scroll_frame)
        self.virtual_customers_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Lade initiale Liste
        self.refresh_virtual_customers_list()
    
    def refresh_virtual_customers_list(self):
        """Aktualisiert die Liste der virtuellen Kunden."""
        # Lösche alte Einträge
        for widget in self.virtual_customers_frame.winfo_children():
            widget.destroy()
        
        # Hole virtuelle Kunden
        virtual_customers = self.virtual_customer_manager.get_all_virtual_customers()
        
        if not virtual_customers:
            no_virt_label = ctk.CTkLabel(self.virtual_customers_frame,
                                         text="✓ Keine virtuellen Kunden vorhanden",
                                         font=ctk.CTkFont(size=14),
                                         text_color="green")
            no_virt_label.pack(pady=20)
            return
        
        # Header
        header_frame = ctk.CTkFrame(self.virtual_customers_frame)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(header_frame, text="Virtuelle Nr.", width=100,
                    font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Name", width=200,
                    font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Dateien", width=80,
                    font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Aktion", width=300,
                    font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        
        # Einträge für jeden virtuellen Kunden
        for virt_nr, name in virtual_customers:
            # Zähle Dateien
            files = self.virtual_customer_manager.find_files_with_customer(virt_nr)
            file_count = len(files)
            
            # Zeile
            row_frame = ctk.CTkFrame(self.virtual_customers_frame)
            row_frame.pack(fill="x", padx=5, pady=2)
            
            # Virtuelle Nummer
            ctk.CTkLabel(row_frame, text=virt_nr, width=100).pack(side="left", padx=5)
            
            # Name
            ctk.CTkLabel(row_frame, text=name, width=200).pack(side="left", padx=5)
            
            # Datei-Anzahl
            ctk.CTkLabel(row_frame, text=str(file_count), width=80).pack(side="left", padx=5)
            
            # Eingabefelder für echte Kundennummer
            real_nr_entry = ctk.CTkEntry(row_frame, placeholder_text="Echte Kd-Nr",
                                        width=100)
            real_nr_entry.pack(side="left", padx=5)
            
            real_name_entry = ctk.CTkEntry(row_frame, placeholder_text="Echter Name",
                                          width=150)
            real_name_entry.pack(side="left", padx=5)
            
            # Zuordnen-Button
            assign_btn = ctk.CTkButton(
                row_frame, 
                text="→ Zuordnen",
                width=100,
                command=lambda v=virt_nr, r_nr=real_nr_entry, r_name=real_name_entry:
                    self.assign_real_customer(v, r_nr, r_name)
            )
            assign_btn.pack(side="left", padx=5)
    
    def assign_real_customer(self, virtual_nr, real_nr_entry, real_name_entry):
        """Ordnet einem virtuellen Kunden eine echte Kundennummer zu."""
        real_nr = real_nr_entry.get().strip()
        real_name = real_name_entry.get().strip()
        
        if not real_nr or not real_name:
            messagebox.showerror("Fehler", "Bitte echte Kundennummer und Namen eingeben!")
            return
        
        # Bestätigung
        files = self.virtual_customer_manager.find_files_with_customer(virtual_nr)
        msg = (
            f"Virtuelle Kundennummer '{virtual_nr}' wird durch '{real_nr}' ersetzt.\n\n"
            f"Betroffen: {len(files)} Dateien\n"
            f"Neuer Kundenname: {real_name}\n\n"
            f"Alle Dateien werden umbenannt. Fortfahren?"
        )
        
        if not messagebox.askyesno("Bestätigung", msg):
            return
        
        # Zuordnung durchführen
        success, error_msg, renamed_count = self.virtual_customer_manager.assign_real_customer_to_virtual(
            virtual_nr, real_nr, real_name
        )
        
        if success:
            messagebox.showinfo("Erfolg",
                               f"✓ Virtuelle Kundennummer ersetzt!\n\n"
                               f"{renamed_count} Dateien umbenannt.\n"
                               f"{virtual_nr} → {real_nr}")
            
            # Liste aktualisieren
            self.refresh_virtual_customers_list()
        else:
            messagebox.showerror("Fehler",
                                f"Fehler beim Zuordnen:\n{error_msg}")
    
    def create_system_tab(self):
        """Erstellt den System-Tab für Backup und Updates."""
        tab = self.tabview.tab("System")

        # Scrollable Frame für System (damit man scrollen kann bei kleinem Fenster)
        system_frame = ctk.CTkScrollableFrame(tab)
        system_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Überschrift
        title = ctk.CTkLabel(system_frame, text="System & Wartung",
                            font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)
        
        # Backup-Bereich
        backup_title = ctk.CTkLabel(system_frame, text="💾 Backup & Wiederherstellung", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
        backup_title.pack(pady=10)
        
        backup_info = ctk.CTkLabel(
            system_frame, 
            text="Sichere alle wichtigen Daten: Konfiguration, Kundendatenbank, Index-Datenbank, Fahrzeug-Index",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        backup_info.pack(pady=5)
        
        backup_buttons_frame = ctk.CTkFrame(system_frame)
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
        self.backup_status = ctk.CTkLabel(system_frame, text="")
        self.backup_status.pack(pady=5)
        
        # Separator
        separator = ctk.CTkFrame(system_frame, height=2, fg_color="gray")
        separator.pack(fill="x", padx=20, pady=20)
        
        # Update-Bereich
        update_title = ctk.CTkLabel(system_frame, text="🔄 Software-Updates", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
        update_title.pack(pady=10)
        
        update_info = ctk.CTkLabel(
            system_frame, 
            text=f"Aktuelle Version: {self.version} | Prüfe auf neue Versionen von GitHub",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        update_info.pack(pady=5)
        
        update_buttons_frame = ctk.CTkFrame(system_frame)
        update_buttons_frame.pack(pady=10)
        
        check_update_btn = ctk.CTkButton(
            update_buttons_frame, 
            text="🔍 Auf Updates prüfen",
            command=self.check_for_updates,
            width=200,
            fg_color="blue"
        )
        check_update_btn.pack(side="left", padx=5)
        
        # Update-Status
        self.update_status = ctk.CTkLabel(system_frame, text="")
        self.update_status.pack(pady=5)

        # Separator
        separator2 = ctk.CTkFrame(system_frame, height=2, fg_color="gray")
        separator2.pack(fill="x", padx=20, pady=20)

        # Datenbank-Bereich
        db_title = ctk.CTkLabel(system_frame, text="🗄️ Datenbank-Verwaltung",
                                font=ctk.CTkFont(size=18, weight="bold"))
        db_title.pack(pady=10)

        db_info = ctk.CTkLabel(
            system_frame,
            text="Verwalte die Dokument-Index-Datenbank: Statistiken anzeigen, neu aufbauen oder zurücksetzen",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        db_info.pack(pady=5)

        # Datenbank-Statistiken
        self.db_stats_label = ctk.CTkLabel(
            system_frame,
            text="Lade Statistiken...",
            font=ctk.CTkFont(size=11),
            text_color="lightblue"
        )
        self.db_stats_label.pack(pady=5)

        db_buttons_frame = ctk.CTkFrame(system_frame)
        db_buttons_frame.pack(pady=10)

        db_stats_btn = ctk.CTkButton(
            db_buttons_frame,
            text="📊 Statistiken aktualisieren",
            command=self.update_db_stats,
            width=200,
            fg_color="blue"
        )
        db_stats_btn.pack(side="left", padx=5)

        db_rebuild_btn = ctk.CTkButton(
            db_buttons_frame,
            text="🔄 Datenbank neu aufbauen",
            command=self.rebuild_database,
            width=200,
            fg_color="orange"
        )
        db_rebuild_btn.pack(side="left", padx=5)

        db_clear_btn = ctk.CTkButton(
            db_buttons_frame,
            text="🗑️ Datenbank löschen",
            command=self.clear_database,
            width=200,
            fg_color="red"
        )
        db_clear_btn.pack(side="left", padx=5)

        # Datenbank-Status
        self.db_status = ctk.CTkLabel(system_frame, text="")
        self.db_status.pack(pady=5)

        # Initial Statistiken laden
        self.update_db_stats()

    def create_logs_tab(self):
        """Erstellt den Logs-Tab für Debug-Ausgaben."""
        tab = self.tabview.tab("Logs")
        
        # Header
        header_frame = ctk.CTkFrame(tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(header_frame, 
                                   text="📋 System-Logs",
                                   font=ctk.CTkFont(size=16, weight="bold"))
        title_label.pack(side="left", padx=10)
        
        # Control-Buttons
        button_frame = ctk.CTkFrame(header_frame)
        button_frame.pack(side="right", padx=10)
        
        clear_btn = ctk.CTkButton(button_frame, text="🗑️ Logs löschen",
                                 command=self.clear_logs,
                                 width=120)
        clear_btn.pack(side="left", padx=5)
        
        export_btn = ctk.CTkButton(button_frame, text="💾 Exportieren",
                                  command=self.export_logs,
                                  width=120)
        export_btn.pack(side="left", padx=5)
        
        refresh_btn = ctk.CTkButton(button_frame, text="🔄 Aktualisieren",
                                   command=self.refresh_logs,
                                   width=120)
        refresh_btn.pack(side="left", padx=5)
        
        # Auto-Scroll Checkbox
        self.auto_scroll_var = ctk.BooleanVar(value=True)
        auto_scroll_cb = ctk.CTkCheckBox(button_frame, text="Auto-Scroll",
                                        variable=self.auto_scroll_var)
        auto_scroll_cb.pack(side="left", padx=5)
        
        # Info
        info_frame = ctk.CTkFrame(tab)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        info_text = ("ℹ️ Zeigt alle wichtigen System-Events: Dokumenten-Verarbeitung, Fehler, Updates, etc.\n"
                    "   Die neuesten Einträge erscheinen unten. Maximal 1000 Einträge im Speicher.")
        info_label = ctk.CTkLabel(info_frame, text=info_text, 
                                 font=ctk.CTkFont(size=11), justify="left")
        info_label.pack(padx=10, pady=10)
        
        # Log-Anzeige (Textbox)
        log_frame = ctk.CTkFrame(tab)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_textbox = ctk.CTkTextbox(log_frame, 
                                          font=ctk.CTkFont(family="Courier", size=11),
                                          wrap="word")
        self.log_textbox.pack(fill="both", expand=True)
        
        # Status
        self.log_status = ctk.CTkLabel(tab, text="")
        self.log_status.pack(pady=5)
        
        # Lade vorherige Logs aus Datei
        self._load_existing_logs()
        
        # Initial-Nachricht
        self.add_log("INFO", "Log-System gestartet")

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
        
        self.scan_btn = ctk.CTkButton(control_frame, text="📂 Eingangsordner scannen",
                                command=self.scan_input_folder,
                                width=200)
        self.scan_btn.pack(side="left", padx=10, pady=10)
        
        # Verarbeiten-Button (initial deaktiviert)
        self.process_btn = ctk.CTkButton(control_frame, text="▶️ Verarbeitung starten",
                                        command=self.start_processing,
                                        width=200,
                                        fg_color="green",
                                        state="disabled")
        self.process_btn.pack(side="left", padx=10, pady=10)
        
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
        
        # Fortschrittsbalken (initial versteckt)
        progress_container = ctk.CTkFrame(tab, fg_color="transparent")
        progress_container.pack(fill="x", padx=10, pady=(5, 0))
        
        self.progress_bar = ctk.CTkProgressBar(progress_container, width=400, height=20)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # Initial versteckt
        
        self.progress_label = ctk.CTkLabel(progress_container, text="", 
                                          font=ctk.CTkFont(size=10))
        self.progress_label.pack_forget()  # Initial versteckt
        
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
        
        # Monat
        ctk.CTkLabel(fields_frame, text="Monat:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        monate = ["Alle", "01 - Januar", "02 - Februar", "03 - März", "04 - April", 
                  "05 - Mai", "06 - Juni", "07 - Juli", "08 - August", 
                  "09 - September", "10 - Oktober", "11 - November", "12 - Dezember"]
        self.search_monat = ctk.CTkComboBox(fields_frame, width=150, values=monate)
        self.search_monat.set("Alle")
        self.search_monat.grid(row=3, column=1, padx=5, pady=5)
        
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
        """Öffnet Dialog zur Pfadauswahl mit intelligentem Start-Verzeichnis."""
        # Cursor auf "Warten" setzen für visuelles Feedback
        self.configure(cursor="watch")
        self.update_idletasks()

        try:
            # Aktuellen Wert holen für intelligentes initialdir
            current_value = self.entries[key].get().strip()

            # Initialdir bestimmen
            if current_value and os.path.exists(current_value):
                if os.path.isfile(current_value):
                    initial_dir = os.path.dirname(current_value)
                else:
                    initial_dir = current_value
            elif current_value and os.path.dirname(current_value):
                # Falls Pfad nicht existiert, nimm das übergeordnete Verzeichnis
                parent = os.path.dirname(current_value)
                if os.path.exists(parent):
                    initial_dir = parent
                else:
                    initial_dir = os.path.expanduser("~")
            else:
                # Fallback: Home-Verzeichnis
                initial_dir = os.path.expanduser("~")

            # Dialog öffnen mit optimiertem initialdir
            if key == "customers_file":
                path = filedialog.askopenfilename(
                    title="Kundendatei auswählen",
                    filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")],
                    initialdir=initial_dir
                )
            elif key == "tesseract_path":
                path = filedialog.askopenfilename(
                    title="Tesseract-Executable auswählen",
                    filetypes=[("Executable", "*.exe"), ("Alle Dateien", "*.*")],
                    initialdir=initial_dir
                )
            else:
                path = filedialog.askdirectory(
                    title=f"{key} auswählen",
                    initialdir=initial_dir,
                    mustexist=False
                )

            if path:
                self.entries[key].delete(0, "end")
                self.entries[key].insert(0, path)

        finally:
            # Cursor zurücksetzen
            self.configure(cursor="")
    
    def save_settings(self):
        """Speichert die Einstellungen in config.json."""
        for key, entry in self.entries.items():
            value = entry.get().strip()
            if value == "" or value.lower() == "none":
                self.config[key] = None
            else:
                self.config[key] = value
        
        # Speichere Ordnerstruktur-Einstellungen
        self.config["folder_structure"] = self.folder_structure_manager.get_config()
        
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self.settings_status.configure(text="✓ Alle Einstellungen gespeichert", 
                                          text_color="green")
            self.add_log("SUCCESS", "Einstellungen gespeichert (inkl. Ordnerstruktur)")
            
        except Exception as e:
            self.settings_status.configure(text=f"✗ Fehler: {e}", 
                                          text_color="red")
            self.add_log("ERROR", "Fehler beim Speichern der Einstellungen", str(e))
    
    def reload_customers(self):
        """Lädt die Kundendatenbank neu."""
        self.customer_manager.load_customers()
        # Cache invalidieren
        self._customer_dropdown_cache = None
        self._customer_dropdown_cache_time = 0
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
        """Scannt den Eingangsordner und zeigt die gefundenen Dateien an."""
        # Prüfe ob bereits ein Scan läuft
        if self.is_scanning:
            messagebox.showwarning("Scan läuft",
                                 "Es läuft bereits ein Scan. Bitte warten Sie, bis er abgeschlossen ist.")
            return

        input_dir = self.config.get("input_dir")

        if not input_dir or not os.path.exists(input_dir):
            self.add_log("ERROR", "Eingangsordner nicht gefunden", input_dir or "Nicht konfiguriert")
            messagebox.showerror("Fehler",
                               "Eingangsordner nicht gefunden. Bitte Einstellungen prüfen.")
            return

        # Setze Scanning-Flag
        self.is_scanning = True
        self.add_log("INFO", f"Starte Scan von Eingangsordner", input_dir)

        # Button sofort deaktivieren - mit doppeltem Update für sofortige Reaktion
        self.scan_btn.configure(state="disabled", text="⏳ Scanne...")
        self.process_status.configure(text="🔍 Scanne Eingangsordner... Bitte warten...", text_color="blue")
        self.update_idletasks()  # GUI-Layout aktualisieren
        self.update()  # Alle pending Events verarbeiten

        # Scan im Thread ausführen für bessere Performance
        threading.Thread(target=self._scan_files_thread, args=(input_dir,), daemon=True).start()
    
    def _scan_files_thread(self, input_dir):
        """Thread-Funktion für schnellen Scan ohne GUI-Blockierung."""
        try:
            # Dateien finden (schnell, ohne GUI-Updates)
            files = []
            all_files = os.listdir(input_dir)
            
            for file in all_files:
                file_path = os.path.join(input_dir, file)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file)[1].lower()
                    if ext in [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
                        files.append(file_path)
            
            if not files:
                self.after(0, lambda: self.process_status.configure(text="❌ Keine Dateien gefunden", text_color="orange"))
                self.after(0, lambda: self.scan_btn.configure(state="normal", text="📂 Eingangsordner scannen"))
                self.is_scanning = False
                # MessageBox: Keine Dateien gefunden
                self.after(100, lambda: messagebox.showinfo("Scan abgeschlossen",
                                                            "Keine Dateien gefunden.\n\nDer Eingangsordner ist leer."))
                return
            
            # Speichere Dateien
            self.scanned_files = files
            
            # GUI-Updates im Main-Thread
            self.after(0, self._display_scanned_files, files)
            
        except Exception as e:
            self.add_log("ERROR", f"Fehler beim Scannen", str(e))
            self.after(0, lambda: self.process_status.configure(
                text=f"❌ Fehler: {str(e)}", text_color="red"
            ))
            self.after(0, lambda: self.scan_btn.configure(state="normal", text="📂 Eingangsordner scannen"))
            self.is_scanning = False
            # MessageBox: Fehler
            self.after(100, lambda e=e: messagebox.showerror("Fehler beim Scannen",
                                                             f"Ein Fehler ist aufgetreten:\n\n{str(e)}"))
    
    def _display_scanned_files(self, files):
        """Zeigt gescannte Dateien in der GUI an."""
        
        self.add_log("SUCCESS", f"Scan abgeschlossen: {len(files)} Dateien gefunden")

        # Alte Ergebnisse löschen
        for widget in self.results_container.winfo_children():
            widget.destroy()

        # Status und Buttons sofort aktualisieren
        self.process_status.configure(
            text=f"✓ {len(files)} Datei(en) gefunden - Klicken Sie auf 'Verarbeitung starten'",
            text_color="green"
        )
        self.scan_btn.configure(state="normal", text="📂 Eingangsordner scannen")
        self.process_btn.configure(state="normal")

        # Scanning-Flag zurücksetzen
        self.is_scanning = False

        # MessageBox: Dateien gefunden
        messagebox.showinfo("Scan abgeschlossen",
                           f"✓ {len(files)} Datei(en) gefunden!\n\nKlicken Sie auf 'Verarbeitung starten', um fortzufahren.")
        
        # Zeige Dateien in kleineren Chunks
        chunk_size = 10
        for i in range(0, len(files), chunk_size):
            chunk = files[i:i + chunk_size]
            for idx, file_path in enumerate(chunk):
                filename = os.path.basename(file_path)
                file_idx = i + idx
                self._add_result_row(filename, {}, f"⏸️ Bereit ({file_idx+1}/{len(files)})", "gray")
            
            # Nach jedem Chunk: GUI-Update erlauben
            if (i + chunk_size) % 30 == 0:  # Nur alle 30 Dateien
                self.update_idletasks()
    
    def start_processing(self):
        """Startet die Verarbeitung der gescannten Dateien."""
        
        if not self.scanned_files:
            messagebox.showwarning("Keine Dateien", "Bitte zuerst den Eingangsordner scannen.")
            return
        
        if self.is_processing:
            messagebox.showwarning("Verarbeitung läuft",
                                 "Es läuft bereits eine Verarbeitung. Bitte warten Sie, bis sie abgeschlossen ist.")
            return
        
        # Setze Processing-Flag
        self.is_processing = True

        # Buttons deaktivieren
        self.scan_btn.configure(state="disabled")
        self.process_btn.configure(state="disabled", text="⏳ VERARBEITUNG LÄUFT...")

        # Fortschrittsbalken anzeigen und zurücksetzen
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)
        self.progress_label.pack(pady=(0, 5))
        self.progress_label.configure(text=f"Starte Verarbeitung von {len(self.scanned_files)} Datei(en)...")

        # Status aktualisieren
        self.process_status.configure(text="🔄 VERARBEITUNG GESTARTET - Bitte warten...", text_color="blue")
        self.update()  # GUI sofort aktualisieren (vollständig, nicht nur idletasks)

        # In separatem Thread verarbeiten
        thread = threading.Thread(target=self._process_documents)
        thread.daemon = True
        thread.start()
    
    def _process_documents(self):
        """Verarbeitet alle Dokumente im Eingangsordner (läuft in Thread)."""

        root_dir = self.config.get("root_dir")
        unclear_dir = self.config.get("unclear_dir")
        duplicates_dir = self.config.get("duplicates_dir")
        tesseract_path = self.config.get("tesseract_path")

        # Validierung
        if not root_dir or not isinstance(root_dir, str):
            self.after(0, lambda: self.process_status.configure(text="Fehler: Basis-Verzeichnis nicht konfiguriert", text_color="red"))
            self.after(0, lambda: self.scan_btn.configure(state="normal"))
            self.after(0, lambda: self.process_btn.configure(state="normal", text="▶️ Verarbeitung starten"))
            self.is_processing = False
            return

        if not unclear_dir or not isinstance(unclear_dir, str):
            self.after(0, lambda: self.process_status.configure(text="Fehler: Unklar-Ordner nicht konfiguriert", text_color="red"))
            self.after(0, lambda: self.scan_btn.configure(state="normal"))
            self.after(0, lambda: self.process_btn.configure(state="normal", text="▶️ Verarbeitung starten"))
            self.is_processing = False
            return

        if not duplicates_dir or not isinstance(duplicates_dir, str):
            self.after(0, lambda: self.process_status.configure(text="Fehler: Duplikate-Ordner nicht konfiguriert", text_color="red"))
            self.after(0, lambda: self.scan_btn.configure(state="normal"))
            self.after(0, lambda: self.process_btn.configure(state="normal", text="▶️ Verarbeitung starten"))
            self.is_processing = False
            return

        # Duplikate-Ordner erstellen, falls nicht vorhanden
        os.makedirs(duplicates_dir, exist_ok=True)
        
        # Verwende die gescannten Dateien
        files = self.scanned_files

        # Unklare Dokumente Liste leeren (aber Ergebnisse NICHT löschen - sie bleiben sichtbar!)
        self.unclear_documents.clear()
        
        if not files:
            self.after(0, lambda: self.process_status.configure(text="Keine Dateien gefunden", text_color="orange"))
            self.after(0, lambda: self.scan_btn.configure(state="normal"))
            self.after(0, lambda: self.process_btn.configure(state="normal", text="▶️ Verarbeitung starten"))
            self.is_processing = False
            return

        # Status-Update: Anzahl Dateien
        self.after(0, lambda: self.process_status.configure(
            text=f"🔄 Verarbeite {len(files)} Datei(en)...",
            text_color="blue"
        ))

        # Legacy-Resolver nur EINMAL initialisieren (nicht für jede Datei!)
        from services.legacy_resolver import LegacyResolver
        from services.vehicles import VehicleManager
        vehicle_manager = VehicleManager()
        legacy_resolver = LegacyResolver(self.customer_manager, vehicle_manager)

        # Dateien verarbeiten
        success_count = 0
        unclear_count = 0
        error_count = 0
        duplicate_count = 0
        
        for i, file_path in enumerate(files):
            filename = os.path.basename(file_path)

            try:
                # Prüfe ob Datei noch existiert
                if not os.path.exists(file_path):
                    self.after(0, lambda f=filename: self._update_result_row(f, {}, "⚠ Datei nicht gefunden", "orange"))
                    error_count += 1
                    continue

                # Fortschritt PRO DATEI: Start bei 0%
                def update_start(f=filename, idx=i, total=len(files)):
                    self._update_result_row(f, {}, f"⏳ Wird verarbeitet...", "yellow")
                    self.progress_bar.set(0)
                    self.progress_label.configure(text=f"Verarbeite Datei {idx+1} von {total}: Starte...")
                    self.process_status.configure(
                        text=f"🔄 Datei {idx+1}/{total}: {f}",
                        text_color="blue"
                    )
                self.after(0, update_start)

                # Kurze Pause für GUI-Update
                time.sleep(0.1)

                # Fortschritt: 20% - Datei wird gelesen
                def update_reading(f=filename, idx=i, total=len(files)):
                    self.progress_bar.set(0.2)
                    self.progress_label.configure(text=f"Verarbeite Datei {idx+1} von {total}: Lese Datei...")
                self.after(0, update_reading)

                # Dokument analysieren mit gewählter Vorlage und Legacy-Support
                analysis = analyze_document(
                    file_path,
                    tesseract_path,
                    vorlage_name=self.vorlagen_manager.get_active_vorlage().name,
                    vorlagen_manager=self.vorlagen_manager,
                    legacy_resolver=legacy_resolver
                )

                # Fortschritt: 70% - Analyse abgeschlossen
                def update_analyzed(f=filename, idx=i, total=len(files)):
                    self.progress_bar.set(0.7)
                    self.progress_label.configure(text=f"Verarbeite Datei {idx+1} von {total}: Analyse abgeschlossen...")
                self.after(0, update_analyzed)

                # DUPLIKATS-PRÜFUNG
                auftrag_nr = analysis.get("auftrag_nr")
                dokument_typ = analysis.get("dokument_typ")

                if auftrag_nr:
                    duplicate = self.document_index.check_duplicate(auftrag_nr, dokument_typ)
                    if duplicate:
                        # Duplikat gefunden - verschiebe in Duplikate-Ordner
                        dup_name = duplicate.get("dateiname", "unbekannt")
                        dup_path = duplicate.get("ziel_pfad", "unbekannt")

                        # Erstelle Ziel-Pfad im Duplikate-Ordner
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        dup_filename = f"DUPLIKAT_{timestamp}_{filename}"
                        dup_target_path = os.path.join(duplicates_dir, dup_filename)

                        # Verschiebe Datei
                        try:
                            shutil.move(file_path, dup_target_path)

                            def update_duplicate(f=filename, dup=dup_name, idx=i, total=len(files)):
                                self.progress_bar.set(1.0)
                                self.progress_label.configure(text=f"Datei {idx+1} von {total}: Duplikat erkannt und verschoben!")
                                self._update_result_row(f, analysis, f"⚠ Duplikat → verschoben in Duplikate/", "orange")
                            self.after(0, update_duplicate)

                            # Zur Datenbank hinzufügen (als Duplikat markiert)
                            analysis["hinweis"] = f"Duplikat von: {dup_name}"
                            self.document_index.add_document(file_path, dup_target_path, analysis, "duplicate")

                            print(f"⚠️  Duplikat erkannt: {filename} → Auftrag {auftrag_nr} existiert bereits als {dup_name}")
                            print(f"   Verschoben nach: {dup_target_path}")
                            duplicate_count += 1
                            time.sleep(0.2)
                            continue
                        except Exception as e:
                            print(f"❌ Fehler beim Verschieben des Duplikats: {e}")
                            # Bei Fehler normal verarbeiten
                            pass

                # Dokument verarbeiten und verschieben
                target_path, is_clear, reason = process_document(
                    file_path, analysis, root_dir, unclear_dir, self.customer_manager
                )

                # Fortschritt: 90% - Dokument verschoben
                def update_moved(f=filename, idx=i, total=len(files)):
                    self.progress_bar.set(0.9)
                    self.progress_label.configure(text=f"Verarbeite Datei {idx+1} von {total}: Dokument organisiert...")
                self.after(0, update_moved)
                
                # Logging
                if is_clear:
                    log_success(file_path, target_path, analysis, analysis["confidence"])
                    status = "✓ Verschoben"
                    color = "green"
                    doc_status = "success"
                    success_count += 1
                else:
                    log_unclear(file_path, target_path, analysis, analysis["confidence"], reason)
                    status = "⚠ Unklar"
                    color = "orange"
                    doc_status = "unclear"
                    unclear_count += 1
                    
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

                # Fortschritt: 100% - Fertig!
                def update_complete(f=filename, a=analysis, s=status, c=color, idx=i, total=len(files)):
                    self.progress_bar.set(1.0)
                    self.progress_label.configure(text=f"Datei {idx+1} von {total}: Fertig!")
                    self._update_result_row(f, a, s, c)
                self.after(0, update_complete)

                # Kurze Pause zwischen Dateien (für bessere Sichtbarkeit)
                time.sleep(0.2)

            except Exception as e:
                log_error(file_path, str(e))
                self.document_index.add_document(file_path, file_path, {}, "error")
                error_count += 1
                # Fehler anzeigen (im Haupt-Thread) mit Fortschrittsbalken auf 100%
                def update_error(f=filename, err=str(e), idx=i, total=len(files)):
                    self.progress_bar.set(1.0)
                    self.progress_label.configure(text=f"Datei {idx+1} von {total}: Fehler!")
                    self._update_result_row(f, {}, f"✗ Fehler: {err}", "red")
                self.after(0, update_error)
                time.sleep(0.2)

        # Status aktualisieren mit Zusammenfassung (im Haupt-Thread)
        summary_parts = []
        if success_count > 0:
            summary_parts.append(f"✓ {success_count} erfolgreich")
        if unclear_count > 0:
            summary_parts.append(f"⚠ {unclear_count} unklar")
        if duplicate_count > 0:
            summary_parts.append(f"🔄 {duplicate_count} Duplikat(e)")
        if error_count > 0:
            summary_parts.append(f"✗ {error_count} Fehler")

        summary = " | ".join(summary_parts) if summary_parts else "Keine Dokumente verarbeitet"
        
        self.after(0, lambda: self.process_status.configure(
            text=f"✓ Fertig: {len(files)} Datei(en) verarbeitet ({summary})",
            text_color="green"
        ))
        
        # Fortschrittsbalken auf 100% setzen und dann verstecken
        self.after(0, lambda: self.progress_bar.set(1.0))
        self.after(0, lambda: self.progress_label.configure(text=f"{len(files)} / {len(files)} Dokumente verarbeitet - Fertig!"))
        self.after(2000, lambda: self.progress_bar.pack_forget())  # Nach 2 Sekunden ausblenden
        self.after(2000, lambda: self.progress_label.pack_forget())

        # Button wieder aktivieren (im Haupt-Thread)
        self.after(0, lambda: self.scan_btn.configure(state="normal"))
        self.after(0, lambda: self.process_btn.configure(state="disabled", text="▶️ Verarbeitung starten"))
        
        # Liste leeren
        self.scanned_files = []

        # Processing-Flag zurücksetzen
        self.is_processing = False

        # Unklare Dokumente anzeigen (im Haupt-Thread)
        self.after(0, self._update_unclear_tab)

        # MessageBox mit Ergebnis-Zusammenfassung
        def show_result_message():
            # Erstelle detaillierte Nachricht
            message_lines = [f"Verarbeitung abgeschlossen!\n"]
            message_lines.append(f"Gesamt: {len(files)} Datei(en)\n")

            if success_count > 0:
                message_lines.append(f"✓ {success_count} erfolgreich verarbeitet")
            if unclear_count > 0:
                message_lines.append(f"⚠ {unclear_count} unklar (siehe Tab 'Unklare Dokumente')")
            if duplicate_count > 0:
                message_lines.append(f"🔄 {duplicate_count} Duplikat(e) übersprungen")
            if error_count > 0:
                message_lines.append(f"✗ {error_count} Fehler aufgetreten")

            message = "\n".join(message_lines)

            # Zeige passende MessageBox
            if error_count > 0 or unclear_count > 0:
                messagebox.showwarning("Verarbeitung abgeschlossen", message)
            else:
                messagebox.showinfo("Verarbeitung erfolgreich", message)

        self.after(100, show_result_message)
    
    def _add_result_row(self, filename: str, analysis: Dict[str, Any], 
                       status: str, color: str):
        """Fügt eine Ergebnis-Zeile zur Tabelle hinzu."""
        row_frame = ctk.CTkFrame(self.results_container)
        row_frame.pack(fill="x", pady=2)
        
        # Speichere Referenz für späteres Update
        row_frame._filename = filename
        
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
    
    def _update_result_row(self, filename: str, analysis: Dict[str, Any], 
                          status: str, color: str):
        """Aktualisiert eine existierende Ergebnis-Zeile."""
        # Finde die Zeile mit diesem Dateinamen
        for widget in self.results_container.winfo_children():
            if hasattr(widget, '_filename') and widget._filename == filename:
                # Lösche alte Labels
                for child in widget.winfo_children():
                    child.destroy()
                
                # Füge aktualisierte Daten ein
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
                    label = ctk.CTkLabel(widget, text=value, width=150, anchor="w")
                    if i == len(values) - 1:  # Status-Spalte
                        label.configure(text_color=color)
                    label.grid(row=0, column=i, padx=5, pady=2, sticky="w")
                break
    
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
        
        monat_str = self.search_monat.get()
        monat = None
        if monat_str != "Alle":
            # Extrahiere Monatsnummer (z.B. "01 - Januar" -> "01")
            monat = int(monat_str.split(" - ")[0])

        # Debug: Zeige Suchparameter im Log
        print(f"🔍 Suche mit: kunden_nr={kunden_nr}, kunden_name={kunden_name}, auftrag_nr={auftrag_nr}, dokument_typ={dokument_typ}, jahr={jahr}, monat={monat}, dateiname={dateiname}")

        try:
            # Suche durchführen
            results = self.document_index.search(
                kunden_nr=kunden_nr,
                auftrag_nr=auftrag_nr,
                dokument_typ=dokument_typ,
                jahr=jahr,
                monat=monat,
                kunden_name=kunden_name,
                dateiname=dateiname
            )

            print(f"✓ Suche erfolgreich: {len(results)} Ergebnisse")

            # Ergebnisse anzeigen
            self._display_search_results(results)

            # Status aktualisieren
            self.search_status.configure(
                text=f"{len(results)} Dokument(e) gefunden",
                text_color="green" if results else "orange"
            )
        except Exception as e:
            print(f"✗ Fehler bei Suche: {e}")
            import traceback
            traceback.print_exc()
            self.search_status.configure(
                text=f"Fehler bei Suche: {str(e)}",
                text_color="red"
            )
    
    def clear_search(self):
        """Setzt alle Suchfelder zurück."""
        self.search_kunden_nr.delete(0, "end")
        self.search_kunden_name.delete(0, "end")
        self.search_auftrag_nr.delete(0, "end")
        self.search_dateiname.delete(0, "end")
        self.search_dokument_typ.set("Alle")
        self.search_jahr.set("Alle")
        self.search_monat.set("Alle")
        self.search_status.configure(text="")
        
        # Ergebnisse löschen
        for widget in self.search_results_container.winfo_children():
            widget.destroy()
    
    def show_statistics(self):
        """Zeigt Statistiken über die indexierten Dokumente."""
        try:
            stats = self.document_index.get_statistics()
            
            # Erstelle ein neues Fenster für Statistiken
            stats_window = ctk.CTkToplevel(self)
            stats_window.title("📊 Dokumentenstatistiken")
            stats_window.geometry("700x800")
            
            # Scrollbarer Frame
            scroll_frame = ctk.CTkScrollableFrame(stats_window)
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Überschrift
            title = ctk.CTkLabel(scroll_frame, text="📊 Dokumentenstatistiken", 
                                font=ctk.CTkFont(size=20, weight="bold"))
            title.pack(pady=10)
            
            # Gesamtanzahl (groß und prominent)
            total_frame = ctk.CTkFrame(scroll_frame, fg_color="blue")
            total_frame.pack(fill="x", pady=10)
            
            total_label = ctk.CTkLabel(total_frame, 
                                      text=f"{stats['total']} Dokumente",
                                      font=ctk.CTkFont(size=32, weight="bold"))
            total_label.pack(pady=20)
            
            total_desc = ctk.CTkLabel(total_frame, text="Gesamt indexiert",
                                     font=ctk.CTkFont(size=14))
            total_desc.pack(pady=(0, 10))
            
            # Zusätzliche Übersicht
            overview_frame = ctk.CTkFrame(scroll_frame)
            overview_frame.pack(fill="x", pady=10)
            
            overview_title = ctk.CTkLabel(overview_frame, text="Übersicht:", 
                                         font=ctk.CTkFont(size=16, weight="bold"))
            overview_title.pack(pady=5, anchor="w", padx=10)
            
            overview_items = [
                ("👥 Eindeutige Kunden", stats.get('unique_customers', 0)),
                ("🚗 Eindeutige Fahrzeuge (FIN)", stats.get('unique_vehicles', 0)),
                ("📄 Legacy-Dokumente", stats.get('legacy_count', 0)),
                ("❓ Unklare Legacy-Aufträge", stats.get('unclear_legacy_count', 0)),
                ("📊 Durchschn. Confidence", f"{stats.get('avg_confidence', 0):.2f}")
            ]
            
            for label, value in overview_items:
                row = ctk.CTkFrame(overview_frame)
                row.pack(fill="x", padx=10, pady=2)
                
                ctk.CTkLabel(row, text=label, width=250, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(row, text=str(value), font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
            
            # Nach Status
            status_frame = ctk.CTkFrame(scroll_frame)
            status_frame.pack(fill="x", pady=10)
            
            status_title = ctk.CTkLabel(status_frame, text="Nach Status:", 
                                       font=ctk.CTkFont(size=16, weight="bold"))
            status_title.pack(pady=5, anchor="w", padx=10)
            
            for status, count in stats['by_status'].items():
                status_color = {
                    'success': 'green',
                    'unclear': 'orange',
                    'error': 'red'
                }.get(status, 'gray')
                
                row = ctk.CTkFrame(status_frame)
                row.pack(fill="x", padx=10, pady=2)
                
                ctk.CTkLabel(row, text=f"• {status}:", width=150, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(row, text=str(count), font=ctk.CTkFont(weight="bold"),
                           text_color=status_color).pack(side="left", padx=5)
                
                # Prozentsatz
                percent = (count / stats['total'] * 100) if stats['total'] > 0 else 0
                ctk.CTkLabel(row, text=f"({percent:.1f}%)", text_color="gray").pack(side="left", padx=5)
            
            # Top Dokumenttypen
            if stats['by_type']:
                type_frame = ctk.CTkFrame(scroll_frame)
                type_frame.pack(fill="x", pady=10)
                
                type_title = ctk.CTkLabel(type_frame, text="Dokumenttypen:", 
                                         font=ctk.CTkFont(size=16, weight="bold"))
                type_title.pack(pady=5, anchor="w", padx=10)
                
                for doc_type, count in list(stats['by_type'].items())[:15]:
                    row = ctk.CTkFrame(type_frame)
                    row.pack(fill="x", padx=10, pady=2)
                    
                    ctk.CTkLabel(row, text=f"• {doc_type or 'N/A'}:", width=200, anchor="w").pack(side="left", padx=5)
                    ctk.CTkLabel(row, text=str(count), font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
                    
                    percent = (count / stats['total'] * 100) if stats['total'] > 0 else 0
                    ctk.CTkLabel(row, text=f"({percent:.1f}%)", text_color="gray").pack(side="left", padx=5)
            
            # Nach Jahr
            if stats['by_year']:
                year_frame = ctk.CTkFrame(scroll_frame)
                year_frame.pack(fill="x", pady=10)
                
                year_title = ctk.CTkLabel(year_frame, text="Nach Jahr:", 
                                         font=ctk.CTkFont(size=16, weight="bold"))
                year_title.pack(pady=5, anchor="w", padx=10)
                
                for jahr, count in list(stats['by_year'].items())[:15]:
                    row = ctk.CTkFrame(year_frame)
                    row.pack(fill="x", padx=10, pady=2)
                    
                    ctk.CTkLabel(row, text=f"• {jahr}:", width=100, anchor="w").pack(side="left", padx=5)
                    ctk.CTkLabel(row, text=str(count), font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
                    
                    percent = (count / stats['total'] * 100) if stats['total'] > 0 else 0
                    ctk.CTkLabel(row, text=f"({percent:.1f}%)", text_color="gray").pack(side="left", padx=5)
            
            # Schließen-Button
            close_btn = ctk.CTkButton(scroll_frame, text="Schließen", 
                                     command=stats_window.destroy, width=200)
            close_btn.pack(pady=20)
            
        except Exception as e:
            print(f"Fehler beim Anzeigen der Statistiken: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Fehler", f"Fehler beim Laden der Statistiken:\n{str(e)}")
    
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
            
            # Zeige "wird verarbeitet" Status
            self._add_result_row(filename, {}, "⏳ Wird verarbeitet...", "yellow")
            self.process_status.configure(text=f"🔄 Verarbeite: {filename}", text_color="blue")
            
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
            
            # Aktualisiere Zeile mit finalem Ergebnis
            self._update_result_row(filename, analysis, status, color)
            
            # Status aktualisieren
            self.process_status.configure(text=f"Letztes Dokument: {filename} - {status}")
            
            # Cache für Such-Daten invalidieren
            self._search_doc_types = []
            self._search_years = []
            self.tabs_data_loaded["Suche"] = False
            self.tabs_data_loaded["Unklare Legacy-Aufträge"] = False
            
            print(f"✅ Dokument verarbeitet: {filename} → {status}")
            
        except Exception as e:
            print(f"❌ Fehler beim Verarbeiten von {file_path}: {e}")
            log_error(file_path, str(e))
            # Zeige Fehler in GUI
            filename = os.path.basename(file_path)
            self._update_result_row(filename, {}, f"✗ Fehler: {str(e)}", "red")
    
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

            # Kundenliste einmal laden (schneller als für jeden Eintrag einzeln)
            kunden_liste = self._get_customer_dropdown_list()

            # Einträge anzeigen mit gecachter Kundenliste
            for entry in entries:
                self._add_legacy_entry_row(entry, kunden_liste)

            self.legacy_status.configure(text=f"{len(entries)} offene Einträge", text_color="orange")
        
        # Update GUI im Haupt-Thread
        if threading.current_thread() != threading.main_thread():
            self.after(0, update_gui)
        else:
            update_gui()
    
    def _add_legacy_entry_row(self, entry: Dict[str, Any], kunden_liste: Optional[List[str]] = None):
        """
        Fügt eine Zeile für einen Legacy-Eintrag hinzu.

        Args:
            entry: Legacy-Eintrag Daten
            kunden_liste: Optionale vorgefertigte Kundenliste (Performance-Optimierung)
        """
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

        # Kunden-Dropdown (verwende übergebene Liste oder lade neu)
        if kunden_liste is None:
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
    
    def _get_customer_dropdown_list(self, use_cache: bool = True) -> List[str]:
        """
        Erstellt eine Liste von Kunden für das Dropdown.

        Args:
            use_cache: Wenn True, wird gecachte Liste verwendet (schneller)

        Returns:
            Sortierte Liste von Kundeneinträgen im Format "Nr - Name"
        """
        import time

        # Cache verwenden wenn verfügbar und nicht zu alt (max 60 Sekunden)
        current_time = time.time()
        if use_cache and self._customer_dropdown_cache is not None:
            if current_time - self._customer_dropdown_cache_time < 60:
                return self._customer_dropdown_cache

        # Neue Liste erstellen
        customers = []
        for nr, kunde in self.customer_manager.customers.items():
            # Format: "12345 - Mustermann, Max"
            name = kunde.name if hasattr(kunde, 'name') else "Unbekannt"
            customers.append(f"{nr} - {name}")

        sorted_customers = sorted(customers)

        # Cache aktualisieren
        self._customer_dropdown_cache = sorted_customers
        self._customer_dropdown_cache_time = current_time

        return sorted_customers
    
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
            
            # Cache für Such-Daten invalidieren
            self._search_doc_types = []
            self._search_years = []
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
    
    def check_for_updates(self):
        """Prüft auf neue Versions-Updates von GitHub."""
        from services.updater import UpdateManager
        
        self.update_status.configure(text="🔄 Prüfe auf Updates...", text_color="blue")
        self.update()
        
        # In Thread ausführen um GUI nicht zu blockieren
        def check_thread():
            updater = UpdateManager(self.version)
            update_available, latest_version, download_url = updater.check_for_updates()
            
            # Ergebnis im Haupt-Thread anzeigen
            self.after(0, lambda: self._handle_update_check(
                update_available, latest_version, download_url, updater
            ))
        
        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()
    
    def _handle_update_check(self, update_available: bool, latest_version: Optional[str], 
                            download_url: Optional[str], updater):
        """Verarbeitet das Ergebnis der Update-Prüfung."""
        if update_available and latest_version and download_url:
            self.update_status.configure(
                text=f"✨ Update verfügbar: v{latest_version}", 
                text_color="green"
            )
            
            # Release Notes holen
            release_notes = updater.get_release_notes()
            
            # Update-Dialog anzeigen
            message = (
                f"🎉 Neue Version verfügbar!\n\n"
                f"Installiert: v{self.version}\n"
                f"Verfügbar: v{latest_version}\n\n"
                f"Was ist neu:\n"
                f"{release_notes[:500] if release_notes else 'Siehe GitHub für Details'}\n\n"
                f"Möchten Sie jetzt aktualisieren?\n\n"
                f"⚠️ Die Anwendung wird neu gestartet."
            )
            
            if messagebox.askyesno("Update verfügbar", message):
                self._install_update(download_url, updater)
        else:
            self.update_status.configure(
                text=f"✓ Aktuell (v{self.version})", 
                text_color="green"
            )
            messagebox.showinfo(
                "Keine Updates", 
                f"Sie verwenden bereits die neueste Version (v{self.version})."
            )
    
    def _install_update(self, download_url: str, updater):
        """Installiert ein Update."""
        # Progress-Dialog erstellen
        progress_window = ctk.CTkToplevel(self)
        progress_window.title("Update wird installiert...")
        progress_window.geometry("500x200")
        progress_window.transient(self)
        progress_window.grab_set()
        
        # Progress-Label
        progress_label = ctk.CTkLabel(
            progress_window,
            text="Bereite Update vor...",
            font=ctk.CTkFont(size=14)
        )
        progress_label.pack(pady=20)
        
        # Progress-Bar
        progress_bar = ctk.CTkProgressBar(progress_window, width=400)
        progress_bar.pack(pady=20)
        progress_bar.set(0)
        
        # Status-Label
        status_label = ctk.CTkLabel(
            progress_window,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        status_label.pack(pady=10)
        
        def progress_callback(percent, message):
            """Callback für Update-Fortschritt."""
            self.after(0, lambda: progress_bar.set(percent / 100))
            self.after(0, lambda: status_label.configure(text=message))
        
        def install_thread():
            """Installiert Update in separatem Thread."""
            success, message = updater.download_and_install_update(
                download_url, 
                progress_callback
            )
            
            # Ergebnis anzeigen
            self.after(0, lambda: self._handle_update_result(
                success, message, progress_window, updater
            ))
        
        # Update in Thread starten
        thread = threading.Thread(target=install_thread, daemon=True)
        thread.start()
    
    def _handle_update_result(self, success: bool, message: str, 
                             progress_window, updater):
        """Verarbeitet das Ergebnis der Update-Installation."""
        progress_window.destroy()
        
        if success:
            if messagebox.askyesno("Update erfolgreich", message):
                # Anwendung neu starten
                updater.restart_application()
        else:
            self.update_status.configure(text="✗ Update fehlgeschlagen", text_color="red")
            messagebox.showerror("Update fehlgeschlagen", message)
    
    def update_db_stats(self):
        """Aktualisiert die Datenbank-Statistiken."""
        try:
            stats = self.document_index.get_statistics()

            total = stats.get("total", 0)
            by_status = stats.get("by_status", {})
            success = by_status.get("success", 0)
            unclear = by_status.get("unclear", 0)
            duplicates = by_status.get("duplicate", 0)
            errors = by_status.get("error", 0)

            stats_text = (
                f"📊 Gesamt: {total} Dokumente  |  "
                f"✓ Erfolgreich: {success}  |  "
                f"⚠ Unklar: {unclear}  |  "
                f"🔄 Duplikate: {duplicates}  |  "
                f"❌ Fehler: {errors}"
            )

            self.db_stats_label.configure(text=stats_text, text_color="lightblue")
        except Exception as e:
            self.db_stats_label.configure(
                text=f"❌ Fehler beim Laden der Statistiken: {e}",
                text_color="red"
            )

    def rebuild_database(self):
        """Baut die Datenbank komplett neu auf aus den vorhandenen Dateien."""
        # Bestätigung einholen
        result = messagebox.askyesno(
            "Datenbank neu aufbauen",
            "Möchten Sie die Datenbank wirklich neu aufbauen?\n\n"
            "Dies wird:\n"
            "1. Die aktuelle Datenbank löschen\n"
            "2. Alle Dokumente im Archiv scannen\n"
            "3. Die Datenbank neu erstellen\n\n"
            "Dieser Vorgang kann einige Minuten dauern!"
        )

        if not result:
            return

        # Backup erstellen VOR dem Neuaufbau
        self.db_status.configure(text="💾 Erstelle Backup vor Neuaufbau...", text_color="blue")
        self.update()

        from services.backup_manager import BackupManager
        from datetime import datetime

        backup_manager = BackupManager(self.config)
        backup_name = f"AUTO_VOR_DB_REBUILD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        success, backup_path, message = backup_manager.create_backup(backup_name)

        if not success:
            error_msg = f"Backup fehlgeschlagen!\n\n{message}\n\nNeuaufbau abgebrochen."
            self.db_status.configure(
                text="❌ Backup fehlgeschlagen - Abbruch",
                text_color="red"
            )
            messagebox.showerror("Backup fehlgeschlagen", error_msg)
            return

        # Backup erfolgreich
        self.db_status.configure(text=f"✓ Backup erstellt, baue Datenbank neu auf...", text_color="blue")
        self.update()

        def rebuild_thread():
            try:
                root_dir = self.config.get("root_dir")
                if not root_dir or not os.path.exists(root_dir):
                    self.after(0, lambda: self.db_status.configure(
                        text="❌ Basis-Verzeichnis nicht gefunden!",
                        text_color="red"
                    ))
                    return

                # Datenbank löschen
                import sqlite3
                db_path = "werkstatt_index.db"
                if os.path.exists(db_path):
                    os.remove(db_path)

                # Neuen Index erstellen
                from services.indexer import DocumentIndex
                new_index = DocumentIndex(db_path)

                # Alle PDFs im Archiv finden
                pdf_files = []
                for root, dirs, files in os.walk(root_dir):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            pdf_files.append(os.path.join(root, file))

                self.after(0, lambda: self.db_status.configure(
                    text=f"📄 {len(pdf_files)} Dokumente gefunden, analysiere...",
                    text_color="blue"
                ))

                # Dokumente analysieren und zur Datenbank hinzufügen
                from services.analyzer import analyze_document
                count = 0
                for pdf_file in pdf_files:
                    try:
                        # Einfache Metadaten aus Pfad extrahieren
                        analysis = {
                            "kunden_nr": None,
                            "kunden_name": None,
                            "auftrag_nr": None,
                            "dokument_typ": None,
                            "jahr": None,
                            "confidence": 1.0
                        }

                        # Versuche Infos aus Pfad zu extrahieren
                        path_parts = pdf_file.split(os.sep)
                        for part in path_parts:
                            # Kundennummer und Name (z.B. "28307 - Anne Schultze")
                            if " - " in part and part[0].isdigit():
                                kunde_parts = part.split(" - ", 1)
                                analysis["kunden_nr"] = kunde_parts[0]
                                analysis["kunden_name"] = kunde_parts[1] if len(kunde_parts) > 1 else None
                            # Jahr
                            elif part.isdigit() and len(part) == 4:
                                analysis["jahr"] = int(part)

                        # Dateiname analysieren (z.B. "78708_Auftrag_...")
                        filename = os.path.basename(pdf_file)
                        name_parts = filename.replace(".pdf", "").split("_")
                        if len(name_parts) >= 2:
                            if name_parts[0].isdigit():
                                analysis["auftrag_nr"] = name_parts[0]
                            if len(name_parts) > 1:
                                analysis["dokument_typ"] = name_parts[1]

                        # Zur Datenbank hinzufügen
                        new_index.add_document(pdf_file, pdf_file, analysis, "success")
                        count += 1

                        if count % 10 == 0:
                            self.after(0, lambda c=count, t=len(pdf_files): self.db_status.configure(
                                text=f"📊 {c} von {t} Dokumenten verarbeitet...",
                                text_color="blue"
                            ))
                    except Exception as e:
                        print(f"Fehler bei {pdf_file}: {e}")
                        continue

                # Fertig
                self.after(0, lambda: self.db_status.configure(
                    text=f"✓ Datenbank neu aufgebaut! {count} Dokumente (Backup: {os.path.basename(backup_path)})",
                    text_color="green"
                ))

                # Statistiken aktualisieren
                self.after(0, self.update_db_stats)

                # Erfolgs-Popup mit Backup-Info
                def show_success():
                    messagebox.showinfo(
                        "Neuaufbau erfolgreich",
                        f"✓ Datenbank erfolgreich neu aufgebaut!\n\n"
                        f"{count} Dokumente wurden indexiert.\n\n"
                        f"Backup gespeichert unter:\n{backup_path}"
                    )
                self.after(0, show_success)

            except Exception as e:
                self.after(0, lambda: self.db_status.configure(
                    text=f"❌ Fehler beim Neuaufbau: {e}",
                    text_color="red"
                ))

        thread = threading.Thread(target=rebuild_thread)
        thread.daemon = True
        thread.start()

    def clear_database(self):
        """Löscht die Datenbank komplett (mit automatischem Backup)."""
        # Erste Bestätigung
        result = messagebox.askyesno(
            "Datenbank löschen",
            "⚠️ WARNUNG ⚠️\n\n"
            "Möchten Sie die Datenbank wirklich komplett löschen?\n\n"
            "Ein automatisches Backup wird vor dem Löschen erstellt.\n"
            "Alle Index-Informationen gehen verloren.",
            icon="warning"
        )

        if not result:
            return

        # Zweite Bestätigung
        result2 = messagebox.askyesno(
            "Sind Sie sicher?",
            "Letzte Warnung!\n\n"
            "Die Datenbank wird unwiderruflich gelöscht.\n\n"
            "Sind Sie absolut sicher?",
            icon="warning"
        )

        if not result2:
            return

        # Dritte Bestätigung mit Tipp-Abfrage
        result3 = messagebox.askyesno(
            "Finale Bestätigung",
            "Dies ist Ihre letzte Chance!\n\n"
            "Ein Backup wird automatisch erstellt, bevor die Datenbank gelöscht wird.\n\n"
            "Fortfahren?",
            icon="warning"
        )

        if not result3:
            return

        try:
            db_path = "werkstatt_index.db"
            if not os.path.exists(db_path):
                self.db_status.configure(
                    text="ℹ️ Keine Datenbank zum Löschen gefunden",
                    text_color="orange"
                )
                return

            # Status aktualisieren
            self.db_status.configure(
                text="💾 Erstelle automatisches Backup...",
                text_color="blue"
            )
            self.update()

            # Automatisches Backup erstellen
            from services.backup_manager import BackupManager
            from datetime import datetime

            backup_manager = BackupManager(self.config)
            backup_name = f"AUTO_VOR_DB_LOESCHEN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            success, backup_path, message = backup_manager.create_backup(backup_name)

            if not success:
                error_msg = f"Backup fehlgeschlagen!\n\n{message}\n\nLöschvorgang abgebrochen."
                self.db_status.configure(
                    text="❌ Backup fehlgeschlagen - Abbruch",
                    text_color="red"
                )
                messagebox.showerror("Backup fehlgeschlagen", error_msg)
                return

            # Backup erfolgreich - zeige Info
            messagebox.showinfo(
                "Backup erstellt",
                f"✓ Backup erfolgreich erstellt:\n\n{backup_path}\n\n"
                "Die Datenbank wird jetzt gelöscht."
            )

            # Datenbank löschen
            self.db_status.configure(
                text="🗑️ Lösche Datenbank...",
                text_color="orange"
            )
            self.update()

            os.remove(db_path)

            # Neuen Index erstellen (leere Datenbank)
            from services.indexer import DocumentIndex
            self.document_index = DocumentIndex(db_path)

            self.db_status.configure(
                text=f"✓ Datenbank gelöscht (Backup: {os.path.basename(backup_path)})",
                text_color="green"
            )
            self.update_db_stats()

            messagebox.showinfo(
                "Datenbank gelöscht",
                f"✓ Datenbank wurde erfolgreich gelöscht!\n\n"
                f"Backup gespeichert unter:\n{backup_path}"
            )

        except Exception as e:
            self.db_status.configure(
                text=f"❌ Fehler: {e}",
                text_color="red"
            )
            messagebox.showerror("Fehler", f"Fehler beim Löschen:\n\n{e}")

    def on_closing(self):
        """Wird beim Schließen des Fensters aufgerufen."""
        # Watchdog stoppen falls aktiv
        if hasattr(self, 'watchdog_service') and self.watchdog_service and self.watchdog_service.is_watching:
            print("Stoppe Watchdog...")
            self.watchdog_service.stop()

        # Log-Eintrag
        if hasattr(self, 'log_buffer'):
            self.add_log("INFO", "Anwendung wird beendet")

        # Fenster schließen
        self.destroy()
    
    def add_log(self, level: str, message: str, detail: str = ""):
        """
        Fügt einen Log-Eintrag hinzu (Buffer + Datei).
        
        Args:
            level: Log-Level (INFO, WARNING, ERROR, SUCCESS, DEBUG)
            message: Haupt-Nachricht
            detail: Optionale Detail-Informationen
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Level-Emoji
        level_emojis = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "SUCCESS": "✅",
            "DEBUG": "🔍"
        }
        emoji = level_emojis.get(level, "📝")
        
        # Formatiere Log-Eintrag für Anzeige (nur Zeit)
        display_time = datetime.now().strftime("%H:%M:%S")
        log_entry_display = f"[{display_time}] {emoji} {level:8s} | {message}"
        if detail:
            log_entry_display += f"\n{'':23s}└─ {detail}"
        
        # Formatiere Log-Eintrag für Datei (vollständiger Timestamp)
        log_entry_file = f"[{timestamp}] {level:8s} | {message}"
        if detail:
            log_entry_file += f" | Detail: {detail}"
        
        # Zum Buffer hinzufügen (für GUI-Anzeige)
        self.log_buffer.append(log_entry_display)
        
        # Limit einhalten
        if len(self.log_buffer) > self.max_log_entries:
            self.log_buffer.pop(0)
        
        # In Datei schreiben
        try:
            # Log-Rotation: Wenn Datei zu groß wird, behalte nur letzte 10.000 Zeilen
            if os.path.exists(self.log_file_path):
                file_size = os.path.getsize(self.log_file_path)
                # Rotation bei ~2MB (ca. 20.000 Zeilen bei 100 Zeichen/Zeile)
                if file_size > 2 * 1024 * 1024:
                    with open(self.log_file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    # Behalte nur letzte 10.000 Zeilen
                    with open(self.log_file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines[-self.max_log_file_lines:])
            
            # Schreibe neuen Log-Eintrag
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry_file + "\n")
        except Exception as e:
            print(f"Fehler beim Schreiben in Log-Datei: {e}")
        
        # In GUI anzeigen (wenn Tab existiert)
        if hasattr(self, 'log_textbox'):
            self.log_textbox.insert("end", log_entry_display + "\n")
            
            # Auto-Scroll
            if hasattr(self, 'auto_scroll_var') and self.auto_scroll_var.get():
                self.log_textbox.see("end")
        
        # Auch in Konsole ausgeben für kritische Fehler
        if level == "ERROR":
            print(f"ERROR: {message}")
            if detail:
                print(f"  Detail: {detail}")
    
    def _load_existing_logs(self):
        """Lädt existierende Logs aus der Datei beim Programmstart."""
        try:
            if os.path.exists(self.log_file_path):
                # Lese nur die letzten 200 Zeilen (Performance)
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Konvertiere Datei-Format zurück zu Display-Format
                for line in lines[-200:]:  # Nur letzte 200 Zeilen
                    line = line.strip()
                    if line and line.startswith('['):
                        # Extrahiere Daten aus Datei-Format: [YYYY-MM-DD HH:MM:SS] LEVEL | Message
                        try:
                            parts = line.split('|', 2)
                            if len(parts) >= 2:
                                timestamp_level = parts[0].strip()
                                message_part = '|'.join(parts[1:]).strip()
                                
                                # Extrahiere Zeit (HH:MM:SS)
                                time_match = timestamp_level.split(']')[0].split()[-1]
                                level = timestamp_level.split(']')[1].strip()
                                
                                # Erstelle Display-Format
                                level_emojis = {
                                    "INFO": "ℹ️",
                                    "WARNING": "⚠️",
                                    "ERROR": "❌",
                                    "SUCCESS": "✅",
                                    "DEBUG": "🔍"
                                }
                                emoji = level_emojis.get(level, "📝")
                                display_entry = f"[{time_match}] {emoji} {level:8s} | {message_part}"
                                self.log_buffer.append(display_entry)
                        except:
                            pass  # Überspringe fehlerhafte Zeilen
                            
        except Exception as e:
            print(f"Fehler beim Laden der Log-Datei: {e}")
    
    def clear_logs(self):
        """Löscht alle Logs."""
        if messagebox.askyesno("Logs löschen", "Alle Logs löschen?"):
            self.log_buffer.clear()
            self.log_textbox.delete("1.0", "end")
            self.add_log("INFO", "Logs gelöscht")
            self.log_status.configure(text="✓ Logs gelöscht", text_color="green")
    
    def export_logs(self):
        """Exportiert Logs in eine Datei."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"werkstatt_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            filetypes=[("Text-Dateien", "*.txt"), ("Alle Dateien", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"WerkstattArchiv Log-Export\n")
                    f.write(f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                    f.write(f"Version: {self.version}\n")
                    f.write("=" * 80 + "\n\n")
                    
                    for entry in self.log_buffer:
                        f.write(entry + "\n")
                
                self.add_log("SUCCESS", f"Logs exportiert: {os.path.basename(filename)}")
                self.log_status.configure(text=f"✓ Exportiert: {os.path.basename(filename)}", 
                                         text_color="green")
            except Exception as e:
                self.add_log("ERROR", f"Fehler beim Exportieren: {str(e)}")
                messagebox.showerror("Fehler", f"Fehler beim Exportieren:\n{str(e)}")
    
    def refresh_logs(self):
        """Aktualisiert die Log-Anzeige."""
        self.log_textbox.delete("1.0", "end")
        for entry in self.log_buffer:
            self.log_textbox.insert("end", entry + "\n")
        
        if self.auto_scroll_var.get():
            self.log_textbox.see("end")
        
        self.log_status.configure(text=f"✓ {len(self.log_buffer)} Log-Einträge", 
                                 text_color="green")


def create_and_run_gui(config: Dict[str, Any], customer_manager: CustomerManager):
    """
    Erstellt und startet die GUI.
    Verwendet das MainWindow selbst für den Loading-Screen.
    
    Args:
        config: Konfigurationsdictionary
        customer_manager: CustomerManager-Instanz
    """
    # Erstelle MainWindow - zeigt automatisch Loading-Screen
    app = MainWindow(config, customer_manager, skip_gui_init=False)
    app.mainloop()


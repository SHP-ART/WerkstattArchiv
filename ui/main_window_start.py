"""
Startup und Ladebildschirm für WerkstattArchiv.
Behandelt die vollständige Initialisierung bevor die Haupt-GUI angezeigt wird.
"""

import customtkinter as ctk


class LoadingWindow(ctk.CTk):
    """Separates Fenster für den Ladebildschirm."""
    
    def __init__(self):
        super().__init__()
        
        # Version importieren
        try:
            from version import __version__, __app_name__
            self.version = __version__
            self.app_name = __app_name__
        except ImportError:
            self.version = "0.8.5"
            self.app_name = "WerkstattArchiv"
        
        # Fenster-Konfiguration
        self.title(f"{self.app_name} - Wird geladen...")
        self.geometry("500x300")
        
        # Zentriere das Fenster
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Nicht schließbar während des Ladens
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Loading Frame
        loading_frame = ctk.CTkFrame(self)
        loading_frame.pack(fill="both", expand=True)
        
        # Logo/App Name
        title = ctk.CTkLabel(loading_frame, text=self.app_name,
                            font=ctk.CTkFont(size=32, weight="bold"))
        title.pack(pady=30)
        
        # Version
        version_label = ctk.CTkLabel(loading_frame, text=f"Version {self.version}",
                                     font=ctk.CTkFont(size=14),
                                     text_color="gray")
        version_label.pack(pady=5)
        
        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(loading_frame, width=400)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)
        
        # Status Label
        self.status_label = ctk.CTkLabel(loading_frame, text="Initialisiere...",
                                        font=ctk.CTkFont(size=12),
                                        text_color="gray")
        self.status_label.pack(pady=5)
        
        # Detaillierter Status
        self.detail_label = ctk.CTkLabel(loading_frame, text="",
                                        font=ctk.CTkFont(size=10),
                                        text_color="darkgray")
        self.detail_label.pack(pady=2)
    
    def update_status(self, status: str, progress: float, detail: str = ""):
        """
        Aktualisiert den Ladestatus.
        
        Args:
            status: Hauptstatus-Text
            progress: Fortschritt 0.0 - 1.0
            detail: Optionaler Detail-Text
        """
        self.status_label.configure(text=status)
        self.progress_bar.set(progress)
        if detail:
            self.detail_label.configure(text=detail)
        self.update_idletasks()


def initialize_main_window(loading_window: LoadingWindow, config: dict, customer_manager):
    """
    Initialisiert das Hauptfenster vollständig.
    
    Args:
        loading_window: Das Loading-Window für Status-Updates
        config: Konfigurationsdictionary
        customer_manager: CustomerManager-Instanz
        
    Returns:
        Vollständig initialisiertes MainWindow
    """
    from ui.main_window import MainWindow
    
    # Schritt 1: MainWindow erstellen (ohne GUI-Erstellung)
    loading_window.update_status("Erstelle Hauptfenster...", 0.1, "Initialisiere Komponenten")
    main_window = MainWindow(config, customer_manager, skip_gui_init=True)
    
    # Schritt 2: Tabview erstellen
    loading_window.update_status("Erstelle Tab-Struktur...", 0.15, "Tabview-System")
    main_window.tabview = ctk.CTkTabview(main_window, command=main_window.on_tab_change)
    
    # Tabs hinzufügen
    main_window.tabview.add("Einstellungen")
    main_window.tabview.add("Verarbeitung")
    main_window.tabview.add("Suche")
    main_window.tabview.add("Unklare Dokumente")
    main_window.tabview.add("Unklare Legacy-Aufträge")
    main_window.tabview.add("Virtuelle Kunden")
    main_window.tabview.add("Regex-Patterns")
    main_window.tabview.add("System")
    
    # Schritt 3: Einstellungen laden
    loading_window.update_status("⚙️  Lade Einstellungen...", 0.2, "Konfiguration und Pfade")
    main_window.create_settings_tab()
    main_window.tabs_created["Einstellungen"] = True
    
    # Schritt 4: Verarbeitung laden
    loading_window.update_status("📁 Lade Verarbeitung...", 0.3, "Scan- und Verarbeitungs-Funktionen")
    main_window.create_processing_tab()
    main_window.tabs_created["Verarbeitung"] = True
    
    # Schritt 5: Suche laden
    loading_window.update_status("🔍 Lade Suche...", 0.4, "Such-Interface")
    main_window.create_search_tab()
    main_window.tabs_created["Suche"] = True
    
    # Schritt 6: Such-Daten laden
    loading_window.update_status("📊 Lade Such-Daten...", 0.5, "Dokumenttypen und Jahre aus Datenbank")
    try:
        doc_types = ["Alle"] + main_window.document_index.get_all_document_types()
        years = ["Alle"] + [str(y) for y in main_window.document_index.get_all_years()]
        main_window._search_doc_types = doc_types
        main_window._search_years = years
        main_window.search_dokument_typ.configure(values=doc_types)
        main_window.search_jahr.configure(values=years)
        main_window.tabs_data_loaded["Suche"] = True
        loading_window.update_status("📊 Such-Daten geladen", 0.55, 
                                    f"{len(doc_types)-1} Dokumenttypen, {len(years)-1} Jahre")
    except Exception as e:
        print(f"Fehler beim Laden der Such-Daten: {e}")
        loading_window.update_status("📊 Such-Daten (Fehler)", 0.55, "Fallback zu Standard-Werten")
    
    # Schritt 7: Unklare Dokumente laden
    loading_window.update_status("⚠️  Lade Unklare Dokumente...", 0.6, "Nachbearbeitungs-Interface")
    main_window.create_unclear_tab()
    main_window.tabs_created["Unklare Dokumente"] = True
    
    # Schritt 8: Legacy-Aufträge laden
    loading_window.update_status("📜 Lade Legacy-Aufträge...", 0.7, "Lade unklare Legacy-Einträge")
    main_window.create_unclear_legacy_tab()
    main_window.tabs_created["Unklare Legacy-Aufträge"] = True
    
    try:
        unclear_legacy = main_window.document_index.get_unclear_legacy_entries()
        for doc in unclear_legacy:
            main_window._add_legacy_row(
                doc.get("ziel_pfad", ""),
                doc.get("kunden_name", "Unbekannt"),
                doc.get("auftrag_nr", "-"),
                doc.get("dokument_typ", "Unbekannt"),
                doc.get("kennzeichen", "-"),
                doc.get("fin", "-"),
                doc.get("confidence", 0.0),
                doc.get("hinweis", "")
            )
        main_window.tabs_data_loaded["Unklare Legacy-Aufträge"] = True
        loading_window.update_status("📜 Legacy-Aufträge geladen", 0.75, 
                                    f"{len(unclear_legacy)} unklare Einträge")
    except Exception as e:
        print(f"Fehler beim Laden der Legacy-Daten: {e}")
        loading_window.update_status("📜 Legacy-Aufträge (Fehler)", 0.75, "Fallback zu leerem Tab")
    
    # Schritt 9: Virtuelle Kunden laden
    loading_window.update_status("👥 Lade Virtuelle Kunden...", 0.8, "Virtuelle Kundennummern-Verwaltung")
    main_window.create_virtual_customers_tab()
    main_window.tabs_created["Virtuelle Kunden"] = True
    
    # Schritt 10: Regex-Patterns laden
    loading_window.update_status("🔤 Lade Regex-Patterns...", 0.85, "Konfigurierbare Suchmuster")
    main_window.create_patterns_tab()
    main_window.tabs_created["Regex-Patterns"] = True
    
    # Schritt 11: System laden
    loading_window.update_status("🔧 Lade System...", 0.9, "Backup, Updates und Wartung")
    main_window.create_system_tab()
    main_window.tabs_created["System"] = True
    
    # Schritt 12: Finalisierung
    loading_window.update_status("✓ Finalisiere GUI...", 0.95, "Vorbereitung abschließen")
    
    # Tabs packen
    main_window.tabview.pack(fill="both", expand=True, padx=10, pady=10)
    main_window.tabview.set("Verarbeitung")
    
    # Fertig!
    loading_window.update_status("✓ Bereit!", 1.0, "Alle Komponenten geladen")
    
    return main_window

"""
Dialog-Funktionen für Config-Vergleiche im Basis-Verzeichnis
"""
import customtkinter as ctk


def show_root_config_comparison_dialog(parent, differences: list, config_path: str):
    """
    Zeigt Dialog bei Unterschieden zwischen Programm-Config und Basis-Verzeichnis-Config.
    
    Args:
        parent: Parent-Window
        differences: Liste der Unterschiede
        config_path: Pfad zur config.json im Basis-Verzeichnis
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title("⚠️ Config-Unterschiede gefunden")
    dialog.geometry("700x400")
    dialog.transient(parent)
    dialog.grab_set()
    
    # Header
    header = ctk.CTkLabel(
        dialog,
        text="⚠️ Config im Basis-Verzeichnis unterscheidet sich",
        font=("Arial", 16, "bold"),
        text_color="orange"
    )
    header.pack(pady=15)
    
    info = ctk.CTkLabel(
        dialog,
        text=f"Die Config im Basis-Verzeichnis hat VORRANG!\nPfad: {config_path}",
        font=("Arial", 12)
    )
    info.pack(pady=5)
    
    # Unterschiede-Liste
    frame = ctk.CTkFrame(dialog)
    frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    textbox = ctk.CTkTextbox(frame, wrap="word", font=("Courier", 11))
    textbox.pack(fill="both", expand=True)
    
    textbox.insert("1.0", "Gefundene Unterschiede:\n\n")
    for diff in differences:
        textbox.insert("end", f"• {diff}\n")
    
    textbox.configure(state="disabled")
    
    # OK-Button
    btn = ctk.CTkButton(
        dialog,
        text="OK - Basis-Config wird verwendet",
        command=dialog.destroy,
        fg_color="green"
    )
    btn.pack(pady=15)
    
    dialog.mainloop()


def show_root_config_same_dialog(parent, config_path: str):
    """
    Zeigt Info-Dialog wenn Config im Basis-Verzeichnis identisch ist.
    
    Args:
        parent: Parent-Window
        config_path: Pfad zur config.json im Basis-Verzeichnis
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title("✅ Config gefunden - identisch")
    dialog.geometry("600x250")
    dialog.transient(parent)
    dialog.grab_set()
    
    # Header
    header = ctk.CTkLabel(
        dialog,
        text="✅ Config im Basis-Verzeichnis gefunden",
        font=("Arial", 16, "bold"),
        text_color="green"
    )
    header.pack(pady=15)
    
    info = ctk.CTkLabel(
        dialog,
        text=f"Die Config ist identisch mit den Programm-Einstellungen.\n\nPfad: {config_path}",
        font=("Arial", 12)
    )
    info.pack(pady=20)
    
    # OK-Button
    btn = ctk.CTkButton(
        dialog,
        text="OK",
        command=dialog.destroy,
        fg_color="green"
    )
    btn.pack(pady=15)
    
    dialog.mainloop()


def show_root_config_not_found_dialog(parent, archive_root: str):
    """
    Zeigt Info-Dialog wenn keine config.json im Basis-Verzeichnis existiert.
    Bietet an, die Config sofort zu speichern.
    
    Args:
        parent: Parent-Window
        archive_root: Pfad zum Basis-Verzeichnis
    
    Returns:
        True wenn Config gespeichert werden soll, False sonst
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title("ℹ️ Keine Config im Basis-Verzeichnis")
    dialog.geometry("650x300")
    dialog.transient(parent)
    dialog.grab_set()
    
    result = {"save": False}
    
    # Header
    header = ctk.CTkLabel(
        dialog,
        text="ℹ️ Keine config.json gefunden",
        font=("Arial", 16, "bold"),
        text_color="blue"
    )
    header.pack(pady=15)
    
    info = ctk.CTkLabel(
        dialog,
        text=f"Im Basis-Verzeichnis existiert keine config.json.\n\n"
             f"Pfad: {archive_root}\n\n"
             f"Möchtest du die aktuelle Programm-Config jetzt speichern?\n"
             f"(Empfohlen - damit beide Orte synchron sind)",
        font=("Arial", 12),
        justify="center"
    )
    info.pack(pady=20)
    
    # Button-Frame
    button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    button_frame.pack(pady=15)
    
    def on_save():
        result["save"] = True
        dialog.destroy()
    
    def on_later():
        result["save"] = False
        dialog.destroy()
    
    # Ja-Button (empfohlen)
    save_btn = ctk.CTkButton(
        button_frame,
        text="✅ Jetzt speichern (empfohlen)",
        command=on_save,
        fg_color="green",
        hover_color="darkgreen",
        width=200
    )
    save_btn.pack(side="left", padx=10)
    
    # Später-Button
    later_btn = ctk.CTkButton(
        button_frame,
        text="⏭️ Später",
        command=on_later,
        fg_color="gray",
        hover_color="darkgray",
        width=150
    )
    later_btn.pack(side="left", padx=10)
    
    parent.wait_window(dialog)
    return result["save"]

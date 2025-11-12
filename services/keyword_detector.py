"""
Keyword Detector
Erkennt Schlagwörter in Dokumenten für erweiterte Suchfunktionen
"""

import os
import json
import re
from typing import List, Dict, Any, Set


class KeywordDetector:
    """Erkennt konfigurierbare Schlagwörter in Dokumenten."""
    
    def __init__(self, config_path: str = "config/keywords.json"):
        """
        Initialisiert den KeywordDetector.
        
        Args:
            config_path: Pfad zur Schlagwort-Konfiguration
        """
        self.config_path = config_path
        self.categories: Dict[str, Dict[str, Any]] = {}
        self.active_keywords: Dict[str, List[str]] = {}
        self.load_config()
    
    def load_config(self) -> bool:
        """
        Lädt Schlagwort-Konfiguration aus JSON-Datei.
        
        Returns:
            bool: True wenn erfolgreich geladen
        """
        try:
            if not os.path.exists(self.config_path):
                print(f"Warnung: {self.config_path} nicht gefunden. Keine Schlagwort-Erkennung aktiv.")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.categories = config.get("kategorien", {})
            
            # Lade nur aktive Kategorien
            self.active_keywords = {}
            for category, data in self.categories.items():
                if data.get("aktiv", False):
                    self.active_keywords[category] = [
                        kw.lower() for kw in data.get("schlagwoerter", [])
                    ]
            
            active_count = len(self.active_keywords)
            total_count = len(self.categories)
            print(f"✓ Schlagwort-Erkennung geladen: {active_count}/{total_count} Kategorien aktiv")
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Laden der Schlagwort-Konfiguration: {e}")
            return False
    
    def detect_keywords(self, text: str, min_confidence: float = 0.8) -> List[Dict[str, Any]]:
        """
        Erkennt Schlagwörter im Text.
        
        Args:
            text: Zu durchsuchender Text
            min_confidence: Minimale Konfidenz (0.0-1.0)
            
        Returns:
            Liste von erkannten Schlagwörtern mit Metadaten
            [{"kategorie": "...", "treffer": [...], "konfidenz": 0.9}, ...]
        """
        if not self.active_keywords:
            return []
        
        text_lower = text.lower()
        results = []
        
        for category, keywords in self.active_keywords.items():
            matches = []
            
            for keyword in keywords:
                # Suche nach Schlagwort (mit Wortgrenzen für bessere Treffer)
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    matches.append(keyword)
            
            if matches:
                # Berechne Konfidenz (je mehr Treffer, desto höher)
                confidence = min(1.0, len(matches) / len(keywords) + 0.5)
                
                if confidence >= min_confidence:
                    results.append({
                        "kategorie": category,
                        "treffer": matches,
                        "anzahl": len(matches),
                        "konfidenz": round(confidence, 2),
                        "beschreibung": self.categories[category].get("beschreibung", "")
                    })
        
        # Sortiere nach Konfidenz (höchste zuerst)
        results.sort(key=lambda x: x["konfidenz"], reverse=True)
        
        return results
    
    def detect_simple(self, text: str) -> List[str]:
        """
        Vereinfachte Erkennung - gibt nur Kategorie-Namen zurück.
        
        Args:
            text: Zu durchsuchender Text
            
        Returns:
            Liste von Kategorie-Namen
        """
        results = self.detect_keywords(text)
        return [r["kategorie"] for r in results]
    
    def get_active_categories(self) -> List[str]:
        """
        Gibt Liste aller aktiven Kategorien zurück.
        
        Returns:
            Liste von Kategorie-Namen
        """
        return list(self.active_keywords.keys())
    
    def get_all_categories(self) -> List[str]:
        """
        Gibt Liste aller Kategorien zurück (aktiv + inaktiv).
        
        Returns:
            Liste von Kategorie-Namen
        """
        return list(self.categories.keys())
    
    def get_category_info(self, category: str) -> Dict[str, Any]:
        """
        Gibt Informationen zu einer Kategorie zurück.
        
        Args:
            category: Kategorie-Name
            
        Returns:
            Dictionary mit Kategorie-Infos
        """
        if category in self.categories:
            return self.categories[category]
        return {}
    
    def is_active(self, category: str) -> bool:
        """
        Prüft ob Kategorie aktiv ist.
        
        Args:
            category: Kategorie-Name
            
        Returns:
            bool: True wenn aktiv
        """
        return category in self.active_keywords
    
    def activate_category(self, category: str) -> bool:
        """
        Aktiviert eine Kategorie.
        
        Args:
            category: Kategorie-Name
            
        Returns:
            bool: True wenn erfolgreich
        """
        if category not in self.categories:
            return False
        
        self.categories[category]["aktiv"] = True
        self.active_keywords[category] = [
            kw.lower() for kw in self.categories[category].get("schlagwoerter", [])
        ]
        
        return self.save_config()
    
    def deactivate_category(self, category: str) -> bool:
        """
        Deaktiviert eine Kategorie.
        
        Args:
            category: Kategorie-Name
            
        Returns:
            bool: True wenn erfolgreich
        """
        if category not in self.categories:
            return False
        
        self.categories[category]["aktiv"] = False
        if category in self.active_keywords:
            del self.active_keywords[category]
        
        return self.save_config()
    
    def save_config(self) -> bool:
        """
        Speichert aktuelle Konfiguration zurück in JSON-Datei.
        
        Returns:
            bool: True wenn erfolgreich
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            config["kategorien"] = self.categories
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Speichern der Schlagwort-Konfiguration: {e}")
            return False
    
    def add_keyword(self, category: str, keyword: str) -> bool:
        """
        Fügt Schlagwort zu einer Kategorie hinzu.
        
        Args:
            category: Kategorie-Name
            keyword: Neues Schlagwort
            
        Returns:
            bool: True wenn erfolgreich
        """
        if category not in self.categories:
            return False
        
        keyword_lower = keyword.lower()
        
        # Füge zu Kategorie hinzu
        if keyword_lower not in self.categories[category]["schlagwoerter"]:
            self.categories[category]["schlagwoerter"].append(keyword_lower)
        
        # Update aktive Keywords wenn Kategorie aktiv
        if category in self.active_keywords:
            if keyword_lower not in self.active_keywords[category]:
                self.active_keywords[category].append(keyword_lower)
        
        return self.save_config()
    
    def remove_keyword(self, category: str, keyword: str) -> bool:
        """
        Entfernt Schlagwort aus einer Kategorie.
        
        Args:
            category: Kategorie-Name
            keyword: Zu entfernendes Schlagwort
            
        Returns:
            bool: True wenn erfolgreich
        """
        if category not in self.categories:
            return False
        
        keyword_lower = keyword.lower()
        
        # Entferne aus Kategorie
        if keyword_lower in self.categories[category]["schlagwoerter"]:
            self.categories[category]["schlagwoerter"].remove(keyword_lower)
        
        # Update aktive Keywords wenn Kategorie aktiv
        if category in self.active_keywords:
            if keyword_lower in self.active_keywords[category]:
                self.active_keywords[category].remove(keyword_lower)
        
        return self.save_config()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken zur Schlagwort-Konfiguration zurück.
        
        Returns:
            Dictionary mit Statistiken
        """
        total_categories = len(self.categories)
        active_categories = len(self.active_keywords)
        total_keywords = sum(len(data.get("schlagwoerter", [])) 
                            for data in self.categories.values())
        active_keywords = sum(len(kws) for kws in self.active_keywords.values())
        
        return {
            "total_categories": total_categories,
            "active_categories": active_categories,
            "inactive_categories": total_categories - active_categories,
            "total_keywords": total_keywords,
            "active_keywords": active_keywords,
            "categories": {
                cat: {
                    "aktiv": data.get("aktiv", False),
                    "anzahl_keywords": len(data.get("schlagwoerter", []))
                }
                for cat, data in self.categories.items()
            }
        }

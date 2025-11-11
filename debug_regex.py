#!/usr/bin/env python3
"""
Debug-Script für Regex-Pattern-Tests
"""

import re

# Test-Text aus der Schultze.pdf
text = """
Frau
Anne Schultze
Schillerstr.23
01968 Senftenberg
KUNDE WARTET!
Datum: 07.10.2025 - 16:24 Uhr
Berater: Sven Hube
Werkstatt - Auftrag Nr.     11
Kd.Nr.:   28307
Seite:   1
"""

print("="*80)
print("REGEX PATTERN DEBUGGING")
print("="*80)

# Teste verschiedene Pattern
patterns = {
    "Kundennummer (alt)": r"Kunde[-\s]*Nr[:\s]+(\d+)",
    "Kundennummer (neu)": r"(?:Kunde(?:n)?[-\s]*(?:Nr|nummer)|Kd\.?[-\s]*Nr\.?)[:\s]+(\d+)",
    "Kundennummer (simpel)": r"Kd\.Nr\.:?\s+(\d+)",
    
    "Auftragsnummer (alt)": r"Auftrag[-\s]*Nr[:\s]+(\d+)",
    "Auftragsnummer (neu)": r"(?:Werkstatt[-\s]*)?Auftrag(?:s)?[-\s]*(?:Nr|nummer)\.?[:\s]+(\d+)",
    "Auftragsnummer (simpel)": r"Auftrag\s+Nr\.\s+(\d+)",
}

for name, pattern in patterns.items():
    print(f"\n{name}:")
    print(f"Pattern: {pattern}")
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        print(f"✅ GEFUNDEN: {match.group(1)}")
    else:
        print(f"❌ Nicht gefunden")

# Zeige auch die exakten Zeilen
print("\n" + "="*80)
print("RELEVANTE ZEILEN IM TEXT:")
print("="*80)
for line in text.split('\n'):
    if 'Kd.' in line or 'Auftrag' in line:
        print(f"'{line}'")

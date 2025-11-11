#!/usr/bin/env python3
"""
Direkter Test der analyzer-Funktionen
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.analyzer import (
    extract_kunden_nr, 
    extract_auftrag_nr,
    PATTERN_KUNDEN_NR,
    PATTERN_AUFTRAG_NR
)

# Test-Text
text = """
Werkstatt - Auftrag Nr.     11
Kd.Nr.:   28307
"""

print("="*80)
print("DIREKTER FUNKTIONS-TEST")
print("="*80)

print(f"\nAktuelles PATTERN_KUNDEN_NR: {PATTERN_KUNDEN_NR}")
print(f"Aktuelles PATTERN_AUFTRAG_NR: {PATTERN_AUFTRAG_NR}")

print(f"\nTest-Text:")
print(repr(text))

kunden_nr = extract_kunden_nr(text)
auftrag_nr = extract_auftrag_nr(text)

print(f"\n✅ Kundennummer gefunden: {kunden_nr}")
print(f"✅ Auftragsnummer gefunden: {auftrag_nr}")

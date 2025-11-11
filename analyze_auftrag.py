#!/usr/bin/env python3
"""
Detaillierte Analyse der auftrag.pdf
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.analyzer import extract_text

pdf_path = "beispiel_auftraege/auftrag.pdf"

print("="*80)
print("DETAILLIERTE ANALYSE: auftrag.pdf")
print("="*80)

text = extract_text(pdf_path)

print(f"\nGesamtlänge: {len(text)} Zeichen\n")
print("VOLLSTÄNDIGER TEXT:")
print("="*80)
print(text)
print("="*80)

# Suche nach relevanten Zeilen
print("\nRELEVANTE ZEILEN MIT NUMMERN:")
print("-"*80)
for i, line in enumerate(text.split('\n'), 1):
    line_clean = line.strip()
    if any(keyword in line_clean.lower() for keyword in ['nummer', 'nr', 'datum', 'kunde', 'auftrag', 'kd']):
        print(f"{i:3d}: {line}")

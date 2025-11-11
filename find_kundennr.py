import fitz

pdf = fitz.open("beispiel_auftraege/auftrag.pdf")
text = ""
for page in pdf:
    text += page.get_text()
pdf.close()

# Suche nach Kundennummer-Feldern
lines = text.split('\n')
print("SUCHE NACH KUNDENNUMMER-HINWEISEN:")
print("="*80)
for i, line in enumerate(lines):
    if any(keyword in line.lower() for keyword in ['kunde', 'kunden', 'kd']):
        print(f"Zeile {i}: '{line}'")

print("\n" + "="*80)
print("ALLE ZEILEN 1-20 (Feld-Bereich):")
print("="*80)
for i in range(0, min(20, len(lines))):
    print(f"{i:3d}: '{lines[i]}'")

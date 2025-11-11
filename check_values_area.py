import fitz

pdf = fitz.open("beispiel_auftraege/auftrag.pdf")
text = ""
for page in pdf:
    text += page.get_text()
pdf.close()

# Zeige den Text zwischen Zeile 78 und 100
lines = text.split('\n')
print("ZEILEN 78-100 (Werte-Bereich):")
print("="*80)
for i in range(78, min(100, len(lines))):
    print(f"{i:3d}: '{lines[i]}'")

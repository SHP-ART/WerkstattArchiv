import fitz

pdf = fitz.open("beispiel_auftraege/auftrag.pdf")
text = ""
for page in pdf:
    text += page.get_text()
pdf.close()

# Finde Position der Auftragsnummer
lines = text.split('\n')
for i, line in enumerate(lines):
    if 'Auftragsnummer' in line:
        print(f"Zeile {i}: '{line}'")
        # Zeige die nächsten 10 Zeilen
        for j in range(i+1, min(i+11, len(lines))):
            print(f"Zeile {j}: '{lines[j]}'")
        break

print("\n" + "="*80)
print("Suche nach 78708:")
for i, line in enumerate(lines):
    if '78708' in line:
        print(f"Zeile {i}: '{line}'")
        # Zeige Kontext
        for j in range(max(0, i-2), min(i+3, len(lines))):
            print(f"  Zeile {j}: '{lines[j]}'")

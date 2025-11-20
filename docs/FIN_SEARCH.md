# FIN/VIN-Suche - Dokumentation

## 🎯 Feature: Flexible Fahrgestellnummer-Suche

Die Dokumentensuche unterstützt jetzt die **flexible Suche nach FIN/VIN** (Fahrgestellnummer).

## ✨ Funktionsweise

### Intelligente Suche

Die Suche erkennt automatisch, ob eine **kurze** oder **komplette** FIN eingegeben wurde:

#### 1️⃣ Kurze Eingabe (≤ 8 Zeichen)
- **Beispiel:** `12345678`
- **Suche:** In den **letzten 8 Zeichen** der gespeicherten FIN
- **Findet:** `WDB1234567890012345678` ✓
- **SQL:** `WHERE fin = '12345678' OR SUBSTR(fin, -8) = '12345678'`

#### 2️⃣ Komplette FIN (> 8 Zeichen)
- **Beispiel:** `WDB1234567890012345678`
- **Suche:** Exakte FIN oder als Teilstring
- **Findet:** `WDB1234567890012345678` ✓
- **SQL:** `WHERE fin LIKE '%WDB1234567890012345678%'`

#### 3️⃣ Automatische Normalisierung
- Eingabe wird **getrimmt** (Leerzeichen entfernt)
- Konvertiert zu **GROSSBUCHSTABEN**
- `"  wdb1234  "` → `"WDB1234"`

## 🖥️ GUI-Integration

### Neues Suchfeld

In der **Dokumentensuche** (Tab "Suche"):

```
┌─────────────────────────────────────┐
│  Dokumentensuche                    │
├─────────────────────────────────────┤
│  Kundennr:  [_______]  Name: [____] │
│  Auftragsnr:[_______]  Datei:[____] │
│  FIN/VIN:   [Letzte 8 oder komplett]│  ← NEU!
│  Typ:       [▼ Alle]   Jahr: [▼   ] │
│                                      │
│  [🔍 Suchen] [Zurücksetzen]         │
└─────────────────────────────────────┘
```

- **Label:** "FIN/VIN:"
- **Placeholder:** "Letzte 8 oder komplett"
- **Position:** Nach Dateiname, vor Dokumenttyp

## 📋 Anwendungsfälle

### Beispiel 1: Schnelle Suche mit kurzer FIN
```
Benutzer gibt ein: "45678901"
System findet:
  - WDB1234567890045678901
  - ABC9876543210045678901
```

### Beispiel 2: Präzise Suche mit kompletter FIN
```
Benutzer gibt ein: "WDB1234567890045678901"
System findet:
  - WDB1234567890045678901 (exakt)
```

### Beispiel 3: Teil-FIN Suche
```
Benutzer gibt ein: "234567890"
System findet:
  - WDB1234567890012345678 (enthält Teilstring)
```

## ⚡ Performance

- **Optimiert:** `SUBSTR(fin, -8)` statt Python-String-Operations
- **Index:** `idx_fin` auf `dokumente(fin)` für schnelle Suche
- **Keine Performance-Einbußen** bei großen Datenbanken

## 🧪 Testing

Test-Script ausführen:
```bash
python test_fin_search.py
```

Testet:
- ✅ Suche mit letzten 8 Zeichen
- ✅ Suche mit kompletter FIN
- ✅ Suche mit Teil-FIN
- ✅ Normalisierung (Groß-/Kleinschreibung)

## 📊 Datenbank

### Gespeicherte Daten
```sql
SELECT fin FROM dokumente;

-- Beispiele:
-- WDB1234567890012345678  (17-stellig, Mercedes)
-- ABC9876543210098765432  (17-stellig, generisch)
-- 12345678                (8-stellig, kurz)
```

### Suche-Query
```sql
-- Bei Eingabe ≤ 8 Zeichen:
SELECT * FROM dokumente 
WHERE fin = '12345678' 
   OR SUBSTR(fin, -8) = '12345678';

-- Bei Eingabe > 8 Zeichen:
SELECT * FROM dokumente 
WHERE fin LIKE '%WDB123456789%';
```

## ✅ Vorteile

1. **Benutzerfreundlich:**
   - Nur letzte 8 Zeichen eingeben genügt
   - Komplette FIN funktioniert auch
   - Kein Nachdenken über Länge nötig

2. **Flexibel:**
   - Findet immer den richtigen Treffer
   - Egal ob kurz oder lang
   - Teil-FIN-Suche möglich

3. **Performance:**
   - Optimierte SQL-Queries
   - Index auf `fin`-Spalte
   - Schnelle Suche auch bei vielen Dokumenten

4. **Praktisch:**
   - Letzte 8 Zeichen sind oft auf Dokumenten
   - Schneller zu tippen
   - Weniger Fehleranfällig

## 🔧 Implementierung

### Geänderte Dateien

1. **`ui/main_window.py`** (+5 Zeilen)
   - Neues Suchfeld `self.search_fin`
   - Integration in `perform_search()`
   - Integration in `clear_search()`

2. **`services/indexer.py`** (+25 Zeilen)
   - Neuer Parameter `fin` in `search()`
   - Intelligente FIN-Suche-Logik
   - Normalisierung (trim, upper)

3. **`test_fin_search.py`** (NEU)
   - Test-Script für FIN-Suche
   - Demonstriert alle Funktionen

## 🚀 Zukünftige Erweiterungen

Mögliche weitere Features:
- **FIN-Validierung:** Prüfe ob FIN gültig (17 Zeichen, Check-Digit)
- **Auto-Complete:** Vorschläge während Eingabe
- **Fuzzy-Search:** Finde ähnliche FINs bei Tippfehlern
- **FIN-Historie:** Zeige alle Dokumente zu einem Fahrzeug

## 📚 Weitere Infos

- **FIN-Format:** 17-stellige Fahrzeug-Identifikationsnummer (ISO 3779)
- **Letzte 8 Zeichen:** Oft auf Rechnungen/Dokumenten sichtbar
- **Hersteller-Code:** Erste 3 Zeichen (WDB = Mercedes, etc.)

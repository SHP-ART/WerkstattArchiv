# EasyOCR Setup - Tesseract Alternative

## Was ist EasyOCR?

**EasyOCR** ist eine reine Python-basierte OCR-Bibliothek, die **keine externe Installation** benötigt (im Gegensatz zu Tesseract). Sie funktioniert auf allen Plattformen (Windows, macOS, Linux) ohne zusätzliche Tools.

## Vorteile gegenüber Tesseract

✅ **Keine externe Installation nötig** - Alles ist in Python
✅ **Funktioniert auf Windows ohne Probleme** - Keine Pfad-Konfiguration
✅ **Bessere Erkennung** - Moderne Deep Learning Modelle
✅ **Einfache Installation** - Nur `pip install easyocr`
✅ **Automatischer Fallback** - Programm wählt beste verfügbare Engine

## Installation

### Schritt 1: Aktiviere Virtual Environment (falls nicht aktiv)

**Windows:**
```cmd
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### Schritt 2: Installiere EasyOCR

```bash
pip install easyocr
```

⚠️ **Hinweis:** Die Installation lädt ca. 150-200 MB an Bibliotheken (PyTorch, OpenCV, etc.). Dies kann einige Minuten dauern.

### Schritt 3: Teste die Installation

Starte das Programm - es sollte automatisch EasyOCR erkennen:

```
✅ EasyOCR verfügbar - verwende Python-basierte OCR (keine externe Installation nötig)
```

## Automatische Engine-Auswahl

Das Programm wählt automatisch die beste verfügbare OCR-Engine:

1. **EasyOCR** (bevorzugt) - Wenn installiert
2. **Tesseract** (Fallback) - Wenn EasyOCR nicht verfügbar
3. **Keine OCR** - Wenn weder EasyOCR noch Tesseract verfügbar

## OCR-Status prüfen

Im Programm-Log beim Start siehst du welche Engine verwendet wird:

```
✅ EasyOCR verfügbar - verwende Python-basierte OCR (keine externe Installation nötig)
```

oder

```
✅ Tesseract verfügbar
```

oder

```
❌ Keine OCR-Engine verfügbar. Installiere: pip install easyocr
```

## GPU-Unterstützung (Optional)

EasyOCR kann GPU-Beschleunigung nutzen, ist aber standardmäßig auf CPU-Modus eingestellt (funktioniert überall).

Für GPU-Beschleunigung (nur bei NVIDIA-Grafikkarten):
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## Tesseract entfernen (Optional)

Falls du Tesseract nicht mehr brauchst:

**Windows:**
1. Systemsteuerung → Programme → Tesseract-OCR deinstallieren
2. In config.json: `"tesseract_path": null` setzen

**macOS:**
```bash
brew uninstall tesseract
```

## Fehlerbehebung

### "No module named 'easyocr'"

→ EasyOCR nicht installiert oder falsches Virtual Environment aktiv
```bash
pip install easyocr
```

### Installation dauert sehr lange

→ Normal! PyTorch ist groß (~150 MB). Warte bis Installation fertig ist.

### "CUDA not available" Warnung

→ Kann ignoriert werden! EasyOCR läuft auf CPU (gpu=False ist Standard).

## Vergleich: EasyOCR vs Tesseract

| Feature | EasyOCR | Tesseract |
|---------|---------|-----------|
| Installation | `pip install` | Externes Tool + Pfad-Konfiguration |
| Windows | ✅ Funktioniert sofort | ❌ Oft Probleme mit Pfaden |
| Genauigkeit | ⭐⭐⭐⭐⭐ Modern | ⭐⭐⭐⭐ Gut |
| Geschwindigkeit | Mittel (Deep Learning) | Schnell (klassisch) |
| Sprachen | 80+ Sprachen | 100+ Sprachen |
| Größe | ~200 MB | ~50 MB |

## Empfehlung

✅ **Für Windows-Nutzer:** Verwende EasyOCR (keine Probleme mit Tesseract-Installation)
✅ **Für macOS/Linux:** Beide Engines funktionieren gut, EasyOCR ist einfacher
✅ **Für beste Qualität:** EasyOCR
✅ **Für beste Geschwindigkeit:** Tesseract (falls bereits installiert)

Das Programm wählt automatisch die beste verfügbare Engine - du musst nichts konfigurieren! 🎉

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WerkstattArchiv is a local Python desktop application for automatic management of workshop documents. It analyzes PDFs and images using OCR, extracts metadata (customer numbers, order numbers, dates, VINs, etc.), and organizes them into a structured folder hierarchy.

**Current Version:** 0.8.0

## Running the Application

### Development
```bash
# Start the application
python3 main.py

# For macOS (if python3 is default)
python main.py
```

### Configuration
The application uses `config.json` for paths. On first run, it creates a default configuration. Key settings:
- `root_dir`: Base directory for organized documents
- `input_dir`: Incoming documents folder (watched for new files)
- `unclear_dir`: Documents that couldn't be auto-classified
- `customers_file`: Customer database CSV (auto-created)
- `tesseract_path`: Path to Tesseract OCR (optional on macOS/Linux)

### Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt

# macOS specific: Install Tesseract OCR
brew install tesseract tesseract-lang
```

**Required:** Python 3.11+
**Key libraries:** customtkinter (GUI), PyMuPDF (PDF processing), pytesseract (OCR), watchdog (file monitoring)

## Architecture

### Core Document Processing Flow

1. **Document Intake** (`services/analyzer.py`)
   - Extracts text from PDFs (PyMuPDF) or runs OCR on images (pytesseract)
   - Uses configurable regex patterns to extract metadata (customer number, order number, date, VIN, license plate, etc.)
   - Determines document type (Invoice, Quote, Order, etc.)
   - Calculates confidence score (0.0-1.0)

2. **Legacy Document Resolution** (`services/legacy_resolver.py`)
   - Handles old documents without customer numbers
   - Uses **strict deterministic rules** (no fuzzy matching, no AI):
     - **Rule A:** VIN match in vehicle index → auto-assign customer
     - **Rule B:** Exact name + (PLZ OR street) match → auto-assign customer
     - **Otherwise:** Mark as "unclear" for manual assignment
   - Builds vehicle index (`data/vehicles.csv`) linking VINs to customers

3. **Document Routing** (`services/router.py`)
   - Constructs target paths based on analysis results:
     - **Normal:** `[ROOT]/Kunde/[Nr] - [Name]/[Year]/[OrderNr]_[Type].pdf`
     - **Legacy (assigned):** `[ROOT]/Kunde/[Nr] - [Name]/[Year]/[OrderNr]_Altauftrag_[Date]_[VIN]_[Name].pdf`
     - **Legacy (unclear):** `[ROOT]/Altbestand/Unklar/[Year]/[OrderNr]_Altauftrag_Unklar_[Date]_[VIN/NA]_[Name].pdf`
   - Moves files to target location and creates folders as needed

4. **Indexing** (`services/indexer.py`)
   - SQLite database (`werkstatt_index.db`) with two tables:
     - `dokumente`: All processed documents with metadata
     - `unclear_legacy`: Legacy documents awaiting manual assignment
   - Provides search and statistics functionality

### Supporting Services

- **Customer Management** (`services/customers.py`): Loads/manages customer database (CSV), auto-adds new customers from documents
- **Vehicle Management** (`services/vehicles.py`): Maintains VIN-to-customer mapping for legacy resolution
- **Pattern Manager** (`services/pattern_manager.py`): Configurable regex patterns stored in `patterns.json`
- **Watchdog Service** (`services/watchdog_service.py`): Monitors input directory for new files, auto-processes them
- **Backup Manager** (`services/backup_manager.py`): Creates/restores ZIP backups of config, database, and CSV files
- **Updater** (`services/updater.py`): Auto-update system that checks GitHub releases and installs updates
- **Template Manager** (`services/vorlagen.py`): Manages different document template types
- **Filename Generator** (`services/filename_generator.py`): Creates standardized filenames with timestamp
- **Logger** (`services/logger.py`): Logging service for all operations

### GUI Structure

Single window application (`ui/main_window.py`) with tabbed interface:
1. **Einstellungen (Settings):** Configure paths, load customer database
2. **Verarbeitung (Processing):** Scan input folder or start auto-watch
3. **Suche (Search):** Search indexed documents by various criteria
4. **Unklare Dokumente (Unclear Docs):** Manual review of low-confidence documents
5. **Unklare Legacy-Aufträge (Unclear Legacy):** Manual assignment of legacy documents
6. **Regex-Patterns:** Configure extraction patterns with built-in tester
7. **System:** Backup/restore, auto-update

## Database Schema

### `dokumente` Table
Stores all processed documents with full metadata: file paths, order data (number, date, type, year), customer data (number, name), vehicle data (VIN, license plate, mileage), legacy info (is_legacy flag, match_reason), quality metrics (confidence, status, notes), and timestamps.

### `unclear_legacy` Table
Temporary storage for legacy documents awaiting manual assignment. Contains similar fields plus `match_reason` (why it's unclear: "unclear", "multiple_fin_matches", "no_details") and `status` ("offen", "zugeordnet").

## Testing

Test files are present but no formal test framework is configured:
- `test_legacy.py`: Legacy resolution tests
- `test_texterkennung.py`: Text extraction tests
- `test_erweitert.py`: Extended functionality tests
- `test_gui_integration.py`: GUI integration tests

Run tests directly: `python3 test_legacy.py`

## Key Design Principles

1. **No Cloud Services:** Fully local processing, no external APIs (except GitHub for updates)
2. **Strict Determinism:** Legacy resolution uses exact matching only - no fuzzy logic, no ML, no guessing
3. **Transparency:** All operations logged, confidence scores shown, unclear cases flagged for manual review
4. **Configurability:** Regex patterns, templates, and paths all user-configurable
5. **Data Safety:** Automatic backups before updates, vehicle index tracks all assignments

## Common Operations

### Adding Support for New Document Fields
1. Add regex pattern to `patterns.json` (or via GUI)
2. Update `services/analyzer.py` to extract the field
3. Update database schema in `services/indexer.py` if storing it
4. Update router logic in `services/router.py` if it affects file placement

### Modifying Legacy Resolution Rules
All logic is in `services/legacy_resolver.py`. The system follows strict rules - avoid adding fuzzy matching or probabilistic logic. If adding new rules, they must be deterministic and 100% certain.

### Debugging Document Processing
1. Check `WerkstattArchiv_log.txt` for processing logs
2. Use debug scripts: `debug_analyzer.py`, `analyze_auftrag.py`
3. Test regex patterns in GUI's "Regex-Patterns" tab with pattern tester
4. Check confidence scores in database or GUI search results

### File Naming Conventions
Generated by `services/filename_generator.py`:
- Normal: `[OrderNr]_[Type]_[Date]_[Timestamp].pdf`
- Legacy: `[OrderNr]_Altauftrag_[Date]_[VIN]_[Name]_[Timestamp].pdf`
- Unclear: `[OrderNr]_Altauftrag_Unklar_[Date]_[VIN/NA]_[Name]_[Timestamp].pdf`

Timestamps use `YYYYMMDD_HHMMSS` format to ensure uniqueness.

## SSL Certificate Issues (macOS)

The application may encounter SSL certificate errors on macOS when checking for updates. This is handled in `services/updater.py` by using a fallback SSL context if certificate verification fails. This is a known issue with Python on macOS and the GitHub API.

## Version Management

Version is stored in `version.py` with three fields:
- `__version__`: Semantic version (e.g., "0.8.0")
- `__app_name__`: "WerkstattArchiv"
- `__description__`: Brief description

Update this file when releasing new versions. The auto-updater compares versions semantically.

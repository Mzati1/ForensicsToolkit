# Developer Guide

This document explains the architecture and module responsibilities of the WhatsApp Forensics Toolkit.

## Architecture Overview

The toolkit is modular, with distinct components for each stage of the forensic process.

### Core Modules (`src/`)

1.  **Acquisition (`src/acquisition/`)**
    -   `acquirer.py`: Handles data acquisition.
    -   `WhatsAppAcquirer`: Main class.
    -   **Methods**:
        -   `acquire_from_android_adb()`: Uses `adb` commands to pull data from connected Android devices. Handles root and non-root access.
        -   `acquire_from_files()`: Copies WhatsApp data from a local directory.
        -   `verify_database()`: Checks if a file is a valid SQLite database.

2.  **Cryptography (`src/crypto/`)**
    -   `decryptor.py`: Handles database decryption.
    -   `WhatsAppDecryptor`: Main class.
    -   **Features**:
        -   Detects encryption type (crypt12, crypt14, crypt15).
        -   Decrypts using AES-GCM (via `pycryptodome`).
        -   Handles key file loading and validation.

3.  **Parsing (`src/parsing/`)**
    -   `parser.py`: Parses SQLite databases.
    -   `WhatsAppParser`: Main class.
    -   **Functionality**:
        -   Connects to `msgstore.db` and `wa.db` using `sqlite3`.
        -   Extracts chats, messages, contacts, and call logs.
        -   Returns data objects (`Chat`, `Message`, `Contact`, `CallLog`).

4.  **Reporting (`src/reporting/`)**
    -   `reporter.py`: Generates forensic reports.
    -   `WhatsAppReporter`: Main class.
    -   **Formats**:
        -   HTML: Interactive report with styling.
        -   PDF: Printable report (uses `reportlab`).
        -   JSON/CSV: Structured data for further analysis.

5.  **Forensics (`src/forensics/`)**
    -   `compliance.py`: Ensures forensic integrity.
    -   **Components**:
        -   `ChainOfCustody`: Logs evidence handling.
        -   `HashVerifier`: Calculates and verifies file hashes (MD5, SHA256).
        -   `AuditLogger`: Logs all user actions.

6.  **Integration (`src/integration/`)**
    -   `toolkit_integration.py`: High-level wrapper combining all modules.
    -   Used to orchestrate the full workflow with compliance tracking.

### Entry Point (`main.py`)

-   Parses CLI arguments using `argparse`.
-   Routes commands (`acquire`, `decrypt`, `parse`, `full`) to appropriate handlers.
-   Configures logging.

## Adding New Features

1.  **New Acquisition Source**: Add a method to `WhatsAppAcquirer` and update `main.py` CLI arguments.
2.  **New Report Format**: Add a method to `WhatsAppReporter` and update `ReportFormat` enum.
3.  **New Parser**: Extend `WhatsAppParser` to extract additional tables or fields.

## Testing

Run tests using `pytest`:
```bash
python -m pytest
```
Tests are located in `tests/` directory and cover all core modules.

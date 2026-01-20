# How The Toolkit Works

This document explains what each part of the toolkit does and how it works together.

## Architecture Overview

The toolkit has 4 main modules plus forensic compliance features:

1. **Acquisition** - Gets WhatsApp data from sources
2. **Crypto** - Decrypts encrypted databases
3. **Parsing** - Extracts data from databases
4. **Reporting** - Generates forensic reports
5. **Forensics** - Chain of custody, hash verification, audit logging

## Module Details

### Acquisition Module (`src/acquisition/`)

**What it does:**
- Gets WhatsApp databases and files from Android devices, local files, or backups
- Supports ADB (Android Debug Bridge) for device extraction
- Supports file system acquisition from local directories

**How it works:**
- For ADB: Uses `adb pull` to extract databases from standard WhatsApp paths on Android
- For files: Recursively searches directories for WhatsApp database files
- Verifies SQLite database integrity
- Creates acquisition summary

**Files:**
- `acquirer.py` - Main acquisition class

### Crypto Module (`src/crypto/`)

**What it does:**
- Decrypts WhatsApp encrypted databases (crypt12, crypt14, crypt15)
- Detects encryption type automatically
- Handles key file loading

**How it works:**
- Loads encryption key from key file (usually at offset 126)
- Detects encryption type from file extension or content
- Uses AES-GCM mode for decryption
- Decompresses decrypted data with zlib

**Files:**
- `decryptor.py` - Decryption class

**Note:** Crypt15 support is basic. Full support requires WhatsApp-Crypt14-Crypt15-Decrypter library.

### Parsing Module (`src/parsing/`)

**What it does:**
- Extracts chats, messages, contacts, and call logs from WhatsApp databases
- Handles multiple database schemas (WhatsApp versions change over time)
- Links contacts to messages using wa.db

**How it works:**
- Connects to msgstore.db (main database)
- Optionally loads contacts from wa.db
- Queries database using SQL
- Supports both modern and older WhatsApp database schemas
- Returns structured data objects (Chat, Message, Contact, CallLog)

**Files:**
- `parser.py` - Main parser class

### Reporting Module (`src/reporting/`)

**What it does:**
- Generates forensic reports in HTML, JSON, and CSV formats
- Creates professional HTML reports with styling
- Exports structured data for analysis

**How it works:**
- Takes parsed data (chats, contacts, call logs)
- Formats data according to selected format
- HTML: Creates styled HTML with tables and chat bubbles
- JSON: Exports all data as structured JSON
- CSV: Creates separate CSV files for contacts, messages, calls

**Files:**
- `reporter.py` - Report generation class

### Forensics Module (`src/forensics/`)

**What it does:**
- Maintains chain of custody for legal admissibility
- Verifies evidence integrity with hash values
- Logs all actions for audit trail
- Checks compliance with forensic standards

**How it works:**

**Chain of Custody (`chain_of_custody.py`):**
- Tracks who handled evidence, when, and how
- Calculates MD5 and SHA256 hashes for all evidence
- Maintains custody chain log
- Generates chain of custody reports

**Hash Verification (`hash_verification.py`):**
- Calculates MD5, SHA256, SHA512 hashes
- Verifies file integrity at any time
- Compares files using hash values

**Audit Logger (`audit_logger.py`):**
- Logs every action with timestamp and user
- Records what resources were accessed
- Tracks success/failure of operations
- Generates audit reports

**Compliance Checker (`compliance.py`):**
- Checks ACPO principles compliance
- Verifies GDPR compliance
- Validates chain of custody requirements
- Generates compliance reports

## Integration (`src/integration/`)

**What it does:**
- Wraps all modules with forensic compliance
- Provides unified interface for forensic investigations
- Ensures compliance features are automatically applied

**How it works:**
- Creates chain of custody entries for all evidence
- Verifies hashes after acquisition and decryption
- Logs all actions in audit trail
- Checks compliance throughout process

**Files:**
- `toolkit_integration.py` - Main integration class

## Command Line Interface (`main.py`)

**What it does:**
- Provides command-line interface for all toolkit functions
- Supports individual commands or full workflow
- Handles command-line arguments and error handling

**Commands:**

1. **acquire** - Acquire WhatsApp data from source
   - `--source`: android_adb or file
   - `--input`: Input directory or device ID
   - `--output`: Output directory

2. **decrypt** - Decrypt encrypted database
   - `--input`: Encrypted database file
   - `--key`: Key file path
   - `--output`: Output decrypted database

3. **parse** - Parse database and generate reports
   - `--msgstore`: Path to msgstore.db
   - `--wa`: Path to wa.db (optional)
   - `--output`: Output directory
   - `--format`: html, json, csv, or all

4. **full** - Complete workflow
   - Combines acquire, decrypt, parse, and report
   - Includes all arguments from individual commands

## Existing Tools Integration

The toolkit builds on existing tools:

**Whapa Toolset (`tools/whapa/`):**
- `whapa.py` - Database parser (for reference)
- `whacipher.py` - Encryption/decryption (for reference)
- `whagodri.py` - Google Drive extractor (can be integrated)
- `whachat.py` - Chat exporter (can be integrated)

**WhatsApp Msgstore Viewer (`tools/whatsapp-msgstore-viewer/`):**
- Crypt15 decryption library
- Database viewer functionality

## Workflow Example

1. **Acquire**: Get WhatsApp data from device or files
2. **Add to Chain of Custody**: Track evidence with hashes
3. **Decrypt** (if needed): Decrypt encrypted databases
4. **Verify Integrity**: Check hashes match
5. **Parse**: Extract structured data
6. **Generate Reports**: Create HTML/JSON/CSV reports
7. **Generate Compliance Reports**: Chain of custody, audit, compliance

## Data Flow

```
Acquisition → Hash Calculation → Chain of Custody Entry
    ↓
Decryption (if needed) → Hash Verification
    ↓
Parsing → Structured Data Objects
    ↓
Reporting → HTML/JSON/CSV Reports
    ↓
Compliance Reports → Chain of Custody, Audit, Compliance
```

## Key Features

- **Non-destructive**: All operations work on copies
- **Hash verification**: Evidence integrity verified at every step
- **Audit trail**: Complete logging of all actions
- **Chain of custody**: Legal admissibility tracking
- **Compliance**: ACPO principles and GDPR compliance

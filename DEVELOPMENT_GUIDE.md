# WhatsApp Forensics Toolkit - Development Guide

This document explains how the toolkit works and how it was built. This guide will help you understand the architecture, pick up where development left off, and extend the functionality.

## Architecture Overview

The toolkit is organized into four main modules:

1. **Acquisition** (`src/acquisition/`): Handles data acquisition from various sources
2. **Crypto** (`src/crypto/`): Handles encryption/decryption of WhatsApp databases
3. **Parsing** (`src/parsing/`): Parses SQLite databases to extract structured data
4. **Reporting** (`src/reporting/`): Generates forensic reports in multiple formats

## Module Details

### Acquisition Module

**Location**: `src/acquisition/acquirer.py`

**Purpose**: Acquires WhatsApp data from Android devices (via ADB), local file systems, iOS backups, and Google Drive.

**Key Classes**:
- `WhatsAppAcquirer`: Main acquisition class
- `AcquisitionSource`: Enumeration of supported sources

**How it works**:
1. Initializes with an output directory for acquired data
2. For ADB acquisition:
   - Checks for connected Android devices
   - Uses `adb pull` to extract databases from standard WhatsApp paths
   - Handles encrypted databases (crypt12/14/15) and keys
3. For file acquisition:
   - Recursively searches directory for WhatsApp files
   - Copies databases, keys, and media directories
   - Validates SQLite databases

**Extension points**:
- Add iOS iTunes backup extraction in `acquire_from_ios_backup()`
- Add Google Drive backup extraction using `gpsoauth`
- Add support for additional file formats

### Crypto Module

**Location**: `src/crypto/decryptor.py`

**Purpose**: Decrypts WhatsApp encrypted databases (crypt12, crypt14, crypt15).

**Key Classes**:
- `WhatsAppDecryptor`: Main decryption class
- `EncryptionType`: Enumeration of encryption types

**How it works**:
1. Loads encryption key from key file (typically 158 bytes, key at offset 126)
2. Detects encryption type from file extension or content
3. For each encryption type:
   - **Crypt12**: Fixed header (51 bytes) + IV (16 bytes) + encrypted data + footer (20 bytes)
   - **Crypt14**: Variable header + IV (at offset 67:83) + encrypted data, tries offsets 185-195
   - **Crypt15**: Uses HMAC-SHA256 derivation, different header structure
4. Decrypts using AES-GCM mode
5. Decompresses using zlib

**Extension points**:
- Improve crypt15 support (currently basic implementation)
- Add encryption capability (currently only decrypt12 is implemented)
- Add support for key extraction from Android devices

### Parsing Module

**Location**: `src/parsing/parser.py`

**Purpose**: Parses WhatsApp SQLite databases to extract chats, messages, contacts, and call logs.

**Key Classes**:
- `WhatsAppParser`: Main parser class
- `Chat`: Represents a WhatsApp chat
- `Message`: Represents a message
- `Contact`: Represents a contact
- `CallLog`: Represents a call log entry

**How it works**:
1. Connects to msgstore.db (main message database) and optionally wa.db (contacts)
2. Loads contacts cache from wa.db for name resolution
3. Queries multiple possible schemas (WhatsApp database schema changes over time)
4. Extracts:
   - Chats: from `chat` or `chat_list` table, joined with `jid` table
   - Messages: from `message` or `messages` table
   - Contacts: from `wa_contacts`, `contacts`, or `user` table in wa.db
   - Call logs: from `call_log` or `calls` table
   - Group participants: from `group_participants` or `group_participant_user` table

**Extension points**:
- Add support for status messages/stories
- Add media file analysis and extraction
- Add deleted message recovery
- Add location data extraction
- Improve schema detection and compatibility

### Reporting Module

**Location**: `src/reporting/reporter.py`

**Purpose**: Generates forensic reports in HTML, JSON, and CSV formats.

**Key Classes**:
- `WhatsAppReporter`: Main reporter class
- `ReportFormat`: Enumeration of output formats

**How it works**:
1. Accepts parsed data (chats, contacts, call logs)
2. Generates metadata (company, examiner, date, notes)
3. For each format:
   - **HTML**: Creates styled HTML report with tables, chat messages, and summaries
   - **JSON**: Creates structured JSON with all data
   - **CSV**: Creates separate CSV files for contacts, messages, and calls
4. Saves reports to specified output directory

**Extension points**:
- Add PDF report generation
- Add timeline visualization
- Add network analysis (contact graphs)
- Add media gallery in HTML reports
- Add search functionality in HTML reports

## Main Entry Point

**Location**: `main.py`

**Purpose**: Command-line interface that ties all modules together.

**Commands**:
- `acquire`: Acquire data from a source
- `decrypt`: Decrypt an encrypted database
- `parse`: Parse a database and generate reports
- `full`: Complete workflow (acquire -> decrypt -> parse -> report)

**How it works**:
1. Parses command-line arguments using `argparse`
2. Routes to appropriate handler function
3. Each handler instantiates necessary modules and orchestrates workflow
4. Logs progress and errors using Python logging

## Database Schema Notes

WhatsApp uses SQLite databases with schema that varies by version:

**Modern schema** (v2.21+):
- Uses `jid` table for JID normalization
- `chat.jid_row_id` references `jid._id`
- `message.key_remote_jid` is a raw string
- Tables: `chat`, `jid`, `message`, `group_participant_user`, `call_log`

**Older schema** (pre-v2.21):
- JIDs stored directly as strings
- Tables: `chat_list`, `messages`, `group_participants`, `calls`

The parser tries both schemas automatically.

## Dependencies

**Core**:
- `pycryptodome`: AES-GCM encryption/decryption
- `sqlite3`: Database access (standard library)
- `json`, `csv`, `html`: Report generation (standard library)

**Optional**:
- `gpsoauth`: Google Drive backup extraction
- `pyicloud`: iCloud backup extraction
- `selenium`: Web automation for Google Drive
- `pandas`, `numpy`: Data processing

See `requirements.txt` for full list.

## Testing

Tests are located in `tests/` directory:

- `test_acquisition.py`: Tests for acquisition module
- `test_crypto.py`: Tests for crypto module
- `test_parsing.py`: Tests for parsing module
- `test_reporting.py`: Tests for reporting module
- `test_integration.py`: Full workflow integration tests

Run tests with:
```bash
pytest
```

## Known Limitations and TODOs

1. **Crypt15 decryption**: Basic implementation, may not work with all crypt15 databases. Full support requires using WhatsApp-Crypt15-Decrypter library.

2. **iOS support**: Acquisition from iOS devices is not fully implemented.

3. **Google Drive backup**: Acquisition from Google Drive is mentioned but not fully implemented in main workflow.

4. **Media extraction**: Media files are referenced but not fully analyzed or extracted from databases.

5. **Deleted messages**: Deleted message recovery is not implemented.

6. **Schema compatibility**: May not work with very old or very new WhatsApp database schemas.

7. **Performance**: Large databases may take significant time to parse. Consider adding pagination or limits.

## CAINE OS Compatibility

This toolkit is designed to run on CAINE OS (Computer Aided INvestigative Environment), a Linux distribution for digital forensics.

**CAINE OS specific considerations**:
- Uses standard Linux tools (ADB, Python 3)
- Output directories follow forensic best practices
- Reports include metadata suitable for forensic documentation
- File permissions and timestamps are preserved during acquisition

**Testing on CAINE**:
1. Install dependencies from requirements.txt
2. Test ADB connection with Android device
3. Verify Python 3.8+ is available
4. Run full workflow with test data

## Development Workflow

1. **Making changes**:
   - Edit module files in `src/`
   - Update tests in `tests/`
   - Run tests: `pytest`
   - Test manually with sample data

2. **Adding features**:
   - Follow existing module structure
   - Add comprehensive error handling
   - Add logging statements
   - Write tests for new functionality
   - Update this guide

3. **Debugging**:
   - Enable verbose logging: Set logging level to DEBUG
   - Test individual modules in isolation
   - Use Python debugger: `pdb` or IDE debugger
   - Check database schemas with `sqlite3` command-line tool

## Troubleshooting

**Common issues**:

1. **ADB not found**: Install Android SDK Platform Tools
2. **Database schema errors**: WhatsApp may use different schema, add support in parser
3. **Decryption fails**: Verify key file is correct (158 bytes for crypt12/14)
4. **Import errors**: Ensure all dependencies are installed: `pip install -r requirements.txt`
5. **Permission errors**: Check file permissions, especially for ADB access

**Getting help**:
- Check logs for detailed error messages
- Verify database integrity: `sqlite3 database.db "PRAGMA integrity_check;"`
- Test with known-good sample databases
- Review WhatsApp database documentation

## Future Enhancements

Potential areas for improvement:

1. **Full crypt15 support**: Integrate WhatsApp-Crypt15-Decrypter library
2. **iOS acquisition**: Complete iTunes backup extraction
3. **Google Drive integration**: Full implementation with OAuth
4. **Deleted message recovery**: SQLite WAL file analysis
5. **Media analysis**: EXIF extraction, hash calculation
6. **Timeline generation**: Unified timeline of all activities
7. **Network analysis**: Contact relationship graphs
8. **Automated testing**: CI/CD pipeline
9. **GUI**: Web-based or desktop GUI interface
10. **API**: REST API for programmatic access

## Code Style

- Follow PEP 8 Python style guide
- Use type hints where appropriate
- Document functions and classes with docstrings
- Use meaningful variable names
- Handle exceptions explicitly
- Log important operations

## License and Attribution

This toolkit builds upon concepts from:
- Whapa toolset by B16f00t
- WhatsApp-Crypt14-Crypt15-Decrypter by ElDavoo
- WhatsApp Msgstore Viewer

See individual tool licenses for details.

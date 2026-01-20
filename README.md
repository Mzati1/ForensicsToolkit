# WhatsApp Forensics Toolkit

A comprehensive toolkit for WhatsApp forensics analysis on CAINE OS. Supports acquisition, decryption, parsing, and reporting of WhatsApp data from Android and iOS devices.

## Features

- **Acquisition**: Extract WhatsApp data from Android devices (ADB), iOS backups, local files, and Google Drive
- **Decryption**: Support for crypt12, crypt14, and crypt15 encrypted databases
- **Parsing**: Extract chats, messages, contacts, and call logs from WhatsApp databases
- **Reporting**: Generate forensic reports in HTML, JSON, and CSV formats
- **CAINE OS Compatible**: Designed to run on Computer Aided INvestigative Environment

## Requirements

- Python 3.8 or higher
- CAINE OS or compatible Linux distribution
- Android SDK Platform Tools (for ADB acquisition)
- Root access to Android device (for ADB acquisition)

## Installation

### On CAINE OS

1. Clone the repository:
```bash
git clone <repository-url>
cd ForensicsToolkit
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. For ADB support, ensure Android SDK Platform Tools are installed:
```bash
sudo apt-get update
sudo apt-get install android-tools-adb
```

4. Make main script executable:
```bash
chmod +x main.py
```

## Setup

1. Verify Python installation:
```bash
python3 --version
```

2. Verify ADB installation (if using ADB acquisition):
```bash
adb version
```

3. Connect Android device and enable USB debugging (if using ADB):
```bash
adb devices
```

4. Prepare output directory:
```bash
mkdir -p output/reports
```

## Usage

### Command-Line Interface

The toolkit provides a command-line interface with the following commands:

#### Acquire Data

Acquire WhatsApp data from various sources:

**From Android device via ADB:**
```bash
python3 main.py acquire --source android_adb --output ./output
```

**From local files:**
```bash
python3 main.py acquire --source file --input ./whatsapp_data --output ./output
```

#### Decrypt Database

Decrypt an encrypted WhatsApp database:

```bash
python3 main.py decrypt --input msgstore.db.crypt14 --key key --output msgstore.db
```

**Arguments:**
- `--input`: Encrypted database file path
- `--key`: Key file path (typically 158 bytes)
- `--output`: Output decrypted database path (optional, defaults to input filename with .db extension)

#### Parse Database and Generate Report

Parse a WhatsApp database and generate forensic reports:

```bash
python3 main.py parse --msgstore msgstore.db --wa wa.db --output ./reports --format html
```

**Arguments:**
- `--msgstore`: Path to msgstore.db (required)
- `--wa`: Path to wa.db for contact names (optional)
- `--output`: Output directory for reports (default: output/reports)
- `--format`: Report format - html, json, csv, or all (default: html)
- `--chat-limit`: Limit number of chats to process (optional)
- `--message-limit`: Limit number of messages per chat (optional)

#### Full Workflow

Execute complete workflow: acquire, decrypt, parse, and report:

```bash
python3 main.py full \
  --source file \
  --input ./whatsapp_data \
  --key key \
  --output ./output \
  --format html \
  --metadata-company "Forensics Unit" \
  --metadata-examiner "John Doe" \
  --metadata-record "CASE-2024-001" \
  --metadata-notes "WhatsApp forensics analysis"
```

**Arguments:**
- `--source`: Acquisition source - android_adb or file
- `--input`: Input directory or device ID
- `--key`: Key file for decryption (if needed)
- `--output`: Output directory (default: output)
- `--format`: Report format - html, json, csv, or all (default: html)
- `--metadata-company`: Company name for report
- `--metadata-examiner`: Examiner name for report
- `--metadata-record`: Record number for report
- `--metadata-notes`: Notes for report

### Examples

**Example 1: Acquire from Android device**
```bash
# Connect device via ADB
adb devices

# Acquire WhatsApp data
python3 main.py acquire --source android_adb --output ./acquisition_output
```

**Example 2: Decrypt and parse encrypted database**
```bash
# Decrypt
python3 main.py decrypt --input ./backup/msgstore.db.crypt14 --key ./backup/key

# Parse decrypted database
python3 main.py parse --msgstore ./backup/msgstore.db --wa ./backup/wa.db --format all
```

**Example 3: Full workflow from local files**
```bash
python3 main.py full \
  --source file \
  --input ./extracted_whatsapp \
  --key ./extracted_whatsapp/key \
  --output ./forensics_output \
  --format html \
  --metadata-company "Digital Forensics Lab" \
  --metadata-examiner "Jane Smith" \
  --metadata-record "DF-2024-042" \
  --metadata-notes "Complete WhatsApp analysis"
```

## Output

### Acquisition Output

Acquired files are stored in `output/acquisition/` directory:
- Databases: msgstore.db, wa.db, etc.
- Encrypted databases: msgstore.db.crypt12/14/15
- Keys: key file
- Media: WhatsApp/Media directory (if available)

### Report Output

Reports are generated in the specified output directory:

**HTML Report** (`whatsapp_report_TIMESTAMP.html`):
- Summary statistics
- Contact list
- Chat conversations with messages
- Call logs
- Styled with CSS for professional presentation

**JSON Report** (`whatsapp_report_TIMESTAMP.json`):
- Complete structured data in JSON format
- Suitable for programmatic processing
- Includes all chats, messages, contacts, and call logs

**CSV Reports** (multiple files):
- `contacts_TIMESTAMP.csv`: Contact information
- `messages_TIMESTAMP.csv`: All messages
- `calls_TIMESTAMP.csv`: Call logs

## Module Structure

- `src/acquisition/`: Data acquisition from various sources
- `src/crypto/`: Database encryption/decryption
- `src/parsing/`: Database parsing and data extraction
- `src/reporting/`: Forensic report generation
- `main.py`: Command-line interface
- `tests/`: Test suite

## Database Files

### msgstore.db
Main message database containing:
- Chats
- Messages
- Media references
- Call logs
- Group information

### wa.db
Contacts database containing:
- Contact names
- Phone numbers
- JID mappings

### Key File
Encryption key file (typically 158 bytes) located at:
- Android: `/data/data/com.whatsapp/files/key`
- Or extracted from WhatsApp backup

## Troubleshooting

### ADB Device Not Found
- Ensure USB debugging is enabled on device
- Verify device is authorized: `adb devices`
- Check USB connection and drivers

### Decryption Fails
- Verify key file is correct (158 bytes for crypt12/14)
- Check encryption type matches (crypt12/14/15)
- Ensure encrypted database is not corrupted

### Database Parsing Errors
- Verify database is not corrupted: `sqlite3 database.db "PRAGMA integrity_check;"`
- Check database schema compatibility (tool supports multiple WhatsApp versions)
- Ensure database is decrypted if encrypted

### Permission Errors
- Ensure output directory is writable
- Check file permissions on input files
- For ADB: ensure device is rooted or use backup method

### Import Errors
- Install dependencies: `pip3 install -r requirements.txt`
- Verify Python version: `python3 --version` (requires 3.8+)
- Check virtual environment is activated if using one

## Testing

Run the test suite:

```bash
pytest
```

Run specific test module:

```bash
pytest tests/test_parsing.py
```

Run with coverage:

```bash
pytest --cov=src tests/
```

## Limitations

- Crypt15 decryption: Basic implementation, may not work with all databases
- iOS acquisition: Limited support, primarily for iTunes backups
- Google Drive backup: Requires manual configuration
- Large databases: May take significant time to parse
- Schema compatibility: Supports modern and older WhatsApp database schemas, but very old or very new versions may have issues

## Development

See DEVELOPMENT_GUIDE.md for detailed information about:
- Architecture and design
- Module implementation details
- Extension points
- Code style guidelines
- Troubleshooting tips

## License

See LICENSE file for license information.

## Contributing

1. Follow existing code style
2. Write tests for new features
3. Update documentation
4. Test on CAINE OS before submitting

## Support

For issues and questions:
- Check DEVELOPMENT_GUIDE.md
- Review error logs for detailed messages
- Test with sample databases to isolate issues
- Verify all dependencies are installed

## References

This toolkit builds upon concepts from:
- Whapa toolset
- WhatsApp-Crypt14-Crypt15-Decrypter
- WhatsApp Msgstore Viewer

See individual tool licenses and documentation for details.

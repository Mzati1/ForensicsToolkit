# WhatsApp Forensics Toolkit

A comprehensive toolkit for WhatsApp forensics analysis on CAINE OS. Supports acquisition, decryption, parsing, and reporting of WhatsApp data.

## Quick Start

```bash
# Setup
./setup.sh
source venv/bin/activate

# Acquire data from local files
python main.py acquire --source file --input ./whatsapp_data --output ./output

# Decrypt database
python main.py decrypt --input msgstore.db.crypt14 --key key --output msgstore.db

# Parse and generate report
python main.py parse --msgstore msgstore.db --wa wa.db --format html

# Full workflow
python main.py full --source file --input ./whatsapp_data --key key --output ./output
```

## Installation

1. Clone repository:
```bash
git clone <repository-url>
cd ForensicsToolkit
```

2. Run setup script:
```bash
chmod +x setup.sh
./setup.sh
```

3. Activate virtual environment:
```bash
source venv/bin/activate
```

## Features

- **Acquisition**: Extract WhatsApp data from Android devices (ADB) or local files
- **Decryption**: Support for crypt12, crypt14, and crypt15 encrypted databases
- **Parsing**: Extract chats, messages, contacts, and call logs
- **Reporting**: Generate forensic reports in HTML, JSON, and CSV formats
- **Forensic Compliance**: Chain of custody, hash verification, audit logging

## Commands

### Acquire
```bash
python main.py acquire --source android_adb --output ./output
python main.py acquire --source file --input ./whatsapp_data --output ./output
```

### Decrypt
```bash
python main.py decrypt --input msgstore.db.crypt14 --key key --output msgstore.db
```

### Parse
```bash
python main.py parse --msgstore msgstore.db --wa wa.db --output ./reports --format html
```

### Full Workflow
```bash
python main.py full \
  --source file \
  --input ./whatsapp_data \
  --key key \
  --output ./output \
  --format html \
  --metadata-company "Forensics Unit" \
  --metadata-examiner "John Doe" \
  --metadata-record "CASE-2024-001"
```

## What Each Module Does

### Acquisition (`src/acquisition/`)
Gets WhatsApp databases and files from Android devices or local directories. Supports ADB extraction and file system acquisition.

### Crypto (`src/crypto/`)
Decrypts WhatsApp encrypted databases (crypt12, crypt14, crypt15). Uses AES-GCM encryption with key files.

### Parsing (`src/parsing/`)
Extracts structured data from WhatsApp databases. Gets chats, messages, contacts, and call logs. Supports multiple database schemas.

### Reporting (`src/reporting/`)
Generates forensic reports in HTML, JSON, or CSV formats. Creates professional HTML reports with styling.

### Forensics (`src/forensics/`)
Provides forensic compliance features:
- **Chain of Custody**: Tracks evidence handling with hashes
- **Hash Verification**: MD5, SHA256, SHA512 for integrity
- **Audit Logging**: Complete audit trail of all actions
- **Compliance**: ACPO principles and GDPR compliance checking

## Documentation

- **HOW_IT_WORKS.md** - Detailed explanation of each module and how it works
- **DEVELOPMENT_GUIDE.md** - Architecture, design, and extension points
- **FORENSIC_COMPLIANCE.md** - Compliance and security practices

## Requirements

- Python 3.8 or higher
- Virtual environment (created by setup.sh)
- Dependencies installed via requirements.txt

## Troubleshooting

**Module not found errors:**
- Ensure virtual environment is activated: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**Import errors:**
- Check Python version: `python3 --version` (needs 3.8+)
- Verify all dependencies installed: `pip list`

**Database errors:**
- Verify database is not corrupted
- Ensure database is decrypted if encrypted
- Check file permissions

## Testing

```bash
pytest
pytest tests/test_parsing.py
pytest --cov=src tests/
```

## License

See LICENSE file.

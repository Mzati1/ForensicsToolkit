# Quick Start Guide

## Setup

1. Run setup script:
```bash
./setup.sh
```

2. Activate virtual environment:
```bash
source venv/bin/activate
```

3. Verify installation:
```bash
python main.py --help
```

## Basic Usage

### Acquire WhatsApp Data
```bash
python main.py acquire --source file --input ./whatsapp_data --output ./output
```

### Decrypt Encrypted Database
```bash
python main.py decrypt --input msgstore.db.crypt14 --key key --output msgstore.db
```

### Parse Database
```bash
python main.py parse --msgstore msgstore.db --wa wa.db --format html
```

### Full Workflow
```bash
python main.py full \
  --source file \
  --input ./whatsapp_data \
  --key key \
  --output ./output \
  --format html
```

## What Each Command Does

**acquire** - Gets WhatsApp databases and files from device or local directory
- Adds files to chain of custody with hash verification
- Creates acquisition summary

**decrypt** - Decrypts encrypted WhatsApp database
- Supports crypt12, crypt14, crypt15
- Requires key file (usually 158 bytes)

**parse** - Extracts data from database and generates reports
- Gets chats, messages, contacts, call logs
- Generates HTML, JSON, or CSV reports

**full** - Complete workflow from acquisition to reporting
- Combines all steps with forensic compliance
- Generates all compliance reports

## Troubleshooting

**If you see "Module not found" errors:**
1. Activate virtual environment: `source venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`

**If setup script fails:**
1. Create virtual environment manually: `python3 -m venv venv`
2. Activate it: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`

## Next Steps

- Read **HOW_IT_WORKS.md** for detailed module explanations
- Read **README.md** for full documentation
- Read **FORENSIC_COMPLIANCE.md** for compliance information

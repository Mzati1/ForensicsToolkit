# WhatsApp Forensics Toolkit

A forensic toolkit for acquiring, decrypting, parsing, and reporting WhatsApp data. Designed for CAINE OS.

## Features

- **Acquisition**: Acquire WhatsApp data from Android devices (ADB) or local files.
- **Decryption**: Decrypt WhatsApp databases (crypt12, crypt14, crypt15).
- **Parsing**: Extract chats, messages, contacts, and call logs from SQLite databases.
- **Reporting**: Generate forensic reports in HTML, PDF, CSV, and JSON formats.
- **Compliance**: Maintain chain of custody, audit logs, and hash verification.

## Installation

1. Ensure Python 3.8+ is installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Install Android SDK Platform Tools for ADB acquisition.

## Usage

Run the toolkit via `main.py`.

### Acquisition

Acquire data from an Android device connected via ADB (default):
```bash
python main.py acquire --output ./output
```

Acquire data from an Android device and include media (can be large/slow):
```bash
python main.py acquire --output ./output --include-media
```

Acquire data from a local directory:
```bash
python main.py acquire --source file --input /path/to/whatsapp/data --output ./output
```

### Decryption

Decrypt an encrypted database using the key file:
```bash
python main.py decrypt --input msgstore.db.crypt14 --key key --output msgstore.db
```

If a key file was successfully acquired from the device, it will be stored as:
- `output/android_adb/<DEVICE_LABEL>/key`
You can pass this path to `--key`.

### Parsing and Reporting

Parse a decrypted database and generate reports:
```bash
python main.py parse --msgstore msgstore.db --wa wa.db --output ./reports --format html
```

Supported formats: `html`, `pdf`, `json`, `csv`, `all`.

### Full Workflow

Run the complete workflow (acquire -> decrypt -> parse -> report):
```bash
python main.py full --source file --input /path/to/data --key key --output ./output --format pdf
```

## Structure

- `src/`: Source code modules.
- `tools/`: External tools (if any).
- `tests/`: Unit and integration tests.
- `output/`: Default output directory for acquired data and reports.
  - `output/android_adb/<DEVICE_LABEL>/databases/`: WhatsApp databases acquired via ADB.
  - `output/android_adb/<DEVICE_LABEL>/media/`: WhatsApp media (if `--include-media` was used).
    - `<DEVICE_LABEL>` is derived from the Android device model or ID.

## License

Open source forensic toolkit.

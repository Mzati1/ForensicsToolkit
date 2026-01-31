#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WhatsApp Acquisition Module

Handles acquisition of WhatsApp databases and media from various sources.
"""

import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from enum import Enum
from typing import Optional, Dict, List, Tuple, Any
import logging

# Add project root to path to allow importing tools
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class AcquisitionSource(Enum):
    """Enumeration of acquisition sources"""
    ANDROID_ADB = "android_adb"
    ANDROID_FILE = "android_file"
    IOS_BACKUP = "ios_backup"
    LOCAL_FILES = "local_files"


class WhatsAppAcquirer:
    """
    Acquires WhatsApp data from various sources.
    
    Supports:
    - Android devices via ADB
    - Android device files directly
    - iOS iTunes backups
    - Local file system
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the acquirer.
        
        Args:
            output_dir: Directory to store acquired data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger  # Ensure logger is available as instance variable if needed
        
    def acquire_from_android_adb(self, device_id: Optional[str] = None) -> Dict[str, str]:
        """
        Acquire WhatsApp data from Android device via ADB.
        
        Note: Accessing /data/data/ requires root access. Non-root devices will only
        be able to access files from /sdcard/WhatsApp/.
        
        Args:
            device_id: Optional device ID if multiple devices connected
            
        Returns:
            Dictionary with paths to acquired files
        """
        logger.info("Starting ADB acquisition")
        result = {}
        
        # Check if ADB is available
        try:
            adb_cmd = ["adb"]
            if device_id:
                adb_cmd.extend(["-s", device_id])
            
            # Check device connection
            check_cmd = adb_cmd + ["devices"]
            proc = subprocess.run(check_cmd, capture_output=True, text=True)
            device_lines = [line for line in proc.stdout.splitlines() if "device" in line and "List" not in line]
            if not device_lines:
                raise RuntimeError(
                    "No Android device connected via ADB.\n"
                    "Please ensure:\n"
                    "  1. USB debugging is enabled on your device\n"
                    "  2. You've authorized the computer on your device\n"
                    "  3. Device shows as 'device' (not 'unauthorized' or 'offline')"
                )
            
            logger.info(f"Device connected: {len(device_lines)} device(s) found")
            
            # Check if device is rooted (try to access /data/data/)
            root_available = False
            test_root_cmd = adb_cmd + ["shell", "su", "-c", "ls /data/data/com.whatsapp 2>/dev/null"]
            root_test = subprocess.run(test_root_cmd, capture_output=True, text=True, timeout=5)
            if root_test.returncode == 0 and root_test.stdout.strip():
                root_available = True
                logger.info("Root access detected - can access /data/data/")
            else:
                logger.warning(
                    "Root access not available. Only files from /sdcard/ can be accessed.\n"
                    "Files in /data/data/ require root access."
                )
            
            # WhatsApp data paths - try SD card locations first (no root needed)
            # Then try /data/data/ paths if root is available
            whatsapp_paths = []
            
            # SD card paths (no root required)
            whatsapp_paths.extend([
                "/sdcard/WhatsApp/Databases/msgstore.db.crypt12",
                "/sdcard/WhatsApp/Databases/msgstore.db.crypt14",
                "/sdcard/WhatsApp/Databases/msgstore.db.crypt15",
                "/storage/emulated/0/WhatsApp/Databases/msgstore.db.crypt12",
                "/storage/emulated/0/WhatsApp/Databases/msgstore.db.crypt14",
                "/storage/emulated/0/WhatsApp/Databases/msgstore.db.crypt15",
            ])
            
            # /data/data/ paths (require root)
            if root_available:
                whatsapp_paths.extend([
                    "/data/data/com.whatsapp/databases/msgstore.db",
                    "/data/data/com.whatsapp/databases/wa.db",
                    "/data/data/com.whatsapp/databases/axolotl.db",
                ])
            else:
                logger.info("Skipping /data/data/ paths (root required)")
            
            # Media directory (try multiple locations)
            whatsapp_paths.extend([
                "/sdcard/WhatsApp/Media",
                "/storage/emulated/0/WhatsApp/Media",
            ])
            
            acquisition_dir = self.output_dir / "android_adb"
            acquisition_dir.mkdir(parents=True, exist_ok=True)
            
            for path in whatsapp_paths:
                try:
                    # Check if path exists on device first
                    test_cmd = adb_cmd + ["shell", "test", "-e", path, "&&", "echo", "exists"]
                    test_proc = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
                    
                    if "exists" not in test_proc.stdout:
                        logger.debug(f"Path does not exist on device: {path}")
                        continue
                    
                    # Handle directories vs files differently
                    is_dir = "Media" in path
                    
                    if is_dir:
                        # For directories, pull entire directory
                        dest_path = acquisition_dir / Path(path).name
                        if dest_path.exists():
                            shutil.rmtree(dest_path)
                        pull_cmd = adb_cmd + ["pull", path, str(dest_path)]
                    else:
                        # For files, pull to acquisition dir
                        filename = Path(path).name
                        dest_path = acquisition_dir / filename
                        pull_cmd = adb_cmd + ["pull", path, str(dest_path)]
                    
                    proc = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=300)
                    
                    if proc.returncode == 0 and dest_path.exists():
                        result[path] = str(dest_path)
                        logger.info(f"✓ Acquired: {path} -> {dest_path}")
                    else:
                        error_msg = proc.stderr.strip() if proc.stderr else proc.stdout.strip()
                        if "Permission denied" in error_msg or "permission" in error_msg.lower():
                            logger.warning(f"Permission denied for {path} (may require root)")
                        else:
                            logger.debug(f"Could not acquire {path}: {error_msg}")
                    
                except subprocess.TimeoutExpired:
                    logger.warning(f"Timeout acquiring {path}")
                except Exception as e:
                    logger.debug(f"Could not acquire {path}: {e}")
            
            if not result:
                logger.warning(
                    "No files were acquired. Possible reasons:\n"
                    "  - WhatsApp is not installed on the device\n"
                    "  - Files are not in expected locations\n"
                    "  - Root access required for /data/data/ files\n"
                    "  - Files may need to be backed up manually first"
                )
            else:
                logger.info(f"ADB acquisition complete. Files acquired: {len(result)}")
            
            return result
            
        except FileNotFoundError:
            raise RuntimeError(
                "ADB not found. Please install Android SDK Platform Tools:\n"
                "  macOS: brew install android-platform-tools\n"
                "  Linux: sudo apt-get install adb\n"
                "  Or download from: https://developer.android.com/studio/releases/platform-tools"
            )
        except Exception as e:
            logger.error(f"ADB acquisition failed: {e}")
            raise

    def acquire_from_files(self, source_dir: str) -> Dict[str, str]:
        """
        Acquire WhatsApp data from local file system.
        
        Args:
            source_dir: Directory containing WhatsApp files
            
        Returns:
            Dictionary with paths to acquired files
        """
        logger.info(f"Starting file acquisition from {source_dir}")
        result = {}
        
        source_path = Path(source_dir).resolve()
        if not source_path.exists():
            # Try treating as relative path
            source_path = Path(source_dir)
            if not source_path.exists():
                raise ValueError(f"Source directory does not exist: {source_dir}")
        
        acquisition_dir = self.output_dir / "local_files"
        acquisition_dir.mkdir(parents=True, exist_ok=True)
        
        # Files to look for
        target_files = [
            "msgstore.db",
            "msgstore.db.crypt12",
            "msgstore.db.crypt14",
            "msgstore.db.crypt15",
            "wa.db",
            "axolotl.db",
            "key"
        ]
        
        # Walk through directory
        for root, _, files in os.walk(source_path):
            for file in files:
                if file in target_files or file.startswith("msgstore-") or file.endswith(".crypt14") or file.endswith(".crypt15"):
                    source_file = Path(root) / file
                    dest_file = acquisition_dir / file
                    
                    shutil.copy2(source_file, dest_file)
                    result[str(source_file)] = str(dest_file)
                    logger.info(f"✓ Acquired: {file}")
        
        # Also look for Media folder
        media_dir = source_path / "Media"
        if media_dir.exists() and media_dir.is_dir():
            dest_media = acquisition_dir / "Media"
            if dest_media.exists():
                shutil.rmtree(dest_media)
            shutil.copytree(media_dir, dest_media)
            result[str(media_dir)] = str(dest_media)
            logger.info(f"✓ Acquired: Media folder")
            
        if not result:
            logger.warning("No WhatsApp databases found in input directory")
            
        return result

    def get_acquisition_summary(self, acquired_files: Dict[str, str]) -> Dict[str, Any]:
        """
        Get detailed summary of acquisition.
        
        Args:
            acquired_files: Dictionary of acquired files
            
        Returns:
            Dictionary with acquisition statistics and details
        """
        summary = {
            "total_files": len(acquired_files),
            "total_size_bytes": 0,
            "databases": [],
            "encrypted_databases": [],
            "media_files": [],
            "keys": [],
            "others": []
        }
        
        for name, path in acquired_files.items():
            file_path = Path(path)
            if file_path.exists():
                if file_path.is_file():
                    size = file_path.stat().st_size
                    summary["total_size_bytes"] += size
                    
                    # Categorize
                    name_lower = file_path.name.lower()
                    if "crypt" in name_lower:
                        summary["encrypted_databases"].append(str(file_path))
                    elif name_lower.endswith(".db"):
                        summary["databases"].append(str(file_path))
                    elif name_lower == "key":
                        summary["keys"].append(str(file_path))
                    elif file_path.suffix.lower().strip('.') in ["jpg", "jpeg", "png", "mp4", "3gp", "opus", "webp"]:
                        summary["media_files"].append(str(file_path))
                    else:
                        summary["others"].append(str(file_path))
                        
                elif file_path.is_dir():
                    # Directory (e.g. Media)
                    dir_size = 0
                    for root, _, files in os.walk(file_path):
                        for f in files:
                            fp = Path(root) / f
                            dir_size += fp.stat().st_size
                    summary["total_size_bytes"] += dir_size
                    summary["media_files"].append(str(file_path)) # Assume dirs are media folders
                    
        return summary

    def verify_database(self, db_path: str) -> bool:
        """
        Verify if a file is a valid SQLite database.
        
        Args:
            db_path: Path to database file
            
        Returns:
            True if valid SQLite database, False otherwise
        """
        if not os.path.exists(db_path):
            return False
            
        try:
            # Open in read-only mode to check validity
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("PRAGMA schema_version")
            conn.close()
            return True
        except sqlite3.DatabaseError:
            return False
        except Exception as e:
            self.logger.debug(f"Database verification failed: {e}")
            return False

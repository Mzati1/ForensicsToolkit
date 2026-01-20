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
from pathlib import Path
from enum import Enum
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class AcquisitionSource(Enum):
    """Enumeration of acquisition sources"""
    ANDROID_ADB = "android_adb"
    ANDROID_FILE = "android_file"
    IOS_BACKUP = "ios_backup"
    GOOGLE_DRIVE = "google_drive"
    LOCAL_FILES = "local_files"


class WhatsAppAcquirer:
    """
    Acquires WhatsApp data from various sources.
    
    Supports:
    - Android devices via ADB
    - Android device files directly
    - iOS iTunes backups
    - Google Drive backups
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
        logger.info(f"Starting file system acquisition from {source_dir}")
        result = {}
        
        source_path = Path(source_dir).resolve()
        if not source_path.exists():
            abs_path = source_path.absolute()
            raise ValueError(
                f"Source directory does not exist: {source_dir}\n"
                f"  Absolute path: {abs_path}\n"
                f"  Please ensure the directory exists and contains WhatsApp data files.\n"
                f"  Expected files include: msgstore.db, wa.db, msgstore.db.crypt12/14/15, etc."
            )
        
        acquisition_dir = self.output_dir / "file_acquisition"
        acquisition_dir.mkdir(parents=True, exist_ok=True)
        
        # Look for common WhatsApp files
        whatsapp_files = [
            "msgstore.db",
            "msgstore.db.crypt12",
            "msgstore.db.crypt14",
            "msgstore.db.crypt15",
            "wa.db",
            "axolotl.db",
            "chatsettings.db",
            "key"
        ]
        
        # Search for files recursively
        for root, dirs, files in os.walk(source_path):
            for file in files:
                if file in whatsapp_files or file.endswith(".crypt12") or file.endswith(".crypt14") or file.endswith(".crypt15"):
                    src_file = Path(root) / file
                    dest_file = acquisition_dir / file
                    
                    try:
                        shutil.copy2(src_file, dest_file)
                        result[str(src_file)] = str(dest_file)
                        logger.info(f"Copied: {src_file} -> {dest_file}")
                    except Exception as e:
                        logger.warning(f"Could not copy {src_file}: {e}")
            
            # Also copy Media directory if found
            if "Media" in dirs and "WhatsApp" in root:
                media_src = Path(root) / "Media"
                media_dest = acquisition_dir / "Media"
                try:
                    if media_dest.exists():
                        shutil.rmtree(media_dest)
                    shutil.copytree(media_src, media_dest)
                    result[str(media_src)] = str(media_dest)
                    logger.info(f"Copied Media directory: {media_src} -> {media_dest}")
                except Exception as e:
                    logger.warning(f"Could not copy Media directory: {e}")
        
        logger.info(f"File acquisition complete. Files: {len(result)}")
        return result
    
    def verify_database(self, db_path: str) -> bool:
        """
        Verify if a file is a valid SQLite database.
        
        Args:
            db_path: Path to database file
            
        Returns:
            True if valid SQLite database
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            return len(tables) > 0
        except Exception:
            return False
    
    def get_acquisition_summary(self, acquired_files: Dict[str, str]) -> Dict:
        """
        Generate summary of acquisition.
        
        Args:
            acquired_files: Dictionary of acquired files
            
        Returns:
            Summary dictionary
        """
        summary = {
            "total_files": len(acquired_files),
            "databases": [],
            "encrypted_databases": [],
            "keys": [],
            "media_dirs": []
        }
        
        for dest_path in acquired_files.values():
            path = Path(dest_path)
            if path.suffix == ".db":
                if self.verify_database(dest_path):
                    summary["databases"].append(dest_path)
            elif path.suffix in [".crypt12", ".crypt14", ".crypt15"]:
                summary["encrypted_databases"].append(dest_path)
            elif path.name == "key":
                summary["keys"].append(dest_path)
            elif path.name == "Media" or "Media" in dest_path:
                summary["media_dirs"].append(dest_path)
        
        return summary

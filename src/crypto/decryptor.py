#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WhatsApp Database Decryption Module

Supports decryption of crypt12, crypt14, and crypt15 encrypted WhatsApp databases.
"""

import os
import zlib
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple
import logging

# Try to import Crypto - support both pycryptodome and pycryptodomex
try:
    from Crypto.Cipher import AES
except ImportError:
    try:
        from Cryptodome.Cipher import AES
    except ImportError:
        raise ImportError(
            "pycryptodome or pycryptodomex is required. "
            "Install with: pip install pycryptodome"
        )

logger = logging.getLogger(__name__)


class EncryptionType(Enum):
    """WhatsApp encryption types"""
    CRYPT12 = "crypt12"
    CRYPT14 = "crypt14"
    CRYPT15 = "crypt15"
    UNENCRYPTED = "unencrypted"


class WhatsAppDecryptor:
    """
    Decrypts WhatsApp encrypted databases.
    
    Supports crypt12, crypt14, and crypt15 encryption formats.
    """
    
    def __init__(self, key_file: str):
        """
        Initialize decryptor with key file.
        
        Args:
            key_file: Path to WhatsApp key file (usually 158 bytes for crypt12/14)
        """
        self.key_file = Path(key_file)
        if not self.key_file.exists():
            raise FileNotFoundError(f"Key file not found: {key_file}")
        
        self.key = self._load_key()
    
    def _load_key(self) -> bytes:
        """
        Load encryption key from key file.
        
        Returns:
            Encryption key bytes
        """
        with open(self.key_file, "rb") as f:
            key_data = f.read()
        
        # Key is typically at offset 126 in the key file
        if len(key_data) >= 158:
            return key_data[126:]
        elif len(key_data) >= 32:
            # Some key files might just contain the key directly
            return key_data[-32:]
        else:
            raise ValueError(f"Invalid key file size: {len(key_data)} bytes")
    
    def detect_encryption_type(self, db_file: str) -> EncryptionType:
        """
        Detect encryption type of database file.
        
        Args:
            db_file: Path to database file
            
        Returns:
            EncryptionType enum
        """
        db_path = Path(db_file)
        if db_path.suffix == ".crypt12":
            return EncryptionType.CRYPT12
        elif db_path.suffix == ".crypt14":
            return EncryptionType.CRYPT14
        elif db_path.suffix == ".crypt15":
            return EncryptionType.CRYPT15
        else:
            # Try to detect by file content
            try:
                with open(db_path, "rb") as f:
                    header = f.read(16)
                    # Check for SQLite magic number
                    if header[:16] == b"SQLite format 3\x00":
                        return EncryptionType.UNENCRYPTED
                    # Crypt14/15 have specific headers
                    if header[:3] == b"\x00\x00\x00":
                        return EncryptionType.CRYPT14
            except Exception:
                pass
            return EncryptionType.UNENCRYPTED
    
    def decrypt_crypt12(self, encrypted_file: str, output_file: str) -> bool:
        """
        Decrypt crypt12 encrypted database.
        
        Args:
            encrypted_file: Path to encrypted database
            output_file: Path to output decrypted database
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Decrypting crypt12: {encrypted_file}")
            
            with open(encrypted_file, "rb") as f:
                db_data = f.read()
            
            if len(db_data) < 87:
                raise ValueError("Database file too small")
            
            # Crypt12 format: header (51) + IV (16) + encrypted data + footer (20)
            iv = db_data[51:67]
            encrypted_data = db_data[67:-20]
            
            # Decrypt using AES-GCM
            cipher = AES.new(self.key, mode=AES.MODE_GCM, nonce=iv)
            decrypted_data = cipher.decrypt(encrypted_data)
            
            # Decompress
            decompressed = zlib.decompress(decrypted_data)
            
            # Write decrypted database
            with open(output_file, "wb") as f:
                f.write(decompressed)
            
            logger.info(f"Successfully decrypted to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to decrypt crypt12: {e}")
            return False
    
    def decrypt_crypt14(self, encrypted_file: str, output_file: str) -> bool:
        """
        Decrypt crypt14 encrypted database.
        
        Args:
            encrypted_file: Path to encrypted database
            output_file: Path to output decrypted database
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Decrypting crypt14: {encrypted_file}")
            
            with open(encrypted_file, "rb") as f:
                db_data = f.read()
            
            if len(db_data) < 195:
                raise ValueError("Database file too small")
            
            # Crypt14 format: header + IV (at offset 67:83) + encrypted data
            # Try different offsets as crypt14 has variable header size
            iv = db_data[67:83]
            
            # Try offsets from 185 to 195
            for offset in range(185, 196):
                try:
                    encrypted_data = db_data[offset:-20] if len(db_data) > offset + 20 else db_data[offset:]
                    
                    cipher = AES.new(self.key, mode=AES.MODE_GCM, nonce=iv)
                    decrypted_data = cipher.decrypt(encrypted_data)
                    
                    # Try to decompress
                    decompressed = zlib.decompress(decrypted_data)
                    
                    # Write decrypted database
                    with open(output_file, "wb") as f:
                        f.write(decompressed)
                    
                    logger.info(f"Successfully decrypted crypt14 with offset {offset} to: {output_file}")
                    return True
                    
                except (zlib.error, ValueError, Exception) as e:
                    if offset == 195:
                        logger.error(f"Failed to decrypt crypt14 with all offsets: {e}")
                        raise
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to decrypt crypt14: {e}")
            return False
    
    def decrypt_crypt15(self, encrypted_file: str, output_file: str) -> bool:
        """
        Decrypt crypt15 encrypted database.
        
        Note: crypt15 uses a different encryption scheme. This is a simplified implementation.
        For full crypt15 support, refer to specialized libraries.
        
        Args:
            encrypted_file: Path to encrypted database
            output_file: Path to output decrypted database
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Decrypting crypt15: {encrypted_file}")
            logger.warning("Crypt15 decryption is limited. Full support may require additional libraries.")
            
            with open(encrypted_file, "rb") as f:
                db_data = f.read()
            
            # Crypt15 uses a different format - this is a basic implementation
            # Full crypt15 support requires additional processing
            # For now, we'll attempt similar approach to crypt14
            
            iv = db_data[67:83]
            encrypted_data = db_data[195:-20] if len(db_data) > 215 else db_data[195:]
            
            cipher = AES.new(self.key, mode=AES.MODE_GCM, nonce=iv)
            decrypted_data = cipher.decrypt(encrypted_data)
            
            decompressed = zlib.decompress(decrypted_data)
            
            with open(output_file, "wb") as f:
                f.write(decompressed)
            
            logger.info(f"Successfully decrypted crypt15 to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to decrypt crypt15: {e}")
            logger.info("Note: Full crypt15 support may require WhatsApp-Crypt15-Decrypter library")
            return False
    
    def decrypt(self, encrypted_file: str, output_file: Optional[str] = None) -> Optional[str]:
        """
        Decrypt WhatsApp encrypted database.
        
        Automatically detects encryption type and decrypts accordingly.
        
        Args:
            encrypted_file: Path to encrypted database
            output_file: Optional output path. If None, generates from input filename
            
        Returns:
            Path to decrypted database if successful, None otherwise
        """
        encrypted_path = Path(encrypted_file)
        if not encrypted_path.exists():
            raise FileNotFoundError(f"Encrypted file not found: {encrypted_file}")
        
        # Determine output file
        if output_file is None:
            output_file = str(encrypted_path.parent / f"{encrypted_path.stem}.db")
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Detect encryption type
        enc_type = self.detect_encryption_type(encrypted_file)
        
        if enc_type == EncryptionType.UNENCRYPTED:
            logger.info("Database is not encrypted, copying as-is")
            import shutil
            shutil.copy2(encrypted_file, output_file)
            return output_file
        
        # Decrypt based on type
        success = False
        if enc_type == EncryptionType.CRYPT12:
            success = self.decrypt_crypt12(encrypted_file, output_file)
        elif enc_type == EncryptionType.CRYPT14:
            success = self.decrypt_crypt14(encrypted_file, output_file)
        elif enc_type == EncryptionType.CRYPT15:
            success = self.decrypt_crypt15(encrypted_file, output_file)
        
        if success and output_path.exists():
            return output_file
        else:
            return None
    
    def encrypt_crypt12(self, db_file: str, output_file: str, reference_encrypted: str) -> bool:
        """
        Encrypt database to crypt12 format.
        
        Args:
            db_file: Path to unencrypted database
            output_file: Path to output encrypted database
            reference_encrypted: Path to existing encrypted database for format reference
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Encrypting to crypt12: {db_file}")
            
            # Read reference encrypted file for header/footer
            with open(reference_encrypted, "rb") as f:
                ref_data = f.read()
            
            header = ref_data[:51]
            iv = ref_data[51:67]
            footer = ref_data[-20:]
            
            # Read database to encrypt
            with open(db_file, "rb") as f:
                db_data = f.read()
            
            # Compress and encrypt
            compressed = zlib.compress(db_data)
            cipher = AES.new(self.key, mode=AES.MODE_GCM, nonce=iv)
            encrypted = cipher.encrypt(compressed)
            
            # Write encrypted database
            with open(output_file, "wb") as f:
                f.write(header + iv + encrypted + footer)
            
            logger.info(f"Successfully encrypted to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to encrypt: {e}")
            return False

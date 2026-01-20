#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for crypto module
"""

import pytest
import tempfile
from pathlib import Path

from src.crypto import WhatsAppDecryptor, EncryptionType


class TestWhatsAppDecryptor:
    """Test WhatsAppDecryptor class"""
    
    def test_init(self):
        """Test initializer"""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_file = Path(tmpdir) / "key"
            # Create a dummy key file (158 bytes)
            key_file.write_bytes(b'\x00' * 158)
            
            decryptor = WhatsAppDecryptor(str(key_file))
            assert decryptor.key is not None
            assert len(decryptor.key) == 32
    
    def test_detect_encryption_type(self):
        """Test encryption type detection"""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_file = Path(tmpdir) / "key"
            key_file.write_bytes(b'\x00' * 158)
            decryptor = WhatsAppDecryptor(str(key_file))
            
            # Test crypt12
            crypt12_file = Path(tmpdir) / "test.crypt12"
            crypt12_file.touch()
            assert decryptor.detect_encryption_type(str(crypt12_file)) == EncryptionType.CRYPT12
            
            # Test crypt14
            crypt14_file = Path(tmpdir) / "test.crypt14"
            crypt14_file.touch()
            assert decryptor.detect_encryption_type(str(crypt14_file)) == EncryptionType.CRYPT14
            
            # Test crypt15
            crypt15_file = Path(tmpdir) / "test.crypt15"
            crypt15_file.touch()
            assert decryptor.detect_encryption_type(str(crypt15_file)) == EncryptionType.CRYPT15
            
            # Test unencrypted
            db_file = Path(tmpdir) / "test.db"
            db_file.write_bytes(b"SQLite format 3\x00")
            assert decryptor.detect_encryption_type(str(db_file)) == EncryptionType.UNENCRYPTED

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for acquisition module
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.acquisition import WhatsAppAcquirer, AcquisitionSource


class TestWhatsAppAcquirer:
    """Test WhatsAppAcquirer class"""
    
    def test_init(self):
        """Test initializer"""
        with tempfile.TemporaryDirectory() as tmpdir:
            acquirer = WhatsAppAcquirer(output_dir=tmpdir)
            assert acquirer.output_dir == Path(tmpdir)
            assert acquirer.output_dir.exists()
    
    def test_acquire_from_files(self):
        """Test file acquisition"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test structure
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            
            # Create dummy files
            (source_dir / "msgstore.db").touch()
            (source_dir / "wa.db").touch()
            (source_dir / "msgstore.db.crypt14").touch()
            (source_dir / "key").touch()
            
            acquirer = WhatsAppAcquirer(output_dir=tmpdir)
            acquired = acquirer.acquire_from_files(str(source_dir))
            
            assert len(acquired) > 0
            assert any("msgstore" in str(p) for p in acquired.values())
    
    def test_verify_database(self):
        """Test database verification"""
        with tempfile.TemporaryDirectory() as tmpdir:
            acquirer = WhatsAppAcquirer(output_dir=tmpdir)
            
            # Create a valid SQLite database
            import sqlite3
            test_db = Path(tmpdir) / "test.db"
            conn = sqlite3.connect(test_db)
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.close()
            
            assert acquirer.verify_database(str(test_db)) is True
            
            # Invalid database
            invalid_db = Path(tmpdir) / "invalid.db"
            invalid_db.write_text("not a database")
            assert acquirer.verify_database(str(invalid_db)) is False
    
    def test_get_acquisition_summary(self):
        """Test acquisition summary"""
        with tempfile.TemporaryDirectory() as tmpdir:
            acquirer = WhatsAppAcquirer(output_dir=tmpdir)
            
            # Create test files
            import sqlite3
            test_db = Path(tmpdir) / "test.db"
            conn = sqlite3.connect(test_db)
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.close()
            
            crypt_db = Path(tmpdir) / "test.crypt14"
            crypt_db.touch()
            
            key_file = Path(tmpdir) / "key"
            key_file.touch()
            
            acquired = {
                "source1": str(test_db),
                "source2": str(crypt_db),
                "source3": str(key_file)
            }
            
            summary = acquirer.get_acquisition_summary(acquired)
            
            assert summary["total_files"] == 3
            assert len(summary["databases"]) > 0
            assert len(summary["encrypted_databases"]) > 0
            assert len(summary["keys"]) > 0

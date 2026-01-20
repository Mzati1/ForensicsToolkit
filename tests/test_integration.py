#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration tests for full workflow
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path

from src.acquisition import WhatsAppAcquirer
from src.parsing import WhatsAppParser
from src.reporting import WhatsAppReporter


class TestIntegration:
    """Integration tests"""
    
    def _create_test_db(self, db_path: Path):
        """Create a test msgstore.db"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE chat (
                _id INTEGER PRIMARY KEY,
                jid_row_id INTEGER,
                subject TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE jid (
                _id INTEGER PRIMARY KEY,
                raw_string TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE message (
                _id INTEGER PRIMARY KEY,
                key_remote_jid TEXT,
                timestamp INTEGER,
                key_from_me INTEGER,
                data TEXT
            )
        """)
        
        cursor.execute("INSERT INTO jid (_id, raw_string) VALUES (1, '1234567890@s.whatsapp.net')")
        cursor.execute("INSERT INTO chat (_id, jid_row_id, subject) VALUES (1, 1, 'Test Chat')")
        cursor.execute("""
            INSERT INTO message (_id, key_remote_jid, timestamp, key_from_me, data)
            VALUES (1, '1234567890@s.whatsapp.net', 1640995200000, 0, 'Test message')
        """)
        
        conn.commit()
        conn.close()
    
    def test_full_workflow(self):
        """Test full workflow: acquire -> parse -> report"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Create test data
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            db_path = source_dir / "msgstore.db"
            self._create_test_db(db_path)
            
            # Step 2: Acquire
            acquirer = WhatsAppAcquirer(output_dir=str(Path(tmpdir) / "output"))
            acquired = acquirer.acquire_from_files(str(source_dir))
            assert len(acquired) > 0
            
            # Step 3: Parse
            parser = WhatsAppParser(str(db_path))
            chats = parser.get_chats()
            contacts = parser.get_contacts()
            call_logs = parser.get_call_logs()
            
            assert len(chats) > 0
            
            # Step 4: Report
            reporter = WhatsAppReporter(output_dir=str(Path(tmpdir) / "reports"))
            report_file = reporter.generate_json_report(chats, contacts, call_logs)
            
            assert Path(report_file).exists()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for parsing module
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path

from src.parsing import WhatsAppParser, Chat, Message, Contact, CallLog


class TestWhatsAppParser:
    """Test WhatsAppParser class"""
    
    def _create_test_db(self, db_path: Path):
        """Create a test msgstore.db"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables (simplified schema)
        cursor.execute("""
            CREATE TABLE chat (
                _id INTEGER PRIMARY KEY,
                jid_row_id INTEGER,
                subject TEXT,
                last_message_row_id INTEGER
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
                data TEXT,
                media_wa_type INTEGER
            )
        """)
        
        # Insert test data
        cursor.execute("INSERT INTO jid (_id, raw_string) VALUES (1, '1234567890@s.whatsapp.net')")
        cursor.execute("""
            INSERT INTO chat (_id, jid_row_id, subject, last_message_row_id)
            VALUES (1, 1, 'Test Chat', 1)
        """)
        cursor.execute("""
            INSERT INTO message (_id, key_remote_jid, timestamp, key_from_me, data)
            VALUES (1, '1234567890@s.whatsapp.net', 1640995200000, 0, 'Test message')
        """)
        
        conn.commit()
        conn.close()
    
    def test_init(self):
        """Test initializer"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "msgstore.db"
            self._create_test_db(db_path)
            
            parser = WhatsAppParser(str(db_path))
            assert parser.msgstore_db == db_path
    
    def test_get_chats(self):
        """Test chat extraction"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "msgstore.db"
            self._create_test_db(db_path)
            
            parser = WhatsAppParser(str(db_path))
            chats = parser.get_chats()
            
            assert len(chats) > 0
            assert isinstance(chats[0], Chat)
    
    def test_get_messages(self):
        """Test message extraction"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "msgstore.db"
            self._create_test_db(db_path)
            
            parser = WhatsAppParser(str(db_path))
            messages = parser.get_messages()
            
            assert len(messages) > 0
            assert isinstance(messages[0], Message)
    
    def test_get_contacts(self):
        """Test contact extraction"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "msgstore.db"
            self._create_test_db(db_path)
            
            # Create wa.db
            wa_db_path = Path(tmpdir) / "wa.db"
            conn = sqlite3.connect(wa_db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE wa_contacts (jid TEXT, display_name TEXT)")
            cursor.execute("INSERT INTO wa_contacts VALUES ('1234567890@s.whatsapp.net', 'Test Contact')")
            conn.commit()
            conn.close()
            
            parser = WhatsAppParser(str(db_path), str(wa_db_path))
            contacts = parser.get_contacts()
            
            assert len(contacts) > 0
            assert isinstance(contacts[0], Contact)
    
    def test_get_call_logs(self):
        """Test call log extraction"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "msgstore.db"
            self._create_test_db(db_path)
            
            parser = WhatsAppParser(str(db_path))
            call_logs = parser.get_call_logs()
            
            # May be empty if no call logs
            assert isinstance(call_logs, list)


class TestDataClasses:
    """Test data classes"""
    
    def test_contact(self):
        """Test Contact dataclass"""
        contact = Contact(jid="1234567890@s.whatsapp.net", display_name="Test")
        assert contact.jid == "1234567890@s.whatsapp.net"
        assert contact.display_name == "Test"
        assert contact.phone_number == "1234567890"
    
    def test_message(self):
        """Test Message dataclass"""
        message = Message(
            message_id=1,
            chat_jid="1234567890@s.whatsapp.net",
            timestamp=1640995200000,
            from_me=False,
            message_text="Test"
        )
        assert message.message_id == 1
        assert message.from_me is False
        assert isinstance(message.get_datetime(), type)

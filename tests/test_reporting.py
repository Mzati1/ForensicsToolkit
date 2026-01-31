#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for reporting module
"""

import pytest
import tempfile
from pathlib import Path

from src.reporting import WhatsAppReporter, ReportFormat
from src.parsing import Chat, Message, Contact, CallLog


class TestWhatsAppReporter:
    """Test WhatsAppReporter class"""
    
    def test_init(self):
        """Test initializer"""
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = WhatsAppReporter(output_dir=tmpdir)
            assert reporter.output_dir == Path(tmpdir)
            assert reporter.output_dir.exists()
    
    def test_generate_json_report(self):
        """Test JSON report generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = WhatsAppReporter(output_dir=tmpdir)
            
            chats = [Chat(jid="1234567890@s.whatsapp.net", display_name="Test Chat")]
            contacts = [Contact(jid="1234567890@s.whatsapp.net", display_name="Test")]
            call_logs = []
            
            report_file = reporter.generate_json_report(chats, contacts, call_logs)
            
            assert Path(report_file).exists()
            assert report_file.endswith(".json")
            
            # Verify JSON is valid
            import json
            with open(report_file, 'r') as f:
                data = json.load(f)
                assert 'summary' in data
                assert 'chats' in data
                assert 'contacts' in data
    
    def test_generate_csv_report(self):
        """Test CSV report generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = WhatsAppReporter(output_dir=tmpdir)
            
            chats = [Chat(jid="1234567890@s.whatsapp.net", display_name="Test Chat")]
            contacts = [Contact(jid="1234567890@s.whatsapp.net", display_name="Test")]
            call_logs = []
            
            report_files = reporter.generate_csv_report(chats, contacts, call_logs)
            
            assert len(report_files) > 0
            for file in report_files:
                assert Path(file).exists()
                assert file.endswith(".csv")
    
    def test_generate_html_report(self):
        """Test HTML report generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = WhatsAppReporter(output_dir=tmpdir)
            
            chats = [Chat(jid="1234567890@s.whatsapp.net", display_name="Test Chat")]
            contacts = [Contact(jid="1234567890@s.whatsapp.net", display_name="Test")]
            call_logs = []
            
            metadata = {
                'company': 'Test Company',
                'examiner': 'Test Examiner',
                'record': '123',
                'unit': 'Test Unit',
                'notes': 'Test notes'
            }
            
            report_file = reporter.generate_html_report(chats, contacts, call_logs, metadata)
            
            assert Path(report_file).exists()
            assert report_file.endswith(".html")
            
            # Verify HTML contains expected content
            with open(report_file, 'r') as f:
                html = f.read()
                assert 'Test Company' in html
                assert 'Test Chat' in html

    def test_generate_pdf_report(self):
        """Test PDF report generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = WhatsAppReporter(output_dir=tmpdir)
            
            chats = [Chat(jid="1234567890@s.whatsapp.net", display_name="Test Chat")]
            # Add some messages to the chat
            chats[0].messages.append(Message(
                message_id=1,
                chat_jid="1234567890@s.whatsapp.net",
                timestamp=1620000000000,
                from_me=True,
                message_text="Hello World",
                status=0
            ))
            
            contacts = [Contact(jid="1234567890@s.whatsapp.net", display_name="Test")]
            call_logs = []
            
            metadata = {
                'company': 'Test Company',
                'examiner': 'Test Examiner',
                'record': '123',
                'unit': 'Test Unit',
                'notes': 'Test notes'
            }
            
            report_file = reporter.generate_pdf_report(chats, contacts, call_logs, metadata)
            
            assert Path(report_file).exists()
            assert report_file.endswith(".pdf")
            
            # PDF content verification is complex, checking file existence and size is usually enough for unit tests
            assert Path(report_file).stat().st_size > 0

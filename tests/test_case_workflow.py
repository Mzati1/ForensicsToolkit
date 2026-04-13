#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for end-to-end modular case workflow.
"""

import json
import sqlite3
import tempfile
from pathlib import Path

from src.integration import ForensicToolkitIntegration


def _create_test_msgstore(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE chat (
            _id INTEGER PRIMARY KEY,
            jid_row_id INTEGER,
            subject TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE jid (
            _id INTEGER PRIMARY KEY,
            raw_string TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE message (
            _id INTEGER PRIMARY KEY,
            key_remote_jid TEXT,
            timestamp INTEGER,
            key_from_me INTEGER,
            data TEXT
        )
        """
    )
    cursor.execute("INSERT INTO jid (_id, raw_string) VALUES (1, '1234567890@s.whatsapp.net')")
    cursor.execute("INSERT INTO chat (_id, jid_row_id, subject) VALUES (1, 1, 'Test Chat')")
    cursor.execute(
        """
        INSERT INTO message (_id, key_remote_jid, timestamp, key_from_me, data)
        VALUES (1, '1234567890@s.whatsapp.net', 1640995200000, 0, 'Test message')
        """
    )
    conn.commit()
    conn.close()


def test_case_workflow_file_source_creates_manifest_and_reports():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        source_dir = tmp / "source_data"
        output_dir = tmp / "output"
        source_dir.mkdir(parents=True, exist_ok=True)

        db_path = source_dir / "msgstore.db"
        _create_test_msgstore(db_path)

        workflow = ForensicToolkitIntegration(
            case_id="CASE_TEST_001",
            examiner="Unit Tester",
            output_dir=str(output_dir),
            enforce_write_blocker=False,
        )
        result = workflow.run_case_workflow(
            source="file",
            method="forensic_logical_copy",
            input_path=str(source_dir),
            report_format="json",
            metadata={"company": "Test Co", "record": "CASE_TEST_001"},
        )

        assert result["success"] is True
        assert Path(result["case_directory"]).exists()
        assert Path(result["manifest"]).exists()
        assert len(result["reports"]) >= 1

        with open(result["manifest"], "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        assert manifest["case_id"] == "CASE_TEST_001"
        assert len(manifest["artifacts"]) >= 1

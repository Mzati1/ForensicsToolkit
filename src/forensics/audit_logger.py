#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Audit Logger Module

Provides comprehensive audit logging for forensic investigations.
Tracks all actions, user activities, and system events to maintain
a verifiable audit trail for legal compliance.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import hashlib

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Provides audit logging for forensic investigations.
    
    Tracks all actions taken during forensic analysis to maintain
    a verifiable audit trail for legal compliance and chain of custody.
    """
    
    def __init__(self, case_id: str, examiner: str, output_dir: str = "output/audit_logs"):
        """
        Initialize audit logger.
        
        Args:
            case_id: Unique case identifier
            examiner: Name of primary examiner
            output_dir: Directory for audit log files
        """
        self.case_id = case_id
        self.examiner = examiner
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.audit_log_file = self.output_dir / f"audit_log_{case_id}.json"
        self.audit_entries: list = []
        
        # Setup file handler for audit log
        self.file_handler = logging.FileHandler(
            self.output_dir / f"audit_{case_id}.log"
        )
        self.file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.file_handler.setFormatter(formatter)
        
        # Load existing audit entries
        self._load_audit_log()
    
    def _load_audit_log(self):
        """Load existing audit log entries"""
        if self.audit_log_file.exists():
            try:
                with open(self.audit_log_file, 'r') as f:
                    data = json.load(f)
                    self.audit_entries = data.get('entries', [])
                logger.info(f"Loaded {len(self.audit_entries)} audit entries")
            except Exception as e:
                logger.warning(f"Could not load audit log: {e}")
    
    def _save_audit_log(self):
        """Save audit log to file"""
        data = {
            'case_id': self.case_id,
            'examiner': self.examiner,
            'created_at': datetime.now().isoformat(),
            'entries': self.audit_entries
        }
        
        with open(self.audit_log_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def log_action(
        self,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None,
        resource: Optional[str] = None,
        result: Optional[str] = None
    ):
        """
        Log an action for audit trail.
        
        Args:
            action: Action performed (acquire, decrypt, parse, report, etc.)
            details: Optional details about the action
            user: User performing the action
            resource: Resource affected by the action
            result: Result of the action (success, failure, etc.)
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user': user or self.examiner,
            'resource': resource,
            'result': result,
            'details': details or {}
        }
        
        self.audit_entries.append(entry)
        self._save_audit_log()
        
        # Also log to file handler
        log_message = f"{action} | User: {entry['user']} | Resource: {resource or 'N/A'}"
        if result:
            log_message += f" | Result: {result}"
        logger.info(log_message)
        
        # Log details if provided
        if details:
            logger.debug(f"Action details: {details}")
    
    def log_acquisition(
        self,
        source: str,
        method: str,
        files_acquired: list,
        user: Optional[str] = None
    ):
        """
        Log evidence acquisition.
        
        Args:
            source: Source of acquisition
            method: Acquisition method
            files_acquired: List of acquired files
            user: User performing acquisition
        """
        self.log_action(
            action='acquire',
            details={
                'source': source,
                'method': method,
                'files_count': len(files_acquired),
                'files': [str(f) for f in files_acquired]
            },
            user=user,
            resource=source,
            result='success' if files_acquired else 'failed'
        )
    
    def log_decryption(
        self,
        input_file: str,
        output_file: str,
        encryption_type: str,
        success: bool,
        user: Optional[str] = None
    ):
        """
        Log database decryption.
        
        Args:
            input_file: Encrypted input file
            output_file: Decrypted output file
            encryption_type: Type of encryption (crypt12/14/15)
            success: Whether decryption succeeded
            user: User performing decryption
        """
        self.log_action(
            action='decrypt',
            details={
                'input_file': input_file,
                'output_file': output_file,
                'encryption_type': encryption_type
            },
            user=user,
            resource=input_file,
            result='success' if success else 'failed'
        )
    
    def log_parsing(
        self,
        database_file: str,
        chats_found: int,
        messages_found: int,
        contacts_found: int,
        user: Optional[str] = None
    ):
        """
        Log database parsing.
        
        Args:
            database_file: Database file parsed
            chats_found: Number of chats found
            messages_found: Number of messages found
            contacts_found: Number of contacts found
            user: User performing parsing
        """
        self.log_action(
            action='parse',
            details={
                'database_file': database_file,
                'chats_found': chats_found,
                'messages_found': messages_found,
                'contacts_found': contacts_found
            },
            user=user,
            resource=database_file,
            result='success'
        )
    
    def log_report_generation(
        self,
        report_file: str,
        report_format: str,
        report_type: str,
        user: Optional[str] = None
    ):
        """
        Log report generation.
        
        Args:
            report_file: Generated report file
            report_format: Report format (html/json/csv)
            report_type: Type of report (forensic/chain_of_custody)
            user: User generating report
        """
        self.log_action(
            action='generate_report',
            details={
                'report_file': report_file,
                'report_format': report_format,
                'report_type': report_type
            },
            user=user,
            resource=report_file,
            result='success'
        )
    
    def log_hash_verification(
        self,
        filepath: str,
        hash_algorithm: str,
        hash_value: str,
        verified: bool,
        user: Optional[str] = None
    ):
        """
        Log hash verification.
        
        Args:
            filepath: File verified
            hash_algorithm: Hash algorithm used
            hash_value: Hash value
            verified: Whether verification passed
            user: User performing verification
        """
        self.log_action(
            action='verify_hash',
            details={
                'filepath': filepath,
                'hash_algorithm': hash_algorithm,
                'hash_value': hash_value
            },
            user=user,
            resource=filepath,
            result='verified' if verified else 'failed'
        )
    
    def get_audit_summary(self) -> Dict:
        """
        Get summary of audit log entries.
        
        Returns:
            Dictionary with audit summary statistics
        """
        summary = {
            'total_entries': len(self.audit_entries),
            'actions': {},
            'users': {},
            'results': {}
        }
        
        for entry in self.audit_entries:
            action = entry['action']
            summary['actions'][action] = summary['actions'].get(action, 0) + 1
            
            user = entry['user']
            summary['users'][user] = summary['users'].get(user, 0) + 1
            
            result = entry.get('result', 'unknown')
            summary['results'][result] = summary['results'].get(result, 0) + 1
        
        return summary
    
    def generate_audit_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate human-readable audit report.
        
        Args:
            output_file: Optional output file path
            
        Returns:
            Path to generated report
        """
        if output_file is None:
            output_file = self.output_dir / f"audit_report_{self.case_id}.html"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        summary = self.get_audit_summary()
        html_content = self._generate_html_report(summary)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Generated audit report: {output_file}")
        return str(output_file)
    
    def _generate_html_report(self, summary: Dict) -> str:
        """Generate HTML audit report"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Audit Report - {self.case_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .header {{ background-color: #f5f5f5; padding: 20px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Audit Report</h1>
        <p><strong>Case ID:</strong> {self.case_id}</p>
        <p><strong>Examiner:</strong> {self.examiner}</p>
        <p><strong>Report Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Entries:</strong> {summary['total_entries']}</p>
    </div>
    
    <h2>Summary</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Count</th>
        </tr>
        <tr>
            <td>Total Actions</td>
            <td>{summary['total_entries']}</td>
        </tr>
        <tr>
            <td>Unique Actions</td>
            <td>{len(summary['actions'])}</td>
        </tr>
        <tr>
            <td>Users Involved</td>
            <td>{len(summary['users'])}</td>
        </tr>
    </table>
    
    <h2>Actions Performed</h2>
    <table>
        <tr>
            <th>Action</th>
            <th>Count</th>
        </tr>
"""
        for action, count in summary['actions'].items():
            html += f"""
        <tr>
            <td>{action}</td>
            <td>{count}</td>
        </tr>
"""
        html += """
    </table>
    
    <h2>Audit Trail</h2>
    <table>
        <tr>
            <th>Timestamp</th>
            <th>Action</th>
            <th>User</th>
            <th>Resource</th>
            <th>Result</th>
        </tr>
"""
        for entry in self.audit_entries:
            html += f"""
        <tr>
            <td>{entry['timestamp']}</td>
            <td>{entry['action']}</td>
            <td>{entry['user']}</td>
            <td>{entry.get('resource', 'N/A')}</td>
            <td>{entry.get('result', 'N/A')}</td>
        </tr>
"""
        html += """
    </table>
</body>
</html>
"""
        return html

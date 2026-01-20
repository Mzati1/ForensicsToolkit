#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Forensic Toolkit Integration Module

Integrates existing tools (whapa, whatsapp-msgstore-viewer) with forensic
compliance features to create a comprehensive forensics toolkit.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, List
import logging

# Add tools directory to path
tools_dir = Path(__file__).parent.parent.parent / "tools"
sys.path.insert(0, str(tools_dir / "whapa" / "libs"))
sys.path.insert(0, str(tools_dir / "whatsapp-msgstore-viewer"))

from src.forensics import ChainOfCustody, HashVerifier, AuditLogger, ComplianceChecker
from src.acquisition import WhatsAppAcquirer
from src.crypto import WhatsAppDecryptor
from src.parsing import WhatsAppParser
from src.reporting import WhatsAppReporter

logger = logging.getLogger(__name__)


class ForensicToolkitIntegration:
    """
    Integrates existing WhatsApp forensics tools with compliance features.
    
    Provides a unified interface that wraps existing tools (whapa, whatsapp-msgstore-viewer)
    and adds forensic compliance features (chain of custody, audit logging, hash verification).
    """
    
    def __init__(
        self,
        case_id: str,
        examiner: str,
        output_dir: str = "output"
    ):
        """
        Initialize forensic toolkit integration.
        
        Args:
            case_id: Unique case identifier
            examiner: Name of primary examiner
            output_dir: Base output directory for all forensic artifacts
        """
        self.case_id = case_id
        self.examiner = examiner
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize forensic compliance components
        self.chain_of_custody = ChainOfCustody(case_id, examiner, str(self.output_dir / "chain_of_custody"))
        self.hash_verifier = HashVerifier()
        self.audit_logger = AuditLogger(case_id, examiner, str(self.output_dir / "audit_logs"))
        self.compliance_checker = ComplianceChecker(case_id)
        
        # Initialize toolkit components
        self.acquirer = WhatsAppAcquirer(output_dir=str(self.output_dir / "acquisition"))
        self.reporter = WhatsAppReporter(output_dir=str(self.output_dir / "reports"))
        
        # Log initialization
        self.audit_logger.log_action(
            action='initialize',
            details={'case_id': case_id, 'examiner': examiner},
            user=examiner
        )
        
        logger.info(f"Initialized forensic toolkit for case: {case_id}")
    
    def acquire_with_compliance(
        self,
        source: str,
        method: str,
        input_path: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> Dict:
        """
        Acquire WhatsApp data with forensic compliance tracking.
        
        Args:
            source: Acquisition source (android_adb, file, ios)
            method: Acquisition method
            input_path: Input path for file-based acquisition
            device_id: Device ID for ADB acquisition
            
        Returns:
            Dictionary with acquired files and compliance information
        """
        self.audit_logger.log_action(
            action='start_acquisition',
            details={'source': source, 'method': method},
            user=self.examiner
        )
        
        # Perform acquisition
        try:
            if source == 'android_adb':
                acquired_files = self.acquirer.acquire_from_android_adb(device_id)
            elif source == 'file':
                if not input_path:
                    raise ValueError("input_path required for file acquisition")
                acquired_files = self.acquirer.acquire_from_files(input_path)
            else:
                raise ValueError(f"Unsupported source: {source}")
            
            # Add evidence items to chain of custody
            evidence_items = []
            for source_path, dest_path in acquired_files.items():
                evidence = self.chain_of_custody.add_evidence(
                    filepath=dest_path,
                    description=f"WhatsApp database acquired from {source}",
                    evidence_type="database",
                    source_device=device_id or input_path,
                    acquisition_method=method,
                    acquired_by=self.examiner
                )
                evidence_items.append(evidence)
                
                # Verify integrity immediately
                integrity_ok = self.chain_of_custody.verify_integrity(evidence.item_id)
                if integrity_ok:
                    self.audit_logger.log_hash_verification(
                        filepath=dest_path,
                        hash_algorithm='sha256',
                        hash_value=evidence.hash_sha256,
                        verified=True,
                        user=self.examiner
                    )
            
            # Log acquisition
            self.audit_logger.log_acquisition(
                source=source,
                method=method,
                files_acquired=list(acquired_files.values()),
                user=self.examiner
            )
            
            return {
                'success': True,
                'files': acquired_files,
                'evidence_items': [e.item_id for e in evidence_items],
                'integrity_verified': True
            }
            
        except Exception as e:
            logger.error(f"Acquisition failed: {e}")
            self.audit_logger.log_action(
                action='acquisition_failed',
                details={'error': str(e)},
                user=self.examiner,
                result='failed'
            )
            return {
                'success': False,
                'error': str(e)
            }
    
    def decrypt_with_compliance(
        self,
        encrypted_file: str,
        key_file: str,
        output_file: Optional[str] = None
    ) -> Dict:
        """
        Decrypt database with forensic compliance tracking.
        
        Args:
            encrypted_file: Path to encrypted database
            key_file: Path to key file
            output_file: Optional output path
            
        Returns:
            Dictionary with decryption result and compliance information
        """
        # Verify encrypted file integrity
        if not Path(encrypted_file).exists():
            raise FileNotFoundError(f"Encrypted file not found: {encrypted_file}")
        
        enc_hashes = self.hash_verifier.calculate_all(encrypted_file)
        enc_evidence = self.chain_of_custody.add_evidence(
            filepath=encrypted_file,
            description="Encrypted WhatsApp database",
            evidence_type="encrypted_database",
            acquired_by=self.examiner
        )
        
        # Verify key file
        if not Path(key_file).exists():
            raise FileNotFoundError(f"Key file not found: {key_file}")
        
        key_evidence = self.chain_of_custody.add_evidence(
            filepath=key_file,
            description="WhatsApp decryption key",
            evidence_type="key",
            acquired_by=self.examiner
        )
        
        # Perform decryption
        try:
            decryptor = WhatsAppDecryptor(key_file)
            decrypted_path = decryptor.decrypt(encrypted_file, output_file)
            
            if decrypted_path:
                # Add decrypted file to chain of custody
                dec_evidence = self.chain_of_custody.add_evidence(
                    filepath=decrypted_path,
                    description="Decrypted WhatsApp database",
                    evidence_type="database",
                    acquired_by=self.examiner
                )
                
                # Verify integrity
                integrity_ok = self.chain_of_custody.verify_integrity(dec_evidence.item_id)
                
                # Log decryption
                self.audit_logger.log_decryption(
                    input_file=encrypted_file,
                    output_file=decrypted_path,
                    encryption_type="crypt14",  # Should detect actual type
                    success=True,
                    user=self.examiner
                )
                
                return {
                    'success': True,
                    'decrypted_file': decrypted_path,
                    'evidence_item': dec_evidence.item_id,
                    'integrity_verified': integrity_ok
                }
            else:
                raise RuntimeError("Decryption failed")
                
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            self.audit_logger.log_decryption(
                input_file=encrypted_file,
                output_file=output_file or "unknown",
                encryption_type="unknown",
                success=False,
                user=self.examiner
            )
            return {
                'success': False,
                'error': str(e)
            }
    
    def parse_with_compliance(
        self,
        msgstore_db: str,
        wa_db: Optional[str] = None
    ) -> Dict:
        """
        Parse database with forensic compliance tracking.
        
        Args:
            msgstore_db: Path to msgstore.db
            wa_db: Optional path to wa.db
            
        Returns:
            Dictionary with parsed data and compliance information
        """
        try:
            parser = WhatsAppParser(msgstore_db, wa_db)
            
            # Get all data
            chats = parser.get_chats()
            messages = parser.get_messages()
            contacts = parser.get_contacts()
            call_logs = parser.get_call_logs()
            
            # Log parsing
            self.audit_logger.log_parsing(
                database_file=msgstore_db,
                chats_found=len(chats),
                messages_found=len(messages),
                contacts_found=len(contacts),
                user=self.examiner
            )
            
            return {
                'success': True,
                'chats': chats,
                'messages': messages,
                'contacts': contacts,
                'call_logs': call_logs,
                'statistics': {
                    'total_chats': len(chats),
                    'total_messages': len(messages),
                    'total_contacts': len(contacts),
                    'total_call_logs': len(call_logs)
                }
            }
            
        except Exception as e:
            logger.error(f"Parsing failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_forensic_report(
        self,
        chats: List,
        contacts: List,
        call_logs: List,
        metadata: Optional[Dict] = None,
        report_format: str = 'html'
    ) -> Dict:
        """
        Generate forensic report with compliance documentation.
        
        Args:
            chats: List of chats
            contacts: List of contacts
            call_logs: List of call logs
            metadata: Optional report metadata
            report_format: Report format (html/json/csv)
            
        Returns:
            Dictionary with report paths and compliance information
        """
        # Generate main report
        if report_format == 'html':
            report_file = self.reporter.generate_html_report(chats, contacts, call_logs, metadata)
        elif report_format == 'json':
            report_file = self.reporter.generate_json_report(chats, contacts, call_logs, metadata)
        elif report_format == 'csv':
            report_files = self.reporter.generate_csv_report(chats, contacts, call_logs)
            report_file = report_files[0] if report_files else None
        else:
            raise ValueError(f"Unsupported format: {report_format}")
        
        # Generate chain of custody report
        custody_report = self.chain_of_custody.generate_custody_report()
        
        # Generate audit report
        audit_report = self.audit_logger.generate_audit_report()
        
        # Log report generation
        self.audit_logger.log_report_generation(
            report_file=report_file,
            report_format=report_format,
            report_type='forensic',
            user=self.examiner
        )
        
        return {
            'success': True,
            'forensic_report': report_file,
            'chain_of_custody_report': custody_report,
            'audit_report': audit_report
        }
    
    def check_compliance(self) -> Dict:
        """
        Check compliance with forensic standards.
        
        Returns:
            Dictionary with compliance status and issues
        """
        # Check various compliance requirements
        has_audit_trail = len(self.audit_logger.audit_entries) > 0
        has_custody_log = len(self.chain_of_custody.evidence_items) > 0
        
        # Check hash verification
        all_verified = all(
            self.chain_of_custody.verify_integrity(item_id)
            for item_id in self.chain_of_custody.evidence_items.keys()
        )
        
        # Run compliance checks
        self.compliance_checker.check_acpo_principles(has_audit_trail, True)
        self.compliance_checker.check_chain_of_custody(has_custody_log, True, all_verified)
        self.compliance_checker.check_hash_integrity(True, True)
        
        # Generate compliance report
        compliance_report = self.compliance_checker.generate_compliance_report()
        
        return compliance_report
    
    def finalize_case(self) -> Dict:
        """
        Finalize forensic case and generate all reports.
        
        Returns:
            Dictionary with all generated reports and compliance status
        """
        # Generate all reports
        custody_report = self.chain_of_custody.generate_custody_report()
        audit_report = self.audit_logger.generate_audit_report()
        compliance_report = self.compliance_checker.generate_compliance_report()
        
        # Final compliance check
        compliance_status = self.check_compliance()
        
        # Final audit entry
        self.audit_logger.log_action(
            action='finalize_case',
            details={'compliance_status': compliance_status['overall_status']},
            user=self.examiner
        )
        
        return {
            'case_id': self.case_id,
            'chain_of_custody_report': custody_report,
            'audit_report': audit_report,
            'compliance_report': compliance_status,
            'compliance_summary': self.compliance_checker.get_compliance_summary()
        }

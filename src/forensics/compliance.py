#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compliance Module

Ensures forensic investigations comply with legal requirements and best practices:
- ACPO (Association of Chief Police Officers) Principles
- GDPR compliance
- Chain of custody requirements
- Evidence handling standards
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ComplianceChecker:
    """
    Checks compliance with forensic standards and legal requirements.
    
    Implements checks for:
    - ACPO principles
    - GDPR compliance
    - Chain of custody requirements
    - Evidence integrity
    - Audit trail completeness
    """
    
    # ACPO Principles
    ACPO_PRINCIPLE_1 = "No action taken by law enforcement agencies or their agents should change data held on a computer or storage media which may subsequently be relied upon in court."
    ACPO_PRINCIPLE_2 = "In circumstances where a person finds it necessary to access original data held on a computer or storage media, that person must be competent to do so and be able to give evidence explaining the relevance and the implications of their actions."
    ACPO_PRINCIPLE_3 = "An audit trail or other record of all processes applied to computer-based electronic evidence should be created and preserved. An independent third party should be able to examine those processes and achieve the same result."
    ACPO_PRINCIPLE_4 = "The person in charge of the investigation has overall responsibility for ensuring that the law and these principles are adhered to."
    
    def __init__(self, case_id: str):
        """
        Initialize compliance checker.
        
        Args:
            case_id: Unique case identifier
        """
        self.case_id = case_id
        self.compliance_issues: List[Dict] = []
        self.compliance_warnings: List[Dict] = []
    
    def check_acpo_principles(self, has_audit_trail: bool, original_preserved: bool) -> bool:
        """
        Check compliance with ACPO principles.
        
        Args:
            has_audit_trail: Whether complete audit trail exists
            original_preserved: Whether original evidence has been preserved
            
        Returns:
            True if compliant, False otherwise
        """
        compliant = True
        
        # Principle 1: Original data must not be changed
        if not original_preserved:
            self.compliance_issues.append({
                'principle': 'ACPO Principle 1',
                'issue': 'Original evidence may have been modified',
                'severity': 'high',
                'recommendation': 'Ensure working on copies, not originals'
            })
            compliant = False
        
        # Principle 3: Audit trail must exist
        if not has_audit_trail:
            self.compliance_issues.append({
                'principle': 'ACPO Principle 3',
                'issue': 'Incomplete or missing audit trail',
                'severity': 'high',
                'recommendation': 'Ensure all actions are logged in audit trail'
            })
            compliant = False
        
        return compliant
    
    def check_gdpr_compliance(
        self,
        has_legal_basis: bool,
        data_minimization: bool,
        purpose_limitation: bool,
        retention_period: Optional[int] = None
    ) -> bool:
        """
        Check GDPR compliance.
        
        Args:
            has_legal_basis: Whether legal basis for processing exists
            data_minimization: Whether only necessary data is processed
            purpose_limitation: Whether data is used only for stated purpose
            retention_period: Data retention period in days
            
        Returns:
            True if compliant, False otherwise
        """
        compliant = True
        
        if not has_legal_basis:
            self.compliance_warnings.append({
                'regulation': 'GDPR Article 6',
                'issue': 'Legal basis for processing personal data not documented',
                'severity': 'medium',
                'recommendation': 'Document legal basis for processing (e.g., legal obligation, legitimate interest)'
            })
        
        if not data_minimization:
            self.compliance_warnings.append({
                'regulation': 'GDPR Article 5(1)(c)',
                'issue': 'Data minimization principle may not be followed',
                'severity': 'medium',
                'recommendation': 'Process only data necessary for the investigation'
            })
        
        if not purpose_limitation:
            self.compliance_warnings.append({
                'regulation': 'GDPR Article 5(1)(b)',
                'issue': 'Purpose limitation principle may not be followed',
                'severity': 'medium',
                'recommendation': 'Use data only for the stated investigative purpose'
            })
        
        if retention_period and retention_period > 365:
            self.compliance_warnings.append({
                'regulation': 'GDPR Article 5(1)(e)',
                'issue': f'Long retention period ({retention_period} days)',
                'severity': 'low',
                'recommendation': 'Ensure retention period is justified and documented'
            })
        
        return compliant
    
    def check_chain_of_custody(
        self,
        has_custody_log: bool,
        all_transfers_documented: bool,
        integrity_verified: bool
    ) -> bool:
        """
        Check chain of custody requirements.
        
        Args:
            has_custody_log: Whether chain of custody log exists
            all_transfers_documented: Whether all transfers are documented
            integrity_verified: Whether evidence integrity has been verified
            
        Returns:
            True if compliant, False otherwise
        """
        compliant = True
        
        if not has_custody_log:
            self.compliance_issues.append({
                'requirement': 'Chain of Custody',
                'issue': 'Chain of custody log missing',
                'severity': 'high',
                'recommendation': 'Maintain complete chain of custody documentation'
            })
            compliant = False
        
        if not all_transfers_documented:
            self.compliance_issues.append({
                'requirement': 'Chain of Custody',
                'issue': 'Not all evidence transfers are documented',
                'severity': 'medium',
                'recommendation': 'Document every transfer of evidence'
            })
        
        if not integrity_verified:
            self.compliance_warnings.append({
                'requirement': 'Evidence Integrity',
                'issue': 'Evidence integrity not verified',
                'severity': 'medium',
                'recommendation': 'Verify evidence integrity using hash values'
            })
        
        return compliant
    
    def check_hash_integrity(self, has_hash_verification: bool, hashes_stored: bool) -> bool:
        """
        Check hash integrity verification.
        
        Args:
            has_hash_verification: Whether hash verification has been performed
            hashes_stored: Whether hash values are stored
            
        Returns:
            True if compliant, False otherwise
        """
        compliant = True
        
        if not has_hash_verification:
            self.compliance_issues.append({
                'requirement': 'Hash Verification',
                'issue': 'Hash verification not performed',
                'severity': 'high',
                'recommendation': 'Verify evidence integrity using hash values (MD5, SHA256)'
            })
            compliant = False
        
        if not hashes_stored:
            self.compliance_issues.append({
                'requirement': 'Hash Storage',
                'issue': 'Hash values not stored for evidence',
                'severity': 'high',
                'recommendation': 'Store hash values (MD5, SHA256) for all evidence'
            })
            compliant = False
        
        return compliant
    
    def generate_compliance_report(self) -> Dict:
        """
        Generate compliance report.
        
        Returns:
            Dictionary with compliance status and issues
        """
        report = {
            'case_id': self.case_id,
            'report_date': datetime.now().isoformat(),
            'total_issues': len(self.compliance_issues),
            'total_warnings': len(self.compliance_warnings),
            'high_severity_issues': len([i for i in self.compliance_issues if i['severity'] == 'high']),
            'compliance_issues': self.compliance_issues,
            'compliance_warnings': self.compliance_warnings,
            'overall_status': 'compliant' if len(self.compliance_issues) == 0 else 'non-compliant'
        }
        
        return report
    
    def get_compliance_summary(self) -> str:
        """
        Get summary of compliance status.
        
        Returns:
            Human-readable compliance summary
        """
        issues_count = len(self.compliance_issues)
        warnings_count = len(self.compliance_warnings)
        high_issues = len([i for i in self.compliance_issues if i['severity'] == 'high'])
        
        summary = f"""
Compliance Summary for Case: {self.case_id}
===========================================
Total Issues: {issues_count}
  - High Severity: {high_issues}
  - Medium Severity: {len([i for i in self.compliance_issues if i['severity'] == 'medium'])}
  - Low Severity: {len([i for i in self.compliance_issues if i['severity'] == 'low'])}
Total Warnings: {warnings_count}

Overall Status: {'COMPLIANT' if issues_count == 0 else 'NON-COMPLIANT'}
"""
        
        if issues_count > 0:
            summary += "\nCritical Issues:\n"
            for issue in self.compliance_issues:
                if issue['severity'] == 'high':
                    summary += f"  - {issue['issue']}\n"
                    summary += f"    Recommendation: {issue['recommendation']}\n"
        
        return summary

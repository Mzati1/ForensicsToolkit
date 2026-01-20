#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chain of Custody Module

Tracks evidence handling throughout the forensic process to ensure legal admissibility.
Implements ACPO principles and maintains verifiable audit trail.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class EvidenceItem:
    """Represents a piece of evidence with chain of custody"""
    item_id: str
    filename: str
    filepath: str
    description: str
    acquired_at: str
    acquired_by: str
    hash_md5: str
    hash_sha256: str
    size_bytes: int
    evidence_type: str  # database, key, media, report, etc.
    source_device: Optional[str] = None
    acquisition_method: Optional[str] = None
    custody_chain: List[Dict] = None
    
    def __post_init__(self):
        if self.custody_chain is None:
            self.custody_chain = []


class ChainOfCustody:
    """
    Manages chain of custody for forensic evidence.
    
    Ensures legal admissibility by tracking:
    - Who handled the evidence
    - When it was handled
    - What actions were performed
    - Integrity verification (hashes)
    """
    
    def __init__(self, case_id: str, examiner: str, output_dir: str = "output/chain_of_custody"):
        """
        Initialize chain of custody tracker.
        
        Args:
            case_id: Unique case identifier
            examiner: Name of primary examiner
            output_dir: Directory for custody documentation
        """
        self.case_id = case_id
        self.examiner = examiner
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.evidence_items: Dict[str, EvidenceItem] = {}
        self.chain_log_file = self.output_dir / f"chain_of_custody_{case_id}.json"
        
        # Load existing chain if it exists
        self._load_chain()
    
    def _load_chain(self):
        """Load existing chain of custody from file"""
        if self.chain_log_file.exists():
            try:
                with open(self.chain_log_file, 'r') as f:
                    data = json.load(f)
                    for item_data in data.get('evidence_items', []):
                        item = EvidenceItem(**item_data)
                        self.evidence_items[item.item_id] = item
                logger.info(f"Loaded {len(self.evidence_items)} evidence items from chain of custody")
            except Exception as e:
                logger.warning(f"Could not load chain of custody: {e}")
    
    def _save_chain(self):
        """Save chain of custody to file"""
        data = {
            'case_id': self.case_id,
            'examiner': self.examiner,
            'created_at': datetime.now().isoformat(),
            'evidence_items': [asdict(item) for item in self.evidence_items.values()]
        }
        
        with open(self.chain_log_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _calculate_hashes(self, filepath: str) -> tuple:
        """
        Calculate MD5 and SHA256 hashes of file.
        
        Args:
            filepath: Path to file
            
        Returns:
            Tuple of (MD5 hash, SHA256 hash)
        """
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)
        
        return md5_hash.hexdigest(), sha256_hash.hexdigest()
    
    def add_evidence(
        self,
        filepath: str,
        description: str,
        evidence_type: str,
        source_device: Optional[str] = None,
        acquisition_method: Optional[str] = None,
        acquired_by: Optional[str] = None
    ) -> EvidenceItem:
        """
        Add evidence item to chain of custody.
        
        Args:
            filepath: Path to evidence file
            description: Description of evidence
            evidence_type: Type of evidence (database, key, media, etc.)
            source_device: Source device identifier
            acquisition_method: Method used to acquire evidence
            acquired_by: Name of person who acquired evidence
            
        Returns:
            EvidenceItem object
        """
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"Evidence file not found: {filepath}")
        
        # Generate unique evidence ID
        item_id = f"{self.case_id}_{evidence_type}_{len(self.evidence_items) + 1:04d}"
        
        # Calculate file hashes
        md5_hash, sha256_hash = self._calculate_hashes(filepath)
        file_size = file_path.stat().st_size
        
        # Create evidence item
        evidence = EvidenceItem(
            item_id=item_id,
            filename=file_path.name,
            filepath=str(file_path.absolute()),
            description=description,
            acquired_at=datetime.now().isoformat(),
            acquired_by=acquired_by or self.examiner,
            hash_md5=md5_hash,
            hash_sha256=sha256_hash,
            size_bytes=file_size,
            evidence_type=evidence_type,
            source_device=source_device,
            acquisition_method=acquisition_method
        )
        
        # Add initial custody entry
        evidence.custody_chain.append({
            'action': 'acquired',
            'timestamp': evidence.acquired_at,
            'handler': evidence.acquired_by,
            'notes': f"Initial acquisition via {acquisition_method or 'unknown method'}"
        })
        
        self.evidence_items[item_id] = evidence
        self._save_chain()
        
        logger.info(f"Added evidence to chain of custody: {item_id} - {description}")
        return evidence
    
    def verify_integrity(self, item_id: str) -> bool:
        """
        Verify integrity of evidence item by recalculating hashes.
        
        Args:
            item_id: Evidence item ID
            
        Returns:
            True if hashes match, False otherwise
        """
        if item_id not in self.evidence_items:
            raise ValueError(f"Evidence item not found: {item_id}")
        
        evidence = self.evidence_items[item_id]
        file_path = Path(evidence.filepath)
        
        if not file_path.exists():
            logger.error(f"Evidence file no longer exists: {evidence.filepath}")
            return False
        
        # Recalculate hashes
        current_md5, current_sha256 = self._calculate_hashes(evidence.filepath)
        
        # Compare with stored hashes
        if current_md5 != evidence.hash_md5 or current_sha256 != evidence.hash_sha256:
            logger.error(f"Integrity check failed for {item_id}: hashes do not match")
            return False
        
        logger.info(f"Integrity verified for {item_id}")
        return True
    
    def add_custody_entry(
        self,
        item_id: str,
        action: str,
        handler: str,
        notes: Optional[str] = None
    ):
        """
        Add entry to custody chain (e.g., examination, transfer, analysis).
        
        Args:
            item_id: Evidence item ID
            action: Action performed (examined, transferred, analyzed, etc.)
            handler: Name of person performing action
            notes: Optional notes about the action
        """
        if item_id not in self.evidence_items:
            raise ValueError(f"Evidence item not found: {item_id}")
        
        entry = {
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'handler': handler,
            'notes': notes or ''
        }
        
        self.evidence_items[item_id].custody_chain.append(entry)
        self._save_chain()
        
        logger.info(f"Added custody entry for {item_id}: {action} by {handler}")
    
    def generate_custody_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate chain of custody report.
        
        Args:
            output_file: Optional output file path
            
        Returns:
            Path to generated report
        """
        if output_file is None:
            output_file = self.output_dir / f"custody_report_{self.case_id}.html"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        html_content = self._generate_html_report()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Generated chain of custody report: {output_file}")
        return str(output_file)
    
    def _generate_html_report(self) -> str:
        """Generate HTML chain of custody report"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Chain of Custody Report - {self.case_id}</title>
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
        <h1>Chain of Custody Report</h1>
        <p><strong>Case ID:</strong> {self.case_id}</p>
        <p><strong>Primary Examiner:</strong> {self.examiner}</p>
        <p><strong>Report Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <h2>Evidence Items</h2>
    <table>
        <tr>
            <th>Item ID</th>
            <th>Filename</th>
            <th>Description</th>
            <th>Type</th>
            <th>Size (bytes)</th>
            <th>MD5 Hash</th>
            <th>SHA256 Hash</th>
            <th>Acquired At</th>
            <th>Acquired By</th>
        </tr>
"""
        
        for evidence in self.evidence_items.values():
            html += f"""
        <tr>
            <td>{evidence.item_id}</td>
            <td>{evidence.filename}</td>
            <td>{evidence.description}</td>
            <td>{evidence.evidence_type}</td>
            <td>{evidence.size_bytes:,}</td>
            <td><code>{evidence.hash_md5}</code></td>
            <td><code>{evidence.hash_sha256}</code></td>
            <td>{evidence.acquired_at}</td>
            <td>{evidence.acquired_by}</td>
        </tr>
"""
        
        html += """
    </table>
    
    <h2>Custody Chain Details</h2>
"""
        
        for evidence in self.evidence_items.values():
            html += f"""
    <h3>{evidence.item_id}: {evidence.filename}</h3>
    <table>
        <tr>
            <th>Timestamp</th>
            <th>Action</th>
            <th>Handler</th>
            <th>Notes</th>
        </tr>
"""
            for entry in evidence.custody_chain:
                html += f"""
        <tr>
            <td>{entry['timestamp']}</td>
            <td>{entry['action']}</td>
            <td>{entry['handler']}</td>
            <td>{entry.get('notes', '')}</td>
        </tr>
"""
            html += """
    </table>
"""
        
        html += """
</body>
</html>
"""
        return html

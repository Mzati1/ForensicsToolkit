#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hash Verification Module

Provides file integrity verification using MD5, SHA256, and other hash algorithms.
Ensures data integrity throughout the forensic process.
"""

import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class HashVerifier:
    """
    Provides hash calculation and verification for forensic files.
    
    Supports multiple hash algorithms to ensure data integrity
    throughout the forensic investigation process.
    """
    
    @staticmethod
    def calculate_md5(filepath: str, chunk_size: int = 8192) -> str:
        """
        Calculate MD5 hash of file.
        
        Args:
            filepath: Path to file
            chunk_size: Size of chunks to read at a time
            
        Returns:
            MD5 hash as hexadecimal string
        """
        md5_hash = hashlib.md5()
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    @staticmethod
    def calculate_sha256(filepath: str, chunk_size: int = 8192) -> str:
        """
        Calculate SHA256 hash of file.
        
        Args:
            filepath: Path to file
            chunk_size: Size of chunks to read at a time
            
        Returns:
            SHA256 hash as hexadecimal string
        """
        sha256_hash = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def calculate_sha512(filepath: str, chunk_size: int = 8192) -> str:
        """
        Calculate SHA512 hash of file.
        
        Args:
            filepath: Path to file
            chunk_size: Size of chunks to read at a time
            
        Returns:
            SHA512 hash as hexadecimal string
        """
        sha512_hash = hashlib.sha512()
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha512_hash.update(chunk)
        return sha512_hash.hexdigest()
    
    @staticmethod
    def calculate_all(filepath: str) -> Dict[str, str]:
        """
        Calculate all supported hashes for a file.
        
        Args:
            filepath: Path to file
            
        Returns:
            Dictionary with hash algorithm names as keys and hashes as values
        """
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        sha512_hash = hashlib.sha512()
        
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)
                sha512_hash.update(chunk)
        
        return {
            'md5': md5_hash.hexdigest(),
            'sha256': sha256_hash.hexdigest(),
            'sha512': sha512_hash.hexdigest()
        }
    
    @staticmethod
    def verify_hash(filepath: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
        """
        Verify file hash matches expected value.
        
        Args:
            filepath: Path to file
            expected_hash: Expected hash value
            algorithm: Hash algorithm to use (md5, sha256, sha512)
            
        Returns:
            True if hashes match, False otherwise
        """
        file_path = Path(filepath)
        if not file_path.exists():
            logger.error(f"File not found: {filepath}")
            return False
        
        if algorithm.lower() == 'md5':
            calculated_hash = HashVerifier.calculate_md5(filepath)
        elif algorithm.lower() == 'sha256':
            calculated_hash = HashVerifier.calculate_sha256(filepath)
        elif algorithm.lower() == 'sha512':
            calculated_hash = HashVerifier.calculate_sha512(filepath)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        match = calculated_hash.lower() == expected_hash.lower()
        
        if not match:
            logger.warning(
                f"Hash verification failed for {filepath}\n"
                f"Expected: {expected_hash}\n"
                f"Calculated: {calculated_hash}"
            )
        else:
            logger.info(f"Hash verification passed for {filepath}")
        
        return match
    
    @staticmethod
    def compare_files(file1: str, file2: str, algorithm: str = 'sha256') -> bool:
        """
        Compare two files using hash values.
        
        Args:
            file1: Path to first file
            file2: Path to second file
            algorithm: Hash algorithm to use
            
        Returns:
            True if files are identical, False otherwise
        """
        if algorithm.lower() == 'md5':
            hash1 = HashVerifier.calculate_md5(file1)
            hash2 = HashVerifier.calculate_md5(file2)
        elif algorithm.lower() == 'sha256':
            hash1 = HashVerifier.calculate_sha256(file1)
            hash2 = HashVerifier.calculate_sha256(file2)
        elif algorithm.lower() == 'sha512':
            hash1 = HashVerifier.calculate_sha512(file1)
            hash2 = HashVerifier.calculate_sha512(file2)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        match = hash1 == hash2
        
        if match:
            logger.info(f"Files are identical: {file1} == {file2}")
        else:
            logger.warning(f"Files differ: {file1} != {file2}")
        
        return match

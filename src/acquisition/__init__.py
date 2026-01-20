"""
WhatsApp Forensics Toolkit - Acquisition Module

This module handles the acquisition of WhatsApp data from various sources:
- Android devices (ADB)
- iOS devices (iTunes backup)
- Google Drive backups
- Local file system
"""

from .acquirer import WhatsAppAcquirer, AcquisitionSource

__all__ = ['WhatsAppAcquirer', 'AcquisitionSource']

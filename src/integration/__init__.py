"""
WhatsApp Forensics Toolkit - Integration Module

Integrates existing tools (whapa, whatsapp-msgstore-viewer) with
forensic compliance features (chain of custody, audit logging, hash verification).
"""

from .toolkit_integration import ForensicToolkitIntegration

__all__ = ['ForensicToolkitIntegration']

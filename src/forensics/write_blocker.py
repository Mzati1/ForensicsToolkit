#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Software write blocker checks for ADB acquisition workflows.

This module enforces a defensive policy that the toolkit should only perform
logical read operations when collecting evidence from Android devices.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class WriteBlockerStatus:
    """Represents write-blocker enforcement status."""

    enabled: bool
    passed: bool
    mode: str
    reason: str
    device_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "enabled": self.enabled,
            "passed": self.passed,
            "mode": self.mode,
            "reason": self.reason,
            "device_id": self.device_id,
        }


class SoftwareWriteBlocker:
    """
    Performs lightweight software write-blocker checks for Android ADB workflows.

    The policy blocks workflows where `adbd` appears to run as root, because that
    often indicates elevated access modes where accidental writes are easier.
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def validate_for_adb(self, device_id: Optional[str] = None) -> WriteBlockerStatus:
        """Validate that ADB session is in safe read-only acquisition mode."""
        if not self.enabled:
            return WriteBlockerStatus(
                enabled=False,
                passed=True,
                mode="disabled",
                reason="Software write blocker disabled by operator",
                device_id=device_id,
            )

        adb_cmd = ["adb"]
        if device_id:
            adb_cmd.extend(["-s", device_id])

        try:
            # If this command returns uid=0, the session is privileged and we
            # fail closed to avoid accidental writes on source evidence.
            proc = subprocess.run(
                adb_cmd + ["shell", "id"],
                capture_output=True,
                text=True,
                timeout=8,
            )
        except FileNotFoundError:
            return WriteBlockerStatus(
                enabled=True,
                passed=False,
                mode="adb_unavailable",
                reason="ADB binary not found; cannot enforce write blocker policy",
                device_id=device_id,
            )
        except Exception as exc:
            return WriteBlockerStatus(
                enabled=True,
                passed=False,
                mode="validation_error",
                reason=f"Unable to validate write blocker state: {exc}",
                device_id=device_id,
            )

        identity = (proc.stdout or "").strip()
        if proc.returncode != 0 or not identity:
            return WriteBlockerStatus(
                enabled=True,
                passed=False,
                mode="validation_error",
                reason="Could not read device identity via `adb shell id`",
                device_id=device_id,
            )

        if "uid=0" in identity:
            return WriteBlockerStatus(
                enabled=True,
                passed=False,
                mode="root_session_blocked",
                reason="ADB session appears rooted (uid=0); blocked by write blocker policy",
                device_id=device_id,
            )

        return WriteBlockerStatus(
            enabled=True,
            passed=True,
            mode="logical_read_only",
            reason="ADB session is non-root; logical read-only acquisition policy enforced",
            device_id=device_id,
        )

"""
Register field access types and related constants.

This module defines the access patterns for register bit fields and any
related constants or utilities for working with access types.
"""

from enum import Enum


class AccessType(Enum):
    """
    Register field access types.

    This enum defines the valid access patterns for register bit fields:
    - RO: Read-only fields (e.g., status bits, hardware state)
    - WO: Write-only fields (e.g., command triggers, control pulses)
    - RW: Read-write fields (e.g., configuration settings)
    - RW1C: Read-write-1-to-clear fields (e.g., interrupt status flags)
    - W1SC: Write-1-self-clearing fields (e.g., command strobes that auto-clear)
    """
    RO = 'ro'       # Read-only
    WO = 'wo'       # Write-only
    RW = 'rw'       # Read-write
    RW1C = 'rw1c'   # Read-write-1-to-clear
    W1SC = 'w1sc'   # Write-1-self-clearing


def validate_access_type(access: str) -> bool:
    """
    Validate if an access type string is valid.

    Args:
        access: Access type string to validate

    Returns:
        True if valid, False otherwise
    """
    valid_access = {at.value for at in AccessType}
    return access in valid_access


def get_valid_access_types() -> set[str]:
    """Get set of all valid access type strings."""
    return {at.value for at in AccessType}

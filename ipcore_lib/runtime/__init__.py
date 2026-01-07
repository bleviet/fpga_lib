"""
Runtime register access for hardware I/O.

This module provides classes for reading/writing hardware registers at runtime.
For YAML schema definitions, use ipcore_lib.model instead.
"""

from .register import (
    AccessType,
    BitField,
    Register,
    AbstractBusInterface,
    RegisterArrayAccessor,
)

__all__ = [
    'AccessType',
    'BitField',
    'Register',
    'AbstractBusInterface',
    'RegisterArrayAccessor',
]

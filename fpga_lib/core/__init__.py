"""
FPGA Library Core Module

This module provides core abstractions and utilities for FPGA IP core development,
including register abstractions, data types, interfaces, and common utilities.
"""

from .register import BitField, Register, AbstractBusInterface, RegisterArrayAccessor
from .data_types import *
from .interface import *
from .ip_core import *
from .port import *

__all__ = [
    # Register abstractions
    'BitField',
    'Register',
    'AbstractBusInterface',
    'RegisterArrayAccessor',

    # Re-exported from other modules
    'VHDLBaseType',
    'VHDLDataType',
    'VHDLRange',
    'VHDLArray',
    'VHDLRecord',
    'VHDLConstraint',
]

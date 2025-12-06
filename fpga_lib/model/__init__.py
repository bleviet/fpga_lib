"""
Pydantic-based canonical data models for FPGA IP cores.

This module provides the single source of truth for IP core representation,
with validation-first design and computed properties.
"""

from .base import VLNV, Parameter
from .bus import BusInterface, BusType, PortMapping, PortWidthOverride, ArrayConfig
from .memory import (
    AccessType,
    MemoryMap,
    AddressBlock,
    Register,
    BitField,
    RegisterArray,
    MemoryMapReference,
)
from .clock_reset import Clock, Reset, Polarity
from .port import Port, PortDirection
from .fileset import FileSet, File, FileType
from .core import IpCore

__all__ = [
    # Base
    "VLNV",
    "Parameter",
    # Bus
    "BusInterface",
    "BusType",
    "PortMapping",
    "PortWidthOverride",
    "ArrayConfig",
    # Memory
    "AccessType",
    "MemoryMap",
    "AddressBlock",
    "Register",
    "BitField",
    "RegisterArray",
    "MemoryMapReference",
    # Clock/Reset
    "Clock",
    "Reset",
    "Polarity",
    # Port
    "Port",
    "PortDirection",
    # FileSet
    "FileSet",
    "File",
    "FileType",
    # Core
    "IpCore",
]

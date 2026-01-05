"""
Pydantic-based canonical data models for FPGA IP cores.

This module provides the single source of truth for IP core representation,
with validation-first design and computed properties.

For runtime register access (hardware I/O), use fpga_lib.runtime.register.
"""

from .base import VLNV, Parameter, Polarity
from .bus import BusInterface, BusType, ArrayConfig
from .memory import (
    AccessType,
    MemoryMap,
    AddressBlock,
    RegisterDef,
    BitFieldDef,
    RegisterArrayDef,
    MemoryMapReference,
    BlockUsage,
    # Backward compatibility aliases
    Register,
    BitField,
    RegisterArray,
)
from .clock_reset import Clock, Reset
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
    "ArrayConfig",
    # Memory (new names)
    "AccessType",
    "MemoryMap",
    "AddressBlock",
    "RegisterDef",
    "BitFieldDef",
    "RegisterArrayDef",
    "MemoryMapReference",
    "BlockUsage",
    # Memory (backward compatibility aliases)
    "Register",
    "BitField",
    "RegisterArray",
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


"""
Pydantic-based canonical data models for FPGA IP cores.

This module provides the single source of truth for IP core representation,
with validation-first design and computed properties.

For runtime register access (hardware I/O), use ipcore_lib.runtime.register.
"""

from .base import VLNV, Parameter, Polarity
from .bus import ArrayConfig, BusInterface, BusType
from .clock_reset import Clock, Reset
from .core import IpCore
from .fileset import File, FileSet, FileType
from .memory import (  # Backward compatibility aliases
    AccessType,
    AddressBlock,
    BitField,
    BitFieldDef,
    BlockUsage,
    MemoryMap,
    MemoryMapReference,
    Register,
    RegisterArray,
    RegisterArrayDef,
    RegisterDef,
)
from .port import Port, PortDirection

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

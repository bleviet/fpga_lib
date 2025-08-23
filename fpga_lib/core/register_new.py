"""
Register abstraction module with clean separation of concerns.

This module provides the main interface for register definitions and access
by importing and re-exporting classes from focused submodules.

The register implementation is now split into several focused modules:
- access_types: AccessType enum and validation
- bit_field: BitField class with bit manipulation logic
- bus_interface: AbstractBusInterface for bus abstraction
- register_def: Pure Register dataclass definition
- memory_map: MemoryMap and RegisterProxy for access
- array_accessor: RegisterArrayAccessor for array handling
- register_utils: Utility functions for validation, testing, documentation

This separation provides:
- Single responsibility for each module
- Better testability of individual components
- Cleaner dependencies and imports
- Easier maintenance and extension
"""

# Re-export all public classes and functions for backward compatibility
from .access_types import AccessType, validate_access_type, get_valid_access_types
from .bit_field import BitField
from .bus_interface import AbstractBusInterface
from .register_def import Register
from .memory_map import MemoryMap, RegisterProxy
from .array_accessor import RegisterArrayAccessor
from .register_utils import (
    validate_register_layout,
    generate_test_patterns,
    generate_register_documentation
)

# Check for optional bitstring dependency
try:
    from bitstring import BitArray
    BITSTRING_AVAILABLE = True
except ImportError:
    BITSTRING_AVAILABLE = False
    BitArray = None

__all__ = [
    # Core classes
    'AccessType',
    'BitField',
    'Register',
    'MemoryMap',
    'RegisterProxy',
    'RegisterArrayAccessor',
    'AbstractBusInterface',

    # Utility functions
    'validate_access_type',
    'get_valid_access_types',
    'validate_register_layout',
    'generate_test_patterns',
    'generate_register_documentation',

    # Optional dependency info
    'BITSTRING_AVAILABLE',
    'BitArray',
]

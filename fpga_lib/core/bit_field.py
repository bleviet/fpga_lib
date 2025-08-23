"""
Bit field definition and manipulation utilities.

This module provides the BitField class for defining register bit fields
with validation, bit manipulation operations, and access control.
"""

from dataclasses import dataclass, field
from typing import Union, Optional
from .access_types import AccessType, validate_access_type, get_valid_access_types


@dataclass
class BitField:
    """
    Represents a bit field within a register.

    This is a generic bit field definition that can be used by any IP core
    driver to define register fields with proper access control and validation.

    Attributes:
        name: Human-readable name of the bit field
        bit_range: Bit range specification - can be int (single bit) or string ("7:4" for range)
        access: Access type - AccessType enum or string ('ro', 'wo', 'rw', 'rw1c', 'w1sc')
        description: Optional human-readable description of the bit field
        reset_value: Default/reset value of the field (optional)
    """
    name: str
    bit_range: Union[int, str]
    access: Union[AccessType, str] = AccessType.RW
    description: str = ''
    reset_value: Optional[int] = None

    # These will be calculated in __post_init__
    offset: int = field(init=False)
    width: int = field(init=False)

    def __post_init__(self):
        """Validate bit field parameters and parse bit range."""
        # Parse bit range to get offset and width
        self.offset, self.width = self._parse_bit_range(self.bit_range)

        if self.width <= 0:
            raise ValueError(f"Bit field '{self.name}' width must be positive, got {self.width}")
        if self.width > 32:
            raise ValueError(f"Bit field '{self.name}' width cannot exceed 32 bits, got {self.width}")
        if self.offset < 0:
            raise ValueError(f"Bit field '{self.name}' offset must be non-negative, got {self.offset}")
        if self.offset + self.width > 32:
            raise ValueError(f"Bit field '{self.name}' extends beyond 32-bit register boundary")

        # Normalize access to string for internal consistency
        if isinstance(self.access, AccessType):
            self.access = self.access.value
        elif isinstance(self.access, str):
            # Validate string access types
            if not validate_access_type(self.access):
                valid_access = get_valid_access_types()
                raise ValueError(f"Bit field '{self.name}' access must be one of {valid_access}, got '{self.access}'")
        else:
            raise ValueError(f"Bit field '{self.name}' access must be AccessType enum or string, got {type(self.access)}")

        # Validate reset value if provided
        if self.reset_value is not None:
            max_value = (1 << self.width) - 1
            if self.reset_value < 0 or self.reset_value > max_value:
                raise ValueError(f"Bit field '{self.name}' reset value {self.reset_value} out of range [0, {max_value}]")

    def _parse_bit_range(self, bit_range: Union[int, str]) -> tuple[int, int]:
        """Parse bit range specification into offset and width."""
        if isinstance(bit_range, int):
            # Single bit
            return bit_range, 1
        elif isinstance(bit_range, str):
            # Parse range string like "7:4" or "[7:4]"
            bit_range = bit_range.strip('[]')
            if ':' in bit_range:
                high_str, low_str = bit_range.split(':')
                high_bit = int(high_str.strip())
                low_bit = int(low_str.strip())
                if high_bit < low_bit:
                    raise ValueError(f"Invalid bit range '{bit_range}': high bit must be >= low bit")
                return low_bit, high_bit - low_bit + 1
            else:
                # Single bit as string
                return int(bit_range), 1
        else:
            raise ValueError(f"Bit range must be int or string, got {type(bit_range)}")

    @property
    def mask(self) -> int:
        """Get the bit mask for this field within the register."""
        return ((1 << self.width) - 1) << self.offset

    @property
    def max_value(self) -> int:
        """Get the maximum value that can be stored in this field."""
        return (1 << self.width) - 1

    def extract_value(self, register_value: int) -> int:
        """Extract this field's value from a complete register value."""
        return (register_value >> self.offset) & ((1 << self.width) - 1)

    def insert_value(self, register_value: int, field_value: int) -> int:
        """Insert this field's value into a complete register value."""
        if field_value > self.max_value:
            raise ValueError(f"Value {field_value} exceeds field '{self.name}' maximum {self.max_value}")

        # Clear the field bits
        cleared_value = register_value & ~self.mask
        # Insert the new field value
        return cleared_value | ((field_value << self.offset) & self.mask)

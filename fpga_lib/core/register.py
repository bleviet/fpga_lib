"""
Generic Register and BitField Classes

This module provides generic, reusable register abstraction classes that can be
used by any IP core driver implementation. These classes handle bit-wise
operations, field validation, and access control.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from abc import ABC, abstractmethod


@dataclass
class BitField:
    """
    Represents a bit field within a register.

    This is a generic bit field definition that can be used by any IP core
    driver to define register fields with proper access control and validation.

    Attributes:
        name: Human-readable name of the bit field
        offset: Bit position within the register (0-based, LSB = 0)
        width: Number of bits in the field (1-32)
        access: Access type - 'r' (read-only), 'w' (write-only), 'rw' (read-write)
        description: Optional human-readable description of the bit field
        reset_value: Default/reset value of the field (optional)
    """
    name: str
    offset: int
    width: int
    access: str = 'rw'
    description: str = ''
    reset_value: Optional[int] = None

    def __post_init__(self):
        """Validate bit field parameters after initialization."""
        if self.width <= 0:
            raise ValueError(f"Bit field '{self.name}' width must be positive, got {self.width}")
        if self.width > 32:
            raise ValueError(f"Bit field '{self.name}' width cannot exceed 32 bits, got {self.width}")
        if self.offset < 0:
            raise ValueError(f"Bit field '{self.name}' offset must be non-negative, got {self.offset}")
        if self.offset + self.width > 32:
            raise ValueError(f"Bit field '{self.name}' extends beyond 32-bit register boundary")
        if self.access not in ['r', 'w', 'rw']:
            raise ValueError(f"Bit field '{self.name}' access must be 'r', 'w', or 'rw', got '{self.access}'")

        # Validate reset value if provided
        if self.reset_value is not None:
            max_value = (1 << self.width) - 1
            if self.reset_value < 0 or self.reset_value > max_value:
                raise ValueError(f"Bit field '{self.name}' reset value {self.reset_value} out of range [0, {max_value}]")

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


class AbstractBusInterface(ABC):
    """
    Abstract base class for bus interfaces.

    This allows the Register class to work with any bus implementation
    without creating circular dependencies.
    """

    @abstractmethod
    def read_word(self, address: int) -> int:
        """Read a 32-bit word from the specified address."""
        pass

    @abstractmethod
    def write_word(self, address: int, data: int) -> None:
        """Write a 32-bit word to the specified address."""
        pass


class Register:
    """
    Generic hardware register abstraction with bit field support.

    This class provides a generic interface for accessing hardware registers
    with support for individual bit field operations, access control, and
    validation. It can be used by any IP core driver implementation.

    Features:
    - Individual bit field read/write operations
    - Access control enforcement (read-only, write-only fields)
    - Value validation for bit field widths
    - Read-modify-write operations for partial register updates
    - Register-level read/write operations
    - Field enumeration and introspection
    """

    def __init__(self, name: str, offset: int, bus: AbstractBusInterface,
                 fields: List[BitField], description: str = ''):
        """
        Initialize a register with bit field definitions.

        Args:
            name: Human-readable name of the register
            offset: Byte offset of the register from the base address
            bus: Bus interface for hardware communication
            fields: List of bit field definitions for this register
            description: Optional description of the register's purpose

        Raises:
            ValueError: If bit fields overlap or extend beyond register boundaries
        """
        self.name = name
        self.offset = offset
        self.description = description
        self._bus = bus
        self._fields: Dict[str, BitField] = {}

        # Validate and register bit fields
        self._validate_and_register_fields(fields)

    def _validate_and_register_fields(self, fields: List[BitField]) -> None:
        """Validate bit field definitions and check for overlaps."""
        # Check for field name uniqueness and overlaps
        used_bits = [False] * 32

        for field in fields:
            # Check for duplicate field names
            if field.name in self._fields:
                raise ValueError(f"Duplicate field name '{field.name}' in register '{self.name}'")

            # Check for bit overlap
            for bit_pos in range(field.offset, field.offset + field.width):
                if used_bits[bit_pos]:
                    raise ValueError(f"Bit overlap in register '{self.name}' at bit {bit_pos}")
                used_bits[bit_pos] = True

            self._fields[field.name] = field

    def read(self) -> int:
        """
        Read the entire register value.

        Returns:
            The 32-bit register value
        """
        return self._bus.read_word(self.offset)

    def write(self, value: int) -> None:
        """
        Write the entire register value.

        Args:
            value: 32-bit value to write to the register
        """
        # Ensure value fits in 32 bits
        value = value & 0xFFFFFFFF
        self._bus.write_word(self.offset, value)

    def read_field(self, field_name: str) -> int:
        """
        Read a specific bit field from the register.

        Args:
            field_name: Name of the bit field to read

        Returns:
            The value of the bit field

        Raises:
            ValueError: If field doesn't exist or is write-only
        """
        if field_name not in self._fields:
            raise ValueError(f"Register '{self.name}' has no field named '{field_name}'")

        field = self._fields[field_name]
        if field.access == 'w':
            raise ValueError(f"Field '{field_name}' in register '{self.name}' is write-only")

        reg_value = self.read()
        return field.extract_value(reg_value)

    def write_field(self, field_name: str, value: int) -> None:
        """
        Write a specific bit field in the register.

        This operation performs a read-modify-write sequence to update only
        the specified field while preserving other fields in the register.

        Args:
            field_name: Name of the bit field to write
            value: Value to write to the bit field

        Raises:
            ValueError: If field doesn't exist, is read-only, or value is out of range
        """
        if field_name not in self._fields:
            raise ValueError(f"Register '{self.name}' has no field named '{field_name}'")

        field = self._fields[field_name]
        if field.access == 'r':
            raise ValueError(f"Field '{field_name}' in register '{self.name}' is read-only")

        if value > field.max_value:
            raise ValueError(f"Value {value} exceeds field '{field_name}' maximum {field.max_value}")

        if field.access == 'rw':
            # Read-modify-write for read-write fields
            reg_value = self.read()
            new_reg_value = field.insert_value(reg_value, value)
        else:
            # Write-only field - don't read current value
            new_reg_value = field.insert_value(0, value)

        self.write(new_reg_value)

    def read_all_fields(self) -> Dict[str, int]:
        """
        Read all readable fields in the register.

        Returns:
            Dictionary mapping field names to their current values

        Note:
            Write-only fields are excluded from the result
        """
        reg_value = self.read()
        result = {}

        for field_name, field in self._fields.items():
            if field.access != 'w':  # Skip write-only fields
                result[field_name] = field.extract_value(reg_value)

        return result

    def write_multiple_fields(self, field_values: Dict[str, int]) -> None:
        """
        Write multiple fields in a single register operation.

        This is more efficient than multiple individual field writes as it
        performs only one read-modify-write cycle.

        Args:
            field_values: Dictionary mapping field names to values

        Raises:
            ValueError: If any field doesn't exist, is read-only, or value is out of range
        """
        # Validate all fields first
        for field_name, value in field_values.items():
            if field_name not in self._fields:
                raise ValueError(f"Register '{self.name}' has no field named '{field_name}'")

            field = self._fields[field_name]
            if field.access == 'r':
                raise ValueError(f"Field '{field_name}' in register '{self.name}' is read-only")

            if value > field.max_value:
                raise ValueError(f"Value {value} exceeds field '{field_name}' maximum {field.max_value}")

        # Check if we need to read current value (if any RW fields are being written)
        has_rw_fields = any(self._fields[name].access == 'rw' for name in field_values.keys())

        if has_rw_fields:
            reg_value = self.read()
        else:
            reg_value = 0

        # Apply all field updates
        for field_name, value in field_values.items():
            field = self._fields[field_name]
            reg_value = field.insert_value(reg_value, value)

        self.write(reg_value)

    def get_fields(self) -> List[str]:
        """
        Get list of available field names.

        Returns:
            List of field names in this register
        """
        return list(self._fields.keys())

    def get_field_info(self, field_name: str) -> BitField:
        """
        Get detailed information about a specific field.

        Args:
            field_name: Name of the field

        Returns:
            BitField object containing field metadata

        Raises:
            ValueError: If field doesn't exist
        """
        if field_name not in self._fields:
            raise ValueError(f"Register '{self.name}' has no field named '{field_name}'")

        return self._fields[field_name]

    def reset(self) -> None:
        """
        Reset the register to its default state.

        This writes the reset values of all fields to the register.
        Fields without defined reset values are set to 0.
        """
        reset_value = 0

        for field in self._fields.values():
            if field.reset_value is not None and field.access != 'r':
                reset_value = field.insert_value(reset_value, field.reset_value)

        self.write(reset_value)

    def __str__(self) -> str:
        """String representation of the register."""
        return f"Register('{self.name}', offset=0x{self.offset:04X}, fields={len(self._fields)})"

    def __repr__(self) -> str:
        """Detailed string representation of the register."""
        field_names = ', '.join(self._fields.keys())
        return f"Register(name='{self.name}', offset=0x{self.offset:04X}, fields=[{field_names}])"

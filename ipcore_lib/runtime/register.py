"""
Generic Register and BitField Classes

This module provides generic, reusable register abstraction classes that can be
used by any IP core driver implementation. These classes handle bit-wise
operations, field validation, and access control.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union


class AccessType(Enum):
    """
    Register field access types.

    This enum defines the valid access patterns for register bit fields:
    - RO: Read-only fields (e.g., status bits, hardware state)
    - WO: Write-only fields (e.g., command triggers, control pulses)
    - RW: Read-write fields (e.g., configuration settings)
    - RW1C: Read-write-1-to-clear fields (e.g., interrupt status flags)
    """

    RO = "ro"  # Read-only
    WO = "wo"  # Write-only
    RW = "rw"  # Read-write
    RW1C = "rw1c"  # Read-write-1-to-clear


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
    access: Access type - AccessType enum or string ('ro', 'wo', 'rw', 'rw1c')
        description: Optional human-readable description of the bit field
        reset_value: Default/reset value of the field (optional)
    """

    name: str
    offset: int
    width: int
    access: Union[AccessType, str] = AccessType.RW
    description: str = ""
    reset_value: Optional[int] = None

    def __post_init__(self):
        """Validate bit field parameters after initialization."""
        if self.width <= 0:
            raise ValueError(f"Bit field '{self.name}' width must be positive, got {self.width}")
        if self.width > 32:
            raise ValueError(
                f"Bit field '{self.name}' width cannot exceed 32 bits, got {self.width}"
            )
        if self.offset < 0:
            raise ValueError(
                f"Bit field '{self.name}' offset must be non-negative, got {self.offset}"
            )
        if self.offset + self.width > 32:
            raise ValueError(f"Bit field '{self.name}' extends beyond 32-bit register boundary")

        # Normalize access to string for internal consistency
        if isinstance(self.access, AccessType):
            self.access = self.access.value
        elif isinstance(self.access, str):
            # Validate string access types
            valid_access = {at.value for at in AccessType}
            if self.access not in valid_access:
                raise ValueError(
                    f"Bit field '{self.name}' access must be one of {valid_access}, got '{self.access}'"
                )
        else:
            raise ValueError(
                f"Bit field '{self.name}' access must be AccessType enum or string, got {type(self.access)}"
            )

        # Validate reset value if provided
        if self.reset_value is not None:
            max_value = (1 << self.width) - 1
            if self.reset_value < 0 or self.reset_value > max_value:
                raise ValueError(
                    f"Bit field '{self.name}' reset value {self.reset_value} out of range [0, {max_value}]"
                )

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
            raise ValueError(
                f"Value {field_value} exceeds field '{self.name}' maximum {self.max_value}"
            )

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

    def __init__(
        self,
        name: str,
        offset: int,
        bus: AbstractBusInterface,
        fields: List[BitField],
        description: str = "",
    ):
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

    @property
    def reset_value(self) -> int:
        """
        Calculate the full reset value of the register from its bit fields.

        Returns:
            The calculated 32-bit reset value based on field reset values
        """
        total_reset = 0
        for field in self._fields.values():
            if field.reset_value is not None:
                # Shift the field's reset value to its proper position and OR it
                total_reset |= field.reset_value << field.offset
        return total_reset

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
        if field.access == "wo":
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
        if field.access == "ro":
            raise ValueError(f"Field '{field_name}' in register '{self.name}' is read-only")

        if value > field.max_value:
            raise ValueError(
                f"Value {value} exceeds field '{field_name}' maximum {field.max_value}"
            )

        if field.access == "rw":
            # Read-modify-write for read-write fields
            reg_value = self.read()
            new_reg_value = field.insert_value(reg_value, value)
        elif field.access == "rw1c":
            # Read-write-1-to-clear: writing 1 clears the bit, writing 0 has no effect
            reg_value = self.read()
            # Only clear bits where value has 1s, preserve bits where value has 0s
            clear_mask = (value << field.offset) & field.mask
            new_reg_value = reg_value & ~clear_mask
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
            if field.access != "wo":  # Skip write-only fields
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
            if field.access == "ro":
                raise ValueError(f"Field '{field_name}' in register '{self.name}' is read-only")

            if value > field.max_value:
                raise ValueError(
                    f"Value {value} exceeds field '{field_name}' maximum {field.max_value}"
                )

        # Check if we need to read current value (if any RW or RW1C fields are being written)
        has_read_fields = any(
            self._fields[name].access in ["rw", "rw1c"] for name in field_values.keys()
        )

        if has_read_fields:
            reg_value = self.read()
        else:
            reg_value = 0

        # Apply all field updates
        for field_name, value in field_values.items():
            field = self._fields[field_name]
            if field.access == "rw1c":
                # Handle rw1c fields specially - clear bits where value has 1s
                clear_mask = (value << field.offset) & field.mask
                reg_value = reg_value & ~clear_mask
            else:
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
            if field.reset_value is not None and field.access != "ro":
                reset_value = field.insert_value(reset_value, field.reset_value)

        self.write(reset_value)

    # =========================================================================
    # Async Methods (for cocotb compatibility)
    # =========================================================================

    async def read_async(self) -> int:
        """
        Async read for cocotb compatibility.

        Handles both sync and async bus implementations.

        Returns:
            The 32-bit register value
        """
        result = self._bus.read_word(self.offset)
        if hasattr(result, "__await__"):
            return await result
        return result

    async def write_async(self, value: int) -> None:
        """
        Async write for cocotb compatibility.

        Handles both sync and async bus implementations.

        Args:
            value: 32-bit value to write to the register
        """
        value = value & 0xFFFFFFFF
        result = self._bus.write_word(self.offset, value)
        if hasattr(result, "__await__"):
            await result

    async def read_field_async(self, field_name: str) -> int:
        """
        Async read a specific bit field from the register.

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
        if field.access == "wo":
            raise ValueError(f"Field '{field_name}' in register '{self.name}' is write-only")

        reg_value = await self.read_async()
        return field.extract_value(reg_value)

    async def write_field_async(self, field_name: str, value: int) -> None:
        """
        Async write a specific bit field in the register.

        Performs a read-modify-write sequence for RW fields.

        Args:
            field_name: Name of the bit field to write
            value: Value to write to the bit field

        Raises:
            ValueError: If field doesn't exist, is read-only, or value is out of range
        """
        if field_name not in self._fields:
            raise ValueError(f"Register '{self.name}' has no field named '{field_name}'")

        field = self._fields[field_name]
        if field.access == "ro":
            raise ValueError(f"Field '{field_name}' in register '{self.name}' is read-only")

        if value > field.max_value:
            raise ValueError(
                f"Value {value} exceeds field '{field_name}' maximum {field.max_value}"
            )

        if field.access == "rw":
            # Read-modify-write for read-write fields
            reg_value = await self.read_async()
            new_reg_value = field.insert_value(reg_value, value)
        elif field.access == "rw1c":
            # Read-write-1-to-clear
            reg_value = await self.read_async()
            clear_mask = (value << field.offset) & field.mask
            new_reg_value = reg_value & ~clear_mask
        else:
            # Write-only field - don't read current value
            new_reg_value = field.insert_value(0, value)

        await self.write_async(new_reg_value)

    def __str__(self) -> str:
        """String representation of the register."""
        return f"Register('{self.name}', offset=0x{self.offset:04X}, fields={len(self._fields)})"

    def __repr__(self) -> str:
        """Detailed string representation of the register."""
        field_names = ", ".join(self._fields.keys())
        return f"Register(name='{self.name}', offset=0x{self.offset:04X}, fields=[{field_names}])"

    def __getattr__(self, name: str):
        """Dynamic field access for reading field values."""
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        if name not in self._fields:
            raise AttributeError(f"Register '{self.name}' has no field named '{name}'")

        field = self._fields[name]

        # Create a property-like object for this field
        class FieldProperty:
            def __init__(self, register, field):
                self._register = register
                self._field = field

            def read(self):
                if self._field.access == "wo":
                    raise ValueError(f"Field '{self._field.name}' is write-only")
                reg_value = self._register.read()
                mask = ((1 << self._field.width) - 1) << self._field.offset
                return (reg_value & mask) >> self._field.offset

            def write(self, value):
                if self._field.access == "ro":
                    raise ValueError(f"Field '{self._field.name}' is read-only")

                if value > ((1 << self._field.width) - 1):
                    raise ValueError(f"Value {value} exceeds field width {self._field.width}")

                if self._field.access == "rw":
                    reg_value = self._register.read()
                    mask = ((1 << self._field.width) - 1) << self._field.offset
                    cleared_val = reg_value & ~mask
                    new_reg_value = cleared_val | ((value << self._field.offset) & mask)
                elif self._field.access == "rw1c":
                    # Read-write-1-to-clear: writing 1 clears the bit, writing 0 has no effect
                    reg_value = self._register.read()
                    clear_mask = (value << self._field.offset) & (
                        (1 << self._field.width) - 1
                    ) << self._field.offset
                    new_reg_value = reg_value & ~clear_mask
                else:
                    # Write-only field
                    reg_value = 0
                    mask = ((1 << self._field.width) - 1) << self._field.offset
                    cleared_val = reg_value & ~mask
                    new_reg_value = cleared_val | ((value << self._field.offset) & mask)
                self._register.write(new_reg_value)

            def __int__(self):
                return self.read()

            def __index__(self):
                return self.read()

            def __format__(self, format_spec):
                return format(self.read(), format_spec)

            def __str__(self):
                return str(self.read())

            def __repr__(self):
                return repr(self.read())

        return FieldProperty(self, field)

    def __setattr__(self, name: str, value):
        """Dynamic field access for writing field values."""
        if name.startswith("_") or name in ["name", "offset", "description"]:
            super().__setattr__(name, value)
        elif hasattr(self, "_fields") and name in self._fields:
            field_prop = getattr(self, name)
            field_prop.write(value)
        else:
            super().__setattr__(name, value)


class RegisterArrayAccessor:
    """
    Provides indexed access to a block of registers (Block RAM regions).

    This class implements the register array functionality from the concept document,
    enabling memory-efficient access to Block RAM regions with structured register
    elements. Registers are created on-demand when accessed.

    Features:
    - On-demand register creation for memory efficiency
    - Pythonic array indexing syntax (accessor[index])
    - Bounds checking with meaningful error messages
    - Configurable stride for different element sizes
    - Compatible with any register field structure
    """

    def __init__(
        self,
        name: str,
        base_offset: int,
        count: int,
        stride: int,
        field_template: List[BitField],
        bus_interface: AbstractBusInterface,
    ):
        """
        Initialize a register array accessor.

        Args:
            name: Human-readable name of the register array
            base_offset: Base address of the first array element
            count: Number of elements in the array
            stride: Byte offset between consecutive elements
            field_template: List of BitField definitions used for each element
            bus_interface: Bus interface for hardware communication
        """
        self._name = name
        self._bus = bus_interface
        self._base_offset = base_offset
        self._count = count
        self._stride = stride
        self._field_template = field_template

    def __getitem__(self, index: int) -> Register:
        """
        Access a specific element in the register array.

        Args:
            index: Array index (0-based)

        Returns:
            Register object for the specified array element

        Raises:
            IndexError: If index is out of bounds
        """
        if not (0 <= index < self._count):
            raise IndexError(
                f"Index {index} out of bounds for array '{self._name}' of size {self._count}"
            )

        # Calculate the absolute address of the requested element
        item_offset = self._base_offset + (index * self._stride)

        # Create a Register object for this specific element on-the-fly
        return Register(
            name=f"{self._name}[{index}]",
            offset=item_offset,
            bus=self._bus,
            fields=self._field_template,
            description=f"Element {index} of {self._name} array",
        )

    def __len__(self) -> int:
        """Get the number of elements in the array."""
        return self._count

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this register array.

        Returns:
            Dictionary containing array metadata
        """
        return {
            "name": self._name,
            "base_address": f"0x{self._base_offset:04X}",
            "count": self._count,
            "stride": self._stride,
            "total_size": self._count * self._stride,
            "address_range": f"0x{self._base_offset:04X} - 0x{self._base_offset + (self._count * self._stride) - 1:04X}",
        }

    def __str__(self) -> str:
        """String representation of the register array."""
        return f"RegisterArray('{self._name}', count={self._count}, stride={self._stride})"

    def __repr__(self) -> str:
        """Detailed string representation of the register array."""
        return f"RegisterArrayAccessor(name='{self._name}', base=0x{self._base_offset:04X}, count={self._count}, stride={self._stride})"

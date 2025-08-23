"""
Generic Register and BitField Classes

This module provides generic, reusable register abstraction classes that can be
used by any IP core driver implementation. These classes handle bit-wise
operations, field validation, and access control with enhanced bitstring support.

Key Features:
- Enhanced bitstring library integration for powerful bit manipulation
- Support for W1SC (Write-1-Self-Clearing) access type
- Advanced debugging with bit-level visualization
- Comprehensive register layout validation
- Test pattern generation for verification
- Professional documentation generation with ASCII bit diagrams
- Backward compatibility when bitstring is not available
- Clean separation of concerns: Register as pure data, MemoryMap for access

Access Types Supported:
- RO: Read-only fields
- WO: Write-only fields
- RW: Read-write fields
- RW1C: Read-write-1-to-clear fields
- W1SC: Write-1-self-clearing fields (new)

Architecture:
- Register: Pure data structure defining register layout and fields
- MemoryMap: Manages bus interface and provides register access through proxies
- RegisterProxy: Provides actual register access operations through memory map
- Clean separation allows register definitions to be reused across different buses
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from abc import ABC, abstractmethod
from enum import Enum, auto

try:
    from bitstring import BitArray
    BITSTRING_AVAILABLE = True
except ImportError:
    BITSTRING_AVAILABLE = False
    BitArray = None


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
            valid_access = {at.value for at in AccessType}
            if self.access not in valid_access:
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


class AbstractBusInterface(ABC):
    """
    Abstract base class for bus interfaces.

    This allows the MemoryMap class to work with any bus implementation
    without creating circular dependencies.
    """

    @abstractmethod
    def read_word(self, address: int, width: int = 32) -> int:
        """Read a word from the specified address.

        Args:
            address: Address to read from
            width: Width of the data in bits (default: 32)

        Returns:
            The read value as an integer
        """
        pass

    @abstractmethod
    def write_word(self, address: int, data: int, width: int = 32) -> None:
        """Write a word to the specified address.

        Args:
            address: Address to write to
            data: Data value to write
            width: Width of the data in bits (default: 32)
        """
        pass


@dataclass
class Register:
    """
    Pure register definition without bus access logic.

    This class represents a register as a pure data structure, defining its
    layout, fields, and properties. It does not contain any bus access logic,
    making it reusable across different bus implementations.

    Features:
    - Pure data structure for register definition
    - Field validation and introspection
    - Bit manipulation utilities
    - Debug information generation
    - Documentation support
    """
    name: str
    offset: int
    width: int = 32
    fields: List[BitField] = field(default_factory=list)
    description: str = ''

    def __post_init__(self):
        """Validate register definition after initialization."""
        if self.width <= 0 or self.width > 32:
            raise ValueError(f"Register '{self.name}' width must be 1-32 bits, got {self.width}")

        if self.offset < 0:
            raise ValueError(f"Register '{self.name}' offset must be non-negative, got {self.offset}")

        # Validate and create field lookup
        self._fields_by_name: Dict[str, BitField] = {}
        self._validate_and_register_fields()

    def _validate_and_register_fields(self) -> None:
        """Validate bit field definitions and check for overlaps."""
        used_bits = [False] * self.width

        for field in self.fields:
            # Check for duplicate field names
            if field.name in self._fields_by_name:
                raise ValueError(f"Duplicate field name '{field.name}' in register '{self.name}'")

            # Check field bounds
            if field.offset + field.width > self.width:
                raise ValueError(f"Field '{field.name}' extends beyond register width {self.width}")

            # Check for bit overlap
            for bit_pos in range(field.offset, field.offset + field.width):
                if used_bits[bit_pos]:
                    raise ValueError(f"Bit overlap in register '{self.name}' at bit {bit_pos}")
                used_bits[bit_pos] = True

            self._fields_by_name[field.name] = field

    def read_field(self, field_name: str, register_value: Union[int, Any]) -> int:
        """
        Extract a field value from a register value.

        Args:
            field_name: Name of the bit field to extract
            register_value: Current register value (int or BitArray)

        Returns:
            The extracted field value

        Raises:
            ValueError: If field doesn't exist or is write-only
        """
        if field_name not in self._fields_by_name:
            raise ValueError(f"Register '{self.name}' has no field named '{field_name}'")

        field = self._fields_by_name[field_name]
        if field.access == 'wo':
            raise ValueError(f"Field '{field_name}' in register '{self.name}' is write-only")

        # Convert to int if needed
        if BITSTRING_AVAILABLE and hasattr(register_value, 'uint'):
            reg_int = register_value.uint
        else:
            reg_int = int(register_value)

        return field.extract_value(reg_int)

    def write_field(self, field_name: str, register_value: Union[int, Any], field_value: int) -> Union[int, Any]:
        """
        Insert a field value into a register value.

        Args:
            field_name: Name of the bit field to write
            register_value: Current register value (int or BitArray)
            field_value: Value to write to the field

        Returns:
            New register value with the field updated

        Raises:
            ValueError: If field doesn't exist, is read-only, or value is out of range
        """
        if field_name not in self._fields_by_name:
            raise ValueError(f"Register '{self.name}' has no field named '{field_name}'")

        field = self._fields_by_name[field_name]
        if field.access == 'ro':
            raise ValueError(f"Field '{field_name}' in register '{self.name}' is read-only")

        if field_value > field.max_value:
            raise ValueError(f"Value {field_value} exceeds field '{field_name}' maximum {field.max_value}")

        # Convert to int for manipulation
        if BITSTRING_AVAILABLE and hasattr(register_value, 'uint'):
            reg_int = register_value.uint
        else:
            reg_int = int(register_value)

        # Handle different access types
        if field.access == 'rw':
            new_value = field.insert_value(reg_int, field_value)
        elif field.access == 'rw1c':
            # Read-write-1-to-clear: writing 1 clears the bit, writing 0 has no effect
            clear_mask = (field_value << field.offset) & field.mask
            new_value = reg_int & ~clear_mask
        elif field.access == 'w1sc':
            # Write-1-self-clearing: write the field value, hardware will auto-clear
            new_value = field.insert_value(0, field_value)
        else:
            # Write-only field - don't use current value
            new_value = field.insert_value(0, field_value)

        # Return in same format as input
        if BITSTRING_AVAILABLE and hasattr(register_value, 'uint'):
            return BitArray(uint=new_value, length=self.width)
        return new_value

    @property
    def reset_value(self) -> int:
        """Calculate the full reset value of the register from its bit fields."""
        total_reset = 0
        for field in self.fields:
            if field.reset_value is not None:
                total_reset |= (field.reset_value << field.offset)
        return total_reset

    def debug_info(self, register_value: Union[int, Any]) -> str:
        """
        Return detailed bit-level information about the register.

        Args:
            register_value: Current register value to analyze

        Returns:
            Formatted string with register and field details
        """
        if BITSTRING_AVAILABLE and hasattr(register_value, 'uint'):
            raw_int = register_value.uint
            binary_str = register_value.bin
        else:
            raw_int = int(register_value)
            binary_str = f"{raw_int:0{self.width}b}"

        info = [f"Register '{self.name}' (0x{self.offset:04X}):"]
        info.append(f"  Raw value: 0x{raw_int:0{self.width//4}X}")
        info.append(f"  Binary:    {binary_str}")

        for field in self.fields:
            try:
                field_value = self.read_field(field.name, register_value)
                field_width_str = f"{field.offset + field.width - 1:2d}:{field.offset:2d}" if field.width > 1 else f"{field.offset:2d}"
                if BITSTRING_AVAILABLE:
                    field_bits = BitArray(uint=field_value, length=field.width).bin
                else:
                    field_bits = f"{field_value:0{field.width}b}"
                info.append(f"  {field.name:15s} [{field_width_str}] = {field_bits} (0x{field_value:X}) {field.access.upper()}")
            except ValueError:
                # Handle write-only fields
                info.append(f"  {field.name:15s} [write-only] {field.access.upper()}")

        return '\n'.join(info)

    def get_field_names(self) -> List[str]:
        """Get list of available field names."""
        return list(self._fields_by_name.keys())

    def get_field_info(self, field_name: str) -> BitField:
        """Get detailed information about a specific field."""
        if field_name not in self._fields_by_name:
            raise ValueError(f"Register '{self.name}' has no field named '{field_name}'")
        return self._fields_by_name[field_name]

    def __str__(self) -> str:
        """String representation of the register."""
        return f"Register('{self.name}', offset=0x{self.offset:04X}, fields={len(self.fields)})"


@dataclass
class MemoryMap:
    """
    Memory map that manages register access through a bus interface.

    This class provides the actual hardware access layer for registers,
    maintaining a clean separation between register definitions (pure data)
    and register access (through the memory map).
    """
    base_address: int
    bus_interface: AbstractBusInterface
    registers: List[Register] = field(default_factory=list)

    def __post_init__(self):
        """Create register lookup and dynamic attributes."""
        self._registers_by_name: Dict[str, Register] = {}

        for register in self.registers:
            if register.name in self._registers_by_name:
                raise ValueError(f"Duplicate register name '{register.name}' in memory map")

            self._registers_by_name[register.name] = register

            # Create dynamic attribute for each register
            setattr(self, register.name, RegisterProxy(self, register))

    def add_register(self, register: Register) -> None:
        """Add a register to the memory map."""
        if register.name in self._registers_by_name:
            raise ValueError(f"Register '{register.name}' already exists in memory map")

        self.registers.append(register)
        self._registers_by_name[register.name] = register
        setattr(self, register.name, RegisterProxy(self, register))

    def get_register_names(self) -> List[str]:
        """Get list of all register names in the memory map."""
        return list(self._registers_by_name.keys())

    def get_register(self, name: str) -> Register:
        """Get register definition by name."""
        if name not in self._registers_by_name:
            raise ValueError(f"No register named '{name}' in memory map")
        return self._registers_by_name[name]


class RegisterProxy:
    """
    Proxy that provides register access through the memory map.

    This class handles the actual hardware communication while keeping
    the register definition as pure data. It provides the same interface
    as the old Register class but delegates to the memory map for access.
    """

    def __init__(self, memory_map: MemoryMap, register: Register):
        self.memory_map = memory_map
        self.register = register

    def read(self) -> Union[int, Any]:
        """Read the entire register."""
        raw_value = self.memory_map.bus_interface.read_word(
            self.memory_map.base_address + self.register.offset,
            self.register.width
        )
        if BITSTRING_AVAILABLE:
            return BitArray(uint=raw_value, length=self.register.width)
        return raw_value

    def write(self, value: Union[int, Any]) -> None:
        """Write the entire register."""
        if BITSTRING_AVAILABLE and hasattr(value, 'uint'):
            int_value = value.uint
        else:
            int_value = int(value)

        # Ensure value fits in register width
        mask = (1 << self.register.width) - 1
        int_value = int_value & mask

        self.memory_map.bus_interface.write_word(
            self.memory_map.base_address + self.register.offset,
            int_value,
            self.register.width
        )

    def debug_info(self) -> str:
        """Get debug information for this register."""
        register_value = self.read()
        return self.register.debug_info(register_value)

    def compare_with(self, other_value: Union[int, Any]) -> str:
        """Compare current register value with another value."""
        current = self.read()

        if BITSTRING_AVAILABLE:
            if hasattr(current, 'uint'):
                current_int = current.uint
            else:
                current_int = int(current)

            if hasattr(other_value, 'uint'):
                other_int = other_value.uint
            else:
                other_int = int(other_value)

            current_bits = BitArray(uint=current_int, length=self.register.width)
            other_bits = BitArray(uint=other_int, length=self.register.width)
            diff = current_bits ^ other_bits
            return f"Differences: {diff.bin} (changed bits marked as 1)"
        else:
            current_int = int(current)
            other_int = int(other_value)
            diff = current_int ^ other_int
            hex_width = self.register.width // 4
            return f"Differences: 0x{diff:0{hex_width}X} (XOR result)"

    def read_field(self, field_name: str) -> int:
        """Read a specific bit field from the register."""
        register_value = self.read()
        return self.register.read_field(field_name, register_value)

    def write_field(self, field_name: str, value: int) -> None:
        """Write a specific bit field in the register."""
        # Handle different access types appropriately
        field = self.register.get_field_info(field_name)

        if field.access in ['rw', 'rw1c']:
            # Need current register value for read-modify-write
            current_value = self.read()
        else:
            # Write-only or self-clearing fields don't need current value
            current_value = 0

        new_value = self.register.write_field(field_name, current_value, value)
        self.write(new_value)

    def read_all_fields(self) -> Dict[str, int]:
        """Read all readable fields in the register."""
        register_value = self.read()
        result = {}

        for field_name in self.register.get_field_names():
            field = self.register.get_field_info(field_name)
            if field.access != 'wo':  # Skip write-only fields
                try:
                    result[field_name] = self.register.read_field(field_name, register_value)
                except ValueError:
                    # Skip if field is write-only
                    pass

        return result

    def write_multiple_fields(self, field_values: Dict[str, int]) -> None:
        """Write multiple fields in a single register operation."""
        # Check if we need to read current value
        needs_current = any(
            self.register.get_field_info(name).access in ['rw', 'rw1c']
            for name in field_values.keys()
        )

        if needs_current:
            current_value = self.read()
        else:
            current_value = 0

        # Apply all field updates
        new_value = current_value
        for field_name, field_value in field_values.items():
            new_value = self.register.write_field(field_name, new_value, field_value)

        self.write(new_value)

    def reset(self) -> None:
        """Reset the register to its default state."""
        self.write(self.register.reset_value)

    def __getattr__(self, name: str):
        """Dynamic field access."""
        if name.startswith('_') or name in ['memory_map', 'register']:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        if name not in self.register._fields_by_name:
            raise AttributeError(f"Register '{self.register.name}' has no field named '{name}'")

        field = self.register._fields_by_name[name]

        class FieldProperty:
            def __init__(self, proxy, field):
                self._proxy = proxy
                self._field = field

            def read(self):
                register_value = self._proxy.read()
                return self._proxy.register.read_field(self._field.name, register_value)

            def write(self, value: int):
                self._proxy.write_field(self._field.name, value)

            def __int__(self):
                return self.read()

            def __str__(self):
                try:
                    return str(self.read())
                except ValueError:
                    return f"<write-only field '{self._field.name}'>"

        return FieldProperty(self, field)

    def __setattr__(self, name: str, value):
        """Dynamic field writing."""
        if name in ['memory_map', 'register']:
            super().__setattr__(name, value)
        elif hasattr(self, 'register') and name in self.register._fields_by_name:
            field_prop = getattr(self, name)
            field_prop.write(value)
        else:
            super().__setattr__(name, value)

    def __str__(self) -> str:
        """String representation of the register proxy."""
        return f"RegisterProxy('{self.register.name}', offset=0x{self.register.offset:04X})"


@dataclass
class RegisterArrayAccessor:
    """
    Provides indexed access to a block of registers.

    This class implements the register array functionality with the new
    MemoryMap-centric architecture, providing memory-efficient access
    to Block RAM regions with structured register elements.
    """
    memory_map: MemoryMap
    name: str
    base_offset: int
    count: int
    stride: int
    width: int
    field_template: List[BitField]

    def __getitem__(self, index: int) -> RegisterProxy:
        """Access a specific element in the register array."""
        if not (0 <= index < self.count):
            raise IndexError(f"Index {index} out of bounds for array of size {self.count}")

        # Calculate the absolute address of the requested element
        item_offset = self.base_offset + (index * self.stride)

        # Create a register definition for this array element
        element_register = Register(
            name=f"{self.name}[{index}]",
            offset=item_offset,
            width=self.width,
            fields=self.field_template
        )

        # Return a proxy that uses the memory map for access
        return RegisterProxy(self.memory_map, element_register)

    def __len__(self):
        return self.count

    def get_info(self) -> Dict[str, Any]:
        """Get information about this register array."""
        return {
            'name': self.name,
            'base_address': f"0x{self.base_offset:04X}",
            'count': self.count,
            'stride': self.stride,
            'total_size': self.count * self.stride,
            'address_range': f"0x{self.base_offset:04X} - 0x{self.base_offset + (self.count * self.stride) - 1:04X}"
        }

    def __str__(self) -> str:
        """String representation of the register array."""
        return f"RegisterArray('{self.name}', count={self.count}, stride={self.stride})"


def validate_register_layout(fields: List[BitField]) -> bool:
    """
    Validate that bit fields don't overlap in a register layout.

    Args:
        fields: List of BitField objects to validate

    Returns:
        True if layout is valid, False if fields overlap
    """
    if BITSTRING_AVAILABLE:
        used_bits = BitArray(length=32)

        for field in fields:
            field_mask = BitArray(length=32)
            field_mask[field.offset:field.offset + field.width] = '1' * field.width

            # Check for overlaps using bitstring operations
            if (used_bits & field_mask).any():
                return False

            used_bits |= field_mask
    else:
        # Fallback validation without bitstring
        used_bits = [False] * 32

        for field in fields:
            for bit_pos in range(field.offset, field.offset + field.width):
                if used_bits[bit_pos]:
                    return False
                used_bits[bit_pos] = True

    return True


def generate_test_patterns(fields: List[BitField], reg_width: int = 32) -> List[Union[int, Any]]:
    """
    Generate comprehensive test patterns for a register using bitstring if available.

    Args:
        fields: List of BitField objects
        reg_width: Width of the register in bits

    Returns:
        List of test patterns (BitArray if available, otherwise int)
    """
    patterns = []

    if BITSTRING_AVAILABLE:
        # Walking ones pattern
        for i in range(reg_width):
            walking_one = BitArray(length=reg_width)
            walking_one[i] = 1
            patterns.append(walking_one)

        # Walking zeros pattern
        for i in range(reg_width):
            walking_zero = BitArray('1' * reg_width)
            walking_zero[i] = 0
            patterns.append(walking_zero)

        # Field-specific patterns
        for field in fields:
            if field.access in ['rw', 'wo', 'w1sc']:
                # All ones in this field
                pattern = BitArray(length=reg_width)
                pattern[field.offset:field.offset + field.width] = '1' * field.width
                patterns.append(pattern)

                # Alternating pattern in this field
                if field.width > 1:
                    alt_pattern = BitArray(length=reg_width)
                    field_alt = BitArray('01' * (field.width // 2) + '0' * (field.width % 2))
                    alt_pattern[field.offset:field.offset + field.width] = field_alt
                    patterns.append(alt_pattern)
    else:
        # Fallback patterns without bitstring
        for i in range(min(reg_width, 8)):  # Limit for performance
            patterns.append(1 << i)
            patterns.append(~(1 << i) & ((1 << reg_width) - 1))

        for field in fields:
            if field.access in ['rw', 'wo', 'w1sc']:
                field_mask = ((1 << field.width) - 1) << field.offset
                patterns.append(field_mask)

    return patterns


def generate_register_documentation(register: Register) -> str:
    """
    Generate human-readable documentation for a register with bit diagrams.

    Args:
        register: Register object to document

    Returns:
        Formatted documentation string with ASCII bit diagrams
    """
    doc = []

    doc.append(f"\n## {register.name.upper()} (Offset: 0x{register.offset:04X})")
    doc.append(f"Width: {register.width} bits")

    if register.description:
        doc.append(f"Description: {register.description}")

    if register.fields:
        doc.append("\n### Bit Layout:")
        doc.append("```")

        # Create bit position header (adjust for register width)
        bit_header = "Bit: " + "".join(f"{i%10:1d}" for i in range(register.width-1, -1, -1))
        doc.append(bit_header)

        # Create field visualization
        field_line = "     " + "".join("." for _ in range(register.width))
        field_chars = list(field_line)

        for field in register.fields:
            # Mark field boundaries
            for i in range(field.offset, field.offset + field.width):
                pos = 5 + (register.width - 1 - i)  # Account for "Bit: " prefix
                if i == field.offset:
                    field_chars[pos] = '['
                elif i == field.offset + field.width - 1:
                    field_chars[pos] = ']'
                else:
                    field_chars[pos] = '-'

        doc.append("".join(field_chars))
        doc.append("```")

        # Field details table
        doc.append("\n### Fields:")
        doc.append("| Field | Bits | Access | Reset | Description |")
        doc.append("|-------|------|--------|-------|-------------|")

        for field in register.fields:
            if field.width == 1:
                bits_str = str(field.offset)
            else:
                bits_str = f"{field.offset + field.width - 1}:{field.offset}"

            reset_val = field.reset_value if field.reset_value is not None else 'N/A'
            access_str = field.access.upper()
            desc = field.description or ''

            doc.append(f"| {field.name} | {bits_str} | {access_str} | {reset_val} | {desc} |")

    return '\n'.join(doc)

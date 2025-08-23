"""
Pure register definition without access logic.

This module provides the Register class as a pure data structure for
defining register layouts, fields, and properties without any bus access logic.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Union, Any, Optional
from .bit_field import BitField

try:
    from bitstring import BitArray
    BITSTRING_AVAILABLE = True
except ImportError:
    BITSTRING_AVAILABLE = False
    BitArray = None


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

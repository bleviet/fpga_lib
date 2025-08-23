"""
Memory map management and register access proxy.

This module provides the MemoryMap class for managing register access
through bus interfaces and the RegisterProxy class for actual hardware
communication while keeping register definitions as pure data.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Union, Any
from .bus_interface import AbstractBusInterface
from .register_def import Register

try:
    from bitstring import BitArray
    BITSTRING_AVAILABLE = True
except ImportError:
    BITSTRING_AVAILABLE = False
    BitArray = None


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

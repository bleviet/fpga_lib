"""
Debug Mode Infrastructure

Provides debug sets, live values, and comparison functionality for hardware debugging.
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class ValueFormat(Enum):
    """Supported value formats for debug input."""
    HEX = "HEX"
    BIN = "BIN"
    DEC = "DEC"


@dataclass
class DebugValue:
    """Represents a live debug value for a register or bit field."""
    value: Optional[int] = None
    format: ValueFormat = ValueFormat.HEX

    def to_string(self) -> str:
        """Convert value to string in the specified format."""
        if self.value is None:
            return ""

        if self.format == ValueFormat.HEX:
            return f"0x{self.value:X}"
        elif self.format == ValueFormat.BIN:
            return f"0b{self.value:b}"
        else:  # DEC
            return str(self.value)

    @classmethod
    def from_string(cls, value_str: str, format_hint: ValueFormat = ValueFormat.HEX) -> 'DebugValue':
        """Parse a value string and create a DebugValue."""
        if not value_str.strip():
            return cls(None, format_hint)

        try:
            # Auto-detect format based on prefix
            if value_str.startswith('0x') or value_str.startswith('0X'):
                value = int(value_str, 16)
                format_used = ValueFormat.HEX
            elif value_str.startswith('0b') or value_str.startswith('0B'):
                value = int(value_str, 2)
                format_used = ValueFormat.BIN
            else:
                # Try decimal first, then hex
                try:
                    value = int(value_str, 10)
                    format_used = ValueFormat.DEC
                except ValueError:
                    value = int(value_str, 16)
                    format_used = ValueFormat.HEX

            return cls(value, format_used)
        except ValueError:
            raise ValueError(f"Invalid value format: {value_str}")


@dataclass
class DebugSet:
    """A named collection of debug values for registers and bit fields."""
    name: str
    register_values: Dict[str, DebugValue] = field(default_factory=dict)
    field_values: Dict[str, Dict[str, DebugValue]] = field(default_factory=dict)  # register_name -> field_name -> value

    def set_register_value(self, register_name: str, value: DebugValue):
        """Set the debug value for a register."""
        self.register_values[register_name] = value

    def get_register_value(self, register_name: str) -> Optional[DebugValue]:
        """Get the debug value for a register."""
        return self.register_values.get(register_name)

    def set_field_value(self, register_name: str, field_name: str, value: DebugValue):
        """Set the debug value for a specific bit field."""
        if register_name not in self.field_values:
            self.field_values[register_name] = {}
        self.field_values[register_name][field_name] = value

    def get_field_value(self, register_name: str, field_name: str) -> Optional[DebugValue]:
        """Get the debug value for a specific bit field."""
        return self.field_values.get(register_name, {}).get(field_name)


class DebugManager:
    """Manages debug sets and provides comparison functionality."""

    def __init__(self):
        self.debug_sets: Dict[str, DebugSet] = {}
        self.current_set_name: Optional[str] = None
        self.debug_mode_enabled: bool = True

    def create_debug_set(self, name: str) -> DebugSet:
        """Create a new debug set."""
        debug_set = DebugSet(name)
        self.debug_sets[name] = debug_set
        if self.current_set_name is None:
            self.current_set_name = name
        return debug_set

    def get_debug_set(self, name: str) -> Optional[DebugSet]:
        """Get a debug set by name."""
        return self.debug_sets.get(name)

    def get_current_debug_set(self) -> Optional[DebugSet]:
        """Get the currently active debug set."""
        if self.current_set_name:
            return self.debug_sets.get(self.current_set_name)
        return None

    def set_current_debug_set(self, name: str):
        """Set the currently active debug set."""
        if name in self.debug_sets:
            self.current_set_name = name

    def delete_debug_set(self, name: str):
        """Delete a debug set."""
        if name in self.debug_sets:
            del self.debug_sets[name]
            if self.current_set_name == name:
                # Switch to another set or None
                if self.debug_sets:
                    self.current_set_name = next(iter(self.debug_sets.keys()))
                else:
                    self.current_set_name = None

    def rename_debug_set(self, old_name: str, new_name: str):
        """Rename a debug set."""
        if old_name in self.debug_sets and new_name not in self.debug_sets:
            debug_set = self.debug_sets[old_name]
            debug_set.name = new_name
            self.debug_sets[new_name] = debug_set
            del self.debug_sets[old_name]
            if self.current_set_name == old_name:
                self.current_set_name = new_name

    def get_debug_set_names(self) -> List[str]:
        """Get list of all debug set names."""
        return list(self.debug_sets.keys())

    def enable_debug_mode(self):
        """Enable debug mode."""
        self.debug_mode_enabled = True

    def disable_debug_mode(self):
        """Disable debug mode."""
        self.debug_mode_enabled = False

    def compare_register_bits(self, register_name: str, register_obj, reset_value: int) -> List[bool]:
        """
        Compare live register value against reset value.
        Returns a list of 32 booleans indicating which bits differ.
        """
        current_set = self.get_current_debug_set()
        if not current_set:
            return [False] * 32  # No differences if no debug set

        live_value_obj = current_set.get_register_value(register_name)
        if not live_value_obj or live_value_obj.value is None:
            return [False] * 32  # No differences if no live value

        live_value = live_value_obj.value
        differences = []

        for bit in range(32):
            reset_bit = (reset_value >> bit) & 1
            live_bit = (live_value >> bit) & 1
            differences.append(reset_bit != live_bit)

        return differences

    def calculate_register_value_from_fields(self, register_name: str, register_obj) -> Optional[int]:
        """
        Calculate the complete register value from individual field debug values.
        """
        current_set = self.get_current_debug_set()
        if not current_set or not hasattr(register_obj, '_fields'):
            return None

        total_value = 0
        has_any_value = False

        for field_name, field in register_obj._fields.items():
            field_debug = current_set.get_field_value(register_name, field_name)
            if field_debug and field_debug.value is not None:
                total_value |= (field_debug.value << field.offset)
                has_any_value = True
            elif field.reset_value is not None:
                # Use reset value if no debug value is set
                total_value |= (field.reset_value << field.offset)

        return total_value if has_any_value else None

    def update_field_values_from_register(self, register_name: str, register_obj, register_value: int):
        """
        Update individual field debug values based on a complete register value.
        """
        current_set = self.get_current_debug_set()
        if not current_set or not hasattr(register_obj, '_fields'):
            return

        for field_name, field in register_obj._fields.items():
            # Extract field value from register value
            field_mask = (1 << field.width) - 1
            field_value = (register_value >> field.offset) & field_mask

            # Create debug value for this field
            debug_value = DebugValue(field_value, ValueFormat.HEX)
            current_set.set_field_value(register_name, field_name, debug_value)


# Global debug manager instance
debug_manager = DebugManager()

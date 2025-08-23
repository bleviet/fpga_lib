"""
Register array accessor for Block RAM and array-like register structures.

This module provides the RegisterArrayAccessor class for efficient access
to arrays of registers with consistent structure, supporting memory-efficient
on-demand register creation.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from .memory_map import MemoryMap, RegisterProxy
from .register_def import Register
from .bit_field import BitField


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

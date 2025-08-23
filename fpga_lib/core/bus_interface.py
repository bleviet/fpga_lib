"""
Abstract bus interface for register access.

This module defines the bus interface abstraction that allows register
access implementations to work with any bus protocol (AXI, Avalon, etc.)
without tight coupling.
"""

from abc import ABC, abstractmethod


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

"""
Abstract Bus Interface - Layer 2

This module defines the abstract bus interface that separates the high-level
IP core logic from the low-level bus implementation details.
"""

from abc import ABC, abstractmethod
from typing import Any


class AbstractBusInterface(ABC):
    """
    Abstract base class for all bus interfaces.

    This interface defines the contract that all concrete bus implementations
    must follow. It provides basic word-level read and write operations.
    """

    @abstractmethod
    def read_word(self, address: int) -> int:
        """
        Read a 32-bit word from the specified address.

        Args:
            address: The byte address to read from

        Returns:
            The 32-bit value read from the address
        """
        pass

    @abstractmethod
    def write_word(self, address: int, data: int) -> None:
        """
        Write a 32-bit word to the specified address.

        Args:
            address: The byte address to write to
            data: The 32-bit value to write
        """
        pass


class MockBusInterface(AbstractBusInterface):
    """
    Mock bus interface for testing and demonstration purposes.

    This implementation uses a simple dictionary to simulate memory,
    allowing for testing without real hardware or simulation.
    """

    def __init__(self):
        self._memory = {}

    def read_word(self, address: int) -> int:
        """Read from mock memory."""
        return self._memory.get(address, 0)

    def write_word(self, address: int, data: int) -> None:
        """Write to mock memory."""
        self._memory[address] = data & 0xFFFFFFFF

    def dump_memory(self) -> dict:
        """Return the current state of mock memory for debugging."""
        return self._memory.copy()

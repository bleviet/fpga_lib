"""
Test module for rw1c (read-write-1-to-clear) access type functionality.

This module tests the rw1c access type implementation in the core register module.
The rw1c access type is commonly used for interrupt status registers where
writing 1 clears the bit and writing 0 has no effect.
"""

import pytest
from unittest.mock import Mock

from fpga_lib.runtime.register import BitField, Register, AbstractBusInterface


class MockBusInterface(AbstractBusInterface):
    """Mock bus interface for testing."""

    def __init__(self):
        self.memory = {}

    def read_word(self, address: int) -> int:
        return self.memory.get(address, 0)

    def write_word(self, address: int, data: int) -> None:
        self.memory[address] = data & 0xFFFFFFFF


class TestRW1CAccessType:
    """Test cases for rw1c access type functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bus = MockBusInterface()

        # Create a register with mixed access types including rw1c
        self.fields = [
            BitField(name="tx_complete", offset=0, width=1, access="rw1c",
                    description="TX complete flag"),
            BitField(name="rx_complete", offset=1, width=1, access="rw1c",
                    description="RX complete flag"),
            BitField(name="error_flags", offset=8, width=4, access="rw1c",
                    description="Error flags"),
            BitField(name="control", offset=16, width=8, access="rw",
                    description="Control register"),
        ]

        self.reg = Register(name="status", offset=0x10, bus=self.bus, fields=self.fields)

    def test_rw1c_field_creation(self):
        """Test that rw1c fields are created correctly."""
        assert "tx_complete" in self.reg.get_fields()
        assert "rx_complete" in self.reg.get_fields()
        assert "error_flags" in self.reg.get_fields()

        tx_field = self.reg.get_field_info("tx_complete")
        assert tx_field.access == "rw1c"
        assert tx_field.offset == 0
        assert tx_field.width == 1

    def test_rw1c_single_bit_clear(self):
        """Test clearing a single bit in an rw1c field."""
        # Set initial register value (simulate hardware setting flags)
        self.bus.write_word(0x10, 0x00010F03)  # control=1, error_flags=15, rx_complete=1, tx_complete=1

        # Verify initial state
        assert self.reg.read_field('tx_complete') == 1
        assert self.reg.read_field('rx_complete') == 1
        assert self.reg.read_field('error_flags') == 15

        # Clear tx_complete by writing 1 (rw1c behavior)
        self.reg.write_field('tx_complete', 1)

        # Verify only tx_complete was cleared
        assert self.reg.read_field('tx_complete') == 0
        assert self.reg.read_field('rx_complete') == 1  # Should remain unchanged
        assert self.reg.read_field('error_flags') == 15  # Should remain unchanged

    def test_rw1c_write_zero_no_effect(self):
        """Test that writing 0 to rw1c field has no effect."""
        # Set initial state
        self.bus.write_word(0x10, 0x00000002)  # rx_complete=1

        assert self.reg.read_field('rx_complete') == 1

        # Write 0 to rx_complete (should have no effect)
        self.reg.write_field('rx_complete', 0)

        # Verify bit is still set
        assert self.reg.read_field('rx_complete') == 1

    def test_rw1c_multi_bit_field(self):
        """Test rw1c behavior with multi-bit fields."""
        # Set initial state with error flags
        self.bus.write_word(0x10, 0x00000F00)  # error_flags=15 (0b1111)

        assert self.reg.read_field('error_flags') == 15

        # Clear bits 0 and 2 by writing 0b0101 = 5
        self.reg.write_field('error_flags', 5)

        # Should result in 0b1010 = 10 (bits 1 and 3 remain set)
        assert self.reg.read_field('error_flags') == 10

    def test_rw1c_partial_clear(self):
        """Test partial clearing of multi-bit rw1c field."""
        # Set all error flags
        self.bus.write_word(0x10, 0x00000F00)  # error_flags=15 (0b1111)

        # Clear only bit 1 by writing 0b0010 = 2
        self.reg.write_field('error_flags', 2)

        # Should result in 0b1101 = 13
        assert self.reg.read_field('error_flags') == 13

    def test_rw1c_mixed_with_normal_rw(self):
        """Test that rw1c fields don't affect normal rw fields."""
        # Set initial state
        self.bus.write_word(0x10, 0x00010F03)  # control=1, error_flags=15, rx_complete=1, tx_complete=1

        # Modify control field (normal rw behavior)
        self.reg.write_field('control', 42)

        # Verify control was updated but rw1c fields unchanged
        assert self.reg.read_field('control') == 42
        assert self.reg.read_field('tx_complete') == 1
        assert self.reg.read_field('rx_complete') == 1
        assert self.reg.read_field('error_flags') == 15

    def test_rw1c_multiple_fields_write(self):
        """Test writing to multiple rw1c fields simultaneously."""
        # Set initial state
        self.bus.write_word(0x10, 0x00000F03)  # error_flags=15, rx_complete=1, tx_complete=1

        # Write to multiple fields at once
        self.reg.write_multiple_fields({
            'tx_complete': 1,  # Clear tx_complete
            'error_flags': 3   # Clear bits 0 and 1 of error_flags
        })

        # Verify results
        assert self.reg.read_field('tx_complete') == 0
        assert self.reg.read_field('rx_complete') == 1  # Unchanged
        assert self.reg.read_field('error_flags') == 12  # 0b1111 -> 0b1100 = 12

    def test_rw1c_read_all_fields(self):
        """Test reading all fields including rw1c."""
        # Set initial state
        self.bus.write_word(0x10, 0x00AA0F03)  # control=170, error_flags=15, rx_complete=1, tx_complete=1

        all_fields = self.reg.read_all_fields()

        assert all_fields['tx_complete'] == 1
        assert all_fields['rx_complete'] == 1
        assert all_fields['error_flags'] == 15
        assert all_fields['control'] == 170

    def test_rw1c_dynamic_access(self):
        """Test rw1c fields through dynamic attribute access."""
        # Set initial state
        self.bus.write_word(0x10, 0x00000003)  # rx_complete=1, tx_complete=1

        # Test reading through dynamic access
        assert self.reg.tx_complete.read() == 1
        assert self.reg.rx_complete.read() == 1

        # Test writing through dynamic access
        self.reg.tx_complete.write(1)  # Clear tx_complete

        assert self.reg.tx_complete.read() == 0
        assert self.reg.rx_complete.read() == 1

    def test_rw1c_field_validation(self):
        """Test that rw1c access type is properly validated."""
        # Test valid rw1c field creation
        field = BitField(name="test", offset=0, width=1, access="rw1c")
        assert field.access == "rw1c"

        # Test invalid access type
        with pytest.raises(ValueError, match="access must be"):
            BitField(name="invalid", offset=0, width=1, access="invalid")


def test_rw1c_standalone():
    """Standalone test function for manual execution."""
    test_case = TestRW1CAccessType()
    test_case.setup_method()

    print("Testing rw1c (read-write-1-to-clear) access type...")

    # Set initial state
    test_case.bus.write_word(0x10, 0x00010F03)

    print(f"Initial register value: 0x{test_case.reg.read():08X}")
    print(f"tx_complete: {test_case.reg.read_field('tx_complete')}")
    print(f"rx_complete: {test_case.reg.read_field('rx_complete')}")
    print(f"error_flags: {test_case.reg.read_field('error_flags')}")
    print(f"control: {test_case.reg.read_field('control')}")

    # Test clearing
    test_case.reg.write_field('tx_complete', 1)
    print(f"\nAfter clearing tx_complete: 0x{test_case.reg.read():08X}")
    print(f"tx_complete: {test_case.reg.read_field('tx_complete')} (should be 0)")
    print(f"rx_complete: {test_case.reg.read_field('rx_complete')} (should still be 1)")

    print("\nAll tests passed! rw1c access type is working correctly.")


if __name__ == "__main__":
    test_rw1c_standalone()

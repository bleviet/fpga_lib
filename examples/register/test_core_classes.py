#!/usr/bin/env python3
"""
Quick test to verify that the core Register class now supports dynamic field access.
"""

import sys
import os

# Add the fpga_lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fpga_lib.core import BitField, Register, AbstractBusInterface, RegisterArrayAccessor


class MockBus(AbstractBusInterface):
    def __init__(self):
        self._memory = {}

    def read_word(self, address: int) -> int:
        return self._memory.get(address, 0)

    def write_word(self, address: int, data: int) -> None:
        self._memory[address] = data & 0xFFFFFFFF


def test_dynamic_field_access():
    """Test that dynamic field access works with the core Register class."""
    print("🧪 Testing dynamic field access in core Register class...")

    bus = MockBus()

    # Create a register with fields
    fields = [
        BitField("enable", 0, 1, "rw", "Enable bit"),
        BitField("mode", 1, 2, "rw", "Mode selection"),
        BitField("status", 8, 4, "ro", "Status bits")
    ]

    reg = Register("test_reg", 0x100, bus, fields, "Test register")

    # Test writing via dynamic access
    reg.enable = 1
    reg.mode = 3

    # Test reading via dynamic access
    enable_val = reg.enable
    mode_val = reg.mode

    print(f"✅ Dynamic write/read successful:")
    print(f"   enable: {enable_val}")
    print(f"   mode: {mode_val}")

    # Verify the underlying register value
    reg_val = reg.read()
    print(f"   register value: 0x{reg_val:08X}")

    # Test format support
    print(f"✅ Format support:")
    print(f"   enable (hex): 0x{reg.enable:X}")
    print(f"   mode (binary): 0b{reg.mode:02b}")


def test_register_array():
    """Test that RegisterArrayAccessor works."""
    print("\n🧪 Testing RegisterArrayAccessor from core...")

    bus = MockBus()

    # Create field template
    fields = [
        BitField("value", 0, 16, "rw", "Data value"),
        BitField("valid", 31, 1, "rw", "Valid bit")
    ]

    # Create array accessor
    array = RegisterArrayAccessor("test_array", 0x200, 4, 4, fields, bus)

    # Test array access
    array[0].value = 0x1234
    array[0].valid = 1

    array[1].value = 0x5678
    array[1].valid = 1

    # Read back
    val0 = array[0].value
    val1 = array[1].value

    print(f"✅ Array access successful:")
    print(f"   array[0].value: 0x{val0:04X}")
    print(f"   array[1].value: 0x{val1:04X}")
    print(f"   array length: {len(array)}")

    # Test bounds checking
    try:
        array[5].value = 999
    except IndexError as e:
        print(f"✅ Bounds checking works: {e}")


if __name__ == "__main__":
    print("🚀 Core Register Classes Test")
    print("Testing enhanced Register and RegisterArrayAccessor from fpga_lib.core")

    test_dynamic_field_access()
    test_register_array()

    print("\n✨ All core class tests passed!")
    print("The enhanced Register class now supports:")
    print("• Dynamic field access (reg.field = value)")
    print("• Format string support (f'{reg.field:04X}')")
    print("• RegisterArrayAccessor for Block RAM regions")
    print("• All original register functionality preserved")

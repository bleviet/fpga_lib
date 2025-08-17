#!/usr/bin/env python3
"""
Access Type Demo

This example demonstrates the benefits of using the centralized AccessType enum
from fpga_lib.core instead of raw strings. It shows type safety, IDE support,
and API clarity improvements.
"""

import sys
import os

# Add the fpga_lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fpga_lib.core import BitField, Register, AbstractBusInterface, AccessType


class MockBus(AbstractBusInterface):
    """Simple mock bus for demonstration."""
    def __init__(self):
        self.memory = {}

    def read_word(self, address: int) -> int:
        return self.memory.get(address, 0)

    def write_word(self, address: int, data: int) -> None:
        self.memory[address] = data


def demonstrate_enum_benefits():
    """Show the benefits of using AccessType enum vs strings."""
    print("🎯 AccessType Enum Benefits Demo")
    print("=" * 50)

    bus = MockBus()

    # ✅ GOOD: Using AccessType enum (type-safe, IDE autocomplete)
    print("\n✅ Using AccessType enum (recommended):")

    fields_with_enum = [
        BitField("enable", 0, 1, AccessType.RW, "System enable"),
        BitField("status", 1, 4, AccessType.RO, "Status flags"),
        BitField("trigger", 8, 1, AccessType.WO, "Command trigger"),
        BitField("int_status", 16, 8, AccessType.RW1C, "Interrupt status"),
    ]

    reg = Register("demo_reg", 0x100, bus, fields_with_enum)

    print(f"Created register with {len(fields_with_enum)} fields:")
    for field in fields_with_enum:
        print(f"  - {field.name:12}: {field.access:>4} (bits {field.offset}:{field.offset+field.width-1})")

    # ✅ GOOD: Still supports string access for backward compatibility
    print("\n✅ String access still supported for compatibility:")

    fields_with_strings = [
        BitField("config", 0, 8, "rw", "Configuration"),
        BitField("version", 8, 8, "ro", "Version info"),
    ]

    reg2 = Register("compat_reg", 0x104, bus, fields_with_strings)

    print(f"Created register with {len(fields_with_strings)} fields:")
    for field in fields_with_strings:
        print(f"  - {field.name:12}: {field.access:>4} (bits {field.offset}:{field.offset+field.width-1})")

    # 🚫 BAD: This would cause a validation error
    print("\n🚫 Invalid access types are caught at creation time:")

    try:
        invalid_field = BitField("bad", 0, 1, "invalid", "This will fail")
        print("ERROR: This should not have succeeded!")
    except ValueError as e:
        print(f"✅ Caught invalid access type: {e}")

    # 🎯 USAGE: Show practical field operations
    print("\n🎯 Practical field operations:")

    # Configure the system
    reg.enable = 1
    reg.trigger = 1  # Write-only trigger

    # Set interrupt status (will be cleared by writing 1)
    bus.write_word(0x100, 0x00FF0000)  # Set some interrupt bits
    print(f"Initial int_status: 0x{reg.int_status:02X}")

    # Clear specific interrupt bits (rw1c behavior)
    reg.int_status = 0x0F  # Clear lower 4 bits
    print(f"After clearing 0x0F: 0x{reg.int_status:02X}")

    # Try to read write-only field (should fail)
    try:
        trigger_val = reg.trigger
        print("ERROR: Should not be able to read write-only field!")
    except ValueError as e:
        print(f"✅ Write-only protection works: {e}")
    except AttributeError as e:
        print(f"✅ Write-only protection works: {e}")

    print(f"\nFinal register value: 0x{reg.read():08X}")


def show_api_improvements():
    """Demonstrate API clarity improvements."""
    print("\n🚀 API Clarity and Type Safety")
    print("=" * 50)

    # Show available access types
    print("\n📋 Available access types:")
    for access_type in AccessType:
        print(f"  - AccessType.{access_type.name:4} = '{access_type.value}'")

    # Show IDE benefits (simulated)
    print("\n💡 IDE Benefits:")
    print("  - Autocomplete: AccessType.[TAB] shows all options")
    print("  - Type checking: Catches typos at development time")
    print("  - Refactoring: Safe rename across entire codebase")
    print("  - Documentation: Clear contract for valid values")

    # Show conversion between enum and string
    print("\n🔄 Enum ↔ String conversion:")
    rw1c_enum = AccessType.RW1C
    rw1c_string = rw1c_enum.value
    print(f"  Enum: {rw1c_enum}")
    print(f"  String: '{rw1c_string}'")
    print(f"  Back to enum: AccessType('{rw1c_string}')")


if __name__ == "__main__":
    demonstrate_enum_benefits()
    show_api_improvements()

    print("\n✨ Summary:")
    print("  • AccessType enum provides type safety and IDE support")
    print("  • String access types still work for backward compatibility")
    print("  • Invalid access types are caught early")
    print("  • API is clearer and more maintainable")

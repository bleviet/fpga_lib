#!/usr/bin/env python3
"""
Register Basics Example

This example demonstrates the fundamental operations of the generic
BitField and Register classes from fpga_lib.core.

Topics covered:
- Creating BitFields with different access types
- Building Registers from BitFields
- Basic read/write operations
- Field validation and error handling
- Reset functionality
"""

import sys
import os

# Add the fpga_lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fpga_lib.core import BitField, Register, AbstractBusInterface


class MockBusInterface(AbstractBusInterface):
    """Simple mock bus for demonstration."""
    def __init__(self):
        self._memory = {}
        print(f"🔌 Mock bus interface created")

    def read_word(self, address: int) -> int:
        value = self._memory.get(address, 0)
        print(f"📖 Bus read  [0x{address:04X}] = 0x{value:08X}")
        return value

    def write_word(self, address: int, data: int) -> None:
        self._memory[address] = data & 0xFFFFFFFF
        print(f"✏️  Bus write [0x{address:04X}] = 0x{data:08X}")


def bitfield_basics():
    """Demonstrate BitField creation and properties."""
    print("=" * 50)
    print("BITFIELD BASICS")
    print("=" * 50)

    # Create different types of bit fields
    enable_field = BitField("enable", 0, 1, "rw", "Enable bit")
    status_field = BitField("status", 1, 3, "r", "Status bits")
    config_field = BitField("config", 4, 4, "w", "Configuration")
    data_field = BitField("data", 8, 8, "rw", "Data byte", reset_value=0xFF)

    print("Created BitFields:")
    print(f"  📍 {enable_field}")
    print(f"  📍 {status_field}")
    print(f"  📍 {config_field}")
    print(f"  📍 {data_field}")

    print(f"\nBitField properties:")
    print(f"  • Enable field covers bits {enable_field.offset}-{enable_field.offset + enable_field.width - 1}")
    print(f"  • Status field max value: {status_field.max_value}")
    print(f"  • Config field is {'writable' if config_field.access in ['w', 'rw'] else 'read-only'}")
    print(f"  • Data field reset value: 0x{data_field.reset_value:02X}")


def register_basics():
    """Demonstrate Register creation and basic operations."""
    print("\n" + "=" * 50)
    print("REGISTER BASICS")
    print("=" * 50)

    bus = MockBusInterface()

    # Create a control register
    control_reg = Register(
        name="control",
        offset=0x100,
        bus=bus,
        fields=[
            BitField("enable", 0, 1, "rw", "Enable device", reset_value=0),
            BitField("mode", 1, 2, "rw", "Operating mode", reset_value=1),
            BitField("status", 4, 3, "r", "Device status"),
            BitField("command", 8, 8, "w", "Command register"),
            BitField("version", 16, 8, "r", "Hardware version", reset_value=0x42),
        ],
        description="Main control register"
    )

    print(f"📋 Created register: {control_reg}")
    print(f"   Description: {control_reg.description}")
    print(f"   Field count: {len(control_reg.get_fields())}")
    print(f"   Field names: {', '.join(control_reg.get_fields())}")

    return control_reg


def field_operations(register):
    """Demonstrate field read/write operations."""
    print("\n" + "=" * 50)
    print("FIELD OPERATIONS")
    print("=" * 50)

    # Reset register to show initial state
    print("🔄 Resetting register to default values...")
    register.reset()

    print(f"\n📊 Initial register state: 0x{register.read():08X}")
    print("📋 Individual field values:")
    for field_name in ["enable", "mode", "status", "version"]:
        try:
            value = register.read_field(field_name)
            print(f"   • {field_name}: {value} (0x{value:X})")
        except Exception as e:
            print(f"   • {field_name}: Error - {e}")

    # Write to writable fields
    print("\n✏️  Writing to writable fields...")
    register.write_field("enable", 1)
    register.write_field("mode", 3)

    print(f"\n📊 After writes: 0x{register.read():08X}")
    print("📋 Updated field values:")
    for field_name in ["enable", "mode", "status", "version"]:
        try:
            value = register.read_field(field_name)
            print(f"   • {field_name}: {value} (0x{value:X})")
        except Exception as e:
            print(f"   • {field_name}: Error - {e}")


def bulk_operations(register):
    """Demonstrate bulk field operations."""
    print("\n" + "=" * 50)
    print("BULK OPERATIONS")
    print("=" * 50)

    # Write multiple fields at once
    print("📝 Writing multiple fields in one operation...")
    register.write_multiple_fields({
        "enable": 1,
        "mode": 2
    })

    # Read all fields
    print("\n📖 Reading all fields...")
    all_fields = register.read_all_fields()
    for name, value in all_fields.items():
        print(f"   • {name}: {value}")


def error_handling(register):
    """Demonstrate error handling and validation."""
    print("\n" + "=" * 50)
    print("ERROR HANDLING & VALIDATION")
    print("=" * 50)

    test_cases = [
        ("Invalid field name", lambda: register.write_field("invalid_field", 1)),
        ("Write to read-only field", lambda: register.write_field("version", 0x99)),
        ("Value too large for field", lambda: register.write_field("mode", 8)),  # mode is 2-bit (max 3)
        ("Read write-only field", lambda: register.read_field("command")),
    ]

    for description, operation in test_cases:
        print(f"\n🧪 Testing: {description}")
        try:
            result = operation()
            print(f"   ❌ Expected error but got: {result}")
        except Exception as e:
            print(f"   ✅ Correctly caught error: {e}")


def demonstrate_register_basics():
    """Main demonstration function."""
    print("🚀 FPGA Register Abstraction - Basic Operations Demo\n")

    bitfield_basics()
    register = register_basics()
    field_operations(register)
    bulk_operations(register)
    error_handling(register)
    register_array_preview()

    print("\n" + "=" * 50)
    print("✅ DEMO COMPLETE")
    print("=" * 50)
    print("Key takeaways:")
    print("• BitFields define register structure with validation")
    print("• Registers provide high-level interface to hardware")
    print("• Access control prevents invalid operations")
    print("• Type safety catches errors at the API level")
    print("• Reset functionality ensures known state")
    print("• Register arrays provide memory-efficient Block RAM access")
    print("• Same patterns work for any IP core type")


def register_array_preview():
    """Preview of register array functionality."""
    print("=" * 50)
    print("REGISTER ARRAY PREVIEW")
    print("=" * 50)
    print("The updated concept document introduces register arrays for Block RAM:")
    print()
    print("YAML Definition:")
    print("  - name: lut_entry")
    print("    offset: 0x100")
    print("    count: 64          # 64 entries")
    print("    stride: 4          # 4 bytes apart")
    print("    fields:")
    print("      - name: coefficient")
    print("        bits: '[15:0]'")
    print("        access: rw")
    print()
    print("Usage:")
    print("  driver.lut_entry[5].coefficient = 0xABCD")
    print("  driver.lut_entry[10].enabled = 1")
    print("  coeff = driver.lut_entry[5].coefficient")
    print()
    print("Benefits:")
    print("• On-demand register creation (memory efficient)")
    print("• Pythonic array indexing syntax")
    print("• Same field validation as single registers")
    print("• Bounds checking with meaningful errors")
    print()
    print("📚 See register_array_example.py for full demonstration")


if __name__ == "__main__":
    demonstrate_register_basics()

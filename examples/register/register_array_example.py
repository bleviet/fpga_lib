#!/usr/bin/env python3
"""
Register Array Example

This example demonstrates the register array functionality from the updated
concept document. It shows how to define and work with Block RAM regions
using the RegisterArrayAccessor pattern from fpga_lib.core.

Topics covered:
- YAML definition of register arrays using count and stride
- RegisterArrayAccessor from fpga_lib.core
- On-demand register creation
- Memory-efficient handling of large register arrays
- Practical examples with lookup tables, packet buffers, and descriptor rings
- Dynamic field access using the enhanced Register class

Note: This example uses the enhanced Register and RegisterArrayAccessor classes
from fpga_lib.core, which now include dynamic field access and array functionality.
"""

import sys
import os
from dataclasses import dataclass
from enum import Enum, auto

# Add the fpga_lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fpga_lib.core import BitField, Register, AbstractBusInterface, RegisterArrayAccessor


class Access(Enum):
    """Access types for register fields."""
    RO = auto()
    RW = auto()
    WO = auto()


class MockBusInterface(AbstractBusInterface):
    """Enhanced mock bus for demonstration with memory visualization."""
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

    def dump_memory(self, start_addr: int, count: int):
        """Debug helper to show memory contents."""
        print(f"\n📋 Memory dump from 0x{start_addr:04X}:")
        for i in range(count):
            addr = start_addr + (i * 4)
            value = self._memory.get(addr, 0)
            print(f"  [0x{addr:04X}] = 0x{value:08X}")


def _parse_bits(bits_def):
    """Helper to parse 'bit: 0' or 'bits: [7:4]' into offset and width."""
    if isinstance(bits_def, int):
        return bits_def, 1
    if isinstance(bits_def, str) and ':' in bits_def:
        high, low = map(int, bits_def.strip('[]').split(':'))
        return low, (high - low + 1)
    raise ValueError(f"Invalid bit definition: {bits_def}")


class IpCoreDriver:
    """A container for all the register objects and arrays."""
    def __init__(self, bus_interface):
        self._bus = bus_interface


def load_from_yaml_data(yaml_data: dict, bus_interface: AbstractBusInterface):
    """Loads a register map from YAML data and builds a driver object."""
    driver = IpCoreDriver(bus_interface)

    for reg_info in yaml_data.get('registers', []):
        fields = []
        for field_info in reg_info.get('fields', []):
            offset, width = _parse_bits(field_info.get('bit') or field_info.get('bits', 0))
            fields.append(BitField(
                name=field_info['name'],
                offset=offset,
                width=width,
                access=field_info.get('access', 'rw').lower(),  # Convert to lowercase
                description=field_info.get('description', '')
            ))

        # Check if this is a register array
        if 'count' in reg_info:
            accessor = RegisterArrayAccessor(
                name=reg_info['name'],
                base_offset=reg_info['offset'],
                count=reg_info['count'],
                stride=reg_info.get('stride', 4), # Default to 4-byte stride
                field_template=fields,
                bus_interface=bus_interface
            )
            setattr(driver, reg_info['name'], accessor)
        else: # It's a single register
            register = Register(
                name=reg_info['name'],
                offset=reg_info['offset'],
                bus=bus_interface,
                fields=fields,
                description=reg_info.get('description', '')
            )
            setattr(driver, reg_info['name'], register)

    return driver


def lookup_table_example():
    """Demonstrate a lookup table using register arrays."""
    print("=" * 60)
    print("LOOKUP TABLE EXAMPLE")
    print("=" * 60)

    # Define YAML for a lookup table
    lut_yaml = {
        'registers': [
            {
                'name': 'control',
                'offset': 0x00,
                'description': 'Main control register',
                'fields': [
                    {'name': 'enable', 'bit': 0, 'access': 'rw', 'description': 'Enable LUT'},
                    {'name': 'reset', 'bit': 1, 'access': 'w', 'description': 'Reset LUT'},
                    {'name': 'mode', 'bits': '[3:2]', 'access': 'rw', 'description': 'LUT mode'}
                ]
            },
            {
                'name': 'lut_entry',
                'offset': 0x100,
                'count': 64,
                'stride': 4,
                'description': 'A 64-entry lookup table',
                'fields': [
                    {'name': 'coefficient', 'bits': '[15:0]', 'access': 'rw', 'description': 'Coefficient value'},
                    {'name': 'enabled', 'bit': 31, 'access': 'rw', 'description': 'Enable this LUT entry'}
                ]
            }
        ]
    }

    bus = MockBusInterface()
    driver = load_from_yaml_data(lut_yaml, bus)

    print(f"📊 Created driver with LUT array")
    info = driver.lut_entry.get_info()
    print(f"   - Array: {info['name']}")
    print(f"   - Count: {info['count']} entries")
    print(f"   - Range: {info['address_range']}")
    print(f"   - Total size: {info['total_size']} bytes")

    print(f"\n🔧 Configuring lookup table...")
    # Configure the LUT
    driver.control.enable = 1
    driver.control.mode = 2  # Some operational mode

    print(f"\n📝 Writing LUT entries...")
    # Write some lookup table entries
    test_coefficients = [0x1000, 0x2000, 0x3000, 0x4000, 0x5000]
    for i, coeff in enumerate(test_coefficients):
        driver.lut_entry[i].coefficient = coeff
        driver.lut_entry[i].enabled = 1
        print(f"   - Entry {i}: coefficient = 0x{coeff:04X}, enabled = 1")

    print(f"\n📖 Reading back LUT entries...")
    # Read back and verify
    for i in range(len(test_coefficients)):
        coeff = driver.lut_entry[i].coefficient
        enabled = driver.lut_entry[i].enabled
        print(f"   - Entry {i}: coefficient = 0x{coeff:04X}, enabled = {enabled}")

    # Show memory layout
    bus.dump_memory(0x100, 8)


def packet_buffer_example():
    """Demonstrate a packet buffer using register arrays."""
    print("\n" + "=" * 60)
    print("PACKET BUFFER EXAMPLE")
    print("=" * 60)

    # Define YAML for a packet buffer
    packet_yaml = {
        'registers': [
            {
                'name': 'status',
                'offset': 0x00,
                'description': 'Buffer status register',
                'fields': [
                    {'name': 'ready', 'bit': 0, 'access': 'r', 'description': 'Buffer ready'},
                    {'name': 'full', 'bit': 1, 'access': 'r', 'description': 'Buffer full'},
                    {'name': 'count', 'bits': '[15:8]', 'access': 'r', 'description': 'Packet count'}
                ]
            },
            {
                'name': 'packet_buffer',
                'offset': 0x1000,
                'count': 16,
                'stride': 8,  # 8 bytes per packet entry
                'description': 'Packet buffer with 16 entries',
                'fields': [
                    {'name': 'header', 'bits': '[31:0]', 'access': 'rw', 'description': 'Packet header'},
                    # Note: This would be at offset 0x04 within each entry if we had multiple registers per entry
                ]
            }
        ]
    }

    bus = MockBusInterface()
    driver = load_from_yaml_data(packet_yaml, bus)

    print(f"📦 Created packet buffer driver")
    info = driver.packet_buffer.get_info()
    print(f"   - Buffer: {info['name']}")
    print(f"   - Capacity: {info['count']} packets")
    print(f"   - Range: {info['address_range']}")
    print(f"   - Entry size: {info['stride']} bytes")

    print(f"\n📝 Writing packet data...")
    # Write some packet data
    packets = [
        {'header': 0xDEADBEEF},
        {'header': 0xCAFEBABE},
        {'header': 0x12345678},
        {'header': 0xABCDEF00}
    ]

    for i, packet in enumerate(packets):
        driver.packet_buffer[i].header = packet['header']
        print(f"   - Packet {i}: header = 0x{packet['header']:08X}")

    print(f"\n📖 Reading back packet data...")
    # Read back packets
    for i in range(len(packets)):
        header = driver.packet_buffer[i].header
        print(f"   - Packet {i}: header = 0x{header:08X}")

    # Show memory layout
    bus.dump_memory(0x1000, 6)


def dma_descriptor_example():
    """Demonstrate DMA descriptors using register arrays."""
    print("\n" + "=" * 60)
    print("DMA DESCRIPTOR RING EXAMPLE")
    print("=" * 60)

    # Define YAML for DMA descriptor ring
    dma_yaml = {
        'registers': [
            {
                'name': 'dma_control',
                'offset': 0x00,
                'description': 'DMA control register',
                'fields': [
                    {'name': 'enable', 'bit': 0, 'access': 'rw', 'description': 'DMA enable'},
                    {'name': 'interrupt_enable', 'bit': 1, 'access': 'rw', 'description': 'Interrupt enable'},
                    {'name': 'ring_size', 'bits': '[7:4]', 'access': 'rw', 'description': 'Ring size'}
                ]
            },
            {
                'name': 'descriptor_ring',
                'offset': 0x2000,
                'count': 8,
                'stride': 16,  # 16 bytes per descriptor
                'description': 'DMA descriptor ring with 8 entries',
                'fields': [
                    {'name': 'src_addr', 'bits': '[31:0]', 'access': 'rw', 'description': 'Source address'},
                    # In a real implementation, each descriptor would have multiple 32-bit registers
                    # For this example, we'll just show the pattern with the first register
                ]
            }
        ]
    }

    bus = MockBusInterface()
    driver = load_from_yaml_data(dma_yaml, bus)

    print(f"🔄 Created DMA descriptor ring driver")
    info = driver.descriptor_ring.get_info()
    print(f"   - Ring: {info['name']}")
    print(f"   - Descriptors: {info['count']}")
    print(f"   - Range: {info['address_range']}")
    print(f"   - Descriptor size: {info['stride']} bytes")

    print(f"\n🔧 Configuring DMA...")
    # Configure DMA
    driver.dma_control.enable = 1
    driver.dma_control.interrupt_enable = 1
    driver.dma_control.ring_size = 8  # 8 descriptors

    print(f"\n📝 Setting up DMA descriptors...")
    # Setup DMA descriptors
    base_addr = 0x10000000
    for i in range(8):
        src_addr = base_addr + (i * 0x1000)
        driver.descriptor_ring[i].src_addr = src_addr
        print(f"   - Descriptor {i}: src_addr = 0x{src_addr:08X}")

    print(f"\n📖 Reading back descriptor ring...")
    # Read back descriptors
    for i in range(8):
        src_addr = driver.descriptor_ring[i].src_addr
        print(f"   - Descriptor {i}: src_addr = 0x{src_addr:08X}")

    # Show memory layout
    bus.dump_memory(0x2000, 10)


def array_bounds_testing():
    """Demonstrate array bounds checking."""
    print("\n" + "=" * 60)
    print("ARRAY BOUNDS TESTING")
    print("=" * 60)

    # Create a small array for testing
    test_yaml = {
        'registers': [
            {
                'name': 'test_array',
                'offset': 0x100,
                'count': 4,
                'stride': 4,
                'description': 'Small test array',
                'fields': [
                    {'name': 'value', 'bits': '[31:0]', 'access': 'rw', 'description': 'Test value'}
                ]
            }
        ]
    }

    bus = MockBusInterface()
    driver = load_from_yaml_data(test_yaml, bus)

    print(f"🧪 Created test array with {len(driver.test_array)} elements")

    print(f"\n✅ Valid access tests:")
    # Valid accesses
    for i in range(len(driver.test_array)):
        driver.test_array[i].value = i * 100
        print(f"   - test_array[{i}].value = {driver.test_array[i].value}")

    print(f"\n❌ Invalid access tests:")
    # Test bounds checking
    try:
        driver.test_array[4].value = 999  # Should fail - index out of bounds
    except IndexError as e:
        print(f"   - Caught expected error: {e}")

    try:
        driver.test_array[-1].value = 999  # Should fail - negative index
    except IndexError as e:
        print(f"   - Caught expected error: {e}")


def main():
    """Run all register array examples."""
    print("🚀 Register Array Examples")
    print("Based on the updated concept document")
    print("Demonstrates: count, stride, RegisterArrayAccessor, on-demand creation")

    # Run examples
    lookup_table_example()
    packet_buffer_example()
    dma_descriptor_example()
    array_bounds_testing()

    print("\n" + "=" * 60)
    print("✨ All examples completed successfully!")
    print("Key benefits demonstrated:")
    print("- Memory efficient on-demand register creation")
    print("- Clean Pythonic array indexing syntax")
    print("- Proper bounds checking and error handling")
    print("- Flexible YAML configuration with count/stride")
    print("- Reusable across different IP core types")


if __name__ == "__main__":
    main()

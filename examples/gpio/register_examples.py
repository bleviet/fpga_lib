#!/usr/bin/env python3
"""
Example: Using Generic Register Classes for Different IP Cores

This example demonstrates how the generic BitField and Register classes
from fpga_lib.core can be used to create drivers for various IP cores,
not just GPIO.
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

    def read_word(self, address: int) -> int:
        return self._memory.get(address, 0)

    def write_word(self, address: int, data: int) -> None:
        self._memory[address] = data & 0xFFFFFFFF


def uart_example():
    """Example: UART IP Core using generic register classes."""
    print("=== UART IP Core Example ===")

    bus = MockBusInterface()

    # Define UART registers using generic BitField and Register classes

    # Control Register (offset 0x00)
    control_reg = Register(
        name="control",
        offset=0x00,
        bus=bus,
        fields=[
            BitField("enable", 0, 1, "rw", "UART enable"),
            BitField("parity_enable", 1, 1, "rw", "Parity enable"),
            BitField("parity_odd", 2, 1, "rw", "Odd parity (0=even, 1=odd)"),
            BitField("stop_bits", 3, 1, "rw", "Stop bits (0=1 bit, 1=2 bits)"),
            BitField("data_bits", 4, 2, "rw", "Data bits (0=5, 1=6, 2=7, 3=8)"),
            BitField("flow_control", 8, 2, "rw", "Flow control (0=none, 1=RTS/CTS)"),
        ],
        description="UART control and configuration register"
    )

    # Status Register (offset 0x04)
    status_reg = Register(
        name="status",
        offset=0x04,
        bus=bus,
        fields=[
            BitField("tx_ready", 0, 1, "r", "Transmitter ready"),
            BitField("rx_valid", 1, 1, "r", "Receiver data valid"),
            BitField("tx_empty", 2, 1, "r", "Transmit buffer empty"),
            BitField("rx_full", 3, 1, "r", "Receive buffer full"),
            BitField("parity_error", 4, 1, "r", "Parity error flag"),
            BitField("frame_error", 5, 1, "r", "Frame error flag"),
            BitField("overrun_error", 6, 1, "r", "Overrun error flag"),
        ],
        description="UART status register"
    )

    # Baud Rate Register (offset 0x08)
    baud_reg = Register(
        name="baud_rate",
        offset=0x08,
        bus=bus,
        fields=[
            BitField("divisor", 0, 16, "rw", "Baud rate divisor"),
            BitField("prescaler", 16, 8, "rw", "Clock prescaler"),
        ],
        description="UART baud rate configuration"
    )

    # Data Registers (separate TX and RX)
    tx_data_reg = Register(
        name="tx_data",
        offset=0x0C,
        bus=bus,
        fields=[
            BitField("tx_data", 0, 8, "w", "Transmit data"),
        ],
        description="UART transmit data register"
    )

    rx_data_reg = Register(
        name="rx_data",
        offset=0x10,
        bus=bus,
        fields=[
            BitField("rx_data", 0, 8, "r", "Receive data"),
        ],
        description="UART receive data register"
    )

    print("Created UART registers with generic register classes:")
    for reg in [control_reg, status_reg, baud_reg, tx_data_reg, rx_data_reg]:
        print(f"  - {reg}")

    # Configure UART
    print("\nConfiguring UART:")
    control_reg.write_field("enable", 1)
    control_reg.write_field("data_bits", 3)  # 8 data bits
    control_reg.write_field("parity_enable", 1)
    baud_reg.write_field("divisor", 868)  # 115200 baud (50MHz / 57.6 = ~868)

    # Read configuration
    print("  - UART enabled:", bool(control_reg.read_field("enable")))
    print("  - Data bits:", control_reg.read_field("data_bits") + 5)
    print("  - Parity enabled:", bool(control_reg.read_field("parity_enable")))
    print("  - Baud divisor:", baud_reg.read_field("divisor"))

    print("  - Control register value: 0x{:08X}".format(control_reg.read()))


def spi_example():
    """Example: SPI Controller IP Core using generic register classes."""
    print("\n=== SPI Controller IP Core Example ===")

    bus = MockBusInterface()

    # SPI Control Register
    spi_control = Register(
        name="spi_control",
        offset=0x00,
        bus=bus,
        fields=[
            BitField("enable", 0, 1, "rw", "SPI controller enable"),
            BitField("master_mode", 1, 1, "rw", "Master mode (1=master, 0=slave)"),
            BitField("cpol", 2, 1, "rw", "Clock polarity"),
            BitField("cpha", 3, 1, "rw", "Clock phase"),
            BitField("data_width", 4, 4, "rw", "Data width (0=8bit, 1=16bit, etc.)"),
            BitField("cs_auto", 8, 1, "rw", "Automatic chip select"),
            BitField("cs_active_low", 9, 1, "rw", "Chip select active low"),
        ]
    )

    # SPI Status Register
    spi_status = Register(
        name="spi_status",
        offset=0x04,
        bus=bus,
        fields=[
            BitField("busy", 0, 1, "r", "Transfer in progress"),
            BitField("tx_ready", 1, 1, "r", "Transmit ready"),
            BitField("rx_valid", 2, 1, "r", "Receive data valid"),
            BitField("tx_underrun", 4, 1, "r", "Transmit underrun error"),
            BitField("rx_overrun", 5, 1, "r", "Receive overrun error"),
        ]
    )

    # SPI Clock Divider Register
    spi_clock = Register(
        name="spi_clock",
        offset=0x08,
        bus=bus,
        fields=[
            BitField("divider", 0, 16, "rw", "Clock divider value"),
        ]
    )

    print("Created SPI registers:")
    for reg in [spi_control, spi_status, spi_clock]:
        print(f"  - {reg}")

    # Configure SPI in master mode
    print("\nConfiguring SPI as master:")
    spi_control.write_multiple_fields({
        "enable": 1,
        "master_mode": 1,
        "cpol": 0,
        "cpha": 0,
        "data_width": 0,  # 8-bit
        "cs_auto": 1,
        "cs_active_low": 1
    })
    spi_clock.write_field("divider", 100)  # Clock divider

    # Read back configuration
    config = spi_control.read_all_fields()
    print("  - Configuration:", config)
    print("  - Clock divider:", spi_clock.read_field("divider"))


def timer_example():
    """Example: Timer IP Core using generic register classes."""
    print("\n=== Timer IP Core Example ===")

    bus = MockBusInterface()

    # Timer Control Register
    timer_ctrl = Register(
        name="timer_control",
        offset=0x00,
        bus=bus,
        fields=[
            BitField("enable", 0, 1, "rw", "Timer enable", reset_value=0),
            BitField("auto_reload", 1, 1, "rw", "Auto-reload mode", reset_value=0),
            BitField("direction", 2, 1, "rw", "Count direction (0=up, 1=down)", reset_value=0),
            BitField("prescaler", 4, 4, "rw", "Clock prescaler", reset_value=0),
            BitField("interrupt_enable", 8, 1, "rw", "Interrupt enable", reset_value=0),
        ]
    )

    # Timer Value Register
    timer_value = Register(
        name="timer_value",
        offset=0x04,
        bus=bus,
        fields=[
            BitField("count", 0, 32, "rw", "Timer count value", reset_value=0),
        ]
    )

    # Timer Compare Register
    timer_compare = Register(
        name="timer_compare",
        offset=0x08,
        bus=bus,
        fields=[
            BitField("compare_value", 0, 32, "rw", "Timer compare value", reset_value=0xFFFFFFFF),
        ]
    )

    # Timer Status Register
    timer_status = Register(
        name="timer_status",
        offset=0x0C,
        bus=bus,
        fields=[
            BitField("overflow", 0, 1, "r", "Timer overflow flag"),
            BitField("compare_match", 1, 1, "r", "Compare match flag"),
            BitField("running", 2, 1, "r", "Timer is running"),
        ]
    )

    print("Created Timer registers:")
    for reg in [timer_ctrl, timer_value, timer_compare, timer_status]:
        print(f"  - {reg}")

    # Test reset functionality
    print("\nTesting reset functionality:")
    print("  - Before reset - Control:", hex(timer_ctrl.read()))
    print("  - Before reset - Compare:", hex(timer_compare.read()))

    # Reset registers to default values
    timer_ctrl.reset()
    timer_value.reset()
    timer_compare.reset()

    print("  - After reset - Control:", hex(timer_ctrl.read()))
    print("  - After reset - Value:", hex(timer_value.read()))
    print("  - After reset - Compare:", hex(timer_compare.read()))

    # Configure timer
    print("\nConfiguring timer:")
    timer_ctrl.write_multiple_fields({
        "enable": 1,
        "auto_reload": 1,
        "prescaler": 7,  # Divide by 128
        "interrupt_enable": 1
    })
    timer_compare.write_field("compare_value", 1000)

    print("  - Timer configured for 1000 count with auto-reload and interrupts")


def demonstrate_reusability():
    """Show how the same register classes work for different IP cores."""
    print("\n" + "="*60)
    print("DEMONSTRATING REGISTER CLASS REUSABILITY")
    print("="*60)
    print("The same BitField and Register classes from fpga_lib.core")
    print("can be used to create drivers for ANY IP core:")
    print()

    uart_example()
    spi_example()
    timer_example()

    print("\n" + "="*60)
    print("BENEFITS OF GENERIC REGISTER CLASSES:")
    print("="*60)
    print("✅ Reusable across all IP core types")
    print("✅ Consistent API for all register operations")
    print("✅ Built-in field validation and access control")
    print("✅ Comprehensive error handling")
    print("✅ Support for complex field operations")
    print("✅ Reset value management")
    print("✅ Register introspection capabilities")
    print("✅ Reduced code duplication")
    print("✅ Easier testing and maintenance")


if __name__ == "__main__":
    demonstrate_reusability()

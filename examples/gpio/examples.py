"""
GPIO Example Usage Scripts

This module demonstrates how to use the GPIO driver with different
bus interfaces, showcasing the portability of the unified architecture.
Now includes examples using both traditional and YAML-driven approaches.
"""

import asyncio
from typing import Any
from config import (
    create_mock_gpio_driver,
    create_simulation_gpio_driver,
    create_jtag_gpio_driver,
    create_pcie_gpio_driver,
    create_ethernet_gpio_driver,
    MockBusConfig,
    SimulationBusConfig,
    JtagBusConfig
)
from gpio_driver import GpioDirection, GpioValue
from gpio_wrapper import GpioDriverWrapper
from memory_map_loader import load_from_yaml


def basic_gpio_example():
    """
    Basic GPIO usage example using mock bus interface.

    This example demonstrates the fundamental GPIO operations
    using a mock bus interface for testing and learning.
    """
    print("=== Basic GPIO Example ===")

    # Create a GPIO driver with 8 pins for simplicity
    driver = create_mock_gpio_driver()

    print(f"Created GPIO driver with {driver.num_pins} pins")

    # Configure pin 0 as output
    driver.configure_pin(0, GpioDirection.OUTPUT, GpioValue.LOW)
    print("Configured pin 0 as output with initial value LOW")

    # Configure pin 1 as input with interrupt enabled
    driver.configure_pin(1, GpioDirection.INPUT, interrupt_enable=True)
    print("Configured pin 1 as input with interrupt enabled")

    # Set pin 0 to HIGH
    driver.set_pin_value(0, GpioValue.HIGH)
    print("Set pin 0 to HIGH")

    # Read pin 0 value
    value = driver.get_pin_value(0)
    print(f"Pin 0 value: {value.name}")

    # Read all pins
    all_values = driver.get_all_pins_value()
    print(f"All pins value: 0x{all_values:02X}")

    # Show register summary
    registers = driver.get_register_summary()
    print("Register Summary:")
    for reg_name, value in registers.items():
        print(f"  {reg_name}: 0x{value:08X}")

    print()


def multi_pin_gpio_example():
    """
    Multi-pin GPIO usage example demonstrating bulk operations.
    """
    print("=== Multi-Pin GPIO Example ===")

    # Create a GPIO driver with 16 pins
    driver = create_mock_gpio_driver()

    # Configure pins 0-7 as outputs
    for pin in range(8):
        driver.set_pin_direction(pin, GpioDirection.OUTPUT)

    # Configure pins 8-15 as inputs
    for pin in range(8, 16):
        driver.set_pin_direction(pin, GpioDirection.INPUT)

    print("Configured pins 0-7 as outputs, pins 8-15 as inputs")

    # Set a pattern on output pins (0b10101010)
    output_pattern = 0b10101010
    driver.set_pins_value(0xFF, output_pattern)  # Mask for pins 0-7
    print(f"Set output pattern: 0b{output_pattern:08b}")

    # Read back the pattern
    current_values = driver.get_all_pins_value()
    print(f"Current GPIO values: 0x{current_values:04X}")

    # Toggle all output pins
    current_outputs = current_values & 0xFF
    toggled_outputs = current_outputs ^ 0xFF
    driver.set_pins_value(0xFF, toggled_outputs)
    print(f"Toggled outputs to: 0b{toggled_outputs:08b}")

    # Final state
    final_values = driver.get_all_pins_value()
    print(f"Final GPIO values: 0x{final_values:04X}")

    print()


def interrupt_gpio_example():
    """
    GPIO interrupt handling example.
    """
    print("=== GPIO Interrupt Example ===")

    driver = create_mock_gpio_driver()

    # Configure pins 0-3 as inputs with interrupts enabled
    interrupt_pins = [0, 1, 2, 3]
    for pin in interrupt_pins:
        driver.configure_pin(pin, GpioDirection.INPUT, interrupt_enable=True)

    print(f"Configured pins {interrupt_pins} as inputs with interrupts enabled")

    # Simulate interrupt status (in real hardware, this would be set by the IP)
    # For demonstration, we'll manually trigger some interrupts
    simulated_interrupt_mask = 0b0101  # Pins 0 and 2 have pending interrupts

    # In a real system, you would read the interrupt status register
    interrupt_status = driver.get_interrupt_status()
    print(f"Current interrupt status: 0x{interrupt_status:02X}")

    # Simulate checking for specific pin interrupts
    for pin in interrupt_pins:
        if simulated_interrupt_mask & (1 << pin):
            print(f"Interrupt detected on pin {pin}")

            # Handle the interrupt (application-specific logic here)
            print(f"  Handling interrupt for pin {pin}")

            # Clear the interrupt for this pin
            driver.clear_interrupt_status(1 << pin)
            print(f"  Cleared interrupt for pin {pin}")

    print()


def simulation_example(dut=None, clock=None):
    """
    Example for simulation environment using cocotb.

    Args:
        dut: DUT object from cocotb (None for demonstration)
        clock: Clock signal (None for demonstration)
    """
    print("=== Simulation Example (Cocotb) ===")

    if dut is None or clock is None:
        print("Note: This example requires a cocotb DUT and clock signal")
        print("Showing configuration only...")

        # Create GPIO driver for simulation (new YAML-driven approach)
        print("Using YAML-driven GPIO driver for simulation:")
        print("  - Memory map: gpio_memory_map.yaml")
        print("  - Bus interface: Simulation (cocotb)")
        print("  - DUT bus: s_axi")
        print("  - Clock domain: provided clock")

        # Example of how it would be created:
        # driver = create_simulation_gpio_driver(dut, "s_axi", clock)
        print("Configuration completed (mock)")
        return

    # Create simulation driver
    driver = create_simulation_gpio_driver(
        dut=dut,
        bus_name="s_axi",
        clock=clock
    )

    print("Created simulation GPIO driver")

    # Example simulation test sequence
    # Note: In real cocotb, these operations would need proper async handling

    # Configure some pins
    driver.set_pin_direction(0, GpioDirection.OUTPUT)
    driver.set_pin_direction(1, GpioDirection.INPUT)

    # Test basic operations
    driver.set_pin_value(0, GpioValue.HIGH)
    value = driver.get_pin_value(0)

    print(f"Simulation test completed, pin 0 value: {value.name}")
    print()


def hardware_jtag_example(jtag_session=None):
    """
    Example for hardware environment using JTAG.

    Args:
        jtag_session: JTAG session object (None for demonstration)
    """
    print("=== Hardware JTAG Example ===")

    if jtag_session is None:
        print("Note: This example requires a JTAG session object")
        print("Showing configuration only...")

        # Create GPIO driver for JTAG (new YAML-driven approach)
        print("Using YAML-driven GPIO driver for JTAG:")
        print("  - Memory map: gpio_memory_map.yaml")
        print("  - Bus interface: JTAG")
        print("  - Chain position: 0")
        print("  - Base address: 0x40000000")

        # Example of how it would be created:
        # driver = create_jtag_gpio_driver(jtag_session, 0, 0x40000000)
        print("Configuration completed (mock)")
        return

    # Create JTAG driver
    driver = create_jtag_gpio_driver(
        jtag_session=jtag_session,
        chain_position=0,
        base_address=0x40000000
    )

    print("Created JTAG GPIO driver")

    # Example hardware test sequence
    try:
        # Configure LED pins as outputs
        led_pins = [0, 1, 2, 3]
        for pin in led_pins:
            driver.set_pin_direction(pin, GpioDirection.OUTPUT)

        # Blink LEDs pattern
        patterns = [0b0001, 0b0010, 0b0100, 0b1000, 0b0100, 0b0010]
        for pattern in patterns:
            driver.set_pins_value(0x0F, pattern)  # Set pins 0-3
            # In real hardware, you might want to add a delay here

        # Configure switch pins as inputs
        switch_pins = [8, 9, 10, 11]
        for pin in switch_pins:
            driver.set_pin_direction(pin, GpioDirection.INPUT)

        # Read switch states
        switch_states = (driver.get_all_pins_value() >> 8) & 0x0F
        print(f"Switch states: 0b{switch_states:04b}")

    except Exception as e:
        print(f"Hardware test failed: {e}")

    print()


def advanced_configuration_example():
    """
    Advanced example showing different configuration options.
    """
    print("=== Advanced Configuration Example ===")

    # Example 1: High pin count GPIO (YAML-based, always 32 pins)
    high_pin_driver = create_mock_gpio_driver(driver_name="High Pin Count GPIO")
    print(f"Created high pin count driver: {high_pin_driver.num_pins} pins")

    # Example 2: Multiple GPIO instances with different names
    gpio_configs = [
        {"name": "GPIO_A"},
        {"name": "GPIO_B"},
        {"name": "GPIO_C"},
    ]

    gpio_drivers = {}
    for config in gpio_configs:
        driver = create_mock_gpio_driver(
            driver_name=config["name"]
        )
        gpio_drivers[config["name"]] = driver
        print(f"Created {config['name']}: {driver.num_pins} pins")

    # Example 3: Different bus types for same functionality
    bus_examples = [
        {"type": "PCIe", "path": "/dev/xdma0_user"},
        {"type": "Ethernet", "host": "192.168.1.100", "port": 8080},
    ]

    for bus_config in bus_examples:
        if bus_config["type"] == "PCIe":
            print(f"PCIe GPIO config: {bus_config['path']}")
        elif bus_config["type"] == "Ethernet":
            print(f"Ethernet GPIO config: {bus_config['host']}:{bus_config['port']}")

    print()


def performance_test_example():
    """
    Performance testing example for different operations.
    """
    print("=== Performance Test Example ===")

    driver = create_mock_gpio_driver()

    # Test individual pin operations
    print("Testing individual pin operations...")
    import time

    start_time = time.time()
    for i in range(1000):
        driver.set_pin_value(0, GpioValue.HIGH)
        driver.set_pin_value(0, GpioValue.LOW)
    end_time = time.time()

    print(f"1000 individual pin toggles took: {(end_time - start_time)*1000:.2f} ms")

    # Test bulk operations
    print("Testing bulk operations...")

    start_time = time.time()
    for i in range(1000):
        driver.set_pins_value(0xFFFFFFFF, 0xAAAAAAAA)
        driver.set_pins_value(0xFFFFFFFF, 0x55555555)
    end_time = time.time()

    print(f"1000 bulk pin toggles took: {(end_time - start_time)*1000:.2f} ms")

    print()


def yaml_driven_example():
    """
    YAML-driven GPIO example using memory map loader.

    This example demonstrates the new YAML-based approach where
    register definitions are loaded from a YAML file.
    """
    print("YAML-Driven GPIO Example")
    print("-" * 40)

    # Create GPIO driver from YAML memory map
    driver = create_mock_gpio_driver("gpio_memory_map.yaml", "YAML GPIO Example")

    print(f"Created GPIO driver from YAML: {driver._driver._name}")

    # Get core information from YAML-defined config
    core_info = driver.get_core_info()
    print(f"Core info: {core_info}")

    # Demonstrate direct register access (YAML-defined registers)
    print("\n1. Direct Register Access (from YAML):")

    # Set direction register (all pins as outputs for lower 16 bits)
    driver._driver.direction.gpio_dir = 0x0000FFFF
    print("   Set lower 16 pins as outputs via direction register")

    # Set data register
    driver._driver.data.gpio_pins = 0x0000AAAA
    print("   Set alternating pattern on data register")

    # Read config register if available
    if hasattr(driver._driver, 'config'):
        pin_count = driver._driver.config.pin_count
        version = driver._driver.config.version
        print(f"   Config - Pin count: {pin_count}, Version: 0x{version:02X}")

    # Show register summary
    summary = driver._driver.get_register_summary()
    print("\n   Register Summary:")
    for reg_name, value in summary.items():
        print(f"     {reg_name.upper():20s}: 0x{value:08X}")

    # Demonstrate high-level GPIO API (wrapper over YAML-driven core)
    print("\n2. High-Level GPIO API (YAML backend):")

    # Configure individual pins using high-level API
    driver.configure_pin(0, GpioDirection.OUTPUT, GpioValue.HIGH)
    driver.configure_pin(1, GpioDirection.OUTPUT, GpioValue.LOW)
    driver.configure_pin(2, GpioDirection.INPUT, interrupt_enable=True)

    print("   Configured pins 0 (OUT=1), 1 (OUT=0), 2 (IN+INT)")

    # Read pin states
    for pin in range(3):
        value = driver.get_pin_value(pin)
        direction = driver.get_pin_direction(pin)
        print(f"   Pin {pin}: {value.name} ({direction.name})")

    # Demonstrate bulk operations
    print("\n3. Bulk Operations (YAML backend):")

    # Set multiple pins direction at once (direct register access)
    driver._driver.direction.gpio_dir = 0xFF  # First 8 pins as outputs
    driver.set_pins_value(0xFF, 0x5A)  # Set pattern 01011010

    all_values = driver.get_all_pins_value()
    print(f"   Set pattern 0x5A on first 8 pins, result: 0x{all_values:08X}")

    # Toggle pins (manual implementation)
    current_value = driver.get_all_pins_value()
    toggled_value = current_value ^ 0x0F  # Toggle first 4 pins
    driver.set_pins_value(0x0F, toggled_value & 0x0F)
    all_values = driver.get_all_pins_value()
    print(f"   After toggling first 4 pins: 0x{all_values:08X}")

    print("\n4. Access Control Demonstration:")

    # Try to access read-only fields
    if hasattr(driver._driver, 'config'):
        try:
            pin_count = driver._driver.config.pin_count
            print(f"   ✅ Read pin_count (RO): {pin_count}")
        except Exception as e:
            print(f"   ❌ Failed to read pin_count: {e}")

        try:
            # This should fail if properly implemented as read-only
            driver._driver.config.pin_count = 64
            print("   ❌ Writing to read-only field should have failed!")
        except Exception as e:
            print(f"   ✅ Write to pin_count (RO) blocked: {type(e).__name__}")

    # Test write-only fields
    if hasattr(driver._driver, 'interrupt_clear'):
        try:
            driver._driver.interrupt_clear.int_clear = 0x0F
            print("   ✅ Write to int_clear (WO): Success")
        except Exception as e:
            print(f"   ❌ Failed to write int_clear: {e}")

    print("\nYAML-driven approach benefits:")
    print("• Single source of truth for register definitions")
    print("• Automatic access control enforcement")
    print("• Human-readable memory map documentation")
    print("• Easy maintenance and hardware sync")

    print()


def run_all_examples():
    """Run all GPIO examples."""
    print("GPIO Driver Examples - Unified Architecture Demonstration")
    print("=" * 60)

    basic_gpio_example()
    multi_pin_gpio_example()
    interrupt_gpio_example()
    simulation_example()
    hardware_jtag_example()
    advanced_configuration_example()
    performance_test_example()
    yaml_driven_example()

    print("All examples completed successfully!")
    print("This demonstrates the portability and flexibility of the unified GPIO driver architecture.")
    print("The new YAML-driven approach provides improved maintainability and documentation.")


if __name__ == "__main__":
    run_all_examples()

#!/usr/bin/env python3
"""
YAML-Driven GPIO Driver Demo

This script demonstrates the new YAML-driven GPIO driver architecture
with a practical example that showcases the improved features and capabilities.
"""

import time
import sys
from pathlib import Path

# Import from local modules
from config import (
    create_mock_gpio_driver,
    DriverConfig,
    MockBusConfig,
    create_ip_core_driver
)
from gpio_wrapper import GpioDirection, GpioValue
from memory_map_loader import validate_yaml_memory_map


def print_banner(title):
    """Print a formatted banner for demo sections."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_register_state(driver, title="Register State"):
    """Print the current state of all registers."""
    print(f"\n{title}:")
    summary = driver.get_register_summary()
    for reg_name, value in summary.items():
        print(f"  {reg_name.upper():20s}: 0x{value:08X} (0b{value:032b})")


def demo_yaml_validation():
    """Demonstrate YAML memory map validation."""
    print_banner("YAML Memory Map Validation Demo")

    yaml_file = "gpio_memory_map.yaml"

    print(f"Validating memory map file: {yaml_file}")
    errors = validate_yaml_memory_map(yaml_file)

    if errors:
        print("❌ Validation errors found:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ Memory map validation passed!")
        return True


def demo_yaml_driven_operations():
    """Demonstrate YAML-driven GPIO operations."""
    print_banner("YAML-Driven GPIO Operations Demo")

    # Create a GPIO driver from YAML memory map
    driver = create_mock_gpio_driver("gpio_memory_map.yaml", "YAML Demo Driver")
    print(f"Created GPIO driver: {driver._driver._name}")

    # Get core information
    core_info = driver.get_core_info()
    print(f"Core info: {core_info}")

    print("\n1. Direct Register Access (YAML-defined):")

    # Access registers directly using YAML-defined names
    print("   - Setting data register directly...")
    driver._driver.data.gpio_pins = 0xAAAAAAAA

    print("   - Setting direction register directly...")
    driver._driver.direction.gpio_dir = 0xFFFF0000

    print("   - Reading config register...")
    if hasattr(driver._driver, 'config'):
        pin_count = driver._driver.config.pin_count
        has_interrupts = driver._driver.config.has_interrupts
        version = driver._driver.config.version
        print(f"     Pin count: {pin_count}")
        print(f"     Has interrupts: {bool(has_interrupts)}")
        print(f"     Version: 0x{version:02X}")

    print_register_state(driver._driver, "After Direct Register Access")

    print("\n2. High-Level GPIO API (Wrapper):")

    # Use high-level GPIO API
    driver.configure_pin(0, GpioDirection.OUTPUT, GpioValue.HIGH)
    driver.configure_pin(1, GpioDirection.INPUT, interrupt_enable=True)

    print("   - Configured pin 0 as output HIGH")
    print("   - Configured pin 1 as input with interrupt")

    # Test pin operations
    value = driver.get_pin_value(0)
    direction = driver.get_pin_direction(0)
    print(f"   - Pin 0: {value.name} ({direction.name})")

    print_register_state(driver._driver, "After High-Level API Usage")


def demo_access_control():
    """Demonstrate register field access control."""
    print_banner("Register Field Access Control Demo")

    driver = create_mock_gpio_driver("gpio_memory_map.yaml")

    print("1. Testing Read-Only Fields:")

    # Test read-only fields (config register fields)
    if hasattr(driver._driver, 'config'):
        try:
            # Try to read a read-only field (should work)
            pin_count = driver._driver.config.pin_count
            print(f"   ✅ Reading pin_count (RO): {pin_count}")

            # Try to write to a read-only field (should fail)
            driver._driver.config.pin_count = 64
            print("   ❌ Writing to pin_count (RO): Should have failed!")

        except AttributeError as e:
            print(f"   ✅ Writing to pin_count (RO) correctly blocked: {e}")

    print("\n2. Testing Write-Only Fields:")

    if hasattr(driver._driver, 'interrupt_clear'):
        try:
            # Write to write-only field (should work)
            driver._driver.interrupt_clear.int_clear = 0x0F
            print("   ✅ Writing to int_clear (WO): Success")

            # Try to read from write-only field (should fail)
            value = driver._driver.interrupt_clear.int_clear
            print(f"   ❌ Reading from int_clear (WO): Should have failed! Got {value}")

        except AttributeError as e:
            print(f"   ✅ Reading from int_clear (WO) correctly blocked: {e}")

    print("\n3. Testing Read-Write Fields:")

    # Test read-write fields (normal operation)
    driver._driver.data.gpio_pins = 0x12345678
    value = driver._driver.data.gpio_pins
    print(f"   ✅ Read-write operation on gpio_pins: 0x{value:08X}")


def demo_bit_field_operations():
    """Demonstrate bit field operations."""
    print_banner("Bit Field Operations Demo")

    driver = create_mock_gpio_driver("gpio_memory_map.yaml")

    print("1. Individual Bit Field Access:")

    # Set individual bits
    driver._driver.data.gpio_pins = 0x00000000

    # Test bit field extraction
    print("   Setting specific bit patterns...")
    driver._driver.data.gpio_pins = 0xF0F0F0F0

    # Extract specific bit ranges if defined in YAML
    all_pins = driver._driver.data.gpio_pins
    print(f"   All GPIO pins: 0x{all_pins:08X}")

    print("\n2. Register Read-Modify-Write:")

    # Demonstrate read-modify-write for partial updates
    print("   Original value: 0x{:08X}".format(driver._driver.direction.gpio_dir))

    # Modify just part of the register
    driver._driver.direction.gpio_dir = 0x0000FFFF  # Set lower 16 bits
    print("   After setting lower 16 bits: 0x{:08X}".format(driver._driver.direction.gpio_dir))

    # This should preserve other bits in a real RMW scenario
    print_register_state(driver._driver, "After Bit Field Operations")


def demo_multiple_yaml_drivers():
    """Demonstrate multiple drivers from the same YAML file."""
    print_banner("Multiple YAML-Based Drivers Demo")

    # Create multiple independent drivers
    drivers = {}

    driver_configs = [
        {"name": "GPIO_BANK_A", "driver_name": "GPIO Bank A"},
        {"name": "GPIO_BANK_B", "driver_name": "GPIO Bank B"},
        {"name": "GPIO_BANK_C", "driver_name": "GPIO Bank C"},
    ]

    print("Creating multiple GPIO drivers from the same YAML:")

    for config in driver_configs:
        driver = create_mock_gpio_driver("gpio_memory_map.yaml", config["driver_name"])
        drivers[config["name"]] = driver
        print(f"   - {config['driver_name']}")

    print("\n2. Configuring Each Driver Independently:")

    # Configure each driver differently
    drivers["GPIO_BANK_A"].set_pins_value(0xFFFFFFFF, 0xAAAAAAAA)
    drivers["GPIO_BANK_B"].set_pins_value(0xFFFFFFFF, 0x55555555)
    drivers["GPIO_BANK_C"].set_pins_value(0xFFFFFFFF, 0xF0F0F0F0)

    print("   - GPIO_BANK_A: Set to 0xAAAAAAAA")
    print("   - GPIO_BANK_B: Set to 0x55555555")
    print("   - GPIO_BANK_C: Set to 0xF0F0F0F0")

    print("\n3. Verifying Independence:")

    for name, driver in drivers.items():
        value = driver.get_all_pins_value()
        print(f"   - {name}: 0x{value:08X}")


def demo_error_handling():
    """Demonstrate error handling in YAML-driven system."""
    print_banner("YAML-Driven Error Handling Demo")

    print("1. Invalid YAML File Handling:")

    try:
        # Try to load non-existent YAML file
        driver = create_mock_gpio_driver("nonexistent.yaml")
        print("   ❌ Should have failed to load non-existent file")
    except FileNotFoundError as e:
        print(f"   ✅ Correctly handled missing file: {e}")

    print("\n2. Access Validation:")

    driver = create_mock_gpio_driver("gpio_memory_map.yaml")

    # Test invalid pin access
    try:
        driver.set_pin_value(99, GpioValue.HIGH)  # Pin out of range
        print("   ❌ Should have failed for invalid pin")
    except ValueError as e:
        print(f"   ✅ Correctly blocked invalid pin: {e}")

    # Test invalid register field access
    try:
        # Try to access non-existent field
        value = driver._driver.data.nonexistent_field
        print("   ❌ Should have failed for non-existent field")
    except AttributeError as e:
        print(f"   ✅ Correctly blocked invalid field: {e}")

    print("\n3. Bit Field Value Validation:")

    try:
        # Try to write a value too large for a single-bit field
        if hasattr(driver._driver, 'config'):
            driver._driver.config.enable = 2  # enable is 1-bit field
        print("   ❌ Should have failed for oversized value")
    except ValueError as e:
        print(f"   ✅ Correctly blocked oversized value: {e}")
    except AttributeError:
        print("   ✅ Config register not writable or field not accessible")


def demo_performance_comparison():
    """Compare performance of YAML-driven vs hardcoded approach."""
    print_banner("Performance Comparison Demo")

    driver = create_mock_gpio_driver("gpio_memory_map.yaml")

    print("Comparing YAML-driven vs direct register access performance...")

    # YAML-driven high-level API
    print("\n1. High-Level GPIO API (via wrapper):")
    start_time = time.time()
    iterations = 1000

    for i in range(iterations):
        driver.set_pin_value(0, GpioValue.HIGH if i % 2 else GpioValue.LOW)

    high_level_time = time.time() - start_time
    print(f"   {iterations} high-level pin operations:")
    print(f"   Total time: {high_level_time*1000:.2f} ms")
    print(f"   Time per operation: {high_level_time*1000000/iterations:.2f} μs")

    # Direct register access
    print("\n2. Direct Register Access (YAML-loaded):")
    start_time = time.time()

    for i in range(iterations):
        current = driver._driver.data.gpio_pins
        if i % 2:
            driver._driver.data.gpio_pins = current | 1
        else:
            driver._driver.data.gpio_pins = current & ~1

    direct_time = time.time() - start_time
    print(f"   {iterations} direct register operations:")
    print(f"   Total time: {direct_time*1000:.2f} ms")
    print(f"   Time per operation: {direct_time*1000000/iterations:.2f} μs")

    # Bulk operations
    print("\n3. Bulk Register Operations:")
    start_time = time.time()

    for i in range(iterations):
        pattern = 0xAAAAAAAA if i % 2 else 0x55555555
        driver._driver.data.gpio_pins = pattern

    bulk_time = time.time() - start_time
    print(f"   {iterations} bulk register operations:")
    print(f"   Total time: {bulk_time*1000:.2f} ms")
    print(f"   Time per operation: {bulk_time*1000000/iterations:.2f} μs")

    # Performance analysis
    if direct_time > 0 and bulk_time > 0:
        high_vs_direct = high_level_time / direct_time
        direct_vs_bulk = direct_time / bulk_time
        print(f"\n4. Performance Analysis:")
        print(f"   High-level vs Direct: {high_vs_direct:.1f}x slower")
        print(f"   Direct vs Bulk: {direct_vs_bulk:.1f}x slower")
        print(f"   Bulk operations are most efficient for batch updates")


def main():
    """Main demo function."""
    print("GPIO IP Core Driver - YAML-Driven Architecture Demonstration")
    print("This demo showcases the new YAML-driven memory map approach")

    try:
        # Validate YAML first
        if not demo_yaml_validation():
            print("❌ YAML validation failed, stopping demo")
            return 1

        demo_yaml_driven_operations()
        demo_access_control()
        demo_bit_field_operations()
        demo_multiple_yaml_drivers()
        demo_error_handling()
        demo_performance_comparison()

        print_banner("Demo Complete")
        print("All demonstrations completed successfully!")
        print("\nKey benefits of YAML-driven approach:")
        print("• Single source of truth for memory maps")
        print("• Human-readable register definitions")
        print("• Automatic access control enforcement")
        print("• Dynamic driver generation")
        print("• Easy maintenance and updates")
        print("• Hardware documentation synchronization")
        print("\nThe same YAML file can be used for:")
        print("• Hardware register documentation")
        print("• Driver code generation")
        print("• Simulation model validation")
        print("• Test vector generation")

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

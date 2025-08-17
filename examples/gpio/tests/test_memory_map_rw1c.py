"""
Test module for memory map loader with rw1c access type support.

This module tests the YAML-based memory map loader's ability to handle
rw1c (read-write-1-to-clear) access types in register field definitions.
"""

import os
import pytest
from typing import Dict, Any

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from memory_map_loader import load_from_yaml, validate_yaml_memory_map
from fpga_lib.core import AccessType
from bus_interface import AbstractBusInterface


class MockBusInterface(AbstractBusInterface):
    """Mock bus interface for testing."""

    def __init__(self):
        self.memory: Dict[int, int] = {}

    def read_word(self, address: int) -> int:
        return self.memory.get(address, 0)

    def write_word(self, address: int, data: int) -> None:
        self.memory[address] = data & 0xFFFFFFFF


class TestMemoryMapLoaderRW1C:
    """Test cases for memory map loader with rw1c support."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bus = MockBusInterface()
        self.test_yaml_path = os.path.join(
            os.path.dirname(__file__),
            'resources',
            'test_rw1c_controller.yaml'
        )

    def test_yaml_validation_with_rw1c(self):
        """Test that YAML files with rw1c fields validate correctly."""
        errors = validate_yaml_memory_map(self.test_yaml_path)
        assert errors == [], f"YAML validation failed: {errors}"

    def test_yaml_loading_with_rw1c(self):
        """Test loading YAML file with rw1c fields."""
        driver = load_from_yaml(self.test_yaml_path, self.bus, "Test Driver")

        assert driver._name == "Test Driver"
        registers = driver.get_registers()
        assert 'control' in registers
        assert 'interrupt_status' in registers

    def test_rw1c_field_access_types(self):
        """Test that rw1c fields are created with correct access types."""
        driver = load_from_yaml(self.test_yaml_path, self.bus)
        int_status = driver.interrupt_status

        # Check that fields have the correct access type
        tx_field = int_status._fields['tx_complete']
        rx_field = int_status._fields['rx_complete']
        error_field = int_status._fields['error']

        assert tx_field.access == 'rw1c'
        assert rx_field.access == 'rw1c'
        assert error_field.access == 'rw1c'

    def test_rw1c_functionality_via_yaml(self):
        """Test that rw1c fields loaded from YAML work correctly."""
        driver = load_from_yaml(self.test_yaml_path, self.bus)
        int_status = driver.interrupt_status

        # Simulate hardware setting interrupt flags
        self.bus.write_word(0x04, 0x07)  # Set all three flags

        # Verify initial state
        assert int_status.tx_complete == 1
        assert int_status.rx_complete == 1
        assert int_status.error == 1

        # Clear tx_complete by writing 1 (rw1c behavior)
        int_status.tx_complete = 1

        # Verify only tx_complete was cleared
        assert int_status.tx_complete == 0
        assert int_status.rx_complete == 1
        assert int_status.error == 1

    def test_rw1c_write_zero_no_effect_via_yaml(self):
        """Test that writing 0 to rw1c fields has no effect."""
        driver = load_from_yaml(self.test_yaml_path, self.bus)
        int_status = driver.interrupt_status

        # Set initial state
        self.bus.write_word(0x04, 0x02)  # rx_complete=1

        assert int_status.rx_complete == 1

        # Write 0 (should have no effect)
        int_status.rx_complete = 0

        assert int_status.rx_complete == 1

    def test_mixed_access_types_via_yaml(self):
        """Test that normal rw fields work alongside rw1c fields."""
        driver = load_from_yaml(self.test_yaml_path, self.bus)
        control = driver.control
        int_status = driver.interrupt_status

        # Set initial state
        self.bus.write_word(0x00, 0x01)  # control.enable = 1
        self.bus.write_word(0x04, 0x07)  # all interrupt flags set

        # Verify initial state
        assert control.enable == 1
        assert int_status.tx_complete == 1

        # Modify control field (normal rw behavior)
        control.enable = 0

        # Clear interrupt flag (rw1c behavior)
        int_status.tx_complete = 1

        # Verify both operations worked correctly
        assert control.enable == 0
        assert int_status.tx_complete == 0
        assert int_status.rx_complete == 1  # Unchanged

    def test_access_enum_string_conversion(self):
        """Test that Access enum values are properly converted to strings."""
        driver = load_from_yaml(self.test_yaml_path, self.bus)

        # Test that fields use string access types, not enum values
        int_status = driver.interrupt_status
        control = driver.control

        # These should be strings, not enum values
        assert isinstance(int_status._fields['tx_complete'].access, str)
        assert isinstance(control._fields['enable'].access, str)

        assert int_status._fields['tx_complete'].access == 'rw1c'
        assert control._fields['enable'].access == 'rw'

    def test_yaml_validation_invalid_access_type(self):
        """Test validation rejects invalid access types."""
        # Create a temporary invalid YAML content
        invalid_yaml_content = """
name: "Invalid Controller"
registers:
  - name: test_reg
    offset: 0x00
    fields:
      - name: invalid_field
        bit: 0
        access: invalid_access
        description: "Invalid access type"
"""

        # Write to temporary file
        temp_yaml_path = os.path.join(
            os.path.dirname(__file__),
            'resources',
            'temp_invalid.yaml'
        )

        try:
            with open(temp_yaml_path, 'w') as f:
                f.write(invalid_yaml_content)

            errors = validate_yaml_memory_map(temp_yaml_path)
            assert len(errors) > 0
            assert any('Invalid access type' in error for error in errors)

        finally:
            # Clean up temporary file
            if os.path.exists(temp_yaml_path):
                os.remove(temp_yaml_path)


def test_memory_map_rw1c_standalone():
    """Standalone test function for manual execution."""
    test_case = TestMemoryMapLoaderRW1C()
    test_case.setup_method()

    print("Testing YAML memory map loader with rw1c access type...")

    # Validate YAML
    errors = validate_yaml_memory_map(test_case.test_yaml_path)
    if errors:
        print("YAML validation errors:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("YAML validation passed!")

    # Load driver
    driver = load_from_yaml(test_case.test_yaml_path, test_case.bus, "Test Driver")
    print(f"Loaded driver: {driver._name}")
    print(f"Registers: {list(driver.get_registers().keys())}")

    # Test rw1c functionality
    int_status = driver.interrupt_status
    test_case.bus.write_word(0x04, 0x07)  # Set all flags

    print(f"\nInterrupt status register value: 0x{int_status.read():08X}")
    print(f"tx_complete: {int_status.tx_complete}")
    print(f"rx_complete: {int_status.rx_complete}")
    print(f"error: {int_status.error}")

    # Clear tx_complete
    int_status.tx_complete = 1

    print(f"\nAfter clearing tx_complete: 0x{int_status.read():08X}")
    print(f"tx_complete: {int_status.tx_complete} (should be 0)")
    print(f"rx_complete: {int_status.rx_complete} (should still be 1)")
    print(f"error: {int_status.error} (should still be 1)")

    print("\nYAML rw1c test passed!")
    return True


if __name__ == "__main__":
    test_memory_map_rw1c_standalone()

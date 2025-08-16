"""
Test Suite for GPIO Driver

This module provides comprehensive tests for the GPIO driver implementation,
demonstrating test-driven development and validation of the unified architecture.
"""

import pytest
from unittest.mock import Mock, patch
from .gpio_driver import GpioDriver, GpioDirection, GpioValue, BitField, Register
from .bus_interface import MockBusInterface
from .config import (
    create_mock_gpio_driver,
    create_gpio_driver,
    GpioDriverConfig,
    MockBusConfig,
    SimulationBusConfig,
    JtagBusConfig
)


class TestBitField:
    """Test cases for BitField dataclass."""

    def test_bitfield_creation(self):
        """Test BitField creation with default values."""
        field = BitField("test_field", 0, 8)
        assert field.name == "test_field"
        assert field.offset == 0
        assert field.width == 8
        assert field.access == "rw"
        assert field.description == ""

    def test_bitfield_with_custom_values(self):
        """Test BitField creation with custom values."""
        field = BitField("status", 16, 4, "r", "Status bits")
        assert field.name == "status"
        assert field.offset == 16
        assert field.width == 4
        assert field.access == "r"
        assert field.description == "Status bits"


class TestRegister:
    """Test cases for Register class."""

    def setup_method(self):
        """Setup for each test method."""
        self.bus = MockBusInterface()
        self.fields = [
            BitField("data", 0, 8, "rw"),
            BitField("enable", 8, 1, "rw"),
            BitField("status", 16, 4, "r")
        ]
        self.register = Register("TEST_REG", 0x100, self.bus, self.fields)

    def test_register_creation(self):
        """Test register creation."""
        assert self.register.name == "TEST_REG"
        assert self.register.offset == 0x100
        assert len(self.register._fields) == 3

    def test_register_read_write(self):
        """Test basic register read/write operations."""
        # Write a value
        self.register.write(0x12345678)

        # Read it back
        value = self.register.read()
        assert value == 0x12345678

    def test_field_read_write(self):
        """Test bit field operations."""
        # Write initial value
        self.register.write(0x00000000)

        # Write to data field (bits 0-7)
        self.register.write_field("data", 0xAB)
        assert self.register.read() == 0x000000AB

        # Write to enable field (bit 8)
        self.register.write_field("enable", 1)
        assert self.register.read() == 0x000001AB

        # Read back individual fields
        assert self.register.read_field("data") == 0xAB
        assert self.register.read_field("enable") == 1

    def test_field_validation(self):
        """Test field validation."""
        # Test invalid field name
        with pytest.raises(ValueError, match="Unknown field"):
            self.register.read_field("invalid_field")

        # Test value too large for field
        with pytest.raises(ValueError, match="exceeds field width"):
            self.register.write_field("enable", 2)  # enable is 1-bit wide

        # Test read-only field write
        with pytest.raises(ValueError, match="read-only"):
            self.register.write_field("status", 1)

    def test_get_fields(self):
        """Test getting list of available fields."""
        fields = self.register.get_fields()
        assert set(fields) == {"data", "enable", "status"}


class TestGpioDriver:
    """Test cases for GpioDriver class."""

    def setup_method(self):
        """Setup for each test method."""
        self.driver = create_mock_gpio_driver(num_pins=8)

    def test_gpio_driver_creation(self):
        """Test GPIO driver creation."""
        assert self.driver.num_pins == 8
        assert isinstance(self.driver._bus, MockBusInterface)

    def test_pin_direction_operations(self):
        """Test pin direction configuration."""
        # Set pin 0 as output
        self.driver.set_pin_direction(0, GpioDirection.OUTPUT)
        assert self.driver.get_pin_direction(0) == GpioDirection.OUTPUT

        # Set pin 1 as input
        self.driver.set_pin_direction(1, GpioDirection.INPUT)
        assert self.driver.get_pin_direction(1) == GpioDirection.INPUT

    def test_pin_value_operations(self):
        """Test pin value operations."""
        # Configure pin as output first
        self.driver.set_pin_direction(0, GpioDirection.OUTPUT)

        # Set pin high
        self.driver.set_pin_value(0, GpioValue.HIGH)
        assert self.driver.get_pin_value(0) == GpioValue.HIGH

        # Set pin low
        self.driver.set_pin_value(0, GpioValue.LOW)
        assert self.driver.get_pin_value(0) == GpioValue.LOW

    def test_multi_pin_operations(self):
        """Test multi-pin operations."""
        # Set pins 0-3 as outputs
        for pin in range(4):
            self.driver.set_pin_direction(pin, GpioDirection.OUTPUT)

        # Set pattern on pins 0-3
        pattern = 0b1010
        self.driver.set_pins_value(0x0F, pattern)

        # Verify the pattern
        all_values = self.driver.get_all_pins_value()
        assert (all_values & 0x0F) == pattern

    def test_interrupt_operations(self):
        """Test interrupt-related operations."""
        # Enable interrupt for pin 0
        self.driver.enable_pin_interrupt(0, True)

        # Check that interrupt is enabled (this would need to read the register)
        # For now, we just verify the operation doesn't raise an exception

        # Disable interrupt
        self.driver.enable_pin_interrupt(0, False)

    def test_pin_configuration(self):
        """Test comprehensive pin configuration."""
        self.driver.configure_pin(
            pin=0,
            direction=GpioDirection.OUTPUT,
            initial_value=GpioValue.HIGH,
            interrupt_enable=True
        )

        # Verify configuration
        assert self.driver.get_pin_direction(0) == GpioDirection.OUTPUT
        assert self.driver.get_pin_value(0) == GpioValue.HIGH

    def test_pin_validation(self):
        """Test pin number validation."""
        # Test invalid pin numbers
        with pytest.raises(ValueError, match="out of range"):
            self.driver.set_pin_direction(8, GpioDirection.OUTPUT)  # 8 pins: 0-7

        with pytest.raises(ValueError, match="out of range"):
            self.driver.get_pin_value(-1)

    def test_register_summary(self):
        """Test register summary functionality."""
        summary = self.driver.get_register_summary()

        # Check that all expected registers are present
        expected_registers = ["data", "direction", "interrupt_enable", "interrupt_status"]
        for reg in expected_registers:
            assert reg in summary
            assert isinstance(summary[reg], int)


class TestDriverFactory:
    """Test cases for driver factory functions."""

    def test_mock_driver_creation(self):
        """Test mock driver creation."""
        driver = create_mock_gpio_driver(num_pins=16, base_address=0x1000)
        assert driver.num_pins == 16
        assert isinstance(driver._bus, MockBusInterface)

    def test_gpio_driver_config_creation(self):
        """Test GPIO driver creation with config."""
        config = GpioDriverConfig(
            bus_type="mock",
            bus_config=MockBusConfig(),
            num_pins=32,
            base_address=0x40000000
        )

        driver = create_gpio_driver(config)
        assert driver.num_pins == 32
        assert isinstance(driver._bus, MockBusInterface)

    def test_invalid_bus_type(self):
        """Test invalid bus type handling."""
        from .config import create_bus_interface

        with pytest.raises(ValueError, match="Unsupported bus_type"):
            create_bus_interface("invalid_type", MockBusConfig())

    def test_config_type_mismatch(self):
        """Test configuration type mismatch."""
        from .config import create_bus_interface

        # Try to use wrong config type for bus type
        with pytest.raises(TypeError, match="Expected MockBusConfig"):
            create_bus_interface("mock", SimulationBusConfig(None, "test", None))


class TestBusInterface:
    """Test cases for bus interface implementations."""

    def test_mock_bus_interface(self):
        """Test mock bus interface."""
        bus = MockBusInterface()

        # Test write and read
        bus.write_word(0x100, 0x12345678)
        value = bus.read_word(0x100)
        assert value == 0x12345678

        # Test uninitialized read returns 0
        value = bus.read_word(0x200)
        assert value == 0

        # Test memory dump
        memory = bus.dump_memory()
        assert 0x100 in memory
        assert memory[0x100] == 0x12345678

    def test_mock_bus_word_masking(self):
        """Test that mock bus properly masks 32-bit values."""
        bus = MockBusInterface()

        # Write a value larger than 32 bits
        large_value = 0x123456789ABCDEF0
        bus.write_word(0x100, large_value)

        # Should be masked to 32 bits
        value = bus.read_word(0x100)
        assert value == (large_value & 0xFFFFFFFF)


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_complete_gpio_workflow(self):
        """Test a complete GPIO workflow."""
        # Create driver
        driver = create_mock_gpio_driver(num_pins=8)

        # Configure pins
        driver.configure_pin(0, GpioDirection.OUTPUT, GpioValue.LOW)
        driver.configure_pin(1, GpioDirection.INPUT, interrupt_enable=True)

        # Test output pin
        driver.set_pin_value(0, GpioValue.HIGH)
        assert driver.get_pin_value(0) == GpioValue.HIGH

        # Test bulk operations
        driver.set_pins_value(0xFF, 0xAA)  # Set alternating pattern
        all_values = driver.get_all_pins_value()
        assert (all_values & 0xFF) == 0xAA

        # Verify register state
        summary = driver.get_register_summary()
        assert summary["data"] == 0xAA

    def test_multiple_drivers(self):
        """Test multiple GPIO drivers with different configurations."""
        # Create multiple drivers
        driver_a = create_mock_gpio_driver(num_pins=8, base_address=0x1000)
        driver_b = create_mock_gpio_driver(num_pins=16, base_address=0x2000)

        # Configure differently
        driver_a.set_pin_value(0, GpioValue.HIGH)
        driver_b.set_pin_value(0, GpioValue.LOW)

        # Verify independence
        assert driver_a.get_pin_value(0) == GpioValue.HIGH
        assert driver_b.get_pin_value(0) == GpioValue.LOW
        assert driver_a.num_pins == 8
        assert driver_b.num_pins == 16


class TestErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Setup for each test method."""
        self.driver = create_mock_gpio_driver(num_pins=4)

    def test_boundary_conditions(self):
        """Test boundary conditions."""
        # Test maximum pin number
        self.driver.set_pin_direction(3, GpioDirection.OUTPUT)  # Should work

        # Test out of bounds
        with pytest.raises(ValueError):
            self.driver.set_pin_direction(4, GpioDirection.OUTPUT)

    def test_register_field_edge_cases(self):
        """Test register field edge cases."""
        # Test maximum field values
        # The GPIO data field should accept values up to 2^num_pins - 1
        max_value = (1 << self.driver.num_pins) - 1
        self.driver.data_reg.write_field("gpio_data", max_value)
        assert self.driver.data_reg.read_field("gpio_data") == max_value


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

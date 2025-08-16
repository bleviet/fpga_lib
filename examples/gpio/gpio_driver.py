"""
GPIO IP Core Driver - Layer 1

This module implements the high-level GPIO IP core driver that provides
an intuitive API for controlling GPIO pins and registers.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from bus_interface import AbstractBusInterface


class GpioDirection(Enum):
    """GPIO pin direction enumeration."""
    INPUT = 0
    OUTPUT = 1


class GpioValue(Enum):
    """GPIO pin value enumeration."""
    LOW = 0
    HIGH = 1


@dataclass
class BitField:
    """
    Represents a bit field within a register.

    Attributes:
        name: Human-readable name of the bit field
        offset: Bit position within the register (0-based)
        width: Number of bits in the field
        access: Access type ('r', 'w', 'rw')
        description: Optional description of the bit field
    """
    name: str
    offset: int
    width: int
    access: str = 'rw'
    description: str = ''


class Register:
    """
    Represents a hardware register with bit fields.

    This class handles bit-wise operations for reading and writing
    individual bit fields within a register.
    """

    def __init__(self, name: str, offset: int, bus: AbstractBusInterface,
                 fields: List[BitField], description: str = ''):
        self.name = name
        self.offset = offset
        self.description = description
        self._bus = bus
        self._fields = {field.name: field for field in fields}

    def read(self) -> int:
        """Read the entire register value."""
        return self._bus.read_word(self.offset)

    def write(self, value: int) -> None:
        """Write the entire register value."""
        self._bus.write_word(self.offset, value)

    def read_field(self, field_name: str) -> int:
        """
        Read a specific bit field from the register.

        Args:
            field_name: Name of the bit field to read

        Returns:
            The value of the bit field
        """
        if field_name not in self._fields:
            raise ValueError(f"Unknown field: {field_name}")

        field = self._fields[field_name]
        reg_value = self.read()
        mask = (1 << field.width) - 1
        return (reg_value >> field.offset) & mask

    def write_field(self, field_name: str, value: int) -> None:
        """
        Write a specific bit field in the register.

        Args:
            field_name: Name of the bit field to write
            value: Value to write to the bit field
        """
        if field_name not in self._fields:
            raise ValueError(f"Unknown field: {field_name}")

        field = self._fields[field_name]
        if field.access == 'r':
            raise ValueError(f"Field {field_name} is read-only")

        # Validate value fits in field width
        max_value = (1 << field.width) - 1
        if value > max_value:
            raise ValueError(f"Value {value} exceeds field width {field.width}")

        # Read current register value
        reg_value = self.read()

        # Clear the field bits
        mask = ((1 << field.width) - 1) << field.offset
        reg_value &= ~mask

        # Set the new field value
        reg_value |= (value << field.offset)

        # Write back to register
        self.write(reg_value)

    def get_fields(self) -> List[str]:
        """Get list of available field names."""
        return list(self._fields.keys())


class GpioDriver:
    """
    High-level GPIO IP Core Driver.

    This driver provides an intuitive API for controlling a configurable
    GPIO IP core. It abstracts away the register-level details and provides
    pin-oriented operations.
    """

    # Register offsets (byte addresses)
    DATA_REG_OFFSET = 0x00
    DIRECTION_REG_OFFSET = 0x04
    INTERRUPT_ENABLE_REG_OFFSET = 0x08
    INTERRUPT_STATUS_REG_OFFSET = 0x0C

    def __init__(self, bus: AbstractBusInterface, num_pins: int = 32, base_address: int = 0):
        """
        Initialize the GPIO driver.

        Args:
            bus: Bus interface for hardware communication
            num_pins: Number of GPIO pins supported by the IP core
            base_address: Base address of the GPIO IP core registers
        """
        self._bus = bus
        self._num_pins = num_pins
        self._base_address = base_address

        # Define bit fields for each register
        data_fields = [
            BitField("gpio_data", 0, num_pins, "rw", "GPIO pin data values")
        ]

        direction_fields = [
            BitField("gpio_dir", 0, num_pins, "rw", "GPIO pin directions (0=input, 1=output)")
        ]

        interrupt_enable_fields = [
            BitField("int_enable", 0, num_pins, "rw", "Interrupt enable for each pin")
        ]

        interrupt_status_fields = [
            BitField("int_status", 0, num_pins, "r", "Interrupt status for each pin")
        ]

        # Create register objects
        self.data_reg = Register(
            "DATA", base_address + self.DATA_REG_OFFSET, bus, data_fields,
            "GPIO data register - controls output values and reads input values"
        )

        self.direction_reg = Register(
            "DIRECTION", base_address + self.DIRECTION_REG_OFFSET, bus, direction_fields,
            "GPIO direction register - configures pins as input (0) or output (1)"
        )

        self.interrupt_enable_reg = Register(
            "INTERRUPT_ENABLE", base_address + self.INTERRUPT_ENABLE_REG_OFFSET, bus, interrupt_enable_fields,
            "Interrupt enable register - enables interrupts for each pin"
        )

        self.interrupt_status_reg = Register(
            "INTERRUPT_STATUS", base_address + self.INTERRUPT_STATUS_REG_OFFSET, bus, interrupt_status_fields,
            "Interrupt status register - shows pending interrupts for each pin"
        )

    def set_pin_direction(self, pin: int, direction: GpioDirection) -> None:
        """
        Set the direction of a specific GPIO pin.

        Args:
            pin: Pin number (0-based)
            direction: Direction (INPUT or OUTPUT)
        """
        self._validate_pin(pin)

        current_directions = self.direction_reg.read_field("gpio_dir")
        if direction == GpioDirection.OUTPUT:
            new_directions = current_directions | (1 << pin)
        else:
            new_directions = current_directions & ~(1 << pin)

        self.direction_reg.write_field("gpio_dir", new_directions)

    def get_pin_direction(self, pin: int) -> GpioDirection:
        """
        Get the direction of a specific GPIO pin.

        Args:
            pin: Pin number (0-based)

        Returns:
            Current direction of the pin
        """
        self._validate_pin(pin)

        directions = self.direction_reg.read_field("gpio_dir")
        is_output = (directions >> pin) & 1
        return GpioDirection.OUTPUT if is_output else GpioDirection.INPUT

    def set_pin_value(self, pin: int, value: GpioValue) -> None:
        """
        Set the output value of a specific GPIO pin.

        Args:
            pin: Pin number (0-based)
            value: Value to set (LOW or HIGH)
        """
        self._validate_pin(pin)

        current_data = self.data_reg.read_field("gpio_data")
        if value == GpioValue.HIGH:
            new_data = current_data | (1 << pin)
        else:
            new_data = current_data & ~(1 << pin)

        self.data_reg.write_field("gpio_data", new_data)

    def get_pin_value(self, pin: int) -> GpioValue:
        """
        Get the current value of a specific GPIO pin.

        Args:
            pin: Pin number (0-based)

        Returns:
            Current value of the pin
        """
        self._validate_pin(pin)

        data = self.data_reg.read_field("gpio_data")
        is_high = (data >> pin) & 1
        return GpioValue.HIGH if is_high else GpioValue.LOW

    def set_pins_value(self, pin_mask: int, value: int) -> None:
        """
        Set multiple GPIO pins simultaneously.

        Args:
            pin_mask: Bit mask indicating which pins to modify
            value: New values for the masked pins
        """
        current_data = self.data_reg.read_field("gpio_data")

        # Clear the bits for pins in the mask
        new_data = current_data & ~pin_mask

        # Set the new values for pins in the mask
        new_data |= value & pin_mask

        self.data_reg.write_field("gpio_data", new_data)

    def get_all_pins_value(self) -> int:
        """
        Get the values of all GPIO pins.

        Returns:
            Bit vector representing all pin values
        """
        return self.data_reg.read_field("gpio_data")

    def enable_pin_interrupt(self, pin: int, enable: bool = True) -> None:
        """
        Enable or disable interrupt for a specific GPIO pin.

        Args:
            pin: Pin number (0-based)
            enable: True to enable interrupt, False to disable
        """
        self._validate_pin(pin)

        current_enables = self.interrupt_enable_reg.read_field("int_enable")
        if enable:
            new_enables = current_enables | (1 << pin)
        else:
            new_enables = current_enables & ~(1 << pin)

        self.interrupt_enable_reg.write_field("int_enable", new_enables)

    def get_interrupt_status(self) -> int:
        """
        Get the interrupt status for all pins.

        Returns:
            Bit vector representing interrupt status for all pins
        """
        return self.interrupt_status_reg.read_field("int_status")

    def clear_interrupt_status(self, pin_mask: int) -> None:
        """
        Clear interrupt status for specified pins.

        Args:
            pin_mask: Bit mask indicating which interrupt flags to clear
        """
        # Note: This assumes write-1-to-clear behavior for interrupt status
        # In a real implementation, this might be a separate register
        current_status = self.interrupt_status_reg.read()
        self.interrupt_status_reg.write(current_status & ~pin_mask)

    def configure_pin(self, pin: int, direction: GpioDirection,
                     initial_value: Optional[GpioValue] = None,
                     interrupt_enable: bool = False) -> None:
        """
        Configure a GPIO pin with direction, initial value, and interrupt setting.

        Args:
            pin: Pin number (0-based)
            direction: Pin direction (INPUT or OUTPUT)
            initial_value: Initial value for output pins (optional)
            interrupt_enable: Whether to enable interrupts for this pin
        """
        self.set_pin_direction(pin, direction)

        if direction == GpioDirection.OUTPUT and initial_value is not None:
            self.set_pin_value(pin, initial_value)

        self.enable_pin_interrupt(pin, interrupt_enable)

    def _validate_pin(self, pin: int) -> None:
        """Validate that the pin number is within the valid range."""
        if not (0 <= pin < self._num_pins):
            raise ValueError(f"Pin {pin} is out of range (0-{self._num_pins-1})")

    @property
    def num_pins(self) -> int:
        """Get the number of GPIO pins supported by this instance."""
        return self._num_pins

    def get_register_summary(self) -> dict:
        """
        Get a summary of all register values for debugging.

        Returns:
            Dictionary with current register values
        """
        return {
            "data": self.data_reg.read(),
            "direction": self.direction_reg.read(),
            "interrupt_enable": self.interrupt_enable_reg.read(),
            "interrupt_status": self.interrupt_status_reg.read()
        }

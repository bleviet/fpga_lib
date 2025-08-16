"""
GPIO Driver Wrapper

This module provides a high-level GPIO wrapper that uses the new YAML-based
memory map system underneath while maintaining a familiar GPIO-specific API.
"""

from enum import Enum
from typing import Optional
from memory_map_loader import IpCoreDriver


class GpioDirection(Enum):
    """GPIO pin direction enumeration."""
    INPUT = 0
    OUTPUT = 1


class GpioValue(Enum):
    """GPIO pin value enumeration."""
    LOW = 0
    HIGH = 1


class GpioDriverWrapper:
    """
    High-level GPIO wrapper around the YAML-based IP core driver.
    
    This class provides a familiar GPIO-specific API while using the
    new unified architecture underneath.
    """
    
    def __init__(self, ip_core_driver: IpCoreDriver):
        """
        Initialize the GPIO wrapper.
        
        Args:
            ip_core_driver: The underlying IP core driver loaded from YAML
        """
        self._driver = ip_core_driver
        
        # Validate that this is actually a GPIO driver
        required_registers = ['data', 'direction']
        for reg_name in required_registers:
            if not hasattr(self._driver, reg_name):
                raise ValueError(f"Missing required GPIO register: {reg_name}")
        
        # Get number of pins from config register if available
        self._num_pins = 32  # Default
        if hasattr(self._driver, 'config'):
            try:
                self._num_pins = self._driver.config.pin_count
            except AttributeError:
                pass  # Use default if field not available
    
    @property
    def num_pins(self) -> int:
        """Get the number of GPIO pins supported by this instance."""
        return self._num_pins
    
    def set_pin_direction(self, pin: int, direction: GpioDirection) -> None:
        """
        Set the direction of a specific GPIO pin.
        
        Args:
            pin: Pin number (0-based)
            direction: Direction (INPUT or OUTPUT)
        """
        self._validate_pin(pin)
        
        current_directions = self._driver.direction.gpio_dir
        if direction == GpioDirection.OUTPUT:
            new_directions = current_directions | (1 << pin)
        else:
            new_directions = current_directions & ~(1 << pin)
        
        self._driver.direction.gpio_dir = new_directions
    
    def get_pin_direction(self, pin: int) -> GpioDirection:
        """
        Get the direction of a specific GPIO pin.
        
        Args:
            pin: Pin number (0-based)
            
        Returns:
            Current direction of the pin
        """
        self._validate_pin(pin)
        
        directions = self._driver.direction.gpio_dir
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
        
        current_data = self._driver.data.gpio_pins
        if value == GpioValue.HIGH:
            new_data = current_data | (1 << pin)
        else:
            new_data = current_data & ~(1 << pin)
        
        self._driver.data.gpio_pins = new_data
    
    def get_pin_value(self, pin: int) -> GpioValue:
        """
        Get the current value of a specific GPIO pin.
        
        Args:
            pin: Pin number (0-based)
            
        Returns:
            Current value of the pin
        """
        self._validate_pin(pin)
        
        data = self._driver.data.gpio_pins
        is_high = (data >> pin) & 1
        return GpioValue.HIGH if is_high else GpioValue.LOW
    
    def set_pins_value(self, pin_mask: int, value: int) -> None:
        """
        Set multiple GPIO pins simultaneously.
        
        Args:
            pin_mask: Bit mask indicating which pins to modify
            value: New values for the masked pins
        """
        current_data = self._driver.data.gpio_pins
        
        # Clear the bits for pins in the mask
        new_data = current_data & ~pin_mask
        
        # Set the new values for pins in the mask
        new_data |= value & pin_mask
        
        self._driver.data.gpio_pins = new_data
    
    def get_all_pins_value(self) -> int:
        """
        Get the values of all GPIO pins.
        
        Returns:
            Bit vector representing all pin values
        """
        return self._driver.data.gpio_pins
    
    def enable_pin_interrupt(self, pin: int, enable: bool = True) -> None:
        """
        Enable or disable interrupt for a specific GPIO pin.
        
        Args:
            pin: Pin number (0-based)
            enable: True to enable interrupt, False to disable
        """
        self._validate_pin(pin)
        
        if not hasattr(self._driver, 'interrupt_enable'):
            raise AttributeError("This GPIO driver does not support interrupts")
        
        current_enables = self._driver.interrupt_enable.int_enable
        if enable:
            new_enables = current_enables | (1 << pin)
        else:
            new_enables = current_enables & ~(1 << pin)
        
        self._driver.interrupt_enable.int_enable = new_enables
    
    def get_interrupt_status(self) -> int:
        """
        Get the interrupt status for all pins.
        
        Returns:
            Bit vector representing interrupt status for all pins
        """
        if not hasattr(self._driver, 'interrupt_status'):
            raise AttributeError("This GPIO driver does not support interrupts")
        
        return self._driver.interrupt_status.int_status
    
    def clear_interrupt_status(self, pin_mask: int) -> None:
        """
        Clear interrupt status for specified pins.
        
        Args:
            pin_mask: Bit mask indicating which interrupt flags to clear
        """
        if not hasattr(self._driver, 'interrupt_clear'):
            raise AttributeError("This GPIO driver does not support interrupt clearing")
        
        # Write to interrupt clear register (write-only, self-clearing)
        self._driver.interrupt_clear.int_clear = pin_mask
    
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
        
        if hasattr(self._driver, 'interrupt_enable'):
            self.enable_pin_interrupt(pin, interrupt_enable)
    
    def _validate_pin(self, pin: int) -> None:
        """Validate that the pin number is within the valid range."""
        if not (0 <= pin < self._num_pins):
            raise ValueError(f"Pin {pin} is out of range (0-{self._num_pins-1})")
    
    def get_register_summary(self) -> dict:
        """
        Get a summary of all register values for debugging.
        
        Returns:
            Dictionary with current register values
        """
        return self._driver.get_register_summary()
    
    def enable_core(self, enable: bool = True) -> None:
        """
        Enable or disable the GPIO core globally.
        
        Args:
            enable: True to enable the core, False to disable
        """
        if hasattr(self._driver, 'config') and hasattr(self._driver.config, 'enable'):
            self._driver.config.enable = 1 if enable else 0
        else:
            # Core might be always enabled
            pass
    
    def get_core_info(self) -> dict:
        """
        Get information about the GPIO core.
        
        Returns:
            Dictionary with core information
        """
        info = {
            'num_pins': self._num_pins,
            'has_interrupts': hasattr(self._driver, 'interrupt_enable'),
            'has_interrupt_clear': hasattr(self._driver, 'interrupt_clear'),
            'has_config': hasattr(self._driver, 'config')
        }
        
        if hasattr(self._driver, 'config'):
            try:
                if hasattr(self._driver.config, 'version'):
                    info['version'] = self._driver.config.version
                if hasattr(self._driver.config, 'has_interrupts'):
                    info['hw_interrupts'] = bool(self._driver.config.has_interrupts)
            except AttributeError:
                pass
        
        return info

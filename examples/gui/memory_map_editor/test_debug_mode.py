#!/usr/bin/env python3
"""Test script for the debug mode functionality of the bit field visualizer."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer

from debug_mode import debug_manager, DebugValue
from gui.bit_field_visualizer import BitFieldVisualizer
from fpga_lib.core.register import BitField, AccessType


class MockRegister:
    """Mock register class for testing the visualizer."""
    def __init__(self, name):
        self.name = name
        self._fields = {}

    def add_field(self, field):
        """Add a field to the register."""
        self._fields[field.name] = field


class DebugModeTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Debug Mode Test - Bit Field Visualizer")
        self.setGeometry(100, 100, 1200, 600)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Create control buttons
        button_layout = QHBoxLayout()

        self.toggle_debug_btn = QPushButton("Enable Debug Mode")
        self.toggle_debug_btn.clicked.connect(self.toggle_debug_mode)
        button_layout.addWidget(self.toggle_debug_btn)

        self.load_debug_data_btn = QPushButton("Load Test Debug Data")
        self.load_debug_data_btn.clicked.connect(self.load_test_debug_data)
        button_layout.addWidget(self.load_debug_data_btn)

        self.simulate_changes_btn = QPushButton("Simulate Value Changes")
        self.simulate_changes_btn.clicked.connect(self.simulate_value_changes)
        button_layout.addWidget(self.simulate_changes_btn)

        layout.addLayout(button_layout)

        # Create bit field visualizer
        self.visualizer = BitFieldVisualizer()
        self.visualizer.setMinimumSize(800, 400)  # Set minimum size
        layout.addWidget(self.visualizer)

        # Create a test register with multiple fields
        self.create_test_register()

        # Set up a timer for periodic updates (simulating live hardware)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_debug_values)
        self.value_counter = 0

    def create_test_register(self):
        """Create a test register with multiple bit fields for demonstration."""
        register = MockRegister("GPIO_CONTROL")

        # Create various bit fields with different sizes and reset values
        register.add_field(BitField("ENABLE", 0, 1, AccessType.RW, reset_value=0x0, description="Enable GPIO"))
        register.add_field(BitField("MODE", 1, 2, AccessType.RW, reset_value=0x1, description="Operating Mode"))
        register.add_field(BitField("INTERRUPT_EN", 3, 1, AccessType.RW, reset_value=0x0, description="Interrupt Enable"))
        register.add_field(BitField("DATA", 4, 8, AccessType.RW, reset_value=0x55, description="Data Bits"))
        register.add_field(BitField("STATUS", 12, 4, AccessType.RO, reset_value=0x0, description="Status Flags"))
        register.add_field(BitField("CONFIG", 16, 8, AccessType.RW, reset_value=0xAA, description="Configuration"))
        register.add_field(BitField("RESERVED", 24, 6, AccessType.RO, reset_value=0x0, description="Reserved"))
        register.add_field(BitField("VERSION", 30, 2, AccessType.RO, reset_value=0x1, description="Version"))
        # Use provided API so internal setup (colors, sizing) occurs
        self.visualizer.set_register(register)

        self.test_register = register

        # Force the visualizer to update
        self.visualizer.update()

    def toggle_debug_mode(self):
        """Toggle debug mode in the visualizer."""
        current_mode = self.visualizer.debug_mode_enabled
        self.visualizer.set_debug_mode(not current_mode)
        self.visualizer.updateGeometry()

        if current_mode:
            self.toggle_debug_btn.setText("Enable Debug Mode")
            self.update_timer.stop()
            debug_manager.disable_debug_mode()
        else:
            self.toggle_debug_btn.setText("Disable Debug Mode")
            debug_manager.enable_debug_mode()
            self.load_test_debug_data()  # Load initial debug data
            self.update_timer.start(2000)  # Update every 2 seconds

    def load_test_debug_data(self):
        """Load test debug data to demonstrate the debug comparison."""
        if not debug_manager.debug_mode_enabled:
            debug_manager.enable_debug_mode()

        # Create a debug set with some test values
        debug_set = debug_manager.create_debug_set("Test Hardware Values")

        # Add register value that differs from reset values in some fields
        # Reset: ENABLE=0, MODE=1, INTERRUPT_EN=0, DATA=0x55, STATUS=0, CONFIG=0xAA, RESERVED=0, VERSION=1
        # Live:  ENABLE=1, MODE=2, INTERRUPT_EN=1, DATA=0xAA, STATUS=5, CONFIG=0x55, RESERVED=0, VERSION=1
        live_value = (
            (0x1 << 0) |   # ENABLE = 1 (different from reset)
            (0x2 << 1) |   # MODE = 2 (different from reset)
            (0x1 << 3) |   # INTERRUPT_EN = 1 (different from reset)
            (0xAA << 4) |  # DATA = 0xAA (different from reset)
            (0x5 << 12) |  # STATUS = 5 (different from reset)
            (0x55 << 16) | # CONFIG = 0x55 (different from reset)
            (0x0 << 24) |  # RESERVED = 0 (same as reset)
            (0x1 << 30)    # VERSION = 1 (same as reset)
        )

        debug_set.set_register_value("GPIO_CONTROL", DebugValue.from_string(f"0x{live_value:08X}"))
        debug_manager.set_current_debug_set("Test Hardware Values")

        print(f"Loaded debug data: GPIO_CONTROL = 0x{live_value:08X}")
        self.visualizer.update()

    def simulate_value_changes(self):
        """Simulate changing hardware values to demonstrate real-time updates."""
        if not self.update_timer.isActive():
            self.update_timer.start(1000)  # Update every second
        else:
            self.update_timer.stop()
            self.simulate_changes_btn.setText("Simulate Value Changes")

    def update_debug_values(self):
        """Update debug values to simulate changing hardware."""
        if not debug_manager.debug_mode_enabled:
            return

        current_set = debug_manager.get_current_debug_set()
        if not current_set:
            return

        # Simulate changing values
        self.value_counter += 1

        # Create varying bit patterns
        enable_bit = self.value_counter % 2
        mode_bits = (self.value_counter % 4)
        data_bits = (0x55 + self.value_counter) & 0xFF
        status_bits = (self.value_counter % 16)
        config_bits = (0xAA - self.value_counter) & 0xFF

        live_value = (
            (enable_bit << 0) |
            (mode_bits << 1) |
            (0x1 << 3) |       # INTERRUPT_EN stays 1
            (data_bits << 4) |
            (status_bits << 12) |
            (config_bits << 16) |
            (0x0 << 24) |      # RESERVED stays 0
            (0x1 << 30)        # VERSION stays 1
        )

        current_set.set_register_value("GPIO_CONTROL", DebugValue.from_string(f"0x{live_value:08X}"))
        self.visualizer.update()

        self.simulate_changes_btn.setText(f"Stop Simulation (Counter: {self.value_counter})")


def main():
    app = QApplication(sys.argv)

    # Create and show the test window
    window = DebugModeTestWindow()
    window.show()

    print("Debug Mode Test Application Started")
    print("Instructions:")
    print("1. Click 'Enable Debug Mode' to switch to two-row visualization")
    print("2. Click 'Load Test Debug Data' to see differences highlighted")
    print("3. Click 'Simulate Value Changes' to see real-time updates")
    print("4. Yellow highlighting indicates differences between reset and live values")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

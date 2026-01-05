"""
Register Properties Widget

Handles display and editing of register/register array properties
including name, address, description, and reset values.
"""

from PySide6.QtWidgets import (
    QWidget, QGroupBox, QFormLayout, QLineEdit, QSpinBox, QTextEdit,
    QLabel, QHBoxLayout
)
from PySide6.QtCore import Signal, QEvent

from fpga_lib.core import Register, RegisterArrayAccessor
from debug_mode import debug_manager, DebugValue


class RegisterPropertiesWidget(QWidget):
    """Widget for editing register properties."""

    # Signals
    property_changed = Signal()
    reset_value_changed = Signal()
    live_value_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_item = None
        self._updating = False
        self._last_description = ""

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the user interface."""
        self.register_group = QGroupBox("Properties")
        register_layout = QFormLayout(self.register_group)

        # Name
        self.name_edit = QLineEdit()
        register_layout.addRow("Name:", self.name_edit)

        # Address/Offset
        self.address_spin = QSpinBox()
        self.address_spin.setRange(0, 0x7FFFFFFF)
        self.address_spin.setDisplayIntegerBase(16)
        self.address_spin.setPrefix("0x")
        register_layout.addRow("Address:", self.address_spin)

        # Array-specific properties
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 1024)
        self.count_label = QLabel("Count:")
        register_layout.addRow(self.count_label, self.count_spin)

        self.stride_spin = QSpinBox()
        self.stride_spin.setRange(1, 256)
        self.stride_label = QLabel("Stride:")
        register_layout.addRow(self.stride_label, self.stride_spin)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        register_layout.addRow("Description:", self.description_edit)

        # Reset + Live values
        reset_live_row = QHBoxLayout()
        self.reset_value_edit = QLineEdit()
        self.reset_value_edit.setReadOnly(True)
        self.reset_value_edit.setPlaceholderText("Calculated from bit fields")

        self.live_value_edit = QLineEdit()
        self.live_value_edit.setPlaceholderText("Live (debug)")
        self.live_value_edit.setToolTip("Current live value from active debug set if available")

        reset_live_row.addWidget(self.reset_value_edit)
        reset_live_row.addWidget(QLabel("Live:"))
        reset_live_row.addWidget(self.live_value_edit)
        register_layout.addRow("Reset Value:", reset_live_row)

        # Add to main layout
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addRow(self.register_group)

        # Install event filter for description
        self.description_edit.installEventFilter(self)

        # Initial state
        self._set_array_controls_visible(False)

    def _connect_signals(self):
        """Connect internal signals."""
        self.name_edit.editingFinished.connect(self._on_name_changed)
        self.address_spin.valueChanged.connect(self._on_address_changed)
        self.count_spin.valueChanged.connect(self._on_count_changed)
        self.stride_spin.valueChanged.connect(self._on_stride_changed)
        self.live_value_edit.editingFinished.connect(self._on_live_register_value_changed)

    def eventFilter(self, obj, event):
        """Handle events for widgets with custom behavior."""
        if obj == self.description_edit and event.type() == QEvent.Type.FocusOut:
            current_description = self.description_edit.toPlainText()
            if current_description != self._last_description:
                self._on_description_changed()
                self._last_description = current_description
        return super().eventFilter(obj, event)

    def set_item(self, item):
        """Set the item to display/edit."""
        self.current_item = item
        self._update_display()

    def _update_display(self):
        """Update display based on current item."""
        self._updating = True

        if self.current_item is None:
            self._clear()
            self.setEnabled(False)
        elif isinstance(self.current_item, Register):
            self._load_register(self.current_item)
            self.setEnabled(True)
            self._set_array_controls_visible(False)
        elif isinstance(self.current_item, RegisterArrayAccessor):
            self._load_register_array(self.current_item)
            self.setEnabled(True)
            self._set_array_controls_visible(True)

        self._updating = False

    def _clear(self):
        """Clear all fields."""
        self.name_edit.clear()
        self.address_spin.setValue(0)
        self.count_spin.setValue(1)
        self.stride_spin.setValue(4)
        self.description_edit.clear()
        self._last_description = ""
        self.reset_value_edit.clear()
        self.live_value_edit.clear()

    def _load_register(self, register: Register):
        """Load register data."""
        self.name_edit.setText(register.name)
        self.address_spin.setValue(register.offset)
        self.description_edit.setPlainText(register.description)
        self._last_description = register.description
        # Ensure live values default to reset values if not already set
        self._ensure_live_defaults(register)
        self.update_reset_value_display()
        self._update_live_value_display()

    def _ensure_live_defaults(self, register: Register):
        """Populate live (debug) values with reset defaults if not already defined.

        This runs when a register is loaded. It will NOT overwrite existing
        user-entered live values. Live values mirror reset only by default.
        """
        current_set = debug_manager.get_current_debug_set()
        if current_set is None:
            current_set = debug_manager.create_debug_set("default")

        reg_name = register.name
        reg_live_obj = current_set.get_register_value(reg_name)

        # Determine if we need to initialize: no register live value or value is None
        if reg_live_obj is None or reg_live_obj.value is None:
            # Use register.reset_value as baseline
            reset_val = register.reset_value
            current_set.set_register_value(reg_name, DebugValue(reset_val))

            # Also set individual field values for consistency
            for field_name, field in register._fields.items():
                field_reset = field.reset_value if field.reset_value is not None else 0
                current_set.set_field_value(reg_name, field_name, DebugValue(field_reset))
        else:
            # Register value exists, but ensure all field values are set
            for field_name, field in register._fields.items():
                existing_field_live = current_set.get_field_value(reg_name, field_name)
                if existing_field_live is None or existing_field_live.value is None:
                    # Extract field value from register value
                    reg_value = reg_live_obj.value
                    mask = (1 << field.width) - 1
                    field_value = (reg_value >> field.offset) & mask
                    current_set.set_field_value(reg_name, field_name, DebugValue(field_value))

    def _load_register_array(self, array: RegisterArrayAccessor):
        """Load register array data."""
        self.name_edit.setText(array._name)
        self.address_spin.setValue(array._base_offset)
        self.count_spin.setValue(array._count)
        self.stride_spin.setValue(array._stride)
        array_description = f"Register array with {array._count} entries"
        self.description_edit.setPlainText(array_description)
        self._last_description = array_description
        self.reset_value_edit.setText("N/A (Array)")
        self.live_value_edit.clear()

    def update_reset_value_display(self):
        """Update the calculated reset value display."""
        if isinstance(self.current_item, Register):
            reset_value = self.current_item.reset_value
            self.reset_value_edit.setText(f"0x{reset_value:08X}")
            self._update_live_value_display()
        else:
            self.reset_value_edit.setText("")
            self.live_value_edit.setText("")

    def _update_live_value_display(self):
        """Update the live value display from debug set."""
        if not isinstance(self.current_item, Register):
            self.live_value_edit.setText("")
            return

        current_set = debug_manager.get_current_debug_set()
        reg_name = self.current_item.name
        reg_val_obj = current_set.get_register_value(reg_name) if current_set else None

        if reg_val_obj and reg_val_obj.value is not None:
            self.live_value_edit.setText(f"0x{reg_val_obj.value:08X}")
        else:
            self.live_value_edit.setText("")

    def refresh_live_value(self):
        """Public method to refresh live value display."""
        self._update_live_value_display()

    def update_live_value_display(self):
        """Public alias for _update_live_value_display for backward compatibility."""
        self._update_live_value_display()

    def _set_array_controls_visible(self, visible: bool):
        """Show or hide array-specific controls."""
        self.count_label.setVisible(visible)
        self.count_spin.setVisible(visible)
        self.stride_label.setVisible(visible)
        self.stride_spin.setVisible(visible)

    def _on_name_changed(self):
        """Handle name field changes."""
        if self._updating or not self.current_item:
            return

        new_name = self.name_edit.text()
        if isinstance(self.current_item, Register):
            self.current_item.name = new_name
        elif isinstance(self.current_item, RegisterArrayAccessor):
            self.current_item._name = new_name

        self.property_changed.emit()

    def _on_address_changed(self):
        """Handle address field changes."""
        if self._updating or not self.current_item:
            return

        new_address = self.address_spin.value()
        if isinstance(self.current_item, Register):
            self.current_item.offset = new_address
        elif isinstance(self.current_item, RegisterArrayAccessor):
            self.current_item._base_offset = new_address

        self.property_changed.emit()

    def _on_count_changed(self):
        """Handle count field changes (arrays only)."""
        if self._updating or not isinstance(self.current_item, RegisterArrayAccessor):
            return

        self.current_item._count = self.count_spin.value()
        self.property_changed.emit()

    def _on_stride_changed(self):
        """Handle stride field changes (arrays only)."""
        if self._updating or not isinstance(self.current_item, RegisterArrayAccessor):
            return

        self.current_item._stride = self.stride_spin.value()
        self.property_changed.emit()

    def _on_description_changed(self):
        """Handle description field changes."""
        if self._updating or not self.current_item:
            return

        new_description = self.description_edit.toPlainText()
        if isinstance(self.current_item, Register):
            self.current_item.description = new_description

        self.property_changed.emit()

    def _on_live_register_value_changed(self):
        """Handle editing of the overall live register value."""
        if self._updating or not isinstance(self.current_item, Register):
            return

        reg_name = self.current_item.name
        current_set = debug_manager.get_current_debug_set()
        if current_set is None:
            current_set = debug_manager.create_debug_set("default")

        raw_text = self.live_value_edit.text().strip()
        if raw_text == "":
            # Clear register debug value
            if reg_name in current_set.register_values:
                del current_set.register_values[reg_name]
            if reg_name in current_set.field_values:
                del current_set.field_values[reg_name]
            self._update_live_value_display()
            return

        try:
            from PySide6.QtWidgets import QMessageBox
            dbg_val = DebugValue.from_string(raw_text)
            if dbg_val.value is None or dbg_val.value < 0 or dbg_val.value > 0xFFFFFFFF:
                raise ValueError("Value must be 0..0xFFFFFFFF")

            current_set.set_register_value(reg_name, dbg_val)
            debug_manager.update_field_values_from_register(reg_name, self.current_item, dbg_val.value)
            self._update_live_value_display()
            self.live_value_changed.emit()  # Emit signal for live value changes
        except ValueError as ve:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Live Register Value", str(ve))
            self._update_live_value_display()

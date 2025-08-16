"""
Register Detail Form - Property Editor Component

Provides form-based editing of register and register array properties,
including name, address, description, and bit field management.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLineEdit, QSpinBox, QComboBox, QTextEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QLabel,
    QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .bit_field_visualizer import BitFieldVisualizerWidget
from memory_map_core import MemoryMapProject
from fpga_lib.core import Register, BitField, RegisterArrayAccessor


class RegisterDetailForm(QWidget):
    """
    Form for editing register and register array properties.
    
    Provides detailed editing capabilities for the selected memory map item,
    including bit field management.
    """
    
    # Signals
    register_changed = Signal()
    field_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_project = None
        self.current_item = None
        self._updating = False  # Prevent recursive updates
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Register properties group
        self.register_group = QGroupBox("Properties")
        register_layout = QFormLayout(self.register_group)
        
        # Name
        self.name_edit = QLineEdit()
        register_layout.addRow("Name:", self.name_edit)
        
        # Address/Offset
        self.address_spin = QSpinBox()
        self.address_spin.setRange(0, 0xFFFFFFFF)
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
        
        layout.addWidget(self.register_group)
        
        # Bit fields group
        self.fields_group = QGroupBox("Bit Fields")
        fields_layout = QVBoxLayout(self.fields_group)
        
        # Bit fields table
        self.fields_table = QTableWidget()
        self.fields_table.setColumnCount(5)
        self.fields_table.setHorizontalHeaderLabels([
            "Name", "Bits", "Width", "Access", "Description"
        ])
        
        # Set column widths
        header = self.fields_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.fields_table.setColumnWidth(0, 100)
        self.fields_table.setColumnWidth(1, 80)
        self.fields_table.setColumnWidth(2, 60)
        self.fields_table.setColumnWidth(3, 80)
        
        # Enable selection
        self.fields_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        fields_layout.addWidget(self.fields_table)
        
        # Field buttons
        field_buttons_layout = QHBoxLayout()
        
        self.add_field_btn = QPushButton("Add Field")
        self.remove_field_btn = QPushButton("Remove Field")
        self.edit_field_btn = QPushButton("Edit Field")
        
        field_buttons_layout.addWidget(self.add_field_btn)
        field_buttons_layout.addWidget(self.remove_field_btn)
        field_buttons_layout.addWidget(self.edit_field_btn)
        field_buttons_layout.addStretch()
        
        fields_layout.addLayout(field_buttons_layout)
        layout.addWidget(self.fields_group)
        
        # Initially hide array-specific controls
        self._set_array_controls_visible(False)
        
        # Disable all controls initially
        self._set_controls_enabled(False)
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.name_edit.textChanged.connect(self._on_name_changed)
        self.address_spin.valueChanged.connect(self._on_address_changed)
        self.count_spin.valueChanged.connect(self._on_count_changed)
        self.stride_spin.valueChanged.connect(self._on_stride_changed)
        self.description_edit.textChanged.connect(self._on_description_changed)
        
        self.add_field_btn.clicked.connect(self._add_field)
        self.remove_field_btn.clicked.connect(self._remove_field)
        self.edit_field_btn.clicked.connect(self._edit_field)
        
        self.fields_table.cellChanged.connect(self._on_field_cell_changed)
        self.fields_table.itemSelectionChanged.connect(self._on_field_selection_changed)
    
    def set_project(self, project: MemoryMapProject):
        """Set the current project."""
        self.current_project = project
    
    def set_current_item(self, item):
        """Set the currently selected memory map item."""
        self.current_item = item
        self._update_form()
    
    def _update_form(self):
        """Update form fields based on current item."""
        self._updating = True
        
        if self.current_item is None:
            self._clear_form()
            self._set_controls_enabled(False)
        elif isinstance(self.current_item, Register):
            self._load_register(self.current_item)
            self._set_controls_enabled(True)
            self._set_array_controls_visible(False)
        elif isinstance(self.current_item, RegisterArrayAccessor):
            self._load_register_array(self.current_item)
            self._set_controls_enabled(True)
            self._set_array_controls_visible(True)
        
        self._updating = False
    
    def _clear_form(self):
        """Clear all form fields."""
        self.name_edit.clear()
        self.address_spin.setValue(0)
        self.count_spin.setValue(1)
        self.stride_spin.setValue(4)
        self.description_edit.clear()
        self.fields_table.setRowCount(0)
    
    def _load_register(self, register: Register):
        """Load register data into the form."""
        self.name_edit.setText(register.name)
        self.address_spin.setValue(register.offset)
        self.description_edit.setPlainText(register.description)
        self._load_bit_fields(register._fields)
    
    def _load_register_array(self, array: RegisterArrayAccessor):
        """Load register array data into the form."""
        self.name_edit.setText(array._name)
        self.address_spin.setValue(array._base_offset)
        self.count_spin.setValue(array._count)
        self.stride_spin.setValue(array._stride)
        self.description_edit.setPlainText(f"Register array with {array._count} entries")
        
        # Load field template
        fields_dict = {field.name: field for field in array._field_template}
        self._load_bit_fields(fields_dict)
    
    def _load_bit_fields(self, fields_dict):
        """Load bit fields into the table."""
        self.fields_table.setRowCount(len(fields_dict))
        
        for row, (name, field) in enumerate(fields_dict.items()):
            # Name
            self.fields_table.setItem(row, 0, QTableWidgetItem(field.name))
            
            # Bits representation
            if field.width == 1:
                bits_text = f"[{field.offset}]"
            else:
                high_bit = field.offset + field.width - 1
                bits_text = f"[{high_bit}:{field.offset}]"
            self.fields_table.setItem(row, 1, QTableWidgetItem(bits_text))
            
            # Width
            self.fields_table.setItem(row, 2, QTableWidgetItem(str(field.width)))
            
            # Access
            self.fields_table.setItem(row, 3, QTableWidgetItem(field.access.upper()))
            
            # Description
            self.fields_table.setItem(row, 4, QTableWidgetItem(field.description))
    
    def _set_controls_enabled(self, enabled: bool):
        """Enable or disable all form controls."""
        self.register_group.setEnabled(enabled)
        self.fields_group.setEnabled(enabled)
    
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
        
        self.register_changed.emit()
    
    def _on_address_changed(self):
        """Handle address field changes."""
        if self._updating or not self.current_item:
            return
        
        new_address = self.address_spin.value()
        if isinstance(self.current_item, Register):
            self.current_item.offset = new_address
        elif isinstance(self.current_item, RegisterArrayAccessor):
            self.current_item._base_offset = new_address
        
        self.register_changed.emit()
    
    def _on_count_changed(self):
        """Handle count field changes (arrays only)."""
        if self._updating or not isinstance(self.current_item, RegisterArrayAccessor):
            return
        
        self.current_item._count = self.count_spin.value()
        self.register_changed.emit()
    
    def _on_stride_changed(self):
        """Handle stride field changes (arrays only)."""
        if self._updating or not isinstance(self.current_item, RegisterArrayAccessor):
            return
        
        self.current_item._stride = self.stride_spin.value()
        self.register_changed.emit()
    
    def _on_description_changed(self):
        """Handle description field changes."""
        if self._updating or not self.current_item:
            return
        
        new_description = self.description_edit.toPlainText()
        if isinstance(self.current_item, Register):
            self.current_item.description = new_description
        # Note: RegisterArrayAccessor doesn't have a description field in the current implementation
        
        self.register_changed.emit()
    
    def _add_field(self):
        """Add a new bit field."""
        if not self.current_item:
            return
        
        # Create a default field
        field_name = f"field_{self.fields_table.rowCount()}"
        new_field = BitField(field_name, 0, 1, "rw", "New field")
        
        # Add to current item
        if isinstance(self.current_item, Register):
            self.current_item._fields[field_name] = new_field
        elif isinstance(self.current_item, RegisterArrayAccessor):
            self.current_item._field_template.append(new_field)
        
        # Refresh table
        self._update_form()
        self.field_changed.emit()
    
    def _remove_field(self):
        """Remove the selected bit field."""
        current_row = self.fields_table.currentRow()
        if current_row < 0:
            return
        
        # Get field name
        field_name_item = self.fields_table.item(current_row, 0)
        if not field_name_item:
            return
        
        field_name = field_name_item.text()
        
        # Remove from current item
        if isinstance(self.current_item, Register):
            if field_name in self.current_item._fields:
                del self.current_item._fields[field_name]
        elif isinstance(self.current_item, RegisterArrayAccessor):
            # Find and remove from template
            self.current_item._field_template = [
                f for f in self.current_item._field_template if f.name != field_name
            ]
        
        # Refresh table
        self._update_form()
        self.field_changed.emit()
    
    def _edit_field(self):
        """Edit the selected bit field."""
        # For now, fields are edited directly in the table
        # This could be enhanced with a dedicated field editor dialog
        pass
    
    def _on_field_cell_changed(self, row, column):
        """Handle changes to field table cells."""
        if self._updating:
            return
        
        # This is a simplified implementation
        # In a full implementation, you'd want to validate and update the BitField objects
        self.field_changed.emit()
    
    def _on_field_selection_changed(self):
        """Handle field table selection changes."""
        has_selection = self.fields_table.currentRow() >= 0
        self.remove_field_btn.setEnabled(has_selection)
        self.edit_field_btn.setEnabled(has_selection)

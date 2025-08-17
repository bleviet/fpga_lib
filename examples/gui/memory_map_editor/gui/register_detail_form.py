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
from PySide6.QtGui import QFont, QColor

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
        self.address_spin.setRange(0, 0x7FFFFFFF)  # Use signed 32-bit max to avoid overflow
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
        self.insert_before_btn = QPushButton("Insert Before")
        self.insert_after_btn = QPushButton("Insert After")
        self.remove_field_btn = QPushButton("Remove Field")
        self.edit_field_btn = QPushButton("Edit Field")
        self.recalc_offsets_btn = QPushButton("Recalculate Offsets")

        field_buttons_layout.addWidget(self.add_field_btn)
        field_buttons_layout.addWidget(self.insert_before_btn)
        field_buttons_layout.addWidget(self.insert_after_btn)
        field_buttons_layout.addWidget(self.remove_field_btn)
        field_buttons_layout.addWidget(self.edit_field_btn)
        field_buttons_layout.addWidget(self.recalc_offsets_btn)
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
        self.insert_before_btn.clicked.connect(lambda: self._insert_field('before'))
        self.insert_after_btn.clicked.connect(lambda: self._insert_field('after'))
        self.remove_field_btn.clicked.connect(self._remove_field)
        self.edit_field_btn.clicked.connect(self._edit_field)
        self.recalc_offsets_btn.clicked.connect(self._recalculate_offsets)

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
        """Load bit fields into the table, sorted by offset."""
        # Convert to list and sort by offset
        if isinstance(fields_dict, dict):
            fields_list = list(fields_dict.values())
        else:
            fields_list = list(fields_dict)
        
        # Sort by offset
        fields_list.sort(key=lambda f: f.offset)
        
        self.fields_table.setRowCount(len(fields_list))

        for row, field in enumerate(fields_list):
            # Name
            name_item = QTableWidgetItem(field.name)
            self.fields_table.setItem(row, 0, name_item)

            # Bits representation
            if field.width == 1:
                bits_text = f"[{field.offset}]"
            else:
                high_bit = field.offset + field.width - 1
                bits_text = f"[{high_bit}:{field.offset}]"
            bits_item = QTableWidgetItem(bits_text)
            self.fields_table.setItem(row, 1, bits_item)

            # Width
            width_item = QTableWidgetItem(str(field.width))
            self.fields_table.setItem(row, 2, width_item)

            # Access
            access_item = QTableWidgetItem(field.access.upper())
            self.fields_table.setItem(row, 3, access_item)

            # Description
            desc_item = QTableWidgetItem(field.description)
            self.fields_table.setItem(row, 4, desc_item)

            # Check for overlaps or gaps and highlight if needed
            self._highlight_field_issues(row, field, fields_list)

    def _highlight_field_issues(self, row, field, fields_list):
        """Highlight fields that have overlaps or gaps."""
        has_issue = False
        
        # Check for overlaps with other fields
        for other_field in fields_list:
            if other_field != field:
                # Check if fields overlap
                field_end = field.offset + field.width - 1
                other_end = other_field.offset + other_field.width - 1
                
                if (field.offset <= other_end and field_end >= other_field.offset):
                    has_issue = True
                    break
        
        # Apply highlighting if there's an issue
        if has_issue:
            for col in range(self.fields_table.columnCount()):
                item = self.fields_table.item(row, col)
                if item:
                    item.setBackground(QColor(255, 200, 200))  # Light red for issues
        else:
            # Check if this field has a gap from the previous field
            sorted_fields = sorted(fields_list, key=lambda f: f.offset)
            field_index = sorted_fields.index(field)
            
            if field_index > 0:
                prev_field = sorted_fields[field_index - 1]
                expected_offset = prev_field.offset + prev_field.width
                if field.offset > expected_offset:
                    # There's a gap - highlight in yellow
                    for col in range(self.fields_table.columnCount()):
                        item = self.fields_table.item(row, col)
                        if item:
                            item.setBackground(QColor(255, 255, 200))  # Light yellow for gaps

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
        """Add a new bit field at the end (highest offset)."""
        if not self.current_item:
            return

        # Find the next available offset
        next_offset = self._find_next_available_offset()
        
        # Create a default field
        field_name = self._generate_unique_field_name()
        new_field = BitField(field_name, next_offset, 1, "rw", "New field")

        # Add to current item
        self._add_field_to_item(new_field)

        # Refresh table and emit signal
        self._update_form()
        self.field_changed.emit()

    def _insert_field(self, position='after'):
        """Insert a new bit field before or after the selected row."""
        if not self.current_item:
            return

        current_row = self.fields_table.currentRow()
        if current_row < 0:
            # No selection, fall back to add at end
            self._add_field()
            return

        # Get the field name from the selected row
        field_name_item = self.fields_table.item(current_row, 0)
        if not field_name_item:
            self._add_field()
            return

        selected_field_name = field_name_item.text()
        
        # Get current fields sorted by offset
        fields_list = self._get_sorted_fields()
        
        if not fields_list:
            self._add_field()
            return

        # Find the selected field in the sorted list
        selected_field = None
        selected_index = -1
        for i, field in enumerate(fields_list):
            if field.name == selected_field_name:
                selected_field = field
                selected_index = i
                break

        if selected_field is None:
            self._add_field()
            return

        # Create new field
        new_field_name = self._generate_unique_field_name()
        
        # Determine insertion strategy
        if position == 'before':
            if selected_index == 0:
                # Insert at the very beginning
                # Create the new field with offset 0
                new_field = BitField(new_field_name, 0, 1, "rw", "New field")
                
                # Add the field first
                self._add_field_to_item(new_field)
                
                # Now shift all other fields by 1 offset
                for field in fields_list:
                    field.offset += 1
                
                # Update the item with the modified existing fields
                self._update_item_fields(fields_list + [new_field])
            else:
                # Insert between previous and current field
                prev_field = fields_list[selected_index - 1]
                insert_offset = prev_field.offset + prev_field.width
                
                new_field = BitField(new_field_name, insert_offset, 1, "rw", "New field")
                
                # Add the field
                self._add_field_to_item(new_field)
                
                # Shift subsequent fields
                for i in range(selected_index, len(fields_list)):
                    fields_list[i].offset += 1
                
                # Update the item
                self._update_item_fields(fields_list + [new_field])
        else:  # after
            insert_offset = selected_field.offset + selected_field.width
            
            new_field = BitField(new_field_name, insert_offset, 1, "rw", "New field")
            
            # Add the field
            self._add_field_to_item(new_field)
            
            # Shift subsequent fields
            for i in range(selected_index + 1, len(fields_list)):
                fields_list[i].offset += 1
            
            # Update the item
            self._update_item_fields(fields_list + [new_field])

        # Refresh table and emit signal
        self._update_form()
        self.field_changed.emit()

    def _recalculate_offsets(self):
        """Recalculate field offsets to pack them sequentially without changing field order."""
        if not self.current_item:
            return

        fields_list = self._get_sorted_fields()
        if not fields_list:
            return

        # Sort fields by their current offset to maintain logical order
        fields_list.sort(key=lambda f: f.offset)

        # Recalculate offsets sequentially starting from 0
        current_offset = 0
        for field in fields_list:
            field.offset = current_offset
            current_offset += field.width

        # Update the item with modified fields
        self._update_item_fields(fields_list)

        # Note: Don't call _update_form() here to avoid infinite recursion
        # The caller should handle refreshing the display

    def _get_sorted_fields(self):
        """Get fields sorted by offset."""
        if isinstance(self.current_item, Register):
            fields = list(self.current_item._fields.values())
        elif isinstance(self.current_item, RegisterArrayAccessor):
            fields = list(self.current_item._field_template)
        else:
            return []

        return sorted(fields, key=lambda f: f.offset)

    def _update_item_fields(self, fields_list):
        """Update the current item with the modified fields list."""
        if isinstance(self.current_item, Register):
            # Rebuild the fields dictionary
            self.current_item._fields = {field.name: field for field in fields_list}
        elif isinstance(self.current_item, RegisterArrayAccessor):
            # Update the field template
            self.current_item._field_template = fields_list

    def _find_next_available_offset(self):
        """Find the next available bit offset."""
        fields_list = self._get_sorted_fields()
        
        if not fields_list:
            return 0

        # Find the highest offset + width
        max_offset = max(field.offset + field.width for field in fields_list)
        return max_offset

    def _generate_unique_field_name(self):
        """Generate a unique field name."""
        base_name = "field"
        counter = 0
        
        existing_names = set()
        if isinstance(self.current_item, Register):
            existing_names = set(self.current_item._fields.keys())
        elif isinstance(self.current_item, RegisterArrayAccessor):
            existing_names = set(field.name for field in self.current_item._field_template)

        while True:
            field_name = f"{base_name}_{counter}"
            if field_name not in existing_names:
                return field_name
            counter += 1

    def _add_field_to_item(self, new_field):
        """Add a field to the current item."""
        if isinstance(self.current_item, Register):
            self.current_item._fields[new_field.name] = new_field
        elif isinstance(self.current_item, RegisterArrayAccessor):
            self.current_item._field_template.append(new_field)

    def _remove_field(self):
        """Remove the selected bit field and recalculate offsets."""
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

        # Recalculate offsets to close gaps
        self._recalculate_offsets()

        # Refresh table
        self._update_form()
        self.field_changed.emit()

    def _edit_field(self):
        """Edit the selected bit field."""
        # For now, fields are edited directly in the table
        # This could be enhanced with a dedicated field editor dialog
        pass

    def _on_field_cell_changed(self, row, column):
        """Handle changes to field table cells with validation."""
        if self._updating:
            return

        # Get the field being edited
        field_name_item = self.fields_table.item(row, 0)
        if not field_name_item:
            return

        field_name = field_name_item.text()
        fields_list = self._get_sorted_fields()
        
        # Find the field object
        field = None
        for f in fields_list:
            if f.name == field_name:
                field = f
                break
        
        if not field:
            return

        try:
            # Handle different column edits
            if column == 0:  # Name
                new_name = field_name_item.text().strip()
                if new_name and new_name != field.name:
                    # Check for duplicate names
                    existing_names = set(f.name for f in fields_list if f != field)
                    if new_name in existing_names:
                        QMessageBox.warning(self, "Duplicate Name", 
                                           f"Field name '{new_name}' already exists.")
                        self._update_form()  # Revert changes
                        return
                    
                    # Update field name
                    old_name = field.name
                    field.name = new_name
                    
                    # Update in the item's fields dictionary if it's a Register
                    if isinstance(self.current_item, Register):
                        if old_name in self.current_item._fields:
                            del self.current_item._fields[old_name]
                        self.current_item._fields[new_name] = field

            elif column == 2:  # Width
                width_item = self.fields_table.item(row, 2)
                if width_item:
                    try:
                        new_width = int(width_item.text())
                        if new_width < 1 or new_width > 32:
                            raise ValueError("Width must be between 1 and 32")
                        field.width = new_width
                        # Recalculate offsets to prevent overlaps
                        self._recalculate_offsets()
                    except ValueError as e:
                        QMessageBox.warning(self, "Invalid Width", str(e))
                        self._update_form()  # Revert changes
                        return

            elif column == 3:  # Access
                access_item = self.fields_table.item(row, 3)
                if access_item:
                    new_access = access_item.text().lower().strip()
                    valid_access = ['ro', 'wo', 'rw', 'rw1c']
                    if new_access not in valid_access:
                        QMessageBox.warning(self, "Invalid Access Type", 
                                           f"Access type must be one of: {', '.join(valid_access)}")
                        self._update_form()  # Revert changes
                        return
                    field.access = new_access

            elif column == 4:  # Description
                desc_item = self.fields_table.item(row, 4)
                if desc_item:
                    field.description = desc_item.text()

            # Update the display to reflect any changes
            if column in [1, 2]:  # Bits or Width changed
                self._update_form()

            self.field_changed.emit()

        except Exception as e:
            QMessageBox.warning(self, "Edit Error", f"Error updating field: {str(e)}")
            self._update_form()  # Revert changes

    def _on_field_selection_changed(self):
        """Handle field table selection changes."""
        has_selection = self.fields_table.currentRow() >= 0
        self.insert_before_btn.setEnabled(has_selection)
        self.insert_after_btn.setEnabled(has_selection)
        self.remove_field_btn.setEnabled(has_selection)
        self.edit_field_btn.setEnabled(has_selection)

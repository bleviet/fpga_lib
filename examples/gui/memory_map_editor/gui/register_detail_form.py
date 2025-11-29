"""
Register Detail Form - Property Editor Component

Provides form-based editing of register and register array properties,
including name, address, description, and bit field management.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLineEdit, QSpinBox, QComboBox, QTextEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QLabel,
    QGroupBox, QStyledItemDelegate, QSplitter
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFont, QColor, QShortcut, QKeySequence

from .bit_field_visualizer import BitFieldVisualizerWidget, BitFieldVisualizer
from examples.gui.memory_map_editor.debug_mode import debug_manager, DebugValue
from memory_map_core import MemoryMapProject
from fpga_lib.core import Register, BitField, RegisterArrayAccessor


class AccessTypeDelegate(QStyledItemDelegate):
    """Custom delegate for access type column with dropdown."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.access_types = ['RO', 'WO', 'RW', 'RW1C']

    def createEditor(self, parent, option, index):
        """Create a combo box editor."""
        combo = QComboBox(parent)
        combo.addItems(self.access_types)
        return combo

    def setEditorData(self, editor, index):
        """Set the current value in the editor."""
        value = index.data(Qt.DisplayRole)
        if value:
            editor.setCurrentText(value.upper())

    def setModelData(self, editor, model, index):
        """Set the data from editor back to model."""
        value = editor.currentText()
        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        """Update editor geometry."""
        editor.setGeometry(option.rect)



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
        self._last_description = ""  # Track description changes

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Create horizontal splitter for bit fields (left) and properties (right)
        self.main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.main_splitter)

        # Bit fields group (left panel - 1/3 width)
        self.fields_group = QGroupBox("Bit Fields")
        fields_layout = QVBoxLayout(self.fields_group)

        # Table
        self.fields_table = QTableWidget()
        self.fields_table.setColumnCount(7)
        self.fields_table.setHorizontalHeaderLabels([
            "Name", "Bits", "Width", "Access", "Reset", "Live", "Description"
        ])
        header = self.fields_table.horizontalHeader(); header.setStretchLastSection(True)
        self.fields_table.setColumnWidth(0, 100)
        self.fields_table.setColumnWidth(1, 80)
        self.fields_table.setColumnWidth(2, 60)
        self.fields_table.setColumnWidth(3, 80)
        self.fields_table.setColumnWidth(4, 60)
        self.fields_table.setColumnWidth(5, 60)

        self.access_delegate = AccessTypeDelegate(self)
        self.fields_table.setItemDelegateForColumn(3, self.access_delegate)
        self.fields_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        fields_layout.addWidget(self.fields_table)

        # Field buttons
        field_buttons_layout = QHBoxLayout()
        self.add_field_btn = QPushButton("Add")
        self.add_field_btn.setToolTip("Add Field")
        self.insert_before_btn = QPushButton("Before")
        self.insert_before_btn.setToolTip("Insert Before")
        self.insert_after_btn = QPushButton("After")
        self.insert_after_btn.setToolTip("Insert After")
        self.remove_field_btn = QPushButton("Remove")
        self.remove_field_btn.setToolTip("Remove Field")
        self.move_field_up_btn = QPushButton("⬆")
        self.move_field_up_btn.setMaximumWidth(40)
        self.move_field_up_btn.setToolTip("Move Selected Field Up (Alt+Up)")
        self.move_field_down_btn = QPushButton("⬇")
        self.move_field_down_btn.setMaximumWidth(40)
        self.move_field_down_btn.setToolTip("Move Selected Field Down (Alt+Down)")

        for btn in [self.add_field_btn, self.insert_before_btn, self.insert_after_btn,
                    self.remove_field_btn, self.move_field_up_btn, self.move_field_down_btn]:
            field_buttons_layout.addWidget(btn)
        field_buttons_layout.addStretch()
        fields_layout.addLayout(field_buttons_layout)

        # Recalculate button on separate row for better layout
        recalc_layout = QHBoxLayout()
        self.recalc_offsets_btn = QPushButton("Recalculate Offsets")
        recalc_layout.addWidget(self.recalc_offsets_btn)
        recalc_layout.addStretch()
        fields_layout.addLayout(recalc_layout)

        self.main_splitter.addWidget(self.fields_group)

        # Register properties group (right panel - 2/3 width)
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
        self.count_spin = QSpinBox(); self.count_spin.setRange(1, 1024)
        self.count_label = QLabel("Count:")
        register_layout.addRow(self.count_label, self.count_spin)

        self.stride_spin = QSpinBox(); self.stride_spin.setRange(1, 256)
        self.stride_label = QLabel("Stride:")
        register_layout.addRow(self.stride_label, self.stride_spin)

        # Description
        self.description_edit = QTextEdit(); self.description_edit.setMaximumHeight(60)
        register_layout.addRow("Description:", self.description_edit)

    # Reset + Live values
        reset_live_row = QHBoxLayout()
        self.reset_value_edit = QLineEdit(); self.reset_value_edit.setReadOnly(True)
        self.reset_value_edit.setPlaceholderText("Calculated from bit fields")
        self.live_value_edit = QLineEdit()
        self.live_value_edit.editingFinished.connect(self._on_live_register_value_changed)
        self.live_value_edit.setPlaceholderText("Live (debug)")
        self.live_value_edit.setToolTip("Current live value from active debug set if available")
        reset_live_row.addWidget(self.reset_value_edit)
        reset_live_row.addWidget(QLabel("Live:"))
        reset_live_row.addWidget(self.live_value_edit)
        register_layout.addRow("Reset Value:", reset_live_row)

        # Create a widget to hold properties and bit visualizer vertically
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.addWidget(self.register_group)

        # Add bit field visualizer below properties
        self.bit_visualizer = BitFieldVisualizer()
        right_panel_layout.addWidget(self.bit_visualizer)

        self.main_splitter.addWidget(right_panel_widget)

        # Set splitter proportions: 1/3 for bit fields, 2/3 for properties+visualizer
        self.main_splitter.setSizes([333, 667])  # Proportional to 1:2 ratio

    # Removed periodic live update timer: live values are static user-entered comparison values.

        # Initial state
        self._set_array_controls_visible(False)
        self._set_controls_enabled(False)

    def _connect_signals(self):
        """Connect internal signals."""
        # Use editingFinished instead of textChanged to avoid focus loss on every keystroke
        self.name_edit.editingFinished.connect(self._on_name_changed)
        self.address_spin.valueChanged.connect(self._on_address_changed)
        self.count_spin.valueChanged.connect(self._on_count_changed)
        self.stride_spin.valueChanged.connect(self._on_stride_changed)
        # Use focusOutEvent for description to avoid focus loss on every keystroke
        self.description_edit.installEventFilter(self)

        self.add_field_btn.clicked.connect(self._add_field)
        self.insert_before_btn.clicked.connect(lambda: self._insert_field('before'))
        self.insert_after_btn.clicked.connect(lambda: self._insert_field('after'))
        self.remove_field_btn.clicked.connect(self._remove_field)
        self.move_field_up_btn.clicked.connect(self._move_field_up)
        self.move_field_down_btn.clicked.connect(self._move_field_down)
        self.recalc_offsets_btn.clicked.connect(self._recalculate_offsets)

        # Keyboard shortcuts for bit field move up/down - widget-specific context
        self.move_field_up_shortcut = QShortcut(QKeySequence("Alt+Up"), self.fields_table)
        self.move_field_up_shortcut.setContext(Qt.WidgetShortcut)
        self.move_field_up_shortcut.activated.connect(self._move_field_up)

        self.move_field_down_shortcut = QShortcut(QKeySequence("Alt+Down"), self.fields_table)
        self.move_field_down_shortcut.setContext(Qt.WidgetShortcut)
        self.move_field_down_shortcut.activated.connect(self._move_field_down)

        self.fields_table.cellChanged.connect(self._on_field_cell_changed)
        self.fields_table.itemSelectionChanged.connect(self._on_field_selection_changed)

    def eventFilter(self, obj, event):
        """Handle events for widgets with custom behavior."""
        if obj == self.description_edit and event.type() == QEvent.Type.FocusOut:
            # Only handle description changes if the content actually changed
            current_description = self.description_edit.toPlainText()
            if current_description != self._last_description:
                self._on_description_changed()
                self._last_description = current_description
        return super().eventFilter(obj, event)

    def set_project(self, project: MemoryMapProject):
        """Set the current project."""
        self.current_project = project
        self.bit_visualizer.set_project(project)

    def set_current_item(self, item):
        """Set the currently selected memory map item."""
        self.current_item = item
        self._update_form()
        self.bit_visualizer.set_current_item(item)

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
        self._last_description = ""  # Reset description tracking
        self.reset_value_edit.clear()
        self.fields_table.setRowCount(0)

    def _load_register(self, register: Register):
        """Load register data into the form."""
        self.name_edit.setText(register.name)
        self.address_spin.setValue(register.offset)
        self.description_edit.setPlainText(register.description)
        self._last_description = register.description  # Track initial description
        # Ensure live values default to reset values before populating table so live column can show them.
        self._ensure_live_defaults(register)
        self._load_bit_fields(register._fields)
        self._update_reset_value_display()
        # Populate live column cells immediately
        self.refresh_live_display()

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

        # For each field, if no live field value set, copy reset
        for field_name, field in register._fields.items():
            existing_field_live = current_set.get_field_value(reg_name, field_name)
            if not existing_field_live or existing_field_live.value is None:
                # If reset_value is None treat as 0 for live default
                fv = field.reset_value if field.reset_value is not None else 0
                current_set.set_field_value(reg_name, field_name, DebugValue(fv))

        # Emit change so visualizer reflects initial live = reset
        self.field_changed.emit()

    def _load_register_array(self, array: RegisterArrayAccessor):
        """Load register array data into the form."""
        self.name_edit.setText(array._name)
        self.address_spin.setValue(array._base_offset)
        self.count_spin.setValue(array._count)
        self.stride_spin.setValue(array._stride)
        array_description = f"Register array with {array._count} entries"
        self.description_edit.setPlainText(array_description)
        self._last_description = array_description  # Track initial description

        # Load field template - arrays don't show reset values since each instance is separate
        fields_dict = {field.name: field for field in array._field_template}
        self._load_bit_fields(fields_dict)
        self.reset_value_edit.setText("N/A (Array)")

    def _update_reset_value_display(self):
        """Update the calculated reset value display."""
        if isinstance(self.current_item, Register):
            reset_value = self.current_item.reset_value
            self.reset_value_edit.setText(f"0x{reset_value:08X}")
            # Update live display (no auto-sync; live is user-entered)
            self._update_live_value_display()
        else:
            self.reset_value_edit.setText("")
            self.live_value_edit.setText("")

    def _load_bit_fields(self, fields_dict):
        """Load bit fields into the table, sorted by offset."""
        fields_list = list(fields_dict.values()) if isinstance(fields_dict, dict) else list(fields_dict)
        fields_list.sort(key=lambda f: f.offset)
        self.fields_table.setRowCount(len(fields_list))
        current_set = debug_manager.get_current_debug_set()
        for row, field in enumerate(fields_list):
            self.fields_table.setItem(row, 0, QTableWidgetItem(field.name))
            if field.width == 1:
                bits_text = f"[{field.offset}]"
            else:
                high_bit = field.offset + field.width - 1
                bits_text = f"[{high_bit}:{field.offset}]"
            self.fields_table.setItem(row, 1, QTableWidgetItem(bits_text))
            self.fields_table.setItem(row, 2, QTableWidgetItem(str(field.width)))
            self.fields_table.setItem(row, 3, QTableWidgetItem(field.access.upper()))
            reset_val = field.reset_value if field.reset_value is not None else 0
            self.fields_table.setItem(row, 4, QTableWidgetItem(f"0x{reset_val:X}"))
            # Determine initial live value (after defaults ensured)
            live_text = ""
            live_val = None
            if isinstance(self.current_item, Register) and current_set:
                reg_name = self.current_item.name
                field_dbg = current_set.get_field_value(reg_name, field.name)
                if field_dbg and field_dbg.value is not None:
                    live_val = field_dbg.value
                    live_text = f"0x{live_val:X}"
            live_item = QTableWidgetItem(live_text)  # editable for live field value
            # Highlight in green if live differs from reset
            if live_val is not None and live_val != reset_val:
                live_item.setBackground(QColor(144, 238, 144))  # Light green
            self.fields_table.setItem(row, 5, live_item)
            self.fields_table.setItem(row, 6, QTableWidgetItem(field.description))
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

    def _update_live_value_display(self):
        """Update overall live register value line edit."""
        if not isinstance(self.current_item, Register):
            self.live_value_edit.setText("")
            return
        # Live value is user-entered static comparison value; derive from current debug set if present
        current_set = debug_manager.get_current_debug_set()
        reg_name = self.current_item.name
        reg_val_obj = current_set.get_register_value(reg_name) if current_set else None
        if reg_val_obj and reg_val_obj.value is not None:
            self.live_value_edit.setText(f"0x{reg_val_obj.value:08X}")
        else:
            self.live_value_edit.setText("")

    def refresh_live_display(self):
        """Refresh displayed live values from debug set once (no polling)."""
        if not isinstance(self.current_item, Register):
            return
        current_set = debug_manager.get_current_debug_set()
        reg_name = self.current_item.name if self.current_item else None
        reg_val_obj = current_set.get_register_value(reg_name) if current_set and reg_name else None
        reg_value = reg_val_obj.value if reg_val_obj and reg_val_obj.value is not None else None
        # If no live value captured yet, default to reset and recalc
        if current_set and (reg_val_obj is None or reg_value is None):
            self._ensure_live_defaults(self.current_item)
            reg_val_obj = current_set.get_register_value(reg_name)
            reg_value = reg_val_obj.value if reg_val_obj and reg_val_obj.value is not None else None

        if reg_value is not None:
            for row in range(self.fields_table.rowCount()):
                name_item = self.fields_table.item(row, 0)
                live_item = self.fields_table.item(row, 5)
                reset_item = self.fields_table.item(row, 4)
                if not name_item or not live_item:
                    continue
                field = self.current_item._fields.get(name_item.text())
                if field:
                    # Use field debug value if explicitly set; else derive from register value (already sync'd)
                    field_dbg = current_set.get_field_value(reg_name, field.name) if current_set else None
                    if field_dbg and field_dbg.value is not None:
                        field_val = field_dbg.value
                    else:
                        mask = (1 << field.width) - 1
                        field_val = (reg_value >> field.offset) & mask
                    hex_width = (field.width + 3) // 4
                    live_item.setText(f"0x{field_val:0{hex_width}X}")

                    # Highlight in green if live differs from reset
                    reset_val = field.reset_value if field.reset_value is not None else 0
                    if field_val != reset_val:
                        live_item.setBackground(QColor(144, 238, 144))  # Light green
                    else:
                        live_item.setBackground(QColor(255, 255, 255))  # White (default)
            self.live_value_edit.setText(f"0x{reg_value:08X}")
        # Trigger visualizer update
        self.field_changed.emit()

    def _set_controls_enabled(self, enabled: bool):
        """Enable or disable all form controls."""
        self.register_group.setEnabled(enabled)
        self.fields_group.setEnabled(enabled)

        if not enabled:
            # Explicitly disable move buttons when controls are disabled
            self.move_field_up_btn.setEnabled(False)
            self.move_field_down_btn.setEnabled(False)

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

        # Find available space for a 1-bit field
        next_offset = self._find_available_space(1)
        if next_offset == -1:
            QMessageBox.warning(self, "Cannot Add Field",
                              "No space available in the 32-bit register for a new field.")
            return

        # Create a default field
        field_name = self._generate_unique_field_name()
        new_field = BitField(field_name, next_offset, 1, "rw", "New field", reset_value=0)

        # Validate the field fits (should always pass, but double-check)
        is_valid, error_msg = self._validate_field_fits(new_field)
        if not is_valid:
            QMessageBox.warning(self, "Cannot Add Field", f"Validation failed: {error_msg}")
            return

        # Add to current item
        self._add_field_to_item(new_field)

        # Refresh table and emit signal
        self._update_form()
        self._update_reset_value_display()
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
                new_field = BitField(new_field_name, 0, 1, "rw", "New field", reset_value=0)

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

                new_field = BitField(new_field_name, insert_offset, 1, "rw", "New field", reset_value=0)

                # Add the field
                self._add_field_to_item(new_field)

                # Shift subsequent fields
                for i in range(selected_index, len(fields_list)):
                    fields_list[i].offset += 1

                # Update the item
                self._update_item_fields(fields_list + [new_field])
        else:  # after
            insert_offset = selected_field.offset + selected_field.width

            new_field = BitField(new_field_name, insert_offset, 1, "rw", "New field", reset_value=0)

            # Add the field
            self._add_field_to_item(new_field)

            # Shift subsequent fields
            for i in range(selected_index + 1, len(fields_list)):
                fields_list[i].offset += 1

            # Update the item
            self._update_item_fields(fields_list + [new_field])

        # Validate that all fields still fit within 32 bits
        all_fields = self._get_sorted_fields()
        for field in all_fields:
            if field.offset + field.width > 32:
                QMessageBox.warning(self, "Cannot Insert Field",
                                  f"Inserting field would cause '{field.name}' to extend beyond bit 31. "
                                  f"Consider removing some fields or recalculating offsets.")
                # Revert the form to show original state
                self._update_form()
                return

        # Refresh table and emit signal
        self._update_form()
        self._update_reset_value_display()
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

    def _recalculate_offsets_preserving_field(self, preserve_field):
        """
        Recalculate field offsets while preserving the position of a specific field.
        Other fields are packed around it.
        """
        if not self.current_item:
            return

        fields_list = self._get_sorted_fields()
        if not fields_list or preserve_field not in fields_list:
            return

        # Remove the preserved field from the list temporarily
        other_fields = [f for f in fields_list if f != preserve_field]

        # Sort other fields by their original offset
        other_fields.sort(key=lambda f: f.offset)

        # Try to fit other fields around the preserved field
        preserved_start = preserve_field.offset
        preserved_end = preserve_field.offset + preserve_field.width

        # Place fields before the preserved field
        current_offset = 0
        fields_before = []
        fields_after = []

        for field in other_fields:
            if field.offset < preserved_start:
                fields_before.append(field)
            else:
                fields_after.append(field)

        # Pack fields before the preserved field
        for field in fields_before:
            if current_offset + field.width <= preserved_start:
                field.offset = current_offset
                current_offset += field.width
            else:
                # Move to after preserved field
                fields_after.append(field)

        # Pack fields after the preserved field
        current_offset = preserved_end
        for field in fields_after:
            field.offset = current_offset
            current_offset += field.width

        # Update the item with modified fields
        self._update_item_fields(fields_list)

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

    def _validate_field_fits(self, new_field, exclude_field=None):
        """
        Validate that a field fits within the 32-bit register without overlaps.

        Args:
            new_field: The BitField to validate
            exclude_field: Optional field to exclude from validation (for editing)

        Returns:
            tuple: (is_valid, error_message)
        """
        if new_field.offset < 0:
            return False, "Offset cannot be negative"

        if new_field.width < 1 or new_field.width > 32:
            return False, "Width must be between 1 and 32"

        if new_field.offset + new_field.width > 32:
            return False, f"Field extends beyond register (bit {new_field.offset + new_field.width - 1} > 31)"

        # Check for overlaps with existing fields
        fields_list = self._get_sorted_fields()
        for existing_field in fields_list:
            if exclude_field and existing_field == exclude_field:
                continue

            # Check if fields overlap
            if not (new_field.offset + new_field.width <= existing_field.offset or
                    existing_field.offset + existing_field.width <= new_field.offset):
                return False, f"Field overlaps with '{existing_field.name}' (bits {existing_field.offset}-{existing_field.offset + existing_field.width - 1})"

        return True, ""

    def _find_available_space(self, width):
        """
        Find available space for a field of given width.

        Returns:
            int: Available offset, or -1 if no space
        """
        if width < 1 or width > 32:
            return -1

        fields_list = self._get_sorted_fields()
        if not fields_list:
            return 0 if width <= 32 else -1

        # Sort fields by offset
        fields_list.sort(key=lambda f: f.offset)

        # Check space at the beginning
        if fields_list[0].offset >= width:
            return 0

        # Check gaps between fields
        for i in range(len(fields_list) - 1):
            current_end = fields_list[i].offset + fields_list[i].width
            next_start = fields_list[i + 1].offset
            gap_size = next_start - current_end

            if gap_size >= width:
                return current_end

        # Check space at the end
        last_field = fields_list[-1]
        last_end = last_field.offset + last_field.width
        if last_end + width <= 32:
            return last_end

        return -1  # No space available

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
        self._update_reset_value_display()
        self.field_changed.emit()

    def _move_field_up(self):
        """Move the selected bit field up in the list and recalculate offsets."""
        self._move_field(-1)

    def _move_field_down(self):
        """Move the selected bit field down in the list and recalculate offsets."""
        self._move_field(1)

    def _move_field(self, direction):
        """
        Move the selected bit field up or down in the list.

        Args:
            direction: -1 for up, 1 for down
        """
        current_row = self.fields_table.currentRow()
        if current_row < 0:
            return

        # Get the selected field name from the table
        field_name_item = self.fields_table.item(current_row, 0)
        if not field_name_item:
            return
        selected_field_name = field_name_item.text()

        # Get all bit fields sorted by offset
        fields_list = self._get_sorted_fields()
        if len(fields_list) < 2:
            return  # Need at least 2 fields to move

        # Find the selected field in the sorted list by name
        selected_field = None
        selected_index = -1
        for i, field in enumerate(fields_list):
            if field.name == selected_field_name:
                selected_field = field
                selected_index = i
                break

        if selected_field is None:
            return  # Selected field not found

        new_index = selected_index + direction

        # Check bounds
        if new_index < 0 or new_index >= len(fields_list):
            return

        # Remove the field from its current position and insert at new position
        fields_list.pop(selected_index)
        fields_list.insert(new_index, selected_field)

        # Recalculate offsets for the reordered fields
        current_offset = 0
        for field in fields_list:
            field.offset = current_offset
            current_offset += field.width

        # Update the item with the new field order
        self._update_item_fields(fields_list)

        # Refresh the form and maintain selection on the moved field
        self._update_form()

        # Update reset value display
        self._update_reset_value_display()

        # Select the moved field at its new position
        for row in range(self.fields_table.rowCount()):
            field_name_item = self.fields_table.item(row, 0)
            if field_name_item and field_name_item.text() == selected_field.name:
                self.fields_table.selectRow(row)
                break

        self.field_changed.emit()

    def _on_field_cell_changed(self, row, column):
        """Handle changes to field table cells with validation."""
        if self._updating:
            return

        # Get the field being edited
        field_name_item = self.fields_table.item(row, 0)
        if not field_name_item:
            return

        fields_list = self._get_sorted_fields()

        # Get the current name in the table (might be new name being typed)
        current_table_name = field_name_item.text()

        # For name changes (column 0), we need special handling since the name might be mid-edit
        if column == 0:
            # Find the field that corresponds to this table row
            # The table is ordered by offset (same as fields_list)
            if row >= len(fields_list):
                return
            field = fields_list[row]
        else:
            # For other columns, find field by current name in the field object
            field = None
            for f in fields_list:
                if f.name == current_table_name:
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
                    elif isinstance(self.current_item, RegisterArrayAccessor):
                        # For arrays, the field template is already updated since we modified the field object
                        pass

            elif column == 1:  # Bits (bit range like [7:0] or [5])
                bits_item = self.fields_table.item(row, 1)
                if bits_item:
                    try:
                        bits_text = bits_item.text().strip()

                        # Parse bit range: [7:0] or [5]
                        if bits_text.startswith('[') and bits_text.endswith(']'):
                            inner = bits_text[1:-1]
                            if ':' in inner:
                                # Range format [high:low]
                                high_str, low_str = inner.split(':')
                                high_bit = int(high_str.strip())
                                low_bit = int(low_str.strip())

                                if high_bit < low_bit:
                                    raise ValueError("High bit must be >= low bit")

                                new_offset = low_bit
                                new_width = high_bit - low_bit + 1
                            else:
                                # Single bit format [5]
                                bit_num = int(inner.strip())
                                new_offset = bit_num
                                new_width = 1
                        else:
                            raise ValueError("Bit range must be in format [high:low] or [bit]")

                        # Validate the new offset and width
                        temp_field = BitField(field.name, new_offset, new_width, field.access, field.description)
                        is_valid, error_msg = self._validate_field_fits(temp_field, exclude_field=field)

                        if not is_valid:
                            # Offer to automatically adjust other fields
                            reply = QMessageBox.question(
                                self,
                                "Field Overlap Detected",
                                f"{error_msg}\n\nWould you like to automatically recalculate other field offsets to accommodate this change?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.Yes
                            )

                            if reply == QMessageBox.Yes:
                                # Apply the changes
                                field.offset = new_offset
                                field.width = new_width

                                # Recalculate offsets for other fields while preserving this one
                                self._recalculate_offsets_preserving_field(field)

                                # Validate final result
                                final_fields = self._get_sorted_fields()
                                max_bit = max(f.offset + f.width for f in final_fields) if final_fields else 0

                                if max_bit > 32:
                                    # Revert if still doesn't fit
                                    self._update_form()
                                    QMessageBox.warning(
                                        self,
                                        "Cannot Fit Fields",
                                        f"Cannot fit all fields within 32-bit register even after recalculation."
                                    )
                                    return
                            else:
                                # User declined, revert
                                self._update_form()
                                return
                        else:
                            # Valid change, apply it
                            field.offset = new_offset
                            field.width = new_width

                    except ValueError as e:
                        QMessageBox.warning(self, "Invalid Bit Range", str(e))
                        self._update_form()  # Revert changes
                        return

            elif column == 2:  # Width
                width_item = self.fields_table.item(row, 2)
                if width_item:
                    try:
                        new_width = int(width_item.text())
                        old_width = field.width

                        # Create a temporary field with new width to validate
                        temp_field = BitField(field.name, field.offset, new_width, field.access, field.description)
                        is_valid, error_msg = self._validate_field_fits(temp_field, exclude_field=field)

                        if not is_valid:
                            # Offer to automatically adjust offsets
                            reply = QMessageBox.question(
                                self,
                                "Field Overlap Detected",
                                f"{error_msg}\n\nWould you like to automatically recalculate all field offsets to accommodate this change?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.Yes
                            )

                            if reply == QMessageBox.Yes:
                                # Apply the width change first
                                field.width = new_width

                                # Then recalculate all offsets
                                self._recalculate_offsets()

                                # Check if the recalculation resolved the issue
                                final_fields = self._get_sorted_fields()
                                max_bit = max(f.offset + f.width for f in final_fields) if final_fields else 0

                                if max_bit > 32:
                                    # Still doesn't fit, revert and show error
                                    field.width = old_width
                                    self._recalculate_offsets()
                                    QMessageBox.warning(
                                        self,
                                        "Cannot Fit Fields",
                                        f"Even after recalculating offsets, the fields would extend to bit {max_bit-1}, "
                                        f"which exceeds the 32-bit register limit. Please reduce field widths."
                                    )
                                    self._update_form()  # Revert changes
                                    return
                            else:
                                # User declined, revert the change
                                self._update_form()  # Revert changes
                                return
                        else:
                            # If valid, apply the change directly
                            field.width = new_width
                        # Note: Don't auto-recalculate offsets for width changes to preserve user intent

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

            elif column == 4:  # Reset value
                reset_item = self.fields_table.item(row, 4)
                if reset_item:
                    try:
                        reset_text = reset_item.text().strip()
                        if reset_text == "" or reset_text.lower() == "none":
                            field.reset_value = None
                        else:
                            new_reset = int(reset_text)
                            max_value = (1 << field.width) - 1
                            if new_reset < 0 or new_reset > max_value:
                                QMessageBox.warning(self, "Invalid Reset Value",
                                                   f"Reset value must be between 0 and {max_value} for a {field.width}-bit field.")
                                self._update_form()  # Revert changes
                                return
                            field.reset_value = new_reset

                        # Update the reset value display
                        self._update_reset_value_display()

                    except ValueError:
                        QMessageBox.warning(self, "Invalid Reset Value", "Reset value must be a valid integer.")
                        self._update_form()  # Revert changes
                        return

            elif column == 5:  # Live value edit
                # User edited a live field value
                live_item = self.fields_table.item(row, 5)
                if live_item and isinstance(self.current_item, Register):
                    reg_name = self.current_item.name
                    current_set = debug_manager.get_current_debug_set()
                    if current_set is None:
                        # Auto-create a default set if none exists
                        current_set = debug_manager.create_debug_set("default")
                    raw_text = live_item.text().strip()
                    if raw_text == "":
                        # Clear field debug value
                        # Leave existing register value intact (will dominate display)
                        field_debugs = current_set.field_values.get(reg_name, {})
                        if field.name in field_debugs:
                            del field_debugs[field.name]
                        # Recompute composed register value from remaining field values
                        composed = debug_manager.calculate_register_value_from_fields(reg_name, self.current_item)
                        if composed is not None:
                            current_set.set_register_value(reg_name, DebugValue(composed))
                        self.refresh_live_display()
                    else:
                        try:
                            dbg_val = DebugValue.from_string(raw_text)
                            max_field_val = (1 << field.width) - 1
                            if dbg_val.value is None or dbg_val.value < 0 or dbg_val.value > max_field_val:
                                raise ValueError(f"Value must be 0..{max_field_val} for a {field.width}-bit field")
                            current_set.set_field_value(reg_name, field.name, dbg_val)
                            # Recalculate whole register value from all field debug values
                            composed = debug_manager.calculate_register_value_from_fields(reg_name, self.current_item)
                            if composed is not None:
                                current_set.set_register_value(reg_name, DebugValue(composed))
                            self.refresh_live_display()
                            self.field_changed.emit()  # trigger visualizer repaint
                        except ValueError as ve:
                            QMessageBox.warning(self, "Invalid Live Field Value", str(ve))
                            # Revert display
                            self.refresh_live_display()
                            return

            elif column == 6:  # Description
                desc_item = self.fields_table.item(row, 6)
                if desc_item:
                    field.description = desc_item.text()

            # Update the display to reflect any changes
            if column in [1, 2]:  # Bits or Width changed
                self._update_form()

            self.bit_visualizer.refresh()
            self.field_changed.emit()

            # Ensure the register's fields dictionary is synchronized
            fields_list = self._get_sorted_fields()
            self._update_item_fields(fields_list)

        except Exception as e:
            QMessageBox.warning(self, "Edit Error", f"Error updating field: {str(e)}")
            self._update_form()  # Revert changes

    def _on_field_selection_changed(self):
        """Handle field table selection changes."""
        current_row = self.fields_table.currentRow()
        has_selection = current_row >= 0

        self.insert_before_btn.setEnabled(has_selection)
        self.insert_after_btn.setEnabled(has_selection)
        self.remove_field_btn.setEnabled(has_selection)

        # Enable move buttons based on position
        if has_selection:
            row_count = self.fields_table.rowCount()
            self.move_field_up_btn.setEnabled(current_row > 0)
            self.move_field_down_btn.setEnabled(current_row < row_count - 1)
        else:
            self.move_field_up_btn.setEnabled(False)
            self.move_field_down_btn.setEnabled(False)

    def _on_live_register_value_changed(self):
        """Handle editing of the overall live register value line edit."""
        if self._updating or not isinstance(self.current_item, Register):
            return
        reg_name = self.current_item.name
        current_set = debug_manager.get_current_debug_set()
        if current_set is None:
            current_set = debug_manager.create_debug_set("default")
        raw_text = self.live_value_edit.text().strip()
        if raw_text == "":
            # Clear register debug value and derived field values
            if reg_name in current_set.register_values:
                del current_set.register_values[reg_name]
            if reg_name in current_set.field_values:
                del current_set.field_values[reg_name]
            self.refresh_live_display()
            return
        try:
            dbg_val = DebugValue.from_string(raw_text)
            if dbg_val.value is None or dbg_val.value < 0 or dbg_val.value > 0xFFFFFFFF:
                raise ValueError("Value must be 0..0xFFFFFFFF")
            # Store register value
            current_set.set_register_value(reg_name, dbg_val)
            # Decompose into field values
            debug_manager.update_field_values_from_register(reg_name, self.current_item, dbg_val.value)
            self.refresh_live_display()
            self.field_changed.emit()  # ensure visualizer updates
        except ValueError as ve:
            QMessageBox.warning(self, "Invalid Live Register Value", str(ve))
            # Revert displayed value
            self.refresh_live_display()
            return

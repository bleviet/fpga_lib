"""
Bit Field Table Widget Module

Provides the table interface for editing and displaying bit fields in a register.
Handles user interactions, cell editing, validation, and visual highlighting.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTableWidget, QTableWidgetItem, QMessageBox)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut

from memory_map_core import Register, RegisterArrayAccessor, BitField
from examples.gui.memory_map_editor.debug_mode import debug_manager, DebugValue
from .delegates import AccessTypeDelegate
from .bit_field_operations import BitFieldOperations


class BitFieldTableWidget(QWidget):
    """Widget for managing bit field table display and editing."""

    # Signals
    field_changed = Signal()  # Emitted when any field is modified

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_item = None
        self._updating = False
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the table and control buttons."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Name", "Bits", "Width", "Access", "Reset Value", "Live Value", "Description"
        ])

        # Set column widths
        self.table.setColumnWidth(0, 100)  # Name
        self.table.setColumnWidth(1, 80)   # Bits
        self.table.setColumnWidth(2, 60)   # Width
        self.table.setColumnWidth(3, 80)   # Access
        self.table.setColumnWidth(4, 100)  # Reset Value
        self.table.setColumnWidth(5, 100)  # Live Value
        self.table.setColumnWidth(6, 200)  # Description

        # Set delegate for Access column
        access_delegate = AccessTypeDelegate(self.table)
        self.table.setItemDelegateForColumn(3, access_delegate)

        # Enable single-click editing for Access column
        from PySide6.QtWidgets import QAbstractItemView
        self.table.setEditTriggers(
            QAbstractItemView.CurrentChanged |
            QAbstractItemView.DoubleClicked |
            QAbstractItemView.SelectedClicked |
            QAbstractItemView.EditKeyPressed
        )

        layout.addWidget(self.table)

        # Control buttons
        button_layout = QHBoxLayout()

        self.add_field_btn = QPushButton("Add Field")
        self.insert_before_btn = QPushButton("Insert Before")
        self.insert_after_btn = QPushButton("Insert After")
        self.remove_field_btn = QPushButton("Remove Field")
        self.move_field_up_btn = QPushButton("Move Up")
        self.move_field_down_btn = QPushButton("Move Down")
        self.recalc_offsets_btn = QPushButton("Recalculate Offsets")

        button_layout.addWidget(self.add_field_btn)
        button_layout.addWidget(self.insert_before_btn)
        button_layout.addWidget(self.insert_after_btn)
        button_layout.addWidget(self.remove_field_btn)
        button_layout.addWidget(self.move_field_up_btn)
        button_layout.addWidget(self.move_field_down_btn)
        button_layout.addWidget(self.recalc_offsets_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Initially disable buttons
        self.insert_before_btn.setEnabled(False)
        self.insert_after_btn.setEnabled(False)
        self.remove_field_btn.setEnabled(False)
        self.move_field_up_btn.setEnabled(False)
        self.move_field_down_btn.setEnabled(False)

    def _connect_signals(self):
        """Connect internal signals."""
        self.add_field_btn.clicked.connect(self._add_field)
        self.insert_before_btn.clicked.connect(lambda: self._insert_field('before'))
        self.insert_after_btn.clicked.connect(lambda: self._insert_field('after'))
        self.remove_field_btn.clicked.connect(self._remove_field)
        self.move_field_up_btn.clicked.connect(self._move_field_up)
        self.move_field_down_btn.clicked.connect(self._move_field_down)
        self.recalc_offsets_btn.clicked.connect(self._recalculate_offsets)

        # Keyboard shortcuts - widget-specific context
        self.move_field_up_shortcut = QShortcut(QKeySequence("Alt+Up"), self.table)
        self.move_field_up_shortcut.setContext(Qt.WidgetShortcut)
        self.move_field_up_shortcut.activated.connect(self._move_field_up)

        self.move_field_down_shortcut = QShortcut(QKeySequence("Alt+Down"), self.table)
        self.move_field_down_shortcut.setContext(Qt.WidgetShortcut)
        self.move_field_down_shortcut.activated.connect(self._move_field_down)

        self.table.cellChanged.connect(self._on_cell_changed)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

    def set_current_item(self, item):
        """Set the current register or array item."""
        self.current_item = item
        self.refresh()

    def refresh(self):
        """Refresh the table display from current item."""
        self._updating = True

        if self.current_item is None:
            self.table.setRowCount(0)
            self._updating = False
            return

        # Get fields sorted by offset
        fields_list = BitFieldOperations.get_sorted_fields(self.current_item)
        self.table.setRowCount(len(fields_list))

        # Set vertical header labels to start from 0
        vertical_labels = [str(i) for i in range(len(fields_list))]
        self.table.setVerticalHeaderLabels(vertical_labels)

        current_set = debug_manager.get_current_debug_set()
        reg_name = self.current_item.name if isinstance(self.current_item, Register) else None

        for row, field in enumerate(fields_list):
            # Name
            self.table.setItem(row, 0, QTableWidgetItem(field.name))

            # Bits
            if field.width == 1:
                bits_text = f"[{field.offset}]"
            else:
                high_bit = field.offset + field.width - 1
                bits_text = f"[{high_bit}:{field.offset}]"
            self.table.setItem(row, 1, QTableWidgetItem(bits_text))

            # Width
            self.table.setItem(row, 2, QTableWidgetItem(str(field.width)))

            # Access
            self.table.setItem(row, 3, QTableWidgetItem(field.access.upper()))

            # Reset Value
            reset_val = field.reset_value if field.reset_value is not None else 0
            self.table.setItem(row, 4, QTableWidgetItem(f"0x{reset_val:X}"))

            # Live Value
            live_text = ""
            live_val = None
            if isinstance(self.current_item, Register) and current_set and reg_name:
                # Try to get field debug value
                field_dbg = current_set.get_field_value(reg_name, field.name)
                if field_dbg and field_dbg.value is not None:
                    live_val = field_dbg.value
                else:
                    # Fall back to extracting from register value
                    reg_val_obj = current_set.get_register_value(reg_name)
                    if reg_val_obj and reg_val_obj.value is not None:
                        mask = (1 << field.width) - 1
                        live_val = (reg_val_obj.value >> field.offset) & mask

                # Format the live value if we have one
                if live_val is not None:
                    hex_width = max(1, (field.width + 3) // 4)
                    live_text = f"0x{live_val:0{hex_width}X}"

            live_item = QTableWidgetItem(live_text)

            # Highlight in green if live differs from reset
            if live_val is not None and live_val != reset_val:
                live_item.setBackground(QColor(144, 238, 144))  # Light green

            self.table.setItem(row, 5, live_item)

            # Description
            self.table.setItem(row, 6, QTableWidgetItem(field.description))

            # Highlight field issues
            self._highlight_field_issues(row, field, fields_list)

        self._updating = False

    def _highlight_field_issues(self, row, field, fields_list):
        """Highlight fields that have overlaps or gaps."""
        has_issue = False

        # Check for overlaps with other fields
        for other_field in fields_list:
            if other_field != field:
                field_end = field.offset + field.width - 1
                other_end = other_field.offset + other_field.width - 1

                if (field.offset <= other_end and field_end >= other_field.offset):
                    has_issue = True
                    break

        # Apply highlighting if there's an issue
        if has_issue:
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
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
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        if item:
                            item.setBackground(QColor(255, 255, 200))  # Light yellow for gaps

    def _add_field(self):
        """Add a new bit field at the end (highest offset)."""
        if not self.current_item:
            return

        # Find available space for a 1-bit field
        next_offset = BitFieldOperations.find_available_space(self.current_item, 1)
        if next_offset == -1:
            QMessageBox.warning(self, "Cannot Add Field",
                              "No space available in the 32-bit register for a new field.")
            return

        # Create a default field
        field_name = BitFieldOperations.generate_unique_field_name(self.current_item)
        new_field = BitField(field_name, next_offset, 1, "rw", "New field", reset_value=0)

        # Validate the field fits
        is_valid, error_msg = BitFieldOperations.validate_field_fits(
            self.current_item, new_field
        )
        if not is_valid:
            QMessageBox.warning(self, "Cannot Add Field", f"Validation failed: {error_msg}")
            return

        # Add to current item
        self._add_field_to_item(new_field)

        # Refresh table and emit signal
        self.refresh()
        self.field_changed.emit()

    def _insert_field(self, position='after'):
        """Insert a new bit field before or after the selected row."""
        if not self.current_item:
            return

        current_row = self.table.currentRow()
        if current_row < 0:
            # No selection, fall back to add at end
            self._add_field()
            return

        # Get the field name from the selected row
        field_name_item = self.table.item(current_row, 0)
        if not field_name_item:
            self._add_field()
            return

        selected_field_name = field_name_item.text()

        # Get current fields sorted by offset
        fields_list = BitFieldOperations.get_sorted_fields(self.current_item)
        if not fields_list:
            self._add_field()
            return

        # Find the selected field
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
        new_field_name = BitFieldOperations.generate_unique_field_name(self.current_item)

        # Determine insertion strategy
        if position == 'before':
            if selected_index == 0:
                # Insert at the very beginning
                new_field = BitField(new_field_name, 0, 1, "rw", "New field", reset_value=0)
                self._add_field_to_item(new_field)

                # Shift all other fields by 1 offset
                for field in fields_list:
                    field.offset += 1

                BitFieldOperations.update_item_fields(self.current_item, fields_list + [new_field])
            else:
                # Insert between previous and current field
                prev_field = fields_list[selected_index - 1]
                insert_offset = prev_field.offset + prev_field.width
                new_field = BitField(new_field_name, insert_offset, 1, "rw", "New field", reset_value=0)
                self._add_field_to_item(new_field)

                # Shift subsequent fields
                for i in range(selected_index, len(fields_list)):
                    fields_list[i].offset += 1

                BitFieldOperations.update_item_fields(self.current_item, fields_list + [new_field])
        else:  # after
            insert_offset = selected_field.offset + selected_field.width
            new_field = BitField(new_field_name, insert_offset, 1, "rw", "New field", reset_value=0)
            self._add_field_to_item(new_field)

            # Shift subsequent fields
            for i in range(selected_index + 1, len(fields_list)):
                fields_list[i].offset += 1

            BitFieldOperations.update_item_fields(self.current_item, fields_list + [new_field])

        # Validate that all fields still fit within 32 bits
        all_fields = BitFieldOperations.get_sorted_fields(self.current_item)
        for field in all_fields:
            if field.offset + field.width > 32:
                QMessageBox.warning(self, "Cannot Insert Field",
                                  f"Inserting field would cause '{field.name}' to extend beyond bit 31.")
                self.refresh()
                return

        # Refresh table and emit signal
        self.refresh()
        self.field_changed.emit()

    def _remove_field(self):
        """Remove the selected bit field and recalculate offsets."""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        # Get field name
        field_name_item = self.table.item(current_row, 0)
        if not field_name_item:
            return

        field_name = field_name_item.text()

        # Remove from current item
        if isinstance(self.current_item, Register):
            if field_name in self.current_item._fields:
                del self.current_item._fields[field_name]
        elif isinstance(self.current_item, RegisterArrayAccessor):
            self.current_item._field_template = [
                f for f in self.current_item._field_template if f.name != field_name
            ]

        # Recalculate offsets to close gaps
        BitFieldOperations.recalculate_offsets(self.current_item)

        # Refresh table
        self.refresh()
        self.field_changed.emit()

    def _move_field_up(self):
        """Move the selected bit field up in the list."""
        self._move_field(-1)

    def _move_field_down(self):
        """Move the selected bit field down in the list."""
        self._move_field(1)

    def _move_field(self, direction):
        """Move the selected bit field up (-1) or down (1)."""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        # Get the selected field name
        field_name_item = self.table.item(current_row, 0)
        if not field_name_item:
            return
        selected_field_name = field_name_item.text()

        # Get all bit fields sorted by offset
        fields_list = BitFieldOperations.get_sorted_fields(self.current_item)
        if len(fields_list) < 2:
            return

        # Find the selected field
        selected_field = None
        selected_index = -1
        for i, field in enumerate(fields_list):
            if field.name == selected_field_name:
                selected_field = field
                selected_index = i
                break

        if selected_field is None:
            return

        new_index = selected_index + direction

        # Check bounds
        if new_index < 0 or new_index >= len(fields_list):
            return

        # Remove and reinsert at new position
        fields_list.pop(selected_index)
        fields_list.insert(new_index, selected_field)

        # Recalculate offsets for the reordered fields
        current_offset = 0
        for field in fields_list:
            field.offset = current_offset
            current_offset += field.width

        # Update the item with the new field order
        BitFieldOperations.update_item_fields(self.current_item, fields_list)

        # Refresh and maintain selection
        self.refresh()

        # Select the moved field at its new position
        for row in range(self.table.rowCount()):
            field_name_item = self.table.item(row, 0)
            if field_name_item and field_name_item.text() == selected_field.name:
                self.table.selectRow(row)
                break

        self.field_changed.emit()

    def _recalculate_offsets(self):
        """Recalculate field offsets to pack them sequentially."""
        if not self.current_item:
            return

        BitFieldOperations.recalculate_offsets(self.current_item)
        self.refresh()
        self.field_changed.emit()

    def _on_cell_changed(self, row, column):
        """Handle changes to table cells with validation."""
        if self._updating:
            return

        # Get the field being edited
        field_name_item = self.table.item(row, 0)
        if not field_name_item:
            return

        fields_list = BitFieldOperations.get_sorted_fields(self.current_item)
        current_table_name = field_name_item.text()

        # Find the field
        if column == 0:
            # For name changes, use row index
            if row >= len(fields_list):
                return
            field = fields_list[row]
        else:
            # For other columns, find by name
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
                self._handle_name_change(row, field, fields_list, current_table_name)
            elif column == 1:  # Bits
                self._handle_bits_change(row, field)
            elif column == 2:  # Width
                self._handle_width_change(row, field)
            elif column == 3:  # Access
                self._handle_access_change(row, field)
            elif column == 4:  # Reset value
                self._handle_reset_value_change(row, field)
            elif column == 5:  # Live value
                self._handle_live_value_change(row, field)
            elif column == 6:  # Description
                self._handle_description_change(row, field)

            # Refresh display and emit signal
            if column in [1, 2]:  # Bits or Width changed
                self.refresh()

            self.field_changed.emit()

            # Ensure fields are synchronized
            fields_list = BitFieldOperations.get_sorted_fields(self.current_item)
            BitFieldOperations.update_item_fields(self.current_item, fields_list)

        except Exception as e:
            QMessageBox.warning(self, "Edit Error", f"Error updating field: {str(e)}")
            self.refresh()

    def _handle_name_change(self, row, field, fields_list, new_name):
        """Handle name column changes."""
        new_name = new_name.strip()
        if new_name and new_name != field.name:
            # Check for duplicates
            existing_names = set(f.name for f in fields_list if f != field)
            if new_name in existing_names:
                QMessageBox.warning(self, "Duplicate Name",
                                   f"Field name '{new_name}' already exists.")
                self.refresh()
                return

            # Update field name
            old_name = field.name
            field.name = new_name

            # Update in the item's fields dictionary
            if isinstance(self.current_item, Register):
                if old_name in self.current_item._fields:
                    del self.current_item._fields[old_name]
                self.current_item._fields[new_name] = field

    def _handle_bits_change(self, row, field):
        """Handle bits column changes (bit range like [7:0] or [5])."""
        bits_item = self.table.item(row, 1)
        if not bits_item:
            return

        try:
            bits_text = bits_item.text().strip()

            # Parse bit range
            if not (bits_text.startswith('[') and bits_text.endswith(']')):
                raise ValueError("Bit range must be in format [high:low] or [bit]")

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

            # Create temporary field for validation
            temp_field = BitField(field.name, new_offset, new_width, field.access, field.description)
            is_valid, error_msg = BitFieldOperations.validate_field_fits(
                self.current_item, temp_field, exclude_field=field
            )

            if not is_valid:
                # Offer to recalculate
                reply = QMessageBox.question(
                    self,
                    "Field Overlap Detected",
                    f"{error_msg}\n\nWould you like to automatically recalculate other field offsets?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )

                if reply == QMessageBox.Yes:
                    field.offset = new_offset
                    field.width = new_width
                    BitFieldOperations.recalculate_offsets_preserving_field(
                        self.current_item, field
                    )

                    # Validate final result
                    final_fields = BitFieldOperations.get_sorted_fields(self.current_item)
                    max_bit = max(f.offset + f.width for f in final_fields) if final_fields else 0

                    if max_bit > 32:
                        self.refresh()
                        QMessageBox.warning(
                            self,
                            "Cannot Fit Fields",
                            "Cannot fit all fields within 32-bit register."
                        )
                        return
                else:
                    self.refresh()
                    return
            else:
                field.offset = new_offset
                field.width = new_width

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Bit Range", str(e))
            self.refresh()

    def _handle_width_change(self, row, field):
        """Handle width column changes."""
        width_item = self.table.item(row, 2)
        if not width_item:
            return

        try:
            new_width = int(width_item.text())
            old_width = field.width

            # Create temporary field for validation
            temp_field = BitField(field.name, field.offset, new_width, field.access, field.description)
            is_valid, error_msg = BitFieldOperations.validate_field_fits(
                self.current_item, temp_field, exclude_field=field
            )

            if not is_valid:
                # Offer to recalculate
                reply = QMessageBox.question(
                    self,
                    "Field Overlap Detected",
                    f"{error_msg}\n\nRecalculate all field offsets?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )

                if reply == QMessageBox.Yes:
                    field.width = new_width
                    BitFieldOperations.recalculate_offsets(self.current_item)

                    # Check if recalculation resolved the issue
                    final_fields = BitFieldOperations.get_sorted_fields(self.current_item)
                    max_bit = max(f.offset + f.width for f in final_fields) if final_fields else 0

                    if max_bit > 32:
                        field.width = old_width
                        BitFieldOperations.recalculate_offsets(self.current_item)
                        QMessageBox.warning(
                            self,
                            "Cannot Fit Fields",
                            f"Fields would extend to bit {max_bit-1}, exceeding 32-bit limit."
                        )
                        self.refresh()
                        return
                else:
                    self.refresh()
                    return
            else:
                field.width = new_width

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Width", str(e))
            self.refresh()

    def _handle_access_change(self, row, field):
        """Handle access type column changes."""
        access_item = self.table.item(row, 3)
        if not access_item:
            return

        new_access = access_item.text().lower().strip()
        valid_access = ['ro', 'wo', 'rw', 'rw1c']
        if new_access not in valid_access:
            QMessageBox.warning(self, "Invalid Access Type",
                               f"Access type must be one of: {', '.join(valid_access)}")
            self.refresh()
            return
        field.access = new_access

    def _handle_reset_value_change(self, row, field):
        """Handle reset value column changes."""
        reset_item = self.table.item(row, 4)
        if not reset_item:
            return

        try:
            reset_text = reset_item.text().strip()
            if reset_text == "" or reset_text.lower() == "none":
                field.reset_value = None
            else:
                new_reset = int(reset_text, 0)  # Support hex/decimal
                max_value = (1 << field.width) - 1
                if new_reset < 0 or new_reset > max_value:
                    QMessageBox.warning(self, "Invalid Reset Value",
                                       f"Reset value must be between 0 and {max_value} for a {field.width}-bit field.")
                    self.refresh()
                    return
                field.reset_value = new_reset

        except ValueError:
            QMessageBox.warning(self, "Invalid Reset Value", "Reset value must be a valid integer.")
            self.refresh()

    def _handle_live_value_change(self, row, field):
        """Handle live value column changes."""
        live_item = self.table.item(row, 5)
        if not live_item or not isinstance(self.current_item, Register):
            return

        reg_name = self.current_item.name
        current_set = debug_manager.get_current_debug_set()
        if current_set is None:
            current_set = debug_manager.create_debug_set("default")

        raw_text = live_item.text().strip()
        if raw_text == "":
            # Clear field debug value
            field_debugs = current_set.field_values.get(reg_name, {})
            if field.name in field_debugs:
                del field_debugs[field.name]

            # Recompute composed register value
            composed = debug_manager.calculate_register_value_from_fields(
                reg_name, self.current_item
            )
            if composed is not None:
                current_set.set_register_value(reg_name, DebugValue(composed))
            self.refresh()
        else:
            try:
                dbg_val = DebugValue.from_string(raw_text)
                max_field_val = (1 << field.width) - 1
                if dbg_val.value is None or dbg_val.value < 0 or dbg_val.value > max_field_val:
                    raise ValueError(f"Value must be 0..{max_field_val} for a {field.width}-bit field")

                current_set.set_field_value(reg_name, field.name, dbg_val)

                # Recalculate whole register value
                composed = debug_manager.calculate_register_value_from_fields(
                    reg_name, self.current_item
                )
                if composed is not None:
                    current_set.set_register_value(reg_name, DebugValue(composed))

                self.refresh()
            except ValueError as ve:
                QMessageBox.warning(self, "Invalid Live Field Value", str(ve))
                self.refresh()

    def _handle_description_change(self, row, field):
        """Handle description column changes."""
        desc_item = self.table.item(row, 6)
        if desc_item:
            field.description = desc_item.text()

    def _on_selection_changed(self):
        """Handle table selection changes."""
        current_row = self.table.currentRow()
        has_selection = current_row >= 0

        self.insert_before_btn.setEnabled(has_selection)
        self.insert_after_btn.setEnabled(has_selection)
        self.remove_field_btn.setEnabled(has_selection)

        # Enable move buttons based on position
        if has_selection:
            row_count = self.table.rowCount()
            self.move_field_up_btn.setEnabled(current_row > 0)
            self.move_field_down_btn.setEnabled(current_row < row_count - 1)
        else:
            self.move_field_up_btn.setEnabled(False)
            self.move_field_down_btn.setEnabled(False)

    def _add_field_to_item(self, new_field):
        """Add a field to the current item."""
        if isinstance(self.current_item, Register):
            self.current_item._fields[new_field.name] = new_field
        elif isinstance(self.current_item, RegisterArrayAccessor):
            self.current_item._field_template.append(new_field)

    def set_enabled(self, enabled: bool):
        """Enable or disable the widget."""
        self.setEnabled(enabled)
        if not enabled:
            self.move_field_up_btn.setEnabled(False)
            self.move_field_down_btn.setEnabled(False)

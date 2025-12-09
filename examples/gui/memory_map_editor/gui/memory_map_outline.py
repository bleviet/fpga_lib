"""
Memory Map Outline - Tree/List View Component

Displays the hierarchical structure of registers and register arrays.
Allows navigation and selection of memory map items.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QShortcut, QKeySequence, QColor, QBrush

from memory_map_core import MemoryMapProject
from fpga_lib.core import Register, RegisterArrayAccessor


class MemoryMapOutline(QWidget):
    """
    Tree widget showing the memory map structure.

    Displays registers and register arrays in a hierarchical view
    with address information and descriptions.
    """

    # Signals
    current_item_changed = Signal(object)  # Emits Register or RegisterArrayAccessor

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_project = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("Memory Map")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Expand/Collapse all buttons for arrays
        self.expand_all_btn = QPushButton("▼ Expand All")
        self.expand_all_btn.setToolTip("Expand All Register Arrays")
        self.expand_all_btn.setMaximumWidth(90)
        header_layout.addWidget(self.expand_all_btn)

        self.collapse_all_btn = QPushButton("▶ Collapse All")
        self.collapse_all_btn.setToolTip("Collapse All Register Arrays")
        self.collapse_all_btn.setMaximumWidth(90)
        header_layout.addWidget(self.collapse_all_btn)

        # Register insertion buttons
        self.insert_register_before_btn = QPushButton("Reg ↑")
        self.insert_register_before_btn.setToolTip("Insert Register Before Selected")
        self.insert_register_before_btn.setMaximumWidth(60)
        header_layout.addWidget(self.insert_register_before_btn)

        self.insert_register_after_btn = QPushButton("Reg ↓")
        self.insert_register_after_btn.setToolTip("Insert Register After Selected")
        self.insert_register_after_btn.setMaximumWidth(60)
        header_layout.addWidget(self.insert_register_after_btn)

        # Array insertion buttons
        self.insert_array_before_btn = QPushButton("Array ↑")
        self.insert_array_before_btn.setToolTip("Insert Array Before Selected")
        self.insert_array_before_btn.setMaximumWidth(70)
        header_layout.addWidget(self.insert_array_before_btn)

        self.insert_array_after_btn = QPushButton("Array ↓")
        self.insert_array_after_btn.setToolTip("Insert Array After Selected")
        self.insert_array_after_btn.setMaximumWidth(70)
        header_layout.addWidget(self.insert_array_after_btn)

        # Remove button
        self.remove_register_btn = QPushButton("✗ Remove")
        self.remove_register_btn.setToolTip("Remove Selected Register")
        self.remove_register_btn.setMaximumWidth(70)
        header_layout.addWidget(self.remove_register_btn)

        # Move up/down buttons for reordering
        self.move_up_btn = QPushButton("⬆ Up")
        self.move_up_btn.setToolTip("Move Selected Register Up (Alt+Up)")
        self.move_up_btn.setMaximumWidth(60)
        header_layout.addWidget(self.move_up_btn)

        self.move_down_btn = QPushButton("⬇ Down")
        self.move_down_btn.setToolTip("Move Selected Register Down (Alt+Down)")
        self.move_down_btn.setMaximumWidth(60)
        header_layout.addWidget(self.move_down_btn)

        layout.addLayout(header_layout)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Address", "Type"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)  # Enable expand/collapse arrows
        layout.addWidget(self.tree)

        # Track expansion state of arrays
        self._expanded_arrays = set()  # Store names of expanded arrays

        # Set column widths
        from PySide6.QtWidgets import QHeaderView
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Name - fit to content
        self.tree.setColumnWidth(1, 150)  # Address - wider for ranges
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Type - fit to content

        # Initially disable register management buttons (no selection)
        self._update_button_states(False)

    def _update_button_states(self, has_selection):
        """Update the enabled state of register management buttons."""
        # Insert buttons are always enabled (will add at start/end if no selection)
        self.insert_register_before_btn.setEnabled(True)
        self.insert_register_after_btn.setEnabled(True)
        self.insert_array_before_btn.setEnabled(True)
        self.insert_array_after_btn.setEnabled(True)

        # Remove and move buttons only enabled when something is selected
        self.remove_register_btn.setEnabled(has_selection)

        # Move buttons enabled based on selection and position
        if has_selection and self.tree.topLevelItemCount() > 1:
            current_index = self.tree.indexOfTopLevelItem(self.tree.currentItem())
            self.move_up_btn.setEnabled(current_index > 0)
            self.move_down_btn.setEnabled(current_index < self.tree.topLevelItemCount() - 1)
        else:
            self.move_up_btn.setEnabled(False)
            self.move_down_btn.setEnabled(False)

    def _connect_signals(self):
        """Connect internal signals."""
        self.tree.currentItemChanged.connect(self._on_selection_changed)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemCollapsed.connect(self._on_item_collapsed)

        # Expand/collapse all buttons
        self.expand_all_btn.clicked.connect(self._expand_all_arrays)
        self.collapse_all_btn.clicked.connect(self._collapse_all_arrays)

        self.insert_register_before_btn.clicked.connect(self._insert_register_before_clicked)
        self.insert_register_after_btn.clicked.connect(self._insert_register_after_clicked)
        self.insert_array_before_btn.clicked.connect(self._insert_array_before_clicked)
        self.insert_array_after_btn.clicked.connect(self._insert_array_after_clicked)
        self.remove_register_btn.clicked.connect(self._remove_register_clicked)

        # Move up/down button connections
        self.move_up_btn.clicked.connect(self._move_up_clicked)
        self.move_down_btn.clicked.connect(self._move_down_clicked)

        # Keyboard shortcuts for move up/down - widget-specific context
        self.move_up_shortcut = QShortcut(QKeySequence("Alt+Up"), self.tree)
        self.move_up_shortcut.setContext(Qt.WidgetShortcut)
        self.move_up_shortcut.activated.connect(self._move_up_clicked)

        self.move_down_shortcut = QShortcut(QKeySequence("Alt+Down"), self.tree)
        self.move_down_shortcut.setContext(Qt.WidgetShortcut)
        self.move_down_shortcut.activated.connect(self._move_down_clicked)

    def set_project(self, project: MemoryMapProject):
        """Set the current project and populate the tree."""
        self.current_project = project
        self.refresh()

    def refresh(self):
        """Refresh the tree view with current project data."""
        # Remember the currently selected item before clearing
        current_selection = self.get_selected_item()

        self.tree.clear()

        if not self.current_project:
            return

        # Group registers by array parent (for nested arrays like DESCRIPTOR[0].SRC_ADDR)
        nested_array_groups = {}  # {array_name: {index: [registers]}}
        standalone_registers = []

        for register in self.current_project.registers:
            if hasattr(register, '_array_parent'):
                # This is part of a nested array
                array_name = register._array_parent
                index = register._array_index

                if array_name not in nested_array_groups:
                    nested_array_groups[array_name] = {
                        'registers': {},
                        'base': register._array_base,
                        'count': register._array_count,
                        'stride': register._array_stride
                    }

                if index not in nested_array_groups[array_name]['registers']:
                    nested_array_groups[array_name]['registers'][index] = []

                nested_array_groups[array_name]['registers'][index].append(register)
            else:
                # Standalone register
                standalone_registers.append(register)

        # Add standalone registers
        for register in sorted(standalone_registers, key=lambda r: r.offset):
            item = QTreeWidgetItem([
                register.name,
                f"0x{register.offset:04X}",
                "Register"
            ])
            item.setData(0, Qt.UserRole, register)
            self.tree.addTopLevelItem(item)

        # Add nested array groups
        for array_name, array_data in sorted(nested_array_groups.items(), key=lambda x: x[1]['base']):
            count = array_data['count']
            stride = array_data['stride']
            base = array_data['base']
            end_addr = base + (count * stride) - 1

            # Create parent array item
            parent_item = QTreeWidgetItem([
                array_name,
                f"0x{base:04X}-0x{end_addr:04X}",
                f"Array[{count}]"
            ])

            # Make array parent bold
            for col in range(3):
                font = parent_item.font(col)
                font.setBold(True)
                parent_item.setFont(col, font)

            # Add child items for each array element
            for idx in sorted(array_data['registers'].keys()):
                registers = array_data['registers'][idx]
                element_offset = base + (idx * stride)

                # Create array element node
                element_item = QTreeWidgetItem([
                    f"{array_name}[{idx}]",
                    f"0x{element_offset:04X}",
                    "Element"
                ])

                # Style array elements (gray, italic)
                gray_brush = QBrush(QColor(100, 100, 100))
                for col in range(3):
                    element_item.setForeground(col, gray_brush)
                    font = element_item.font(col)
                    font.setItalic(True)
                    element_item.setFont(col, font)

                # Add sub-registers as children of the element
                for reg in sorted(registers, key=lambda r: r.offset):
                    # Extract sub-register name (e.g., "SRC_ADDR" from "DESCRIPTOR[0].SRC_ADDR")
                    sub_name = reg.name.split('.')[-1] if '.' in reg.name else reg.name

                    sub_item = QTreeWidgetItem([
                        sub_name,
                        f"0x{reg.offset:04X}",
                        "Register"
                    ])
                    sub_item.setData(0, Qt.UserRole, reg)

                    # Make sub-registers even lighter gray
                    lighter_gray = QBrush(QColor(120, 120, 120))
                    for col in range(3):
                        sub_item.setForeground(col, lighter_gray)

                    element_item.addChild(sub_item)

                # Store the first register as UserRole data for the element (for compatibility)
                element_item.setData(0, Qt.UserRole, registers[0] if registers else None)
                parent_item.addChild(element_item)

            self.tree.addTopLevelItem(parent_item)

            # Restore expansion state
            if array_name in self._expanded_arrays:
                parent_item.setExpanded(True)
            else:
                parent_item.setExpanded(False)

        # Add register arrays (sorted by base offset for logical display order)
        sorted_arrays = sorted(self.current_project.register_arrays, key=lambda a: a._base_offset)
        for array in sorted_arrays:
            end_addr = array._base_offset + (array._count * array._stride) - 1
            item = QTreeWidgetItem([
                array._name,
                f"0x{array._base_offset:04X}-0x{end_addr:04X}",
                f"Array[{array._count}]"
            ])
            item.setData(0, Qt.UserRole, array)

            # Make array parent items bold to distinguish from registers
            for col in range(3):
                font = item.font(col)
                font.setBold(True)
                item.setFont(col, font)

            # Add child items for each array element
            for i in range(array._count):
                element_offset = array._base_offset + (i * array._stride)
                element_accessor = array[i]  # Get RegisterArrayAccessor for this element
                child_item = QTreeWidgetItem([
                    f"{array._name}[{i}]",
                    f"0x{element_offset:04X}",
                    "Element"
                ])
                child_item.setData(0, Qt.UserRole, element_accessor)
                child_item.setData(0, Qt.UserRole + 1, i)  # Store index
                child_item.setData(0, Qt.UserRole + 2, array)  # Store parent array

                # Style array elements differently (subtle gray, italic)
                gray_brush = QBrush(QColor(100, 100, 100))
                for col in range(3):
                    child_item.setForeground(col, gray_brush)
                    font = child_item.font(col)
                    font.setItalic(True)
                    child_item.setFont(col, font)

                item.addChild(child_item)

            self.tree.addTopLevelItem(item)

            # Restore expansion state
            if array._name in self._expanded_arrays:
                item.setExpanded(True)
            else:
                item.setExpanded(False)  # Collapsed by default

        # Sort by address (this will mix registers and arrays by address)
        self.tree.sortItems(1, Qt.AscendingOrder)

        # Try to restore the previous selection, otherwise select first item
        if current_selection and self.tree.topLevelItemCount() > 0:
            # Try to find and select the previously selected item
            selection_restored = False
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                if item.data(0, Qt.UserRole) == current_selection:
                    self.tree.setCurrentItem(item)
                    selection_restored = True
                    break

            # If we couldn't restore selection, select first item
            if not selection_restored:
                self.tree.setCurrentItem(self.tree.topLevelItem(0))
        elif self.tree.topLevelItemCount() > 0:
            # No previous selection, select first item
            self.tree.setCurrentItem(self.tree.topLevelItem(0))

    def select_item(self, memory_item):
        """Select a specific register or array in the tree."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == memory_item:
                self.tree.setCurrentItem(item)
                return

            # Check child items (array elements)
            for j in range(item.childCount()):
                child = item.child(j)
                if child.data(0, Qt.UserRole) == memory_item:
                    item.setExpanded(True)  # Expand parent if selecting child
                    self.tree.setCurrentItem(child)
                    return

    def get_selected_item(self):
        """Get the currently selected memory map item."""
        current = self.tree.currentItem()
        if current:
            return current.data(0, Qt.UserRole)
        return None

    def _on_selection_changed(self, current, previous):
        """Handle tree selection changes."""
        if current:
            memory_item = current.data(0, Qt.UserRole)
            self.current_item_changed.emit(memory_item)
            # Enable register management buttons when an item is selected
            self._update_button_states(True)
        else:
            self.current_item_changed.emit(None)
            # Disable register management buttons when no item is selected
            self._update_button_states(False)

    def _insert_register_before_clicked(self):
        """Handle insert register before button click."""
        selected_item = self.get_selected_item()
        parent = self.parent()
        while parent and not hasattr(parent, 'insert_register_before'):
            parent = parent.parent()
        if parent:
            if selected_item:
                parent.insert_register_before(selected_item)
            else:
                # No selection - add at beginning
                parent.add_register()

    def _insert_register_after_clicked(self):
        """Handle insert register after button click."""
        selected_item = self.get_selected_item()
        parent = self.parent()
        while parent and not hasattr(parent, 'insert_register_after'):
            parent = parent.parent()
        if parent:
            if selected_item:
                parent.insert_register_after(selected_item)
            else:
                # No selection - add at end
                parent.add_register()

    def _insert_array_before_clicked(self):
        """Handle insert array before button click."""
        selected_item = self.get_selected_item()
        parent = self.parent()
        while parent and not hasattr(parent, 'insert_array_before'):
            parent = parent.parent()
        if parent:
            if selected_item:
                parent.insert_array_before(selected_item)
            else:
                # No selection - add at beginning
                parent.add_register_array()

    def _insert_array_after_clicked(self):
        """Handle insert array after button click."""
        selected_item = self.get_selected_item()
        parent = self.parent()
        while parent and not hasattr(parent, 'insert_array_after'):
            parent = parent.parent()
        if parent:
            if selected_item:
                parent.insert_array_after(selected_item)
            else:
                # No selection - add at end
                parent.add_register_array()

    def _remove_register_clicked(self):
        """Handle remove register button click."""
        selected_item = self.get_selected_item()
        if selected_item:
            parent = self.parent()
            while parent and not hasattr(parent, 'remove_register'):
                parent = parent.parent()
            if parent:
                parent.remove_register(selected_item)

    def _move_up_clicked(self):
        """Handle move up button click."""
        self._move_register(-1)

    def _move_down_clicked(self):
        """Handle move down button click."""
        self._move_register(1)

    def _move_register(self, direction):
        """
        Move the selected register or array up or down in the list.

        Args:
            direction: -1 for up, 1 for down
        """
        selected_item = self.get_selected_item()
        if not selected_item or not self.current_project:
            return

        # Find the parent main window to access project manipulation methods
        parent = self.parent()
        while parent and not hasattr(parent, 'current_project'):
            parent = parent.parent()
        if not parent:
            return

        # Get all memory map items (registers and arrays) sorted by their base address
        all_items = []

        # Add registers
        for reg in self.current_project.registers:
            all_items.append(('register', reg, reg.offset, 4))  # registers are 4 bytes

        # Add register arrays
        for array in self.current_project.register_arrays:
            array_size = array._count * array._stride
            all_items.append(('array', array, array._base_offset, array_size))

        # Sort by address
        all_items.sort(key=lambda x: x[2])

        # Find the selected item in the list
        selected_index = -1
        for i, (item_type, item, address, size) in enumerate(all_items):
            if item == selected_item:
                selected_index = i
                break

        if selected_index == -1:
            return  # Selected item not found

        # Calculate new position
        new_index = selected_index + direction
        if new_index < 0 or new_index >= len(all_items):
            return  # Can't move beyond bounds

        # Reorder the items list by moving the selected item
        moved_item = all_items.pop(selected_index)
        all_items.insert(new_index, moved_item)

        # Recalculate all addresses from 0, placing items sequentially with no gaps
        current_address = 0
        for item_type, item, old_address, size in all_items:
            if item_type == 'register':
                item.offset = current_address
            else:  # array
                item._base_offset = current_address
            current_address += size

        # Refresh the view to show new order
        self.refresh()

        # Maintain selection on the moved item
        self.select_item(selected_item)

        # Emit project changed signal to update other views
        if hasattr(parent, 'project_changed'):
            parent.project_changed.emit()

    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Track when an array is expanded."""
        array = item.data(0, Qt.UserRole)
        if hasattr(array, '_name'):  # It's a register array
            self._expanded_arrays.add(array._name)

    def _on_item_collapsed(self, item: QTreeWidgetItem):
        """Track when an array is collapsed."""
        array = item.data(0, Qt.UserRole)
        if hasattr(array, '_name'):  # It's a register array
            self._expanded_arrays.discard(array._name)

    def _expand_all_arrays(self):
        """Expand all register arrays in the tree."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.childCount() > 0:  # It's an array with children
                item.setExpanded(True)
                array = item.data(0, Qt.UserRole)
                if hasattr(array, '_name'):
                    self._expanded_arrays.add(array._name)

    def _collapse_all_arrays(self):
        """Collapse all register arrays in the tree."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.childCount() > 0:  # It's an array with children
                item.setExpanded(False)
                array = item.data(0, Qt.UserRole)
                if hasattr(array, '_name'):
                    self._expanded_arrays.discard(array._name)

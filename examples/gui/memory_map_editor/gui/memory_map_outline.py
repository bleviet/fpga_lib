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
from PySide6.QtGui import QFont

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

        layout.addLayout(header_layout)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Address", "Type"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)
        layout.addWidget(self.tree)

        # Set column widths
        self.tree.setColumnWidth(0, 150)
        self.tree.setColumnWidth(1, 80)
        self.tree.setColumnWidth(2, 70)

        # Initially disable register management buttons (no selection)
        self._update_button_states(False)

    def _update_button_states(self, has_selection):
        """Update the enabled state of register management buttons."""
        # Insert buttons are always enabled (will add at start/end if no selection)
        self.insert_register_before_btn.setEnabled(True)
        self.insert_register_after_btn.setEnabled(True)
        self.insert_array_before_btn.setEnabled(True)
        self.insert_array_after_btn.setEnabled(True)

        # Remove button only enabled when something is selected
        self.remove_register_btn.setEnabled(has_selection)

    def _connect_signals(self):
        """Connect internal signals."""
        self.tree.currentItemChanged.connect(self._on_selection_changed)
        self.insert_register_before_btn.clicked.connect(self._insert_register_before_clicked)
        self.insert_register_after_btn.clicked.connect(self._insert_register_after_clicked)
        self.insert_array_before_btn.clicked.connect(self._insert_array_before_clicked)
        self.insert_array_after_btn.clicked.connect(self._insert_array_after_clicked)
        self.remove_register_btn.clicked.connect(self._remove_register_clicked)

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

        # Add registers (sorted by offset for logical display order)
        sorted_registers = sorted(self.current_project.registers, key=lambda r: r.offset)
        for register in sorted_registers:
            item = QTreeWidgetItem([
                register.name,
                f"0x{register.offset:04X}",
                "Register"
            ])
            item.setData(0, Qt.UserRole, register)
            self.tree.addTopLevelItem(item)

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
            self.tree.addTopLevelItem(item)

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
                break

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

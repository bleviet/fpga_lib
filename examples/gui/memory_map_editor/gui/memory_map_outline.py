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
        
        # Add buttons
        self.add_register_btn = QPushButton("+ Reg")
        self.add_register_btn.setToolTip("Add Register")
        self.add_register_btn.setMaximumWidth(60)
        header_layout.addWidget(self.add_register_btn)
        
        self.add_array_btn = QPushButton("+ Array")
        self.add_array_btn.setToolTip("Add Register Array")
        self.add_array_btn.setMaximumWidth(60)
        header_layout.addWidget(self.add_array_btn)
        
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
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.tree.currentItemChanged.connect(self._on_selection_changed)
        self.add_register_btn.clicked.connect(self._add_register_clicked)
        self.add_array_btn.clicked.connect(self._add_array_clicked)
    
    def set_project(self, project: MemoryMapProject):
        """Set the current project and populate the tree."""
        self.current_project = project
        self.refresh()
    
    def refresh(self):
        """Refresh the tree view with current project data."""
        self.tree.clear()
        
        if not self.current_project:
            return
        
        # Add registers
        for register in self.current_project.registers:
            item = QTreeWidgetItem([
                register.name,
                f"0x{register.offset:04X}",
                "Register"
            ])
            item.setData(0, Qt.UserRole, register)
            self.tree.addTopLevelItem(item)
        
        # Add register arrays
        for array in self.current_project.register_arrays:
            end_addr = array._base_offset + (array._count * array._stride) - 1
            item = QTreeWidgetItem([
                array._name,
                f"0x{array._base_offset:04X}-0x{end_addr:04X}",
                f"Array[{array._count}]"
            ])
            item.setData(0, Qt.UserRole, array)
            self.tree.addTopLevelItem(item)
        
        # Sort by address
        self.tree.sortItems(1, Qt.AscendingOrder)
        
        # Select first item if available
        if self.tree.topLevelItemCount() > 0:
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
        else:
            self.current_item_changed.emit(None)
    
    def _add_register_clicked(self):
        """Handle add register button click."""
        # Emit a signal that will be handled by the main window
        parent = self.parent()
        while parent and not hasattr(parent, 'add_register'):
            parent = parent.parent()
        if parent:
            parent.add_register()
    
    def _add_array_clicked(self):
        """Handle add array button click."""
        # Emit a signal that will be handled by the main window
        parent = self.parent()
        while parent and not hasattr(parent, 'add_register_array'):
            parent = parent.parent()
        if parent:
            parent.add_register_array()

"""
Main Window - Primary GUI Container

Implements the main application window with menu bar, toolbar, and layout.
Coordinates between different UI components.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QToolBar, QStatusBar, QMessageBox, QFileDialog,
    QLabel, QPushButton, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QKeySequence, QIcon
from pathlib import Path

from .memory_map_outline import MemoryMapOutline
from .register_detail_form import RegisterDetailForm
from .bit_field_visualizer import BitFieldVisualizer
from memory_map_core import MemoryMapProject, load_from_yaml, save_to_yaml, create_new_project
from fpga_lib.core import Register, RegisterArrayAccessor


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    project_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_project = None
        self.current_file_path = None
        
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()
        self._connect_signals()
        
        # Start with a new project
        self.new_project()
        
        # Window settings
        self.setWindowTitle("FPGA Memory Map Editor")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
    
    def _setup_ui(self):
        """Set up the main user interface layout."""
        # Central widget with splitter layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Left pane: Memory map outline
        self.outline = MemoryMapOutline()
        self.outline.setMinimumWidth(300)
        self.outline.setMaximumWidth(500)
        self.main_splitter.addWidget(self.outline)
        
        # Right pane: Detail view with vertical splitter
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Detail form and bit field visualizer
        self.detail_form = RegisterDetailForm()
        self.bit_visualizer = BitFieldVisualizer()
        
        # Right pane splitter
        self.right_splitter = QSplitter(Qt.Vertical)
        self.right_splitter.addWidget(self.detail_form)
        self.right_splitter.addWidget(self.bit_visualizer)
        self.right_splitter.setSizes([400, 300])
        
        right_layout.addWidget(self.right_splitter)
        self.main_splitter.addWidget(right_widget)
        
        # Set splitter proportions
        self.main_splitter.setSizes([350, 850])
    
    def _setup_menu_bar(self):
        """Set up the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # New project
        self.action_new = QAction("&New", self)
        self.action_new.setShortcut(QKeySequence.New)
        self.action_new.setStatusTip("Create a new memory map project")
        self.action_new.triggered.connect(self.new_project)
        file_menu.addAction(self.action_new)
        
        # Open project
        self.action_open = QAction("&Open...", self)
        self.action_open.setShortcut(QKeySequence.Open)
        self.action_open.setStatusTip("Open an existing memory map file")
        self.action_open.triggered.connect(self.open_project)
        file_menu.addAction(self.action_open)
        
        file_menu.addSeparator()
        
        # Save project
        self.action_save = QAction("&Save", self)
        self.action_save.setShortcut(QKeySequence.Save)
        self.action_save.setStatusTip("Save the current project")
        self.action_save.triggered.connect(self.save_project)
        file_menu.addAction(self.action_save)
        
        # Save as
        self.action_save_as = QAction("Save &As...", self)
        self.action_save_as.setShortcut(QKeySequence.SaveAs)
        self.action_save_as.setStatusTip("Save the project with a new name")
        self.action_save_as.triggered.connect(self.save_project_as)
        file_menu.addAction(self.action_save_as)
        
        file_menu.addSeparator()
        
        # Exit
        self.action_exit = QAction("E&xit", self)
        self.action_exit.setShortcut(QKeySequence.Quit)
        self.action_exit.setStatusTip("Exit the application")
        self.action_exit.triggered.connect(self.close)
        file_menu.addAction(self.action_exit)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Add register
        self.action_add_register = QAction("Add &Register", self)
        self.action_add_register.setStatusTip("Add a new register")
        self.action_add_register.triggered.connect(self.add_register)
        edit_menu.addAction(self.action_add_register)
        
        # Add register array
        self.action_add_array = QAction("Add Register &Array", self)
        self.action_add_array.setStatusTip("Add a new register array")
        self.action_add_array.triggered.connect(self.add_register_array)
        edit_menu.addAction(self.action_add_array)
        
        edit_menu.addSeparator()
        
        # Validate
        self.action_validate = QAction("&Validate Memory Map", self)
        self.action_validate.setShortcut(QKeySequence("Ctrl+R"))
        self.action_validate.setStatusTip("Check for errors and conflicts")
        self.action_validate.triggered.connect(self.validate_project)
        edit_menu.addAction(self.action_validate)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Refresh
        self.action_refresh = QAction("&Refresh", self)
        self.action_refresh.setShortcut(QKeySequence.Refresh)
        self.action_refresh.setStatusTip("Refresh the display")
        self.action_refresh.triggered.connect(self.refresh_views)
        view_menu.addAction(self.action_refresh)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About
        self.action_about = QAction("&About", self)
        self.action_about.setStatusTip("About this application")
        self.action_about.triggered.connect(self.show_about)
        help_menu.addAction(self.action_about)
    
    def _setup_toolbar(self):
        """Set up the main toolbar."""
        toolbar = self.addToolBar("Main")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        toolbar.addAction(self.action_new)
        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_save)
        toolbar.addSeparator()
        toolbar.addAction(self.action_add_register)
        toolbar.addAction(self.action_add_array)
        toolbar.addSeparator()
        toolbar.addAction(self.action_validate)
    
    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = self.statusBar()
        
        # Project info label
        self.project_info_label = QLabel("Ready")
        self.status_bar.addWidget(self.project_info_label)
        
        # Validation status
        self.validation_label = QLabel("")
        self.status_bar.addPermanentWidget(self.validation_label)
    
    def _connect_signals(self):
        """Connect signals between components."""
        # Outline selection changes
        self.outline.current_item_changed.connect(self.on_item_selected)
        
        # Detail form changes
        self.detail_form.register_changed.connect(self.on_register_changed)
        self.detail_form.field_changed.connect(self.on_field_changed)
        
        # Auto-validation timer
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self.auto_validate)
        
        # Project change notifications
        self.project_changed.connect(self.update_status)
    
    def new_project(self):
        """Create a new memory map project."""
        if self.check_unsaved_changes():
            self.current_project = create_new_project()
            self.current_file_path = None
            self.refresh_views()
            self.update_window_title()
            self.project_changed.emit()
    
    def open_project(self):
        """Open an existing memory map project."""
        if not self.check_unsaved_changes():
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Memory Map", 
            "", 
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        
        if file_path:
            try:
                self.current_project = load_from_yaml(file_path)
                self.current_file_path = Path(file_path)
                self.refresh_views()
                self.update_window_title()
                self.project_changed.emit()
                self.status_bar.showMessage(f"Opened: {file_path}", 3000)
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "Error Opening File", 
                    f"Failed to open file:\n{str(e)}"
                )
    
    def save_project(self):
        """Save the current project."""
        if self.current_file_path:
            self._save_to_file(self.current_file_path)
        else:
            self.save_project_as()
    
    def save_project_as(self):
        """Save the project with a new filename."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Memory Map As",
            "",
            "YAML Files (*.yaml);;All Files (*)"
        )
        
        if file_path:
            if not file_path.endswith('.yaml'):
                file_path += '.yaml'
            self._save_to_file(Path(file_path))
    
    def _save_to_file(self, file_path: Path):
        """Save project to specified file."""
        try:
            save_to_yaml(self.current_project, file_path)
            self.current_file_path = file_path
            self.update_window_title()
            self.status_bar.showMessage(f"Saved: {file_path}", 3000)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving File",
                f"Failed to save file:\n{str(e)}"
            )
    
    def add_register(self):
        """Add a new register to the project."""
        if self.current_project:
            # Find next available offset
            used_offsets = {reg.offset for reg in self.current_project.registers}
            next_offset = 0
            while next_offset in used_offsets:
                next_offset += 4
            
            register = self.current_project.add_register(
                f"register_{len(self.current_project.registers)}",
                next_offset,
                "New register"
            )
            
            self.refresh_views()
            self.outline.select_item(register)
            self.project_changed.emit()
    
    def add_register_array(self):
        """Add a new register array to the project."""
        if self.current_project:
            # Find next available offset block
            used_offsets = {reg.offset for reg in self.current_project.registers}
            for array in self.current_project.register_arrays:
                for i in range(array._count):
                    used_offsets.add(array._base_offset + i * array._stride)
            
            next_offset = 0x100  # Start arrays at higher addresses
            while next_offset in used_offsets:
                next_offset += 0x100
            
            array = self.current_project.add_register_array(
                f"array_{len(self.current_project.register_arrays)}",
                next_offset,
                8,  # Default count
                4   # Default stride
            )
            
            self.refresh_views()
            self.outline.select_item(array)
            self.project_changed.emit()
    
    def insert_register_before(self, reference_item):
        """Insert a new register before the reference item."""
        if not self.current_project:
            return
            
        if isinstance(reference_item, Register):
            # Insert before a regular register
            target_offset = max(0, reference_item.offset - 4)
        elif isinstance(reference_item, RegisterArrayAccessor):
            # Insert before a register array
            target_offset = max(0, reference_item._base_offset - 4)
        else:
            return
            
        # Find a free offset near the target
        used_offsets = {reg.offset for reg in self.current_project.registers}
        for array in self.current_project.register_arrays:
            for i in range(array._count):
                used_offsets.add(array._base_offset + i * array._stride)
        
        # Find the best available offset before the reference
        new_offset = target_offset
        while new_offset in used_offsets and new_offset >= 0:
            new_offset -= 4
        
        if new_offset < 0:
            # If no space before, use the next available after
            new_offset = target_offset + 4
            while new_offset in used_offsets:
                new_offset += 4
        
        register = self.current_project.add_register(
            f"register_{len(self.current_project.registers)}",
            new_offset,
            "New register (inserted before)"
        )
        
        self.refresh_views()
        self.outline.select_item(register)
        self.project_changed.emit()
    
    def insert_register_after(self, reference_item):
        """Insert a new register after the reference item."""
        if not self.current_project:
            return
            
        if isinstance(reference_item, Register):
            # Insert after a regular register
            target_offset = reference_item.offset + 4
        elif isinstance(reference_item, RegisterArrayAccessor):
            # Insert after a register array (after its last element)
            target_offset = reference_item._base_offset + (reference_item._count * reference_item._stride)
        else:
            return
            
        # Find a free offset near the target
        used_offsets = {reg.offset for reg in self.current_project.registers}
        for array in self.current_project.register_arrays:
            for i in range(array._count):
                used_offsets.add(array._base_offset + i * array._stride)
        
        # Find the best available offset after the reference
        new_offset = target_offset
        while new_offset in used_offsets:
            new_offset += 4
        
        register = self.current_project.add_register(
            f"register_{len(self.current_project.registers)}",
            new_offset,
            "New register (inserted after)"
        )
        
        self.refresh_views()
        self.outline.select_item(register)
        self.project_changed.emit()
    
    def remove_register(self, item_to_remove):
        """Remove a register or register array from the project."""
        if not self.current_project:
            return
            
        # Confirm removal
        from PySide6.QtWidgets import QMessageBox
        
        if isinstance(item_to_remove, Register):
            item_name = f"Register '{item_to_remove.name}'"
            reply = QMessageBox.question(
                self,
                "Confirm Removal",
                f"Are you sure you want to remove {item_name}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.current_project.registers.remove(item_to_remove)
                
        elif isinstance(item_to_remove, RegisterArrayAccessor):
            item_name = f"Register Array '{item_to_remove.name}'"
            reply = QMessageBox.question(
                self,
                "Confirm Removal",
                f"Are you sure you want to remove {item_name}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.current_project.register_arrays.remove(item_to_remove)
        else:
            return
        
        self.refresh_views()
        self.project_changed.emit()
    
    def validate_project(self):
        """Validate the current project and show results."""
        if not self.current_project:
            return
        
        errors = self.current_project.validate()
        
        if errors:
            error_text = "Validation Errors:\n\n" + "\n".join(f"• {error}" for error in errors)
            QMessageBox.warning(self, "Validation Results", error_text)
            self.validation_label.setText(f"❌ {len(errors)} errors")
        else:
            QMessageBox.information(self, "Validation Results", "✅ No errors found!")
            self.validation_label.setText("✅ Valid")
    
    def auto_validate(self):
        """Perform automatic validation in the background."""
        if self.current_project:
            errors = self.current_project.validate()
            if errors:
                self.validation_label.setText(f"❌ {len(errors)} errors")
            else:
                self.validation_label.setText("✅ Valid")
    
    def on_item_selected(self, item):
        """Handle selection change in the outline."""
        self.detail_form.set_current_item(item)
        self.bit_visualizer.set_current_item(item)
    
    def on_register_changed(self):
        """Handle register property changes."""
        self.outline.refresh()
        self.schedule_validation()
        self.project_changed.emit()
    
    def on_field_changed(self):
        """Handle bit field changes."""
        self.bit_visualizer.refresh()
        self.schedule_validation()
        self.project_changed.emit()
    
    def schedule_validation(self):
        """Schedule automatic validation."""
        self.validation_timer.start(1000)  # Validate after 1 second of inactivity
    
    def refresh_views(self):
        """Refresh all UI components."""
        if self.current_project:
            self.outline.set_project(self.current_project)
            self.detail_form.set_project(self.current_project)
            self.bit_visualizer.set_project(self.current_project)
            self.schedule_validation()
    
    def update_window_title(self):
        """Update the window title based on current project."""
        if self.current_project:
            project_name = self.current_project.name
            if self.current_file_path:
                title = f"{project_name} - {self.current_file_path.name} - Memory Map Editor"
            else:
                title = f"{project_name} - Memory Map Editor"
        else:
            title = "Memory Map Editor"
        
        self.setWindowTitle(title)
    
    def update_status(self):
        """Update status bar information."""
        if self.current_project:
            reg_count = len(self.current_project.registers)
            array_count = len(self.current_project.register_arrays)
            self.project_info_label.setText(
                f"Project: {self.current_project.name} | "
                f"Registers: {reg_count} | Arrays: {array_count}"
            )
        else:
            self.project_info_label.setText("No project loaded")
    
    def check_unsaved_changes(self) -> bool:
        """Check for unsaved changes and prompt user if needed."""
        # For now, always return True (proceed)
        # TODO: Implement proper change tracking
        return True
    
    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About Memory Map Editor",
            "<h3>FPGA Memory Map Editor</h3>"
            "<p>A visual editor for FPGA memory maps using Python/Qt.</p>"
            "<p>Integrates with fpga_lib.core register abstractions.</p>"
            "<p>Version 1.0.0</p>"
        )
    
    def closeEvent(self, event):
        """Handle application close event."""
        if self.check_unsaved_changes():
            event.accept()
        else:
            event.ignore()

"""
Main Window - Primary GUI Container

Implements the main application window with menu bar, toolbar, and layout.
Coordinates between different UI components.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QToolBar, QStatusBar, QMessageBox, QFileDialog,
    QLabel, QPushButton, QApplication, QSlider, QDialog, QDialogButtonBox,
    QFormLayout, QSpinBox, QComboBox, QStyle
)
from PySide6.QtCore import Qt, Signal, QTimer, QSettings, QSize
from PySide6.QtGui import QAction, QKeySequence, QIcon, QFont, QShortcut
from pathlib import Path

from .memory_map_outline import MemoryMapOutline
from .register_detail_form import RegisterDetailForm
from .bit_field_visualizer import BitFieldVisualizer
from memory_map_core import MemoryMapProject, load_from_yaml, save_to_yaml, create_new_project
from fpga_lib.runtime.register import Register, RegisterArrayAccessor


class ScalingDialog(QDialog):
    """Dialog for adjusting application text size and scaling."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Display Settings")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        # Font size adjustment
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setSuffix(" pt")
        current_font = QApplication.font()
        self.font_size_spin.setValue(current_font.pointSize())
        layout.addRow("Text Size:", self.font_size_spin)

        # UI scale factor
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["75%", "100%", "125%", "150%", "175%", "200%"])
        self.scale_combo.setCurrentText("100%")
        layout.addRow("UI Scale:", self.scale_combo)

        # Preview label
        self.preview_label = QLabel("Preview: The quick brown fox jumps over the lazy dog")
        self.preview_label.setWordWrap(True)
        layout.addRow("Preview:", self.preview_label)

        # Connect signals for live preview
        self.font_size_spin.valueChanged.connect(self._update_preview)
        self.scale_combo.currentTextChanged.connect(self._update_preview)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self._restore_defaults)
        layout.addRow(buttons)

        self._update_preview()

    def _update_preview(self):
        """Update the preview label with current settings."""
        font = QFont()
        font.setPointSize(self.font_size_spin.value())
        self.preview_label.setFont(font)

    def _restore_defaults(self):
        """Restore default settings."""
        self.font_size_spin.setValue(10)
        self.scale_combo.setCurrentText("100%")

    def get_font_size(self):
        """Get the selected font size."""
        return self.font_size_spin.value()

    def get_scale_factor(self):
        """Get the selected scale factor as a float."""
        scale_text = self.scale_combo.currentText().rstrip('%')
        return float(scale_text) / 100.0


class MainWindow(QMainWindow):
    """Main application window."""

    # Signals
    project_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_project = None
        self.current_file_path = None

        # Load saved settings
        self.settings = QSettings("FPGALib", "MemoryMapEditor")
        self._load_display_settings()

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

    def showEvent(self, event):
        """Handle window show event to set initial focus."""
        super().showEvent(event)
        # Set focus on the memory outline tree for vim-style navigation
        self.outline.tree.setFocus()
        self._update_panel_focus_style()

    def _focus_left_panel(self):
        """Switch focus to left panel (memory outline)."""
        self.outline.tree.setFocus()
        self._update_panel_focus_style()

    def _focus_right_panel(self):
        """Switch focus to right panel (bit field table)."""
        self.detail_form.bit_field_table.table.setFocus()
        self._update_panel_focus_style()

    def _on_outline_focus(self, event):
        """Handle focus event for outline panel."""
        from PySide6.QtWidgets import QTreeWidget
        QTreeWidget.focusInEvent(self.outline.tree, event)
        self._update_panel_focus_style()

    def _on_detail_focus(self, event):
        """Handle focus event for detail panel."""
        from PySide6.QtWidgets import QTableWidget
        QTableWidget.focusInEvent(self.detail_form.bit_field_table.table, event)
        self._update_panel_focus_style()

    def _update_panel_focus_style(self):
        """Update visual style to indicate which panel has focus."""
        outline_focused = self.outline.tree.hasFocus()
        detail_focused = self.detail_form.bit_field_table.table.hasFocus()

        # Apply focused style with blue border
        focused_style = """
            QTreeWidget:focus, QTableWidget:focus {
                border: 2px solid #4A90E2;
            }
            QTreeWidget, QTableWidget {
                border: 1px solid #CCCCCC;
            }
        """

        if outline_focused:
            self.outline.tree.setStyleSheet("""
                QTreeWidget {
                    border: 2px solid #4A90E2;
                }
            """)
            self.detail_form.bit_field_table.table.setStyleSheet("""
                QTableWidget {
                    border: 1px solid #CCCCCC;
                }
            """)
            self.status_bar.showMessage("Focus: Memory Map Outline", 1000)
        elif detail_focused:
            self.outline.tree.setStyleSheet("""
                QTreeWidget {
                    border: 1px solid #CCCCCC;
                }
            """)
            self.detail_form.bit_field_table.table.setStyleSheet("""
                QTableWidget {
                    border: 2px solid #4A90E2;
                }
            """)
            self.status_bar.showMessage("Focus: Bit Field Table", 1000)
        else:
            # No focus - reset both
            self.outline.tree.setStyleSheet("""
                QTreeWidget {
                    border: 1px solid #CCCCCC;
                }
            """)
            self.detail_form.bit_field_table.table.setStyleSheet("""
                QTableWidget {
                    border: 1px solid #CCCCCC;
                }
            """)

    def _load_display_settings(self):
        """Load and apply saved display settings."""
        # Load font size
        font_size = self.settings.value("display/font_size", 10, type=int)
        self._apply_font_size(font_size)

        # Load and apply scale factor
        scale_factor = self.settings.value("display/scale_factor", 1.0, type=float)
        self._apply_scale_factor(scale_factor)

    def _apply_font_size(self, font_size):
        """Apply font size to the application."""
        app_font = QApplication.font()
        app_font.setPointSize(font_size)
        QApplication.setFont(app_font)

    def _apply_scale_factor(self, scale_factor):
        """Apply scale factor to the application."""
        # Note: Scale factor changes require application restart to take full effect
        # We store it for the next launch
        pass

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

        # Right pane: Detail view (now includes bit visualizer internally)
        self.detail_form = RegisterDetailForm()
        self.main_splitter.addWidget(self.detail_form)

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

        # Validate
        self.action_validate = QAction("&Validate Memory Map", self)
        self.action_validate.setShortcut(QKeySequence("Ctrl+R"))
        self.action_validate.setStatusTip("Check for errors and conflicts")
        self.action_validate.triggered.connect(self.validate_project)
        self.action_validate.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        edit_menu.addAction(self.action_validate)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Refresh
        self.action_refresh = QAction("&Refresh", self)
        self.action_refresh.setShortcut(QKeySequence.Refresh)
        self.action_refresh.setStatusTip("Refresh the display")
        self.action_refresh.triggered.connect(self.refresh_views)
        view_menu.addAction(self.action_refresh)

        view_menu.addSeparator()

        # Zoom In
        self.action_zoom_in = QAction("Zoom &In", self)
        self.action_zoom_in.setShortcut(QKeySequence.ZoomIn)
        self.action_zoom_in.setStatusTip("Increase text size")
        self.action_zoom_in.triggered.connect(self.zoom_in)
        zoom_in_icon = QIcon.fromTheme("zoom-in")
        if zoom_in_icon.isNull():
            zoom_in_icon = self.style().standardIcon(QStyle.SP_FileDialogContentsView)
        self.action_zoom_in.setIcon(zoom_in_icon)
        view_menu.addAction(self.action_zoom_in)

        # Zoom Out
        self.action_zoom_out = QAction("Zoom &Out", self)
        self.action_zoom_out.setShortcut(QKeySequence.ZoomOut)
        self.action_zoom_out.setStatusTip("Decrease text size")
        self.action_zoom_out.triggered.connect(self.zoom_out)
        zoom_out_icon = QIcon.fromTheme("zoom-out")
        if zoom_out_icon.isNull():
            zoom_out_icon = self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        self.action_zoom_out.setIcon(zoom_out_icon)
        view_menu.addAction(self.action_zoom_out)

        # Reset Zoom
        self.action_zoom_reset = QAction("&Reset Zoom", self)
        self.action_zoom_reset.setShortcut(QKeySequence("Ctrl+0"))
        self.action_zoom_reset.setStatusTip("Reset text size to default")
        self.action_zoom_reset.triggered.connect(self.zoom_reset)
        self.action_zoom_reset.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        view_menu.addAction(self.action_zoom_reset)

        view_menu.addSeparator()

        # Display Settings
        self.action_display_settings = QAction("&Display Settings...", self)
        self.action_display_settings.setStatusTip("Adjust text size and UI scaling")
        self.action_display_settings.triggered.connect(self.show_display_settings)
        view_menu.addAction(self.action_display_settings)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # Keyboard Shortcuts
        self.action_shortcuts = QAction("&Keyboard Shortcuts", self)
        self.action_shortcuts.setShortcut(QKeySequence("F1"))
        self.action_shortcuts.setStatusTip("Show keyboard shortcuts")
        self.action_shortcuts.triggered.connect(self.show_keyboard_shortcuts)
        help_menu.addAction(self.action_shortcuts)

        help_menu.addSeparator()

        # About
        self.action_about = QAction("&About", self)
        self.action_about.setStatusTip("About this application")
        self.action_about.triggered.connect(self.show_about)
        help_menu.addAction(self.action_about)

    def _setup_toolbar(self):
        """Set up the main toolbar."""
        toolbar = self.addToolBar("Main")
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        toolbar.setIconSize(QSize(20, 20))

        toolbar.addAction(self.action_new)
        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_save)
        toolbar.addSeparator()

        toolbar.addAction(self.action_validate)

        toolbar.addSeparator()

        # Add zoom controls to toolbar
        toolbar.addAction(self.action_zoom_in)
        toolbar.addAction(self.action_zoom_out)
        toolbar.addAction(self.action_zoom_reset)

    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = self.statusBar()

        # Project info label
        self.project_info_label = QLabel("Ready")
        self.status_bar.addWidget(self.project_info_label)

        # Validation status
        self.validation_label = QLabel("")
        self.status_bar.addPermanentWidget(self.validation_label)

        # Zoom level indicator
        self.zoom_label = QLabel("Zoom: 100%")
        self.status_bar.addPermanentWidget(self.zoom_label)
        self._update_zoom_label()

    def _connect_signals(self):
        """Connect signals between components."""
        # Outline selection changes
        self.outline.current_item_changed.connect(self.on_item_selected)

        # Detail form changes
        self.detail_form.register_changed.connect(self.on_register_changed)
        self.detail_form.field_changed.connect(self.on_field_changed)
        self.detail_form.array_template_changed.connect(self.on_array_template_changed)

        # Auto-validation timer
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self.auto_validate)

        # Panel focus switching shortcuts (Ctrl+H/L)
        self.focus_left_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        self.focus_left_shortcut.activated.connect(self._focus_left_panel)

        self.focus_right_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self.focus_right_shortcut.activated.connect(self._focus_right_panel)

        # Track focus changes for visual feedback
        self.outline.tree.focusInEvent = lambda e: self._on_outline_focus(e)
        self.detail_form.bit_field_table.table.focusInEvent = lambda e: self._on_detail_focus(e)

        # Project change notifications
        self.project_changed.connect(self.update_status)

    def zoom_in(self):
        """Increase text size."""
        current_font = QApplication.font()
        new_size = min(current_font.pointSize() + 1, 24)
        self._apply_font_size(new_size)
        self.settings.setValue("display/font_size", new_size)
        self._update_zoom_label()
        self.refresh_views()

    def zoom_out(self):
        """Decrease text size."""
        current_font = QApplication.font()
        new_size = max(current_font.pointSize() - 1, 8)
        self._apply_font_size(new_size)
        self.settings.setValue("display/font_size", new_size)
        self._update_zoom_label()
        self.refresh_views()

    def zoom_reset(self):
        """Reset text size to default."""
        self._apply_font_size(10)
        self.settings.setValue("display/font_size", 10)
        self._update_zoom_label()
        self.refresh_views()

    def _update_zoom_label(self):
        """Update the zoom level indicator in the status bar."""
        current_font = QApplication.font()
        percentage = int((current_font.pointSize() / 10) * 100)
        self.zoom_label.setText(f"Zoom: {percentage}%")

    def show_display_settings(self):
        """Show the display settings dialog."""
        dialog = ScalingDialog(self)

        # Set current values
        current_font = QApplication.font()
        dialog.font_size_spin.setValue(current_font.pointSize())

        current_scale = self.settings.value("display/scale_factor", 1.0, type=float)
        scale_percentage = f"{int(current_scale * 100)}%"
        index = dialog.scale_combo.findText(scale_percentage)
        if index >= 0:
            dialog.scale_combo.setCurrentIndex(index)

        if dialog.exec() == QDialog.Accepted:
            # Apply font size
            new_font_size = dialog.get_font_size()
            self._apply_font_size(new_font_size)
            self.settings.setValue("display/font_size", new_font_size)

            # Save scale factor (requires restart)
            new_scale_factor = dialog.get_scale_factor()
            old_scale_factor = self.settings.value("display/scale_factor", 1.0, type=float)
            self.settings.setValue("display/scale_factor", new_scale_factor)

            # Update UI
            self._update_zoom_label()
            self.refresh_views()

            # Show restart message if scale changed
            if abs(new_scale_factor - old_scale_factor) > 0.01:
                QMessageBox.information(
                    self,
                    "Restart Required",
                    "UI scaling changes will take full effect after restarting the application."
                )

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
            reference_offset = reference_item.offset
        elif isinstance(reference_item, RegisterArrayAccessor):
            # Insert before a register array
            reference_offset = reference_item._base_offset
        else:
            return

        # Strategy: Always ensure we can insert before by potentially shifting registers
        # Find what offset the new register should have
        target_offset = max(0, reference_offset - 4)

        # Check if we need to shift existing registers to make space
        used_offsets = {reg.offset for reg in self.current_project.registers}
        for array in self.current_project.register_arrays:
            for i in range(array._count):
                used_offsets.add(array._base_offset + i * array._stride)

        # If target offset is occupied or we're trying to insert at a negative offset,
        # we need to shift everything forward to make space
        if target_offset in used_offsets or target_offset < 0:
            # Shift all registers and arrays forward by 4 to make space at the beginning
            # if inserting before the first register, or find a gap

            if reference_offset == 0:
                # Special case: inserting before register at offset 0
                # Shift all registers forward by 4
                for reg in self.current_project.registers:
                    reg.offset += 4
                for array in self.current_project.register_arrays:
                    array._base_offset += 4
                new_offset = 0
            else:
                # Find the largest gap we can use before the reference
                sorted_offsets = sorted(used_offsets)

                # Find gaps before the reference offset
                new_offset = 0
                for offset in sorted_offsets:
                    if offset >= reference_offset:
                        break
                    if offset - new_offset >= 4:
                        # Found a gap of at least 4 bytes
                        break
                    new_offset = offset + 4

                # If new_offset would be >= reference_offset, we need to shift
                if new_offset >= reference_offset:
                    # Shift all registers and arrays at or after reference_offset forward by 4
                    shift_amount = 4
                    for reg in self.current_project.registers:
                        if reg.offset >= reference_offset:
                            reg.offset += shift_amount
                    for array in self.current_project.register_arrays:
                        if array._base_offset >= reference_offset:
                            array._base_offset += shift_amount
                    new_offset = reference_offset
        else:
            new_offset = target_offset

        # Create the register
        register = Register(
            name=f"register_{len(self.current_project.registers)}",
            offset=new_offset,
            bus=self.current_project._bus,
            fields=[],
            description="New register (inserted before)"
        )

        # Add the register and then sort the entire list by offset
        self.current_project.registers.append(register)
        self.current_project.registers.sort(key=lambda r: r.offset)

        self.refresh_views()
        self.outline.select_item(register)
        self.project_changed.emit()

    def insert_register_after(self, reference_item):
        """Insert a new register after the reference item."""
        if not self.current_project:
            return

        if isinstance(reference_item, Register):
            # Insert after a regular register
            reference_offset = reference_item.offset
            target_offset = reference_offset + 4
        elif isinstance(reference_item, RegisterArrayAccessor):
            # Insert after a register array (after its last element)
            last_array_offset = reference_item._base_offset + ((reference_item._count - 1) * reference_item._stride)
            target_offset = last_array_offset + 4
        else:
            return

        # Strategy: Always ensure we can insert immediately after by potentially shifting registers
        # Check what's currently at the target offset
        used_offsets = {reg.offset for reg in self.current_project.registers}
        for array in self.current_project.register_arrays:
            for i in range(array._count):
                used_offsets.add(array._base_offset + i * array._stride)

        # If target offset is occupied, we need to shift registers forward
        if target_offset in used_offsets:
            # Shift all registers and arrays at or after target_offset forward by 4
            shift_amount = 4
            for reg in self.current_project.registers:
                if reg.offset >= target_offset:
                    reg.offset += shift_amount
            for array in self.current_project.register_arrays:
                if array._base_offset >= target_offset:
                    array._base_offset += shift_amount

        new_offset = target_offset

        # Create the register
        register = Register(
            name=f"register_{len(self.current_project.registers)}",
            offset=new_offset,
            bus=self.current_project._bus,
            fields=[],
            description="New register (inserted after)"
        )

        # Add the register and then sort the entire list by offset
        self.current_project.registers.append(register)
        self.current_project.registers.sort(key=lambda r: r.offset)

        self.refresh_views()
        self.outline.select_item(register)
        self.project_changed.emit()

    # Wrapper methods for context-aware insertion actions
    def insert_array_before(self, reference_item):
        """Insert a new register array before the reference item."""
        if not self.current_project:
            return

        if isinstance(reference_item, Register):
            reference_offset = reference_item.offset
        elif isinstance(reference_item, RegisterArrayAccessor):
            reference_offset = reference_item._base_offset
        else:
            return

        # Similar logic to insert_register_before but for arrays
        target_offset = max(0, reference_offset - 16)  # Arrays typically need more space

        used_offsets = {reg.offset for reg in self.current_project.registers}
        for array in self.current_project.register_arrays:
            for i in range(array._count):
                used_offsets.add(array._base_offset + i * array._stride)

        if target_offset in used_offsets or target_offset < 0:
            if reference_offset == 0:
                # Shift everything forward
                for reg in self.current_project.registers:
                    reg.offset += 16
                for array in self.current_project.register_arrays:
                    array._base_offset += 16
                new_offset = 0
            else:
                # Find gap or shift
                new_offset = 0
                sorted_offsets = sorted(used_offsets)
                for offset in sorted_offsets:
                    if offset >= reference_offset:
                        break
                    if offset - new_offset >= 16:
                        break
                    new_offset = offset + 4

                if new_offset >= reference_offset:
                    shift_amount = 16
                    for reg in self.current_project.registers:
                        if reg.offset >= reference_offset:
                            reg.offset += shift_amount
                    for array in self.current_project.register_arrays:
                        if array._base_offset >= reference_offset:
                            array._base_offset += shift_amount
                    new_offset = reference_offset
        else:
            new_offset = target_offset

        # Create the array
        array = self.current_project.add_register_array(
            f"array_{len(self.current_project.register_arrays)}",
            new_offset,
            4,  # Default count
            4   # Default stride
        )

        self.refresh_views()
        self.outline.select_item(array)
        self.project_changed.emit()

    def insert_array_after(self, reference_item):
        """Insert a new register array after the reference item."""
        if not self.current_project:
            return

        if isinstance(reference_item, Register):
            reference_offset = reference_item.offset
            target_offset = reference_offset + 4
        elif isinstance(reference_item, RegisterArrayAccessor):
            last_array_offset = reference_item._base_offset + ((reference_item._count - 1) * reference_item._stride)
            target_offset = last_array_offset + 4
        else:
            return

        used_offsets = {reg.offset for reg in self.current_project.registers}
        for array in self.current_project.register_arrays:
            for i in range(array._count):
                used_offsets.add(array._base_offset + i * array._stride)

        # Check if we need space for the new array (4 registers by default)
        needed_space = 16  # 4 registers * 4 bytes each
        space_available = True
        for i in range(4):
            if target_offset + (i * 4) in used_offsets:
                space_available = False
                break

        if not space_available:
            # Shift registers forward to make space
            shift_amount = 16
            for reg in self.current_project.registers:
                if reg.offset >= target_offset:
                    reg.offset += shift_amount
            for array in self.current_project.register_arrays:
                if array._base_offset >= target_offset:
                    array._base_offset += shift_amount

        new_offset = target_offset

        # Create the array
        array = self.current_project.add_register_array(
            f"array_{len(self.current_project.register_arrays)}",
            new_offset,
            4,  # Default count
            4   # Default stride
        )

        self.refresh_views()
        self.outline.select_item(array)
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
            item_name = f"Register Array '{item_to_remove._name}'"
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

    def on_item_selected(self, item, parent_array):
        """Handle selection change in the outline.

        Args:
            item: Selected Register or RegisterArrayAccessor
            parent_array: If item is an array element, this is the parent RegisterArrayAccessor
        """
        self.detail_form.set_current_item(item, parent_array)

    def on_register_changed(self):
        """Handle register property changes."""
        self.outline.refresh()
        self.schedule_validation()
        self.project_changed.emit()

    def on_field_changed(self):
        """Handle bit field changes."""
        self.schedule_validation()
        self.project_changed.emit()

    def on_array_template_changed(self):
        """Handle array template changes - refresh outline to show updates across all elements."""
        self.outline.refresh()
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

    def show_keyboard_shortcuts(self):
        """Show keyboard shortcuts help dialog."""
        help_text = """<h3>Keyboard Shortcuts</h3>

        <h4>File Operations</h4>
        <table>
        <tr><td><b>Ctrl+N</b></td><td>New Project</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>Open Project</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Save Project</td></tr>
        <tr><td><b>Ctrl+Shift+S</b></td><td>Save As</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Quit</td></tr>
        </table>

        <h4>View Operations</h4>
        <table>
        <tr><td><b>Ctrl+R</b></td><td>Validate Memory Map</td></tr>
        <tr><td><b>Ctrl++</b></td><td>Zoom In</td></tr>
        <tr><td><b>Ctrl+-</b></td><td>Zoom Out</td></tr>
        <tr><td><b>Ctrl+0</b></td><td>Reset Zoom</td></tr>
        <tr><td><b>F5</b></td><td>Refresh</td></tr>
        <tr><td><b>Ctrl+H</b></td><td>Focus Memory Map Outline (Left Panel)</td></tr>
        <tr><td><b>Ctrl+L</b></td><td>Focus Bit Field Table (Right Panel)</td></tr>
        </table>

        <h4>Memory Map Outline (Vim-style)</h4>
        <table>
        <tr><td><b>j</b></td><td>Move Down</td></tr>
        <tr><td><b>k</b></td><td>Move Up</td></tr>
        <tr><td><b>h</b></td><td>Collapse Array / Move to Parent</td></tr>
        <tr><td><b>l</b></td><td>Expand Array / Move to Child</td></tr>
        <tr><td><b>o</b></td><td>Insert Register After</td></tr>
        <tr><td><b>Shift+O</b></td><td>Insert Register Before</td></tr>
        <tr><td><b>a</b></td><td>Insert Array After</td></tr>
        <tr><td><b>Shift+A</b></td><td>Insert Array Before</td></tr>
        <tr><td><b>dd</b></td><td>Delete Selected</td></tr>
        <tr><td><b>Alt+Up/Down</b></td><td>Move Item Up/Down</td></tr>
        <tr><td><b>Alt+k/j</b></td><td>Move Item Up/Down (vim-style)</td></tr>
        </table>

        <h4>Bit Field Table (Vim-style Modal)</h4>
        <table>
        <tr><td colspan=\"2\"><b>Normal Mode:</b></td></tr>
        <tr><td><b>h/j/k/l</b></td><td>Move Left/Down/Up/Right</td></tr>
        <tr><td><b>i</b></td><td>Enter Insert Mode (Edit Cell)</td></tr>
        <tr><td><b>o</b></td><td>Insert Field After</td></tr>
        <tr><td><b>Shift+O</b></td><td>Insert Field Before</td></tr>
        <tr><td><b>dd</b></td><td>Delete Selected Field</td></tr>
        <tr><td><b>Alt+Up/Down</b></td><td>Move Field Up/Down</td></tr>
        <tr><td><b>Alt+k/j</b></td><td>Move Field Up/Down (vim-style)</td></tr>
        <tr><td colspan=\"2\"><b>Insert Mode:</b></td></tr>
        <tr><td><b>ESC or Ctrl+[</b></td><td>Return to Normal Mode</td></tr>
        </table>

        <h4>Help</h4>
        <table>
        <tr><td><b>F1</b></td><td>Show This Help</td></tr>
        </table>
        """

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Keyboard Shortcuts")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(help_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

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

"""
Register Detail Form - Main Coordinator Component

Orchestrates the register editing interface by composing specialized widgets:
- RegisterPropertiesWidget: Property editing
- BitFieldTableWidget: Bit field management
- BitFieldVisualizerWidget: Visual representation
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QGroupBox
from PySide6.QtCore import Qt, Signal

from .bit_field_visualizer import BitFieldVisualizer
from .register_properties_widget import RegisterPropertiesWidget
from .bit_field_table_widget import BitFieldTableWidget
from memory_map_core import MemoryMapProject, Register, RegisterArrayAccessor


class RegisterDetailForm(QWidget):
    """
    Main form for editing register and register array properties.

    This widget acts as a coordinator, composing specialized sub-widgets
    and managing their interactions. It follows the composition pattern
    to keep responsibilities focused and maintainable.
    """

    # Signals
    register_changed = Signal()  # Emitted when register properties change
    field_changed = Signal()     # Emitted when bit fields change
    array_template_changed = Signal()  # Emitted when an array template is modified

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_project = None
        self.current_item = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the user interface with composed widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Create horizontal splitter for bit fields (left) and properties (right)
        self.main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.main_splitter)

        # Left panel: Bit Fields Table (1/3 width)
        fields_group = QGroupBox("Bit Fields")
        fields_layout = QVBoxLayout(fields_group)

        self.bit_field_table = BitFieldTableWidget()
        fields_layout.addWidget(self.bit_field_table)

        self.main_splitter.addWidget(fields_group)

        # Right panel: Properties and Visualizer (2/3 width)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Properties widget
        self.properties_widget = RegisterPropertiesWidget()
        right_layout.addWidget(self.properties_widget)

        # Bit field visualizer
        visualizer_group = QGroupBox("Bit Field Visualization")
        visualizer_layout = QVBoxLayout(visualizer_group)

        self.bit_visualizer = BitFieldVisualizer()
        visualizer_layout.addWidget(self.bit_visualizer)

        right_layout.addWidget(visualizer_group)

        self.main_splitter.addWidget(right_widget)

        # Set initial splitter sizes (1/3 for left, 2/3 for right)
        self.main_splitter.setSizes([300, 600])

        # Initial state
        self._set_controls_enabled(False)

    def _connect_signals(self):
        """Connect signals between composed widgets."""
        # Properties widget signals
        self.properties_widget.property_changed.connect(self._on_property_changed)
        self.properties_widget.reset_value_changed.connect(self._on_reset_value_changed)
        self.properties_widget.live_value_changed.connect(self._on_live_value_changed)

        # Bit field table signals
        self.bit_field_table.field_changed.connect(self._on_field_changed)
        self.bit_field_table.array_template_changed.connect(self._on_array_template_changed)

    def set_project(self, project: MemoryMapProject):
        """Set the current project."""
        self.current_project = project
        self.bit_visualizer.set_project(project)

    def set_current_item(self, item, parent_array=None):
        """Set the currently selected memory map item.

        Args:
            item: Register or RegisterArrayAccessor to display
            parent_array: If item is an array element, this is the parent RegisterArrayAccessor
        """
        self.current_item = item
        self._update_all_widgets(parent_array)

    def _update_all_widgets(self, parent_array=None):
        """Update all composed widgets with current item.

        Args:
            parent_array: If current_item is an array element, this is the parent RegisterArrayAccessor
        """
        if self.current_item is None:
            self._set_controls_enabled(False)
            self.properties_widget.set_item(None)
            self.bit_field_table.set_current_item(None)
            self.bit_visualizer.set_current_item(None)
        else:
            self._set_controls_enabled(True)

            # Update properties widget FIRST - this initializes live defaults
            self.properties_widget.set_item(self.current_item)

            # Update bit field table - will now see initialized live values
            # Pass parent_array so changes can be propagated to all array elements
            self.bit_field_table.set_current_item(self.current_item, parent_array)

            # Update visualizer
            self.bit_visualizer.set_current_item(self.current_item)

            # Force refresh to ensure live values are displayed
            if isinstance(self.current_item, Register):
                self.bit_field_table.refresh()

    def refresh_live_display(self):
        """Refresh displayed live values from debug set."""
        if isinstance(self.current_item, Register):
            self.properties_widget.refresh_live_value()
            self.bit_field_table.refresh()
            self.bit_visualizer.refresh()
            self.field_changed.emit()

    def _set_controls_enabled(self, enabled: bool):
        """Enable or disable all form controls."""
        self.properties_widget.setEnabled(enabled)
        self.bit_field_table.set_enabled(enabled)
        self.bit_visualizer.setEnabled(enabled)

    def _on_property_changed(self):
        """Handle property changes from properties widget."""
        self.register_changed.emit()

    def _on_reset_value_changed(self):
        """Handle reset value changes."""
        # Refresh table and visualizer to show updated reset value
        self.bit_field_table.refresh()
        self.bit_visualizer.refresh()
        self.register_changed.emit()

    def _on_live_value_changed(self):
        """Handle live value changes from register-level edit."""
        # Refresh table and visualizer to show updated live values
        self.bit_field_table.refresh()
        self.bit_visualizer.refresh()
        self.field_changed.emit()

    def _on_field_changed(self):
        """Handle bit field changes from table widget."""
        # Update properties widget to show recalculated reset value
        if isinstance(self.current_item, Register):
            self.properties_widget.update_reset_value_display()

        # Update visualizer to show field changes
        self.bit_visualizer.refresh()

        # Forward signal
        self.field_changed.emit()

    def _on_array_template_changed(self, array):
        """Handle array template changes - refresh outline to show all elements updated."""
        # Emit specialized signal for array template changes
        self.array_template_changed.emit()
        # Also emit field_changed for validation
        self.field_changed.emit()

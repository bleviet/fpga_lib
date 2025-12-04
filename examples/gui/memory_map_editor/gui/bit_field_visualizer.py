"""
Bit Field Visualizer - Custom Qt Widget

Provides visual representation of register bit fields with real-time updates.
Shows 32-bit register layout with color-coded fields and interactive elements.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics

from memory_map_core import MemoryMapProject
from fpga_lib.core import Register, RegisterArrayAccessor, BitField
from examples.gui.memory_map_editor.debug_mode import debug_manager


class BitFieldVisualizerWidget(QWidget):
    """
    Custom widget that draws a visual representation of register bit fields.

    Displays a 32-bit register as a series of boxes, with each bit field
    color-coded and labeled. Provides visual feedback for overlaps and errors.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_register = None
        self.field_colors = {}

        # Visual parameters
        self.bit_width = 30
        self.bit_height = 50  # Height for each row (reset or live)
        self.margin = 60  # Increased margin for labels
        self.label_height = 80
        self.bit_number_height = 25
        self.reset_value_height = 25
        self.debug_mode_enabled = True

        self._update_size_parameters()
        
        # Enable mouse tracking for click events
        self.setMouseTracking(True)

    def _update_size_parameters(self):
        """Update size parameters based on debug mode."""
        if self.debug_mode_enabled:
            # In debug mode, we need space for two rows plus labels
            total_height = self.bit_number_height + (2 * self.bit_height) + self.label_height + 2 * self.margin + 40
        else:
            # Normal mode
            total_height = self.bit_number_height + self.bit_height + self.label_height + 2 * self.margin

        self.setMinimumHeight(total_height)
        self.setMinimumWidth(32 * self.bit_width + 2 * self.margin)

    def set_register(self, register):
        """Set the register to visualize."""
        self.current_register = register
        # Sync debug mode state with global manager on each register set
        try:
            self.set_debug_mode(debug_manager.debug_mode_enabled)
        except Exception:
            pass
        self._generate_field_colors()
        self.update()

    def set_debug_mode(self, enabled):
        """Enable or disable debug mode visualization."""
        if self.debug_mode_enabled != enabled:
            self.debug_mode_enabled = enabled
            self._update_size_parameters()
            self.update()  # Trigger repaint
            self.updateGeometry()  # Update size hint

    def toggle_debug_mode(self):
        """Toggle debug mode on/off."""
        self.set_debug_mode(not self.debug_mode_enabled)

    def _generate_field_colors(self):
        """Generate distinct colors for each bit field."""
        self.field_colors.clear()

        if not self.current_register or not hasattr(self.current_register, '_fields'):
            return

        # Predefined color palette
        colors = [
            QColor(100, 150, 255),  # Light blue
            QColor(255, 150, 100),  # Light orange
            QColor(150, 255, 150),  # Light green
            QColor(255, 150, 255),  # Light magenta
            QColor(255, 255, 100),  # Light yellow
            QColor(150, 255, 255),  # Light cyan
            QColor(255, 200, 150),  # Light peach
            QColor(200, 150, 255),  # Light purple
        ]

        for i, field_name in enumerate(self.current_register._fields.keys()):
            self.field_colors[field_name] = colors[i % len(colors)]

    def paintEvent(self, event):
        """Custom paint event to draw the bit field visualization."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Clear background
        painter.fillRect(self.rect(), QColor(240, 240, 240))

        if not self.current_register:
            self._draw_empty_state(painter)
            return

        # Draw bit numbers at the top
        self._draw_bit_numbers(painter)

        # Draw bit boxes with reset values
        self._draw_bit_boxes(painter)

        # Draw field labels at the bottom
        self._draw_field_labels(painter)

    def _draw_empty_state(self, painter):
        """Draw empty state message."""
        painter.setPen(QPen(QColor(128, 128, 128)))
        font = QFont()
        font.setPointSize(12)
        painter.setFont(font)

        text = "Select a register to view bit fields"
        text_rect = painter.fontMetrics().boundingRect(text)
        x = (self.width() - text_rect.width()) // 2
        y = (self.height() - text_rect.height()) // 2
        painter.drawText(x, y, text)

    def _draw_bit_boxes(self, painter):
        """Draw the 32-bit register as individual bit boxes with reset values and optional debug comparison."""
        if not hasattr(self.current_register, '_fields'):
            return

        # Create array to track which bits are used by which fields
        bit_fields = [None] * 32
        overlaps = [False] * 32
        reset_bits = [0] * 32  # Track reset value for each bit
        live_bits = [0] * 32   # Track live debug value for each bit

        # Get register name for debug comparison
        register_name = getattr(self.current_register, 'name', 'unknown_register')

        # Map bits to fields and detect overlaps
        for field_name, field in self.current_register._fields.items():
            for bit_pos in range(field.offset, min(field.offset + field.width, 32)):
                if bit_fields[bit_pos] is not None:
                    overlaps[bit_pos] = True
                bit_fields[bit_pos] = field_name

                # Calculate reset bit value for this position
                if field.reset_value is not None:
                    field_bit_index = bit_pos - field.offset
                    reset_bits[bit_pos] = (field.reset_value >> field_bit_index) & 1

        # Get debug differences if in debug mode
        debug_differences = []
        if self.debug_mode_enabled:
            # Calculate reset value for comparison
            reset_value = 0
            for field in self.current_register._fields.values():
                if field.reset_value is not None:
                    reset_value |= (field.reset_value << field.offset)

            debug_differences = debug_manager.compare_register_bits(register_name, self.current_register, reset_value)

            # Get live values for display
            current_set = debug_manager.get_current_debug_set()
            if current_set:
                live_value_obj = current_set.get_register_value(register_name)
                if live_value_obj and live_value_obj.value is not None:
                    live_value = live_value_obj.value
                    for bit_pos in range(32):
                        live_bits[bit_pos] = (live_value >> bit_pos) & 1
                else:
                    # No live value yet; mirror reset bits so live row shows defaults instead of zeros
                    for bit_pos in range(32):
                        live_bits[bit_pos] = reset_bits[bit_pos]

        # Draw each bit box (from bit 31 to 0, left to right)
        for bit in range(32):
            actual_bit = 31 - bit  # Map display position to actual bit number
            x = self.margin + bit * self.bit_width

            if self.debug_mode_enabled:
                # Two-row mode: reset on top, live on bottom
                self._draw_debug_bit_box(painter, x, actual_bit, bit_fields, overlaps, reset_bits, live_bits, debug_differences)
            else:
                # Normal mode: single row
                self._draw_normal_bit_box(painter, x, actual_bit, bit_fields, overlaps, reset_bits)

        # Draw labels
        if self.debug_mode_enabled:
            self._draw_debug_labels(painter)
        else:
            self._draw_normal_labels(painter)

    def _draw_normal_bit_box(self, painter, x, actual_bit, bit_fields, overlaps, reset_bits):
        """Draw a single bit box in normal mode."""
        y = self.margin + self.bit_number_height
        rect = QRect(x, y, self.bit_width, self.bit_height)

        # Determine color
        if overlaps[actual_bit]:
            color = QColor(255, 100, 100)  # Red for overlaps
        elif bit_fields[actual_bit] is not None:
            field_name = bit_fields[actual_bit]
            color = self.field_colors.get(field_name, QColor(200, 200, 200))
        else:
            color = QColor(250, 250, 250)  # Light gray for unused bits

        # Draw box
        painter.fillRect(rect, QBrush(color))
        painter.setPen(QPen(QColor(64, 64, 64)))
        painter.drawRect(rect)

        # Draw reset value
        if bit_fields[actual_bit] is not None:
            painter.setPen(QPen(QColor(0, 120, 0) if reset_bits[actual_bit] == 1 else QColor(100, 100, 100)))
            font = QFont()
            font.setPointSize(14)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, str(reset_bits[actual_bit]))
        else:
            painter.setPen(QPen(QColor(180, 180, 180)))
            font = QFont()
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, "0")

    def _draw_debug_bit_box(self, painter, x, actual_bit, bit_fields, overlaps, reset_bits, live_bits, debug_differences):
        """Draw a two-row bit box in debug mode."""
        y_reset = self.margin + self.bit_number_height
        y_live = y_reset + self.bit_height

        # Determine base color
        if overlaps[actual_bit]:
            base_color = QColor(255, 100, 100)  # Red for overlaps
        elif bit_fields[actual_bit] is not None:
            field_name = bit_fields[actual_bit]
            base_color = self.field_colors.get(field_name, QColor(200, 200, 200))
        else:
            base_color = QColor(250, 250, 250)  # Light gray for unused bits

        # Draw reset row (top)
        reset_rect = QRect(x, y_reset, self.bit_width, self.bit_height)
        painter.fillRect(reset_rect, QBrush(base_color))
        painter.setPen(QPen(QColor(64, 64, 64)))
        painter.drawRect(reset_rect)

        # Draw live row (bottom) - highlight if different
        live_rect = QRect(x, y_live, self.bit_width, self.bit_height)
        if actual_bit < len(debug_differences) and debug_differences[actual_bit]:
            # Highlight differences with bright yellow
            painter.fillRect(live_rect, QBrush(QColor(255, 255, 0)))
        else:
            painter.fillRect(live_rect, QBrush(base_color))
        painter.setPen(QPen(QColor(64, 64, 64)))
        painter.drawRect(live_rect)

        # Draw reset value text
        if bit_fields[actual_bit] is not None:
            painter.setPen(QPen(QColor(0, 120, 0) if reset_bits[actual_bit] == 1 else QColor(100, 100, 100)))
        else:
            painter.setPen(QPen(QColor(180, 180, 180)))

        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(reset_rect, Qt.AlignCenter, str(reset_bits[actual_bit]))

        # Draw live value text
        live_bit_value = live_bits[actual_bit] if actual_bit < len(live_bits) else 0
        if bit_fields[actual_bit] is not None:
            # Use red for differences, green/gray for normal
            if actual_bit < len(debug_differences) and debug_differences[actual_bit]:
                painter.setPen(QPen(QColor(200, 0, 0)))  # Red for differences
            else:
                painter.setPen(QPen(QColor(0, 120, 0) if live_bit_value == 1 else QColor(100, 100, 100)))
        else:
            painter.setPen(QPen(QColor(180, 180, 180)))

        painter.drawText(live_rect, Qt.AlignCenter, str(live_bit_value))

    def _draw_normal_labels(self, painter):
        """Draw the normal single-row labels."""
        y = self.margin + self.bit_number_height
        painter.setPen(QPen(QColor(0, 0, 0)))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)

        reset_label_rect = QRect(5, y + self.bit_height // 2 - 10, 50, 20)
        painter.drawText(reset_label_rect, Qt.AlignCenter | Qt.AlignVCenter, "Reset:")

    def _draw_debug_labels(self, painter):
        """Draw the two-row debug mode labels."""
        y_reset = self.margin + self.bit_number_height
        y_live = y_reset + self.bit_height

        painter.setPen(QPen(QColor(0, 0, 0)))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)

        # Reset label
        reset_label_rect = QRect(5, y_reset + self.bit_height // 2 - 10, 50, 20)
        painter.drawText(reset_label_rect, Qt.AlignCenter | Qt.AlignVCenter, "Reset:")

        # Live label
        live_label_rect = QRect(5, y_live + self.bit_height // 2 - 10, 50, 20)
        painter.drawText(live_label_rect, Qt.AlignCenter | Qt.AlignVCenter, "Live:")

    def _draw_field_labels(self, painter):
        """Draw field name labels below the bit boxes with straight lines and rotated text."""
        if not hasattr(self.current_register, '_fields'):
            return

        # Base Y position for labels (depends on debug mode)
        if self.debug_mode_enabled:
            bits_bottom_y = self.margin + self.bit_number_height + (self.bit_height * 2)  # Two rows
        else:
            bits_bottom_y = self.margin + self.bit_number_height + self.bit_height  # Single row

        # Sort fields by their offset in ascending order (lowest offset first)
        sorted_fields = sorted(self.current_register._fields.items(),
                             key=lambda x: x[1].offset)

        # Calculate label positions
        painter.setPen(QPen(QColor(0, 0, 0)))
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)

        fm = QFontMetrics(font)

        for field_name, field in sorted_fields:
            # Calculate field position and width (accounting for MSB-first display)
            start_bit = field.offset
            end_bit = min(field.offset + field.width - 1, 31)

            # Convert to display positions (31-bit maps to position 0)
            start_pos = 31 - end_bit
            end_pos = 31 - start_bit

            field_center_x = self.margin + start_pos * self.bit_width + ((end_pos - start_pos + 1) * self.bit_width) // 2

            # Draw a straight vertical line down from the bit box
            line_length = 50  # Length of the vertical line
            line_end_y = bits_bottom_y + line_length

            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.drawLine(field_center_x, bits_bottom_y, field_center_x, line_end_y)

            # Prepare text with field name and bit range
            if field.width == 1:
                label_text = f"{field_name} [{field.offset}]"
            else:
                label_text = f"{field_name} [{end_bit}:{start_bit}]"

            # Measure text dimensions
            text_width = fm.horizontalAdvance(label_text)
            text_height = fm.height()

            # Save the painter state before rotation
            painter.save()

            # Rotate text 30 degrees counter-clockwise around the end point of the line
            # The tip of the line should touch the last character of the label
            painter.translate(field_center_x, line_end_y)
            painter.rotate(-30)  # Negative for counter-clockwise

            # Position text so its bottom-right corner (end of text) is at the rotation point
            # We need to shift the text to the left by its width and down slightly
            text_x = -text_width
            text_y = text_height // 2  # Center vertically around the line tip

            # Draw the rotated text
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(text_x, text_y, label_text)

            # Restore painter state
            painter.restore()

    def _draw_bit_numbers(self, painter):
        """Draw bit numbers at the top of the visualization."""
        painter.setPen(QPen(QColor(0, 0, 0)))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)

        # Draw "Bit:" label
        label_rect = QRect(5, self.margin, 50, self.bit_number_height)
        painter.drawText(label_rect, Qt.AlignCenter | Qt.AlignVCenter, "Bit:")

        # Draw bit numbers from 31 down to 0 (MSB to LSB)
        for bit in range(32):
            display_bit = 31 - bit  # Show from 31 to 0
            x = self.margin + bit * self.bit_width
            y = self.margin

            rect = QRect(x, y, self.bit_width, self.bit_number_height)
            painter.drawText(rect, Qt.AlignCenter, str(display_bit))

    def sizeHint(self):
        """Return the preferred size for this widget."""
        # Simple width calculation based on 32 bits plus margins
        width = 32 * self.bit_width + 2 * self.margin

        # Calculate height based on debug mode and label space
        if self.debug_mode_enabled:
            # Two-row mode: account for reset + live rows plus label space
            height = self.bit_number_height + (self.bit_height * 2) + self.label_height + 2 * self.margin + 80
        else:
            # Normal mode: single row plus label space
            height = self.bit_number_height + self.bit_height + self.label_height + 2 * self.margin + 80

        return QSize(width, height)
    
    def mousePressEvent(self, event):
        """Handle mouse click events to toggle live bit values."""
        if not self.debug_mode_enabled or not self.current_register:
            return
        
        # Get click position
        x = event.pos().x()
        y = event.pos().y()
        
        # Calculate which row was clicked (reset or live)
        y_reset = self.margin + self.bit_number_height
        y_live = y_reset + self.bit_height
        
        # Check if click is in the live row
        if y < y_live or y > y_live + self.bit_height:
            return  # Not in live row
        
        # Calculate which bit was clicked
        if x < self.margin or x > self.margin + 32 * self.bit_width:
            return  # Not in bit area
        
        bit_index = (x - self.margin) // self.bit_width
        if bit_index >= 32:
            return
        
        # Convert display position to actual bit number (31-bit is at position 0)
        actual_bit = 31 - bit_index
        
        # Toggle the bit in the live register value
        register_name = getattr(self.current_register, 'name', None)
        if not register_name:
            return
        
        current_set = debug_manager.get_current_debug_set()
        if not current_set:
            current_set = debug_manager.create_debug_set("default")
        
        # Get current live value or use reset value as baseline
        live_value_obj = current_set.get_register_value(register_name)
        if live_value_obj and live_value_obj.value is not None:
            current_value = live_value_obj.value
        else:
            # Use reset value as starting point
            current_value = 0
            for field in self.current_register._fields.values():
                if field.reset_value is not None:
                    current_value |= (field.reset_value << field.offset)
        
        # Toggle the bit
        new_value = current_value ^ (1 << actual_bit)
        
        # Update the register value
        from examples.gui.memory_map_editor.debug_mode import DebugValue
        current_set.set_register_value(register_name, DebugValue(new_value))
        
        # Update field values from the new register value
        debug_manager.update_field_values_from_register(register_name, self.current_register, new_value)
        
        # Trigger repaint
        self.update()
        
        # Notify parent widgets to update (find the RegisterDetailForm)
        parent = self.parent()
        while parent:
            # Look for the wrapper BitFieldVisualizer
            if isinstance(parent, BitFieldVisualizer):
                # Now find the RegisterDetailForm
                form_parent = parent.parent()
                while form_parent:
                    # Check if this is the RegisterDetailForm by looking for refresh_live_display method
                    if hasattr(form_parent, 'refresh_live_display'):
                        form_parent.refresh_live_display()
                        return
                    form_parent = form_parent.parent()
                return
            parent = parent.parent()


class BitFieldVisualizer(QWidget):
    """
    Container widget for the bit field visualizer with scroll support.

    Wraps the BitFieldVisualizerWidget in a scroll area and provides
    additional controls and information.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_project = None
        self.current_item = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("Bit Field Visualization")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Info label
        self.info_label = QLabel("No register selected")
        header_layout.addWidget(self.info_label)

        layout.addLayout(header_layout)

        # Scroll area for the visualizer
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create the actual visualizer widget
        self.visualizer = BitFieldVisualizerWidget()
        scroll.setWidget(self.visualizer)

        layout.addWidget(scroll)

        # Legend
        self._create_legend(layout)

    def _create_legend(self, layout):
        """Create a legend explaining the visualization."""
        legend_layout = QHBoxLayout()

        legend_layout.addWidget(QLabel("Legend:"))

        # Color samples
        colors = [
            (QColor(100, 150, 255), "Field"),
            (QColor(240, 240, 240), "Unused"),
            (QColor(255, 100, 100), "Overlap/Error")
        ]

        for color, label in colors:
            sample = QLabel("  ")
            sample.setStyleSheet(f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); border: 1px solid black;")
            sample.setMaximumWidth(20)
            sample.setMaximumHeight(15)

            legend_layout.addWidget(sample)
            legend_layout.addWidget(QLabel(label))
            legend_layout.addSpacing(15)

        legend_layout.addStretch()
        layout.addLayout(legend_layout)

    # --- Pass-through convenience API so external code can treat this as the visualizer ---
    def set_register(self, register):
        self.visualizer.set_register(register)

    def set_debug_mode(self, enabled: bool):
        self.visualizer.set_debug_mode(enabled)

    def toggle_debug_mode(self):
        self.visualizer.toggle_debug_mode()

    @property
    def debug_mode_enabled(self):  # read-only property for convenience
        return self.visualizer.debug_mode_enabled

    def update(self):  # ensure both wrapper and inner widget repaint
        self.visualizer.update()
        super().update()

    def set_project(self, project: MemoryMapProject):
        """Set the current project."""
        self.current_project = project

    def set_current_item(self, item):
        """Set the currently selected memory map item."""
        self.current_item = item
        self.refresh()

    def refresh(self):
        """Refresh the visualization."""
        if isinstance(self.current_item, Register):
            self.visualizer.set_register(self.current_item)
            field_count = len(self.current_item._fields)
            self.info_label.setText(f"Register: {self.current_item.name} ({field_count} fields)")
            # Also update the visualizer display
            self.visualizer.update()
        elif isinstance(self.current_item, RegisterArrayAccessor):
            # For arrays, show the field template
            if self.current_item._field_template:
                # Create a mock register to show the field template
                mock_register = type('MockRegister', (), {
                    '_fields': {field.name: field for field in self.current_item._field_template}
                })()
                self.visualizer.set_register(mock_register)
                field_count = len(self.current_item._field_template)
                self.info_label.setText(f"Array: {self.current_item._name} ({field_count} fields per entry)")
            else:
                self.visualizer.set_register(None)
                self.info_label.setText(f"Array: {self.current_item._name} (no fields defined)")
        else:
            self.visualizer.set_register(None)
            self.info_label.setText("No register selected")

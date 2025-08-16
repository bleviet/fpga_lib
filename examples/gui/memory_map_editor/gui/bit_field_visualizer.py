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
        self.bit_width = 20
        self.bit_height = 40
        self.margin = 10
        self.label_height = 60
        
        self.setMinimumHeight(self.bit_height + self.label_height + 2 * self.margin)
        self.setMinimumWidth(32 * self.bit_width + 2 * self.margin)
    
    def set_register(self, register):
        """Set the register to visualize."""
        self.current_register = register
        self._generate_field_colors()
        self.update()
    
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
        
        # Draw bit boxes
        self._draw_bit_boxes(painter)
        
        # Draw field labels
        self._draw_field_labels(painter)
        
        # Draw bit numbers
        self._draw_bit_numbers(painter)
    
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
        """Draw the 32-bit register as individual bit boxes."""
        if not hasattr(self.current_register, '_fields'):
            return
        
        # Create array to track which bits are used by which fields
        bit_fields = [None] * 32
        overlaps = [False] * 32
        
        # Map bits to fields and detect overlaps
        for field_name, field in self.current_register._fields.items():
            for bit_pos in range(field.offset, min(field.offset + field.width, 32)):
                if bit_fields[bit_pos] is not None:
                    overlaps[bit_pos] = True
                bit_fields[bit_pos] = field_name
        
        # Draw each bit box
        for bit in range(32):
            x = self.margin + bit * self.bit_width
            y = self.margin
            
            rect = QRect(x, y, self.bit_width, self.bit_height)
            
            # Determine color
            if overlaps[bit]:
                # Red for overlaps
                color = QColor(255, 100, 100)
            elif bit_fields[bit] is not None:
                # Field color
                field_name = bit_fields[bit]
                color = self.field_colors.get(field_name, QColor(200, 200, 200))
            else:
                # Gray for unused bits
                color = QColor(240, 240, 240)
            
            # Draw box
            painter.fillRect(rect, QBrush(color))
            painter.setPen(QPen(QColor(64, 64, 64)))
            painter.drawRect(rect)
            
            # Draw bit number in box
            painter.setPen(QPen(QColor(0, 0, 0)))
            font = QFont()
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, str(bit))
    
    def _draw_field_labels(self, painter):
        """Draw field name labels below the bit boxes."""
        if not hasattr(self.current_register, '_fields'):
            return
        
        painter.setPen(QPen(QColor(0, 0, 0)))
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        
        label_y = self.margin + self.bit_height + 15
        
        for field_name, field in self.current_register._fields.items():
            # Calculate field position and width
            start_bit = field.offset
            end_bit = min(field.offset + field.width - 1, 31)
            
            start_x = self.margin + start_bit * self.bit_width
            end_x = self.margin + (end_bit + 1) * self.bit_width
            width = end_x - start_x
            
            # Draw field label
            label_rect = QRect(start_x, label_y, width, 20)
            painter.drawText(label_rect, Qt.AlignCenter, field_name)
            
            # Draw connecting line
            center_x = start_x + width // 2
            painter.setPen(QPen(QColor(128, 128, 128)))
            painter.drawLine(center_x, self.margin + self.bit_height, center_x, label_y)
            
            # Draw field range
            painter.setPen(QPen(QColor(64, 64, 64)))
            if field.width == 1:
                range_text = f"[{field.offset}]"
            else:
                range_text = f"[{end_bit}:{start_bit}]"
            
            range_rect = QRect(start_x, label_y + 20, width, 15)
            font.setBold(False)
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(range_rect, Qt.AlignCenter, range_text)
    
    def _draw_bit_numbers(self, painter):
        """Draw bit numbers at the top of the visualization."""
        painter.setPen(QPen(QColor(64, 64, 64)))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        for bit in range(32):
            x = self.margin + bit * self.bit_width
            y = self.margin - 5
            
            rect = QRect(x, y - 15, self.bit_width, 15)
            painter.drawText(rect, Qt.AlignCenter, str(bit))
    
    def sizeHint(self):
        """Return the preferred size for this widget."""
        width = 32 * self.bit_width + 2 * self.margin
        height = self.bit_height + self.label_height + 2 * self.margin
        return QSize(width, height)


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

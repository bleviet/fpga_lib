"""
Custom Delegates for Table Cells

Provides specialized cell editors for different data types in the bit fields table.
"""

from PySide6.QtWidgets import QStyledItemDelegate, QComboBox, QListView
from PySide6.QtCore import Qt, QEvent


class AccessTypeDelegate(QStyledItemDelegate):
    """Custom delegate for access type column with dropdown."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.access_types = ['RO', 'WO', 'RW', 'RW1C']

    def createEditor(self, parent, option, index):
        """Create a combo box editor."""
        combo = QComboBox(parent)
        combo.addItems(self.access_types)

        # Prevent the popup from scrolling to center the current item
        combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Connect to auto-commit when selection changes
        combo.activated.connect(lambda: self.commitData.emit(combo))
        combo.activated.connect(lambda: self.closeEditor.emit(combo))

        # Install event filter to open popup immediately
        combo.installEventFilter(self)

        return combo

    def eventFilter(self, obj, event):
        """Open combo box popup on first show event."""
        if isinstance(obj, QComboBox) and event.type() == QEvent.Type.Show:
            # Set current item before showing popup to prevent repositioning
            obj.view().scrollToTop()
            # Open popup immediately when combo is shown
            obj.showPopup()
            obj.removeEventFilter(self)  # Remove filter after first show
            return False
        return super().eventFilter(obj, event)

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

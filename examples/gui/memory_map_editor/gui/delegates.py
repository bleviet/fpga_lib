"""
Custom Delegates for Table Cells

Provides specialized cell editors for different data types in the bit fields table.
"""

from PySide6.QtWidgets import QStyledItemDelegate, QComboBox
from PySide6.QtCore import Qt


class AccessTypeDelegate(QStyledItemDelegate):
    """Custom delegate for access type column with dropdown."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.access_types = ['RO', 'WO', 'RW', 'RW1C']

    def createEditor(self, parent, option, index):
        """Create a combo box editor."""
        combo = QComboBox(parent)
        combo.addItems(self.access_types)
        return combo

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

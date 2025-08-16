#!/usr/bin/env python3
"""
Memory Map Editor - Main Application Entry Point

A visual editor for FPGA memory maps using Python/Qt.
Integrates with fpga_lib.core register abstractions.
"""

import sys
import os
from pathlib import Path

# Get absolute path to this file and calculate fpga_lib root
current_file = Path(__file__).resolve()  # Get absolute path
fpga_lib_root = current_file.parent.parent.parent.parent
sys.path.insert(0, str(fpga_lib_root))

# Also add current directory to path for local imports
current_dir = current_file.parent
sys.path.insert(0, str(current_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from gui.main_window import MainWindow


def main():
    """Main application entry point."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("FPGA Memory Map Editor")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("FPGA Lib")
    
    # Set application icon (if available)
    icon_path = Path(__file__).parent / "resources" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create and show main window
    main_window = MainWindow()
    main_window.show()
    
    # Start event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

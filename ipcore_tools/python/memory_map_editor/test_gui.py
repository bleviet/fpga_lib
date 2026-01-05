#!/usr/bin/env python3
"""
Headless test for GUI components without actually showing windows.
Tests that all GUI classes can be imported and instantiated.
"""
import sys
import os
from pathlib import Path

# Setup paths
current_dir = Path(__file__).parent
fpga_lib_dir = current_dir.parent.parent.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(fpga_lib_dir))

def test_gui_imports():
    """Test GUI imports without creating Qt application."""
    print("Testing GUI imports...")
    
    try:
        # Test Qt imports
        import PySide6
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        print("✓ PySide6 imported successfully")
        
        # Test our GUI modules (but don't instantiate widgets yet)
        from gui.main_window import MainWindow
        from gui.memory_map_outline import MemoryMapOutline
        from gui.register_detail_form import RegisterDetailForm
        from gui.bit_field_visualizer import BitFieldVisualizerWidget
        print("✓ All GUI modules imported successfully")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_headless_qt():
    """Test creating Qt application in headless mode."""
    print("\nTesting Qt application creation...")
    
    try:
        # Set headless environment
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        
        from PySide6.QtWidgets import QApplication
        
        # Create QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        print("✓ Qt application created successfully")
        
        # Try to create main window (but don't show it)
        from gui.main_window import MainWindow
        window = MainWindow()
        print("✓ Main window created successfully")
        
        return True
    except Exception as e:
        print(f"✗ Qt application test failed: {e}")
        return False

def main():
    print("Memory Map Editor - GUI Component Test")
    print("=" * 50)
    
    success = True
    success &= test_gui_imports()
    success &= test_headless_qt()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All GUI components working correctly!")
        print("The application should be ready to run with a display.")
    else:
        print("✗ Some GUI tests failed.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Simple test script to verify the memory map editor components work correctly.
"""
import sys
import os
from pathlib import Path

# Add the current directory to Python path so we can import our modules
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Add the fpga_lib directory to Python path
fpga_lib_dir = current_dir.parent.parent.parent
sys.path.insert(0, str(fpga_lib_dir))

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import PySide6
        print("✓ PySide6 imported successfully")
    except ImportError as e:
        print(f"✗ PySide6 import failed: {e}")
        return False
    
    try:
        import yaml
        print("✓ PyYAML imported successfully")
    except ImportError as e:
        print(f"✗ PyYAML import failed: {e}")
        return False
    
    try:
        from fpga_lib.core import Register, BitField
        print("✓ fpga_lib.core imported successfully")
    except ImportError as e:
        print(f"✗ fpga_lib.core import failed: {e}")
        return False
    
    try:
        from memory_map_core import MemoryMapProject, load_from_yaml
        print("✓ memory_map_core imported successfully")
    except ImportError as e:
        print(f"✗ memory_map_core import failed: {e}")
        return False
    
    try:
        from gui.main_window import MainWindow
        print("✓ GUI modules imported successfully")
    except ImportError as e:
        print(f"✗ GUI modules import failed: {e}")
        return False
    
    return True

def test_memory_map_loading():
    """Test loading a sample memory map."""
    print("\nTesting memory map loading...")
    
    try:
        from memory_map_core import load_from_yaml
        
        # Test loading the GPIO controller sample
        gpio_file = current_dir / "resources" / "sample_memory_maps" / "gpio_controller.yaml"
        if gpio_file.exists():
            project = load_from_yaml(str(gpio_file))
            print(f"✓ Successfully loaded GPIO controller: {project.name}")
            print(f"  - Base address: 0x{project.base_address:08X}")
            print(f"  - Register count: {len(project.registers)}")
        else:
            print(f"✗ GPIO controller file not found: {gpio_file}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Memory map loading failed: {e}")
        return False

def test_gui_components():
    """Test that GUI components can be created."""
    print("\nTesting GUI components...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create main window
        window = MainWindow()
        print("✓ Main window created successfully")
        
        # Don't show the window in this test, just verify it can be created
        return True
    except Exception as e:
        print(f"✗ GUI component creation failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Memory Map Editor - Component Test")
    print("=" * 40)
    
    success = True
    success &= test_imports()
    success &= test_memory_map_loading()
    success &= test_gui_components()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed! The memory map editor should work correctly.")
    else:
        print("✗ Some tests failed. Please check the error messages above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

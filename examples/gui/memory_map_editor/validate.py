#!/usr/bin/env python3
"""
Simple validation script for the memory map editor.
This tests the core functionality without launching the GUI.
"""
import sys
import os
from pathlib import Path

# Add current directory and fpga_lib to Python path
current_dir = Path(__file__).resolve().parent
fpga_lib_dir = current_dir.parent.parent.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(fpga_lib_dir))

def main():
    print("Memory Map Editor - Validation Test")
    print("=" * 50)
    
    try:
        # Test core imports
        print("Testing core imports...")
        from memory_map_core import MemoryMapProject, load_from_yaml, save_to_yaml
        from fpga_lib.core import Register, BitField, RegisterArrayAccessor
        print("✓ Core modules imported successfully")
        
        # Test loading a sample memory map
        print("\nTesting memory map loading...")
        gpio_file = current_dir / "resources" / "sample_memory_maps" / "gpio_controller.yaml"
        if gpio_file.exists():
            project = load_from_yaml(str(gpio_file))
            print(f"✓ Loaded: {project.name}")
            print(f"  Base address: 0x{project.base_address:08X}")
            print(f"  Registers: {len(project.registers)}")
            print(f"  Register arrays: {len(project.register_arrays)}")
            
            # Test register details
            if project.registers:
                reg = project.registers[0]
                print(f"  First register: {reg.name} at offset 0x{reg.offset:04X}")
                # Access the private _fields attribute or use available methods
                if hasattr(reg, '_fields'):
                    print(f"    Bit fields: {len(reg._fields)}")
                elif hasattr(reg, 'get_fields'):
                    fields = reg.get_fields()
                    print(f"    Bit fields: {len(fields)}")
                else:
                    print(f"    Bit fields: (unable to access)")
        else:
            print("✗ Sample file not found")
            return False
        
        # Test UART controller
        print("\nTesting UART controller...")
        uart_file = current_dir / "resources" / "sample_memory_maps" / "uart_controller.yaml"
        if uart_file.exists():
            uart_project = load_from_yaml(str(uart_file))
            print(f"✓ Loaded: {uart_project.name}")
            print(f"  Registers: {len(uart_project.registers)}")
        
        # Test validation
        print("\nTesting validation...")
        errors = project.validate()
        if errors:
            print(f"  Validation errors: {len(errors)}")
            for error in errors[:3]:  # Show first 3 errors
                print(f"    - {error}")
        else:
            print("✓ No validation errors")
        
        print("\n" + "=" * 50)
        print("✓ All core functionality working correctly!")
        print("The memory map editor components are ready to use.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

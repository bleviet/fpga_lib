#!/usr/bin/env python3
"""
Path debugging script
"""
import sys
from pathlib import Path

print("=== Path Debug Info ===")
print("Current file:", __file__)
current_dir = Path(__file__).parent
print("Current dir:", current_dir)

fpga_lib_root = Path(__file__).parent.parent.parent.parent
print("fpga_lib_root calculated:", fpga_lib_root)
print("fpga_lib_root exists:", fpga_lib_root.exists())

fpga_lib_module_dir = fpga_lib_root / 'fpga_lib'
print("fpga_lib module dir:", fpga_lib_module_dir)
print("fpga_lib module dir exists:", fpga_lib_module_dir.exists())

# Check what's in the fpga_lib_root
if fpga_lib_root.exists():
    print("Contents of fpga_lib_root:")
    for item in fpga_lib_root.iterdir():
        if item.is_dir():
            print(f"  DIR:  {item.name}")
        else:
            print(f"  FILE: {item.name}")

# Try import
sys.path.insert(0, str(fpga_lib_root))
sys.path.insert(0, str(current_dir))

print("\nTrying import...")
try:
    import fpga_lib
    print("✓ fpga_lib imported successfully")
    print("fpga_lib location:", fpga_lib.__file__)
except ImportError as e:
    print("✗ fpga_lib import failed:", e)

try:
    from fpga_lib.core import Register
    print("✓ fpga_lib.core.Register imported successfully")
except ImportError as e:
    print("✗ fpga_lib.core.Register import failed:", e)

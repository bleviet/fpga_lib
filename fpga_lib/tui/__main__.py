#!/usr/bin/env python3
"""
Launch script for Memory Map Editor TUI.

Usage:
    python -m fpga_lib.tui examples/ip/my_timer_core.memmap.yml
"""

from fpga_lib.tui.app import MemoryMapEditorApp
from pathlib import Path
import sys

if __name__ == "__main__":
    file_path = None
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

    app = MemoryMapEditorApp(file_path=file_path)
    app.run()

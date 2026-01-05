#!/usr/bin/env python3
"""Terminal UI for memory map editing."""
import sys
from pathlib import Path

# Add fpga_lib to path
repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tui.app import MemoryMapEditorApp

if __name__ == "__main__":
    file_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    app = MemoryMapEditorApp(file_path)
    app.run()

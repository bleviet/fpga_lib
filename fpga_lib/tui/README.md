# Memory Map Editor TUI

A terminal-based UI for editing memory map YAML files, built with [Textual](https://textual.textualize.io/).

## Installation

First install the TUI dependencies:

```bash
pip install textual rich
```

## Usage

Launch the editor with a memory map file:

```bash
python -m fpga_lib.tui examples/ip/my_timer_core.memmap.yml
```

Or start with an empty editor:

```bash
python -m fpga_lib.tui
```

## Features

- **Tree navigation** (left pane): Browse memory maps, address blocks, and registers
- **Detail editor** (right pane): Edit register properties and bit fields
- **Bit visualizer**: Visual 32-bit representation with reset values
- **Keyboard shortcuts**:
  - `Ctrl+H`: Focus outline tree
  - `Ctrl+L`: Focus detail pane
  - `Ctrl+S`: Save (placeholder)
  - `Ctrl+Q`: Quit

## Current Status

✅ YAML parsing and tree population
✅ Register detail display
✅ Bit field table
✅ 32-bit visualizer with reset values
⏳ Full editing support (add/remove fields)
⏳ YAML serialization (save back to file)

See [TUI_DESIGN_PLAN.md](../../docs/TUI_DESIGN_PLAN.md) for the full design.

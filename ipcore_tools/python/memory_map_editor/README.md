# Memory Map Editor Application

A complete visual editor for FPGA memory map definitions using Python and Qt.

## Overview

This application provides a graphical interface for creating, editing, and managing memory map definitions for FPGA IP cores. It integrates with the ipcore_lib.core system to provide a seamless development experience.

## Features

- **Memory Map Project Management**: Create, open, and save memory map projects
- **Visual Register Navigation**: Tree-based outline view of all registers and arrays
- **Detailed Register Editing**: Form-based editing of register properties and bit fields
- **Bit Field Visualization**: Visual representation of register bit layouts
- **YAML Import/Export**: Human-readable configuration file format
- **Integration**: Works with existing ipcore_lib.core Register and BitField classes

## Requirements

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (recommended)

## Installation

1. Install dependencies using uv:
```bash
# From project root
uv sync
```

2. Ensure `ipcore_lib` is installed in editable mode (handled by `uv sync` if configured in pyproject.toml).

---

## Terminal UI (TUI)

A lightweight terminal-based editor for quick edits and SSH sessions.

### Running the TUI

```bash
# From project root
uv run ipcore_tools/python/memory_map_editor/tui_main.py [path/to/file.mm.yml]
```

### TUI Features

- **Vim-style navigation** (hjkl keys)
- **Tree navigation** of memory maps and registers
- **Inline editing** of bit fields
- **32-bit visualizer** with reset values
- **Undo/Redo** support
- **Works over SSH** - no GUI required

See [tui/README.md](tui/README.md) for detailed TUI documentation.

---

## Desktop GUI

A full-featured PyQt6 application for visual memory map editing.

```bash
# From project root
uv run ipcore_tools/python/memory_map_editor/main.py
```

### Creating a New Memory Map

1. Launch the application
2. Use File → New to create a new memory map project
3. Set the project name, description, and base address
4. Add registers using the toolbar or Edit menu
5. Configure bit fields for each register
6. Save your project as a YAML file

### Opening Sample Memory Maps

Sample memory maps are available in the `ipcore_spec/examples/` directory:

**TUI:**
```bash
uv run ipcore_tools/python/memory_map_editor/tui_main.py ipcore_spec/examples/timers/my_timer_core.mm.yml
uv run ipcore_tools/python/memory_map_editor/tui_main.py ipcore_spec/examples/interfaces/gpio/gpio_controller.mm.yml
```

**GUI:**
```bash
uv run ipcore_tools/python/memory_map_editor/main.py
# Then use File → Open to select a .mm.yml file from ipcore_spec/examples/
```

**Available examples:**
- `ipcore_spec/examples/timers/my_timer_core.mm.yml` - Timer with array registers
- `ipcore_spec/examples/interfaces/gpio/gpio_controller.mm.yml` - Simple GPIO controller
- `ipcore_spec/examples/interfaces/uart/uart_controller.mm.yml` - UART controller
- `ipcore_spec/examples/interfaces/dma/dma_engine.mm.yml` - Complex DMA engine
- `ipcore_spec/examples/networking/ethernet_mac.mm.yml` - Ethernet MAC controller

### Interface Components

#### Main Window
- **Menu Bar**: File operations, edit commands, view options, help
- **Toolbar**: Quick access to common operations
- **Splitter Layout**: Resizable panes for optimal workspace organization

#### Memory Map Outline (Left Pane)
- Tree view of all registers and register arrays
- Right-click context menu for adding/removing registers
- Keyboard shortcuts for navigation

#### Register Detail Form (Right Pane)
- **Properties Tab**: Register name, offset, description, access mode
- **Bit Fields Tab**: Table view for editing individual bit fields
- **Visualization**: Graphical representation of bit field layout

## Memory Map YAML Format

The application uses a standard YAML format for memory map definitions:

```yaml
name: "Controller Name"
description: "Controller description"
base_address: 0x40000000

registers:
  - name: control_reg
    offset: 0x00
    description: "Control register"
    fields:
      - name: enable
        bit: 0
        access: rw
        description: "Enable bit"
      - name: mode
        bits: '[3:1]'
        access: rw
        description: "Operating mode"
  
  - name: data_array
    offset: 0x100
    count: 16
    stride: 4
    description: "Data register array"
    fields:
      - name: value
        bits: '[31:0]'
        access: rw
        description: "Data value"
```

### Field Specifications

- **Single Bit**: `bit: 0` or `bits: '0'`
- **Bit Range**: `bits: '[7:0]'` (MSB:LSB format)
- **Access Modes**: `r` (read-only), `w` (write-only), `rw` (read-write), `rw1c` (read-write-1-to-clear)

## Architecture

The application follows the Model-View-Controller (MVC) pattern:

### Model Layer (`memory_map_core.py`)
- `MemoryMapProject`: Core data model for memory map projects
- YAML serialization/deserialization functions
- Integration with ipcore_lib.core classes

### View Layer (`gui/` package)
- `MainWindow`: Primary application window with menus and layout
- `MemoryMapOutline`: Tree widget for register navigation
- `RegisterDetailForm`: Property editor with forms and tables
- `BitFieldVisualizerWidget`: Custom Qt widget for bit field visualization

### Controller Layer
- Qt signals and slots provide communication between components
- Event handling for user interactions
- Data validation and error handling

## Extending the Application

### Adding New Register Types

1. Extend the `MemoryMapProject` class to support new register types
2. Update the YAML serialization functions
3. Add UI components in the detail form as needed

### Custom Bit Field Visualizations

The `BitFieldVisualizerWidget` can be extended to support:
- Different color schemes
- Interactive bit selection
- Tooltip information
- Export to image formats

### Integration with HDL Generators

The memory map data can be used to drive:
- SystemVerilog register file generation
- C header file creation
- Documentation generation
- Verification testbench creation

## Development

### Project Structure

```
memory_map_editor/
├── gui/                       # Desktop GUI (PyQt6)
│   ├── __init__.py
│   ├── main_window.py         # Main application window
│   ├── memory_map_outline.py  # Register tree view
│   ├── register_detail_form.py # Property editor
│   ├── register_properties_widget.py
│   ├── bit_field_table_widget.py
│   ├── bit_field_visualizer.py # Bit field visualization
│   ├── bit_field_operations.py
│   └── delegates.py
├── tui/                       # Terminal UI (Textual)
│   ├── __init__.py
│   ├── app.py                 # TUI application
│   └── README.md              # TUI-specific docs
├── main.py                    # GUI entry point
├── tui_main.py                # TUI entry point
├── memory_map_core.py         # Core data model (shared)
├── debug_mode.py              # Debug functionality (shared)
├── validate.py                # Validation utility
└── requirements.txt           # Dependencies
```

### Testing

Test with sample memory maps from ipcore_spec:

**GUI:**
```bash
python main.py
# File → Open → ../../../ipcore_spec/examples/timers/my_timer_core.mm.yml
```

**TUI:**
```bash
python tui_main.py ../../../ipcore_spec/examples/timers/my_timer_core.mm.yml
```

### Contributing

When contributing to this application:

1. Follow PEP 8 style guidelines
2. Add type hints for new functions
3. Update documentation for new features
4. Test with multiple memory map configurations
5. Ensure Qt signals/slots are properly connected

## Troubleshooting

### Common Issues

**Import Error**: Ensure ipcore_lib is in your Python path
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/ipcore_lib"
```

**Qt Application Not Starting**: Verify PySide6 installation
```bash
python -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"
```

**YAML Parsing Error**: Check YAML syntax and indentation
- Use spaces, not tabs
- Ensure proper list formatting
- Validate against sample files

### Performance

For large memory maps (>1000 registers):
- Use lazy loading in the tree view
- Implement virtual scrolling for bit field tables
- Consider pagination for register arrays

## Future Enhancements

- **Undo/Redo**: Command pattern for edit operations
- **Search/Filter**: Find registers by name or address
- **Validation**: Real-time checking of address conflicts
- **Templates**: Pre-defined register templates for common patterns
- **Export Formats**: Generate HDL, C headers, documentation
- **Version Control**: Git integration for memory map versioning

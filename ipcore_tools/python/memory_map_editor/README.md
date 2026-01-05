# Memory Map Editor Application

A complete visual editor for FPGA memory map definitions using Python and Qt.

## Overview

This application provides a graphical interface for creating, editing, and managing memory map definitions for FPGA IP cores. It integrates with the fpga_lib.core system to provide a seamless development experience.

## Features

- **Memory Map Project Management**: Create, open, and save memory map projects
- **Visual Register Navigation**: Tree-based outline view of all registers and arrays
- **Detailed Register Editing**: Form-based editing of register properties and bit fields
- **Bit Field Visualization**: Visual representation of register bit layouts
- **YAML Import/Export**: Human-readable configuration file format
- **Integration**: Works with existing fpga_lib.core Register and BitField classes

## Requirements

```
PySide6
PyYAML
fpga_lib
```

## Installation

1. Install dependencies:
```bash
pip install PySide6 PyYAML
```

2. Ensure fpga_lib is available in your Python path

## Usage

### Running the Application

```bash
cd examples/gui/memory_map_editor
python main.py
```

### Creating a New Memory Map

1. Launch the application
2. Use File → New to create a new memory map project
3. Set the project name, description, and base address
4. Add registers using the toolbar or Edit menu
5. Configure bit fields for each register
6. Save your project as a YAML file

### Opening Sample Memory Maps

The application includes several sample memory maps in the `resources/sample_memory_maps/` directory:

- `gpio_controller.yaml` - Simple GPIO controller with input/output registers
- `uart_controller.yaml` - UART controller with configuration and data registers
- `dma_engine.yaml` - Complex DMA engine with descriptor rings
- `ethernet_mac.yaml` - Ethernet MAC controller with buffer descriptors

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
- Integration with fpga_lib.core classes

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
├── main.py                    # Application entry point
├── memory_map_core.py         # Core data model
├── gui/
│   ├── __init__.py
│   ├── main_window.py         # Main application window
│   ├── memory_map_outline.py  # Register tree view
│   ├── register_detail_form.py # Property editor
│   └── bit_field_visualizer.py # Bit field visualization
└── resources/
    └── sample_memory_maps/    # Example memory maps
```

### Testing

The application can be tested with the provided sample memory maps:

```bash
python main.py resources/sample_memory_maps/gpio_controller.yaml
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

**Import Error**: Ensure fpga_lib is in your Python path
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/fpga_lib"
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

---
trigger: always_on
---

# Project Map Template

## [Backend] - Python (uv)

### Entry Points
* `scripts/generate_vhdl.py`: CLI tool for IP Core YAML parsing and VHDL/testbench generation.
* `pyproject.toml`: Dependency definitions and project configuration.

### Core Library (`fpga_lib/`)
* **Models** (`model/`): Pydantic schemas (base, bus, clock_reset, core, fileset, memory, port, validators).
* **Parsers** (`parser/`): YAML IP Core parser, VHDL/Verilog parsers (deprecated).
* **Generators** (`generator/`): Base generator, VHDL generator with Jinja2 templates.
* **Runtime** (`runtime/`): Register access classes (Register, BitField, RegisterArrayAccessor).
* **Drivers** (`driver/`): Cocotb simulation drivers with AXI-Lite bus interface.
* **Converters** (`converter/`): Format conversion utilities.
* **Utils** (`utils/`): Shared utility functions.
* **Tests** (`tests/`): Test suite mirroring source structure.

### Tools (`ipcore_tools/`)
* **Memory Map Editor** (`python/memory_map_editor/`): PyQt6 GUI and Textual TUI editors.
* **VSCode Extension** (`vscode/ipcore_editor/`): TypeScript extension for visual editing.

### Specifications (`ipcore_spec/`)
* **Schemas** (`schemas/`): JSON schemas for IP Core and Memory Map validation.
* **Templates** (`templates/`): YAML templates for common patterns.
* **Examples** (`examples/`): Reference implementations.
* **Common** (`common/`): Shared definitions and file sets.

_[Agent: Update above sections when adding new modules]_

## [VSCode Extension] - TypeScript (npm)

### Location
* `ipcore_tools/vscode/ipcore_editor/`

### Structure
* `package.json`: Extension manifest with commands and custom editors.
* `src/extension.ts`: Activation handler.
* `src/providers/`: Custom editor providers.
* `src/commands/`: Command implementations.
* `src/services/`: Core services (document management, validation, generation).
* `src/generator/`: TypeScript VHDL generator with Nunjucks templates.
* `src/webview/`: React-based visual editors.

_[Agent: Update when adding new TS modules]_

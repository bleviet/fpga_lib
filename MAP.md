# Project Map & Architecture

## [Backend] - Python (uv)

* **Entry Point:** `run_gen.py` - CLI tool that parses IP Core YAML and generates VHDL/testbench files.
* **Schema Models:** `fpga_lib/model/` - Pydantic models for IP cores, memory maps, buses, clocks, resets, ports, and file sets (YAML validation).
* **Runtime I/O:** `fpga_lib/runtime/` - Hardware register access classes (Register, BitField, RegisterArrayAccessor) for drivers and testbenches.
* **Parsers:** `fpga_lib/parser/yaml/` - `YamlIpCoreParser` for IP core YAML; `fpga_lib/parser/hdl/` - VHDL/Verilog parsers (deprecated).
* **Generators:** `fpga_lib/generator/hdl/vhdl_generator.py` - Jinja2-based VHDL code generator for packages, cores, bus wrappers, testbenches.
* **Drivers:** `fpga_lib/driver/` - Runtime drivers for Cocotb simulation with AXI-Lite bus interface.
* **Converters:** `fpga_lib/converter/` - Format conversion utilities.
* **Tests:** `fpga_lib/tests/` - Test suite with core, generator, model, and parser tests.
* **Dependencies:** pydantic, jinja2, pyyaml, pyparsing, textual, PySide6 (see `pyproject.toml`).

---

## [Tools] - Standalone Applications

### VSCode Extension (`ipcore_tools/vscode/ipcore_editor/`)
* **Manifest:** `package.json` - Extension configuration, commands, and custom editors.
  * **Commands:** `createIpCore`, `createMemoryMap`, `generateVHDL`, `generateVHDLWithBus`
  * **Custom Editors:** `fpgaMemoryMap.editor` (*.memmap.yml), `fpgaIpCore.editor` (*.yml)
* **Entry Point:** `src/extension.ts` - Registers custom editor providers and commands on activation.
* **Providers:** `src/providers/` - `MemoryMapEditorProvider`, `IpCoreEditorProvider` for visual YAML editing.
* **Commands:** `src/commands/` - `FileCreationCommands.ts`, `GenerateCommands.ts` for file scaffolding and VHDL generation.
* **Services:** `src/services/` - `DocumentManager`, `HtmlGenerator`, `ImportResolver`, `MessageHandler`, `YamlValidator`.
* **Generator:** `src/generator/` - TypeScript reimplementation of VHDL generator with Nunjucks templates.
* **Webview:** `src/webview/` - React-based UI components for custom editors.

### Memory Map Editor (`ipcore_tools/python/memory_map_editor/`)
* `main.py`: PyQt6 standalone GUI application.
* `tui_main.py`: Textual-based TUI application.
* `gui/`: PyQt6 widgets and components.
* `tui/`: Textual components and screens.
* `memory_map_core.py`: Core memory map data structures and logic.

---

---

## [Specifications] - IP Core & Memory Map Definitions

* **Location:** `ipcore_spec/`
* **Schemas:** `schemas/` - JSON schemas for IP Core (`ip_core.schema.json`) and Memory Map (`memory_map.schema.json`) validation.
* **Templates:** `templates/` - YAML templates for common patterns (AXI slave, basic, minimal, arrays, multi-block).
* **Examples:** `examples/` - Reference implementations (interfaces, networking, timers, test cases).
* **Common:** `common/` - Shared bus definitions and file sets.

---

## [Cross-Domain Bridge]

**No direct runtime bridge exists.** The VSCode extension and Python backend are independent implementations sharing:

1. **Templates:** `npm run sync-templates` copies Jinja2 templates from `fpga_lib/generator/hdl/templates/` to `ipcore_tools/vscode/ipcore_editor/src/generator/templates/`.
2. **YAML Schema:** Both use the same IP Core and Memory Map YAML format defined in `ipcore_spec/schemas/`.
3. **Dual Implementation:** VHDL generation exists in both Python (`fpga_lib/generator/hdl/vhdl_generator.py`) and TypeScript (`ipcore_tools/vscode/ipcore_editor/src/generator/`).

The extension operates standalone without calling the Python backend at runtime.

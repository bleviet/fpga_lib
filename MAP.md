# Project Map & Architecture

## [Backend] - Python (uv)

* **Entry Point:** `run_gen.py` - CLI tool that parses IP Core YAML and generates VHDL/testbench files.
* **Schema Models:** `fpga_lib/model/` - Pydantic models for IP cores, memory maps, buses, clocks, resets, ports, and file sets (YAML validation).
* **Runtime I/O:** `fpga_lib/runtime/` - Hardware register access classes (Register, BitField, RegisterArrayAccessor) for drivers and testbenches.
* **Parsers:** `fpga_lib/parser/yaml/` - `YamlIpCoreParser` for IP core YAML; `fpga_lib/parser/hdl/` - VHDL/Verilog parsers (deprecated).
* **Generators:** `fpga_lib/generator/hdl/vhdl_generator.py` - Jinja2-based VHDL code generator for packages, cores, bus wrappers, testbenches.
* **Drivers:** `fpga_lib/driver/` - Runtime drivers for Cocotb simulation with AXI-Lite bus interface.
* **Memory Map Editor:** `ipcore_tools/python/memory_map_editor/` - Standalone GUI (PyQt6) and TUI (Textual) for editing memory maps.
* **Dependencies:** pydantic, jinja2, pyyaml, pyparsing, textual, PySide6 (see `pyproject.toml`).

---

## [Tools] - Standalone Applications

### VSCode Extension (`ipcore_tools/vscode/ipcore_editor/`)
* `package.json`: Extension manifest and configuration.
* `src/extension.ts`: Main activation handler.
* `src/providers/`: Custom editor providers for `.ip.yml` and `.mm.yml` files.
* `src/webview/`: React-based visual editors (IP Core & Memory Map).
* `src/generator/`: VHDL and testbench generation.

### Memory Map Editor (`ipcore_tools/python/memory_map_editor/`)
* `main.py`: PyQt6 standalone GUI application.
* `tui_main.py`: Textual-based TUI application.
* `gui/`: PyQt6 widgets and components.
* `tui/`: Textual components and screens.

---

## [VSCode Extension] - TypeScript (npm)

## [Backend] - Python (uv)

* **Manifest:** `vscode-extension/package.json`
  * **Commands:** `createIpCore`, `createMemoryMap`, `generateVHDL`, `generateVHDLWithBus`
  * **Custom Editors:** `fpgaMemoryMap.editor` (*.memmap.yml), `fpgaIpCore.editor` (*.yml)

* **Entry Point:** `vscode-extension/src/extension.ts` - Registers custom editor providers and commands on activation.
* **Providers:** `src/providers/` - `MemoryMapEditorProvider`, `IpCoreEditorProvider` for visual YAML editing.
* **Commands:** `src/commands/` - `FileCreationCommands.ts`, `GenerateCommands.ts` for file scaffolding and VHDL generation.
* **Services:** `src/services/` - `DocumentManager`, `HtmlGenerator`, `ImportResolver`, `MessageHandler`, `YamlValidator`.
* **Generator:** `src/generator/` - TypeScript reimplementation of VHDL generator with Nunjucks templates.
* **Webview:** `src/webview/` - React-based UI components for custom editors.

---

## [Cross-Domain Bridge]

**No direct runtime bridge exists.** The extension and Python backend are independent implementations sharing:

1. **Templates:** `npm run sync-templates` copies Jinja2 templates from `fpga_lib/generator/hdl/templates/` to `src/generator/templates/`.
2. **YAML Schema:** Both use the same IP Core and Memory Map YAML format defined in `vscode-extension/schemas/`.
3. **Dual Implementation:** VHDL generation exists in both Python (`VHDLGenerator`) and TypeScript (`src/generator/`).

The extension operates standalone without calling the Python backend at runtime.

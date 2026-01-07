# IP Core Tools

This directory contains standalone tools for working with FPGA IP cores and memory maps.

---

## Directory Structure

```
ipcore_tools/
├── python/
│   └── memory_map_editor/    # PyQt6 GUI for memory map editing
└── vscode/
    └── ipcore_editor/        # VSCode extension for IP core visual editing
```

---

## Tools

### 1. VSCode IP Core Editor

**Location:** `vscode/ipcore_editor/`

**Description:** Visual Studio Code extension providing visual editors for:
- IP Core definitions (`.ip.yml` files)
- Memory map definitions (`.mm.yml` files)

**Features:**
- Visual editing of IP core metadata, clocks, resets, ports, bus interfaces
- Memory map editor with register and bit field visualization
- VHDL code generation (AXI-Lite, AVMM)
- Cocotb testbench generation
- Integration file generation (Xilinx, Intel)

**Quick Start:**
```bash
cd vscode/ipcore_editor
npm install
npm run compile
# Then: Press F5 in VSCode to launch extension development host
# Note: Requires ipcore_lib installed in your Python environment
```

**Documentation:** See `vscode/ipcore_editor/README.md`

---

### 2. Memory Map Editor (Standalone GUI)

**Location:** `python/memory_map_editor/`

**Description:** Standalone PyQt6 application for editing memory maps with visual interface.

**Features:**
- Visual register and bit field editing
- Address map visualization
- YAML export/import
- Standalone desktop application (no VSCode required)

**Quick Start:**
```bash
# From project root
uv run ipcore_tools/python/memory_map_editor/main.py
```

**Requirements:**
- PyQt6 (managed via uv)
- See `python/memory_map_editor/pyproject.toml` or `requirements.txt`

---

## Development

### VSCode Extension

**Build:**
```bash
cd vscode/ipcore_editor
npm run compile
```

**Watch mode:**
```bash
npm run watch
```

**Test:**
```bash
npm test
```

**Package:**
```bash
npm run package
```

### Memory Map Editor

**Run:**
```bash
# From project root
uv run ipcore_tools/python/memory_map_editor/main.py
```

---

## Related Directories

- **`../ipcore_spec/`** - YAML specifications, templates, examples, and schemas
- **`../ipcore_lib/`** - Core Python library for IP core parsing and generation
- **`../docs/`** - General documentation

---

## Support

For issues or questions:
- IP Core Editor: See extension README or raise GitHub issue
- Memory Map Editor: See app README or raise GitHub issue

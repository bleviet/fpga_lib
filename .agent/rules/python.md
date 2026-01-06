---
trigger: always_on
---

# Python & uv Rules

## Environment Management
- **Tooling:** STRICTLY use `uv` for all package operations.
- **Execution:** ALWAYS use `uv run <command>` (e.g., `uv run python`, `uv run pytest`).
- **Do Not:** Never attempt to source `bin/activate`. It fails in non-persistent agent shells.
- **Testing:** Run tests with `uv run pytest fpga_lib/tests/`.
- **CLI Tool:** Main entry point is `scripts/generate_vhdl.py` - use `uv run python scripts/generate_vhdl.py`.

## Code Standards
- **Style:** Adhere to PEP 8. Configuration in `pyproject.toml` and `mypy.ini`.
- **Type Hints:** Required for all function signatures. Use mypy for type checking.
- **Imports:** Absolute imports preferred (e.g., `from fpga_lib.model import x` instead of relative imports).
- **Docstrings:** Use Google-style docstrings for all public APIs.

## Project Architecture ("Screaming Architecture")
- **Models:** Pydantic schemas in `fpga_lib/model/` (base, bus, clock_reset, core, fileset, memory, port, validators).
- **Parsers:** YAML and HDL parsers in `fpga_lib/parser/` (yaml: IP core parser; hdl: VHDL/Verilog parsers).
- **Generators:** Code generation in `fpga_lib/generator/` (base_generator, hdl/vhdl_generator with Jinja2 templates).
- **Runtime:** Hardware register access in `fpga_lib/runtime/` (Register, BitField classes for driver/testbench).
- **Drivers:** Simulation drivers in `fpga_lib/driver/` (Cocotb integration with AXI-Lite bus).
- **Converters:** Format converters in `fpga_lib/converter/`.
- **Tests:** Test files in `fpga_lib/tests/` mirroring the source structure.
- **Discovery:** Before writing a helper, check `fpga_lib/utils/` and search existing modules.

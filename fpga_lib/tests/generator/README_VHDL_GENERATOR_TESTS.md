# VHDL Generator Test Suite

This directory contains comprehensive tests for the VHDLGenerator that ensure it produces correct, syntactically valid VHDL code.

## Test Files

### `test_vhdl_generator.py`
Unit tests for individual generator methods:
- **TestVHDLGeneratorBasic**: Core functionality tests (15 tests)
  - Initialization, package, top, core, bus wrappers
  - Generation of all files, register file inclusion
- **TestVHDLGeneratorWithRegisters**: Tests with memory maps and registers
  - Simple register generation
  - User-defined ports
- **TestVHDLGeneratorVendorFiles**: Vendor integration file tests
  - Intel Platform Designer `_hw.tcl`
  - Xilinx Vivado `component.xml`
- **TestVHDLGeneratorTestbench**: Testbench generation tests
  - cocotb test file
  - Makefile generation
  - All testbench files

### `test_vhdl_generator_e2e.py`
End-to-end tests using actual example YAML files:
- **TestVHDLGeneratorE2E**: Full pipeline tests (5 tests)
  - Parse minimal/basic/timer YAML examples
  - Generate complete VHDL outputs
  - Verify testbench and vendor file generation
- **TestVHDLGeneratorSyntaxValidation**: GHDL syntax checks (marked `@pytest.mark.slow`)
  - Validate generated VHDL with GHDL `--std=08`
  - Requires GHDL installed (skipped if not available)

## Running Tests

### Run all generator tests:
```bash
cd /home/balevision/workspace/bleviet/fpga_lib
PYTHONPATH=/home/balevision/workspace/bleviet/fpga_lib uv run pytest fpga_lib/tests/generator/hdl/ -v
```

### Run only unit tests:
```bash
PYTHONPATH=/home/balevision/workspace/bleviet/fpga_lib uv run pytest fpga_lib/tests/generator/hdl/test_vhdl_generator.py -v
```

### Run only end-to-end tests:
```bash
PYTHONPATH=/home/balevision/workspace/bleviet/fpga_lib uv run pytest fpga_lib/tests/generator/hdl/test_vhdl_generator_e2e.py -v
```

### Run syntax validation tests (requires GHDL):
```bash
PYTHONPATH=/home/balevision/workspace/bleviet/fpga_lib uv run pytest fpga_lib/tests/generator/hdl/test_vhdl_generator_e2e.py::TestVHDLGeneratorSyntaxValidation -v
```

### Skip slow tests:
```bash
PYTHONPATH=/home/balevision/workspace/bleviet/fpga_lib uv run pytest fpga_lib/tests/generator/hdl/ -v -m "not slow"
```

## Test Coverage

Current coverage:
- ✅ **15/15** unit tests passing
- ✅ **4/5** E2E tests passing (1 fails due to missing example file)
- ⏳ **0/2** syntax validation tests (require GHDL installation)

### What's Tested

**Generation Methods:**
- `generate_package()` - VHDL package with register types
- `generate_top()` - Top-level entity with bus interface
- `generate_core()` - Bus-agnostic core logic
- `generate_bus_wrapper()` - AXI-Lite and Avalon-MM wrappers
- `generate_register_file()` - Standalone register file
- `generate_all()` - Complete file set

**Vendor Integration:**
- `generate_intel_hw_tcl()` - Intel Platform Designer TCL
- `generate_xilinx_component_xml()` - Xilinx IP-XACT XML
- `generate_vendor_files()` - Batch vendor file generation

**Testbench:**
- `generate_cocotb_test()` - cocotb Python test
- `generate_cocotb_makefile()` - GHDL Makefile
- `generate_memmap_yaml()` - Driver memory map
- `generate_testbench()` - Complete testbench set

**End-to-End:**
- Parsing example YAML files
- Generating all outputs
- Content validation (non-empty, expected patterns)

### What's NOT Tested (Yet)

- ❌ **VHDL Syntax Validation**: GHDL syntax checks (need GHDL installed)
- ❌ **Simulation**: Running generated cocotb tests
- ❌ **Template Coverage**: Ensuring all templates render without errors
- ❌ **Functional Verification**: Register access correctness in simulation

## Adding New Tests

### Unit Test Pattern

```python
def test_new_feature(self):
    """Test description."""
    ip_core = IpCore(
        api_version="test/v1.0",
        vlnv=VLNV(vendor="test", library="lib", name="test_ip", version="1.0"),
        # ... add required fields
    )
    
    generator = VHDLGenerator()
    result = generator.generate_something(ip_core)
    
    assert result is not None
    assert "expected content" in result
```

### E2E Test Pattern

```python
def test_new_yaml_example(self, example_dir, parser, generator):
    """Test with new example."""
    yaml_file = example_dir / "path" / "to" / "example.ip.yml"
    
    if not yaml_file.exists():
        pytest.skip(f"Example file not found: {yaml_file}")
    
    ip_core = parser.parse_file(str(yaml_file))
    files = generator.generate_all(ip_core, bus_type='axil')
    
    # Verify expected outputs
    assert len(files) >= 4
    # ... additional assertions
```

## Dependencies

- **pytest**: Test framework
- **pydantic**: Data validation
- **jinja2**: Template engine
- **pyyaml**: YAML parsing
- **GHDL** (optional): For syntax validation tests

## Known Issues

1. **Timer example test fails**: `my_timer_core.ip.yml` references missing `common/c_api.fileset.yml`
2. **GHDL tests skipped**: Syntax validation requires GHDL installation
3. **PYTHONPATH required**: Tests need explicit PYTHONPATH until package is properly installed

## Future Work

1. **Install package in editable mode**: Fix `pyproject.toml` to allow `uv pip install -e .`
2. **Add GHDL CI check**: Run syntax validation in CI if GHDL available
3. **Simulation tests**: Run generated cocotb testbenches with GHDL
4. **Template coverage**: Test all 13 templates render without errors
5. **Functional tests**: Verify register behavior in simulation

# FPGA Library Tests

This directory contains the test suite for the FPGA library components.

## Test Structure

### Core Tests (`fpga_lib/tests/core/`)
Tests for the core register and IP core functionality:

- `test_register_rw1c.py` - Tests for the rw1c (read-write-1-to-clear) access type functionality
- `test_ip_core.py` - Tests for IP core base functionality

### GPIO Example Tests (`examples/gpio/tests/`)
Tests for the GPIO example and memory map loader:

- `test_memory_map_rw1c.py` - Tests for YAML memory map loader with rw1c support
- `resources/` - Test data files for GPIO tests
  - `test_rw1c_controller.yaml` - Sample YAML file with rw1c fields

## Running Tests

### Individual Test Files
```bash
# Run core register tests
cd /path/to/fpga_lib
uv run python fpga_lib/tests/core/test_register_rw1c.py

# Run GPIO memory map loader tests  
cd examples/gpio
uv run python tests/test_memory_map_rw1c.py
```

### Using pytest (recommended)
```bash
# Run all core tests
uv run pytest fpga_lib/tests/core/ -v

# Run specific test file
uv run pytest fpga_lib/tests/core/test_register_rw1c.py -v
```

## Test Coverage

The tests cover:

1. **RW1C Access Type**: 
   - Single bit clearing
   - Multi-bit field partial clearing
   - Write-0-no-effect behavior
   - Mixed access types in same register

2. **YAML Memory Map Loading**:
   - YAML validation with rw1c fields
   - Driver creation from YAML
   - Field access type conversion
   - Runtime rw1c behavior

3. **Integration Testing**:
   - Core register module with memory map loader
   - Dynamic field access patterns
   - Bus interface interactions

## Adding New Tests

When adding new test files:

1. Place core functionality tests in `fpga_lib/tests/core/`
2. Place example-specific tests in `examples/{example}/tests/`
3. Use descriptive test names following the pattern `test_{component}_{feature}.py`
4. Include both unittest and standalone execution support
5. Add test data files to appropriate `resources/` subdirectories

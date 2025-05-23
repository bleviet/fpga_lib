# fpga_lib

A Python library for working with FPGA designs, including HDL parsing, generation, and manipulation.

## Features

- Parse VHDL entity declarations and Verilog module declarations
- Generate VHDL code from an internal representation
- Convert between VHDL and Verilog representations
- Object-oriented representation of IP cores, interfaces, and ports
- Support for various data types and constraints

## Installation

### Prerequisites

- Python 3.7 or higher

### Install from source

Clone the repository and install the package:

```bash
git clone <repository-url>
cd fpga_lib
pip install -e .
```

### Install dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Example: Creating an IP Core

```python
from fpga_lib.core.ip_core import IPCore
from fpga_lib.generator.hdl.vhdl_generator import generate_vhdl

# Create a simple IP core
simple_core = IPCore(name="simple_ip")
simple_core.add_port("clk", "in", "std_logic")
simple_core.add_port("rst", "in", "std_logic")
simple_core.add_port("data_in", "in", "std_logic_vector(7 downto 0)")
simple_core.add_port("data_out", "out", "std_logic_vector(7 downto 0)")

# Generate VHDL code
vhdl_code = generate_vhdl(simple_core)
print(vhdl_code)
```

### Parsing HDL Files

```python
from fpga_lib.parser.hdl.vhdl_parser import VHDLParser
from fpga_lib.parser.hdl.verilog_parser import VerilogParser

# Parse VHDL
vhdl_parser = VHDLParser()
vhdl_result = vhdl_parser.parse_file("path/to/entity.vhd")
vhdl_ip_core = vhdl_result["entity"]

# Parse Verilog
verilog_parser = VerilogParser()
verilog_result = verilog_parser.parse_file("path/to/module.v")
verilog_ip_core = verilog_result["module"]
```

## Testing

This project uses pytest for testing. There are several test cases covering different components of the library.

### Using the Makefile (Recommended)

The easiest way to run tests is using the provided Makefile:

```bash
# See all available commands
make help

# Run all tests
make test

# Run tests with verbose output
make test-verbose

# Run tests with coverage reporting
make test-coverage

# Run specific test modules
make test-vhdl-parser      # VHDL parser tests only
make test-verilog-parser   # Verilog parser tests only
make test-core             # IP core tests only
make test-generator        # Generator tests only
make test-parser           # All parser tests
make test-roundtrip        # HDL roundtrip tests
```

### Running Tests Manually

You can also run tests directly with pytest:

### Running All Tests

To run all tests:

```bash
python -m pytest
```

### Running Specific Test Modules

To run a specific test module:

```bash
# Run just the VHDL parser tests
python -m pytest fpga_lib/tests/parser/hdl/test_vhdl_parser.py

# Run just the Verilog parser tests
python -m pytest fpga_lib/tests/parser/hdl/test_verilog_parser.py

# Run just the IP core tests
python -m pytest fpga_lib/tests/core/test_ip_core.py
```

### Running Tests with Verbose Output

For more detailed test output:

```bash
python -m pytest -v
```

### Test Coverage

To run tests with coverage reporting:

```bash
python -m pytest --cov=fpga_lib
```

## License

[Specify license information here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

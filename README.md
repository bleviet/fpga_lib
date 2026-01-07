# ipcore_lib

A Python library for working with FPGA designs, including HDL parsing, generation, and manipulation.

## Features

- Parse VHDL entity declarations and Verilog module declarations
- Generate VHDL code from an internal representation
- Convert between VHDL and Verilog representations
- Object-oriented representation of IP cores, interfaces, and ports
- Support for various data types and constraints

## Installation

### Prerequisites

- [uv](https://github.com/astral-sh/uv) (recommended) or Python 3.8+

### Install from source

Clone the repository and install the package using `uv`:

```bash
git clone <repository-url>
cd ipcore_lib
uv sync
```

Or using pip:

```bash
pip install -e .
```

## Usage

### Generating an IP Core

This project includes a CLI tool `ipcore` for generating VHDL from YAML specifications.

```bash
# Generate VHDL for an IP core
uv run scripts/ipcore.py generate path/to/core.ip.yml --output output_dir
```

### Parsing HDL Files

```python
from ipcore_lib.parser.hdl.vhdl_parser import VHDLParser

# Parse VHDL
vhdl_parser = VHDLParser()
vhdl_result = vhdl_parser.parse_file("path/to/entity.vhd")
vhdl_ip_core = vhdl_result["entity"]
```

## Testing

This project uses pytest for testing.

### Using uv (Recommended)

```bash
# Run all tests
uv run pytest

# Run specific test
uv run pytest ipcore_lib/tests/parser/hdl/test_vhdl_parser.py
```

## License

[Specify license information here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

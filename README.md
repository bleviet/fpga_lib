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

### CLI Tool

After installation, the `ipcore` command is available:

```bash
# Generate VHDL for an IP core
ipcore generate path/to/core.ip.yml --output output_dir

# Parse VHDL and create IP core YAML
ipcore parse path/to/entity.vhd

# List available bus types
ipcore list-buses
```

With uv (without installing):
```bash
uv run ipcore generate path/to/core.ip.yml
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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

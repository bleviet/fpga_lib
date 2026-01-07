# IP Core Specifications

YAML specifications for FPGA IP cores and memory maps.

## Directory Structure

```
ipcore_spec/
├── docs/           # Documentation
│   └── IP_YAML_SPEC.md   # IP YAML format specification
├── schemas/        # JSON schemas for validation
├── templates/      # Starter templates
├── examples/       # Real-world examples
└── common/         # Shared definitions (bus types)
```

## Quick Start

1. **New IP Core:** Copy `templates/axi_slave.ip.yml`
2. **New Memory Map:** Copy `templates/basic.mm.yml`
3. **Generate VHDL:** `ipcore generate my_core.ip.yml`

## Documentation

📘 **[IP YAML Specification](docs/IP_YAML_SPEC.md)** - Complete format reference

## Templates

| Template | Description |
|----------|-------------|
| `minimal.ip.yml` | Bare minimum IP core |
| `basic.ip.yml` | Clock, reset, ports |
| `axi_slave.ip.yml` | AXI-Lite slave with registers |
| `basic.mm.yml` | Simple memory map |
| `array.mm.yml` | Register arrays |

## Examples

- `examples/timers/` - Timer with AXI-Lite + AXI-Stream
- `examples/led/` - LED controller
- `examples/test_cases/` - Test configurations

## File Naming

- `*.ip.yml` - IP Core definitions
- `*.mm.yml` - Memory map definitions
- `*.fileset.yml` - File set definitions

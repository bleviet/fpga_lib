# Register Examples

This directory contains examples demonstrating the use of generic register classes from `fpga_lib.core`. These examples show how the same register abstractions can be used across different types of IP cores.

## Examples

### 1. `register_basics.py`
Demonstrates fundamental register and bitfield operations:
- Creating BitFields with different access types (read-only, write-only, read-write)
- Building Registers from BitFields
- Basic read/write operations
- Field validation and error handling
- Reset functionality
- Bulk operations

**Run with:**
```bash
python register_basics.py
```

### 2. `multi_ip_core_demo.py`
Shows register reusability across different IP core types:
- **UART Controller**: Control, status, baud rate, and data registers
- **SPI Controller**: Control, status, and clock divider registers  
- **Timer Peripheral**: Control, value, compare, and status registers

Each IP core uses the same generic `BitField` and `Register` classes from `fpga_lib.core`, demonstrating the power of abstraction.

**Run with:**
```bash
python multi_ip_core_demo.py
```

## Key Benefits Demonstrated

✅ **Reusability**: Same register classes work for any IP core type  
✅ **Consistency**: Uniform API across all register operations  
✅ **Maintainability**: Single source of truth for register logic  
✅ **Type Safety**: Built-in validation and access control  
✅ **Error Handling**: Comprehensive error detection and reporting  
✅ **Documentation**: Self-documenting register definitions  

## Architecture

These examples use the generic register classes from `fpga_lib.core`:

```python
from fpga_lib.core import BitField, Register, AbstractBusInterface
```

- **`BitField`**: Defines individual fields within registers with validation
- **`Register`**: Manages collections of bit fields with bus communication
- **`AbstractBusInterface`**: Provides bus abstraction for different hardware interfaces

## Integration

The register classes demonstrated here are the same ones used by:
- GPIO driver (`examples/gpio/`)
- Any other IP core drivers in your FPGA library
- Custom IP core implementations

This consistent approach reduces learning curve and maintenance burden across your entire FPGA driver ecosystem.

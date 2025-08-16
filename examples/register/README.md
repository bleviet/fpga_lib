# Register Examples

This directory contains examples demonstrating the use of generic register classes from `fpga_lib.core`. These examples show how the same register abstractions can be used across different types of IP cores, including support for register arrays and Block RAM regions.

## Examples

### 1. `register_basics.py`
Demonstrates fundamental register and bitfield operations:
- Creating BitFields with different access types (read-only, write-only, read-write)
- Building Registers from BitFields
- Basic read/write operations
- Field validation and error handling
- Reset functionality
- Bulk operations
- Preview of register array functionality

**Run with:**
```bash
python register_basics.py
```

### 2. `multi_ip_core_demo.py`
Shows register reusability across different IP core types:
- **UART Controller**: Control, status, baud rate, and data registers
- **SPI Controller**: Control, status, and clock divider registers  
- **Timer Peripheral**: Control, value, compare, and status registers
- **Register Array Examples**: Mathematical accelerators, network controllers, audio processors

Each IP core uses the same generic `BitField` and `Register` classes from `fpga_lib.core`, demonstrating the power of abstraction.

**Run with:**
```bash
python multi_ip_core_demo.py
```

### 3. `register_array_example.py` ⭐ NEW
Comprehensive demonstration of register arrays based on the updated concept document:
- **RegisterArrayAccessor**: On-demand register creation for memory efficiency
- **YAML Configuration**: Using `count` and `stride` parameters for Block RAM
- **Lookup Table Example**: 64-entry coefficient table with enable bits
- **Packet Buffer Example**: 16-entry packet buffer with header fields
- **DMA Descriptor Example**: 8-entry descriptor ring for DMA operations
- **Bounds Testing**: Array index validation and error handling

**Features demonstrated:**
- Memory-efficient on-demand register creation
- Pythonic array indexing syntax (`driver.array[index].field`)
- Proper bounds checking with meaningful error messages
- YAML-driven configuration with `count` and `stride`
- Same field validation as single registers

**Run with:**
```bash
python register_array_example.py
```

## Key Benefits Demonstrated

✅ **Reusability**: Same register classes work for any IP core type  
✅ **Consistency**: Uniform API across all register operations  
✅ **Maintainability**: Single source of truth for register logic  
✅ **Type Safety**: Built-in validation and access control  
✅ **Error Handling**: Comprehensive error detection and reporting  
✅ **Documentation**: Self-documenting register definitions  
✅ **Memory Efficiency**: On-demand register creation for large arrays  
✅ **Block RAM Support**: Clean access to structured memory regions  

## Register Arrays (New Feature)

The updated architecture supports register arrays for Block RAM regions:

### YAML Configuration
```yaml
- name: lut_entry
  offset: 0x100
  count: 64          # 64 entries
  stride: 4          # 4 bytes apart
  fields:
    - name: coefficient
      bits: '[15:0]'
      access: rw
```

### Usage
```python
# Pythonic array access
driver.lut_entry[5].coefficient = 0xABCD
driver.lut_entry[10].enabled = 1

# Read values
coeff = driver.lut_entry[5].coefficient

# Array information
print(f"Array length: {len(driver.lut_entry)}")
```

### Benefits
- **Memory Efficient**: Registers created on-demand, not pre-allocated
- **Pythonic**: Natural array indexing with `[]` syntax
- **Type Safe**: Same validation as single registers
- **Scalable**: Handles large Block RAM regions without memory overhead

```python
from fpga_lib.core import BitField, Register, AbstractBusInterface
## Architecture

These examples use the generic register classes from `fpga_lib.core`:

```python
from fpga_lib.core import BitField, Register, AbstractBusInterface
```

### Core Classes
- **`BitField`**: Defines individual fields within registers with validation
- **`Register`**: Manages collections of bit fields with bus communication
- **`RegisterArrayAccessor`**: Provides indexed access to register arrays (new)
- **`AbstractBusInterface`**: Provides bus abstraction for different hardware interfaces

### New: Register Arrays
The `RegisterArrayAccessor` class enables efficient access to Block RAM regions:

```python
class RegisterArrayAccessor:
    """Provides indexed access to a block of registers."""
    def __getitem__(self, index):
        # Creates Register objects on-demand
        item_offset = self._base_offset + (index * self._stride)
        return Register(...)  # On-demand creation
```

## Integration

The register classes demonstrated here are the same ones used by:
- GPIO driver (`examples/gpio/`)
- Any other IP core drivers in your FPGA library
- Custom IP core implementations
- Block RAM and memory-mapped regions

This consistent approach reduces learning curve and maintenance burden across your entire FPGA driver ecosystem, whether dealing with simple control registers or complex memory structures.

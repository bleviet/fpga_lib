# IP Core Specifications

This directory contains YAML specifications for FPGA IP cores and memory maps.

## Directory Structure

- **schemas/** - JSON schemas for validation
- **templates/** - Starter templates for new IP cores
- **examples/** - Real-world IP core examples organized by category
- **common/** - Shared definitions (bus types, file sets)

## File Naming Convention

**To avoid tool detection conflicts:**

- **IP core files:** `<name>.ip.yml` - Contains `apiVersion` and `vlnv` fields
- **Memory map files:** `<name>.mm.yml` - Memory map definitions without IP core metadata
- **File set files:** `<name>.fileset.yml` - File set definitions

**Rationale:** Tools detect IP cores by looking for `apiVersion` and `vlnv` fields. Using distinct extensions prevents memory map files from being incorrectly detected as IP cores.

## IP Core YAML Format

### Basic Structure

```yaml
apiVersion: "1.0"

vlnv:
  vendor: company.com
  library: library_name
  name: core_name
  version: 1.0.0

description: Description of IP core

clocks:
  - name: i_clk            # Physical port name
    logicalName: CLK       # Logical name for associations
    direction: in
    frequency: 100MHz

resets:
  - name: i_rst_n          # Physical port name
    logicalName: RESET_N   # Logical name for associations
    direction: in
    polarity: activeLow

ports:
  - name: o_signal         # Physical port name
    logicalName: signal    # Logical name
    direction: out

busInterfaces: [...]
parameters: [...]
memoryMaps: [...]
fileSets: [...]
```

## Quick Start

1. **New IP Core:** Start with `templates/basic.ip.yml`
2. **AXI Slave:** Use `templates/axi_slave.ip.yml`
3. **Simple Memory Map:** Use `templates/basic.mm.yml`
4. **Multiple Address Blocks:** Use `templates/multi_block.mm.yml`
5. **Register Arrays:** Use `templates/array.mm.yml`

## Templates

### IP Core Templates

- **minimal.ip.yml** - Bare minimum valid IP core (just VLNV)
- **basic.ip.yml** - IP core with clock, reset, and simple ports
- **axi_slave.ip.yml** - Complete AXI-Lite slave with register map

### Memory Map Templates

- **minimal.mm.yml** - Simplest memory map with one register
- **basic.mm.yml** - Memory map with multiple registers and bit fields
- **multi_block.mm.yml** - Multiple address blocks (registers, memory, reserved)
- **array.mm.yml** - Register arrays with count and stride

## Examples by Category

- **Timers:** `examples/timers/` - Timer IP core with AXI-Lite and AXI-Stream
- **Interfaces:** `examples/interfaces/` - GPIO, UART, DMA controller examples
- **Networking:** `examples/networking/` - Ethernet MAC and related cores
- **Test Cases:** `examples/test_cases/` - Test cases for validation

## Common Definitions

- **bus_definitions.yml** - Standard bus type definitions (AXI4L, AXIS, etc.)
- **file_sets/** - Reusable file set definitions

## Key Concepts

### Physical vs Logical Names

- **Physical Name** (`name`): The actual HDL port name (e.g., `i_clk_sys`)
- **Logical Name** (`logicalName`): Internal identifier for associations (e.g., `CLK`)

Bus interfaces use logical names to associate with clocks/resets via the logical name.

### Bus Interfaces

Bus interfaces allow you to define standard protocol interfaces (AXI, AXI-Stream, etc.):

- **physicalPrefix**: Generates port names (e.g., `s_axi_` → `s_axi_awaddr`, `s_axi_wdata`)
- **associatedClock**: Links to physical clock port name
- **associatedReset**: Links to physical reset port name
- **memoryMapRef**: Links to memory map by name
- **portWidthOverrides**: Override default signal widths

### Memory Maps

Memory maps define register address spaces:

- **addressBlocks**: Contiguous regions with different purposes
  - **usage**: `register`, `memory`, or `reserved`
  - **defaultRegWidth**: Default register width (typically 32 bits)
- **Register Arrays**: Use `count` and `stride` to replicate register patterns
- **Bit Fields**: Define individual bits or bit ranges within registers

### Access Types

- `read-write` - Normal read/write register
- `read-only` - Read-only (status, version, etc.)
- `write-only` - Write-only (command registers)
- `write-1-to-clear` - Writing 1 clears the bit (interrupt flags)

## Validation

JSON schemas in `schemas/` can be used to validate your YAML files for correctness.

## Related Documentation

- See `../docs/` for detailed format documentation
- See `../examples/` for additional examples in the original location

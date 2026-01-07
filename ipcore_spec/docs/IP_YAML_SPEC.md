# IP Core YAML Specification

> Author's Guide to defining IP cores and memory maps in YAML format.

## File Conventions

| Extension | Purpose | Detection |
|-----------|---------|-----------|
| `*.ip.yml` | IP Core definition | Contains `apiVersion` + `vlnv` |
| `*.mm.yml` | Memory Map definition | Register/address block definitions |
| `*.fileset.yml` | File Set definition | Importable file lists |

---

## IP Core Structure

### Minimal Example

```yaml
apiVersion: '1.0'
vlnv:
  vendor: company.com
  library: peripherals
  name: my_core
  version: 1.0.0
```

### Complete Example

```yaml
apiVersion: '1.0'
vlnv:
  vendor: my-company.com
  library: processing
  name: my_timer_core
  version: 1.2.0

description: A 4-channel timer IP with AXI-Lite interface

useBusLibrary: ../common/bus_definitions.yml

clocks:
  - name: i_clk_sys           # Physical HDL port name
    logicalName: CLK          # Logical name for associations
    direction: in
    frequency: 100MHz

resets:
  - name: i_rst_n_sys
    logicalName: RESET_N
    direction: in
    polarity: activeLow       # or activeHigh

ports:
  - name: o_irq
    direction: out
    width: 1

busInterfaces:
  - name: S_AXI_LITE
    type: AXI4L
    mode: slave
    physicalPrefix: s_axi_
    associatedClock: i_clk_sys
    associatedReset: i_rst_n_sys
    memoryMapRef: CSR_MAP
    portWidthOverrides:
      AWADDR: 12
      ARADDR: 12

memoryMaps:
  import: my_timer_core.mm.yml

parameters:
  - name: NUM_CHANNELS
    value: 4
    dataType: integer

fileSets:
  - name: RTL_Sources
    files:
      - path: rtl/my_core.vhd
        type: vhdl
```

---

## VLNV (Required)

Every IP core requires a **Vendor-Library-Name-Version** identifier:

```yaml
vlnv:
  vendor: company.com      # Your organization
  library: peripherals     # IP category
  name: timer_core         # Core name (underscore preferred)
  version: 1.0.0           # Semantic version
```

---

## Clocks & Resets

```yaml
clocks:
  - name: i_clk_sys         # Physical port name in HDL
    logicalName: CLK        # Used by associatedClock references
    direction: in
    frequency: 100MHz

resets:
  - name: i_rst_n
    logicalName: RESET_N
    direction: in
    polarity: activeLow     # activeLow | activeHigh
```

---

## Ports

Generic (non-bus) ports:

```yaml
ports:
  - name: o_irq
    direction: out          # in | out | inout
    width: 1
    description: Interrupt output
```

---

## Bus Interfaces

```yaml
busInterfaces:
  - name: S_AXI_LITE
    type: AXI4L             # From bus library: AXI4L, AXIS, AVALON_MM, etc.
    mode: slave             # slave | master
    physicalPrefix: s_axi_  # Generates: s_axi_awaddr, s_axi_wdata, etc.
    associatedClock: i_clk  # References clock by physical port name
    associatedReset: i_rst_n
    memoryMapRef: CSR_MAP   # Links to memory map name
    useOptionalPorts:       # Include optional bus signals
      - AWPROT
      - ARPROT
    portWidthOverrides:     # Override default signal widths
      AWADDR: 12
      ARADDR: 12
```

### Bus Interface Arrays

For multiple similar interfaces (e.g., 4 AXI-Stream channels):

```yaml
- name: M_AXIS_EVENTS
  type: AXIS
  mode: master
  array:
    count: 4
    indexStart: 0
    namingPattern: M_AXIS_CH{index}_EVENTS
    physicalPrefixPattern: m_axis_ch{index}_evt_
```

---

## Memory Maps

### Import (Recommended)

```yaml
memoryMaps:
  import: my_core.mm.yml
```

### Inline

```yaml
memoryMaps:
  - name: CSR_MAP
    addressBlocks:
      - name: REGS
        offset: 0
        range: 4K
        usage: register
        registers: [...]
```

---

## Memory Map File Format (`*.mm.yml`)

```yaml
- name: CSR_MAP
  description: Control and status registers
  addressBlocks:
    - name: REGS
      offset: 0
      range: 4K
      usage: register           # register | memory | reserved
      defaultRegWidth: 32
      registers:
        - name: CTRL
          offset: 0
          size: 32
          access: read-write
          resetValue: 0x00000000
          description: Control register
          fields:
            - name: ENABLE
              bits: "[0:0]"
              access: read-write
              description: Enable bit

            - name: MODE
              bits: "[2:1]"
              access: read-write

        - name: STATUS
          offset: 4
          access: read-only
          fields:
            - name: BUSY
              bits: "[0:0]"

        - name: IRQ_FLAGS
          offset: 8
          access: write-1-to-clear
```

### Register Arrays

```yaml
registers:
  - name: TIMER
    count: 4
    stride: 16               # Bytes between array elements
    registers:
      - name: CTRL
        offset: 0
      - name: STATUS
        offset: 4
      - name: COMPARE
        offset: 8
```

This expands to: `TIMER_0_CTRL`, `TIMER_0_STATUS`, `TIMER_1_CTRL`, etc.

### Access Types

| Type | Description |
|------|-------------|
| `read-write` | Normal read/write register |
| `read-only` | Read-only (status, version) |
| `write-only` | Write-only (command) |
| `write-1-to-clear` | Writing 1 clears bits (interrupt flags) |

---

## Parameters

```yaml
parameters:
  - name: DATA_WIDTH
    value: 32
    dataType: integer        # integer | string | boolean
    description: Data bus width
```

---

## File Sets

```yaml
fileSets:
  - name: RTL_Sources
    files:
      - path: rtl/core.vhd
        type: vhdl
      - path: rtl/pkg.vhd
        type: vhdl

  - name: Simulation
    files:
      - path: tb/test.py
        type: python

  # Import external file set
  - import: ../common/c_api.fileset.yml
```

---

## Templates

Start with these templates in `ipcore_spec/templates/`:

| Template | Use Case |
|----------|----------|
| `minimal.ip.yml` | Bare minimum valid IP core |
| `basic.ip.yml` | Clock, reset, and simple ports |
| `axi_slave.ip.yml` | AXI-Lite slave with register map |
| `basic.mm.yml` | Simple memory map |
| `array.mm.yml` | Register arrays with count/stride |
| `multi_block.mm.yml` | Multiple address blocks |

---

## Examples

Real-world examples in `ipcore_spec/examples/`:

- `timers/my_timer_core.ip.yml` - Timer with AXI-Lite + AXI-Stream
- `led/led_controller.ip.yml` - Simple LED controller
- `test_cases/` - Various test configurations

---

## CLI Usage

```bash
# Generate VHDL from IP core
ipcore generate my_core.ip.yml --output ./generated

# Parse VHDL to create IP core YAML
ipcore parse entity.vhd

# List available bus types
ipcore list-buses
```

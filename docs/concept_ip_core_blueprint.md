# IP Core Blueprint: A Lean Source of Truth

This document defines a lean, human-friendly blueprint for describing an IP core. It uses a single YAML file to capture all essential information, enabling automation and ensuring consistency.

**The Goal:** Move away from scattered, manually-maintained files and create a single source of truth that can drive:
*   Register Header & Driver Generation
*   RTL Wrapper & Stub Creation
*   Simulation Harnesses & Testbenches
*   Automated Documentation
*   Design & Linting Checks

This concept borrows the best ideas from heavier standards like IP-XACT and SystemRDL but leaves out the noise and complexity.

---
## 1. The Blueprint at a Glance

Here is a complete, recommended blueprint. It defines a GPIO controller with an AXI4-Lite control bus and two AXI4-Stream data outputs.

```yaml
# file: blueprints/axi_gpio_controller.yaml
meta:
  vendor: your-company.com
  name: AXI_GPIO_Controller
  version: "2.1.0"
  description: GPIO controller with AXI4-Lite control and AXI-Stream data.

parameters:
  - { name: NUM_GPIO_PINS, type: integer, value: 32 }
  - { name: AXI_DATA_WIDTH, type: integer, value: 32 }

interfaces:
  # --- Custom & Board-Level Ports ---
  # Only non-standard signals are listed explicitly.
  ports:
    - { name: sys_clk, direction: in, width: 1 }
    - { name: sys_resetn, direction: in, width: 1 }
    - { name: gpio_pins, direction: inout, width: "${NUM_GPIO_PINS}" }

  # --- Standard Bus Interfaces ---
  # These are expanded automatically from protocol descriptors.
  busInterfaces:
    - name: S_AXI_CTRL
      descriptor: axi4_lite_slave
      portMap:
        ACLK: sys_clk
        ARESETn: sys_resetn
      memoryMap:
        file: "memory_maps/axi_gpio_controller_map.yaml"

    - name: M_AXIS_DATA
      descriptor: axi4_stream_master
      count: 2 # Create two instances of this interface
      naming:
        prefix: m_axis_data
      portMap:
        ACLK: sys_clk
        ARESETn: sys_resetn
        TDATA: m_axis_data_{index}_tdata # Use {index} for per-instance names

fileSets:
  - name: RTL
    files:
      - "rtl/axi_gpio_controller.vhd"
      - "rtl/axi_lite_if.vhd"
  - name: Testbench
    files:
      - "tb/gpio_tb.sv"
```

---
## 2. How It Works: Generating Ports from Descriptors

The key to simplicity is that **you don't list every port of a standard bus**. Instead, you point to a **Protocol Descriptor** file, and the tools generate the ports for you.

### Protocol Descriptors
A descriptor is a small YAML file that defines a standard bus, like AXI4-Lite. It lists all the logical signals (`ACLK`, `AWADDR`, etc.), their properties, and default naming conventions.

Here’s a snippet from `protocols/axi4_lite_slave.yaml`:
```yaml
# file: protocols/axi4_lite_slave.yaml
protocol: AXI4-Lite
mode: slave
defaultPrefix: s_axi_ # Default prefix for generated ports

logicalSignals:
  mandatory:
    - { name: ACLK,    width: 1,          direction: in }
    - { name: ARESETn, width: 1,          direction: in }
    - { name: AWADDR,  width: ADDR_WIDTH, direction: in }
    - { name: AWVALID, width: 1,          direction: in }
    # ... and so on for all AXI4-Lite signals
  optional:
    - { name: AWPROT,  width: 3,          direction: in }

defaults:
  ADDR_WIDTH: 32
  DATA_WIDTH: 32
```
The build tools use this file to expand the `S_AXI_CTRL` interface into a full set of physical ports (e.g., `s_axi_awaddr`, `s_axi_wdata`, etc.).

### Customizing Generated Ports
You can easily customize the generated ports from your blueprint using `portMap` and `naming`.

#### `portMap`: Overriding Specific Signals
Use `portMap` to override the physical name of a specific logical signal. This is most commonly used to connect multiple interfaces to a shared, global signal.

In our example, we map the logical `ACLK` and `ARESETn` signals of our AXI interfaces to the top-level `sys_clk` and `sys_resetn` ports.
```yaml
busInterfaces:
  - name: S_AXI_CTRL
    descriptor: axi4_lite_slave
    portMap:
      ACLK: sys_clk       # Maps logical ACLK to physical port 'sys_clk'
      ARESETn: sys_resetn # Maps logical ARESETn to 'sys_resetn'
```
All other signals (`AWADDR`, `WDATA`, etc.) are generated with the default prefix (`s_axi_ctrl_awaddr`).

#### `naming.prefix`: Changing the Default Prefix
If you don't like the default prefix from the descriptor, you can specify your own.
```yaml
busInterfaces:
  - name: M_AXIS_DATA
    descriptor: axi4_stream_master
    naming:
      prefix: stream_out_ # Generates stream_out_tdata, stream_out_tvalid, etc.
```

---
## 3. Creating Arrays of Interfaces

You can create multiple instances of the same interface by adding a `count` property. This is useful for designs with multiple identical channels.

```yaml
busInterfaces:
  - name: M_AXIS_DATA
    descriptor: axi4_stream_master
    count: 2 # This creates two AXI-Stream master interfaces
```

When `count > 1`, you can use the `{index}` placeholder in `portMap` or `naming.prefix` to create unique names for each instance.

**Example: Per-Instance Naming**
This `portMap` gives each of the two stream interfaces a uniquely named `TDATA` port.
```yaml
portMap:
  # ACLK and ARESETn are shared by both instances
  ACLK: sys_clk
  ARESETn: sys_resetn
  # TDATA is unique for each instance
  TDATA: m_axis_data_{index}_tdata # -> m_axis_data_0_tdata, m_axis_data_1_tdata
```
If a prefix is used without `{index}`, the index is automatically appended (e.g., `prefix: m_axis_` becomes `m_axis_0_`, `m_axis_1_`, etc.).

---
## 4. Blueprint Schema Reference

### Top-Level Keys
| Key | Type | Description |
|---|---|---|
| `meta` | `object` | Core identification metadata (name, vendor, version). |
| `parameters` | `list` | Compile-time or synthesis-time generics. |
| `interfaces` | `object` | Contains all hardware ports and bus interfaces. |
| `fileSets` | `list` | Lists of source files (RTL, testbenches, etc.). |

### `interfaces` Block
| Key | Type | Description |
|---|---|---|
| `ports` | `list` | Explicitly defines custom, non-standard, or board-level ports. |
| `busInterfaces` | `list` | Defines standard bus interfaces to be generated from descriptors. |

### `busInterfaces` Entry
| Key | Type | Description |
|---|---|---|
| `name` | `string` | Logical name for the interface (e.g., `S_AXI_CTRL`). |
| `descriptor` | `string` | **Required.** The name of the protocol descriptor file (without extension). |
| `descriptorFile`| `string` | Path to a custom descriptor file. Overrides `descriptor`. |
| `count` | `integer` | (Optional) Number of instances to create. Defaults to 1. |
| `naming` | `object` | (Optional) Contains rules for naming generated ports. |
| `portMap` | `object` | (Optional) A map of `logical_signal: physical_name` to override specific ports. |
| `memoryMap` | `object` | (Optional) Points to a memory map definition file for this interface. |

---
## 5. Available Protocol Descriptors

The following built-in descriptors are available.

| Protocol | Descriptor Name | Default Prefix |
|---|---|---|
| AXI4-Lite | `axi4_lite_slave` | `s_axi_` |
| AXI4-Full | `axi4_full_slave` | `s_axi_` |
| AXI4-Stream | `axi4_stream_master` | `m_axis_` |
| AXI4-Stream | `axi4_stream_slave` | `s_axis_` |
| Avalon-MM | `avalon_mm_master` | `m_avmm_` |
| Avalon-MM | `avalon_mm_slave` | `s_avmm_` |
| Avalon-ST | `avalon_st_source` | `m_avst_` |
| Avalon-ST | `avalon_st_sink` | `s_avst_` |

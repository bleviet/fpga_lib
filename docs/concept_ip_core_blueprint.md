# IP Core Blueprint Concept (Clarity Edition)

This document defines a lean, human-friendly blueprint format for describing an IP core. It borrows only the useful ideas from heavier standards (IP-XACT, SystemRDL) and leaves out noise. The result: a single YAML file that:

* Identifies the IP (metadata & parameters)
* Describes its external interfaces (ports + standard bus interfaces)
* Points to its register memory map (separate file)
* Lists implementation files (RTL, testbench, etc.)

You can then automate: register drivers, RTL wrappers, simulation harnesses, docs, and consistency checks—all from this one source of truth.

---
## Table of Contents
1. Quick Start (TL;DR)
2. Core YAML Structure (Annotated Legacy Example)
3. Recommended Modern Style (Simplified Ports)
4. Simplified Standard Bus Port Generation
5. External Protocol Descriptor Files
6. Protocol Defaults Summary
7. Rules & Validation (Conflict Resolution, Reserved Names)
8. Migration Guide (Explicit -> Simplified)
9. Advanced: Descriptor Implementation Outline
10. Future Extensions & Open Questions

---
## 1. Quick Start (TL;DR)
Minimal recommended blueprint (using auto-generated standard bus ports):

```yaml
meta:
  vendor: your-company.com
  name: AXI_GPIO_Controller
  version: 2.1.0
  description: GPIO controller with AXI4-Lite control + AXI4-Stream data.

parameters:
  - { name: NUM_GPIO_PINS, type: integer, value: 32, description: Total GPIOs }
  - { name: AXI_DATA_WIDTH, type: integer, value: 32, description: AXIS tdata width }

interfaces:
  ports:                       # Only non-standard signals here
    - { name: gpio_pins, direction: inout, width: 32 }
  busInterfaces:
    - name: S_AXI_LITE
      descriptor: axi4_lite_slave   # Uses built-in descriptor file
      memoryMap: { file: axi_gpio_controller_map.yaml }
    - name: M_AXIS_DATA
      descriptor: axi4_stream_master
      naming: { prefix: m_axis_ }   # Optional (would default anyway)

fileSets:
  - name: RTL
    files:
      - rtl/axi_gpio_controller.vhd
      - rtl/axi_lite_if.vhd
  - name: TB
    files:
      - tb/gpio_tb.sv
```

That’s it. All AXI4-Lite and AXI4-Stream ports are generated from protocol descriptors.

---
## 2. Core YAML Structure (Annotated Legacy Example)
This earlier (v2.0.0) style listed every port explicitly. Still supported, but noisier. Shown here for clarity and migration reference.

```yaml
# ===================================================================
# IP Core Blueprint
# ===================================================================
# This document describes the essential properties of a GPIO controller
# IP with AXI interfaces for control and data streaming.
# -------------------------------------------------------------------

# --- Top-Level Metadata ---
# Basic identification details for the IP core.
meta:
  vendor: "your-company.com"
  name: "AXI_GPIO_Controller"
  version: "2.0.0"
  description: "A GPIO controller with an AXI4-Lite control interface and an AXI4-Stream data interface."

# --- Configuration Parameters ---
# These are compile-time or synthesis-time parameters that alter the
# IP core's structure or behavior.
parameters:
  - name: "NUM_GPIO_PINS"
    type: "integer"
    value: 32
    description: "Number of general-purpose I/O pins."
  - name: "AXI_DATA_WIDTH"
    type: "integer"
    value: 32
    description: "Width of the AXI4-Stream data bus (tdata) in bits."

# --- Hardware Interfaces (Legacy Explicit Form) ---
# FULL explicit listing of standard bus ports (now optional in 2.1.0+)
interfaces:
  # Top-level physical ports of the IP core.
  ports:
    # AXI4-Lite Clock and Reset
    - name: "s_axi_aclk"
      direction: "in"
      width: 1
    - name: "s_axi_aresetn"
      direction: "in"
      width: 1
    # AXI4-Lite Write Address Channel
    - name: "s_axi_awaddr"
      direction: "in"
      width: 32
    - name: "s_axi_awprot"
      direction: "in"
      width: 3
    - name: "s_axi_awvalid"
      direction: "in"
      width: 1
    # ... other AXI4-Lite ports (awready, wdata, wstrb, wvalid, wready, bresp, bvalid, bready, etc.)

    # AXI4-Stream Ports
    - name: "m_axis_tdata"
      direction: "out"
      width: 32 # Should match AXI_DATA_WIDTH
    - name: "m_axis_tvalid"
      direction: "out"
      width: 1
    - name: "m_axis_tready"
      direction: "in"
      width: 1
    # ... other AXI4-Stream ports (tstrb, tlast, etc.)

    # GPIO Port
    - name: "gpio_pins"
      direction: "inout"
      width: 32 # Should match NUM_GPIO_PINS

  # Logical grouping of ports into standard bus interfaces.
  busInterfaces:
    - name: "S_AXI_LITE"
      protocol: "AXI4-Lite"
      mode: "slave"
      description: "AXI4-Lite interface for register access and control."
      # Maps logical protocol signals to physical top-level ports.
      portMap:
        ACLK: "s_axi_aclk"
        ARESETn: "s_axi_aresetn"
        AWADDR: "s_axi_awaddr"
        AWPROT: "s_axi_awprot"
        AWVALID: "s_axi_awvalid"
        # ... other AXI4-Lite mappings
      # The memory map for this specific bus interface.
      memoryMap:
        file: "axi_gpio_controller_map.yaml"

    - name: "M_AXIS_DATA"
      protocol: "AXI4-Stream"
      mode: "master"
      description: "AXI4-Stream master interface for outputting GPIO data."
      portMap:
        ACLK: "s_axi_aclk"
        ARESETn: "s_axi_aresetn"
        TDATA: "m_axis_tdata"
        TVALID: "m_axis_tvalid"
        TREADY: "m_axis_tready"
        # ... other AXI4-Stream mappings

# --- File Sets (Implementation Artifacts) ---
fileSets:
  - name: "RTL_Sources_VHDL"
    description: "Synthesizable VHDL source files."
    files:
      - "rtl/axi_gpio_controller.vhd"
      - "rtl/axi_lite_if.vhd"
      - "rtl/axis_master_if.vhd"

  - name: "Testbench_Sources"
    description: "SystemVerilog testbench files."
    files:
      - "tb/gpio_tb.sv"
```

---
## 3. Recommended Modern Style (Simplified Ports)
Version ≥ 2.1.0: Omit standard bus ports and let the tool expand them from descriptors. Only keep custom / board-facing signals (like `gpio_pins`). See Quick Start.

---
## 4. Simplified Standard Bus Port Generation

To reduce boilerplate and potential mistakes when defining widely used standard bus interfaces (AXI4-Lite, AXI4-Full, AXI4-Stream, Avalon-MM, Avalon-ST, etc.), the blueprint supports **implicit port generation**. Instead of explicitly listing every physical signal under `interfaces.ports`, you declare the bus interface with a `naming` block. The tool then materializes the standard signals using a predefined naming convention.

### Design Goals
* Eliminate repetitive manual enumeration of standard bus signals.
* Provide consistent, convention-based naming (e.g. `s_axi_awaddr`, `m_axis_tdata`).
* Allow selective overrides (clock/reset sharing, alternative prefixes, custom renames).
* Keep non-standard / custom signals explicitly listed for clarity.

### Naming Block Semantics
Within each entry of `busInterfaces`:
* `naming.convention`: Identifies a predefined naming pattern (currently: `default`). Future values could include `xilinx`, `intel`, etc., if vendor-specific variants are needed.
* Optional `naming.prefix`: Overrides the auto-derived prefix (`s_axi_`, `m_axis_`, etc.).
* Optional `portMap`: Provides selective overrides for logical protocol signals (e.g. map `ACLK` to a shared `sys_clk`). Only the overridden signals need be listed; the rest follow the convention.

### Generated Signals (Illustrative)
For `protocol: AXI4-Lite` + `mode: slave` + `naming.convention: default`, the tool generates the canonical minimal set (write/read address, data, response, clock/reset). The exact set is protocol-version–aware and can be extended (e.g. optional protections, QoS) if declared via configuration flags later.

### Example 1: Minimal Definition (Modern Style)
Only `gpio_pins` is declared; standard bus ports are implicit.

```yaml
# ===================================================================
# IP Core Blueprint (with Simplified Port Definitions)
# ===================================================================
meta:
  vendor: "your-company.com"
  name: "AXI_GPIO_Controller"
  version: "2.1.0"
  description: "A GPIO controller with an AXI4-Lite control interface and an AXI4-Stream data interface."

parameters:
  - name: "NUM_GPIO_PINS"
    type: "integer"
    value: 32
    description: "Number of general-purpose I/O pins."
  - name: "AXI_DATA_WIDTH"
    type: "integer"
    value: 32
    description: "Width of the AXI4-Stream data bus (tdata) in bits."

interfaces:
  # Only NON-standard ports appear here.
  ports:
    - name: "gpio_pins"
      direction: "inout"
      width: 32 # Should match NUM_GPIO_PINS

  busInterfaces:
    - name: "S_AXI_LITE"
      protocol: "AXI4-Lite"
      mode: "slave"
      description: "AXI4-Lite interface for register access."
      naming:
        convention: "default"  # Generates ports like s_axi_aclk, s_axi_awaddr, ...
      memoryMap:
        file: "axi_gpio_controller_map.yaml"

    - name: "M_AXIS_DATA"
      protocol: "AXI4-Stream"
      mode: "master"
      description: "AXI4-Stream master interface for outputting GPIO data."
      naming:
        convention: "default"  # Generates ports like m_axis_tdata, m_axis_tvalid, ...
        # prefix: "stream_out_"  # (Optional) Uncomment to override the prefix

fileSets:
  - name: "RTL_Sources_VHDL"
    description: "Synthesizable VHDL source files."
    files:
      - "rtl/axi_gpio_controller.vhd"
      - "rtl/axi_lite_if.vhd"
      - "rtl/axis_master_if.vhd"
  - name: "Testbench_Sources"
    description: "SystemVerilog testbench files."
    files:
      - "tb/gpio_tb.sv"
```

### Example 2: Selective Overrides (Shared Clock/Reset)
Override only what differs (e.g. shared system clock), keep rest auto-generated.

```yaml
busInterfaces:
  - name: "S_AXI_LITE"
    protocol: "AXI4-Lite"
    mode: "slave"
    description: "AXI4-Lite interface using a global system clock."
    naming:
      convention: "default"
    portMap:
      ACLK: "sys_clk"       # Overrides the default generated s_axi_aclk
      ARESETn: "sys_resetn" # Overrides the default generated s_axi_aresetn
    memoryMap:
      file: "axi_gpio_controller_map.yaml"
```

### Future Extensions (Planned)
* Additional conventions (e.g. vendor-specific naming patterns).
* Optional signal sets toggles (e.g. remove unused AXI4 signals like `AWPROT`).
* Parameterized data/ID widths for AXI4-Full with automatic signal width adaptation.
* Support for interface abstraction tags to drive automated RTL stub / wrapper generation.

---
## 5. External Protocol Descriptor Files
Descriptors live in standalone YAML files defining logical signals + metadata.

### Implementation Outline (High-Level)
1. Ship a directory of built-in descriptor YAMLs.
2. Resolve descriptor via precedence: `descriptorFile` > `descriptor` > `naming.convention`.
3. Expand logical signals → concrete port names (apply prefix; default from descriptor).
4. Apply overrides (`portMap`, `prefix`, optional lists).
5. Merge with custom ports; validate collisions + completeness.
6. Emit optional expansion artifact for review.
7. Allow user-supplied custom descriptor files (zero code changes required).

This approach keeps the blueprint terse while remaining explicit where customization matters.

### Why Descriptor Files?
* Decouple protocol definitions from blueprints.
* Allow easy customization / extension.
* Enable linting & version control of interface specs.

The default `naming.convention: "default"` resolves to a built-in descriptor appropriate for the protocol.

### Ways to Reference
Users can:
* Reference a built-in descriptor by logical name (`descriptor: axi4_lite_slave`).
* Point directly to a custom file (`descriptorFile: protocols/my_company_axi4_lite.yaml`).
* Still specify `naming.prefix`, `portMap`, or `optional` to refine the generated set.

### Recommended Directory Layout
```
protocols/
  axi4_lite_slave.yaml
  axi4_full_slave.yaml
  axi4_stream_master.yaml
  axi4_stream_slave.yaml
  avalon_mm_slave.yaml
  avalon_mm_master.yaml
  avalon_st_source.yaml
  avalon_st_sink.yaml
  # future: wishbone_classic_master.yaml, apb_slave.yaml, tilelink_lite_client.yaml
```

### Example Descriptor (`protocols/axi4_lite_slave.yaml`)
```yaml
protocol: AXI4-Lite
mode: slave
logicalSignals:
  mandatory:
    - { name: ACLK,     width: 1,            direction: in }
    - { name: ARESETn,  width: 1,            direction: in }
    - { name: AWADDR,   width: ADDR_WIDTH,   direction: in }
    - { name: AWVALID,  width: 1,            direction: in }
    - { name: WDATA,    width: DATA_WIDTH,   direction: in }
    - { name: WSTRB,    width: DATA_WIDTH/8, direction: in }
    - { name: WVALID,   width: 1,            direction: in }
    - { name: BREADY,   width: 1,            direction: in }
    - { name: ARADDR,   width: ADDR_WIDTH,   direction: in }
    - { name: ARVALID,  width: 1,            direction: in }
    - { name: RREADY,   width: 1,            direction: in }
    - { name: BRESP,    width: 2,            direction: out }
    - { name: RDATA,    width: DATA_WIDTH,   direction: out }
    - { name: RVALID,   width: 1,            direction: out }
  optional:
    - { name: AWPROT, width: 3, direction: in }
    - { name: ARPROT, width: 3, direction: in }
defaults:
  ADDR_WIDTH: 32
  DATA_WIDTH: 32
defaultPrefix: s_axi_
notes: |
  Minimal AXI4-Lite subset; READY signals implied for simplicity and can be generated automatically.
```

### Referencing a Descriptor in the Blueprint
```yaml
busInterfaces:
  - name: S_AXI_LITE
    descriptor: axi4_lite_slave   # Uses built-in protocols/axi4_lite_slave.yaml
    naming:
      prefix: s_axi_              # Optional (falls back to descriptor defaultPrefix)
    memoryMap:
      file: axi_gpio_controller_map.yaml

  - name: CUSTOM_STREAM
    descriptorFile: protocols/custom_axis_stream.yaml
    naming:
      prefix: m_axis_
    portMap:
      ACLK: sys_clk  # Override only clock/reset
      ARESETn: sys_resetn
```

### Descriptor Selection Precedence
`descriptorFile` > `descriptor` > `naming.convention` for selecting the base logical signal set. The `naming.convention` key becomes a shorthand alias for a particular built-in descriptor (e.g. `default` -> `axi4_lite_slave` for AXI4-Lite).

### Customization Workflow
1. Copy a built-in descriptor to your repo (e.g. `protocols/my_axi_variant.yaml`).
2. Adjust widths / optional signals / defaults.
3. Point `descriptorFile` at the customized file.
4. Run the expansion tool (future CLI) with `--emit-expanded-ports` to review changes.

### Descriptor Validation (Additional)
* Ensure each `logicalSignals.mandatory` entry has unique `name`.
* Verify width expressions only reference allowed symbols (descriptor defaults + global parameters + per-interface parameters).
* Reject unknown keys to avoid silent typos.
* Provide lint command: `fpga-lib validate-descriptor protocols/axi4_lite_slave.yaml`.

These external descriptor files decouple protocol knowledge from individual blueprints and make extending or overriding behavior a simple, traceable file-based operation.

---
## 6. Protocol Defaults Summary
Below is a concise summary of the default generated signal sets (illustrative, not exhaustive). Optional signals are only emitted if enabled by a future flag (e.g. `include: [PROT, QOS]`).

| Protocol | Mode   | Default Prefix | Mandatory Logical Signals (core subset) | Common Optional Signals |
|----------|--------|----------------|------------------------------------------|-------------------------|
| AXI4-Lite | slave | `s_axi_` | ACLK, ARESETn, AWADDR, AWVALID, WDATA, WSTRB, WVALID, BREADY, ARADDR, ARVALID, RREADY, BRESP, RDATA, RVALID | AWPROT, ARPROT |
| AXI4-Full | slave | `s_axi_` | (All AXI4-Lite) + AWLEN, AWSIZE, AWBURST, AWID, AWLOCK, AWCACHE, AWQOS, WLAST, ARLEN, ARSIZE, ARBURST, ARID, ARLOCK, ARCACHE, ARQOS, RLAST | AWUSER, WUSER, BUSER, ARUSER, RUSER |
| AXI4-Stream | master | `m_axis_` | ACLK, ARESETn, TDATA, TVALID, TREADY | TKEEP, TSTRB, TLAST, TID, TDEST, TUSER |
| AXI4-Stream | slave | `s_axis_` | ACLK, ARESETn, TDATA, TVALID, TREADY | TKEEP, TSTRB, TLAST, TID, TDEST, TUSER |
| Avalon-MM | slave  | `s_avmm_` | clk, reset, address, writedata, readdata, write, read, waitrequest | byteenable, burstcount |
| Avalon-MM | master | `m_avmm_` | clk, reset, address, writedata, readdata, write, read, waitrequest | byteenable, burstcount |
| Avalon-ST | source | `m_avst_` | clk, reset, data, valid, ready | empty, sop, eop |
| Avalon-ST | sink   | `s_avst_` | clk, reset, data, valid, ready | empty, sop, eop |

---
## 7. Rules & Validation
### Conflict Resolution Order
When generating and merging ports the following order applies (highest precedence first):
1. `portMap` overrides: A logical signal explicitly mapped to a physical name always wins.
2. Explicitly declared `interfaces.ports` entries (non-generated custom ports) are preserved; if a generated name would collide, the parser MUST raise an error unless `allowShadow: true` is explicitly supplied in the `naming` block (future feature).
3. `naming.prefix` is applied before collision checking; if omitted the default prefix table above is used.
4. Generated defaults fill any remaining mandatory logical signals; missing mandatory logical signals after expansion is an error.
5. Optional signals are only generated if flagged (future: e.g. `optional: [AWPROT, TKEEP]`).

### Reserved Identifiers
Logical signal names (ACLK, ARESETn, AWADDR, TDATA, etc.) are reserved within their protocol scope. Avoid using these as standalone custom port names unless intentionally overriding via `portMap`.

---
## 8. Migration Guidance (Explicit → Simplified)
If migrating an existing blueprint from fully explicit port listings to the simplified `naming` approach:
1. Increment `meta.version` (e.g. 2.0.0 -> 2.1.0) to signal structural declaration style change.
2. Remove explicit standard bus ports from `interfaces.ports` (keep only custom / sideband signals).
3. Introduce `naming.convention: "default"` under each affected `busInterfaces` entry.
4. Add a temporary validation step in CI to diff the expanded generated port set against the previous explicit list to ensure parity before removing the old style.

### Incremental Adoption Strategy
You can adopt simplification per interface:
* Start with AXI4-Lite (usually the noisiest) while leaving AXI-Stream explicit.
* Once validated, convert remaining interfaces.
* Maintain a `--emit-expanded-ports` CLI option (future tool) that prints the fully expanded list for design reviews.

### Validation Checklist (Parser SHOULD Enforce)
* All mandatory logical signals present post-expansion.
* No duplicate physical port identifiers.
* Width expressions resolvable (e.g. `TDATA` width equals `AXI_DATA_WIDTH`).
* Overridden clock/reset are single-bit unless protocol spec allows multi-bit.
* Optional signals not requested are omitted.

### Example (Future): AXI4-Full With Custom Prefix & Optional Signals
```yaml
busInterfaces:
  - name: "S_AXI_FULL"
    protocol: "AXI4-Full"
    mode: "slave"
    naming:
      convention: "default"
      prefix: "mem_axi_"
      optional:
        - AWPROT
        - ARPROT
        - AWQOS
        - ARQOS
    parameters:  # (Optional future extension for per-interface parameterization)
      AXI_ID_WIDTH: 4
      AXI_DATA_WIDTH: 128
    portMap:
      ACLK: "sys_clk"
      ARESETn: "sys_resetn"
```

### Tooling Stub (Internal Descriptor Form)
An internal Python descriptor for AXI4-Lite could look like:
```python
AXI4_LITE_SLAVE = {
    "protocol": "AXI4-Lite",
    "mode": "slave",
    "mandatory": [
        ("ACLK", 1), ("ARESETn", 1),
        ("AWADDR", "ADDR_WIDTH"), ("AWVALID", 1), ("WVALID", 1), ("WDATA", "DATA_WIDTH"), ("WSTRB", "DATA_WIDTH/8"),
        ("BREADY", 1), ("ARADDR", "ADDR_WIDTH"), ("ARVALID", 1), ("RREADY", 1), ("BRESP", 2), ("RDATA", "DATA_WIDTH"), ("RVALID", 1)
    ],
    "optional": ["AWPROT", "ARPROT"],
    "defaults": {
        "ADDR_WIDTH": 32,
        "DATA_WIDTH": 32
    },
    "default_prefix": "s_axi_"
}
```

### Error Reporting Examples
* Duplicate port: `ERROR: Generated port 's_axi_awaddr' collides with explicit port declaration (interfaces.ports[3]).`
* Missing mandatory after overrides: `ERROR: Logical signal 'RVALID' not bound (provide portMap override or allow generation).`
* Invalid override: `ERROR: portMap assigns unknown logical signal 'AWLEN' for AXI4-Lite.`

---
## 9. Future Extensions & Open Questions
* Should per-interface parameter overrides (e.g. `DATA_WIDTH`) live inside `parameters:` or `interfaces.busInterfaces[].parameters`? (Current leaning: local scoping inside the interface for clarity.)
* Whether to auto-prune unreferenced generated signals when memory map proves they are unused (e.g. no write path -> drop write channel). Likely defer to explicit config flags to avoid surprising implicit behavior.
* Introduce a `style:` section at top-level to declare global defaults (e.g. default naming convention) for multi-interface consistency.

---
---
## 10. Summary
* Use the simplified style (v2.1.0+) for clarity.
* Keep only custom ports under `interfaces.ports`.
* Let descriptors generate standard bus signals; override selectively.
* Validation + descriptors keep designs consistent and auditable.

This structure keeps the blueprint readable for humans while rich enough for automation.


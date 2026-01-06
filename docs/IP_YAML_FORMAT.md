# IP YAML format and Pydantic model mapping

This document describes the **IP core YAML format** used by `fpga_lib`, and how it is parsed into the canonical **Pydantic models** under `fpga_lib.model.*`.

It is intentionally grounded in the actual implementation in `fpga_lib.parser.yaml.YamlIpCoreParser`.

## Big picture

- The "root" YAML file (example: `examples/ip/my_timer_core.yml`) describes an IP core: metadata, clocks/resets/ports, bus interfaces, parameters, file sets, and (optionally) memory maps.
- Memory maps are usually kept in a separate YAML file (example: `examples/ip/my_timer_core.memmap.yml`) and referenced via `memoryMaps: { import: "..." }`.
- Parsing is performed by `fpga_lib/parser/yaml/ip_yaml_parser.py`.
- The output is always an `fpga_lib.model.core.IpCore` instance.

## Parser entry point

### Parse an IP YAML file

The primary API is:

- `fpga_lib.parser.yaml.YamlIpCoreParser.parse_file(path) -> fpga_lib.model.core.IpCore`

Parsing is strict:

- YAML root must be a mapping/dict.
- Unknown keys are rejected at the Pydantic model layer (`model_config = {"extra": "forbid"}` across models).
- Many sections are optional; if omitted, Pydantic defaults are used.

### “None filtering” behavior

The parser uses an internal helper `_filter_none()` which removes keys whose value is `None` before constructing Pydantic models.

This matters because many model fields have defaults (e.g. `description: ""`), and passing `None` explicitly can cause validation errors in Pydantic v2.

## Key naming conventions

The YAML format generally uses **camelCase** keys, while the Pydantic models use **snake_case** fields.

Examples:

- YAML `apiVersion` → model `IpCore.api_version`
- YAML `physicalPort` → model `Port.physical_port`
- YAML `busInterfaces` → model `IpCore.bus_interfaces`

The conversion is not automatic for arbitrary keys; it is done explicitly field-by-field inside the parser.

## Terminology and semantics (what these terms mean)

This document is intentionally “parser-accurate”, but it also helps to understand what the YAML is *trying to represent*.

### Names: logical vs physical

- **Logical name**: a stable identifier used inside the YAML and models (e.g. `SYS_CLK`, `S_AXI_LITE`, `CSR_MAP`). Logical names are used for references like `associatedClock` and `memoryMapRef`.
- **Physical port/prefix**: the actual HDL signal naming. Examples:
  - `physicalPort`: exact HDL port name for a single port/clock/reset (e.g. `i_clk_sys`).
  - `physicalPrefix`: prefix used to build a *bundle* of HDL ports for a bus (e.g. `s_axi_` so the generator can form `s_axi_awaddr`, `s_axi_wdata`, etc.).

### Addressing and units

- Unless stated otherwise, offsets and sizes used by the memory map parser are treated as **bytes**.
- A **memory map** is a named container (e.g. `CSR_MAP`) for one or more **address blocks**.
- An **address block** is a contiguous region of address space, starting at a base offset within the map.
- A **register** has an `offset` (byte offset within its block base), `size` (bits; default 32), and optional `fields`.
- A **bit field** is a named bit slice within a register (e.g. `[7:4]`) with access semantics.

### References (string links)

Some YAML keys are *references by name* to other objects defined elsewhere in the same IP definition:

- `busInterfaces[*].associatedClock` → must match a `clocks[*].name`
- `busInterfaces[*].associatedReset` → must match a `resets[*].name`
- `busInterfaces[*].memoryMapRef` → must match a `memoryMaps[*].name`

The model provides `IpCore.validate_references()` to check these links.

## IP core YAML schema (root file)

### Top-level structure

At the top level, the parser expects a mapping with keys like:

- `apiVersion` (required)
- `vlnv` (required)
- `description` (optional)
- `clocks` (optional, list)
- `resets` (optional, list)
- `ports` (optional, list)
- `useBusLibrary` (optional)
- `busInterfaces` (optional, list)
- `memoryMaps` (optional, either `{import: ...}` or a list)
- `parameters` (optional, list)
- `fileSets` (optional, list; entries may include `{import: ...}`)

### Mapping table: top-level → `IpCore`

| YAML key | Model field | Model type |
|---|---|---|
| `apiVersion` | `IpCore.api_version` | `str` (required) |
| `vlnv` | `IpCore.vlnv` | `VLNV` (required) |
| `description` | `IpCore.description` | `str` |
| `clocks` | `IpCore.clocks` | `list[Clock]` |
| `resets` | `IpCore.resets` | `list[Reset]` |
| `ports` | `IpCore.ports` | `list[Port]` |
| `busInterfaces` | `IpCore.bus_interfaces` | `list[BusInterface]` |
| `parameters` | `IpCore.parameters` | `list[Parameter]` |
| `memoryMaps` | `IpCore.memory_maps` | `list[MemoryMap]` |
| `fileSets` | `IpCore.file_sets` | `list[FileSet]` |
| `useBusLibrary` | `IpCore.use_bus_library` | `str` |

## `vlnv` section

### YAML

```yaml
vlnv:
  vendor: "my-company.com"
  library: "processing"
  name: "my_timer_core"
  version: "1.2.0"
```

### Model mapping

- YAML `vlnv.vendor` → `VLNV.vendor`
- YAML `vlnv.library` → `VLNV.library`
- YAML `vlnv.name` → `VLNV.name`
- YAML `vlnv.version` → `VLNV.version`

All four fields are required.

## `clocks` section

### YAML shape

`clocks` is a list of objects:

```yaml
clocks:
  - name: "SYS_CLK"
    physicalPort: "i_clk_sys"
    direction: "in"      # optional, defaults to "in" in parser
    frequency: "100MHz"  # optional
    description: "..."   # optional
```

### Model mapping (`fpga_lib.model.clock_reset.Clock`)

The parser constructs `Clock(...)` with:

- `name` ← YAML `name`
- `physical_port` ← YAML `physicalPort`
- `direction` ← YAML `direction` (default: `"in"`)
- `frequency` ← YAML `frequency`
- `description` ← YAML `description`

Notes:

- `Clock` inherits from `Port` and uses the same `direction` normalization as `Port`.
- `Clock.frequency` is a string like `"100MHz"`; the model exposes a convenience property `frequency_hz`.

## `resets` section

### YAML shape

`resets` is a list of objects:

```yaml
resets:
  - name: "SYS_RST"
    physicalPort: "i_rst_n_sys"
    direction: "in"           # optional, defaults to "in" in parser
    polarity: "activeLow"     # optional, defaults to activeLow in parser
    description: "..."        # optional
```

### Model mapping (`fpga_lib.model.clock_reset.Reset`)

The parser constructs `Reset(...)` with:

- `name` ← YAML `name`
- `physical_port` ← YAML `physicalPort`
- `direction` ← YAML `direction` (default: `"in"`)
- `polarity` ← YAML `polarity` (default: `"activeLow"`)
- `description` ← YAML `description`

Polarity handling:

- The parser maps exactly `"activeLow"` → `Polarity.ACTIVE_LOW`; anything else → `Polarity.ACTIVE_HIGH`.
- The `Reset` model itself also normalizes strings case-insensitively.

## `ports` section

### YAML shape

`ports` is a list of generic (non-bus) ports:

```yaml
ports:
  - name: "o_irq"
    physicalPort: "o_global_irq"
    direction: "out"
    width: 1              # optional, defaults to 1
    description: "..."   # optional
```

### Model mapping (`fpga_lib.model.port.Port`)

- `name` ← YAML `name`
- `physical_port` ← YAML `physicalPort`
- `direction` ← YAML `direction`
- `width` ← YAML `width` (default: `1`)
- `description` ← YAML `description`

`direction` normalization:

- Accepts `in/out/inout` (also accepts `input/output` and normalizes to `in/out`).

## `useBusLibrary` section

### YAML

```yaml
useBusLibrary: "common/bus_definitions.yml"
```

### Behavior

If present, the parser:

- Resolves the path relative to the IP YAML file directory.
- Loads the YAML document with `yaml.safe_load`.
- Caches the bus library contents by absolute `Path`.

Important: in the current parser, loading the bus library does not (by itself) validate `busInterfaces[*].type` against the library. The bus library is loaded and cached for downstream usage, but `busInterfaces.type` is stored as a plain string.

## `busInterfaces` section

### YAML shape

`busInterfaces` is a list of bus interface definitions:

```yaml
busInterfaces:
  - name: "S_AXI_LITE"
    type: "AXI4L"
    mode: "slave"
    physicalPrefix: "s_axi_"
    associatedClock: "REG_CLK"    # optional
    associatedReset: "REG_RST"    # optional
    memoryMapRef: "CSR_MAP"       # optional
    useOptionalPorts: ["AWPROT"]  # optional
    portWidthOverrides:            # optional
      AWADDR: 12

  - name: "M_AXIS_EVENTS"
    type: "AXIS"
    mode: "master"
    array:
      count: 4
      indexStart: 0
      namingPattern: "M_AXIS_CH{index}_EVENTS"
      physicalPrefixPattern: "m_axis_ch{index}_evt_"
    physicalPrefix: "m_axis_evt_"
```

Important terms in `busInterfaces`:

- `type`: a short identifier of the bus standard (e.g. `AXI4L`, `AXIS`). The current parser stores this as a string. If you provide `useBusLibrary`, it is loaded and cached, but the parser does not currently verify that `type` exists in the library.
- `mode`: how the core participates in the bus (`master`/`slave` or `source`/`sink`). The `BusInterface` model normalizes this to lowercase.
- `physicalPrefix`: prefix used to form HDL signal names for this interface. This is how one logical interface corresponds to many HDL ports.
- `associatedClock` / `associatedReset`: binds the bus interface to one of the core’s top-level `clocks`/`resets` by logical name.
- `memoryMapRef`: binds the bus interface to a memory map by name (typical for register bus interfaces like AXI-Lite).
- `useOptionalPorts`: a list of optional bus signals to include when generating ports (e.g. `AWPROT`, `ARPROT` for AXI). The parser stores the list; enforcement/meaning is generator-dependent.
- `portWidthOverrides`: per-signal width overrides (see below).
- `array`: a compact way to describe multiple similar interfaces (e.g. one AXI Stream per timer channel) without copy/paste.

### Model mapping (`fpga_lib.model.bus.BusInterface`)

- `name` ← YAML `name`
- `type` ← YAML `type`
- `mode` ← YAML `mode` (normalized to lowercase)
- `physical_prefix` ← YAML `physicalPrefix`
- `associated_clock` ← YAML `associatedClock`
- `associated_reset` ← YAML `associatedReset`
- `memory_map_ref` ← YAML `memoryMapRef`
- `use_optional_ports` ← YAML `useOptionalPorts` (default: `[]`)
- `port_width_overrides` ← YAML `portWidthOverrides` (default: `{}`)
- `array` ← YAML `array` (optional; mapped to `ArrayConfig`)

### `portWidthOverrides` explained

`portWidthOverrides` is a dictionary mapping a *bus signal name* to a new integer width in bits.

Example:

```yaml
portWidthOverrides:
  AWADDR: 12
  WDATA: 32
```

Semantics:

- It exists so an IP can deviate from the “standard” widths provided by a bus definition (for example, shrinking `AWADDR`/`ARADDR` when the register space is only 4KB).
- The `BusInterface` model only enforces that override widths are positive.
- Whether the override names are valid for a given bus `type` and how they influence generated HDL depends on the bus-definition consumer (generator). The current YAML parser itself does not validate override keys against the bus library.

### `useOptionalPorts` explained

`useOptionalPorts` is a list of **bus signal names** that are considered optional by the bus definition, but that you want to include for this interface.

Example:

```yaml
useOptionalPorts:
  - AWPROT
  - ARPROT
```

Semantics:

- Many bus standards define optional signals (for example, AXI has protection signals, IDs, QoS, etc.).
- `useOptionalPorts` is your way to say: “generate/expect these optional signals for this specific instance”.
- The YAML parser stores this list in `BusInterface.use_optional_ports` but does not validate the names against the bus library; validation and signal generation is generator-dependent.

### Bus interface arrays: `array`, `namingPattern`, `physicalPrefixPattern`

The `array` block lets you define **multiple similar bus interfaces** with one YAML entry (e.g., 4 identical AXI-Stream outputs, one per channel).

Example:

```yaml
array:
  count: 4
  indexStart: 0
  namingPattern: "M_AXIS_CH{index}_EVENTS"
  physicalPrefixPattern: "m_axis_ch{index}_evt_"
```

Semantics:

- `count`: number of instances.
- `indexStart`: starting index. The instance indices are `indexStart .. indexStart + count - 1`.
- `namingPattern`: a format string used to generate the *logical interface name* per instance.
  - `{index}` is replaced with the instance index.
  - Example: with `indexStart: 0`, instance names become `M_AXIS_CH0_EVENTS`, `M_AXIS_CH1_EVENTS`, ...
- `physicalPrefixPattern`: a format string used to generate the *physical HDL prefix* per instance.
  - `{index}` is replaced with the instance index.
  - Example: `m_axis_ch0_evt_`, `m_axis_ch1_evt_`, ...

Current parser behavior (important):

- The YAML parser does **not** expand arrays into multiple `BusInterface` objects.
- Instead it stores `BusInterface.array: ArrayConfig` as metadata. Downstream tooling (generators / editors) is expected to expand the array if needed.
- The `ArrayConfig` model provides helpers like `indices`, `get_instance_name(index)`, and `get_instance_prefix(index)`.

Array mapping (`fpga_lib.model.bus.ArrayConfig`):

- `count` ← YAML `count`
- `index_start` ← YAML `indexStart` (default: `0`)
- `naming_pattern` ← YAML `namingPattern`
- `physical_prefix_pattern` ← YAML `physicalPrefixPattern`

Reference integrity:

- `IpCore.validate_references()` checks that `associatedClock`, `associatedReset`, and `memoryMapRef` refer to known objects by name.

## `parameters` section

### YAML shape

```yaml
parameters:
  - name: "NUM_CHANNELS"
    value: 4
    dataType: "integer"     # optional, defaults to "integer" in parser
    description: "..."      # optional
```

### Model mapping (`fpga_lib.model.base.Parameter`)

- `name` ← YAML `name`
- `value` ← YAML `value` (any YAML scalar/structure; stored as `Any`)
- `data_type` ← YAML `dataType` (default: `"integer"`)
- `description` ← YAML `description`

The `Parameter.data_type` field is an enum (`ParameterType`) and normalizes strings to lowercase.

## `fileSets` section

### YAML shape

`fileSets` is a list. Each entry is either:

1) An inline file set definition

```yaml
- name: "RTL_Sources"
  description: "..."
  files:
    - path: "rtl/my_timer_core_top.v"
      type: "verilog"
      description: "..."  # optional
```

2) An import entry

```yaml
- import: "common/c_api.fileset.yml"
```

### Import behavior

- Import paths are resolved relative to the current YAML file.
- The imported YAML may be a single mapping or a list; it is normalized to a list.
- Imported file sets are parsed using the same `_parse_file_sets` logic.

### Model mapping (`fpga_lib.model.fileset.FileSet`, `fpga_lib.model.fileset.File`)

`FileSet` fields:

- `name` ← YAML `name`
- `description` ← YAML `description`
- `files` ← YAML `files`

`File` fields:

- `path` ← YAML `path`
- `type` ← YAML `type` mapped to `FileType` enum
- `description` ← YAML `description`

Notes on file type parsing:

- The parser first tries `FileType(file_type_str)` directly.
- If that fails, it tries `FileType(file_type_str.upper())`.
- Types like `"verilog"`, `"vhdl"`, `"pdf"` match directly.

## `memoryMaps` section (IP YAML side)

### Supported shapes

The parser supports two shapes for the `memoryMaps` key in the IP YAML:

1) Import form (most common):

```yaml
memoryMaps:
  import: "my_timer_core.memmap.yml"
```

2) Inline list form:

```yaml
memoryMaps:
  - name: "CSR_MAP"
    addressBlocks: [...]
```

If `memoryMaps` is present but not one of these shapes, parsing fails.

## Memory map YAML schema (`*.memmap.yml`)

### Root shape

The "new" memory map format uses a YAML root list:

```yaml
- name: CSR_MAP
  description: "..."
  addressBlocks:
    - name: GLOBAL_REGS
      offset: 0
      usage: register
      registers: [...]
```

The parser also supports a "legacy" multi-document format:

- document 1: a dict containing `registerTemplates`
- document 2: actual memory map structure

### Mapping: memory map → model

A memory map becomes `fpga_lib.model.memory.MemoryMap`:

- YAML `name` → `MemoryMap.name`
- YAML `description` → `MemoryMap.description`
- YAML `addressBlocks` → `MemoryMap.address_blocks`

### Address blocks

Address blocks become `fpga_lib.model.memory.AddressBlock`.

What is an `addressBlocks` entry?

- An `addressBlocks` entry represents a *contiguous chunk* of address space inside a memory map.
- Conceptually it is where you group related registers (e.g., `GLOBAL_REGS`) or define a memory region (e.g., `LOCAL_RAM`).
- In the generated address map, each block has a base and a size; registers inside it live at `block_base + register_offset`.

Supported YAML keys:

- `name` (required)
- `offset` (new format) or `baseAddress` (legacy format)
- `range` (optional)
- `usage` (optional; defaults to `"register"`)
- `description` (optional)
- `registers` (optional; list)

Key terms:

- `offset` / `baseAddress`: the **block base address**, expressed as a byte offset from the start of the memory map.
- `range`: the **size of the block in bytes**. The model supports integers or strings like `"4K"`, `"1M"`; the parser passes the value through to the `AddressBlock` model.
- `usage`: describes what the region is for:
  - `register`: contains registers
  - `memory`: represents a RAM-like region (may have no registers)
  - `reserved`: reserved / not used

Range behavior:

- If `range` is omitted and registers exist, the parser computes a range based on the last register offset and size, with a minimum of 64 bytes.
- If `range` is omitted and there are no registers, the parser defaults to 4096 (4 KB).

Important current limitation:

- The YAML format in `examples/ip/my_timer_core.memmap.yml` includes `defaultRegWidth`, but the parser does not currently read or use it.
- The `AddressBlock` model has `register_arrays`, but the parser expands arrays into flat `registers` and does not populate `register_arrays`.

### Registers

Registers become `fpga_lib.model.memory.Register`.

Supported YAML keys (new and legacy):

- `name` (required)
- `offset` (new) or `addressOffset` (legacy)
- `size` (optional, default 32)
- `access` (optional, default `read-write`)
- `resetValue` (optional)
- `description` (optional)
- `fields` (optional list)

Reserved space:

- A register entry may contain `{ reserved: <bytes> }`, which advances the internal offset without producing a register.

Access type normalization:

- Access strings are normalized by `AccessType.normalize()`.
- Common values include: `read-only`, `write-only`, `read-write`, `write-1-to-clear`.

### Register arrays (two supported syntaxes)

The parser supports two styles of arrays:

1) New nested array form (used in `*.memmap.yml`):

```yaml
- name: TIMER
  count: 4
  stride: 16
  registers:
    - name: CTRL
      offset: 0
    - name: STATUS
      offset: 4
```

  Explanation of `count` and `stride` (new nested array form):

  - `count` is the number of *instances* of the array element to generate. With `count: 4`, the parser generates instances `0, 1, 2, 3`.
  - `stride` is the byte distance between consecutive instances’ base offsets (i.e., how far the next instance is placed in address space). With `stride: 16`, instance 1 starts 16 bytes after instance 0, instance 2 starts 32 bytes after instance 0, etc.
  - Each sub-register’s `offset` is **relative to the instance base**.

  Address calculation (what the parser effectively does):

  $$\text{final\_offset} = \text{array\_base\_offset} + (\text{instance\_idx} \times \text{stride}) + \text{sub\_offset}$$

  Where `array_base_offset` is the running offset within the address block at the point the array appears, `instance_idx` is `0..count-1`, and `sub_offset` is the sub-register’s `offset` (default `0`).

This is expanded into flat registers with hierarchical names:

- `TIMER_0_CTRL`, `TIMER_0_STATUS`, ...
- `TIMER_1_CTRL`, `TIMER_1_STATUS`, ...

2) Legacy `generateArray` form (template-based):

```yaml
- generateArray:
    name: TIMER
    count: 4
    template: TIMER_TEMPLATE
```

The template comes from `registerTemplates` loaded from the memory map YAML.

### Bit fields

Bit fields become `fpga_lib.model.memory.BitField`.

Supported YAML keys:

- `name` (required)
- `bits` (new format, e.g. `"[7:4]"`)
- OR `bitOffset` / `bitWidth` (legacy format)
- `access` (optional)
- `resetValue` or `reset` (optional)
- `description` (optional)

Bits notation (`bits: "[msb:lsb]"`):

- The parser requires a colon form like `[0:0]` (single-bit fields must still include `:`).
- Parsed as:
  - `bit_offset = lsb`
  - `bit_width = msb - lsb + 1`

Auto bit positioning:

- If a field does not specify `bits` or `bitOffset`, the parser assigns offsets sequentially using an internal `current_bit` pointer.

## Reference validation lifecycle

Parsing builds the `IpCore` model but does not automatically call `IpCore.validate_references()`.

If you want reference checking (e.g., a bus interface referencing a missing clock), call:

- `errors = ip_core.validate_references()`

and handle the returned list of human-readable error strings.

## Practical examples

### Minimal IP YAML

```yaml
apiVersion: my-ip-schema/v1.0
vlnv:
  vendor: acme.com
  library: peripherals
  name: gpio
  version: 1.0.0
```

### Memory map import

```yaml
memoryMaps:
  import: "gpio.memmap.yml"
```

## Where to look in code

- Parser: `fpga_lib/parser/yaml/ip_yaml_parser.py`
- Root model: `fpga_lib/model/core.py`
- Memory map models: `fpga_lib/model/memory.py`
- Bus models: `fpga_lib/model/bus.py`
- Fileset models: `fpga_lib/model/fileset.py`
- Clock/reset models: `fpga_lib/model/clock_reset.py`


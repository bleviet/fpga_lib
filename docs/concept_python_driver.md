# IP Core Driver Architecture: Concept Document

## 1\. Introduction

This document outlines a refined conceptual design for a unified Python-based driver architecture for IP cores. The primary goal is to create a single, elegant API that can seamlessly control an IP core in both hardware (via interfaces like JTAG) and simulation (via cocotb). This design promotes code reusability, simplifies maintenance, and standardizes the developer experience.

The architecture is built on the principle of abstraction, separating the high-level register and bit-field logic from the low-level bus access mechanism. This is achieved through a multi-layered, object-oriented approach that is now driven by a human-readable memory map definition.

-----

## 2\. Core Concept: The Memory Map

Manually defining registers and bit-fields in Python for a complex IP core is tedious and error-prone. The foundation of this refined architecture is a **single source of truth** for the IP core's memory map, defined in a simple, human-readable **YAML** file.

This approach decouples the hardware specification from the driver's implementation. The driver will dynamically construct itself based on the contents of this file.

### Why YAML?

Of course. YAML was chosen because it strikes the best balance between **human readability** and its ability to naturally represent the **nested structure** of a hardware memory map.

The primary goal of this file is to be a "single source of truth" that is easy for engineers to read, understand, and, if necessary, edit by hand.

* ✨ Superior Readability: YAML's syntax is minimal and uses indentation to denote structure. This makes the file look clean and almost like a document outline, which is perfect for describing a hierarchy of registers and their bit fields.

* ✍️ Natural for Nested Lists: The core structure is a "list of registers," where each register contains a "list of bit fields." This pattern maps perfectly and intuitively to YAML's indented list format.

* 💬 Essential Comment Support: Hardware design requires documentation. YAML's first-class support for comments (`#`) is crucial for adding descriptions and notes directly within the map, which is a major advantage.

#### Comparison with TOML and JSON

Here’s a direct comparison for this specific use case:

##### Why Not JSON?

The biggest reason is its **lack of support for comments**. For a file that serves as documentation, this is a significant drawback. Additionally, JSON's syntax is much noisier with required braces, quotes, and commas, making it more tedious to read and write manually compared to YAML.

##### Why Not TOML?

TOML is excellent for configuration files, but it's less intuitive for representing a **deeply nested list of complex objects**, which is exactly what a memory map is. Defining an array of registers, each with its own array of fields, can become syntactically awkward and visually disconnected in TOML. YAML’s simple indented structure keeps the definition of a register and its fields grouped together more cleanly.

| Feature | YAML | TOML | JSON |
| :--- | :--- | :--- | :--- |
| **Human Readability** | ✅ **Excellent** | ✅ Good | 🆗 Okay |
| **Comment Support** | ✅ Yes | ✅ Yes | ❌ **No** |
| **Nested Lists/Objects** | ✅ **Very Natural** | 🆗 Awkward | ✅ Natural |


#### Example Memory Map (`ip_core_map.yaml`)

```yaml
# ip_core_map.yaml
# Memory map definition for our example IP core.

registers:
  - name: control
    offset: 0x00
    width: 32 # Register width in bits. Defaults to 32 if omitted.
    description: "Main control register for the core."
    fields:
      - name: enable
        bit: 0
        access: rw
        description: "Enable or disable the core."
      - name: int_enable
        bit: 1
        access: rw
        description: "Enable interrupts."
      - name: soft_reset
        bit: 31
        access: wo # Write-only field
        description: "Trigger a software reset (self-clearing)."

  - name: status
    offset: 0x04
    width: 32
    description: "Status register for the core."
    fields:
      - name: ready
        bit: 0
        access: ro # Read-only field
        description: "Core is ready to accept commands."
      - name: error_code
        bits: [7:4] # Defines a 4-bit field from bit 4 to 7
        access: ro
        description: "Indicates the type of error."

  - name: data_in
    offset: 0x08
    width: 128 # Example of a wider-than-default register
    description: "Input data FIFO."
    fields: # This register has no bit-fields, it's accessed as a whole

  # --- Definition for a Block RAM region ---
  - name: lut_entry
    offset: 0x100      # Base address of the entire block RAM
    count: 64          # There are 64 entries in this RAM
    stride: 4          # Each entry is 4 bytes apart
    description: "A 64-entry lookup table."
    fields: # This is the template for EACH of the 64 entries
      - name: coefficient
        bits: [15:0]
        access: rw
        description: "Coefficient value for this entry."
      - name: enabled
        bit: 31
        access: rw
        description: "Enable this specific LUT entry."
```

-----

## 3\. Architectural Layers

The driver is structured into layers, each with a specific responsibility. The architecture dynamically builds the top-level driver from the memory map.

### Layer 1: The Register Map Loader

This is a new, crucial component. A parser function is responsible for reading the `ip_core_map.yaml` file and programmatically instantiating the `Register` and `BitField` objects. This loader becomes the entry point for defining the driver's structure.

#### Example Implementation (`driver_loader.py`)

```python
import yaml
from enum import Enum, auto

# --- Data Models (explained in next section) ---
class Access(Enum):
    RO = auto(); RW = auto(); WO = auto(); RW1C = auto()

@dataclass
class BitField:
    # ... as defined in the next section

@dataclass
class Register:
    # ... as defined in the next section

def _parse_bits(bits_def):
    """Helper to parse 'bit: 0' or 'bits: [7:4]' into offset and width."""
    if isinstance(bits_def, int):
        return bits_def, 1
    if isinstance(bits_def, str) and ':' in bits_def:
        high, low = map(int, bits_def.strip('[]').split(':'))
        return low, (high - low + 1)
    raise ValueError(f"Invalid bit definition: {bits_def}")

@dataclass
class RegisterArrayAccessor:
    """Provides indexed access to a block of registers."""
    bus_interface: AbstractBusInterface
    base_offset: int
    count: int
    stride: int
    width: int
    field_template: list[BitField]

    def __getitem__(self, index):
        if not (0 <= index < self.count):
            raise IndexError(f"Index {index} out of bounds for array of size {self.count}")
        
        # Calculate the absolute address of the requested element
        item_offset = self.base_offset + (index * self.stride)
        
        # Create a Register object for this specific element on-the-fly
        return Register(
            name=f"item[{index}]",
            offset=item_offset,
            width=self.width,
            bus_interface=self.bus_interface,
            fields=self.field_template
        )

    def __len__(self):
        return self.count

def load_from_yaml(yaml_path: str, bus_interface: AbstractBusInterface):
    """Loads a register map from YAML and builds a driver object."""
    driver = IpCoreDriver(bus_interface=bus_interface)
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    for reg_info in data.get('registers', []):
        fields = []
        for field_info in reg_info.get('fields', []):
            offset, width = _parse_bits(field_info.get('bit') or field_info.get('bits', 0))
            fields.append(BitField(
                name=field_info['name'],
                offset=offset,
                width=width,
                access=Access[field_info.get('access', 'rw').upper()]
            ))
        
        reg_width = reg_info.get('width', 32) # Default to 32-bit registers

        # Check if this is a register array
        if 'count' in reg_info:
            accessor = RegisterArrayAccessor(
                base_offset=reg_info['offset'],
                count=reg_info['count'],
                stride=reg_info.get('stride', reg_width // 8), # Default stride to register width
                width=reg_width,
                field_template=fields,
                bus_interface=bus_interface
            )
            setattr(driver, reg_info['name'], accessor)
        else: # It's a single register
            register = Register(
                name=reg_info['name'],
                offset=reg_info['offset'],
                width=reg_width,
                bus_interface=bus_interface,
                fields=fields
            )
            setattr(driver, reg_info['name'], register)
        
    return driver

@dataclass
class IpCoreDriver:
    """A container for all the register objects."""
    bus_interface: "AbstractBusInterface"
```

### Layer 2: The Core IP Driver and Data Models

This is the top-level API that users interact with. It contains the logical representation of the IP core, populated by the loader. The `Register` and `BitField` classes are now more robust, enforcing access rights and performing proper read-modify-write operations.

#### Example Implementation

```python
from dataclasses import dataclass, field
from enum import Enum, auto

class Access(Enum):
    RO = auto()
    RW = auto()
    WO = auto()

@dataclass
class BitField:
    name: str
    offset: int
    width: int
    access: Access = Access.RW

@dataclass
class Register:
    name: str
    offset: int
    width: int
    bus_interface: "AbstractBusInterface"
    fields: list[BitField] = field(default_factory=list)
    _fields_by_name: dict[str, BitField] = field(init=False, repr=False)

    def __post_init__(self):
        self._fields_by_name = {f.name: f for f in self.fields}

    def read(self):
        """Reads the entire register value."""
        return self.bus_interface.read_word(self.offset, self.width)

    def write(self, value: int):
        """Writes a value to the entire register."""
        self.bus_interface.write_word(self.offset, value, self.width)

    def __getattr__(self, name: str):
        if name not in self._fields_by_name:
            raise AttributeError(f"Register '{self.name}' has no bit-field named '{name}'")
        
        field = self._fields_by_name[name]
        mask = ((1 << field.width) - 1) << field.offset

        def getter(_):
            if field.access == Access.WO:
                raise AttributeError(f"Bit-field '{name}' is write-only.")
            return (self.read() & mask) >> field.offset

        def setter(_, value: int):
            if field.access == Access.RO:
                raise AttributeError(f"Bit-field '{name}' is read-only.")
            
            reg_value = self.read() if field.access == Access.RW else 0
            cleared_val = reg_value & ~mask
            new_reg_value = cleared_val | ((value << field.offset) & mask)
            self.write(new_reg_value)

        return property(getter, setter)
```

### Layer 3: The Bus Interface

This abstraction layer defines the contract for all bus backends. By using Python's `abc` module, we enforce that any concrete implementation provides the necessary methods.

#### Example Implementation

```python
from abc import ABC, abstractmethod

class AbstractBusInterface(ABC):
    @abstractmethod
    def read_word(self, address: int, width: int) -> int:
        """Reads a single word of a given width (in bits) from the given address."""
        raise NotImplementedError

    @abstractmethod
    def write_word(self, address: int, data: int, width: int) -> None:
        """Writes a single word of a given width (in bits) to the given address."""
        raise NotImplementedError
```

### Layer 4: The Concrete Bus Backends

These are the environment-specific implementations of the `AbstractBusInterface`.

#### Simulation Backend (CocotbBus)

```python
from cocotb.bus.axibuses import Axi4LiteBus

class CocotbBus(AbstractBusInterface):
    def __init__(self, dut, bus_name, clock):
        self._axi_driver = Axi4LiteBus.from_entity(dut, bus_name, clock)

    async def read_word(self, address: int, width: int) -> int:
        # Note: AXI4-Lite is typically 32-bit. Wider reads would require a different bus or protocol.
        # This implementation would need to be adapted for non-32-bit buses.
        if width > 32:
            # Perform multiple reads for wider registers
            num_reads = (width + 31) // 32
            val = 0
            for i in range(num_reads):
                word = await self._axi_driver.read(address + i * 4)
                val |= int(word) << (i * 32)
            return val
        val = await self._axi_driver.read(address)
        return int(val)

    async def write_word(self, address: int, data: int, width: int) -> None:
        if width > 32:
            num_writes = (width + 31) // 32
            for i in range(num_writes):
                word = (data >> (i * 32)) & 0xFFFFFFFF
                await self._axi_driver.write(address + i * 4, word)
            return
        await self._axi_driver.write(address, data)
```

#### Hardware Backend (JtagBus)

```python
import tclrpc  # A library for JTAG access

class JtagBus(AbstractBusInterface):
    def __init__(self, xsdb_session):
        self._xsdb = xsdb_session

    def read_word(self, address: int, width: int) -> int:
        # JTAG memory access might also have width limitations.
        # This is a simplified example.
        num_bytes = (width + 7) // 8
        data_bytes = self._xsdb.read_mem(address, num_bytes)
        return int.from_bytes(data_bytes, 'little')

    def write_word(self, address: int, data: int, width: int) -> None:
        num_bytes = (width + 7) // 8
        data_bytes = data.to_bytes(num_bytes, 'little')
        self._xsdb.write_mem(address, list(data_bytes))
```

-----

## 4\. The Unified Factory and Configuration

To seamlessly switch between environments, the factory is now simplified. It takes a self-contained configuration object, instantiates the correct bus backend, and then uses the `load_from_yaml` function to build and return the complete driver.

#### Example Configuration (`config.py`)

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class AxiSimConfig:
    dut: Any
    bus_name: str
    clock: Any

@dataclass
class JtagBusConfig:
    xsdb_session: Any

@dataclass
class DriverConfig:
    map_file: str # Path to the YAML file
    bus_type: str
    bus_spec: AxiSimConfig | JtagBusConfig
```

#### Example Usage

```python
# In a simulation testbench
sim_config = DriverConfig(
    map_file="ip_core_map.yaml",
    bus_type="sim",
    bus_spec=AxiSimConfig(dut=dut, bus_name="s_axi", clock=dut.aclk)
)
driver = create_driver(config=sim_config)

# In a hardware test script
hw_config = DriverConfig(
    map_file="ip_core_map.yaml",
    bus_type="jtag",
    bus_spec=JtagBusConfig(xsdb_session=tclrpc.connect(...))
)
driver = create_driver(config=hw_config)

# --- The API is identical in both environments! ---
driver.control.enable = 1
status = driver.status.ready

# --- Register arrays provide clean access to Block RAM ---
# Accessing the 5th entry in the lookup table:
driver.lut_entry[5].coefficient = 0xABCD

# Enabling the 10th entry:
driver.lut_entry[10].enabled = 1

# Reading a value back from the 5th entry:
coeff = driver.lut_entry[5].coefficient

# Can also write to the whole register in the array
driver.lut_entry[20].write(0xFFFFFFFF)
```

-----

## 5\. Key Advantages

  - **Single Source of Truth**: The YAML memory map ensures that hardware documentation, simulation, and hardware control are always in sync.
  - **Portability and Reusability**: A single test script can be executed against both a simulator and a physical FPGA with only a configuration change.
  - **Reduced Boilerplate**: The register map loader eliminates the need to manually write and maintain tedious register definition code. 📝
  - **Decoupled Design**: Changes to a bus protocol do not require changes to the high-level register access logic.
  - **Clean and Intuitive API**: The user-facing API allows developers to interact with registers and bit fields using simple, dot notation (`driver.reg_name.field_name`).
  - **Handles Complex Structures**: The architecture elegantly supports not only single registers but also complex register arrays and block RAM regions. 🎛️
  - **Memory Efficient**: The driver is lightweight as it doesn't pre-instantiate hundreds of objects for a large RAM; register objects are created on-demand.
  - **Scalability**: New bus backends (e.g., for PCIe or SPI) can be added by simply implementing the `AbstractBusInterface`.

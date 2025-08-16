# IP Core Driver Architecture: Concept Document

## 1\. Introduction

This document outlines a refined conceptual design for a unified Python-based driver architecture for IP cores. The primary goal is to create a single, elegant API that can seamlessly control an IP core in both hardware (via interfaces like JTAG) and simulation (via cocotb). This design promotes code reusability, simplifies maintenance, and standardizes the developer experience.

The architecture is built on the principle of abstraction, separating the high-level register and bit-field logic from the low-level bus access mechanism. This is achieved through a multi-layered, object-oriented approach that is now driven by a human-readable memory map definition.

-----

## 2\. Core Concept: The Memory Map

Manually defining registers and bit-fields in Python for a complex IP core is tedious and error-prone. The foundation of this refined architecture is a **single source of truth** for the IP core's memory map, defined in a simple, human-readable **YAML** file.

This approach decouples the hardware specification from the driver's implementation. The driver will dynamically construct itself based on the contents of this file.

#### Example Memory Map (`ip_core_map.yaml`)

```yaml
# ip_core_map.yaml
# Memory map definition for our example IP core.

registers:
  - name: control
    offset: 0x00
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
    description: "Input data FIFO."
    fields: # This register has no bit-fields, it's accessed as a whole
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
    RO = auto(); RW = auto(); WO = auto()

@dataclass
class BitField:
    # ... as defined in the next section

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

def load_from_yaml(yaml_path: str, bus_interface: AbstractBusInterface):
    """Loads a register map from YAML and builds a driver object."""
    driver = IpCoreDriver(bus_interface)
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
        
        register = Register(
            name=reg_info['name'],
            offset=reg_info['offset'],
            bus_interface=bus_interface,
            fields=fields
        )
        setattr(driver, reg_info['name'], register)
        
    return driver

class IpCoreDriver:
    """A container for all the register objects."""
    def __init__(self, bus_interface):
        self._bus = bus_interface
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

class Register:
    def __init__(self, name, offset, bus_interface, fields: list[BitField]):
        self._name = name
        self._offset = offset
        self._bus = bus_interface
        self._fields = {f.name: f for f in fields}

    def read(self):
        """Reads the entire register value."""
        return self._bus.read_word(self._offset)

    def write(self, value: int):
        """Writes a value to the entire register."""
        self._bus.write_word(self._offset, value)

    def __getattr__(self, name: str):
        if name not in self._fields:
            raise AttributeError(f"Register '{self._name}' has no bit-field named '{name}'")
        
        field = self._fields[name]
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
    def read_word(self, address: int) -> int:
        """Reads a single word from the given address."""
        raise NotImplementedError

    @abstractmethod
    def write_word(self, address: int, data: int) -> None:
        """Writes a single word to the given address."""
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

    async def read_word(self, address: int) -> int:
        val = await self._axi_driver.read(address)
        return int(val)

    async def write_word(self, address: int, data: int) -> None:
        await self._axi_driver.write(address, data)
```

#### Hardware Backend (JtagBus)

```python
import tclrpc  # A library for JTAG access

class JtagBus(AbstractBusInterface):
    def __init__(self, xsdb_session):
        self._xsdb = xsdb_session

    def read_word(self, address: int) -> int:
        return self._xsdb.read_mem(address, 1)[0]

    def write_word(self, address: int, data: int) -> None:
        self._xsdb.write_mem(address, [data])
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
```

-----

## 5\. Key Advantages

  - **Single Source of Truth**: The YAML memory map ensures that hardware documentation, simulation, and hardware control are always in sync.
  - **Portability and Reusability**: A single test script can be executed against both a simulator and a physical FPGA with only a configuration change.
  - **Reduced Boilerplate**: The register map loader eliminates the need to manually write and maintain tedious register definition code. 📝
  - **Decoupled Design**: Changes to a bus protocol do not require changes to the high-level register access logic.
  - **Clean and Intuitive API**: The user-facing API allows developers to interact with registers and bit fields using simple, dot notation (`driver.reg_name.field_name`).
  - **Scalability**: New bus backends (e.g., for PCIe or SPI) can be added by simply implementing the `AbstractBusInterface`.

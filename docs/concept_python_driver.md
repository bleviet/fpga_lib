# IP Core Driver Architecture: Concept Document

## 1. Introduction

This document outlines the conceptual design for a unified Python-based driver architecture for IP cores. The primary goal is to create a single, elegant API that can seamlessly control an IP core in both hardware (via interfaces like JTAG) and simulation (via cocotb). This design promotes code reusability, simplifies maintenance, and standardizes the developer experience across different environments.

The architecture is built on the principle of abstraction, separating the high-level register and bit-field logic from the low-level bus access mechanism. This separation is achieved through a multi-layered, object-oriented approach that heavily leverages the `dataclasses` library for concise and robust data modeling.

---

## 2. Architectural Layers

The driver is structured into three main layers, each with a specific responsibility.

### Layer 1: The Core IP Driver

This is the top-level API that users interact with. It contains the logical representation of the IP core, including its registers and bit fields. The `IpCoreDriver` class and its nested `Register` and `BitField` classes are protocol-agnostic. They do not contain any bus-specific read or write logic. Instead, they rely on the layer below to perform all I/O operations. This design ensures that the high-level API remains consistent, regardless of the underlying bus technology.

The use of `dataclasses` here significantly reduces boilerplate code, making the models for hardware components clear and concise. This makes the code more readable and easier to maintain.

#### Example Implementation

```python
from dataclasses import dataclass, field

@dataclass
class BitField:
    name: str
    offset: int
    width: int
    access: str = 'rw'

class Register:
    def __init__(self, name, offset, bus_interface, fields: list[BitField]):
        self._bus = bus_interface
        self._fields = {f.name: f for f in fields}
        # ... other initializations
    
    def __getattr__(self, name):
        """Dynamic getter for bit fields."""
        if name in self._fields:
            field = self._fields[name]
            def getter():
                reg_value = self.read()
                # Bit-wise operations to read field
                return (reg_value >> field.offset) & ((1 << field.width) - 1)
            # ... and a setter for writing
            return property(getter, setter)
```

---

### Layer 2: The Bus Interface

This is the key abstraction layer. It defines a standardized interface (`AbstractBusInterface`) with methods for basic word-level read and write operations (`read_word`, `write_word`). This interface acts as a contract, ensuring that any lower-level bus implementation adheres to the required API. It hides the complexities of bus protocols from the higher layers.

#### Example Implementation

```python
class AbstractBusInterface:
    def read_word(self, address):
        raise NotImplementedError

    def write_word(self, address, data):
        raise NotImplementedError
```

---

### Layer 3: The Concrete Bus Backends

This is where the environment-specific implementation resides. Each concrete bus backend implements the `AbstractBusInterface` for a particular environment.

#### Simulation Backend (CocotbBus)

Wraps a cocotb-bus driver (e.g., `Axi4LiteBus` or `AvalonBus`). It handles the asynchronous nature of simulation, using `await` for transactions. This backend translates the high-level `read_word` call into the correct cocotb-bus transaction, including all handshake and timing details.

##### Example

```python
from cocotb.bus.axibuses import Axi4LiteBus

class CocotbBus(AbstractBusInterface):
    def __init__(self, dut, bus_name, clock):
        self._axi_driver = Axi4LiteBus.from_entity(dut, bus_name, clock)

    async def read_word(self, address):
        return await self._axi_driver.read(address=address)
```

#### Hardware Backend (JtagBus)

Wraps a hardware communication library (e.g., `tclrpc` for Vivado's XSDB). This backend handles synchronous or blocking I/O, converting `read_word` calls into the appropriate JTAG commands to physically communicate with the device.

##### Example

```python
import tclrpc  # A library for JTAG access

class JtagBus(AbstractBusInterface):
    def __init__(self, xsdb_session):
        self._xsdb = xsdb_session

    def read_word(self, address):
        return self._xsdb.read_mem(address, 1)[0]
```

---

## 3. The Unified Factory and Configuration

To seamlessly switch between environments, the architecture includes a driver factory. This is a simple function (`create_driver`) that takes a configuration object as input. The configuration specifies the intended environment and bus type (e.g., "sim" with an "Avalon" bus or "jtag"). The factory function inspects this configuration and instantiates the correct concrete bus backend, then uses it to build and return the complete `IpCoreDriver` object.

The configuration itself is a perfect use case for `dataclasses`, as they provide a clear, type-hinted way to define the parameters for each bus.

#### Example Configuration (`config.py`)

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class AxiSimConfig:
    bus_name: str
    clock: Any

@dataclass
class JtagBusConfig:
    xsdb_session: Any

@dataclass
class DriverConfig:
    bus_type: str
    bus_spec: AxiSimConfig | JtagBusConfig
```

#### Example Usage

##### Simulation Testbench (e.g., `test_axi_ip.py`)

```python
config = DriverConfig(
    bus_type="sim",
    bus_spec=AxiSimConfig(bus_name="s_axi", clock=dut.aclk)
)
driver = create_driver(dut=dut, config=config)

await driver.some_register.enable = 1
```

##### Hardware Test Script (e.g., `run_hw_test.py`)

```python
xsdb_session = tclrpc.connect(...)
config = DriverConfig(
    bus_type="jtag",
    bus_spec=JtagBusConfig(xsdb_session=xsdb_session)
)
driver = create_driver(dut=None, config=config)

driver.some_register.status = 1
```

---

## 4. Key Advantages

- **Portability and Reusability**: A single test script can be executed in both a simulator and on a physical FPGA, significantly reducing development effort.
- **Decoupled Design**: Changes to a bus protocol (e.g., updating a cocotb-bus driver) do not require changes to the high-level register access logic.
- **Clear and Clean API**: The user-facing API is intuitive, allowing developers to interact with registers and bit fields using simple dot notation (`driver.reg_name.field_name`).
- **Scalability**: New bus backends (e.g., for PCIe or SPI) can be added by simply implementing the `AbstractBusInterface` without modifying existing code.
- **Dataclasses Benefits**: The use of the `dataclasses` library provides clear data models 📊, reduces boilerplate code 📝, and ensures robustness by preventing common bugs with mutable default arguments.

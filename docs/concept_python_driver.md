# IP Core Driver Architecture: Concept Document

## 1. Introduction

This document outlines the design for a unified Python-based driver architecture for IP cores. The primary goal is to create a single, elegant API that can seamlessly control an IP core in both hardware (via interfaces like JTAG) and simulation (via cocotb). This design promotes code reusability, simplifies maintenance, and standardizes the developer experience.

The architecture is built on the principle of abstraction, separating the high-level register and bit-field logic from the low-level bus access mechanism. This is achieved through a multi-layered, object-oriented approach driven by a human-readable memory map definition.

---

## 2. Core Concept: The Memory Map

Manually defining registers and bit-fields in Python for a complex IP core is tedious and error-prone. The foundation of this architecture is a **single source of truth** for the IP core's memory map, defined in a simple, human-readable **YAML** file.

This approach decouples the hardware specification from the driver's implementation. The driver dynamically constructs itself based on the contents of this file.

### Why YAML?

YAML was chosen because it strikes the best balance between **human readability** and its ability to naturally represent the **nested structure** of a hardware memory map.

* ✨ **Superior Readability**: YAML's syntax is minimal and uses indentation to denote structure
* ✍️ **Natural for Nested Lists**: Registers containing bit fields map perfectly to YAML's indented list format
* 💬 **Comment Support**: First-class support for comments (`#`) is crucial for documentation

| Feature | YAML | TOML | JSON |
| :--- | :--- | :--- | :--- |
| **Human Readability** | ✅ **Excellent** | ✅ Good | 🆗 Okay |
| **Comment Support** | ✅ Yes | ✅ Yes | ❌ **No** |
| **Nested Lists/Objects** | ✅ **Very Natural** | 🆗 Awkward | ✅ Natural |

### Example Memory Map

```yaml
# my_timer_core.memmap.yml
- name: CSR_MAP
  description: Control/Status Registers
  addressBlocks:
    - name: GLOBAL_REGS
      offset: 0x00
      range: 4K
      registers:
        - name: CONTROL
          offset: 0x00
          fields:
            - name: ENABLE
              bits: "[0:0]"
              access: read-write
            - name: INT_ENABLE
              bits: "[1:1]"
              access: read-write
            - name: SOFT_RESET
              bits: "[31:31]"
              access: write-only

        - name: STATUS
          offset: 0x04
          access: read-only
          fields:
            - name: READY
              bits: "[0:0]"
            - name: ERROR_CODE
              bits: "[7:4]"

    - name: LUT_BLOCK
      offset: 0x100
      registers:
        - name: LUT_ENTRY
          count: 64
          stride: 4
          fields:
            - name: COEFFICIENT
              bits: "[15:0]"
            - name: ENABLED
              bits: "[31:31]"
```

---

## 3. Implementation Architecture

The driver is structured into layers, each with a specific responsibility. The implementation is split across several modules in `ipcore_lib`:

```
ipcore_lib/
├── core/
│   └── register.py          # Runtime register classes (AccessType, BitField, Register, RegisterArrayAccessor)
├── model/
│   └── memory.py             # Pydantic models for YAML parsing (RegisterDef, BitFieldDef, MemoryMap)
└── driver/
    ├── bus.py                # AbstractBusInterface and CocotbBus
    └── loader.py             # load_driver() function
```

### Layer 1: Pydantic Models for YAML Parsing

The `ipcore_lib.model.memory` module provides Pydantic models for parsing and validating YAML files:

```python
from ipcore_lib.model import (
    MemoryMap,
    AddressBlock,
    RegisterDef,    # Pydantic model for YAML
    BitFieldDef,    # Pydantic model for YAML
    AccessType,
)

# These are schema/definition models, not runtime objects
# Use to_runtime_*() methods to convert to runtime objects
```

### Layer 2: Runtime Register Classes

The `ipcore_lib.core.register` module provides runtime register classes for hardware access:

```python
from ipcore_lib.core.register import (
    AccessType,             # Enum: RO, WO, RW, RW1C
    BitField,               # Runtime bit field with offset, width, access
    Register,               # Runtime register with bus I/O
    RegisterArrayAccessor,  # Indexed access to register arrays
    AbstractBusInterface,   # ABC for bus backends
)
```

#### AccessType Enum

```python
class AccessType(Enum):
    RO = 'ro'       # Read-only
    WO = 'wo'       # Write-only
    RW = 'rw'       # Read-write
    RW1C = 'rw1c'   # Read-write-1-to-clear
```

#### BitField Class

```python
@dataclass
class BitField:
    name: str
    offset: int                           # Bit position (0-based, LSB = 0)
    width: int                            # Number of bits
    access: Union[AccessType, str] = AccessType.RW
    description: str = ''
    reset_value: Optional[int] = None
    
    @property
    def mask(self) -> int:
        """Bit mask for this field."""
        return ((1 << self.width) - 1) << self.offset
```

#### Register Class

```python
class Register:
    def __init__(self, name: str, offset: int, bus: AbstractBusInterface,
                 fields: List[BitField], description: str = ''):
        ...
    
    def read(self) -> int:
        """Read entire register value."""
        return self._bus.read_word(self.offset)
    
    def write(self, value: int) -> None:
        """Write entire register value."""
        self._bus.write_word(self.offset, value)
    
    def read_field(self, field_name: str) -> int:
        """Read specific bit field."""
        ...
    
    def write_field(self, field_name: str, value: int) -> None:
        """Write specific bit field (read-modify-write)."""
        ...
```

#### RegisterArrayAccessor Class

```python
class RegisterArrayAccessor:
    """Provides indexed access to register arrays (Block RAM regions)."""
    
    def __init__(self, name: str, base_offset: int, count: int, stride: int,
                 field_template: List[BitField], bus_interface: AbstractBusInterface):
        ...
    
    def __getitem__(self, index: int) -> Register:
        """Access specific element, creating Register on-demand."""
        ...
    
    def __len__(self) -> int:
        return self._count
```

### Layer 3: Bus Interface

The `AbstractBusInterface` ABC defines the contract for all bus backends:

```python
from abc import ABC, abstractmethod

class AbstractBusInterface(ABC):
    @abstractmethod
    def read_word(self, address: int) -> int:
        """Read a 32-bit word from the given address."""
        pass

    @abstractmethod
    def write_word(self, address: int, data: int) -> None:
        """Write a 32-bit word to the given address."""
        pass
```

### Layer 4: Concrete Bus Backends

#### Simulation Backend (CocotbBus)

```python
from ipcore_lib.core.register import AbstractBusInterface

class CocotbBus(AbstractBusInterface):
    """Bus interface for cocotb simulations using AXI-Lite."""
    
    def __init__(self, dut, bus_name: str, clock):
        from cocotbext.axi import AxiLiteMaster, AxiLiteBus
        bus = AxiLiteBus.from_prefix(dut, bus_name)
        self._axi = AxiLiteMaster(bus, clock, dut.rst)

    async def read_word(self, address: int) -> int:
        val = await self._axi.read(address, 4)
        return int.from_bytes(val.data, byteorder='little')

    async def write_word(self, address: int, data: int) -> None:
        await self._axi.write(address, data.to_bytes(4, byteorder='little'))
```

#### Hardware Backend (JtagBus)

```python
class JtagBus(AbstractBusInterface):
    """Bus interface for hardware access via JTAG."""
    
    def __init__(self, xsdb_session):
        self._xsdb = xsdb_session

    def read_word(self, address: int) -> int:
        return self._xsdb.read_mem(address, 1)[0]

    def write_word(self, address: int, data: int) -> None:
        self._xsdb.write_mem(address, [data])
```

---

## 4. Handling Async Operations in Cocotb

### The Challenge

In cocotb, bus operations must be `async` (awaited). This creates a fundamental limitation:

```python
# This CANNOT work in async context:
driver.CONTROL.ENABLE = 1  # Property setter can't be async

# This is REQUIRED in cocotb:
await driver.CONTROL.write_field('ENABLE', 1)  # Explicit async call
```

### Solution: Dual API Pattern

The driver provides **two APIs** depending on the use case:

#### 1. Synchronous API (Hardware/Blocking)

For hardware backends (JTAG, SPI, etc.) where operations are blocking:

```python
# Works with JtagBus and other synchronous backends
driver.GLOBAL_REGS.CONTROL.ENABLE = 1
status = driver.GLOBAL_REGS.STATUS.READY
```

#### 2. Async API (Simulation/Cocotb)

For cocotb simulations, use explicit async methods:

```python
# In cocotb test functions
@cocotb.test()
async def test_registers(dut):
    driver = await create_async_driver(dut)
    
    # Read/write entire register
    await driver.GLOBAL_REGS.CONTROL.write(0x01)
    val = await driver.GLOBAL_REGS.CONTROL.read()
    
    # Read/write specific fields
    await driver.GLOBAL_REGS.CONTROL.write_field('ENABLE', 1)
    ready = await driver.GLOBAL_REGS.STATUS.read_field('READY')
    
    # Register arrays
    await driver.LUT_BLOCK.LUT_ENTRY[5].write_field('COEFFICIENT', 0xABCD)
```

### Alternative: Shadow Register Pattern

For cases where property-style access is desired in simulation, use **shadow registers**:

```python
class ShadowRegister:
    """Cached register that batches writes."""
    
    def __init__(self, register: Register):
        self._reg = register
        self._shadow = 0
        self._dirty = False
    
    def __setattr__(self, name: str, value: int):
        if name.startswith('_'):
            super().__setattr__(name, value)
            return
        # Update shadow, mark dirty
        field = self._reg._fields[name]
        self._shadow = field.insert_value(self._shadow, value)
        self._dirty = True
    
    async def commit(self):
        """Flush shadow to hardware."""
        if self._dirty:
            await self._reg.write(self._shadow)
            self._dirty = False

# Usage:
shadow = ShadowRegister(driver.GLOBAL_REGS.CONTROL)
shadow.ENABLE = 1
shadow.INT_ENABLE = 1
await shadow.commit()  # Single bus transaction
```

---

## 5. Driver Loading

The `load_driver` function creates a complete driver from a YAML memory map:

```python
from ipcore_lib.driver import load_driver, CocotbBus
from ipcore_lib.core.register import AbstractBusInterface

# For simulation
bus = CocotbBus(dut, 's_axi', dut.clk)
driver = load_driver('my_core_memmap.yml', bus)

# For hardware
bus = JtagBus(xsdb_session)
driver = load_driver('my_core_memmap.yml', bus)

# Access registers (async in cocotb, sync in hardware)
await driver.GLOBAL_REGS.CONTROL.write_field('ENABLE', 1)
```

---

## 6. Complete Example

### Cocotb Testbench

```python
import cocotb
from cocotb.clock import Clock
from ipcore_lib.driver import load_driver
from ipcore_lib.driver.bus import CocotbBus

@cocotb.test()
async def test_ip_core(dut):
    """Test the IP core registers."""
    
    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst.value = 1
    await cocotb.triggers.ClockCycles(dut.clk, 10)
    dut.rst.value = 0
    await cocotb.triggers.ClockCycles(dut.clk, 5)
    
    # Create driver
    bus = CocotbBus(dut, 's_axi', dut.clk)
    driver = load_driver('my_timer_core_memmap.yml', bus)
    
    # Test control register
    await driver.GLOBAL_REGS.CONTROL.write_field('ENABLE', 1)
    await driver.GLOBAL_REGS.CONTROL.write_field('INT_ENABLE', 1)
    
    # Verify status
    ready = await driver.GLOBAL_REGS.STATUS.read_field('READY')
    assert ready == 1, "Core should be ready"
    
    # Test LUT array
    for i in range(64):
        await driver.LUT_BLOCK.LUT_ENTRY[i].write_field('COEFFICIENT', i * 10)
        await driver.LUT_BLOCK.LUT_ENTRY[i].write_field('ENABLED', 1)
    
    # Verify LUT
    coeff = await driver.LUT_BLOCK.LUT_ENTRY[32].read_field('COEFFICIENT')
    assert coeff == 320, f"Expected 320, got {coeff}"
```

### Hardware Test Script

```python
from ipcore_lib.driver import load_driver
from my_jtag_lib import JtagBus, connect_xsdb

# Connect to hardware
xsdb = connect_xsdb('localhost:3121')
bus = JtagBus(xsdb)
driver = load_driver('my_timer_core_memmap.yml', bus)

# Same API, but synchronous (no await)
driver.GLOBAL_REGS.CONTROL.write_field('ENABLE', 1)
ready = driver.GLOBAL_REGS.STATUS.read_field('READY')
print(f"Core ready: {ready}")

# LUT programming
for i in range(64):
    driver.LUT_BLOCK.LUT_ENTRY[i].write_field('COEFFICIENT', i * 10)
```

---

## 7. Key Advantages

| Advantage | Description |
|-----------|-------------|
| **Single Source of Truth** | YAML memory map ensures hardware, simulation, and tests are in sync |
| **Portability** | Same test script works on simulator and hardware (with config change) |
| **Reduced Boilerplate** | Register map loader eliminates manual register definition code |
| **Decoupled Design** | Bus protocol changes don't affect register access logic |
| **Type Safety** | Pydantic validation catches YAML errors at load time |
| **Memory Efficient** | Register arrays create objects on-demand |
| **Scalable** | New bus backends (PCIe, SPI) just implement `AbstractBusInterface` |

---

## 8. Module Reference

| Module | Purpose |
|--------|---------|
| `ipcore_lib.core.register` | Runtime register classes (`Register`, `BitField`, `AccessType`, `RegisterArrayAccessor`) |
| `ipcore_lib.model.memory` | Pydantic models for YAML parsing (`RegisterDef`, `BitFieldDef`, `MemoryMap`) |
| `ipcore_lib.driver.loader` | `load_driver()` function, `IpCoreDriver` class |
| `ipcore_lib.driver.bus` | `AbstractBusInterface`, `CocotbBus` |

# IP Core Driver Architecture: Concept Document

## 1\. Introduction

This document outlines a refined conceptual design for a unified Python-based driver architecture for IP cores. The primary goal is to create a single, elegant API that can seamlessly control an IP core in both hardware (via interfaces like JTAG) and simulation (via cocotb). This design promotes code reusability, simplifies maintenance, and standardizes the developer experience.

The architecture is built on the principle of abstraction, separating the high-level register and bit-field logic from the low-level bus access mechanism. This is achieved through a multi-layered, object-oriented approach that is now driven by a human-readable memory map definition.

-----

## 2\. Core Concept: The Memory Map

Manually defining registers and bit-fields indoc = generate_register_documentation(memory_map)
print(doc)
# Generates formatted documentation with ASCII bit diagrams
```

## 8. Usage Example

```python
# Example with the improved architecture
from fpga_lib.core.register import MemoryMap, Register, BitField, AccessType
from your_bus_implementation import SomeBusInterface

# Define register structure (pure data)
control_reg = Register(
    name="control",
    offset=0x00,
    width=32,
    fields=[
        BitField(name="enable", bit_range="0", access=AccessType.RW, description="Enable bit"),
        BitField(name="mode", bit_range="3:1", access=AccessType.RW, description="Operation mode"),
        BitField(name="start", bit_range="4", access=AccessType.W1SC, description="Start command"),
    ]
)

status_reg = Register(
    name="status",
    offset=0x04,
    width=32,
    fields=[
        BitField(name="busy", bit_range="0", access=AccessType.R, description="Busy flag"),
        BitField(name="error", bit_range="1", access=AccessType.RW1C, description="Error flag"),
    ]
)

# Create memory map with bus interface
bus = SomeBusInterface()
memory_map = MemoryMap(
    base_address=0x10000000,
    bus_interface=bus,
    registers=[control_reg, status_reg]
)

# Access registers through memory map
memory_map.control.enable.write(1)
memory_map.control.mode.write(3)
memory_map.control.start.write(1)  # Trigger operation

# Read status
if memory_map.status.busy.read():
    print("Operation in progress")

# Debug support
print(memory_map.control.debug_info())
```

## 9. Key Benefits

1. **Separation of Concerns**: Register definitions are pure data structures, independent of bus access
2. **Clean Architecture**: Bus interface is properly encapsulated at the MemoryMap level
3. **Flexibility**: Register definitions can be reused across different bus implementations
4. **Testability**: Register logic can be tested independently of bus interface
5. **Type Safety**: Enhanced with proper type hints and validation
6. **Enhanced Debugging**: Rich debugging and comparison capabilities
7. **Backward Compatibility**: Graceful handling of optional dependencies like bitstring

This architecture provides a clean separation between what registers *are* (data structure) and how they are *accessed* (through the memory map), leading to better maintainability and testability.

-----

## 5. Key Advantagesfor a complex IP core is tedious and error-prone. The foundation of this refined architecture is a **single source of truth** for the IP core's memory map, defined in a simple, human-readable **YAML** file.

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
from bitstring import BitArray

# --- Data Models (explained in next section) ---
class Access(Enum):
    RO = auto(); RW = auto(); WO = auto(); RW1C = auto(); W1SC = auto()

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
    memory_map: "MemoryMap"
    name: str
    base_offset: int
    count: int
    stride: int
    width: int
    field_template: list[BitField]

    def __getitem__(self, index: int) -> "RegisterProxy":
        if not (0 <= index < self.count):
            raise IndexError(f"Index {index} out of bounds for array of size {self.count}")
        
        # Calculate the absolute address of the requested element
        item_offset = self.base_offset + (index * self.stride)
        
        # Create a register definition for this array element
        element_register = Register(
            name=f"{self.name}[{index}]",
            offset=item_offset,
            width=self.width,
            fields=self.field_template
        )
        
        # Return a proxy that uses the memory map for access
        return RegisterProxy(self.memory_map, element_register)

    def __len__(self):
        return self.count

class RegisterProxy:
    """Proxy that provides register access through the memory map."""
    
    def __init__(self, memory_map: "MemoryMap", register: Register):
        self.memory_map = memory_map
        self.register = register
    
    def read(self) -> Union[int, BitArray]:
        """Read the entire register."""
        raw_value = self.memory_map.bus_interface.read_word(
            self.memory_map.base_address + self.register.offset, 
            self.register.width
        )
        if BITSTRING_AVAILABLE:
            return BitArray(uint=raw_value, length=self.register.width)
        return raw_value
    
    def write(self, value: Union[int, BitArray]) -> None:
        """Write the entire register."""
        if BITSTRING_AVAILABLE and hasattr(value, 'uint'):
            int_value = value.uint
        else:
            int_value = int(value)
        
        self.memory_map.bus_interface.write_word(
            self.memory_map.base_address + self.register.offset,
            int_value,
            self.register.width
        )
    
    def debug_info(self) -> str:
        """Get debug information for this register."""
        register_value = self.read()
        return self.register.debug_info(register_value)
    
    def compare_with(self, other_value: Union[int, BitArray]) -> str:
        """Compare current register value with another value."""
        current = self.read()
        
        if BITSTRING_AVAILABLE:
            if hasattr(current, 'uint'):
                current_int = current.uint
            else:
                current_int = int(current)
                
            if hasattr(other_value, 'uint'):
                other_int = other_value.uint
            else:
                other_int = int(other_value)
                
            current_bits = BitArray(uint=current_int, length=self.register.width)
            other_bits = BitArray(uint=other_int, length=self.register.width)
            diff = current_bits ^ other_bits
            return f"Differences: {diff.bin} (changed bits marked as 1)"
        else:
            current_int = int(current)
            other_int = int(other_value)
            diff = current_int ^ other_int
            return f"Differences: 0x{diff:0{self.register.width//4}X} (XOR result)"

    def __getattr__(self, name: str):
        """Dynamic field access."""
        if name.startswith('_') or name in ['memory_map', 'register']:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        if name not in self.register._fields_by_name:
            raise AttributeError(f"Register '{self.register.name}' has no field named '{name}'")

        field = self.register._fields_by_name[name]

        class FieldProperty:
            def __init__(self, proxy, field):
                self._proxy = proxy
                self._field = field

            def read(self):
                register_value = self._proxy.read()
                return self._proxy.register.read_field(self._field.name, register_value)

            def write(self, value: int):
                if self._field.access in ['rw', 'rw1c']:
                    current_value = self._proxy.read()
                else:
                    current_value = 0
                
                new_value = self._proxy.register.write_field(self._field.name, current_value, value)
                self._proxy.write(new_value)

            def __int__(self):
                return self.read()

            def __str__(self):
                try:
                    return str(self.read())
                except ValueError:
                    return f"<write-only field '{self._field.name}'>"

        return FieldProperty(self, field)

    def __setattr__(self, name: str, value):
        """Dynamic field writing."""
        if name in ['memory_map', 'register']:
            super().__setattr__(name, value)
        elif hasattr(self, 'register') and name in self.register._fields_by_name:
            field_prop = getattr(self, name)
            field_prop.write(value)
        else:
            super().__setattr__(name, value)

def validate_register_layout(register_def: dict) -> bool:
    """Validate that bit fields don't overlap using bitstring."""
    reg_width = register_def.get('width', 32)
    used_bits = BitArray(length=reg_width)
    
    for field in register_def.get('fields', []):
        offset, width = _parse_bits(field.get('bit') or field.get('bits', 0))
        field_mask = BitArray(length=reg_width)
        field_mask[offset:offset + width] = '1' * width
        
        # Check for overlaps using bitstring operations
        if (used_bits & field_mask).any():
            return False
        
        used_bits |= field_mask
    
    return True

def generate_test_patterns(register_def: dict) -> list[BitArray]:
    """Generate comprehensive test patterns for a register using bitstring."""
    reg_width = register_def.get('width', 32)
    patterns = []
    
    # Walking ones pattern
    for i in range(reg_width):
        walking_one = BitArray(length=reg_width)
        walking_one[i] = 1
        patterns.append(walking_one)
    
    # Walking zeros pattern
    for i in range(reg_width):
        walking_zero = BitArray('1' * reg_width)
        walking_zero[i] = 0
        patterns.append(walking_zero)
    
    # Field-specific patterns
    for field in register_def.get('fields', []):
        offset, width = _parse_bits(field.get('bit') or field.get('bits', 0))
        if field.get('access') in ['rw', 'wo']:
            # All ones in this field
            pattern = BitArray(length=reg_width)
            pattern[offset:offset + width] = '1' * width
            patterns.append(pattern)
            
            # Alternating pattern in this field
            alt_pattern = BitArray(length=reg_width)
            field_alt = BitArray('01' * (width // 2) + '0' * (width % 2))
            alt_pattern[offset:offset + width] = field_alt
            patterns.append(alt_pattern)
    
    return patterns

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

def generate_register_documentation(memory_map: dict) -> str:
    """Generate human-readable documentation with bit diagrams using bitstring."""
    doc = []
    
    for reg in memory_map.get('registers', []):
        reg_width = reg.get('width', 32)
        doc.append(f"\n## {reg['name'].upper()} (Offset: 0x{reg['offset']:04X})")
        doc.append(f"Width: {reg_width} bits")
        
        if reg.get('description'):
            doc.append(f"Description: {reg['description']}")
        
        # Create bit field diagram using bitstring
        if reg.get('fields'):
            doc.append("\n### Bit Layout:")
            doc.append("```")
            
            # Create bit position header
            bit_header = "Bit: " + "".join(f"{i%10:1d}" for i in range(reg_width-1, -1, -1))
            doc.append(bit_header)
            
            # Create field visualization
            field_line = "     " + "".join("." for _ in range(reg_width))
            field_chars = list(field_line)
            
            for field in reg.get('fields', []):
                offset, width = _parse_bits(field.get('bit') or field.get('bits', 0))
                # Mark field boundaries
                for i in range(offset, offset + width):
                    pos = 5 + (reg_width - 1 - i)  # Account for "Bit: " prefix
                    if i == offset:
                        field_chars[pos] = '['
                    elif i == offset + width - 1:
                        field_chars[pos] = ']'
                    else:
                        field_chars[pos] = '-'
            
            doc.append("".join(field_chars))
            doc.append("```")
            
            # Field details table
            doc.append("\n### Fields:")
            doc.append("| Field | Bits | Access | Reset | Description |")
            doc.append("|-------|------|--------|-------|-------------|")
            
            for field in reg.get('fields', []):
                offset, width = _parse_bits(field.get('bit') or field.get('bits', 0))
                if width == 1:
                    bits_str = str(offset)
                else:
                    bits_str = f"{offset + width - 1}:{offset}"
                
                reset_val = field.get('reset', 'N/A')
                access_str = field.get('access', 'rw').upper()
                desc = field.get('description', '')
                
                doc.append(f"| {field['name']} | {bits_str} | {access_str} | {reset_val} | {desc} |")
    
    return '\n'.join(doc)

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
from bitstring import BitArray

class Access(Enum):
    RO = auto()
    RW = auto()
    WO = auto()
    RW1C = auto()  # Read/Write, 1 to Clear
    W1SC = auto()  # Write 1, Self-Clearing

@dataclass
class BitField:
    name: str
    offset: int
    width: int
    access: Access = Access.RW
    description: str = ''
    reset_value: Optional[int] = None

@dataclass 
class Register:
    """Pure register definition without bus coupling."""
    name: str
    offset: int  # Relative to memory map base
    width: int
    fields: list[BitField] = field(default_factory=list)
    description: str = ''
    _fields_by_name: dict[str, BitField] = field(init=False, repr=False)

    def __post_init__(self):
        self._fields_by_name = {f.name: f for f in self.fields}

    def read_field(self, field_name: str, register_value: Union[int, BitArray]) -> int:
        """Extract field value from a register value."""
        if field_name not in self._fields_by_name:
            raise ValueError(f"Register '{self.name}' has no field '{field_name}'")
        
        field = self._fields_by_name[field_name]
        if field.access in ['wo', 'w1sc']:
            raise ValueError(f"Field '{field_name}' is write-only")
        
        if BITSTRING_AVAILABLE and hasattr(register_value, 'uint'):
            reg_int = register_value.uint
        else:
            reg_int = int(register_value)
        
        return field.extract_value(reg_int)

    def write_field(self, field_name: str, register_value: Union[int, BitArray], field_value: int) -> Union[int, BitArray]:
        """Insert field value into a register value, handling access types."""
        if field_name not in self._fields_by_name:
            raise ValueError(f"Register '{self.name}' has no field '{field_name}'")
        
        field = self._fields_by_name[field_name]
        if field.access == 'ro':
            raise ValueError(f"Field '{field_name}' is read-only")
        
        if BITSTRING_AVAILABLE and hasattr(register_value, 'uint'):
            reg_int = register_value.uint
            return_bitarray = True
        else:
            reg_int = int(register_value)
            return_bitarray = False
        
        if field.access == 'rw1c':
            # Clear bits where field_value has 1s
            clear_mask = (field_value << field.offset) & field.mask
            result = reg_int & ~clear_mask
        elif field.access == 'w1sc':
            # Self-clearing fields - just set the value
            result = field.insert_value(0, field_value)
        else:
            # Normal RW or WO fields
            result = field.insert_value(reg_int, field_value)
        
        if return_bitarray and BITSTRING_AVAILABLE:
            return BitArray(uint=result, length=self.width)
        return result

    def debug_info(self, register_value: Union[int, BitArray]) -> str:
        """Generate debug information for a register value."""
        if BITSTRING_AVAILABLE and hasattr(register_value, 'uint'):
            raw_int = register_value.uint
            binary_str = register_value.bin
        else:
            raw_int = int(register_value)
            binary_str = f"{raw_int:0{self.width}b}"
        
        info = [f"Register '{self.name}' (0x{self.offset:04X}):"]
        info.append(f"  Raw value: 0x{raw_int:0{self.width//4}X}")
        info.append(f"  Binary:    {binary_str}")
        
        for field in self.fields:
            if field.access not in ['wo', 'w1sc']:
                field_value = self.read_field(field.name, register_value)
                field_width_str = f"{field.offset + field.width - 1:2d}:{field.offset:2d}" if field.width > 1 else f"{field.offset:2d}"
                field_bits = f"{field_value:0{field.width}b}"
                info.append(f"  {field.name:15s} [{field_width_str}] = {field_bits} (0x{field_value:X}) {field.access.upper()}")
        
        return '\n'.join(info)

@dataclass
class MemoryMap:
    """Represents the complete memory map of an IP core."""
    name: str
    base_address: int
    bus_interface: "AbstractBusInterface"
    registers: dict[str, Register] = field(default_factory=dict)
    register_arrays: dict[str, "RegisterArrayAccessor"] = field(default_factory=dict)
    
    def read_register(self, register_name: str) -> Union[int, BitArray]:
        """Read a register through the bus interface."""
        if register_name not in self.registers:
            raise ValueError(f"No register '{register_name}' in memory map")
        
        register = self.registers[register_name]
        raw_value = self.bus_interface.read_word(self.base_address + register.offset, register.width)
        
        if BITSTRING_AVAILABLE:
            return BitArray(uint=raw_value, length=register.width)
        return raw_value
    
    def write_register(self, register_name: str, value: Union[int, BitArray]) -> None:
        """Write a register through the bus interface."""
        if register_name not in self.registers:
            raise ValueError(f"No register '{register_name}' in memory map")
        
        register = self.registers[register_name]
        
        if BITSTRING_AVAILABLE and hasattr(value, 'uint'):
            int_value = value.uint
        else:
            int_value = int(value)
        
        self.bus_interface.write_word(self.base_address + register.offset, int_value, register.width)
    
    def read_field(self, register_name: str, field_name: str) -> int:
        """Read a specific field from a register."""
        register_value = self.read_register(register_name)
        register = self.registers[register_name]
        return register.read_field(field_name, register_value)
    
    def write_field(self, register_name: str, field_name: str, field_value: int) -> None:
        """Write a specific field in a register."""
        register = self.registers[register_name]
        field = register._fields_by_name[field_name]
        
        if field.access in ['rw', 'rw1c']:
            # Need to read current value for read-modify-write
            current_value = self.read_register(register_name)
        else:
            # Write-only or self-clearing fields
            current_value = 0
        
        new_value = register.write_field(field_name, current_value, field_value)
        self.write_register(register_name, new_value)
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
# Basic register and field access
driver.control.enable = 1
status = driver.status.ready

# Enhanced debugging with bitstring
print(driver.control.debug_info())
# Output:
# Register 'control' (0x0000):
#   Raw value: 0x00000001
#   Binary:    00000000000000000000000000000001
#   enable          [ 0: 0] = 1 (0x1) RW
#   int_enable      [ 1: 1] = 0 (0x0) RW
#   soft_reset      [31:31] = 0 (0x0) WO

# Compare register states
old_value = 0x00000000
print(driver.control.compare_with(old_value))
# Output: Differences: 00000000000000000000000000000001 (changed bits marked as 1)

# Advanced bit pattern operations
from bitstring import BitArray

# Set complex bit patterns
control_pattern = BitArray('0b10000000000000000000000000000011')
driver.control.write(control_pattern)

# Read as BitArray for advanced manipulation
status_bits = driver.status.read()
error_detected = status_bits[4:8].uint  # Extract error code field

# --- Register arrays provide clean access to Block RAM ---
# Accessing the 5th entry in the lookup table:
driver.lut_entry[5].coefficient = 0xABCD

# Using bitstring for complex LUT patterns
lut_pattern = BitArray(uint=0x5555, length=16)  # Alternating bit pattern
driver.lut_entry[10].write(BitArray(length=32))  # Clear entire entry
driver.lut_entry[10].coefficient = lut_pattern.uint
driver.lut_entry[10].enabled = 1

# Generate and apply test patterns
test_patterns = generate_test_patterns({
    'width': 32,
    'fields': [
        {'name': 'coefficient', 'bits': '[15:0]', 'access': 'rw'},
        {'name': 'enabled', 'bit': 31, 'access': 'rw'}
    ]
})

for i, pattern in enumerate(test_patterns[:5]):  # Test first 5 patterns
    driver.lut_entry[i].write(pattern)
    print(f"LUT[{i}]: {pattern.bin}")

# Validate register layout during development
register_def = {
    'width': 32,
    'fields': [
        {'name': 'enable', 'bit': 0},
        {'name': 'mode', 'bits': '[3:1]'},
        {'name': 'status', 'bits': '[7:4]'}
    ]
}

if validate_register_layout(register_def):
    print("✓ Register layout is valid - no overlapping fields")
else:
    print("✗ Register layout has overlapping fields!")

# Generate documentation
memory_map = {
    'registers': [
        {
            'name': 'control',
            'offset': 0x00,
            'width': 32,
            'description': 'Main control register',
            'fields': [
                {'name': 'enable', 'bit': 0, 'access': 'rw', 'reset': 0, 'description': 'Enable the core'},
                {'name': 'mode', 'bits': '[3:1]', 'access': 'rw', 'reset': 1, 'description': 'Operation mode'}
            ]
        }
    ]
}

doc = generate_register_documentation(memory_map)
print(doc)
# Generates formatted documentation with ASCII bit diagrams
```

-----

## 5\. Key Advantages

  - **Single Source of Truth**: The YAML memory map ensures that hardware documentation, simulation, and hardware control are always in sync.
  - **Portability and Reusability**: A single test script can be executed against both a simulator and a physical FPGA with only a configuration change.
  - **Reduced Boilerplate**: The register map loader eliminates the need to manually write and maintain tedious register definition code. 📝
  - **Enhanced Bit Manipulation**: The bitstring library provides powerful, readable bit operations that eliminate error-prone manual bit masking and shifting.
  - **Advanced Debugging**: Built-in register introspection with bit-level visualization and comparison capabilities for debugging hardware issues.
  - **Comprehensive Validation**: Automatic detection of register layout conflicts and generation of thorough test patterns for verification.
  - **Professional Documentation**: Automatic generation of human-readable register documentation with ASCII bit diagrams directly from the memory map.
  - **Decoupled Design**: Changes to a bus protocol do not require changes to the high-level register access logic.
  - **Clean and Intuitive API**: The user-facing API allows developers to interact with registers and bit fields using simple, dot notation (`driver.reg_name.field_name`).
  - **Handles Complex Structures**: The architecture elegantly supports not only single registers but also complex register arrays and block RAM regions. 🎛️
  - **Memory Efficient**: The driver is lightweight as it doesn't pre-instantiate hundreds of objects for a large RAM; register objects are created on-demand.
  - **Scalability**: New bus backends (e.g., for PCIe or SPI) can be added by simply implementing the `AbstractBusInterface`.
  - **Hardware-Focused**: Bitstring operations are particularly valuable for FPGA/hardware work where bit-level precision and visualization are essential.
